import os
import requests
import pandas as pd
import numpy as np
from shapely.geometry import Point
from bs4 import BeautifulSoup
import io
import csv
import json
from datetime import datetime, timedelta
import gzip
import re

# --- Configuration ---
BASE_PAGE_URL = 'https://data.opentransportdata.swiss/dataset/istdaten'
BASE_DOMAIN = 'https://data.opentransportdata.swiss'
ARCHIVE_BASE_URL = 'https://archive.opentransportdata.swiss/actual_data_archive'
OUTPUT_DIR = r'./Data/Delays/Departure'
SERVICE_POINTS_FILE = r'./Data/actual_date-swiss-only-service_point-2025-05-20.csv'
PROCESSED_LOG = os.path.join(OUTPUT_DIR, 'processed_files.txt')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Headers for HTTP requests
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Define 15-minute time windows for the day (96 intervals)
TIME_WINDOWS = [(datetime.min + timedelta(minutes=15 * i)).strftime("%H:%M") for i in range(96)]

# Try to automatically detect CSV delimiter
def detect_delimiter(sample_text):
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(sample_text)
        return dialect.delimiter
    except Exception:
        return ','

# Retrieve all CSV file links for 2025 from the main dataset page (current month data)
def get_2025_csv_links():
    response = requests.get(BASE_PAGE_URL, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    # Find all CSV links on the page containing '2025' in the URL (daily files for current month)
    links = [
        (href if href.startswith('http') else BASE_DOMAIN + href)
        for a_tag in soup.find_all('a', href=True)
        if (href := a_tag['href']).endswith('.csv') and '2025' in href
    ]
    # Exclude March and April 2025 links if present (these will be fetched from the archive)
    links = [link for link in links if not ('/2025-03' in link or '/2025-04' in link)]
    return links

# Convert time into the nearest 15-minute time window string (HH:MM)
def get_zeitfenster(time_obj):
    minute_slot = (time_obj.minute // 15) * 15
    return time_obj.replace(minute=minute_slot, second=0).strftime("%H:%M")

# Recursively convert NumPy types to native Python types (for JSON serialization)
def convert_types(obj):
    if isinstance(obj, dict):
        return {k: convert_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_types(v) for v in obj]
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    else:
        return obj

# Load list of already processed filenames to avoid reprocessing
def load_processed_files():
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, 'r') as f:
            return set(line.strip() for line in f)
    return set()

# Adjust forecast time if delay/advance crosses midnight (±12 hours)
def adjust_forecast_time(row):
    forecast = row['AB_PROGNOSE']
    planned = row['ABFAHRTSZEIT']
    if pd.isnull(forecast) or pd.isnull(planned):
        return forecast
    delta = (forecast - planned).total_seconds()
    if delta < -43200:  # More than 12h early (forecast is next day)
        return forecast + timedelta(days=1)
    elif delta > 43200:  # More than 12h late (forecast is previous day)
        return forecast - timedelta(days=1)
    return forecast

# Helper function to process a single CSV (content already loaded) and export GeoJSON
def process_csv_content(filename, content, service_df, processed_files):
    formatted_date = filename.split('_')[0].replace('-', '')  # e.g., '20250331' for '2025-03-31_IstDaten.csv'
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_geojson_path = os.path.abspath(os.path.join(OUTPUT_DIR, f"delays_dep_{formatted_date}.geojson"))
    # Skip processing if this file was already handled
    if os.path.exists(output_geojson_path) or filename in processed_files:
        print(f"Skipping {filename}")
        return

    # Detect delimiter from sample text
    delimiter = detect_delimiter(content[:2000])
    # Determine if 'PRODUKT_ID' column is present in the header and set usecols accordingly
    header = pd.read_csv(io.StringIO(content), sep=delimiter, nrows=0)
    usecols = ['BETRIEBSTAG', 'BPUIC', 'ABFAHRTSZEIT', 'AB_PROGNOSE', 'AB_PROGNOSE_STATUS']
    if 'PRODUKT_ID' in header.columns:
        usecols.append('PRODUKT_ID')
        print("PRODUKT_ID detected and will be used")
    else:
        print("PRODUKT_ID not found in columns:", header.columns.tolist())

    # Read the CSV content in chunks for memory efficiency
    chunk_iter = pd.read_csv(io.StringIO(content), sep=delimiter, chunksize=50000, engine='c', usecols=usecols)
    daily_files = {}

    for chunk in chunk_iter:
        print("Columns in chunk:", chunk.columns.tolist())
        # Filter for real-time data only and drop rows missing required columns
        chunk = chunk[chunk['AB_PROGNOSE_STATUS'] == 'REAL'].dropna(subset=['BPUIC', 'ABFAHRTSZEIT', 'AB_PROGNOSE'])
        if chunk.empty:
            continue
        # Convert time columns to datetime objects
        chunk['ABFAHRTSZEIT'] = pd.to_datetime(chunk['ABFAHRTSZEIT'], dayfirst=True, errors='coerce')
        chunk['AB_PROGNOSE'] = pd.to_datetime(chunk['AB_PROGNOSE'], dayfirst=True, errors='coerce')
        chunk = chunk.dropna(subset=['ABFAHRTSZEIT', 'AB_PROGNOSE'])
        # Keep only departures after 03:00 to exclude previous night's late departures
        chunk = chunk[chunk['ABFAHRTSZEIT'].dt.time >= datetime.strptime("03:00", "%H:%M").time()]
        # Correct forecast times that cross date boundaries (e.g., predictions past midnight)
        chunk['AB_PROGNOSE'] = chunk.apply(adjust_forecast_time, axis=1)
        # Compute delay in seconds for each departure (negative if early)
        chunk['VERZÖGERUNG'] = (chunk['AB_PROGNOSE'] - chunk['ABFAHRTSZEIT']).dt.total_seconds()
        # Determine 15-minute time window of each departure
        chunk['ZEITFENSTER'] = chunk['ABFAHRTSZEIT'].dt.time.apply(
            lambda t: get_zeitfenster(datetime.combine(datetime.min, t))
        )
        # Join with station data to get station name and coordinates
        merged = pd.merge(chunk, service_df, on='BPUIC', how='inner')

        # Group by date, station, and time window to aggregate delays
        for (date, bpuic, name, east, north, zeitfenster), group in merged.groupby(
            ['BETRIEBSTAG', 'BPUIC', 'HALTESTELLEN_NAME', 'wgs84East', 'wgs84North', 'ZEITFENSTER']
        ):
            if date not in daily_files:
                daily_files[date] = {}
            key = bpuic
            if key not in daily_files[date]:
                # Initialize transport type to 'unknown'
                t_value = 'unknown'
                if 'PRODUKT_ID' in group.columns:
                    values = group['PRODUKT_ID'].dropna()
                    if not values.empty:
                        t_value = values.value_counts().idxmax()
                # Initialize station entry
                daily_files[date][key] = {
                    'coordinates': [east, north],
                    'n': name,
                    'id': bpuic,
                    't': t_value,
                    'v': {tw: {'d': 0.0, 'c': 0} for tw in TIME_WINDOWS}
                }
            # Calculate delay statistics for this 15-min window at the station
            mean_delay = round(group['VERZÖGERUNG'].mean(), 4) if len(group) > 1 else round(group['VERZÖGERUNG'].iloc[0], 4)
            count = int(group['VERZÖGERUNG'].count())
            daily_files[date][key]['v'][zeitfenster] = {'d': mean_delay, 'c': count}

    # Write output GeoJSON (gzipped) per date
    for date, stations in daily_files.items():
        features = []
        for info in stations.values():
            # Prepare delay values array in order of TIME_WINDOWS
            values_array = [info['v'][tw] for tw in TIME_WINDOWS]
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": info['coordinates']},
                "properties": {
                    "n": info['n'],
                    "id": info['id'],
                    "t": info.get('t', 'unknown'),
                    "v": values_array
                }
            })
        geojson_data = {"type": "FeatureCollection", "features": features}
        geojson_data = convert_types(geojson_data)
        out_path = os.path.join(OUTPUT_DIR, f"delays_dep_{datetime.strptime(date, '%d.%m.%Y').strftime('%Y%m%d')}.geojson")
        # Save GeoJSON as .geojson.gz
        with gzip.open(out_path + '.gz', 'wt', encoding='utf-8') as f_out:
            json.dump(geojson_data, f_out)
    print(f"Processed {filename}")

