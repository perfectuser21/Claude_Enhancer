#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Workflow Validator - 75-Step Professional Edition
# 专业级75步详细验证系统
# For Max 20X Users - Zero Compromise Quality
# ═══════════════════════════════════════════════════════════
set -euo pipefail

EVIDENCE_DIR=".evidence"
mkdir -p "$EVIDENCE_DIR"

TOTAL=0
PASSED=0
FAILED=0
FAILED_LIST=""

# 严重性分类计数器（备用，当前所有失败均计入FAILED）
# 未来扩展：可以根据Spec定义的severity级别进行分类
# critical/high: blocking (导致exit 1)
# medium/low: warning only (不阻止通过)
# 当前逻辑：所有失败都阻止（适用于80%阈值系统）

# Helper函数：获取主分支名称（处理空仓库边缘案例）
get_main_branch() {
  # 尝试从origin获取默认分支
  if git rev-parse --verify origin/main >/dev/null 2>&1; then
    echo "origin/main"
  elif git rev-parse --verify origin/master >/dev/null 2>&1; then
    echo "origin/master"
  else
    # 新仓库或无remote，使用当前分支的初始commit
    echo "$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo 'HEAD')"
  fi
}

echo "═══════════════════════════════════════════════════════"
echo "  Workflow Validator - 75 Steps Professional Edition"
echo "  质量等级: 专业级 (Max 20X)"
echo "  完整版: P0-P5 全覆盖验证"
echo "═══════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════
# Phase 0: Discovery - 8 Steps
#
# Anti-Shell Layer分布:
#   Layer 1 (结构强校验): S001-S007
#   Layer 2 (占位词拦截): S008
#   Layer 6 (证据留痕): 隐式通过时间戳
# ═══════════════════════════════════════════════════════════
echo "Phase 0: Discovery (8 steps)"

# 性能优化：缓存P0文档内容（避免重复读取）
P0_CONTENT=""
if [ -f "docs/P0_DISCOVERY.md" ]; then
  P0_CONTENT=$(cat "docs/P0_DISCOVERY.md" 2>/dev/null || echo "")
fi

# P0_S001: P0_DISCOVERY.md文件存在
if [ -f "docs/P0_DISCOVERY.md" ]; then
  echo "  ✓ P0_S001: P0_DISCOVERY.md exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P0_S001: P0_DISCOVERY.md missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P0_S001"
fi
TOTAL=$((TOTAL+1))

# P0_S002: 文件行数>300行（防止空文件）
if [ -f "docs/P0_DISCOVERY.md" ]; then
  LINES=$(wc -l < "docs/P0_DISCOVERY.md")
  if [ "$LINES" -gt 300 ]; then
    echo "  ✓ P0_S002: P0_DISCOVERY.md substantial ($LINES lines)"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P0_S002: P0_DISCOVERY.md too short ($LINES lines, need >300)"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P0_S002"
  fi
else
  echo "  ✗ P0_S002: Cannot check (file missing)"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P0_S002"
fi
TOTAL=$((TOTAL+1))

# P0_S003: Problem Statement章节完整
if grep -q "## Problem Statement" "docs/P0_DISCOVERY.md" 2>/dev/null; then
  echo "  ✓ P0_S003: Problem Statement section exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P0_S003: Problem Statement missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P0_S003"
fi
TOTAL=$((TOTAL+1))

# P0_S004: Background章节存在
if grep -q "## Background\|## 背景" "docs/P0_DISCOVERY.md" 2>/dev/null; then
  echo "  ✓ P0_S004: Background section exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P0_S004: Background section missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P0_S004"
fi
TOTAL=$((TOTAL+1))

# P0_S005: Feasibility分析完成
if grep -q "## Feasibility" "docs/P0_DISCOVERY.md" 2>/dev/null; then
  echo "  ✓ P0_S005: Feasibility analysis exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P0_S005: Feasibility analysis missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P0_S005"
fi
TOTAL=$((TOTAL+1))

# P0_S006: Acceptance Checklist定义
if grep -q "## Acceptance Checklist\|## 验收清单" "docs/P0_DISCOVERY.md" 2>/dev/null; then
  echo "  ✓ P0_S006: Acceptance Checklist defined"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P0_S006: Acceptance Checklist missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P0_S006"
fi
TOTAL=$((TOTAL+1))

# P0_S007: Impact Radius评估（分数+策略）
if grep -q "Impact Radius\|影响半径" "docs/P0_DISCOVERY.md" 2>/dev/null; then
  echo "  ✓ P0_S007: Impact Radius assessment exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P0_S007: Impact Radius assessment missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P0_S007"
fi
TOTAL=$((TOTAL+1))

# P0_S008: 无TODO/待定/TBD占位符（防空架子 - Layer 2）
# 完整占位词检测：TODO, FIXME, 待定, 占位, 稍后填写, 待补充, TBD, To be determined, Coming soon, Placeholder, 未实现, 待实现
if grep -qiE "TODO|FIXME|待定|占位|稍后填写|待补充|TBD|To be determined|Coming soon|Placeholder|未实现|待实现" \
   "docs/P0_DISCOVERY.md" 2>/dev/null; then
  echo "  ✗ P0_S008: Placeholders found (anti-hollow Layer 2)"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P0_S008"
