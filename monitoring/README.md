# Perfect21 Monitoring System

## 🎯 概述

Perfect21 监控系统是一个完整的可观测性解决方案，提供以下核心功能：

- **📊 指标收集** - Prometheus格式的业务和系统指标
- **🔍 分布式追踪** - 基于OpenTelemetry的请求追踪
- **🏥 健康检查** - 多层级健康状态监控
- **📈 性能仪表板** - Grafana可视化面板
- **🚨 智能告警** - 多渠道告警通知系统
- **📝 审计日志** - 完整的操作审计记录

## 🏗️ 架构设计

```
Perfect21 Monitoring Stack
├── 数据收集层
│   ├── Metrics Collector (Prometheus格式)
│   ├── Trace Exporter (OpenTelemetry)
│   ├── Health Checker (多维度检查)
│   └── Audit Logger (合规审计)
├── 数据存储层
│   ├── Prometheus (指标存储)
│   ├── Jaeger (追踪存储)
│   ├── Loki (日志存储)
│   └── 文件存储 (审计日志)
├── 数据处理层
│   ├── Alert Manager (告警规则)
│   ├── Recording Rules (预计算)
│   └── Data Retention (数据保留)
└── 展示层
    ├── Grafana (仪表板)
    ├── Jaeger UI (追踪界面)
    └── Custom APIs (自定义接口)
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 创建必要目录
mkdir -p logs/audit logs/traces monitoring/dashboards
```

### 2. 基础使用

```python
from monitoring import start_monitoring_system

# 启动完整监控系统
config = {
    'metrics': {'port': 8080, 'update_interval': 30},
    'tracing': {'service_name': 'perfect21'},
    'health': {'interval': 60},
    'alerting': {'slack_webhook': 'your-webhook-url'},
    'dashboards': {'generate': True}
}

start_monitoring_system(config)
```

### 3. Docker 部署

```bash
# 启动完整监控栈
cd monitoring/
docker-compose -f docker-compose.monitoring.yml up -d

# 访问服务
# Grafana: http://localhost:3000 (admin/perfect21admin)
# Prometheus: http://localhost:9090
# Jaeger: http://localhost:16686
# AlertManager: http://localhost:9093
```

## 📊 指标收集

### 系统指标
- CPU使用率、内存使用量、磁盘空间
- 网络流量、系统负载
- 应用运行时间

### API指标
- 请求速率、响应时间分布
- 错误率、状态码分布
- 并发连接数

### Agent执行指标
- 执行次数、成功率
- 执行时间分布
- 并行工作流性能

### Git工作流指标
- Git操作频率
- Hook执行状态
- 代码质量指标

### 业务指标
- 活跃用户数
- 工作空间数量
- 功能使用率

## 🔍 分布式追踪

### 自动追踪
```python
# HTTP请求自动追踪
app.add_middleware(Perfect21TracingMiddleware)

# Agent执行追踪
with trace_agent_execution("agent_name", "task") as span:
    # 执行逻辑
    pass
```

### 手动追踪
```python
from monitoring import start_span

with start_span("custom_operation") as span:
    span.set_tag("user_id", user_id)
    span.set_tag("operation_type", "data_processing")
    # 业务逻辑
```

### 追踪上下文传播
```python
# HTTP头注入
headers = tracer.inject_context(headers)

# 跨服务传播
parent_context = tracer.extract_context(request.headers)
```

## 🏥 健康检查

### 内置检查
- **系统资源** - CPU、内存、磁盘使用率
- **数据库连接** - SQLite/PostgreSQL连接测试
- **Git仓库** - 仓库状态、提交信息
- **Perfect21组件** - 核心模块可用性
- **外部服务** - 第三方服务连通性

### 自定义检查
```python
from monitoring import HealthCheck, HealthStatus

class CustomHealthCheck(HealthCheck):
    async def _perform_check(self):
        # 自定义检查逻辑
        return HealthCheckResult(
            name="custom_check",
            status=HealthStatus.HEALTHY,
            message="Everything is fine"
        )

health_checker.add_check(CustomHealthCheck())
```

## 📈 仪表板配置

### 预置仪表板
1. **系统概览** - 整体状态和关键指标
2. **Agent性能** - Agent执行详细分析
3. **质量监控** - 代码质量和测试指标
4. **基础设施** - 系统资源和服务状态
5. **SLA监控** - 服务等级协议合规性
6. **业务指标** - 用户和业务KPI

