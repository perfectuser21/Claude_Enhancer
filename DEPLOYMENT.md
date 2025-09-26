# 🚀 Claude Enhancer 5.1 - 完整部署指南

## 📋 概述

Claude Enhancer 5.1 部署指南涵盖以下核心场景：

### 🎯 部署目标
- **开发环境**：本地开发和调试
- **测试环境**：集成测试和质量保证
- **预发布环境**：生产前验证
- **生产环境**：高可用、高性能部署

### 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Enhancer 5.1                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  8-Phase    │  │  61-Agent   │  │   Quality   │         │
│  │  Workflow   │  │   System    │  │    Gates    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│              智能加载策略 + Hook系统                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Config    │  │    Cache    │  │ Monitoring  │         │
│  │  Management │  │   System    │  │    Stack    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ 系统要求

### 最低要求
```bash
# 基础环境
Python >= 3.9
Node.js >= 16.0
Git >= 2.30
Docker >= 20.10 (可选)

# 系统资源
RAM: 4GB+ (推荐 8GB+)
Disk: 10GB+ 可用空间
CPU: 2核+ (推荐 4核+)
```

### 推荐配置
```bash
# 高性能环境
Python 3.11+
Node.js 18+
Docker 24+
RAM: 16GB+
SSD: 50GB+
CPU: 8核+
```

## 📦 快速部署

### 1. 源码获取

```bash
# 克隆仓库
git clone https://github.com/your-org/claude-enhancer-5.1.git
cd claude-enhancer-5.1

# 检查版本
git tag -l | grep "v5.1"
git checkout v5.1.0
```

### 2. 环境准备

```bash
# 创建Python虚拟环境
python -m venv claude-env
source claude-env/bin/activate  # Linux/Mac
# 或
claude-env\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
npm install  # 如果有前端组件
```

### 3. 配置初始化

```bash
# 复制配置模板
cp .claude/config/config.template.yaml .claude/config/config.yaml
cp .env.example .env

# 安装Claude Hooks
./.claude/install.sh

# 验证安装
./verify_installation.py
```

### 4. 启动系统

```bash
# 启动Claude Enhancer 5.1
python -m claude_enhancer.main

# 或使用启动脚本
./start.sh

# 验证运行状态
curl http://localhost:8080/health
```

## 🐳 容器化部署

### Docker部署

```bash
# 构建镜像
docker build -t claude-enhancer:5.1.0 .

# 运行容器
docker run -d \
  --name claude-enhancer \
  -p 8080:8080 \
  -v $(pwd)/.claude:/app/.claude \
  -v $(pwd)/projects:/app/projects \
  claude-enhancer:5.1.0

# 检查状态
docker ps
docker logs claude-enhancer
```

### Docker Compose部署

```yaml
# docker-compose.yml
version: '3.8'
services:
  claude-enhancer:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./.claude:/app/.claude
      - ./projects:/app/projects
      - ./logs:/app/logs
    environment:
      - CLAUDE_ENV=production
      - LOG_LEVEL=INFO
    restart: unless-stopped
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

```bash
# 启动服务栈
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## ☸️ Kubernetes部署

### 命名空间创建

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: claude-enhancer
  labels:
    app: claude-enhancer
    version: v5.1
```

### ConfigMap配置

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: claude-enhancer-config
  namespace: claude-enhancer
data:
  config.yaml: |
    system:
      version: "5.1.0"
      mode: "production"
      max_agents: 61
      phases: 8
    
    performance:
      cache_enabled: true
      smart_loading: true
      parallel_execution: true
    
    security:
      hook_validation: true
      quality_gates: true
      audit_logging: true
```

### Deployment配置

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: claude-enhancer
  namespace: claude-enhancer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: claude-enhancer
  template:
    metadata:
      labels:
        app: claude-enhancer
        version: v5.1
    spec:
      containers:
      - name: claude-enhancer
        image: claude-enhancer:5.1.0
        ports:
        - containerPort: 8080
        env:
        - name: CLAUDE_ENV
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        volumeMounts:
        - name: config-volume
          mountPath: /app/.claude/config
        - name: cache-volume
          mountPath: /app/.claude/cache
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config-volume
        configMap:
          name: claude-enhancer-config
      - name: cache-volume
        emptyDir: {}
```

### Service配置

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: claude-enhancer-service
  namespace: claude-enhancer
spec:
  selector:
    app: claude-enhancer
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
  type: LoadBalancer
```

### 部署执行