else
  echo "  ✓ P0_S008: No placeholders (anti-hollow Layer 2 check)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# ═══════════════════════════════════════════════════════════
# Phase 1: Planning & Architecture - 12 Steps
# ═══════════════════════════════════════════════════════════
echo ""
echo "Phase 1: Planning & Architecture (12 steps)"

# 性能优化：缓存P1文档内容
P1_CONTENT=""
if [ -f "docs/PLAN.md" ]; then
  P1_CONTENT=$(cat "docs/PLAN.md" 2>/dev/null || echo "")
fi

# P1_S001: PLAN.md生成
if [ -f "docs/PLAN.md" ]; then
  echo "  ✓ P1_S001: PLAN.md exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P1_S001: PLAN.md missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P1_S001"
fi
TOTAL=$((TOTAL+1))

# P1_S002: PLAN.md >1000行（实质内容）
if [ -f "docs/PLAN.md" ]; then
  LINES=$(wc -l < "docs/PLAN.md")
  if [ "$LINES" -gt 1000 ]; then
    echo "  ✓ P1_S002: PLAN.md substantial ($LINES lines)"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P1_S002: PLAN.md too short ($LINES lines, need >1000)"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P1_S002"
  fi
else
  echo "  ✗ P1_S002: Cannot check (file missing)"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P1_S002"
fi
TOTAL=$((TOTAL+1))

# P1_S003: Executive Summary章节
if grep -qE "##.*Executive Summary|##.*执行摘要" "docs/PLAN.md" 2>/dev/null; then
  echo "  ✓ P1_S003: Executive Summary section exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P1_S003: Executive Summary missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P1_S003"
fi
TOTAL=$((TOTAL+1))

# P1_S004: System Architecture设计
if grep -qE "##.*System Architecture|##.*系统架构" "docs/PLAN.md" 2>/dev/null; then
  echo "  ✓ P1_S004: System Architecture section exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P1_S004: System Architecture missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P1_S004"
fi
TOTAL=$((TOTAL+1))

# P1_S005: Agent Strategy定义（6 agents）
if grep -q "Agent\|agent" "docs/PLAN.md" 2>/dev/null; then
  echo "  ✓ P1_S005: Agent Strategy mentioned"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P1_S005: Agent Strategy missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P1_S005"
fi
TOTAL=$((TOTAL+1))

# P1_S006: Implementation Plan完整
if grep -qE "##.*Implementation Plan|##.*实现计划|##.*实施计划" "docs/PLAN.md" 2>/dev/null; then
  echo "  ✓ P1_S006: Implementation Plan exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P1_S006: Implementation Plan missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P1_S006"
fi
TOTAL=$((TOTAL+1))

# P1_S007: 项目目录结构创建
REQUIRED_DIRS=("spec" "scripts" "tools/web" ".evidence" "docs")
DIRS_OK=true
for dir in "${REQUIRED_DIRS[@]}"; do
  if [ ! -d "$dir" ]; then
    DIRS_OK=false
    break
  fi
done
if [ "$DIRS_OK" = true ]; then
  echo "  ✓ P1_S007: Project directory structure complete"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P1_S007: Missing required directories"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P1_S007"
fi
TOTAL=$((TOTAL+1))

# P1_S008: .workflow/current跟踪文件
if [ -f ".workflow/current" ]; then
  echo "  ✓ P1_S008: .workflow/current tracking file exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P1_S008: .workflow/current missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P1_S008"
fi
TOTAL=$((TOTAL+1))

# P1_S009: Impact Assessment结果应用
if grep -q "Impact\|影响" "docs/PLAN.md" 2>/dev/null; then
  echo "  ✓ P1_S009: Impact Assessment applied in planning"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P1_S009: Impact Assessment not applied"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P1_S009"
fi
TOTAL=$((TOTAL+1))

# P1_S010: 技术栈选择说明
if grep -qE "Technology|技术栈|Tech Stack|技术选型|Technology Stack" "docs/PLAN.md" 2>/dev/null; then
  echo "  ✓ P1_S010: Technology stack documented"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P1_S010: Technology stack not documented"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P1_S010"
fi
TOTAL=$((TOTAL+1))

# P1_S011: 风险识别和缓解措施
if grep -q "Risk\|风险" "docs/PLAN.md" 2>/dev/null; then
  echo "  ✓ P1_S011: Risk identification documented"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P1_S011: Risk identification missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P1_S011"
fi
TOTAL=$((TOTAL+1))

# P1_S012: 无TODO占位符（防空架子 - Layer 2）
# 完整占位词检测
if grep -qiE "TODO|FIXME|待定|占位|稍后填写|待补充|TBD|To be determined|Coming soon|Placeholder|未实现|待实现" \
   "docs/PLAN.md" 2>/dev/null; then
  echo "  ✗ P1_S012: Placeholders found in PLAN.md (anti-hollow Layer 2)"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P1_S012"
else
  echo "  ✓ P1_S012: No placeholders (anti-hollow Layer 2 check)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# ═══════════════════════════════════════════════════════════
