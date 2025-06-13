from shiny import App
from ui import ui
from server import server
from data_logic import load_geojson_for_selection, data_cache
from datetime import datetime as dt
import builtins
from fastapi import FastAPI, Request
from starlette.responses import HTMLResponse
from matplotlib import pyplot as plt
import io
import uvicorn
import webbrowser
import threading

# Create the core Shiny app
shiny_app = App(ui=ui, server=server)

# Create a FastAPI app and mount the Shiny app under root "/"
fastapi_app = FastAPI()

# Define a custom route for static charts
@fastapi_app.get("/static_plot")
async def static_plot(request: Request):
    delay_id = request.query_params.get("delay_id", "")
    date_str = request.query_params.get("date", "")

    if not delay_id or not date_str:
        return HTMLResponse("<p>Missing delay_id or date.</p>", status_code=400)

    date_obj = dt.strptime(date_str, "%Y-%m-%d").date()
    # Read from shared cache (already loaded by the Shiny app)
    cached_data = builtins.global_data_snapshot
    
    # Optional: check if data for the correct date is available
    if cached_data["date_from"] != date_obj:
        return HTMLResponse("<p>Data not loaded for selected date.</p>", status_code=400)

    # Combine features from arrivals and departures
    all_features = cached_data["features_arr"] + cached_data["features_dep"]
    print(f"--- STATIC PLOT DEBUG ---")
    print(f"Requested delay_id: {delay_id}")
    print(f"Requested date: {date_str}")
    print(f"Cache loaded? {cached_data is not None}")
    print(f"Cache date_from: {cached_data.get('date_from')}")
    print(f"Number of features: {len(all_features)}")

    print(f"Number of features: {len(all_features)}")
    print("Available marker IDs in cache:")
    for f in all_features:
        f["properties"]["delay_id"] = f"{f['properties'].get('id')}_{f['properties'].get('__type__')}"
        print(f["properties"]["delay_id"])

    # DEBUG: print the delay ID being requested
    print(f"Looking for delay_id: {delay_id}")

    # Match by prefix (ignore hash suffix)
    def matches_marker_id(f):
        actual_id = f["properties"].get("delay_id")
        return delay_id.startswith(actual_id)

    feature = next((f for f in all_features if matches_marker_id(f)), None)


    if not feature:
        return HTMLResponse("<p>Feature not found.</p>", status_code=404)

    v_data = feature["properties"].get("v", [])
    delays = [entry.get("d") for entry in v_data]
    labels = [f"{i//4:02}:00" if i % 4 == 0 else "" for i in range(len(delays))]

    name = feature["properties"].get("n", "Unknown")

    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(delays, marker='o', linestyle='-', color="#2a6ebb", linewidth=1.8, markersize=4)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8, rotation=90)
    ax.set_title(f"Delay trends for {name}", fontsize=11, weight='bold')
    ax.set_xlabel("Time", fontsize=9)
    ax.set_ylabel("Delays (s)", fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.4)

    buf = io.BytesIO()
    fig.savefig(buf, format="svg")
    buf.seek(0)
    plt.close(fig)
    svg_data = buf.getvalue().decode("utf-8")

    html = f"""
        <html>
        <head>
            <title>Static Delay Chart</title>
            <style>
                body {{
                    margin: 0;
                    font-family: 'Segoe UI', sans-serif;
                    background: #fff;
                    overflow: hidden;
                }}
                h2 {{
                    text-align: center;
                    margin-top: 10px;
                }}
                .chart-container {{
                    width: 100vw;
                    height: calc(100vh - 60px);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                svg {{
                    width: 100%;
                    height: 100%;
                }}
            </style>
        </head>
        <body>
            <h2>{name} – {date_str}</h2>
            <div class="chart-container">
                {svg_data}
            </div>
        </body>
        </html>
        """

    return HTMLResponse(html)

# Auto-launch the app in a browser after a short delay
if __name__ == "__main__":
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:8000")

    # Wait a bit to let the server start, then open the browser
    threading.Timer(1.5, open_browser).start()

    # Start Uvicorn server, binding to all interfaces, and enable live reload
    uvicorn.run(
        "app:fastapi_app",   # Use the FastAPI app
        host="0.0.0.0",
        port=8000,
        reload=True
    )

fastapi_app.mount("/", shiny_app)