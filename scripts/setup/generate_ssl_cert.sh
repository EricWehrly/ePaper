#!/bin/bash
# Generate self-signed SSL certificate for raspberrypi.local
# Usage: ./scripts/generate_ssl_cert.sh

set -e

echo "🔒 Generating self-signed SSL certificate for raspberrypi.local..."

# Ensure config directory exists
mkdir -p config

# Generate the certificate
openssl req -x509 -newkey rsa:4096 \
    -keyout config/raspberrypi.local.key \
    -out config/raspberrypi.local.crt \
    -days 365 -nodes \
    -subj "/C=US/ST=Local/L=Local/O=ePaper/OU=Display/CN=raspberrypi.local"

# Set appropriate permissions
chmod 600 config/raspberrypi.local.key
chmod 644 config/raspberrypi.local.crt

echo "✅ SSL certificate generated:"
echo "   Private key: config/raspberrypi.local.key"
echo "   Certificate: config/raspberrypi.local.crt"
echo ""
echo "📋 Next steps:"
echo "   1. Update docker-compose.yml to use HTTPS (✅ Done)"
echo "   2. Add certificate to your browser/system trust store"
echo "   3. Access via https://raspberrypi.local (standard HTTPS port)"
echo ""
echo "🔧 To add certificate to your system:"
echo ""
echo "📱 Windows:"
echo "   1. Copy config/raspberrypi.local.crt to your Windows machine"
echo "   2. Double-click the .crt file"
echo "   3. Click 'Install Certificate...'"
echo "   4. Select 'Local Machine' → Next"
echo "   5. Select 'Place all certificates in the following store'"
echo "   6. Click 'Browse' → Select 'Trusted Root Certification Authorities'"
echo "   7. Click Next → Finish"
echo ""
echo "🍎 macOS:"
echo "   1. Copy config/raspberrypi.local.crt to your Mac"
echo "   2. Double-click the .crt file (opens Keychain Access)"
echo "   3. Select 'System' keychain"
echo "   4. Double-click the certificate in Keychain Access"
echo "   5. Expand 'Trust' section"
echo "   6. Set 'When using this certificate' to 'Always Trust'"
echo "   7. Close and enter your password"
echo ""
echo "🐧 Linux:"
echo "   # Ubuntu/Debian:"
echo "   sudo cp config/raspberrypi.local.crt /usr/local/share/ca-certificates/"
echo "   sudo update-ca-certificates"
echo ""
echo "   # CentOS/RHEL/Fedora:"
echo "   sudo cp config/raspberrypi.local.crt /etc/pki/ca-trust/source/anchors/"
echo "   sudo update-ca-trust"
echo ""
echo "🌐 Browser-only (Alternative):"
echo "   Chrome: Settings → Privacy/Security → Manage certificates → Authorities → Import"
echo "   Firefox: Settings → Privacy → View Certificates → Authorities → Import"
echo "   Safari: Uses system keychain (follow macOS steps)"
echo ""
echo "📋 Quick copy commands:"
echo "   # Copy to current directory for easy transfer:"
echo "   cp config/raspberrypi.local.crt ./raspberrypi-cert.crt"
echo ""
echo "   # Or serve temporarily for download:"
echo "   python3 -m http.server 8000"
echo "   # Then visit http://raspberrypi.local:8000/config/raspberrypi.local.crt"