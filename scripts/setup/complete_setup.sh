#!/bin/bash
# Complete Raspberry Pi setup for ePaper Display Project
# This script runs all necessary configuration steps
# Usage: ./scripts/complete_setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🍓 ePaper Display Project - Complete Pi Setup"
echo "=============================================="
echo ""

# Function to run a script and handle errors
run_script() {
    local script_name=$1
    local script_path="$SCRIPT_DIR/$script_name"
    
    echo "🚀 Running: $script_name"
    if [[ -x "$script_path" ]]; then
        if bash "$script_path"; then
            echo "✅ $script_name completed successfully"
        else
            echo "❌ $script_name failed"
            return 1
        fi
    else
        echo "❌ Script not found or not executable: $script_path"
        return 1
    fi
    echo ""
}

# Check if we're on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null && ! grep -q "BCM" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "    Some hardware-specific features may not work"
    echo ""
fi

# 1. Docker User Setup (must be first, requires logout/login)
echo "📋 Step 1: Docker User Permissions"
if groups | grep -q '\bdocker\b'; then
    echo "✅ User already in docker group, skipping..."
else
# Docker user setup removed - this is baseline Docker functionality
    echo "⚠️  STOP: You must log out and log back in now!"
    echo "    Run this script again after logging back in."
    exit 0
fi
echo ""

# 2. SSL Certificate Generation
echo "📋 Step 2: SSL Certificate Generation"
run_script "setup/generate_ssl_cert.sh"

# 3. Avahi Configuration
echo "📋 Step 3: Avahi/mDNS Configuration"
run_script "environment/setup_avahi.sh"

# 4. Docker Environment
echo "📋 Step 4: Docker Environment Setup"
cd "$PROJECT_DIR"

echo "🐳 Building Docker containers..."
if docker compose up --build -d; then
    echo "✅ Docker containers started successfully"
else
    echo "❌ Docker containers failed to start"
    exit 1
fi

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# 5. Health Check
echo ""
echo "📋 Step 5: Health Check"
echo "🔍 Checking services..."

# Check Docker containers
if docker compose ps | grep -q "Up"; then
    echo "✅ Docker containers running"
else
    echo "❌ Docker containers not running"
fi

# Check HTTP access
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200"; then
    echo "✅ HTTP server responding on localhost:5000"
else
    echo "⚠️  HTTP server not responding on localhost:5000"
fi

# Check HTTPS access (allow self-signed certificate)
if curl -k -s -o /dev/null -w "%{http_code}" https://localhost:5000 2>/dev/null | grep -q "200"; then
    echo "✅ HTTPS server responding on localhost:5000"
else
    echo "⚠️  HTTPS server not responding on localhost:5000"
fi

# Check hostname resolution
HOSTNAME=$(hostname)
if getent hosts "$HOSTNAME.local" >/dev/null 2>&1; then
    echo "✅ Hostname resolution working: $HOSTNAME.local"
    
    # Get the resolved IP
    RESOLVED_IP=$(getent hosts "$HOSTNAME.local" | awk '{print $1}')
    echo "📍 Resolved to: $RESOLVED_IP"
    
    # Check if we can reach the web server via hostname
    if curl -s -o /dev/null -w "%{http_code}" "http://$HOSTNAME.local:5000" 2>/dev/null | grep -q "200"; then
        echo "✅ Web server accessible via $HOSTNAME.local:5000"
    else
        echo "⚠️  Web server not accessible via $HOSTNAME.local:5000"
    fi
else
    echo "⚠️  Hostname resolution not working for $HOSTNAME.local"
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📱 Access your ePaper display interface at:"
echo "   🌐 Local:     http://localhost:5000"
echo "   🔒 HTTPS:     https://localhost:5000 (self-signed cert)"
echo "   🏠 Network:   http://$HOSTNAME.local:5000"
echo "   🔐 HTTPS:     https://$HOSTNAME.local:5000 (self-signed cert)"
echo ""
echo "📋 Next steps:"
echo "   1. Configure Google Photos credentials in config/"
echo "   2. Update Google Cloud Console with HTTPS redirect URIs"
echo "   3. Test photo selection and display workflow"
echo ""
echo "🔧 Useful commands:"
echo "   docker compose logs -f     # View logs"
echo "   docker compose down        # Stop containers"
echo "   docker compose up -d       # Restart containers"