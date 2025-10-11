#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 质量门禁 - 安全的质量检查

# 统一日志记录（激活追踪）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/claude_hooks.log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date +'%F %T') [quality_gate.sh] triggered by ${USER:-claude}" >> "$LOG_FILE"

set -e

# 读取输入
INPUT=$(cat)

# 检查基本质量标准
check_quality() {
    local task="$1"
    local warnings=()
    local score=100

    # 1. 检查任务描述长度
    if [ ${#task} -lt 10 ]; then
        warnings+=("⚠️ 任务描述过短 (${#task}字符)")
        ((score-=10))
    fi

    # 2. 检查是否包含基本信息
    if ! echo "$task" | grep -qE "(实现|修复|优化|测试|部署)"; then
        warnings+=("💡 建议包含明确的动作词")
        ((score-=5))
    fi

    # 3. 安全检查 - 禁止危险操作
    if echo "$task" | grep -qE "(删除全部|rm -rf|格式化|destroy)"; then
        warnings+=("🚨 检测到潜在危险操作")
        ((score-=50))
    fi

    # 根据静默模式决定是否输出质量报告
    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
        echo "🎯 质量评分: ${score}/100" >&2

        if [ ${#warnings[@]} -gt 0 ]; then
            echo "📋 质量建议:" >&2
            printf "  %s\n" "${warnings[@]}" >&2
        fi
    elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
        # 紧凑模式：一行输出
        echo "[Quality] Score: ${score}/100" >&2
    fi
    # CE_SILENT_MODE=true时完全不输出

    if [ $score -ge 70 ]; then
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "✅ 质量检查通过" >&2
        fi
        return 0
    else
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "⚠️ 质量评分较低，建议优化" >&2
        fi
        return 0  # 不阻止执行，只给建议
    fi
}

# 提取任务描述
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")

if [ -n "$TASK_DESC" ]; then
    check_quality "$TASK_DESC"
fi

# 输出原始输入（不修改）
echo "$INPUT"
exit 0
