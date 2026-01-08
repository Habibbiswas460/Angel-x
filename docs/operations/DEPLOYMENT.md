# Deployment Guide

## Pre-Deployment Checklist

- [ ] All tests passing (`pytest tests/`)
- [ ] Code review completed
- [ ] Configuration validated for target environment
- [ ] Database migrations reviewed
- [ ] Monitoring and alerting configured
- [ ] Rollback plan documented
- [ ] Backup current version

## Development Deployment

### Local Development

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
python main.py
```

### Docker Local

```bash
docker build -t angel-x:dev -f infra/docker/Dockerfile .
docker run -p 5000:5000 \
  -v $(pwd)/logs:/app/logs \
  -e ENVIRONMENT=development \
  angel-x:dev
```

## Staging Deployment

### Prerequisites
- Access to staging PostgreSQL cluster
- Staging AngelOne broker credentials
- Staging Docker registry

### Deploy

```bash
# Build image
docker build -t angel-x:staging -f infra/docker/Dockerfile.prod .
docker tag angel-x:staging registry.angelx.internal/angel-x:staging
docker push registry.angelx.internal/angel-x:staging

# Deploy to staging
kubectl set image deployment/angel-x \
  api=registry.angelx.internal/angel-x:staging \
  -n staging

# Verify deployment
kubectl rollout status deployment/angel-x -n staging
```

## Production Deployment

### Prerequisites
- Production database credentials in secrets
- Production broker credentials
- Production domain/SSL certificates
- At least 2 replicas for high availability
- Monitoring and alerting configured

### Deploy

```bash
# Build production image
docker build -t angel-x:prod -f infra/docker/Dockerfile.prod .
docker tag angel-x:prod registry.angelx.internal/angel-x:$(git describe --tags)
docker push registry.angelx.internal/angel-x:$(git describe --tags)

# Apply secrets
kubectl create secret generic angel-x-secrets \
  --from-literal=DB_PASSWORD=$PROD_DB_PASSWORD \
  --from-literal=BROKER_API_KEY=$PROD_API_KEY \
  --from-literal=BROKER_CLIENT_CODE=$PROD_CLIENT_CODE \
  -n production

# Deploy
kubectl apply -f infra/kubernetes/deployment.yaml -n production

# Verify
kubectl rollout status deployment/angel-x -n production
kubectl get pods -n production
```

### Canary Deployment

Deploy to 10% of traffic first:

```bash
# Deploy canary
kubectl apply -f infra/kubernetes/canary.yaml

# Monitor metrics
kubectl logs -f deployment/angel-x-canary -n production

# If healthy, gradually increase traffic
# If issues, rollback immediately
```

## Post-Deployment

### Health Checks

```bash
# Check API health
curl -H "Authorization: Bearer $TOKEN" https://api.angelx.com/health

# Check database connectivity
psql postgresql://user:pass@host:5432/db -c "SELECT 1"

# Check broker connectivity
kubectl exec -it pod/angel-x-xxxx -- python -c "from app.services.broker import angelone_client; angelone_client.test_connection()"
```

### Monitoring

```bash
# View logs
kubectl logs -f deployment/angel-x -n production

# View metrics
kubectl top pods -n production

# Check alerts
kubectl get events -n production
```

## Rollback

If issues are detected:

```bash
# Immediate rollback
kubectl rollout undo deployment/angel-x -n production

# Verify previous version
kubectl rollout status deployment/angel-x -n production

# Check logs for errors
kubectl logs -f deployment/angel-x -n production
```

## Database Migrations

Before deployment, ensure migrations are applied:

```bash
# Check pending migrations
alembic current

# Apply migrations
alembic upgrade head

# If issues, rollback
alembic downgrade -1
```

## Performance Tuning

After deployment, optimize:

```yaml
# Adjust resource limits in deployment.yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"

# Scale based on load
kubectl autoscale deployment angel-x --min=2 --max=10 -n production
```

## Monitoring Dashboards

Access Grafana dashboards:
- **Trading Performance**: http://grafana.angelx.internal/d/trading
- **System Metrics**: http://grafana.angelx.internal/d/system
- **Database Health**: http://grafana.angelx.internal/d/database

## Support Contacts

- **Deployment Issues**: devops@angelx.internal
- **Trading Logic**: quants@angelx.internal
- **Infrastructure**: sre@angelx.internal
