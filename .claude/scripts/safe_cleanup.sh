#!/bin/bash

# Claude Enhancer 安全清理脚本
# 用途：列出垃圾文件并确认后清理

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}🧹 Claude Enhancer 安全清理工具${NC}"
echo "=================================="

# 扫描垃圾文件
echo -e "\n${YELLOW}🔍 扫描垃圾文件...${NC}\n"

# Python缓存
PYTHON_CACHE=$(find . \( -name "*.pyc" -o -name "*.pyo" -o -type d -name "__pycache__" \) -not -path "./.git/*" 2>/dev/null)
if [ ! -z "$PYTHON_CACHE" ]; then
    echo -e "${BLUE}Python缓存文件:${NC}"
    echo "$PYTHON_CACHE" | head -10
    PYTHON_COUNT=$(echo "$PYTHON_CACHE" | wc -l)
    [ $PYTHON_COUNT -gt 10 ] && echo "... 还有 $((PYTHON_COUNT-10)) 个文件"
    echo
fi

# 备份文件
BACKUP_FILES=$(find . \( -name "*.bak" -o -name "*.backup" -o -name "*.old" \) -not -path "./.git/*" 2>/dev/null)
if [ ! -z "$BACKUP_FILES" ]; then
    echo -e "${BLUE}备份文件:${NC}"
    echo "$BACKUP_FILES" | head -10
    BACKUP_COUNT=$(echo "$BACKUP_FILES" | wc -l)
    [ $BACKUP_COUNT -gt 10 ] && echo "... 还有 $((BACKUP_COUNT-10)) 个文件"
    echo
fi

# 临时文件
TEMP_FILES=$(find . \( -name "*.tmp" -o -name "*.temp" -o -name "*.swp" -o -name "*~" \) -not -path "./.git/*" 2>/dev/null)
if [ ! -z "$TEMP_FILES" ]; then
    echo -e "${BLUE}临时文件:${NC}"
    echo "$TEMP_FILES" | head -10
    TEMP_COUNT=$(echo "$TEMP_FILES" | wc -l)
    [ $TEMP_COUNT -gt 10 ] && echo "... 还有 $((TEMP_COUNT-10)) 个文件"
    echo
fi

# 测试文件
TEST_FILES=$(find . \( -name "test_*.txt" -o -name "test_*.md" -o -name "*_test_output.*" \) -not -path "./.git/*" 2>/dev/null)
if [ ! -z "$TEST_FILES" ]; then
    echo -e "${BLUE}测试输出文件:${NC}"
    echo "$TEST_FILES" | head -10
    TEST_COUNT=$(echo "$TEST_FILES" | wc -l)
    [ $TEST_COUNT -gt 10 ] && echo "... 还有 $((TEST_COUNT-10)) 个文件"
    echo
fi

# 系统文件
SYSTEM_FILES=$(find . \( -name ".DS_Store" -o -name "Thumbs.db" \) 2>/dev/null)
if [ ! -z "$SYSTEM_FILES" ]; then
    echo -e "${BLUE}系统生成文件:${NC}"
    echo "$SYSTEM_FILES"
    echo
fi

# 统计总数
TOTAL=0
[ ! -z "$PYTHON_CACHE" ] && TOTAL=$((TOTAL + $(echo "$PYTHON_CACHE" | wc -l)))
[ ! -z "$BACKUP_FILES" ] && TOTAL=$((TOTAL + $(echo "$BACKUP_FILES" | wc -l)))
[ ! -z "$TEMP_FILES" ] && TOTAL=$((TOTAL + $(echo "$TEMP_FILES" | wc -l)))
[ ! -z "$TEST_FILES" ] && TOTAL=$((TOTAL + $(echo "$TEST_FILES" | wc -l)))
[ ! -z "$SYSTEM_FILES" ] && TOTAL=$((TOTAL + $(echo "$SYSTEM_FILES" | wc -l)))

if [ $TOTAL -eq 0 ]; then
    echo -e "${GREEN}✅ 没有垃圾文件需要清理！${NC}"
    exit 0
fi

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${RED}📊 共发现 $TOTAL 个垃圾文件${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 询问用户
echo
read -p "$(echo -e ${YELLOW}确认删除这些文件吗？[y/N]:${NC}) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}❌ 取消清理${NC}"
    exit 0
fi

# 执行清理
echo -e "\n${GREEN}🚀 开始清理...${NC}"

# 清理各类文件
[ ! -z "$PYTHON_CACHE" ] && echo "$PYTHON_CACHE" | xargs rm -rf 2>/dev/null && echo -e "${GREEN}✅ Python缓存已清理${NC}"
[ ! -z "$BACKUP_FILES" ] && echo "$BACKUP_FILES" | xargs rm -f 2>/dev/null && echo -e "${GREEN}✅ 备份文件已清理${NC}"
[ ! -z "$TEMP_FILES" ] && echo "$TEMP_FILES" | xargs rm -f 2>/dev/null && echo -e "${GREEN}✅ 临时文件已清理${NC}"
[ ! -z "$TEST_FILES" ] && echo "$TEST_FILES" | xargs rm -f 2>/dev/null && echo -e "${GREEN}✅ 测试文件已清理${NC}"
[ ! -z "$SYSTEM_FILES" ] && echo "$SYSTEM_FILES" | xargs rm -f 2>/dev/null && echo -e "${GREEN}✅ 系统文件已清理${NC}"

# 清理空目录
find . -type d -empty -not -path "./.git/*" -delete 2>/dev/null || true

echo -e "\n${GREEN}🎉 清理完成！已删除 $TOTAL 个垃圾文件${NC}"

# 显示当前项目大小
CURRENT_SIZE=$(du -sh . 2>/dev/null | cut -f1)
echo -e "${GREEN}💾 当前项目大小: $CURRENT_SIZE${NC}"