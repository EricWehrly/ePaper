#!/bin/bash

mkdir -p logs

# Check if SSL certificates exist
if [[ -f "/app/config/raspberrypi.local.crt" && -f "/app/config/raspberrypi.local.key" ]]; then
    echo "🔒 SSL certificates found - starting HTTPS server"
    echo "🚀 Starting web servers:"
    echo "   📡 HTTP:       http://0.0.0.0:80"
    echo "   🔐 HTTPS:      https://0.0.0.0:443"
    echo "   🛠️  HTTP Dev:   http://0.0.0.0:5000"
    SSL_MODE="--ssl"
else
    echo "📡 No SSL certificates found - HTTP only"
    echo "🚀 Starting web server on http://0.0.0.0:5000"
    SSL_MODE=""
fi

# Set environment variables
export PYTHONPATH=/app

# Start our custom web server with optional SSL support
exec python cli.py --mode=web --host=0.0.0.0 --port=5000 $SSL_MODE
