# 🚀 Claude Enhancer 监控和告警系统

完整的监控、观测和告警解决方案，专门为Claude Enhancer Hook系统设计。

## ✨ 功能特性

### 🔍 全面监控
- **Hook执行监控**: 实时追踪Hook执行时间、成功率、错误率
- **系统资源监控**: CPU、内存、磁盘使用率监控
- **性能指标**: P50/P95/P99延迟统计和趋势分析
- **容器监控**: Docker容器资源使用情况

### 📊 可视化Dashboard
- **实时Dashboard**: Web界面实时显示关键指标
- **Grafana集成**: 专业的可视化和告警Dashboard
- **交互式图表**: 支持时间范围选择和钻取分析
- **移动端适配**: 响应式设计支持移动设备

### 🚨 智能告警
- **多级告警**: Warning/Critical告警级别
- **智能阈值**: 基于历史数据的动态阈值
- **告警聚合**: 避免告警风暴的智能聚合
- **多渠道通知**: 支持邮件、Slack、Webhook等

### 📈 性能分析
- **趋势分析**: 自动检测性能趋势变化
- **异常检测**: 基于统计的异常检测算法
- **瓶颈识别**: 自动识别性能瓶颈
- **容量规划**: 基于历史数据的容量预测

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Enhancer 监控架构                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Hooks     │───▶│  Monitor    │───▶│  Dashboard  │     │
│  │ Execution   │    │  Collector  │    │   (Web UI)  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                              │
│         ▼                   ▼                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │Performance  │    │ Prometheus  │    │   Grafana   │     │
│  │  Logs       │    │ (Metrics)   │    │(Visualization)│    │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │          │
│         ▼                   ▼                   ▼          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │    Loki     │    │AlertManager │    │   Reports   │     │
│  │ (Log Store) │    │ (Alerting)  │    │(Analysis)   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📋 组件说明

### 核心监控组件
- **Claude Enhancer Monitor**: 主监控应用，提供Web Dashboard和API
- **Performance Collector**: 专门收集Hook性能数据
- **Prometheus**: 时序数据库，存储和查询指标
- **Grafana**: 可视化平台，展示Dashboard和图表

### 数据收集组件
- **Node Exporter**: 系统指标收集
- **cAdvisor**: 容器指标收集
- **Promtail**: 日志收集和转发
- **Blackbox Exporter**: 端点可用性监控

### 存储和告警
- **Loki**: 日志聚合和存储
- **AlertManager**: 告警管理和通知
- **SQLite**: 本地数据存储和缓存

## 🚀 快速开始

### 1. 一键部署
```bash
# 进入监控目录
cd .claude/monitoring

# 一键部署完整监控栈
./deploy_monitoring.sh deploy
```

### 2. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| Claude Enhancer Dashboard | http://localhost:8091 | 主监控界面 |
| Grafana | http://localhost:3001 | 专业可视化 (admin/admin123) |
| Prometheus | http://localhost:9090 | 指标查询界面 |
| AlertManager | http://localhost:9093 | 告警管理界面 |

### 3. 管理命令
```bash
# 查看服务状态
./deploy_monitoring.sh status

# 查看日志
./deploy_monitoring.sh logs

# 停止服务
./deploy_monitoring.sh stop

# 重启服务
./deploy_monitoring.sh restart

# 清理资源
./deploy_monitoring.sh cleanup
```

## 📊 监控指标

### Hook性能指标
- `claude_enhancer_hook_executions_total`: Hook执行总次数
- `claude_enhancer_hook_duration_seconds`: Hook执行时间分布
- `claude_enhancer_hook_errors_total`: Hook错误总次数
- `claude_enhancer_active_hooks`: 当前活跃Hook数量
- `claude_enhancer_queue_size`: Hook队列大小

### 系统资源指标
- `claude_enhancer_cpu_usage_percent`: CPU使用率
- `claude_enhancer_memory_usage_percent`: 内存使用率
- `claude_enhancer_disk_usage_percent`: 磁盘使用率

### 业务指标
- Hook成功率和错误率
- P50/P95/P99延迟统计
- 吞吐量和QPS
- 性能趋势分析

## 🚨 告警规则

