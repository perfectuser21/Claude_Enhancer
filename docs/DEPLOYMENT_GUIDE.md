# Perfect21 部署指南

> 🚀 **部署 Perfect21**: 从开发环境到生产环境的完整部署指南
>
> 支持本地开发、Docker 容器化、Kubernetes 集群部署

## 📖 目录

- [环境要求](#环境要求)
- [快速部署](#快速部署)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Docker 部署](#docker-部署)
- [Kubernetes 部署](#kubernetes-部署)
- [配置管理](#配置管理)
- [监控与日志](#监控与日志)
- [故障排除](#故障排除)

## 🎯 环境要求

### 基础要求

| 组件 | 最低版本 | 推荐版本 | 说明 |
|------|---------|---------|------|
| Python | 3.8+ | 3.11+ | 支持异步特性 |
| Git | 2.0+ | 2.40+ | 工作流集成 |
| Node.js | 16+ | 18+ | 前端构建 (可选) |
| Redis | 6.0+ | 7.0+ | 缓存和会话 |
| Nginx | 1.18+ | 1.24+ | 反向代理 |

### 系统资源

#### 开发环境
- **CPU**: 2核心
- **内存**: 4GB
- **存储**: 10GB
- **网络**: 100Mbps

#### 生产环境
- **CPU**: 4核心+
- **内存**: 8GB+
- **存储**: 50GB+
- **网络**: 1Gbps+

### 依赖服务

```bash
# 必需服务
- Claude Code CLI (官方)
- Git 版本控制

# 可选服务 (增强功能)
- Redis (缓存)
- PostgreSQL (持久化存储)
- Elasticsearch (日志搜索)
- Prometheus (监控)
```

## ⚡ 快速部署

### 一键启动脚本

```bash
#!/bin/bash
# quick_deploy.sh - Perfect21 一键部署脚本

set -e

echo "🚀 Perfect21 快速部署开始..."

# 1. 检查环境
check_environment() {
    echo "📋 检查环境依赖..."

    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 未安装"
        exit 1
    fi

    # 检查 Git
    if ! command -v git &> /dev/null; then
        echo "❌ Git 未安装"
        exit 1
    fi

    # 检查 pip
    if ! command -v pip3 &> /dev/null; then
        echo "❌ pip3 未安装"
        exit 1
    fi

    echo "✅ 环境检查通过"
}

# 2. 安装依赖
install_dependencies() {
    echo "📦 安装 Python 依赖..."
    pip3 install -r requirements.txt

    echo "✅ 依赖安装完成"
}

# 3. 初始化配置
initialize_config() {
    echo "⚙️ 初始化配置..."

    # 创建配置目录
    mkdir -p .perfect21/{logs,cache,data}

    # 生成默认配置
    python3 scripts/generate_config.py --env development

    echo "✅ 配置初始化完成"
}

# 4. 安装 Git Hooks
install_git_hooks() {
    echo "🔗 安装 Git Hooks..."
    python3 main/cli.py hooks install standard
    echo "✅ Git Hooks 安装完成"
}

# 5. 验证安装
verify_installation() {
    echo "🔍 验证安装..."

    # 检查系统状态
    python3 main/cli.py status

    # 运行快速测试
    python3 main/cli.py develop "测试任务" --timeout 30

    echo "✅ 安装验证完成"
}

# 6. 启动服务
start_services() {
    echo "🚀 启动 Perfect21 服务..."

    # 启动 API 服务器
    python3 api/rest_server.py --host 0.0.0.0 --port 8000 &
    API_PID=$!

    echo "📡 API 服务器已启动 (PID: $API_PID)"
    echo "📚 API 文档: http://localhost:8000/docs"
    echo "🎯 管理界面: http://localhost:8000"

    # 保存 PID
    echo $API_PID > .perfect21/api.pid
}

# 执行部署步骤
main() {
    check_environment
    install_dependencies
    initialize_config
    install_git_hooks
    verify_installation
    start_services

    echo ""
    echo "🎉 Perfect21 快速部署完成!"
    echo "📋 使用指南:"
    echo "  python3 main/cli.py develop \"任务描述\""
    echo "  python3 main/cli.py parallel \"任务描述\" --force-parallel"
    echo "  curl http://localhost:8000/health"
}

main "$@"
```

### 使用快速部署

```bash
# 1. 克隆仓库
git clone <your-perfect21-repo>
cd Perfect21

# 2. 运行一键部署
chmod +x scripts/quick_deploy.sh
./scripts/quick_deploy.sh

# 3. 验证部署
curl http://localhost:8000/health
python3 main/cli.py status
```

## 💻 开发环境部署

### 手动安装步骤

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 3. 环境配置
cp config/development.yaml.example config/development.yaml
# 编辑 config/development.yaml 文件

# 4. 数据库初始化 (可选)
python3 scripts/init_database.py

# 5. 启动开发服务器
./start_dev_server.sh
```

### 开发服务器配置

```bash
#!/bin/bash
# start_dev_server.sh - 开发服务器启动脚本

# 设置环境变量
export ENV=development
export DEBUG=true
export LOG_LEVEL=DEBUG
export RELOAD=true

# 启动 Redis (可选)
if command -v redis-server &> /dev/null; then
    redis-server --port 6379 --daemonize yes
    echo "✅ Redis 已启动"
fi

# 启动 API 服务器
python3 api/rest_server.py \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level debug &

API_PID=$!
echo "🚀 开发服务器已启动"
echo "📡 API 地址: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"
echo "🔧 调试模式: 启用"
echo "📝 PID: $API_PID"

# 保存 PID 用于后续管理
echo $API_PID > .perfect21/dev_api.pid

# 启动 CLI 监控 (可选)
python3 main/cli.py monitor --live &
MONITOR_PID=$!
echo $MONITOR_PID > .perfect21/monitor.pid

echo ""
echo "🎯 开发环境已就绪!"
echo "💡 使用 Ctrl+C 停止服务"

# 等待中断信号
trap "kill $API_PID $MONITOR_PID; exit" INT
wait
```

### 开发工具配置

```bash
# VS Code 配置 (.vscode/launch.json)
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Perfect21 API Debug",
            "type": "python",
            "request": "launch",
            "program": "api/rest_server.py",
            "args": ["--reload", "--debug"],
            "console": "integratedTerminal",
            "env": {
                "ENV": "development",
                "DEBUG": "true"
            }
        },
        {
            "name": "Perfect21 CLI Debug",
            "type": "python",
            "request": "launch",
            "program": "main/cli.py",
            "args": ["develop", "测试任务", "--verbose"],
            "console": "integratedTerminal"
        }
    ]
}

# PyCharm 配置
# Run/Debug Configurations -> Python
# Script path: /path/to/Perfect21/api/rest_server.py
# Parameters: --reload --debug
# Environment variables: ENV=development;DEBUG=true
```

## 🏭 生产环境部署

### 生产服务器配置

```bash
#!/bin/bash
# deploy_production.sh - 生产环境部署脚本

set -e

# 生产环境变量
export ENV=production
export DEBUG=false
export LOG_LEVEL=INFO
export WORKERS=4

echo "🏭 Perfect21 生产环境部署开始..."

# 1. 系统优化
optimize_system() {
    echo "⚙️ 系统优化..."

    # 内核参数优化
    echo 'net.core.somaxconn = 65535' >> /etc/sysctl.conf
    echo 'fs.file-max = 100000' >> /etc/sysctl.conf
    sysctl -p

    # ulimit 优化
    echo '* soft nofile 65535' >> /etc/security/limits.conf
    echo '* hard nofile 65535' >> /etc/security/limits.conf

    echo "✅ 系统优化完成"
}

# 2. 安装生产依赖
install_production_deps() {
    echo "📦 安装生产依赖..."

    # 安装 Redis
    apt-get update
    apt-get install -y redis-server
    systemctl enable redis-server
    systemctl start redis-server

    # 安装 Nginx
    apt-get install -y nginx
    systemctl enable nginx

    # 安装 Supervisor
    apt-get install -y supervisor

    echo "✅ 生产依赖安装完成"
}

# 3. 配置 Nginx
configure_nginx() {
    echo "🌐 配置 Nginx..."

    cat > /etc/nginx/sites-available/perfect21 << 'EOF'
upstream perfect21_api {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name your-domain.com;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # 静态文件
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API 代理
    location / {
        proxy_pass http://perfect21_api;
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
        proxy_buffer_size 8k;
        proxy_buffers 8 8k;
    }

    # WebSocket 支持
    location /ws/ {
        proxy_pass http://perfect21_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # 健康检查
    location /health {
        proxy_pass http://perfect21_api/health;
        access_log off;
    }
}
EOF

    # 启用站点
    ln -sf /etc/nginx/sites-available/perfect21 /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    # 测试配置
    nginx -t
    systemctl reload nginx

    echo "✅ Nginx 配置完成"
}

# 4. 配置 Supervisor
configure_supervisor() {
    echo "👥 配置 Supervisor..."

    cat > /etc/supervisor/conf.d/perfect21.conf << 'EOF'
[program:perfect21-api]
command=/app/venv/bin/python /app/scripts/start_api.py --workers 4
directory=/app
user=perfect21
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/perfect21/api.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=ENV=production,DEBUG=false

[program:perfect21-worker]
command=/app/venv/bin/python /app/scripts/start_worker.py
directory=/app
user=perfect21
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/perfect21/worker.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
numprocs=2
process_name=%(program_name)s_%(process_num)02d

[group:perfect21]
programs=perfect21-api,perfect21-worker
EOF

    # 创建用户和目录
    useradd -r -s /bin/false perfect21
    mkdir -p /var/log/perfect21
    chown perfect21:perfect21 /var/log/perfect21

    # 重载配置
    supervisorctl reread
    supervisorctl update

    echo "✅ Supervisor 配置完成"
}

# 5. 配置日志轮转
configure_logrotate() {
    echo "📝 配置日志轮转..."

    cat > /etc/logrotate.d/perfect21 << 'EOF'
/var/log/perfect21/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 perfect21 perfect21
    postrotate
        supervisorctl signal HUP perfect21:*
    endscript
}
EOF

    echo "✅ 日志轮转配置完成"
}

# 6. 安全配置
configure_security() {
    echo "🔒 安全配置..."

    # 防火墙配置
    ufw --force enable
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp

    # 禁用不必要的服务
    systemctl disable bluetooth
    systemctl disable cups

    # 配置 fail2ban
    apt-get install -y fail2ban

    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
EOF

    systemctl enable fail2ban
    systemctl start fail2ban

    echo "✅ 安全配置完成"
}

# 执行部署
main() {
    optimize_system
    install_production_deps
    configure_nginx
    configure_supervisor
    configure_logrotate
    configure_security

    echo ""
    echo "🎉 生产环境部署完成!"
    echo "🌐 服务地址: http://your-domain.com"
    echo "📊 监控命令: supervisorctl status"
    echo "📝 日志路径: /var/log/perfect21/"
}

# 检查权限
if [[ $EUID -ne 0 ]]; then
   echo "❌ 此脚本需要 root 权限"
   exit 1
fi

main "$@"
```

### 生产环境启动脚本

```python
#!/usr/bin/env python3
# scripts/start_api.py - 生产环境 API 启动脚本

import os
import sys
import argparse
import uvicorn
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

def main():
    parser = argparse.ArgumentParser(description='Perfect21 生产环境 API 服务器')
    parser.add_argument('--host', default='127.0.0.1', help='绑定地址')
    parser.add_argument('--port', type=int, default=8000, help='端口号')
    parser.add_argument('--workers', type=int, default=4, help='工作进程数')
    parser.add_argument('--access-log', action='store_true', help='启用访问日志')

    args = parser.parse_args()

    # 生产环境配置
    config = {
        'app': 'api.rest_server:app',
        'host': args.host,
        'port': args.port,
        'workers': args.workers,
        'worker_class': 'uvicorn.workers.UvicornWorker',
        'access_log': args.access_log,
        'log_level': 'info',
        'keepalive': 2,
        'max_requests': 1000,
        'max_requests_jitter': 100,
        'preload_app': True,
        'timeout': 30,
    }

    print(f"🚀 启动 Perfect21 API 服务器")
    print(f"📡 地址: {args.host}:{args.port}")
    print(f"👥 工作进程: {args.workers}")

    # 使用 Gunicorn 启动 (生产环境)
    if os.getenv('ENV') == 'production':
        import gunicorn.app.wsgiapp as wsgi
        sys.argv = [
            'gunicorn',
            '--bind', f'{args.host}:{args.port}',
            '--workers', str(args.workers),
            '--worker-class', 'uvicorn.workers.UvicornWorker',
            '--access-logfile', '/var/log/perfect21/access.log' if args.access_log else '-',
            '--error-logfile', '/var/log/perfect21/error.log',
            '--log-level', 'info',
            '--keepalive', '2',
            '--max-requests', '1000',
            '--max-requests-jitter', '100',
            '--preload',
            '--timeout', '30',
            'api.rest_server:app'
        ]
        wsgi.run()
    else:
        # 开发环境使用 uvicorn
        uvicorn.run(**config)

if __name__ == '__main__':
    main()
```

## 🐳 Docker 部署

### Dockerfile

```dockerfile
# Dockerfile - Perfect21 容器镜像
FROM python:3.11-slim as base

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN useradd -m -u 1000 perfect21 && \
    chown perfect21:perfect21 /app

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY --chown=perfect21:perfect21 . .

# 创建必要的目录
RUN mkdir -p .perfect21/{logs,cache,data} && \
    chown -R perfect21:perfect21 .perfect21

# 切换到非 root 用户
USER perfect21

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "scripts/start_api.py", "--host", "0.0.0.0", "--workers", "4"]

# 开发环境镜像
FROM base as development

# 安装开发依赖
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# 启用开发模式
CMD ["python", "api/rest_server.py", "--host", "0.0.0.0", "--reload"]

# 生产环境镜像
FROM base as production

# 生产环境优化
ENV ENV=production
ENV DEBUG=false
ENV PYTHONOPTIMIZE=1

# 启动生产服务
CMD ["python", "scripts/start_api.py", "--host", "0.0.0.0", "--workers", "4"]
```

### Docker Compose

```yaml
# docker-compose.yml - Perfect21 服务编排
version: '3.8'

services:
  # Perfect21 API 服务
  perfect21-api:
    build:
      context: .
      target: production
    container_name: perfect21-api
    ports:
      - "8000:8000"
    environment:
      - ENV=production
      - DEBUG=false
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://perfect21:password@postgres:5432/perfect21
    depends_on:
      - redis
      - postgres
    volumes:
      - ./data:/app/data
      - ./logs:/app/.perfect21/logs
    networks:
      - perfect21-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Redis 缓存服务
  redis:
    image: redis:7-alpine
    container_name: perfect21-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - perfect21-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 5s
      retries: 3

  # PostgreSQL 数据库 (可选)
  postgres:
    image: postgres:15-alpine
    container_name: perfect21-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=perfect21
      - POSTGRES_USER=perfect21
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - perfect21-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U perfect21"]
      interval: 30s
      timeout: 5s
      retries: 3

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: perfect21-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf
      - ./config/ssl:/etc/nginx/ssl
      - ./static:/usr/share/nginx/html/static
    depends_on:
      - perfect21-api
    networks:
      - perfect21-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  # 监控服务 (可选)
  prometheus:
    image: prom/prometheus:latest
    container_name: perfect21-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - perfect21-network
    restart: unless-stopped

  # Grafana 仪表板 (可选)
  grafana:
    image: grafana/grafana:latest
    container_name: perfect21-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./config/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
    networks:
      - perfect21-network
    restart: unless-stopped

# 数据卷
volumes:
  redis_data:
  postgres_data:
  prometheus_data:
  grafana_data:

# 网络
networks:
  perfect21-network:
    driver: bridge
```

### Docker 部署命令

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f perfect21-api

# 5. 扩展服务
docker-compose up -d --scale perfect21-api=3

# 6. 停止服务
docker-compose down

# 7. 清理资源
docker-compose down -v --rmi all
```

## ☸️ Kubernetes 部署

### Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: perfect21
  labels:
    app: perfect21
    version: v2.3.0
```

### ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: perfect21-config
  namespace: perfect21
data:
  production.yaml: |
    env: production
    debug: false
    log_level: INFO

    api:
      host: 0.0.0.0
      port: 8000
      workers: 4
      timeout: 30

    redis:
      host: redis-service
      port: 6379
      db: 0

    database:
      host: postgres-service
      port: 5432
      name: perfect21
      user: perfect21

    security:
      jwt_expire_hours: 1
      rate_limit_per_hour: 1000

    monitoring:
      enabled: true
      metrics_port: 9090
```

### Secret

```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: perfect21-secret
  namespace: perfect21
type: Opaque
data:
  database-password: cGFzc3dvcmQ=  # base64 编码的密码
  jwt-secret-key: your-jwt-secret-key-base64
  admin-password: admin-password-base64
```

### Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: perfect21-api
  namespace: perfect21
  labels:
    app: perfect21-api
    version: v2.3.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: perfect21-api
  template:
    metadata:
      labels:
        app: perfect21-api
        version: v2.3.0
    spec:
      containers:
      - name: perfect21-api
        image: perfect21:v2.3.0
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 9090
          name: metrics
        env:
        - name: ENV
          value: "production"
        - name: DEBUG
          value: "false"
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: DATABASE_URL
          value: "postgresql://perfect21:$(DATABASE_PASSWORD)@postgres-service:5432/perfect21"
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: perfect21-secret
              key: database-password
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: perfect21-secret
              key: jwt-secret-key
        volumeMounts:
        - name: config
          mountPath: /app/config/production.yaml
          subPath: production.yaml
        - name: data
          mountPath: /app/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
      volumes:
      - name: config
        configMap:
          name: perfect21-config
      - name: data
        persistentVolumeClaim:
          claimName: perfect21-data-pvc
```

### Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: perfect21-api-service
  namespace: perfect21
  labels:
    app: perfect21-api
spec:
  selector:
    app: perfect21-api
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  - name: metrics
    port: 9090
    targetPort: 9090
    protocol: TCP
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: perfect21
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: perfect21
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

### Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: perfect21-ingress
  namespace: perfect21
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - perfect21.your-domain.com
    secretName: perfect21-tls
  rules:
  - host: perfect21.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: perfect21-api-service
            port:
              number: 80
```

### PersistentVolumeClaim

```yaml
# k8s/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: perfect21-data-pvc
  namespace: perfect21
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data-pvc
  namespace: perfect21
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: fast-ssd
```

### HorizontalPodAutoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: perfect21-api-hpa
  namespace: perfect21
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: perfect21-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

### 部署脚本

```bash
#!/bin/bash
# scripts/deploy_k8s.sh - Kubernetes 部署脚本

set -e

echo "☸️ Perfect21 Kubernetes 部署开始..."

# 配置
NAMESPACE="perfect21"
REGISTRY="your-registry.com"
IMAGE_TAG="${1:-v2.3.0}"

# 1. 构建和推送镜像
build_and_push_image() {
    echo "🏗️ 构建镜像..."

    docker build -t perfect21:$IMAGE_TAG .
    docker tag perfect21:$IMAGE_TAG $REGISTRY/perfect21:$IMAGE_TAG
    docker push $REGISTRY/perfect21:$IMAGE_TAG

    echo "✅ 镜像推送完成"
}

# 2. 创建命名空间
create_namespace() {
    echo "📦 创建命名空间..."
    kubectl apply -f k8s/namespace.yaml
    echo "✅ 命名空间创建完成"
}

# 3. 应用配置
apply_configs() {
    echo "⚙️ 应用配置..."

    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/secret.yaml
    kubectl apply -f k8s/pvc.yaml

    echo "✅ 配置应用完成"
}

# 4. 部署服务
deploy_services() {
    echo "🚀 部署服务..."

    # 部署 PostgreSQL
    kubectl apply -f k8s/postgres.yaml

    # 部署 Redis
    kubectl apply -f k8s/redis.yaml

    # 等待数据库就绪
    kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s
    kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=300s

    # 部署 Perfect21 API
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/service.yaml

    # 等待 API 就绪
    kubectl wait --for=condition=ready pod -l app=perfect21-api -n $NAMESPACE --timeout=300s

    echo "✅ 服务部署完成"
}

# 5. 配置网络
configure_networking() {
    echo "🌐 配置网络..."

    kubectl apply -f k8s/ingress.yaml
    kubectl apply -f k8s/hpa.yaml

    echo "✅ 网络配置完成"
}

# 6. 验证部署
verify_deployment() {
    echo "🔍 验证部署..."

    # 检查 Pod 状态
    kubectl get pods -n $NAMESPACE

    # 检查服务状态
    kubectl get services -n $NAMESPACE

    # 检查 Ingress
    kubectl get ingress -n $NAMESPACE

    # 健康检查
    echo "等待服务就绪..."
    sleep 30

    INGRESS_IP=$(kubectl get ingress perfect21-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ ! -z "$INGRESS_IP" ]; then
        curl -f http://$INGRESS_IP/health
        echo "✅ 健康检查通过"
    else
        echo "⚠️ Ingress IP 未分配，使用端口转发测试"
        kubectl port-forward service/perfect21-api-service 8080:80 -n $NAMESPACE &
        PORT_FORWARD_PID=$!
        sleep 10
        curl -f http://localhost:8080/health
        kill $PORT_FORWARD_PID
        echo "✅ 端口转发测试通过"
    fi

    echo "✅ 部署验证完成"
}

# 主函数
main() {
    build_and_push_image
    create_namespace
    apply_configs
    deploy_services
    configure_networking
    verify_deployment

    echo ""
    echo "🎉 Perfect21 Kubernetes 部署完成!"
    echo ""
    echo "📋 有用的命令:"
    echo "  kubectl get all -n $NAMESPACE"
    echo "  kubectl logs -f deployment/perfect21-api -n $NAMESPACE"
    echo "  kubectl describe ingress perfect21-ingress -n $NAMESPACE"
    echo ""
    echo "🌐 访问地址:"
    echo "  https://perfect21.your-domain.com"
    echo "  https://perfect21.your-domain.com/docs"
}

main "$@"
```

## ⚙️ 配置管理

### 环境配置文件

```yaml
# config/development.yaml - 开发环境配置
env: development
debug: true
log_level: DEBUG

api:
  host: 127.0.0.1
  port: 8000
  workers: 1
  reload: true
  timeout: 30

redis:
  host: localhost
  port: 6379
  db: 0
  password: null

database:
  url: sqlite:///data/perfect21_dev.db
  echo: true

security:
  jwt_secret_key: dev-secret-key
  jwt_expire_hours: 24
  password_min_length: 6
  rate_limit_per_hour: 10000

monitoring:
  enabled: false

claude_code:
  timeout: 300
  max_retries: 3

workflow:
  default_template: premium_quality
  max_parallel_agents: 8
  sync_point_timeout: 300

quality:
  code_coverage_threshold: 80
  performance_threshold_ms: 500
  security_scan_enabled: false
```

```yaml
# config/production.yaml - 生产环境配置
env: production
debug: false
log_level: INFO

api:
  host: 0.0.0.0
  port: 8000
  workers: 4
  timeout: 30
  access_log: true

redis:
  host: redis-service
  port: 6379
  db: 0
  password: ${REDIS_PASSWORD}
  max_connections: 100

database:
  url: postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
  pool_size: 20
  max_overflow: 30
  echo: false

security:
  jwt_secret_key: ${JWT_SECRET_KEY}
  jwt_expire_hours: 1
  password_min_length: 8
  rate_limit_per_hour: 1000
  cors_origins:
    - https://perfect21.your-domain.com
    - https://admin.your-domain.com

monitoring:
  enabled: true
  metrics_port: 9090
  prometheus_endpoint: /metrics

claude_code:
  timeout: 600
  max_retries: 5

workflow:
  default_template: premium_quality
  max_parallel_agents: 12
  sync_point_timeout: 600

quality:
  code_coverage_threshold: 90
  performance_threshold_ms: 200
  security_scan_enabled: true
```

### 配置加载器

```python
# modules/config.py - 配置管理模块
import os
import yaml
from typing import Dict, Any
from pathlib import Path

class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.env = os.getenv('ENV', 'development')
        self.load_config()

    def load_config(self):
        """加载配置文件"""
        config_dir = Path(__file__).parent.parent / 'config'

        # 加载基础配置
        base_config_file = config_dir / 'base.yaml'
        if base_config_file.exists():
            with open(base_config_file) as f:
                self.config = yaml.safe_load(f)

        # 加载环境特定配置
        env_config_file = config_dir / f'{self.env}.yaml'
        if env_config_file.exists():
            with open(env_config_file) as f:
                env_config = yaml.safe_load(f)
                self.config.update(env_config)

        # 环境变量覆盖
        self.apply_env_overrides()

    def apply_env_overrides(self):
        """应用环境变量覆盖"""
        env_mappings = {
            'API_HOST': 'api.host',
            'API_PORT': 'api.port',
            'REDIS_HOST': 'redis.host',
            'REDIS_PORT': 'redis.port',
            'DB_HOST': 'database.host',
            'DB_PORT': 'database.port',
            'JWT_SECRET_KEY': 'security.jwt_secret_key',
        }

        for env_var, config_path in env_mappings.items():
            if env_var in os.environ:
                self.set_nested_value(config_path, os.environ[env_var])

    def set_nested_value(self, path: str, value: Any):
        """设置嵌套配置值"""
        keys = path.split('.')
        current = self.config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # 类型转换
        if keys[-1] == 'port':
            value = int(value)
        elif value.lower() in ('true', 'false'):
            value = value.lower() == 'true'

        current[keys[-1]] = value

    def get(self, path: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = path.split('.')
        current = self.config

        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default

# 全局配置实例
config = ConfigManager()
```

## 📊 监控与日志

### Prometheus 监控配置

```yaml
# config/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "perfect21_rules.yml"

scrape_configs:
  - job_name: 'perfect21-api'
    static_configs:
      - targets: ['perfect21-api:9090']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

### 告警规则

```yaml
# config/perfect21_rules.yml
groups:
  - name: perfect21_alerts
    rules:
      - alert: PerfectAPIDown
        expr: up{job="perfect21-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Perfect21 API is down"
          description: "Perfect21 API has been down for more than 1 minute"

      - alert: HighResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
```

### 日志配置

```python
# modules/logging_config.py
import logging
import logging.config
from pathlib import Path

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'detailed',
            'filename': '.perfect21/logs/perfect21.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'detailed',
            'filename': '.perfect21/logs/error.log',
            'maxBytes': 10485760,
            'backupCount': 5
        }
    },
    'loggers': {
        'perfect21': {
            'level': 'DEBUG',
            'handlers': ['console', 'file', 'error_file'],
            'propagate': False
        },
        'uvicorn': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    },
    'root': {
        'level': 'WARNING',
        'handlers': ['console']
    }
}

