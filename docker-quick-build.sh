#!/bin/bash
# Quick Docker build script using existing binary

set -e

IMAGE_NAME="teamelitekrb/snort-dev-ml-enhanced:snortDevML"

echo "🐳 Building lightweight ML-Enhanced Snort image..."

# Create a simple Dockerfile that uses the existing installation
cat > Dockerfile.simple << 'EOF'
FROM ubuntu:24.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    libpcap0.8 libluajit-5.1-2 \
    net-tools iproute2 sudo \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir openai requests asyncio aiofiles scikit-learn numpy python-dateutil

# Create directories
RUN mkdir -p /var/log/snort /var/run /etc/snort /app

# Copy application
COPY . /app/
WORKDIR /app

# Install Snort3 using our installer
RUN python3 /app/snort3_installer.py --auto-confirm

# Make scripts executable
RUN chmod +x /app/*.sh /app/*.py

# Copy entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8080
HEALTHCHECK CMD pgrep -f snort || exit 1
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["services"]
EOF

# Build the image
docker build -f Dockerfile.simple -t "${IMAGE_NAME}" .

# Test the image
echo "🧪 Testing the image..."
docker run --rm "${IMAGE_NAME}" bash -c "echo 'Container test successful' && python3 --version"

echo "✅ Build completed successfully!"
echo "Image: ${IMAGE_NAME}"

# Clean up
rm -f Dockerfile.simple