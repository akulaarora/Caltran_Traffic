#!/home/akul/anaconda3/bin/python3

import sys
from ftplib import FTP  # For communicating with FTP server
import arrow  # For formatting the time format
import pandas as pd  # For reading and interpreting the data
import xml.etree.ElementTree as ET  # For reading XML file for metadata
from influxdb import InfluxDBClient  # For writing to influxdb database


def main(argv):
    # Declare variables
    filename = "5minagg_latest.txt"  # Altered to work with 5 minute aggregate data
    # VDS IDs have been placed in code for ease of use; however, code can be altered to have IDs passed as arguments or via file.
    IDs = ["1108498", "1108719", "1123087", "1123086", "1108452", "1118544", "1125911", "1123072", "1123081", "1123064"]
    flow_data = None
    occupancy_data = None

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
    for ID in IDs:
        try:
            flow_data, occupancy_data = get_data(df, int(ID))
        except:
            error_log("Data for %s could not be found. Will not be written to database." % (ID))

        if flow_data and occupancy_data:
            write_influxdb(ID, flow_data, occupancy_data, iso_timestamp.timestamp)


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
    stations = root[11][1] # Gets detector_stations child tag in XML file for District 11

    # Finds correct VDS based upon identifier and stores its metadata to dictionary
    for vds in stations.findall('vds'):
        if identifier == vds.get('id'):
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
    client = InfluxDBClient('localhost', 8086, 'root', 'root', 'caltran_traffic')  # caltran_traffic is given name of database
    client.write_points(data_point)


def error_log(error):
    # TODO: Replace this with the logging API.
    """For logging errors that occur to the log file."""
    with open("error.log", "a") as file:
        file.write("%s\n" % (error))

#Executes from here
if __name__ == "__main__":
    main(sys.argv[1:])