```bash
# 应用所有配置
kubectl apply -f k8s/

# 检查部署状态
kubectl get pods -n claude-enhancer
kubectl get services -n claude-enhancer

# 查看日志
kubectl logs -f deployment/claude-enhancer -n claude-enhancer

# 端口转发测试
kubectl port-forward -n claude-enhancer service/claude-enhancer-service 8080:80
```

## 🔧 配置管理

### 主配置文件

**位置**: `.claude/config/config.yaml`

```yaml
# Claude Enhancer 5.1 主配置
system:
  version: "5.1.0"
  name: "Claude Enhancer"
  mode: "production"  # development, staging, production
  
workflow:
  phases: 8
  phase_timeout: 300  # 秒
  auto_checkpoint: true
  
agents:
  total_count: 61
  parallel_limit: 8
  selection_strategy: "smart"  # smart, manual, balanced
  
performance:
  cache_enabled: true
  cache_ttl: 3600
  smart_loading: true
  memory_limit: "2GB"
  
security:
  hook_validation: true
  quality_gates: true
  audit_logging: true
  secure_mode: true
  
logging:
  level: "INFO"  # DEBUG, INFO, WARN, ERROR
  format: "structured"  # simple, structured
  rotate: true
  max_size: "100MB"
  max_files: 10
  
monitoring:
  enabled: true
  metrics_port: 9090
  health_check_interval: 30
  performance_tracking: true
```

### 环境变量配置

**位置**: `.env`

```bash
# Claude Enhancer 5.1 环境配置

# 基础配置
CLAUDE_VERSION=5.1.0
CLAUDE_ENV=production
CLAUDE_CONFIG_PATH=.claude/config/config.yaml

# 性能配置
MAX_WORKERS=4
CACHE_SIZE=1000
MEMORY_LIMIT=2048

# 安全配置
SECURE_MODE=true
AUDIT_ENABLED=true
ENCRYPTION_KEY=your-secret-key

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=./logs
LOG_ROTATION=true

# 监控配置
METRICS_ENABLED=true
METRICS_PORT=9090
HEALTH_CHECK_PORT=8081

# 数据库配置（如果使用）
DB_HOST=localhost
DB_PORT=5432
DB_NAME=claude_enhancer
DB_USER=claude
DB_PASSWORD=secure-password

# Redis配置（如果使用）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis-password

# API配置
API_HOST=0.0.0.0
API_PORT=8080
API_TIMEOUT=300

# 开发配置
DEBUG=false
DEV_MODE=false
HOT_RELOAD=false
```

### Hook配置

**位置**: `.claude/hooks/config.yaml`

```yaml
# Claude Hooks 5.1 配置
hooks:
  branch_helper:
    enabled: true
    blocking: false
    timeout: 3000
    triggers: ["phase_0"]
    
  smart_agent_selector:
    enabled: true
    blocking: false
    timeout: 5000
    triggers: ["phase_3"]
    strategies: ["smart", "balanced"]
    
  quality_gate:
    enabled: true
    blocking: false
    timeout: 10000
    triggers: ["phase_4", "phase_5"]
    checks: ["lint", "test", "security"]
    
  performance_monitor:
    enabled: true
    blocking: false
    timeout: 2000
    triggers: ["all_phases"]
    metrics: ["memory", "cpu", "response_time"]
    
  error_handler:
    enabled: true
    blocking: false
    timeout: 5000
    triggers: ["on_error"]
    recovery_strategies: ["retry", "fallback"]
```

## 🚦 部署验证

### 健康检查

