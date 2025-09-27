# =============================================================================
# Multi-stage Dockerfile for Claude Enhancer Frontend (React + TypeScript)
# Optimized for production with Nginx static serving
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Node.js Builder - Build React Application
# -----------------------------------------------------------------------------
FROM node:18-alpine as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Add metadata
LABEL org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.url="https://github.com/claude-enhancer/frontend" \
      org.opencontainers.image.source="https://github.com/claude-enhancer/frontend" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.vendor="Claude Enhancer" \
      org.opencontainers.image.title="Claude Enhancer Frontend" \
      org.opencontainers.image.description="React frontend for Claude Enhancer task management system"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    git \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Copy package files for better layer caching
COPY package*.json ./
COPY yarn.lock* ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Copy source code
COPY . .

# Set environment variables for build
ENV NODE_ENV=production
ENV REACT_APP_API_URL=/api
ENV GENERATE_SOURCEMAP=false

# Build application
RUN npm run build

# Verify build output
RUN ls -la build/ && \
    echo "Build completed successfully"

# -----------------------------------------------------------------------------
# Stage 2: Nginx Production Server
# -----------------------------------------------------------------------------
FROM nginx:1.25-alpine as production

# Install system updates
RUN apk add --no-cache \
    curl \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Create nginx user and directories
RUN addgroup -g 1001 -S nginx && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx

# Copy built application from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx-default.conf /etc/nginx/conf.d/default.conf

# Create nginx runtime directories with proper permissions
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run && \
    chown -R nginx:nginx /var/cache/nginx /var/log/nginx /var/run /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Security: Run as non-root user
USER nginx

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# -----------------------------------------------------------------------------
# Stage 3: Development Server (optional)
# -----------------------------------------------------------------------------
FROM node:18-alpine as development

WORKDIR /app

# Install development dependencies
RUN apk add --no-cache \
    git \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Copy package files
COPY package*.json ./
COPY yarn.lock* ./

# Install all dependencies (including dev)
RUN npm install

# Copy source code
COPY . .

# Set development environment
ENV NODE_ENV=development
ENV REACT_APP_API_URL=http://localhost:8000/api
ENV FAST_REFRESH=true

# Health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Expose development port
EXPOSE 3000

# Start development server
CMD ["npm", "start"]