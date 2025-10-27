# Docker Deployment Guide for ML-Enhanced Snort

## 🐳 Quick Start

### Pull and Run (Recommended)
```bash
# Pull the pre-built image
docker pull teamelitekrb/snort-dev-ml-enhanced:snortDevML

# Run with default settings
docker run --privileged --network host \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML

# Run with OpenAI API key
docker run --privileged --network host \
  -e ML_API_KEY="your_openai_api_key_here" \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

### Using Docker Compose (Recommended)
```bash
# Clone the repository
git clone https://github.com/markmonk123/snortMakeShiftInstall.git
cd snortMakeShiftInstall

# Set your API key (optional)
export ML_API_KEY="your_openai_api_key_here"

# Start the services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔧 Available Run Modes

### 1. Full System (Default)
Runs both Snort3 IDS and ML Runner:
```bash
docker run --privileged --network host \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

### 2. Snort3 IDS Only
```bash
docker run --privileged --network host \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML snort-only
```

### 3. ML Runner Only
```bash
docker run --network bridge \
  -v snort_logs:/var/log/snort:ro \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML ml-only
```

### 4. Interactive Shell
```bash
docker run --privileged --network host -it \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML bash
```

## 📁 Volume Mounts

### Log Persistence
```bash
# Mount logs to host
docker run --privileged --network host \
  -v $(pwd)/logs:/var/log/snort \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

### Configuration Files
```bash
# Mount custom Snort config
docker run --privileged --network host \
  -v $(pwd)/my-snort.lua:/usr/local/etc/snort/snort.lua:ro \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML

# Mount custom rules
docker run --privileged --network host \
  -v $(pwd)/my-rules:/usr/local/etc/snort/rules:ro \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

### API Key Configuration
```bash
# Method 1: Environment variable
docker run --privileged --network host \
  -e ML_API_KEY="sk-your-key-here" \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML

# Method 2: Config file mount
docker run --privileged --network host \
  -v $(pwd)/api_config.json:/etc/snort/ml_runner/api_config.json:ro \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

## 🔍 Monitoring & Management

### Check Status
```bash
# Using docker-compose
docker-compose ps
docker-compose logs snort-ml-enhanced

# Using docker directly
docker ps | grep snort
docker logs container_name
```

### Access Logs
```bash
# Real-time log monitoring
docker exec -it container_name tail -f /var/log/snort/alert_fast.txt

# ML Runner logs
docker exec -it container_name tail -f /var/log/snort/ml-runner.log
```

### Service Management
```bash
# Restart services inside container
docker exec -it container_name /app/service_manager.sh restart

# Check service status
docker exec -it container_name /app/service_manager.sh status
```

## 🚀 Production Deployment

### Resource Limits
```bash
docker run --privileged --network host \
  --memory="2g" \
  --cpus="1.5" \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

### Auto-Restart
```bash
docker run --privileged --network host \
  --restart=unless-stopped \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

### Health Checks
The container includes built-in health checks:
```bash
# Check container health
docker inspect container_name | jq '.[0].State.Health'
```

## 🔒 Security Considerations

### Network Requirements
- **Privileged Mode**: Required for packet capture
- **Host Networking**: Recommended for direct interface access
- **Interface Access**: Ensure eth0 (or target interface) is available

### API Key Security
```bash
# Use Docker secrets (recommended)
echo "your_api_key" | docker secret create openai_key -
docker run --privileged --network host \
  --secret openai_key \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML

# Or use environment file
echo "ML_API_KEY=your_key_here" > .env
docker run --privileged --network host \
  --env-file .env \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

## 🐛 Troubleshooting

### Common Issues

**Container exits immediately:**
```bash
# Check if interface exists
docker run --privileged --network host -it \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML bash
ip link show
```

**Permission denied:**
```bash
# Ensure privileged mode
docker run --privileged --network host \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

**Snort3 configuration errors:**
```bash
# Test configuration
docker exec -it container_name \
  snort -T -c /usr/local/etc/snort/snort.lua
```

### Debug Mode
```bash
# Run with verbose logging
docker run --privileged --network host \
  -e PYTHONUNBUFFERED=1 \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

## 📊 Performance Tuning

### CPU and Memory
```bash
# High-performance setup
docker run --privileged --network host \
  --memory="4g" \
  --cpus="2.0" \
  --ulimit nofile=65536:65536 \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

### Storage Optimization
```bash
# Use tmpfs for high-speed logs (loses data on restart)
docker run --privileged --network host \
  --tmpfs /var/log/snort:size=1G \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

## 🔗 Integration Examples

### With ELK Stack
```bash
# Forward logs to Elasticsearch
docker run --privileged --network host \
  -v elk-config:/etc/filebeat \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

### With Prometheus Monitoring
```bash
# Expose metrics (if monitoring is added)
docker run --privileged --network host \
  -p 9090:9090 \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

## 📋 Build Information

- **Base Image**: Ubuntu 24.04 LTS
- **Snort Version**: 3.1.75.0
- **LibDAQ Version**: 3.0.13
- **Python Version**: 3.x with ML libraries
- **Image Size**: ~800MB (approximate)
- **Architecture**: x86_64

## 🔗 Links

- **Docker Hub**: https://hub.docker.com/r/teamelitekrb/snort-dev-ml-enhanced
- **GitHub Repository**: https://github.com/markmonk123/snortMakeShiftInstall
- **Snort Documentation**: https://docs.snort.org/