def main():
    # Load station reference data with coordinates
    service_df = pd.read_csv(SERVICE_POINTS_FILE, encoding='utf-8', sep=';', low_memory=False)
    service_df = service_df.rename(columns={'number': 'BPUIC', 'designationOfficial': 'HALTESTELLEN_NAME'})
    service_df = service_df[['BPUIC', 'HALTESTELLEN_NAME', 'wgs84East', 'wgs84North']].dropna()

    # Load already processed filenames from the log file
    processed_files = load_processed_files()

    # Define a function to extract archive links for March and April 2025
    def get_archive_zip_links():
        """
        Manually constructs the correct URLs for March and April 2025 archive ZIPs
        based on known pattern: /istdaten/2025/ist-daten-2025-MM.zip
        """
        months = ['03', '04']
        base_url = 'https://archive.opentransportdata.swiss/istdaten/2025'
        
        links = [
            f"{base_url}/ist-daten-2025-{month}.zip" for month in months
        ]

        print("Archive ZIP URLs to be downloaded:")
        for url in links:
            print(f"  → {url}")
            
        return links

    # Fetch archive ZIP links
    archive_links = get_archive_zip_links()

    # Process each ZIP file from the archive
    from zipfile import ZipFile
    for archive_url in archive_links:
        zip_filename = os.path.basename(archive_url)
        print(f"Downloading archive {zip_filename} from {archive_url} ...")
        try:
            resp = requests.get(archive_url, headers=HEADERS)
            resp.raise_for_status()
            zip_data = ZipFile(io.BytesIO(resp.content))
        except Exception as e:
            print(f"Error opening archive {zip_filename}: {e}")
            continue

        for csv_name in zip_data.namelist():
            if not csv_name.lower().endswith('.csv') and '_IstDaten' not in csv_name:
                continue
            try:
                print(f"Processing {csv_name} from {zip_filename}")
                file_content = zip_data.read(csv_name).decode('utf-8')
                process_csv_content(csv_name, file_content, service_df, processed_files)
                processed_files.add(csv_name)
            except Exception as e:
                print(f"Failed to process {csv_name}: {e}")
                continue

        zip_data.close()

    # Fetch and process current/future 2025 daily CSVs from main dataset page
    links = get_2025_csv_links()
    for idx, link in enumerate(links, start=1):
        filename = os.path.basename(link)
        print(f"Processing file {idx} of {len(links)}: {filename}")
        try:
            response = requests.get(link, headers=HEADERS)
            response.raise_for_status()
            csv_content = response.content.decode('utf-8')
            process_csv_content(filename, csv_content, service_df, processed_files)
            processed_files.add(filename)
        except Exception as e:
            print(f"Failed to download {filename}: {e}")
            continue

    # Save updated processed files log (create or overwrite)
    with open(PROCESSED_LOG, 'w') as f:
        for fname in sorted(processed_files):
            f.write(f"{fname}\n")

    print(f"All available data processed. Log saved to {PROCESSED_LOG}.")

if __name__ == '__main__':
    main()
