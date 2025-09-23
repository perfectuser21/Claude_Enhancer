# 🔄 Claude Enhancer 回滚应急方案

> 确保快速、安全回滚的完整应急方案

## 📋 回滚方案概览

### 🎯 回滚目标
- **RTO (恢复时间目标)**: < 5分钟
- **RPO (恢复点目标)**: < 1分钟
- **可用性目标**: 99.9%
- **数据一致性**: 100%

### ⚡ 回滚触发条件
1. **系统指标异常**
   - 错误率 > 5%
   - 响应时间 > 2000ms
   - 系统可用性 < 99%
   - CPU/内存使用率 > 90%

2. **功能故障**
   - 核心 Agent 系统失效
   - Hook 系统无响应
   - 数据库连接故障
   - 认证系统故障

3. **安全问题**
   - 检测到安全漏洞
   - 异常访问模式
   - 数据泄露风险
   - 恶意攻击迹象

4. **业务影响**
   - 用户投诉激增
   - 关键业务流程中断
   - 数据丢失或损坏
   - 监管合规问题

## 🚨 应急响应流程

### Phase 1: 问题识别与确认 (0-2分钟)

#### 自动监控告警
```bash
# 关键监控指标
- 应用错误率: > 5%
- API 响应时间: > 2000ms
- 系统可用性: < 99%
- 数据库连接: 失败率 > 1%
```

#### 人工验证步骤
```bash
# 1. 健康检查
curl -f http://localhost:8080/health || echo "服务异常"

# 2. 数据库连接测试
docker exec postgres-container pg_isready -h localhost -p 5432

# 3. 关键功能验证
bash .claude/scripts/quick_functionality_test.sh

# 4. 日志错误检查
tail -n 100 /var/log/perfect21/error.log | grep -E "ERROR|FATAL"
```

### Phase 2: 回滚决策 (2-3分钟)

#### 决策矩阵
| 影响程度 | 影响范围 | 回滚决策 | 执行时间 |
|----------|----------|----------|----------|
| 高 | 全部用户 | 立即回滚 | < 5分钟 |
| 高 | 部分用户 | 金丝雀回滚 | < 10分钟 |
| 中 | 全部用户 | 计划回滚 | < 15分钟 |
| 中 | 部分用户 | 监控观察 | 持续监控 |
| 低 | 任何范围 | 热修复 | < 30分钟 |

#### 决策权限
- **自动回滚**: 系统自动触发（错误率 > 10%）
- **技术负责人**: 可独立决策回滚（影响 < 50% 用户）
- **业务负责人**: 重大回滚决策（影响 > 50% 用户）
- **紧急回滚**: 任何团队成员（安全问题）

### Phase 3: 回滚执行 (3-5分钟)

## 🔧 回滚执行方案

### 方案A: 蓝绿部署回滚

#### 自动回滚脚本
```bash
#!/bin/bash
# 文件: deployment/scripts/auto_rollback.sh

set -euo pipefail

# 配置变量
NAMESPACE="claude-enhancer"
BLUE_VERSION=$(kubectl get deployment blue-deployment -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d':' -f2)
GREEN_VERSION=$(kubectl get deployment green-deployment -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d':' -f2)

echo "🔄 开始蓝绿部署回滚..."
echo "当前蓝版本: $BLUE_VERSION"
echo "当前绿版本: $GREEN_VERSION"

# 1. 确定当前活动版本
CURRENT_ACTIVE=$(kubectl get service claude-enhancer-service -n $NAMESPACE -o jsonpath='{.spec.selector.version}')
echo "当前活动版本: $CURRENT_ACTIVE"

# 2. 切换到备用版本
if [ "$CURRENT_ACTIVE" = "blue" ]; then
    TARGET_VERSION="green"
    TARGET_DEPLOYMENT="green-deployment"
else
    TARGET_VERSION="blue"
    TARGET_DEPLOYMENT="blue-deployment"
fi

echo "🎯 切换到版本: $TARGET_VERSION"

# 3. 验证目标版本健康状态
echo "🔍 验证目标版本健康状态..."
kubectl rollout status deployment/$TARGET_DEPLOYMENT -n $NAMESPACE --timeout=60s

# 4. 健康检查
HEALTH_CHECK_URL="http://$(kubectl get service claude-enhancer-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}'):8080/health"
for i in {1..5}; do
    if curl -f $HEALTH_CHECK_URL > /dev/null 2>&1; then
        echo "✅ 健康检查通过 (尝试 $i/5)"
        break
    fi
    if [ $i -eq 5 ]; then
        echo "❌ 健康检查失败，回滚中止"
        exit 1
    fi
    echo "⏳ 健康检查失败，重试中... ($i/5)"
    sleep 5
done

# 5. 更新服务选择器
echo "🔄 更新服务路由..."
kubectl patch service claude-enhancer-service -n $NAMESPACE -p '{"spec":{"selector":{"version":"'$TARGET_VERSION'"}}}'

# 6. 验证回滚成功
echo "🔍 验证回滚结果..."
sleep 10
NEW_ACTIVE=$(kubectl get service claude-enhancer-service -n $NAMESPACE -o jsonpath='{.spec.selector.version}')
if [ "$NEW_ACTIVE" = "$TARGET_VERSION" ]; then
    echo "✅ 回滚成功! 当前活动版本: $NEW_ACTIVE"
else
    echo "❌ 回滚失败! 当前版本: $NEW_ACTIVE, 期望版本: $TARGET_VERSION"
    exit 1
fi

# 7. 发送通知
echo "📢 发送回滚通知..."
curl -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-type: application/json' \
  --data '{"text":"🔄 Claude Enhancer 已成功回滚到版本: '$TARGET_VERSION'"}'

echo "🎉 回滚完成!"
```

