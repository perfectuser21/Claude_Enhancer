#!/bin/bash
# Workflow Guardian - 强制执行7-Phase workflow
# 用途: 检测并阻止跳过workflow的行为
# 调用: pre-commit hook中调用此脚本

set -euo pipefail

# 颜色
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

# 检测CE_HOME
if [[ -z "${CE_HOME:-}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  CE_HOME="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

cd "$CE_HOME"

# ============================================================================
# Module 1: 检测分支类型
# ============================================================================
detect_branch_type() {
  local branch
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

  # 编码任务分支
  if [[ "$branch" =~ ^(feature|bugfix|fix|perf|refactor|style|chore)/ ]]; then
    echo "coding"
    return 0
  fi

  # 文档分支（仅文档更新，可能不需要完整workflow）
  if [[ "$branch" =~ ^docs/ ]]; then
    echo "docs"
    return 0
  fi

  # 主分支（不应该直接commit）
  if [[ "$branch" =~ ^(main|master|production)$ ]]; then
    echo "protected"
    return 0
  fi

  echo "unknown"
}

# ============================================================================
# Module 2: 检测代码改动
# ============================================================================
has_code_changes() {
  # 检查staged files
  local code_files
  code_files=$(git diff --cached --name-only | grep -E '\.(sh|bash|py|js|ts|jsx|tsx|yml|yaml|json|go|rs|c|cpp|java)$' || true)

  if [[ -n "$code_files" ]]; then
    echo "true"
    echo "  代码文件改动:" >&2
    while IFS= read -r file; do
      echo "    - $file" >&2
    done <<< "$code_files"
    return 0
  fi

  echo "false"
}

# ============================================================================
# Module 3: 检查Phase 1文档（分支特定）
# Phase 1 包括5个子步骤：
#   1.1 Branch Check
#   1.2 Requirements Discussion
#   1.3 Technical Discovery (P1_DISCOVERY.md)
#   1.4 Impact Assessment (IMPACT_ASSESSMENT.md) ← 新增检查
#   1.5 Architecture Planning (PLAN.md)
# ============================================================================
check_phase1_docs() {
  local p1_count checklist_count plan_count impact_count
  local branch branch_base branch_keywords

  # 获取当前分支名并转换为文件名安全的slug
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  # 提取分支名主体（去掉feature/bugfix/等前缀）
  branch_base=$(basename "$branch")
  # 提取关键词（取前2-3个单词，忽略分隔符）
  branch_keywords=$(echo "$branch_base" | sed 's/[-_]/ /g' | awk '{for(i=1;i<=3&&i<=NF;i++) printf "%s ", toupper($i)}')

  # 策略1: 检查分支特定文档（模糊匹配关键词）
  # 格式: 文件名包含分支关键词
  p1_count=0
  checklist_count=0
  plan_count=0
  impact_count=0

  # 对每个关键词尝试匹配
  for keyword in $branch_keywords; do
    if [[ ${#keyword} -ge 4 ]]; then  # 至少4个字符的关键词才匹配
      local p1_tmp checklist_tmp plan_tmp impact_tmp
      p1_tmp=$(find docs/ -maxdepth 1 -iname "P1_*${keyword}*.md" -type f 2>/dev/null | wc -l)
      checklist_tmp=$(find docs/ -maxdepth 1 -iname "*CHECKLIST*${keyword}*.md" -type f 2>/dev/null | wc -l)
      plan_tmp=$(find docs/ -maxdepth 1 -iname "PLAN*${keyword}*.md" -type f 2>/dev/null | wc -l)
      impact_tmp=$(find docs/ -maxdepth 1 -iname "*IMPACT*${keyword}*.md" -type f 2>/dev/null | wc -l)

      # 取最大值（可能多个关键词都匹配）
      [[ $p1_tmp -gt $p1_count ]] && p1_count=$p1_tmp
      [[ $checklist_tmp -gt $checklist_count ]] && checklist_count=$checklist_tmp
      [[ $plan_tmp -gt $plan_count ]] && plan_count=$plan_tmp
      [[ $impact_tmp -gt $impact_count ]] && impact_count=$impact_tmp
    fi
  done

  # 如果找到所有4个必需文档，返回成功
  if [[ $p1_count -gt 0 && $checklist_count -gt 0 && $plan_count -gt 0 && $impact_count -gt 0 ]]; then
    echo "$p1_count|$checklist_count|$plan_count|$impact_count|branch-specific"
    return 0
  fi

  # 策略2: 没有找到分支特定文档，返回失败
  # 原因: 避免误判（其他分支的Phase 1文档不应该被当前分支使用）
  echo "0|0|0|0|none"
  return 1
}

# ============================================================================
# Module 4: 检查Bypass - REMOVED FOR SECURITY
# ============================================================================
# SECURITY: Bypass mechanism completely removed
# AI must follow workflow strictly, no exceptions
# Only user can override by modifying git hooks directly
check_bypass() {
  # Always return "no-bypass"
  # Bypass functionality removed to enforce 100% workflow compliance
  echo "no-bypass"
}

# ============================================================================
# Module 5: 主逻辑
# ============================================================================
enforce_workflow() {
  local branch_type code_changes docs_status

  echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║  Workflow Guardian - 7-Phase Enforcement                 ║${NC}"
  echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # 1. 检测分支类型
  branch_type=$(detect_branch_type)
  echo -e "${CYAN}[1/4]${NC} 分支类型: $branch_type"

  # 如果是受保护分支，不应该在这里（应该被pre-push阻止）
  if [[ "$branch_type" == "protected" ]]; then
    echo -e "${RED}❌ 错误：不能直接在 main/master 分支commit${NC}"
    echo -e "${YELLOW}   请创建feature分支${NC}"
    return 1
  fi

  # 2. 检测代码改动
  echo -e "${CYAN}[2/4]${NC} 检测代码改动..."
  code_changes=$(has_code_changes)

  # 3. 检查bypass (always no-bypass now)
  echo -e "${CYAN}[3/4]${NC} 检查Bypass状态..."
  # Bypass functionality removed - check_bypass() always returns "no-bypass"
  check_bypass >/dev/null

  # 4. 检查Phase 1文档
  echo -e "${CYAN}[4/4]${NC} 检查Phase 1文档..."
  docs_status=$(check_phase1_docs) || true

  IFS='|' read -r p1_count checklist_count plan_count impact_count detection_method <<< "$docs_status"

  echo "  - P1_DISCOVERY.md: $p1_count 个"
  echo "  - CHECKLIST.md: $checklist_count 个"
  echo "  - PLAN.md: $plan_count 个"
  echo "  - IMPACT_ASSESSMENT.md: $impact_count 个"
  if [[ -n "$detection_method" ]]; then
    echo "  - 检测方式: $detection_method"
  fi
  echo ""

  # ===== 决策逻辑 =====

  # SECURITY: Bypass mechanism removed
  # No more "情况1: 有bypass" - always enforce workflow

  # 规则0：所有改动必须走完整 7-Phase 工作流（无例外）
  # 删除了原来的docs分支豁免逻辑

  # 情况1: 无文件改动 - 允许（空commit）
  if [[ -z "$(git diff --cached --name-only)" ]]; then
    echo -e "${GREEN}✓${NC} 无文件改动，跳过workflow检查"
    return 0
  fi

  # 情况2: 有文件改动 - 必须有Phase 1文档（无例外）
  if [[ $p1_count -eq 0 || $checklist_count -eq 0 || $plan_count -eq 0 || $impact_count -eq 0 ]]; then
      echo -e "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
      echo -e "${RED}║  ❌ Phase 1 文档缺失 - Commit 被阻止                       ║${NC}"
      echo -e "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"
      echo ""
      echo -e "${RED}错误：有文件改动但缺少Phase 1文档${NC}"
      echo ""
      echo -e "${YELLOW}规则0：所有改动必须走完整 7-Phase 工作流（无例外）${NC}"
      echo ""
      echo -e "Phase 1 包含以下4个必需文档:"
      echo ""
      echo "  必需文档："
      [[ $p1_count -eq 0 ]] && echo -e "    ${RED}✗${NC} docs/P1_DISCOVERY.md (Phase 1.3 - 缺失)"
      [[ $p1_count -gt 0 ]] && echo -e "    ${GREEN}✓${NC} docs/P1_DISCOVERY.md (Phase 1.3)"

      [[ $checklist_count -eq 0 ]] && echo -e "    ${RED}✗${NC} .workflow/ACCEPTANCE_CHECKLIST.md (缺失)"
      [[ $checklist_count -gt 0 ]] && echo -e "    ${GREEN}✓${NC} .workflow/ACCEPTANCE_CHECKLIST.md"

      [[ $impact_count -eq 0 ]] && echo -e "    ${RED}✗${NC} .workflow/IMPACT_ASSESSMENT.md (Phase 1.4 - 缺失)"
      [[ $impact_count -gt 0 ]] && echo -e "    ${GREEN}✓${NC} .workflow/IMPACT_ASSESSMENT.md (Phase 1.4)"

      [[ $plan_count -eq 0 ]] && echo -e "    ${RED}✗${NC} docs/PLAN.md (Phase 1.5 - 缺失)"
      [[ $plan_count -gt 0 ]] && echo -e "    ${GREEN}✓${NC} docs/PLAN.md (Phase 1.5)"

      echo ""
      echo -e "${CYAN}修复方法:${NC}"
      echo ""
      echo "  1. 创建Phase 1文档:"
      echo "     touch docs/P1_DISCOVERY.md"
      echo "     touch .workflow/ACCEPTANCE_CHECKLIST.md"
      echo "     touch .workflow/IMPACT_ASSESSMENT.md"
      echo "     touch docs/PLAN.md"
      echo ""
      echo "  2. 填写文档内容"
      echo ""
      echo "  3. 重新commit:"
      echo "     git add docs/ .workflow/"
      echo "     git commit"
      echo ""
      echo -e "${RED}注意：所有改动必须走完整 7-Phase 工作流，无例外${NC}"
      echo ""

      return 1
  fi

  # 情况3: Phase 1文档齐全 - 允许
  echo -e "${GREEN}✓${NC} Phase 1文档齐全，允许commit"
  return 0
}

# ============================================================================
# 执行
# ============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  enforce_workflow
  exit $?
fi
