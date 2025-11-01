# Implementation Plan
## 修复11个系统问题（1 CRITICAL + 3 HIGH + 4 MEDIUM + 3 LOW）

**版本**: 8.8.1 → 8.8.2
**分支**: rfc/fix-3-core-issues-properly
**日期**: 2025-11-01
**问题总数**: 11个（深度逻辑分析发现）

---

## 🎯 核心原则

1. **基于现有机制改进** - 不重新造轮子
2. **最小化改动** - 只修复真正的Gap
3. **避免重复** - 检查现有文件后再创建
4. **证据驱动** - 每个改动都有调研支撑
5. **分批修复** - P0立即修复，P1本周，P2-P3可选

---

## 📋 改动清单总览

### 🔴 CRITICAL修复（立即）

| 文件 | 类型 | 改动 | 理由 |
|------|------|------|------|
| `~/.claude.json` | 用户配置 | 修复permissions字段 | 全局覆盖项目配置（C1）|

### 🟠 HIGH修复（立即+本周）

| 文件 | 类型 | 改动 | 理由 |
|------|------|------|------|
| `.claude/skills/parallel-execution-guide.yml` | 修改 | 修复trigger配置 | Skill从未触发（H1）|
| `.workflow/SPEC.yaml` | 修改 | 重新定义immutable_kernel | 逻辑矛盾（H2）|
| `.claude/settings.json` | 修改 | 统一并行限制配置 | 配置冲突（H3）|
| `.workflow/gates.yml` | 修改 | 删除冗余并行限制 | 配置冲突（H3）|

### 🟡 MEDIUM修复（可选）

| 文件 | 类型 | 改动 | 理由 |
|------|------|------|------|
| `.claude/hooks/*` | 优化 | 消除重复功能 | Hooks vs Skills重复（M1）|
| `tools/verify-core-structure.sh` | 增强 | 加上SPEC.yaml检查 | 版本文件数量不一致（M2）|
| `.workflow/gates.yml` | 修改 | 更新Lock模式为strict | 观测期过期（M3）|
| `.workflow/steps/current` | 删除或链接 | 统一Phase状态文件 | 状态分散（M4）|

### 🟢 LOW优化（后续）

| 文件 | 类型 | 改动 | 理由 |
|------|------|------|------|
| `.claude/hooks/*` | 优化 | 性能优化 | Hooks延迟（L1）|
| `CLAUDE.md` | 文档 | 说明防绕过机制 | 文档完善（L2）|
| `.claude/hooks/phase_completion_validator.sh` | 增强 | 增加Bash检查 | 验证覆盖（L3）|

### 通用修改

| 文件 | 类型 | 改动 | 理由 |
|------|------|------|------|
| `VERSION` (×6) | 修改 | 8.8.1 → 8.8.2 | 版本升级 |
| `CHANGELOG.md` | 修改 | 记录11个问题修复 | 变更追踪 |

**预计修改文件数**:
- CRITICAL+HIGH: 5-6个
- MEDIUM: 4-5个（可选）
- LOW: 3-4个（可选）
- **总计**: 12-15个

**新增文件数**: 0个（全是修改现有文件）
**删除文件数**: 1个（.workflow/steps/current，可选）

---

## 🔧 详细实现方案

---

## 🔴 Phase 2.1: CRITICAL修复（立即执行）

### 任务C1: 修复Bypass Permissions全局配置覆盖 🔴

**优先级**: P0（CRITICAL）
**预计时间**: 15分钟
**复杂度**: 极低
**影响**: 修复后Task工具不再弹窗，并行执行恢复正常

#### 1.1 检查现有工具

```bash
# 检查是否已有修复工具
ls -la tools/fix-bypass-permissions.sh

# 如果存在且功能完整，直接使用
# 如果不存在或功能不足，创建简化版
```

#### 1.2 方案A: 已有工具完整（推荐）

如果`tools/fix-bypass-permissions.sh`已存在且功能完整：

```bash
# 直接使用
chmod +x tools/fix-bypass-permissions.sh
bash tools/fix-bypass-permissions.sh
```

#### 1.3 方案B: 创建简化版工具

如果需要创建，使用**最小化实现**：

**文件**: `tools/fix-bypass-permissions-simple.sh`

