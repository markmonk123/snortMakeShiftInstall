# ML-Enhanced Snort Runner - System Documentation

## Overview

The ML-Enhanced Snort Runner is a sophisticated system that integrates machine learning capabilities with Snort3 IDS/IPS to provide intelligent threat analysis and automated rule generation. The system monitors Snort alerts in real-time, analyzes them using AI/ML models, and automatically generates new detection rules when high-confidence threats are identified.

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    Snort3       │    │  ML-Enhanced     │    │   ML Model      │
│   IDS/IPS       │───▶│     Runner       │───▶│   (OpenAI/      │
│                 │    │                  │    │    Local)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Alert Log Files │    │ Generated Rules  │    │ Analysis Results│
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Key Features

### 1. **Real-Time Alert Monitoring**
- Continuously monitors Snort alert files (`/var/log/snort/alert_fast.txt`)
- Parses Snort fast alert format with comprehensive feature extraction
- Handles batch processing for efficient ML analysis

### 2. **Advanced ML Analysis**
- **OpenAI Integration**: Uses GPT-4 for sophisticated threat analysis
- **Local Model Support**: Framework for local ML models (extensible)
- **Feature Extraction**: 23+ features extracted from each alert including:
  - Network topology analysis (internal/external traffic)
  - Port categorization and suspicious port detection
  - Temporal patterns (time of day, day of week)
  - Severity scoring based on classification and priority
  - Attack pattern matching

### 3. **Intelligent Rule Generation**
- Generates Snort rules only for high-confidence detections (≥98% by default)
- Creates valid Snort rule syntax with proper SID management
- Includes comprehensive rule metadata and references
- Automatic rule validation and testing before deployment

### 4. **Automated Rule Deployment**
- Safely adds new rules to Snort configuration
- Automatic backup of existing rules before modification
- Configuration testing before rule activation
- Hot-reload of Snort service to apply new rules

### 5. **Comprehensive Logging and Monitoring**
- Detailed logging with configurable levels
- Real-time statistics and performance monitoring
- Historical analysis data retention
- Rule generation history tracking

## Installation and Setup

### Prerequisites
- Ubuntu 24.04 LTS (or compatible Linux distribution)
- Python 3.8+ with asyncio support
- Snort3 installed and configured
- Root/sudo access for Snort configuration management

### Installation Steps

1. **Install Snort3** (if not already installed):
   ```bash
   sudo ./snort3_installer.py --auto
   ```

2. **Set up ML Runner**:
   ```bash
   # Install Python dependencies (optional - most are built-in)
   pip install openai  # Only needed for OpenAI integration
   
   # Make runner executable
   chmod +x main.py
   ```

3. **Configuration**:
   ```bash
   # Test configuration
   sudo python3 main.py --test-config --model local
   
   # For OpenAI integration
   export ML_API_KEY="your-openai-api-key"
   sudo python3 main.py --test-config --model openai
   ```

### Running the System

#### Basic Usage
```bash
# Run with local mock ML model
sudo python3 main.py --model local

# Run with OpenAI integration (requires API key)
sudo ML_API_KEY="your-key" python3 main.py --model openai

# Run with custom configuration
sudo python3 main.py --config custom_config.json --verbose
```

#### Advanced Configuration
```bash
# Custom confidence threshold
sudo python3 main.py --confidence 0.95

# Custom log file location
sudo python3 main.py --log-file /custom/path/ml_runner.log

# Test mode only
sudo python3 main.py --test-config
```

## Configuration Options

### Environment Variables
- `ML_API_KEY`: API key for OpenAI integration
- `ML_MODEL_TYPE`: Model type (openai, local)
- `ML_MODEL_NAME`: Specific model name (default: gpt-4)
- `CONFIDENCE_THRESHOLD`: Confidence threshold for rule generation (default: 0.98)

### Key Configuration Parameters
```python
# ML Model Configuration
ml_model_type = "openai"  # or "local"
confidence_threshold = 0.98
max_concurrent_analyses = 3

# File Paths
snort_alert_file = "/var/log/snort/alert_fast.txt"
snort_rules_file = "/etc/snort/rules/ml_generated.rules"
log_file = "/var/log/snort/ml_runner.log"

# Processing Configuration
max_alerts_per_batch = 10
processing_interval = 5.0  # seconds
```

## System Components

### 1. **config.py**
- Centralized configuration management
- Environment variable integration
- Configuration validation and file I/O

### 2. **alert_parser.py**
- Snort alert parsing and validation
- Feature extraction from network events
- Support for Snort fast alert format

### 3. **ml_analyzer.py**
- ML model integration and analysis
- OpenAI API integration with error handling
- Extensible framework for local models
- Confidence scoring and threat classification

### 4. **rule_generator.py**
- Snort rule generation from ML analysis
- Rule syntax validation and SID management
- Safe rule deployment with backups
- Integration with Snort service management

