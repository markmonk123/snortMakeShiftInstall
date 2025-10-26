# Workflow Architecture and Implementation

## Overview

This document describes the complete architecture of the GitHub Actions workflows for IDS/IPS decision making and packet filtering.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions Workflows                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐      ┌──────────────────┐                 │
│  │   IDS/IPS       │      │    Packet        │                 │
│  │   Analysis      │─────▶│    Filtering     │                 │
│  │   Workflow      │      │    Workflow      │                 │
│  └─────────────────┘      └──────────────────┘                 │
│         │                          │                             │
│         │                          │                             │
│         └──────────┬───────────────┘                            │
│                    │                                             │
│                    ▼                                             │
│         ┌──────────────────┐                                    │
│         │   Communication  │                                    │
│         │      Hub         │                                    │
│         │    Workflow      │                                    │
│         └──────────────────┘                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ Runs on
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Self-Hosted Runner (snort-runner)              │
├─────────────────────────────────────────────────────────────────┤
│  • Snort3 IDS/IPS Engine                                        │
│  • Network Packet Capture                                       │
│  • Rule Processing                                              │
│  • Log Generation                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Workflow Components

### 1. IDS/IPS Packet Analysis Workflow

**File**: `.github/workflows/ids-ips-analysis.yml`

**Purpose**: Analyzes network packets using Snort3 for intrusion detection and prevention.

**Triggers**:
- Manual dispatch via Actions UI
- Repository dispatch with event type `analyze_packets`

**Key Features**:
- Configurable analysis modes (IDS/IPS)
- Adjustable sensitivity levels (low/medium/high)
- PCAP file processing
- Automatic workflow chaining (triggers packet filtering in IPS mode)
- Artifact storage for analysis results
- Job summary generation

**Process Flow**:
1. Receive analysis parameters
2. Verify Snort3 installation
3. Load Snort3 configuration
4. Run packet analysis
5. Generate analysis report (JSON format)
6. Upload results as artifacts
7. Trigger packet filtering workflow (if IPS mode)
8. Generate workflow summary

**Security**:
- Minimal permissions: `contents: read`, `actions: write`
- Runs on isolated self-hosted runner

### 2. Packet Filtering Decision Workflow

**File**: `.github/workflows/packet-filtering.yml`

**Purpose**: Generates and applies Snort filtering rules based on analysis results or manual input.

**Triggers**:
- Manual dispatch via Actions UI
- Repository dispatch with event type `filter_packets`
- Automatically triggered by IDS/IPS workflow

**Key Features**:
- Multiple filter modes (allow/block/monitor)
- Protocol-specific filtering
- IP address pattern matching
- Port-based filtering
- Automatic rule generation
- Rule validation
- Unique SID generation for each rule
- Communication with hub workflow

**Process Flow**:
1. Receive filtering parameters
2. Verify Snort3 installation
3. Load previous analysis results (if available)
4. Generate Snort filtering rules
5. Validate generated rules
6. Apply filtering rules
7. Upload rules and logs as artifacts
8. Notify communication hub
9. Generate workflow summary

**Security**:
- Minimal permissions: `contents: read`, `actions: write`
- Rule validation before application
- Unique SID generation to prevent conflicts

### 3. Runner Communication Hub Workflow

**File**: `.github/workflows/runner-communication.yml`

**Purpose**: Coordinates communication between workflows and monitors system status.

**Triggers**:
- Manual dispatch via Actions UI
- Repository dispatch with event types: `rules_updated`, `system_status`, `alert_triggered`
- Scheduled execution (hourly)

**Key Features**:
- Multiple message types (status/alert/update/sync)
- System status collection
- Snort3 health monitoring
- Runner information tracking
- Alert handling
- Configuration synchronization
- Communication logging

**Process Flow**:
1. Determine message source and type
2. Collect system status information
3. Check for pending communications
4. Process message based on type:
   - **Status**: Broadcast system status
   - **Alert**: Create alert log and notify
   - **Update/Sync**: Synchronize configuration
5. Upload communication logs
6. Generate workflow summary

**Security**:
- Minimal permissions: `contents: read`, `actions: write`
- Scheduled monitoring for proactive health checks

## Communication Protocol

### Repository Dispatch Events

The workflows communicate using GitHub's repository_dispatch API:

1. **analyze_packets**
   - Source: External systems, manual trigger
   - Target: IDS/IPS Analysis workflow
   - Payload: `pcap_file`, `analysis_mode`, `sensitivity`

2. **filter_packets**
   - Source: IDS/IPS Analysis workflow
   - Target: Packet Filtering workflow
   - Payload: `analysis_results`, `mode`

3. **rules_updated**
   - Source: Packet Filtering workflow
   - Target: Communication Hub workflow
   - Payload: `rules_file`, `log_file`

4. **alert_triggered**
   - Source: Any monitoring system
   - Target: Communication Hub workflow
   - Payload: `severity`, `message`, `source`

5. **system_status**
   - Source: Monitoring systems
   - Target: Communication Hub workflow
   - Payload: Status information

### API Request Format

```bash
curl -L -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/${OWNER}/${REPO}/dispatches \
  -d '{
    "event_type": "analyze_packets",
    "client_payload": {
      "pcap_file": "traffic.pcap",
      "analysis_mode": "ips",
      "sensitivity": "high"
    }
  }'
```

