import sys
import os.path
import gwd  # Watchdog timer
from ftplib import FTP  # For communicating with FTP server
import arrow  # For formatting the time format
import pandas as pd  # For reading and interpreting the data
import xml.etree.ElementTree as ET  # For reading XML file for metadata
from influxdb import InfluxDBClient  # For writing to influxdb database


def main(argv):
    # Declare static variables
    filename = "5minagg_latest.txt"  # Altered to work with 5 minute aggregate data

    # Get VDS IDs
    IDs = get_ids()

    # Initiate watchdog
    wd_name = "ucsd.caltrans"
    gwd.auth(wd_name)

    # Establish FTP connection and get necessary file
    try:
        ftp = FTP("pems.dot.ca.gov")
        ftp.login(argv[0], argv[1])
        ftp.cwd("D11/Data/5min")  # This is to work with District 11's 5 minute raw data
        ftp.retrbinary("RETR " + filename, open(filename, "wb").write)
        ftp.quit()
    except:  # TODO: Add specific exceptions for each type of error (see ftplib). Can also do this for other exceptions.
        error_log("FTP Error. Please make sure you entered the username and password for the FTP server as arguments and are able to connect to the server. Exited script")
        sys.exit(1)

    # Open raw data file and get timestamp
    with open(filename, "r") as data_file:
        timestamp = data_file.readline()
    # Convert timestamp to ISO time format and in UTC-0:00 time zone
    iso_timestamp = arrow.get(timestamp, "MM/DD/YYYY HH:mm:ss").replace(tzinfo="US/Pacific")

    # Parse data file using Pandas API
    df = pd.read_csv("5minagg_latest.txt", skiprows = 1, header = None)  # Parses data into Pandas dataframe. Skips first line (timestamp).
    df.columns = ["VDS_ID", "FLOW", "OCCUPANCY", "SPEED", "VMT", "VHT", "Q", "TRAVEL_TIME", "DELAY", "NUM_SAMPLES", "PCT_OBSERVED"]  # Renames headers for the columns. This is based off of provided documentation.

    df = df.set_index("VDS_ID")  #Sets VDS_ID to index for efficient use

    # Get data (flow and occupancy) from file and write to influxdb for all the IDs.
    error_flag = False
    for ID in IDs:
        try:
            flow_data, occupancy_data = get_data(df, int(ID))
        except:
            error_log("Data for %s could not be found. Will not be written to database." % (ID))
            flow_data, occupancy_data = None

        if flow_data and occupancy_data: # Checks to see if data was received
            write_influxdb(ID, flow_data, occupancy_data, iso_timestamp.timestamp)
        else:
            gwd.fault(wd_name, "No data found at {0}".format(ID))  # Notify that there is a fault
            error_flag = True
    if not error_flag:  # Will run if error flag is false (positive). This means that data for all the IDs was found.
        gwd.kick(wd_name, 600)  # Notify that this is running correctly. This signal is valid for 600 seconds.


def get_ids():
    """
    Returns VDS IDs that's data will be extracted from the file and posted to the influxdb server.
    To use the IDs.txt file method, use the vds_discovery.py script or enter specified IDs into the file manually (use line breaks).
    """
    if os.path.isfile("IDs.txt"): # If IDs.txt exists, use the IDs in the file
        with open("IDs.txt") as IDs_file:
            IDs = IDs_file.readlines()  # Read all IDs into list
            IDs = [ID.strip() for ID in IDs]  # Removes whitespace, notably the newline
    else: # Otherwise use hardcoded pre-determined IDs
        IDs = ["1108498", "1108719", "1123087", "1123086", "1108452", "1118544", "1125911", "1123072", "1123081",
               "1123064"]
    return IDs


