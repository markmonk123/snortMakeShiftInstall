# ML-Enhanced Snort Service Management

## Overview
This document explains how to manage the ML-Enhanced Snort Runner services in both container and systemd environments.

## 🐳 Container Environment (Current)

Since we're in a container without systemd, use the service manager script:

### Service Commands
```bash
# Start both services
sudo ./service_manager.sh start

# Stop both services  
sudo ./service_manager.sh stop

# Restart both services
sudo ./service_manager.sh restart

# Check service status
sudo ./service_manager.sh status

# View recent logs
sudo ./service_manager.sh logs
```

### Current Status
✅ **Both services are running:**
- **Snort3 IDS/IPS**: Multiple instances monitoring network traffic
- **ML Runner**: Analyzing alerts with AI, generating rules when confidence ≥98%

### Auto-Start
To auto-start services when container starts:
```bash
./autostart_services.sh
```

---

## 🖥️ Full Linux System with systemd

For deployment on a real Linux system with systemd:

### Setup
```bash
# Run the systemd setup script (as root)
sudo ./setup_systemd_services.sh
```

### Service Files Created
- `/etc/systemd/system/snort3.service` - Snort3 IDS/IPS daemon
- `/etc/systemd/system/snort-ml-runner.service` - ML analysis service

### systemd Commands
```bash
# Start services
sudo systemctl start snort3 snort-ml-runner

# Stop services
sudo systemctl stop snort3 snort-ml-runner

# Restart services
sudo systemctl restart snort3 snort-ml-runner

# Check status
sudo systemctl status snort3 snort-ml-runner

# Enable auto-start on boot
sudo systemctl enable snort3 snort-ml-runner

# Disable auto-start
sudo systemctl disable snort3 snort-ml-runner

# View logs
sudo journalctl -u snort3 -u snort-ml-runner -f
```

---

## 📊 Monitoring & Logs

### Log Locations
- **Snort3 Alerts**: `/var/log/snort/alert_fast.txt`
- **ML Runner Logs**: `/var/log/snort/ml-runner.log`
- **Generated Rules**: `/usr/local/etc/snort/rules/ml_generated.rules`

### Process Information
- **Snort3 PIDs**: `/var/run/snort3.pid`
- **ML Runner PID**: `/var/run/snort-ml-runner.pid`

### Health Checks
```bash
# Check if processes are running
pgrep -f snort
pgrep -f "python3.*main.py"

# Monitor alert generation
tail -f /var/log/snort/alert_fast.txt

# Monitor ML analysis
tail -f /var/log/snort/ml-runner.log
```

---

## ⚙️ Configuration

### ML Runner Configuration
Edit `/workspaces/snortMakeShiftInstall/ml_runner/config.py` or use config files:
- `/etc/snort/ml_runner/api_config.json`
- `./ml_runner_config.json`

### Snort3 Configuration
Main config: `/usr/local/etc/snort/snort.lua`

### API Key Setup
```bash
# Interactive setup
sudo ./setup_openai_api.sh

# Check configuration
sudo python3 main.py --test-config --model openai
```

---

## 🔧 Troubleshooting

### Service Won't Start
1. Check configuration: `sudo snort -T -c /usr/local/etc/snort/snort.lua`
2. Check permissions on log directories
3. Verify network interface exists: `ip link show`

### ML Runner Issues
1. Check API key configuration
2. Verify Python dependencies: `pip3 list | grep -E "(openai|requests|asyncio)"`
3. Check log file permissions

### Performance Issues
1. Monitor CPU/memory usage: `top -p $(pgrep snort)`
2. Check disk space: `df -h /var/log/snort`
3. Review alert volume: `wc -l /var/log/snort/alert_fast.txt`

---

## 🚀 Production Deployment

### Security Considerations
- Run services with minimal privileges
- Secure API key storage (600 permissions)
- Regular log rotation
- Monitor resource usage
- Implement backup strategies for rules

### High Availability
- Consider multiple Snort3 instances
- Load balance ML analysis
- Implement health checks
- Set up alerting for service failures

### Maintenance
- Regular rule updates
- ML model retraining
- Log cleanup and archival
- Performance tuning based on traffic patterns

---

## 📈 Current System Status

**Services**: ✅ Running  
**Snort3**: ✅ Multiple instances active  
**ML Runner**: ✅ Processing alerts  
**Rule Generation**: ✅ Configured (confidence ≥98%)  
**Persistence**: ✅ Container service manager ready  
**Systemd**: ✅ Service files created for real systems  

The ML-Enhanced Snort Runner is fully operational and persistent!