# Claude Enhancer Docker Guide

## Overview

This guide explains how to use Claude Enhancer in Docker containers for isolated, reproducible development environments.

## Quick Start

### Build and Run

```bash
# Build the Docker image
docker-compose build

# Start the container
docker-compose up -d claude-enhancer

# Access the container
docker-compose exec claude-enhancer bash

# Inside the container
ce --version
ce start my-feature
```

### Using Pre-built Image (if available)

```bash
# Pull the image
docker pull ghcr.io/your-org/claude-enhancer:1.0.0

# Run container
docker run -it -v $(pwd):/workspace ghcr.io/your-org/claude-enhancer:1.0.0
```

## Docker Compose Services

### Main Service: `claude-enhancer`

Primary development environment with CE_TERMINAL_ID=t1.

```bash
# Start
docker-compose up -d claude-enhancer

# Access
docker-compose exec claude-enhancer bash

# Stop
docker-compose stop claude-enhancer
```

### Secondary Service: `claude-enhancer-t2`

Additional terminal for parallel development (CE_TERMINAL_ID=t2).

```bash
# Start both terminals
docker-compose up -d

# Access terminal 2
docker-compose exec claude-enhancer-t2 bash
```

## Multi-Terminal Development

Claude Enhancer supports multi-terminal workflows in Docker:

### Terminal 1 (Feature A)
```bash
# In terminal 1
docker-compose exec claude-enhancer bash

# Inside container
cd /workspace
ce start login-form
# ... develop feature A ...
ce next
```

### Terminal 2 (Feature B)
```bash
# In terminal 2
docker-compose exec claude-enhancer-t2 bash

# Inside container
cd /workspace
ce start login-api --terminal t2
# ... develop feature B ...
ce next
```

### Check Status Across Terminals
```bash
# From either terminal
ce status

# View all active sessions
ls -la .workflow/cli/state/sessions/
```

## Volume Mounts

### Persistent Data

The docker-compose.yml configures several volumes:

1. **Project Directory**: `./:/workspace`
   - Your local project synced with container

2. **Git Configuration**: `ce-git-config`
   - Persists git settings between container restarts

3. **Bash History**: `ce-bash-history`, `ce-bash-history-t2`
   - Separate history for each terminal

4. **CE State**: `ce-state`
   - Shared workflow state across all containers

### Managing Volumes

```bash
# List volumes
docker volume ls | grep ce-

# Inspect volume
docker volume inspect ce-state

# Backup state volume
docker run --rm -v ce-state:/data -v $(pwd):/backup \
    ubuntu tar czf /backup/ce-state-backup.tar.gz /data

# Restore state volume
docker run --rm -v ce-state:/data -v $(pwd):/backup \
    ubuntu tar xzf /backup/ce-state-backup.tar.gz -C /
```

## Environment Configuration

### Git Configuration

Set your git identity in docker-compose.yml:

```yaml
environment:
  - GIT_AUTHOR_NAME=Your Name
  - GIT_AUTHOR_EMAIL=your.email@example.com
  - GIT_COMMITTER_NAME=Your Name
  - GIT_COMMITTER_EMAIL=your.email@example.com
```

Or configure inside the container:

```bash
docker-compose exec claude-enhancer bash

git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### CE Environment Variables

Configure in docker-compose.yml:

```yaml
environment:
  - CE_TERMINAL_ID=t1          # Terminal identifier
  - CE_VERBOSE=false           # Verbose output
  - CE_DEBUG=false             # Debug mode
  - CE_COLOR=always            # Color output
```

## Resource Limits

Adjust resource limits in docker-compose.yml:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'          # Max CPU cores
      memory: 2G         # Max memory
    reservations:
      cpus: '0.5'        # Guaranteed CPU
      memory: 512M       # Guaranteed memory
```

## Networking

Containers share a network for inter-container communication:

```bash
# Access from one container to another
docker-compose exec claude-enhancer bash

# Ping the other container
ping claude-enhancer-t2

# SSH (if configured)
ssh developer@claude-enhancer-t2
```

## Health Checks

Docker monitors container health automatically:

```bash
# Check health status
docker-compose ps

# View health logs
docker inspect claude-enhancer --format='{{.State.Health.Status}}'

# Manual health check
docker-compose exec claude-enhancer bash /opt/claude-enhancer/scripts/healthcheck.sh
```

## Dockerfile Details

### Base Image
- **Ubuntu 22.04**: Stable, well-supported base

### Installed Tools
- **Required**: bash, git, curl, wget, jq
- **Optional**: yq, gh (GitHub CLI), shellcheck
- **Editors**: vim, nano

### User Setup
- **Non-root user**: `developer`
- **Sudo access**: Passwordless (for package installation)

### File Locations
- **CE Installation**: `/opt/claude-enhancer/`
- **Global Command**: `/usr/local/bin/ce` (symlink)
- **Workspace**: `/workspace` (your project)

## Common Workflows

### 1. Standard Development