```bash
#!/bin/bash
# health_check.sh

echo "🔍 Claude Enhancer 5.1 健康检查"
echo "====================================="

# 1. 系统状态检查
echo "1. 系统状态检查..."
if curl -s http://localhost:8080/health > /dev/null; then
    echo "   ✅ API服务正常"
else
    echo "   ❌ API服务异常"
    exit 1
fi

# 2. 配置文件检查
echo "2. 配置文件检查..."
if [ -f ".claude/config/config.yaml" ]; then
    echo "   ✅ 主配置文件存在"
else
    echo "   ❌ 主配置文件缺失"
    exit 1
fi

# 3. Hook系统检查
echo "3. Hook系统检查..."
if [ -d ".claude/hooks" ] && [ -f ".claude/hooks/config.yaml" ]; then
    echo "   ✅ Hook系统配置正常"
else
    echo "   ❌ Hook系统配置异常"
    exit 1
fi

# 4. Agent系统检查
echo "4. Agent系统检查..."
AGENT_COUNT=$(find .claude/agents -name "*.py" | wc -l)
if [ $AGENT_COUNT -eq 61 ]; then
    echo "   ✅ Agent系统完整 (${AGENT_COUNT}/61)"
else
    echo "   ⚠️  Agent系统不完整 (${AGENT_COUNT}/61)"
fi

# 5. 依赖检查
echo "5. 依赖检查..."
if python -c "import claude_enhancer" 2>/dev/null; then
    echo "   ✅ Python依赖正常"
else
    echo "   ❌ Python依赖异常"
    exit 1
fi

# 6. 性能检查
echo "6. 性能检查..."
START_TIME=$(date +%s%N | cut -b1-13)
RESPONSE=$(curl -s http://localhost:8080/api/v1/ping)
END_TIME=$(date +%s%N | cut -b1-13)
RESPONSE_TIME=$((END_TIME - START_TIME))

if [ $RESPONSE_TIME -lt 1000 ]; then
    echo "   ✅ 响应时间正常 (${RESPONSE_TIME}ms)"
else
    echo "   ⚠️  响应时间较慢 (${RESPONSE_TIME}ms)"
fi

echo "====================================="
echo "🎉 Claude Enhancer 5.1 健康检查完成"
```

### 功能验证

```bash
#!/bin/bash
# functional_test.sh

echo "🧪 Claude Enhancer 5.1 功能验证"
echo "====================================="

# 1. 8-Phase工作流测试
echo "1. 测试8-Phase工作流..."
PHASE_RESPONSE=$(curl -s http://localhost:8080/api/v1/phases)
if echo $PHASE_RESPONSE | grep -q "phase_0\|phase_7"; then
    echo "   ✅ 8-Phase工作流正常"
else
    echo "   ❌ 8-Phase工作流异常"
fi

# 2. Agent系统测试
echo "2. 测试Agent系统..."
AGENT_RESPONSE=$(curl -s http://localhost:8080/api/v1/agents)
if echo $AGENT_RESPONSE | grep -q "61"; then
    echo "   ✅ 61-Agent系统正常"
else
    echo "   ❌ Agent系统异常"
fi

# 3. Hook系统测试
echo "3. 测试Hook系统..."
HOOK_RESPONSE=$(curl -s http://localhost:8080/api/v1/hooks/status)
if echo $HOOK_RESPONSE | grep -q "enabled"; then
    echo "   ✅ Hook系统正常"
else
    echo "   ❌ Hook系统异常"
fi

# 4. 缓存系统测试
echo "4. 测试缓存系统..."
CACHE_RESPONSE=$(curl -s http://localhost:8080/api/v1/cache/status)
if echo $CACHE_RESPONSE | grep -q "active"; then
    echo "   ✅ 缓存系统正常"
else
    echo "   ⚠️  缓存系统可能异常"
fi

# 5. 智能加载测试
echo "5. 测试智能加载..."
LOADING_RESPONSE=$(curl -s http://localhost:8080/api/v1/smart-loading/test)
if echo $LOADING_RESPONSE | grep -q "success"; then
    echo "   ✅ 智能加载正常"
else
    echo "   ⚠️  智能加载可能异常"
fi

echo "====================================="
echo "🎉 Claude Enhancer 5.1 功能验证完成"
```

## 📊 性能优化

### 内存优化

```yaml
# 内存优化配置
performance:
  memory:
    max_heap_size: "2GB"
    gc_strategy: "generational"
    cache_size: "512MB"
    buffer_size: "64MB"
    
  cache:
    enabled: true
    type: "lru"  # lru, lfu, fifo
    max_entries: 10000
    ttl: 3600
    
  smart_loading:
    enabled: true
    chunk_size: 1024
    prefetch: true
    lazy_loading: true
```

### 并发优化

```yaml
# 并发优化配置
performance:
  concurrency:
    max_workers: 8
    thread_pool_size: 16
    async_enabled: true
    queue_size: 1000
    
  agents:
    parallel_limit: 8
    batch_size: 4
    timeout: 300
    retry_count: 3
```

### 网络优化

```yaml
# 网络优化配置
network:
  connection_pool:
    max_connections: 100
    max_per_host: 20
    timeout: 30
    
  compression:
    enabled: true
    algorithm: "gzip"
    level: 6
    
  keep_alive:
    enabled: true
    timeout: 60
```

## 🔄 滚动升级

### 版本升级脚本