def setup_logging():
    """设置日志配置"""
    # 创建日志目录
    log_dir = Path('.perfect21/logs')
    log_dir.mkdir(parents=True, exist_ok=True)

    # 应用日志配置
    logging.config.dictConfig(LOGGING_CONFIG)
```

## 🔧 故障排除

### 常见问题解决方案

#### 1. 服务启动失败

```bash
# 问题诊断
docker-compose logs perfect21-api

# 常见原因和解决方案
echo "检查端口占用"
netstat -tulpn | grep :8000

echo "检查权限问题"
ls -la .perfect21/

echo "检查配置文件"
python3 -c "import yaml; print(yaml.safe_load(open('config/production.yaml')))"

# 解决方案
sudo fuser -k 8000/tcp  # 释放端口
chmod -R 755 .perfect21/  # 修复权限
```

#### 2. 数据库连接问题

```bash
# PostgreSQL 连接测试
docker exec -it perfect21-postgres psql -U perfect21 -d perfect21 -c "SELECT 1;"

# Redis 连接测试
docker exec -it perfect21-redis redis-cli ping

# 解决方案
docker-compose restart postgres redis
```

#### 3. 性能问题

```bash
# 监控系统资源
docker stats

# 查看应用性能指标
curl http://localhost:8000/metrics