```bash
# Build and start
docker-compose up -d

# Access container
docker-compose exec claude-enhancer bash

# Develop
ce start my-feature
# ... make changes ...
ce validate
ce publish
```

### 2. Parallel Feature Development

```bash
# Start both terminals
docker-compose up -d

# Terminal 1: Frontend
docker-compose exec claude-enhancer bash
ce start frontend-component

# Terminal 2: Backend (new terminal window)
docker-compose exec claude-enhancer-t2 bash
ce start backend-api

# Monitor progress
ce status
```

### 3. Testing Before Release

```bash
# Build fresh container
docker-compose build --no-cache

# Run tests
docker-compose run --rm claude-enhancer bash -c "
  cd /opt/claude-enhancer
  scripts/healthcheck.sh
  scripts/verify_release.sh
"
```

### 4. Clean Environment

```bash
# Remove all containers and volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

### Permission Issues

```bash
# If you get permission errors
docker-compose exec --user root claude-enhancer bash

# Fix ownership
chown -R developer:developer /workspace
```

### State Sync Issues

```bash
# If state is not syncing between terminals
docker-compose exec claude-enhancer bash

# Check state directory permissions
ls -la .workflow/cli/state/

# Reset locks
rm -f .workflow/cli/state/locks/*.lock
```

### Container Won't Start

```bash
# Check logs
docker-compose logs claude-enhancer

# Check health
docker inspect claude-enhancer

# Recreate container
docker-compose up -d --force-recreate claude-enhancer
```

### Git Operations Fail

```bash
# Ensure git is configured
docker-compose exec claude-enhancer bash

git config --global --list

# If safe directory error
git config --global --add safe.directory /workspace
```

## Advanced Usage

### Custom Dockerfile

Create `Dockerfile.custom`:

```dockerfile
FROM claude-enhancer:1.0.0

# Add your custom tools
RUN apt-get update && apt-get install -y \
    python3 \
    nodejs \
    npm

# Install custom scripts
COPY my-scripts/ /opt/my-scripts/
RUN chmod +x /opt/my-scripts/*.sh
```

Build:
```bash
docker build -f Dockerfile.custom -t my-ce:latest .
```

### CI/CD Integration

Use in GitHub Actions:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: claude-enhancer:1.0.0
    steps:
      - uses: actions/checkout@v4
      - name: Run CE tests
        run: |
          ce validate
          scripts/healthcheck.sh
```

### Production Deployment

For production, use docker-compose.production.yml (if available):

```bash
docker-compose -f docker-compose.production.yml up -d
```

## Best Practices

### 1. Use Named Volumes
- Persist important data
- Easy backup and restore
- Share between containers

### 2. Separate Concerns
- One container per terminal/feature
- Use docker-compose for orchestration

### 3. Resource Management
- Set appropriate limits
- Monitor usage: `docker stats`

### 4. Security
- Run as non-root user
- Keep image updated
- Scan for vulnerabilities: `docker scan claude-enhancer:1.0.0`

### 5. Cleanup Regularly
```bash
# Remove stopped containers
docker-compose down

# Remove dangling images
docker image prune

# Remove unused volumes
docker volume prune
```

## Performance Optimization

### Build Cache

Use BuildKit for faster builds:

```bash
export DOCKER_BUILDKIT=1
docker-compose build
```

### Multi-stage Builds

For smaller images (advanced):

```dockerfile
# Builder stage
FROM ubuntu:22.04 as builder
# ... build tools ...

# Runtime stage
FROM ubuntu:22.04
COPY --from=builder /app /app
```

### Volume Performance

For better performance on macOS/Windows:

```yaml
volumes:
  - ./:/workspace:delegated  # Relaxed consistency
```

## Maintenance

### Update Dependencies

```bash
# Rebuild with latest packages
docker-compose build --no-cache --pull

# Test updated image
docker-compose run --rm claude-enhancer ce --version
```

### Backup Strategy

```bash
#!/bin/bash
# backup-ce-docker.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./docker-backups/$DATE"

mkdir -p "$BACKUP_DIR"

# Backup volumes
docker run --rm -v ce-state:/data -v $(pwd):/backup \
    ubuntu tar czf "/backup/$BACKUP_DIR/ce-state.tar.gz" /data

# Export images
docker save claude-enhancer:1.0.0 | gzip > "$BACKUP_DIR/claude-enhancer.tar.gz"

echo "Backup completed: $BACKUP_DIR"
```

## Support

### Getting Help

```bash
# CE help
docker-compose exec claude-enhancer ce --help

# Container info
docker-compose exec claude-enhancer bash -c "
  ce --version
  git --version
  bash --version
"
```

### Reporting Issues

When reporting Docker-related issues, include:

1. Docker version: `docker --version`
2. Docker Compose version: `docker-compose --version`
3. Container logs: `docker-compose logs`
4. System info: `docker info`

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Claude Enhancer Issues](https://github.com/your-org/claude-enhancer/issues)

---

**Last Updated:** 2025-10-09
**Version:** 1.0.0
