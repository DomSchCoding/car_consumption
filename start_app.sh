#!/bin/bash
cd /home/hermes/code/car_consumption
source .venv/bin/activate
exec python -m app.main --port 8080 --bind 0.0.0.0
