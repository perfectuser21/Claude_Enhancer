#!/bin/bash
# ===========================================
# Claude Enhancer - Branch Protection快速配置脚本
# ===========================================
#
# 用途: 自动配置GitHub仓库的Branch Protection规则
# 依赖: GitHub CLI (gh)
#
# 使用方法:
#   ./scripts/setup_branch_protection.sh [options]
#
# 选项:
#   --repo OWNER/REPO    指定仓库（默认从git remote读取）
#   --branch BRANCH      指定分支（默认：main）
#   --level LEVEL        保护级别：basic|standard|strict|claude-enhancer（默认：claude-enhancer）
#   --dry-run            预览配置但不实际应用
#   --help               显示帮助信息

set -euo pipefail

# ===========================================
# 配置变量
# ===========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 默认值
REPO=""
BRANCH="main"
PROTECTION_LEVEL="claude-enhancer"
DRY_RUN=false

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ===========================================
# 辅助函数
# ===========================================

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠️${NC}  $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

print_header() {
    echo ""
    echo "═══════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════"
    echo ""
}

show_help() {
    cat << EOF
Claude Enhancer - Branch Protection配置脚本

用法:
    $0 [options]

选项:
    --repo OWNER/REPO       指定仓库（如：myorg/myrepo）
    --branch BRANCH         指定分支（默认：main）
    --level LEVEL           保护级别（默认：claude-enhancer）
    --dry-run               预览配置但不实际应用
    --help                  显示此帮助信息

保护级别:
    basic               基础保护
                        - 禁止直接push
                        - 需要1个approval

    standard            标准保护
                        - 基础保护 +
                        - 需要2个approvals
                        - Required status checks: build, test

    strict              严格保护
                        - 标准保护 +
                        - Signed commits
                        - Linear history
                        - Include administrators

    claude-enhancer     Claude Enhancer工作流（推荐）
                        - 严格保护 +
                        - Phase gates验证
                        - Must-produce检查
                        - 9个CI status checks

示例:
    # 使用默认设置（当前仓库，main分支，claude-enhancer级别）
    $0

    # 指定仓库和分支
    $0 --repo myorg/myrepo --branch develop

    # 使用标准保护级别
    $0 --level standard

    # 预览配置（不实际应用）
    $0 --dry-run

依赖:
    - GitHub CLI (gh) - https://cli.github.com/
    - jq - JSON处理工具

文档:
    详细配置指南见: docs/BRANCH_PROTECTION_SETUP.md
EOF
    exit 0
}

check_dependencies() {
    local missing=()

    if ! command -v gh &> /dev/null; then
        missing+=("gh (GitHub CLI)")
    fi

    if ! command -v jq &> /dev/null; then
        missing+=("jq")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "缺少依赖工具："
        for tool in "${missing[@]}"; do
            echo "  - $tool"
        done
        echo ""
        echo "安装指南："
        echo "  macOS: brew install gh jq"
        echo "  Ubuntu/Debian: sudo apt install gh jq"
        echo "  其他: 参见 https://cli.github.com/ 和 https://stedolan.github.io/jq/"
        exit 1
    fi
}

detect_repo() {
    if [ -z "$REPO" ]; then
        # 从git remote读取
        local remote_url
        remote_url=$(git config --get remote.origin.url 2>/dev/null || echo "")

        if [ -z "$remote_url" ]; then
            log_error "无法检测仓库，请使用 --repo 指定"
            exit 1
        fi

        # 解析GitHub仓库名称
        # 支持: git@github.com:owner/repo.git 和 https://github.com/owner/repo.git
        if [[ "$remote_url" =~ github\.com[:/](.+)\.git$ ]]; then
            REPO="${BASH_REMATCH[1]}"
        elif [[ "$remote_url" =~ github\.com[:/](.+)$ ]]; then
            REPO="${BASH_REMATCH[1]}"
        else
            log_error "无法解析GitHub仓库URL: $remote_url"
            exit 1
        fi
    fi

    log_info "检测到仓库: $REPO"
}

verify_access() {
    log_info "验证仓库访问权限..."

    # 检查是否登录
    if ! gh auth status &>/dev/null; then
        log_error "未登录GitHub，请先运行: gh auth login"
        exit 1
    fi

    # 检查仓库权限
    local permission
    permission=$(gh api repos/"$REPO" --jq '.permissions.admin' 2>/dev/null || echo "false")

    if [ "$permission" != "true" ]; then
        log_error "你没有仓库的Admin权限，无法配置Branch Protection"
        log_info "当前权限: $(gh api repos/"$REPO" --jq '.permissions')"
        exit 1
    fi

    log_success "权限验证通过"
}