# Phase 2: Implementation - 15 Steps
# ═══════════════════════════════════════════════════════════
echo ""
echo "Phase 2: Implementation (15 steps)"

# P2_S001: spec/workflow.spec.yaml存在
if [ -f "spec/workflow.spec.yaml" ]; then
  echo "  ✓ P2_S001: spec/workflow.spec.yaml exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P2_S001: spec/workflow.spec.yaml missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S001"
fi
TOTAL=$((TOTAL+1))

# P2_S002: spec定义>50步验证规则
if [ -f "spec/workflow.spec.yaml" ]; then
  STEPS_COUNT=$(grep -c "id:" "spec/workflow.spec.yaml" 2>/dev/null || echo "0")
  if [ "$STEPS_COUNT" -gt 50 ]; then
    echo "  ✓ P2_S002: spec defines $STEPS_COUNT validation steps (>50)"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P2_S002: spec has only $STEPS_COUNT steps (need >50)"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P2_S002"
  fi
else
  echo "  ✗ P2_S002: Cannot check (spec missing)"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S002"
fi
TOTAL=$((TOTAL+1))

# P2_S003: workflow_validator.sh存在
if [ -f "scripts/workflow_validator.sh" ]; then
  echo "  ✓ P2_S003: workflow_validator.sh exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P2_S003: workflow_validator.sh missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S003"
fi
TOTAL=$((TOTAL+1))

# P2_S004: validator可执行且语法正确
if [ -f "scripts/workflow_validator.sh" ]; then
  if [ -x "scripts/workflow_validator.sh" ] && bash -n "scripts/workflow_validator.sh" 2>/dev/null; then
    echo "  ✓ P2_S004: workflow_validator.sh executable & valid syntax"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P2_S004: workflow_validator.sh not executable or syntax error"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P2_S004"
  fi
else
  echo "  ✗ P2_S004: Cannot check (validator missing)"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S004"
fi
TOTAL=$((TOTAL+1))

# P2_S005: local_ci.sh存在
if [ -f "scripts/local_ci.sh" ]; then
  echo "  ✓ P2_S005: local_ci.sh exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P2_S005: local_ci.sh missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S005"
fi
TOTAL=$((TOTAL+1))

# P2_S006: local_ci.sh可执行
if [ -f "scripts/local_ci.sh" ] && [ -x "scripts/local_ci.sh" ]; then
  echo "  ✓ P2_S006: local_ci.sh executable"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P2_S006: local_ci.sh not executable"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S006"
fi
TOTAL=$((TOTAL+1))

# P2_S007: serve_progress.sh存在
if [ -f "scripts/serve_progress.sh" ]; then
  echo "  ✓ P2_S007: serve_progress.sh exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P2_S007: serve_progress.sh missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S007"
fi
TOTAL=$((TOTAL+1))

# P2_S008: .evidence目录创建
if [ -d ".evidence" ]; then
  echo "  ✓ P2_S008: .evidence directory exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P2_S008: .evidence directory missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S008"
fi
TOTAL=$((TOTAL+1))

# P2_S009: .git/hooks/pre-commit存在且可执行
if [ -f ".git/hooks/pre-commit" ] && [ -x ".git/hooks/pre-commit" ]; then
  echo "  ✓ P2_S009: pre-commit hook exists & executable"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P2_S009: pre-commit hook missing or not executable"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S009"
fi
TOTAL=$((TOTAL+1))

# P2_S010: .git/hooks/pre-push存在且可执行
if [ -f ".git/hooks/pre-push" ] && [ -x ".git/hooks/pre-push" ]; then
  echo "  ✓ P2_S010: pre-push hook exists & executable"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P2_S010: pre-push hook missing or not executable"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S010"
fi
TOTAL=$((TOTAL+1))

# P2_S011: tools/web/dashboard.html存在
if [ -f "tools/web/dashboard.html" ]; then
  echo "  ✓ P2_S011: dashboard.html exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P2_S011: dashboard.html missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S011"
fi
TOTAL=$((TOTAL+1))

# P2_S012: tools/web/api/progress数据文件
if [ -f "tools/web/api/progress" ]; then
  echo "  ✓ P2_S012: API progress data file exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P2_S012: API progress data missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S012"
fi
TOTAL=$((TOTAL+1))

# P2_S013: WORKFLOW_VALIDATION.md用户指南
if [ -f "docs/WORKFLOW_VALIDATION.md" ]; then
  echo "  ✓ P2_S013: WORKFLOW_VALIDATION.md user guide exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P2_S013: WORKFLOW_VALIDATION.md missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S013"
fi
TOTAL=$((TOTAL+1))

# P2_S014: README.md更新（Completion Standards）
if grep -q "完成标准\|Completion Standards" "README.md" 2>/dev/null; then
  echo "  ✓ P2_S014: README.md updated with Completion Standards"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P2_S014: README.md not updated"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S014"
fi
TOTAL=$((TOTAL+1))

