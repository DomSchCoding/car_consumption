#!/bin/bash
cd /home/hermes/code/car_consumption
source .venv/bin/activate
python -m app.main --port 8080 --bind 0.0.0.0
