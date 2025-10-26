#!/bin/bash
set -e

echo "🚀 Starting ML-Enhanced Snort3 Container"
echo "========================================"

# Wait for network interface to be ready
sleep 2

# Check if Snort3 is properly installed
if ! command -v snort &> /dev/null; then
    echo "❌ Snort3 not found in PATH"
    exit 1
fi

# Test Snort3 configuration
echo "🔍 Testing Snort3 configuration..."
if ! snort -T -c /usr/local/etc/snort/snort.lua >/dev/null 2>&1; then
    echo "⚠️  Snort3 configuration test failed, using defaults"
    if [ ! -f /usr/local/etc/snort/snort.lua ]; then
        cp /usr/local/etc/snort/snort_defaults.lua /usr/local/etc/snort/snort.lua
    fi
fi

# Create log directory if it doesn't exist
mkdir -p /var/log/snort

# Check for API key configuration
if [ -n "$ML_API_KEY" ]; then
    echo "✅ ML_API_KEY environment variable detected"
elif [ -f "/etc/snort/ml_runner/api_config.json" ]; then
    echo "✅ API configuration file detected"
else
    echo "⚠️  No OpenAI API key configured. ML analysis will use local models only."
    echo "💡 Set ML_API_KEY environment variable or mount config file to enable OpenAI integration"
fi

# Start services based on command
case "$1" in
    "snort-only")
        echo "🔍 Starting Snort3 only..."
        exec snort -c /usr/local/etc/snort/snort.lua -i eth0 -A alert_fast -l /var/log/snort
        ;;
    "ml-only")
        echo "🧠 Starting ML Runner only..."
        exec python3 /app/main.py --model local --verbose
        ;;
    "services"|"")
        echo "🚀 Starting both Snort3 and ML Runner..."
        # Start services using service manager
        exec /app/service_manager.sh start
        ;;
    "bash")
        echo "🐚 Starting interactive bash shell..."
        exec /bin/bash
        ;;
    *)
        echo "🔧 Running custom command: $@"
        exec "$@"
        ;;
esac