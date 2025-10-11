#!/bin/bash

# TODO: Is this actually used?
mkdir -p logs

# Start the application
echo "🚀 Starting web server on http://localhost:5000"

# Set environment variables
export PYTHONPATH=/app

# Start our custom web server (not flask run)
exec python -m src.main --mode=web --host=0.0.0.0 --port=5000
