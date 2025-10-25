#!/bin/bash
# Branch Display Functions
# Part of branch_common.sh modularization
# Version: 1.0.0

# Color Definitions
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'  # No Color

# ═══════════════════════════════════════════════════════════════
# Display Functions
# ═══════════════════════════════════════════════════════════════

# Show branch naming guidance
show_branch_naming_guide() {
    cat <<EOF >&2
${BOLD}📝 分支命名规范：${NC}
  ${GREEN}•${NC} feature/xxx    - 新功能开发
  ${GREEN}•${NC} bugfix/xxx     - Bug修复
  ${GREEN}•${NC} perf/xxx       - 性能优化
  ${GREEN}•${NC} docs/xxx       - 文档更新
  ${GREEN}•${NC} experiment/xxx - 实验性改动
EOF
}

# Show Phase workflow overview
show_phase_workflow() {
    cat <<EOF >&2
${BOLD}🚀 Claude Enhancer 7-Phase工作流：${NC}
  ${CYAN}Phase 1:${NC} Discovery & Planning  ${YELLOW}← 分支准备${NC}
  ${CYAN}Phase 2:${NC} Implementation
  ${CYAN}Phase 3:${NC} Testing (质量门禁1)
  ${CYAN}Phase 4:${NC} Review (质量门禁2)
  ${CYAN}Phase 5:${NC} Release
  ${CYAN}Phase 6:${NC} Acceptance
  ${CYAN}Phase 7:${NC} Closure
EOF
}

# Show protected branch warning box
show_protected_branch_warning() {
    local current_branch="${1:-main}"
    local hook_name="${2:-branch_common}"

    cat <<EOF >&2

${BOLD}╔═══════════════════════════════════════════════════════════╗${NC}
${BOLD}║  ${RED}⚠️  PROTECTED BRANCH DETECTED${NC}${BOLD}                            ║${NC}
${BOLD}╚═══════════════════════════════════════════════════════════╝${NC}

${RED}${BOLD}📍 当前分支: $current_branch${NC}

${BOLD}🔴 规则0（Phase 1）强制要求：新任务 = 新分支${NC}

${BOLD}❌ 禁止操作：${NC}
  • 禁止在 main/master/production 分支上执行 Write/Edit 操作

${BOLD}✅ 解决方案：${NC}
  ${GREEN}git checkout -b feature/任务描述${NC}

EOF
    show_branch_naming_guide
    echo "" >&2
    show_phase_workflow
    echo "" >&2
    echo "${BOLD}💡 这是100%强制规则，不是建议！${NC}" >&2
    echo "${BOLD}═══════════════════════════════════════════════════════════${NC}" >&2
    echo "" >&2
}

# Show protected branch error box (for hard blocking)
show_protected_branch_error() {
    local current_branch="${1:-main}"

    cat <<EOF >&2

${BOLD}🚨 Claude Enhancer - 分支检查失败${NC}
${BOLD}═══════════════════════════════════════════════════════════${NC}

${RED}${BOLD}❌ 错误：禁止在 $current_branch 分支上修改文件${NC}

${BOLD}📋 规则0：新任务 = 新分支（100%强制执行）${NC}

${BOLD}🔧 解决方案：${NC}
  ${BOLD}1. AI必须先创建feature分支：${NC}
     ${GREEN}git checkout -b feature/任务描述${NC}

  ${BOLD}2. 或启用自动创建（推荐）：${NC}
     ${GREEN}export CE_AUTO_CREATE_BRANCH=true${NC}

EOF
    show_branch_naming_guide
    echo "" >&2
    echo "${BOLD}💡 这是100%强制规则，不是建议！${NC}" >&2
    echo "${BOLD}═══════════════════════════════════════════════════════════${NC}" >&2
    echo "" >&2
}