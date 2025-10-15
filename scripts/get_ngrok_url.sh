#!/bin/bash
# Get the current ngrok public URL for Google OAuth configuration
# Usage: ./scripts/get_ngrok_url.sh

echo "🌐 Getting ngrok tunnel URL..."
echo ""

# Wait for ngrok to be ready
echo "⏳ Waiting for ngrok to start..."
sleep 5

# Get the public URL from ngrok API
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null)

if [[ "$NGROK_URL" == "null" ]] || [[ -z "$NGROK_URL" ]]; then
    echo "❌ Could not get ngrok URL. Is ngrok running?"
    echo ""
    echo "🔧 To start ngrok:"
    echo "   docker compose up ngrok -d"
    echo ""
    echo "🌐 Then check ngrok web interface:"
    echo "   http://localhost:4040"
    exit 1
fi

echo "✅ ngrok tunnel active:"
echo "   Public URL: $NGROK_URL"
echo ""
echo "📋 Add these redirect URIs to Google Cloud Console:"
echo "   $NGROK_URL/auth/callback"
echo "   $NGROK_URL/auth/google/callback"
echo ""
echo "🌐 ngrok web interface: http://localhost:4040"
echo ""
echo "📱 Access your ePaper app via:"
echo "   $NGROK_URL"