from shiny import ui
from shiny.ui import tags

# Define the full UI layout using Shiny's sidebar page layout
ui = ui.page_sidebar(

    # Right sidebar with plots (hidden by default)
    ui.sidebar(
        ui.div(
            ui.output_plot("marker_bar_chart", height="600px", fill=False),
            style="margin-top: 15px; width: 100%; text-align: right;"
        ),
        ui.div(
            # Plot for selected delay
            ui.output_ui("selected_point_plot_box"),
            #ui.output_plot("selected_point_timeseries", height="400px", fill=False),
            ui.output_ui("plot_ready_flag"),

            # Plot for selected situation
            ui.output_ui("situation_delay_plot_box"),
            style="width: 100%"
        ),
        position="right",
        open="closed",
        width="800px",
    ),

    # Main layout container
    ui.div(

        # Left panel with user inputs and info panels
        ui.div(
            ui.input_date("selected_date", "Dates"),

            ui.input_action_button(
                "load_data",
                "Load Data",
                style="""
                    color: black;
                    border: none;
                    padding: 6px 12px;
                    font-size: 14px;
                    cursor: pointer;
                    margin-top: 8px;
                    margin-bottom: 12px;
                """
            ),

            ui.input_checkbox("show_arrivals", "Arrivals", value=False),
            ui.input_checkbox("show_departures", "Departures", value=True),

           # Output UI elements (legends, info)
            ui.output_ui("bottom_legend"),
            ui.output_ui("alert_legend"),

            ui.div(
                ui.output_ui("marker_info_panel"),
                style="margin-top: 40px; width: 100%; text-align: left;"
            ),

            ui.output_ui("language_selector"),
            ui.div(
                ui.output_ui("situation_info_panel"),
                style="text-align: left;"
            ),

            # Sidebar styling
            style="""
                width: 250px;
                float: left;
                padding: 10px;
                background-color: #f4f6f8;
                border-right: 1px solid #bbb;
                height: 100%;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                box-shadow: 2px 0 4px rgba(0, 0, 0, 0.01);
            """
        ),

        # Right side: map + time controls
        ui.div(
            ui.output_ui("map"),

            # Hidden input to capture map zoom level (if needed later)
            ui.div(
                ui.input_numeric(
                    "map_zoom_level",
                    "Zoom Level",
                    value=9,
                    min=1,
                    max=20,
                    step=1,
                ),
                style="display: none;"
            ),

            # Time window slider (15-minute steps)
            ui.input_slider(
                "time_window",
                "",             # No label
                min=1,
                max=96,         # 96 x 15min = 24h
                value=1,
                step=1,
                width="100%",
            ),

            # Text display for current time window
            ui.output_ui("timeline"),

            # Styling
            style="""
                margin-left: 270px;
                padding: 20px;
                background-color: white;
                border-radius: 8px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            """
        )
    ),

    # JavaScript for marker click handling and communication with Shiny
    tags.script("""
    // --- Run after page fully loads ---
    window.addEventListener('load', function () {
        console.log("[JS] Waiting 1s before attaching marker click handlers...");

        setTimeout(() => {
            console.log("[JS] Attaching click handlers...");

            // --- Handle SITUATION markers (hexagonal icons) ---
            const situationTooltips = document.querySelectorAll('[data-situation-id]');
            situationTooltips.forEach(el => {
                const situationId = el.getAttribute("data-situation-id");
                const markerEl = el.closest(".leaflet-interactive");
                if (markerEl) {
                    markerEl.addEventListener("click", () => {
                        console.log("[JS] Situation marker clicked:", situationId);
                        window.parent.postMessage(
                            { type: "situation_click", situation_id: situationId },
                            "*"
                        );
                    });
                }
            });

            // --- Handle DELAY markers (circle icons) ---
            const delayTooltips = document.querySelectorAll('[data-delay-id]');
            console.log("[JS] Found delay markers:", delayTooltips.length);
            delayTooltips.forEach(el => {
                const delayId = el.getAttribute("data-delay-id");
                const markerEl = el.closest(".leaflet-interactive");
                if (markerEl) {
                    markerEl.addEventListener("click", () => {
                        console.log("[JS] Delay marker clicked:", delayId);

                        // Send event to Shiny server
                        window.parent.postMessage(
                            { type: "delay_click", delay_id: delayId },
                            "*"
                        );
                    });
                }
            });
        }, 1000);  // Delay to ensure map markers are rendered
    });

    // --- Listen to messages from the map iframe and forward them to Shiny ---
    window.addEventListener("message", function(event) {
         if (event.data && event.data.type === "delay_click") {
            Shiny.setInputValue("clicked_delay_id", event.data.delay_id, {priority: "event"});
            // window.selectedDelayId = event.data.delay_id;  // Keep this accessible from JS
        }
        if (event.data && event.data.type === "situation_click") {
            Shiny.setInputValue("clicked_situation_id", event.data.situation_id, {priority: "event"});
        }
    });

    // --- Handle export button click by reading data-delay-id and data-date from DOM ---
    document.addEventListener("click", function(e) {
        if (e.target && e.target.id === "open_static_plot_btn") {
            const btn = e.target;
            let delayId = btn.getAttribute("data-delay-id");
            if (delayId.includes("_")) {
                delayId = delayId.split("_").slice(0, 2).join("_");  // Keep only id + type
            }
            const selectedDate = btn.getAttribute("data-date");

            if (delayId && selectedDate) {
                const url = `/static_plot?delay_id=${encodeURIComponent(delayId)}&date=${encodeURIComponent(selectedDate)}`;
                window.open(url, "_blank", "width=1000,height=600");
            } else {
                alert("No point selected. Please click on a delay marker first.");
            }
        }
    });

                
    // --- Periodically log delay ID readiness ---
    setInterval(() => {
        const delayId = Shiny?.shinyapp?.$inputValues?.clicked_delay_id;

        if (!delayId) {
            console.log("[DELAY ID] Not ready yet – wait before clicking the export button.");
        } else {
            console.log(`[DELAY ID] Ready: ${delayId} – you can safely click the export button.`);
        }
    }, 500);  // check every 0.5 seconds

"""),

    title = ui.tags.div(
        ui.tags.div(
            ui.tags.h2("Unplanned Events and Delays in Public Transport", style="margin: 0;"),
            ui.tags.p(
                "Spatio-temporal visualization and analysis using SIRI SX for unplanned events and Actual data for delays",
                style="font-size: 14px; color: #666; margin-top: 4px;"
            ),
            style="padding-right: 80px;"
        ),
        ui.tags.a(
            ui.tags.span("GitHub"),
            href="https://github.com/Mattia-V01/Unplanned_Events_and_Delays_in_Public_Transport.git",
            target="_blank",
            style="""
                position: absolute;
                top: 18px;
                right: 24px;
                background-color: #24292e;
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                text-decoration: none;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                z-index: 100;
            """
        ),
        style="position: relative; width: 100%;"
    )

)
