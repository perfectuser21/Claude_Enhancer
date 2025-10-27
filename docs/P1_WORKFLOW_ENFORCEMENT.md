# Phase 1: Discovery - Workflow Enforcement Mechanism

## 问题分析

### 当前问题
在v8.0.1开发中，AI跳过了完整的7-Phase workflow：
- ❌ 没有创建Phase 1文档（P1_DISCOVERY.md, ACCEPTANCE_CHECKLIST.md, PLAN.md）
- ❌ 直接cherry-pick commit并修改代码
- ❌ 直接创建PR和merge
- ✅ 结果：虽然代码正确，但违反了workflow规则

### 根本原因
**缺少自动化机制来强制执行workflow**

当前状态：
- 文档说明了规则（CLAUDE.md中的规则0）
- 但没有技术手段阻止违反
- 完全依赖AI自觉遵守

### 风险
1. **一致性风险**：不同任务可能采用不同流程
2. **追溯性风险**：缺少Phase 1文档，6个月后不知道为什么做某个改动
3. **质量风险**："小改动"可能跳过关键验证
4. **习惯风险**：偶尔跳过→经常跳过→workflow失效

## 技术发现

### 检测点分析

**在哪里检测workflow违规？**

| 检测点 | 时机 | 检测内容 | 优缺点 |
|--------|------|----------|--------|
| `.claude/hooks/PreToolUse` | AI准备写代码前 | 检查是否存在P1文档 | ✅ 最早拦截<br>❌ 只能提醒，无法强制 |
| `.git/hooks/pre-commit` | Git commit前 | 检查分支是否有P1文档 | ✅ 本地强制<br>✅ 可以硬阻止 |
| `.github/workflows` | CI时 | PR必须包含P1文档 | ✅ 服务端强制<br>❌ 太晚（已经commit了）|

**推荐方案**：**三层防护**
1. PreToolUse hook - AI层提醒（软阻止）
2. pre-commit hook - 本地强制（硬阻止）
3. GitHub Actions - 服务端验证（最终防线）

### 检测逻辑

**如何判断是否跳过workflow？**

```bash
# 检查1：分支命名
if [[ $BRANCH =~ ^(feature|bugfix|perf|refactor|style)/ ]]; then
  # 这是编码任务分支，需要workflow
  NEEDS_WORKFLOW=true
fi

# 检查2：是否有代码改动
CODE_CHANGES=$(git diff --cached --name-only | grep -E '\.(sh|py|js|ts|yml|yaml)$')
if [[ -n "$CODE_CHANGES" ]]; then
  NEEDS_WORKFLOW=true
fi

# 检查3：是否存在Phase 1文档
P1_EXISTS=$(ls docs/P1_*.md 2>/dev/null | wc -l)
CHECKLIST_EXISTS=$(ls docs/*CHECKLIST*.md 2>/dev/null | wc -l)
PLAN_EXISTS=$(ls docs/PLAN*.md 2>/dev/null | wc -l)

# 判断
if [[ $NEEDS_WORKFLOW == true ]] && [[ $P1_EXISTS == 0 ]]; then
  echo "❌ 错误：编码任务但没有Phase 1文档"
  exit 1
fi
```

### 豁免机制

**什么情况下可以跳过？**

创建 `.workflow/BYPASS_WORKFLOW` 文件：
```json
{
  "reason": "Emergency hotfix - production down",
  "approved_by": "user",
  "task": "Fix critical security vulnerability",
  "timestamp": "2025-10-27T16:00:00Z",
  "expires_after_commit": true
}
```

条件：
- ✅ 用户明确创建bypass文件
- ✅ 有明确理由
- ✅ 仅对当前commit有效
- ✅ commit后自动删除

## 解决方案设计

### 方案1：Workflow Guardian Hook（推荐）

**实现位置**：`.git/hooks/pre-commit`

**功能**：
1. 检测当前分支类型
2. 检测是否有代码改动
3. 检查Phase 1文档是否存在
4. 如果违规，硬阻止commit并给出清晰提示

