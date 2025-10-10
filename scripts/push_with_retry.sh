#!/bin/bash
# Push with Retry - Network Failure Resilience
# Claude Enhancer 5.0 - Git Workflow Automation

set -euo pipefail

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Configuration
readonly MAX_RETRIES=3
readonly RETRY_DELAY=5
readonly OFFLINE_STATE_FILE=".workflow/_offline_state.json"

# ==================== Push with Retry ====================

push_with_retry() {
    local branch="${1:-$(git branch --show-current)}"
    local force="${2:-false}"
    local attempt=1

    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  📤 Git Push with Network Retry${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "分支: ${branch}"
    echo "最大重试: ${MAX_RETRIES}"
    echo ""

    while [[ $attempt -le $MAX_RETRIES ]]; do
        echo -e "${YELLOW}[尝试 ${attempt}/${MAX_RETRIES}]${NC} 推送到远程..."

        local push_cmd="git push"
        if [[ "$force" == "true" ]]; then
            push_cmd="git push --force-with-lease"
            echo -e "${YELLOW}⚠️  使用 force-with-lease 模式${NC}"
        fi

        # Set upstream if not tracking
        if ! git config "branch.${branch}.remote" > /dev/null 2>&1; then
            push_cmd="git push -u origin ${branch}"
            echo -e "${CYAN}设置上游跟踪: origin/${branch}${NC}"
        fi

        # Execute push
        if eval "$push_cmd" 2>&1 | tee .workflow/temp/push.log; then
            echo ""
            echo -e "${GREEN}✅ 推送成功！${NC}"
            echo ""

            # Show remote info
            show_remote_info "$branch"

            # Clean up offline state if exists
            [[ -f "$OFFLINE_STATE_FILE" ]] && rm -f "$OFFLINE_STATE_FILE"

            return 0
        fi

        # Push failed
        local error_msg=$(cat .workflow/temp/push.log 2>/dev/null | tail -5)

        echo ""
        echo -e "${RED}❌ 推送失败${NC}"
        echo "错误信息:"
        echo "$error_msg" | sed 's/^/  /'
        echo ""

        # Analyze failure reason
        local failure_reason=$(analyze_failure "$error_msg")

        case "$failure_reason" in
            "network")
                if [[ $attempt -lt $MAX_RETRIES ]]; then
                    echo -e "${YELLOW}网络错误，${RETRY_DELAY}秒后重试...${NC}"
                    sleep $RETRY_DELAY
                fi
                ;;
            "rejected")
                echo -e "${RED}推送被拒绝（远程有新提交）${NC}"
                echo ""
                echo "建议操作:"
                echo "  1. 拉取远程更新: git pull --rebase origin ${branch}"
                echo "  2. 解决冲突（如果有）"
                echo "  3. 重新推送: bash $0 ${branch}"
                return 1
                ;;
            "permission")
                echo -e "${RED}权限不足${NC}"
                echo ""
                echo "建议操作:"
                echo "  1. 检查 SSH 密钥: ssh -T git@github.com"
                echo "  2. 确认仓库写权限"
                echo "  3. 联系仓库管理员"
                return 1
                ;;
            "size")
                echo -e "${RED}推送内容过大${NC}"
                echo ""
                echo "建议操作:"
                echo "  1. 检查是否有大文件: git ls-files -z | xargs -0 du -h | sort -rh | head -20"
                echo "  2. 使用 Git LFS: git lfs track '*.bin'"
                echo "  3. 分批推送: git push origin HEAD~N:${branch}"
                return 1
                ;;
            *)
                echo -e "${YELLOW}未知错误${NC}"
                ;;
        esac

        ((attempt++))
    done

    # All retries failed
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  ❌ 推送失败（已重试 ${MAX_RETRIES} 次）${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Save offline state
    echo -e "${CYAN}💾 保存离线状态...${NC}"
    save_offline_state "$branch"

    echo ""
    echo -e "${YELLOW}后续操作:${NC}"
    echo "  1. 检查网络连接"
    echo "  2. 网络恢复后运行: bash scripts/resume_publish.sh"
    echo "  3. 或手动推送: git push origin ${branch}"
    echo ""

    return 1
}

# ==================== Failure Analysis ====================

analyze_failure() {
    local error_msg="$1"

    # Network errors
    if echo "$error_msg" | grep -qiE "(network|connection|timeout|could not resolve|failed to connect)"; then
        echo "network"
        return
    fi

    # Rejected (non-fast-forward)
    if echo "$error_msg" | grep -qiE "(rejected|non-fast-forward|fetch first)"; then
        echo "rejected"
        return
    fi

    # Permission denied
    if echo "$error_msg" | grep -qiE "(permission denied|authentication failed|access denied)"; then
        echo "permission"
        return
    fi

    # Size limit exceeded
    if echo "$error_msg" | grep -qiE "(size.*exceeded|too large|pack.*too big)"; then
        echo "size"
        return
    fi

    echo "unknown"
}

# ==================== Offline State Management ====================

