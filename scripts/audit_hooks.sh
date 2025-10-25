#!/bin/bash
# Claude Hooks审计脚本
# 用途：识别真实有效的hooks vs 空架子/废弃hooks

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.claude/hooks"
SETTINGS_FILE="$PROJECT_ROOT/.claude/settings.json"
OUTPUT_FILE="$PROJECT_ROOT/.temp/hooks_audit_result.md"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo "# Claude Hooks 审计报告" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "**生成时间**: $(date '+%Y-%m-%d %H:%M:%S')" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "## 统计摘要" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 统计变量
total_hooks=0
registered_hooks=0
unregistered_hooks=0
empty_hooks=0
small_hooks=0
large_hooks=0
likely_valid=0
likely_empty=0

echo "| Hook名称 | 行数 | 逻辑行 | 注册状态 | 有退出逻辑 | 评估 |" >> "$OUTPUT_FILE"
echo "|----------|------|--------|----------|------------|------|" >> "$OUTPUT_FILE"

# 遍历所有hooks
for hook_file in "$HOOKS_DIR"/*.sh; do
    if [[ ! -f "$hook_file" ]]; then
        continue
    fi

    ((total_hooks++))
    hook_name=$(basename "$hook_file")

    # 1. 统计总行数
    total_lines=$(wc -l < "$hook_file")

    # 2. 统计逻辑行数（排除注释和空行）
    logic_lines=$(grep -v "^[[:space:]]*#" "$hook_file" | grep -v "^[[:space:]]*$" | wc -l || echo "0")

    # 3. 检查是否在settings.json中注册
    if grep -q "\"$hook_name\"" "$SETTINGS_FILE" 2>/dev/null; then
        registration_status="✅ 已注册"
        ((registered_hooks++))
    else
        registration_status="❌ 未注册"
        ((unregistered_hooks++))
    fi

    # 4. 检查是否有exit/return语句
    if grep -qE "exit [0-9]|return [0-9]" "$hook_file" 2>/dev/null; then
        has_exit="✅"
    else
        has_exit="❌"
    fi

    # 5. 评估hook有效性
    if [[ $logic_lines -lt 20 ]]; then
        assessment="⚠️ 可能空壳"
        ((likely_empty++))
        ((small_hooks++))
    elif [[ $logic_lines -gt 100 ]]; then
        assessment="✅ 有效"
        ((likely_valid++))
        ((large_hooks++))
    else
        if [[ "$registration_status" == "✅ 已注册" ]] && [[ "$has_exit" == "✅" ]]; then
            assessment="✅ 有效"
            ((likely_valid++))
        else
            assessment="🟡 需检查"
        fi
    fi

    # 输出到文件
    echo "| $hook_name | $total_lines | $logic_lines | $registration_status | $has_exit | $assessment |" >> "$OUTPUT_FILE"
done

echo "" >> "$OUTPUT_FILE"
echo "## 统计结果" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "- **总计hooks**: $total_hooks" >> "$OUTPUT_FILE"
echo "- **已注册**: $registered_hooks" >> "$OUTPUT_FILE"
echo "- **未注册**: $unregistered_hooks" >> "$OUTPUT_FILE"
echo "- **可能有效**: $likely_valid" >> "$OUTPUT_FILE"
echo "- **可能空壳**: $likely_empty" >> "$OUTPUT_FILE"
echo "- **小型hooks** (<20逻辑行): $small_hooks" >> "$OUTPUT_FILE"
echo "- **大型hooks** (>100逻辑行): $large_hooks" >> "$OUTPUT_FILE"

echo "" >> "$OUTPUT_FILE"
echo "## 详细分析" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 分析每个注册的hook组
echo "### PrePrompt Hooks" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
if command -v jq >/dev/null 2>&1; then
    jq -r '.hooks.PrePrompt[]' "$SETTINGS_FILE" 2>/dev/null | while read -r hook_path; do
        hook_name=$(basename "$hook_path")
        if [[ -f "$HOOKS_DIR/$hook_name" ]]; then
            lines=$(wc -l < "$HOOKS_DIR/$hook_name")
            echo "- ✅ $hook_name ($lines行)" >> "$OUTPUT_FILE"
        else
            echo "- ❌ $hook_name (文件不存在)" >> "$OUTPUT_FILE"
        fi
    done
fi

echo "" >> "$OUTPUT_FILE"
echo "### PreToolUse Hooks" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
if command -v jq >/dev/null 2>&1; then
    jq -r '.hooks.PreToolUse[]' "$SETTINGS_FILE" 2>/dev/null | while read -r hook_path; do
        hook_name=$(basename "$hook_path")
        if [[ -f "$HOOKS_DIR/$hook_name" ]]; then
            lines=$(wc -l < "$HOOKS_DIR/$hook_name")
            echo "- ✅ $hook_name ($lines行)" >> "$OUTPUT_FILE"
        else
            echo "- ❌ $hook_name (文件不存在)" >> "$OUTPUT_FILE"
        fi
    done
fi

echo "" >> "$OUTPUT_FILE"
echo "### 未注册但存在的Hooks（可能是废弃的）" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

for hook_file in "$HOOKS_DIR"/*.sh; do
    if [[ ! -f "$hook_file" ]]; then
        continue
    fi
    hook_name=$(basename "$hook_file")
    if ! grep -q "\"$hook_name\"" "$SETTINGS_FILE" 2>/dev/null; then
        lines=$(wc -l < "$hook_file")
        echo "- ⚠️ $hook_name ($lines行) - 未注册" >> "$OUTPUT_FILE"
    fi
done

# 输出结果
echo ""
echo -e "${GREEN}✅ 审计完成！${NC}"
echo ""
echo -e "${CYAN}报告已保存到：${NC} $OUTPUT_FILE"
echo ""
echo -e "${YELLOW}摘要：${NC}"
echo "  总计hooks: $total_hooks"
echo "  已注册: $registered_hooks"
echo "  未注册: $unregistered_hooks"
echo "  可能有效: $likely_valid"
echo "  可能空壳: $likely_empty"

# 显示前10行结果
echo ""
echo -e "${CYAN}前10个hooks：${NC}"
head -20 "$OUTPUT_FILE"