## Artifacts and Data Storage

### Artifact Types

1. **Analysis Results**
   - Name: `ids-ips-analysis-{mode}-{run_number}`
   - Contents: JSON files with analysis data
   - Retention: 30 days

2. **Filter Rules**
   - Name: `packet-filter-rules-{run_number}`
   - Contents: Snort rule files and application logs
   - Retention: 30 days

3. **Communication Logs**
   - Name: `communication-logs-{run_number}`
   - Contents: Status reports, alerts, sync manifests
   - Retention: 30 days

### Data Schemas

See `examples/api-examples.json` for complete schema definitions.

## Security Considerations

### Workflow Security

1. **Least Privilege Permissions**: All workflows use minimal required permissions
2. **Self-Hosted Runner Isolation**: Runs on dedicated, isolated runners
3. **Token Scope**: Uses GITHUB_TOKEN with limited scope
4. **Rule Validation**: All generated rules are validated before application
5. **Audit Trail**: All actions are logged and stored as artifacts

### Runner Security

1. **Network Isolation**: Runner should be in a controlled network segment
2. **Access Control**: Limited access to runner machine
3. **Regular Updates**: Keep Snort3 and runner software updated
4. **Monitoring**: Communication Hub provides continuous monitoring
5. **Encryption**: All communication with GitHub is encrypted

### Data Security

1. **Artifact Retention**: Limited to 30 days
2. **Sensitive Data**: Avoid including sensitive data in PCAP files
3. **Access Logs**: Monitor who accesses artifacts
4. **Rule Review**: Review generated rules before production deployment

## Self-Hosted Runner Requirements

### Hardware
- CPU: 4+ cores recommended
- RAM: 8GB+ recommended
- Storage: 50GB+ for logs and artifacts
- Network: Dedicated network interface for packet capture

### Software
- OS: Linux (Ubuntu 20.04+ recommended)
- Snort3 3.1.74.0 or later
- DAQ 3.0.13 or later
- GitHub Actions Runner (latest)

### Network Requirements
- Outbound HTTPS to GitHub (443)
- Access to monitored network segments
- Promiscuous mode for packet capture (if needed)

## Operational Procedures

### Starting a New Analysis

1. **Manual Trigger**:
   - Navigate to Actions tab
   - Select "IDS/IPS Packet Analysis"
   - Click "Run workflow"
   - Fill in parameters
   - Click "Run workflow"

2. **Automated Trigger**:
   ```bash
   curl -L -X POST \
     -H "Authorization: Bearer ${PAT}" \
     -H "Accept: application/vnd.github+json" \
     https://api.github.com/repos/${OWNER}/${REPO}/dispatches \
     -d '{"event_type":"analyze_packets","client_payload":{...}}'
   ```

### Monitoring Workflow Status

1. Check Actions tab for running workflows
2. Review job summaries for quick status
3. Download artifacts for detailed analysis
4. Monitor Communication Hub for alerts

### Responding to Alerts

1. Communication Hub receives alert
2. Review alert details in artifacts
3. Analyze associated analysis results
4. Make informed decision on response
5. Trigger packet filtering if needed
6. Document response actions

## Troubleshooting

### Common Issues

1. **Snort3 not found**
   - Verify installation: `snort --version`
   - Check PATH configuration
   - Update library cache: `sudo ldconfig`

2. **Workflow fails to trigger**
   - Verify runner is online and idle
   - Check runner labels match workflow
   - Verify GITHUB_TOKEN permissions
   - Review API request format

3. **Rules not applying**
   - Check rule syntax with Snort3
   - Verify unique SIDs
   - Review Snort3 configuration
   - Check file permissions

4. **Communication Hub not receiving messages**
   - Verify repository_dispatch event type
   - Check API credentials
   - Review workflow trigger configuration

## Performance Optimization

### For Large PCAP Files

1. Use streaming analysis instead of batch
2. Increase runner resources
3. Adjust Snort3 memory limits
4. Consider splitting large files

### For High-Volume Environments

1. Deploy multiple self-hosted runners
2. Use load balancing
3. Implement result caching
4. Optimize rule sets

## Future Enhancements

### Planned Features

1. **Machine Learning Integration**: Anomaly detection using ML models
2. **Real-Time Processing**: Stream processing instead of batch
3. **Dashboard**: Web dashboard for visualization
4. **SIEM Integration**: Integration with external SIEM systems
5. **Automated Response**: Automatic blocking of detected threats
6. **Multi-Runner Coordination**: Better coordination across multiple runners
7. **Performance Analytics**: Detailed performance metrics and optimization

### Community Contributions

Contributions are welcome! Areas for improvement:
- Additional Snort rule templates
- Integration with other security tools
- Enhanced reporting and visualization
- Documentation improvements
- Performance optimizations

## Support and Resources

### Documentation
- [Runner Setup Guide](.github/RUNNER_SETUP.md)
- [API Examples](examples/api-examples.json)
- [Snort3 Documentation](https://www.snort.org/documents)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

### Getting Help
1. Review workflow logs in Actions tab
2. Check artifacts for detailed error messages
3. Consult Snort3 documentation
4. Open an issue in this repository

### Related Projects
- [Snort3](https://www.snort.org/)
- [GitHub Actions](https://github.com/features/actions)
- [DAQ](https://github.com/snort3/libdaq)