```bash
#!/bin/bash
# upgrade.sh

SET -e

CURRENT_VERSION=$(cat .claude/VERSION)
TARGET_VERSION="5.1.0"

echo "🚀 升级 Claude Enhancer ${CURRENT_VERSION} → ${TARGET_VERSION}"
echo "========================================================"

# 1. 备份当前配置
echo "1. 备份当前配置..."
cp -r .claude .claude.backup.$(date +%Y%m%d_%H%M%S)
echo "   ✅ 配置备份完成"

# 2. 下载新版本
echo "2. 下载新版本..."
git fetch origin
git checkout v${TARGET_VERSION}
echo "   ✅ 版本切换完成"

# 3. 更新依赖
echo "3. 更新依赖..."
pip install -r requirements.txt --upgrade
echo "   ✅ 依赖更新完成"

# 4. 迁移配置
echo "4. 迁移配置..."
python .claude/scripts/migrate_config.py --from=${CURRENT_VERSION} --to=${TARGET_VERSION}
echo "   ✅ 配置迁移完成"

# 5. 验证升级
echo "5. 验证升级..."
python -c "import claude_enhancer; print(f'版本: {claude_enhancer.__version__}')"
echo "   ✅ 升级验证完成"

# 6. 重启服务
echo "6. 重启服务..."
./restart.sh
echo "   ✅ 服务重启完成"

echo "========================================================"
echo "🎉 升级完成！Claude Enhancer ${TARGET_VERSION} 已就绪"
```

### Kubernetes滚动升级

```bash
# K8s滚动升级
kubectl set image deployment/claude-enhancer \
  claude-enhancer=claude-enhancer:5.1.0 \
  -n claude-enhancer

# 监控滚动升级状态
kubectl rollout status deployment/claude-enhancer -n claude-enhancer

# 如果需要回滚
kubectl rollout undo deployment/claude-enhancer -n claude-enhancer
```

## 📈 监控告警

### Prometheus配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "claude_enhancer_rules.yml"

scrape_configs:
  - job_name: 'claude-enhancer'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 10s
    metrics_path: /metrics
```

### Grafana仪表板

```json
{
  "dashboard": {
    "title": "Claude Enhancer 5.1 监控",
    "panels": [
      {
        "title": "系统健康度",
        "type": "stat",
        "targets": [
          {
            "expr": "claude_enhancer_health_status"
          }
        ]
      },
      {
        "title": "8-Phase执行状态",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(claude_enhancer_phase_duration[5m])"
          }
        ]
      },
      {
        "title": "Agent使用情况",
        "type": "heatmap",
        "targets": [
          {
            "expr": "claude_enhancer_agent_usage"
          }
        ]
      }
    ]
  }
}
```

## 🛡️ 安全加固

### 访问控制

```yaml
# 安全配置
security:
  authentication:
    enabled: true
    method: "jwt"  # jwt, oauth, basic
    secret_key: "your-secret-key"
    token_ttl: 3600
    
  authorization:
    enabled: true
    rbac: true
    permissions:
      - role: "admin"
        actions: ["*"]
      - role: "user"
        actions: ["read", "execute"]
      - role: "guest"
        actions: ["read"]
        
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"
    key_rotation: 86400  # 24小时
    
  audit:
    enabled: true
    log_all_requests: true
    retention_days: 90
    
  rate_limiting:
    enabled: true
    requests_per_minute: 100
    burst_size: 200
```

### 网络安全

```yaml
# 网络安全配置
network_security:
  tls:
    enabled: true
    cert_file: "/etc/ssl/certs/claude-enhancer.crt"
    key_file: "/etc/ssl/private/claude-enhancer.key"
    min_version: "TLSv1.2"
    
  firewall:
    enabled: true
    allowed_ips:
      - "10.0.0.0/8"
      - "192.168.0.0/16"
      - "172.16.0.0/12"
    blocked_ips: []
    
  cors:
    enabled: true
    allowed_origins:
      - "https://your-domain.com"
    allowed_methods: ["GET", "POST", "PUT", "DELETE"]
    allowed_headers: ["Content-Type", "Authorization"]
```

---

**📝 部署总结**

Claude Enhancer 5.1 提供了完整的部署解决方案：

✅ **多环境支持** - 开发、测试、生产环境
✅ **容器化部署** - Docker & Kubernetes支持
✅ **配置管理** - 灵活的配置系统
✅ **健康监控** - 完整的监控告警体系
✅ **安全加固** - 多层安全防护
✅ **滚动升级** - 零停机升级方案

**🔗 相关文档**
- [运维手册 OPERATIONS.md](OPERATIONS.md)
- [故障排除 TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [版本发布说明 RELEASE_NOTES.md](RELEASE_NOTES.md)
