# Claude Enhancer 5.1 - 部署指南

## 📋 概述

本指南详细介绍了Claude Enhancer 5.1在不同环境中的部署方法，包括开发环境、测试环境和生产环境的完整配置流程。

### 部署特点
- **一键部署** - 自动化的安装和配置脚本
- **环境隔离** - 支持多环境独立部署
- **容器化支持** - Docker和Kubernetes原生支持
- **零停机部署** - 蓝绿部署和滚动更新
- **自动回滚** - 故障自动检测和回滚机制

---

## 🔧 系统要求

### 最低系统要求

#### 硬件要求
```
CPU:    2核心 (推荐4核心+)
内存:   4GB (推荐8GB+)
存储:   20GB可用空间 (推荐50GB+)
网络:   稳定的互联网连接
```

#### 软件要求
```
操作系统: Linux (Ubuntu 20.04+), macOS (10.15+), Windows 10+
Python:   3.9+ (推荐3.11)
Node.js:  16+ (推荐18 LTS)
Git:      2.25+
Docker:   20.10+ (可选，推荐)
```

### 推荐生产环境配置

#### 服务器配置
```
CPU:    8核心 Intel/AMD x64
内存:   16GB+ DDR4
存储:   100GB+ SSD (系统) + 500GB+ SSD (数据)
网络:   千兆网卡，低延迟网络
```

#### 软件环境
```
操作系统: Ubuntu 22.04 LTS Server
Python:   3.11
Node.js:  18 LTS
数据库:   PostgreSQL 14+ / Redis 7+
反向代理: Nginx 1.20+
容器:     Docker 24+ / Kubernetes 1.25+
```

---

## 🚀 快速部署

### 方法1：一键安装脚本（推荐）

```bash
# 下载并运行一键安装脚本
curl -fsSL https://raw.githubusercontent.com/claude-enhancer/claude-enhancer/main/install.sh | bash

# 或者手动下载
wget https://github.com/claude-enhancer/claude-enhancer/releases/latest/download/claude-enhancer-5.1.tar.gz
tar -xzf claude-enhancer-5.1.tar.gz
cd claude-enhancer-5.1
chmod +x install.sh
./install.sh
```

### 方法2：Git克隆安装

```bash
# 克隆仓库
git clone https://github.com/claude-enhancer/claude-enhancer-5.1.git
cd claude-enhancer-5.1

# 检查系统要求
python3 check_requirements.py

# 运行安装脚本
./scripts/setup.sh

# 验证安装
python3 run_tests.py --type all
```

### 方法3：Docker容器部署

```bash
# 拉取官方镜像
docker pull claudeenhancer/claude-enhancer:5.1

# 运行容器
docker run -d \
  --name claude-enhancer \
  -p 8000:8000 \
  -p 3000:3000 \
  -v $(pwd)/.claude:/app/.claude \
  -v $(pwd)/data:/app/data \
  claudeenhancer/claude-enhancer:5.1

# 检查状态
docker logs claude-enhancer
```

---

## 📁 详细安装步骤

### 1. 环境准备

#### Ubuntu/Debian系统
```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装基础依赖
sudo apt install -y \
  python3 python3-pip python3-venv \
  nodejs npm \
  git curl wget \
  build-essential \
  postgresql-client \
  redis-tools

# 安装Docker (可选)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### CentOS/RHEL系统
```bash
# 安装EPEL仓库
sudo yum install -y epel-release

# 安装基础依赖
sudo yum groupinstall -y "Development Tools"
sudo yum install -y \
  python39 python39-pip \
  nodejs npm \
  git curl wget \
  postgresql-devel \
  redis

# 配置Python3为默认
sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1
```

#### macOS系统
```bash
# 安装Homebrew (如果没有)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装依赖
brew install python@3.11 node git postgresql redis
brew install --cask docker

