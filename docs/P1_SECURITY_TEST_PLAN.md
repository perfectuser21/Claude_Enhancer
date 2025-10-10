# P1 Security Enhancement - Test Plan

**基于**: P1_SECURITY_AUDIT_ENHANCEMENT_PLAN.md  
**测试日期**: 2025-10-10  
**测试范围**: 3个高优先级风险修复验证

---

## 🎯 测试目标

验证以下安全增强功能：
1. **Owner Bypass审计追踪** - 100%覆盖
2. **自动化权限验证** - 所有自动化操作被验证
3. **结构化日志** - CRITICAL操作完整记录

---

## 📋 Test Suite 1: Owner Bypass审计追踪

### TC-1.1: GitHub Audit Log监控

**测试场景**: 验证Owner绕过保护规则时被正确审计

**前置条件**:
- Branch Protection已配置（`enforce_admins=true`）
- GitHub Audit Log Monitor workflow已部署
- 审计API可访问

**测试步骤**:
```bash
# 1. Owner用户直接推送到main分支（绕过PR）
git checkout main
echo "test bypass" >> README.md
git add README.md
git commit -m "test: owner bypass test"
git push origin main  # 应该成功（Owner权限）

# 2. 等待15分钟（GitHub Audit Log同步周期）
sleep 900

# 3. 检查审计日志
curl -X GET http://localhost:8000/api/audit/bypass-approvals \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# 4. 检查Slack告警
# 应该收到#security-alerts频道的告警消息
```

**预期结果**:
- ✅ GitHub Audit Log中记录了`protected_branch.policy_override`事件
- ✅ 后端数据库`audit_logs`表中创建了记录
  - `bypass_type` = 'owner_bypass'
  - `level` = 'CRITICAL'
  - `approval_required` = true
- ✅ Slack收到告警（包含actor、branch、reason）
- ✅ Email发送给security-team和CTO
- ✅ PagerDuty触发incident（如果severity=critical）

**验证SQL**:
```sql
-- 查询最近的Owner Bypass记录
SELECT 
    id,
    timestamp,
    bypass_type,
    bypass_reason,
    bypassed_rules,
    approval_required,
    approved_by
FROM audit_logs
WHERE bypass_type = 'owner_bypass'
  AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC
LIMIT 10;

-- 使用专用视图
SELECT * FROM v_owner_bypass_audit
WHERE timestamp > NOW() - INTERVAL '1 hour';
```

---

### TC-1.2: 审批工作流

**测试场景**: 验证Bypass需要审批

**测试步骤**:
```bash
# 1. 登录审批界面
open https://audit.claude-enhancer.local/admin/security/bypass-approvals

# 2. 查看待审批列表
# 应该看到TC-1.1创建的bypass记录

# 3. 点击"Details"查看完整信息
# - Commit SHA
# - Commit Message
# - IP Address
# - Bypassed Rules

# 4. 点击"Approve"并填写审批备注
curl -X POST http://localhost:8000/api/audit/approvals/{approval_id}/approve \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Reviewed and approved - legitimate emergency hotfix",
    "approved_by": "admin-user-id"
  }'

# 5. 验证审批状态更新
curl -X GET http://localhost:8000/api/audit/approvals/{approval_id} \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.approval_status'
```

**预期结果**:
- ✅ 审批界面正确显示pending状态
- ✅ 审批后`approved_by`和`approved_at`字段更新
- ✅ 审批通知发送给原操作者
- ✅ Pending时间超过24小时会显示overdue标记

---

### TC-1.3: 数据库触发器

**测试场景**: 验证数据库自动标记bypass操作

**测试步骤**:
```sql
-- 1. 插入一个bypass记录
INSERT INTO audit_logs (
    user_id,
    action,
    level,
    resource_type,
    resource_id,
    description,
    bypass_type,
    bypass_reason,
    timestamp
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    'CONFIGURE',
    'CRITICAL',
    'github_branch_protection',
    'claude-enhancer:main',
    'Test bypass',
    'owner_bypass',
    'Test reason',
    NOW()
) RETURNING id, approval_required;

-- 2. 验证trigger自动设置approval_required = TRUE

-- 3. 检查pg_notify是否触发
LISTEN security_alert;
-- 应该收到通知
```

