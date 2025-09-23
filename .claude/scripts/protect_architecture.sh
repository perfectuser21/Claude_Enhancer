#!/bin/bash

# Claude Enhancer架构文档保护脚本
# 用途：检查ARCHITECTURE目录的完整性，确保重要文档不被删除

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ARCH_DIR="$PROJECT_ROOT/.claude/ARCHITECTURE"

echo "🔒 Claude Enhancer架构保护检查"
echo "================================"

# 检查ARCHITECTURE目录是否存在
if [ ! -d "$ARCH_DIR" ]; then
    echo -e "${RED}❌ 严重错误：ARCHITECTURE目录不存在！${NC}"
    echo "   路径：$ARCH_DIR"
    echo "   这是永久保护目录，必须存在！"
    exit 1
fi

# 定义必须存在的核心文件
declare -a REQUIRED_FILES=(
    "README.md"
    "v2.0-FOUNDATION.md"
    "LAYER-DEFINITION.md"
    "GROWTH-STRATEGY.md"
    "NAMING-CONVENTIONS.md"
)

# 定义必须存在的目录
declare -a REQUIRED_DIRS=(
    "decisions"
)

# 检查文件完整性
echo "检查核心文档..."
MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$ARCH_DIR/$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ 缺失: $file${NC}"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

# 检查目录完整性
echo -e "\n检查子目录..."
MISSING_DIRS=0
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$ARCH_DIR/$dir" ]; then
        # 计算目录中的文件数
        FILE_COUNT=$(find "$ARCH_DIR/$dir" -type f -name "*.md" | wc -l)
        echo -e "${GREEN}✅ $dir/ (包含 $FILE_COUNT 个文档)${NC}"
    else
        echo -e "${RED}❌ 缺失: $dir/${NC}"
        MISSING_DIRS=$((MISSING_DIRS + 1))
    fi
done

# 检查decisions目录中的ADR文档
echo -e "\n检查架构决策记录(ADR)..."
if [ -d "$ARCH_DIR/decisions" ]; then
    ADR_COUNT=$(ls -1 "$ARCH_DIR/decisions"/*.md 2>/dev/null | wc -l)
    if [ "$ADR_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ 找到 $ADR_COUNT 个ADR文档${NC}"
        ls -1 "$ARCH_DIR/decisions"/*.md | while read -r adr; do
            basename "$adr"
        done | sed 's/^/   - /'
    else
        echo -e "${YELLOW}⚠️ decisions目录为空${NC}"
    fi
fi

# 检查文件大小（确保不是空文件）
echo -e "\n检查文档完整性..."
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$ARCH_DIR/$file" ]; then
        SIZE=$(stat -f%z "$ARCH_DIR/$file" 2>/dev/null || stat -c%s "$ARCH_DIR/$file" 2>/dev/null)
        if [ "$SIZE" -lt 100 ]; then
            echo -e "${YELLOW}⚠️ $file 可能不完整 (仅 $SIZE 字节)${NC}"
        fi
    fi
done

# 统计总体状态
echo -e "\n================================"
TOTAL_ISSUES=$((MISSING_FILES + MISSING_DIRS))

if [ "$TOTAL_ISSUES" -eq 0 ]; then
    echo -e "${GREEN}✅ 架构文档完整性检查通过！${NC}"
    echo "所有核心文档都存在且受保护。"

    # 显示统计信息
    TOTAL_SIZE=$(du -sh "$ARCH_DIR" | cut -f1)
    TOTAL_FILES=$(find "$ARCH_DIR" -type f | wc -l)
    echo -e "\n📊 统计信息："
    echo "   - 文档总数：$TOTAL_FILES"
    echo "   - 占用空间：$TOTAL_SIZE"
    echo "   - 最后检查：$(date '+%Y-%m-%d %H:%M:%S')"
else
    echo -e "${RED}❌ 发现 $TOTAL_ISSUES 个问题！${NC}"
    echo "请立即恢复缺失的架构文档。"
    echo ""
    echo "恢复方法："
    echo "1. 从Git历史恢复："
    echo "   git checkout HEAD -- .claude/ARCHITECTURE/"
    echo "2. 从备份恢复"
    echo "3. 重新创建缺失文档"
    exit 1
fi

# 创建保护标记文件
echo "$(date '+%Y-%m-%d %H:%M:%S')" > "$ARCH_DIR/.last_check"

echo -e "\n💡 提示：此目录受永久保护，请勿删除任何文件。"