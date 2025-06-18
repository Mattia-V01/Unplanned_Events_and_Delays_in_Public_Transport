from shiny import ui
from shiny.ui import tags

# Full UI layout with header, left panel, map, slider, and sidebar
ui = ui.TagList(

    # Header bar with title and GitHub link
    tags.div(
        tags.div(
            tags.h2("Unplanned Events and Delays in Public Transport", style="margin: 0;"),
            tags.p(
                ui.HTML("""
                    Spatio-temporal visualization and analysis using 
                    <a href="https://data.opentransportdata.swiss/en/dataset/siri-sx" target="_blank" style="color: #3366cc;">SIRI SX</a>
                    for unplanned events and 
                    <a href="https://data.opentransportdata.swiss/en/dataset/istdaten" target="_blank" style="color: #3366cc;">Actual Data</a>
                """),
                style="font-size: 14px; color: #666; margin-top: 4px;"
            ),
            style="padding-right: 80px;"
        ),
        tags.a(
            tags.span("GitHub"),
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
        style="""
            position: relative;
            width: 100%;
            padding: 20px 24px 10px 24px;
            background-color: white;
            box-shadow: 0 1px 4px rgba(0,0,0,0.1);
            z-index: 1000;
        """
    ),

    # Main layout using page_sidebar
    ui.page_sidebar(

        # Right sidebar (toggleable panel)
        ui.sidebar(
            ui.div(
                ui.output_plot("marker_bar_chart", height="600px", fill=False),
                style="margin-top: 15px; width: 100%; text-align: right;"
            ),
            ui.div(
                ui.output_ui("selected_point_plot_box"),
                ui.output_ui("plot_ready_flag"),
                ui.output_ui("situation_delay_plot_box"),
                style="width: 100%;"
            ),
            position="right",
            open="closed",
            width="35%",
        ),

        # Main container with left sidebar and main map/timeline content
        ui.div(

            # Left fixed-width scrollable control panel
            ui.div(
                ui.input_date("selected_date", "Dates"),
                ui.input_action_button(
                    "load_data", "Load Data",
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
                style="""
                    position: fixed;
                    top: 110px;
                    left: 0;
                    width: 20%;
                    height: calc(100vh - 110px);
                    overflow-y: auto;
                    padding: 10px 16px;
                    border-right: 1px solid #bbb;
                    background-color: white;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 14px;
                    line-height: 1.6;
                    z-index: 999;
                """
            ),

            # Main content area: map, slider and timeline
            ui.div(
                ui.div(
                    ui.output_ui("map"),
                    style="""
                    flex: 1 1 auto;       
                    min-height: 0;
                    overflow: hidden;     
                    """
                ),
                ui.div(
                    ui.input_slider(
                    "time_window", "Time Window",
                    min=1, max=96, value=1, step=1, width="100%"
                    ),
                    ui.output_ui("timeline"),
                    style="""
                    flex: 0 0 auto;
                    padding: 8px 16px;
                    background: white;
                    border-top: 1px solid #ddd;
                    """
                ),
                style="""
                    display: flex;
                    flex-direction: column;
                    margin-left: 19vw; 
                    height: calc(100vh - 160px);
                    box-sizing: border-box;
                """
                )
        ),

        # Global style tweaks
        tags.style("""
            .bslib-page-main.bslib-gap-spacing > div {
                padding-top: 0 !important;
            }

            

            label {
                font-weight: 500;
            }

            input[type="checkbox"] {
                margin-right: 6px;
            }
        """),

        # JavaScript for map interaction and export
        tags.script("""
            window.addEventListener('load', function () {
                setTimeout(() => {
                    const situationTooltips = document.querySelectorAll('[data-situation-id]');
                    situationTooltips.forEach(el => {
                        const situationId = el.getAttribute("data-situation-id");
                        const markerEl = el.closest(".leaflet-interactive");
                        if (markerEl) {
                            markerEl.addEventListener("click", () => {
                                window.parent.postMessage(
                                    { type: "situation_click", situation_id: situationId },
                                    "*"
                                );
                            });
                        }
                    });

                    const delayTooltips = document.querySelectorAll('[data-delay-id]');
                    delayTooltips.forEach(el => {
                        const delayId = el.getAttribute("data-delay-id");
                        const markerEl = el.closest(".leaflet-interactive");
                        if (markerEl) {
                            markerEl.addEventListener("click", () => {
                                window.parent.postMessage(
                                    { type: "delay_click", delay_id: delayId },
                                    "*"
                                );
                            });
                        }
                    });
                }, 1000);
            });

            window.addEventListener("message", function(event) {
                if (event.data?.type === "delay_click") {
                    Shiny.setInputValue("clicked_delay_id", event.data.delay_id, {priority: "event"});
                }
                if (event.data?.type === "situation_click") {
                    Shiny.setInputValue("clicked_situation_id", event.data.situation_id, {priority: "event"});
                }
            });

            document.addEventListener("click", function(e) {
                if (e.target?.id === "open_static_plot_btn") {
                    const btn = e.target;
                    let delayId = btn.getAttribute("data-delay-id")?.split("_").slice(0, 2).join("_");
                    const selectedDate = btn.getAttribute("data-date");

                    if (delayId && selectedDate) {
                        const url = `/static_plot?delay_id=${encodeURIComponent(delayId)}&date=${encodeURIComponent(selectedDate)}`;
                        window.open(url, "_blank", "width=1000,height=600");
                    } else {
                        alert("No point selected. Please click on a delay marker first.");
                    }
                }
            });

            setInterval(() => {
                const delayId = Shiny?.shinyapp?.$inputValues?.clicked_delay_id;
                if (!delayId) {
                    console.log("[DELAY ID] Not ready yet – wait before clicking the export button.");
                } else {
                    console.log(`[DELAY ID] Ready: ${delayId} – you can safely click the export button.`);
                }
            }, 500);
        """)
    )
)
