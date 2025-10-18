#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# workflow_validator.sh - 工作流完成度验证器
# 用途：验证当前Phase的完成度，检测空壳文件和占位符
# 输出：通过率（0-100%）和详细报告
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKFLOW_CURRENT="$PROJECT_ROOT/.workflow/current"
EVIDENCE_DIR="$PROJECT_ROOT/.evidence"
SPEC_FILE="$PROJECT_ROOT/spec/workflow.spec.yaml"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# 统计变量
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
SKIPPED_CHECKS=0

# 结果数组
declare -a FAILED_ITEMS=()
declare -a CHECK_RESULTS=()

# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[✗]${NC} $*"
}

log_section() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}$*${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
}

# 记录检查结果
record_check() {
    local check_id="$1"
    local check_name="$2"
    local status="$3"  # pass/fail/skip
    local message="${4:-}"

    ((TOTAL_CHECKS++))

    case "$status" in
        pass)
            ((PASSED_CHECKS++))
            CHECK_RESULTS+=("✓ $check_id: $check_name")
            ;;
        fail)
            ((FAILED_CHECKS++))
            CHECK_RESULTS+=("✗ $check_id: $check_name")
            FAILED_ITEMS+=("$check_id: $check_name${message:+ - $message}")
            ;;
        skip)
            ((SKIPPED_CHECKS++))
            CHECK_RESULTS+=("⊘ $check_id: $check_name (skipped)")
            ;;
    esac
}

# 检查文件是否存在且非空
check_file_exists_and_not_empty() {
    local file="$1"
    [[ -f "$file" ]] && [[ -s "$file" ]]
}

# 检查文件内容行数
check_file_min_lines() {
    local file="$1"
    local min_lines="$2"

    if [[ ! -f "$file" ]]; then
        return 1
    fi

    local line_count
    line_count=$(wc -l < "$file" 2>/dev/null || echo "0")
    [[ $line_count -ge $min_lines ]]
}

# 检查占位符内容
check_no_placeholders() {
    local file="$1"

    if [[ ! -f "$file" ]]; then
        return 1
    fi

    # 检测常见占位符
    if grep -qE 'TODO:|FIXME:|待定|占位|TBD|To be determined|placeholder|XXX' "$file" 2>/dev/null; then
        return 1
    fi

    return 0
}

# 检查Markdown结构
check_markdown_structure() {
    local file="$1"
    shift
    local required_sections=("$@")

    if [[ ! -f "$file" ]]; then
        return 1
    fi

    for section in "${required_sections[@]}"; do
        if ! grep -q "^## $section" "$file" 2>/dev/null; then
            return 1
        fi
    done

    return 0
}

# ═══════════════════════════════════════════════════════════════
# 读取当前Phase信息
# ═══════════════════════════════════════════════════════════════

get_current_phase() {
    if [[ ! -f "$WORKFLOW_CURRENT" ]]; then
        echo "unknown"
        return
    fi

    # 提取phase字段
    local phase
    phase=$(grep '^phase:' "$WORKFLOW_CURRENT" | head -1 | awk '{print $2}' || echo "unknown")
    echo "$phase"
}

get_phase_status() {
    if [[ ! -f "$WORKFLOW_CURRENT" ]]; then
        echo "unknown"
        return
    fi

    # 提取status字段
    local status
    status=$(grep '^status:' "$WORKFLOW_CURRENT" | head -1 | awk '{print $2}' | tr -d '"' || echo "unknown")
    echo "$status"
}

# ═══════════════════════════════════════════════════════════════
# Phase 0 检查项（发现与探索）
# ═══════════════════════════════════════════════════════════════