get_protection_config() {
    local level="$1"
    local config_file="/tmp/branch_protection_$$.json"

    case "$level" in
        basic)
            cat > "$config_file" << 'EOF'
{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismissal_restrictions": {},
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
            ;;

        standard)
            cat > "$config_file" << 'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["build", "test"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismissal_restrictions": {},
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 2
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF
            ;;

        strict)
            cat > "$config_file" << 'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["build", "test", "lint", "security-scan"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismissal_restrictions": {},
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 2,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true,
  "required_signatures": true
}
EOF
            ;;

        claude-enhancer)
            cat > "$config_file" << 'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "validate-phase-gates",
      "validate-must-produce",
      "run-unit-tests",
      "run-boundary-tests",
      "run-smoke-tests",
      "run-bdd-tests",
      "check-security",
      "validate-openapi",
      "check-performance"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismissal_restrictions": {},
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 2,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": true
}
EOF
            ;;

        *)
            log_error "未知的保护级别: $level"
            echo "支持的级别: basic, standard, strict, claude-enhancer"
            exit 1
            ;;
    esac

    echo "$config_file"
}

show_config_preview() {
    local config_file="$1"

    print_header "配置预览"

    log_info "仓库: $REPO"
    log_info "分支: $BRANCH"
    log_info "保护级别: $PROTECTION_LEVEL"
    echo ""

    log_info "详细配置:"
    jq '.' "$config_file"

    echo ""
    log_info "将启用以下保护:"

    # 解析配置并显示
    local approvals
    approvals=$(jq -r '.required_pull_request_reviews.required_approving_review_count' "$config_file")
    echo "  - 需要 $approvals 个approval"

    if [ "$(jq -r '.required_pull_request_reviews.require_code_owner_reviews' "$config_file")" = "true" ]; then
        echo "  - 需要Code Owner审查"
    fi

    if [ "$(jq -r '.required_pull_request_reviews.dismiss_stale_reviews' "$config_file")" = "true" ]; then
        echo "  - 新提交时取消旧的approval"
    fi

    if [ "$(jq -r '.required_linear_history' "$config_file")" = "true" ]; then
        echo "  - 要求线性历史"
    fi

    if [ "$(jq -r '.enforce_admins' "$config_file")" = "true" ]; then
        echo "  - 管理员也需遵守规则"
    fi

    if [ "$(jq -r '.required_conversation_resolution' "$config_file")" = "true" ]; then
        echo "  - 需要解决所有对话"
    fi

    # Required status checks
    local contexts
    contexts=$(jq -r '.required_status_checks.contexts[]?' "$config_file" 2>/dev/null || echo "")
    if [ -n "$contexts" ]; then
        echo "  - Required status checks:"
        echo "$contexts" | sed 's/^/      • /'
    fi

    echo ""
}

apply_protection() {
    local config_file="$1"

    print_header "应用Branch Protection"

    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN模式 - 不会实际应用配置"
        return 0
    fi

    log_info "正在配置 $REPO 的 $BRANCH 分支..."

    # 应用配置
    if gh api repos/"$REPO"/branches/"$BRANCH"/protection \
        --method PUT \
        --input "$config_file" > /dev/null 2>&1; then
        log_success "Branch Protection配置成功！"
    else
        log_error "配置失败"
        echo ""
        log_info "可能的原因:"
        echo "  1. 分支不存在"
        echo "  2. 权限不足"
        echo "  3. Status checks未定义（需要先运行CI）"
        echo "  4. CODEOWNERS文件有语法错误"
        echo ""
        log_info "调试建议:"
        echo "  - 检查分支是否存在: gh api repos/$REPO/branches/$BRANCH"
        echo "  - 验证权限: gh api repos/$REPO --jq '.permissions'"
        echo "  - 查看详细错误:"
        echo "    gh api repos/$REPO/branches/$BRANCH/protection --method PUT --input $config_file"
        exit 1
    fi
}

verify_protection() {
    print_header "验证配置"

    log_info "获取当前Branch Protection配置..."

    local current_config
    current_config=$(gh api repos/"$REPO"/branches/"$BRANCH"/protection 2>/dev/null || echo "{}")

    if [ "$current_config" = "{}" ] || [ "$current_config" = "null" ]; then
        log_warning "无法获取Branch Protection配置（可能尚未配置）"
        return 1
    fi

    echo "$current_config" | jq '{
        required_approvals: .required_pull_request_reviews.required_approving_review_count,
        code_owner_reviews: .required_pull_request_reviews.require_code_owner_reviews,
        dismiss_stale: .required_pull_request_reviews.dismiss_stale_reviews,
        enforce_admins: .enforce_admins.enabled,
        linear_history: .required_linear_history.enabled,
        required_checks: .required_status_checks.contexts
    }'

    log_success "配置验证完成"
}

