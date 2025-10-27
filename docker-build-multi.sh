#!/bin/bash
# Enhanced Docker Build Script with Multiple OS Options

set -e

# Configuration
DOCKER_USERNAME="teamelitekrb"
IMAGE_NAME="snort-dev-ml-enhanced"
TAG="snortDevML"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Available Dockerfile options
declare -A DOCKERFILES=(
    ["ubuntu22"]="Dockerfile.ubuntu22"
    ["python39"]="Dockerfile.python39" 
    ["clean"]="Dockerfile.clean"
)

show_options() {
    echo "🐳 ML-Enhanced Snort Docker Build Options"
    echo "========================================="
    echo ""
    echo "Available Dockerfile options:"
    echo "  ubuntu22  - Ubuntu 22.04 LTS (Recommended - stable, fewer restrictions)"
    echo "  python39  - Python 3.9 on Debian Bullseye (Pure Python environment)"
    echo "  clean     - Ubuntu 24.04 (Latest, may have package restrictions)"
    echo ""
    echo "Usage: $0 <option> <command>"
    echo "Examples:"
    echo "  $0 ubuntu22 build    # Build with Ubuntu 22.04"
    echo "  $0 python39 build    # Build with Python 3.9"
    echo "  $0 ubuntu22 push     # Build and push Ubuntu 22.04 version"
    echo ""
}

build_image() {
    local dockerfile_key="$1"
    local dockerfile="${DOCKERFILES[$dockerfile_key]}"
    local image_tag="${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}-${dockerfile_key}"
    
    if [ ! -f "$dockerfile" ]; then
        log_error "Dockerfile not found: $dockerfile"
        exit 1
    fi
    
    log_info "Building with $dockerfile -> $image_tag"
    
    docker build \
        -f "$dockerfile" \
        --tag "$image_tag" \
        --tag "${DOCKER_USERNAME}/${IMAGE_NAME}:latest-${dockerfile_key}" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        .
    
    if [ $? -eq 0 ]; then
        log_success "Build completed: $image_tag"
        return 0
    else
        log_error "Build failed for $dockerfile_key"
        return 1
    fi
}

test_image() {
    local dockerfile_key="$1"
    local image_tag="${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}-${dockerfile_key}"
    
    log_info "Testing image: $image_tag"
    
    # Basic functionality test
    docker run --rm "$image_tag" bash -c "echo 'Container test: OK' && python3 --version"
    
    # Test Python packages
    docker run --rm "$image_tag" bash -c "python3 -c 'import openai, sklearn, numpy; print(\"Python packages: OK\")'"
    
    log_success "Image tests passed"
}

push_image() {
    local dockerfile_key="$1"
    local image_tag="${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}-${dockerfile_key}"
    
    log_info "Pushing image: $image_tag"
    
    docker push "$image_tag"
    docker push "${DOCKER_USERNAME}/${IMAGE_NAME}:latest-${dockerfile_key}"
    
    log_success "Image pushed successfully"
}

build_all() {
    log_info "Building all Docker variants..."
    
    for key in "${!DOCKERFILES[@]}"; do
        log_info "Building $key variant..."
        build_image "$key" || log_warning "Failed to build $key variant"
    done
    
    log_success "All builds completed"
}

main() {
    if [ $# -eq 0 ]; then
        show_options
        exit 1
    fi
    
    local dockerfile_key="$1"
    local command="${2:-build}"
    
    # Handle special commands
    case "$dockerfile_key" in
        "help"|"-h"|"--help")
            show_options
            exit 0
            ;;
        "all")
            case "$command" in
                "build") build_all ;;
                *) log_error "Only 'build' command supported for 'all'"; exit 1 ;;
            esac
            exit 0
            ;;
    esac
    
    # Validate dockerfile option
    if [[ ! "${!DOCKERFILES[@]}" =~ "$dockerfile_key" ]]; then
        log_error "Invalid dockerfile option: $dockerfile_key"
        show_options
        exit 1
    fi
    
    # Execute command
    case "$command" in
        "build")
            build_image "$dockerfile_key"
            ;;
        "test")
            test_image "$dockerfile_key"
            ;;
        "push")
            build_image "$dockerfile_key" && push_image "$dockerfile_key"
            ;;
        "build-test")
            build_image "$dockerfile_key" && test_image "$dockerfile_key"
            ;;
        "all")
            build_image "$dockerfile_key" && test_image "$dockerfile_key" && push_image "$dockerfile_key"
            ;;
        *)
            log_error "Unknown command: $command"
            echo "Available commands: build, test, push, build-test, all"
            exit 1
            ;;
    esac
}

main "$@"