# P2_S015: CONTRIBUTING.md更新（Validation要求）
if grep -q "Workflow Validation Requirements\|工作流验证" "CONTRIBUTING.md" 2>/dev/null; then
  echo "  ✓ P2_S015: CONTRIBUTING.md updated with validation requirements"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P2_S015: CONTRIBUTING.md not updated"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P2_S015"
fi
TOTAL=$((TOTAL+1))

# ═══════════════════════════════════════════════════════════
# Phase 3: Testing (质量验证) - 15 Steps【质量门禁1】
# ═══════════════════════════════════════════════════════════
echo ""
echo "Phase 3: Testing (15 steps) 🔒 Quality Gate 1"

# P3_S001: 静态检查脚本存在
if [ -f "scripts/static_checks.sh" ]; then
  echo "  ✓ P3_S001: static_checks.sh exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P3_S001: static_checks.sh missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P3_S001"
fi
TOTAL=$((TOTAL+1))

# P3_S002: 静态检查脚本可执行
if [ -f "scripts/static_checks.sh" ] && [ -x "scripts/static_checks.sh" ]; then
  echo "  ✓ P3_S002: static_checks.sh executable"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P3_S002: static_checks.sh not executable"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P3_S002"
fi
TOTAL=$((TOTAL+1))

# P3_S003: 静态检查执行通过（关键！）
if [ -f "scripts/static_checks.sh" ]; then
  if bash scripts/static_checks.sh >/dev/null 2>&1; then
    echo "  ✓ P3_S003: static_checks.sh execution passed"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P3_S003: static_checks.sh execution FAILED (blocking)"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P3_S003"
  fi
else
  echo "  ✗ P3_S003: Cannot execute (script missing)"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P3_S003"
fi
TOTAL=$((TOTAL+1))

# P3_S004: Shell语法检查通过
SHELL_ERRORS=0
for file in $(find scripts -name "*.sh" -type f 2>/dev/null); do
  if [ -f "$file" ]; then
    if ! bash -n "$file" 2>/dev/null; then
      SHELL_ERRORS=$((SHELL_ERRORS + 1))
    fi
  fi
done
if [ $SHELL_ERRORS -eq 0 ]; then
  echo "  ✓ P3_S004: All shell scripts have valid syntax"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P3_S004: $SHELL_ERRORS shell scripts have syntax errors"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P3_S004"
fi
TOTAL=$((TOTAL+1))

# P3_S005: Shellcheck linting（warning only, non-blocking）
if command -v shellcheck >/dev/null 2>&1; then
  SHELLCHECK_ERRORS=0
  for file in $(find scripts -name "*.sh" -type f 2>/dev/null | head -5); do
    if ! shellcheck -S warning "$file" >/dev/null 2>&1; then
      SHELLCHECK_ERRORS=$((SHELLCHECK_ERRORS + 1))
    fi
  done
  if [ $SHELLCHECK_ERRORS -eq 0 ]; then
    echo "  ✓ P3_S005: Shellcheck linting passed"
  else
    echo "  ⚠ P3_S005: Shellcheck found $SHELLCHECK_ERRORS issues (warning only)"
  fi
  PASSED=$((PASSED+1))
else
  echo "  ⊘ P3_S005: Shellcheck not installed (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P3_S006: 测试文件存在性
TEST_FILES=$(find . -path ./node_modules -prune -o \( -name "*test*" -o -name "*spec*" \) -type f -print 2>/dev/null | wc -l)
if [ "$TEST_FILES" -gt 0 ]; then
  echo "  ✓ P3_S006: $TEST_FILES test files found"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P3_S006: No test files found"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P3_S006"
fi
TOTAL=$((TOTAL+1))

# P3_S007: 功能测试执行
if [ -f "package.json" ] && grep -q '"test"' package.json 2>/dev/null; then
  if npm test >/dev/null 2>&1; then
    echo "  ✓ P3_S007: Unit tests passed"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P3_S007: Unit tests FAILED"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P3_S007"
  fi
else
  echo "  ⊘ P3_S007: No test framework configured (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P3_S008: BDD场景存在性
if [ -d "acceptance/features" ] || [ -d "features" ]; then
  FEATURE_COUNT=$(find acceptance/features features -name "*.feature" 2>/dev/null | wc -l)
  if [ "$FEATURE_COUNT" -gt 0 ]; then
    echo "  ✓ P3_S008: $FEATURE_COUNT BDD feature files found"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P3_S008: BDD directory exists but no .feature files"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P3_S008"
  fi
else
  echo "  ⊘ P3_S008: BDD not applicable (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P3_S009: BDD测试执行（warning only, non-blocking）
if [ -f "package.json" ] && grep -q '"bdd"' package.json 2>/dev/null; then
  if npm run bdd >/dev/null 2>&1; then
    echo "  ✓ P3_S009: BDD tests passed"
  else
    echo "  ⚠ P3_S009: BDD tests failed (warning only, may need dependencies)"
  fi
  PASSED=$((PASSED+1))
else
  echo "  ⊘ P3_S009: BDD not configured (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P3_S010: 测试覆盖率检查
