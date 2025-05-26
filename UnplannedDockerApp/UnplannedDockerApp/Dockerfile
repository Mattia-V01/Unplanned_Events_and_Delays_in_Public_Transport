# Use a slim Python image as the base
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install required OS packages and clone the GitHub repo
RUN apt-get update && \
    apt-get install -y git && \
    git clone https://github.com/Mattia-V01/Unplanned_Events_and_Delays_in_Public_Transport.git .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the Shiny app
CMD ["shiny", "run", "--reload", "App/app.py"]
