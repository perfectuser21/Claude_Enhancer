#!/bin/bash
# pre_merge_audit.sh - P5 Review Phase合并前审计工具
# 用途：在P5阶段运行全面的代码审查和一致性检查
#
# 检查项：
# 1. 配置完整性（hooks注册、权限）
# 2. 遗留问题扫描（TODO/FIXME）
# 3. 垃圾文档检测（根目录文档数量）
# 4. 版本号完全一致性（VERSION + settings.json + manifest.yml + package.json + CHANGELOG.md）
# 5. 代码一致性（相似代码模式）
# 6. 文档完整性（REVIEW.md存在且完整）

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 统计变量
total_checks=0
passed_checks=0
failed_checks=0
warnings=0
manual_review_needed=0

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  P5 Pre-Merge Audit - 合并前全面审计${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# 辅助函数
log_check() {
    echo -e "${BLUE}[CHECK]${NC} $1"
    ((total_checks++)) || true
}

log_pass() {
    echo -e "${GREEN}  ✅ PASS${NC} $1"
    ((passed_checks++)) || true
}

log_fail() {
    echo -e "${RED}  ❌ FAIL${NC} $1"
    ((failed_checks++)) || true
}

log_warn() {
    echo -e "${YELLOW}  ⚠️  WARN${NC} $1"
    ((warnings++)) || true
}

log_info() {
    echo -e "${CYAN}  ℹ️  INFO${NC} $1"
}

log_manual() {
    echo -e "${YELLOW}  👤 MANUAL${NC} $1"
    ((manual_review_needed++)) || true
}

# ============================================
# 检查1：配置完整性验证
# ============================================
log_check "Configuration Completeness"
config_issues=0

# 检查hooks注册
if ! grep -q "code_writing_check.sh" "$PROJECT_ROOT/.claude/settings.json" 2>/dev/null; then
    log_fail "code_writing_check.sh not registered in settings.json"
    ((config_issues++)) || true
fi

if ! grep -q "agent_usage_enforcer.sh" "$PROJECT_ROOT/.claude/settings.json" 2>/dev/null; then
    log_fail "agent_usage_enforcer.sh not registered in settings.json"
    ((config_issues++)) || true
fi

# 检查git hooks安装（CI环境除外）
if [[ ! -x "$PROJECT_ROOT/.git/hooks/pre-commit" ]]; then
    if [ "${CI:-false}" = "true" ]; then
        log_warn "pre-commit hook not installed (OK in CI environment)"
    else
        log_fail "pre-commit hook not installed or not executable"
        ((config_issues++)) || true
    fi
fi

if [[ ! -x "$PROJECT_ROOT/.git/hooks/pre-push" ]]; then
    if [ "${CI:-false}" = "true" ]; then
        log_warn "pre-push hook not installed (OK in CI environment)"
    else
        log_fail "pre-push hook not installed or not executable"
        ((config_issues++)) || true
    fi
fi

# 检查bypassPermissionsMode
if grep -q '"bypassPermissionsMode": true' "$PROJECT_ROOT/.claude/settings.json" 2>/dev/null; then
    log_pass "bypassPermissionsMode enabled"
else
    log_warn "bypassPermissionsMode not enabled (may cause permission prompts)"
fi

if [[ $config_issues -eq 0 ]]; then
    log_pass "All configuration checks passed"
else
    log_fail "Found $config_issues configuration issue(s)"
fi

# ============================================
# 检查2：遗留问题扫描
# ============================================
log_check "Legacy Issues Scan (TODO/FIXME)"

# 扫描active代码中的TODO/FIXME（排除archive）
todo_count=$(find "$PROJECT_ROOT/.claude/hooks" -name "*.sh" -type f ! -path "*/archive*" ! -path "*/test/*" ! -path "*/.temp/*" -exec grep -l "TODO\|FIXME" {} \; 2>/dev/null | wc -l || echo "0")
todo_files=${todo_count:-0}
todo_files=$(echo "$todo_files" | tr -d ' \n')

if [[ $todo_files -eq 0 ]]; then
    log_pass "No TODO/FIXME found in active code"
elif [[ $todo_files -lt 5 ]]; then
    log_warn "Found $todo_files TODO/FIXME (review if blocking)"
    grep -r "TODO\|FIXME" \
        --include="*.sh" \
        --exclude-dir="archive" \
        --exclude-dir="test" \
        "$PROJECT_ROOT/.claude/hooks" 2>/dev/null | sed 's/^/      /' || true
else
    log_fail "Found $todo_files TODO/FIXME (too many, needs cleanup)"
fi

# ============================================
# 检查3：垃圾文档检测
# ============================================
log_check "Documentation Cleanliness"

# 检查根目录.md文件数量（应该≤7个核心文档）
root_md_count=$(find "$PROJECT_ROOT" -maxdepth 1 -name "*.md" -type f 2>/dev/null | wc -l || echo "0")

# 定义核心文档白名单
core_docs=("README.md" "CLAUDE.md" "INSTALLATION.md" "ARCHITECTURE.md" "CONTRIBUTING.md" "CHANGELOG.md" "LICENSE.md")

# 检查是否有未授权的文档
unauthorized_docs=()
# Performance optimized: Use simple for loop instead of find+while read
for file in "$PROJECT_ROOT"/*.md; do
    # Skip if glob didn't match any files
    [[ -f "$file" ]] || continue

    basename_file=$(basename "$file")
    is_core=false
    for core in "${core_docs[@]}"; do
        if [[ "$basename_file" == "$core" ]]; then
            is_core=true
            break
        fi
    done

    if [[ "$is_core" == "false" ]]; then
        # 检查是否是报告文件模式
        if [[ "$basename_file" =~ _REPORT\.md$|_ANALYSIS\.md$|_AUDIT\.md$|_SUMMARY\.md$ ]]; then
            unauthorized_docs+=("$basename_file")
        fi
    fi
done

if [[ ${#unauthorized_docs[@]} -gt 0 ]]; then
    log_fail "Found ${#unauthorized_docs[@]} unauthorized document(s):"
    for doc in "${unauthorized_docs[@]}"; do
        echo "        - $doc (should be in .temp/ or removed)"
    done
else
    log_pass "No unauthorized documents in root directory"
fi

if [[ $root_md_count -le 7 ]]; then
    log_pass "Root directory has $root_md_count documents (≤7 target)"
else
    log_warn "Root directory has $root_md_count documents (>7, consider cleanup)"
fi

# ============================================
# 检查4：版本号完全一致性（5个文件）
# ============================================
log_check "Version Number Consistency (5 files)"

# 提取所有5个文件的版本号
version_file=$(tr -d '\n\r' < "$PROJECT_ROOT/VERSION" 2>/dev/null | xargs || echo "unknown")
settings_version=$(grep '"version"' "$PROJECT_ROOT/.claude/settings.json" 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1 || echo "unknown")
manifest_version=$(grep '^version:' "$PROJECT_ROOT/.workflow/manifest.yml" 2>/dev/null | grep -oP '\d+\.\d+\.\d+' || echo "unknown")
package_version=$(grep '"version"' "$PROJECT_ROOT/package.json" 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1 || echo "unknown")
changelog_version=$(grep -oP '\[\K[0-9]+\.[0-9]+\.[0-9]+(?=\])' "$PROJECT_ROOT/CHANGELOG.md" 2>/dev/null | head -1 || echo "unknown")

log_info "VERSION file:      $version_file"
log_info "settings.json:     $settings_version"
log_info "manifest.yml:      $manifest_version"
log_info "package.json:      $package_version"
log_info "CHANGELOG.md:      $changelog_version"

# 版本号必须完全一致（硬性要求）
version_inconsistency=0

if [[ "$version_file" == "unknown" ]] || [[ "$settings_version" == "unknown" ]] || \
   [[ "$manifest_version" == "unknown" ]] || [[ "$package_version" == "unknown" ]] || \
   [[ "$changelog_version" == "unknown" ]]; then
    log_fail "Could not extract all version numbers"
    ((version_inconsistency++)) || true
fi

# 检查所有版本是否完全相同
if [[ "$version_file" != "$settings_version" ]]; then
    log_fail "VERSION ($version_file) ≠ settings.json ($settings_version)"
    ((version_inconsistency++)) || true
fi

if [[ "$version_file" != "$manifest_version" ]]; then
    log_fail "VERSION ($version_file) ≠ manifest.yml ($manifest_version)"
    ((version_inconsistency++)) || true
fi

if [[ "$version_file" != "$package_version" ]]; then
    log_fail "VERSION ($version_file) ≠ package.json ($package_version)"
    ((version_inconsistency++)) || true
fi

if [[ "$version_file" != "$changelog_version" ]]; then
    log_fail "VERSION ($version_file) ≠ CHANGELOG.md ($changelog_version)"
    ((version_inconsistency++)) || true
fi

if [[ $version_inconsistency -eq 0 ]] && [[ "$version_file" != "unknown" ]]; then
    log_pass "All 5 version files are consistent: $version_file"
else
    log_fail "Version inconsistency detected - THIS IS A HARD BLOCK"
    echo -e "${RED}      Action required: Run 'bash scripts/check_version_consistency.sh' for fix instructions${NC}"
fi

# ============================================
# 检查5：代码一致性（模式检查）
# ============================================
log_check "Code Pattern Consistency"

# 检查workflow_guard.sh的Layers一致性
if [[ -f "$PROJECT_ROOT/.claude/hooks/workflow_guard.sh" ]]; then
    # 检查是否所有Layers使用统一的exit code检查模式
    # 正确模式：detect_*; result=$?; if [[ result -eq 0 ]]

    inconsistent_patterns=0

    # 检查Layer 1-6的实现模式
    for layer in {1..6}; do
        # 查找每个Layer的实现
        layer_section=$(sed -n "/Layer $layer:/,/Layer $((layer+1)):/p" "$PROJECT_ROOT/.claude/hooks/workflow_guard.sh" 2>/dev/null || echo "")

        if [[ -n "$layer_section" ]]; then
            # 检查是否使用了正确的模式
            if echo "$layer_section" | grep -q "local layer${layer}_result=\$?"; then
                # 正确模式
                continue
            elif echo "$layer_section" | grep -q "if detect_.*; then"; then
                # 错误模式（旧的IF直接调用）
                log_warn "Layer $layer uses old pattern (should store exit code first)"
                ((inconsistent_patterns++)) || true
            fi
        fi
    done

    if [[ $inconsistent_patterns -eq 0 ]]; then
        log_pass "All layers use consistent exit code checking pattern"
    else
        log_fail "Found $inconsistent_patterns layer(s) with inconsistent patterns"
        log_manual "Review workflow_guard.sh layers for pattern consistency"
    fi
else
    log_warn "workflow_guard.sh not found"
fi

# ============================================
# 检查6：文档完整性
# ============================================
log_check "Documentation Completeness"

# 检查REVIEW.md存在
if [[ ! -f "$PROJECT_ROOT/docs/REVIEW.md" ]] && [[ ! -f "$PROJECT_ROOT/REVIEW.md" ]]; then
    log_fail "REVIEW.md not found (required for P5)"
else
    review_file="$PROJECT_ROOT/docs/REVIEW.md"
    [[ ! -f "$review_file" ]] && review_file="$PROJECT_ROOT/REVIEW.md"

    review_lines=$(wc -l < "$review_file" 2>/dev/null || echo "0")
    if [[ $review_lines -lt 50 ]]; then
        log_warn "REVIEW.md only has $review_lines lines (seems incomplete)"
        log_manual "Verify REVIEW.md covers all important changes"
    else
        log_pass "REVIEW.md exists and has $review_lines lines"
    fi
fi

# 检查git staged changes是否有文档更新
changed_code_count=$(git diff --cached --name-only 2>/dev/null | grep -cE '\.(sh|py|js|ts)$' || echo "0")
changed_code_files=${changed_code_count:-0}
changed_code_files=$(echo "$changed_code_files" | tr -d ' \n')

changed_doc_count=$(git diff --cached --name-only 2>/dev/null | grep -cE '\.(md)$|^docs/' || echo "0")
changed_doc_files=${changed_doc_count:-0}
changed_doc_files=$(echo "$changed_doc_files" | tr -d ' \n')

if [[ $changed_code_files -gt 0 ]]; then
    log_info "Found $changed_code_files code file(s) changed"
    if [[ $changed_doc_files -eq 0 ]]; then
        log_warn "Code changed but no documentation updated"
        log_manual "Verify if documentation needs updates"
    else
        log_pass "Code changes accompanied by $changed_doc_files documentation update(s)"
    fi
fi

# ============================================
# 检查7：Runtime Behavior Validation
# ============================================
log_check "Runtime Behavior Validation"

# 7.1 检查parallel_subagent_suggester.sh是否执行过
suggester_log="$PROJECT_ROOT/.workflow/logs/subagent/suggester.log"
if [[ ! -f "$suggester_log" ]]; then
    log_fail "suggester.log never created - hollow implementation!"
else
    # 检查文件最后修改时间
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        file_mtime=$(stat -f "%m" "$suggester_log" 2>/dev/null || echo "0")
    else
        # Linux
        file_mtime=$(stat -c "%Y" "$suggester_log" 2>/dev/null || echo "0")
    fi
    current_time=$(date +%s)
    days_old=$(( (current_time - file_mtime) / 86400 ))

    if [[ $days_old -gt 7 ]]; then
        log_warn "suggester.log is $days_old days old (>7 days, may be stale)"
    else
        log_pass "suggester.log executed recently ($days_old days ago)"
    fi
fi

# 7.2 检查.phase/current是否维护
phase_current="$PROJECT_ROOT/.phase/current"
if [[ ! -f "$phase_current" ]]; then
    log_warn ".phase/current not found (phase tracking may not be active)"
else
    # 检查文件最后修改时间
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        file_mtime=$(stat -f "%m" "$phase_current" 2>/dev/null || echo "0")
    else
        # Linux
        file_mtime=$(stat -c "%Y" "$phase_current" 2>/dev/null || echo "0")
    fi
    current_time=$(date +%s)
    days_old=$(( (current_time - file_mtime) / 86400 ))

    if [[ $days_old -gt 7 ]]; then
        log_warn ".phase/current is $days_old days old (>7 days, phase tracking may be stale)"
    else
        log_pass ".phase/current maintained recently ($days_old days ago)"
    fi
fi

# 7.3 检查evidence收集情况
evidence_dir="$PROJECT_ROOT/.evidence"
if [[ ! -d "$evidence_dir" ]]; then
    log_warn "No .evidence/ directory found"
else
    # 查找7天内修改的.yml文件
    recent_evidence_count=0
    current_time=$(date +%s)
    seven_days_ago=$((current_time - 604800))  # 7 days in seconds

    while IFS= read -r -d '' file; do
        if [[ "$(uname)" == "Darwin" ]]; then
            # macOS
            file_mtime=$(stat -f "%m" "$file" 2>/dev/null || echo "0")
        else
            # Linux
            file_mtime=$(stat -c "%Y" "$file" 2>/dev/null || echo "0")
        fi

        if [[ $file_mtime -gt $seven_days_ago ]]; then
            ((recent_evidence_count++)) || true
        fi
    done < <(find "$evidence_dir" -name "*.yml" -print0 2>/dev/null || true)

    if [[ $recent_evidence_count -eq 0 ]]; then
        log_warn "No evidence collected in last 7 days (0 .yml files)"
    else
        log_pass "Evidence collected recently ($recent_evidence_count .yml files in last 7 days)"
    fi
fi

# ============================================
# 检查8：Git状态检查
# ============================================
log_check "Git Repository Status"

# 检查当前分支
current_branch=$(git -C "$PROJECT_ROOT" branch --show-current 2>/dev/null || echo "unknown")
log_info "Current branch: $current_branch"

if [[ "$current_branch" == "main" ]] || [[ "$current_branch" == "master" ]]; then
    log_fail "Currently on $current_branch branch (should be on feature/bugfix branch)"
elif [[ "$current_branch" =~ ^(feature|bugfix|hotfix)/ ]]; then
    log_pass "On appropriate branch: $current_branch"
else
    log_warn "Unusual branch name: $current_branch"
fi

# 检查是否有未提交的修改
if git -C "$PROJECT_ROOT" diff --quiet 2>/dev/null; then
    log_pass "No unstaged changes"
else
    log_warn "Found unstaged changes (stage or stash before merge)"
fi

# ============================================
# 人工审查清单
# ============================================
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Manual Review Checklist (人工验证项)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}请人工确认以下项目：${NC}"
echo ""
echo "  [ ] 代码逻辑正确性"
echo "      - IF判断方向正确（exit code检查）"
echo "      - Return值语义一致（0=成功）"
echo "      - 错误处理模式统一"
echo ""
echo "  [ ] 代码一致性"
echo "      - 相似功能使用相同代码模式"
echo "      - 所有Layers使用统一逻辑"
echo "      - 日志输出与实际行为匹配"
echo ""
echo "  [ ] 文档完整性"
echo "      - REVIEW.md记录所有重要决策"
echo "      - 修改的功能有对应文档更新"
echo "      - 复杂逻辑有注释说明"
echo ""
echo "  [ ] P0 Acceptance Checklist验证"
echo "      - 对照P0创建的验收清单逐项验证"
echo "      - 所有验收标准100%达成"
echo ""
echo "  [ ] Diff全面审查"
echo "      - 逐文件检查所有修改"
echo "      - 确认没有误删重要代码"
echo "      - 验证新增代码质量"
echo ""

# ============================================
# 总结报告
# ============================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Pre-Merge Audit Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Total Checks:         $total_checks"
echo -e "  ${GREEN}✅ Passed:            $passed_checks${NC}"
echo -e "  ${RED}❌ Failed:            $failed_checks${NC}"
echo -e "  ${YELLOW}⚠️  Warnings:          $warnings${NC}"
echo -e "  ${YELLOW}👤 Manual Review:     $manual_review_needed item(s)${NC}"
echo ""

# 退出状态
if [[ $failed_checks -gt 0 ]]; then
    echo -e "${RED}❌ Pre-merge audit FAILED - Fix critical issues before merge${NC}"
    echo ""
    exit 1
elif [[ $manual_review_needed -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Automated checks PASSED - Complete manual review checklist${NC}"
    echo -e "${YELLOW}   Run this script again after addressing manual items${NC}"
    echo ""
    exit 0
elif [[ $warnings -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Pre-merge audit PASSED with warnings - Review recommended${NC}"
    echo ""
    exit 0
else
    echo -e "${GREEN}✅ All pre-merge checks PASSED - Ready for P6 Release${NC}"
    echo ""
    exit 0
fi

# ═══════════════════════════════════════════════════════════
# Checklist Consistency Check
# ═══════════════════════════════════════════════════════════
echo ""
echo "📋 Checklist Consistency Check"

if [ -f ".workflow/ACCEPTANCE_CHECKLIST.md" ] && [ -f ".workflow/TECHNICAL_CHECKLIST.md" ]; then
  # Run validator
  if bash .claude/hooks/validate_checklist_mapping.sh 2>/dev/null; then
    echo "  ✓ Checklist mapping consistent"
  else
    echo "  ✗ Checklist mapping has issues"
    CRITICAL_ISSUES=$((CRITICAL_ISSUES+1))
  fi
  
  # Check user version has no forbidden terms
  forbidden_count=$(grep -ciE "\b(API|JWT|BCrypt|Redis|OAuth|JSON|YAML|HTTP|SQL|NoSQL|Token|Hash|Encrypt|Decrypt|Cookie|Session|Database|Table|Index|Query|Schema)\b" \
    .workflow/ACCEPTANCE_CHECKLIST.md 2>/dev/null || echo 0)
  
  if [ "$forbidden_count" -gt 0 ]; then
    echo "  ✗ User checklist contains $forbidden_count forbidden terms"
    CRITICAL_ISSUES=$((CRITICAL_ISSUES+1))
  else
    echo "  ✓ User checklist language appropriate"
  fi
else
  # shellcheck disable=SC2317
  echo "  ⊘ No checklists found (may not be applicable)"
fi