# 启动服务
brew services start postgresql
brew services start redis
```

### 2. 下载和配置

#### 获取源码
```bash
# 方式1：从GitHub下载
git clone https://github.com/claude-enhancer/claude-enhancer-5.1.git
cd claude-enhancer-5.1

# 方式2：从官网下载
wget https://releases.claude-enhancer.com/v5.1/claude-enhancer-5.1.tar.gz
tar -xzf claude-enhancer-5.1.tar.gz
cd claude-enhancer-5.1
```

#### 创建Python虚拟环境
```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 升级pip
pip install --upgrade pip setuptools wheel
```

#### 安装Python依赖
```bash
# 安装核心依赖 (23个精简包)
pip install -r requirements.txt

# 安装开发依赖 (可选)
pip install -r requirements-dev.txt

# 验证安装
python -c "import fastapi, asyncio, jwt, bcrypt; print('所有依赖安装成功')"
```

#### 安装前端依赖
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 返回根目录
cd ..
```

### 3. 数据库配置

#### PostgreSQL配置
```bash
# 创建数据库用户
sudo -u postgres createuser claude_user
sudo -u postgres createdb claude_enhancer

# 设置用户密码
sudo -u postgres psql -c "ALTER USER claude_user PASSWORD 'claude_secure_password';"

# 授予权限
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE claude_enhancer TO claude_user;"

# 初始化数据库
python scripts/init_database.py
```

#### Redis配置
```bash
# 编辑Redis配置
sudo nano /etc/redis/redis.conf

# 关键配置项
bind 127.0.0.1
port 6379
requirepass claude_redis_password
maxmemory 256mb
maxmemory-policy allkeys-lru

# 重启Redis
sudo systemctl restart redis
sudo systemctl enable redis
```

### 4. 应用配置

#### 环境变量配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

**`.env` 文件内容：**
```bash
# 应用配置
CLAUDE_ENHANCER_ENV=production
CLAUDE_ENHANCER_DEBUG=false
CLAUDE_ENHANCER_SECRET_KEY=your-super-secret-key-here

# 数据库配置
DATABASE_URL=postgresql://claude_user:claude_secure_password@localhost:5432/claude_enhancer
REDIS_URL=redis://:claude_redis_password@localhost:6379/0

# Claude Code配置
CLAUDE_CODE_API_KEY=your-claude-api-key
CLAUDE_CODE_MAX_TOKENS=20000
CLAUDE_ENHANCER_MODE=production

# 安全配置
JWT_SECRET_KEY=your-jwt-secret-key
PASSWORD_SALT_ROUNDS=12
SESSION_TIMEOUT=3600

# 性能配置
CLAUDE_ENHANCER_LAZY_LOAD=true
CLAUDE_ENHANCER_CACHE_SIZE=256MB
CLAUDE_ENHANCER_PARALLEL_AGENTS=8

# 监控配置
CLAUDE_ENHANCER_MONITORING=enabled
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
```

#### Claude配置文件
```bash
# 复制Claude配置
cp .claude/settings.json.example .claude/settings.json

# 编辑配置
nano .claude/settings.json
```

**`.claude/settings.json` 内容：**
```json
{
  "version": "5.1.0",
  "project": "Claude Enhancer 5.1 Production",
  "workflow": {
    "phases": 6,
    "agent_strategy": "4-6-8",
    "parallel_execution": true,
    "quality_gates": true
  },
  "hooks": {
    "mode": "non-blocking",
    "timeout_ms": 2000,
    "retry_count": 3,
    "enabled": [
      "smart_agent_selector",
      "branch_helper",
      "quality_gate"
    ]
  },
  "agents": {
    "max_parallel": 8,
    "timeout_seconds": 300,
    "retry_policy": "exponential_backoff"
  },
  "performance": {
    "lazy_loading": true,
    "cache_enabled": true,
    "monitoring": true,
    "memory_limit": "512MB"
  },
  "security": {
    "input_validation": true,
    "audit_logging": true,
    "encryption": "aes256",
    "secure_headers": true
  }
}
```

