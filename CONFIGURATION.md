# Snort3 IDS/IPS Configuration Examples

This directory contains example configurations and deployment scenarios for Snort3.

## Basic IDS Configuration

The installer creates a basic IDS/IPS configuration at `/etc/snort/snort.lua` with:

- Network address definitions (HOME_NET, EXTERNAL_NET)
- Detection engine with built-in rules
- DAQ configuration for packet capture
- Stream processing for TCP/UDP/ICMP
- Active responses for IPS mode
- Protocol-specific inspection (HTTP, etc.)
- Logging configuration

## Network Adapter Examples

### Example 1: Physical Server with 3 NICs

```bash
# List adapters
ip link show

# Example output:
# eth0 - Onboard ethernet (incoming)
# eth1 - USB ethernet adapter (offload)
# wlan0 - Wireless adapter (control)

sudo ./snort3_installer.py --incoming eth0 --offload eth1 --control wlan0
```

### Example 2: Auto-Detection

```bash
# Let the installer detect and assign adapters automatically
sudo ./snort3_installer.py --auto
```

### Example 3: Virtual Machine

```bash
# VM with 3 virtual adapters
# enp0s3 - NAT adapter (incoming)
# enp0s8 - Bridged adapter (offload)
# enp0s9 - Host-only adapter (control)

sudo ./snort3_installer.py --incoming enp0s3 --offload enp0s8 --control enp0s9
```

## Container Deployment

### Docker Example

```bash
# Create a privileged container with network access
docker run -it --privileged --net=host \
  -v $(pwd):/installer \
  -v /var/log/snort:/var/log/snort \
  ubuntu:22.04 /bin/bash

# Inside container
cd /installer
apt-get update
apt-get install -y python3 iproute2
./snort3_installer.py --auto
```

### Docker Compose Example

```yaml
version: '3.8'
services:
  snort3:
    image: ubuntu:22.04
    privileged: true
    network_mode: host
    volumes:
      - ./:/installer
      - snort-logs:/var/log/snort
      - snort-config:/etc/snort
    command: >
      bash -c "
        apt-get update &&
        apt-get install -y python3 iproute2 &&
        cd /installer &&
        ./snort3_installer.py --auto &&
        tail -f /var/log/snort/alert_fast.txt
      "
volumes:
  snort-logs:
  snort-config:
```

## IDS vs IPS Mode

### IDS Mode (Default)
- Monitors traffic passively
- Generates alerts
- Does not block traffic
- Lower performance impact

### IPS Mode (Inline)
- Actively inspects traffic
- Can block malicious traffic
- Forwards clean traffic to offload adapter
- Higher performance requirements

The installer configures for inline IPS mode by default with the offload adapter for forwarding.

## Custom Rules

To add custom rules, edit `/etc/snort/snort.lua` and add rule files:

```lua
ips = {
    enable_builtin_rules = true,
    include = '/etc/snort/rules/local.rules',
    variables = default_variables
}
```

Create `/etc/snort/rules/local.rules`:

```
alert tcp any any -> $HOME_NET 22 (msg:"SSH Connection Attempt"; sid:1000001; rev:1;)
alert tcp any any -> $HOME_NET 80 (msg:"HTTP Traffic"; sid:1000002; rev:1;)
```

Restart Snort3:
```bash
sudo systemctl restart snort3
```

## Performance Tuning

### High Traffic Networks

For high-throughput networks, adjust the DAQ configuration:

```lua
daq = {
    inputs = { 'eth0' },
    module_dirs = { '/usr/local/lib/daq' },
    modules = {
        {
            name = 'afpacket',
            mode = 'inline',
            variables = {
                buffer_size_mb = 128,
                fanout_type = 'hash',
                fanout_flag = 'rollover'
            }
        }
    }
}
```

### CPU Affinity

Pin Snort3 to specific CPU cores for better performance:

```bash
# Edit /etc/systemd/system/snort3.service
[Service]
CPUAffinity=0-3
```

## Monitoring and Alerts

### Real-time Alert Monitoring

```bash
# Watch alerts in real-time
tail -f /var/log/snort/alert_fast.txt

# Search for specific alerts
grep "CRITICAL" /var/log/snort/alert_fast.txt
```

### Integration with SIEM

Forward Snort alerts to a SIEM system:

```bash
# Example: Forward to syslog
alert_syslog = {
    level = 'info',
    facility = 'local7'
}
```

## Troubleshooting

### Check Adapter Configuration

```bash
# Verify promiscuous mode
ip link show eth0 | grep PROMISC

# Check if adapter is up
ip addr show eth0

# Test packet capture
tcpdump -i eth0 -c 10
```

### Verify Snort3 Configuration

```bash
# Test configuration syntax
/usr/local/bin/snort -c /etc/snort/snort.lua -T

# Run in verbose mode
/usr/local/bin/snort -c /etc/snort/snort.lua -i eth0 -A console -v
```

### Service Issues

```bash
# Check service status
systemctl status snort3

# View service logs
journalctl -u snort3 -f

# Restart service
systemctl restart snort3
```

## Security Best Practices

1. **Isolate Control Network**: Keep the wireless control adapter on a separate, secure network
2. **Regular Updates**: Update Snort rules regularly
3. **Monitor Logs**: Set up automated log monitoring and alerting
4. **Backup Configuration**: Keep backups of `/etc/snort/` configuration
5. **Rate Limiting**: Configure rate limiting on the incoming adapter to prevent DoS
6. **Access Control**: Restrict SSH access to the control adapter only

## Additional Resources

- Snort3 Official Documentation: https://www.snort.org/snort3
- Community Rules: https://www.snort.org/downloads
- LibDAQ Documentation: https://github.com/snort3/libdaq
