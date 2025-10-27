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

usage() {
    cat <<'EOF'
Usage: setup_openai_api.sh [options]

Options:
  --auto                 Run in non-interactive mode; requires ML_API_KEY env var
  --auto-config-only     Auto-create only the secure JSON configuration file
  --auto-env-only        Auto-create only the environment export file
  --force                Overwrite existing files when running in auto mode
  -h, --help             Show this help message
EOF
}

AUTO_MODE=false
AUTO_CREATE_CONFIG=true
AUTO_CREATE_ENV=true
OVERWRITE=false
API_KEY=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --auto)
            AUTO_MODE=true
            AUTO_CREATE_CONFIG=true
            AUTO_CREATE_ENV=true
            shift
            ;;
        --auto-config-only)
            AUTO_MODE=true
            AUTO_CREATE_CONFIG=true
            AUTO_CREATE_ENV=false
            shift
            ;;
        --auto-env-only)
            AUTO_MODE=true
            AUTO_CREATE_CONFIG=false
            AUTO_CREATE_ENV=true
            shift
            ;;
        --force)
            OVERWRITE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

SECURE_DIR="/etc/snort/ml_runner"
CONFIG_FILE="${SECURE_DIR}/api_config.json"
ENV_FILE="${SECURE_DIR}/ml_runner.env"
CREATED_BY="${SUDO_USER:-$(whoami)}"

ensure_secure_dir() {
    mkdir -p "$SECURE_DIR"
    chmod 700 "$SECURE_DIR"
}

create_config_file() {
    if [ -f "$CONFIG_FILE" ] && [ "$OVERWRITE" = false ]; then
        echo "ℹ️  Configuration file already exists at $CONFIG_FILE (use --force to overwrite)."
        return 0
    fi

    ensure_secure_dir

    cat > "$CONFIG_FILE" << EOF
{
    "ml_api_key": "$API_KEY",
    "ml_model_type": "openai",
    "ml_model_name": "gpt-4",
    "confidence_threshold": 0.98,
    "created_date": "$(date -I)",
    "created_by": "$CREATED_BY"
}
EOF

    chmod 600 "$CONFIG_FILE"
    chown root:root "$CONFIG_FILE"
    echo "✅ Configuration file ready at $CONFIG_FILE"
}

create_env_file() {
    if [ -f "$ENV_FILE" ] && [ "$OVERWRITE" = false ]; then
        echo "ℹ️  Environment file already exists at $ENV_FILE (use --force to overwrite)."
        return 0
    fi

    ensure_secure_dir

    cat > "$ENV_FILE" << EOF
# ML-Enhanced Snort Runner Environment Variables
# Source this file before running: source $ENV_FILE

export ML_API_KEY="$API_KEY"
export ML_MODEL_TYPE="openai"
export ML_MODEL_NAME="gpt-4"
export CONFIDENCE_THRESHOLD="0.98"

# Usage:
# source $ENV_FILE
# sudo -E python3 main.py --model openai
EOF

    chmod 600 "$ENV_FILE"
    chown root:root "$ENV_FILE"
    echo "✅ Environment file ready at $ENV_FILE"
}

if [ "$AUTO_MODE" = true ]; then
    API_KEY="${ML_API_KEY:-${OPENAI_API_KEY:-}}"

    if [ -z "$API_KEY" ]; then
        echo "ℹ️  ML_API_KEY not provided; skipping automatic OpenAI setup."
        exit 0
    fi

    echo "⚙️  Running OpenAI setup in auto mode."

    if [ "$AUTO_CREATE_CONFIG" = true ]; then
        create_config_file
    fi

    if [ "$AUTO_CREATE_ENV" = true ]; then
        create_env_file
    fi

    echo "✅ Auto setup complete."
    exit 0
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
    
    # Prompt for API key
    echo ""
    echo "⚠️  IMPORTANT: Your API key will be stored securely"
    echo "   File: $CONFIG_FILE"
    echo "   Permissions: 600 (root only)"
    echo ""
    read -p "Enter your OpenAI API key: " -s api_key
    echo ""
    
    if [ -z "$api_key" ]; then
        echo "❌ No API key provided. Exiting."
        exit 1
    fi

    API_KEY="$api_key"
    create_config_file
    echo ""
    echo "🚀 You can now run:"
    echo "   sudo python3 main.py --config $CONFIG_FILE"
    echo ""
fi

# Option 3: System environment file
echo "Option 3: Create system environment file"
read -p "Would you like to create a system environment file? (y/n): " create_env

if [[ $create_env =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔐 Creating system environment file..."
    
    # Prompt for API key if not already provided
    if [ -z "$API_KEY" ]; then
        echo ""
        read -p "Enter your OpenAI API key: " -s api_key
        echo ""
        API_KEY="$api_key"
    fi
    
    if [ -z "$API_KEY" ]; then
        echo "❌ No API key provided. Skipping environment file."
    else
        create_env_file
        echo ""
        echo "🚀 You can now run:"
        echo "   source $ENV_FILE"
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