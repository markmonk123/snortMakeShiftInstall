#!/usr/bin/env python3
"""
ML Analysis interface for processing Snort alerts with AI models
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from config import config
from alert_parser import SnortAlert

logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available. OpenAI analyzer will be disabled.")


@dataclass
class MLAnalysisResult:
    """Result of ML analysis on alert data"""
    confidence: float
    threat_classification: str
    threat_description: str
    recommended_action: str
    additional_context: Dict[str, Any]
    rule_suggestion: Optional[str] = None
    analysis_timestamp: datetime = None
    
    def __post_init__(self):
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'confidence': self.confidence,
            'threat_classification': self.threat_classification,
            'threat_description': self.threat_description,
            'recommended_action': self.recommended_action,
            'additional_context': self.additional_context,
            'rule_suggestion': self.rule_suggestion,
            'analysis_timestamp': self.analysis_timestamp.isoformat()
        }


class BaseMLAnalyzer:
    """Base class for ML analyzers"""
    
    def __init__(self):
        self.analysis_count = 0
        self.error_count = 0
    
    async def analyze_alert(self, alert: SnortAlert, features: Dict[str, Any]) -> MLAnalysisResult:
        """Analyze a single alert with ML model"""
        raise NotImplementedError("Subclasses must implement analyze_alert")
    
    async def analyze_alerts_batch(self, alerts_with_features: List[tuple]) -> List[MLAnalysisResult]:
        """Analyze multiple alerts in batch"""
        results = []
        for alert, features in alerts_with_features:
            try:
                result = await self.analyze_alert(alert, features)
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing alert {alert.sid}: {e}")
                self.error_count += 1
        return results
    
    def get_stats(self) -> Dict[str, int]:
        """Get analysis statistics"""
        return {
            'analysis_count': self.analysis_count,
            'error_count': self.error_count
        }


class OpenAIAnalyzer(BaseMLAnalyzer):
    """OpenAI-based ML analyzer for Snort alerts"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", max_retries: int = 3):
        super().__init__()
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        
        # System prompt for threat analysis
        self.system_prompt = """
You are a cybersecurity expert specializing in network intrusion detection and threat analysis. 
Your task is to analyze Snort IDS/IPS alerts and provide detailed threat assessment.

For each alert, provide:
1. Confidence score (0.0 to 1.0) - how confident you are this represents a real threat
2. Threat classification (e.g., malware, reconnaissance, exploit, false_positive)
3. Detailed threat description
4. Recommended action (block, monitor, investigate, ignore)
5. Additional context about the threat
6. If confidence >= 0.98, suggest a specific Snort rule to detect similar threats

Consider factors like:
- Source/destination IPs (internal vs external)
- Ports and protocols involved
- Alert classification and message
- Time patterns
- Known attack signatures
- False positive likelihood

Respond in JSON format with the structure:
{
    "confidence": 0.95,
    "threat_classification": "malware",
    "threat_description": "Detailed description of the threat",
    "recommended_action": "block",
    "additional_context": {"key": "value"},
    "rule_suggestion": "alert tcp any any -> any any (msg:\"...\"; ...)"
}
        """
    
    async def analyze_alert(self, alert: SnortAlert, features: Dict[str, Any]) -> MLAnalysisResult:
        """Analyze alert using OpenAI API"""
        try:
            # Prepare the analysis prompt
            analysis_prompt = self._create_analysis_prompt(alert, features)
            
            # Make API call with retries
            for attempt in range(self.max_retries):
                try:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": analysis_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1000
                    )
                    
                    # Parse response
                    result_json = json.loads(response.choices[0].message.content)
                    
                    # Create analysis result
                    analysis_result = MLAnalysisResult(
                        confidence=float(result_json.get('confidence', 0.0)),
                        threat_classification=result_json.get('threat_classification', 'unknown'),
                        threat_description=result_json.get('threat_description', ''),
                        recommended_action=result_json.get('recommended_action', 'monitor'),
                        additional_context=result_json.get('additional_context', {}),
                        rule_suggestion=result_json.get('rule_suggestion')
                    )
                    
                    self.analysis_count += 1
                    logger.info(f"ML Analysis: SID {alert.sid}, Confidence: {analysis_result.confidence:.2f}, "
                              f"Classification: {analysis_result.threat_classification}")
                    
                    return analysis_result
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse ML response (attempt {attempt + 1}): {e}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"OpenAI API error (attempt {attempt + 1}): {e}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
        except Exception as e:
            logger.error(f"Error in ML analysis for alert {alert.sid}: {e}")
            self.error_count += 1
            
            # Return default analysis on error
            return MLAnalysisResult(
                confidence=0.5,
                threat_classification='analysis_error',
                threat_description=f'Failed to analyze alert: {str(e)}',
                recommended_action='investigate',
                additional_context={'error': str(e)}
            )
    
    def _create_analysis_prompt(self, alert: SnortAlert, features: Dict[str, Any]) -> str:
        """Create detailed analysis prompt for the ML model"""
        prompt = f"""
Analyze this Snort IDS alert for threat assessment:

ALERT DETAILS:
- Timestamp: {alert.timestamp}
- Message: {alert.message}
- Classification: {alert.classification}
- Priority: {alert.priority}
- SID: {alert.sid}
- Protocol: {alert.protocol}
- Source: {alert.src_ip}:{alert.src_port}
- Destination: {alert.dst_ip}:{alert.dst_port}

EXTRACTED FEATURES:
- Source IP is private: {features.get('src_is_private')}
- Destination IP is private: {features.get('dst_is_private')}
- Traffic direction: {'inbound' if features.get('is_inbound') else 'outbound' if features.get('is_outbound') else 'lateral'}
- Source port category: {features.get('src_port_category')}
- Destination port category: {features.get('dst_port_category')}
- Suspicious port detected: {features.get('suspicious_port')}
- Known attack pattern: {features.get('known_attack_pattern')}
- Severity score: {features.get('severity_score', 0):.2f}
- Time of day: {features.get('hour_of_day')}
- Day of week: {features.get('day_of_week')}
- Weekend: {features.get('is_weekend')}

CONTEXT:
This alert was generated by Snort3 IDS/IPS monitoring network traffic. Please assess the likelihood this represents a genuine security threat versus a false positive.

If you determine this is a high-confidence threat (>= 0.98), please suggest a specific Snort rule that could be used to detect similar attacks in the future.
        """
        return prompt.strip()


