import sys
from ftplib import FTP #for working with FTP server
import os.path #error checking if file was downloaded
import csv
#from influxdb import InfluxDBClient TODO: Currently unusable as it requires installation.

"""
Currently unnecessary:
import xml.etree.ElementTree as ElementTree #For working with metadata
metadata = ET.parse(vds_config.xml)
root = 
"""


def main(argv):
    #Declare variables
    filename = "30sec_latest.txt"
    IDs = ["1108498", "1108719", "1123087", "1123086", "1108452", "1118544", "1125911", "1123072", "1123081", "1123064"]
    #VDS IDs have been placed in code for ease of use; however, code can be altered to have IDs passed as arguments or via file.

    #Establish FTP connection and get necessary file
    ftp = FTP("pems.dot.ca.gov")
    ftp.login(argv[0], argv[1])
    ftp.cwd("D11/Data/30sec")  # This is to work with District 11's 30 second raw data
    ftp.retrbinary("RETR " + filename, open(filename, "wb").write)
    ftp.quit()

    #Checks if file was successfully received from. If not, breaks out of program.
    if not os.path.isfile(filename):
        print("Could not successfully get file from FTP server") #TODO: This may want to be altered to put errors in a log file
        sys.exit()

    #Open raw data file and get data
    data_file = open(filename, "r")
    datareader = csv.reader(data_file) #Using CSV API to read file
    timestamp = format_timestamp(''.join(next(datareader))) #Gets time from file as a list, which is then converted to a string, and manipulated to match timeseries for format

    # Get data (flow and occupancy) from file. TODO:  Get metadata from XML and POST to influxdb. Use REST API/influxDB-python client?
    for ID in IDs:
        print(get_data(datareader, ID))
        data_file.seek(0) #This resets datareader back to beginning of file

    #Close connection with data file
    data_file.close()


def get_data(rows, VDS_ID):
    #Traverse until correct line is found.
    for row in rows:
        if VDS_ID in row: #checks to see if row is correct
            #Returns flow and occupancy values
            flow = row[3]
            occupancy = row[4]

    #Returns values if they were found
    if flow and occupancy:
        return flow, occupancy
    print("Data for %s could not be found" % (VDS_ID)) #TODO: Put in log file


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


#Executes from here
if __name__ == "__main__":
    #TODO: Add check if user entered arguments for username and password. Put in log file
    main(sys.argv[1:])

