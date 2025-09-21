#!/bin/bash
# Claude Enhancer 真实验证器
# 集成bash验证和Python追踪

set -e

# 读取输入
INPUT=$(cat)

# 执行Python追踪器
echo "$INPUT" | python3 /home/xx/dev/Perfect21/execution_tracker.py 2>&1

# 执行bash验证（获取详细信息）
echo "$INPUT" | /home/xx/dev/Perfect21/real_validation_system.sh 2>&1

# 输出原始内容
echo "$INPUT"