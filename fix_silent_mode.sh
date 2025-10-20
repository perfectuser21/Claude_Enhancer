#!/bin/bash
# 批量修复hooks的静默模式实现

set -euo pipefail

# 获取所有需要修复的hooks
HOOKS_DIR=".claude/hooks"
FIXED_COUNT=0
SKIPPED_COUNT=0

echo "🔧 开始修复hooks的静默模式实现..."
echo "=================================="

# 已经修复的hooks（跳过）
ALREADY_FIXED=(
    "smart_agent_selector.sh"
    "workflow_auto_start.sh"
    "branch_helper.sh"
)

# 处理每个hook文件
for hook_file in $HOOKS_DIR/*.sh; do
    hook_name=$(basename "$hook_file")

    # 跳过已修复的
    if [[ " ${ALREADY_FIXED[@]} " =~ " ${hook_name} " ]]; then
        echo "✓ 跳过已修复: $hook_name"
        ((SKIPPED_COUNT++))
        continue
    fi

    # 检查是否有输出语句需要包装
    if grep -q 'echo.*>&2' "$hook_file" && ! grep -q 'if.*CE_SILENT_MODE' "$hook_file"; then
        echo "🔨 修复: $hook_name"

        # 创建临时文件
        temp_file="${hook_file}.tmp"
        cp "$hook_file" "$temp_file"

        # 在文件中查找主要的echo输出并添加条件判断
        # 这里使用简单的策略：在第一个实质性echo前添加条件判断

        # 标记是否已添加过条件
        added_condition=false

        # 读取文件并处理
        while IFS= read -r line; do
            # 如果是主要输出部分且还未添加条件
            # 修复regex：转义特殊字符 > 和 &
            if [[ "$line" =~ ^[[:space:]]*echo.*"═".* ]] && [[ "$line" =~ ">&2" ]] && [[ "$added_condition" == false ]]; then
                # 在这个echo前添加条件判断
                cat >> "$temp_file.new" << 'EOF'
    # 根据静默模式决定是否输出
    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
EOF
                echo "$line" >> "$temp_file.new"
                added_condition=true
            else
                echo "$line" >> "$temp_file.new"
            fi
        done < "$temp_file"

        # 如果添加了条件，需要在合适的地方关闭if
        if [[ "$added_condition" == true ]]; then
            # 简单策略：在文件末尾关闭
            echo "    fi # CE_SILENT_MODE check" >> "$temp_file.new"
        fi

        # 只有真正修改了才替换文件
        if [[ "$added_condition" == true ]]; then
            mv "$temp_file.new" "$hook_file"
            ((FIXED_COUNT++))
        else
            rm -f "$temp_file.new"
        fi

        rm -f "$temp_file"
    fi
done

echo ""
echo "=================================="
echo "📊 修复统计："
echo "  • 已修复: $FIXED_COUNT 个hooks"
echo "  • 已跳过: $SKIPPED_COUNT 个hooks"
echo "  • 总计: $((FIXED_COUNT + SKIPPED_COUNT)) 个hooks"
echo ""
echo "✅ 静默模式修复完成！"
