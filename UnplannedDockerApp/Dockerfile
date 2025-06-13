# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all project files
COPY ../ /app

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Set working directory to App so that app.py and ui.py are importable
WORKDIR /app/App

# Expose port used by FastAPI
EXPOSE 8000

# Run the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
