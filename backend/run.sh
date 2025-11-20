#!/bin/bash
set -euo pipefail

# Start the MQTT listener in the background and then run the FastAPI app in foreground.
# This keeps the container alive under PID 1 with uvicorn as the foreground process.

echo "Starting mqtt_test.py in background..."
python -u /app/app/mqtt_test.py &
MQTT_PID=$!

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