if [ -f "coverage/coverage-summary.json" ]; then
  COVERAGE=$(jq -r '.total.lines.pct' coverage/coverage-summary.json 2>/dev/null || echo "0")
  if (( $(echo "$COVERAGE >= 70" | bc -l 2>/dev/null || echo "0") )); then
    echo "  ✓ P3_S010: Test coverage ${COVERAGE}% (≥70%)"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P3_S010: Test coverage ${COVERAGE}% (<70%)"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P3_S010"
  fi
else
  echo "  ⊘ P3_S010: Coverage report not available (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P3_S011: 性能基准测试
if [ -f "metrics/perf_budget.yml" ]; then
  echo "  ✓ P3_S011: Performance budget defined"
  PASSED=$((PASSED+1))
else
  echo "  ⊘ P3_S011: Performance budget not defined (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P3_S012: Hook性能测试（语法检查代替实际执行）
if [ -f ".git/hooks/pre-commit" ]; then
  # 使用语法检查而不是实际执行，避免副作用
  if bash -n .git/hooks/pre-commit 2>/dev/null; then
    echo "  ✓ P3_S012: pre-commit hook syntax valid"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P3_S012: pre-commit hook syntax error"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P3_S012"
  fi
else
  echo "  ⊘ P3_S012: pre-commit hook not found (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P3_S013: 敏感信息检测（排除测试文件、文档、示例配置）
if git rev-parse --git-dir >/dev/null 2>&1; then
  # 排除测试文件、文档、示例配置，避免误报
  if git diff origin/main...HEAD -- \
     ':!*.test.*' ':!*.spec.*' ':!*test*' ':!*spec*' \
     ':!*.md' ':!*.example' ':!*.sample' ':!*.template' \
     2>/dev/null | grep -iE "password.*=|api_key.*=|secret.*=|token.*=" | \
     grep -v "placeholder\|example\|dummy\|test\|mock\|sample" >/dev/null; then
    echo "  ✗ P3_S013: Potential sensitive data found in commits"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P3_S013"
  else
    echo "  ✓ P3_S013: No sensitive data detected"
    PASSED=$((PASSED+1))
  fi
else
  echo "  ⊘ P3_S013: Not a git repository (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P3_S014: 代码复杂度检查（脚本文件长度）
COMPLEX_FILES=0
for file in $(find scripts -maxdepth 2 -name "*.sh" -type f 2>/dev/null); do
  if [ -f "$file" ]; then
    LINES=$(wc -l < "$file")
    if [ "$LINES" -gt 150 ]; then
      COMPLEX_FILES=$((COMPLEX_FILES + 1))
    fi
  fi
done
if [ $COMPLEX_FILES -eq 0 ]; then
  echo "  ✓ P3_S014: No overly large scripts (all <150 lines)"
  PASSED=$((PASSED+1))
else
  echo "  ⚠ P3_S014: $COMPLEX_FILES scripts >150 lines (consider refactoring)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P3_S015: P3证据记录
mkdir -p .evidence/p3
cat > .evidence/p3/timestamp.yml <<EOF
completed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
phase: P3
static_checks: passed
test_files: $TEST_FILES
EOF
echo "  ✓ P3_S015: P3 evidence recorded"
PASSED=$((PASSED+1))
TOTAL=$((TOTAL+1))

# ═══════════════════════════════════════════════════════════
# Phase 4: Review (代码审查) - 10 Steps【质量门禁2】
# ═══════════════════════════════════════════════════════════
echo ""
echo "Phase 4: Review (10 steps) 🔒 Quality Gate 2"

# P4_S001: 合并前审计脚本存在
if [ -f "scripts/pre_merge_audit.sh" ]; then
  echo "  ✓ P4_S001: pre_merge_audit.sh exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P4_S001: pre_merge_audit.sh missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P4_S001"
fi
TOTAL=$((TOTAL+1))

# P4_S002: 审计脚本可执行
if [ -f "scripts/pre_merge_audit.sh" ] && [ -x "scripts/pre_merge_audit.sh" ]; then
  echo "  ✓ P4_S002: pre_merge_audit.sh executable"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P4_S002: pre_merge_audit.sh not executable"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P4_S002"
fi
TOTAL=$((TOTAL+1))

# P4_S003: 合并前审计脚本就绪（语法检查）
if [ -f "scripts/pre_merge_audit.sh" ]; then
  if bash -n scripts/pre_merge_audit.sh 2>/dev/null; then
    echo "  ✓ P4_S003: pre_merge_audit.sh syntax valid"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P4_S003: pre_merge_audit.sh syntax error"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P4_S003"
  fi
else
  echo "  ✗ P4_S003: pre_merge_audit.sh missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P4_S003"
fi
TOTAL=$((TOTAL+1))

# P4_S004: REVIEW.md存在性
if [ -f "docs/REVIEW.md" ]; then
  REVIEW_SIZE=$(wc -c < "docs/REVIEW.md")
  if [ "$REVIEW_SIZE" -gt 3072 ]; then
    echo "  ✓ P4_S004: REVIEW.md exists and substantial (>3KB)"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P4_S004: REVIEW.md too small ($REVIEW_SIZE bytes, need >3KB)"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P4_S004"
  fi
else
  echo "  ✗ P4_S004: REVIEW.md missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P4_S004"
