import folium
from shiny import ui
from folium import Element

# Function to render a basic folium map with custom styling
def render_base_map():
    m = folium.Map(
        location=[46.8182, 8.2275],  # Center of Switzerland
        zoom_start=9,               # Default zoom
        tiles=None,                 # No default tile, we'll add OpenStreetMap manually
        control_scale=True
    )

    # Add a semi-transparent OpenStreetMap tile layer
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Basemap",
        control=False,
        opacity=0.5,
        min_zoom=8,
        max_zoom=16
    ).add_to(m)

    # Add custom style for the folium map container
    m.get_root().html.add_child(folium.Element("""
        <style>
        .folium-map {
            height: height: calc(100vh - 180px);
            width: 100%;
            border: 1px solid #ccc;
        }
        </style>
    """))
    return m

# Function to overlay dynamic layers and markers onto the base map
def add_layers_to_base(base_map, layers, center, zoom):
    m = folium.Map(
        location=center,   # Map center coordinates
        zoom_start=zoom,   # Initial zoom level
        min_zoom=9,
        max_zoom=16,
        tiles=None,
        control_scale=True,
        prefer_canvas=True
    )

    # Add OpenStreetMap tile layer again for consistency
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Basemap",
        control=False,
        opacity=0.5,
        min_zoom=8,
        max_zoom=16
    ).add_to(m)

    # Add all layers/markers passed into this function
    for point in layers:
        point.add_to(m)

    # Add layer control UI
    folium.LayerControl().add_to(m)

    # Apply the same custom CSS style as the base map
    m.get_root().html.add_child(folium.Element("""
        <style>
        .folium-map {
            height: 60vh;
            width: 100%;
            border: 1px solid #ccc;
        }
        </style>
        <script>
        const t0 = performance.now();
        window.addEventListener('load', () => {
            const t1 = performance.now();
            console.log(`[MAP RENDER] Client-side rendering time: ${(t1 - t0).toFixed(2)} ms`);
        });
        </script>
    """))

    m.get_root().html.add_child(folium.Element("""
    <script>
        window.addEventListener('load', function() {
            console.log("[JS] Map iframe loaded, attaching click to delay markers...");

            for (const key in window) {
                if (key.startsWith("delay_")) {
                    const marker = window[key];
                    if (marker && typeof marker.on === "function") {
                        const id = key.replace("delay_", "");

                        marker.on('click', function() {
                            console.log("[JS] Marker clicked, sending ID to parent:", id);

                            // Invia il messaggio all'app Shiny (fuori dall'iframe)
                            window.parent.postMessage(
                                { type: "delay_click", delay_id: id },
                                "*"
                            );
                        });
                    }
                }
            }
        });
    </script>
    <script>
        window.addEventListener('load', function() {
            for (const key in window) {
                if (key.startsWith("situation_")) {
                    const marker = window[key];
                    if (marker && typeof marker.on === "function") {
                        const id = key.replace("situation_", "");
                        marker.on('click', function() {
                            window.parent.postMessage(
                                { type: "situation_click", situation_id: id },
                                "*"
                            );
                        });
                    }
                }
            }
        });
    </script>
    <script>
        window.addEventListener('load', function () {
            const map = document.querySelector('.folium-map')._leaflet_map;
            if (!map) return;

            function updateShinyInputs() {
                const zoom = map.getZoom();
                const center = map.getCenter();
                Shiny.setInputValue("map_zoom_level", zoom);
                Shiny.setInputValue("map_center_lat", center.lat);
                Shiny.setInputValue("map_center_lng", center.lng);
            }

            map.on('zoomend', updateShinyInputs);
            map.on('moveend', updateShinyInputs);

            // Initial trigger
            updateShinyInputs();
        });
    </script>
    """))

    # Return the map as HTML for Shiny rendering
    return ui.HTML(m._repr_html_())