**预期结果**:
- ✅ `approval_required`自动设置为`true`
- ✅ `pg_notify`发送了`security_alert`通知
- ✅ 通知payload包含完整的alert信息

---

## 📋 Test Suite 2: 自动化权限验证

### TC-2.1: 合法自动化操作

**测试场景**: Claude Enhancer CLI的git push操作被正确验证

**前置条件**:
- 配置环境变量：`export CLAUDE_ENHANCER_SECRET_KEY=test-secret-key-123`
- 后端权限验证API已启动

**测试步骤**:
```bash
# 1. 生成自动化签名
export CE_AUTOMATION_NAME="claude-enhancer-cli"
export CE_AUTOMATION_TIMESTAMP=$(date +%s)
export CE_AUTOMATION_SIGNATURE=$(echo -n "${CE_AUTOMATION_NAME}:git_push:${CE_AUTOMATION_TIMESTAMP}" | \
  openssl dgst -sha256 -hmac "$CLAUDE_ENHANCER_SECRET_KEY" | awk '{print $2}')

echo "Signature: $CE_AUTOMATION_SIGNATURE"

# 2. 执行git push（会触发pre-push hook）
git checkout feature/test-automation
echo "test" >> test.txt
git add test.txt
git commit -m "test: automation permission test"
git push origin feature/test-automation

# 3. 查看日志
cat .workflow/logs/automation_audit.log
```

**预期结果**:
- ✅ Pre-push hook检测到自动化标识
- ✅ 调用后端API验证权限
- ✅ 验证通过（authorized=true）
- ✅ Git push成功
- ✅ 审计日志记录了自动化操作

**验证SQL**:
```sql
SELECT 
    automation_name,
    automation_verified,
    action,
    resource_id,
    timestamp
FROM audit_logs
WHERE automation_name = 'claude-enhancer-cli'
  AND timestamp > NOW() - INTERVAL '10 minutes'
ORDER BY timestamp DESC;
```

---

### TC-2.2: 未授权的自动化操作

**测试场景**: 未知自动化工具被拒绝

**测试步骤**:
```bash
# 1. 使用未知的automation_name
export CE_AUTOMATION_NAME="unknown-script"
export CE_AUTOMATION_TIMESTAMP=$(date +%s)
export CE_AUTOMATION_SIGNATURE="invalid-signature-123456"

# 2. 尝试git push
git push origin feature/test-unauthorized

# 预期：pre-push hook阻止
```

**预期结果**:
- ❌ Pre-push hook返回错误
- ❌ 错误消息：`Automation not authorized to push`
- ❌ Git push失败
- ✅ 审计日志记录了失败尝试（`success=false`）

---

### TC-2.3: 签名过期检测

**测试场景**: 过期的签名被拒绝（防止重放攻击）

**测试步骤**:
```bash
# 1. 使用1小时前的时间戳
export CE_AUTOMATION_NAME="claude-enhancer-cli"
export CE_AUTOMATION_TIMESTAMP=$(($(date +%s) - 3600))  # 1小时前
export CE_AUTOMATION_SIGNATURE=$(echo -n "${CE_AUTOMATION_NAME}:git_push:${CE_AUTOMATION_TIMESTAMP}" | \
  openssl dgst -sha256 -hmac "$CLAUDE_ENHANCER_SECRET_KEY" | awk '{print $2}')

# 2. 尝试git push
git push origin feature/test-expired
```

**预期结果**:
- ❌ 验证失败：`Timestamp expired`
- ❌ Git push被阻止
- ✅ 安全事件记录（potential replay attack）

---

## 📋 Test Suite 3: 结构化日志

### TC-3.1: CRITICAL操作日志格式

**测试场景**: 验证Push到main分支的日志结构

