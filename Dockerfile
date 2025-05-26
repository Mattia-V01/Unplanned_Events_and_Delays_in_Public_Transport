FROM python:3.11-slim

# Create working directory
WORKDIR /app

# Install git and clone the repo
RUN apt-get update && \
    apt-get install -y git && \
    git clone https://github.com/Mattia-V01/Unplanned_Events_and_Delays_in_Public_Transport.git && \
    mv Unplanned_Events_and_Delays_in_Public_Transport/* . && \
    mv Unplanned_Events_and_Delays_in_Public_Transport/.* . 2>/dev/null || true && \
    rmdir Unplanned_Events_and_Delays_in_Public_Transport

# Overwrite the cloned requirements.txt with the correct one downloaded by the .bat
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Clean up to reduce image size
RUN apt-get remove -y git && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Expose the Shiny app port
EXPOSE 8000

# Run the app
CMD ["shiny", "run", "--reload", "App/app.py"]
