# Perfect21 Production-Ready Multi-Stage Docker Build

# ========================= BUILD STAGE =========================
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=latest

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# ========================= RUNTIME STAGE =========================
FROM python:3.11-slim as runtime

# Add labels for better maintainability
LABEL maintainer="Perfect21 Team" \
      description="Perfect21 Claude Code Enhanced Development Platform" \
      version="${VERSION}" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}" \
      org.opencontainers.image.title="Perfect21" \
      org.opencontainers.image.description="Enhanced Claude Code Development Platform" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="Perfect21" \
      org.opencontainers.image.source="https://github.com/perfect21/perfect21"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    dumb-init \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create application user and group with specific UID/GID for security
RUN groupadd -g 1001 -r perfect21 && \
    useradd -u 1001 -r -g perfect21 -m -d /app -s /sbin/nologin \
    -c "Perfect21 service user" perfect21

# Set working directory
WORKDIR /app

# Create directory structure with proper permissions
RUN mkdir -p \
    /var/lib/perfect21/{data,cache,uploads,backups} \
    /var/log/perfect21 \
    /tmp/perfect21 \
    /app/{config,logs} && \
    chown -R perfect21:perfect21 \
    /var/lib/perfect21 \
    /var/log/perfect21 \
    /tmp/perfect21 \
    /app

# Copy application code with proper ownership
COPY --chown=perfect21:perfect21 . /app/

# Create optimized health check script
RUN echo '#!/bin/bash\nset -e\ncurl -f -s -o /dev/null --max-time 10 http://localhost:8000/health || exit 1' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh && \
    chown perfect21:perfect21 /app/healthcheck.sh

# Create startup script for better signal handling
RUN echo '#!/bin/bash\nset -e\nexec python -m uvicorn api.rest_server:app \\\n    --host 0.0.0.0 \\\n    --port 8000 \\\n    --workers ${WORKERS:-1} \\\n    --loop uvloop \\\n    --http h11 \\\n    --access-log \\\n    --use-colors' > /app/start.sh && \
    chmod +x /app/start.sh && \
    chown perfect21:perfect21 /app/start.sh

# Set environment variables for production
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    WORKERS=1 \
    MAX_WORKERS=4 \
    WEB_CONCURRENCY=1 \
    PORT=8000

# Switch to non-root user
USER perfect21

# Expose port
EXPOSE 8000

# Add health check with optimized settings
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /app/healthcheck.sh

# Use dumb-init for proper signal handling and start script
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/app/start.sh"]