import os
import json
from datetime import datetime
import gzip
import pandas as pd
import sqlite3
import pytz
from folium import CircleMarker, Tooltip
from folium.plugins import MarkerCluster
from collections import defaultdict
from matplotlib import cm
from matplotlib.colors import to_hex
from folium import CircleMarker, FeatureGroup


# This function loads GeoJSON features from compressed arrival and departure files
# depending on selected date range and which types (arrivals/departures) to include.
def load_geojson_for_selection(date_from, date_to, show_arrivals=True, show_departures=True):
    folder_path_arrival = r"./Data/Delays/Arrival"
    folder_path_departure = r"./Data/Delays/Departure"
    features = []

    if show_arrivals:
        for filename in os.listdir(folder_path_arrival):
            if filename.endswith(".geojson.gz"):
                date_str = filename.replace("delays_arr_", "").replace(".geojson.gz", "")
                try:
                    file_date = datetime.strptime(date_str, "%Y%m%d").date()
                    if date_from <= file_date <= date_to:
                        with gzip.open(os.path.join(folder_path_arrival, filename), "rt", encoding="utf-8") as f:
                            data = json.load(f)
                            for feature in data["features"]:
                                feature["properties"]["__type__"] = "arrival"
                                features.append(feature)
                except ValueError:
                    continue

    if show_departures:
        for filename in os.listdir(folder_path_departure):
            if filename.endswith(".geojson.gz"):
                date_str = filename.replace("delays_dep_", "").replace(".geojson.gz", "")
                try:
                    file_date = datetime.strptime(date_str, "%Y%m%d").date()
                    if date_from <= file_date <= date_to:
                        with gzip.open(os.path.join(folder_path_departure, filename), "rt", encoding="utf-8") as f:
                            data = json.load(f)
                            for feature in data["features"]:
                                feature["properties"]["__type__"] = "departure"
                                features.append(feature)
                except ValueError:
                    continue

    return features

# This function loads situation data from a SQLite database and service point CSV
def load_situations_for_datetime(sqlite_path, service_point_csv, selected_datetime, language="en"):
    local_tz = pytz.timezone("Europe/Zurich")

    df_service = pd.read_csv(service_point_csv, sep=';', low_memory=False)
    df_service["sloid"] = df_service["sloid"].astype(str)

    coord_map = dict(zip(df_service["sloid"], zip(df_service["wgs84North"], df_service["wgs84East"])))
    name_map = dict(zip(df_service["sloid"], df_service["designationOfficial"]))

    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(f"SQLite file not found: {sqlite_path}")

    query = """
    SELECT s.*, 
        t.PIA_Desc_EN, t.PIA_Desc_DE, t.PIA_Desc_FR, t.PIA_Desc_IT,
        t.PIA_Reason_EN, t.PIA_Reason_DE, t.PIA_Reason_FR, t.PIA_Reason_IT
    FROM Situations s
    LEFT JOIN Text_L t ON s.SituationID = t.SituationID
    """

    conn = sqlite3.connect(sqlite_path)
    df = pd.read_sql_query(query, conn)
    conn.close()

    df["Publication_Start"] = pd.to_datetime(df["Publication_Start"], errors="coerce", utc=True).dt.tz_convert(local_tz)
    df["Publication_End"] = pd.to_datetime(df["Publication_End"], errors="coerce", utc=True).dt.tz_convert(local_tz)
    selected_time = pd.to_datetime(selected_datetime).tz_localize(local_tz)

    active = df[
        (df["Publication_Start"] <= selected_time) &
        (df["Publication_End"] >= selected_time)
    ].copy()

    active["sloid"] = active["Publish_Affects_StopPlace_Ref"].str.extract(r"(ch:1:sloid:\d+)")[0]
    active["sloid"] = active["sloid"].astype(str)
    active["coords"] = active["sloid"].map(coord_map)
    active["Name"] = active["sloid"].map(name_map)
    active.dropna(subset=["coords"], inplace=True)

    desc_column = f"PIA_Desc_{language.upper()}"
    reason_column = f"PIA_Reason_{language.upper()}"
    active["Description"] = active[desc_column]
    active["Reason"] = active[reason_column]

    return active

