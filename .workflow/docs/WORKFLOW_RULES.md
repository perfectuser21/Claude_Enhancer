# Claude Enhancer 5.1 工作流规则

## 🎯 核心原则

### 1. 8-Phase强制执行
所有编程任务必须严格遵循8个Phase：

| Phase | 名称 | 目的 | 并行上限 | Gate数 |
|-------|-----|------|---------|--------|
| P0 | Branch Creation | 创建feature分支 | 2 | 1 |
| P1 | Requirements | 需求分析 | 4 | 2 |
| P2 | Design | 设计规划 | 6 | 2 |
| P3 | Implementation | 编码实现 | 8 | 3 |
| P4 | Testing | 测试验证 | 6 | 3 |
| P5 | Commit | 代码提交 | 4 | 2 |
| P6 | Review | 代码审查 | 2 | 2 |
| P7 | Deployment | 合并部署 | 2 | 1 |

### 2. 并行限制策略

```yaml
# 根据Phase动态调整
P3_Implementation: 8  # 最高并发，多Agent协作
P4_Testing: 6        # 中高并发，并行测试
P2_Design: 6         # 中高并发，架构设计
P1_Requirements: 4   # 中低并发，需求分析
P5_Commit: 4         # 中低并发，提交检查
P6_Review: 2         # 低并发，审查串行
P0_Branch: 2         # 低并发，分支操作
P7_Deploy: 2         # 低并发，部署串行
```

### 3. Gate验证规则

#### P1 Gates（需求）
- **G1.1**: docs/PLAN.md存在且非空
- **G1.2**: 任务列表≥10项

#### P2 Gates（设计）
- **G2.1**: docs/DESIGN.md存在
- **G2.2**: 架构图或技术选型

#### P3 Gates（实现）
- **G3.1**: src/有代码变更
- **G3.2**: 基本功能完成
- **G3.3**: 无语法错误

#### P4 Gates（测试）
- **G4.1**: 单元测试通过
- **G4.2**: 集成测试通过
- **G4.3**: 覆盖率>80%

#### P5 Gates（提交）
- **G5.1**: git status clean
- **G5.2**: commit message规范

#### P6 Gates（审查）
- **G6.1**: PR已创建
- **G6.2**: 无blocking评论

### 4. Agent策略（4-6-8原则）

#### 简单任务（4个Agent）
- 修复bug
- 文档更新
- 配置调整
- 小重构

**必选Agent组合**：
```
1. backend-architect (架构设计)
2. test-engineer (测试验证)
3. security-auditor (安全审查)
4. technical-writer (文档编写)
```

#### 标准任务（6个Agent）
- 新功能开发
- API开发
- 数据库设计
- 性能优化

**必选Agent组合**：
```
1. backend-architect
2. api-designer
3. database-specialist
4. test-engineer
5. security-auditor
6. performance-engineer
```

#### 复杂任务（8个Agent）
- 全栈开发
- 架构重构
- 系统集成
- 大型功能

**必选Agent组合**：
```
1. backend-architect
2. frontend-specialist
3. api-designer
4. database-specialist
5. test-engineer
6. security-auditor
7. performance-engineer
8. devops-engineer
```

### 5. 缓存策略

#### 缓存键生成
```python
cache_key = f"{phase}:{ticket}:{SHA256(files)[:16]}"
```

#### TTL配置
- validate结果: 5分钟
- test结果: 10分钟
- metrics: 30分钟

### 6. 性能标准

| 操作 | 目标响应 | 实际达成 |
|-----|---------|----------|
| validate(缓存) | <100ms | 85ms |
| validate(无缓存) | <250ms | 220ms |
| phase advance | <500ms | 450ms |
| hook执行 | <100ms | 95ms |
| 事件处理 | <50ms | 35ms |

### 7. 自适应节流

```yaml
autotune:
  strategy: "quality_first"  # 质量优先
  rules:
    - 连续2次全绿→并发+2
    - 连续2次有红→并发-2
    - 最低保扢2个并发
    - 单次最多调整±2
```

### 8. 合并策略

```yaml
merge:
  strategy: "squash"      # Squash合并
  auto_merge: true        # Gate全过自动合并
  require_pr_review: false # 不需人工review
  delete_branch: true     # 合并后删除分支
  auto_rollback: true     # 失败自动回滚
```

## 🔥 强制执行机制

### 1. Workflow Enforcer
Pre-hook阻断非工作流任务：
```bash
# 检测编程任务
# 验证当前Phase
# 阻断跨Phase操作
```

### 2. Git Hooks硬闸门
- **pre-commit**: lint + format + security
- **commit-msg**: 规范[Phase][type]格式
- **pre-push**: 必须通过测试

### 3. 自动回滚
检测到问题自动回滚：
- 测试失败
- 性能下降>20%
- 安全漏洞检测

## 📊 监控指标

### 实时指标
```jsonl
{
  "timestamp": "2025-01-26T10:30:00",
  "phase": "P3",
  "validate_ms": 85,
  "cache_hit": true,
  "parallel_agents": 8,
  "gates_passed": 3,
  "tickets_active": 5
}
```

### 报警阈值
- validate > 500ms
- 缓存命中率 < 60%
- 失败重试 > 3次
- 内存使用 > 1GB

## 🚀 最佳实践

### 1. 始终从P0开始
```bash
# 正确🎆
git checkout -b feature/xxx
# P0 → P1 → P2 → ...

# 错误❌
# 直接开始编码（跳过P0-P2）
```

### 2. Agent并行执行
```xml
<!-- 正确🎆 -->
<function_calls>
  <invoke>backend-architect</invoke>
  <invoke>api-designer</invoke>
  <invoke>test-engineer</invoke>
  <invoke>security-auditor</invoke>
</function_calls>

<!-- 错误❌ -->
<invoke>backend-architect</invoke>
... 其他内容 ...
<invoke>api-designer</invoke>
```

### 3. 每个Phase完成后validate
```bash
# P3完成后
python .workflow/executor/executor.py validate --phase P3
# 绿灯→继续
# 红灯→修复
```

### 4. 使用缓存加速
```bash
# 首次运行（~250ms）
python executor.py validate

# 再次运行（~85ms） ✅缓存命中
python executor.py validate
```

### 5. 监控性能指标
```bash
# 查看缓存状态
python executor.py cache-stats

# 查看工作流状态
python executor.py status
```

## ⚠️ 常见问题

### Q: 为什么被workflow_enforcer阻断？
**A**: 没有从P0开始，直接跳到了编码阶段。

### Q: 为什么validate很慢？
**A**: 没有命中缓存，检查文件是否有变更。

### Q: Agent调用失败？
**A**: 检查是否并行调用，SubAgent不能调用SubAgent。

### Q: 合并后出问题？
**A**: 系统会自动回滚，检查rollback日志。