# Phase 1: 任务-分支绑定系统实现计划

**创建时间**: 2025-10-15
**基于**: P0_TASK_BRANCH_BINDING_DISCOVERY.md
**目标**: 实现100%强制的任务-分支绑定机制

---

## 🎯 P0 Acceptance Checklist（从Phase 0继承）

### 功能需求 (8项)
- [ ] 任务启动时自动创建绑定记录到JSON文件
- [ ] Write/Edit操作前自动验证分支绑定
- [ ] 分支不匹配时硬阻止操作（exit 1）
- [ ] 任务完成时自动清理绑定记录
- [ ] 提供清晰的错误信息（问题+原因+解决方案）
- [ ] 提供紧急绕过机制（task_force_unbind）
- [ ] 支持查询当前任务状态（task_status）
- [ ] 记录任务历史（task_history）

### 性能需求 (3项)
- [ ] Hook执行时间 < 50ms
- [ ] JSON读写操作 < 5ms
- [ ] 不阻塞正常git操作

### 质量需求 (4项)
- [ ] 所有脚本通过shellcheck语法检查
- [ ] 有完整的错误处理（set -euo pipefail）
- [ ] 有自动化测试用例（≥10个场景）
- [ ] 文档完整（使用手册+故障排除）

### 兼容性需求 (3项)
- [ ] 与Phase -1完全兼容（不冲突）
- [ ] 与现有hooks系统兼容
- [ ] 可以随时启用/禁用（通过settings.json）

**总计**: 18项验收标准

---

## 📋 实现任务分解

### 任务1: 任务生命周期管理脚本

**文件**: `.claude/hooks/task_lifecycle.sh`

**功能**:
- `task_start <description> <branch>` - 启动任务并创建绑定
- `task_complete` - 完成任务并清理绑定
- `task_status` - 查询当前任务状态
- `task_cancel` - 取消任务（紧急绕过）
- `task_history` - 查看任务历史

**输入输出**:
```bash
# 输入
$ task_start "任务-分支绑定系统" "feature/task-branch-binding"

# 输出
✅ 任务已启动
  ID: TASK_20251015_140000_abc12345
  描述: 任务-分支绑定系统
  绑定分支: feature/task-branch-binding

# 文件创建: .workflow/task_branch_map.json
```

**复杂度**: 简单
**预计时间**: 45分钟

---

### 任务2: 分支绑定强制执行器

**文件**: `.claude/hooks/task_branch_enforcer.sh`

**功能**:
- PreToolUse hook，在Write/Edit前执行
- 读取`.workflow/task_branch_map.json`
- 验证current_branch == bound_branch
- 不匹配时exit 1硬阻止

**关键逻辑**:
```bash
enforce_binding() {
    local active_task=$(jq -r '.active_task // empty' "$TASK_MAP")

    if [[ -z "$active_task" ]]; then
        # 无活动任务，允许操作
        return 0
    fi

    local bound_branch=$(echo "$active_task" | jq -r '.branch')
    local current_branch=$(git rev-parse --abbrev-ref HEAD)

    if [[ "$current_branch" != "$bound_branch" ]]; then
        show_binding_error "$active_task" "$current_branch"
        exit 1  # 硬阻止
    fi
}
```

**错误信息模板**:
```
╔═══════════════════════════════════════════════════════════╗
║  ❌ 任务-分支绑定冲突检测                               ║
╚═══════════════════════════════════════════════════════════╝

🔴 错误：当前分支与任务绑定不符

任务信息：
  ID: TASK_20251015_140000_abc12345
  描述: 任务-分支绑定系统实现
  绑定分支: feature/task-branch-binding

当前状态：
  当前分支: main

🚫 禁止操作：Write/Edit/MultiEdit 被阻止

✅ 解决方法（选择一项）：
  1. 切回正确分支：
     git checkout feature/task-branch-binding

  2. 完成当前任务：
     bash .claude/hooks/task_lifecycle.sh complete

  3. 紧急绕过（谨慎使用）：
     bash .claude/hooks/task_lifecycle.sh cancel
```

**复杂度**: 中等
**预计时间**: 1.5小时

---

### 任务3: AI行为监控器（可选）

**文件**: `.claude/hooks/ai_behavior_monitor.sh`

**功能**:
- PrePrompt hook，在AI思考前执行
- 检测git reflog中的分支切换频率
- ≥3次/小时显示警告信息
- exit 0（仅警告，不阻止）

