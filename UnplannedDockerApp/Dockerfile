FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean

# Set working directory
WORKDIR /app

# Clone repository
RUN git clone https://github.com/Mattia-V01/Unplanned_Events_and_Delays_in_Public_Transport.git

# Change directory to the cloned repo
WORKDIR /app/Unplanned_Events_and_Delays_in_Public_Transport

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the Shiny app
CMD ["shiny", "run", "--reload", "App/app.py"]
