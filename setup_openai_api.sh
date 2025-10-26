#!/bin/bash
# OpenAI API Key Setup Script for ML-Enhanced Snort Runner
# This script helps you securely configure your OpenAI API key

echo "🔑 OpenAI API Key Setup for ML-Enhanced Snort Runner"
echo "=================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo $0"
    exit 1
fi

echo ""
echo "📋 You need to obtain an OpenAI API key manually:"
echo "   1. Visit: https://platform.openai.com/api-keys"
echo "   2. Sign up/login to your OpenAI account"
echo "   3. Click 'Create new secret key'"
echo "   4. Copy the generated key (starts with 'sk-...')"
echo ""

# Option 1: Environment variable (temporary)
echo "🔧 Setup Options:"
echo ""
echo "Option 1: Set as environment variable (session-only)"
echo "Usage: export ML_API_KEY='your-api-key-here'"
echo "Then: python3 main.py --model openai"
echo ""

# Option 2: Create secure config file
echo "Option 2: Create secure configuration file"
read -p "Would you like to create a secure config file? (y/n): " create_config

if [[ $create_config =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔐 Creating secure configuration file..."
    
    # Create secure directory
    mkdir -p /etc/snort/ml_runner
    chmod 700 /etc/snort/ml_runner
    
    # Prompt for API key
    echo ""
    echo "⚠️  IMPORTANT: Your API key will be stored securely"
    echo "   File: /etc/snort/ml_runner/api_config.json"
    echo "   Permissions: 600 (root only)"
    echo ""
    read -p "Enter your OpenAI API key: " -s api_key
    echo ""
    
    if [ -z "$api_key" ]; then
        echo "❌ No API key provided. Exiting."
        exit 1
    fi
    
    # Create config file
    cat > /etc/snort/ml_runner/api_config.json << EOF
{
    "ml_api_key": "$api_key",
    "ml_model_type": "openai",
    "ml_model_name": "gpt-4",
    "confidence_threshold": 0.98,
    "created_date": "$(date -I)",
    "created_by": "$SUDO_USER"
}
EOF
    
    # Set secure permissions
    chmod 600 /etc/snort/ml_runner/api_config.json
    chown root:root /etc/snort/ml_runner/api_config.json
    
    echo "✅ Configuration file created successfully!"
    echo "   Location: /etc/snort/ml_runner/api_config.json"
    echo "   Permissions: 600 (root read/write only)"
    echo ""
    echo "🚀 You can now run:"
    echo "   sudo python3 main.py --config /etc/snort/ml_runner/api_config.json"
    echo ""
fi

# Option 3: System environment file
echo "Option 3: Create system environment file"
read -p "Would you like to create a system environment file? (y/n): " create_env

if [[ $create_env =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔐 Creating system environment file..."
    
    # Prompt for API key if not already provided
    if [ -z "$api_key" ]; then
        echo ""
        read -p "Enter your OpenAI API key: " -s api_key
        echo ""
    fi
    
    if [ -z "$api_key" ]; then
        echo "❌ No API key provided. Skipping environment file."
    else
        # Create environment file
        cat > /etc/snort/ml_runner/ml_runner.env << EOF
# ML-Enhanced Snort Runner Environment Variables
# Source this file before running: source /etc/snort/ml_runner/ml_runner.env

export ML_API_KEY="$api_key"
export ML_MODEL_TYPE="openai"
export ML_MODEL_NAME="gpt-4"
export CONFIDENCE_THRESHOLD="0.98"

# Usage:
# source /etc/snort/ml_runner/ml_runner.env
# sudo -E python3 main.py --model openai
EOF
        
        # Set secure permissions
        chmod 600 /etc/snort/ml_runner/ml_runner.env
        chown root:root /etc/snort/ml_runner/ml_runner.env
        
        echo "✅ Environment file created successfully!"
        echo "   Location: /etc/snort/ml_runner/ml_runner.env"
        echo "   Permissions: 600 (root read/write only)"
        echo ""
        echo "🚀 You can now run:"
        echo "   source /etc/snort/ml_runner/ml_runner.env"
        echo "   sudo -E python3 main.py --model openai"
        echo ""
    fi
fi

echo "🔒 Security Notes:"
echo "   • API keys are stored with root-only permissions"
echo "   • Never commit API keys to version control"
echo "   • Rotate your API keys regularly"
echo "   • Monitor your OpenAI usage and billing"
echo ""

echo "✅ Setup complete! Choose your preferred method above."
echo ""
echo "🧪 Test your configuration:"
echo "   sudo python3 main.py --test-config --model openai"
echo ""