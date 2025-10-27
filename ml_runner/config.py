#!/usr/bin/env python3
"""
Configuration management for ML-Enhanced Snort Runner
"""

import os
from dataclasses import dataclass
from typing import Optional
import json


@dataclass
class MLRunnerConfig:
    """Configuration for the ML-Enhanced Snort Runner"""
    
    # Snort Configuration
    snort_alert_file: str = "/var/log/snort/alert_fast.txt"
    snort_config_dir: str = "/etc/snort"
    snort_rules_file: str = "/etc/snort/rules/ml_generated.rules"
    snort_binary: str = "/usr/local/bin/snort"
    
    # ML Model Configuration
    ml_model_type: str = "openai"  # "openai", "local", "huggingface"
    ml_model_name: str = "gpt-4"
    ml_api_key: Optional[str] = None
    ml_api_endpoint: Optional[str] = None
    confidence_threshold: float = 0.98
    
    # Processing Configuration
    max_alerts_per_batch: int = 10
    processing_interval: float = 5.0  # seconds
    max_concurrent_analyses: int = 3
    
    # Rule Generation Configuration
    rule_sid_start: int = 2000000  # Start SID for ML-generated rules
    rule_prefix: str = "ML_GENERATED"
    rule_classtype: str = "trojan-activity"
    rule_priority: int = 1
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "/var/log/snort/ml_runner.log"
    log_max_bytes: int = 10485760  # 10MB
    log_backup_count: int = 5
    
    # Storage Configuration
    alert_history_file: str = "/var/log/snort/alert_history.json"
    rule_history_file: str = "/var/log/snort/rule_history.json"
    max_history_days: int = 30
    
    @classmethod
    def from_env(cls) -> 'MLRunnerConfig':
        """Create configuration from environment variables"""
        config = cls()
        
        # Try to load from secure config file first
        secure_config_paths = [
            '/etc/snort/ml_runner/api_config.json',
            '/etc/snort/ml_runner/config.json',
            './ml_runner_config.json'
        ]
        
        for config_path in secure_config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        secure_config = json.load(f)
                    
                    # Load from secure config
                    config.ml_api_key = secure_config.get('ml_api_key', config.ml_api_key)
                    config.ml_model_type = secure_config.get('ml_model_type', config.ml_model_type)
                    config.ml_model_name = secure_config.get('ml_model_name', config.ml_model_name)
                    config.ml_api_endpoint = secure_config.get('ml_api_endpoint', config.ml_api_endpoint)
                    
                    if 'confidence_threshold' in secure_config:
                        config.confidence_threshold = float(secure_config['confidence_threshold'])
                    if 'max_alerts_per_batch' in secure_config:
                        config.max_alerts_per_batch = int(secure_config['max_alerts_per_batch'])
                    if 'processing_interval' in secure_config:
                        config.processing_interval = float(secure_config['processing_interval'])
                    
                    print(f"✅ Loaded secure configuration from: {config_path}")
                    break
                    
                except Exception as e:
                    print(f"⚠️  Failed to load config from {config_path}: {e}")
                    continue
        
        # Override with environment variables if present (takes precedence)
        config.ml_api_key = os.getenv('ML_API_KEY', config.ml_api_key)
        config.ml_model_type = os.getenv('ML_MODEL_TYPE', config.ml_model_type)
        config.ml_model_name = os.getenv('ML_MODEL_NAME', config.ml_model_name)
        config.ml_api_endpoint = os.getenv('ML_API_ENDPOINT', config.ml_api_endpoint)
        
        # Parse numeric values
        if os.getenv('CONFIDENCE_THRESHOLD'):
            config.confidence_threshold = float(os.getenv('CONFIDENCE_THRESHOLD'))
        if os.getenv('MAX_ALERTS_PER_BATCH'):
            config.max_alerts_per_batch = int(os.getenv('MAX_ALERTS_PER_BATCH'))
        if os.getenv('PROCESSING_INTERVAL'):
            config.processing_interval = float(os.getenv('PROCESSING_INTERVAL'))
        
        return config
    
    @classmethod
    def from_file(cls, config_path: str) -> 'MLRunnerConfig':
        """Load configuration from JSON file"""
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        config = cls()
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return config
    
    def to_file(self, config_path: str) -> None:
        """Save configuration to JSON file"""
        config_data = {
            key: value for key, value in self.__dict__.items() 
            if not key.startswith('_')
        }
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def validate(self) -> None:
        """Validate configuration parameters"""
        if not os.path.exists(os.path.dirname(self.snort_alert_file)):
            raise ValueError(f"Snort log directory does not exist: {os.path.dirname(self.snort_alert_file)}")
        
        if not os.path.exists(self.snort_config_dir):
            raise ValueError(f"Snort config directory does not exist: {self.snort_config_dir}")
        
        if not os.path.exists(self.snort_binary):
            raise ValueError(f"Snort binary not found: {self.snort_binary}")
        
        if self.confidence_threshold < 0 or self.confidence_threshold > 1:
            raise ValueError(f"Confidence threshold must be between 0 and 1: {self.confidence_threshold}")
        
        if self.ml_model_type == "openai" and not self.ml_api_key:
            raise ValueError("OpenAI API key required for OpenAI model type")
        
        # Create required directories
        os.makedirs(os.path.dirname(self.snort_rules_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.alert_history_file), exist_ok=True)


# Global configuration instance
config = MLRunnerConfig.from_env()