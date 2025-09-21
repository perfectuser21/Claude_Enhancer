# Perfect21 Claude Enhancer - Deployment Guide

## 🚀 Complete Deployment Configuration

This document provides comprehensive deployment configurations for the Perfect21 Claude Enhancer system, supporting both Docker Compose and Kubernetes deployments in development and production environments.

## 📁 Deployment Files Created

### Core Application Files
- `/main.py` - FastAPI application entry point with production-ready configuration
- `/backend/api/` - Complete API structure with authentication, agents, workflows, and health endpoints

### Docker Configuration
- `/Dockerfile` - Multi-stage production-optimized Docker image
- `/docker-compose.yml` - Development and testing environment
- `/docker-compose.production.yml` - Production-optimized deployment
- `/.dockerignore` - Optimized for minimal image size

### Environment Configuration
- `/.env.example` - Template with all configuration options
- `/.env.development` - Safe development defaults
- `/.env.production` - Production template (requires secret updates)

### Kubernetes Configuration
- `/k8s/namespace.yaml` - Kubernetes namespace
- `/k8s/configmap.yaml` - Configuration management
- `/k8s/secrets.yaml` - Secret management (template)
- `/k8s/deployment.yaml` - Main application deployment
- Existing: `/k8s/postgres.yaml`, `/k8s/redis.yaml`, `/k8s/monitoring.yaml`

### Deployment Automation
- `/deploy.sh` - Comprehensive deployment script with multiple options

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (Nginx)                   │
├─────────────────────────────────────────────────────────────┤
│  Perfect21 Claude Enhancer API (FastAPI + Uvicorn/Gunicorn)│
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Auth System │ │ Agent Mgmt  │ │ Workflows   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
├─────────────────────┬─────────────────┬─────────────────────┤
│   PostgreSQL        │      Redis       │    Monitoring      │
│   (Primary Data)    │    (Cache)       │ (Prometheus/Grafana)│
└─────────────────────┴─────────────────┴─────────────────────┘
```

## 🚀 Quick Start

### Development Deployment

1. **Prerequisites**
   ```bash
   # Ensure Docker and Docker Compose are installed
   docker --version
   docker-compose --version
   ```

2. **Deploy Development Environment**
   ```bash
   # Clone and navigate to project
   cd /home/xx/dev/Perfect21

   # Deploy development stack
   ./deploy.sh docker:dev
   ```

3. **Access Services**
   - API: http://localhost:8080
   - API Documentation: http://localhost:8080/docs
   - Grafana: http://localhost:3001 (admin/admin123)
   - pgAdmin: http://localhost:5050 (admin@claude-enhancer.local/admin123)

### Production Deployment

1. **Configure Production Environment**
   ```bash
   # Copy and customize production environment
   cp .env.production .env

   # IMPORTANT: Update all secrets in .env
   # - Database passwords
   # - JWT secrets
   # - API keys
   # - Domain configuration
   ```

2. **Deploy Production Stack**
   ```bash
   # Deploy with production configuration
   ./deploy.sh docker:prod -v 1.0.0
   ```

### Kubernetes Deployment

1. **Prepare Kubernetes Secrets**
   ```bash
   # Update k8s/secrets.yaml with your production secrets
   kubectl apply -f k8s/secrets.yaml
   ```

2. **Deploy to Kubernetes**
   ```bash
   # Deploy full stack to Kubernetes
   ./deploy.sh k8s:deploy -e production
   ```

## 🔧 Configuration Details

### Environment Variables

#### Core Application Settings
```bash
CLAUDE_ENV=production|development
DEBUG=false|true
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR
SECRET_KEY=your-256-bit-secret
API_VERSION=v1
WORKERS=4  # Number of worker processes
```

#### Database Configuration
```bash
DB_HOST=postgres
DB_PORT=5432
DB_NAME=claude_enhancer_prod
DB_USER=claude_user_prod
DB_PASSWORD=your-strong-password
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
```

#### Authentication & Security
```bash
JWT_ACCESS_SECRET=your-jwt-access-secret
JWT_REFRESH_SECRET=your-jwt-refresh-secret
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=7
CORS_ORIGINS=https://your-domain.com
ALLOWED_HOSTS=your-domain.com,api.your-domain.com
```

#### Monitoring & Observability
```bash
PROMETHEUS_ENABLED=true
SENTRY_DSN=your-sentry-dsn
DATADOG_API_KEY=your-datadog-key
LOG_FORMAT=json|text
```

### Resource Requirements

#### Development
- **CPU**: 2 cores minimum
- **Memory**: 4GB minimum
- **Storage**: 10GB minimum
- **Network**: Standard Docker networking

#### Production
- **Application**: 2-4 CPU cores, 2-4GB RAM per instance
- **Database**: 2 CPU cores, 4GB RAM, 100GB SSD
- **Redis**: 1 CPU core, 1GB RAM
- **Load Balancer**: 1 CPU core, 512MB RAM

## 🔒 Security Configuration

### Production Security Checklist
- [ ] Update all default passwords and secrets
- [ ] Configure SSL/TLS certificates
- [ ] Enable firewall rules
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Enable audit logging
- [ ] Implement rate limiting
- [ ] Configure CORS properly

### SSL/TLS Configuration
```bash
# Place certificates in nginx/ssl/
your-domain.crt
your-domain.key