**测试步骤**:
```python
# 使用EnhancedAuditLogger记录操作
from backend.core.audit_logger import EnhancedAuditLogger

audit_logger = EnhancedAuditLogger()

log_id = audit_logger.log_operation(
    action_type='git_push',
    resource_type='repository_branch',
    resource_id='claude-enhancer:main',
    description='Pushed 3 commits to main branch',
    actor={
        'user_id': 'test-user-id',
        'username': 'john.doe',
        'email': 'john@example.com',
        'role': 'owner',
        'is_automation': False
    },
    context={
        'session_id': 'test-session-id',
        'ip_address': '203.0.113.42',
        'user_agent': 'git/2.39.0',
        'device_fingerprint': 'fp-test-123'
    },
    details={
        'commits': [
            {
                'sha': 'abc123',
                'message': 'feat: add feature',
                'author': 'John Doe <john@example.com>',
                'timestamp': '2025-10-10T10:29:00Z'
            }
        ],
        'branch': 'main',
        'force_push': False,
        'bypass_protection': True,
        'bypass_reason': 'emergency hotfix',
        'tags': ['production', 'hotfix']
    },
    success=True
)

print(f"Log ID: {log_id}")
```

**预期结果**:
- ✅ 日志文件包含完整JSON格式
- ✅ 日志级别为`CRITICAL`
- ✅ `security.sensitivity` = "CRITICAL"
- ✅ `security.requires_approval` = true
- ✅ `security.risk_score` >= 80
- ✅ 包含IP地址、会话ID、设备指纹
- ✅ CRITICAL告警被触发

**验证日志文件**:
```bash
# 查看日志文件
tail -n 1 /var/log/claude-enhancer/audit.log | jq

# 验证必需字段
tail -n 1 /var/log/claude-enhancer/audit.log | jq '
  .version,
  .level,
  .actor.username,
  .context.ip_address,
  .security.sensitivity,
  .security.risk_score
'
```

---

### TC-3.2: 风险评分计算

**测试场景**: 验证风险评分逻辑

**测试用例**:

| 场景 | 操作类型 | Bypass? | Force Push? | 异常IP? | 预期评分 |
|-----|---------|---------|------------|---------|----------|
| 1 | git_push | ❌ | ❌ | ❌ | 30 |
| 2 | git_push | ✅ | ❌ | ❌ | 60 (30+30) |
| 3 | git_force_push | ❌ | ✅ | ❌ | 60 |
| 4 | owner_bypass | ✅ | ❌ | ✅ | 100 (80+30+20, cap 100) |

**测试代码**:
```python
test_cases = [
    # Case 1: Normal push
    {
        'action_type': 'git_push',
        'details': {'bypass_protection': False, 'force_push': False},
        'context': {'ip_address': '192.168.1.1'},
        'expected_score': 30
    },
    # Case 2: Push with bypass
    {
        'action_type': 'git_push',
        'details': {'bypass_protection': True, 'force_push': False},
        'context': {'ip_address': '192.168.1.1'},
        'expected_score': 60
    },
    # ... more cases
]

for case in test_cases:
    score = audit_logger._calculate_risk_score(
        case['action_type'],
        {},
        case['context'],
        case['details']
    )
    assert score == case['expected_score'], \
        f"Expected {case['expected_score']}, got {score}"
```

---

### TC-3.3: IP和会话追踪

**测试场景**: 验证所有日志包含IP和会话信息

**测试步骤**:
```sql
-- 检查最近1小时的所有CRITICAL日志
SELECT 
    COUNT(*) AS total_logs,
    COUNT(ip_address) AS logs_with_ip,
    COUNT(session_id) AS logs_with_session,
    COUNT(CASE WHEN ip_address IS NULL THEN 1 END) AS missing_ip,
    COUNT(CASE WHEN session_id IS NULL THEN 1 END) AS missing_session
FROM audit_logs
WHERE level = 'CRITICAL'
  AND timestamp > NOW() - INTERVAL '1 hour';

-- 验证：missing_ip和missing_session应该为0
```

**预期结果**:
- ✅ 100%的CRITICAL日志包含`ip_address`
- ✅ 100%的CRITICAL日志包含`session_id`
- ✅ IP地址格式正确（IPv4或IPv6）

