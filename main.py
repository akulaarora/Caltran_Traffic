import sys
from ftplib import FTP #for working with FTP server
import os.path #error checking if file was downloaded

"""
Currently unnecessary:
import xml.etree.ElementTree as ElementTree #For working with metadata
metadata = ET.parse(vds_config.xml)
root = 
"""


def main(argv):

    #Declare variables
    filename = "30sec_latest_txt"
    IDs = ["1108498", "1108719", "1123087", "1123086", "1108452", "1118544", "1122528", "1123072", "1123081", "1114296"] #VDS IDs have been placed in code; however, code can be altered to have IDs passed as arguments


    #Establish FTP connection and get necessary file
    get_file(filename);

    #Checks if file was successfully received from. If not, breaks out of program. 
    if os.path.isfile(filename) == False:
        print("Could not successfully download file") #NOTE: This may want to be altered to put errors in a log file
        sys.exit()


    #Get timestamp of raw data

    #Get data (occupancy and flow) from file and send to influxdb database. NOTE: Will need to get metadata for VDSs whether from XML file or some other method. Use REST API to send to influx database.
    #NOTE: The raw data file may be readable using CSV APIs



def get_file(file):
    ftp = FTP("pems.dot.ca.gov")
    ftp.login(argv[0], argv[1])
    ftp.cwd("D11/Data/30sec") #This is to work with District 11's 30 second raw data
    ftp.retrbinary("RETR " + file, open(file, "wb").write)
    ftp.quit()


if __name__ == "__main__":
    main(sys.argv[1:])