### 自定义面板
```python
from monitoring import GrafanaDashboardGenerator

generator = GrafanaDashboardGenerator()
dashboard = generator.create_overview_dashboard()

# 保存配置
with open('custom-dashboard.json', 'w') as f:
    json.dump(dashboard, f, indent=2)
```

## 🚨 告警系统

### 默认告警规则
- **高CPU使用率** (>90%, 5分钟)
- **高API延迟** (>2秒, 2分钟)
- **高错误率** (>10/分钟, 1分钟)
- **长时间Agent执行** (>5分钟, 1分钟)

### 通知渠道
```python
# Slack通知
configure_slack_notifications(
    webhook_url="https://hooks.slack.com/...",
    channel="#alerts"
)

# 邮件通知
configure_email_notifications(
    smtp_config={
        'host': 'smtp.gmail.com',
        'port': 587,
        'username': 'your-email@gmail.com',
        'password': 'app-password'
    },
    to_emails=['admin@perfect21.com']
)

# Webhook通知
configure_webhook_notifications(
    url="https://your-webhook-endpoint.com/alerts"
)
```

### 自定义告警
```python
from monitoring import fire_custom_alert

fire_custom_alert(
    name="CustomAlert",
    message="Something needs attention",
    severity="warning",
    labels={"component": "business_logic"},
    annotations={"runbook": "https://wiki.com/runbook"}
)
```

## 📝 审计日志

### 自动记录
- 用户登录/登出
- API请求/响应
- Agent执行
- Git操作
- 系统事件

### 手动记录
```python
from monitoring import audit_logger

# 记录用户操作
audit_logger.log_user_event(
    event_type=AuditEventType.USER_ACTION,
    user_id="user123",
    action="data_export",
    resource="customer_data",
    result="success"
)

# 记录安全事件
audit_logger.log_security_event(
    event_type=AuditEventType.SECURITY_VIOLATION,
    action="unauthorized_access",
    result="blocked",
    source_ip="192.168.1.100"
)
```

### 审计查询
```python
# 查询特定用户的操作
events = audit_logger.query_events(
    users=["user123"],
    time_range=(start_time, end_time)
)

# 获取安全事件
security_events = audit_logger.query_events(
    event_types=[AuditEventType.SECURITY_VIOLATION],
    levels=[AuditLevel.WARNING, AuditLevel.CRITICAL]
)
```

## 🔧 配置说明

### 指标配置
```python
metrics_config = {
    'port': 8080,                    # 指标暴露端口
    'update_interval': 30,           # 系统指标更新间隔(秒)
    'retention_period': '30d',       # 数据保留期
    'custom_labels': {               # 自定义标签
        'environment': 'production',
        'version': '1.0.0'
    }
}
```

### 追踪配置
```python
tracing_config = {
    'service_name': 'perfect21',     # 服务名称
    'jaeger_host': 'localhost:6831', # Jaeger Agent地址
    'sampling_rate': 0.1,            # 采样率 (10%)
    'file_output': 'logs/traces.jsonl', # 文件输出路径
    'max_spans': 10000               # 内存中最大span数
}
```

### 健康检查配置
```python
health_config = {
    'interval': 60,                  # 检查间隔(秒)
    'timeout': 30,                   # 单个检查超时(秒)
    'cpu_threshold': 90,             # CPU阈值(%)
    'memory_threshold': 90,          # 内存阈值(%)
    'disk_threshold': 85             # 磁盘阈值(%)
}
```

### 告警配置
```python
alerting_config = {
    'evaluation_interval': 30,      # 规则评估间隔(秒)
    'group_wait': 10,               # 告警分组等待时间(秒)
    'group_interval': 300,          # 分组告警间隔(秒)
    'repeat_interval': 3600,        # 重复告警间隔(秒)
    'notification_timeout': 30      # 通知超时(秒)
}
```

## 📊 监控最佳实践

### 1. 指标设计原则
- **RED方法** - Rate, Errors, Duration
- **USE方法** - Utilization, Saturation, Errors
- **四个黄金信号** - 延迟、流量、错误、饱和度

### 2. 告警设计原则
- **症状导向** - 关注用户影响，不是原因
- **可操作性** - 每个告警都应该有明确的处理步骤
- **降噪** - 避免告警疲劳
- **分级** - 根据严重程度分级处理

