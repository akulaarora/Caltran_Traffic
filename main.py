#!/usr/bin/env python3

import sys
from ftplib import FTP #for working with FTP server
import os.path #error checking if file was downloaded
import csv

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
    #TODO: 1108719 is giving values of 0. Change this?

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
    timestamp = next(datareader) #TODO: Format based upon timeseries format

    # Get data (flow and occupancy) from file. TODO:  Get metadata from XML and POST to influxdb. Use REST API/influxDB-python client?
    for ID in IDs:
        print(get_data(datareader, ID)) #Temporarily printing values
        data_file.seek(0) #This resets datareader back to beginning of file

    #Close connection with data file
    data_file.close()


def get_data(rows, VDS_ID):
    #Traverse until correct line is found. TODO:Is this too inefficient?
    for row in rows:
        if VDS_ID in row: #checks to see if row is correct
            #Returns flow and occupancy values
            flow = row[3]
            occupancy = row[4]
            return flow, occupancy
    #TODO: This currently returns flow and occupancy values for loop 1. Unsure if loop 10 matters (only available for mainline VDSs).


#Executes from here
if __name__ == "__main__":
    #TODO: Add check if user entered arguments for username and password
    main(sys.argv[1:])

