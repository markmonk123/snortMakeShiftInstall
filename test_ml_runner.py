#!/usr/bin/env python3
"""
Test script for ML-Enhanced Snort Runner
"""

import os
import sys
import asyncio
import tempfile
import json
from datetime import datetime
from pathlib import Path

# Add ml_runner to path
script_dir = Path(__file__).parent
ml_runner_dir = script_dir / "ml_runner"
sys.path.insert(0, str(ml_runner_dir))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from config import config, MLRunnerConfig
        print("✓ Config module imported")
    except ImportError as e:
        print(f"✗ Config import failed: {e}")
        return False
    
    try:
        from alert_parser import AlertParser, AlertFeatureExtractor, SnortAlert
        print("✓ Alert parser module imported")
    except ImportError as e:
        print(f"✗ Alert parser import failed: {e}")
        return False
    
    try:
        from ml_analyzer import MLAnalysisManager, MLAnalysisResult
        print("✓ ML analyzer module imported")
    except ImportError as e:
        print(f"✗ ML analyzer import failed: {e}")
        return False
    
    try:
        from rule_generator import SnortRuleGenerator, SnortRuleManager
        print("✓ Rule generator module imported")
    except ImportError as e:
        print(f"✗ Rule generator import failed: {e}")
        return False
    
    return True

def test_alert_parsing():
    """Test alert parsing functionality"""
    print("\nTesting alert parsing...")
    
    try:
        from alert_parser import AlertParser, AlertFeatureExtractor
        
        parser = AlertParser()
        feature_extractor = AlertFeatureExtractor()
        
        # Test alert line (Snort fast alert format)
        test_alert = "10/26-11:09:09.414867  [**] [1:1000001:1] SSH Connection Attempt [**] [Classification: Attempted Administrator Privilege Gain] [Priority: 1] {TCP} 192.168.1.100:22 -> 192.168.1.200:54321"
        
        alert = parser.parse_alert(test_alert)
        if alert:
            print(f"✓ Parsed alert: {alert.message}")
            print(f"  Source: {alert.src_ip}:{alert.src_port}")
            print(f"  Destination: {alert.dst_ip}:{alert.dst_port}")
            print(f"  Priority: {alert.priority}")
            
            # Test feature extraction
            features = feature_extractor.extract_features(alert)
            print(f"✓ Extracted {len(features)} features")
            print(f"  Severity score: {features.get('severity_score', 0):.2f}")
            print(f"  Suspicious port: {features.get('suspicious_port', False)}")
            
            return True
        else:
            print("✗ Failed to parse test alert")
            return False
            
    except Exception as e:
        print(f"✗ Alert parsing test failed: {e}")
        return False

