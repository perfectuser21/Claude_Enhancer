# =============================================================================
# Multi-stage Dockerfile for Claude Enhancer 5.1 Task Management System
# Optimized for production deployment with security and performance
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build Frontend (React/Vite)
# -----------------------------------------------------------------------------
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies with cache optimization
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY frontend/ ./

# Build for production
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Build Backend (Python)
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY requirements.txt ./
COPY src/requirements.txt ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY src/ ./src/
COPY .claude/ ./.claude/

# -----------------------------------------------------------------------------
# Stage 3: Production Runtime
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

# Create non-root user
RUN groupadd -r claude && useradd -r -g claude claude

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies and application
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /app/src ./src
COPY --from=backend-builder /app/.claude ./.claude

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./static

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads /app/temp && \
    chown -R claude:claude /app

# Switch to non-root user
USER claude

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose application port
EXPOSE 8080

# Set production environment
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    CLAUDE_ENV=production

# Start application
CMD ["python", "-m", "src.main"]