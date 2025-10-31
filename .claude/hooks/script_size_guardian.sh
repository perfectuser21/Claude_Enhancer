#!/bin/bash
# Script Size Guardian - 防止脚本文件过大
# Purpose: 在AI写入脚本前检查大小，强制模块化
# Version: 1.0.0
# Created: 2025-10-25

set -euo pipefail

# Configuration
readonly MAX_LINES=300          # 最大行数限制
readonly WARNING_LINES=200      # 警告阈值
readonly MAX_SIZE_KB=50         # 最大文件大小(KB)
readonly PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

# 检查是否是脚本文件
is_script_file() {
    local file="$1"
    [[ "$file" =~ \.(sh|bash|py|js)$ ]]
}

# 主检查函数
check_script_size() {
    local file_path="$1"
    local content="${2:-}"

    # 如果不是脚本文件，跳过
    if ! is_script_file "$file_path"; then
        return 0
    fi

    # 计算内容行数
    local line_count
    if [[ -n "$content" ]]; then
        line_count=$(echo "$content" | wc -l)
    else
        if [[ -f "$file_path" ]]; then
            line_count=$(wc -l < "$file_path")
        else
            line_count=0
        fi
    fi

    # 计算大小
    local size_kb=0
    if [[ -n "$content" ]]; then
        size_kb=$(echo "$content" | wc -c | awk '{print int($1/1024)}')
    elif [[ -f "$file_path" ]]; then
        size_kb=$(du -k "$file_path" | cut -f1)
    fi

    # 检查是否超限
    if [[ $line_count -gt $MAX_LINES ]] || [[ $size_kb -gt $MAX_SIZE_KB ]]; then
        cat <<EOF >&2

╔════════════════════════════════════════════════════════════════════╗
║                    🚨 脚本大小超限警告 🚨                          ║
╚════════════════════════════════════════════════════════════════════╝

❌ 文件: $(basename "$file_path")
❌ 行数: ${line_count} 行 (限制: ${MAX_LINES} 行)
❌ 大小: ${size_kb} KB (限制: ${MAX_SIZE_KB} KB)

📋 强制要求：必须模块化拆分

建议拆分方案：
1. 核心逻辑 → $(basename "$file_path" .sh)_core.sh
2. 工具函数 → $(basename "$file_path" .sh)_utils.sh
3. 验证检查 → $(basename "$file_path" .sh)_checks.sh
4. 主入口   → $(basename "$file_path") (仅调用其他模块)

示例结构：
\`\`\`bash
# 主文件 (< 50行)
source "\${SCRIPT_DIR}/$(basename "$file_path" .sh)_core.sh"
source "\${SCRIPT_DIR}/$(basename "$file_path" .sh)_utils.sh"
main "\$@"
\`\`\`

💡 这是强制规则，防止产生难以维护的大文件！

EOF
        return 1
    elif [[ $line_count -gt $WARNING_LINES ]]; then
        echo "⚠️  警告：脚本接近大小限制 (${line_count}/${MAX_LINES} 行)" >&2
    fi

    return 0
}

# 如果直接调用，执行检查
if [[ "${1:-}" == "--check" ]]; then
    check_script_size "${2:-}" "${3:-}"
fi

# Hook集成点
if [[ -n "${CE_HOOK_MODE:-}" ]]; then
    # 从环境变量获取文件路径和内容
    if [[ -n "${CE_TARGET_FILE:-}" ]]; then
        if ! check_script_size "$CE_TARGET_FILE" "${CE_FILE_CONTENT:-}"; then
            exit 1  # 阻止写入
        fi
    fi
fi

exit 0