### 5. 服务启动

#### 后端服务启动
```bash
# 方式1：直接启动
python run_api.py

# 方式2：使用Gunicorn (生产推荐)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --keep-alive 5 \
  --access-logfile - \
  --error-logfile - \
  run_api:app

# 方式3：使用systemd服务 (Linux)
sudo cp scripts/claude-enhancer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable claude-enhancer
sudo systemctl start claude-enhancer
```

#### 前端服务启动
```bash
# 开发模式
cd frontend
npm start

# 生产模式 (使用Nginx)
sudo cp scripts/nginx.conf /etc/nginx/sites-available/claude-enhancer
sudo ln -s /etc/nginx/sites-available/claude-enhancer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🐳 Docker部署

### Docker Compose部署 (推荐)

#### 创建docker-compose.yml
```yaml
version: '3.8'

services:
  # 应用服务
  claude-enhancer:
    image: claudeenhancer/claude-enhancer:5.1
    container_name: claude-enhancer-app
    restart: unless-stopped
    ports:
      - "8000:8000"
      - "3000:3000"
    environment:
      - CLAUDE_ENHANCER_ENV=production
      - DATABASE_URL=postgresql://claude_user:claude_password@postgres:5432/claude_enhancer
      - REDIS_URL=redis://:redis_password@redis:6379/0
    volumes:
      - ./data:/app/data
      - ./.claude:/app/.claude
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # PostgreSQL数据库
  postgres:
    image: postgres:14
    container_name: claude-enhancer-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=claude_enhancer
      - POSTGRES_USER=claude_user
      - POSTGRES_PASSWORD=claude_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U claude_user -d claude_enhancer"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: claude-enhancer-redis
    restart: unless-stopped
    command: redis-server --requirepass redis_password --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    container_name: claude-enhancer-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - claude-enhancer

  # 监控服务
  prometheus:
    image: prom/prometheus:latest
    container_name: claude-enhancer-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    container_name: claude-enhancer-grafana
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin_password
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  default:
    name: claude-enhancer-network
```

#### 启动服务
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f claude-enhancer

# 停止服务
docker-compose down

# 完全清理
docker-compose down -v --remove-orphans
```

### 单容器部署

#### 构建自定义镜像
```dockerfile
# Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    git \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# 安装Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# 复制依赖文件
COPY requirements.txt ./
COPY frontend/package*.json ./frontend/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装前端依赖
RUN cd frontend && npm ci --only=production

# 复制应用代码
COPY . .

# 构建前端
RUN cd frontend && npm run build

# 创建非root用户
RUN useradd -m -s /bin/bash claude && \
    chown -R claude:claude /app
USER claude

# 暴露端口
EXPOSE 8000 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "run_api:app"]
```

#### 构建和运行
```bash
# 构建镜像
docker build -t claude-enhancer:5.1 .

# 运行容器
docker run -d \
  --name claude-enhancer \
  -p 8000:8000 \
  -p 3000:3000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.claude:/app/.claude \
  claude-enhancer:5.1
```

---

## ☸️ Kubernetes部署

### 基础Kubernetes配置

#### Namespace配置
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: claude-enhancer
  labels:
    name: claude-enhancer
    version: "5.1"
```

#### ConfigMap配置
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: claude-enhancer-config
  namespace: claude-enhancer
data:
  settings.json: |
    {
      "version": "5.1.0",
      "project": "Claude Enhancer 5.1 Kubernetes",
      "workflow": {
        "phases": 6,
        "agent_strategy": "4-6-8",
        "parallel_execution": true
      },
      "performance": {
        "lazy_loading": true,
        "cache_enabled": true,
        "monitoring": true
      }
    }
  nginx.conf: |
    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://claude-enhancer-service:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /static/ {
            alias /app/frontend/dist/;
        }
    }
```