### 方案B: 金丝雀部署回滚

#### 逐步回滚脚本
```bash
#!/bin/bash
# 文件: deployment/scripts/canary_rollback.sh

set -euo pipefail

NAMESPACE="claude-enhancer"
ROLLBACK_STAGES=(100 75 50 25 0)  # 回滚比例

echo "🔄 开始金丝雀回滚..."

for stage in "${ROLLBACK_STAGES[@]}"; do
    echo "📊 设置新版本流量比例: ${stage}%"

    # 更新 Istio 流量分配
    kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: claude-enhancer-vs
  namespace: $NAMESPACE
spec:
  hosts:
  - claude-enhancer-service
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: claude-enhancer-service
        subset: canary
      weight: $stage
    - destination:
        host: claude-enhancer-service
        subset: stable
      weight: $((100 - stage))
  - route:
    - destination:
        host: claude-enhancer-service
        subset: stable
      weight: 100
EOF

    echo "⏳ 等待流量分配生效..."
    sleep 30

    # 验证指标
    echo "📊 检查关键指标..."
    ERROR_RATE=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~'5..'}[5m])" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "0")

    if (( $(echo "$ERROR_RATE > 0.05" | bc -l) )); then
        echo "❌ 错误率过高 ($ERROR_RATE), 继续回滚"
    else
        echo "✅ 指标正常，回滚阶段完成"
    fi
done

echo "🎉 金丝雀回滚完成!"
```

### 方案C: 数据库回滚

#### 数据库回滚脚本
```bash
#!/bin/bash
# 文件: deployment/scripts/database_rollback.sh

set -euo pipefail

DB_HOST="postgres-service"
DB_NAME="claude_enhancer"
DB_USER="postgres"
BACKUP_DIR="/backups"

echo "🗄️ 开始数据库回滚..."

# 1. 获取最新的可用备份
LATEST_BACKUP=$(ls -t $BACKUP_DIR/db_backup_*.sql | head -n1)
echo "📁 使用备份文件: $LATEST_BACKUP"

# 2. 创建当前状态备份
CURRENT_BACKUP="$BACKUP_DIR/pre_rollback_$(date +%Y%m%d_%H%M%S).sql"
echo "💾 创建回滚前备份: $CURRENT_BACKUP"
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $CURRENT_BACKUP

# 3. 停止应用连接
echo "🔌 停止应用数据库连接..."
kubectl scale deployment claude-enhancer-deployment --replicas=0 -n $NAMESPACE

# 4. 终止活动连接
echo "🔌 终止数据库活动连接..."
psql -h $DB_HOST -U $DB_USER -d postgres -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();"

# 5. 删除当前数据库
echo "🗑️ 删除当前数据库..."
psql -h $DB_HOST -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"

# 6. 重新创建数据库
echo "🏗️ 重新创建数据库..."
psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"

# 7. 恢复数据
echo "📥 恢复数据库数据..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < $LATEST_BACKUP

# 8. 验证数据完整性
echo "🔍 验证数据完整性..."
RECORD_COUNT=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM users;" | xargs)
echo "用户记录数: $RECORD_COUNT"

if [ "$RECORD_COUNT" -gt 0 ]; then
    echo "✅ 数据库回滚成功"
else
    echo "❌ 数据库回滚失败，记录数为0"
    exit 1
fi

# 9. 重启应用
echo "🚀 重启应用服务..."
kubectl scale deployment claude-enhancer-deployment --replicas=3 -n $NAMESPACE

echo "🎉 数据库回滚完成!"
```

