# Phase 1: Phase -1工作流违规修复 - 实施规划

## 📋 任务概述

**目标**: 将Phase -1（规则0：新任务=新分支）的违规率从50% → 0%

**方案**: 3层防护架构（Hook + PrePrompt + 文档）

**预计时间**: 2小时

---

## 🎯 P0 Acceptance Checklist（从Phase 0继承）

### 必须100%完成的标准

#### 功能完整性（8项）
- [ ] branch_helper.sh删除EXECUTION_MODE检测
- [ ] branch_helper.sh存在exit 1硬阻止
- [ ] force_branch_check.sh创建且可执行
- [ ] force_branch_check.sh包含CRITICAL警告
- [ ] CLAUDE.md第1行是强制指令
- [ ] settings.json注册force_branch_check.sh到PrePrompt
- [ ] 自动创建分支默认启用
- [ ] 3层逻辑一致（都提到规则0）

#### 质量标准（4项）
- [ ] 压力测试通过率≥95%
- [ ] Hook执行时间<100ms
- [ ] 所有hook语法正确（bash -n）
- [ ] 日志记录完整

#### 文档完整性（3项）
- [ ] P0文档生成（可行性分析）
- [ ] P1文档生成（本文件）
- [ ] REVIEW.md生成（Phase 5）

**总计**: 15项验收标准

---

## 📝 详细任务清单

### 任务1: 修复branch_helper.sh（优先级P0）

**目标**: 将v2.0改造为v3.0，实现无条件硬阻止

**受影响文件**: `.claude/hooks/branch_helper.sh`

**具体改动**:

1. **删除不可靠的EXECUTION_MODE检测**（行24-35）
   ```bash
   # 删除这些代码：
   EXECUTION_MODE=false
   if [[ "$CE_EXECUTION_MODE" == "true" ]] || \
      [[ "$TOOL_NAME" =~ ^(Write|Edit|MultiEdit)$ ]] || \
      [[ -f "$PROJECT_ROOT/.workflow/ACTIVE" ]]; then
       EXECUTION_MODE=true
   fi
   ```

2. **修改版本声明**（行7）
   ```bash
   # 修改前:
   # 版本：2.0

   # 修改后:
   # 版本：3.0 - 100%强制执行模式（无条件硬阻止）
   ```

3. **添加修复说明**（行8-9，新增）
   ```bash
   # 修复日期：2025-10-15
   # 修复原因：之前的EXECUTION_MODE检测不可靠，导致50%违规率
   ```

4. **改造主逻辑为无条件检测**（行77-156）
   ```bash
   # 改为直接检测分支，不依赖EXECUTION_MODE
   if [[ "$current_branch" == "main" ]] || [[ "$current_branch" == "master" ]]; then
       # 优先级1: 自动创建分支（默认启用）
       if [[ "${CE_AUTO_CREATE_BRANCH:-true}" == "true" ]]; then
           date_str=$(date +%Y%m%d-%H%M%S)
           new_branch="feature/auto-${date_str}"
           git checkout -b "$new_branch" 2>/dev/null && exit 0
       fi

       # 优先级2: 硬阻止
       echo "❌ 错误：禁止在 $current_branch 分支上修改文件" >&2
       echo "💡 这是100%强制规则，不是建议！" >&2
       exit 1  # ← 硬阻止
   fi
   ```

5. **更改默认行为**（行85）
   ```bash
   # 修改前:
   if [[ "${CE_AUTO_CREATE_BRANCH:-false}" == "true" ]]; then

   # 修改后:
   if [[ "${CE_AUTO_CREATE_BRANCH:-true}" == "true" ]]; then
   ```

**验收标准**:
- ✅ 文件中不再有"EXECUTION_MODE=false"
- ✅ 存在"exit 1"硬阻止逻辑
- ✅ 版本号是3.0
- ✅ 默认值是:-true
- ✅ bash -n语法检查通过

**预计时间**: 30分钟

---

### 任务2: 创建force_branch_check.sh（优先级P0）

**目标**: 创建PrePrompt hook，在AI思考前注入警告

**新建文件**: `.claude/hooks/force_branch_check.sh`

**文件内容**:

