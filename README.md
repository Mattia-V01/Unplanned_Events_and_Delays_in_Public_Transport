# Unplanned Events and Delays in Public Transport

This application is an interactive dashboard designed to explore and visualize unplanned events and delay patterns in public transport across Switzerland.  
It combines spatial and temporal analysis using real-world data from SIRI SX (for unplanned service disruptions) and actual delay data (aggregated per 15-minute intervals).

Built with [Shiny for Python](https://shiny.posit.co/py/), [Folium](https://python-visualization.github.io/folium/), and [FastAPI](https://fastapi.tiangolo.com/), the app enables users to explore:

- Delay intensity and variation at station-level granularity
- The impact of specific disruption causes (e.g., accidents, maintenance)
- Hour-by-hour evolution of delays with optional historical comparison
- Exportable trend plots per location and unplanned event

## Running the Application with Docker

Follow the steps below to run the application using the pre-built Docker image.

### 1. Install Docker Desktop

- Download and install Docker Desktop (tested with version 4.41.2).
- Once installed, start Docker Desktop and ensure it is running in the background.

### 2. Download the Repository

- Download the repository from GitHub as a ZIP file, or clone it:

```
git clone https://github.com/Mattia-V01/Unplanned_Events_and_Delays_in_Public_Transport.git
```

### 3. Run the Application

To start the app, simply double-click the file:

```
.\Unplanned_Events_and_Delays_in_Public_Transport\UnplannedDockerApp\run-dashboard.bat
```

You can also move this file anywhere on your system (e.g., the desktop) and run it from there.  
```