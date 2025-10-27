#!/bin/bash
# Demo: OpenAI API Key Integration for ML-Enhanced Snort Runner

echo "🚀 OpenAI API Key Integration Demo"
echo "================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo $0"
    exit 1
fi

echo ""
echo "📋 Available Methods to Set OpenAI API Key:"
echo ""

echo "Method 1: Environment Variable (Temporary)"
echo "   export ML_API_KEY='sk-your-key-here'"
echo "   sudo -E python3 main.py --model openai"
echo ""

echo "Method 2: Secure Configuration File"
echo "   ./setup_openai_api.sh  # Run the setup script"
echo "   sudo python3 main.py --config /etc/snort/ml_runner/api_config.json"
echo ""

echo "Method 3: Auto-Detection (Recommended)"
echo "   1. Store API key in secure config file"
echo "   2. System automatically detects and loads it"
echo "   sudo python3 main.py --model openai"
echo ""

# Check current configuration status
echo "🔍 Current Configuration Status:"
echo ""

# Check for environment variable
if [ -n "$ML_API_KEY" ]; then
    echo "✅ ML_API_KEY environment variable is set"
else
    echo "❌ ML_API_KEY environment variable not set"
fi

# Check for secure config files
config_files=(
    "/etc/snort/ml_runner/api_config.json"
    "/etc/snort/ml_runner/config.json" 
    "./ml_runner_config.json"
)

found_config=false
for config_file in "${config_files[@]}"; do
    if [ -f "$config_file" ]; then
        echo "✅ Found secure config file: $config_file"
        found_config=true
        
        # Check permissions for security
        perms=$(stat -c "%a" "$config_file")
        if [ "$perms" = "600" ]; then
            echo "   🔒 Permissions: $perms (secure)"
        else
            echo "   ⚠️  Permissions: $perms (consider setting to 600)"
        fi
    fi
done

if [ "$found_config" = false ]; then
    echo "❌ No secure config files found"
fi

echo ""
echo "💡 Recommendations:"

if [ -z "$ML_API_KEY" ] && [ "$found_config" = false ]; then
    echo "   1. Get your OpenAI API key from: https://platform.openai.com/api-keys"
    echo "   2. Run: ./setup_openai_api.sh"
    echo "   3. Test with: sudo python3 main.py --test-config --model openai"
    
elif [ -n "$ML_API_KEY" ]; then
    echo "   ✅ You're ready to go! Test with:"
    echo "      sudo -E python3 main.py --test-config --model openai"
    
elif [ "$found_config" = true ]; then
    echo "   ✅ You're ready to go! Test with:"
    echo "      sudo python3 main.py --test-config --model openai"
fi

echo ""
echo "🧪 Test Commands:"
echo "   # Test configuration only"
echo "   sudo python3 main.py --test-config --model openai"
echo ""
echo "   # Run with OpenAI (short test)"
echo "   timeout 30s sudo python3 main.py --model openai --verbose"
echo ""

echo "🔐 Security Best Practices:"
echo "   • Never commit API keys to version control"
echo "   • Use secure file permissions (600)"
echo "   • Rotate API keys regularly"
echo "   • Monitor OpenAI usage and billing"
echo "   • Consider using local models for sensitive environments"
echo ""