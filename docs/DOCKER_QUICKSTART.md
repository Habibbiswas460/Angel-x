# 🐳 Docker Quick Start Guide

**Get Angel-X running with Docker in 5 minutes**

---

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed ([Get Docker Compose](https://docs.docker.com/compose/install/))
- AngelOne API credentials

---

## 🚀 Quick Start (3 Steps)

### Step 1: Setup Environment

```bash
# Copy environment template
cp .env.docker .env

# Edit .env and add your credentials
nano .env  # or vim .env
```

Required credentials in `.env`:
```bash
ANGELONE_CLIENT_CODE=your_client_code
ANGELONE_API_KEY=your_api_key
ANGELONE_PASSWORD=your_password
ANGELONE_TOTP_SECRET=your_totp_secret
```

### Step 2: Start Services

```bash
# Using deployment script (recommended)
./docker-deploy.sh up

# Or using docker-compose directly
docker-compose up -d
```

### Step 3: Initialize Database

```bash
./docker-deploy.sh init-db

# Or manually
docker-compose exec angel-x python init_db.py
```

**Done!** Access dashboard at: http://localhost:5001

---

## 📋 Deployment Script Commands

The `docker-deploy.sh` script provides easy management:

```bash
# Start services
./docker-deploy.sh up

# Start with monitoring (Prometheus + Grafana)
./docker-deploy.sh up-monitoring

# Stop services
./docker-deploy.sh down

# View logs
./docker-deploy.sh logs

# Check status
./docker-deploy.sh status

# Rebuild image
./docker-deploy.sh build

# Validate config
./docker-deploy.sh validate

# Open shell
./docker-deploy.sh shell

# Backup data
./docker-deploy.sh backup

# Clean everything (CAUTION: deletes data)
./docker-deploy.sh clean
```

---

## 🏗️ Services Included

### Core Services (Always Running)

1. **angel-x** - Trading application
   - Dashboard: http://localhost:5001
   - API: http://localhost:5000

2. **postgres** - PostgreSQL database
   - Port: 5432
   - Stores trades, performance, market data

3. **redis** - Redis cache
   - Port: 6379
   - Caches market data, sessions

### Monitoring Services (Optional)

Start with: `./docker-deploy.sh up-monitoring`

4. **prometheus** - Metrics collection
   - Web UI: http://localhost:9090

5. **grafana** - Visualization
   - Web UI: http://localhost:3000
   - Login: admin/admin

---

## ⚙️ Configuration

### Database

Default PostgreSQL configuration:
```bash
DATABASE_NAME=angel_x
DATABASE_USER=angelx
DATABASE_PASSWORD=changeme  # Change this!
```

### Redis Cache

Default Redis configuration:
```bash
REDIS_PASSWORD=changeme  # Change this!
CACHE_ENABLED=True
```

### Trading

```bash
TRADING_ENABLED=False  # Set True for live trading
PAPER_TRADING=True     # Keep True for testing
```

---

## 📊 Common Tasks

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f angel-x
docker-compose logs -f postgres
docker-compose logs -f redis

# Last 100 lines
docker-compose logs --tail=100 angel-x
```

### Check Database

```bash
# Database info
docker-compose exec angel-x python init_db.py --info

# Database schema
docker-compose exec angel-x python init_db.py --schema

# Connect to PostgreSQL
docker-compose exec postgres psql -U angelx -d angel_x
```

### Execute Commands

```bash
# Run any Python script
docker-compose exec angel-x python script.py

# Open Python shell
docker-compose exec angel-x python

# Open bash shell
docker-compose exec angel-x bash
```

### Restart Services

```bash
# Restart all
./docker-deploy.sh restart

# Restart specific service
docker-compose restart angel-x
docker-compose restart postgres
```

---

## 💾 Backup & Restore

### Backup

```bash
# Automatic backup (creates timestamped backup)
./docker-deploy.sh backup

# Manual database backup
docker-compose exec postgres pg_dump -U angelx angel_x > backup_$(date +%Y%m%d).sql

# Manual data backup
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/ logs/ models/
```

### Restore

```bash
# Restore database
docker-compose exec -T postgres psql -U angelx angel_x < backup_20260115.sql

# Restore data
tar -xzf data_backup_20260115.tar.gz
```

---

## 🔒 Security Checklist

Before production deployment:

- [ ] Change `DATABASE_PASSWORD` in `.env`
- [ ] Change `REDIS_PASSWORD` in `.env`
- [ ] Set strong `GRAFANA_PASSWORD` in `.env`
- [ ] Review exposed ports (consider firewall)
- [ ] Enable SSL/TLS for external access
- [ ] Set `TRADING_ENABLED=False` until ready
- [ ] Test with `PAPER_TRADING=True` first
- [ ] Configure backup schedule

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check status
docker-compose ps

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Failed

```bash
# Check PostgreSQL is healthy
docker-compose ps postgres

# Test connection
docker-compose exec postgres pg_isready -U angelx

# View PostgreSQL logs
docker-compose logs postgres
```

### Permission Errors

```bash
# Fix file permissions (run on host)
sudo chown -R 1000:1000 data/ logs/ models/
```

### Out of Disk Space

```bash
# Clean up Docker resources
docker system prune -a

# Remove unused volumes
docker volume prune
```

---

## 🔄 Updating

```bash
# 1. Pull latest code
git pull origin main

# 2. Stop services
./docker-deploy.sh down

# 3. Backup data (recommended)
./docker-deploy.sh backup

# 4. Rebuild image
./docker-deploy.sh build

# 5. Start services
./docker-deploy.sh up

# 6. Initialize database (if schema changed)
./docker-deploy.sh init-db
```

---

## 🌐 Production Deployment

### Using Different Database

Edit `docker-compose.yml` to use external PostgreSQL:

```yaml
angelx:
  environment:
    DATABASE_HOST: your-postgres-server.com
    DATABASE_PORT: 5432
    # ... other settings
```

Remove `postgres` service from docker-compose.yml.

### Using External Redis

Edit `docker-compose.yml`:

```yaml
angelx:
  environment:
    REDIS_HOST: your-redis-server.com
    REDIS_PORT: 6379
```

Remove `redis` service from docker-compose.yml.

### Scaling

```bash
# Docker Swarm
docker stack deploy -c docker-compose.yml angelx

# Kubernetes
kompose convert -f docker-compose.yml
kubectl apply -f .
```

---

## 📚 Additional Resources

- [Complete Docker Deployment Guide](DOCKER_DEPLOYMENT.md)
- [Configuration Guide](../config/README.md)
- [Database Schema](DATABASE_SCHEMA.md)
- [API Documentation](API.md)

---

## ❓ FAQ

**Q: Can I use SQLite instead of PostgreSQL?**  
A: Yes, set `DB_TYPE=sqlite` in `.env` and remove postgres from dependencies.

**Q: Do I need Redis?**  
A: No, Redis is optional. Set `CACHE_ENABLED=False` to disable.

**Q: How do I enable live trading?**  
A: Set `TRADING_ENABLED=True` and `PAPER_TRADING=False` in `.env`. Test thoroughly first!

**Q: Can I run without Docker?**  
A: Yes, see [INSTALLATION.md](../INSTALLATION.md) for manual setup.

**Q: How much RAM does it need?**  
A: Minimum 2GB, recommended 4GB.

---

**Version:** 1.0  
**Last Updated:** January 15, 2026