class LocalMLAnalyzer(BaseMLAnalyzer):
    """Local ML model analyzer (placeholder for future implementation)"""
    
    def __init__(self, model_path: str):
        super().__init__()
        self.model_path = model_path
        logger.warning("LocalMLAnalyzer is not yet implemented - using mock analysis")
    
    async def analyze_alert(self, alert: SnortAlert, features: Dict[str, Any]) -> MLAnalysisResult:
        """Mock analysis for local model (to be implemented)"""
        # This is a placeholder - real implementation would load and use a local ML model
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Mock analysis based on features
        confidence = features.get('severity_score', 0.5)
        if features.get('suspicious_port') or features.get('known_attack_pattern'):
            confidence = min(confidence + 0.3, 1.0)
        
        self.analysis_count += 1
        
        return MLAnalysisResult(
            confidence=confidence,
            threat_classification='mock_analysis',
            threat_description=f'Mock analysis of alert: {alert.message}',
            recommended_action='monitor',
            additional_context={'mock': True, 'features_count': len(features)}
        )


class MLAnalyzerFactory:
    """Factory for creating ML analyzers"""
    
    @staticmethod
    def create_analyzer(analyzer_type: str = None) -> BaseMLAnalyzer:
        """Create appropriate ML analyzer based on configuration"""
        analyzer_type = analyzer_type or config.ml_model_type
        
        if analyzer_type == "openai":
            if not config.ml_api_key:
                raise ValueError("OpenAI API key required for OpenAI analyzer")
            return OpenAIAnalyzer(
                api_key=config.ml_api_key,
                model=config.ml_model_name
            )
        elif analyzer_type == "local":
            model_path = config.ml_api_endpoint or "/tmp/model.pkl"
            return LocalMLAnalyzer(model_path)
        else:
            raise ValueError(f"Unsupported analyzer type: {analyzer_type}")


# Async context manager for ML analyzer
class MLAnalysisManager:
    """Manages ML analysis sessions with proper cleanup"""
    
    def __init__(self, analyzer_type: str = None):
        self.analyzer_type = analyzer_type
        self.analyzer = None
        self.semaphore = asyncio.Semaphore(config.max_concurrent_analyses)
    
    async def __aenter__(self):
        self.analyzer = MLAnalyzerFactory.create_analyzer(self.analyzer_type)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self.analyzer, 'close'):
            await self.analyzer.close()
    
    async def analyze_alert(self, alert: SnortAlert, features: Dict[str, Any]) -> MLAnalysisResult:
        """Analyze alert with concurrency control"""
        async with self.semaphore:
            return await self.analyzer.analyze_alert(alert, features)
    
    async def analyze_alerts_batch(self, alerts_with_features: List[tuple]) -> List[MLAnalysisResult]:
        """Analyze multiple alerts with concurrency control"""
        tasks = []
        for alert, features in alerts_with_features:
            task = self.analyze_alert(alert, features)
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)