validate_phase_0() {
    log_section "Phase 0: Discovery Validation"

    local p0_doc="$PROJECT_ROOT/docs/P0_DISCOVERY.md"

    # S001: P0文档存在
    if check_file_exists_and_not_empty "$p0_doc"; then
        log_success "S001: P0 Discovery document exists"
        record_check "S001" "P0 Discovery document exists" "pass"
    else
        log_error "S001: P0 Discovery document missing"
        record_check "S001" "P0 Discovery document exists" "fail"
    fi

    # S002: 问题陈述定义
    if grep -q "^## Problem Statement" "$p0_doc" 2>/dev/null; then
        log_success "S002: Problem Statement section exists"
        record_check "S002" "Problem Statement defined" "pass"
    else
        log_error "S002: Problem Statement section missing"
        record_check "S002" "Problem Statement defined" "fail"
    fi

    # S003: 可行性分析
    if grep -q "^## Feasibility" "$p0_doc" 2>/dev/null; then
        log_success "S003: Feasibility analysis exists"
        record_check "S003" "Feasibility analysis completed" "pass"
    else
        log_error "S003: Feasibility analysis missing"
        record_check "S003" "Feasibility analysis completed" "fail"
    fi

    # S004: 验收清单
    if grep -q "^## Acceptance Checklist" "$p0_doc" 2>/dev/null; then
        log_success "S004: Acceptance Checklist exists"
        record_check "S004" "Acceptance Checklist defined" "pass"

        # 检查是否有至少3个验收项
        local checklist_items
        checklist_items=$(grep -c '^\- \[ \]' "$p0_doc" 2>/dev/null || echo "0")
        if [[ $checklist_items -ge 3 ]]; then
            log_success "S005: Acceptance Checklist has $checklist_items items (≥3)"
            record_check "S005" "Sufficient checklist items" "pass"
        else
            log_error "S005: Only $checklist_items checklist items (need ≥3)"
            record_check "S005" "Sufficient checklist items" "fail"
        fi
    else
        log_error "S004: Acceptance Checklist missing"
        record_check "S004" "Acceptance Checklist defined" "fail"
        record_check "S005" "Sufficient checklist items" "skip"
    fi

    # S006: 成功标准
    if grep -q "^## Success Criteria" "$p0_doc" 2>/dev/null; then
        log_success "S006: Success Criteria exists"
        record_check "S006" "Success Criteria defined" "pass"
    else
        log_error "S006: Success Criteria missing"
        record_check "S006" "Success Criteria defined" "fail"
    fi

    # S007: 影响半径评估
    if grep -q "^## Impact Radius" "$p0_doc" 2>/dev/null; then
        log_success "S007: Impact Radius assessment exists"
        record_check "S007" "Impact Radius assessed" "pass"
    else
        log_error "S007: Impact Radius assessment missing"
        record_check "S007" "Impact Radius assessed" "fail"
    fi

    # S008: 无占位符内容
    if check_no_placeholders "$p0_doc"; then
        log_success "S008: No placeholder content detected"
        record_check "S008" "No placeholder content" "pass"
    else
        log_error "S008: Placeholder content detected (TODO/待定/占位)"
        record_check "S008" "No placeholder content" "fail"
    fi

    # S009: 文档长度合理（至少50行）
    if check_file_min_lines "$p0_doc" 50; then
        local line_count
        line_count=$(wc -l < "$p0_doc")
        log_success "S009: Document has $line_count lines (≥50)"
        record_check "S009" "Adequate document length" "pass"
    else
        log_error "S009: Document too short (<50 lines)"
        record_check "S009" "Adequate document length" "fail"
    fi
}

# ═══════════════════════════════════════════════════════════════
# Phase 1 检查项（规划与架构）
# ═══════════════════════════════════════════════════════════════