# Update environment variables
SSL_CERTIFICATE_PATH=/etc/nginx/ssl/your-domain.crt
SSL_PRIVATE_KEY_PATH=/etc/nginx/ssl/your-domain.key
```

## 📊 Monitoring & Observability

### Metrics Collection
- **Prometheus**: Metrics collection at `/metrics` endpoint
- **Grafana**: Visualization dashboards
- **Health Checks**: `/api/v1/health/*` endpoints
- **Structured Logging**: JSON logs for production

### Health Check Endpoints
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Comprehensive health with dependencies
- `GET /api/v1/health/ready` - Kubernetes readiness probe
- `GET /api/v1/health/live` - Kubernetes liveness probe

## 🔄 Deployment Commands

### Using deploy.sh Script

```bash
# Development deployment
./deploy.sh docker:dev

# Production deployment
./deploy.sh docker:prod -v 1.0.0

# Kubernetes deployment
./deploy.sh k8s:deploy -e production

# Build images only
./deploy.sh build -v 1.2.3

# Check deployment health
./deploy.sh health

# View logs
./deploy.sh logs

# Clean up resources
./deploy.sh clean

# Remove Kubernetes deployment
./deploy.sh k8s:undeploy
```

### Manual Docker Compose

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d

# View logs
docker-compose logs -f claude-enhancer

# Stop services
docker-compose down
```

### Manual Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n claude-enhancer

# View logs
kubectl logs -f deployment/claude-enhancer -n claude-enhancer

# Scale deployment
kubectl scale deployment claude-enhancer --replicas=5 -n claude-enhancer
```

## 🔧 Troubleshooting

### Common Issues

1. **Application Won't Start**
   ```bash
   # Check logs
   docker-compose logs claude-enhancer

   # Verify environment variables
   docker-compose exec claude-enhancer env | grep CLAUDE
   ```

2. **Database Connection Issues**
   ```bash
   # Check database status
   docker-compose exec postgres pg_isready

   # Verify credentials
   docker-compose exec postgres psql -U claude_user -d claude_enhancer
   ```

3. **Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R 1000:1000 /opt/claude-enhancer/

   # Check security contexts in Kubernetes
   kubectl describe pod <pod-name> -n claude-enhancer
   ```

### Performance Tuning

1. **Application Performance**
   ```bash
   # Increase worker processes
   WORKERS=8

   # Tune database connections
   POOL_SIZE=20
   MAX_OVERFLOW=30
   ```

2. **Database Performance**
   ```bash
   # PostgreSQL tuning
   shared_buffers=512MB
   effective_cache_size=2GB
   max_connections=200
   ```

3. **Redis Performance**
   ```bash
   # Redis memory optimization
   maxmemory=1gb
   maxmemory-policy=allkeys-lru
   ```

## 📋 Maintenance

### Backup Strategy
1. **Database Backups**: Automated PostgreSQL dumps
2. **Configuration Backups**: Git-based configuration management
3. **Volume Backups**: Docker volume and persistent volume snapshots

### Updates and Upgrades
1. **Rolling Updates**: Zero-downtime deployments
2. **Database Migrations**: Automated schema migrations
3. **Security Updates**: Regular base image updates

### Monitoring
1. **Application Metrics**: Performance and usage metrics
2. **Infrastructure Metrics**: System resource monitoring
3. **Log Aggregation**: Centralized logging with ELK stack

## 🎯 Production Deployment Checklist

- [ ] Environment secrets configured
- [ ] SSL certificates installed
- [ ] Database initialized and secured
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Team training completed
- [ ] Incident response plan ready

## 📞 Support

For deployment issues or questions:
1. Check this documentation
2. Review application logs
3. Consult the troubleshooting section
4. Contact the development team

---

**Note**: This deployment configuration is production-ready but requires customization of secrets, domains, and environment-specific settings before production use.