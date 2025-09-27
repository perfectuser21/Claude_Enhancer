#!/bin/bash

# 📋 Local Documentation Quality Check Script
# 用于本地快速验证文档质量，与GitHub Actions workflow保持一致

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 图标定义
CHECK_MARK="✅"
CROSS_MARK="❌"
WARNING="⚠️"
INFO="ℹ️"
ROCKET="🚀"
MAGNIFY="🔍"
DOCUMENT="📄"
LINK="🔗"
PENCIL="✏️"
REPORT="📊"

# 脚本信息
SCRIPT_NAME="Documentation Quality Check"
VERSION="1.0.0"
START_TIME=$(date +%s)

# 工作目录设置
WORK_DIR="${1:-$(pwd)}"
TEMP_DIR=$(mktemp -d)
LOG_FILE="$TEMP_DIR/docs_quality.log"

# 清理函数
cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# 日志函数
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}${INFO} $1${NC}"
}

log_success() {
    log "${GREEN}${CHECK_MARK} $1${NC}"
}

log_warning() {
    log "${YELLOW}${WARNING} $1${NC}"
}

log_error() {
    log "${RED}${CROSS_MARK} $1${NC}"
}

log_header() {
    log "\n${PURPLE}=== $1 ===${NC}"
}

# 检查依赖
check_dependencies() {
    log_header "Checking Dependencies"

    local missing_deps=()

    # 检查必需工具
    local deps=("markdownlint-cli2" "markdown-link-check" "python3")

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing_deps+=("$dep")
        else
            log_success "$dep is available"
        fi
    done

    # 检查可选工具
    local optional_deps=("write-good" "alex")

    for dep in "${optional_deps[@]}"; do
        if command -v "$dep" &> /dev/null; then
            log_success "$dep is available (optional)"
        else
            log_warning "$dep is not available (optional)"
        fi
    done

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Please install missing dependencies:"
        log_info "npm install -g markdownlint-cli2 markdown-link-check"
        log_info "# For writing quality checks:"
        log_info "npm install -g write-good alex"
        exit 1
    fi
}

# 发现文档文件
discover_docs() {
    log_header "Discovering Documentation Files"

    cd "$WORK_DIR"

    # 查找文档文件
    find . -type f \( -name "*.md" -o -name "*.mdx" \) \
        ! -path "./node_modules/*" \
        ! -path "./.git/*" \
        ! -path "./build/*" \
        ! -path "./dist/*" \
        ! -path "./coverage/*" > "$TEMP_DIR/docs_files.txt"

    local total_files=$(wc -l < "$TEMP_DIR/docs_files.txt")
    local total_size=$(cat "$TEMP_DIR/docs_files.txt" | xargs du -b 2>/dev/null | awk '{sum += $1} END {print sum}' || echo "0")
    local total_size_kb=$((total_size / 1024))

    log_success "Found $total_files documentation files"
    log_info "Total size: ${total_size_kb}KB"

    # 分类文件
    grep -E "(README|readme)" "$TEMP_DIR/docs_files.txt" > "$TEMP_DIR/readme_files.txt" || touch "$TEMP_DIR/readme_files.txt"
    grep -E "(CHANGELOG|changelog)" "$TEMP_DIR/docs_files.txt" > "$TEMP_DIR/changelog_files.txt" || touch "$TEMP_DIR/changelog_files.txt"
    grep -E "docs/" "$TEMP_DIR/docs_files.txt" > "$TEMP_DIR/docs_folder_files.txt" || touch "$TEMP_DIR/docs_folder_files.txt"

    # 导出变量供其他函数使用
    export TOTAL_FILES=$total_files
    export TOTAL_SIZE_KB=$total_size_kb
}