```bash
#!/bin/bash
# 简化版bypass permissions修复工具

GLOBAL_CONFIG="$HOME/.claude.json"

# 备份
cp "$GLOBAL_CONFIG" "$GLOBAL_CONFIG.backup.$(date +%s)"

# 使用jq添加permissions配置
jq '.permissions = {
  "defaultMode": "bypassPermissions",
  "allow": ["*"]
}' "$GLOBAL_CONFIG" > "$GLOBAL_CONFIG.tmp"

mv "$GLOBAL_CONFIG.tmp" "$GLOBAL_CONFIG"

echo "✅ 全局配置已修复"
echo "请重启Claude Code测试"
```

**大小**: ~20行
**功能**: 只修复permissions字段，避免复杂逻辑

#### 1.4 测试验证

```bash
# 测试1: 配置验证
bash tools/verify-bypass-permissions.sh

# 测试2: 重启Claude Code
# 观察是否还有权限提示

# 测试3: 实际使用Task工具
# 应该无需用户确认
```

**完成标准**:
- [ ] 全局配置permissions正确
- [ ] verify-bypass-permissions.sh通过
- [ ] 重启后无权限弹窗

---

### 任务2: 增强并行执行Skill提醒 ✅

**优先级**: P0
**预计时间**: 20分钟
**复杂度**: 低

#### 2.1 当前问题

`.claude/skills/parallel-execution-guide.yml`存在但trigger可能不够明确：

```yaml
trigger:
  phase_transition: "Phase1 → Phase2"  # 可能不触发
  event: "before_phase2_implementation"
```

#### 2.2 增强trigger

**文件**: `.claude/skills/parallel-execution-guide.yml`

**修改部分**（只改trigger和priority）:

```yaml
name: "parallel-execution-guide"
description: "指导AI在Phase 2正确使用Claude Code并行执行机制"
enabled: true
priority: "P0"  # 保持最高优先级

trigger:
  # 增强trigger条件，确保Phase 2时触发
  event: "before_tool_use"
  tool: ["Task", "Write", "Edit"]
  context: "phase2_detected"  # 检测到Phase2状态

prompt: |
  🚀 **Phase 2 并行执行指南** (Critical!)

  ⚠️ **关键原则**: 必须在**单个消息**中调用多个Task工具才能实现真正的并行！

  ## ✅ 正确方式（真并行）

  在单个消息中同时调用多个Task工具：

  <function_calls>
    <invoke name="Task">...</invoke>
    <invoke name="Task">...</invoke>
    <invoke name="Task">...</invoke>
  </function_calls>

  ## ❌ 错误方式（假并行，实际串行）

  - 生成parallel_groups配置文件，然后让脚本调度 ❌
  - 一个消息只调用一个Task，然后等结果，再调用下一个 ❌

  **典型加速比**: 3-6x（3个agent: 3x, 6个agent: 5.3x）

  ## 📋 实施步骤

  **Phase 2开始时**:
  1. 分析PLAN.md，识别可以并行的独立任务
  2. 在**一个消息**中调用多个Task工具（示例如上）
  3. 每个Task的prompt包含完整的任务描述和上下文
  4. 等待所有Task完成后，验证结果并整合

  **成功标准**:
  - 单个消息调用≥3个Task工具
  - 执行时间比串行快3x以上
  - 所有并行任务正确完成

  **记住**: 这不是配置问题，是使用方法问题！
```

**改动大小**: ~10行trigger修改，prompt保持原样

#### 2.3 替代方案: 添加PostToolUse Hook

如果Skills trigger不够可靠，创建Hook强制提醒：

**文件**: `.claude/hooks/parallel_execution_reminder.sh`（可选）

```bash
#!/bin/bash
# Parallel Execution Reminder - PostToolUse Hook
# 在Phase 2检测到Task使用时提醒AI

PHASE_CURRENT=".phase/current"

if [[ -f "$PHASE_CURRENT" ]]; then
    phase=$(cat "$PHASE_CURRENT")
    if [[ "$phase" == "Phase2" ]] && [[ "$TOOL_NAME" == "Task" ]]; then
        echo ""
        echo "💡 并行执行提醒:"
        echo "   在单个消息中调用多个Task才是真正的并行"
        echo "   参考: .claude/skills/parallel-execution-guide.yml"
        echo ""
    fi
fi

exit 0
```

