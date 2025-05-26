# Updated version of your arrivals script
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

# --- Configuration ---
BASE_PAGE_URL = 'https://data.opentransportdata.swiss/dataset/istdaten'
BASE_DOMAIN = 'https://data.opentransportdata.swiss'
ARCHIVE_BASE_URL = 'https://archive.opentransportdata.swiss/istdaten/2025'
OUTPUT_DIR = r'C:/Tesi/Data/Delays/Arrival'
SERVICE_POINTS_FILE = r'C:/Tesi/Data/actual_date-swiss-only-service_point-2025-05-20.csv'
PROCESSED_LOG = os.path.join(OUTPUT_DIR, 'processed_files_arrivals.txt')

os.makedirs(OUTPUT_DIR, exist_ok=True)
HEADERS = {'User-Agent': 'Mozilla/5.0'}
TIME_WINDOWS = [(datetime.min + timedelta(minutes=15 * i)).strftime("%H:%M") for i in range(96)]

def detect_delimiter(sample_text):
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(sample_text)
        return dialect.delimiter
    except Exception:
        return ','

def get_2025_csv_links():
    response = requests.get(BASE_PAGE_URL, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    links = [
        (href if href.startswith('http') else BASE_DOMAIN + href)
        for a_tag in soup.find_all('a', href=True)
        if (href := a_tag['href']).endswith('.csv') and '2025' in href
    ]
    links = [link for link in links if not ('/2025-03' in link or '/2025-04' in link)]
    return links

def get_archive_zip_links():
    months = ['03', '04']
    return [f"{ARCHIVE_BASE_URL}/ist-daten-2025-{month}.zip" for month in months]

def get_zeitfenster(time_obj):
    minute_slot = (time_obj.minute // 15) * 15
    return time_obj.replace(minute=minute_slot, second=0).strftime("%H:%M")

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

def load_processed_files():
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, 'r') as f:
            return set(line.strip() for line in f)
    return set()

def adjust_forecast_time(row):
    forecast = row['AN_PROGNOSE']
    planned = row['ANKUNFTSZEIT']
    if pd.isnull(forecast) or pd.isnull(planned):
        return forecast
    delta = (forecast - planned).total_seconds()
    if delta < -43200:
        return forecast + timedelta(days=1)
    elif delta > 43200:
        return forecast - timedelta(days=1)
    return forecast

def process_csv_content(filename, content, service_df, processed_files):
    formatted_date = filename.split('_')[0].replace('-', '')
    output_geojson_path = os.path.join(OUTPUT_DIR, f"delays_arr_{formatted_date}.geojson")
    if os.path.exists(output_geojson_path) or filename in processed_files:
        print(f"Skipping {filename}")
        return

    delimiter = detect_delimiter(content[:2000])
    header_line = content.split('\n', 1)[0]
    usecols = ['BETRIEBSTAG', 'BPUIC', 'ANKUNFTSZEIT', 'AN_PROGNOSE', 'AN_PROGNOSE_STATUS']
    if 'PRODUCT_ID' in header_line:
        usecols.append('PRODUCT_ID')

    chunk_iter = pd.read_csv(io.StringIO(content), sep=delimiter, chunksize=50000, engine='c', usecols=usecols)
    daily_files = {}

    for chunk in chunk_iter:
        chunk = chunk[chunk['AN_PROGNOSE_STATUS'] == 'REAL'].dropna(subset=['BPUIC', 'ANKUNFTSZEIT', 'AN_PROGNOSE'])
        if chunk.empty:
            continue
        chunk['ANKUNFTSZEIT'] = pd.to_datetime(chunk['ANKUNFTSZEIT'], dayfirst=True, errors='coerce')
        chunk['AN_PROGNOSE'] = pd.to_datetime(chunk['AN_PROGNOSE'], dayfirst=True, errors='coerce')
        chunk = chunk.dropna(subset=['ANKUNFTSZEIT', 'AN_PROGNOSE'])
        chunk = chunk[chunk['ANKUNFTSZEIT'].dt.time >= datetime.strptime("03:00", "%H:%M").time()]
        chunk['AN_PROGNOSE'] = chunk.apply(adjust_forecast_time, axis=1)
        chunk['VERZOGERUNG'] = (chunk['AN_PROGNOSE'] - chunk['ANKUNFTSZEIT']).dt.total_seconds()
        chunk['ZEITFENSTER'] = chunk['ANKUNFTSZEIT'].dt.time.apply(lambda t: get_zeitfenster(datetime.combine(datetime.min, t)))
        merged = pd.merge(chunk, service_df, on='BPUIC', how='inner')

        for (date, bpuic, name, east, north, zeitfenster), group in merged.groupby(
            ['BETRIEBSTAG', 'BPUIC', 'HALTESTELLEN_NAME', 'wgs84East', 'wgs84North', 'ZEITFENSTER']):

            if date not in daily_files:
                daily_files[date] = {}

            if bpuic not in daily_files[date]:
                daily_files[date][bpuic] = {
                    'coordinates': [east, north],
                    'n': name,
                    'id': bpuic,
                    'v': {tw: {'d': 0.0, 'c': 0} for tw in TIME_WINDOWS}
                }

            mean_delay = round(group['VERZOGERUNG'].mean(), 4) if len(group) > 1 else round(group['VERZOGERUNG'].iloc[0], 4)
            count = int(group['VERZOGERUNG'].count())
            daily_files[date][bpuic]['v'][zeitfenster] = {'d': mean_delay, 'c': count}

    for date, stations in daily_files.items():
        features = []
        for info in stations.values():
            values_array = [info['v'][tw] for tw in TIME_WINDOWS]
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": info['coordinates']},
                "properties": {"n": info['n'], "id": info['id'], "v": values_array}
            })

        geojson_data = {"type": "FeatureCollection", "features": features}
        geojson_data = convert_types(geojson_data)
        out_path = os.path.join(OUTPUT_DIR, f"delays_arr_{datetime.strptime(date, '%d.%m.%Y').strftime('%Y%m%d')}.geojson")
        with gzip.open(out_path + '.gz', 'wt', encoding='utf-8') as f_out:
            json.dump(geojson_data, f_out)
    print(f"Processed {filename}")

def main():
    service_df = pd.read_csv(SERVICE_POINTS_FILE, encoding='utf-8', sep=';', low_memory=False)
    service_df = service_df.rename(columns={'number': 'BPUIC', 'designationOfficial': 'HALTESTELLEN_NAME'})
    service_df = service_df[['BPUIC', 'HALTESTELLEN_NAME', 'wgs84East', 'wgs84North']].dropna()
    processed_files = load_processed_files()

    from zipfile import ZipFile
    archive_links = get_archive_zip_links()
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

    with open(PROCESSED_LOG, 'w') as f:
        for fname in sorted(processed_files):
            f.write(f"{fname}\n")

    print(f"All available arrival data processed. Log saved to {PROCESSED_LOG}.")

if __name__ == '__main__':
    main()
