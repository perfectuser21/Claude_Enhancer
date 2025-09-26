# Claude Enhancer 5.1 部署指南

## 📖 快速开始

### 🚀 执行部署

```bash
# 1. 进入部署目录
cd /home/xx/dev/Claude\ Enhancer\ 5.0/deployment

# 2. 设置环境变量
export SLACK_WEBHOOK_URL="your-slack-webhook-url"
export PAGERDUTY_KEY="your-pagerduty-key"

# 3. 执行部署
./deploy-5.1.sh
```

### 🚨 紧急回滚

```bash
# 立即回滚（跳过确认）
./emergency-rollback.sh -r "error_rate_high" -f

# 交互式回滚
./emergency-rollback.sh -r "agent_coordination_failed"
```

## 📁 文件结构

```
deployment/
├── deploy-5.1.sh                    # 主部署脚本
├── emergency-rollback.sh            # 紧急回滚脚本
├── deployment-config.yaml           # 部署配置
├── monitoring-dashboard.json        # Grafana仪表板
├── README.md                        # 本文件
└── k8s/                             # Kubernetes配置
    ├── canary-deployment.yaml       # 金丝雀部署
    ├── virtual-service-canary-5.yaml # 5%流量配置
    ├── virtual-service-canary-20.yaml # 20%流量配置
    ├── virtual-service-canary-50.yaml # 50%流量配置
    └── virtual-service-stable.yaml  # 稳定版本配置
```

## 🎯 部署策略概览

### 混合蓝绿-金丝雀部署

1. **Phase 1** (30分钟): 金丝雀启动 - 5%流量
2. **Phase 2** (45分钟): 金丝雀扩展 - 20%流量
3. **Phase 3** (30分钟): 蓝绿准备 - 50%流量
4. **Phase 4** (15分钟): 完全切换 - 100%流量

### 关键特性

- ✅ **零停机部署**: 渐进式流量切换
- ✅ **自动回滚**: 30秒内完成回滚
- ✅ **全面监控**: 实时健康检查
- ✅ **Agent协调**: 61个专业Agent协调
- ✅ **工作流保持**: 8-Phase工作流连续性

## 📊 监控仪表板

### Grafana仪表板导入

```bash
# 导入仪表板
kubectl create configmap grafana-dashboard \
  --from-file=monitoring-dashboard.json \
  -n monitoring
```

### 关键监控指标

- **错误率**: < 0.1%
- **P95响应时间**: < 500ms
- **Agent可用性**: > 99%
- **工作流成功率**: > 98%

## 🔧 配置说明

### 环境变量

| 变量名 | 描述 | 必需 |
|--------|------|------|
| `SLACK_WEBHOOK_URL` | Slack通知地址 | 否 |
| `PAGERDUTY_KEY` | PagerDuty集成密钥 | 否 |
| `PROMETHEUS_URL` | Prometheus服务地址 | 否 |

### 回滚触发条件

- 错误率 > 0.5%
- P95响应时间 > 1秒
- Agent失败数 > 5个
- 工作流错误 > 10个
- 内存使用率 > 90%
- CPU使用率 > 85%

## 🚨 故障排除

### 常见问题

#### 1. 部署卡在Phase 1

```bash
# 检查金丝雀Pod状态
kubectl get pods -l version=5.1

# 查看Pod日志
kubectl logs -l version=5.1 -f

# 检查健康检查端点
curl http://claude-enhancer.example.com/health
```

#### 2. Agent协调失败

```bash
# 检查Agent配置
kubectl get configmap claude-enhancer-5.1-agents

# 查看Agent状态
kubectl exec -it <pod-name> -- curl localhost:9091/metrics
```

#### 3. 流量路由异常

```bash
# 检查VirtualService
kubectl get virtualservice claude-enhancer-canary-5 -o yaml

# 检查DestinationRule
kubectl get destinationrule claude-enhancer-destination -o yaml
```

### 日志位置

- **部署日志**: `deployment-YYYYMMDD_HHMMSS.log`
- **回滚日志**: `rollback-YYYYMMDD_HHMMSS.log`
- **Kubernetes日志**: `kubectl logs -l app=claude-enhancer`

## 📋 部署前检查清单

### 环境准备

- [ ] Kubernetes集群可访问
- [ ] Docker镜像已构建 (`claude-enhancer:5.1`)
- [ ] 配置文件已更新
- [ ] 监控系统正常运行
- [ ] 通知渠道已配置

### 资源检查

- [ ] 节点资源充足 (CPU < 70%, Memory < 80%)
- [ ] 存储空间充足
- [ ] 网络连通性正常
- [ ] DNS解析正确

### 团队协调

- [ ] 所有团队成员就位
- [ ] 通讯渠道建立
- [ ] 回滚权限确认
- [ ] 紧急联系人列表更新

## 📞 紧急联系信息

### 团队角色

- **部署负责人**: deployment-lead@example.com
- **技术负责人**: tech-lead@example.com
- **SRE工程师**: sre@example.com
- **质量保证**: qa-lead@example.com

### 通讯渠道

- **Slack**: `#claude-enhancer-deployment`
- **PagerDuty**: `claude-enhancer-critical`
- **会议室**: `deployment-war-room`

## 📈 成功标准

### 技术指标

- 错误率 < 0.1%
- P95响应时间 < 500ms
- 可用性 >= 99.9%
- Agent可用性 >= 99%

### 业务指标

- 用户满意度 >= 95%
- 任务完成率 >= 98%
- 工作流中断率 < 1%

## 🎉 部署后操作

### 立即验证

1. 访问应用首页确认正常
2. 执行关键业务流程测试
3. 检查所有61个Agent状态
4. 验证8-Phase工作流正常

### 持续监控

1. 监控系统72小时
2. 收集用户反馈
3. 分析性能数据
4. 更新部署文档

### 清理工作

1. 删除旧版本实例
2. 清理临时资源
3. 归档部署日志
4. 更新系统文档

## 📚 相关文档

- [Claude Enhancer 5.1 部署策略文档](./CLAUDE_ENHANCER_5.1_DEPLOYMENT_STRATEGY.md)
- [紧急回滚程序](./emergency-rollback.sh)
- [监控仪表板配置](./monitoring-dashboard.json)
- [Kubernetes配置文件](./k8s/)

---

**最后更新**: 2025-09-26
**版本**: 5.1.0
**维护团队**: Claude Enhancer DevOps Team