#### Secret配置
```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: claude-enhancer-secrets
  namespace: claude-enhancer
type: Opaque
data:
  # Base64编码的密钥
  database-url: cG9zdGdyZXNxbDovL2NsYXVkZV91c2VyOmNsYXVkZV9wYXNzd29yZEBwb3N0Z3Jlczp0NDMyL2NsYXVkZV9lbmhhbmNlcg==
  redis-url: cmVkaXM6Ly86cmVkaXNfcGFzc3dvcmRAcmVkaXM6NjM3OS8w
  jwt-secret: eW91ci1qd3Qtc2VjcmV0LWtleS1oZXJl
  claude-api-key: eW91ci1jbGF1ZGUtYXBpLWtleQ==
```

#### Deployment配置
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: claude-enhancer
  namespace: claude-enhancer
  labels:
    app: claude-enhancer
    version: "5.1"
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: claude-enhancer
  template:
    metadata:
      labels:
        app: claude-enhancer
        version: "5.1"
    spec:
      containers:
      - name: claude-enhancer
        image: claudeenhancer/claude-enhancer:5.1
        ports:
        - containerPort: 8000
          name: api
        - containerPort: 3000
          name: frontend
        env:
        - name: CLAUDE_ENHANCER_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: claude-enhancer-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: claude-enhancer-secrets
              key: redis-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: claude-enhancer-secrets
              key: jwt-secret
        volumeMounts:
        - name: config
          mountPath: /.claude/settings.json
          subPath: settings.json
        - name: data
          mountPath: /app/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
      volumes:
      - name: config
        configMap:
          name: claude-enhancer-config
      - name: data
        persistentVolumeClaim:
          claimName: claude-enhancer-data
```

#### Service配置
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: claude-enhancer-service
  namespace: claude-enhancer
  labels:
    app: claude-enhancer
spec:
  type: ClusterIP
  selector:
    app: claude-enhancer
  ports:
  - name: api
    port: 8000
    targetPort: 8000
  - name: frontend
    port: 3000
    targetPort: 3000
```

#### Ingress配置
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: claude-enhancer-ingress
  namespace: claude-enhancer
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
spec:
  tls:
  - hosts:
    - claude-enhancer.yourdomain.com
    secretName: claude-enhancer-tls
  rules:
  - host: claude-enhancer.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: claude-enhancer-service
            port:
              number: 8000
```

#### 部署到Kubernetes
```bash
# 创建命名空间
kubectl apply -f k8s/namespace.yaml

# 部署配置和密钥
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 部署应用
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# 检查部署状态
kubectl get pods -n claude-enhancer
kubectl get services -n claude-enhancer
kubectl get ingress -n claude-enhancer

# 查看日志
kubectl logs -f deployment/claude-enhancer -n claude-enhancer
```

---

## 🔍 监控和日志

### Prometheus监控配置

#### prometheus.yml
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'claude-enhancer'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### 告警规则
```yaml
# monitoring/alert_rules.yml
groups:
- name: claude-enhancer-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Claude Enhancer high error rate"
      description: "Error rate is {{ $value }} for 5 minutes"

  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Memory usage is above 85%"

  - alert: DatabaseDown
    expr: up{job="postgres"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "PostgreSQL is down"
      description: "PostgreSQL database is not responding"
```

### Grafana仪表板

#### 系统概览仪表板
```json
{
  "dashboard": {
    "id": null,
    "title": "Claude Enhancer 5.1 Overview",
    "description": "System overview dashboard",
    "panels": [
      {
        "title": "API Requests per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[1m])",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "System Memory",
        "type": "graph",
        "targets": [
          {
            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / 1024 / 1024 / 1024",
            "legendFormat": "Used Memory (GB)"
          }
        ]
      }
    ]
  }
}
```

### 日志管理

#### 日志配置
```python
# config/logging.py
import logging
import logging.handlers
from pathlib import Path

def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 应用日志
    app_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=100*1024*1024,  # 100MB
        backupCount=5
    )

    # 错误日志
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=50*1024*1024,   # 50MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)

    # 访问日志
    access_handler = logging.handlers.RotatingFileHandler(
        log_dir / "access.log",
        maxBytes=200*1024*1024,  # 200MB
        backupCount=7
    )

    # 配置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    for handler in [app_handler, error_handler, access_handler]:
        handler.setFormatter(formatter)

    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)

    return {
        "app": app_handler,
        "error": error_handler,
        "access": access_handler
    }