**注册**: `.claude/settings.json` → `hooks.PostToolUse`

#### 2.4 测试验证

```bash
# 测试1: Skill触发
# 进入Phase 2，调用Task工具
# 应该看到并行执行指南提醒

# 测试2: 实际使用
# AI应该在单个消息中调用多个Task

# 测试3: 性能验证
# 记录并行vs串行的执行时间对比
```

**完成标准**:
- [ ] Phase 2时Skill或Hook触发
- [ ] AI收到清晰的并行执行指导
- [ ] 下次Phase 2实际使用并行方式

---

### 任务3: 增强verify-core-structure.sh（防掏空） ✅

**优先级**: P1
**预计时间**: 1小时
**复杂度**: 中

#### 3.1 当前功能

`tools/verify-core-structure.sh` (214行) 现在检查：
- 7 Phases数量
- 97检查点分布
- 2质量门禁
- 版本一致性（6文件）
- LOCK.json SHA256指纹

#### 3.2 新增检查

**添加运行时执行证据验证**:

```bash
# 在verify-core-structure.sh中添加新的检查函数

# 检查1: Hook文件大小（防掏空）
check_hook_not_hollowed() {
    local hook=$1
    local min_size=$2

    if [[ ! -f "$hook" ]]; then
        echo "❌ Hook missing: $hook"
        return 1
    fi

    size=$(wc -c < "$hook")
    if [[ $size -lt $min_size ]]; then
        echo "❌ Hook too small (hollowed?): $hook ($size bytes < $min_size)"
        return 1
    fi

    echo "✅ $hook intact ($size bytes)"
    return 0
}

# 检查2: Sentinel字符串验证（防逻辑删除）
check_sentinel_strings() {
    local file=$1
    shift
    local sentinels=("$@")

    for sentinel in "${sentinels[@]}"; do
        if ! grep -q "$sentinel" "$file"; then
            echo "❌ Missing sentinel string in $file: $sentinel"
            return 1
        fi
    done

    echo "✅ $file sentinel strings intact"
    return 0
}

# 检查3: Hook注册验证
check_hook_registered() {
    local hook_name=$1

    if ! grep -q "$hook_name" .claude/settings.json; then
        echo "❌ Hook not registered: $hook_name"
        return 1
    fi

    echo "✅ $hook_name registered"
    return 0
}

# 调用新检查
echo ""
echo "═══ Additional Integrity Checks ═══"

# Critical Hooks检查
check_hook_not_hollowed ".claude/hooks/pr_creation_guard.sh" 3000
check_sentinel_strings ".claude/hooks/pr_creation_guard.sh" "Phase7" "ACCEPTANCE_REPORT"

check_hook_not_hollowed ".claude/hooks/phase_completion_validator.sh" 5000
check_sentinel_strings ".claude/hooks/phase_completion_validator.sh" "Phase1" "comprehensive_cleanup"

check_hook_not_hollowed "scripts/comprehensive_cleanup.sh" 5000
check_sentinel_strings "scripts/comprehensive_cleanup.sh" ".phase/current" ".workflow/current"

# Hook注册检查
for hook in pr_creation_guard phase_completion_validator workflow_enforcer; do
    check_hook_registered "$hook"
done
```

**改动大小**: +80行左右

#### 3.3 可选增强: Hook依赖检查

如果时间允许，添加Hook依赖关系验证：

```bash
# 检查Hook之间的依赖关系
# 例如: workflow_enforcer → phase_completion_validator → pr_creation_guard

check_hook_dependencies() {
    # 定义依赖关系
    local deps=(
        "workflow_enforcer:phase_completion_validator"
        "phase_completion_validator:comprehensive_cleanup.sh"
    )

    for dep in "${deps[@]}"; do
        parent=$(echo "$dep" | cut -d: -f1)
        child=$(echo "$dep" | cut -d: -f2)

        # 检查依赖文件存在
        # ...
    done
}
```

#### 3.4 测试验证