**关键逻辑**:
```bash
detect_branch_chaos() {
    local threshold=3
    local switches=$(git reflog --since="1 hour ago" | grep -c "checkout:" || echo 0)

    if [[ $switches -ge $threshold ]]; then
        cat <<EOF >&2
⚠️⚠️⚠️ 警告：检测到频繁分支切换 ⚠️⚠️⚠️

过去1小时内切换分支: $switches 次（阈值: $threshold）

可能原因：
1. 任务规划不清晰，导致反复切换
2. 遇到问题未在当前分支解决
3. 违反"一任务一分支"原则

建议操作：
- 暂停当前工作
- 回顾任务目标和计划
- 确认正确的工作分支
- 在一个分支上完成整个任务
EOF
    fi
}
```

**复杂度**: 简单
**预计时间**: 30分钟

---

### 任务4: Hook注册配置

**文件**: `.claude/settings.json`

**修改内容**:
```json
{
  "PreToolUse": [
    ".claude/hooks/force_branch_check.sh",
    ".claude/hooks/task_branch_enforcer.sh",  // ← 新增
    ".claude/hooks/branch_helper.sh",
    ".claude/hooks/workflow_enforcer.sh"
  ],
  "PrePrompt": [
    ".claude/hooks/ai_behavior_monitor.sh"  // ← 新增（可选）
  ]
}
```

**复杂度**: 极简单
**预计时间**: 5分钟

---

### 任务5: 自动化测试套件

**文件**: `test/test_task_branch_binding.sh`

**测试场景** (≥10个):

1. **正常流程测试**
   - Test 1: 任务启动 → 绑定创建 → 验证JSON内容
   - Test 2: 正确分支 → Write操作 → 应该成功
   - Test 3: 任务完成 → 绑定清除 → 验证JSON为空

2. **错误场景测试**
   - Test 4: 切换到错误分支 → Write操作 → 应该被阻止
   - Test 5: 无活动任务 → Write操作 → 应该成功
   - Test 6: JSON文件损坏 → 应该优雅降级

3. **生命周期测试**
   - Test 7: task_status → 显示当前任务信息
   - Test 8: task_cancel → 强制取消绑定
   - Test 9: task_history → 显示历史任务

4. **性能测试**
   - Test 10: Hook执行时间 < 50ms
   - Test 11: JSON读取时间 < 5ms

5. **边界测试**
   - Test 12: 分支名包含特殊字符
   - Test 13: 任务描述包含换行符
   - Test 14: 并发操作安全性

**实现示例**:
```bash
#!/bin/bash
# Test 4: 切换到错误分支应该被阻止

test_branch_switch_blocked() {
    echo "[TEST 4] Branch switch should be blocked"

    # Setup
    bash .claude/hooks/task_lifecycle.sh start "测试任务" "feature/test"
    git checkout -b feature/test

    # 切换到错误分支
    git checkout main

    # 尝试Write操作（应该被阻止）
    if bash .claude/hooks/task_branch_enforcer.sh 2>/dev/null; then
        echo "❌ FAIL: 操作未被阻止"
        return 1
    else
        echo "✅ PASS: 操作被正确阻止"
        return 0
    fi

    # Cleanup
    bash .claude/hooks/task_lifecycle.sh complete
    git checkout main
    git branch -D feature/test
}
```

**复杂度**: 中等
**预计时间**: 2小时

---

### 任务6: 文档编写

**文件1**: `docs/TASK_BRANCH_BINDING_USER_GUIDE.md`

**内容**:
- 功能介绍
- 使用场景
- 命令参考（task_start/complete/status/cancel）
- 常见问题FAQ
- 故障排除

**文件2**: `CHANGELOG.md` 更新

**内容**:
```markdown
## [6.5.0] - 2025-10-15

### ✨ Added
- **任务-分支绑定系统**: 100%强制防止任务中途切换分支
  - 自动追踪任务-分支绑定关系
  - PreToolUse硬阻止跨分支操作
  - 清晰的错误提示和解决方案
  - 任务生命周期管理（start/complete/cancel）
  - 可选的AI行为监控和警告
```

**复杂度**: 简单
**预计时间**: 1小时

---

## 🔗 依赖关系

