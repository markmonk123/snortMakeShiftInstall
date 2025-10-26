#!/usr/bin/env python3
"""
Snort rule generation and management based on ML analysis
"""

import re
import os
import logging
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import subprocess

from config import config
from alert_parser import SnortAlert
from ml_analyzer import MLAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class SnortRule:
    """Represents a Snort rule"""
    sid: int
    message: str
    protocol: str
    src_addr: str
    src_port: str
    direction: str
    dst_addr: str
    dst_port: str
    options: Dict[str, str]
    raw_rule: str
    created_timestamp: datetime
    confidence_score: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'sid': self.sid,
            'message': self.message,
            'protocol': self.protocol,
            'src_addr': self.src_addr,
            'src_port': self.src_port,
            'direction': self.direction,
            'dst_addr': self.dst_addr,
            'dst_port': self.dst_port,
            'options': self.options,
            'raw_rule': self.raw_rule,
            'created_timestamp': self.created_timestamp.isoformat(),
            'confidence_score': self.confidence_score
        }


class SnortRuleGenerator:
    """Generates Snort rules based on ML analysis results"""
    
    def __init__(self):
        self.next_sid = config.rule_sid_start
        self.generated_rules: List[SnortRule] = []
        self.rule_patterns: Set[str] = set()
        
        # Load existing SIDs to avoid conflicts
        self._load_existing_sids()
    
    def _load_existing_sids(self):
        """Load existing SIDs from rule files to avoid conflicts"""
        existing_sids = set()
        
        # Check main rules directory
        rules_dir = os.path.join(config.snort_config_dir, 'rules')
        if os.path.exists(rules_dir):
            for filename in os.listdir(rules_dir):
                if filename.endswith('.rules'):
                    filepath = os.path.join(rules_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#'):
                                    sid_match = re.search(r'sid:\s*(\d+)', line)
                                    if sid_match:
                                        existing_sids.add(int(sid_match.group(1)))
                    except Exception as e:
                        logger.warning(f"Error reading rules file {filepath}: {e}")
        
        # Set next SID to avoid conflicts
        if existing_sids:
            max_existing = max(existing_sids)
            if max_existing >= self.next_sid:
                self.next_sid = max_existing + 1
        
        logger.info(f"Starting SID allocation at: {self.next_sid}")
    
    def generate_rule_from_ml_analysis(self, alert: SnortAlert, analysis: MLAnalysisResult) -> Optional[SnortRule]:
        """Generate a Snort rule based on ML analysis results"""
        try:
            # Only generate rules for high-confidence analyses
            if analysis.confidence < config.confidence_threshold:
                logger.debug(f"Skipping rule generation for low confidence: {analysis.confidence:.2f}")
                return None
            
            # Check if we have a suggested rule from ML model
            if analysis.rule_suggestion:
                return self._parse_suggested_rule(analysis.rule_suggestion, alert, analysis)
            
            # Generate rule based on alert and analysis
            return self._generate_rule_from_alert(alert, analysis)
            
        except Exception as e:
            logger.error(f"Error generating rule for alert {alert.sid}: {e}")
            return None
    
    def _parse_suggested_rule(self, suggested_rule: str, alert: SnortAlert, analysis: MLAnalysisResult) -> Optional[SnortRule]:
        """Parse and validate ML-suggested rule"""
        try:
            # Extract SID if present, otherwise assign new one
            sid_match = re.search(r'sid:\s*(\d+)', suggested_rule)
            if sid_match:
                # Replace with our SID to avoid conflicts
                suggested_rule = re.sub(r'sid:\s*\d+', f'sid:{self.next_sid}', suggested_rule)
            
            # Ensure rule has required elements
            rule_pattern = re.compile(
                r'(alert|drop|reject)\s+(\w+)\s+([^\s]+)\s+([^\s]+)\s+([<>-]+)\s+([^\s]+)\s+([^\s]+)\s+\(([^)]+)\)'
            )
            
            match = rule_pattern.match(suggested_rule.strip())
            if not match:
                logger.warning(f"Invalid rule format from ML model: {suggested_rule}")
                return self._generate_rule_from_alert(alert, analysis)
            
            action, protocol, src_addr, src_port, direction, dst_addr, dst_port, options_str = match.groups()
            
            # Parse options
            options = self._parse_rule_options(options_str)
            
            # Ensure SID is set
            if 'sid' not in options:
                options['sid'] = str(self.next_sid)
            else:
                options['sid'] = str(self.next_sid)  # Override to avoid conflicts
            
            # Add our metadata
            options['classtype'] = analysis.threat_classification
            options['reference'] = f"ml_analysis,confidence_{analysis.confidence:.2f}"
            options['metadata'] = f"{config.rule_prefix},generated_{datetime.now().strftime('%Y%m%d')}"
            
            # Rebuild rule string
            options_list = [f'{k}:{v}' if v else k for k, v in options.items()]
            rebuilt_rule = f"{action} {protocol} {src_addr} {src_port} {direction} {dst_addr} {dst_port} ({'; '.join(options_list)};)"
            
            rule = SnortRule(
                sid=self.next_sid,
                message=options.get('msg', analysis.threat_description).strip('"'),
                protocol=protocol.upper(),
                src_addr=src_addr,
                src_port=src_port,
                direction=direction,
                dst_addr=dst_addr,
                dst_port=dst_port,
                options=options,
                raw_rule=rebuilt_rule,
                created_timestamp=datetime.now(),
                confidence_score=analysis.confidence
            )
            
            self.next_sid += 1
            return rule
            
        except Exception as e:
            logger.error(f"Error parsing suggested rule: {e}")
            return self._generate_rule_from_alert(alert, analysis)
    
    def _generate_rule_from_alert(self, alert: SnortAlert, analysis: MLAnalysisResult) -> SnortRule:
        """Generate a basic rule from alert characteristics"""
        # Determine action based on analysis
        action = "alert"
        if analysis.recommended_action == "block":
            action = "drop"
        elif analysis.recommended_action == "reject":
            action = "reject"
        
        # Generate rule components
        protocol = alert.protocol.lower()
        src_addr = alert.src_ip if alert.src_ip != "any" else "any"
        src_port = str(alert.src_port) if alert.src_port else "any"
        dst_addr = alert.dst_ip if alert.dst_ip != "any" else "any"
        dst_port = str(alert.dst_port) if alert.dst_port else "any"
        direction = "->"
        
        # Create rule message
        message = f"{config.rule_prefix}: {analysis.threat_description[:80]}"
        
        # Build options
        options = {
            'msg': f'"{message}"',
            'sid': str(self.next_sid),
            'rev': '1',
            'classtype': analysis.threat_classification,
            'priority': str(config.rule_priority),
            'reference': f"ml_analysis,confidence_{analysis.confidence:.2f}",
            'metadata': f"{config.rule_prefix},generated_{datetime.now().strftime('%Y%m%d')}"
        }
        
        # Add content matching if possible
        if hasattr(alert, 'payload_data'):
            # This would be available if we had packet payload data
            pass
        
        # Build rule string
        options_list = [f'{k}:{v}' if v else k for k, v in options.items()]
        raw_rule = f"{action} {protocol} {src_addr} {src_port} {direction} {dst_addr} {dst_port} ({'; '.join(options_list)};)"
        
        rule = SnortRule(
            sid=self.next_sid,
            message=message,
            protocol=protocol.upper(),
            src_addr=src_addr,
            src_port=src_port,
            direction=direction,
            dst_addr=dst_addr,
            dst_port=dst_port,
            options=options,
            raw_rule=raw_rule,
            created_timestamp=datetime.now(),
            confidence_score=analysis.confidence
        )
        
        self.next_sid += 1
        return rule
    
    def _parse_rule_options(self, options_str: str) -> Dict[str, str]:
        """Parse rule options string into dictionary"""
        options = {}
        
        # Split by semicolon, but handle quoted strings
        parts = []
        current_part = ""
        in_quotes = False
        
        for char in options_str:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ';' and not in_quotes:
                if current_part.strip():
                    parts.append(current_part.strip())
                current_part = ""
                continue
            current_part += char
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        # Parse each part
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                options[key.strip()] = value.strip()
            else:
                options[part.strip()] = ""
        
        return options
    
    def validate_rule(self, rule: SnortRule) -> bool:
        """Validate a Snort rule syntax"""
        try:
            # Basic syntax validation
            if not re.match(r'^(alert|drop|reject|pass)\s+\w+\s+\S+\s+\S+\s+[<>-]+\s+\S+\s+\S+\s+\([^)]+\);?$', rule.raw_rule):
                logger.warning(f"Invalid rule syntax: {rule.raw_rule}")
                return False
            
            # Check for required options
            required_options = ['msg', 'sid']
            for opt in required_options:
                if opt not in rule.options:
                    logger.warning(f"Missing required option '{opt}' in rule {rule.sid}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating rule {rule.sid}: {e}")
            return False


class SnortRuleManager:
    """Manages Snort rules - loading, saving, and applying"""
    
    def __init__(self):
        self.rules_file = config.snort_rules_file
        self.backup_count = 5
        
        # Ensure rules directory exists
        os.makedirs(os.path.dirname(self.rules_file), exist_ok=True)
    
    def add_rules(self, rules: List[SnortRule]) -> bool:
        """Add new rules to the rules file"""
        try:
            valid_rules = [rule for rule in rules if self._validate_and_log_rule(rule)]
            if not valid_rules:
                logger.info("No valid rules to add")
                return True
            
            # Backup existing rules file
            self._backup_rules_file()
            
            # Write new rules
            with open(self.rules_file, 'a') as f:
                f.write(f"\n# ML-Generated Rules - {datetime.now().isoformat()}\n")
                for rule in valid_rules:
                    f.write(f"{rule.raw_rule}\n")
                f.write("\n")
            
            logger.info(f"Added {len(valid_rules)} new rules to {self.rules_file}")
            
            # Test configuration
            if self._test_snort_config():
                # Reload Snort to apply new rules
                return self._reload_snort()
            else:
                # Restore backup if config test fails
                self._restore_backup()
                return False
            
        except Exception as e:
            logger.error(f"Error adding rules: {e}")
            return False
    
    def _validate_and_log_rule(self, rule: SnortRule) -> bool:
        """Validate rule and log details"""
        generator = SnortRuleGenerator()
        is_valid = generator.validate_rule(rule)
        
        if is_valid:
            logger.info(f"Adding rule SID {rule.sid}: {rule.message} (confidence: {rule.confidence_score:.2f})")
        else:
            logger.warning(f"Rejecting invalid rule SID {rule.sid}: {rule.raw_rule}")
        
        return is_valid
    
    def _backup_rules_file(self):
        """Create backup of current rules file"""
        if os.path.exists(self.rules_file):
            backup_file = f"{self.rules_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.rules_file, backup_file)
            
            # Clean up old backups
            self._cleanup_old_backups()
    
    def _cleanup_old_backups(self):
        """Remove old backup files"""
        backup_dir = os.path.dirname(self.rules_file)
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.startswith(f"{os.path.basename(self.rules_file)}.backup."):
                backups.append(os.path.join(backup_dir, filename))
        
        backups.sort(key=os.path.getmtime, reverse=True)
        
        # Keep only the most recent backups
        for backup in backups[self.backup_count:]:
            try:
                os.remove(backup)
                logger.debug(f"Removed old backup: {backup}")
            except Exception as e:
                logger.warning(f"Failed to remove backup {backup}: {e}")
    
    def _test_snort_config(self) -> bool:
        """Test Snort configuration with new rules"""
        try:
            cmd = [
                config.snort_binary,
                '-c', os.path.join(config.snort_config_dir, 'snort.lua'),
                '-T'  # Test configuration
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("Snort configuration test passed")
                return True
            else:
                logger.error(f"Snort configuration test failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Snort configuration test timed out")
            return False
        except Exception as e:
            logger.error(f"Error testing Snort configuration: {e}")
            return False
    
    def _reload_snort(self) -> bool:
        """Reload Snort service to apply new rules"""
        try:
            # Try systemctl first
            result = subprocess.run(['systemctl', 'reload', 'snort3'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("Snort service reloaded successfully")
                return True
            else:
                # Try alternative reload methods
                logger.warning("systemctl reload failed, trying alternative methods")
                
                # Send HUP signal to reload rules
                result = subprocess.run(['pkill', '-HUP', 'snort'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    logger.info("Snort reloaded via HUP signal")
                    return True
                else:
                    logger.error("Failed to reload Snort service")
                    return False
                    
        except subprocess.TimeoutExpired:
            logger.error("Snort reload timed out")
            return False
        except Exception as e:
            logger.error(f"Error reloading Snort: {e}")
            return False
    
    def _restore_backup(self):
        """Restore the most recent backup"""
        backup_dir = os.path.dirname(self.rules_file)
        backup_pattern = f"{os.path.basename(self.rules_file)}.backup."
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.startswith(backup_pattern):
                backups.append(os.path.join(backup_dir, filename))
        
        if backups:
            latest_backup = max(backups, key=os.path.getmtime)
            shutil.copy2(latest_backup, self.rules_file)
            logger.info(f"Restored rules from backup: {latest_backup}")
        else:
            logger.warning("No backup found to restore")
    
    def get_rule_stats(self) -> Dict[str, int]:
        """Get statistics about managed rules"""
        stats = {'total_rules': 0, 'ml_generated_rules': 0}
        
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'r') as f:
                    content = f.read()
                    stats['total_rules'] = len([line for line in content.split('\n') 
                                              if line.strip() and not line.strip().startswith('#')])
                    stats['ml_generated_rules'] = content.count(config.rule_prefix)
            except Exception as e:
                logger.error(f"Error getting rule stats: {e}")
        
        return stats