save_offline_state() {
    local branch="$1"

    mkdir -p "$(dirname "$OFFLINE_STATE_FILE")"

    cat > "$OFFLINE_STATE_FILE" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "branch": "${branch}",
    "phase": "$(cat .phase/current 2>/dev/null || echo 'Unknown')",
    "last_commit": "$(git rev-parse HEAD)",
    "commits_ahead": $(git rev-list --count @{u}..HEAD 2>/dev/null || echo 0),
    "quality_score": "$(cat .workflow/_reports/quality_score.txt 2>/dev/null || echo 'N/A')",
    "pending_action": "push_and_create_pr",
    "remote_url": "$(git config --get remote.origin.url)"
}
EOF

    echo "离线状态已保存到: ${OFFLINE_STATE_FILE}"
    echo ""
    echo "状态快照:"
    cat "$OFFLINE_STATE_FILE" | python3 -m json.tool 2>/dev/null || cat "$OFFLINE_STATE_FILE"
}

resume_from_offline() {
    if [[ ! -f "$OFFLINE_STATE_FILE" ]]; then
        echo -e "${YELLOW}⚠️  无离线状态文件${NC}"
        return 1
    fi

    echo -e "${CYAN}📂 加载离线状态...${NC}"
    echo ""

    # Parse JSON
    local branch=$(cat "$OFFLINE_STATE_FILE" | python3 -c "import sys,json; print(json.load(sys.stdin)['branch'])" 2>/dev/null)
    local saved_time=$(cat "$OFFLINE_STATE_FILE" | python3 -c "import sys,json; print(json.load(sys.stdin)['timestamp'])" 2>/dev/null)

    echo "分支: ${branch}"
    echo "保存时间: ${saved_time}"
    echo ""

    # Verify current state
    local current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "$branch" ]]; then
        echo -e "${YELLOW}⚠️  当前分支 (${current_branch}) 与保存的分支 (${branch}) 不一致${NC}"
        read -p "是否切换到 ${branch}? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git checkout "$branch"
        else
            echo "操作取消"
            return 1
        fi
    fi

    # Test network
    echo "测试网络连接..."
    if ! timeout 5 git ls-remote origin HEAD > /dev/null 2>&1; then
        echo -e "${RED}❌ 网络仍然不可用${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ 网络已恢复${NC}"
    echo ""

    # Resume push
    push_with_retry "$branch"
}

# ==================== Remote Info Display ====================

show_remote_info() {
    local branch="$1"

    echo -e "${GREEN}📊 远程分支信息${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Remote URL
    local remote_url=$(git config --get remote.origin.url)
    echo "远程仓库: ${remote_url}"

    # Tracking info
    local upstream=$(git config --get "branch.${branch}.merge" 2>/dev/null || echo "N/A")
    echo "上游分支: ${upstream}"

    # Commits ahead/behind
    if git rev-parse @{u} > /dev/null 2>&1; then
        local ahead=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo 0)
        local behind=$(git rev-list --count HEAD..@{u} 2>/dev/null || echo 0)

        if [[ $ahead -eq 0 && $behind -eq 0 ]]; then
            echo -e "状态: ${GREEN}同步${NC}"
        elif [[ $ahead -gt 0 && $behind -eq 0 ]]; then
            echo -e "状态: ${YELLOW}领先 ${ahead} 个提交${NC}"
        elif [[ $ahead -eq 0 && $behind -gt 0 ]]; then
            echo -e "状态: ${YELLOW}落后 ${behind} 个提交${NC}"
        else
            echo -e "状态: ${RED}分叉 (领先 ${ahead}, 落后 ${behind})${NC}"
        fi
    else
        echo "状态: 无上游跟踪"
    fi

    echo ""
}

# ==================== Network Test ====================

test_network() {
    echo -e "${CYAN}🔍 测试网络连接...${NC}"
    echo ""

    # Test DNS
    echo -n "DNS 解析: "
    if timeout 3 host github.com > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
        return 1
    fi

    # Test HTTPS
    echo -n "HTTPS 连接: "
    if timeout 5 curl -sI https://github.com > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
        return 1
    fi

    # Test SSH
    echo -n "SSH 连接: "
    if timeout 5 ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
        return 1
    fi

    # Test Git remote
    echo -n "Git 远程: "
    if timeout 5 git ls-remote origin HEAD > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
        return 1
    fi

    echo ""
    echo -e "${GREEN}✅ 网络连接正常${NC}"
    return 0
}

# ==================== Usage Help ====================

show_usage() {
    cat << EOF
${CYAN}Push with Retry - Network Failure Resilience${NC}

用法:
  $0 [branch] [options]

参数:
  branch         目标分支（默认当前分支）
  --force        使用 --force-with-lease 推送
  --resume       从离线状态恢复
  --test         测试网络连接

示例:
  $0                           # 推送当前分支
  $0 feature/P3-auth           # 推送指定分支
  $0 --force                   # 强制推送（安全模式）
  $0 --resume                  # 网络恢复后继续
  $0 --test                    # 测试网络

配置:
  MAX_RETRIES=${MAX_RETRIES}      # 最大重试次数
  RETRY_DELAY=${RETRY_DELAY}      # 重试延迟（秒）

离线状态文件:
  ${OFFLINE_STATE_FILE}

EOF
}

# ==================== Entry Point ====================

main() {
    mkdir -p .workflow/temp

    case "${1:-}" in
        --help|-h)
            show_usage
            exit 0
            ;;
        --resume)
            resume_from_offline
            exit $?
            ;;
        --test)
            test_network
            exit $?
            ;;
        --force)
            push_with_retry "$(git branch --show-current)" "true"
            exit $?
            ;;
        *)
            push_with_retry "$@"
            exit $?
            ;;
    esac
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
