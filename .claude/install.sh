#!/bin/bash
# Claude Enhancer 安装脚本

echo "🚀 Claude Enhancer 安装"
echo "========================"

# 检查是否在git仓库
if [ ! -d .git ]; then
    echo "⚠️  警告：当前不是git仓库，Git Hooks将不会安装"
    echo "继续安装？(y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        exit 1
    fi
fi

# 1. 确保hooks有执行权限
echo "📝 设置执行权限..."
chmod +x .claude/hooks/*.sh 2>/dev/null

# 2. 安装Git Hooks（可选）
if [ -d .git ]; then
    echo "📌 安装Git Hooks..."

    # 备份现有hooks
    for hook in pre-commit commit-msg pre-push; do
        if [ -f .git/hooks/$hook ]; then
            cp .git/hooks/$hook .git/hooks/$hook.backup.$(date +%Y%m%d)
            echo "  备份: $hook → $hook.backup"
        fi
    done

    # 安装新hooks
    cp .claude/hooks/simple_pre_commit.sh .git/hooks/pre-commit
    cp .claude/hooks/simple_commit_msg.sh .git/hooks/commit-msg
    cp .claude/hooks/simple_pre_push.sh .git/hooks/pre-push

    chmod +x .git/hooks/pre-commit
    chmod +x .git/hooks/commit-msg
    chmod +x .git/hooks/pre-push

    echo "  ✅ Git Hooks已安装"
fi

# 3. 创建配置软链接（可选）
if [ ! -f .claude/settings.json ]; then
    echo "⚠️  未找到settings.json，跳过"
else
    echo "✅ Claude配置已就绪"
fi

# 4. 显示使用说明
echo ""
echo "✨ 安装完成！"
echo ""
echo "📋 使用方法："
echo "  1. Claude会自动分析任务并选择4-6-8个Agent"
echo "  2. Git提交时会自动检查代码质量"
echo "  3. 查看 .claude/README.md 了解详情"
echo ""
echo "💡 工作流程："
echo "  Phase 0-2: 需求分析和设计"
echo "  Phase 3: Agent并行开发"
echo "  Phase 4-7: 测试、提交、审查、部署"
echo ""
echo "🎯 Agent策略："
echo "  简单任务：4个Agent"
echo "  标准任务：6个Agent"
echo "  复杂任务：8个Agent"
echo ""
echo "Happy coding with Claude Enhancer! 🚀"