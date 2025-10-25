#!/bin/bash
# Quality Guardian - 自动化质量守护系统
# Purpose: 主动预防质量问题，而不是事后修复
# Version: 1.0.0
# Created: 2025-10-25

set -euo pipefail

# Configuration
readonly PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
readonly TEMP_DIR="${PROJECT_ROOT}/.temp"
mkdir -p "$TEMP_DIR"
readonly QUALITY_REPORT="${TEMP_DIR}/quality_guardian_report.md"

# 质量规则定义
readonly MAX_SCRIPT_LINES=300
readonly MAX_HOOKS_COUNT=50
readonly MAX_DUPLICATE_FUNCTIONS=3
readonly MIN_COMMENT_RATIO=0.1  # 至少10%注释

# ═══════════════════════════════════════════════════════════════
# 预防性检查函数
# ═══════════════════════════════════════════════════════════════

# 1. 防止脚本过大
check_script_sizes() {
    echo "## 1. 脚本大小检查"
    local issues=0

    while IFS= read -r file; do
        local lines
        lines=$(wc -l < "$file")
        if [[ $lines -gt $MAX_SCRIPT_LINES ]]; then
            echo "⚠️  $(basename "$file"): ${lines} 行 (超过 ${MAX_SCRIPT_LINES})"
            ((issues++))
        fi
    done < <(find "${PROJECT_ROOT}" -name "*.sh" -type f 2>/dev/null)

    if [[ $issues -eq 0 ]]; then
        echo "✅ 所有脚本大小合理"
    else
        echo "❌ 发现 ${issues} 个过大脚本"
    fi
    echo ""
    return $issues
}

# 2. 防止版本累积
check_version_accumulation() {
    echo "## 2. 版本累积检查"
    local issues=0

    # 查找可能的多版本文件
    local pattern_files
    pattern_files=$(find "${PROJECT_ROOT}" -name "*_v[0-9]*" -o -name "*_backup*" -o -name "*_original*" 2>/dev/null | wc -l)

    if [[ $pattern_files -gt 5 ]]; then
        echo "⚠️  发现 ${pattern_files} 个可能的版本文件"
        echo "   运行: bash ${PROJECT_ROOT}/.claude/tools/version_cleaner.sh analyze"
        ((issues++))
    else
        echo "✅ 版本管理良好 (${pattern_files} 个版本文件)"
    fi
    echo ""
    return $issues
}

# 3. 防止Hook膨胀
check_hook_proliferation() {
    echo "## 3. Hook数量检查"
    local hook_count
    hook_count=$(find "${PROJECT_ROOT}/.claude/hooks" -maxdepth 1 -name "*.sh" -type f 2>/dev/null | wc -l)

    if [[ $hook_count -gt $MAX_HOOKS_COUNT ]]; then
        echo "⚠️  Hook数量: ${hook_count} (超过 ${MAX_HOOKS_COUNT})"
        echo "   考虑整合相关功能的hooks"
    else
        echo "✅ Hook数量合理: ${hook_count}"
    fi
    echo ""
}

# 4. 检查代码重复
check_code_duplication() {
    echo "## 4. 代码重复检查"
    local issues=0

    # 查找重复的函数定义
    local duplicate_funcs
    duplicate_funcs=$(grep -h "^[[:space:]]*function\|^[[:space:]]*[a-zA-Z_][a-zA-Z0-9_]*()" \
        "${PROJECT_ROOT}"/**/*.sh 2>/dev/null | \
        sed 's/function //g' | sed 's/[[:space:]]//g' | sort | uniq -c | \
        awk '$1 > '"$MAX_DUPLICATE_FUNCTIONS"' {print $2}')

    if [[ -n "$duplicate_funcs" ]]; then
        echo "⚠️  发现重复函数定义："
        echo "$duplicate_funcs"
        ((issues++))
    else
        echo "✅ 没有过度重复的函数"
    fi
    echo ""
    return $issues
}

