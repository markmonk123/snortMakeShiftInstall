#!/bin/bash
# Auto-start script for ML-Enhanced Snort Services
# This script can be added to container startup or cron @reboot

echo "🚀 Auto-starting ML-Enhanced Snort Services..."

# Wait for network to be ready
sleep 5

# Change to the correct directory
cd /workspaces/snortMakeShiftInstall

# Start the services
sudo ./service_manager.sh start

echo "✅ Auto-start complete"