---

## 🔍 测试覆盖率目标

| 组件 | 测试用例数 | 覆盖率目标 | 实际覆盖率 |
|-----|-----------|-----------|-----------|
| GitHub Audit Log监控 | 5 | 95% | TBD |
| 审批工作流 | 8 | 90% | TBD |
| 自动化权限验证 | 12 | 100% | TBD |
| 结构化日志 | 15 | 95% | TBD |
| 数据库触发器 | 6 | 100% | TBD |
| **总计** | **46** | **95%** | **TBD** |

---

## 🚨 安全漏洞测试（Penetration Testing）

### PT-1: 尝试绕过Owner Bypass审计

**攻击场景**: 恶意Owner尝试不留痕迹地推送代码

**测试步骤**:
1. 禁用GitHub Audit Log workflow（需要admin权限）
2. 直接推送到main分支
3. 检查是否有任何审计记录

**预期防御**:
- ✅ 即使workflow被禁用，backend仍会在git hook中记录
- ✅ 禁用workflow的操作本身会被审计
- ✅ 多层防御确保至少有一层记录

---

### PT-2: 伪造自动化签名

**攻击场景**: 攻击者尝试伪装成Claude Enhancer CLI

**测试步骤**:
```bash
# 1. 不知道secret_key的情况下尝试生成签名
export CE_AUTOMATION_NAME="claude-enhancer-cli"
export CE_AUTOMATION_TIMESTAMP=$(date +%s)
export CE_AUTOMATION_SIGNATURE="fake-signature-attempt"

# 2. 尝试push
git push origin feature/malicious
```

**预期防御**:
- ❌ 签名验证失败
- ✅ 安全事件记录（potential signature forgery attempt）
- ✅ 告警发送给安全团队

---

### PT-3: SQL注入审计日志

**攻击场景**: 尝试通过日志字段注入SQL

**测试步骤**:
```python
# 尝试在description字段注入SQL
audit_logger.log_operation(
    action_type='git_push',
    resource_id="'; DROP TABLE audit_logs; --",
    description="Test'; DELETE FROM audit_logs WHERE 1=1; --",
    ...
)
```

**预期防御**:
- ✅ ORM参数化查询防止SQL注入
- ✅ 输入验证拒绝异常字符
- ✅ 日志字段长度限制

---

## 📊 性能测试

### PERF-1: 审计日志写入延迟

**测试目标**: < 100ms  
**测试方法**:
```python
import time

start = time.time()
log_id = audit_logger.log_operation(...)
end = time.time()

latency_ms = (end - start) * 1000
assert latency_ms < 100, f"Latency {latency_ms}ms exceeds 100ms threshold"
```

---

### PERF-2: GitHub Audit Log同步延迟

**测试目标**: < 5分钟  
**测试方法**:
1. 记录Owner bypass操作的时间戳
2. 等待GitHub Audit Log同步
3. 查询后端数据库中对应记录的创建时间
4. 计算时间差

**预期**: 时间差 < 5分钟

---

## ✅ 测试通过标准

### Phase 1必须全部通过：
- [ ] TC-1.1: GitHub Audit Log监控
- [ ] TC-1.2: 审批工作流
- [ ] TC-1.3: 数据库触发器
- [ ] TC-2.1: 合法自动化操作
- [ ] TC-2.2: 未授权自动化被拒绝
- [ ] TC-2.3: 签名过期检测
- [ ] TC-3.1: CRITICAL日志格式
- [ ] TC-3.2: 风险评分计算
- [ ] TC-3.3: IP和会话追踪

### 安全性测试：
- [ ] PT-1: 无法绕过审计
- [ ] PT-2: 签名伪造被阻止
- [ ] PT-3: SQL注入防御有效

### 性能测试：
- [ ] PERF-1: 审计延迟 < 100ms
- [ ] PERF-2: 同步延迟 < 5分钟

---

**测试负责人**: security-auditor + test-engineer  
**测试环境**: Staging (mirror production)  
**测试数据**: 使用test fixtures，不影响生产数据
