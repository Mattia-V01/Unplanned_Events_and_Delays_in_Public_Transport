# Unplanned Events and Delays in Public Transport

This application is an interactive dashboard designed to explore and visualize unplanned events and delay patterns in public transport across Switzerland. It combines **spatial and temporal analysis** using real-world data from SIRI SX (for unplanned service disruptions) and actual delay data (aggregated per 15-minute intervals).

Built with [Shiny for Python](https://shiny.posit.co/py/), [Folium](https://python-visualization.github.io/folium/), and [FastAPI](https://fastapi.tiangolo.com/), the app enables users to explore:

- Delay intensity and variation at station-level granularity
- The impact of specific disruption causes (e.g., accidents, maintenance)
- Hour-by-hour evolution of delays with optional historical comparison
- Exportable trend plots per location and unplanned event

## Installation Using Docker

Follow the steps below to set up and run the application on your Windows machine.

### 1. Download and Extract

- Download the file `UnplannedDockerAppZip.zip`.
- Extract its content into `C:\`.
```
C:\
```

You should now have the following directory:

```
C:\UnplannedDockerApp\UnplannedDockerApp
```

### 2. Install Docker Desktop

- Download and install **Docker Desktop** (tested with version **4.41.2**).
- Once installed, **start Docker Desktop** (make sure it's running in the background).

### 3. Build the Docker Image

Open Command Prompt (`cmd`) and run the following commands:

```
cd C:\UnplannedDockerApp\UnplannedDockerApp
```
```
docker build --no-cache -t transport-delays .
```

> If you placed the Docker files in a different location, adjust the path accordingly.

### 4. Prepare the Run Script

Move the following file to your desktop:

```
C:\UnplannedDockerApp\run-dashboard.bat
```

### 5. Launch the Dashboard

After the Docker build is completed, double-click `run-dashboard.bat` from your desktop to launch the application.

## Support

For custom map-based projects or commercial inquiries, contact me at: [your-email@example.com]