```bash
# 测试1: 基本功能
bash tools/verify-core-structure.sh

# 测试2: Hook掏空检测
# 临时删除hook中的代码，保留空文件
# 应该检测到文件过小

# 测试3: Sentinel删除检测
# 临时删除sentinel字符串
# 应该检测到缺失
```

**完成标准**:
- [ ] Hook大小检查功能正常
- [ ] Sentinel字符串检查正常
- [ ] Hook注册验证正常
- [ ] 所有测试通过

---

### 任务4: 注册和集成 ✅

**优先级**: P0
**预计时间**: 15分钟
**复杂度**: 低

#### 4.1 更新settings.json

如果创建了新Hook，需要注册：

**文件**: `.claude/settings.json`

```json
{
  "hooks": {
    "PostToolUse": [
      // ... 现有hooks
      ".claude/hooks/parallel_execution_reminder.sh"  // 如果创建了
    ]
  },
  "version": "8.8.2"  // 更新版本号
}
```

#### 4.2 更新所有版本文件

**6个文件同步更新**:

```bash
# 使用现有脚本自动更新
bash scripts/bump_version.sh patch

# 或手动更新
echo "8.8.2" > VERSION
jq '.version = "8.8.2"' .claude/settings.json > .tmp && mv .tmp .claude/settings.json
# ... 其他4个文件
```

#### 4.3 更新CHANGELOG.md

**文件**: `CHANGELOG.md`

```markdown
## [8.8.2] - 2025-11-01

### Fixed - 3大核心问题修复（基于现有机制）

**问题1: Bypass Permissions失效**
- 修复全局配置`~/.claude.json`覆盖项目配置
- 工具: tools/fix-bypass-permissions-simple.sh (20行)
- 原理: 全局配置优先级 > 项目配置

**问题2: 并行执行失败**
- 增强parallel-execution-guide.yml的trigger
- 在Phase 2自动提醒AI使用单消息多Task
- 原理: 使用方法问题，非配置问题

**问题3: Workflow Enforcement确认**
- 验证pr_creation_guard.sh工作正常
- 无需修改，现有Hook有效

**元问题: 保护机制被破坏**
- 增强verify-core-structure.sh的检查
  - Hook大小验证（防掏空）
  - Sentinel字符串验证（防逻辑删除）
  - Hook注册验证
- 避免重复创建文件（PROTECTION_MANIFEST等已有）

**关键改进**:
- ✅ 基于现有机制改进，不重新造轮子
- ✅ 最小化改动（4-6个文件）
- ✅ 证据驱动（3个并行Task调研）
- ✅ 避免重复（检查后发现大量现有机制）

**修改文件数**: 4-6个
**新增文件数**: 0-1个
**代码行数**: +120行（净增加）
```

---

## 🏗️ 系统架构更新

### Before (v8.8.1)

```
保护机制:
├─ SPEC.yaml:immutable_kernel ✅ (已有)
├─ verify-core-structure.sh ✅ (已有，但检查不够)
├─ 50+ Hooks ✅ (已有)
└─ guard-core.yml CI ✅ (已有)

问题:
├─ Bypass permissions全局配置覆盖 ❌
├─ 并行执行Skill trigger不明确 ❌
└─ Hook掏空无法检测 ❌
```

### After (v8.8.2)

```
保护机制:
├─ SPEC.yaml:immutable_kernel ✅ (保持不变)
├─ verify-core-structure.sh ✅ (增强80行)
│   ├─ Hook大小检查 (新增)
│   ├─ Sentinel字符串验证 (新增)
│   └─ Hook注册验证 (新增)
├─ 50+ Hooks ✅ (保持不变)
├─ guard-core.yml CI ✅ (保持不变)
└─ fix-bypass-permissions ✅ (新增20行或使用现有)

改进:
├─ Bypass permissions全局配置修复 ✅
├─ 并行执行Skill trigger增强 ✅
└─ Hook掏空可检测 ✅
```

**关键**: 99%复用现有机制，只增强Gap部分

---

## 📊 工作量估算

| 任务 | 时间 | 复杂度 | 依赖 |
|------|------|--------|------|
| 任务1: 修复Bypass Permissions | 30分钟 | 低 | 无 |
| 任务2: 增强Skill trigger | 20分钟 | 低 | 无 |
| 任务3: 增强verify-core-structure | 1小时 | 中 | 无 |
| 任务4: 注册和集成 | 15分钟 | 低 | 任务1-3 |

