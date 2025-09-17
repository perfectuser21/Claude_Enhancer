# Perfect21 DevOps Deployment Guide

> 🚀 **Production-Ready Deployment Configuration for Perfect21**
> Complete guide for deploying Perfect21 to Docker, Kubernetes, and cloud environments

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Monitoring & Observability](#monitoring--observability)
7. [Security](#security)
8. [Backup & Recovery](#backup--recovery)
9. [Troubleshooting](#troubleshooting)

## 🎯 Overview

Perfect21 deployment architecture provides:

- **Multi-stage Docker builds** for optimized production images
- **Kubernetes-native** deployment with autoscaling and monitoring
- **Complete CI/CD pipeline** with GitHub Actions
- **Production-grade security** with secret management
- **Comprehensive monitoring** with Prometheus, Grafana, and Loki
- **Automated backup** and disaster recovery

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer                          │
│                    (Nginx/Ingress)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                Perfect21 API Pods                          │
│              (Auto-scaling: 2-20 replicas)                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
┌───▼───┐      ┌─────▼──────┐     ┌────▼─────┐
│PostgreSQL│    │   Redis    │     │Monitoring│
│(Primary)│      │  (Cache)   │     │ Stack    │
└─────────┘      └────────────┘     └──────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Kubernetes 1.24+ (for K8s deployment)
- kubectl configured
- Git

### Local Development

```bash
# 1. Clone and setup
git clone <repository>
cd Perfect21
cp .env.example .env

# 2. Edit environment variables
nano .env

# 3. Start with Docker Compose
docker-compose up -d

# 4. Check health
curl http://localhost:8000/health
```

### Production Deployment

```bash
# 1. Deploy to staging
./scripts/deploy.sh staging deploy

# 2. Run health checks
./scripts/deploy.sh staging health-check

# 3. Deploy to production
./scripts/deploy.sh production deploy
```

## 🐳 Docker Deployment

### Multi-Stage Dockerfile

Our optimized Dockerfile provides:

- **Builder stage**: Compiles dependencies and application
- **Runtime stage**: Minimal production image
- **Security**: Non-root user, minimal attack surface
- **Performance**: Optimized for container orchestration

### Key Features

```dockerfile
# Production optimizations
FROM python:3.11-slim as runtime
RUN groupadd -g 1001 -r perfect21
COPY --from=builder /opt/venv /opt/venv
USER perfect21
HEALTHCHECK --interval=30s CMD /app/healthcheck.sh
```

### Docker Compose

#### Development
```bash
docker-compose up -d
```

#### Production
```bash
# With production overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Critical settings
JWT_SECRET_KEY=your-super-secret-key
POSTGRES_PASSWORD=strong-database-password
GRAFANA_PASSWORD=secure-grafana-password

# Performance tuning
API_WORKERS=4
REDIS_MAX_MEMORY=512mb
```

## ☸️ Kubernetes Deployment

### Architecture

```
perfect21 namespace:
├── Deployments
│   ├── perfect21-api (2-20 replicas)
│   ├── postgres (StatefulSet)
│   ├── redis (StatefulSet)
│   ├── prometheus
│   └── grafana
├── Services (ClusterIP/NodePort)
├── Ingress (TLS termination)
├── ConfigMaps & Secrets
├── PersistentVolumes
└── HorizontalPodAutoscaler
```

### Quick Deploy

```bash
# 1. Apply all manifests
kubectl apply -f k8s/

# 2. Or use deployment script
./scripts/deploy.sh production deploy

# 3. Check status
./scripts/deploy.sh production status
```

### Manual Deployment Steps

```bash
# 1. Create namespace and secrets
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml

# 2. Setup storage
kubectl apply -f k8s/persistent-volumes.yaml

# 3. Deploy data layer
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml

# 4. Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/autoscaling.yaml

# 5. Setup monitoring
kubectl apply -f k8s/monitoring.yaml
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment perfect21-api --replicas=5 -n perfect21

# Or use script
./scripts/deploy.sh production scale 5

# Auto-scaling is configured:
# - Min replicas: 2
# - Max replicas: 20
# - CPU threshold: 70%
# - Memory threshold: 80%
```

### Resource Limits

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Our CI/CD pipeline includes:

1. **Code Quality**: Black, Flake8, MyPy, Bandit
2. **Testing**: Unit, Integration, Security, Performance
3. **Building**: Multi-platform Docker images
4. **Security**: Vulnerability scanning, SBOM generation
5. **Deployment**: Blue-green deployment to staging/production

### Pipeline Stages

```yaml
jobs:
  code-quality → unit-tests → integration-tests
       ↓              ↓             ↓
  security-tests → build-image → performance-tests
       ↓              ↓             ↓
  deploy-staging ← e2e-tests ← deploy-production
```

### Secrets Configuration

Required GitHub secrets:

```bash
# Container Registry
GITHUB_TOKEN=ghp_xxx

# Kubernetes
KUBE_CONFIG_STAGING=base64-encoded-kubeconfig
KUBE_CONFIG_PROD=base64-encoded-kubeconfig

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

### Manual Triggers

```bash
# Trigger deployment
gh workflow run ci-cd-pipeline.yml \
  -f environment=production \
  -f deploy=true
```

## 📊 Monitoring & Observability

### Monitoring Stack

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **Application metrics**: Custom Perfect21 metrics

### Key Metrics

```
# Application metrics
perfect21_requests_total
perfect21_request_duration_seconds
perfect21_active_users
perfect21_task_execution_time

# Infrastructure metrics
cpu_usage_percent
memory_usage_percent
disk_usage_percent
postgres_connections
redis_memory_usage
```

### Alerts

```yaml
groups:
- name: perfect21-alerts
  rules:
  - alert: Perfect21APIDown
    expr: up{job="perfect21-api"} == 0
    for: 1m

  - alert: HighCPUUsage
    expr: cpu_usage_percent > 80
    for: 5m

  - alert: DatabaseDown
    expr: up{job="postgres"} == 0
    for: 1m
```

### Accessing Monitoring

```bash
# Grafana dashboard
kubectl port-forward svc/grafana-service 3000:3000 -n perfect21

# Prometheus
kubectl port-forward svc/prometheus-service 9090:9090 -n perfect21

# Or via Ingress (production)
# https://grafana.perfect21.example.com
# https://prometheus.perfect21.example.com
```

## 🔒 Security

### Security Features

1. **Container Security**
   - Non-root user execution
   - Read-only root filesystem
   - Minimal base images
   - Security scanning

2. **Network Security**
   - Network policies
   - TLS everywhere
   - Rate limiting
   - CORS configuration

3. **Secret Management**
   - Kubernetes secrets
   - External secret operators
   - Encryption at rest

4. **Access Control**
   - RBAC policies
   - Service accounts
   - Pod security standards

### Security Hardening

```yaml
# Pod Security Context
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
```

### TLS Configuration

```bash
# Generate certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=perfect21.example.com"

# Create TLS secret
kubectl create secret tls perfect21-tls \
  --cert=tls.crt --key=tls.key -n perfect21
```

## 💾 Backup & Recovery

### Automated Backups

```bash
# Database backup (runs daily at 2 AM)
kubectl create job --from=cronjob/postgres-backup manual-backup-$(date +%s) -n perfect21

# Manual backup
./scripts/backup.sh --type=full --retention=30d
```

### Backup Strategy

1. **Database**: Daily PostgreSQL dumps
2. **Persistent volumes**: Snapshot-based backups
3. **Configuration**: Git-based versioning
4. **Secrets**: Encrypted backup to secure storage

### Disaster Recovery

```bash
# 1. Restore from backup
./scripts/restore.sh --backup-date=2024-01-15 --type=full

# 2. Verify data integrity
./scripts/verify.sh --check-database --check-files

# 3. Resume operations
kubectl scale deployment perfect21-api --replicas=3 -n perfect21
```

## 🔧 Troubleshooting

### Common Issues

#### Pod Startup Issues

```bash
# Check pod status
kubectl get pods -n perfect21

# View pod logs
kubectl logs perfect21-api-xxx -n perfect21

# Describe pod for events
kubectl describe pod perfect21-api-xxx -n perfect21
```

#### Database Connection Issues

```bash
# Test database connectivity
kubectl exec -it postgres-0 -n perfect21 -- psql -U perfect21_user -d perfect21

# Check database logs
kubectl logs postgres-0 -n perfect21

# Verify secrets
kubectl get secret perfect21-secrets -n perfect21 -o yaml
```

#### Performance Issues

```bash
# Check resource usage
kubectl top pods -n perfect21

# Scale up if needed
./scripts/deploy.sh production scale 10

# Check HPA status
kubectl get hpa -n perfect21
```

### Health Checks

```bash
# Application health
curl -f http://localhost:8000/health

# Detailed health check
curl -f http://localhost:8000/health/detailed

# Readiness check
curl -f http://localhost:8000/health/ready
```

### Debugging Commands

```bash
# Get all resources
kubectl get all -n perfect21

# Check events
kubectl get events -n perfect21 --sort-by='.lastTimestamp'

# Port forward for debugging
kubectl port-forward svc/perfect21-api-service 8000:80 -n perfect21

# Execute into container
kubectl exec -it perfect21-api-xxx -n perfect21 -- /bin/bash
```

### Log Analysis

```bash
# Application logs
kubectl logs -f deployment/perfect21-api -n perfect21

# Database logs
kubectl logs -f statefulset/postgres -n perfect21

# Filter by error level
kubectl logs deployment/perfect21-api -n perfect21 | grep ERROR

# Export logs for analysis
kubectl logs deployment/perfect21-api -n perfect21 > perfect21-logs.txt
```

## 📞 Support & Maintenance

### Regular Maintenance

```bash
# Update deployments
./scripts/deploy.sh production deploy

# Rotate secrets (quarterly)
./scripts/rotate-secrets.sh --environment=production

# Database maintenance
kubectl exec postgres-0 -n perfect21 -- psql -U perfect21_user -d perfect21 -c "VACUUM ANALYZE;"

# Clean up old images
docker system prune -f
```

### Performance Optimization

1. **Database tuning**: Optimize PostgreSQL configuration
2. **Caching**: Configure Redis for optimal performance
3. **Resource limits**: Adjust based on usage patterns
4. **Scaling policies**: Fine-tune HPA thresholds

---

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Security Best Practices](https://kubernetes.io/docs/concepts/security/)

For issues and support, please check the [troubleshooting section](#troubleshooting) or create an issue in the repository.