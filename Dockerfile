# =============================================================================
# Multi-stage Dockerfile for Claude Enhancer Claude Enhancer
# Optimized for production with security and performance
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Python Builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim as python-builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Add metadata
LABEL org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.url="https://github.com/perfect21/claude-enhancer" \
      org.opencontainers.image.source="https://github.com/perfect21/claude-enhancer" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.vendor="Claude Enhancer" \
      org.opencontainers.image.title="Claude Enhancer" \
      org.opencontainers.image.description="AI-driven development workflow system"

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Node.js Builder (for frontend assets)
# -----------------------------------------------------------------------------
FROM node:18-alpine as node-builder

WORKDIR /app

# Copy package files
COPY auth-system/package*.json ./
COPY auth-system/tsconfig.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code and build
COPY auth-system/src ./src
COPY auth-system/public ./public

# Build frontend assets
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 3: Production Runtime
# -----------------------------------------------------------------------------
FROM python:3.11-slim as production

# Create non-root user for security
RUN groupadd -r claude && useradd -r -g claude claude

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    dumb-init \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code (excluding unnecessary files)
COPY run_api.py .
COPY backend/ ./backend/
COPY database/ ./database/
COPY .claude/ ./.claude/
COPY test/ ./test/
# COPY monitoring/ ./monitoring/
COPY requirements.txt .

# Copy built frontend assets (when available)
# COPY --from=node-builder /app/build ./auth-system/build

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp /app/uploads && \
    chown -R claude:claude /app

# Set environment variables
ENV PYTHONPATH=/app \
    CLAUDE_ENV=production \
    WORKERS=4

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Security: Run as non-root user
USER claude

# Expose port
EXPOSE 8080

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]

# Start application with gunicorn (production) or uvicorn (development)
CMD if [ "$CLAUDE_ENV" = "development" ]; then \
        uvicorn run_api:app --host 0.0.0.0 --port 8080 --reload; \
    else \
        gunicorn --bind 0.0.0.0:8080 --workers $WORKERS --worker-class uvicorn.workers.UvicornWorker --access-logfile - --error-logfile - run_api:app; \
    fi

# -----------------------------------------------------------------------------
# Stage 4: Development Runtime (optional)
# -----------------------------------------------------------------------------
FROM production as development

# Switch back to root for development tools
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    htop \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install pytest pytest-cov black flake8 mypy

# Switch back to claude user
USER claude

# Development command (with hot reload)
CMD ["uvicorn", "run_api:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]