def get_data(data_df, VDS_ID):
    """
    Returns the flow and occupancy for a specified VDS (based upon ID passed) using the passed Pandas Dataframe.
    Note that VDS_ID must be passed as an integer variable (typecasted from string).
    """
    # Get the flow and occupancy
    flow = data_df.loc[VDS_ID].loc["FLOW"]
    occupancy = data_df.loc[VDS_ID].loc["OCCUPANCY"]

    # Return the values
    return flow, occupancy


def write_influxdb(VDS_ID, flow, occupancy, timestamp):
    """
    Gets metadata and writes data (along with metadata) to influxdb database.
    Data values being stored are currently only flow and occupancy.
    Gets metadata using get_metadata() function.
    Writes each data value using write_point() function.   
    """
    # Get metadata for writing to database as tags
    metadata = get_metadata(VDS_ID)

    # Write flow and occupancy measurements to database.
    write_point("flow", VDS_ID, metadata, flow, timestamp)
    write_point("occupancy", VDS_ID, metadata, occupancy, timestamp)


def get_metadata(identifier):
    """Gets metadata from XML file for use when writing data to database."""
    # Declare metadata dictionary
    metadata = {"name": None, "type": None, "country_id": None, "city_id": None, "freeway_id": None, "freeway_dir": None, "lanes": None, "cal_pm": None, "abs_pm": None, "latitude": None, "longitude": None, "last_modified": None}

    # Parse XML file for metadata
    tree = ET.parse("vds_config.xml")
    root = tree.getroot()
    stations = root[11][1]  # Gets detector_stations child tag in XML file for District 11

    # Finds correct VDS based upon identifier and stores its metadata to dictionary
    for vds in stations.findall("vds"):
        if identifier == vds.get("id"):
            metadata["name"] = vds.get("name")
            metadata["type"] = vds.get("type")
            metadata["county_id"] = vds.get("county_id")
            metadata["city_id"] = vds.get("city_id")
            metadata["freeway_id"] = vds.get("freeway_id")
            metadata["freeway_dir"] = vds.get("freeway_dir")
            metadata["lanes"] = vds.get("lanes")
            metadata["cal_pm"] = vds.get("cal_pm")
            metadata["abs_pm"] = vds.get("abs_pm")
            metadata["latitude"] = vds.get("latitude")
            metadata["longitude"] = vds.get("longitude")
            metadata["last_modified"] = vds.get("last_modified")
            return metadata


def write_point(data_type, identifier, metadata_tags, value, timestamp):
    """
    Writes data point to database.
    Documentation used: http://influxdb-python.readthedocs.io/en/latest/include-readme.html#documentation
    """
    # Creating json body for measurement.
    data_point = [
        {
            "measurement": data_type,
            "tags": {
                "ID": identifier,
                "name": metadata_tags["name"],
                "type": metadata_tags["type"],
                "county_id": metadata_tags["county_id"],
                "city_id": metadata_tags["city_id"],
                "freeway_id": metadata_tags["freeway_id"],
                "freeway_dir": metadata_tags["freeway_dir"],
                "lanes": metadata_tags["lanes"],
                "cal_pm": metadata_tags["cal_pm"],
                "abs_pm": metadata_tags["abs_pm"],
                "latitude": metadata_tags["latitude"],
                "longitude": metadata_tags["longitude"],
                "last_modified": metadata_tags["last_modified"]
            },
            "time": timestamp,
            "fields": {
                "value": value
            }
        }
    ]

    # Write to database
    try:
        client = InfluxDBClient('localhost', 8086, 'root', 'root', 'caltran_traffic')  # caltran_traffic is given name of database
        client.create_database("caltran_traffic")  # Will create database if it does not exist. Otherwise, does not modify database.
        client.write_points(data_point)
    except:
        error_log("Could not write data for {} due to error with InfluxDB database".format(identifier))


def error_log(error):
    # TODO: Replace this with the logging API.
    """For logging errors that occur to the log file."""
    with open("error.log", "a") as file:
        file.write("%s\n" % (error))


# Executes from here
if __name__ == "__main__":
    main(sys.argv[1:])