# Markdown Linting
run_markdown_lint() {
    log_header "Markdown Linting"

    local config_file=".markdownlint.json"
    local lint_output="$TEMP_DIR/markdown_lint.log"

    # 检查配置文件
    if [[ ! -f "$config_file" ]]; then
        log_warning "No .markdownlint.json found, using default configuration"
        config_file=""
    else
        log_info "Using configuration: $config_file"
    fi

    # 运行linting
    local lint_cmd="markdownlint-cli2 \"**/*.md\" \"!node_modules/**\""
    if [[ -n "$config_file" ]]; then
        lint_cmd="markdownlint-cli2 --config $config_file \"**/*.md\" \"!node_modules/**\""
    fi

    if eval "$lint_cmd" > "$lint_output" 2>&1; then
        log_success "Markdown linting passed"
        export LINT_STATUS="passed"
        export LINT_ISSUES=0
    else
        local issues=$(wc -l < "$lint_output")
        log_error "Markdown linting found $issues issues"
        log_info "Check $lint_output for details"
        export LINT_STATUS="failed"
        export LINT_ISSUES=$issues

        # 显示前5个问题
        if [[ $issues -gt 0 ]]; then
            log_info "First 5 issues:"
            head -5 "$lint_output" | while read -r line; do
                log "  ${YELLOW}$line${NC}"
            done
        fi
    fi
}

