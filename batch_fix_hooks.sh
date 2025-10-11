#!/bin/bash
# 批量修复剩余hooks的静默模式

cd "/home/xx/dev/Claude Enhancer 5.0/.claude/hooks"

# 待修复的hooks列表
HOOKS_TO_FIX=(
    "git_status_monitor.sh"
    "implementation_orchestrator.sh"
    "optimized_performance_monitor.sh"
    "parallel_agent_highlighter.sh"
    "performance_monitor.sh"
    "requirements_validator.sh"
    "review_preparation.sh"
    "smart_cleanup_advisor.sh"
    "smart_git_workflow.sh"
    "task_type_detector.sh"
    "testing_coordinator.sh"
    "workflow_auto_trigger_integration.sh"
    "workflow_executor_integration.sh"
)

echo "🔧 批量修复剩余hooks的静默模式"
echo "================================"
echo

for hook in "${HOOKS_TO_FIX[@]}"; do
    if [[ ! -f "$hook" ]]; then
        echo "⚠️ 文件不存在: $hook"
        continue
    fi

    echo "修复: $hook"

    # 创建临时文件
    temp_file="${hook}.tmp"

    # 读取文件并处理
    while IFS= read -r line; do
        # 跳过shebang和auto-mode检测部分
        if [[ "$line" == "#!/bin/bash" ]] || \
           [[ "$line" == "# Auto-mode detection" ]] || \
           [[ "$line" == 'if [[ "$CE_AUTO_MODE" == "true" ]]; then' ]] || \
           [[ "$line" == '    export CE_SILENT_MODE=true' ]] || \
           [[ "$line" == 'fi' && "$prev_line" == '    export CE_SILENT_MODE=true' ]]; then
            echo "$line" >> "$temp_file"
            prev_line="$line"
            continue
        fi

        # 处理echo语句
        if [[ "$line" =~ ^[[:space:]]*echo[[:space:]] ]] && \
           ! [[ "$line" =~ 'CE_SILENT_MODE' ]] && \
           ! [[ "$line" =~ '>/dev/null' ]] && \
           ! [[ "$line" =~ '>>' ]] && \
           ! [[ "$line" =~ '\$' && "$line" =~ 'echo' ]]; then
            # 这是一个需要包装的echo语句
            # 获取缩进
            indent=$(echo "$line" | sed 's/^\([[:space:]]*\).*/\1/')

            # 如果还没有添加过条件判断，添加它
            if ! grep -q "CE_SILENT_MODE.*!=" "$temp_file"; then
                echo "${indent}if [[ \"\${CE_SILENT_MODE:-false}\" != \"true\" ]]; then" >> "$temp_file"
                echo "$line" >> "$temp_file"
                echo "${indent}elif [[ \"\${CE_COMPACT_OUTPUT:-false}\" == \"true\" ]]; then" >> "$temp_file"
                # 提取简短信息
                if [[ "$line" =~ "echo.*\".*\"" ]]; then
                    # 生成紧凑输出
                    hook_name=$(basename "$hook" .sh | sed 's/_/ /g' | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1' | sed 's/ //')
                    echo "${indent}    echo \"[${hook_name:0:10}] Active\"" >> "$temp_file"
                fi
                echo "${indent}fi" >> "$temp_file"
                wrapped=true
            else
                # 已经有条件判断了，直接输出
                echo "$line" >> "$temp_file"
            fi
        else
            echo "$line" >> "$temp_file"
        fi

        prev_line="$line"
    done < "$hook"

    # 替换原文件
    mv "$temp_file" "$hook"
    echo "  ✅ 完成"
done

echo
echo "✨ 批量修复完成！"