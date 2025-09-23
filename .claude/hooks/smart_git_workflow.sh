#!/bin/bash
# Claude Enhancer - 智能Git工作流助手
# 根据不同情况提供完整的Git流程指导

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 获取Git状态
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "none")
MODIFIED=$(git status --porcelain 2>/dev/null | wc -l)
STAGED=$(git diff --cached --name-only 2>/dev/null | wc -l)
UNPUSHED=$(git log origin/$BRANCH..$BRANCH 2>/dev/null | grep -c "^commit" || echo 0)
UNTRACKED=$(git status --porcelain 2>/dev/null | grep "^??" | wc -l)

# 判断工作流阶段
determine_workflow_phase() {
    if [ "$BRANCH" == "main" ] || [ "$BRANCH" == "master" ]; then
        echo "NEED_BRANCH"
    elif [ "$MODIFIED" -eq 0 ]; then
        echo "CLEAN"
    elif [ "$MODIFIED" -lt 10 ]; then
        echo "MINOR_CHANGES"
    elif [ "$MODIFIED" -lt 50 ]; then
        echo "MODERATE_CHANGES"
    else
        echo "MAJOR_CHANGES"
    fi
}

PHASE=$(determine_workflow_phase)

echo -e "${BLUE}🔄 Git工作流智能助手${NC}"
echo "════════════════════════════════════════"

# 显示当前状态
echo -e "📊 当前状态:"
echo -e "  • 分支: ${GREEN}$BRANCH${NC}"
echo -e "  • 修改: ${YELLOW}$MODIFIED${NC} 个文件"
[ "$STAGED" -gt 0 ] && echo -e "  • 已暂存: ${GREEN}$STAGED${NC} 个文件"
[ "$UNTRACKED" -gt 0 ] && echo -e "  • 未跟踪: ${YELLOW}$UNTRACKED${NC} 个文件"
[ "$UNPUSHED" -gt 0 ] && echo -e "  • 未推送: ${RED}$UNPUSHED${NC} 个提交"
echo

# 根据阶段提供建议
case "$PHASE" in
    "NEED_BRANCH")
        echo -e "${RED}⚠️ Phase 0: 需要创建分支${NC}"
        echo
        echo "📝 建议操作流程:"
        echo "  1. 创建功能分支:"

        # 智能分支名建议
        if [ "$MODIFIED" -gt 0 ]; then
            # 分析修改文件类型
            if git diff --name-only | grep -q "\.claude"; then
                echo "     git checkout -b feature/claude-enhancer-$(date +%Y%m%d)"
            elif git diff --name-only | grep -q "test"; then
                echo "     git checkout -b test/testing-$(date +%Y%m%d)"
            else
                echo "     git checkout -b feature/new-feature-$(date +%Y%m%d)"
            fi
        else
            echo "     git checkout -b feature/your-feature"
        fi

        echo "  2. 开始开发工作"
        echo
        echo "🔄 8-Phase工作流:"
        echo "  Phase 0: 创建分支 ← 当前"
        echo "  Phase 1-7: 后续流程"
        ;;

    "MINOR_CHANGES")
        echo -e "${GREEN}✅ 少量修改${NC}"
        echo
        echo "📝 建议操作:"
        echo "  1. 查看修改: git diff"
        echo "  2. 暂存文件: git add -A"
        echo "  3. 提交更改: git commit -m 'feat: ...'"

        # 智能提交信息建议
        if git diff --name-only | grep -q "fix"; then
            echo
            echo "💡 提交信息建议:"
            echo '  git commit -m "fix: 修复XXX问题"'
        elif git diff --name-only | grep -q "test"; then
            echo
            echo "💡 提交信息建议:"
            echo '  git commit -m "test: 添加XXX测试"'
        fi
        ;;

    "MODERATE_CHANGES")
        echo -e "${YELLOW}⚠️ 中等修改量${NC}"
        echo
        echo "📝 建议分批提交:"
        echo "  1. 按功能分组查看:"
        echo "     git status -s | grep '\.sh$'   # Shell脚本"
        echo "     git status -s | grep '\.md$'   # 文档"
        echo "     git status -s | grep '\.py$'   # Python"
        echo
        echo "  2. 分批提交:"
        echo "     git add .claude/hooks/*.sh"
        echo '     git commit -m "feat: 添加Hook功能"'
        echo
        echo "     git add *.md"
        echo '     git commit -m "docs: 更新文档"'
        ;;

    "MAJOR_CHANGES")
        echo -e "${RED}🔴 大量修改（$MODIFIED 个文件）${NC}"
        echo
        echo "⚠️ 建议操作:"
        echo "  1. 先备份当前工作:"
        echo "     git stash"
        echo "     git stash branch backup-$(date +%Y%m%d)"
        echo
        echo "  2. 或分类提交:"

        # 分析文件类型
        echo "     📂 按类型统计:"
        git status --porcelain | cut -c4- | sed 's/.*\.//' | sort | uniq -c | head -5 | while read count ext; do
            echo "        • .$ext: $count 个文件"
        done

        echo
        echo "  3. 建议操作序列:"
        echo "     # 先提交核心功能"
        echo "     git add .claude/core .claude/hooks"
        echo '     git commit -m "feat: 核心功能优化"'
        echo
        echo "     # 再提交配置"
        echo "     git add .claude/config .claude/settings.json"
        echo '     git commit -m "config: 更新配置"'
        echo
        echo "     # 最后提交文档"
        echo "     git add *.md"
        echo '     git commit -m "docs: 更新文档"'
        ;;

    "CLEAN")
        echo -e "${GREEN}✨ 工作区干净${NC}"
        if [ "$UNPUSHED" -gt 0 ]; then
            echo
            echo "💡 有 $UNPUSHED 个提交未推送:"
            echo "   git push origin $BRANCH"
        fi
        ;;
esac

# 快捷命令提示
echo
echo "════════════════════════════════════════"
echo "🚀 快捷命令:"
echo "  查看: git status | git diff | git log --oneline -5"
echo "  提交: git add -A && git commit -m '...'"
echo "  推送: git push origin $BRANCH"

exit 0