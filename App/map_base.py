import folium
from shiny import ui
from folium import Element

# Function to render a base map (no slider, no extra UI injected)
def render_base_map():
    m = folium.Map(
        location=[46.8182, 8.2275],
        tiles=None,
        control_scale=True
    )

    # Add OpenStreetMap base layer
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Basemap",
        control=False,
        opacity=0.5,
        min_zoom=8,
        max_zoom=16
    ).add_to(m)

    # Style only (no controls or sliders)
    m.get_root().html.add_child(folium.Element("""
        <style>
            html, body {
                margin: 0;
                padding: 0;
                overflow: hidden;
            }

            .folium-map {
                width: 100%;
                display: block;
                border: none;
            }
        </style>
    """))

    return m

# Function to apply layers and markers on top of the base map (also without slider)
def add_layers_to_base(base_map, layers, center, zoom):
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=None,
        control_scale=True,
        prefer_canvas=True
    )

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Basemap",
        control=False,
        opacity=0.5,
        min_zoom=8,
        max_zoom=16
    ).add_to(m)

    for point in layers:
        point.add_to(m)

    folium.LayerControl().add_to(m)

    # Inject only styling
    m.get_root().html.add_child(folium.Element("""
        <style>
            html, body {
                margin: 0;
                padding: 0;
                height: 90%;
                overflow: hidden;
            }

            .folium-map {
                width: 100%;
                display: block;
                border: none;
            }
        </style>
    """))

    # Add JavaScript to pass map events back to Shiny
    m.get_root().html.add_child(folium.Element("""
        <script>
        window.addEventListener('load', function () {
            console.log("[MAP JS] Iframe loaded. Connecting markers...");

            for (const key in window) {
                if (key.startsWith("delay_")) {
                    const marker = window[key];
                    if (marker && typeof marker.on === "function") {
                        const id = key.replace("delay_", "");
                        marker.on('click', () => {
                            window.parent.postMessage(
                                { type: "delay_click", delay_id: id },
                                "*"
                            );
                        });
                    }
                }

                if (key.startsWith("situation_")) {
                    const marker = window[key];
                    if (marker && typeof marker.on === "function") {
                        const id = key.replace("situation_", "");
                        marker.on('click', () => {
                            window.parent.postMessage(
                                { type: "situation_click", situation_id: id },
                                "*"
                            );
                        });
                    }
                }
            }
        });

        window.addEventListener('load', function () {
            const map = document.querySelector('.folium-map')?._leaflet_map;
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
            updateShinyInputs();
        });
        </script>
    """))

    return ui.HTML(m._repr_html_())
