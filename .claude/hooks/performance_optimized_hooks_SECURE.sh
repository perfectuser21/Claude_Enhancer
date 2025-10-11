#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Performance-Optimized Git Hooks for Document Quality Management
# 性能优化的Git Hooks - 文档质量管理三层防护
# SECURITY PATCH: Fixed unprotected rm -rf vulnerability

set -e

# 性能配置
PERFORMANCE_MODE="${CLAUDE_PERFORMANCE_MODE:-balanced}"  # fast, balanced, thorough
MAX_PARALLEL_JOBS="${CLAUDE_MAX_JOBS:-4}"
CACHE_ENABLED="${CLAUDE_CACHE_ENABLED:-true}"
TIMEOUT_PRECOMMIT="${CLAUDE_TIMEOUT_PRECOMMIT:-2}"
TIMEOUT_PREPUSH="${CLAUDE_TIMEOUT_PREPUSH:-5}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════════════════
# SECURITY: Safe rm -rf implementation
# 防止误删除、路径注入、符号链接攻击
# ═══════════════════════════════════════════════════════════════════
safe_rm_rf() {
    local target_dir="$1"
    local dry_run="${DRY_RUN:-0}"
    
    # 1. 路径白名单验证
    local allowed_prefixes=(
        "/tmp/"
        "/var/tmp/"
        "${TMPDIR:-/tmp}/"
    )
    
    local path_allowed=false
    for prefix in "${allowed_prefixes[@]}"; do
        if [[ "$target_dir" == "$prefix"* ]]; then
            path_allowed=true
            break
        fi
    done
    
    if [[ "$path_allowed" == "false" ]]; then
        echo -e "${RED}❌ SECURITY: Path not in whitelist: $target_dir${NC}" >&2
        echo "   Allowed prefixes: ${allowed_prefixes[*]}" >&2
        return 1
    fi
    
    # 2. 路径完整性检查
    if [[ -z "$target_dir" ]]; then
        echo -e "${RED}❌ SECURITY: Empty path provided${NC}" >&2
        return 1
    fi
    
    if [[ ! "$target_dir" =~ ^/tmp/.+ && ! "$target_dir" =~ ^/var/tmp/.+ ]]; then
        echo -e "${RED}❌ SECURITY: Invalid temp path format${NC}" >&2
        return 1
    fi
    
    # 3. 检查目录存在性（防止符号链接攻击）
    if [[ ! -d "$target_dir" ]]; then
        echo -e "${YELLOW}⚠️  Directory does not exist: $target_dir${NC}" >&2
        return 0
    fi
    
    # 4. 检查是否为符号链接
    if [[ -L "$target_dir" ]]; then
        echo -e "${RED}❌ SECURITY: Refusing to delete symbolic link: $target_dir${NC}" >&2
        return 1
    fi
    
    # 5. Dry-run模式
    if [[ "$dry_run" == "1" ]]; then
        echo -e "${BLUE}[DRY-RUN] Would remove: $target_dir${NC}"
        if [[ -d "$target_dir" ]]; then
            local file_count=$(find "$target_dir" -type f | wc -l)
            local dir_size=$(du -sh "$target_dir" 2>/dev/null | cut -f1)
            echo "   Files: $file_count, Size: $dir_size"
        fi
        return 0
    fi
    
    # 6. 交互确认（生产环境）
    if [[ "${CLAUDE_ENV:-dev}" == "production" ]]; then
        echo -e "${YELLOW}⚠️  About to delete: $target_dir${NC}"
        read -p "Confirm deletion? (yes/NO): " -r answer
        if [[ "$answer" != "yes" ]]; then
            echo "Deletion cancelled"
            return 0
        fi
    fi
    
    # 7. 安全删除（使用--preserve-root防护）
    if rm -rf --preserve-root -- "$target_dir" 2>/dev/null; then
        echo -e "${GREEN}✓ Safely removed: $target_dir${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to remove: $target_dir${NC}" >&2
        return 1
    fi
}

# 性能监控
start_time() {
    echo $(date +%s.%N)
}

end_time() {
    local start=$1
    local end=$(date +%s.%N)
    echo "scale=3; $end - $start" | bc -l 2>/dev/null || echo "0.001"
}

