#!/bin/bash
# Configure Avahi daemon for proper .local hostname resolution
# This fixes Docker bridge network interference with mDNS
# Usage: sudo ./scripts/setup_avahi.sh

set -e

if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)" 
   exit 1
fi

echo "🔧 Configuring Avahi daemon for proper .local resolution..."

# Backup original config
if [[ ! -f /etc/avahi/avahi-daemon.conf.backup ]]; then
    cp /etc/avahi/avahi-daemon.conf /etc/avahi/avahi-daemon.conf.backup
    echo "✅ Backed up original Avahi config"
fi

# Check if wlan0 interface exists
if ! ip link show wlan0 &>/dev/null; then
    echo "⚠️  Warning: wlan0 interface not found, using eth0 instead"
    INTERFACE="eth0"
else
    INTERFACE="wlan0"
fi

# Update Avahi config to only use WiFi interface
# This prevents Docker bridge networks from interfering
sed -i "s/#allow-interfaces=eth0/allow-interfaces=$INTERFACE/" /etc/avahi/avahi-daemon.conf

# Restart Avahi daemon
systemctl restart avahi-daemon

# Wait a moment for service to start
sleep 2

# Verify it's working
if systemctl is-active --quiet avahi-daemon; then
    echo "✅ Avahi daemon restarted successfully"
    echo "📡 Interface: $INTERFACE"
    echo "🌐 Hostname: $(hostname).local"
    
    # Show the IP being advertised
    IP=$(ip addr show $INTERFACE | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
    echo "📍 IP Address: $IP"
    
    echo ""
    echo "🧪 Testing resolution..."
    sleep 3
    getent hosts $(hostname).local || echo "⚠️  DNS resolution may need a moment to propagate"
else
    echo "❌ Avahi daemon failed to start"
    exit 1
fi

echo ""
echo "✅ Avahi configuration complete!"
echo "📋 You should now be able to access:"
echo "   http://$(hostname).local:5000"
echo "   https://$(hostname).local:5000 (after SSL setup)"