```bash
#!/bin/bash
# Claude Enhancer - PrePrompt强制分支检查（规则0：Phase -1）
# 版本：1.0
# 创建日期：2025-10-15
# 目的：在AI思考之前注入强制警告，确保100%遵守Phase -1分支检查

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/claude_hooks.log"
mkdir -p "$(dirname "$LOG_FILE")"

# 记录激活
echo "$(date +'%F %T') [force_branch_check.sh v1.0] PrePrompt triggered" >> "$LOG_FILE"

# 获取当前分支
current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

# 如果不在git仓库，跳过
if [[ -z "$current_branch" ]]; then
    exit 0
fi

# 检测main/master分支
if [[ "$current_branch" == "main" ]] || [[ "$current_branch" == "master" ]]; then
    # 注入强制警告到AI上下文
    cat <<'EOF' >&2

╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  ⚠️ ⚠️ ⚠️  CRITICAL: 你正在 MAIN/MASTER 分支上！ ⚠️ ⚠️ ⚠️             ║
║                                                                           ║
║  🔴 规则0（Phase -1）强制要求：新任务 = 新分支                          ║
║                                                                           ║
║  ❌ 你**禁止**在main/master分支上执行任何Write/Edit操作                 ║
║                                                                           ║
║  ✅ 你**必须**先执行以下命令创建新分支：                                ║
║                                                                           ║
║     git checkout -b feature/任务描述                                     ║
║                                                                           ║
║  💡 这是100%强制规则，不是建议！                                        ║
║     违反将导致Hook硬阻止（exit 1）                                      ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

EOF

    echo "$(date +'%F %T') [force_branch_check.sh v1.0] WARNING: AI on $current_branch, warning injected" >> "$LOG_FILE"

    # PrePrompt hook不应该阻止（exit 0），而是注入警告
    # 实际阻止由PreToolUse hook (branch_helper.sh) 完成
    exit 0
else
    # 在feature分支上 - 静默通过
    echo "$(date +'%F %T') [force_branch_check.sh v1.0] PASSED: on branch $current_branch" >> "$LOG_FILE"
    exit 0
fi
```

**后续操作**:
```bash
chmod +x .claude/hooks/force_branch_check.sh
```

**验收标准**:
- ✅ 文件存在且可执行（-x）
- ✅ 包含CRITICAL警告消息框
- ✅ 包含"规则0"和"Phase -1"引用
- ✅ 存在"exit 0"（PrePrompt不硬阻止）
- ✅ bash -n语法检查通过

**预计时间**: 20分钟

---

### 任务3: 更新CLAUDE.md顶部（优先级P0）

**目标**: 在第1行添加强制执行指令（impossible to miss）

**受影响文件**: `CLAUDE.md`

**具体改动**:

在文件最顶部（标题之前）插入：

```markdown
🚨🚨🚨 **AI强制执行指令（优先级最高）** 🚨🚨🚨

**在执行任何Write/Edit操作之前，你必须：**

1. **检查当前分支**（执行`git rev-parse --abbrev-ref HEAD`）
2. **如果在main/master分支**：
   - ❌ 禁止执行任何Write/Edit操作
   - ✅ 必须先执行：`git checkout -b feature/任务描述`
   - 💡 这是100%强制规则，违反将被Hook硬阻止（exit 1）
3. **如果在feature分支**：
   - ✅ 检查分支名是否与当前任务相关
   - 🟡 不相关则建议创建新分支

**规则0（Phase -1）：新任务 = 新分支（No Exceptions）**

这不是建议，是强制要求。所有编码任务必须从分支检查开始。

---

# Claude Enhancer 6.3 - 专业级个人AI编程工作流系统
（原有内容继续）
```

**验收标准**:
- ✅ 第1行是"🚨🚨🚨 AI强制执行指令"
- ✅ 包含"检查当前分支"指令
- ✅ 包含"禁止执行任何Write/Edit操作"
- ✅ 包含"git checkout -b feature"命令
- ✅ 包含"100%强制规则"声明

**预计时间**: 15分钟

---

### 任务4: 更新settings.json配置（优先级P0）

**目标**: 将force_branch_check.sh注册到PrePrompt（最高优先级）

**受影响文件**: `.claude/settings.json`

**具体改动**:

```json
// 修改前:
"PrePrompt": [
  ".claude/hooks/workflow_enforcer.sh",
  ".claude/hooks/smart_agent_selector.sh",
  ".claude/hooks/gap_scan.sh"
],

// 修改后:
"PrePrompt": [
  ".claude/hooks/force_branch_check.sh",  // ← 新增，优先级第1
  ".claude/hooks/workflow_enforcer.sh",
  ".claude/hooks/smart_agent_selector.sh",
  ".claude/hooks/gap_scan.sh"
],
```

**验收标准**:
- ✅ PrePrompt数组包含"force_branch_check.sh"
- ✅ force_branch_check.sh在第1位（优先级最高）
- ✅ JSON语法正确（python3 -m json.tool验证）

**预计时间**: 5分钟

---

### 任务5: 压力测试（优先级P1）

**目标**: 验证3层防护架构的完整性和性能

**测试脚本**: `/tmp/phase_minus1_stress_test_fixed.sh`

**测试覆盖**:
1. **层1测试**（7项）: Hook可执行性、版本、逻辑、语法
2. **层2测试**（6项）: PrePrompt可执行性、版本、警告、语法
3. **层3测试**（6项）: 文档位置、内容、强制性
4. **集成测试**（4项）: settings.json配置、优先级
5. **逻辑测试**（2项）: 3层一致性
6. **性能测试**（2项）: 执行时间<100ms

**验收标准**:
- ✅ 通过率≥95%（27/28或更好）
- ✅ Hook执行时间<100ms
- ✅ PrePrompt执行时间<100ms
- ✅ 所有语法检查通过