# 获取变更的文档文件
get_changed_doc_files() {
    local filter_type="$1"  # staged, push, all
    local files=()

    case "$filter_type" in
        "staged")
            # Pre-commit: 只检查暂存的文档文件
            files=($(git diff --cached --name-only --diff-filter=AM | grep -E '\.(md|txt|rst|adoc|org)$' || true))
            ;;
        "push")
            # Pre-push: 检查将要推送的文档文件
            local remote_ref="$2"
            local local_ref="$3"
            files=($(git diff --name-only "$remote_ref..$local_ref" | grep -E '\.(md|txt|rst|adoc|org)$' || true))
            ;;
        "all")
            # 所有文档文件
            files=($(find . -name "*.md" -o -name "*.txt" -o -name "*.rst" -o -name "*.adoc" -o -name "*.org" | grep -v node_modules | head -100))
            ;;
    esac

    printf '%s\n' "${files[@]}"
}

# 快速语法检查
fast_syntax_check() {
    local file="$1"
    local issues=0

    if [[ ! -f "$file" ]]; then
        return 1
    fi

    # 检查文件是否为空
    if [[ ! -s "$file" ]]; then
        echo "❌ Empty file: $file"
        return 1
    fi

    # Markdown特定检查
    if [[ "$file" == *.md ]]; then
        # 检查是否有标题
        if ! grep -q '^#' "$file"; then
            echo "⚠️ No headers in: $file"
            ((issues++))
        fi

        # 检查破损链接
        if grep -q ']\(\)' "$file"; then
            echo "❌ Empty links in: $file"
            ((issues++))
        fi
    fi

    return $issues
}

