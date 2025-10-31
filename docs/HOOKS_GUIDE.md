# Claude Enhancer Hooks完全指南

**版本**：8.8.0  
**更新日期**：2025-10-31  
**作者**：Claude Code Team

---

## 目录
1. [什么是Hooks？](#什么是hooks)
2. [Hooks分类](#hooks分类)
3. [20个Hooks详解](#20个hooks详解)
4. [如何创建新Hook](#如何创建新hook)
5. [Hook调试技巧](#hook调试技巧)
6. [Hook性能优化](#hook性能优化)
7. [常见问题FAQ](#常见问题faq)

---

## 1. 什么是Hooks？

Hooks是在Claude Code特定事件发生时自动执行的脚本，类似于Git hooks的概念。

**核心特点**：
- 自动触发（无需手动调用）
- 事件驱动（PrePrompt、PostToolUse等）
- 可配置（通过settings.json启用/禁用）
- 轻量级（<50ms执行时间）

**使用场景**：
- ✅ Phase转换验证（防止跳Phase）
- ✅ 分支管理提醒（新任务创建分支）
- ✅ 质量门禁检查（代码规范、测试覆盖率）
- ✅ 自动文档生成（checklist、traceability）

---

## 2. Hooks分类

### 2.1 PrePrompt Hooks（AI响应前触发）

**触发时机**：用户消息到达 → PrePrompt hooks执行 → AI生成响应

**用途**：
- 上下文注入（添加Phase状态、branch信息）
- 提醒机制（"您现在在Phase 3，需要..."）
- 状态检查（Phase一致性、分支名规范）

**执行顺序**：PrePrompt[1] → PrePrompt[2] → ... → PrePrompt[N]

**示例hooks**：
- branch_helper.sh（PrePrompt[3]）
- workflow_phase_injector.sh（PrePrompt[5]）

### 2.2 PreToolUse Hooks（工具使用前触发）

**触发时机**：AI决定使用工具 → PreToolUse hooks执行 → 工具执行

**用途**：
- 操作验证（Write根目录文档 → 拦截）
- 权限检查（修改敏感文件 → 审计）
- 自动修正（文件路径错误 → 提示）

**Hook接收参数**：
- TOOL_NAME（工具名：Write/Edit/Bash等）
- TOOL_PARAMS（工具参数：文件路径、命令等）

**示例hooks**：
- root_doc_enforcer.sh（拦截根目录文档创建）
- sensitive_file_protector.sh（保护敏感文件）

### 2.3 PostToolUse Hooks（工具使用后触发）

**触发时机**：工具执行完成 → PostToolUse hooks执行 → 返回结果

**用途**：
- 状态更新（Phase转换、进度追踪）
- 自动触发（Phase完成 → 生成checklist）
- 日志记录（操作审计、性能监控）

**Hook接收参数**：
- TOOL_NAME（工具名）
- TOOL_RESULT（工具执行结果）
- EXIT_CODE（退出码：0=成功）

**示例hooks**：
- phase_completion_validator.sh（Phase转换验证）
- checklist_generator.sh（自动生成checklist）

### 2.4 PostMessage Hooks（用户消息后触发）

**触发时机**：用户发送消息 → PostMessage hooks执行 → AI处理

**用途**：
- 消息预处理（关键词提取、意图识别）
- 上下文准备（加载相关文档）

**示例hooks**：
- message_intent_analyzer.sh

---

## 3. 20个Hooks详解

### 3.1 branch_helper.sh

**分类**：PrePrompt[3]  
**作用**：分支管理助手，提醒在main分支创建feature分支  
**触发时机**：每次AI响应前  
**配置位置**：`.claude/settings.json`

**检查逻辑**：
```bash
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" == "main" ]]; then
    echo "⚠️  You're on main branch. Consider creating a feature branch."
fi
```

**输出示例**：
```
⚠️  You're on main branch.
💡 Suggest: git checkout -b feature/your-task-name
```

**使用场景**：
- 用户在main分支开始新任务
- AI提醒创建feature分支

**性能**：<5ms

---

### 3.2 phase_completion_validator.sh

**分类**：PostToolUse  
**作用**：Phase转换验证，防止跳Phase  
**触发时机**：Write/Edit操作完成后  
**配置位置**：`.claude/settings.json`

**检查逻辑**：
```bash
# 检测Phase转换
if [[ "$TOOL_NAME" == "Write" ]] && [[ "$FILE_PATH" == ".phase/current" ]]; then
    OLD_PHASE=$(cat .phase/current.backup)
    NEW_PHASE=$(cat .phase/current)
    
    # 验证Phase转换合法性
    if ! is_valid_transition "$OLD_PHASE" "$NEW_PHASE"; then
        echo "❌ Invalid Phase transition: $OLD_PHASE → $NEW_PHASE"
        exit 1
    fi
fi
```

**Phase转换规则**：
- Phase1 → Phase2 ✓
- Phase2 → Phase3 ✓
- Phase3 → Phase1 ✗（不能回退）
- Phase5 → Phase7 ✗（不能跳Phase6）

**性能**：<10ms

---

### 3.3 checklist_generator.sh

**分类**：PostToolUse  
**作用**：自动生成双语checklist（技术版+用户版）  
**触发条件**：Phase 1.3完成（trigger: phase1.3_complete）  
**配置位置**：`.claude/settings.json`

**工作流程**：
1. 读取`.workflow/user_request.md`
2. 解析用户需求
3. 生成3个文件：
   - ACCEPTANCE_CHECKLIST.md（用户版，plain language）
   - TECHNICAL_CHECKLIST.md（技术版，professional terms）
   - TRACEABILITY.yml（映射关系）

**输入格式**（user_request.md）：
```markdown
## 你需要得到什么（用人话说）

### 问题1：Phase 7清理机制有Bug
**现象**：你merge代码到main分支后，系统留下了"Phase7"标记文件
**你希望**：merge后自动清理
**就像**：租车归还后清理车内
```

**输出示例**（ACCEPTANCE_CHECKLIST.md）：
```markdown
## 验收标准

### 场景1：merge代码后检查
- 你说"merge"
- AI执行merge
- 你检查main分支：`ls -la .phase/current`应该显示"文件不存在"
- ✅ 通过：文件不存在
- ❌ 失败：文件还在
```

**性能**：<100ms

---

### 3.4 ~ 3.20 其他Hooks（概览）

**完整列表**：
1. branch_helper.sh ✓（已详述）
2. phase_completion_validator.sh ✓（已详述）
3. checklist_generator.sh ✓（已详述）
4. root_doc_enforcer.sh - 防止根目录文档创建
5. parallel_subagent_suggester.sh - 并行执行提醒
6. per_phase_impact_assessor.sh - Phase级Impact Assessment
7. workflow_phase_injector.sh - Phase状态注入
8. impact_assessment_enforcer.sh - 强制Impact Assessment
9. agent_evidence_collector.sh - 证据收集
10. sensitive_file_protector.sh - 敏感文件保护
11. version_consistency_checker.sh - 版本一致性
12. changelog_reminder.sh - CHANGELOG提醒
13. test_coverage_enforcer.sh - 测试覆盖率强制
14. documentation_completeness_checker.sh - 文档完整性
15. performance_budget_monitor.sh - 性能预算监控
16. security_audit_trigger.sh - 安全审计
17. dependency_update_notifier.sh - 依赖更新通知
18. code_complexity_analyzer.sh - 代码复杂度
19. commit_message_validator.sh - 提交信息验证
20. pr_template_injector.sh - PR模板注入

**详细说明见完整版文档**

---

## 4. 如何创建新Hook

### 4.1 创建步骤

**Step 1：创建脚本文件**
```bash
touch .claude/hooks/my_custom_hook.sh
chmod +x .claude/hooks/my_custom_hook.sh
```

**Step 2：编写Hook逻辑**
```bash
#!/bin/bash
# my_custom_hook.sh - 我的自定义Hook

# Hook标准输入（由Claude Code注入）
# TOOL_NAME, TOOL_PARAMS, PHASE, BRANCH等

echo "🔍 My Custom Hook triggered"

# 你的检查逻辑
if [[ some_condition ]]; then
    echo "✅ Check passed"
    exit 0
else
    echo "❌ Check failed"
    exit 1
fi
```

**Step 3：注册到settings.json**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "name": "my_custom_hook",
        "path": ".claude/hooks/my_custom_hook.sh",
        "enabled": true,
        "description": "My custom hook description"
      }
    ]
  }
}
```

**Step 4：测试Hook**
```bash
# 模拟触发
TOOL_NAME="Write" \
TOOL_PARAMS='{"file_path":"test.md"}' \
bash .claude/hooks/my_custom_hook.sh
```

### 4.2 Hook开发最佳实践

**性能要求**：
- ⏱️ 执行时间 <50ms
- 🧪 测试覆盖率 ≥80%
- 📝 文档完整（README + 代码注释）

**错误处理**：
```bash
# 设置错误处理
set -euo pipefail

# 捕获错误
trap 'echo "❌ Hook failed at line $LINENO"' ERR
```

**日志记录**：
```bash
# 使用LOG_FILE环境变量
LOG_FILE="${LOG_FILE:-/tmp/claude_hooks.log}"
echo "[$(date -Iseconds)] my_custom_hook: Check passed" >> "$LOG_FILE"
```

---

## 5. Hook调试技巧

### 5.1 启用调试模式

```bash
# 设置DEBUG环境变量
export CLAUDE_HOOK_DEBUG=1

# Hook中添加调试输出
if [[ "${CLAUDE_HOOK_DEBUG:-0}" == "1" ]]; then
    echo "[DEBUG] TOOL_NAME=$TOOL_NAME"
    echo "[DEBUG] TOOL_PARAMS=$TOOL_PARAMS"
fi
```

### 5.2 查看Hook日志

```bash
# 查看所有hooks日志
tail -f /tmp/claude_hooks.log

# 查看特定hook
grep "my_custom_hook" /tmp/claude_hooks.log
```

### 5.3 手动触发Hook测试

```bash
# 模拟PreToolUse事件
TOOL_NAME="Write" \
TOOL_PARAMS='{"file_path":".phase/current","content":"Phase2"}' \
bash .claude/hooks/phase_completion_validator.sh

# 检查退出码
echo $?  # 0=成功, 1=失败
```

---

## 6. Hook性能优化

### 6.1 性能预算

| Hook类型 | 预算 | 实测 | 状态 |
|---------|------|------|------|
| PrePrompt | <20ms | 15ms | ✓ |
| PreToolUse | <50ms | 30ms | ✓ |
| PostToolUse | <100ms | 80ms | ✓ |

### 6.2 优化技巧

**避免慢操作**：
```bash
# ❌ 慢：遍历所有文件
find . -name "*.sh" -exec bash -n {} \;

# ✅ 快：使用缓存
if [[ ! -f .cache/validated_scripts ]]; then
    find . -name "*.sh" > .cache/script_list
fi
```

**并行检查**：
```bash
# 并行检查多个条件
(check_condition_1 &)
(check_condition_2 &)
wait
```

---

## 7. 常见问题FAQ

### Q1: Hook执行失败会影响Claude Code吗？

**A**: 取决于Hook类型：
- PreToolUse hook失败 → 工具不执行（拦截成功）
- PostToolUse hook失败 → 记录日志，不影响工具执行
- PrePrompt hook失败 → 跳过该hook，继续执行

### Q2: 如何临时禁用某个Hook？

**A**: 修改settings.json：
```json
{
  "name": "my_hook",
  "enabled": false  // 设置为false
}
```

### Q3: Hook可以修改工具参数吗？

**A**: PreToolUse hook可以通过输出修改参数：
```bash
# 修改file_path
echo "MODIFIED_PARAMS: {\"file_path\": \"docs/new_location.md\"}"
```

---

**总结**：
- 20个hooks覆盖workflow全流程
- 性能预算 <50ms
- 易于扩展和定制
- 完整测试和文档

**更多信息**：
- 源代码：`.claude/hooks/`
- 配置：`.claude/settings.json`
- 示例：`examples/hooks/`
