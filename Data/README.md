# OpenTransportData Delay Processing

This repository contains two Python scripts for processing delay data in Swiss public transport, using official datasets from OpenTransportData.swiss.

## Scripts

- Arrival.py: processes arrival delays.
- Departure.py: processes departure delays.

## Requirements

Python 3.8 or higher is required.

## Python Dependencies

Install the required packages with the following command:

pip install requests pandas numpy shapely beautifulsoup4

Dependency list:

- requests: to download data from the internet
- pandas: for handling and processing tabular data
- numpy: for numerical operations
- shapely: for handling geographic coordinates (points)
- beautifulsoup4: for parsing HTML pages

Note: The modules os, csv, io, json, datetime, gzip, and zipfile are part of Python’s standard library.

## Required File

The following file must be present in the specified path:

./Data/actual_date-swiss-only-service_point-2025-05-20.csv

## Execution

To run the scripts:

python Arrival.py  
python Departure.py

## Output

The output files will be saved in the following locations:

- ./Data/Delays/Arrival/
- ./Data/Delays/Departure/

Each file will be in .geojson.gz format and will contain aggregated delay data per day and 15-minute intervals.
