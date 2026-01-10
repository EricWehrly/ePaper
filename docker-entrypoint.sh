#!/bin/bash

mkdir -p logs

# Check if SSL certificates exist (Let's Encrypt or self-signed)
LE_CERT="/etc/letsencrypt/live/epaper.whirlwind.family/fullchain.pem"
LE_KEY="/etc/letsencrypt/live/epaper.whirlwind.family/privkey.pem"
SELF_CERT="/app/config/raspberrypi.local.crt"
SELF_KEY="/app/config/raspberrypi.local.key"

if [[ -f "$LE_CERT" && -f "$LE_KEY" ]]; then
    echo "🔒 Let's Encrypt SSL certificates found - starting HTTPS server"
    echo "🚀 Starting web servers:"
    echo "   📡 HTTP:       http://0.0.0.0:80"
    echo "   🔐 HTTPS:      https://0.0.0.0:443"
    echo "   🛠️  HTTP Dev:   http://0.0.0.0:5000"
    SSL_MODE="--ssl"
elif [[ -f "$SELF_CERT" && -f "$SELF_KEY" ]]; then
    echo "🔒 Self-signed SSL certificates found - starting HTTPS server (browser warnings expected)"
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
