# Docker Deployment Guide - Angel-X Trading System

## 📋 Overview

This guide covers Docker-based deployment of the Angel-X options trading system using containerization for production environments.

## 🏗️ Architecture

### Multi-Stage Build
- **Stage 1 (Builder)**: Compiles dependencies with build tools
- **Stage 2 (Runtime)**: Minimal production image with only runtime dependencies

### Key Features
✅ Multi-stage build for minimal image size
✅ Non-root user for security (angelx:1000)
✅ Health checks for container orchestration
✅ Volume mounts for config, logs, and data
✅ Indian timezone (Asia/Kolkata)
✅ Production-ready configurations

## 📦 Files Created

```
Angel-x/
├── Dockerfile              # Multi-stage production Dockerfile
├── .dockerignore          # Files excluded from Docker build
├── docker-compose.yml     # Complete stack with PostgreSQL, Prometheus, Grafana
└── deploy.sh              # Deployment automation script
```

## 🚀 Quick Start

### Prerequisites

**Install Docker:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group (logout/login required)
sudo usermod -aG docker $USER
```

### Build Image

```bash
# Build with version tag
docker build -t angel-x:1.0.0 -t angel-x:latest .

# Verify image
docker images | grep angel-x
```

### Run Container

**Option 1: Using deploy script (recommended)**
```bash
# Make executable
chmod +x deploy.sh

# Build and run
./deploy.sh build
./deploy.sh run

# Check health
./deploy.sh health

# View logs
./deploy.sh logs

# Stop container
./deploy.sh stop
```

**Option 2: Docker run command**
```bash
# Create directories
mkdir -p logs data

# Ensure config.py exists
cp config/config.example.py config/config.py
# Edit config/config.py with your credentials

# Run container
docker run -d \
  --name angel-x-trading \
  --restart unless-stopped \
  -p 5000:5000 \
  -v $(pwd)/config/config.py:/app/config/config.py:ro \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  -e ENVIRONMENT=production \
  -e TRADING_ENABLED=false \
  -e LOG_LEVEL=INFO \
  -e TZ=Asia/Kolkata \
  angel-x:latest
```

**Option 3: Docker Compose (full stack)**
```bash
# Run complete stack (app + PostgreSQL)
docker-compose up -d

# Run with monitoring (app + PostgreSQL + Prometheus + Grafana)
docker-compose --profile monitoring up -d

# View logs
docker-compose logs -f angel-x

# Stop all services
docker-compose down
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | production | Environment mode |
| `TRADING_ENABLED` | false | Enable live trading |
| `LOG_LEVEL` | INFO | Logging verbosity |
| `TZ` | Asia/Kolkata | Container timezone |
| `POSTGRES_PASSWORD` | angelx_secure_password | PostgreSQL password |
| `GRAFANA_PASSWORD` | admin | Grafana admin password |

### Volume Mounts

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./config/config.py` | `/app/config/config.py` | Configuration (read-only) |
| `./logs` | `/app/logs` | Application logs |
| `./data` | `/app/data` | Persistent data storage |

### Exposed Ports

| Port | Service | Description |
|------|---------|-------------|
| 5000 | Angel-X API | Main application API |
| 5432 | PostgreSQL | Database (optional) |
| 9090 | Prometheus | Metrics (monitoring profile) |
| 3000 | Grafana | Dashboards (monitoring profile) |

## 🏥 Health Monitoring

### Container Health Check
```bash
# Manual health check
curl http://localhost:5000/health

# Docker health status
docker ps --format "table {{.Names}}\t{{.Status}}"

# Using deploy script
./deploy.sh health
```

### Health Endpoint Response
```json
{
  "status": "healthy",
  "timestamp": "2026-01-08T10:30:00+05:30",
  "version": "1.0.0",
  "environment": "production"
}
```

## 📊 Container Management

### View Logs
```bash
# All logs
docker logs angel-x-trading

# Follow logs (real-time)
docker logs -f angel-x-trading

