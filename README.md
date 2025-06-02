# Unplanned Docker App

This repository contains a Dockerized application for managing and visualizing transport delay data.

## Installation Using Docker

Follow the steps below to set up and run the application on your Windows machine.

### 1. Download and Extract

- Download the file `UnplannedDockerAppZip.zip`.
- Extract its content into `C:\`.

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