**预计时间**: 30分钟

---

### 任务6: 文档生成（优先级P1）

**目标**: 生成Phase 0、Phase 1、Phase 5文档

**文件清单**:
1. `docs/P0_PHASE_MINUS1_FIX_DISCOVERY.md` - 可行性分析
2. `docs/P1_PHASE_MINUS1_FIX_PLAN.md` - 本文件
3. `.temp/REVIEW_PHASE_MINUS1_FIX.md` - 代码审查报告（Phase 5生成）

**验收标准**:
- ✅ P0文档包含4个Spike验证
- ✅ P1文档包含6个详细任务
- ✅ REVIEW.md包含完整审查报告

**预计时间**: 20分钟

---

## 🗂️ 受影响文件清单

### 修改的文件（3个）
1. `.claude/hooks/branch_helper.sh` - v2.0 → v3.0（约60行改动）
2. `.claude/settings.json` - PrePrompt配置（1行新增）
3. `CLAUDE.md` - 顶部强制指令（16行新增）

### 新建的文件（4个）
4. `.claude/hooks/force_branch_check.sh` - v1.0（87行）
5. `docs/P0_PHASE_MINUS1_FIX_DISCOVERY.md` - Phase 0文档
6. `docs/P1_PHASE_MINUS1_FIX_PLAN.md` - 本文件
7. `.temp/REVIEW_PHASE_MINUS1_FIX.md` - Phase 5审查报告

### 测试文件（2个）
8. `/tmp/phase_minus1_stress_test_fixed.sh` - 压力测试脚本
9. `.temp/phase_minus1_stress_test_report.md` - 测试报告

---

## 🔄 回滚方案

### 场景1: Hook阻止正常操作

**症状**: 在feature分支也被阻止

**诊断**:
```bash
# 检查当前分支
git rev-parse --abbrev-ref HEAD

# 检查hook日志
tail -20 .workflow/logs/claude_hooks.log
```

**回滚**:
```bash
# 方案A: 临时禁用hook
export CE_AUTO_CREATE_BRANCH=false

# 方案B: 恢复v2.0
git restore .claude/hooks/branch_helper.sh
```

---

### 场景2: PrePrompt警告过于频繁

**症状**: 每次操作都显示警告框

**诊断**: 检查是否在main分支

**回滚**:
```bash
# 从settings.json移除force_branch_check.sh
vim .claude/settings.json
# 删除第32行
```

---

### 场景3: 测试未通过（<95%）

**症状**: 压力测试失败项>2个

**处理**:
1. 不要merge到main
2. 在feature分支继续修复
3. 重新运行测试
4. 通过率≥95%后才merge

---

## 📊 时间估算

| 任务 | 预计时间 | 复杂度 | 依赖 |
|-----|---------|--------|-----|
| 任务1: branch_helper.sh | 30分钟 | 中等 | 无 |
| 任务2: force_branch_check.sh | 20分钟 | 简单 | 无 |
| 任务3: CLAUDE.md | 15分钟 | 简单 | 无 |
| 任务4: settings.json | 5分钟 | 简单 | 任务2完成 |
| 任务5: 压力测试 | 30分钟 | 简单 | 任务1-4完成 |
| 任务6: 文档生成 | 20分钟 | 简单 | 任务5完成 |
| **总计** | **2小时** | | |

---

## 🎯 成功指标

### 短期指标（完成时）
- ✅ 违规率: 50% → 0%
- ✅ 测试通过率: ≥95%
- ✅ Hook性能: <100ms
- ✅ P0验收: 15/15通过

### 中期指标（1周后）
- ✅ 实际违规次数: 0次
- ✅ 自动创建分支成功率: >90%
- ✅ 用户反馈: 正面

### 长期指标（1个月后）
- ✅ 零违规事故
- ✅ Hook稳定性: 100%
- ✅ 成为Claude Enhancer标准流程

---

## 🔗 依赖关系

```
任务1 (branch_helper.sh) ─┐
任务2 (force_branch_check) ┼─→ 任务4 (settings.json) ─→ 任务5 (测试) ─→ 任务6 (文档)
任务3 (CLAUDE.md) ─────────┘
```

**并行执行建议**:
- Phase 2: 任务1 + 任务2 + 任务3（并行）
- Phase 3: 任务4（依赖任务2）
- Phase 4: 任务5（依赖任务1-4）
- Phase 5: 任务6（依赖任务5）

---

## 📈 预期收益

| 维度 | 修复前 | 修复后 | 改进 |
|-----|-------|-------|-----|
| **可靠性** | 50%违规 | 0%违规 | **100%改善** |
| **效率** | 手动修复 | 自动创建分支 | **节省5分钟/次** |
| **体验** | 困惑 | 清晰指引 | **满意度↑** |
| **维护** | 频繁问题 | 零维护 | **成本↓** |

---

创建时间: 2025-10-15
预计完成: 2小时
验收标准: 15项P0 checklist
成功标准: 通过率≥95%, 违规率=0%