## 🔍 回滚验证程序

### 全面健康检查脚本
```bash
#!/bin/bash
# 文件: deployment/scripts/post_rollback_verification.sh

set -euo pipefail

echo "🔍 开始回滚后验证..."

# 1. 服务健康检查
echo "🏥 检查服务健康状态..."
SERVICES=("claude-enhancer-service" "postgres-service" "redis-service")
for service in "${SERVICES[@]}"; do
    if kubectl get service $service -n $NAMESPACE > /dev/null 2>&1; then
        echo "✅ $service: 正常"
    else
        echo "❌ $service: 异常"
        exit 1
    fi
done

# 2. 应用功能验证
echo "🔧 验证应用核心功能..."
API_BASE="http://$(kubectl get service claude-enhancer-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}'):8080"

# Health endpoint
if curl -f "$API_BASE/health" > /dev/null 2>&1; then
    echo "✅ Health endpoint: 正常"
else
    echo "❌ Health endpoint: 异常"
    exit 1
fi

# Agent system
if curl -f "$API_BASE/api/agents/status" > /dev/null 2>&1; then
    echo "✅ Agent 系统: 正常"
else
    echo "❌ Agent 系统: 异常"
    exit 1
fi

# 3. 数据库连接验证
echo "🗄️ 验证数据库连接..."
if psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ 数据库连接: 正常"
else
    echo "❌ 数据库连接: 异常"
    exit 1
fi

# 4. 缓存服务验证
echo "💾 验证缓存服务..."
if redis-cli -h redis-service ping | grep -q PONG; then
    echo "✅ Redis 缓存: 正常"
else
    echo "❌ Redis 缓存: 异常"
    exit 1
fi

# 5. 性能指标检查
echo "📊 检查性能指标..."
RESPONSE_TIME=$(curl -w "%{time_total}" -o /dev/null -s "$API_BASE/health")
if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    echo "✅ 响应时间: ${RESPONSE_TIME}s (正常)"
else
    echo "⚠️ 响应时间: ${RESPONSE_TIME}s (较慢)"
fi

# 6. 日志检查
echo "📄 检查错误日志..."
ERROR_COUNT=$(kubectl logs deployment/claude-enhancer-deployment -n $NAMESPACE --since=5m | grep -c ERROR || echo "0")
if [ "$ERROR_COUNT" -lt 5 ]; then
    echo "✅ 错误日志: $ERROR_COUNT 条 (正常)"
else
    echo "⚠️ 错误日志: $ERROR_COUNT 条 (异常)"
fi

echo "🎉 回滚验证完成!"
```

## 📊 回滚监控和告警

### 回滚过程监控
```yaml
# 文件: monitoring/rollback_alerts.yml
groups:
- name: rollback_monitoring
  rules:
  - alert: RollbackInProgress
    expr: increase(rollback_initiated_total[5m]) > 0
    for: 0m
    labels:
      severity: warning
    annotations:
      summary: "Claude Enhancer 回滚正在进行"
      description: "系统正在执行回滚操作"

  - alert: RollbackFailed
    expr: increase(rollback_failed_total[5m]) > 0
    for: 0m
    labels:
      severity: critical
    annotations:
      summary: "Claude Enhancer 回滚失败"
      description: "回滚操作失败，需要立即人工介入"

  - alert: PostRollbackHealthCheck
    expr: up{job="claude-enhancer"} != 1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "回滚后健康检查失败"
      description: "回滚完成后服务仍然不健康"
```