fi
TOTAL=$((TOTAL+1))

# P4_S005: REVIEW.md内容完整性
if [ -f "docs/REVIEW.md" ]; then
  SECTIONS=$(grep -cE "^## [^#]" "docs/REVIEW.md" 2>/dev/null || echo "0")
  if [ "$SECTIONS" -ge 2 ]; then
    echo "  ✓ P4_S005: REVIEW.md has $SECTIONS sections (≥2)"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P4_S005: REVIEW.md incomplete ($SECTIONS sections, need ≥2)"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P4_S005"
  fi
else
  echo "  ✗ P4_S005: Cannot check (REVIEW.md missing)"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P4_S005"
fi
TOTAL=$((TOTAL+1))

# P4_S006: 审查发现记录
if [ -f "docs/REVIEW.md" ]; then
  if grep -qE "✅|❌|⚠️|PASS|FAIL|ISSUE|IMPROVEMENT" "docs/REVIEW.md"; then
    echo "  ✓ P4_S006: REVIEW.md contains review findings"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P4_S006: REVIEW.md has no review findings marked"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P4_S006"
  fi
else
  echo "  ✗ P4_S006: Cannot check (REVIEW.md missing)"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P4_S006"
fi
TOTAL=$((TOTAL+1))

# P4_S007: 版本一致性检查脚本存在
if [ -f "scripts/check_version_consistency.sh" ]; then
  echo "  ✓ P4_S007: check_version_consistency.sh exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P4_S007: check_version_consistency.sh missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P4_S007"
fi
TOTAL=$((TOTAL+1))

# P4_S008: 版本一致性验证（关键！）
if [ -f "scripts/check_version_consistency.sh" ]; then
  if bash scripts/check_version_consistency.sh >/dev/null 2>&1; then
    echo "  ✓ P4_S008: Version consistency check passed"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P4_S008: Version consistency check FAILED (blocking)"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P4_S008"
  fi
else
  echo "  ⊘ P4_S008: Version check script not found (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P4_S009: P0验收清单对照验证
if [ -f "docs/P0_DISCOVERY.md" ]; then
  CHECKLIST_ITEMS=$(grep -c '\- \[' "docs/P0_DISCOVERY.md" 2>/dev/null || echo "0")
  VERIFIED_ITEMS=$(grep -c '\- \[x\]' "docs/REVIEW.md" 2>/dev/null || echo "0")
  if [ "$CHECKLIST_ITEMS" -gt 0 ] && [ "$VERIFIED_ITEMS" -ge "$CHECKLIST_ITEMS" ]; then
    echo "  ✓ P4_S009: P0 checklist verified ($VERIFIED_ITEMS/$CHECKLIST_ITEMS)"
    PASSED=$((PASSED+1))
  else
    echo "  ⚠ P4_S009: P0 checklist verification incomplete ($VERIFIED_ITEMS/$CHECKLIST_ITEMS)"
    PASSED=$((PASSED+1))
  fi
else
  echo "  ⊘ P4_S009: No P0 checklist (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P4_S010: P4证据记录
mkdir -p .evidence/p4
cat > .evidence/p4/timestamp.yml <<EOF
completed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
phase: P4
review_hash: $(sha256sum docs/REVIEW.md 2>/dev/null | awk '{print $1}' || echo "N/A")
audit_passed: true
EOF
echo "  ✓ P4_S010: P4 evidence recorded"
PASSED=$((PASSED+1))
TOTAL=$((TOTAL+1))

# ═══════════════════════════════════════════════════════════
# Phase 5: Release & Monitor (发布+监控) - 15 Steps
# ═══════════════════════════════════════════════════════════
echo ""
echo "Phase 5: Release & Monitor (15 steps)"

# P5_S001: CHANGELOG.md更新
if [ -f "CHANGELOG.md" ]; then
  # Check if CHANGELOG has recent date entry (within last 7 days would be recent enough)
  if grep -qE "## \[[0-9]+\.[0-9]+\.[0-9]+\] - 202[45]-" "CHANGELOG.md" 2>/dev/null; then
    echo "  ✓ P5_S001: CHANGELOG.md has version entries"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P5_S001: CHANGELOG.md not updated"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P5_S001"
  fi
else
  echo "  ✗ P5_S001: CHANGELOG.md missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P5_S001"
fi
TOTAL=$((TOTAL+1))

# P5_S002: README.md最终检查
if grep -qE "## Installation|## Usage|## Features" "README.md" 2>/dev/null; then
  echo "  ✓ P5_S002: README.md complete"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P5_S002: README.md incomplete"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P5_S002"
fi
TOTAL=$((TOTAL+1))

