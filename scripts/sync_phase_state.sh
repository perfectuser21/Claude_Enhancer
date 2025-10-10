#!/bin/bash
# Phase状态同步修复工具
# 确保 .phase/current 和 .workflow/ACTIVE 保持一致

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PHASE_FILE="$PROJECT_ROOT/.phase/current"
ACTIVE_FILE="$PROJECT_ROOT/.workflow/ACTIVE"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔍 检查Phase状态一致性..."
echo

# 读取当前状态
if [[ -f "$PHASE_FILE" ]]; then
    PHASE_CURRENT=$(cat "$PHASE_FILE" | tr -d '\n\r')
    echo "📍 .phase/current: $PHASE_CURRENT"
else
    echo -e "${RED}❌ .phase/current 不存在${NC}"
    PHASE_CURRENT=""
fi

if [[ -f "$ACTIVE_FILE" ]]; then
    ACTIVE_PHASE=$(grep -oP 'phase:\s*\K\w+' "$ACTIVE_FILE" 2>/dev/null || echo "")
    echo "📍 .workflow/ACTIVE: $ACTIVE_PHASE"
else
    echo -e "${RED}❌ .workflow/ACTIVE 不存在${NC}"
    ACTIVE_PHASE=""
fi

echo

# 检查一致性
if [[ "$PHASE_CURRENT" == "$ACTIVE_PHASE" && -n "$PHASE_CURRENT" ]]; then
    echo -e "${GREEN}✅ Phase状态一致: $PHASE_CURRENT${NC}"
    exit 0
fi

# 不一致，需要修复
echo -e "${YELLOW}⚠️  Phase状态不一致！${NC}"
echo

# 确定正确的Phase（优先使用 .phase/current）
CORRECT_PHASE=""
if [[ -n "$PHASE_CURRENT" ]]; then
    CORRECT_PHASE="$PHASE_CURRENT"
elif [[ -n "$ACTIVE_PHASE" ]]; then
    CORRECT_PHASE="$ACTIVE_PHASE"
else
    CORRECT_PHASE="P1"  # 默认值
fi

echo "🔧 将同步到: $CORRECT_PHASE"
echo

# 创建必要目录
mkdir -p "$(dirname "$PHASE_FILE")" "$(dirname "$ACTIVE_FILE")"

# 同步更新
echo "$CORRECT_PHASE" > "$PHASE_FILE"
echo "phase: $CORRECT_PHASE" > "$ACTIVE_FILE"

echo -e "${GREEN}✅ Phase状态已同步: $CORRECT_PHASE${NC}"
echo
echo "验证结果："
echo "  .phase/current: $(cat "$PHASE_FILE")"
echo "  .workflow/ACTIVE: $(cat "$ACTIVE_FILE")"