### 3. 仪表板设计
- **概览优先** - 从高层次开始，支持下钻
- **时间对齐** - 所有面板使用相同时间范围
- **注释支持** - 标记部署、事件等关键时间点
- **移动友好** - 支持移动设备访问

### 4. 追踪策略
- **智能采样** - 根据服务重要性调整采样率
- **上下文传播** - 确保跨服务追踪连续性
- **标签规范** - 统一的标签命名约定
- **性能考虑** - 避免追踪影响业务性能

## 🔍 故障排查

### 常见问题

#### 1. 指标缺失
```bash
# 检查指标收集器状态
curl http://localhost:8080/metrics

# 检查Prometheus配置
docker exec perfect21-prometheus promtool check config /etc/prometheus/prometheus.yml
```

#### 2. 追踪数据不完整
```python
# 检查追踪配置
from monitoring import get_trace_summary
summary = get_trace_summary()
print(summary)
```

#### 3. 告警不触发
```bash
# 检查告警规则
curl http://localhost:9090/api/v1/rules

# 检查AlertManager状态
curl http://localhost:9093/api/v1/status
```

#### 4. 健康检查失败
```python
# 运行单个健康检查
from monitoring import run_health_check
result = await run_health_check("system_resources")
print(result)
```

## 📚 API参考

### 指标API
```python
# 记录自定义指标
from monitoring import metrics_collector

metrics_collector.record_api_request("GET", "/api/users", 200, 0.5)
metrics_collector.record_agent_execution("my-agent", "success", 2.3)
metrics_collector.update_active_users(150)
```

### 追踪API
```python
# 创建Span
from monitoring import tracer

with tracer.span("database_query") as span:
    span.set_tag("query_type", "SELECT")
    span.set_tag("table", "users")
    # 数据库操作
```

### 健康检查API
```python
# 异步健康检查
from monitoring import run_health_checks

health_results = await run_health_checks()
print(f"Overall status: {health_results['status']}")
```

### 告警API
```python
# 触发告警
from monitoring import fire_custom_alert

fire_custom_alert(
    name="DataProcessingDelay",
    message="Data processing is taking longer than expected",
    severity="warning"
)
```

### 审计API
```python
# 记录审计事件
from monitoring import log_user_login, log_api_request

log_user_login("user123", "192.168.1.100", success=True)
log_api_request("POST", "/api/data", 201, user_id="user123")
```

## 🛠️ 高级配置

### 自定义指标
```python
from prometheus_client import Counter, Histogram

# 定义自定义指标
business_operations = Counter(
    'business_operations_total',
    'Total business operations',
    ['operation_type', 'status']
)

# 使用指标
business_operations.labels(
    operation_type='data_export',
    status='success'
).inc()
```

### 自定义追踪
```python
from monitoring import Perfect21Tracer

# 创建自定义追踪器
custom_tracer = Perfect21Tracer("my-service")

with custom_tracer.span("complex_operation") as span:
    span.set_tag("complexity", "high")
    # 复杂操作
```

### 自定义健康检查
```python
from monitoring import HealthCheck, HealthStatus

class DatabaseHealthCheck(HealthCheck):
    async def _perform_check(self):
        # 数据库连接检查
        try:
            # 连接测试
            return HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database connection OK"
            )
        except Exception as e:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {e}"
            )
```

## 📈 性能调优

### 指标优化
- 使用合适的桶大小（Histogram）
- 避免高基数标签
- 定期清理过期指标
- 使用记录规则预计算

### 追踪优化
- 智能采样策略
- 异步span处理
- 批量导出
- 内存管理

### 存储优化
- 配置合适的保留期
- 使用压缩
- 定期备份
- 监控存储使用

## 🔐 安全考虑

### 访问控制
- 配置Grafana认证
- 限制Prometheus访问
- 使用HTTPS传输
- API密钥管理

### 数据保护
- 敏感数据脱敏
- 审计日志加密
- 访问日志记录
- 合规性要求

## 📞 支持与贡献

### 获取帮助
- 查看文档和示例
- 检查已知问题
- 社区讨论

### 贡献代码
- Fork项目
- 创建特性分支
- 提交Pull Request
- 参与代码审查

## 📄 许可证

MIT License - 详见 LICENSE 文件