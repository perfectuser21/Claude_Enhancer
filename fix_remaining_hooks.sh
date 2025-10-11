#!/bin/bash
# 修复剩余hooks的静默模式实现

cd "/home/xx/dev/Claude Enhancer 5.0/.claude/hooks"

# 通用的修复函数
fix_hook() {
    local hook="$1"
    echo "修复: $hook"

    # 创建Python脚本来处理
    python3 << 'EOF'
import sys
import re

hook_file = "''' + hook + '''"

with open(hook_file, 'r') as f:
    lines = f.readlines()

output = []
i = 0
while i < len(lines):
    line = lines[i]

    # 保留shebang和auto-mode部分
    if i < 5:
        output.append(line)
        i += 1
        continue

    # 检查是否是echo语句（不在条件内）
    if (re.match(r'^[^#]*echo\s+["\']', line.strip()) and
        'CE_SILENT_MODE' not in line and
        '>/dev/null' not in line and
        '>>' not in line and
        not any(x in lines[max(0, i-3):i] for x in ['CE_SILENT_MODE', 'if [[ "${CE_SILENT_MODE'])):

        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent

        # 包装echo语句
        output.append(f'{indent_str}if [[ "${{CE_SILENT_MODE:-false}}" != "true" ]]; then\n')
        output.append(line)

        # 查找后续的echo语句
        j = i + 1
        while j < len(lines) and (lines[j].strip().startswith('echo ') or lines[j].strip() == ''):
            if lines[j].strip().startswith('echo '):
                output.append(lines[j])
                j += 1
            elif lines[j].strip() == '':
                output.append(lines[j])
                j += 1
            else:
                break

        output.append(f'{indent_str}fi\n')
        i = j
    else:
        output.append(line)
        i += 1

with open(hook_file, 'w') as f:
    f.writelines(output)
EOF

    echo "  ✅ 完成"
}

# 需要修复的hooks
REMAINING_HOOKS=(
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

echo "🔧 修复剩余的hooks"
echo "=================="
echo

for hook in "${REMAINING_HOOKS[@]}"; do
    if [[ -f "$hook" ]]; then
        fix_hook "$hook"
    else
        echo "⚠️ 文件不存在: $hook"
    fi
done

echo
echo "✨ 修复完成！"