**优点**：
- ✅ 在本地就阻止违规
- ✅ 清晰的错误提示
- ✅ 可以提供bypass机制
- ✅ 不依赖CI

**缺点**：
- ⚠️ 可以用`--no-verify`绕过（但会被GitHub PR检查拦截）

### 方案2：AI层软提醒

**实现位置**：`.claude/hooks/workflow_enforcer.sh` (PreToolUse)

**功能**：
- 在AI准备写代码前检查
- 如果没有P1文档，提醒AI先创建
- 不硬阻止，但强烈建议

### 方案3：GitHub Actions验证

**实现位置**：`.github/workflows/workflow-validation.yml`

**功能**：
- PR必须包含Phase 1文档
- 如果是`feature/*`或`bugfix/*`分支，强制检查
- 最终防线

## 技术栈

- **Bash**: pre-commit hook实现
- **Git**: 分支和改动检测
- **JSON**: bypass配置文件
- **GitHub Actions**: CI验证

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 用户用`--no-verify`绕过 | 中 | GitHub Actions作为最终防线 |
| 误判（非编码任务被拦截） | 低 | 明确的分支命名规则 + bypass机制 |
| 开发体验下降 | 低 | 清晰的错误提示 + 简化Phase 1模板 |

## Impact Assessment

- **Risk**: Low（技术成熟，逻辑清晰）
- **Complexity**: Medium（需要整合到现有hook系统）
- **Scope**: 4个文件（1个新hook, 2个CI配置, 1个文档）
- **Impact Radius**: **25** (Low-Medium)

**Agent建议**: 0个（solo work，简单hook脚本）

---

## 实现状态更新 (2025-10-27)

### Phase 2 完成

**已实现**:
1. ✅ `scripts/workflow_guardian.sh` (234行)
   - 分支类型检测 (coding/docs/protected)
   - 代码改动检测 (支持10+语言)
   - Phase 1文档检测 (P1_*.md, *CHECKLIST*.md, PLAN*.md)
   - Bypass机制 (.workflow/BYPASS_WORKFLOW)
   - 清晰的错误提示和修复指导

2. ✅ 集成到 `.git/hooks/pre-commit`
   - 位置: Check 2.5 (在comprehensive_guard之前)
   - 硬阻止: 违规时exit 1
   - 性能: <2秒

3. ✅ 测试验证
   - Positive case: Phase 1文档存在 → allowed ✅
   - 集成测试: Hook正确调用 ✅

### 已知限制

**限制1: Phase 1文档检测精度**
- **问题**: 检测ANY matching文件，不验证是否与当前分支相关
- **影响**: 如果repo中有其他分支的P1文档，会误判通过
- **示例**:
  - 当前分支: `feature/new-feature` (无Phase 1文档)
  - repo中存在: `docs/P1_DISCOVERY.md` (其他分支的)
  - 结果: Guardian误判为满足要求 ❌

**改进方向**:
- 方案A: 分支特定命名 (`P1_<branch-name>.md`)
- 方案B: 文档内branch字段验证
- 方案C: git时间戳验证 (文档commit时间 vs 分支创建时间)

**限制2: .git/hooks不被git追踪**
- **问题**: Hook修改需要手动同步到所有开发机
- **缓解**:
  - 通过CI验证确保hook已正确安装
  - 提供 `.claude/install.sh` 自动安装

### 下一步 (Phase 3-7)

**Phase 3 - Testing**:
- [ ] 完善negative test (需要先修复限制1)
- [ ] Bypass机制测试
- [ ] docs分支豁免测试
- [ ] 性能测试 (确保<2秒)

**Phase 4 - Implementation续**:
- [ ] AI层hook: `.claude/hooks/workflow_guardian.sh` (PreToolUse提醒)
- [ ] CI验证: `.github/workflows/workflow-validation.yml`
- [ ] 更新CLAUDE.md: 文档化新机制

**Phase 5-7**: 按标准workflow完成
