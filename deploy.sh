#!/bin/bash
# Angel-X Docker Deployment Script
# Usage: ./deploy.sh [build|run|stop|logs|health]

set -e

PROJECT_NAME="angel-x"
IMAGE_NAME="angel-x"
VERSION="1.0.0"
CONTAINER_NAME="angel-x-trading"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        echo ""
        echo "Install Docker with one of these commands:"
        echo "  sudo apt install docker.io"
        echo "  sudo snap install docker"
        echo ""
        exit 1
    fi
    echo -e "${GREEN}✅ Docker found${NC}"
}

# Build Docker image
build_image() {
    echo -e "${YELLOW}🏗️  Building ${IMAGE_NAME}:${VERSION}...${NC}"
    docker build -t ${IMAGE_NAME}:${VERSION} -t ${IMAGE_NAME}:latest .
    echo -e "${GREEN}✅ Build complete${NC}"
    docker images | grep ${IMAGE_NAME}
}

# Run container
run_container() {
    echo -e "${YELLOW}🚀 Starting ${CONTAINER_NAME}...${NC}"
    
    # Create necessary directories
    mkdir -p logs data
    
    # Stop existing container if running
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
    
    # Run new container
    docker run -d \
        --name ${CONTAINER_NAME} \
        --restart unless-stopped \
        -p 5000:5000 \
        -v $(pwd)/config/config.py:/app/config/config.py:ro \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd)/data:/app/data \
        -e ENVIRONMENT=production \
        -e TRADING_ENABLED=false \
        -e LOG_LEVEL=INFO \
        -e TZ=Asia/Kolkata \
        ${IMAGE_NAME}:${VERSION}
    
    echo -e "${GREEN}✅ Container started${NC}"
    echo ""
    echo "Container ID: $(docker ps -q -f name=${CONTAINER_NAME})"
    echo "API URL: http://localhost:5000"
}

# Stop container
stop_container() {
    echo -e "${YELLOW}🛑 Stopping ${CONTAINER_NAME}...${NC}"
    docker stop ${CONTAINER_NAME}
    docker rm ${CONTAINER_NAME}
    echo -e "${GREEN}✅ Container stopped and removed${NC}"
}

# Show logs
show_logs() {
    echo -e "${YELLOW}📋 Showing logs for ${CONTAINER_NAME}...${NC}"
    docker logs -f ${CONTAINER_NAME}
}

# Health check
health_check() {
    echo -e "${YELLOW}🏥 Checking health of ${CONTAINER_NAME}...${NC}"
    
    # Check if container is running
    if ! docker ps | grep -q ${CONTAINER_NAME}; then
        echo -e "${RED}❌ Container not running${NC}"
        exit 1
    fi
    
    # Check health endpoint
    if curl -sf http://localhost:5000/health > /dev/null; then
        echo -e "${GREEN}✅ Container is healthy${NC}"
        echo ""
        curl -s http://localhost:5000/health | python -m json.tool 2>/dev/null || curl -s http://localhost:5000/health
    else
        echo -e "${RED}❌ Health check failed${NC}"
        exit 1
    fi
}

# Main script
case "$1" in
    build)
        check_docker
        build_image
        ;;
    run)
        check_docker
        run_container
        sleep 5
        health_check
        ;;
    stop)
        check_docker
        stop_container
        ;;
    logs)
        check_docker
        show_logs
        ;;
    health)
        health_check
        ;;
    *)
        echo "Angel-X Docker Deployment Script"
        echo ""
        echo "Usage: $0 {build|run|stop|logs|health}"
        echo ""
        echo "Commands:"
        echo "  build   - Build Docker image"
        echo "  run     - Run container (builds if needed)"
        echo "  stop    - Stop and remove container"
        echo "  logs    - Show container logs"
        echo "  health  - Check container health"
        echo ""
        exit 1
        ;;
esac
