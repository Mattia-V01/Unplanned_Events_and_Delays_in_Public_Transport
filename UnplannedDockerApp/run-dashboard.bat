@echo off
start "" http://localhost:8000
docker run --rm -it -p 8000:8000 ghcr.io/mattia-v01/unplanned-delays-dashboard:latest