# 优化建议
docker-compose up -d --scale perfect21-api=3  # 扩展实例
```

#### 4. SSL/TLS 证书问题

```bash
# 检查证书状态
openssl x509 -in /etc/nginx/ssl/cert.pem -text -noout

# 更新证书 (Let's Encrypt)
certbot renew --nginx

# 手动证书配置
kubectl create secret tls perfect21-tls \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem \
  --namespace=perfect21
```

### 监控脚本

```bash
#!/bin/bash
# scripts/health_check.sh - 健康检查脚本

check_api_health() {
    echo "🔍 检查 API 健康状态..."

    HEALTH_URL="http://localhost:8000/health"
    if curl -f -s $HEALTH_URL > /dev/null; then
        echo "✅ API 健康检查通过"
    else
        echo "❌ API 健康检查失败"
        return 1
    fi
}

check_database_health() {
    echo "🔍 检查数据库连接..."

    if docker exec perfect21-postgres pg_isready -U perfect21; then
        echo "✅ 数据库连接正常"
    else
        echo "❌ 数据库连接失败"
        return 1
    fi
}

check_redis_health() {
    echo "🔍 检查 Redis 连接..."

    if docker exec perfect21-redis redis-cli ping | grep -q PONG; then
        echo "✅ Redis 连接正常"
    else
        echo "❌ Redis 连接失败"
        return 1
    fi
}

main() {
    echo "🏥 Perfect21 健康检查开始..."

    check_api_health
    check_database_health
    check_redis_health

    echo "✅ 健康检查完成"
}

main "$@"
```

---

> 🚀 **总结**: Perfect21 提供了从开发环境到生产环境的完整部署方案，支持传统部署、Docker 容器化和 Kubernetes 集群部署。通过完善的配置管理、监控系统和故障排除指南，确保 Perfect21 能够稳定高效地运行在各种环境中。