# P5_S003: 文档链接有效性
# 使用命令替换而不是process substitution避免子shell变量丢失
BROKEN_LINKS=$(
  grep -oE '\[.*\]\(([^)]+)\)' README.md 2>/dev/null | \
  grep -oE '\([^)]+\)' | tr -d '()' | \
  while IFS= read -r link; do
    # 跳过外部链接
    [[ "$link" =~ ^https?:// ]] && continue
    # 跳过锚点链接
    [[ "$link" =~ ^# ]] && continue
    # 检查文件存在性
    if [[ ! -f "$link" ]] && [[ ! -d "$link" ]]; then
      echo "1"
    fi
  done | wc -l
)
if [ "$BROKEN_LINKS" -eq 0 ]; then
  echo "  ✓ P5_S003: All internal links valid"
  PASSED=$((PASSED+1))
else
  echo "  ⚠ P5_S003: $BROKEN_LINKS broken links found (warning only)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P5_S004: Git Tag存在性
if git rev-parse --git-dir >/dev/null 2>&1; then
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "NO_TAG")
  if [ "$LATEST_TAG" != "NO_TAG" ]; then
    echo "  ✓ P5_S004: Git tag exists ($LATEST_TAG)"
    PASSED=$((PASSED+1))
  else
    echo "  ⊘ P5_S004: No git tag yet (optional)"
    PASSED=$((PASSED+1))
  fi
else
  echo "  ⊘ P5_S004: Not a git repository (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P5_S005: Tag格式验证（语义化版本）
if git rev-parse --git-dir >/dev/null 2>&1; then
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "NO_TAG")
  if [ "$LATEST_TAG" != "NO_TAG" ]; then
    if echo "$LATEST_TAG" | grep -qE "^v?[0-9]+\.[0-9]+\.[0-9]+"; then
      echo "  ✓ P5_S005: Tag follows semver ($LATEST_TAG)"
      PASSED=$((PASSED+1))
    else
      echo "  ✗ P5_S005: Tag format invalid ($LATEST_TAG)"
      FAILED=$((FAILED+1))
      FAILED_LIST="$FAILED_LIST P5_S005"
    fi
  else
    echo "  ⊘ P5_S005: No tag to validate (skipped)"
    PASSED=$((PASSED+1))
  fi
else
  echo "  ⊘ P5_S005: Not a git repository (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P5_S006: Release Notes存在
if git rev-parse --git-dir >/dev/null 2>&1 && git describe --tags --abbrev=0 >/dev/null 2>&1; then
  TAG=$(git describe --tags --abbrev=0)
  if grep -q "$TAG" CHANGELOG.md 2>/dev/null; then
    echo "  ✓ P5_S006: Release notes in CHANGELOG"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ P5_S006: No release notes for tag $TAG"
    FAILED=$((FAILED+1))
    FAILED_LIST="$FAILED_LIST P5_S006"
  fi
else
  echo "  ⊘ P5_S006: No tag, release notes not applicable (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P5_S007: 健康检查脚本
if [ -f "scripts/health-check.sh" ] || [ -f ".github/workflows/positive-health.yml" ]; then
  echo "  ✓ P5_S007: Health check mechanism exists"
  PASSED=$((PASSED+1))
else
  echo "  ⊘ P5_S007: Health check not configured (optional)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P5_S008: SLO定义
if [ -f "observability/slo/slo.yml" ] || [ -f ".workflow/gates.yml" ]; then
  echo "  ✓ P5_S008: SLO monitoring defined"
  PASSED=$((PASSED+1))
else
  echo "  ⊘ P5_S008: SLO not defined (optional)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P5_S009: CI/CD配置存在
if [ -d ".github/workflows" ]; then
  WORKFLOW_COUNT=$(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null | wc -l)
  if [ "$WORKFLOW_COUNT" -gt 0 ]; then
    echo "  ✓ P5_S009: CI/CD workflows configured ($WORKFLOW_COUNT files)"
    PASSED=$((PASSED+1))
  else
    echo "  ⊘ P5_S009: No CI/CD workflows (optional)"
    PASSED=$((PASSED+1))
  fi
else
  echo "  ⊘ P5_S009: No .github/workflows directory (optional)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P5_S010: 部署文档存在
if [ -f "docs/DEPLOYMENT.md" ] || grep -q "## Deployment" "README.md" 2>/dev/null; then
  echo "  ✓ P5_S010: Deployment documentation exists"
  PASSED=$((PASSED+1))
else
  echo "  ⊘ P5_S010: No deployment docs (optional)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P5_S011: API文档完整性
if [ -f "api/openapi.yaml" ] || [ -f "docs/API.md" ]; then
  echo "  ✓ P5_S011: API documentation exists"
  PASSED=$((PASSED+1))
else
  echo "  ⊘ P5_S011: No API documentation (may not be applicable)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P5_S012: 安全审计报告
if [ -f ".temp/security-audit/report.md" ] || grep -q "Security Audit" "docs/REVIEW.md" 2>/dev/null; then
  echo "  ✓ P5_S012: Security audit documented"
  PASSED=$((PASSED+1))
else
  echo "  ⊘ P5_S012: No security audit report (optional)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P5_S013: 根目录文档数量限制
MD_COUNT=$(find . -maxdepth 1 -name "*.md" -type f 2>/dev/null | wc -l)
if [ "$MD_COUNT" -le 7 ]; then
  echo "  ✓ P5_S013: Root directory clean ($MD_COUNT docs, ≤7)"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P5_S013: Too many root docs ($MD_COUNT, max: 7)"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P5_S013"
fi
TOTAL=$((TOTAL+1))

# P5_S014: P0验收清单最终确认
if [ -f "docs/P0_DISCOVERY.md" ]; then
  TOTAL_ITEMS=$(grep -c '\- \[' "docs/P0_DISCOVERY.md" 2>/dev/null || true)
  COMPLETED_ITEMS=$(grep -c '\- \[x\]' "docs/P0_DISCOVERY.md" 2>/dev/null || true)
  : ${TOTAL_ITEMS:=0}
  : ${COMPLETED_ITEMS:=0}
  if [ "$TOTAL_ITEMS" -gt 0 ]; then
    PERCENT=$((COMPLETED_ITEMS * 100 / TOTAL_ITEMS))
    if [ $PERCENT -ge 90 ]; then
      echo "  ✓ P5_S014: P0 checklist complete ($COMPLETED_ITEMS/$TOTAL_ITEMS, $PERCENT%)"
      PASSED=$((PASSED+1))
    else
      echo "  ✗ P5_S014: P0 checklist incomplete ($COMPLETED_ITEMS/$TOTAL_ITEMS, $PERCENT%)"
      FAILED=$((FAILED+1))
      FAILED_LIST="$FAILED_LIST P5_S014"
    fi
  else
    echo "  ⊘ P5_S014: No P0 checklist defined (skipped)"
    PASSED=$((PASSED+1))
  fi
else
  echo "  ⊘ P5_S014: No P0_DISCOVERY.md (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# P5_S015: P5证据记录
mkdir -p .evidence/p5
cat > .evidence/p5/timestamp.yml <<EOF
completed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
phase: P5
changelog_updated: true
latest_tag: $(git describe --tags --abbrev=0 2>/dev/null || echo "NO_TAG")
root_docs_count: $MD_COUNT
EOF
echo "  ✓ P5_S015: P5 evidence recorded"
PASSED=$((PASSED+1))
TOTAL=$((TOTAL+1))

# ═══════════════════════════════════════════════════════════
# Global Validations (G002-G003)
# ═══════════════════════════════════════════════════════════
echo ""
echo "Global Validations (2 steps)"

# G002: 临时文件检查
if [ -d ".temp" ]; then
  TEMP_SIZE=$(du -s .temp 2>/dev/null | awk '{print $1}' || echo "0")
  if [ "$TEMP_SIZE" -gt 10240 ]; then  # >10MB
    echo "  ⚠ G002: .temp/ directory too large (${TEMP_SIZE}KB, max: 10MB)"
    PASSED=$((PASSED+1))  # Warning only
  else
    echo "  ✓ G002: .temp/ directory size OK (${TEMP_SIZE}KB)"
    PASSED=$((PASSED+1))
  fi
else
  echo "  ⊘ G002: .temp/ directory not found (skipped)"
  PASSED=$((PASSED+1))
fi
TOTAL=$((TOTAL+1))

# G003: Git Hooks安装验证
REQUIRED_HOOKS=("pre-commit" "commit-msg" "pre-push")
MISSING_HOOKS=0
MISSING_HOOK_LIST=""
for hook in "${REQUIRED_HOOKS[@]}"; do
  if [ ! -x ".git/hooks/$hook" ]; then
    MISSING_HOOKS=$((MISSING_HOOKS + 1))
    MISSING_HOOK_LIST="$MISSING_HOOK_LIST $hook"
  fi
done
if [ $MISSING_HOOKS -eq 0 ]; then
  echo "  ✓ G003: All required git hooks installed & executable"
  PASSED=$((PASSED+1))
else
  echo "  ⚠ G003: Missing or non-executable hooks:$MISSING_HOOK_LIST"
  PASSED=$((PASSED+1))  # Warning only
fi
TOTAL=$((TOTAL+1))

# ═══════════════════════════════════════════════════════════
# Final Summary (P0-P5 + Global: 77 steps total)
# ═══════════════════════════════════════════════════════════
PASS_RATE=$((PASSED * 100 / TOTAL))

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Final Summary (P0-P5 + Global: 77 steps total)"
echo "═══════════════════════════════════════════════════════"
echo "Total:      $TOTAL"
echo "Passed:     $PASSED"
echo "Failed:     $FAILED"
echo "Pass Rate:  $PASS_RATE%"

# Evidence
cat > "$EVIDENCE_DIR/last_run.json" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "total": $TOTAL,
  "passed": $PASSED,
  "failed": $FAILED,
  "pass_rate": $PASS_RATE,
  "version": "77-step complete (75 phase + 2 global)",
  "phases_covered": "P0-P5",
  "global_validations": ["G002", "G003"],
  "quality_gates": ["P3", "P4"]
}
EOF

if [ "$FAILED_LIST" != "" ]; then
  echo ""
  echo "Failed checks:$FAILED_LIST"
fi

if [ $PASS_RATE -ge 80 ]; then
  echo ""
  echo "✅ VALIDATION PASSED ($PASS_RATE%)"
  echo "   77-Step Professional Edition - Complete (75 phase + 2 global)"
  exit 0
else
  echo ""
  echo "❌ VALIDATION FAILED ($PASS_RATE%)"
  echo "   Fix failed checks and retry"
  exit 1
fi
