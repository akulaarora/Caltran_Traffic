# Caltran_Traffic

This project is intended to read the data from the California Transit dataset for writing traffic timeseries data to a database. This is was created for use by UC San Diego and was created by Akul Arora and Jason Koh.

Please note that the database being used to store the timeseries data is currently InfluxDB, however, this may change. 

## Setup

_Note the following_: In order to use this project, it is required that you have access to the Caltran FTP server.
More information can be found on the [Caltran site](pems.dot.ca.gov). You can also read more about the traffic data from here.

To write data to the database, an Influx server must be setup. 
To learn how to use InfluxDB, look here: https://docs.influxdata.com/influxdb/v1.2/

To use: download the python files and place in a folder that also contains the vds_config.xml file. The XML file is for the python scripts to get metadata for the VDSs.

### Python and Dependencies
_Version_: Tested using Python 3.6 with anaconda3.

The following dependencies/libraries must be installed for Python using pip:

https://github.com/immesys/wd

http://arrow.readthedocs.io/en/latest/

https://pandas.pydata.org/pandas-docs/stable/

https://github.com/influxdata/influxdb-python

## Usage

### main.py

This will read the data from the Caltran FTP server and write to the Influx database for specified Vehicle Detector Stations (VDSs) based upon their IDs (more information on this is in the "Other Notes" section). It is the core of this project.

Use the following command to run main.py. Sudo priviliges are not required:
```
$ python main.py <caltran_username> < caltran_password>
```

To run this as a cronjob, add the following to crontab. Sudo priviliges are not required for cron:
```
*/5 *  *   *   *     cd <directory_containing_files> && python main.py <caltran_username> <caltran_password>
```

__Other Notes__:

_VDS IDs used_: By default, main.py will use the VDS IDs contained in the IDs.txt file (separated by line breaks). If this file does not exist in the same directory as main.py, main.py will resort to a set of VDS IDs that are contained in the code. IDs.txt can be manually created using user-specified IDs, or generated using vds_discovery.py (see below).

_Error logging_: This script will create an error.log file for any errors that appear during runtime. 

Please note that main.py has the following values that can be modified:

1. _Data time length_ - 5 minutes (aggregate). The time granularity is 30 seconds. Can be altered to use 30 seconds raw data rather than 5 minute aggregate.

3. _Watchdog name_ - ucsd.caltrans

4. _District_ - District 11 (\*must be altered in vds_discovery.py as well, if using)

5. _Values being read_ - flow, occupancy, speed, VMT, VHT, delay

### vds_discovery.py

This is an interactive script that takes as input the latitude and longitude of a specific location as well as the radius from that location and outputs the found IDs to files.

This script creates an "IDs.txt" file, which will contain the Mainline/HOV VDS IDs within the radius specified of the location. It will also create an "otherIDs.txt" file that will contain all other IDs within the radius of the location. IDs are separated by line breaks (newline).

The purpose of this is to collect data for a specific area through main.py, which will read the IDs.txt file. _Please note that this is currently set to work with locations within District 11._ The district being used should be kept consistent with that of main.py.

For UC San Diego, the location is 32.879956, -117.233928 and I am using a radius of 0.03 to get approximately two times the size of UCSD.

## Final Notes

This project is still a work in progress and more may be added to it. This is not the final version as various parts of this project may be altered, most notably the server that this data is being written to.
