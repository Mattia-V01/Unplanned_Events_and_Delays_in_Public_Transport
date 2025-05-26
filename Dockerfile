# Use a minimal Python 3.11 image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install git, clone the repository, and clean up
RUN apt-get update && \
    apt-get install -y git && \
    git clone https://github.com/Mattia-V01/Unplanned_Events_and_Delays_in_Public_Transport.git && \
    mv Unplanned_Events_and_Delays_in_Public_Transport/* . && \
    mv Unplanned_Events_and_Delays_in_Public_Transport/.* . 2>/dev/null || true && \
    rmdir Unplanned_Events_and_Delays_in_Public_Transport && \
    apt-get remove -y git && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements.txt from local build context (you provide it)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Write run-dashboard.bat to the Windows desktop using a mounted volume
CMD powershell -Command "Set-Content -Path 'C:\\desktop\\run-dashboard.bat' -Value 'docker run -it --rm -p 8000:8000 shiny-dashboard'"
