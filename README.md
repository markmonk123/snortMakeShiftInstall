# snortMakeShiftInstall

A python executable to install snort3 the networking application and then configure it for IDS/IPS

## GitHub Actions Integration

This repository includes GitHub Actions workflows for automated IDS/IPS decision making and packet filtering using self-hosted runners.

### Features

- **IDS/IPS Packet Analysis**: Automated network packet analysis using Snort3
- **Packet Filtering Decision**: Dynamic rule generation and filtering based on analysis
- **Runner Communication Hub**: Centralized communication and coordination between workflows
- **Self-Hosted Runner Support**: Dedicated runners for handling sensitive network traffic

### Quick Start

1. **Set up a self-hosted runner** with Snort3 installed (see [Runner Setup Guide](.github/RUNNER_SETUP.md))
2. **Configure your runner** with the `snort-runner` label
3. **Trigger workflows** manually from the Actions tab or via API

### Workflows

- **IDS/IPS Packet Analysis** - Analyze network packets for threats and anomalies
- **Packet Filtering Decision** - Generate and apply Snort filtering rules
- **Runner Communication Hub** - Coordinate communication between runners and monitor system status

### Documentation

- [Runner Setup Guide](.github/RUNNER_SETUP.md) - Complete setup instructions
- [API Examples](examples/api-examples.json) - Integration examples
- [Snort Configuration](examples/snort.lua) - Example Snort3 configuration
- [Sample Rules](examples/local.rules) - Example Snort detection rules

### Architecture

```
GitHub Actions Workflows
    ├── IDS/IPS Analysis
    │   └── Analyzes packets → Triggers filtering (IPS mode)
    ├── Packet Filtering
    │   └── Generates rules → Notifies communication hub
    └── Communication Hub
        └── Coordinates workflows → Monitors system status
```

### Usage

Trigger workflows from the Actions tab or programmatically:

```bash
curl -L -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.github.com/repos/YOUR_USERNAME/snortMakeShiftInstall/dispatches \
  -d '{"event_type":"analyze_packets","client_payload":{"pcap_file":"traffic.pcap","analysis_mode":"ips","sensitivity":"high"}}'
```

For detailed usage instructions, see the [Runner Setup Guide](.github/RUNNER_SETUP.md).
