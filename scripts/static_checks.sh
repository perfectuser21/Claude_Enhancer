#!/bin/bash
# static_checks.sh - P4 Testing Phase静态检查工具
# 用途：在P4阶段运行自动化静态检查，防止技术债务
#
# 检查项：
# 1. Shell语法检查（bash -n）
# 2. Shellcheck linting（如果可用）
# 3. 代码复杂度检查（函数长度）
# 4. Hook性能测试（执行时间<2s）
# 5. 临时文件清理提醒

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 统计变量
total_checks=0
passed_checks=0
failed_checks=0
warnings=0

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  P4 Static Checks - 静态代码质量检查${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# 辅助函数
log_check() {
    echo -e "${BLUE}[CHECK]${NC} $1"
    ((total_checks++))
}

log_pass() {
    echo -e "${GREEN}  ✅ PASS${NC} $1"
    ((passed_checks++))
}

log_fail() {
    echo -e "${RED}  ❌ FAIL${NC} $1"
    ((failed_checks++))
}

log_warn() {
    echo -e "${YELLOW}  ⚠️  WARN${NC} $1"
    ((warnings++))
}

log_info() {
    echo -e "${BLUE}  ℹ️  INFO${NC} $1"
}

# ============================================
# 检查1：Shell语法检查
# ============================================
log_check "Shell Syntax Validation"
syntax_errors=0

# Performance optimized: Use simple for loop instead of find+while read
for file in "$PROJECT_ROOT/.claude/hooks"/*.sh "$PROJECT_ROOT/.git/hooks"/*.sh; do
    # Skip if glob didn't match any files
    [[ -f "$file" ]] || continue

    if ! bash -n "$file" 2>/dev/null; then
        log_fail "Syntax error in: $file"
        bash -n "$file" 2>&1 | sed 's/^/      /'
        ((syntax_errors++))
    fi
done

if [[ $syntax_errors -eq 0 ]]; then
    log_pass "All shell scripts have valid syntax"
else
    log_fail "Found $syntax_errors file(s) with syntax errors"
fi

# ============================================
# 检查2：Shellcheck Linting
# ============================================
log_check "Shellcheck Linting (if available)"

if command -v shellcheck >/dev/null 2>&1; then
    shellcheck_errors=0
    shellcheck_warnings=0

    # Performance optimized: Use simple for loop instead of find+while read
    for file in "$PROJECT_ROOT/.claude/hooks"/*.sh; do
        # Skip if glob didn't match any files
        [[ -f "$file" ]] || continue

        output=$(shellcheck -S error "$file" 2>&1 || true)
        if [[ -n "$output" ]]; then
            log_fail "Shellcheck errors in: $file"
            echo "$output" | sed 's/^/      /'
            ((shellcheck_errors++))
        fi

        # 检查warnings（不阻止，但记录）
        warn_output=$(shellcheck -S warning "$file" 2>&1 | grep -v "^$" || true)
        if [[ -n "$warn_output" ]]; then
            ((shellcheck_warnings++))
        fi
    done

    if [[ $shellcheck_errors -eq 0 ]]; then
        log_pass "No shellcheck errors found"
        if [[ $shellcheck_warnings -gt 0 ]]; then
            log_warn "$shellcheck_warnings file(s) have shellcheck warnings (non-blocking)"
        fi
    else
        log_fail "Found shellcheck errors in $shellcheck_errors file(s)"
    fi
else
    log_warn "Shellcheck not installed (optional but recommended)"
    log_info "Install: apt-get install shellcheck  or  brew install shellcheck"
fi

# ============================================
# 检查3：代码复杂度（函数长度）
# ============================================
log_check "Code Complexity (Function Length)"
complex_functions=0
too_long_functions=0

# Performance optimized: Use simple for loop instead of find+while read
for file in "$PROJECT_ROOT/.claude/hooks"/*.sh; do
    # Skip if glob didn't match any files
    [[ -f "$file" ]] || continue

    # 检测函数长度>100行的情况
    result=$(awk '
        /^[a-zA-Z_][a-zA-Z0-9_]*\(\)[ ]*{/ {
            func_name=$1;
            start=NR;
            brace_count=1;
            next;
        }
        brace_count > 0 {
            if (/\{/) brace_count++;
            if (/\}/) brace_count--;
            if (brace_count == 0) {
                length = NR - start;
                if (length > 150) {
                    print FILENAME ":" start ":" func_name " (" length " lines) - TOO LONG";
                    too_long=1;
                } else if (length > 100) {
                    print FILENAME ":" start ":" func_name " (" length " lines) - COMPLEX";
                    complex=1;
                }
            }
        }
        END {
            if (too_long) exit 2;
            if (complex) exit 1;
        }
    ' "$file")
    exit_code=$?

    if [[ $exit_code -eq 2 ]]; then
        log_fail "Function too long in: $(basename "$file")"
        echo "$result" | sed 's/^/      /'
        ((too_long_functions++))
    elif [[ $exit_code -eq 1 ]]; then
        log_warn "Complex function in: $(basename "$file")"
        echo "$result" | sed 's/^/      /'
        ((complex_functions++))
    fi
done

if [[ $too_long_functions -eq 0 ]]; then
    log_pass "No functions exceed 150 lines"
    if [[ $complex_functions -gt 0 ]]; then
        log_warn "$complex_functions function(s) exceed 100 lines (consider refactoring)"
    fi
else
    log_fail "$too_long_functions function(s) exceed 150 lines (blocking)"
fi

# ============================================
# 检查4：Hook性能测试
# ============================================
log_check "Hook Performance Test"

if [[ -x "$PROJECT_ROOT/.git/hooks/pre-commit" ]]; then
    # 测试pre-commit hook执行时间（使用空输入避免实际修改）
    start_time=$(date +%s%N)

    # 使用subshell避免实际执行副作用
    (
        cd "$PROJECT_ROOT"
        GIT_INDEX_FILE=/dev/null bash .git/hooks/pre-commit 2>/dev/null || true
    ) &
    pid=$!

    # 等待最多5秒
    timeout=5
    elapsed=0
    while kill -0 $pid 2>/dev/null && [[ $elapsed -lt $timeout ]]; do
        sleep 0.1
        ((elapsed++))
    done

    if kill -0 $pid 2>/dev/null; then
        kill $pid 2>/dev/null
        log_fail "Hook execution exceeded ${timeout}s (blocked)"
    else
        wait $pid
        end_time=$(date +%s%N)
        duration=$(( (end_time - start_time) / 1000000 ))  # 转换为毫秒
        duration_sec=$(echo "scale=2; $duration / 1000" | bc)

        if (( $(echo "$duration_sec < 2.0" | bc -l) )); then
            log_pass "Hook execution time: ${duration_sec}s (< 2s target)"
        elif (( $(echo "$duration_sec < 5.0" | bc -l) )); then
            log_warn "Hook execution time: ${duration_sec}s (2-5s, consider optimization)"
        else
            log_fail "Hook execution time: ${duration_sec}s (> 5s, blocking)"
        fi
    fi
else
    log_warn "pre-commit hook not found or not executable"
fi

# ============================================
# 检查5：临时文件清理提醒
# ============================================
log_check "Temporary Files Cleanup"

temp_files_count=$(find "$PROJECT_ROOT/.temp" -type f 2>/dev/null | wc -l || echo "0")
if [[ $temp_files_count -gt 50 ]]; then
    log_warn "Found $temp_files_count temporary files in .temp/ (consider cleanup)"
elif [[ $temp_files_count -gt 0 ]]; then
    log_pass "$temp_files_count temporary files found (acceptable, auto-cleanup in 7 days)"
else
    log_pass "No temporary files found"
fi

# ============================================
# 总结报告
# ============================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Static Checks Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Total Checks:    $total_checks"
echo -e "  ${GREEN}✅ Passed:       $passed_checks${NC}"
echo -e "  ${RED}❌ Failed:       $failed_checks${NC}"
echo -e "  ${YELLOW}⚠️  Warnings:     $warnings${NC}"
echo ""

# 退出状态
if [[ $failed_checks -gt 0 ]]; then
    echo -e "${RED}❌ Static checks FAILED - Fix errors before proceeding to P5${NC}"
    echo ""
    exit 1
elif [[ $warnings -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Static checks PASSED with warnings - Review and improve${NC}"
    echo ""
    exit 0
else
    echo -e "${GREEN}✅ All static checks PASSED - Ready for P5 Review${NC}"
    echo ""
    exit 0
fi
