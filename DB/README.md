# Continuous SIRI-SX Data Collection on Raspberry Pi

This script is designed to continuously collect unplanned public transport events in Switzerland using the SIRI-SX API.  
It stores all data into a local SQLite database and runs automatically every hour on a Raspberry Pi.

The script is written in pure Python and uses the official SIRI-SX endpoint provided by [Open Transport Data Switzerland](https://opentransportdata.swiss/en/).

---

## Features

- Fetches data from the official SIRI-SX API
- Stores unplanned disruptions in SQLite format
- Automatically creates all necessary database tables
- Skips planned events and avoids duplicate entries
- Runs every hour without manual intervention
- Designed to run indefinitely on low-power devices like Raspberry Pi

---

## How to Run on Raspberry Pi

You can run the script directly on a Raspberry Pi without Docker or virtualization.  
It uses only lightweight Python libraries and is suitable for headless setups.

### Step 1: Install Python and Pip

Open a terminal and install Python 3 if it's not already installed:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip -y
```

### Step 2: Install Python Dependencies

Install the required Python libraries:

```bash
pip3 install requests schedule
```

### Step 3: Prepare and Run the Script

Open the script (`DB_sirisx.py`) in Thonny and make the following changes:

```python
# 1. Set a valid database path (Linux-compatible)
# Replace:
DB_PATH = "c:/Tesi/Daten/data/situations_sirisx.sqlite"
# With:
DB_PATH = "/home/pi/sirisx_data/situations_sirisx.sqlite"

# 2. Insert your API key
# Replace:
KEY = "YOUR KEY"
# With your actual API key:
KEY = "your_actual_api_key"

# You can create a free API key at:
# https://api-manager.opentransportdata.swiss/

# 3. Save the script and click 'Run' in Thonny to start collecting data.
```
