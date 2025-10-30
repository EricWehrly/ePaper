#!/bin/bash
# ePaper Display Project - Status Summary
# Shows current configuration and access information

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOSTNAME=$(hostname)

echo "🍓 ePaper Display Project - Status Summary"
echo "==========================================="
echo ""

# Project Info
echo "📂 Project Directory: $PROJECT_DIR"
echo "🏠 Hostname: $HOSTNAME"
echo "📍 Network IP: $(ip addr show wlan0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1 || echo 'N/A')"
echo ""

# SSL Certificates
echo "🔒 SSL Certificates:"
if [[ -f "$PROJECT_DIR/config/raspberrypi.local.crt" && -f "$PROJECT_DIR/config/raspberrypi.local.key" ]]; then
    echo "   ✅ SSL certificates present"
    echo "   📄 Certificate: config/raspberrypi.local.crt"
    echo "   🔑 Private key: config/raspberrypi.local.key"
    
    # Check certificate validity
    CERT_INFO=$(openssl x509 -in "$PROJECT_DIR/config/raspberrypi.local.crt" -noout -dates 2>/dev/null)
    if [[ $? -eq 0 ]]; then
        echo "   📅 $(echo "$CERT_INFO" | head -1)"
        echo "   📅 $(echo "$CERT_INFO" | tail -1)"
    fi
else
    echo "   ❌ SSL certificates missing"
    echo "   💡 Run: ./scripts/generate_ssl_cert.sh"
fi
echo ""

# Docker Status
echo "🐳 Docker Services:"
if command -v docker >/dev/null 2>&1; then
    if docker compose ps 2>/dev/null | grep -q "Up"; then
        echo "   ✅ Docker containers running"
        docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    else
        echo "   ❌ Docker containers not running"
        echo "   💡 Run: docker compose up -d"
    fi
else
    echo "   ❌ Docker not installed or not accessible"
    echo "   💡 Run: ./scripts/setup_docker_user.sh"
fi
echo ""

# Network Services
echo "🌐 Network Services:"
echo "   📡 HTTP:  http://$HOSTNAME.local (port 80)"
echo "   🔐 HTTPS: https://$HOSTNAME.local (port 443, self-signed)"
echo "   🛠️  Dev:   http://$HOSTNAME.local:5000"
echo ""

# Test connectivity
echo "🧪 Connectivity Tests:"

# Test HTTP
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:5000" 2>/dev/null | grep -q "200"; then
    echo "   ✅ HTTP localhost:5000"
else
    echo "   ❌ HTTP localhost:5000"
fi

# Test HTTPS
if curl -k -s -o /dev/null -w "%{http_code}" "https://localhost:443" 2>/dev/null | grep -q "200"; then
    echo "   ✅ HTTPS localhost:443"
else
    echo "   ❌ HTTPS localhost:443"
fi

# Test hostname resolution
if getent hosts "$HOSTNAME.local" >/dev/null 2>&1; then
    echo "   ✅ Hostname resolution: $HOSTNAME.local"
    
    # Test hostname HTTP
    if curl -s -o /dev/null -w "%{http_code}" "http://$HOSTNAME.local" 2>/dev/null | grep -q "200"; then
        echo "   ✅ HTTP $HOSTNAME.local"
    else
        echo "   ❌ HTTP $HOSTNAME.local"
    fi
    
    # Test hostname HTTPS  
    if curl -k -s -o /dev/null -w "%{http_code}" "https://$HOSTNAME.local" 2>/dev/null | grep -q "200"; then
        echo "   ✅ HTTPS $HOSTNAME.local"
    else
        echo "   ❌ HTTPS $HOSTNAME.local"
    fi
    
    # Test development HTTP port
    if curl -s -o /dev/null -w "%{http_code}" "http://$HOSTNAME.local:5000" 2>/dev/null | grep -q "200"; then
        echo "   ✅ HTTP Dev $HOSTNAME.local:5000"
    else
        echo "   ❌ HTTP Dev $HOSTNAME.local:5000"
    fi
else
    echo "   ❌ Hostname resolution: $HOSTNAME.local"
    echo "   💡 Run: sudo ./scripts/setup_avahi.sh"
fi
echo ""

# Google Photos Integration
echo "🌅 Google Photos Integration:"
if [[ -f "$PROJECT_DIR/config/google_photos_credentials.json" ]]; then
    echo "   ✅ Google Photos credentials configured"
else
    echo "   ❌ Google Photos credentials missing"
    echo "   💡 Add credentials to: config/google_photos_credentials.json"
fi

if [[ -f "$PROJECT_DIR/config/settings.json" ]]; then
    echo "   ✅ Application settings configured"
else
    echo "   ❌ Application settings missing"
    echo "   💡 Configure: config/settings.json"
fi
echo ""

# Quick Actions
echo "🚀 Quick Actions:"
echo "   🔧 Complete setup:    ./scripts/complete_setup.sh"
echo "   🔒 Generate SSL:      ./scripts/generate_ssl_cert.sh"  
echo "   📡 Setup networking:  sudo ./scripts/setup_avahi.sh"
echo "   🐳 Setup Docker:      ./scripts/setup_docker_user.sh"
echo "   📋 View logs:         docker compose logs -f"
echo "   🛑 Stop services:     docker compose down"
echo ""

echo "📱 Access your ePaper interface:"
echo "   🌐 Web UI:      http://$HOSTNAME.local"
echo "   🔐 HTTPS UI:    https://$HOSTNAME.local"
echo "   🛠️  Dev UI:      http://$HOSTNAME.local:5000"
echo "   📊 API Status:  http://$HOSTNAME.local/api/status"