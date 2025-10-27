"""
ML-Enhanced Snort Runner Package
Provides ML-based analysis and rule generation for Snort IDS/IPS
"""

from config import config, MLRunnerConfig
from alert_parser import SnortAlert, AlertParser, AlertFeatureExtractor
from ml_analyzer import MLAnalysisResult, MLAnalysisManager
from rule_generator import SnortRule, SnortRuleGenerator, SnortRuleManager

__version__ = "1.0.0"
__author__ = "ML-Enhanced Snort Runner"

__all__ = [
    'config',
    'MLRunnerConfig',
    'SnortAlert',
    'AlertParser', 
    'AlertFeatureExtractor',
    'MLAnalysisResult',
    'MLAnalysisManager',
    'SnortRule',
    'SnortRuleGenerator',
    'SnortRuleManager'
]