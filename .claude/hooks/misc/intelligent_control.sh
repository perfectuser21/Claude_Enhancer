#!/bin/bash
# Claude Enhancer 智能控制Hook
# 保留用户原始意图，只补充必要的agents

set -e

INPUT=$(cat)

# 使用智能控制器
RESULT=$(echo "$INPUT" | python3 /home/xx/dev/Perfect21/intelligent_controller.py 2>&1)

# 输出结果
echo "$RESULT"

# 总是返回0让执行继续
exit 0