#!/usr/bin/env python3
"""
ML-Enhanced Snort Runner - Main Entry Point
Provides real-time ML analysis of Snort alerts and automated rule generation
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path

# Add the ml_runner module to the path
script_dir = Path(__file__).parent
ml_runner_dir = script_dir / "ml_runner"
sys.path.insert(0, str(ml_runner_dir))

from ml_enhanced_runner import main as runner_main, setup_logging
from config import config, MLRunnerConfig


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║              ML-Enhanced Snort Runner v1.0.0                ║
║                                                              ║
║  Real-time ML analysis of Snort IDS/IPS alerts with         ║
║  automated rule generation for improved threat detection     ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_prerequisites():
    """Check system prerequisites"""
    issues = []
    
    # Check if running as root
    if os.geteuid() != 0:
        issues.append("Must run as root to access Snort files and reload service")
    
    # Check if Snort is installed
    if not os.path.exists(config.snort_binary):
        issues.append(f"Snort binary not found: {config.snort_binary}")
    
    # Check if Snort config directory exists
    if not os.path.exists(config.snort_config_dir):
        issues.append(f"Snort config directory not found: {config.snort_config_dir}")
    
    # Check if alert file directory exists
    alert_dir = os.path.dirname(config.snort_alert_file)
    if not os.path.exists(alert_dir):
        try:
            os.makedirs(alert_dir, exist_ok=True)
            print(f"Created alert directory: {alert_dir}")
        except PermissionError:
            issues.append(f"Cannot create alert directory: {alert_dir}")
    
    return issues


def setup_environment():
    """Setup the runtime environment"""
    # Create necessary directories
    directories = [
        os.path.dirname(config.log_file),
        os.path.dirname(config.alert_history_file),
        os.path.dirname(config.rule_history_file),
        os.path.dirname(config.snort_rules_file)
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Set up logging early
    setup_logging()


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='ML-Enhanced Snort Runner - Intelligent IDS/IPS with automated rule generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration
  sudo python3 main.py
  
  # Run with OpenAI analysis (requires API key)
  sudo ML_API_KEY="your-key" python3 main.py --model openai
  
  # Run with custom configuration
  sudo python3 main.py --config custom_config.json
  
  # Test configuration without running
  sudo python3 main.py --test-config
  
Environment Variables:
  ML_API_KEY          - API key for ML model (required for OpenAI)
  ML_MODEL_TYPE       - Model type: openai, local (default: openai)
  ML_MODEL_NAME       - Model name (default: gpt-4)
  CONFIDENCE_THRESHOLD - Confidence threshold for rule generation (default: 0.98)
        """
    )
    
    parser.add_argument('--model', choices=['openai', 'local'], 
                       help='ML model type to use (overrides env var)')
    parser.add_argument('--model-name', help='Specific model name to use')
    parser.add_argument('--confidence', type=float, 
                       help='Confidence threshold for rule generation (0.0-1.0)')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--test-config', action='store_true',
                       help='Test configuration and exit')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Reduce logging output')
    parser.add_argument('--log-file', help='Override log file path')
    
    return parser.parse_args()


def apply_arguments(args):
    """Apply command line arguments to configuration"""
    global config
    
    # Load custom configuration if specified
    if args.config:
        if os.path.exists(args.config):
            config = MLRunnerConfig.from_file(args.config)
            print(f"Loaded configuration from: {args.config}")
        else:
            print(f"Configuration file not found: {args.config}")
            sys.exit(1)
    
    # Apply argument overrides
    if args.model:
        config.ml_model_type = args.model
    if args.model_name:
        config.ml_model_name = args.model_name
    if args.confidence:
        config.confidence_threshold = args.confidence
    if args.log_file:
        config.log_file = args.log_file
    
    # Adjust log level
    if args.verbose:
        config.log_level = "DEBUG"
    elif args.quiet:
        config.log_level = "WARNING"


def test_configuration():
    """Test the configuration and exit"""
    print("Testing configuration...")
    
    try:
        config.validate()
        print("✓ Configuration validation passed")
    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        return False
    
    # Test ML model availability
    try:
        if config.ml_model_type == "openai":
            if not config.ml_api_key:
                print("✗ OpenAI API key not configured")
                print("  Set ML_API_KEY environment variable or use --model local")
                return False
            else:
                print("✓ OpenAI API key configured")
        
        print(f"✓ ML model type: {config.ml_model_type}")
        print(f"✓ Model name: {config.ml_model_name}")
        print(f"✓ Confidence threshold: {config.confidence_threshold}")
        
    except Exception as e:
        print(f"✗ ML configuration error: {e}")
        return False
    
    # Test file paths
    paths_to_check = [
        ("Snort binary", config.snort_binary),
        ("Snort config directory", config.snort_config_dir),
        ("Alert file directory", os.path.dirname(config.snort_alert_file))
    ]
    
    for name, path in paths_to_check:
        if os.path.exists(path):
            print(f"✓ {name}: {path}")
        else:
            print(f"✗ {name} not found: {path}")
            return False
    
    print("\n✓ All configuration tests passed!")
    return True


def main():
    """Main entry point"""
    # Parse arguments
    args = parse_arguments()
    
    # Print banner
    print_banner()
    
    # Apply configuration
    apply_arguments(args)
    
    # Test configuration if requested
    if args.test_config:
        success = test_configuration()
        sys.exit(0 if success else 1)
    
    # Check prerequisites
    issues = check_prerequisites()
    if issues:
        print("❌ Prerequisites check failed:")
        for issue in issues:
            print(f"   • {issue}")
        print("\nPlease resolve these issues before running.")
        sys.exit(1)
    
    print("✓ Prerequisites check passed")
    
    # Setup environment
    setup_environment()
    
    # Display configuration summary
    print(f"""
Configuration Summary:
  ML Model: {config.ml_model_type} ({config.ml_model_name})
  Confidence Threshold: {config.confidence_threshold}
  Alert File: {config.snort_alert_file}
  Rules File: {config.snort_rules_file}
  Log File: {config.log_file}
  Log Level: {config.log_level}
""")
    
    # Run the ML-enhanced runner
    try:
        print("🚀 Starting ML-Enhanced Snort Runner...")
        asyncio.run(runner_main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()