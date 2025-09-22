# 🔍 主动自检机制 - Agent数量验证

## 核心原理
**每个阶段执行前，Claude Code必须先自检Agent数量是否符合要求**

## 执行流程

### Step 1: 任务分析
```
用户请求 → 识别任务类型 → 确定复杂度
```

### Step 2: 自检点（CHECK POINT）
```
┌─────────────────────────────────┐
│  🔍 自检：我准备用几个Agent？    │
│  ❓ 任务类型需要几个？           │
│  ⚖️ 对比：数量是否匹配？         │
└─────────────────────────────────┘
        ↓ 不匹配
┌─────────────────────────────────┐
│  🔄 重新规划：                   │
│  - 增加缺少的Agent               │
│  - 重新组织并行执行              │
│  - 再次自检                      │
└─────────────────────────────────┘
```

### Step 3: 执行验证
```python
# 伪代码逻辑
def execute_task(task):
    # 1. 分析任务
    complexity = analyze_task_complexity(task)
    required_agents = get_required_agent_count(complexity)

    # 2. 自检循环
    while True:
        planned_agents = plan_agents(task)

        # 检查数量
        if len(planned_agents) < required_agents:
            print(f"❌ 需要{required_agents}个Agent，只规划了{len(planned_agents)}个")
            print("🔄 重新规划...")
            continue
        else:
            print(f"✅ Agent数量正确: {len(planned_agents)}")
            break

    # 3. 执行
    execute_parallel(planned_agents)
```

## 实施方案

### 方案1: 专门的Validator Agent
创建一个`agent-validator`，在每个Phase执行前调用：
```xml
<function_calls>
  <!-- 先调用验证器 -->
  <invoke name="Task">
    <parameter name="subagent_type">agent-validator</parameter>
    <parameter name="prompt">检查Phase 3需要的Agent数量</parameter>
  </invoke>

  <!-- 根据验证结果执行 -->
  <invoke name="Task">...</invoke>
  <invoke name="Task">...</invoke>
  <invoke name="Task">...</invoke>
</function_calls>
```

### 方案2: Claude Code内置检查表
在执行前使用TodoWrite创建检查清单：
```
□ 任务类型：认证系统
□ 复杂度：高
□ 需要Agent数：8个
□ 已规划Agent数：？
□ 数量匹配：？
```

### 方案3: Hook增强提醒
```bash
#!/bin/bash
# pre_execution_check.sh

# 检测即将执行的Agent数量
AGENT_COUNT=$(grep -c "subagent_type" /tmp/pending_execution.json)
REQUIRED_COUNT=$(determine_required_count)

if [ $AGENT_COUNT -lt $REQUIRED_COUNT ]; then
    echo "⚠️ 警告：Agent数量不足！"
    echo "📊 当前：$AGENT_COUNT | 需要：$REQUIRED_COUNT"
    echo "🔄 建议：重新规划并添加以下Agent："
    suggest_missing_agents
fi
```

## 具体规则映射

### 任务类型 → 最少Agent数
```yaml
authentication:
  min_agents: 5
  required: [backend-architect, security-auditor, database-specialist, test-engineer, api-designer]

api_development:
  min_agents: 4
  required: [api-designer, backend-architect, test-engineer, technical-writer]

database_design:
  min_agents: 4
  required: [database-specialist, backend-architect, performance-engineer, data-engineer]

frontend:
  min_agents: 4
  required: [frontend-specialist, ux-designer, test-engineer, performance-engineer]

bug_fix:
  min_agents: 3
  required: [error-detective, test-engineer, code-reviewer]

refactoring:
  min_agents: 4
  required: [backend-architect, test-engineer, code-reviewer, performance-engineer]
```

## 强制执行示例

```markdown
用户：实现用户登录功能

Claude Code思考过程：
1. 🔍 自检：这是authentication任务
2. 📊 查表：需要最少5个Agent
3. 📝 规划：
   - backend-architect ✓
   - security-auditor ✓
   - database-specialist ✓
   - test-engineer ✓
   - api-designer ✓
4. ✅ 数量匹配，执行！

如果只规划了3个：
1. ❌ 自检失败：3 < 5
2. 🔄 重新规划：添加security-auditor和api-designer
3. ✅ 再次自检：5 = 5
4. ✅ 执行！
```

## 关键差异

### ❌ 错误方式（依赖自律）
```
CLAUDE.md说要用5个 → 我可能忘记 → 只用了2个 → Hook提醒但无法阻止
```

### ✅ 正确方式（主动自检）
```
准备执行 → 先自检数量 → 不够就重新规划 → 直到满足要求 → 才执行
```

## 实现要点

1. **每个Phase开始前必须自检**
2. **自检不通过不能继续**
3. **自动重新规划直到满足**
4. **记录自检结果便于审计**

这样就不依赖"自律"，而是**强制的自检流程**！