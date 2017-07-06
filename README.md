# Caltran_Traffic

This project is intended to read the 5-minute flow and occupancy data from the California Transit dataset for writing traffic timeseries data to a database.

Please note that this is currently writing data to an Influx database, however, this may change.

## Setup

__Note the following__: In order to use this project, it is required that you have access to the Caltran FTP server.

More information can be found here: pems.dot.ca.gov


To write data to the database, an Influx database must be setup.
main.py is currently set to writing to localhost using the user pre-created database "caltran_traffic".

To learn how to use InfluxDB, look here: https://docs.influxdata.com/influxdb/v1.2/

Please have Python 3.6 installed.
The following dependencies must be installed for Python using pip: 
https://github.com/immesys/wd

http://arrow.readthedocs.io/en/latest/

https://pandas.pydata.org/pandas-docs/stable/

https://github.com/influxdata/influxdb-python

https://github.com/influxdata/influxdb-python

## Usage

Parameters

Cron job
