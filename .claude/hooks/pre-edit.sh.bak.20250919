#!/bin/bash
# Claude Code Pre-edit Hook - 编辑前检查Perfect21规则

echo "🔍 Perfect21规则检查中..."

# 检查是否在进行Agent选择
if echo "$1" | grep -q "Task\|Agent\|agent"; then
    python3 -c "
import sys
sys.path.insert(0, '/home/xx/dev/Perfect21')
from features.guardian.rule_guardian import get_rule_guardian

guardian = get_rule_guardian()

# 分析输入以确定Agent数量
import re
input_text = '''$1'''
agents = re.findall(r'subagent_type[\"\']\s*:\s*[\"\']([\w-]+)', input_text)

if len(agents) > 0 and len(agents) < 3:
    print('⚠️ Perfect21规则提醒：')
    print(f'  当前只选择了{len(agents)}个Agent')
    print('  规则要求至少3个Agent并行执行')
    print('  建议添加更多相关Agent')
    sys.exit(1)
"
fi

exit 0