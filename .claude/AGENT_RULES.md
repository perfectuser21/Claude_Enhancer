# ⚠️ Agent调用规则 - 防止死循环

## 🔴 核心规则：SubAgent不能调用SubAgent

### 为什么？
防止无限递归调用导致死循环或资源耗尽。

### 正确的调用链
```
Claude Code (主控)
    ├── SubAgent 1 (执行任务)
    ├── SubAgent 2 (执行任务)
    └── SubAgent 3 (执行任务)
```

### ❌ 错误的调用链
```
Claude Code
    └── SubAgent 1
           └── SubAgent 2  ← 错误！SubAgent不能调用SubAgent
                  └── SubAgent 3  ← 更错误！
```

## 安全的Agent列表

### 可以并行调用的Agent（不会调用其他Agent）
```yaml
safe_agents:
  # 开发类
  - backend-architect
  - frontend-specialist
  - database-specialist
  - api-designer

  # 测试类
  - test-engineer
  - performance-engineer
  - security-auditor

  # 审查类
  - code-reviewer
  - accessibility-auditor

  # 文档类
  - technical-writer
  - documentation-writer
```

### ⚠️ 需要谨慎使用的Agent（可能调用其他Agent）
```yaml
risky_agents:
  - orchestrator  # 可能协调其他agent
  - claude_enhancer  # 可能调用多个agent
  - fullstack-engineer  # 可能分解任务
```

### 🔴 绝对不要在SubAgent中使用
```yaml
forbidden_in_subagent:
  - Task  # SubAgent不能调用Task工具
  - orchestrator  # 不能嵌套协调器
```

## 正确的使用方式

### ✅ 正确：Claude Code并行调用多个Agent
```python
# 在Claude Code主控中
agents = [
    ("backend-architect", "设计架构"),
    ("test-engineer", "编写测试"),
    ("security-auditor", "安全审查")
]

# 并行执行
execute_parallel(agents)
```

### ❌ 错误：在Agent中再调用Agent
```python
# 在SubAgent中
def subagent_task():
    # 错误！SubAgent不能调用Task
    Task(subagent_type="another-agent")
```

## 检查机制

在执行前检查：
1. 确认是Claude Code在调用Agent
2. 确认Agent不会再调用其他Agent
3. 使用safe_agents列表中的Agent