**总预计时间**: 2小时5分钟
**可并行度**: 任务1-3可并行执行

---

## 🚀 执行顺序

### Phase 2: Implementation (并行执行)

**推荐并行方案**:

在**单个消息**中调用3个Task:

```xml
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">general-purpose</parameter>
    <parameter name="description">Task 1: 修复Bypass Permissions</parameter>
    <parameter name="prompt">
      任务: 修复Bypass Permissions全局配置冲突

      步骤:
      1. 检查tools/fix-bypass-permissions.sh是否存在
      2. 如果不存在或功能不足，创建简化版（20行）
      3. 执行修复脚本，更新~/.claude.json
      4. 运行verify-bypass-permissions.sh验证

      交付物:
      - tools/fix-bypass-permissions-simple.sh (如需创建)
      - 验证输出日志
    </parameter>
  </invoke>

  <invoke name="Task">
    <parameter name="subagent_type">general-purpose</parameter>
    <parameter name="description">Task 2: 增强并行执行Skill</parameter>
    <parameter name="prompt">
      任务: 增强parallel-execution-guide.yml的trigger

      步骤:
      1. 读取.claude/skills/parallel-execution-guide.yml
      2. 修改trigger部分，增强触发条件
      3. 保持prompt内容不变
      4. 测试Skill在Phase 2时触发

      交付物:
      - 修改后的parallel-execution-guide.yml
      - trigger逻辑说明
    </parameter>
  </invoke>

  <invoke name="Task">
    <parameter name="subagent_type">general-purpose</parameter>
    <parameter name="description">Task 3: 增强verify-core-structure</parameter>
    <parameter name="prompt">
      任务: 增强verify-core-structure.sh防止Hook掏空

      步骤:
      1. 读取tools/verify-core-structure.sh
      2. 添加3个新检查函数（80行）:
         - check_hook_not_hollowed (文件大小)
         - check_sentinel_strings (关键字符串)
         - check_hook_registered (注册验证)
      3. 集成到主验证流程
      4. 测试所有检查

      交付物:
      - 修改后的verify-core-structure.sh
      - 测试报告
    </parameter>
  </invoke>
</function_calls>
```

**预期加速**: 3x（2小时 → 40分钟）

### Phase 3-7: 标准流程

- Phase 3: 运行static_checks.sh
- Phase 4: 运行pre_merge_audit.sh + 手动审查
- Phase 5: 更新版本号 + CHANGELOG
- Phase 6: 用户验收
- Phase 7: 清理 + 创建PR

---

## 🎯 成功标准

### 技术标准

- [ ] Bypass permissions工作（无弹窗）
- [ ] 并行执行Skill在Phase 2触发
- [ ] verify-core-structure.sh检测到Hook掏空
- [ ] 所有静态检查通过
- [ ] Pre-merge audit通过
- [ ] 版本一致性100%

### 质量标准

- [ ] 无重复文件创建
- [ ] 基于现有机制改进
- [ ] 代码增量 <200行
- [ ] 修改文件数 ≤6个

### 用户验收标准

- [ ] 3个核心问题修复
- [ ] Protection Integrity = 100%
- [ ] 用户确认"没问题"

---

## 📝 风险和缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 全局配置修复后仍弹窗 | 低 | 中 | 准备多个备选方案 |
| Skill trigger不触发 | 中 | 低 | 添加PostToolUse Hook备选 |
| verify增强破坏现有功能 | 低 | 高 | 充分测试+备份 |
| 版本升级冲突 | 低 | 低 | 使用bump_version.sh自动化 |

---

## 📖 参考文档

- **现有机制**: `.workflow/SPEC.yaml:246-280` (immutable_kernel)
- **验证工具**: `tools/verify-core-structure.sh` (214行)
- **并行指南**: `docs/PARALLEL_SUBAGENT_STRATEGY.md` (454行)
- **Skill配置**: `.claude/skills/parallel-execution-guide.yml`
- **CI检查**: `.github/workflows/guard-core.yml`

---

**计划大小**: >500行 ✅
**下一步**: Phase 1完成，等待用户确认开始Phase 2