# 并行文件检查
parallel_check() {
    local check_function="$1"
    shift
    local files=("$@")

    if [[ ${#files[@]} -eq 0 ]]; then
        return 0
    fi

    # 创建临时目录存储结果（使用安全的mktemp）
    local temp_dir
    temp_dir=$(mktemp -d -t claude_hooks.XXXXXXXXXX) || {
        echo -e "${RED}❌ Failed to create temp directory${NC}" >&2
        return 1
    }
    
    local job_count=0
    local max_jobs=$MAX_PARALLEL_JOBS

    # 启动并行任务
    for file in "${files[@]}"; do
        {
            local result_file="$temp_dir/result_$$_$job_count"
            if $check_function "$file" > "$result_file" 2>&1; then
                echo "0" > "$result_file.exit"
            else
                echo "$?" > "$result_file.exit"
            fi
        } &

        ((job_count++))

        # 控制并发数
        if ((job_count % max_jobs == 0)); then
            wait
        fi
    done

    # 等待所有任务完成
    wait

    # 收集结果
    local total_issues=0
    for result_file in "$temp_dir"/result_*; do
        if [[ -f "$result_file" && ! "$result_file" == *.exit ]]; then
            if [[ -s "$result_file" ]]; then
                cat "$result_file"
            fi

            local exit_file="${result_file}.exit"
            if [[ -f "$exit_file" ]]; then
                local exit_code=$(cat "$exit_file")
                ((total_issues += exit_code))
            fi
        fi
    done

    # 清理临时文件（使用安全删除）
    safe_rm_rf "$temp_dir"

    return $total_issues
}

# Pre-commit Hook (目标: < 2秒)
pre_commit_hook() {
    local start=$(start_time)
    echo -e "${BLUE}🔍 Pre-commit Document Check (Fast Mode)${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # 获取暂存的文档文件
    local staged_files
    mapfile -t staged_files < <(get_changed_doc_files "staged")

    if [[ ${#staged_files[@]} -eq 0 ]]; then
        echo -e "${GREEN}✅ No documentation files to check${NC}"
        return 0
    fi

    echo "📁 Checking ${#staged_files[@]} documentation files..."

    # 快速并行检查
    local issues=0
    if ! parallel_check fast_syntax_check "${staged_files[@]}"; then
        issues=$?
    fi

    local duration=$(end_time $start)
    echo "⏱️ Pre-commit check completed in ${duration}s"

    # 性能目标检查
    if (( $(echo "$duration > $TIMEOUT_PRECOMMIT" | bc -l 2>/dev/null || echo "0") )); then
        echo -e "${YELLOW}⚠️ Performance warning: check took ${duration}s (target: ${TIMEOUT_PRECOMMIT}s)${NC}"
    fi

    if [[ $issues -eq 0 ]]; then
        echo -e "${GREEN}✅ All pre-commit checks passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ Found $issues issue(s) in documentation${NC}"
        echo "💡 Fix these issues before committing"
        return 1
    fi
}

# Pre-push Hook (目标: < 5秒)
pre_push_hook() {
    local remote="$1"
    local url="$2"
    local local_ref="$3"
    local local_sha="$4"
    local remote_ref="$5"
    local remote_sha="$6"

    local start=$(start_time)
    echo -e "${BLUE}🚀 Pre-push Document Check (Enhanced Mode)${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # 获取将要推送的文档文件
    local push_files
    if [[ "$remote_sha" != "0000000000000000000000000000000000000000" ]]; then
        mapfile -t push_files < <(get_changed_doc_files "push" "$remote_ref" "$local_ref")
    else
        # 新分支，检查所有文档文件
        mapfile -t push_files < <(get_changed_doc_files "all")
    fi

    if [[ ${#push_files[@]} -eq 0 ]]; then
        echo -e "${GREEN}✅ No documentation files to check${NC}"
        return 0
    fi

    echo "📁 Checking ${#push_files[@]} documentation files..."

    # 增强检查：语法 + 样式 + 基本内容
    local total_issues=0

    # 1. 快速语法检查
    echo "🔍 Stage 1: Syntax check..."
    if ! parallel_check fast_syntax_check "${push_files[@]}"; then
        ((total_issues += $?))
    fi

    # 2. 样式检查（如果时间允许）
    local current_time=$(end_time $start)
    if (( $(echo "$current_time < 3.0" | bc -l 2>/dev/null || echo "1") )); then
        echo "🎨 Stage 2: Style check..."
        # 简化的样式检查
        for file in "${push_files[@]}"; do
            if [[ -f "$file" ]]; then
                # 检查行长度
                if grep -n '.\{121,\}' "$file" > /dev/null; then
                    echo "⚠️ Long lines in: $file"
                    ((total_issues++))
                fi

                # 检查空行比例
                local total_lines=$(wc -l < "$file")
                local empty_lines=$(grep -c '^$' "$file" || echo "0")
                if [[ $total_lines -gt 0 ]]; then
                    local empty_ratio=$(echo "scale=2; $empty_lines / $total_lines" | bc -l 2>/dev/null || echo "0")
                    if (( $(echo "$empty_ratio > 0.5" | bc -l 2>/dev/null || echo "0") )); then
                        echo "⚠️ Too many empty lines in: $file"
                        ((total_issues++))
                    fi
                fi
            fi
        done
    fi

    local duration=$(end_time $start)
    echo "⏱️ Pre-push check completed in ${duration}s"

    # 性能目标检查
    if (( $(echo "$duration > $TIMEOUT_PREPUSH" | bc -l 2>/dev/null || echo "0") )); then
        echo -e "${YELLOW}⚠️ Performance warning: check took ${duration}s (target: ${TIMEOUT_PREPUSH}s)${NC}"
    fi

    if [[ $total_issues -eq 0 ]]; then
        echo -e "${GREEN}✅ All pre-push checks passed!${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ Found $total_issues issue(s) in documentation${NC}"
        echo "💡 Consider fixing these issues, but push is not blocked"
        return 0  # 不阻止推送，只警告
    fi
}

# 主入口点
main() {
    local hook_type="$1"
    shift

    # 设置性能模式
    case "$PERFORMANCE_MODE" in
        "fast")
            MAX_PARALLEL_JOBS=8
            TIMEOUT_PRECOMMIT=1
            TIMEOUT_PREPUSH=3
            ;;
        "balanced")
            MAX_PARALLEL_JOBS=4
            TIMEOUT_PRECOMMIT=2
            TIMEOUT_PREPUSH=5
            ;;
        "thorough")
            MAX_PARALLEL_JOBS=2
            TIMEOUT_PRECOMMIT=5
            TIMEOUT_PREPUSH=10
            ;;
    esac

    echo -e "${BLUE}🎯 Performance Mode: $PERFORMANCE_MODE (Jobs: $MAX_PARALLEL_JOBS)${NC}"

    case "$hook_type" in
        "pre-commit")
            pre_commit_hook "$@"
            ;;
        "pre-push")
            pre_push_hook "$@"
            ;;
        *)
            echo "Usage: $0 {pre-commit|pre-push} [args...]"
            exit 1
            ;;
    esac
}

# 如果直接运行此脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
