# Snort3 Installation and Configuration Tool

A Python executable to automatically install Snort3 and configure it for IDS/IPS operation with support for 3 network adapters in container, VM, or bare-metal environments.

## Features

- **Automated Installation**: Installs Snort3 and all dependencies from source
- **IDS/IPS Configuration**: Configures Snort3 for intrusion detection and prevention
- **Multi-Adapter Support**: Configures 3 network adapters:
  - **Incoming Adapter** (onboard ethernet): Monitors incoming traffic
  - **Offload Adapter** (USB ethernet): Handles offload traffic  
  - **Control Adapter** (wireless): Management and SSH access
- **Environment Detection**: Automatically detects container, VM, or bare-metal environments
- **Persistent Configuration**: Creates systemd service for automatic startup
- **Network Persistence**: Ensures network settings persist across reboots

## Requirements

- Ubuntu/Debian-based Linux distribution
- Root/sudo privileges
- Python 3.6 or higher
- At least 3 network adapters
- Internet connection for downloading packages

## Installation

### Quick Start (Auto-Detection)

```bash
sudo ./snort3_installer.py --auto
```

This will automatically detect available network adapters and assign them appropriately.

### Manual Adapter Configuration

If you want to specify adapters manually:

```bash
sudo ./snort3_installer.py --incoming eth0 --offload eth1 --control wlan0
```

### List Available Adapters

To see what network adapters are available:

```bash
sudo ./snort3_installer.py --list-adapters
```

## Usage

```
usage: snort3_installer.py [-h] [--incoming INCOMING] [--offload OFFLOAD]
                           [--control CONTROL] [--auto] [--list-adapters]
                           [--install-dir INSTALL_DIR]
                           [--config-dir CONFIG_DIR]

Snort3 Installation and Configuration Tool

optional arguments:
  -h, --help            show this help message and exit
  --incoming INCOMING   Incoming traffic adapter (onboard ethernet)
  --offload OFFLOAD     Offload adapter (USB ethernet)
  --control CONTROL     Control adapter (wireless)
  --auto                Auto-detect and assign adapters
  --list-adapters       List available network adapters
  --install-dir INSTALL_DIR
                        Installation directory (default: /usr/local)
  --config-dir CONFIG_DIR
                        Configuration directory (default: /etc/snort)

Examples:
  # Auto-detect adapters and install
  sudo ./snort3_installer.py --auto

  # Specify network adapters manually
  sudo ./snort3_installer.py --incoming eth0 --offload eth1 --control wlan0
  
  # List available network adapters
  sudo ./snort3_installer.py --list-adapters
```

## Network Adapter Configuration

The installer configures three network adapters with specific roles:

### 1. Incoming Adapter (Onboard Ethernet)
- **Purpose**: Monitor incoming network traffic
- **Configuration**:
  - Promiscuous mode enabled
  - Hardware offload (GRO/LRO) disabled
  - Used by Snort3 for packet capture

### 2. Offload Adapter (USB Ethernet)
- **Purpose**: Handle forwarded/offload traffic
- **Configuration**:
  - Normal operation mode
  - Used for IPS inline mode forwarding

### 3. Control Adapter (Wireless)
- **Purpose**: Management and remote access
- **Configuration**:
  - Normal operation mode
  - Dedicated for SSH and administrative access
  - Not monitored by Snort3

## What Gets Installed

1. **System Dependencies**:
   - Build tools (gcc, make, cmake)
   - Network libraries (libpcap, libdaq)
   - Required Snort3 dependencies

2. **LibDAQ** (Data Acquisition Library):
   - Latest version from GitHub
   - Compiled and installed from source

3. **Snort3**:
   - Latest stable version
   - Compiled with all features enabled
   - Installed to `/usr/local` by default

4. **Configuration Files**:
   - `/etc/snort/snort.lua` - Main Snort3 configuration
   - IDS/IPS rules and policies

5. **Systemd Service**:
   - `/etc/systemd/system/snort3.service`
   - Automatic startup on boot
   - Restart on failure

6. **Network Persistence**:
   - `/etc/network/if-up.d/snort-network-config`
   - Ensures adapter settings persist

## Post-Installation

### Check Service Status

```bash
sudo systemctl status snort3
```

### View Snort Logs

```bash
sudo tail -f /var/log/snort/alert_fast.txt
```

### Restart Service

```bash
sudo systemctl restart snort3
```

### Stop Service

```bash
sudo systemctl stop snort3
```

### Edit Configuration

```bash
sudo nano /etc/snort/snort.lua
sudo systemctl restart snort3
```

## Container/VM Support

The installer automatically detects if it's running in:
- **Docker/Podman containers**: Checks for `/.dockerenv` or `/run/.containerenv`
- **Virtual Machines**: Uses `systemd-detect-virt`
- **Bare Metal**: Direct hardware installation

### Running in Docker

```bash
docker run -it --privileged --net=host \
  -v $(pwd):/installer \
  ubuntu:22.04 /bin/bash
  
# Inside container
cd /installer
./snort3_installer.py --auto
```

### Running in VirtualBox/VMware

Ensure you have 3 network adapters configured in your VM settings:
1. NAT or Bridged adapter (incoming)
2. Bridged adapter (offload)
3. NAT or Host-only adapter (control)

Then run the installer normally.

## Troubleshooting

### Installation Fails

Check the logs for specific errors. Common issues:
- **Insufficient disk space**: Ensure at least 2GB free
- **Missing dependencies**: Run `sudo apt-get update` first
- **Network issues**: Check internet connectivity

### Service Won't Start

```bash
# Check service logs
sudo journalctl -u snort3 -n 50

# Verify Snort3 installation
/usr/local/bin/snort -V

# Test configuration
/usr/local/bin/snort -c /etc/snort/snort.lua -T
```

### Network Adapters Not Detected

```bash
# List all network interfaces
ip link show

# Check adapter status
ip addr show
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Internet/Network                  │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │ Incoming Port  │ (Onboard Ethernet)
              │   (Monitor)    │ - Promiscuous mode
              └────────┬───────┘ - Packet capture
                       │
                       ▼
              ┌────────────────┐
              │   Snort3 IDS   │
              │   IPS Engine   │ - Analyze traffic
              └────────┬───────┘ - Detect threats
                       │         - Block/Alert
                       ▼
              ┌────────────────┐
              │ Offload Port   │ (USB Ethernet)
              │  (Forward)     │ - Clean traffic
              └────────────────┘
                       
         ┌─────────────────────┐
         │  Control Port       │ (Wireless)
         │  (Management)       │ - SSH access
         └─────────────────────┘ - Configuration
```

## Security Considerations

- Snort3 runs as root (required for packet capture)
- Systemd service has restricted capabilities
- Control adapter should be on a secure management network
- Regular rule updates recommended
- Monitor logs for alerts

## License

See LICENSE file for details.

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

## Support

For issues and questions, please use the GitHub issue tracker.
