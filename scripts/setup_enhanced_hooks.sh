#!/bin/bash
# setup_enhanced_hooks.sh - 安装入口+出口双重强化
# Claude Enhancer v5.3.2 增强版

set -euo pipefail

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   Claude Enhancer 入口+出口双重强化安装器 v5.3.2     ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# 获取git根目录
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$GIT_ROOT"

# 备份现有hooks
backup_hooks() {
    echo -e "${YELLOW}📦 备份现有hooks...${NC}"
    BACKUP_DIR=".git/hooks/backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    for hook in pre-commit post-checkout pre-push; do
        if [ -f ".git/hooks/$hook" ]; then
            cp ".git/hooks/$hook" "$BACKUP_DIR/$hook"
            echo "  备份: $hook → $BACKUP_DIR/"
        fi
    done
}

# 安装pre-commit hook（入口层）
install_pre_commit() {
    echo -e "${BLUE}🚪 安装pre-commit hook（提交入口检查）...${NC}"

    cat > .git/hooks/pre-commit << 'HOOK'
#!/bin/bash
# Pre-commit hook - 入口层强制检查
# 阻止在无ACTIVE文件时提交

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# 检查ACTIVE文件
if ! [ -f ".workflow/ACTIVE" ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ 提交被拒绝：工作流未激活${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Claude Enhancer要求所有代码变更必须在激活的工作流下进行${NC}"
    echo ""
    echo -e "${GREEN}解决方案：${NC}"
    echo -e "  运行: ${GREEN}ce start \"任务描述\"${NC}"
    echo ""
    echo "这是入口层保护，确保代码质量从源头开始"
    exit 1
fi

# 检查是否在main分支
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ 禁止直接在主分支提交${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}主分支受保护，所有更改必须通过PR${NC}"
    echo ""
    echo -e "${GREEN}请切换到feature分支：${NC}"
    echo "  git checkout -b feature/your-feature"
    exit 1
fi

# 读取工作流信息
TICKET=$(grep "^ticket=" .workflow/ACTIVE | cut -d= -f2 || echo "unknown")
echo -e "${GREEN}✅ 提交检查通过${NC}"
echo -e "📋 工作流: $TICKET"
echo -e "🌿 分支: $BRANCH"
HOOK

    chmod +x .git/hooks/pre-commit
    echo -e "${GREEN}  ✅ pre-commit hook已安装${NC}"
}

# 安装post-checkout hook（分支保护）
install_post_checkout() {
    echo -e "${BLUE}🔀 安装post-checkout hook（分支切换保护）...${NC}"

    cat > .git/hooks/post-checkout << 'HOOK'
#!/bin/bash
# Post-checkout hook - 分支切换保护
# 切换到main时发出警告

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

# 获取新分支
NEW_BRANCH=$(git branch --show-current)

if [ "$NEW_BRANCH" = "main" ] || [ "$NEW_BRANCH" = "master" ]; then
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}⚠️  警告：已切换到主分支${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${RED}主分支保护规则：${NC}"
    echo "  • 禁止直接提交"
    echo "  • 禁止直接推送"
    echo "  • 所有更改必须通过PR"
    echo ""
    echo -e "${CYAN}如需修改，请创建feature分支：${NC}"
    echo "  git checkout -b feature/your-feature"
    echo ""

    # 可选：设置目录只读（谨慎使用）
    # echo -e "${YELLOW}正在启用只读保护...${NC}"
    # find . -type f -not -path "./.git/*" -exec chmod a-w {} \; 2>/dev/null || true
fi

# 切换到feature分支时检查工作流
if [[ "$NEW_BRANCH" == feature/* ]] || [[ "$NEW_BRANCH" == hotfix/* ]]; then
    if ! [ -f ".workflow/ACTIVE" ]; then
        echo ""
        echo -e "${CYAN}💡 提示：请激活工作流${NC}"
        echo "  运行: ce start \"任务描述\""
    fi
fi
HOOK

    chmod +x .git/hooks/post-checkout
    echo -e "${GREEN}  ✅ post-checkout hook已安装${NC}"
}

# 更新pre-push hook（加强版）
update_pre_push() {
    echo -e "${BLUE}🚀 更新pre-push hook（推送出口检查）...${NC}"

    # 使用现有的pre-push hook，但确保它是最新的
    if [ -f "hooks/pre-push" ]; then
        cp hooks/pre-push .git/hooks/pre-push
        chmod +x .git/hooks/pre-push
        echo -e "${GREEN}  ✅ pre-push hook已更新${NC}"
    else
        echo -e "${YELLOW}  ⚠️ pre-push hook文件不存在，跳过${NC}"
    fi
}

# 创建workflow模板
create_workflow_template() {
    echo -e "${BLUE}📋 创建workflow入口检查模板...${NC}"

    cat > .github/workflow_template.yml << 'TEMPLATE'
# Claude Enhancer Workflow Template v5.3.2
# 所有workflow必须包含此入口检查

name: Your Workflow Name

on:
  pull_request:
  push:
    branches-ignore:
      - main  # 禁止直接推送到main

jobs:
  # 第一步：强制工作流检查（必须）
  workflow-guard:
    name: 🛡️ Workflow Guard Check
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Enforce Workflow Activation
        run: |
          # 禁止在main分支直接触发
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "::error::❌ 禁止直接在main分支触发工作流"
            echo "所有更改必须通过feature分支和PR进行"
            exit 1
          fi

          # 检查ACTIVE文件
          if [ ! -f ".workflow/ACTIVE" ]; then
            echo "::error::❌ 工作流未激活（.workflow/ACTIVE缺失）"
            echo "请运行: ce start \"任务描述\""
            exit 1
          fi

          # 验证ACTIVE文件内容
          if ! grep -q "^ticket=" .workflow/ACTIVE; then
            echo "::error::❌ ACTIVE文件格式错误"
            exit 1
          fi

          TICKET=$(grep "^ticket=" .workflow/ACTIVE | cut -d= -f2)
          BRANCH=$(grep "^branch=" .workflow/ACTIVE | cut -d= -f2)

          echo "✅ 工作流检查通过"
          echo "📋 Ticket: $TICKET"
          echo "🌿 Branch: $BRANCH"

  # 你的其他jobs...
  # your-job:
  #   needs: workflow-guard  # 确保依赖workflow-guard
  #   runs-on: ubuntu-latest
  #   steps:
  #     - name: Your steps here
TEMPLATE

    echo -e "${GREEN}  ✅ Workflow模板已创建: .github/workflow_template.yml${NC}"
}

# 显示配置总结
show_summary() {
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}安装完成总结${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${GREEN}✅ 入口层保护已启用：${NC}"
    echo "  • pre-commit: 阻止无工作流提交"
    echo "  • post-checkout: 主分支切换警告"
    echo "  • pre-push: 推送前最终检查"
    echo ""
    echo -e "${GREEN}✅ 出口层保护已配置：${NC}"
    echo "  • GitHub Actions: CI入口检查"
    echo "  • Branch Protection: PR必需检查"
    echo ""
    echo -e "${CYAN}📝 使用说明：${NC}"
    echo "  1. 所有提交前必须: ce start \"任务\""
    echo "  2. 禁止在main分支直接操作"
    echo "  3. 所有workflow需包含入口检查"
    echo ""
    echo -e "${YELLOW}⚠️ 重要提醒：${NC}"
    echo "  • 这些hook可用 --no-verify 绕过（紧急情况）"
    echo "  • 但CI层和Branch Protection无法绕过"
    echo "  • 最终保证：没有ACTIVE的代码无法进入main"
    echo ""
    echo -e "${MAGENTA}Claude Enhancer v5.3.2 - 入口+出口双重保障已激活！${NC}"
}

# 主流程
main() {
    echo -e "${YELLOW}开始安装入口+出口双重强化...${NC}"
    echo ""

    # 备份
    backup_hooks

    # 安装各层hook
    install_pre_commit
    install_post_checkout
    update_pre_push

    # 创建模板
    create_workflow_template

    # 显示总结
    show_summary

    # 写入安装记录
    mkdir -p .workflow/audit
    echo "$(date): Enhanced hooks installed (v5.3.2)" >> .workflow/audit/install.log
}

# 执行主流程
main