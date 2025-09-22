# 🎯 8-Phase贯穿保证机制

## 核心问题
**如何确保每个任务都完整执行8个Phase？**

## 解决方案：Phase流程控制器

### 方案1：TodoWrite作为Phase控制器 ✅ (推荐)

**使用TodoWrite强制创建8个Phase检查点**

```markdown
用户：实现用户认证功能

Claude Code必须执行：
1. 立即创建8个Phase的TodoWrite清单
2. 按顺序执行，不能跳过
3. 每个Phase都有Agent数量要求
```

#### 实现方式：
```python
# Claude Code的执行模板
def execute_with_8_phases(task):
    # Step 1: 强制创建8个Phase清单
    todo_list = [
        {"content": "Phase 0: 创建功能分支", "status": "pending"},
        {"content": "Phase 1: 需求分析 (1-2 agents)", "status": "pending"},
        {"content": "Phase 2: 设计规划 (2-3 agents)", "status": "pending"},
        {"content": "Phase 3: 开发实现 (4-8 agents)", "status": "pending"},
        {"content": "Phase 4: 本地测试 (2-3 agents)", "status": "pending"},
        {"content": "Phase 5: 代码提交", "status": "pending"},
        {"content": "Phase 6: 代码审查 (1-2 agents)", "status": "pending"},
        {"content": "Phase 7: 合并部署", "status": "pending"}
    ]

    # Step 2: 逐个Phase执行
    for phase in todo_list:
        # 标记为in_progress
        phase["status"] = "in_progress"
        update_todo(todo_list)

        # 执行Phase（包含Agent数量检查）
        execute_phase(phase)

        # 标记为completed
        phase["status"] = "completed"
        update_todo(todo_list)
```

### 方案2：Phase状态文件追踪

**创建.claude/phase_state.json追踪进度**

```json
{
  "current_task": "用户认证功能",
  "start_time": "2025-01-21T10:00:00",
  "phases": {
    "phase_0": {
      "name": "分支创建",
      "status": "completed",
      "branch": "feature/user-auth",
      "timestamp": "2025-01-21T10:01:00"
    },
    "phase_1": {
      "name": "需求分析",
      "status": "in_progress",
      "agents_used": 2,
      "agents_required": 2
    },
    "phase_2": {
      "name": "设计规划",
      "status": "pending",
      "agents_required": 3
    }
    // ... 其他phases
  }
}
```

### 方案3：Phase Manager Agent

**创建专门的phase-manager agent监督流程**

```xml
<function_calls>
  <!-- 先调用Phase Manager检查当前应该执行哪个Phase -->
  <invoke name="Task">
    <parameter name="subagent_type">phase-manager</parameter>
    <parameter name="prompt">
      检查任务"用户认证"当前应该执行哪个Phase
      如果没有开始，从Phase 0开始
      如果已经在进行中，继续下一个Phase
    </parameter>
  </invoke>
</function_calls>
```

## 📋 Phase执行要求矩阵

| Phase | 名称 | 最少Agent数 | 必须的Agent类型 | 可跳过? |
|-------|------|------------|----------------|---------|
| 0 | 分支创建 | 0 | - | ❌ 不可跳过 |
| 1 | 需求分析 | 1-2 | requirements-analyst | ❌ 不可跳过 |
| 2 | 设计规划 | 2-3 | backend-architect, api-designer | ❌ 不可跳过 |
| 3 | 开发实现 | 4-8 | 根据任务类型动态 | ❌ 不可跳过 |
| 4 | 本地测试 | 2-3 | test-engineer | ⚠️ 可选 |
| 5 | 代码提交 | 0 | - | ❌ 不可跳过 |
| 6 | 代码审查 | 1-2 | code-reviewer | ⚠️ 可选 |
| 7 | 合并部署 | 1 | devops-engineer | ⚠️ 可选 |

## 🔄 强制执行流程

### 每个编程任务开始时：

```
1. 识别任务
   ↓
2. 创建8-Phase TodoWrite清单
   ↓
3. Phase 0: 检查/创建分支
   ↓
4. Phase 1: 需求分析（检查Agent数量）
   ↓
5. Phase 2: 设计规划（检查Agent数量）
   ↓
6. Phase 3: 开发实现（检查Agent数量）
   ↓
7. Phase 4: 本地测试
   ↓
8. Phase 5: 代码提交
   ↓
9. Phase 6: 代码审查
   ↓
10. Phase 7: 合并部署
```

### 关键检查点：

1. **Phase开始前**
   - 检查前一个Phase是否完成
   - 验证当前Phase的Agent要求
   - 记录Phase开始时间

2. **Phase执行中**
   - 监控Agent执行情况
   - 收集执行结果
   - 处理异常情况

3. **Phase完成后**
   - 验证输出结果
   - 更新Phase状态
   - 决定是否继续下一Phase

## 🚨 中断和恢复机制

### 如果任务被中断：

```python
def resume_task():
    # 1. 读取phase_state.json
    state = load_phase_state()

    # 2. 找到最后完成的Phase
    last_completed = find_last_completed_phase(state)

    # 3. 从下一个Phase继续
    continue_from_phase(last_completed + 1)
```

### Hook配合提醒：

```bash
# phase_monitor.sh
#!/bin/bash

# 检查是否有未完成的8-Phase流程
if [ -f ".claude/phase_state.json" ]; then
    INCOMPLETE=$(jq '.phases | map(select(.status != "completed")) | length' .claude/phase_state.json)
    if [ "$INCOMPLETE" -gt 0 ]; then
        echo "⚠️ 发现未完成的8-Phase流程！"
        echo "📋 还有 $INCOMPLETE 个Phase未完成"
        echo "🔄 建议继续执行或重置"
    fi
fi
```

## 💡 实际执行示例

```markdown
用户：实现登录功能

Claude Code：
我将使用8-Phase工作流来实现登录功能。

[创建TodoWrite清单]
□ Phase 0: 创建feature/login分支
□ Phase 1: 分析登录需求（2 agents）
□ Phase 2: 设计登录架构（3 agents）
□ Phase 3: 实现登录代码（6 agents）
□ Phase 4: 测试登录功能（2 agents）
□ Phase 5: 提交代码
□ Phase 6: 代码审查（1 agent）
□ Phase 7: 合并到main

[开始执行]
✅ Phase 0: 创建feature/login分支 - 完成
⏳ Phase 1: 分析登录需求
   - 检查：需要2个agents
   - 执行：requirements-analyst + business-analyst
✅ Phase 1: 完成

[继续所有Phase...]
```

## 🎯 关键差异

### ❌ 现在的问题
- 只在单个任务执行前检查Agent数量
- 没有强制8个Phase
- 可能跳过某些Phase

### ✅ 改进后
- **强制8-Phase流程**：TodoWrite清单强制可见
- **Phase间依赖**：前一个完成才能执行下一个
- **状态持久化**：中断后可恢复
- **全程监控**：每个Phase都有Agent要求

这样就确保了**每个编程任务都贯穿完整的8个Phase**！