# GitHub Runners and Workflows for IDS/IPS

This repository includes GitHub Actions workflows to help with decision making for IDS/IPS (Intrusion Detection/Prevention System) and packet filtering using Snort3.

## Architecture Overview

The system uses three main workflows that communicate with each other:

1. **IDS/IPS Packet Analysis** - Analyzes network packets using Snort3
2. **Packet Filtering Decision** - Generates and applies filtering rules
3. **Runner Communication Hub** - Coordinates communication between runners

## Self-Hosted Runner Setup

To use these workflows, you need to set up a self-hosted GitHub runner with Snort3 installed.

### Prerequisites

- A Linux machine (Ubuntu 20.04+ recommended)
- Root or sudo access
- Network access for packet capture
- GitHub repository access

### Step 1: Install Snort3

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y build-essential libpcap-dev libpcre3-dev \
  libdumbnet-dev bison flex zlib1g-dev liblzma-dev openssl libssl-dev \
  libnghttp2-dev libluajit-5.1-dev pkg-config libhwloc-dev cmake

# Install DAQ (Data Acquisition library)
cd /tmp
wget https://www.snort.org/downloads/snortplus/daq-3.0.13.tar.gz
tar -xvzf daq-3.0.13.tar.gz
cd daq-3.0.13
./bootstrap
./configure
make
sudo make install

# Install Snort3
cd /tmp
wget https://www.snort.org/downloads/snortplus/snort3-3.1.74.0.tar.gz
tar -xvzf snort3-3.1.74.0.tar.gz
cd snort3-3.1.74.0
./configure_cmake.sh --prefix=/usr/local --enable-tcmalloc
cd build
make
sudo make install

# Update library cache
sudo ldconfig

# Verify installation
snort --version
```

### Step 2: Configure Snort3

```bash
# Create Snort directories
sudo mkdir -p /etc/snort/rules
sudo mkdir -p /var/log/snort
sudo mkdir -p /usr/local/lib/snort_dynamicrules

# Create basic Snort configuration
sudo tee /etc/snort/snort.lua > /dev/null << 'EOF'
-- Snort3 basic configuration for IDS/IPS
HOME_NET = '192.168.1.0/24'
EXTERNAL_NET = '!$HOME_NET'

-- Configure IPS mode
ips = {
    enable_builtin_rules = true,
    variables = default_variables
}

-- Alert configuration
alert_full = {
    file = true,
    limit = 10
}

-- Output to file
output = {
    logdir = '/var/log/snort'
}
EOF

# Set permissions
sudo chmod -R 755 /etc/snort
sudo chmod -R 755 /var/log/snort
```

### Step 3: Install GitHub Actions Runner

```bash
# Create a directory for the runner
mkdir -p ~/actions-runner && cd ~/actions-runner

# Download the latest runner package
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract the installer
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure the runner
# Navigate to your GitHub repository > Settings > Actions > Runners > New self-hosted runner
# Use the token provided by GitHub
./config.sh --url https://github.com/YOUR_USERNAME/snortMakeShiftInstall \
  --token YOUR_REGISTRATION_TOKEN \
  --labels snort-runner

# Install and start the runner as a service
sudo ./svc.sh install
sudo ./svc.sh start
```

### Step 4: Verify Runner Setup

1. Go to your repository on GitHub
2. Navigate to Settings > Actions > Runners
3. Verify that your self-hosted runner appears with the label "snort-runner"
4. Check that the status is "Idle" or "Active"

## Using the Workflows

### 1. IDS/IPS Packet Analysis

**Purpose**: Analyze network packets for threats and anomalies.

**Trigger**: 
- Manual: Go to Actions > IDS/IPS Packet Analysis > Run workflow
- Automated: Via repository_dispatch event

**Parameters**:
- `pcap_file`: Path to PCAP file to analyze (default: sample.pcap)
- `analysis_mode`: Choose between `ids` (detection only) or `ips` (prevention)
- `sensitivity`: Detection sensitivity level (low/medium/high)

**Workflow**:
```
Manual Trigger → Load PCAP → Run Snort Analysis → Generate Report → Upload Results
                                                   ↓
                                            (If IPS mode)
                                                   ↓
                                    Trigger Packet Filtering Workflow
