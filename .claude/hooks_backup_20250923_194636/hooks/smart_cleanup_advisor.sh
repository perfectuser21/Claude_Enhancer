#!/bin/bash
# Claude Enhancer - 智能清理顾问
# 分级清理策略：安全 → 临时 → 冗余 → 深度

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}🧹 智能清理顾问${NC}"
echo "════════════════════════════════════════"

# Level 1: 安全清理（无风险）
LEVEL1_TEMP=$(find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name "*~" -o -name ".DS_Store" -o -name "Thumbs.db" \) 2>/dev/null | wc -l)
LEVEL1_LOGS=$(find . -name "*.log" -type f -mtime +7 2>/dev/null | wc -l)
LEVEL1_CACHE=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
LEVEL1_TOTAL=$((LEVEL1_TEMP + LEVEL1_LOGS + LEVEL1_CACHE))

# Level 2: 临时文件（低风险）
LEVEL2_TMP=$(find /tmp -name "*claude*" -o -name "*perfect21*" 2>/dev/null | wc -l)
LEVEL2_TEST=$(ls -1 *test*.sh *diagnostic*.py *validation*.sh 2>/dev/null | wc -l)
LEVEL2_DEMO=$(ls -1 *demo*.* *example*.* *sample*.* 2>/dev/null | wc -l)
LEVEL2_TOTAL=$((LEVEL2_TMP + LEVEL2_TEST + LEVEL2_DEMO))

# Level 3: 冗余文件（中风险）
LEVEL3_BACKUP=$(find .claude -name "*.bak*" -o -name "*backup*" -o -name "*.old" 2>/dev/null | wc -l)
LEVEL3_REPORT=$(find . -maxdepth 2 -name "*REPORT*.md" -o -name "*ANALYSIS*.md" 2>/dev/null | wc -l)
LEVEL3_DUPLICATE=$(find .claude -name "*.md" | xargs -I {} basename {} | sort | uniq -d | wc -l)
LEVEL3_TOTAL=$((LEVEL3_BACKUP + LEVEL3_REPORT + LEVEL3_DUPLICATE))

# Level 4: 深度清理（高风险）
LEVEL4_TRASH=$(du -sh .trash 2>/dev/null | cut -f1 || echo "0")
LEVEL4_HOOKS_BAK=$(find .claude/hooks -name "*backup*" 2>/dev/null | wc -l)
LEVEL4_CONFIG_OLD=$(find .claude/config-archive -type f 2>/dev/null | wc -l)
LEVEL4_TOTAL=$((LEVEL4_HOOKS_BAK + LEVEL4_CONFIG_OLD))

# 计算总数
TOTAL_JUNK=$((LEVEL1_TOTAL + LEVEL2_TOTAL + LEVEL3_TOTAL + LEVEL4_TOTAL))