```
任务1 (task_lifecycle.sh)
  └─ 独立，优先实现

任务2 (task_branch_enforcer.sh)
  ├─ 依赖: 任务1（需要task_lifecycle.sh的函数）
  └─ 优先级: 高（核心功能）

任务3 (ai_behavior_monitor.sh)
  └─ 独立，可并行，可选

任务4 (settings.json)
  ├─ 依赖: 任务2完成后注册
  └─ 优先级: 高

任务5 (test suite)
  ├─ 依赖: 任务1-2完成
  └─ 并行: 可与任务3并行

任务6 (文档)
  ├─ 依赖: 所有功能完成
  └─ 优先级: 中（最后实施）
```

**关键路径**: 任务1 → 任务2 → 任务4 → 任务5 → 任务6

---

## 📊 时间估算

| 任务 | 复杂度 | 预计时间 |
|------|--------|----------|
| 任务1: task_lifecycle.sh | 简单 | 45分钟 |
| 任务2: task_branch_enforcer.sh | 中等 | 1.5小时 |
| 任务3: ai_behavior_monitor.sh | 简单 | 30分钟 |
| 任务4: settings.json | 极简单 | 5分钟 |
| 任务5: test suite | 中等 | 2小时 |
| 任务6: 文档 | 简单 | 1小时 |
| **总计** | | **~6小时** |

---

## 🎯 成功指标

### 短期指标（本PR）
- ✅ 18/18 P0验收标准通过
- ✅ 10/10 测试场景通过
- ✅ Hook执行时间 < 50ms
- ✅ 代码质量 ≥ 90/100

### 长期指标（3个月）
- 📉 分支混乱事件：从100% → 0%
- 📈 一任务一分支一PR率：从60% → 100%
- ⏱️ PR review时间：减少30%
- 📊 Git历史清晰度：主观评分8/10 → 10/10

---

## 🚨 风险管理

### 技术风险

**风险1**: JSON文件损坏导致hook失败
- **等级**: 低
- **缓解**: 添加validate函数，损坏时自动重建
- **Plan B**: 降级为纯文本存储（branch name only）

**风险2**: jq命令不可用
- **等级**: 极低
- **缓解**: 安装检测+友好提示
- **Plan B**: 使用grep/sed解析（性能略降）

**风险3**: Hook性能影响开发体验
- **等级**: 极低
- **缓解**: 性能测试确保<50ms
- **Plan B**: 异步检查（降低准确性）

### 用户体验风险

**风险4**: AI被频繁误报阻止
- **等级**: 中
- **缓解**: 完善错误信息，提供3种解决方案
- **Plan B**: 提供--force标志绕过（记录日志）

**风险5**: 紧急情况无法操作
- **等级**: 低
- **缓解**: 提供task_cancel紧急绕过
- **Plan B**: 直接删除.workflow/task_branch_map.json

---

## 📋 实施检查清单

### Phase 2 (实现)
- [ ] 创建`.workflow/`目录（如不存在）
- [ ] 实现task_lifecycle.sh（4个函数）
- [ ] 实现task_branch_enforcer.sh（核心验证逻辑）
- [ ] 实现ai_behavior_monitor.sh（可选）
- [ ] 更新settings.json（注册hooks）

### Phase 3 (测试)
- [ ] 编写test_task_branch_binding.sh
- [ ] 执行10个测试场景
- [ ] 验证性能指标（<50ms）
- [ ] 修复发现的bugs

### Phase 4 (文档)
- [ ] 编写用户手册
- [ ] 更新CHANGELOG.md
- [ ] 更新CLAUDE.md（如需）

### Phase 5 (审查)
- [ ] 代码审查（code-reviewer agent）
- [ ] 安全审计（security-auditor agent）
- [ ] 对照P0 checklist逐项验证

### Phase 6 (发布)
- [ ] 创建PR
- [ ] CI通过
- [ ] Merge到main
- [ ] 更新VERSION（如需）

---

## 💡 未来扩展（v6.6+）

### 扩展1: AI自动化
- AI自动调用task_start（检测到新任务时）
- AI自动调用task_complete（检测到PR merge时）
- 零人工干预

### 扩展2: 数据分析
- 统计任务平均时长
- 统计分支切换频率
- 生成开发效率报告

### 扩展3: IDE集成
- VSCode插件显示当前任务状态
- 分支切换时自动提示
- 可视化任务历史

---

**创建时间**: 2025-10-15
**预计完成**: 2025-10-15 (同一天)
**负责人**: Claude Code
**状态**: 待实施
