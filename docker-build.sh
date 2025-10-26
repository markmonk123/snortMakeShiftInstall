#!/bin/bash
# Build and Push Script for ML-Enhanced Snort Docker Image

set -e

# Configuration
DOCKER_REGISTRY="docker.io"
DOCKER_USERNAME="teamelitekrb"
IMAGE_NAME="snort-dev-ml-enhanced"
TAG="snortDevML"
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed and running
check_docker() {
    log_info "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    log_success "Docker is ready"
}

# Build the Docker image
build_image() {
    log_info "Building Docker image: ${FULL_IMAGE_NAME}"
    
    # Use the clean Dockerfile
    DOCKERFILE_NAME="Dockerfile.clean"
    if [ ! -f "$DOCKERFILE_NAME" ]; then
        log_error "$DOCKERFILE_NAME not found in current directory"
        exit 1
    fi
    
    # Build the image
    docker build \
        -f "$DOCKERFILE_NAME" \
        --tag "${FULL_IMAGE_NAME}" \
        --tag "${DOCKER_USERNAME}/${IMAGE_NAME}:latest" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        .
    
    if [ $? -eq 0 ]; then
        log_success "Docker image built successfully"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Test the Docker image
test_image() {
    log_info "Testing Docker image..."
    
    # Test basic functionality
    log_info "Testing image startup..."
    docker run --rm "${FULL_IMAGE_NAME}" bash -c "echo 'Container test successful'"
    
    # Test Snort3 installation
    log_info "Testing Snort3 installation..."
    docker run --rm "${FULL_IMAGE_NAME}" bash -c "snort --version"
    
    # Test Python dependencies
    log_info "Testing Python dependencies..."
    docker run --rm "${FULL_IMAGE_NAME}" bash -c "python3 -c 'import asyncio, json, sys; print(\"Python environment OK\")'  "
    
    log_success "All tests passed"
}

# Push to Docker Hub
push_image() {
    log_info "Pushing Docker image to Docker Hub..."
    
    # Check if logged in to Docker Hub
    if ! docker info | grep -q "Username:"; then
        log_warning "Not logged in to Docker Hub. Please login first:"
        docker login
    fi
    
    # Push both tags
    log_info "Pushing ${FULL_IMAGE_NAME}..."
    docker push "${FULL_IMAGE_NAME}"
    
    log_info "Pushing ${DOCKER_USERNAME}/${IMAGE_NAME}:latest..."
    docker push "${DOCKER_USERNAME}/${IMAGE_NAME}:latest"
    
    log_success "Image pushed successfully to Docker Hub"
}

# Show image information
show_info() {
    log_info "Docker Image Information:"
    echo "=========================="
    echo "Repository: ${DOCKER_USERNAME}/${IMAGE_NAME}"
    echo "Tag: ${TAG}"
    echo "Full Name: ${FULL_IMAGE_NAME}"
    echo "Size: $(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep "${IMAGE_NAME}" | grep "${TAG}" | awk '{print $3}')"
    echo ""
    echo "Usage Commands:"
    echo "==============="
    echo "# Run full ML-Enhanced Snort system:"
    echo "docker run --privileged --network host ${FULL_IMAGE_NAME}"
    echo ""
    echo "# Run with API key:"
    echo "docker run --privileged --network host -e ML_API_KEY=your_key_here ${FULL_IMAGE_NAME}"
    echo ""
    echo "# Run interactive shell:"
    echo "docker run --privileged --network host -it ${FULL_IMAGE_NAME} bash"
    echo ""
    echo "# Using docker-compose:"
    echo "docker-compose up -d"
    echo ""
    echo "Docker Hub URL: https://hub.docker.com/r/${DOCKER_USERNAME}/${IMAGE_NAME}"
}

# Main execution
main() {
    echo "🐳 ML-Enhanced Snort Docker Build & Push"
    echo "========================================"
    
    check_docker
    
    case "${1:-all}" in
        "build")
            build_image
            test_image
            show_info
            ;;
        "test")
            test_image
            ;;
        "push")
            push_image
            show_info
            ;;
        "all"|"")
            build_image
            test_image
            push_image
            show_info
            ;;
        "info")
            show_info
            ;;
        *)
            echo "Usage: $0 {all|build|test|push|info}"
            echo ""
            echo "Commands:"
            echo "  all   - Build, test, and push (default)"
            echo "  build - Build the Docker image only"
            echo "  test  - Test the built image"
            echo "  push  - Push to Docker Hub"
            echo "  info  - Show image information"
            exit 1
            ;;
    esac
}

# Run the script
main "$@"