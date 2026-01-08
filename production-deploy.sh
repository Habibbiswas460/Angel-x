#!/bin/bash
# Angel-X Production Deployment Script
# Complete deployment with verification

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT="${ENVIRONMENT:-production}"
TRADING_ENABLED="${TRADING_ENABLED:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# ============================================================================
# Pre-flight Checks
# ============================================================================
pre_flight_checks() {
    log_info "Running pre-flight checks..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not installed"
        exit 1
    fi
    log_success "Docker found"
    
    # Check Docker daemon
    if ! docker ps > /dev/null 2>&1; then
        log_error "Docker daemon not running"
        exit 1
    fi
    log_success "Docker daemon running"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose not installed"
        exit 1
    fi
    log_success "Docker Compose found"
    
    # Check config
    if [ ! -f "${PROJECT_DIR}/config/config.py" ]; then
        log_warning "config.py not found, creating from template..."
        cp "${PROJECT_DIR}/config/config.production.py" "${PROJECT_DIR}/config/config.py"
        log_warning "Please update config.py with your production credentials"
    fi
    log_success "Configuration files present"
    
    # Check directories
    mkdir -p "${PROJECT_DIR}/logs" "${PROJECT_DIR}/data" "${PROJECT_DIR}/backups"
    log_success "Directories verified"
}

# ============================================================================
# Build Phase
# ============================================================================
build_phase() {
    log_info "Building Docker image..."
    
    cd "${PROJECT_DIR}"
    
    if docker build -t angel-x:latest -t angel-x:1.0.0 . > /dev/null 2>&1; then
        log_success "Docker image built successfully"
    else
        log_error "Docker build failed"
        exit 1
    fi
}

# ============================================================================
# Deployment Phase
# ============================================================================
deploy_phase() {
    log_info "Starting deployment..."
    
    # Stop existing containers
    if docker ps -a | grep -q "angel-x-trading"; then
        log_info "Stopping existing container..."
        docker stop angel-x-trading 2>/dev/null || true
        docker rm angel-x-trading 2>/dev/null || true
    fi
    
    # Start container
    docker run -d \
        --name angel-x-trading \
        --restart unless-stopped \
        -p 5000:5000 \
        -v "$(pwd)/config/config.py:/app/config/config.py:ro" \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/data:/app/data" \
        -e ENVIRONMENT="${ENVIRONMENT}" \
        -e TRADING_ENABLED="${TRADING_ENABLED}" \
        -e LOG_LEVEL=INFO \
        -e TZ=Asia/Kolkata \
        angel-x:latest
    
    log_success "Container started"
}

# ============================================================================
# Verification Phase
# ============================================================================
verify_phase() {
    log_info "Verifying deployment..."
    
    # Wait for startup
    log_info "Waiting for application startup (40 seconds)..."
    sleep 40
    
    # Check container running
    if ! docker ps | grep -q "angel-x-trading"; then
        log_error "Container not running"
        docker logs angel-x-trading | tail -20
        exit 1
    fi
    log_success "Container running"
    
    # Check health endpoint
    log_info "Checking health endpoint..."
    for i in {1..5}; do
        if curl -sf http://localhost:5000/monitor/health > /dev/null; then
            log_success "Health endpoint responding"
            break
        fi
        if [ $i -eq 5 ]; then
            log_error "Health endpoint not responding"
            exit 1
        fi
        sleep 5
    done
    
    # Display health status
    log_info "System health status:"
    curl -s http://localhost:5000/monitor/health | python3 -m json.tool | sed 's/^/  /'
}

# ============================================================================
# Monitoring Setup
# ============================================================================
setup_monitoring() {
    log_info "Setting up monitoring infrastructure..."
    
    # Start monitoring stack
    if docker-compose --profile monitoring up -d > /dev/null 2>&1; then
        log_success "Monitoring stack started"
        log_info "  Prometheus: http://localhost:9090"
        log_info "  Grafana: http://localhost:3000 (admin/admin)"
    else
        log_warning "Monitoring setup skipped (optional)"
    fi
}

# ============================================================================
# Post-Deployment Summary
# ============================================================================
summary() {
    cat <<EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ DEPLOYMENT COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 DEPLOYMENT SUMMARY:
   Environment:     ${ENVIRONMENT}
   Trading Enabled: ${TRADING_ENABLED}
   Image Version:   1.0.0
   Container:       angel-x-trading
   Status:          Running ✅

🔗 ACCESS POINTS:
   Application:    http://localhost:5000
   Health Check:   http://localhost:5000/monitor/health
   Metrics:        http://localhost:5000/metrics
   Prometheus:     http://localhost:9090
   Grafana:        http://localhost:3000

📝 NEXT STEPS:
   1. Update config.py with your production credentials
   2. Configure database connection
   3. Setup broker authentication
   4. Verify market data feed
   5. Run smoke tests
   6. Monitor system for 24 hours
   7. Enable live trading when ready

⚠️  IMPORTANT:
   • Change Grafana admin password (default: admin/admin)
   • Configure alert notification channels
   • Setup backup schedule
   • Review and adjust alert thresholds
   • Enable live trading only after verification

📋 COMMON COMMANDS:
   View logs:          ./deploy.sh logs
   Health check:       ./deploy.sh health
   Stop container:     ./deploy.sh stop
   View stats:         docker stats angel-x-trading
   Execute command:    docker exec angel-x-trading <command>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
}

# ============================================================================
# Main Execution
# ============================================================================
main() {
    log_info "Starting Angel-X Production Deployment"
    log_info "Environment: ${ENVIRONMENT} | Trading: ${TRADING_ENABLED}"
    echo
    
    pre_flight_checks
    echo
    
    build_phase
    echo
    
    deploy_phase
    echo
    
    verify_phase
    echo
    
    setup_monitoring
    echo
    
    summary
}

# Run main
main