### 性能告警
- **高延迟告警**: P95延迟 > 5秒 (Warning) / 10秒 (Critical)
- **高错误率告警**: 错误率 > 5% (Warning) / 20% (Critical)
- **Hook失败告警**: 5分钟内失败3次以上
- **性能下降告警**: 延迟持续增长超过阈值

### 资源告警
- **高CPU使用率**: > 80% (Warning) / 95% (Critical)
- **高内存使用率**: > 85% (Warning) / 95% (Critical)
- **高磁盘使用率**: > 80% (Warning) / 90% (Critical)

### 服务告警
- **服务宕机告警**: 监控服务不可达
- **健康检查失败**: 端点健康检查失败
- **数据收集停止**: 超过5分钟未收集到数据

## 🔧 配置说明

### 监控配置
编辑 `monitoring_config.yaml` 调整监控参数:
```yaml
monitoring:
  enabled: true
  metrics_interval: 5  # 指标收集间隔(秒)
  data_retention_days: 7  # 数据保留天数

alerts:
  channels:
    console:
      enabled: true
    webhook:
      enabled: false
      url: "your-webhook-url"
```

### 告警配置
编辑 `alertmanager.claude.yml` 配置告警通知:
```yaml
receivers:
  - name: 'claude-enhancer-alerts'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#alerts'
```

### Dashboard配置
- Grafana Dashboard: 导入 `grafana_dashboard.json`
- 自定义指标: 编辑 `prometheus.claude.yml`
- 记录规则: 编辑 `alert_rules.claude.yml`

## 📈 使用场景

### 1. 实时监控
- 在Dashboard上实时查看Hook执行状态
- 监控系统资源使用情况
- 观察性能指标变化趋势

### 2. 性能优化
- 识别执行慢的Hook
- 分析性能瓶颈
- 优化Hook执行策略

### 3. 故障排查
- 快速定位问题Hook
- 查看错误日志和堆栈
- 分析故障时间线

### 4. 容量规划
- 基于历史数据预测资源需求
- 制定扩容计划
- 优化资源配置

## 🔍 故障排查

### 常见问题

1. **监控服务无法启动**
   ```bash
   # 检查端口占用
   ./deploy_monitoring.sh status

   # 查看详细日志
   ./deploy_monitoring.sh logs
   ```

2. **指标数据缺失**
   ```bash
   # 检查Hook性能日志
   tail -f .claude/logs/performance.log

   # 检查收集器状态
   ./deploy_monitoring.sh logs performance-collector
   ```

3. **告警不工作**
   ```bash
   # 检查AlertManager配置
   curl http://localhost:9093/api/v1/status

   # 检查告警规则
   curl http://localhost:9090/api/v1/rules
   ```

### 调试模式
启用调试模式获取更多信息:
```bash
# 修改配置文件
vim monitoring_config.yaml

debug:
  enabled: true
  verbose_logging: true
```

## 📚 扩展开发

### 自定义指标
添加新的监控指标:
```python
# 在 claude_enhancer_monitor.py 中添加
custom_metric = Counter(
    'claude_enhancer_custom_metric',
    'Custom metric description',
    ['label1', 'label2']
)
```

### 自定义告警
添加新的告警规则:
```yaml
# 在 alert_rules.claude.yml 中添加
- alert: CustomAlert
  expr: custom_metric > threshold
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Custom alert description"
```

### 自定义Dashboard
创建新的Grafana面板:
1. 访问 http://localhost:3001
2. 创建新Dashboard
3. 添加Panel和查询
4. 导出JSON配置

## 🤝 贡献指南

### 开发环境
```bash
# 安装开发依赖
pip install -r requirements.monitor.txt

# 运行监控应用
python claude_enhancer_monitor.py

# 运行性能收集器
python performance_collector.py
```

### 测试
```bash
# 运行集成测试
./deploy_monitoring.sh deploy
./deploy_monitoring.sh status

# 生成测试数据
python test_data_generator.py
```

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 🆘 支持

- 问题报告: 请在项目Issues中提交
- 功能请求: 请在项目Discussions中讨论
- 文档改进: 欢迎提交PR

---

**Claude Enhancer 监控系统** - 让你的Hook执行清晰可见，性能优化有据可依！ 🚀