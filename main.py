import sys
from ftplib import FTP #for working with FTP server
import os.path #error checking if file was downloaded
import csv
import xml.etree.ElementTree as ET #For reading XML file for metadata
from collections import namedtuple #For returning the metadata from the XML (get_metadata() function) to the write_influxdb() function
from influxdb import InfluxDBClient #For writing to influxdb database


def main(argv):
    #Declare variables
    filename = "30sec_latest.txt"
    IDs = ["1108498", "1108719", "1123087", "1123086", "1108452", "1118544", "1125911", "1123072", "1123081", "1123064"]
    #VDS IDs have been placed in code for ease of use; however, code can be altered to have IDs passed as arguments or via file.

    #Establish FTP connection and get necessary file
    try:
        ftp = FTP("pems.dot.ca.gov")
        ftp.login(argv[0], argv[1])
        ftp.cwd("D11/Data/30sec")  # This is to work with District 11's 30 second raw data
        ftp.retrbinary("RETR " + filename, open(filename, "wb").write)
        ftp.quit()
    except:
        error_log("FTP Error. Please make sure you entered the username and password for the FTP server as arguments and are able to connect to the server. Exited script")
        sys.exit(1)

    #Open raw data file and get data
    data_file = open(filename, "r")
    datareader = csv.reader(data_file) #Using CSV API to read file
    time = format_timestamp(''.join(next(datareader))) #Gets time from file in a list, which is then converted to a string, and manipulated to match timeseries for format

    # Get data (flow and occupancy) from file.
    for ID in IDs:
        try:
            flow_data, occupancy_data = get_data(datareader, ID)
        except:
            error_log("Data for %s could not be found. Will not be written to database." % (ID))

        if flow_data and occupancy_data: #Checks to see if data was indeed received
            write_influxdb(ID, flow_data, occupancy_data, time) #Passes raw flow and occupancy values to write_influxdb() function (along with time) for writing to database.

        data_file.seek(0) #This resets datareader back to beginning of file for next ID

    #Close connection with data file
    data_file.close()


def get_data(rows, VDS_ID):
    #Traverse until correct line is found.
    for row in rows:
        if VDS_ID in row: #checks to see if row is correct
            #Gets flow and occupancy values. Typecasted for use when writing data.
            flow = float(row[3])
            occupancy = float(row[4])

    #Returns values as tuple
    return flow, occupancy



def format_timestamp(timestamp):
    """
    Format provided: 06/15/2017 17:52:30
    Format wanted: 2017-06-15T17:52:30Z
    """
    #Break string into pieces for concatenating
    hourminsec = timestamp[11:]
    month = timestamp[0:2]
    day = timestamp[3:5]
    year = timestamp[6:10]

    #Concatenate strings into timeseries format and return final formatted string
    formatted = "%s-%s-%sT%sZ" % (year, month, day, hourminsec)
    return formatted


def write_influxdb(VDS_ID, flow, occupancy, timestamp):
    #Get metadata for writing to database as tags (metadata is returned in a named tuple)
    metadata = get_metadata(VDS_ID)

    #Write flow and occupancy measurements to database
    write_point("flow", VDS_ID, metadata, flow, timestamp)
    write_point("occupancy", VDS_ID, metadata, occupancy, timestamp)


def get_metadata(identifier):
    #Declare metadata named tuple
    metadata = namedtuple("metadata", "name type county_id city_id freeway_id freeway_dir lanes cal_pm abs_pm latitude longitude last_modified")

    #Parse XML file for metadata
    tree = ET.parse("vds_config.xml")
    root = tree.getroot()
    stations = root[11][1] #Gets detector_stations child tag in XML file for District 11

    #Finds correct VDS based upon identifier and stores to
    for vds in stations.findall('vds'):
        if identifier == vds.get('id'):
            return (metadata(vds.get("name"), vds.get("type"), vds.get("county_id"), vds.get("city_id"), vds.get("freeway_id"), vds.get("freeway_dir"), vds.get("lanes"), vds.get("cal_pm"), vds.get("abs_pm"), vds.get("latitude"), vds.get("longitude"), vds.get("last_modified"))) #Return metadata as named tuple


def write_point(data_type, identifier, metadata_tags, value, timeseries):
    # http://influxdb-python.readthedocs.io/en/latest/include-readme.html#documentation
    # Creating json body for measurement.

    data_point = [
        {
            "measurement": data_type,
            "tags": {
                "ID": identifier,
                "name": metadata_tags.name,
                "type": metadata_tags.type,
                "county_id": metadata_tags.county_id,
                "city_id": metadata_tags.city_id,
                "freeway_id": metadata_tags.freeway_id,
                "freeway_dir": metadata_tags.freeway_dir,
                "lanes": metadata_tags.lanes,
                "cal_pm": metadata_tags.cal_pm,
                "abs_pm": metadata_tags.abs_pm,
                "latitude": metadata_tags.latitude,
                "longitude": metadata_tags.longitude,
                "last_modified": metadata_tags.last_modified
            },
            "time": timeseries,
            "fields": {
                "value": value
            }
        }
    ]

    # Write to database
    client = InfluxDBClient('localhost', 8086, 'root', 'root', 'caltran_traffic')  # caltran_traffic is name of database
    client.write_points(data_point)


def error_log(error):
    with open("error.log", "a") as file:
        file.write(error)

#Executes from here
if __name__ == "__main__":
    main(sys.argv[1:])

