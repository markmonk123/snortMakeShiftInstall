#!/bin/bash
# Systemd Service Setup for ML-Enhanced Snort Runner
# Use this script on a real Linux system with systemd

echo "🔧 Systemd Service Setup for ML-Enhanced Snort Runner"
echo "====================================================="

# Check if running on systemd
if ! command -v systemctl &> /dev/null; then
    echo "❌ systemctl not found. This script requires systemd."
    echo "💡 For container environments, use ./service_manager.sh instead"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo $0"
    exit 1
fi

echo "✅ systemctl found. Proceeding with systemd setup..."
echo ""

# Function to check service file
check_service_file() {
    local service_name=$1
    local service_file="/etc/systemd/system/${service_name}.service"
    
    if [ -f "$service_file" ]; then
        echo "✅ $service_name service file exists"
        return 0
    else
        echo "❌ $service_name service file missing: $service_file"
        return 1
    fi
}

# Check service files
echo "🔍 Checking service files..."
check_service_file "snort3"
check_service_file "snort-ml-runner"

echo ""
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

echo ""
echo "🔧 Setting up services..."

# Enable services for auto-start
echo "📝 Enabling services for auto-start..."
systemctl enable snort3.service
systemctl enable snort-ml-runner.service

echo ""
echo "🚀 Starting services..."

# Start Snort3 first
echo "Starting Snort3..."
systemctl start snort3.service

# Wait a moment for Snort3 to initialize
sleep 3

# Check if Snort3 started successfully
if systemctl is-active --quiet snort3.service; then
    echo "✅ Snort3 started successfully"
    
    # Start ML Runner
    echo "Starting ML Runner..."
    systemctl start snort-ml-runner.service
    
    sleep 2
    
    if systemctl is-active --quiet snort-ml-runner.service; then
        echo "✅ ML Runner started successfully"
    else
        echo "❌ ML Runner failed to start"
        echo "📜 ML Runner status:"
        systemctl status snort-ml-runner.service --no-pager -l
    fi
else
    echo "❌ Snort3 failed to start"
    echo "📜 Snort3 status:"
    systemctl status snort3.service --no-pager -l
fi

echo ""
echo "📊 Service Status:"
echo "=================="
systemctl --no-pager status snort3.service snort-ml-runner.service

echo ""
echo "🔧 Useful systemctl commands:"
echo "============================="
echo "View status:          sudo systemctl status snort3 snort-ml-runner"
echo "Stop services:        sudo systemctl stop snort3 snort-ml-runner"
echo "Start services:       sudo systemctl start snort3 snort-ml-runner"
echo "Restart services:     sudo systemctl restart snort3 snort-ml-runner"
echo "View logs:            sudo journalctl -u snort3 -u snort-ml-runner -f"
echo "Disable auto-start:   sudo systemctl disable snort3 snort-ml-runner"
echo ""

echo "🏁 Setup complete!"
echo ""
echo "📝 Service Files Created:"
echo "  • /etc/systemd/system/snort3.service"
echo "  • /etc/systemd/system/snort-ml-runner.service"
echo ""
echo "🔄 Services are now persistent and will auto-start on boot"