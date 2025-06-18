# Unplanned Events and Delays in Public Transport

This application is an interactive dashboard designed to explore and visualize unplanned events and delay patterns in public transport across Switzerland.  
It combines spatial and temporal analysis using real-world data from SIRI SX (for unplanned service disruptions) and actual delay data (aggregated per 15-minute intervals).

Built with [Shiny for Python](https://shiny.posit.co/py/), [Folium](https://python-visualization.github.io/folium/), and [FastAPI](https://fastapi.tiangolo.com/), the app allows users to:

- Analyze delays at station level
- Explore causes of service disruptions
- Visualize delay patterns over time
- Export charts per location and event type

---

## How to Run the Application

You can run the application using Docker, without installing Python or additional libraries.

### Step 1: Install Docker

Download and install Docker Desktop from the official website:  
https://www.docker.com/products/docker-desktop

Make sure Docker is running before continuing.

### Step 2: Download the Repository

Download the project as a ZIP file from GitHub and extract it to any location,  
or clone it directly using Git:

```
git clone https://github.com/Mattia-V01/Unplanned_Events_and_Delays_in_Public_Transport.git
```

### Step 3: Start the Application

Double-click the `run-dashboard.bat` file included in the project to launch the application.  
Your browser will open automatically at:

```
http://localhost:8000
```

The application runs in a Docker container and does not require any additional setup.

---

## Rebuilding the Docker Image (if necessary)

If needed, you can build the Docker image manually.

1. Open a terminal in the folder containing the Dockerfile.
2. Run the following command to build the image:

```
docker build -f Dockerfile -t ghcr.io/mattia-v01/unplanned-delays-dashboard:latest ..
```

3. Then start the container with:

```
docker run --rm -it -p 8000:8000 ghcr.io/mattia-v01/unplanned-delays-dashboard:latest
```

This may be useful if you have modified the code or if the prebuilt image is unavailable.

## Running Without Docker

If you prefer to run the app without Docker, make sure to manually adjust the relative paths in the source files:  
change all occurrences of `../Data/...` and `../DB/...` to `./Data/...` and `./DB/...` respectively.

After setting up a Python environment and installing the required dependencies, you can start the app locally with:

```
python app.py
```