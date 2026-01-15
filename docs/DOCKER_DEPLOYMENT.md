# Docker Deployment Guide for Angel-X

**Complete guide for deploying Angel-X with Docker**

---

## 🐳 Quick Start

### Option 1: Basic Deployment (SQLite)

```bash
# 1. Clone repository
git clone <repository-url>
cd Angel-x

# 2. Create .env file
cp .env.example .env
# Edit .env with your AngelOne credentials

# 3. Start with Docker Compose
docker-compose up -d angelx
```

### Option 2: Production Deployment (PostgreSQL + Redis)

```bash
# 1. Setup environment
cp .env.production .env
# Edit .env with your credentials

# 2. Start all services
docker-compose up -d

# 3. Initialize database
docker-compose exec angelx python init_db.py

# 4. Check status
docker-compose ps
```

### Option 3: With Monitoring (Prometheus + Grafana)

```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d

# Access:
# - Angel-X Dashboard: http://localhost:5001
# - Grafana: http://localhost:3000 (admin/admin)
# - Prometheus: http://localhost:9090
```

---

## 📋 Services

### Core Services

1. **angelx** - Main trading application
   - Port 5001: Dashboard
   - Port 5000: REST API
   
2. **postgres** - PostgreSQL database
   - Port 5432: Database
   - Persistent storage
   
3. **redis** - Redis cache
   - Port 6379: Cache
   - Session storage

### Monitoring Services (Optional)

4. **prometheus** - Metrics collection
   - Port 9090: Web UI
   
5. **grafana** - Metrics visualization
   - Port 3000: Web UI

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file with:

```bash
# Environment
ENVIRONMENT=production
DEBUG=False

# AngelOne API
ANGELONE_API_KEY=your_api_key
ANGELONE_CLIENT_CODE=your_client_code
ANGELONE_PASSWORD=your_password
ANGELONE_TOTP_SECRET=your_totp_secret

# Database
DATABASE_NAME=angel_x
DATABASE_USER=angel_x_user
DATABASE_PASSWORD=strong_password_here

# Redis
REDIS_PASSWORD=strong_password_here

# Trading
PAPER_TRADING=True
TRADING_ENABLED=False

# Ports (optional, defaults shown)
DASHBOARD_PORT=5001
API_PORT=5000
DATABASE_PORT=5432
REDIS_PORT=6379
```

### Custom Configuration

Edit `docker-compose.yml` to customize:
- Resource limits
- Volume mounts
- Network settings
- Health checks

---

## 🚀 Docker Commands

### Start Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d angelx

# Start with logs
docker-compose up

# Start with monitoring
docker-compose --profile monitoring up -d
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Stop specific service
docker-compose stop angelx
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f angelx

# Last 100 lines
docker-compose logs --tail=100 angelx
```

### Execute Commands

```bash
# Run Python script
docker-compose exec angelx python script.py

# Initialize database
docker-compose exec angelx python init_db.py

# Validate configuration
docker-compose exec angelx python validate_config.py

# Open Python shell
docker-compose exec angelx python

# Open bash shell
docker-compose exec angelx bash
```

### Service Management

```bash
# Restart service
docker-compose restart angelx

# Rebuild image
docker-compose build angelx

# Rebuild without cache
docker-compose build --no-cache angelx

# Check status
docker-compose ps

# View resource usage
docker stats
```

---

## 📊 Database Management

### Initialize Database

```bash
# First time setup
docker-compose exec angelx python init_db.py

# Reset database (WARNING: deletes data)
docker-compose exec angelx python init_db.py --reset

# Check database info
docker-compose exec angelx python init_db.py --info
```

### Backup Database

```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U angel_x_user angel_x > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U angel_x_user angel_x < backup.sql
```

### Access Database

```bash
# PostgreSQL
docker-compose exec postgres psql -U angel_x_user -d angel_x

# Redis
docker-compose exec redis redis-cli -a your_redis_password
```

---

## 🔒 Security Best Practices

### 1. Change Default Passwords

```bash
# Generate strong passwords
openssl rand -base64 32

# Update in .env:
DATABASE_PASSWORD=<generated_password>
REDIS_PASSWORD=<generated_password>
GRAFANA_PASSWORD=<generated_password>
```

### 2. Use Secrets (Docker Swarm/Kubernetes)

```yaml
# docker-compose.yml
secrets:
  db_password:
    external: true
  redis_password:
    external: true
