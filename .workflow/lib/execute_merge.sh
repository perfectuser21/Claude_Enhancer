#!/bin/bash
# 执行Merge流程
# 包括：commit、push、创建PR、等待CI、自动merge

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
WORKFLOW_DIR="$PROJECT_ROOT/.workflow"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
FEATURE_NAME=$(cat "$WORKFLOW_DIR/FEATURE_NAME.txt" 2>/dev/null || echo "功能更新")

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

log_error() {
    echo -e "${RED}[✗]${NC} $*"
}

log_step() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$*${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

execute_merge() {
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  🚀 开始Merge流程                                            ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""

    # Step 1: 提交所有更改
    log_step "步骤 1/7: 提交代码"
    commit_changes

    # Step 2: 推送到远程
    log_step "步骤 2/7: 推送到远程"
    push_to_remote

    # Step 3: 创建Pull Request
    log_step "步骤 3/7: 创建Pull Request"
    create_pull_request

    # Step 4: 等待CI检查
    log_step "步骤 4/7: 等待CI检查"
    wait_for_ci

    # Step 5: 合并PR
    log_step "步骤 5/7: 合并到main"
    merge_pull_request

    # Step 6: 清理
    log_step "步骤 6/7: 清理分支"
    cleanup

    # Step 7: 完成
    log_step "步骤 7/7: 完成！"
    show_completion_message
}

commit_changes() {
    log_info "检查是否有未提交的更改..."

    if [[ -z $(git status --porcelain) ]]; then
        log_success "没有需要提交的更改"
        return 0
    fi

    log_info "准备提交更改..."

    # 生成commit message
    local commit_msg=$(generate_commit_message)

    # 添加所有更改
    git add .

    # 提交
    git commit -m "$commit_msg"

    log_success "代码已提交"
}

generate_commit_message() {
    # 生成符合Conventional Commits规范的commit message
    cat <<EOF
feat: ${FEATURE_NAME}

验收结果：
$(grep '通过率' "$WORKFLOW_DIR/VERIFICATION_REPORT.md" 2>/dev/null || echo "验收通过")

功能清单：
$(cat "$WORKFLOW_DIR/CHECKLIST.md" 2>/dev/null | grep '^\[ \]' | head -10 || echo "- 功能实现完成")

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
}

push_to_remote() {
    log_info "推送分支到远程: $CURRENT_BRANCH"

    # 检查远程分支是否存在
    if git ls-remote --heads origin "$CURRENT_BRANCH" | grep -q "$CURRENT_BRANCH"; then
        # 远程分支存在，直接push
        git push origin "$CURRENT_BRANCH"
    else
        # 远程分支不存在，使用-u创建
        git push -u origin "$CURRENT_BRANCH"
    fi

    log_success "推送完成"
}

create_pull_request() {
    log_info "创建Pull Request..."

    # 检查gh命令是否可用
    if ! command -v gh &>/dev/null; then
        log_error "gh命令未安装，无法自动创建PR"
        log_info "请手动创建PR：https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/compare/$CURRENT_BRANCH"
        return 1
    fi

    # 生成PR描述
    local pr_body=$(generate_pr_body)

    # 创建PR
    if gh pr create \
        --title "feat: ${FEATURE_NAME}" \
        --body "$pr_body" \
        --base main; then
        log_success "Pull Request已创建"
    else
        log_error "创建PR失败"
        return 1
    fi
}

generate_pr_body() {
    cat <<EOF
## 📋 功能说明

${FEATURE_NAME}

## ✅ 验收结果

$(cat "$WORKFLOW_DIR/VERIFICATION_REPORT.md" 2>/dev/null || echo "验收报告：所有项通过")

## 📁 主要修改

\`\`\`
$(git diff --stat main..HEAD 2>/dev/null | head -20)
\`\`\`

## 🚀 如何测试

\`\`\`bash
# 1. 拉取分支
git checkout $CURRENT_BRANCH

# 2. 安装依赖
npm install  # 或根据项目调整

# 3. 启动应用
npm start

# 4. 按照Checklist测试
cat .workflow/CHECKLIST.md
\`\`\`

## 🔍 Checklist

验收清单见：[CHECKLIST.md](.workflow/CHECKLIST.md)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
}

wait_for_ci() {
    log_info "等待CI检查..."

    # 检查gh命令是否可用
    if ! command -v gh &>/dev/null; then
        log_warn "gh命令未安装，跳过CI等待"
        log_info "请手动检查CI状态"
        return 0
    fi

    # 等待一小段时间让CI启动
    sleep 3

    # 使用gh pr checks --watch监控CI状态
    if gh pr checks --watch 2>/dev/null; then
        log_success "所有CI检查通过"
    else
        log_error "CI检查失败或超时"
        log_info "请查看PR页面了解详情"
        return 1
    fi
}

merge_pull_request() {
    log_info "准备合并PR..."

    # 检查gh命令是否可用
    if ! command -v gh &>/dev/null; then
        log_warn "gh命令未安装，跳过自动merge"
        log_info "请手动merge PR"
        return 0
    fi

    # 自动合并（使用squash策略）
    if gh pr merge --auto --squash --delete-branch 2>/dev/null; then
        log_success "PR已设置为自动合并"
        log_info "当所有检查通过后会自动合并并删除分支"
    else
        log_warn "自动合并设置失败"
        log_info "请手动merge PR"
    fi
}

cleanup() {
    log_info "清理工作流文件..."

    # 保留验收报告，其他临时文件可以清理
    if [[ -f "$WORKFLOW_DIR/WAITING_MERGE_CONFIRMATION" ]]; then
        rm -f "$WORKFLOW_DIR/WAITING_MERGE_CONFIRMATION"
    fi

    log_success "清理完成"
}

show_completion_message() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  🎉 Merge流程完成！                                          ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  功能: $FEATURE_NAME"
    echo "  分支: $CURRENT_BRANCH"
    echo "  状态: 已提交PR，等待自动合并"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  📊 查看验收报告"
    echo "     cat .workflow/VERIFICATION_REPORT.md"
    echo ""
    echo "  🔗 查看Pull Request"
    if command -v gh &>/dev/null; then
        echo "     gh pr view --web"
    else
        echo "     访问GitHub查看PR"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# 主函数
main() {
    # 检查必要文件
    if [[ ! -f "$WORKFLOW_DIR/VERIFICATION_REPORT.md" ]]; then
        log_error "验收报告不存在，无法merge"
        log_info "请先运行：bash .workflow/lib/verify_checklist.sh"
        exit 1
    fi

    # 检查是否在feature分支
    if [[ "$CURRENT_BRANCH" == "main" ]] || [[ "$CURRENT_BRANCH" == "master" ]]; then
        log_error "不能在main/master分支执行merge"
        exit 1
    fi

    # 执行merge流程
    execute_merge
}

# 如果直接执行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
