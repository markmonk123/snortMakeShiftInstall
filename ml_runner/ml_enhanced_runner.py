#!/usr/bin/env python3
"""
Main ML-Enhanced Snort Runner
Monitors Snort alerts, analyzes them with ML, and generates rules
"""

import asyncio
import logging
import signal
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from pathlib import Path

# Add the ml_runner directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from alert_parser import AlertParser, AlertFeatureExtractor, SnortAlert
from ml_analyzer import MLAnalysisManager, MLAnalysisResult
from rule_generator import SnortRuleGenerator, SnortRuleManager

# Configure logging
def setup_logging():
    """Set up logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.log_level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if config.log_file:
        from logging.handlers import RotatingFileHandler
        os.makedirs(os.path.dirname(config.log_file), exist_ok=True)
        file_handler = RotatingFileHandler(
            config.log_file,
            maxBytes=config.log_max_bytes,
            backupCount=config.log_backup_count
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)

logger = logging.getLogger(__name__)


class AlertMonitor:
    """Monitors Snort alert file for new alerts"""
    
    def __init__(self, alert_file: str):
        self.alert_file = alert_file
        self.last_position = 0
        self.running = False
        
        # Ensure alert file exists
        Path(alert_file).parent.mkdir(parents=True, exist_ok=True)
        Path(alert_file).touch(exist_ok=True)
    
    async def start_monitoring(self, callback):
        """Start monitoring alerts and call callback for new alerts"""
        self.running = True
        logger.info(f"Starting alert monitoring: {self.alert_file}")
        
        # Get initial file position
        if os.path.exists(self.alert_file):
            self.last_position = os.path.getsize(self.alert_file)
        
        while self.running:
            try:
                new_alerts = await self._read_new_alerts()
                if new_alerts:
                    await callback(new_alerts)
                
                await asyncio.sleep(config.processing_interval)
                
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _read_new_alerts(self) -> List[str]:
        """Read new alerts from file since last position"""
        if not os.path.exists(self.alert_file):
            return []
        
        try:
            current_size = os.path.getsize(self.alert_file)
            if current_size <= self.last_position:
                return []
            
            with open(self.alert_file, 'r') as f:
                f.seek(self.last_position)
                new_content = f.read()
                self.last_position = current_size
            
            # Split into lines and filter empty lines
            new_alerts = [line.strip() for line in new_content.split('\n') if line.strip()]
            
            if new_alerts:
                logger.debug(f"Found {len(new_alerts)} new alerts")
            
            return new_alerts
            
        except Exception as e:
            logger.error(f"Error reading alert file: {e}")
            return []
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        logger.info("Alert monitoring stopped")


class MLEnhancedRunner:
    """Main runner that orchestrates the ML-enhanced Snort analysis"""
    
    def __init__(self):
        self.alert_parser = AlertParser()
        self.feature_extractor = AlertFeatureExtractor()
        self.rule_generator = SnortRuleGenerator()
        self.rule_manager = SnortRuleManager()
        self.alert_monitor = AlertMonitor(config.snort_alert_file)
        
        # Statistics
        self.stats = {
            'alerts_processed': 0,
            'ml_analyses_performed': 0,
            'rules_generated': 0,
            'high_confidence_detections': 0,
            'start_time': datetime.now()
        }
        
        # Alert history for analysis
        self.alert_batch = []
        self.last_batch_process = datetime.now()
        
        # Shutdown handling
        self.shutdown_event = asyncio.Event()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self._shutdown())
    
    async def _shutdown(self):
        """Graceful shutdown"""
        self.alert_monitor.stop()
        self.shutdown_event.set()
        logger.info("Shutdown initiated")
    
    async def run(self):
        """Main run loop"""
        logger.info("Starting ML-Enhanced Snort Runner")
        logger.info(f"Configuration: {config.ml_model_type} model, confidence threshold: {config.confidence_threshold}")
        
        try:
            # Validate configuration
            config.validate()
            
            # Start alert monitoring
            monitor_task = asyncio.create_task(
                self.alert_monitor.start_monitoring(self._process_new_alerts)
            )
            
            # Start periodic batch processing
            batch_task = asyncio.create_task(self._batch_processor())
            
            # Start statistics reporting
            stats_task = asyncio.create_task(self._stats_reporter())
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
            # Cancel tasks
            monitor_task.cancel()
            batch_task.cancel()
            stats_task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(monitor_task, batch_task, stats_task, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Fatal error in runner: {e}")
            raise
        finally:
            await self._save_final_stats()
            logger.info("ML-Enhanced Snort Runner stopped")
    
    async def _process_new_alerts(self, alert_lines: List[str]):
        """Process new alerts from Snort"""
        try:
            # Parse alerts
            alerts = self.alert_parser.parse_alerts_batch(alert_lines)
            if not alerts:
                return
            
            self.stats['alerts_processed'] += len(alerts)
            logger.info(f"Processing {len(alerts)} new alerts")
            
            # Add to batch for processing
            self.alert_batch.extend(alerts)
            
            # Process batch if it's large enough or enough time has passed
            if (len(self.alert_batch) >= config.max_alerts_per_batch or
                datetime.now() - self.last_batch_process > timedelta(seconds=config.processing_interval * 2)):
                await self._process_alert_batch()
            
        except Exception as e:
            logger.error(f"Error processing new alerts: {e}")
    
    async def _process_alert_batch(self):
        """Process accumulated alerts with ML analysis"""
        if not self.alert_batch:
            return
        
        try:
            batch_size = len(self.alert_batch)
            logger.info(f"Processing batch of {batch_size} alerts with ML analysis")
            
            # Extract features for all alerts
            alerts_with_features = []
            for alert in self.alert_batch:
                features = self.feature_extractor.extract_features(alert)
                alerts_with_features.append((alert, features))
            
            # Perform ML analysis
            async with MLAnalysisManager() as ml_manager:
                analysis_results = await ml_manager.analyze_alerts_batch(alerts_with_features)
            
            self.stats['ml_analyses_performed'] += len(analysis_results)
            
            # Process results and generate rules
            await self._process_analysis_results(alerts_with_features, analysis_results)
            
            # Clear batch
            self.alert_batch = []
            self.last_batch_process = datetime.now()
            
            logger.info(f"Completed batch processing of {batch_size} alerts")
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            # Clear batch to prevent getting stuck
            self.alert_batch = []
    
    async def _process_analysis_results(self, alerts_with_features: List[tuple], 
                                      analysis_results: List[MLAnalysisResult]):
        """Process ML analysis results and generate rules"""
        try:
            high_confidence_results = []
            
            for i, result in enumerate(analysis_results):
                if isinstance(result, Exception):
                    logger.error(f"Analysis error for alert {i}: {result}")
                    continue
                
                alert, features = alerts_with_features[i]
                
                # Log analysis result
                logger.info(f"Alert SID {alert.sid}: Confidence={result.confidence:.2f}, "
                          f"Classification={result.threat_classification}, "
                          f"Action={result.recommended_action}")
                
                # Track high-confidence detections
                if result.confidence >= config.confidence_threshold:
                    high_confidence_results.append((alert, result))
                    self.stats['high_confidence_detections'] += 1
                
                # Save analysis to history
                await self._save_analysis_history(alert, features, result)
            
            # Generate rules for high-confidence detections
            if high_confidence_results:
                await self._generate_and_apply_rules(high_confidence_results)
            
        except Exception as e:
            logger.error(f"Error processing analysis results: {e}")
    
    async def _generate_and_apply_rules(self, high_confidence_results: List[tuple]):
        """Generate and apply Snort rules for high-confidence detections"""
        try:
            new_rules = []
            
            for alert, analysis in high_confidence_results:
                rule = self.rule_generator.generate_rule_from_ml_analysis(alert, analysis)
                if rule:
                    new_rules.append(rule)
                    logger.info(f"Generated rule SID {rule.sid} for high-confidence detection: {rule.message}")
            
            if new_rules:
                # Apply rules to Snort
                success = self.rule_manager.add_rules(new_rules)
                if success:
                    self.stats['rules_generated'] += len(new_rules)
                    logger.info(f"Successfully applied {len(new_rules)} new rules to Snort")
                    
                    # Save rule history
                    await self._save_rule_history(new_rules)
                else:
                    logger.error("Failed to apply new rules to Snort")
            
        except Exception as e:
            logger.error(f"Error generating and applying rules: {e}")
    
    async def _save_analysis_history(self, alert: SnortAlert, features: Dict, 
                                   analysis: MLAnalysisResult):
        """Save analysis history for future reference"""
        try:
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'alert': alert.to_dict(),
                'features': features,
                'analysis': analysis.to_dict()
            }
            
            # Append to history file (async)
            history_file = config.alert_history_file
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            
            # Read existing history
            history = []
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r') as f:
                        history = json.load(f)
                except json.JSONDecodeError:
                    history = []
            
            # Add new entry
            history.append(history_entry)
            
            # Keep only recent history
            cutoff_date = datetime.now() - timedelta(days=config.max_history_days)
            history = [
                entry for entry in history 
                if datetime.fromisoformat(entry['timestamp']) > cutoff_date
            ]
            
            # Save updated history
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error saving analysis history: {e}")
    
    async def _save_rule_history(self, rules: List):
        """Save rule generation history"""
        try:
            rule_entries = [rule.to_dict() for rule in rules]
            
            history_file = config.rule_history_file
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            
            # Read existing history
            history = []
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r') as f:
                        history = json.load(f)
                except json.JSONDecodeError:
                    history = []
            
            # Add new entries
            history.extend(rule_entries)
            
            # Save updated history
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error saving rule history: {e}")
    
    async def _batch_processor(self):
        """Periodic batch processor"""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(config.processing_interval)
                
                # Process any pending alerts
                if self.alert_batch and datetime.now() - self.last_batch_process > timedelta(seconds=config.processing_interval):
                    await self._process_alert_batch()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
    
    async def _stats_reporter(self):
        """Periodic statistics reporting"""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(60)  # Report every minute
                
                uptime = datetime.now() - self.stats['start_time']
                
                logger.info(f"Statistics - Uptime: {uptime}, "
                          f"Alerts: {self.stats['alerts_processed']}, "
                          f"ML Analyses: {self.stats['ml_analyses_performed']}, "
                          f"High Confidence: {self.stats['high_confidence_detections']}, "
                          f"Rules Generated: {self.stats['rules_generated']}")
                
                # Get parser stats
                parser_stats = self.alert_parser.get_stats()
                logger.debug(f"Parser stats: {parser_stats}")
                
                # Get rule manager stats
                rule_stats = self.rule_manager.get_rule_stats()
                logger.debug(f"Rule stats: {rule_stats}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in stats reporter: {e}")
    
    async def _save_final_stats(self):
        """Save final statistics on shutdown"""
        try:
            # Convert datetime to string for JSON serialization
            stats_copy = self.stats.copy()
            stats_copy['start_time'] = stats_copy['start_time'].isoformat()
            
            final_stats = {
                'session_stats': stats_copy,
                'parser_stats': self.alert_parser.get_stats(),
                'rule_stats': self.rule_manager.get_rule_stats(),
                'shutdown_time': datetime.now().isoformat()
            }
            
            stats_file = "/var/log/snort/ml_runner_final_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(final_stats, f, indent=2)
            
            logger.info(f"Final statistics saved to {stats_file}")
            
        except Exception as e:
            logger.error(f"Error saving final stats: {e}")


async def main():
    """Main entry point"""
    # Set up logging
    setup_logging()
    
    try:
        logger.info("Starting ML-Enhanced Snort Runner")
        
        # Create and run the ML runner
        runner = MLEnhancedRunner()
        await runner.run()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())