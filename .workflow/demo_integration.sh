#!/bin/bash

# Demo: Gate Validator Integration
# 演示如何在工作流中集成Gate验证器
# 版本：5.0.0 | 更新：2025-09-26

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE_VALIDATOR="$SCRIPT_DIR/gate_validator.sh"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Gate Validator 集成演示 ===${NC}"
echo

# 1. 显示当前状态
echo -e "${YELLOW}📊 当前状态:${NC}"
"$GATE_VALIDATOR" --status
echo

# 2. 演示Phase验证
echo -e "${YELLOW}🔍 演示Phase验证:${NC}"

phases=("P1" "P2" "P3" "P4" "P5" "P6")
agent_counts=(4 6 8 6 4 2)

for i in "${!phases[@]}"; do
    phase="${phases[i]}"
    count="${agent_counts[i]}"

    echo -e "${BLUE}验证 $phase 阶段 (使用 $count agents)...${NC}"

    if "$GATE_VALIDATOR" "$phase" "$count" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ $phase 验证通过${NC}"
    else
        echo -e "  ${RED}❌ $phase 验证失败${NC}"
    fi
done

echo

# 3. 演示并行限制违规
echo -e "${YELLOW}⚠️  演示并行限制违规:${NC}"
echo -e "${BLUE}尝试在P6阶段使用5个agents (限制为2)...${NC}"

if "$GATE_VALIDATOR" "P6" "5" >/dev/null 2>&1; then
    echo -e "  ${RED}❌ 应该失败但通过了!${NC}"
else
    echo -e "  ${GREEN}✅ 正确检测到并行限制违规${NC}"
fi

echo

# 4. 显示最终状态
echo -e "${YELLOW}📈 最终状态:${NC}"
"$GATE_VALIDATOR" --status

echo
echo -e "${GREEN}🎉 演示完成!${NC}"
echo -e "${BLUE}💡 集成建议:${NC}"
echo "   1. 在Agent选择前调用验证器检查并行限制"
echo "   2. 在Phase完成后调用验证器检查产出和条件"
echo "   3. 使用 --verbose 模式获得详细的调试信息"
echo "   4. 检查生成的报告文件了解详细结果"