```

---

## 🔒 安全配置

### SSL/TLS配置

#### Nginx SSL配置
```nginx
# nginx/ssl.conf
server {
    listen 80;
    server_name claude-enhancer.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name claude-enhancer.yourdomain.com;

    # SSL证书配置
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # 主要代理配置
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # 缓冲配置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # 静态文件服务
    location /static/ {
        alias /app/frontend/dist/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

### 防火墙配置

#### UFW防火墙 (Ubuntu)
```bash
# 启用UFW
sudo ufw enable

# 允许SSH
sudo ufw allow ssh

# 允许HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许应用端口 (仅本地)
sudo ufw allow from 127.0.0.1 to any port 8000
sudo ufw allow from 127.0.0.1 to any port 5432
sudo ufw allow from 127.0.0.1 to any port 6379

# 查看状态
sudo ufw status verbose
```

#### iptables防火墙
```bash
# 基础防火墙规则
#!/bin/bash

# 清空现有规则
iptables -F
iptables -X
iptables -Z

# 设置默认策略
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 允许本地回环
iptables -A INPUT -i lo -j ACCEPT

# 允许已建立的连接
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 允许SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# 允许HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 允许内部服务 (仅本地)
iptables -A INPUT -s 127.0.0.1 -p tcp --dport 8000 -j ACCEPT
iptables -A INPUT -s 127.0.0.1 -p tcp --dport 5432 -j ACCEPT
iptables -A INPUT -s 127.0.0.1 -p tcp --dport 6379 -j ACCEPT

# 保存规则
iptables-save > /etc/iptables/rules.v4
```

---

## 🚨 故障排除

### 常见问题和解决方案

#### 1. 服务启动失败

**问题**: 应用无法启动
```bash
# 检查日志
tail -f logs/app.log
tail -f logs/error.log

# 检查端口占用
sudo netstat -tlnp | grep :8000

# 检查环境变量
printenv | grep CLAUDE

# 验证配置文件
python -c "import json; json.load(open('.claude/settings.json'))"
```

**解决方案**:
- 检查端口是否被占用：`sudo fuser -k 8000/tcp`
- 验证环境变量配置
- 检查Python虚拟环境是否激活
- 确认数据库连接配置正确

#### 2. 数据库连接问题

**问题**: 无法连接到PostgreSQL
```bash
# 测试数据库连接
psql -h localhost -U claude_user -d claude_enhancer

# 检查PostgreSQL状态
sudo systemctl status postgresql

# 查看PostgreSQL日志
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

**解决方案**:
- 检查数据库服务是否运行
- 验证用户权限和密码
- 检查防火墙规则
- 确认数据库配置文件中的监听地址

#### 3. Redis连接问题

**问题**: Redis缓存不可用
```bash
# 测试Redis连接
redis-cli -h localhost -p 6379 -a redis_password ping

# 检查Redis状态
sudo systemctl status redis

# 查看Redis日志
sudo tail -f /var/log/redis/redis-server.log
```

**解决方案**:
- 检查Redis服务状态
- 验证密码配置
- 检查内存使用情况
- 确认Redis配置文件设置

#### 4. 性能问题

**问题**: 响应时间过长
```bash
# 检查系统资源
top
htop
iostat 1

# 检查数据库性能
psql -c "SELECT * FROM pg_stat_activity;"

# 分析应用日志
grep "slow" logs/app.log | tail -20
```

**解决方案**:
- 优化数据库查询和索引
- 增加系统内存
- 启用缓存策略
- 调整Agent并发数量

#### 5. 权限问题

**问题**: 文件权限错误
```bash
# 检查文件权限
ls -la .claude/
ls -la data/
ls -la logs/

# 修复权限
sudo chown -R $USER:$USER .claude/ data/ logs/
chmod -R 755 .claude/
chmod -R 644 .claude/settings.json
```

### 日志分析工具

#### 日志监控脚本
```bash
#!/bin/bash
# scripts/monitor_logs.sh

echo "=== Claude Enhancer 5.1 日志监控 ==="

# 实时监控错误日志
tail -f logs/error.log | while read line; do
    echo "[$(date)] ERROR: $line"

    # 发送告警 (可选)
    if [[ $line == *"CRITICAL"* ]]; then
        echo "Critical error detected: $line" | mail -s "Claude Enhancer Alert" admin@yourdomain.com
    fi
done
```

#### 性能分析脚本
```bash
#!/bin/bash
# scripts/performance_check.sh

echo "=== 系统性能检查 ==="

# CPU使用率
echo "CPU使用率:"
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//'

# 内存使用
echo -e "\n内存使用情况:"
free -h

# 磁盘空间
echo -e "\n磁盘使用情况:"
df -h

# 应用进程状态
echo -e "\n应用进程:"
ps aux | grep "claude-enhancer\|gunicorn\|python"

# 数据库连接数
echo -e "\n数据库连接数:"
psql -U claude_user -d claude_enhancer -c "SELECT count(*) FROM pg_stat_activity;"

# Redis内存使用
echo -e "\nRedis内存使用:"
redis-cli -a redis_password info memory | grep used_memory_human
```

---

## 🔄 维护和更新

### 版本升级流程

#### 1. 备份现有系统
```bash
# 创建备份目录
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"

# 备份应用代码
tar -czf $BACKUP_DIR/app_backup.tar.gz --exclude='logs/*' --exclude='.venv/*' .

# 备份数据库
pg_dump -U claude_user claude_enhancer > $BACKUP_DIR/database_backup.sql

# 备份Redis数据
redis-cli -a redis_password --rdb $BACKUP_DIR/redis_backup.rdb

# 备份配置文件
cp -r .claude $BACKUP_DIR/
cp .env $BACKUP_DIR/
```

#### 2. 下载新版本
```bash
# 下载新版本
wget https://github.com/claude-enhancer/claude-enhancer/releases/download/v5.2/claude-enhancer-5.2.tar.gz

# 解压到临时目录
mkdir -p temp/upgrade
tar -xzf claude-enhancer-5.2.tar.gz -C temp/upgrade/
```

#### 3. 执行升级
```bash
# 停止服务
sudo systemctl stop claude-enhancer
docker-compose down  # 如果使用Docker

# 运行升级脚本
cd temp/upgrade/claude-enhancer-5.2
./scripts/upgrade.sh --from-version 5.1.0

# 更新依赖
pip install -r requirements.txt
cd frontend && npm install && npm run build

# 运行数据库迁移
python scripts/migrate_database.py

# 更新配置文件
./scripts/update_config.sh
```

#### 4. 验证升级
```bash
# 启动服务
sudo systemctl start claude-enhancer
docker-compose up -d  # 如果使用Docker

# 验证版本
curl http://localhost:8000/version

# 运行健康检查
python scripts/health_check.py

# 运行测试
python run_tests.py --type smoke
```

### 定期维护任务

#### 每日维护脚本
```bash
#!/bin/bash
# scripts/daily_maintenance.sh

echo "=== Claude Enhancer 每日维护 - $(date) ==="

# 清理旧日志 (保留30天)
find logs/ -name "*.log" -mtime +30 -delete

# 清理临时文件
find /tmp -name "claude_*" -mtime +1 -delete

# 备份数据库 (保留7天)
pg_dump -U claude_user claude_enhancer | gzip > "backups/daily_$(date +%Y%m%d).sql.gz"
find backups/ -name "daily_*.sql.gz" -mtime +7 -delete

# 检查磁盘空间
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "警告: 磁盘使用率超过80% ($DISK_USAGE%)"
    echo "磁盘空间不足" | mail -s "Claude Enhancer 磁盘告警" admin@yourdomain.com
fi

# 重启Redis (清理内存碎片)
redis-cli -a redis_password DEBUG RESTART

# 更新系统包 (安全更新)
sudo apt update && sudo apt upgrade -y --only-upgrade $(apt list --upgradable 2>/dev/null | grep security | cut -d'/' -f1)

echo "每日维护完成"
```

#### 每周维护脚本
```bash
#!/bin/bash
# scripts/weekly_maintenance.sh

echo "=== Claude Enhancer 每周维护 - $(date) ==="

# 数据库维护
psql -U claude_user -d claude_enhancer << EOF
VACUUM ANALYZE;
REINDEX DATABASE claude_enhancer;
EOF

# 清理Docker镜像 (如果使用Docker)
docker system prune -f
docker image prune -a -f --filter "until=168h"

# 安全扫描
python scripts/security_scan.py

# 性能报告
python scripts/generate_performance_report.py

# 完整备份
./scripts/full_backup.sh

echo "每周维护完成"
```

### 自动化维护

#### Crontab配置
```bash
# 编辑crontab
crontab -e

# 添加维护任务
# 每日凌晨2点执行日常维护
0 2 * * * /path/to/claude-enhancer/scripts/daily_maintenance.sh >> /path/to/logs/maintenance.log 2>&1

# 每周日凌晨3点执行周维护
0 3 * * 0 /path/to/claude-enhancer/scripts/weekly_maintenance.sh >> /path/to/logs/maintenance.log 2>&1

# 每15分钟检查服务状态
*/15 * * * * /path/to/claude-enhancer/scripts/health_check.sh

# 每小时清理临时文件
0 * * * * find /tmp -name "claude_*" -mtime +0.1 -delete
```

---

## 📞 技术支持

### 获取支持

#### 社区支持
- 📖 [官方文档](https://docs.claude-enhancer.com)
- 💬 [GitHub讨论区](https://github.com/claude-enhancer/claude-enhancer/discussions)
- 🐛 [问题反馈](https://github.com/claude-enhancer/claude-enhancer/issues)
- 📧 [邮件列表](mailto:community@claude-enhancer.com)

#### 企业支持
- 🏢 [企业技术支持](mailto:enterprise@claude-enhancer.com)
- 📞 **24/7技术热线**: +1-800-CLAUDE-5
- 💼 [专业服务咨询](https://claude-enhancer.com/professional-services)
- 🎓 [培训和认证](https://claude-enhancer.com/training)

### 系统信息收集

#### 诊断信息收集脚本
```bash
#!/bin/bash
# scripts/collect_diagnostics.sh

echo "=== Claude Enhancer 5.1 诊断信息收集 ==="

DIAG_DIR="diagnostics_$(date +%Y%m%d_%H%M%S)"
mkdir -p $DIAG_DIR

# 系统信息
echo "收集系统信息..."
uname -a > $DIAG_DIR/system_info.txt
cat /etc/os-release >> $DIAG_DIR/system_info.txt
free -h > $DIAG_DIR/memory_info.txt
df -h > $DIAG_DIR/disk_info.txt
ps aux > $DIAG_DIR/processes.txt

# 应用信息
echo "收集应用信息..."
python --version > $DIAG_DIR/python_version.txt
pip list > $DIAG_DIR/python_packages.txt
node --version > $DIAG_DIR/node_version.txt
npm list --depth=0 > $DIAG_DIR/npm_packages.txt 2>/dev/null

# 配置文件
echo "收集配置文件..."
cp .env $DIAG_DIR/ 2>/dev/null || echo "No .env file" > $DIAG_DIR/env_missing.txt
cp .claude/settings.json $DIAG_DIR/ 2>/dev/null || echo "No settings.json" > $DIAG_DIR/settings_missing.txt

# 日志文件 (最近1000行)
echo "收集日志文件..."
tail -1000 logs/app.log > $DIAG_DIR/app_log.txt 2>/dev/null
tail -1000 logs/error.log > $DIAG_DIR/error_log.txt 2>/dev/null

# 网络连接
echo "收集网络信息..."
netstat -tlnp > $DIAG_DIR/network_connections.txt
curl -I http://localhost:8000/health > $DIAG_DIR/health_check.txt 2>&1

# 数据库状态
echo "收集数据库信息..."
psql -U claude_user -d claude_enhancer -c "\l" > $DIAG_DIR/database_list.txt 2>/dev/null
psql -U claude_user -d claude_enhancer -c "SELECT version();" > $DIAG_DIR/postgres_version.txt 2>/dev/null

# Redis状态
echo "收集Redis信息..."
redis-cli -a redis_password info > $DIAG_DIR/redis_info.txt 2>/dev/null

# 创建压缩包
tar -czf claude_enhancer_diagnostics_$(date +%Y%m%d_%H%M%S).tar.gz $DIAG_DIR/

echo "诊断信息收集完成: claude_enhancer_diagnostics_$(date +%Y%m%d_%H%M%S).tar.gz"
echo "请将此文件发送给技术支持团队"
```

---

## 📋 部署检查清单

### 部署前检查

#### 系统准备
- [ ] 系统要求满足（CPU、内存、存储）
- [ ] 操作系统版本支持
- [ ] Python 3.9+ 安装
- [ ] Node.js 16+ 安装
- [ ] Git 安装和配置
- [ ] 网络连接正常

#### 依赖服务
- [ ] PostgreSQL 14+ 安装和配置
- [ ] Redis 7+ 安装和配置
- [ ] Nginx 安装和配置（生产环境）
- [ ] SSL证书准备（HTTPS）
- [ ] 防火墙规则配置

#### 应用配置
- [ ] 环境变量配置完整
- [ ] Claude配置文件正确
- [ ] 数据库连接配置
- [ ] Redis连接配置
- [ ] 安全密钥配置

### 部署后验证

#### 功能测试
- [ ] 应用成功启动
- [ ] 健康检查接口响应正常
- [ ] 数据库连接正常
- [ ] Redis缓存工作
- [ ] 前端页面加载正常
- [ ] API端点响应正确

#### 性能测试
- [ ] 响应时间 < 100ms
- [ ] 内存使用 < 512MB
- [ ] CPU使用率正常
- [ ] 并发处理能力验证
- [ ] 缓存命中率检查

#### 安全测试
- [ ] HTTPS配置正确
- [ ] 安全头设置
- [ ] 输入验证工作
- [ ] 权限控制有效
- [ ] 审计日志记录

#### 监控和告警
- [ ] Prometheus指标收集
- [ ] Grafana仪表板显示
- [ ] 日志轮转工作
- [ ] 告警规则配置
- [ ] 邮件通知测试

### 生产环境最终检查

#### 高可用性
- [ ] 负载均衡配置
- [ ] 故障转移测试
- [ ] 数据库主从复制
- [ ] 备份恢复测试
- [ ] 监控覆盖完整

#### 运维准备
- [ ] 维护脚本就位
- [ ] 升级流程文档
- [ ] 故障处理手册
- [ ] 联系方式更新
- [ ] 团队培训完成

---

**Claude Enhancer 5.1** - 企业级部署解决方案
*Professional deployment for production environments*

🚀 **祝您部署成功！如有任何问题，请联系技术支持团队。**