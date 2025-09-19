# 🛡️ Claude Code 自我约束指南

> **Perfect21 规则守护机制** - 让Claude Code时刻遵守规则

## 🎯 核心理念

不是死板的框架，而是**活的监督机制**：
- Claude Code在每个关键决策点自动检查规则
- 违规时立即获得提醒和修正建议
- 像有个教练在旁边实时指导

## 📋 自我检查清单

### 1️⃣ 接到任务时
```python
# Claude Code应该立即自问：
□ 这个任务的复杂度如何？
□ 需要哪些类型的Agent？
□ Perfect21规则建议用几个Agent？
□ 应该并行还是串行？

# 调用守护者检查
from features.guardian.rule_guardian import get_rule_guardian
guardian = get_rule_guardian()
guardian.check_rule("task_analysis", context)
```

### 2️⃣ 选择Agent时
```python
# 必须检查：
□ 是否至少3个Agent？
□ 组合是否合理？
□ 是否设置为并行执行？

# 守护者会提醒
guardian.check_rule("agent_selection", {
    "selected_agents": agents,
    "execution_mode": "parallel"
})
```

### 3️⃣ 执行前
```python
# 最后确认：
□ 质量要求是否明确？
□ 反馈机制是否就绪？
□ Git hooks是否配置？

guardian.check_rule("before_execution", context)
```

### 4️⃣ 测试失败时
```python
# 关键决策点：
□ 是否触发反馈循环？
□ 是否回到原Agent修复？
□ 是否需要升级到专家？

guardian.check_rule("after_test", {
    "test_failed": True,
    "feedback_triggered": True  # 必须是True！
})
```

### 5️⃣ 提交代码时
```python
# 提交检查：
□ 提交消息格式正确？
□ 测试是否通过？
□ 质量门是否满足？

guardian.check_rule("before_commit", {
    "commit_message": "feat: 新功能",
    "tests_passed": True
})
```

## 🚨 违规警告示例

当Claude Code违反规则时，守护者会立即警告：

```
⚠️ Perfect21规则守护者发现违规:
============================================================

🔴 [CRITICAL] 最少Agent数量
   期望: 至少3个
   实际: 2个
   建议: Perfect21规则要求至少使用3个Agent并行执行

🟠 [HIGH] 并行执行
   期望: parallel
   实际: sequential
   建议: 多个Agent必须并行执行，使用单个function_calls批量调用

============================================================
```

## 💡 自动修复建议

守护者不只是警告，还会给出具体建议：

### 场景1：Agent太少
```
原计划：[backend-architect, test-engineer]
守护建议：添加 security-auditor, api-designer
理由：认证系统需要安全审查和API设计
```

### 场景2：忘记并行
```
错误方式：分开调用每个Agent
正确方式：
<function_calls>
  <invoke name="Task">...</invoke>
  <invoke name="Task">...</invoke>
  <invoke name="Task">...</invoke>
</function_calls>
```

### 场景3：测试失败直接提交
```
错误：测试失败 → 继续提交
正确：测试失败 → 反馈循环 → 同Agent修复 → 重新测试 → 通过后提交
```

## 🎮 使用方式

### 方式1：主动调用（推荐）
Claude Code在关键点主动调用守护者：
```python
# 在我的决策逻辑中
if about_to_select_agents:
    guardian.check_rule("agent_selection", my_context)
```

### 方式2：装饰器模式
```python
@guardian_check("agent_selection")
def select_agents(task):
    # 选择逻辑
    pass
```

### 方式3：上下文管理器
```python
with guardian.checkpoint("before_execution"):
    # 执行代码
    pass
```

## 📊 健康分数

守护者会维护一个健康分数（0-100）：
- 每个关键违规 -20分
- 每个普通违规 -5分
- 连续遵守规则 +10分

目标：保持80分以上

## 🔄 持续改进

守护者会记录所有违规历史，用于：
1. 识别常见错误模式
2. 优化规则定义
3. 改进Claude Code的行为习惯

## 🎯 最终目标

让Perfect21的规则不是死的文档，而是**活的监督者**：
- 实时监督
- 即时反馈
- 持续改进
- 习惯养成

通过规则守护者，Claude Code会逐渐养成遵守Perfect21规则的习惯，最终实现自动化的高质量执行。

---

**记住**：规则守护者不是限制，而是帮助。它确保Claude Code始终按照最佳实践工作。