# Generate folium markers or clusters depending on zoom level
def generate_markers_by_zoom(
    features,
    value_index,
    zoom_level,
    zoom_threshold,
    get_color_func,
    get_class_func,
    delay_bins,
    show_popup=False
):
    # Separate markers into arrivals and departures
    arrivals_by_class = defaultdict(list)
    departures_by_class = defaultdict(list)

    # Iterate over each GeoJSON feature
    for feature in features:
        values = feature.get("properties", {}).get("v", [])
        if len(values) <= value_index:
            continue  # Skip if not enough time windows

        delay = values[value_index].get("d", None)
        count = values[value_index].get("c", 0)
        if delay is None or count == 0:
            continue  # Skip features without valid delay or count

        lon, lat = feature["geometry"]["coordinates"]
        class_index = get_class_func(delay)
        color = get_color_func(delay)

        # Build a unique marker ID
        raw_id = feature["properties"].get("id", "unknown")
        feature_type = feature["properties"].get("__type__", "unknown")
        marker_id = f"{raw_id}_{feature_type}"

        # Create a folium CircleMarker with delay class
        marker = CircleMarker(
            location=[lat, lon],
            radius=6,
            color='black',
            weight=0.7,
            fill=True,
            fill_color=color,
            fill_opacity=1,
        )

        marker.tooltip = Tooltip(f'<div data-delay-id="{marker_id}"></div>', sticky=False)
        marker.options['class'] = class_index
        marker._name = f"delay_{marker_id}"

        if feature_type == "arrival":
            arrivals_by_class[class_index].append(marker)
        elif feature_type == "departure":
            departures_by_class[class_index].append(marker)

    # Helper to build a FeatureGroup with or without clustering
    def build_group_by_class(name, class_dict):
        group = FeatureGroup(name=name)

        for class_index, markers in class_dict.items():
            color = get_color_func(delay_bins[class_index])

            if zoom_level < zoom_threshold:
                # Use clustering at lower zoom levels
                icon_create_function = f"""
                function(cluster) {{
                    return L.divIcon({{
                        html: '<div style="background-color: {color}; border-radius: 50%; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; color: white; font-size: 14px;">' + cluster.getChildCount() + '</div>',
                        className: 'marker-cluster',
                        iconSize: new L.Point(36, 36)
                    }});
                }}
                """
                cluster = MarkerCluster(icon_create_function=icon_create_function)
                for marker in markers:
                    cluster.add_child(marker)
                group.add_child(cluster)
            else:
                # Add individual markers at higher zoom levels
                for marker in markers:
                    group.add_child(marker)

        return group

    # Build and return separate groups for arrivals and departures
    arrivals_group = build_group_by_class("Arrivals", arrivals_by_class)
    departures_group = build_group_by_class("Departures", departures_by_class)

    return [arrivals_group, departures_group]

# Define 8 delay bins in seconds
delay_bins = [
    -float("inf"),  # Class 0: very early
    -300,           # Class 1: early
    0,              # Class 2: on time
    30,             # Class 3: slight delay
    60,             # Class 4: moderate delay
    120,            # Class 5: serious delay
    240,            # Class 6: heavy delay
    360,            # Class 7: extreme delay
    float("inf")
]

# Modern desaturated hex colors with a smooth gradient
colors = [
    "#5A93E5",  # Class 0: darker blue
    "#A3D1F5",  # Class 1: light sky blue
    "#98E0A8",  # Class 2: mint green
    "#C6E58A",  # Class 3: light olive
    "#FFE28B",  # Class 4: soft yellow
    "#FFCB6B",  # Class 5: light orange
    "#FFA07A",  # Class 6: light salmon
    "#F08080"   # Class 7: soft red
]

# Map delay value to a HEX color
def get_color_class(d):
    for i in range(len(delay_bins) - 1):
        if delay_bins[i] <= d < delay_bins[i + 1]:
            return colors[i]
    return colors[-1]

# Map delay value to its class index
def get_color_class_index(d):
    for i in range(len(delay_bins) - 1):
        if delay_bins[i] <= d < delay_bins[i + 1]:
            return i
    return len(delay_bins) - 2

# Shared reactive cache to store loaded delay features
from shiny import reactive

data_cache = reactive.Value({
    "date_from": None,
    "date_to": None,
    "features_arr": [],
    "features_dep": []
})