### 自动化告警通知
```bash
# 文件: scripts/rollback_notification.sh
#!/bin/bash

ROLLBACK_STATUS="$1"  # success/failed/in_progress
ROLLBACK_REASON="$2"  # 回滚原因
ROLLBACK_VERSION="$3" # 回滚到的版本

# Slack 通知
send_slack_notification() {
    local status_emoji
    case $ROLLBACK_STATUS in
        "success") status_emoji="✅" ;;
        "failed") status_emoji="❌" ;;
        "in_progress") status_emoji="🔄" ;;
    esac

    curl -X POST "$SLACK_WEBHOOK_URL" \
      -H 'Content-type: application/json' \
      --data '{
        "text": "'$status_emoji' Claude Enhancer 回滚状态: '$ROLLBACK_STATUS'",
        "attachments": [
          {
            "color": "'$([ "$ROLLBACK_STATUS" = "success" ] && echo "good" || echo "danger")'",
            "fields": [
              {"title": "回滚原因", "value": "'$ROLLBACK_REASON'", "short": true},
              {"title": "目标版本", "value": "'$ROLLBACK_VERSION'", "short": true},
              {"title": "时间", "value": "'$(date)'", "short": true}
            ]
          }
        ]
      }'
}

# 邮件通知
send_email_notification() {
    cat <<EOF | mail -s "Claude Enhancer 回滚通知" admin@example.com
回滚状态: $ROLLBACK_STATUS
回滚原因: $ROLLBACK_REASON
目标版本: $ROLLBACK_VERSION
时间: $(date)

请检查系统状态并采取必要措施。
EOF
}

# 发送通知
send_slack_notification
send_email_notification
```

## 📋 回滚后行动清单

### 立即行动 (0-30分钟)
- [ ] **服务验证**
  - [ ] 所有服务正常运行
  - [ ] 数据库连接正常
  - [ ] 缓存服务可用
  - [ ] API 接口响应正常

- [ ] **用户通知**
  - [ ] 发送服务恢复通知
  - [ ] 更新状态页面
  - [ ] 客服团队通知
  - [ ] 社交媒体更新

### 短期行动 (1-4小时)
- [ ] **问题分析**
  - [ ] 根因分析报告
  - [ ] 时间线整理
  - [ ] 影响范围评估
  - [ ] 数据完整性验证

- [ ] **沟通协调**
  - [ ] 团队回顾会议
  - [ ] 管理层汇报
  - [ ] 客户沟通
  - [ ] 合作伙伴通知

### 中期行动 (1-7天)
- [ ] **流程改进**
  - [ ] 回滚流程优化
  - [ ] 监控告警调整
  - [ ] 测试用例增加
  - [ ] 文档更新

- [ ] **技术优化**
  - [ ] 问题修复
  - [ ] 代码审查
  - [ ] 性能优化
  - [ ] 安全加固

### 长期行动 (1-4周)
- [ ] **系统改进**
  - [ ] 架构优化
  - [ ] 容灾能力提升
  - [ ] 自动化程度提高
  - [ ] 运维工具完善

- [ ] **团队建设**
  - [ ] 培训计划
  - [ ] 知识分享
  - [ ] 技能提升
  - [ ] 流程标准化

## 📞 紧急联系人

### 一级响应团队
- **系统架构师**: [姓名] - [手机] - [邮箱]
- **DevOps 负责人**: [姓名] - [手机] - [邮箱]
- **数据库 DBA**: [姓名] - [手机] - [邮箱]

### 二级支持团队
- **产品负责人**: [姓名] - [手机] - [邮箱]
- **测试负责人**: [姓名] - [手机] - [邮箱]
- **安全负责人**: [姓名] - [手机] - [邮箱]

### 外部支持
- **云服务商**: [联系方式]
- **CDN 提供商**: [联系方式]
- **监控服务商**: [联系方式]

## 🔒 回滚安全考虑

### 数据安全
- 回滚前必须创建数据备份
- 验证备份完整性和可恢复性
- 确保敏感数据不会泄露
- 保持审计日志完整

### 访问控制
- 回滚操作需要双重授权
- 记录所有回滚操作
- 限制回滚窗口时间
- 监控异常访问行为

### 合规性
- 满足数据保护法规要求
- 保持操作记录可追溯
- 及时通知相关监管机构
- 更新合规性文档

---

**⚠️ 重要提醒**:
- 回滚是保护系统和用户的重要手段，不应视为失败
- 快速决策和执行比完美计划更重要
- 回滚后的问题分析和改进同样重要
- 定期演练回滚流程，确保团队熟练掌握

**🎯 目标**: 在最短时间内恢复系统稳定性，保护用户利益和业务连续性