# 分级展示
if [ "$TOTAL_JUNK" -gt 0 ]; then
    echo -e "📊 清理分析报告:"
    echo

    # Level 1 - 安全清理
    if [ "$LEVEL1_TOTAL" -gt 0 ]; then
        echo -e "${GREEN}Level 1: 安全清理${NC} (无风险)"
        echo "────────────────────"
        [ "$LEVEL1_TEMP" -gt 0 ] && echo "  • 编译缓存: $LEVEL1_TEMP 个"
        [ "$LEVEL1_LOGS" -gt 0 ] && echo "  • 旧日志: $LEVEL1_LOGS 个"
        [ "$LEVEL1_CACHE" -gt 0 ] && echo "  • Python缓存: $LEVEL1_CACHE 个"
        echo -e "  ${GREEN}→ 可安全删除${NC}"
        echo
    fi

    # Level 2 - 临时文件
    if [ "$LEVEL2_TOTAL" -gt 0 ]; then
        echo -e "${YELLOW}Level 2: 临时文件${NC} (低风险)"
        echo "────────────────────"
        [ "$LEVEL2_TMP" -gt 0 ] && echo "  • /tmp文件: $LEVEL2_TMP 个"
        [ "$LEVEL2_TEST" -gt 0 ] && echo "  • 测试脚本: $LEVEL2_TEST 个"
        [ "$LEVEL2_DEMO" -gt 0 ] && echo "  • 示例文件: $LEVEL2_DEMO 个"
        echo -e "  ${YELLOW}→ 确认后可删除${NC}"
        echo
    fi

    # Level 3 - 冗余文件
    if [ "$LEVEL3_TOTAL" -gt 0 ]; then
        echo -e "${YELLOW}Level 3: 冗余文件${NC} (中风险)"
        echo "────────────────────"
        [ "$LEVEL3_BACKUP" -gt 0 ] && echo "  • 备份文件: $LEVEL3_BACKUP 个"
        [ "$LEVEL3_REPORT" -gt 0 ] && echo "  • 报告文档: $LEVEL3_REPORT 个"
        [ "$LEVEL3_DUPLICATE" -gt 0 ] && echo "  • 重复文件: $LEVEL3_DUPLICATE 组"
        echo -e "  ${YELLOW}→ 建议备份后删除${NC}"
        echo
    fi

    # Level 4 - 深度清理
    if [ "$LEVEL4_TOTAL" -gt 0 ] || [ "$LEVEL4_TRASH" != "0" ]; then
        echo -e "${RED}Level 4: 深度清理${NC} (高风险)"
        echo "────────────────────"
        [ "$LEVEL4_TRASH" != "0" ] && echo "  • 垃圾箱: $LEVEL4_TRASH"
        [ "$LEVEL4_HOOKS_BAK" -gt 0 ] && echo "  • Hook备份: $LEVEL4_HOOKS_BAK 个"
        [ "$LEVEL4_CONFIG_OLD" -gt 0 ] && echo "  • 旧配置: $LEVEL4_CONFIG_OLD 个"
        echo -e "  ${RED}→ 谨慎处理${NC}"
        echo
    fi

    # 智能建议
    echo "════════════════════════════════════════"
    echo -e "${CYAN}🎯 清理建议:${NC}"

    if [ "$LEVEL1_TOTAL" -gt 10 ]; then
        echo
        echo "1️⃣ 立即执行安全清理:"
        echo "   find . -name '*.pyc' -delete"
        echo "   find . -name '__pycache__' -type d -exec rm -rf {} +"
    fi

    if [ "$LEVEL2_TOTAL" -gt 5 ]; then
        echo
        echo "2️⃣ 清理测试文件:"
        echo "   rm -f *test*.sh *diagnostic*.py"
    fi

    if [ "$LEVEL3_TOTAL" -gt 20 ]; then
        echo
        echo "3️⃣ 整理备份文件:"
        echo "   mkdir -p .archive/$(date +%Y%m%d)"
        echo "   mv .claude/**/*.bak* .archive/$(date +%Y%m%d)/"
    fi

    if [ "$TOTAL_JUNK" -gt 50 ]; then
        echo
        echo -e "${RED}⚠️ 建议执行完整清理:${NC}"
        echo "   .claude/scripts/hyper_performance_cleanup.sh"
    elif [ "$TOTAL_JUNK" -gt 20 ]; then
        echo
        echo -e "${YELLOW}💡 建议执行标准清理:${NC}"
        echo "   .claude/scripts/cleanup.sh --safe"
    fi

    # 空间预估
    echo
    echo "💾 预计可释放空间:"
    ESTIMATED_SIZE=$(find . -type f \( -name "*.pyc" -o -name "*.log" -o -name "*.bak*" \) -exec du -ch {} + 2>/dev/null | tail -1 | cut -f1 || echo "未知")
    echo "   约 $ESTIMATED_SIZE"

else
    echo -e "${GREEN}✨ 系统清洁${NC}"
    echo "没有需要清理的文件"
fi

echo "════════════════════════════════════════"

exit 0