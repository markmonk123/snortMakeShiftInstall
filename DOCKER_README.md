# 🐳 Docker Setup for ML-Enhanced Snort3

This directory contains everything needed to build and deploy the ML-Enhanced Snort3 system as a Docker container.

## 📁 Files Overview

- `Dockerfile.clean` - Production-ready Dockerfile for building the container
- `docker-entrypoint.sh` - Container entry point script
- `docker-compose.yml` - Docker Compose configuration for easy deployment
- `docker-build.sh` - Automated build and push script
- `.dockerignore` - Files to exclude from Docker build context
- `DOCKER_DEPLOYMENT.md` - Comprehensive deployment guide

## 🚀 Quick Start

### Option 1: Pull from Docker Hub (Recommended)
```bash
docker pull teamelitekrb/snort-dev-ml-enhanced:snortDevML
docker run --privileged --network host teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

### Option 2: Build Locally
```bash
# Build the image
./docker-build.sh build

# Or use docker-compose
docker-compose build
docker-compose up -d
```

### Option 3: One-Command Deploy
```bash
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables
- `ML_API_KEY` - OpenAI API key for ML analysis
- `SNORT_INTERFACE` - Network interface to monitor (default: eth0)
- `PYTHONUNBUFFERED=1` - Enable real-time Python logging

### Volume Mounts
- `/var/log/snort` - Snort logs and alerts
- `/etc/snort/ml_runner/api_config.json` - API configuration file
- `/usr/local/etc/snort/snort.lua` - Main Snort configuration
- `/usr/local/etc/snort/rules/` - Snort rules directory

## 🏗️ Build Information

### Docker Image Details
- **Base Image**: Ubuntu 24.04 LTS
- **Snort Version**: 3.1.75.0 (built from source)
- **Python**: 3.x with ML libraries (OpenAI, scikit-learn, numpy, etc.)
- **Size**: ~800MB (approximate)
- **Architecture**: x86_64

### Build Process
1. **Base Setup**: Ubuntu 24.04 with system dependencies
2. **Snort3 Installation**: Uses `snort3_installer.py` to build from source
3. **ML Dependencies**: Installs Python packages for AI analysis
4. **Configuration**: Copies example configs and sets up directories
5. **Permissions**: Sets proper security permissions
6. **Entrypoint**: Configures startup script for container environment

## 🎯 Run Modes

The container supports multiple run modes:

```bash
# Full system (default)
docker run --privileged --network host teamelitekrb/snort-dev-ml-enhanced:snortDevML

# Snort3 IDS only
docker run --privileged --network host teamelitekrb/snort-dev-ml-enhanced:snortDevML snort-only

# ML Runner only
docker run teamelitekrb/snort-dev-ml-enhanced:snortDevML ml-only

# Interactive shell
docker run --privileged --network host -it teamelitekrb/snort-dev-ml-enhanced:snortDevML bash

# System test
docker run teamelitekrb/snort-dev-ml-enhanced:snortDevML test
```

## 🔒 Security Requirements

### Privileged Mode
Required for packet capture and network monitoring:
```bash
docker run --privileged --network host ...
```

### Network Access
- **Host networking** recommended for direct interface access
- **Bridge networking** possible but may require additional configuration

### API Key Security
```bash
# Environment variable (temporary)
docker run -e ML_API_KEY="sk-your-key" ...

# Config file mount (recommended)
docker run -v ./api_config.json:/etc/snort/ml_runner/api_config.json:ro ...

# Docker secrets (production)
echo "your_key" | docker secret create openai_key -
docker run --secret openai_key ...
```

## 📊 Monitoring

### Health Checks
The container includes built-in health monitoring:
```bash
docker inspect container_name | jq '.[0].State.Health'
```

### Logs
```bash
# Container logs
docker logs -f container_name

# Snort alerts
docker exec container_name tail -f /var/log/snort/alert_fast.txt

# ML Runner logs
docker exec container_name tail -f /var/log/snort/ml-runner.log
```

### Service Management
```bash
# Check service status
docker exec container_name /app/service_manager.sh status

# Restart services
docker exec container_name /app/service_manager.sh restart
```

## 🚀 Production Deployment

### Resource Limits
```bash
docker run --privileged --network host \
  --memory="2g" --cpus="1.5" \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

### Auto-Restart
```bash
docker run --privileged --network host \
  --restart=unless-stopped \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML
```

### Docker Compose Production
```yaml
version: '3.8'
services:
  snort-ml:
    image: teamelitekrb/snort-dev-ml-enhanced:snortDevML
    privileged: true
    network_mode: host
    restart: unless-stopped
    environment:
      - ML_API_KEY=${ML_API_KEY}
    volumes:
      - snort-logs:/var/log/snort
      - ./config:/etc/snort/ml_runner:ro
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.5'
volumes:
  snort-logs:
```

## 🛠️ Development

### Building Custom Images
```bash
# Build with custom tag
docker build -f Dockerfile.clean -t my-snort:latest .

# Build with build args
docker build -f Dockerfile.clean \
  --build-arg SNORT_VERSION=3.1.75.0 \
  -t my-snort:latest .
```

### Debugging
```bash
# Run with debug output
docker run --privileged --network host \
  -e PYTHONUNBUFFERED=1 \
  teamelitekrb/snort-dev-ml-enhanced:snortDevML

# Access container shell
docker exec -it container_name bash
```

## 📋 Troubleshooting

### Common Issues

**Container exits immediately:**
- Check network interface availability
- Ensure privileged mode is enabled
- Verify Snort configuration

**Permission denied errors:**
- Confirm privileged mode: `--privileged`
- Check volume mount permissions

**Network interface not found:**
- List available interfaces: `docker exec container_name ip link show`
- Set custom interface: `-e SNORT_INTERFACE=your_interface`

**ML analysis not working:**
- Verify API key: `docker exec container_name env | grep ML_API_KEY`
- Check logs: `docker exec container_name tail -f /var/log/snort/ml-runner.log`

### Support Commands
```bash
# System information
docker exec container_name /app/demo_openai_setup.sh

# Configuration test
docker exec container_name python3 /app/main.py --test-config

# Manual service management
docker exec container_name /app/service_manager.sh status
```

## 🔗 Links

- **Docker Hub**: https://hub.docker.com/r/teamelitekrb/snort-dev-ml-enhanced
- **Full Deployment Guide**: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- **GitHub Repository**: https://github.com/markmonk123/snortMakeShiftInstall