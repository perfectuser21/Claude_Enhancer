# 🚨 强制执行策略 - Agent数量保证

## 核心机制：三重保障

### 1️⃣ Claude Code自检（主动）
**每次执行前的自我检查流程**

```python
def before_execute():
    """Claude Code在执行任务前必须运行的检查"""

    # Step 1: 识别任务类型
    task_type = analyze_task()

    # Step 2: 查询要求
    min_agents = get_min_agents(task_type)

    # Step 3: 检查规划
    planned_agents = count_planned_agents()

    # Step 4: 验证循环
    while planned_agents < min_agents:
        print(f"❌ 需要{min_agents}个Agent，当前{planned_agents}个")
        # 重新规划
        replan_with_more_agents()
        planned_agents = count_planned_agents()

    # Step 5: 通过后执行
    execute_with_agents()
```

### 2️⃣ TodoWrite检查清单（可视化）
**使用TodoWrite创建可见的检查项**

```markdown
任务：实现用户认证
□ 任务分析完成
□ 确认需要5个Agent（authentication类型）
□ Agent 1: backend-architect ✓
□ Agent 2: security-auditor ✓
□ Agent 3: database-specialist ✓
□ Agent 4: test-engineer ✓
□ Agent 5: api-designer ✓
□ 数量验证：5/5 ✅
□ 开始并行执行
```

### 3️⃣ Hook监督提醒（辅助）
**phase_checker.sh实时监控**

```bash
# 检测到执行意图时触发
bash .claude/hooks/phase_checker.sh authentication 3

# 输出
❌ 检查失败：Agent数量不足！
需要至少 5 个Agent，当前只有 3 个
🔄 请重新规划...
```

## 执行示例

### ❌ 错误流程（会被阻止）
```
用户: 实现登录功能
Claude: 我使用2个Agent...
自检: ❌ authentication需要5个
重新规划: 添加3个Agent
再次自检: ✅ 5个满足要求
执行: 5个Agent并行
```

### ✅ 正确流程
```
用户: 实现登录功能
Claude:
1. 识别任务类型: authentication
2. 查询要求: 最少5个Agent
3. 规划5个Agent
4. 自检通过
5. 执行
```

## 关键代码位置

### 在CLAUDE.md中添加
```markdown
## 🔴 强制自检规则

**执行任何编程任务前必须：**
1. 运行phase_checker.sh检查Agent数量
2. 使用TodoWrite创建检查清单
3. 数量不足时必须重新规划
4. 只有检查通过才能执行
```

### 在settings.json中配置
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "command": "bash .claude/hooks/phase_checker.sh",
        "blocking": false  // 注：无法真正阻止，但会提醒
      }
    ]
  }
}
```

## 实际操作指南

### Claude Code执行时的思考过程
```
1. "用户要我实现登录功能"
2. "让我先检查这是什么类型的任务" → authentication
3. "authentication需要几个Agent？" → 查表：5个
4. "我准备用几个？" → 如果少于5个
5. "不行，必须重新规划" → 添加到5个
6. "现在可以执行了" → 并行调用5个Agent
```

### 重试逻辑
```javascript
// 伪代码
function executeWithRetry(task) {
    let attempts = 0;
    const maxAttempts = 3;

    while (attempts < maxAttempts) {
        const agents = planAgents(task);
        const required = getRequiredCount(task.type);

        if (agents.length >= required) {
            // 执行
            return executeParallel(agents);
        }

        console.log(`Attempt ${attempts + 1}: 需要${required}个，只有${agents.length}个，重新规划...`);
        attempts++;
    }

    throw new Error("无法满足Agent数量要求");
}
```

## 总结

**不是依赖自律，而是强制自检流程：**

1. **执行前必须自检** - 不是选择性的
2. **不通过就重来** - 不是继续执行
3. **可视化检查过程** - 用TodoWrite展示
4. **Hook辅助提醒** - 额外的安全网

这样即使Claude Code想跳过也不行，因为**自检是执行流程的一部分**，不是可选项！