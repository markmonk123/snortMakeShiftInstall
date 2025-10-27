#!/usr/bin/env python3
"""
Alert parsing and feature extraction for Snort alerts
"""

import re
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import ipaddress
import logging

logger = logging.getLogger(__name__)


@dataclass
class SnortAlert:
    """Represents a parsed Snort alert"""
    timestamp: datetime
    priority: int
    classification: str
    message: str
    protocol: str
    src_ip: str
    src_port: Optional[int]
    dst_ip: str
    dst_port: Optional[int]
    sid: Optional[int]
    rev: Optional[int]
    raw_alert: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SnortAlert':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class AlertParser:
    """Parser for Snort alert_fast format"""
    
    # Regex pattern for Snort alert_fast format
    # Example: 10/26-11:09:09.414867  [**] [1:1000001:1] SSH Connection Attempt [**] [Classification: Attempted Administrator Privilege Gain] [Priority: 1] {TCP} 192.168.1.100:22 -> 192.168.1.200:54321
    ALERT_PATTERN = re.compile(
        r'(\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)\s+' +  # timestamp
        r'\[\*\*\]\s+' +                               # delimiter
        r'\[(\d+):(\d+):(\d+)\]\s+' +                  # gid:sid:rev
        r'([^\[]+?)\s+' +                              # message
        r'\[\*\*\]\s+' +                               # delimiter
        r'\[Classification:\s+([^\]]+)\]\s+' +         # classification
        r'\[Priority:\s+(\d+)\]\s+' +                  # priority
        r'\{([^}]+)\}\s+' +                            # protocol
        r'([^:]+):(\d+|\*)\s+->\s+' +                  # src_ip:src_port
        r'([^:]+):(\d+|\*)'                            # dst_ip:dst_port
    )
    
    def __init__(self):
        self.parsed_count = 0
        self.error_count = 0
    
    def parse_alert(self, alert_line: str) -> Optional[SnortAlert]:
        """Parse a single alert line"""
        alert_line = alert_line.strip()
        if not alert_line:
            return None
        
        try:
            match = self.ALERT_PATTERN.match(alert_line)
            if not match:
                logger.warning(f"Failed to parse alert line: {alert_line}")
                self.error_count += 1
                return None
            
            # Extract matched groups
            timestamp_str, _gid, sid, rev, message, classification, priority, protocol, src_ip, src_port, dst_ip, dst_port = match.groups()
            
            # Parse timestamp (MM/DD-HH:MM:SS.microseconds)
            timestamp = self._parse_timestamp(timestamp_str)
            
            # Parse ports (handle '*' as None)
            src_port_int = int(src_port) if src_port != '*' else None
            dst_port_int = int(dst_port) if dst_port != '*' else None
            
            # Create alert object
            alert = SnortAlert(
                timestamp=timestamp,
                priority=int(priority),
                classification=classification.strip(),
                message=message.strip(),
                protocol=protocol.upper(),
                src_ip=src_ip.strip(),
                src_port=src_port_int,
                dst_ip=dst_ip.strip(),
                dst_port=dst_port_int,
                sid=int(sid),
                rev=int(rev),
                raw_alert=alert_line
            )
            
            self.parsed_count += 1
            logger.debug(f"Parsed alert: {alert.message} from {alert.src_ip} to {alert.dst_ip}")
            return alert
            
        except Exception as e:
            logger.error(f"Error parsing alert: {e}, line: {alert_line}")
            self.error_count += 1
            return None
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse Snort timestamp format MM/DD-HH:MM:SS.microseconds"""
        try:
            # Add current year since Snort doesn't include it
            current_year = datetime.now().year
            # Convert MM/DD-HH:MM:SS.microseconds to YYYY-MM-DD HH:MM:SS.microseconds
            date_part, time_part = timestamp_str.split('-')
            month, day = date_part.split('/')
            
            timestamp_full = f"{current_year}-{month.zfill(2)}-{day.zfill(2)} {time_part}"
            return datetime.strptime(timestamp_full, "%Y-%m-%d %H:%M:%S.%f")
        except Exception as e:
            logger.warning(f"Failed to parse timestamp {timestamp_str}: {e}")
            return datetime.now()
    
    def parse_alerts_batch(self, alert_lines: List[str]) -> List[SnortAlert]:
        """Parse multiple alert lines"""
        alerts = []
        for line in alert_lines:
            alert = self.parse_alert(line)
            if alert:
                alerts.append(alert)
        return alerts
    
    def get_stats(self) -> Dict[str, int]:
        """Get parsing statistics"""
        return {
            'parsed_count': self.parsed_count,
            'error_count': self.error_count,
            'total_processed': self.parsed_count + self.error_count
        }


class AlertFeatureExtractor:
    """Extract features from alerts for ML analysis"""
    
    def __init__(self):
        self.feature_cache = {}
    
    def extract_features(self, alert: SnortAlert) -> Dict[str, any]:
        """Extract features from a Snort alert for ML analysis"""
        features = {
            # Basic alert information
            'priority': alert.priority,
            'protocol': alert.protocol,
            'sid': alert.sid,
            'classification': alert.classification,
            'message': alert.message,
            
            # Temporal features
            'hour_of_day': alert.timestamp.hour,
            'day_of_week': alert.timestamp.weekday(),
            'is_weekend': alert.timestamp.weekday() >= 5,
            
            # Source IP features
            'src_ip': alert.src_ip,
            'src_port': alert.src_port or 0,
            'src_is_private': self._is_private_ip(alert.src_ip),
            'src_port_category': self._categorize_port(alert.src_port),
            
            # Destination IP features
            'dst_ip': alert.dst_ip,
            'dst_port': alert.dst_port or 0,
            'dst_is_private': self._is_private_ip(alert.dst_ip),
            'dst_port_category': self._categorize_port(alert.dst_port),
            
            # Network flow features
            'is_inbound': self._is_inbound_traffic(alert.src_ip, alert.dst_ip),
            'is_outbound': self._is_outbound_traffic(alert.src_ip, alert.dst_ip),
            'is_lateral': self._is_lateral_movement(alert.src_ip, alert.dst_ip),
            
            # Security relevance features
            'severity_score': self._calculate_severity_score(alert),
            'suspicious_port': self._is_suspicious_port(alert.src_port, alert.dst_port),
            'known_attack_pattern': self._match_attack_patterns(alert.message, alert.classification),
            
            # Raw data for model
            'raw_alert': alert.raw_alert
        }
        
        return features
    
    def _is_private_ip(self, ip_str: str) -> bool:
        """Check if IP is in private range"""
        try:
            ip = ipaddress.ip_address(ip_str)
            return ip.is_private
        except ValueError:
            return False
    
    def _categorize_port(self, port: Optional[int]) -> str:
        """Categorize port into well-known ranges"""
        if port is None:
            return "unknown"
        elif port < 1024:
            return "well_known"
        elif port < 49152:
            return "registered"
        else:
            return "dynamic"
    
    def _is_inbound_traffic(self, src_ip: str, dst_ip: str) -> bool:
        """Check if traffic is inbound (external to internal)"""
        return not self._is_private_ip(src_ip) and self._is_private_ip(dst_ip)
    
    def _is_outbound_traffic(self, src_ip: str, dst_ip: str) -> bool:
        """Check if traffic is outbound (internal to external)"""
        return self._is_private_ip(src_ip) and not self._is_private_ip(dst_ip)
    
    def _is_lateral_movement(self, src_ip: str, dst_ip: str) -> bool:
        """Check if traffic is lateral (internal to internal)"""
        return self._is_private_ip(src_ip) and self._is_private_ip(dst_ip)
    
    def _calculate_severity_score(self, alert: SnortAlert) -> float:
        """Calculate a severity score based on alert characteristics"""
        score = 0.0
        
        # Priority-based scoring (higher priority = higher score)
        if alert.priority == 1:
            score += 0.4
        elif alert.priority == 2:
            score += 0.3
        elif alert.priority == 3:
            score += 0.2
        else:
            score += 0.1
        
        # Classification-based scoring
        high_risk_classifications = [
            'trojan-activity', 'malware-cnc', 'attempted-admin',
            'successful-admin', 'attempted-dos', 'denial-of-service'
        ]
        
        for high_risk in high_risk_classifications:
            if high_risk in alert.classification.lower():
                score += 0.3
                break
        
        # Protocol-based scoring
        if alert.protocol in ['TCP', 'UDP']:
            score += 0.1
        
        # Port-based scoring
        suspicious_ports = [22, 23, 135, 139, 445, 1433, 3389, 5900]
        if alert.dst_port in suspicious_ports or alert.src_port in suspicious_ports:
            score += 0.2
        
        return max(0.0, min(1.0, score))  # Clamp between 0 and 1
    
    def _is_suspicious_port(self, src_port: Optional[int], dst_port: Optional[int]) -> bool:
        """Check if ports are commonly associated with attacks"""
        suspicious_ports = {
            22: 'ssh', 23: 'telnet', 135: 'rpc', 139: 'netbios',
            445: 'smb', 1433: 'mssql', 3389: 'rdp', 5900: 'vnc',
            6667: 'irc', 31337: 'backdoor', 12345: 'netbus'
        }
        
        return (src_port in suspicious_ports) or (dst_port in suspicious_ports)
    
    def _match_attack_patterns(self, message: str, classification: str) -> bool:
        """Check if message/classification matches known attack patterns"""
        attack_keywords = [
            'exploit', 'backdoor', 'trojan', 'malware', 'shellcode',
            'buffer overflow', 'sql injection', 'xss', 'reconnaissance',
            'scan', 'brute force', 'denial of service', 'dos', 'ddos'
        ]
        
        text_to_check = (message + " " + classification).lower()
        return any(keyword in text_to_check for keyword in attack_keywords)
    
    def extract_batch_features(self, alerts: List[SnortAlert]) -> List[Dict[str, any]]:
        """Extract features from multiple alerts"""
        return [self.extract_features(alert) for alert in alerts]