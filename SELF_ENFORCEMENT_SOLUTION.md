# Claude Enhancer 自我强制执行解决方案

## 问题诊断

### 根本原因
1. **Hook触发条件太窄**：只在使用`Task`工具时触发
2. **我的惯性思维**：直接写代码，不用Task工具
3. **缺少主动检查机制**：没有在开始时自检

## 永久性解决方案

### 方案1：扩展Hook触发范围（立即实施）

修改`.claude/settings.json`，让Hook在更多场景触发：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "command": "bash .claude/hooks/smart_agent_selector.sh"
      },
      {
        "matcher": "Write|Edit|MultiEdit",  // 写代码前也触发！
        "command": "bash .claude/hooks/code_writing_check.sh",
        "description": "检查是否应该用Task而不是直接写代码"
      }
    ],
    "UserPromptSubmit": [
      {
        "command": "bash .claude/hooks/task_type_detector.sh",
        "description": "用户提交后立即分析任务类型"
      }
    ]
  }
}
```

### 方案2：创建强制检查Hook（code_writing_check.sh）

```bash
#!/bin/bash
# 检查是否应该使用Task工具而不是直接写代码

INPUT=$(cat)

# 检测是否在写新功能/测试代码
if echo "$INPUT" | grep -qE "stress_test|performance|benchmark|新功能|测试套件"; then
    echo "⚠️ 警告：检测到复杂任务！" >&2
    echo "🔴 应该使用Task工具调用多个Agent，而不是直接写代码" >&2
    echo "建议使用以下Agent：" >&2
    echo "  - performance-engineer" >&2
    echo "  - test-engineer" >&2
    echo "  - monitoring-specialist" >&2

    # 返回JSON建议
    cat <<EOF
{
  "approve": false,
  "message": "应该使用Task工具和多Agent并行开发",
  "suggestion": "使用至少4-6个专业Agent"
}
EOF
    exit 1
fi

echo "$INPUT"
```

### 方案3：UserPromptSubmit立即介入

创建`task_type_detector.sh`：

```bash
#!/bin/bash
# 用户输入后立即分析任务类型并提醒

USER_INPUT="$1"

# 关键词检测
KEYWORDS="压力测试|性能|优化|重构|新功能|架构|设计|实现|开发"

if echo "$USER_INPUT" | grep -qE "$KEYWORDS"; then
    echo "═════════════════════════════════════" >&2
    echo "🚨 Claude Enhancer工作流提醒" >&2
    echo "═════════════════════════════════════" >&2
    echo "" >&2
    echo "检测到开发任务，必须遵循：" >&2
    echo "1. 使用Task工具（不是直接写代码）" >&2
    echo "2. 至少4-6个Agent并行" >&2
    echo "3. 遵循8-Phase工作流" >&2
    echo "" >&2
    echo "正确做法示例：" >&2
    echo "1. 先创建分支(Phase 0)" >&2
    echo "2. 使用Task调用多个Agent" >&2
    echo "3. 让Agent们并行工作" >&2
    echo "═════════════════════════════════════" >&2
fi
```

### 方案4：创建自检机制

在CLAUDE.md中添加强制自检清单：

```markdown
## 🚨 强制自检（每次任务前必须回答）

在执行任何编程任务前，我必须：
1. [ ] 这是编程/开发任务吗？
   - 是 → 必须用Task工具
   - 否 → 可以直接执行

2. [ ] 需要几个Agent？
   - 简单：4个
   - 标准：6个
   - 复杂：8个

3. [ ] 当前在哪个Phase？
   - Phase 0：需要创建分支吗？
   - Phase 3：使用Task并行执行
   - Phase 5：需要提交代码吗？
```

### 方案5：修改我的决策树

```
用户请求
    ↓
是否涉及编程/开发？
    ├─ 否 → 直接回答
    └─ 是 → 必须使用Task工具
             ↓
         分析任务复杂度
             ↓
         选择4-6-8个Agent
             ↓
         使用Task并行调用
```

## 实施步骤

1. **立即修改settings.json** - 扩展Hook触发范围
2. **创建检查脚本** - 阻止直接写代码
3. **添加UserPromptSubmit Hook** - 第一时间介入
4. **更新CLAUDE.md** - 添加强制自检清单
5. **验证方案有效性** - 测试各种场景

## 期望效果

- 用户说"压力测试" → UserPromptSubmit Hook触发 → 提醒使用Task
- 我尝试Write代码 → PreToolUse Hook触发 → 阻止并提醒
- 最终被迫使用Task → smart_agent_selector触发 → 正确流程

这样形成三重保险，确保不会再跳过Claude Enhancer工作流！