validate_phase_1() {
    log_section "Phase 1: Planning & Architecture Validation"

    local plan_doc="$PROJECT_ROOT/docs/PLAN.md"

    # S101: PLAN.md存在
    if check_file_exists_and_not_empty "$plan_doc"; then
        log_success "S101: PLAN.md document exists"
        record_check "S101" "PLAN.md exists" "pass"
    else
        log_error "S101: PLAN.md missing"
        record_check "S101" "PLAN.md exists" "fail"
        return
    fi

    # S102: 架构设计章节
    if grep -q "^## Architecture" "$plan_doc" 2>/dev/null; then
        log_success "S102: Architecture section exists"
        record_check "S102" "Architecture defined" "pass"
    else
        log_error "S102: Architecture section missing"
        record_check "S102" "Architecture defined" "fail"
    fi

    # S103: 技术栈定义
    if grep -qE "^##.*(Tech|技术|Stack)" "$plan_doc" 2>/dev/null; then
        log_success "S103: Tech stack defined"
        record_check "S103" "Tech stack defined" "pass"
    else
        log_error "S103: Tech stack definition missing"
        record_check "S103" "Tech stack defined" "fail"
    fi

    # S104: 实施步骤
    if grep -qE "^##.*(Implementation|Steps|实施)" "$plan_doc" 2>/dev/null; then
        log_success "S104: Implementation steps defined"
        record_check "S104" "Implementation steps" "pass"
    else
        log_error "S104: Implementation steps missing"
        record_check "S104" "Implementation steps" "fail"
    fi

    # S105: 无占位符
    if check_no_placeholders "$plan_doc"; then
        log_success "S105: No placeholder content"
        record_check "S105" "No placeholders" "pass"
    else
        log_error "S105: Placeholder content detected"
        record_check "S105" "No placeholders" "fail"
    fi

    # S106: 文档长度（至少30行）
    if check_file_min_lines "$plan_doc" 30; then
        log_success "S106: Document adequate length"
        record_check "S106" "Adequate length" "pass"
    else
        log_error "S106: Document too short"
        record_check "S106" "Adequate length" "fail"
    fi
}

# ═══════════════════════════════════════════════════════════════
# Phase 2 检查项（实现）
# ═══════════════════════════════════════════════════════════════