setup_codeowners() {
    print_header "检查CODEOWNERS配置"

    local codeowners_file="$PROJECT_ROOT/.github/CODEOWNERS"

    if [ ! -f "$codeowners_file" ]; then
        log_warning "CODEOWNERS文件不存在: $codeowners_file"
        log_info "建议创建CODEOWNERS文件以启用自动审查分配"
        log_info "参考文档: docs/BRANCH_PROTECTION_SETUP.md"
        return 1
    fi

    log_success "CODEOWNERS文件存在"

    # 验证语法
    log_info "验证CODEOWNERS语法..."
    local errors
    errors=$(gh api repos/"$REPO"/codeowners/errors 2>/dev/null || echo '{"errors":[]}')

    local error_count
    error_count=$(echo "$errors" | jq '.errors | length')

    if [ "$error_count" -gt 0 ]; then
        log_warning "发现 $error_count 个CODEOWNERS错误:"
        echo "$errors" | jq -r '.errors[] | "  • Line \(.line): \(.message)"'
        return 1
    fi

    log_success "CODEOWNERS语法正确"
}

create_test_pr() {
    print_header "创建测试PR（可选）"

    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN模式 - 跳过测试PR创建"
        return 0
    fi

    log_info "是否创建测试PR以验证配置？(y/N)"
    read -r response

    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log_info "跳过测试PR创建"
        return 0
    fi

    local test_branch="test/branch-protection-$(date +%s)"

    log_info "创建测试分支: $test_branch"

    # 创建测试分支
    git checkout -b "$test_branch" 2>/dev/null || {
        log_error "创建分支失败"
        return 1
    }

    # 做一个小改动
    echo "# Branch Protection Test - $(date)" >> README.md
    git add README.md
    git commit -m "test: verify branch protection config"

    # Push分支
    git push origin "$test_branch"

    # 创建PR
    local pr_url
    pr_url=$(gh pr create \
        --title "Test: Branch Protection Verification" \
        --body "自动化测试PR - 验证Branch Protection配置

## 验证项目
- [ ] 需要approval
- [ ] Required status checks显示
- [ ] CODEOWNERS自动添加reviewer
- [ ] 无法直接合并

## 清理
测试完成后请关闭此PR并删除分支。" \
        --base "$BRANCH" \
        --head "$test_branch")

    log_success "测试PR已创建: $pr_url"

    echo ""
    log_info "请检查以下内容:"
    echo "  1. PR页面显示需要的approvals数量"
    echo "  2. Required status checks列表正确"
    echo "  3. CODEOWNERS自动添加为reviewer"
    echo "  4. 尝试合并时被正确阻止"
    echo ""
    log_info "测试完成后，运行以下命令清理:"
    echo "  gh pr close $pr_url --delete-branch"
    echo "  git checkout $BRANCH"
}

print_summary() {
    print_header "配置完成"

    log_success "Branch Protection已成功配置！"

    echo ""
    echo "配置摘要:"
    echo "  仓库: $REPO"
    echo "  分支: $BRANCH"
    echo "  级别: $PROTECTION_LEVEL"
    echo ""

    log_info "下一步:"
    echo "  1. 验证配置: 访问 https://github.com/$REPO/settings/branches"
    echo "  2. 查看CODEOWNERS: cat .github/CODEOWNERS"
    echo "  3. 创建测试PR验证工作流"
    echo "  4. 培训团队成员了解新流程"
    echo ""

    log_info "相关文档:"
    echo "  - Branch Protection配置指南: docs/BRANCH_PROTECTION_SETUP.md"
    echo "  - PR模板: .github/PULL_REQUEST_TEMPLATE.md"
    echo "  - 工作流文档: .claude/WORKFLOW.md"
    echo ""

    log_info "获取帮助:"
    echo "  - GitHub Docs: https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests"
    echo "  - 项目Issues: https://github.com/$REPO/issues"
}

# ===========================================
# 参数解析
# ===========================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --repo)
            REPO="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --level)
            PROTECTION_LEVEL="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            show_help
            ;;
        *)
            log_error "未知选项: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# ===========================================
# 主流程
# ===========================================

main() {
    print_header "Claude Enhancer - Branch Protection配置"

    # 1. 检查依赖
    check_dependencies

    # 2. 检测仓库
    detect_repo

    # 3. 验证访问权限
    verify_access

    # 4. 获取配置
    local config_file
    config_file=$(get_protection_config "$PROTECTION_LEVEL")

    # 5. 显示配置预览
    show_config_preview "$config_file"

    # 6. 确认应用
    if [ "$DRY_RUN" = false ]; then
        echo ""
        log_warning "即将应用以上配置到 $REPO/$BRANCH"
        log_info "继续？(y/N)"
        read -r response

        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "已取消"
            rm -f "$config_file"
            exit 0
        fi
    fi

    # 7. 应用配置
    apply_protection "$config_file"

    # 8. 验证配置
    verify_protection

    # 9. 检查CODEOWNERS
    setup_codeowners

    # 10. 可选：创建测试PR
    create_test_pr

    # 11. 显示摘要
    print_summary

    # 清理临时文件
    rm -f "$config_file"
}

# 运行主流程
main
