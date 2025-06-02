@echo off
start "" http://localhost:8000
docker run --rm -it -p 8000:8000 -e PYTHONPATH=/app/Unplanned_Events_and_Delays_in_Public_Transport/App transport-delays uvicorn app:fastapi_app --host 0.0.0.0 --port 8000