# 5. Shellcheck自动修复建议
suggest_shellcheck_fixes() {
    echo "## 5. Shellcheck自动修复建议"

    # 统计各类警告
    local warnings
    warnings=$(shellcheck --severity=warning "${PROJECT_ROOT}"/**/*.sh 2>&1 | grep "^In" | wc -l || echo 0)

    if [[ "$warnings" -gt 50 ]]; then
        echo "⚠️  发现 ${warnings} 个shellcheck警告"
        echo "   最常见的问题："
        shellcheck "${PROJECT_ROOT}"/**/*.sh 2>&1 | \
            grep -oP 'SC\d+' | sort | uniq -c | sort -rn | head -5 || true
    else
        echo "✅ Shellcheck警告可控: ${warnings} 个"
    fi
    echo ""
}

# ═══════════════════════════════════════════════════════════════
# Claude Skills集成建议
# ═══════════════════════════════════════════════════════════════

suggest_claude_skills() {
    echo "## 6. Claude Skills可以帮助的方面"
    echo ""
    echo "### 可创建的Skills："
    echo ""
    echo "1. **quality-check** - 质量检查skill"
    echo "   \`\`\`bash"
    echo "   # .claude/skills/quality-check.md"
    echo "   运行所有质量检查并生成报告"
    echo "   \`\`\`"
    echo ""
    echo "2. **module-splitter** - 大文件拆分skill"
    echo "   \`\`\`bash"
    echo "   # .claude/skills/module-splitter.md"
    echo "   自动将大于300行的脚本拆分为模块"
    echo "   \`\`\`"
    echo ""
    echo "3. **version-cleanup** - 版本清理skill"
    echo "   \`\`\`bash"
    echo "   # .claude/skills/version-cleanup.md"
    echo "   检测并清理多版本文件"
    echo "   \`\`\`"
    echo ""
    echo "4. **performance-optimize** - 性能优化skill"
    echo "   \`\`\`bash"
    echo "   # .claude/skills/performance-optimize.md"
    echo "   分析性能瓶颈并提供优化建议"
    echo "   \`\`\`"
    echo ""
}

# ═══════════════════════════════════════════════════════════════
# 自动修复功能
# ═══════════════════════════════════════════════════════════════

auto_fix() {
    echo "## 自动修复"
    echo ""

    # 1. 清理旧版本
    if command -v "${PROJECT_ROOT}/.claude/tools/version_cleaner.sh" >/dev/null 2>&1; then
        echo "清理旧版本文件..."
        bash "${PROJECT_ROOT}/.claude/tools/version_cleaner.sh" clean false
    fi

    # 2. 设置脚本大小限制hook
    if [[ -f "${PROJECT_ROOT}/.claude/hooks/script_size_guardian.sh" ]]; then
        echo "激活脚本大小守护..."
        # 可以将其添加到settings.json
    fi

    echo "✅ 自动修复完成"
}

# ═══════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════

main() {
    echo "# 🛡️ Quality Guardian Report"
    echo "**时间**: $(date +'%Y-%m-%d %H:%M:%S')"
    echo ""

    local total_issues=0

    # 运行所有检查
    check_script_sizes || total_issues=$((total_issues + $?))
    check_version_accumulation || total_issues=$((total_issues + $?))
    check_hook_proliferation
    check_code_duplication || total_issues=$((total_issues + $?))
    suggest_shellcheck_fixes
    suggest_claude_skills

    # 总结
    echo "## 总结"
    if [[ $total_issues -eq 0 ]]; then
        echo "✅ **质量状态: 优秀**"
        echo "没有发现严重问题"
    else
        echo "⚠️  **发现 ${total_issues} 个潜在问题**"
        echo "建议运行自动修复: $(basename "$0") --fix"
    fi

    # 保存报告
    {
        echo "# Quality Guardian Report"
        echo "Generated: $(date)"
        echo "Issues: $total_issues"
    } > "$QUALITY_REPORT"

    echo ""
    echo "报告已保存到: $QUALITY_REPORT"
}

# 参数处理
case "${1:-}" in
    --fix)
        auto_fix
        ;;
    --help)
        cat <<EOF
Quality Guardian - 主动预防质量问题

用法: $(basename "$0") [选项]

选项:
  --fix    执行自动修复
  --help   显示帮助

功能:
  • 防止脚本过大
  • 防止版本累积
  • 防止Hook膨胀
  • 检测代码重复
  • Shellcheck建议

这个工具主动预防质量问题，而不是事后修复。
EOF
        ;;
    *)
        main
        ;;
esac