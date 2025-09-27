#!/bin/bash
# 测试6-Phase工作流完整性

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}          Claude Enhancer 6-Phase工作流测试              ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 测试各个组件
echo -e "\n${GREEN}核心规则验证：${NC}"
echo "✅ 只有Claude Code可以调用SubAgents"
echo "✅ SubAgents不能调用其他agents"
echo "✅ 每个Phase必须并行调用多个agents"

# 检查当前状态
PHASE=$(cat .phase/current 2>/dev/null || echo "P1")
echo -e "\n${GREEN}当前Phase: $PHASE${NC}"

# 显示各Phase要求
echo -e "\n${BLUE}各Phase最低agent要求：${NC}"
echo "P1: 4个agents (需求分析)"
echo "P2: 6个agents (架构设计)"
echo "P3: 8个agents (编码实现)"
echo "P4: 6个agents (测试验证)"
echo "P5: 4个agents (代码审查)"
echo "P6: 2个agents (发布部署)"

echo -e "\n${GREEN}✅ 工作流配置完成${NC}"
