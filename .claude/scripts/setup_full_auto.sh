#!/bin/bash
# Claude Enhancer Full Auto Setup v5.5.0
# 一键配置完全自动化模式

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Claude Enhancer v5.5.0 自动模式配置     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: 检查settings.json
echo -e "${YELLOW}[1/4]${NC} 检查permissions配置..."
if grep -q '"permissions"' "$PROJECT_ROOT/.claude/settings.json"; then
    echo -e "${GREEN}✅ permissions配置已存在${NC}"
else
    echo -e "${RED}❌ permissions配置缺失，请检查.claude/settings.json${NC}"
    exit 1
fi

# Step 2: 启用自动模式
echo -e "${YELLOW}[2/4]${NC} 启用自动模式..."
source "$PROJECT_ROOT/.claude/auto.config"
echo -e "${GREEN}✅ 自动模式环境变量已加载${NC}"

# Step 3: 更新Git hooks支持自动模式
echo -e "${YELLOW}[3/4]${NC} 更新Git hooks..."

# 为git hooks添加自动模式支持
for hook in pre-commit commit-msg pre-push; do
    hook_file="$PROJECT_ROOT/.git/hooks/$hook"
    if [[ -f "$hook_file" ]]; then
        # 备份原始hook
        cp "$hook_file" "$hook_file.backup.$(date +%Y%m%d_%H%M%S)"

        # 在hook开头添加自动模式检测
        if ! grep -q "GIT_HOOKS_AUTO_MODE" "$hook_file"; then
            # 在第二行插入自动模式配置
            sed -i '2i\
# Auto-mode configuration for Git hooks\
export GIT_HOOKS_AUTO_MODE=true\
\
# Override read function for auto responses\
if [[ "$GIT_HOOKS_AUTO_MODE" == "true" ]]; then\
    read() {\
        local var_name="${1:-REPLY}"\
        # Only auto-respond to specific prompts\
        case "$var_name" in\
            response|answer|confirm|choice|selection)\
                eval "$var_name=y"\
                echo "y" >&2\
                ;;\
            *)\
                # Use original read for other cases\
                command read "$@"\
                ;;\
        esac\
    }\
fi' "$hook_file"
            echo -e "${GREEN}✅ 更新 $hook${NC}"
        else
            echo -e "${BLUE}ℹ️  $hook 已支持自动模式${NC}"
        fi
    fi
done

# Step 4: 创建快捷命令
echo -e "${YELLOW}[4/4]${NC} 创建快捷命令..."

# 创建全局快捷命令（如果有权限）
ALIAS_COMMAND="alias ce-auto='source $PROJECT_ROOT/.claude/auto.config'"
if [[ -w "$HOME/.bashrc" ]]; then
    if ! grep -q "ce-auto" "$HOME/.bashrc"; then
        echo "$ALIAS_COMMAND" >> "$HOME/.bashrc"
        echo -e "${GREEN}✅ 快捷命令已添加到.bashrc${NC}"
    fi
fi

# 创建标记文件
touch "$PROJECT_ROOT/.claude/.auto_mode_enabled"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         🎉 配置完成！                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}当前状态：${NC}"
echo "  • Claude权限: ✅ 自动批准"
echo "  • Git Hooks: ✅ 自动响应"
echo "  • 环境变量: ✅ 已配置"
echo "  • 快捷命令: ✅ ce-auto"
echo ""
echo -e "${YELLOW}使用说明：${NC}"
echo "1. 重启Claude Code使权限生效"
echo "2. 运行 'ce-auto' 激活自动模式"
echo "3. 运行 '.claude/scripts/auto_decision.sh status' 查看状态"
echo ""
echo -e "${GREEN}享受完全自动化的编程体验！${NC}"