# Last 100 lines
docker logs --tail 100 angel-x-trading

# With timestamps
docker logs -t angel-x-trading
```

### Container Stats
```bash
# Resource usage
docker stats angel-x-trading

# Detailed inspection
docker inspect angel-x-trading
```

### Execute Commands
```bash
# Interactive shell
docker exec -it angel-x-trading bash

# Run Python script
docker exec angel-x-trading python scripts/test_credentials.py

# Check Python packages
docker exec angel-x-trading pip list
```

## 🔒 Security Best Practices

### Implemented Security Features
✅ Non-root user execution (angelx:1000)
✅ Read-only config mount
✅ Minimal base image (python:3.12-slim)
✅ No build tools in production image
✅ .dockerignore to exclude sensitive files
✅ Health checks for container orchestration
✅ Explicit version pinning in requirements.txt

### Additional Security Steps
1. **Secure config.py**: Never commit credentials to git
2. **Use secrets**: Consider Docker secrets for production
3. **Network isolation**: Use Docker networks for service communication
4. **Resource limits**: Add CPU/memory limits in production
5. **Image scanning**: Scan for vulnerabilities regularly

## 🎯 Production Deployment

### Pre-deployment Checklist
- [ ] Docker installed and running
- [ ] config.py configured with production credentials
- [ ] TRADING_ENABLED set appropriately
- [ ] PostgreSQL database running (if using ML features)
- [ ] Firewall rules configured for port 5000
- [ ] SSL/TLS configured (reverse proxy)
- [ ] Monitoring setup (Prometheus/Grafana)
- [ ] Log rotation configured
- [ ] Backup strategy in place

### Resource Recommendations
```yaml
# Add to docker-compose.yml or docker run command
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

### Auto-restart Configuration
```bash
# Container restarts automatically on failure
docker update --restart=unless-stopped angel-x-trading
```

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check logs for errors
docker logs angel-x-trading

# Verify config.py exists and is valid
docker run --rm -v $(pwd)/config:/app/config angel-x:latest python -c "import config.config"
```

### Health Check Failing
```bash
# Check application logs
docker logs angel-x-trading | grep ERROR

# Check port binding
netstat -tulpn | grep 5000

# Test health endpoint manually
docker exec angel-x-trading curl -f http://localhost:5000/health
```

### Permission Issues
```bash
# Ensure directories have correct permissions
chmod 755 logs data
chown -R 1000:1000 logs data
```

### Build Failures
```bash
# Clean build cache
docker builder prune

# Rebuild without cache
docker build --no-cache -t angel-x:latest .

# Check .dockerignore is not excluding required files
cat .dockerignore
```

## 📈 Scaling and Orchestration

### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml angel-x-stack

# Scale service
docker service scale angel-x-stack_angel-x=3
```

### Kubernetes
- Helm chart available in `infra/kubernetes/`
- See Kubernetes deployment guide for cluster setup

## 🔄 Updates and Maintenance

### Update Application
```bash
# Pull latest code
git pull

# Rebuild image
docker build -t angel-x:latest .

# Restart with new image
docker-compose up -d --build
```

### Backup Data
```bash
# Backup volumes
docker run --rm \
  -v angel-x_postgres-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres-$(date +%Y%m%d).tar.gz /data
```

### Clean Up
```bash
# Remove unused images
docker image prune -a

# Remove stopped containers
docker container prune

# Remove unused volumes
docker volume prune
```

## 📚 Additional Resources

- [Dockerfile Reference](https://docs.docker.com/reference/dockerfile/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Production Deployment Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Angel-X Architecture Guide](./PHASE5_README.md)

## 🆘 Support

For deployment issues:
1. Check container logs: `docker logs angel-x-trading`
2. Verify health: `./deploy.sh health`
3. Review configuration: `config/config.py`
4. Check system resources: `docker stats`

---

**Status**: Phase 5 Complete - Docker Infrastructure Ready ✅
**Next Phase**: Phase 6 - Monitoring Setup (Prometheus + Grafana)