validate_phase_2() {
    log_section "Phase 2: Implementation Validation"

    # S201: 有Git提交记录（Phase 2应该有实际代码）
    local recent_commits
    recent_commits=$(git log --since="7 days ago" --oneline 2>/dev/null | wc -l || echo "0")

    if [[ $recent_commits -gt 0 ]]; then
        log_success "S201: Found $recent_commits commits in last 7 days"
        record_check "S201" "Has implementation commits" "pass"
    else
        log_warn "S201: No recent commits found"
        record_check "S201" "Has implementation commits" "fail" "No commits in 7 days"
    fi

    # S202: 脚本文件存在且可执行
    local script_count
    script_count=$(find "$PROJECT_ROOT/scripts" -type f -name "*.sh" 2>/dev/null | wc -l || echo "0")

    if [[ $script_count -gt 0 ]]; then
        log_success "S202: Found $script_count script files"
        record_check "S202" "Script files exist" "pass"

        # 检查可执行权限
        local non_executable
        non_executable=$(find "$PROJECT_ROOT/scripts" -type f -name "*.sh" ! -perm -u+x 2>/dev/null | wc -l || echo "0")

        if [[ $non_executable -eq 0 ]]; then
            log_success "S203: All scripts are executable"
            record_check "S203" "Scripts executable" "pass"
        else
            log_error "S203: $non_executable scripts missing execute permission"
            record_check "S203" "Scripts executable" "fail"
        fi
    else
        log_error "S202: No script files found"
        record_check "S202" "Script files exist" "fail"
        record_check "S203" "Scripts executable" "skip"
    fi

    # S204: 代码质量 - 无明显语法错误
    local syntax_errors=0
    for script in "$PROJECT_ROOT/scripts"/*.sh; do
        [[ -f "$script" ]] || continue
        if ! bash -n "$script" 2>/dev/null; then
            ((syntax_errors++))
        fi
    done

    if [[ $syntax_errors -eq 0 ]]; then
        log_success "S204: No syntax errors in scripts"
        record_check "S204" "No syntax errors" "pass"
    else
        log_error "S204: Found $syntax_errors scripts with syntax errors"
        record_check "S204" "No syntax errors" "fail"
    fi
}

# ═══════════════════════════════════════════════════════════════
# Phase 3 检查项（测试）
# ═══════════════════════════════════════════════════════════════

validate_phase_3() {
    log_section "Phase 3: Testing Validation"

    # S301: 静态检查脚本存在
    local static_checks="$PROJECT_ROOT/scripts/static_checks.sh"
    if [[ -x "$static_checks" ]]; then
        log_success "S301: static_checks.sh exists and executable"
        record_check "S301" "Static checks script exists" "pass"
    else
        log_error "S301: static_checks.sh missing or not executable"
        record_check "S301" "Static checks script exists" "fail"
    fi

    # S302: 测试目录存在
    if [[ -d "$PROJECT_ROOT/test" ]] || [[ -d "$PROJECT_ROOT/tests" ]]; then
        log_success "S302: Test directory exists"
        record_check "S302" "Test directory exists" "pass"
    else
        log_warn "S302: No test directory found"
        record_check "S302" "Test directory exists" "fail"
    fi

    # S303: 测试文件存在
    local test_file_count=0
    test_file_count=$(find "$PROJECT_ROOT" -name "*test*.sh" -o -name "*test*.js" -o -name "*.spec.js" 2>/dev/null | wc -l || echo "0")

    if [[ $test_file_count -gt 0 ]]; then
        log_success "S303: Found $test_file_count test files"
        record_check "S303" "Test files exist" "pass"
    else
        log_warn "S303: No test files found"
        record_check "S303" "Test files exist" "fail"
    fi

    # S304: 测试可执行（快速检查）
    if command -v npm >/dev/null 2>&1 && [[ -f "$PROJECT_ROOT/package.json" ]]; then
        if grep -q '"test":' "$PROJECT_ROOT/package.json" 2>/dev/null; then
            log_success "S304: npm test script configured"
            record_check "S304" "Test execution configured" "pass"
        else
            log_warn "S304: npm test script not configured"
            record_check "S304" "Test execution configured" "fail"
        fi
    else
        log_info "S304: npm not available or no package.json"
        record_check "S304" "Test execution configured" "skip"
    fi
}

# ═══════════════════════════════════════════════════════════════
# Phase 4 检查项（审查）
# ═══════════════════════════════════════════════════════════════

validate_phase_4() {
    log_section "Phase 4: Review Validation"

    # S401: REVIEW.md存在
    local review_doc=""
    if [[ -f "$PROJECT_ROOT/docs/REVIEW.md" ]]; then
        review_doc="$PROJECT_ROOT/docs/REVIEW.md"
    elif [[ -f "$PROJECT_ROOT/REVIEW.md" ]]; then
        review_doc="$PROJECT_ROOT/REVIEW.md"
    fi

    if [[ -n "$review_doc" ]] && [[ -s "$review_doc" ]]; then
        log_success "S401: REVIEW.md exists"
        record_check "S401" "REVIEW.md exists" "pass"

        # S402: REVIEW.md内容充分（至少50行）
        if check_file_min_lines "$review_doc" 50; then
            local line_count
            line_count=$(wc -l < "$review_doc")
            log_success "S402: REVIEW.md has $line_count lines (≥50)"
            record_check "S402" "REVIEW.md adequate" "pass"
        else
            log_error "S402: REVIEW.md too short (<50 lines)"
            record_check "S402" "REVIEW.md adequate" "fail"
        fi
    else
        log_error "S401: REVIEW.md missing"
        record_check "S401" "REVIEW.md exists" "fail"
        record_check "S402" "REVIEW.md adequate" "skip"
    fi

    # S403: 审计脚本存在
    if [[ -x "$PROJECT_ROOT/scripts/pre_merge_audit.sh" ]]; then
        log_success "S403: pre_merge_audit.sh exists"
        record_check "S403" "Audit script exists" "pass"
    else
        log_error "S403: pre_merge_audit.sh missing"
        record_check "S403" "Audit script exists" "fail"
    fi

    # S404: 版本一致性
    local version_checker="$PROJECT_ROOT/scripts/check_version_consistency.sh"
    if [[ -x "$version_checker" ]]; then
        if "$version_checker" >/dev/null 2>&1; then
            log_success "S404: Version consistency check passed"
            record_check "S404" "Version consistency" "pass"
        else
            log_error "S404: Version consistency check failed"
            record_check "S404" "Version consistency" "fail"
        fi
    else
        log_warn "S404: Version checker not available"
        record_check "S404" "Version consistency" "skip"
    fi
}

# ═══════════════════════════════════════════════════════════════
# Phase 5 检查项（发布与监控）
# ═══════════════════════════════════════════════════════════════

validate_phase_5() {
    log_section "Phase 5: Release & Monitor Validation"

    # S501: CHANGELOG更新
    if [[ -f "$PROJECT_ROOT/CHANGELOG.md" ]]; then
        # 检查最近7天是否有更新
        local mtime
        mtime=$(stat -c %Y "$PROJECT_ROOT/CHANGELOG.md" 2>/dev/null || stat -f %m "$PROJECT_ROOT/CHANGELOG.md" 2>/dev/null || echo "0")
        local now
        now=$(date +%s)
        local diff=$((now - mtime))

        if [[ $diff -lt 604800 ]]; then  # 7 days in seconds
            log_success "S501: CHANGELOG.md recently updated"
            record_check "S501" "CHANGELOG updated" "pass"
        else
            log_warn "S501: CHANGELOG.md not updated in last 7 days"
            record_check "S501" "CHANGELOG updated" "fail"
        fi
    else
        log_error "S501: CHANGELOG.md missing"
        record_check "S501" "CHANGELOG updated" "fail"
    fi

    # S502: Git标签存在
    local tag_count
    tag_count=$(git tag -l 2>/dev/null | wc -l || echo "0")

    if [[ $tag_count -gt 0 ]]; then
        local latest_tag
        latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
        log_success "S502: Found $tag_count tags, latest: $latest_tag"
        record_check "S502" "Git tags exist" "pass"
    else
        log_warn "S502: No git tags found"
        record_check "S502" "Git tags exist" "fail"
    fi

    # S503: 文档完整性
    local core_docs=("README.md" "CLAUDE.md" "INSTALLATION.md")
    local missing_docs=0

    for doc in "${core_docs[@]}"; do
        if [[ ! -f "$PROJECT_ROOT/$doc" ]]; then
            ((missing_docs++))
        fi
    done

    if [[ $missing_docs -eq 0 ]]; then
        log_success "S503: All core documentation exists"
        record_check "S503" "Core docs complete" "pass"
    else
        log_error "S503: Missing $missing_docs core documents"
        record_check "S503" "Core docs complete" "fail"
    fi
}

# ═══════════════════════════════════════════════════════════════
# 通用检查项（所有阶段）
# ═══════════════════════════════════════════════════════════════

validate_general() {
    log_section "General Quality Checks"

    # G001: .workflow/current存在
    if [[ -f "$WORKFLOW_CURRENT" ]]; then
        log_success "G001: .workflow/current exists"
        record_check "G001" "Workflow state tracked" "pass"
    else
        log_error "G001: .workflow/current missing"
        record_check "G001" "Workflow state tracked" "fail"
    fi

    # G002: Git仓库干净（无未追踪的重要文件）
    local untracked_scripts
    untracked_scripts=$(git ls-files --others --exclude-standard "$PROJECT_ROOT/scripts" 2>/dev/null | grep -E '\.sh$' | wc -l || echo "0")

    if [[ $untracked_scripts -eq 0 ]]; then
        log_success "G002: No untracked scripts"
        record_check "G002" "No untracked scripts" "pass"
    else
        log_warn "G002: Found $untracked_scripts untracked scripts"
        record_check "G002" "No untracked scripts" "fail"
    fi

    # G003: 根目录文档数量≤7
    local root_md_count
    root_md_count=$(ls -1 "$PROJECT_ROOT"/*.md 2>/dev/null | wc -l || echo "0")

    if [[ $root_md_count -le 7 ]]; then
        log_success "G003: Root has $root_md_count documents (≤7 target)"
        record_check "G003" "Root docs clean" "pass"
    else
        log_warn "G003: Root has $root_md_count documents (>7)"
        record_check "G003" "Root docs clean" "fail"
    fi
}

# ═══════════════════════════════════════════════════════════════
# 生成证据文件
# ═══════════════════════════════════════════════════════════════

generate_evidence() {
    mkdir -p "$EVIDENCE_DIR"

    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    local evidence_file="$EVIDENCE_DIR/last_run.json"

    # 计算通过率
    local pass_rate=0
    if [[ $TOTAL_CHECKS -gt 0 ]]; then
        pass_rate=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
    fi

    # 生成JSON报告
    cat > "$evidence_file" <<EOF
{
  "timestamp": "$timestamp",
  "phase": "$(get_current_phase)",
  "status": "$(get_phase_status)",
  "checks": {
    "total": $TOTAL_CHECKS,
    "passed": $PASSED_CHECKS,
    "failed": $FAILED_CHECKS,
    "skipped": $SKIPPED_CHECKS
  },
  "pass_rate": $pass_rate,
  "threshold": 80,
  "result": "$(if [[ $pass_rate -ge 80 ]]; then echo "PASS"; else echo "FAIL"; fi)",
  "failed_items": [
$(IFS=$'\n'; for item in "${FAILED_ITEMS[@]}"; do echo "    \"$item\","; done | sed '$ s/,$//')
  ],
  "all_checks": [
$(IFS=$'\n'; for check in "${CHECK_RESULTS[@]}"; do echo "    \"$check\","; done | sed '$ s/,$//')
  ]
}
EOF

    log_info "Evidence saved to: $evidence_file"
}

# ═══════════════════════════════════════════════════════════════
# 主执行流程
# ═══════════════════════════════════════════════════════════════

main() {
    local start_time
    start_time=$(date +%s)

    log_section "Workflow Validator - Claude Enhancer 6.5"

    local current_phase
    current_phase=$(get_current_phase)

    log_info "Current Phase: $current_phase"
    log_info "Current Status: $(get_phase_status)"
    log_info "Timestamp: $(date)"
    echo ""

    # 执行通用检查
    validate_general

    # 根据Phase执行对应检查
    case "$current_phase" in
        P0)
            validate_phase_0
            ;;
        P1)
            validate_phase_0  # P1依赖P0完成
            validate_phase_1
            ;;
        P2)
            validate_phase_0
            validate_phase_1
            validate_phase_2
            ;;
        P3)
            validate_phase_0
            validate_phase_1
            validate_phase_2
            validate_phase_3
            ;;
        P4)
            validate_phase_0
            validate_phase_1
            validate_phase_2
            validate_phase_3
            validate_phase_4
            ;;
        P5)
            validate_phase_0
            validate_phase_1
            validate_phase_2
            validate_phase_3
            validate_phase_4
            validate_phase_5
            ;;
        *)
            log_warn "Unknown phase: $current_phase"
            log_info "Running general checks only"
            ;;
    esac

    # 生成证据文件
    generate_evidence

    # 总结报告
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_section "Validation Summary"

    local pass_rate=0
    if [[ $TOTAL_CHECKS -gt 0 ]]; then
        pass_rate=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
    fi

    echo -e "  Total Checks:      $TOTAL_CHECKS"
    echo -e "  ${GREEN}✓ Passed:          $PASSED_CHECKS${NC}"
    echo -e "  ${RED}✗ Failed:          $FAILED_CHECKS${NC}"
    echo -e "  ${YELLOW}⊘ Skipped:         $SKIPPED_CHECKS${NC}"
    echo ""
    echo -e "  ${BOLD}Pass Rate:         ${pass_rate}%${NC}"
    echo -e "  Threshold:         80%"
    echo -e "  Duration:          ${duration}s"
    echo ""

    # 显示失败项
    if [[ ${#FAILED_ITEMS[@]} -gt 0 ]]; then
        echo -e "${RED}Failed Items:${NC}"
        for item in "${FAILED_ITEMS[@]}"; do
            echo -e "  ${RED}✗${NC} $item"
        done
        echo ""
    fi

    # 退出状态
    if [[ $pass_rate -ge 80 ]]; then
        echo -e "${GREEN}${BOLD}✅ VALIDATION PASSED${NC} (≥80% threshold)"
        echo ""
        exit 0
    else
        echo -e "${RED}${BOLD}❌ VALIDATION FAILED${NC} (<80% threshold)"
        echo ""
        echo -e "${YELLOW}Fix the failed items above to proceed${NC}"
        exit 1
    fi
}

# 执行主函数
main "$@"
