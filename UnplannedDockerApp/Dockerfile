# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy everything from the parent folder into the container
COPY ../ /app

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI app located in App/app.py
CMD ["uvicorn", "App.app:app", "--host", "0.0.0.0", "--port", "8000"]
