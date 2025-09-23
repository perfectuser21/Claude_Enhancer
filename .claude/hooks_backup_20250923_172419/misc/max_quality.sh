#!/bin/bash
# Claude Max 20X Quality Mode
# 最高质量，不计成本

set -e

INPUT=$(cat)

# 使用Max Quality控制器
RESULT=$(echo "$INPUT" | python3 /home/xx/dev/Claude Enhancer/max_quality_controller.py 2>&1)

echo "$RESULT"
exit 0