def test_rule_generation():
    """Test rule generation functionality"""
    print("\nTesting rule generation...")
    
    try:
        from alert_parser import AlertParser
        from ml_analyzer import MLAnalysisResult
        from rule_generator import SnortRuleGenerator
        
        parser = AlertParser()
        rule_generator = SnortRuleGenerator()
        
        # Create test alert
        test_alert = "10/26-11:09:09.414867  [**] [1:1000001:1] SSH Connection Attempt [**] [Classification: Attempted Administrator Privilege Gain] [Priority: 1] {TCP} 192.168.1.100:22 -> 192.168.1.200:54321"
        alert = parser.parse_alert(test_alert)
        
        if not alert:
            print("✗ Failed to parse test alert for rule generation")
            return False
        
        # Create test ML analysis result
        analysis = MLAnalysisResult(
            confidence=0.99,
            threat_classification="brute-force",
            threat_description="Potential SSH brute force attack detected",
            recommended_action="block",
            additional_context={"attack_type": "ssh_brute_force"},
            rule_suggestion='alert tcp any any -> any 22 (msg:"SSH Brute Force Attempt"; flow:to_server,established; content:"SSH"; sid:2000001; rev:1;)'
        )
        
        # Generate rule
        rule = rule_generator.generate_rule_from_ml_analysis(alert, analysis)
        if rule:
            print(f"✓ Generated rule SID {rule.sid}")
            print(f"  Message: {rule.message}")
            print(f"  Rule: {rule.raw_rule[:100]}...")
            print(f"  Confidence: {rule.confidence_score:.2f}")
            return True
        else:
            print("✗ Failed to generate rule")
            return False
            
    except Exception as e:
        print(f"✗ Rule generation test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading and validation"""
    print("\nTesting configuration...")
    
    try:
        from config import config, MLRunnerConfig
        
        # Test default config
        print(f"✓ Default ML model: {config.ml_model_type}")
        print(f"  Confidence threshold: {config.confidence_threshold}")
        print(f"  Snort alert file: {config.snort_alert_file}")
        
        # Test custom config creation
        custom_config = MLRunnerConfig()
        custom_config.confidence_threshold = 0.95
        custom_config.ml_model_type = "local"
        
        print("✓ Custom configuration created")
        
        # Test config file save/load
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_file = f.name
        
        try:
            custom_config.to_file(config_file)
            loaded_config = MLRunnerConfig.from_file(config_file)
            
            if loaded_config.confidence_threshold == 0.95:
                print("✓ Configuration save/load works")
                return True
            else:
                print("✗ Configuration save/load failed")
                return False
        finally:
            os.unlink(config_file)
            
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_mock_ml_analysis():
    """Test mock ML analysis (without API calls)"""
    print("\nTesting mock ML analysis...")
    
    try:
        from alert_parser import AlertParser, AlertFeatureExtractor
        from ml_analyzer import LocalMLAnalyzer
        
        parser = AlertParser()
        feature_extractor = AlertFeatureExtractor()
        analyzer = LocalMLAnalyzer("/tmp/mock_model")
        
        # Create test alert
        test_alert = "10/26-11:09:09.414867  [**] [1:1000001:1] SSH Connection Attempt [**] [Classification: Attempted Administrator Privilege Gain] [Priority: 1] {TCP} 192.168.1.100:22 -> 192.168.1.200:54321"
        alert = parser.parse_alert(test_alert)
        
        if not alert:
            print("✗ Failed to parse test alert")
            return False
        
        # Extract features
        features = feature_extractor.extract_features(alert)
        
        # Run analysis
        async def run_analysis():
            result = await analyzer.analyze_alert(alert, features)
            return result
        
        result = asyncio.run(run_analysis())
        
        if result:
            print(f"✓ Mock analysis completed")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Classification: {result.threat_classification}")
            print(f"  Action: {result.recommended_action}")
            return True
        else:
            print("✗ Mock analysis failed")
            return False
            
    except Exception as e:
        print(f"✗ Mock ML analysis test failed: {e}")
        return False

def create_test_alert_file():
    """Create a test alert file with sample data"""
    print("\nCreating test alert file...")
    
    try:
        # Create test alerts directory
        test_dir = "/tmp/snort_test"
        os.makedirs(test_dir, exist_ok=True)
        
        alert_file = f"{test_dir}/alert_fast.txt"
        
        sample_alerts = [
            "10/26-11:09:09.414867  [**] [1:1000001:1] SSH Connection Attempt [**] [Classification: Attempted Administrator Privilege Gain] [Priority: 1] {TCP} 192.168.1.100:22 -> 192.168.1.200:54321",
            "10/26-11:09:10.525478  [**] [1:1000002:1] HTTP Traffic [**] [Classification: Web Application Attack] [Priority: 2] {TCP} 10.0.0.100:80 -> 192.168.1.50:43210",
            "10/26-11:09:11.636589  [**] [1:1000003:1] Suspicious Port Scan [**] [Classification: Attempted Information Leak] [Priority: 2] {TCP} 203.0.113.10:12345 -> 192.168.1.1:443"
        ]
        
        with open(alert_file, 'w') as f:
            for alert in sample_alerts:
                f.write(alert + '\n')
        
        print(f"✓ Created test alert file: {alert_file}")
        print(f"  Contains {len(sample_alerts)} sample alerts")
        
        return alert_file
        
    except Exception as e:
        print(f"✗ Failed to create test alert file: {e}")
        return None

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("ML-Enhanced Snort Runner - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Alert Parsing", test_alert_parsing),
        ("Rule Generation", test_rule_generation),
        ("Configuration", test_configuration),
        ("Mock ML Analysis", test_mock_ml_analysis)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")
    
    # Create test alert file
    test_alert_file = create_test_alert_file()
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if test_alert_file:
        print(f"\nTest alert file created: {test_alert_file}")
        print("You can use this for testing the full system:")
        print(f"  sudo ML_API_KEY='your-key' python3 main.py --test-config")
    
    print("\nTo run the full system:")
    print("  1. Ensure Snort3 is running and generating alerts")
    print("  2. Set ML_API_KEY environment variable (for OpenAI)")
    print("  3. Run: sudo python3 main.py")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)