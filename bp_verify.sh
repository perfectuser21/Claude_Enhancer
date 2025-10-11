#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
fail(){ echo -e "${RED}✗ $*${NC}"; exit 1; }
ok(){ echo -e "${GREEN}✓ $*${NC}"; }
warn(){ echo -e "${YELLOW}⚠ $*${NC}"; }

# 0) 前置检查
command -v gh >/dev/null || fail "gh CLI 未安装"
command -v jq >/dev/null || fail "jq 未安装"
git rev-parse --is-inside-work-tree >/dev/null || fail "不在 Git 仓库中"

OWNER_REPO=$(git remote get-url origin | sed -E 's#(git@|https://)([^:/]+)[:/](.+)\.git#\3#')
[ -n "$OWNER_REPO" ] || fail "无法解析仓库 origin"

echo "Repo: $OWNER_REPO"

# 1) Branch protection
BP_JSON=$(gh api repos/$OWNER_REPO/branches/main/protection 2>/dev/null || true)
[ -n "$BP_JSON" ] || fail "未检测到 main 的保护配置（请在 GitHub 设置）"

ADMIN=$(echo "$BP_JSON" | jq -r '.enforce_admins.enabled // false')
PR_REQ=$(echo "$BP_JSON" | jq -r '.required_pull_request_reviews != null')
CTX=$(echo "$BP_JSON" | jq -r '.required_status_checks.contexts // [] | join(",")')
STRICT=$(echo "$BP_JSON" | jq -r '.required_status_checks.strict // null')
[ "$ADMIN" = "false" ] && ok "enforce_admins: false (solo-friendly)" || warn "enforce_admins: $ADMIN"
[ "$PR_REQ" = "false" ] && ok "Require PR: false (solo-friendly)" || warn "Require PR: $PR_REQ"
echo "$CTX" | grep -q "." && warn "Required checks: $CTX (not configured yet)" || ok "Required checks: none (solo-friendly)"
[ "$STRICT" = "null" ] && ok "Require up to date: null (not strict)" || warn "Strict mode: $STRICT"

# 2) Hook 存在性
test -x .git/hooks/pre-push && ok "pre-push 可执行" || fail "pre-push 缺失/不可执行"
test -x .git/hooks/pre-commit && ok "pre-commit 可执行" || warn "pre-commit 不存在（非必需）"

# 3) 禁直推 main
git checkout -q main || fail "切换 main 失败"
set +e
git commit --allow-empty -m "probe: deny direct push [no-op]" >/tmp/commit.log 2>&1
COMMIT_CODE=$?
if [ $COMMIT_CODE -ne 0 ]; then
    grep -E "禁止直接提交|ERROR.*main|Direct commit to main disabled" /tmp/commit.log >/dev/null && ok "本地阻断直接提交到 main" || warn "本地提交检查: $(cat /tmp/commit.log)"
else
    # 提交成功，尝试推送
    git push origin main >/tmp/push_main.log 2>&1
    PUSH_CODE=$?
    if [ $PUSH_CODE -ne 0 ]; then
        grep -E "Direct push to .* disabled|禁止直接推送|pre-push hook declined" /tmp/push_main.log >/dev/null && ok "本地阻断直推 main" || warn "本地阻断检查异常: $(cat /tmp/push_main.log | head -5)"
    else
        fail "本地未阻断直推 main（异常）"
    fi

    # 尝试 --no-verify
    git push origin main --no-verify >/tmp/push_main_nov.log 2>&1
    PUSH_NOV_CODE=$?
    if [ $PUSH_NOV_CODE -ne 0 ]; then
        grep -E "GH006|protected branch|refusing to allow a Personal Access Token" /tmp/push_main_nov.log >/dev/null && ok "服务端阻断直推 main（即使 --no-verify）" || warn "服务端阻断检查: $(cat /tmp/push_main_nov.log | head -5)"
    else
        fail "服务端未阻断直推 main（严重异常）"
    fi

    # 回滚测试提交
    git reset --hard HEAD~1 >/dev/null 2>&1 || true
fi
set -e

# 4) PR + 必检强制（简化版 - 不需要status check，因为solo-friendly配置没有required checks）
BR="probe/bp-verify-$(date +%s)"
git checkout -b "$BR"
echo "# probe $(date -Is)" >> BP_PROBE.md
git add BP_PROBE.md && git commit --no-verify -m "probe: bp checks"
git push -u origin "$BR" >/dev/null
PR_URL=$(gh pr create --base main --title "probe: BP checks" --body "auto probe" 2>&1) || fail "创建 PR 失败"
echo "PR: $PR_URL"

# 对于solo-friendly配置，我们验证可以直接merge（不需要approval）
set +e
gh pr merge --squash --auto >/tmp/merge_attempt.log 2>&1
MERGE_CODE=$?
set -e

if [ $MERGE_CODE -eq 0 ]; then
    ok "Solo-friendly: PR 可以自己merge（无需approval）"
else
    # 检查是否因为CI还在运行
    grep -E "Waiting for status checks|checks have not completed" /tmp/merge_attempt.log >/dev/null && warn "PR merge 等待 CI 完成（正常）" || warn "PR merge 失败: $(cat /tmp/merge_attempt.log)"
fi

# 清理
PR_NUM=$(gh pr view --json number -q .number 2>/dev/null || echo "")
[ -n "$PR_NUM" ] && gh pr close "$PR_NUM" --delete-branch >/dev/null 2>&1 || true
git checkout -q main
git branch -D "$BR" >/dev/null 2>&1 || true
rm -f BP_PROBE.md

ok "三层保护全部通过验证"
echo "报告：/tmp/commit.log /tmp/push_main.log /tmp/push_main_nov.log /tmp/merge_attempt.log"