### 5. **ml_enhanced_runner.py**
- Main orchestration and event loop
- Real-time alert monitoring
- Batch processing and concurrency control
- Statistics and performance monitoring

### 6. **main.py**
- CLI interface and argument parsing
- System validation and prerequisite checking
- Environment setup and configuration

## ML Analysis Process

### 1. **Alert Ingestion**
```
Raw Snort Alert → Parser → Structured Alert Object
```

### 2. **Feature Extraction**
```
Alert Object → Feature Extractor → Feature Vector (23+ features)
```

### 3. **ML Analysis**
```
Features + Context → ML Model → Confidence Score + Classification
```

### 4. **Rule Generation** (if confidence ≥ 98%)
```
High-Confidence Analysis → Rule Generator → Valid Snort Rule
```

### 5. **Rule Deployment**
```
Generated Rule → Validation → Backup → Deploy → Reload Snort
```

## Monitoring and Maintenance

### Log Files
- **Application Logs**: `/var/log/snort/ml_runner.log`
- **Alert History**: `/var/log/snort/alert_history.json`
- **Rule History**: `/var/log/snort/rule_history.json`
- **Statistics**: `/var/log/snort/ml_runner_final_stats.json`

### Real-Time Monitoring
The system provides continuous statistics including:
- Alerts processed per minute
- ML analyses performed
- High-confidence detections
- Rules generated and deployed
- System uptime and performance metrics

### Rule Management
- Generated rules are stored in `/etc/snort/rules/ml_generated.rules`
- Automatic rule backups with timestamp
- SID management to avoid conflicts (starting from 2000000)
- Rule validation before deployment

## Security Considerations

### 1. **API Key Security**
- OpenAI API keys should be stored securely
- Use environment variables or secure configuration files
- Regular API key rotation recommended

### 2. **Rule Quality**
- High confidence threshold (98%) minimizes false positives
- All generated rules are validated before deployment
- Automatic backup and rollback capabilities

### 3. **Access Control**
- System requires root privileges for Snort integration
- Log files contain sensitive network information
- Proper file permissions and access controls recommended

### 4. **Network Security**
- ML analysis may include sensitive network data
- Consider local model deployment for sensitive environments
- Network traffic analysis capabilities should be used responsibly

## Troubleshooting

### Common Issues

1. **Permission Errors**
   ```bash
   # Ensure running as root
   sudo python3 main.py
   ```

2. **Configuration Validation Fails**
   ```bash
   # Check Snort installation
   /usr/local/bin/snort -V
   
   # Verify directories exist
   ls -la /var/log/snort /etc/snort
   ```

3. **ML Analysis Errors**
   ```bash
   # Check API key for OpenAI
   echo $ML_API_KEY
   
   # Use local mode for testing
   sudo python3 main.py --model local
   ```

4. **Rule Generation Issues**
   ```bash
   # Check Snort configuration
   sudo /usr/local/bin/snort -c /etc/snort/snort.lua -T
   
   # Review generated rules
   cat /etc/snort/rules/ml_generated.rules
   ```

### Debug Mode
```bash
# Enable verbose logging
sudo python3 main.py --verbose

# Check system logs
tail -f /var/log/snort/ml_runner.log
```

## Performance Considerations

### Resource Usage
- **Memory**: Approximately 50-100MB for base system
- **CPU**: Low baseline, spikes during ML analysis
- **Network**: Outbound HTTPS for OpenAI API calls
- **Storage**: Log rotation prevents excessive disk usage

### Scaling Recommendations
- **High Traffic Networks**: Increase `max_concurrent_analyses`
- **Resource Constraints**: Reduce `max_alerts_per_batch`
- **API Rate Limits**: Adjust `processing_interval`

## Future Enhancements

### Planned Features
1. **Local ML Model Integration**
   - TensorFlow/PyTorch model support
   - Custom model training capabilities
   - Offline analysis capabilities

2. **Advanced Analytics**
   - Threat trend analysis
   - Attack pattern correlation
   - Network behavior anomaly detection

3. **Integration Enhancements**
   - SIEM integration (Splunk, ELK)
   - Webhook notifications
   - API endpoint for external integration

4. **Rule Management**
   - Rule effectiveness scoring
   - Automatic rule tuning
   - Rule lifecycle management

## Conclusion

The ML-Enhanced Snort Runner represents a significant advancement in network security automation, combining the proven capabilities of Snort3 with cutting-edge AI analysis. The system provides:

- **Automated Threat Detection**: Reduces manual analysis workload
- **Improved Accuracy**: ML analysis helps reduce false positives
- **Rapid Response**: Automated rule generation for new threats
- **Scalable Architecture**: Supports both cloud and local ML models
- **Production Ready**: Comprehensive logging, monitoring, and error handling

This system bridges the gap between traditional signature-based detection and modern AI-powered security analysis, providing organizations with enhanced threat detection capabilities while maintaining the reliability and performance of Snort3.