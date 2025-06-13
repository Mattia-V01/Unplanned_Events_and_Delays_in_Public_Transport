# Use official Python base image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy all local files to container
COPY . /app

# Upgrade pip and install required packages
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose the port used by FastAPI
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