```

**Example API trigger**:
```bash
curl -L \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_PAT" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/YOUR_USERNAME/snortMakeShiftInstall/dispatches \
  -d '{"event_type":"analyze_packets","client_payload":{"pcap_file":"traffic.pcap","analysis_mode":"ips","sensitivity":"high"}}'
```

### 2. Packet Filtering Decision

**Purpose**: Generate and apply Snort filtering rules based on analysis or manual input.

**Trigger**:
- Manual: Go to Actions > Packet Filtering Decision > Run workflow
- Automated: Triggered by IDS/IPS Analysis workflow (IPS mode)

**Parameters**:
- `filter_mode`: Action to take (allow/block/monitor)
- `source_ip`: Source IP pattern (optional)
- `destination_ip`: Destination IP pattern (optional)
- `protocol`: Protocol to filter (tcp/udp/icmp/all)
- `port`: Port number to filter (optional)

**Workflow**:
```
Trigger → Generate Rules → Validate Rules → Apply Rules → Upload Artifacts
                                                           ↓
                                            Notify Communication Hub
```

**Example manual trigger**: Go to Actions tab and select "Packet Filtering Decision" workflow.

### 3. Runner Communication Hub

**Purpose**: Coordinate communication between workflows and monitor system status.

**Trigger**:
- Manual: Go to Actions > Runner Communication Hub > Run workflow
- Automated: Triggered by other workflows or scheduled hourly
- Repository dispatch events: rules_updated, system_status, alert_triggered

**Parameters**:
- `message_type`: Type of message (status/alert/update/sync)
- `message_content`: Custom message content

**Workflow**:
```
Trigger → Collect System Status → Process Message → Broadcast/Sync → Upload Logs
```

**Scheduled execution**: Runs automatically every hour to check system status.

## Communication Flow

The workflows communicate using GitHub's repository_dispatch events:

```
IDS/IPS Analysis (IPS mode)
    ↓ [repository_dispatch: filter_packets]
Packet Filtering Decision
    ↓ [repository_dispatch: rules_updated]
Runner Communication Hub
    ↓ [broadcasts status/alerts]
Monitoring & Logging
```

## Artifacts and Results

All workflows generate artifacts that are stored for 30 days:

1. **IDS/IPS Analysis**: Analysis results in JSON format
2. **Packet Filtering**: Generated Snort rules and application logs
3. **Communication Hub**: Communication logs and status reports

Access artifacts: Actions > Workflow Run > Artifacts section

## Security Considerations

1. **Self-hosted runner security**: Ensure the runner machine is properly secured
2. **Network isolation**: Run the runner in a controlled network environment
3. **Access control**: Use repository secrets for sensitive data
4. **Rule validation**: Always validate generated rules before production deployment
5. **Monitoring**: Regularly review communication hub logs for anomalies

## Advanced Usage

### Automatic IPS Mode

To enable fully automatic IPS mode:

1. Run IDS/IPS Analysis in `ips` mode
2. The workflow automatically triggers Packet Filtering
3. Rules are generated based on detected threats
4. Communication Hub is notified
5. Review and approve rules before deployment

### Custom Rule Integration

You can integrate custom Snort rules by:

1. Adding rules to the filter-rules directory
2. Modifying the Packet Filtering workflow
3. Using the Communication Hub to sync across runners

### Multi-Runner Setup

For distributed packet analysis:

1. Set up multiple self-hosted runners with the `snort-runner` label
2. Workflows will distribute across available runners
3. Use Communication Hub to synchronize state
4. Aggregate results using artifacts

## Troubleshooting

### Runner not appearing

- Check runner service: `sudo ./svc.sh status`
- Review runner logs: `tail -f ~/actions-runner/_diag/Runner_*.log`
- Verify network connectivity to GitHub

### Snort not found

- Verify installation: `which snort`
- Check PATH: `echo $PATH`
- Update library cache: `sudo ldconfig`

### Workflow fails

- Check workflow logs in Actions tab
- Verify runner has necessary permissions
- Ensure Snort configuration is valid

## Support

For issues or questions:
1. Check workflow run logs in the Actions tab
2. Review artifacts for detailed error messages
3. Consult Snort3 documentation for configuration issues
4. Open an issue in this repository

## Future Enhancements

- Machine learning-based threat detection
- Integration with external SIEM systems
- Real-time alerting via webhooks
- Dashboard for visualization
- Automated response actions
