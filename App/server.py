from shiny import render, reactive, ui
import map_base
from data_logic import load_geojson_for_selection, load_situations_for_datetime, generate_markers_by_zoom, get_color_class, get_color_class_index, delay_bins, colors, data_cache
from datetime import timedelta, datetime, time
import folium
from matplotlib import cm
from matplotlib.colors import to_hex
from collections import Counter
import matplotlib.pyplot as plt
import logging
import time as systime
import threading
from folium import CircleMarker, Marker, DivIcon
import matplotlib
matplotlib.use("Agg")
import numpy as np
from shiny.ui import tags
import builtins
from math import radians, cos, sin, asin, sqrt

# Global reference to background precache thread
precache_thread = None

precache_paused = reactive.Value(False)

# Flag to stop background processing when needed
precache_stop_event = threading.Event()

# Lock to synchronize marker rendering
render_lock = threading.Lock()

# Configure basic logging to the console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Main server function for Shiny app
def server(input, output, session):
    # Reactive value to store base map object
    base_map = reactive.Value(None)

    # Lock to ensure only one window is rendered at a time
    render_lock = threading.Lock()

    # wait till rendering
    precache_trigger = reactive.Value(False)

    # Event to stop background precaching when inputs change
    precache_stop_event = threading.Event()

    # Reference to the background thread
    precache_thread = None

    # Default map center and zoom level
    map_center = reactive.Value([46.8182, 8.2275])
    map_zoom = reactive.Value(8)

    # Mapping AlertCause values to marker icons and colors
    cause_to_icon = {
        "constructionWork": ("wrench", "#FF6B6B"),           # Bright red
        "serviceDisruption": ("exclamation-sign", "#F06595"),  # Pink
        "emergencyServicesCall": ("plus", "#5F0F40"),        # Deep purple
        "vehicleFailure": ("road", "#D00000"),               # Scarlet red
        "poorWeather": ("cloud", "#1C77C3"),                 # Vivid blue
        "routeBlockage": ("remove-sign", "#3A0CA3"),         # Indigo
        "technicalProblem": ("cog", "#FFB703"),              # Gold
        "unknown": ("question-sign", "#6C757D"),             # Neutral grey
        "accident": ("warning-sign", "#E85D04"),             # Orange-red
        "specialEvent": ("flag", "#0FA3B1"),                 # Aqua
        "congestion": ("bullhorn", "#9D02D7"),               # Vivid violet
        "maintenanceWork": ("wrench", "#A44A3F"),            # Brick red
        "undefinedAlertCause": ("info-sign", "#ADB5BD"),     # Light grey
        "liftFailure": ("arrow-up", "#5E412E")               # Bright yellow
    }

    # Cache to avoid recomputing markers
    marker_cache = {}

    @reactive.Effect
    def update_map_zoom_level():
        zoom = input.map_zoom_level()
        if zoom is not None:
            map_zoom.set(zoom)

    @reactive.Effect
    def update_map_center():
        lat = input.map_center_lat()
        lng = input.map_center_lng()
        if lat is not None and lng is not None:
            map_center.set([lat, lng])

    # Clear cache when session ends
    @session.on_ended
    def _():
        marker_cache.clear()

    # Return or generate base map
    @reactive.Calc
    def get_base_map():
        if base_map.get() is None:
            base_map.set(map_base.render_base_map())
        return base_map.get()

    # Load delay data button is clicked
    @reactive.Effect
    @reactive.event(input.load_data)
    def _():
        global precache_thread
        precache_paused.set(True)

        # Get the selected date from UI input
        selected_date = input.selected_date()
        logger.info(f"'Load Data' triggered for date: {selected_date}")

        # Load geojson features from file
        features = load_geojson_for_selection(selected_date, selected_date, True, True)

        # Separate into arrivals and departures
        features_arr = [f for f in features if f["properties"].get("__type__") == "arrival"]
        features_dep = [f for f in features if f["properties"].get("__type__") == "departure"]

        logger.info(f"Loaded {len(features_arr)} arrival and {len(features_dep)} departure features")

        # Store features in reactive cache
        data_cache.set({
            "date_from": selected_date,
            "date_to": selected_date,
            "features_arr": features_arr,
            "features_dep": features_dep
        })

        builtins.global_data_snapshot = {
            "features_arr": features_arr,
            "features_dep": features_dep,
            "date_from": selected_date,
        }

        # Stop any previously running precache thread
        if precache_thread and precache_thread.is_alive():
            precache_stop_event.set()
            precache_thread.join()

        # Prepare new thread parameters
        precache_paused.set(False)
        date_from_val = selected_date
        current_index = input.time_window() -1
        show_arr = input.show_arrivals()
        show_dep = input.show_departures()
        features_arr_copy = features_arr.copy()
        features_dep_copy = features_dep.copy()
    
    @reactive.Effect
    def on_time_change():
        _ = input.time_window() -1
        _ = input.show_arrivals()
        _ = input.show_departures()

        # Interrupt any running background rendering
        if precache_thread and precache_thread.is_alive():
            precache_stop_event.set()


    # Check if any delay data was loaded
    @reactive.Calc
    def data_is_loaded():
        data = data_cache.get()
        return len(data.get("features_arr", [])) > 0 or len(data.get("features_dep", [])) > 0

    # Generate markers (delay & situations) for current time window
    @reactive.Calc
    def current_markers():
        with render_lock:
            start_time = systime.time()
            logger.info("Generating current markers...")

            window_index = max(0, input.time_window() - 1)
            show_arr = input.show_arrivals()
            show_dep = input.show_departures()
            selected_date = input.selected_date()

            zoom_level = 10
            zoom_threshold = 11

            cached_data = data_cache.get()
            delay_layers = []
            situation_markers = []

            if cached_data and cached_data.get("date_from") == selected_date:
                logger.info("Using cached markers for delay data")

                def make_unique_delay_id(feature):
                    props = feature["properties"]
                    return f'{props["id"]}_{props["__type__"]}'

                features = []
                if show_arr:
                    for f in cached_data.get("features_arr", []):
                        f["properties"]["delay_id"] = make_unique_delay_id(f)
                        features.append(f)
                if show_dep:
                    for f in cached_data.get("features_dep", []):
                        f["properties"]["delay_id"] = make_unique_delay_id(f)
                        features.append(f)

                delay_layers = generate_markers_by_zoom(
                    features=features,
                    value_index=window_index,
                    zoom_level=zoom_level,
                    zoom_threshold=zoom_threshold,
                    get_color_func=get_color_class,
                    get_class_func=get_color_class_index,
                    delay_bins=delay_bins,
                    show_popup=False
                )
            else:
                logger.info("No valid cache for delays or date mismatch: skipping delay markers")

            cache_key = (
                cached_data.get("date_from") if cached_data else None,
                show_arr,
                show_dep,
                window_index,
                zoom_level
            )

            if (
                cached_data and
                cached_data.get("date_from") == selected_date and
                cache_key in marker_cache
            ):
                logger.info("Using cached delay markers")
                delay_layers = marker_cache[cache_key]
            else:
                if cached_data and cached_data.get("date_from") == selected_date:
                    marker_cache[cache_key] = delay_layers
                else:
                    logger.info("Skipping delay marker cache due to date mismatch")

            try:
                start_seconds = window_index * 900
                selected_time = datetime.combine(
                    selected_date,
                    time(hour=start_seconds // 3600, minute=(start_seconds % 3600) // 60)
                )

                sqlite_path = "../DB/situations_sirisx.sqlite"
                csv_mapping_path = "../Data/actual_date-swiss-only-service_point-2025-05-20.csv"

                logger.info(f"Loading situations for datetime: {selected_time}")
                situations = load_situations_for_datetime(sqlite_path, csv_mapping_path, selected_time, language="de")
                logger.info(f"Loaded {len(situations)} situations")

                for _, row in situations.iterrows():
                    lat, lon = row["coords"]
                    lat += 0.0003
                    lon -= 0.0003
                    cause = str(row["AlertCause"]).strip()
                    icon_name, icon_color = cause_to_icon.get(cause, ("question-sign", "gray"))

                    html = f"""
                        <div 
                            data-situation-id="{row['SituationID']}"
                            class="leaflet-interactive"
                            onclick="window.parent.postMessage({{ type: 'situation_click', situation_id: '{row['SituationID']}' }}, '*')"
                            style="
                                width: 32px;
                                height: 32px;
                                background-color: {icon_color};
                                clip-path: polygon(50% 0%, 100% 38%, 78% 100%, 22% 100%, 0% 38%);
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                box-shadow: 0 1px 4px rgba(0,0,0,0.3);
                                color: white;
                                font-size: 14px;
                                cursor: pointer;
                            "
                        >
                            <span class="glyphicon glyphicon-{icon_name}"></span>
                        </div>
                        """


                    icon = DivIcon(
                        icon_size=(32, 32),
                        icon_anchor=(16, 32),
                        html=html
                    )

                    marker = Marker(location=[lat, lon], icon=icon)
                    situation_markers.append(marker)


            except Exception as e:
                logger.error(f"Error loading situations: {e}")

            all_markers = delay_layers + situation_markers

            logger.info(f"Generated {len(all_markers)} marker objects in {systime.time() - start_time:.2f} seconds")
            return all_markers

    # Map output
    @output
    @render.ui
    def map():
        render_start = systime.time()
        base = get_base_map()
        logger.info(f"Returned base_map in {(systime.time()-render_start):.2f} seconds")

        render_start = systime.time()
        layers = current_markers()
        logger.info(f"Returned current_markers in {(systime.time()-render_start):.2f} seconds")
        logger.info(f"Number of layers being added to the map: {len(layers)}")

        render_start = systime.time()
        html = map_base.add_layers_to_base(None, layers, map_center.get(), map_zoom.get())
        logger.info(f"Returned UI map HTML in {(systime.time()-render_start):.2f} seconds")

        # Return first, then trigger precache
        result = html
        precache_trigger.set(False)  
        precache_trigger.set(True)  
        return result


    # Display time window label
    @output
    @render.ui
    def timeline():
        window_index = input.time_window() - 1
        start_seconds = window_index * 900
        end_seconds = start_seconds + 899
        start_time = str(timedelta(seconds=start_seconds)).rjust(8, "0")
        end_time = str(timedelta(seconds=end_seconds)).rjust(8, "0")
        return ui.tags.div(f"Time Window: {start_time} - {end_time}", style="margin-top: 10px; font-weight: bold;")

    # Delay color legend output
    @output
    @render.ui
    def bottom_legend():
        if not data_is_loaded():
            return ui.HTML("")
        legend_items = ""
        for i in range(len(delay_bins) - 1):
            lower = delay_bins[i]
            upper = delay_bins[i + 1]
            color = colors[i]
            if lower == -float("inf"):
                label = "< -300s"
            elif upper == 0:
                label = "-300s – 0s"
            elif upper == float("inf"):
                label = f"> {lower}s"
            else:
                label = f"{lower}s – {upper}s"
            legend_items += f"""
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <div style="width: 20px; height: 12px; background:{color}; margin-right: 6px;"></div>
                    <div style="font-size: 11px;">{label}</div>
                </div>
            """
        return ui.HTML(f"""
            <div style="margin-top: 20px;">
                <div style="font-weight: bold; font-size: 12px; margin-bottom: 8px;">Delays classes
                </div>
                {legend_items}
            </div>
        """)

    # Generate horizontal bar chart of delay counts
    @output
    @render.plot
    def marker_bar_chart():
        features_arr = data_cache.get().get("features_arr", [])
        features_dep = data_cache.get().get("features_dep", [])

        window_index = input.time_window() - 1
        show_arr = input.show_arrivals()
        show_dep = input.show_departures()

        true_delays = []

        if show_arr:
            for f in features_arr:
                v = f["properties"].get("v", [])
                if 0 <= window_index < len(v):
                    entry = v[window_index]
                    d = entry.get("d", None)
                    n = entry.get("n", entry.get("c", None))
                    if d is not None and n and n > 0:
                        true_delays.append(d)

        if show_dep:
            for f in features_dep:
                v = f["properties"].get("v", [])
                if 0 <= window_index < len(v):
                    entry = v[window_index]
                    d = entry.get("d", None)
                    n = entry.get("n", entry.get("c", None))
                    if d is not None and n and n > 0:
                        true_delays.append(d)

        marker_groups = current_markers()
        all_markers = []

        def extract_markers(layer):
            if isinstance(layer, CircleMarker) and 'class' in layer.options:
                all_markers.append(layer)
            elif hasattr(layer, '_children'):
                for child in layer._children.values():
                    extract_markers(child)

        for group in marker_groups:
            extract_markers(group)

        class_counts = Counter(marker.options.get('class') for marker in all_markers)

        labels, values, color_list = [], [], []
        for i in range(len(delay_bins) - 1):
            lower = delay_bins[i]
            upper = delay_bins[i + 1]
            color = colors[i]
            count = class_counts.get(i, 0)

            if lower == -float("inf"):
                label = "< -300s"
            elif upper == 0:
                label = "-300s – 0s"
            elif upper == float("inf"):
                label = f"> {lower}s"
            else:
                label = f"{lower}s – {upper}s"

            labels.append(label)
            values.append(count)
            color_list.append(color)

        fig, ax = plt.subplots(figsize=(6, 8))
        y_positions = range(len(labels))
        bars = ax.barh(y_positions, values, color=color_list)

        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels, fontsize=10)
        ax.set_xlabel("Number of Markers", fontsize=11)
        ax.set_title("Delay Distribution", fontsize=13, weight='bold')

        for bar in bars:
            width = bar.get_width()
            y = bar.get_y() + bar.get_height() / 2
            ax.text(width + 0.5, y, str(int(width)), va='center', fontsize=9)

        for spine in ['top', 'right', 'left', 'bottom']:
            ax.spines[spine].set_visible(False)

        ax.xaxis.grid(True, linestyle='--', alpha=0.5)
        ax.set_axisbelow(True)

        #Show stddev annotations with percentage coverage
        if true_delays:
            mu = np.mean(true_delays)
            sigma = np.std(true_delays)

            info_lines = [
                (1, 68.27),
                (2, 95.45),
                (3, 99.73)
            ]

            for i, percent in info_lines:
                lower = mu - i * sigma
                upper = mu + i * sigma
                ax.text(
                    0.98, 0.98 - 0.05 * i,
                    f"±{i}σ ≈ [{lower:.1f}s – {upper:.1f}s] → {percent:.2f}%",
                    transform=ax.transAxes,
                    fontsize=9,
                    color="black",
                    ha="right",
                    va="top",
                    bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.3')
                )

        try:
            plt.tight_layout()
        except Exception as e:
            logger.warning(f"tight_layout failed: {e}")

    # AlertCause legend
    @output
    @render.ui
    def alert_legend():
        html = """
        <div style="margin-top: 20px;">
            <div style="font-weight: bold; font-size: 12px; margin-bottom: 8px;">Unplanned events type</div>
            <div style="font-size: 12px;">
        """

        for cause, (icon, color) in cause_to_icon.items():
            html += f"""
            <div style="margin-bottom: 6px; display: flex; align-items: center;">
                <span class="glyphicon glyphicon-{icon}" style="color: {color}; margin-right: 8px;"></span>
                {cause}
            </div>
            """

        html += "</div></div>"
        return ui.HTML(html)
    
    @output
    @render.ui
    def marker_info_panel():
        # Extract clicked delay ID with type suffix
        delay_id = input.clicked_delay_id()
        if not delay_id:
            return ui.HTML("<p>No point selected.</p>")

        # Split into base ID and feature type
        parts = str(delay_id).split("_")
        base_id = parts[0]
        selected_type = parts[1] if len(parts) > 1 else None

        # Determine which types are currently enabled by checkboxes
        show_arrivals = input.show_arrivals()
        show_departures = input.show_departures()

        # Filter features accordingly
        all_features = []
        if show_arrivals:
            all_features += data_cache.get().get("features_arr", [])
        if show_departures:
            all_features += data_cache.get().get("features_dep", [])

        # Match feature by ID and type
        target = next(
            (
                f for f in all_features
                if str(f["properties"].get("id")) == base_id
                and f["properties"].get("__type__") == selected_type
            ),
            None
        )

        if not target:
            return ui.HTML(f"<p>No data found for ID: {delay_id}</p>")

        # Extract values for display
        name = target["properties"].get("n", "Unnamed")
        v_data = target["properties"].get("v", [])
        raw_type = target["properties"].get("t", "unknown")
        feature_type = target["properties"].get("__type__", "unknown")

        # Get current time window index
        window_index = input.time_window() - 1

        delay = None
        n_vehicles = None
        if 0 <= window_index < len(v_data):
            entry = v_data[window_index]
            delay = entry.get("d", None)
            n_vehicles = entry.get("n", None) or entry.get("c", None)

        delay_text = f"{delay:.0f} s" if delay is not None else "No Data"
        count_text = f" ({n_vehicles} Vehicles)" if n_vehicles is not None else ""

        html = f"""
            <div style="font-family: 'Segoe UI', sans-serif; font-size: 14px;">
                <h4 style="margin-top: 0;">{name}</h4>
                <p><strong>ID:</strong> {base_id}<br>
                <strong>Delays:</strong> {delay_text}{count_text}<br>
                <strong>Category:</strong> {feature_type.capitalize()}<br>
                <strong>Type:</strong> {raw_type}</p>
            </div>
        """

        return ui.HTML(html)


    @reactive.Effect
    @reactive.event(precache_trigger)
    def delayed_precache_start():
        global precache_thread

        logger.info(">>> precache_trigger received — checking if paused or already running")

        if precache_paused.get():
            logger.info("Precaching è in pausa — skipping")
            return

        if precache_thread and precache_thread.is_alive():
            logger.info("Precaching already running — skipping")
            return

        selected_date = input.selected_date()
        current_index = input.time_window() - 1
        show_arr = input.show_arrivals()
        show_dep = input.show_departures()

        features_arr_copy = data_cache.get().get("features_arr", []).copy()
        features_dep_copy = data_cache.get().get("features_dep", []).copy()

        # Define the thread function to precache clusters for all other time windows
        def run_precache(date_from, show_arrivals, show_departures, current_idx, features_arr, features_dep):
            logger.info(f"Entered precache with index={current_idx}")
            systime.sleep(1)

            for idx in range(1, 97):  # Loop over 96 time windows
                if idx == current_idx:
                    continue  # Skip the current window

                if precache_stop_event.is_set():
                    logger.info(f"Precaching stopped at window {idx}")
                    break

                try:
                    logger.info(f"Precaching markers for window {idx}")

                    # Combine features based on selection
                    features = []
                    if show_arrivals:
                        features += features_arr
                    if show_departures:
                        features += features_dep

                    # Generate markers using the shared cluster/point function
                    markers = generate_markers_by_zoom(
                        features=features,
                        value_index=idx,
                        zoom_level=12,
                        zoom_threshold=11,
                        get_color_func=get_color_class,
                        get_class_func=get_color_class_index,
                        delay_bins=delay_bins,
                        show_popup=False
                    )

                    # Cache the result
                    cache_key = (date_from, show_arrivals, show_departures, idx, 12)
                    marker_cache[cache_key] = markers

                    logger.info(f"Precached {len(markers)} markers for window {idx}")
                    systime.sleep(0.25)

                except Exception as e:
                    logger.error(f"Error while precaching window {idx}: {e}")

        # Start the precache thread
        precache_thread = threading.Thread(
            target=run_precache,
            args=(selected_date, show_arr, show_dep, current_index, features_arr_copy, features_dep_copy),
            daemon=True
        )
        precache_thread.start()

    @output
    @render.plot
    def selected_point_timeseries():
        delay_id = input.clicked_delay_id()
        if not delay_id:
            return

        parts = str(delay_id).split("_")
        base_id = parts[0]
        selected_type = parts[1] if len(parts) > 1 else None

        show_arrivals = input.show_arrivals()
        show_departures = input.show_departures()

        all_features = []
        if show_arrivals:
            all_features += data_cache.get().get("features_arr", [])
        if show_departures:
            all_features += data_cache.get().get("features_dep", [])

        feature = next(
            (f for f in all_features if str(f["properties"].get("id")) == base_id and f["properties"].get("__type__") == selected_type),
            None
        )

        if not feature:
            return

        v_data = feature["properties"].get("v", [])
        delays = [entry.get("d") for entry in v_data]

        labels = [f"{i//4:02}:00" if i % 4 == 0 else "" for i in range(len(delays))]

        name = feature["properties"].get("n", "Unknown")

        fig, ax = plt.subplots(figsize=(10, 3.5))

        ax.plot(delays, marker='o', linestyle='-', color="#2a6ebb", linewidth=1.8, markersize=4)

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=8, rotation=90)
        ax.set_yticks(ax.get_yticks())
        ax.set_yticklabels([int(y) for y in ax.get_yticks()], fontsize=9)

        ax.set_title(f"Delay trends for {name}", fontsize=11, weight='bold', fontname='Segoe UI')
        ax.set_xlabel("Time", fontsize=9, fontname='Segoe UI')
        ax.set_ylabel("Delays (s)", fontsize=9, fontname='Segoe UI')

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', linestyle='--', alpha=0.4)
        ax.grid(axis='x', visible=False)

        plt.tight_layout(rect=[0.05, 0, 1, 1])

    @output
    @render.ui
    def language_selector():
        if not input.clicked_situation_id():
            return ui.HTML("")

        return ui.input_select(
            "selected_language",
            "Language",
            choices=["en", "de", "fr", "it"],
            selected="en"
        )

    @output
    @render.ui
    def situation_info_panel():
        situation_id = input.clicked_situation_id()
        if not situation_id:
            return ui.HTML("<p>No situation selected.</p>")

        selected_date = input.selected_date()
        window_index = input.time_window() - 1
        selected_time = datetime.combine(
            selected_date,
            time(hour=(window_index * 15) // 60, minute=(window_index * 15) % 60)
        )
        language = input.selected_language()

        try:
            sqlite_path = "../DB/situations_sirisx.sqlite"
            csv_mapping_path = "../Data/actual_date-swiss-only-service_point-2025-05-20.csv"
            logger.info(f"Looking for situation ID: {situation_id}")
            df = load_situations_for_datetime(sqlite_path, csv_mapping_path, selected_time, language)
            df["SituationID"] = df["SituationID"].astype(str)

            builtins.global_situation_df = df

            row = df[df["SituationID"] == str(situation_id)]

            if row.empty:
                return ui.HTML(f"<p>No data found for situation ID: {situation_id}</p>")

            row = row.iloc[0]

        except Exception as e:
            return ui.HTML(f"<p>Could not load situation data: {e}</p>")

        html = f"""
        <div style="font-family: 'Segoe UI', sans-serif; font-size: 14px; padding-top: 20px; text-align: left; display: block;">
            <h4 style="margin-bottom: 10px; border-bottom: 1px solid #ddd; padding-bottom: 5px;">
                {row.get('Name', 'Unknown')}
            </h4>
            
            <div style="margin-bottom: 10px;">
                <strong>Cause:</strong> {row['AlertCause']}
            </div>

            <div style="margin-bottom: 10px;">
                <strong>Start:</strong> {row['Publication_Start']}<br>
                <strong>End:</strong> {row['Publication_End']}
            </div>

            <div style="margin-bottom: 10px;">
                <strong>Reason ({language.upper()}):</strong><br>
                <div style="white-space: pre-wrap; font-size: 13px; text-align: left;">
                    {row.get('Reason', 'None') or 'None'}
                </div>
            </div>

            <div style="margin-bottom: 10px;">
                <strong>Description ({language.upper()}):</strong><br>
                <div style="white-space: pre-wrap; font-size: 13px; text-align: left;">
                    {row.get('Description', 'None') or 'None'}
                </div>
            </div>

            <hr style="margin: 10px 0;">
        </div>
        """

        return ui.HTML(html)

    @output
    @render.ui
    def selected_point_plot_box():
        delay_id = input.clicked_delay_id()
        selected_date = input.selected_date()
        if not delay_id:
            return ui.HTML("")  # Show nothing if no point is selected

        # Embed delay_id and date as data attributes for the export button
        return ui.div(
            tags.div(
                tags.button(
                    "",  # No visible text
                    id="open_static_plot_btn",
                    title="Open this chart in a new window",
                    class_="glyphicon glyphicon-new-window",
                    **{
                        "data-delay-id": delay_id,
                        "data-date": str(selected_date),
                        "style": """
                            position: relative;
                            top: 8px;
                            right: 10px;
                            font-size: 16px;
                            background: none;
                            border: none;
                            color: black;
                            cursor: pointer;
                            z-index: 10;
                        """
                    }
                ),
                style="position: relative; height: 0;"
            ),
            ui.output_plot("selected_point_timeseries", fill=False),
            style="position: relative;"
        )

    @output
    @render.ui
    def plot_ready_flag():
        delay_id = input.clicked_delay_id()
        if delay_id:
            return ui.tags.script("window.plotReady = true;")
        else:
            return ui.tags.script("window.plotReady = false;")
        
    @output
    @render.ui
    def situation_delay_plot_box():
        # Check if a situation marker has been clicked
        if not input.clicked_situation_id():
            # If not, show nothing
            return ui.HTML("")

        # If a situation is selected, render the associated plot
        return ui.output_plot("situation_delay_trend", height="400px", fill=False)

        
    @output
    @render.plot
    def situation_delay_trend():
        logger.info("situation_delay_trend triggered")

        # Get clicked situation ID from input
        situation_id = input.clicked_situation_id()
        if not situation_id:
            logger.warning("No situation ID provided")
            return

        # Access the global situation DataFrame set earlier
        situation_df = builtins.global_situation_df
        situation_df["SituationID"] = situation_df["SituationID"].astype(str).str.strip()
        situation_id = str(situation_id).strip()

        # Extract row corresponding to the selected situation
        situation = situation_df[situation_df["SituationID"] == situation_id]
        if situation.empty:
            logger.warning(f"No matching row found for ID: {situation_id}")
            return

        # Extract metadata
        start_time = situation["Publication_Start"].iloc[0].replace(tzinfo=None)
        end_time = situation["Publication_End"].iloc[0].replace(tzinfo=None)
        alert_cause = situation["AlertCause"].iloc[0]
        name = situation["Name"].iloc[0]
        situation_coords = situation["coords"].iloc[0]
        lat0, lon0 = situation_coords

        # Determine selected day and define 15-min windows
        selected_date = input.selected_date()
        day_start = datetime.combine(selected_date, datetime.min.time())
        day_end = datetime.combine(selected_date, datetime.max.time())

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # Earth radius in km
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
            return 2 * R * asin(sqrt(a))

        # Load all delay features
        all_features = data_cache.get().get("features_arr", []) + data_cache.get().get("features_dep", [])

        # Prepare full-day time window (96 slots of 15 minutes)
        avg_delays = []
        time_labels = []

        for i in range(96):
            window_time = day_start + timedelta(minutes=15 * i)
            time_labels.append(window_time.strftime("%H:%M"))
            delays = []

            for feature in all_features:
                coords = feature["geometry"]["coordinates"]
                lat, lon = coords[1], coords[0]
                if haversine(lat0, lon0, lat, lon) <= 10:
                    v = feature["properties"].get("v", [])
                    if i < len(v):
                        entry = v[i]
                        d = entry.get("d")
                        n = entry.get("n", entry.get("c", 0))
                        if d is not None and n > 0:
                            delays.append(d)

            avg_delays.append(np.mean(delays) if delays else np.nan)

        # Plot the data
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(time_labels, avg_delays, marker='o', linestyle='-', color="#2a6ebb", linewidth=1.8, markersize=4)

        # Show only hour labels on x-axis
        hourly_indices = [i for i in range(len(time_labels)) if i % 4 == 0]
        hourly_labels = [time_labels[i] for i in hourly_indices]
        ax.set_xticks(hourly_indices)
        ax.set_xticklabels(hourly_labels, fontsize=8, rotation=90)

        # Add vertical lines for start/end times if they are within the current day
        def add_vertical_line_if_in_day(dt, label):
            if day_start <= dt <= day_end:
                index = int((dt - day_start).total_seconds() // 900)
                if 0 <= index < len(time_labels):
                    ax.axvline(x=index, color='red', linestyle='--', linewidth=1.5, label=label)

        add_vertical_line_if_in_day(start_time, "Start")
        add_vertical_line_if_in_day(end_time, "End")

        # Title and labels
        ax.set_title(
            f"Delay trends within 10 km of unplanned event\n'{alert_cause}' at {name}",
            fontsize=11, weight='bold'
        )
        ax.set_xlabel("Time", fontsize=9)
        ax.set_ylabel("Average Delay (s)", fontsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', linestyle='--', alpha=0.4)

        # Show legend only if any vertical line was drawn
        if (day_start <= start_time <= day_end) or (day_start <= end_time <= day_end):
            ax.legend(loc="upper left", fontsize=8)

        try:
            plt.tight_layout()
        except Exception as e:
            logger.warning(f"tight_layout failed: {e}")