```

### 3. Network Isolation

```bash
# Expose only necessary ports
# Remove port mappings for internal services
```

### 4. Resource Limits

```yaml
# Add to docker-compose.yml
services:
  angelx:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## 🔍 Monitoring

### Check Health

```bash
# Service health
docker-compose ps

# Container health
docker inspect angelx-app | grep -A 10 Health

# Application health endpoint
curl http://localhost:5001/health
```

### View Metrics

```bash
# Prometheus metrics
curl http://localhost:9090/metrics

# Angel-X metrics (if exposed)
curl http://localhost:5001/metrics
```

### Grafana Dashboards

1. Access: http://localhost:3000
2. Login: admin / admin (change on first login)
3. Add Prometheus data source
4. Import pre-configured dashboards

---

## 📦 Data Persistence

### Volumes

Data is persisted in Docker volumes:

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect angelx_postgres_data

# Backup volume
docker run --rm -v angelx_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore volume
docker run --rm -v angelx_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

### Local Mounts

Application data is also mounted locally:

```
./data     - SQLite database (if used)
./logs     - Application logs
./models   - ML models
./journal  - Trade journals
./ticks    - Market data
```

---

## 🛠️ Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs angelx

# Check container status
docker-compose ps

# Rebuild image
docker-compose build --no-cache angelx

# Remove and recreate
docker-compose down
docker-compose up -d
```

### Database Connection Issues

```bash
# Check PostgreSQL health
docker-compose exec postgres pg_isready -U angel_x_user

# Check network
docker-compose exec angelx ping postgres

# View database logs
docker-compose logs postgres
```

### Permission Issues

```bash
# Fix ownership (run on host)
sudo chown -R 1000:1000 data/ logs/ models/

# Or run container as root (not recommended)
user: root  # in docker-compose.yml
```

### Out of Disk Space

```bash
# Clean up unused resources
docker system prune -a

# Remove unused volumes
docker volume prune

# Check disk usage
docker system df
```

---

## 🔄 Updates and Upgrades

### Update Application

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild image
docker-compose build angelx

# 3. Restart service
docker-compose up -d angelx
```

### Update Dependencies

```bash
# 1. Update requirements.txt
# 2. Rebuild image
docker-compose build --no-cache angelx

# 3. Restart
docker-compose up -d angelx
```

### Database Migration

```bash
# 1. Backup database
docker-compose exec postgres pg_dump -U angel_x_user angel_x > pre_migration_backup.sql

# 2. Run migrations
docker-compose exec angelx python init_db.py  # or alembic upgrade head

# 3. Verify
docker-compose exec angelx python init_db.py --info
```

---

## 📈 Performance Tuning

### PostgreSQL

```yaml
# docker-compose.yml
postgres:
  environment:
    POSTGRES_SHARED_BUFFERS: 256MB
    POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
    POSTGRES_WORK_MEM: 16MB
```

### Redis

```yaml
# docker-compose.yml
redis:
  command: >
    redis-server
    --maxmemory 512mb
    --maxmemory-policy allkeys-lru
```

### Application

```yaml
# docker-compose.yml
angelx:
  environment:
    WORKER_THREADS: 4
    DATABASE_POOL_SIZE: 10
```

---

## 🌐 Production Deployment

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml angelx

# Check services
docker service ls

# Scale service
docker service scale angelx_angelx=3
```

### Using Kubernetes

```bash
# Generate Kubernetes manifests
kompose convert -f docker-compose.yml

# Apply manifests
kubectl apply -f .

# Check pods
kubectl get pods
```

---

## 📞 Support

### Logs Location

```bash
# Container logs
docker-compose logs

# Application logs
./logs/angel-x.log

# Database logs
docker-compose logs postgres
```

### Debug Mode

```bash
# Enable debug logging
docker-compose exec angelx bash -c 'DEBUG=True python main.py'
```

### Get Help

```bash
# View container info
docker-compose exec angelx python --version
docker-compose exec angelx pip list

# Check configuration
docker-compose exec angelx python validate_config.py
```

---

## ✅ Checklist

Before going to production:

- [ ] Change all default passwords
- [ ] Configure backups
- [ ] Setup monitoring
- [ ] Test disaster recovery
- [ ] Configure SSL/TLS
- [ ] Setup log rotation
- [ ] Configure resource limits
- [ ] Test health checks
- [ ] Document custom changes
- [ ] Setup alerts

---

**Version:** 1.0  
**Last Updated:** January 15, 2026  
**Status:** ✅ Production Ready