# 链接检查
check_links() {
    log_header "Link Validation"

    local config_file=".markdown-link-check.json"
    local broken_links=0
    local total_links=0
    local checked_files=0

    # 检查配置文件
    if [[ ! -f "$config_file" ]]; then
        log_warning "No .markdown-link-check.json found, using default settings"
        config_args=""
    else
        log_info "Using configuration: $config_file"
        config_args="--config $config_file"
    fi

    # 并行检查链接（限制并发数）
    local max_concurrent=5
    local pids=()

    while IFS= read -r file; do
        if [[ -f "$file" && -s "$file" ]]; then
            # 控制并发数
            while [[ ${#pids[@]} -ge $max_concurrent ]]; do
                for i in "${!pids[@]}"; do
                    if ! kill -0 "${pids[$i]}" 2>/dev/null; then
                        unset "pids[$i]"
                    fi
                done
                pids=("${pids[@]}")  # 重新索引数组
                sleep 0.1
            done

            # 启动新的检查进程
            (
                local link_output="$TEMP_DIR/link_check_$(basename "$file").log"
                if markdown-link-check "$file" $config_args --quiet > "$link_output" 2>&1; then
                    echo "OK:$file" >> "$TEMP_DIR/link_results.txt"
                else
                    echo "FAIL:$file" >> "$TEMP_DIR/link_results.txt"
                fi

                # 统计链接数量
                local link_count=$(grep -o '\[.*\](.*)'  "$file" 2>/dev/null | wc -l || echo 0)
                echo "$link_count" >> "$TEMP_DIR/link_counts.txt"
            ) &

            pids+=($!)
            ((checked_files++))

            if ((checked_files % 10 == 0)); then
                log_info "Checked $checked_files files..."
            fi
        fi
    done < "$TEMP_DIR/docs_files.txt"

    # 等待所有进程完成
    for pid in "${pids[@]}"; do
        wait "$pid" 2>/dev/null || true
    done

    # 统计结果
    if [[ -f "$TEMP_DIR/link_results.txt" ]]; then
        broken_links=$(grep -c "FAIL:" "$TEMP_DIR/link_results.txt" 2>/dev/null || echo 0)
    fi

    if [[ -f "$TEMP_DIR/link_counts.txt" ]]; then
        total_links=$(awk '{sum += $1} END {print sum}' "$TEMP_DIR/link_counts.txt" 2>/dev/null || echo 0)
    fi

    log_success "Checked $checked_files files"
    log_info "Total links found: $total_links"

    if [[ $broken_links -eq 0 ]]; then
        log_success "No broken links found"
    else
        log_error "Found $broken_links files with broken links"
    fi

    export BROKEN_LINKS=$broken_links
    export TOTAL_LINKS=$total_links
}

# 写作质量分析
analyze_writing_quality() {
    log_header "Writing Quality Analysis"

    local total_issues=0
    local readability_scores=()
    local analyzed_files=0

    # 检查Python textstat模块
    if ! python3 -c "import textstat" 2>/dev/null; then
        log_warning "textstat module not available, skipping readability analysis"
        log_info "Install with: pip install textstat"
    fi

    while IFS= read -r file; do
        if [[ -f "$file" && -s "$file" ]]; then
            ((analyzed_files++))

            # 可读性分析
            if python3 -c "import textstat" 2>/dev/null; then
                local score=$(python3 -c "
import textstat
import sys
import re
try:
    with open('$file', 'r', encoding='utf-8') as f:
        text = f.read()
    # 移除markdown语法
    text = re.sub(r'[#*\`\[\]()]', '', text)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    if len(text.strip()) > 100:
        score = textstat.flesch_reading_ease(text)
        print(f'{score:.1f}')
    else:
        print('N/A')
except Exception as e:
    print('N/A')
" 2>/dev/null)

                if [[ "$score" != "N/A" && "$score" != "" ]]; then
                    readability_scores+=("$score")
                fi
            fi

            # 写作建议检查
            if command -v write-good >/dev/null; then
                local suggestions=$(write-good "$file" 2>/dev/null | wc -l || echo 0)
                total_issues=$((total_issues + suggestions))
            fi

            # 进度显示
            if ((analyzed_files % 20 == 0)); then
                log_info "Analyzed $analyzed_files files..."
            fi
        fi
    done < "$TEMP_DIR/docs_files.txt"

    # 计算平均可读性
    local avg_readability="N/A"
    if [[ ${#readability_scores[@]} -gt 0 ]]; then
        local sum=0
        for score in "${readability_scores[@]}"; do
            sum=$(echo "$sum + $score" | bc -l)
        done
        avg_readability=$(echo "scale=1; $sum / ${#readability_scores[@]}" | bc -l)
    fi

    log_success "Analyzed $analyzed_files files"
    log_info "Writing suggestions found: $total_issues"
    log_info "Average readability score: $avg_readability"

    export WRITING_ISSUES=$total_issues
    export AVG_READABILITY=$avg_readability
}

# 结构分析
analyze_structure() {
    log_header "Documentation Structure Analysis"

    local readme_count=$(wc -l < "$TEMP_DIR/readme_files.txt")
    local changelog_count=$(wc -l < "$TEMP_DIR/changelog_files.txt")
    local docs_folder_count=$(wc -l < "$TEMP_DIR/docs_folder_files.txt")

    # 检查重要文档
    local has_main_readme=false
    local has_contributing=false
    local has_license=false

    if [[ -f "README.md" || -f "readme.md" || -f "Readme.md" ]]; then
        has_main_readme=true
    fi

    if find . -maxdepth 2 -name "CONTRIBUTING*" -o -name "contributing*" -o -name "Contributing*" | grep -q .; then
        has_contributing=true
    fi

    if find . -maxdepth 2 -name "LICENSE*" -o -name "license*" -o -name "License*" | grep -q .; then
        has_license=true
    fi

    # 分析标题层次问题
    local heading_issues=0
    while IFS= read -r file; do
        if [[ -f "$file" ]]; then
            # 检查是否第一个标题跳级
            local first_heading=$(grep -E '^#{1,6} ' "$file" 2>/dev/null | head -1 | grep -o '^#\+' | wc -c 2>/dev/null || echo 1)
            if [[ $first_heading -gt 2 ]]; then
                ((heading_issues++))
            fi
        fi
    done < "$TEMP_DIR/docs_files.txt"

    log_info "README files: $readme_count"
    log_info "Changelog files: $changelog_count"
    log_info "Docs folder files: $docs_folder_count"

    if $has_main_readme; then
        log_success "Main README present"
    else
        log_warning "No main README found"
    fi

    if $has_contributing; then
        log_success "Contributing guide present"
    else
        log_info "No contributing guide found (optional)"
    fi

    if $has_license; then
        log_success "License file present"
    else
        log_info "No license file found (optional)"
    fi

    if [[ $heading_issues -eq 0 ]]; then
        log_success "No heading structure issues"
    else
        log_warning "Found $heading_issues files with heading structure issues"
    fi

    export README_COUNT=$readme_count
    export CHANGELOG_COUNT=$changelog_count
    export DOCS_FOLDER_COUNT=$docs_folder_count
    export HAS_MAIN_README=$has_main_readme
    export HAS_CONTRIBUTING=$has_contributing
    export HAS_LICENSE=$has_license
    export HEADING_ISSUES=$heading_issues
}

# 生成质量报告
generate_report() {
    log_header "Generating Quality Report"

    local report_file="docs_quality_report.md"

    # 计算质量分数
    local score=100

    # 扣分规则
    if [[ "${LINT_ISSUES:-0}" -gt 0 ]]; then
        score=$((score - 10))
    fi

    if [[ "${BROKEN_LINKS:-0}" -gt 0 ]]; then
        score=$((score - 15))
    fi

    if [[ "${WRITING_ISSUES:-0}" -gt 10 ]]; then
        score=$((score - 10))
    fi

    if [[ "${HAS_MAIN_README:-false}" != "true" ]]; then
        score=$((score - 20))
    fi

    if [[ "${HEADING_ISSUES:-0}" -gt 0 ]]; then
        score=$((score - 5))
    fi

    # 确保分数不低于0
    if [[ $score -lt 0 ]]; then
        score=0
    fi

    # 确定等级
    local grade emoji
    if [[ $score -ge 90 ]]; then
        grade="A+"
        emoji="🏆"
    elif [[ $score -ge 80 ]]; then
        grade="A"
        emoji="🥇"
    elif [[ $score -ge 70 ]]; then
        grade="B"
        emoji="🥈"
    elif [[ $score -ge 60 ]]; then
        grade="C"
        emoji="🥉"
    else
        grade="D"
        emoji="❌"
    fi

    # 生成报告
    cat > "$report_file" << EOF
# 📋 Documentation Quality Report

## 📊 Overview

| Metric | Value | Status |
|--------|-------|--------|
| Total Documentation Files | ${TOTAL_FILES:-0} | 📄 |
| Total Size | ${TOTAL_SIZE_KB:-0}KB | 💾 |
| Markdown Lint Issues | ${LINT_ISSUES:-0} | $([ "${LINT_STATUS:-failed}" = "passed" ] && echo "✅" || echo "⚠️") |
| Broken Links | ${BROKEN_LINKS:-0} | $([ "${BROKEN_LINKS:-1}" = "0" ] && echo "✅" || echo "⚠️") |
| Writing Quality Issues | ${WRITING_ISSUES:-0} | $([ "${WRITING_ISSUES:-1}" = "0" ] && echo "✅" || echo "📝") |
| Average Readability Score | ${AVG_READABILITY:-N/A} | 📖 |

## 🏗️ Documentation Structure

| Element | Count | Present |
|---------|-------|---------|
| README Files | ${README_COUNT:-0} | 📖 |
| Changelog Files | ${CHANGELOG_COUNT:-0} | 📅 |
| Docs Folder Files | ${DOCS_FOLDER_COUNT:-0} | 📁 |
| Main README | - | $([ "${HAS_MAIN_README:-false}" = "true" ] && echo "✅" || echo "❌") |
| Contributing Guide | - | $([ "${HAS_CONTRIBUTING:-false}" = "true" ] && echo "✅" || echo "❌") |
| License File | - | $([ "${HAS_LICENSE:-false}" = "true" ] && echo "✅" || echo "❌") |

## 🎯 Quality Score

### Overall Score: ${score}/100 (Grade: ${grade}) ${emoji}

$(if [[ $score -ge 80 ]]; then
    echo "🎉 **Excellent!** Your documentation meets high quality standards."
elif [[ $score -ge 60 ]]; then
    echo "👍 **Good!** Your documentation is solid with room for improvement."
else
    echo "⚠️ **Needs Improvement** Your documentation needs attention to meet quality standards."
fi)

## 🔧 Recommendations

EOF

    # 生成建议
    if [[ "${LINT_ISSUES:-0}" -gt 0 ]]; then
        echo "- 🔧 Fix markdown linting issues for better consistency" >> "$report_file"
    fi

    if [[ "${BROKEN_LINKS:-0}" -gt 0 ]]; then
        echo "- 🔗 Update or remove broken links" >> "$report_file"
    fi

    if [[ "${HAS_MAIN_README:-false}" != "true" ]]; then
        echo "- 📖 Add a comprehensive README.md file" >> "$report_file"
    fi

    if [[ "${HAS_CONTRIBUTING:-false}" != "true" ]]; then
        echo "- 🤝 Consider adding a CONTRIBUTING.md guide" >> "$report_file"
    fi

    if [[ "${WRITING_ISSUES:-0}" -gt 5 ]]; then
        echo "- ✍️ Review and improve writing quality based on suggestions" >> "$report_file"
    fi

    if [[ "${HEADING_ISSUES:-0}" -gt 0 ]]; then
        echo "- 📝 Fix heading structure issues (avoid skipping heading levels)" >> "$report_file"
    fi

    # 添加时间戳
    cat >> "$report_file" << EOF

---
*Report generated on $(date -u '+%Y-%m-%d %H:%M:%S UTC') by local quality check script*
EOF

    log_success "Quality report generated: $report_file"
    log_info "Quality score: $score/100 (Grade: $grade)"

    export QUALITY_SCORE=$score
    export QUALITY_GRADE=$grade
}

# 显示结果摘要
show_summary() {
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))

    log_header "Summary"

    log_info "Execution time: ${duration}s"
    log_info "Files analyzed: ${TOTAL_FILES:-0}"
    log_info "Quality score: ${QUALITY_SCORE:-0}/100 (${QUALITY_GRADE:-N/A})"

    # 显示关键指标
    if [[ "${LINT_STATUS:-failed}" = "passed" ]]; then
        log_success "Markdown linting: PASSED"
    else
        log_error "Markdown linting: FAILED (${LINT_ISSUES:-0} issues)"
    fi

    if [[ "${BROKEN_LINKS:-1}" = "0" ]]; then
        log_success "Link checking: PASSED"
    else
        log_error "Link checking: FAILED (${BROKEN_LINKS:-0} broken links)"
    fi

    if [[ "${QUALITY_SCORE:-0}" -ge 70 ]]; then
        log_success "Overall quality: ACCEPTABLE"
        return 0
    else
        log_error "Overall quality: NEEDS IMPROVEMENT"
        return 1
    fi
}

# 主函数
main() {
    log "${CYAN}${ROCKET} $SCRIPT_NAME v$VERSION${NC}"
    log_info "Working directory: $WORK_DIR"
    log_info "Temporary directory: $TEMP_DIR"

    cd "$WORK_DIR"

    # 执行检查流程
    check_dependencies
    discover_docs
    run_markdown_lint
    check_links
    analyze_writing_quality
    analyze_structure
    generate_report

    # 显示摘要并返回适当的退出码
    if show_summary; then
        log_success "Documentation quality check completed successfully!"
        exit 0
    else
        log_error "Documentation quality check failed!"
        log_info "Check the generated report for detailed recommendations"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
$SCRIPT_NAME v$VERSION

Usage: $0 [DIRECTORY]

Description:
    Local documentation quality check script that validates markdown files,
    checks links, analyzes writing quality, and generates a comprehensive report.

Arguments:
    DIRECTORY    Directory to analyze (default: current directory)

Options:
    -h, --help   Show this help message

Examples:
    $0                    # Check current directory
    $0 /path/to/project   # Check specific directory

Dependencies:
    Required:
    - markdownlint-cli2   (npm install -g markdownlint-cli2)
    - markdown-link-check (npm install -g markdown-link-check)
    - python3

    Optional:
    - write-good          (npm install -g write-good)
    - alex                (npm install -g alex)
    - textstat            (pip install textstat)

Output:
    - Console output with colored progress indicators
    - docs_quality_report.md with detailed analysis
    - Temporary log files for troubleshooting

Exit Codes:
    0    Success (quality score >= 70)
    1    Failure (quality score < 70 or errors)

EOF
}

# 处理命令行参数
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac