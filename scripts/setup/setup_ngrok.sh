#!/bin/bash
# Setup ngrok tunnel for Google Photos OAuth
# This creates a public HTTPS URL that Google will accept
# Usage: ./scripts/setup_ngrok.sh

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NGROK_TOKEN_FILE="$PROJECT_DIR/config/ngrok_token.txt"

echo "🌐 Setting up ngrok tunnel for Google Photos OAuth..."

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok not found. Installing..."
    
    # Install ngrok
    if [[ "$OSTYPE" == "linux"* ]]; then
        # Linux installation
        curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
        echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
        sudo apt update && sudo apt install ngrok
    else
        echo "❌ Please install ngrok manually: https://ngrok.com/download"
        exit 1
    fi
fi

# Authenticate with ngrok token
if [[ -f "$NGROK_TOKEN_FILE" ]]; then
    NGROK_TOKEN=$(cat "$NGROK_TOKEN_FILE" | tr -d '\n\r ')
    echo "🔑 Authenticating with ngrok..."
    ngrok config add-authtoken "$NGROK_TOKEN"
else
    echo "❌ ngrok token not found at: $NGROK_TOKEN_FILE"
    echo "💡 Add your ngrok token to that file"
    exit 1
fi

echo "✅ ngrok setup complete!"
echo ""
echo "🚀 To start the tunnel:"
echo "   ngrok http https://localhost:443"
echo ""
echo "📋 Then update Google Cloud Console with:"
echo "   https://[your-ngrok-subdomain].ngrok.app/auth/callback"
echo "   https://[your-ngrok-subdomain].ngrok.app/auth/google/callback"
echo ""
echo "💡 The ngrok URL will be different each time unless you have a paid plan"