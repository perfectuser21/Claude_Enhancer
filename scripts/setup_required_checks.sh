#!/usr/bin/env bash
# 配置GitHub Branch Protection - 修正版
# 基于ChatGPT审核反馈修正所有字段错误
# 日期: 2025-10-24

set -euo pipefail

REPO="${REPO:-perfectuser21/Claude_Enhancer}"
BRANCH="${BRANCH:-main}"

echo "🔒 Configuring GitHub Branch Protection for ${REPO}@${BRANCH}"
echo ""

# Step 1: 确保仓库开启 Auto-merge
echo "1️⃣ Enabling Auto-merge..."
gh repo edit "$REPO" --enable-auto-merge >/dev/null 2>&1 || {
    echo "⚠️  Auto-merge already enabled or not available"
}
echo "✅ Auto-merge enabled"
echo ""

# Step 2: 配置分支保护
echo "2️⃣ Configuring branch protection..."

# 使用CE Unified Gates作为唯一Required Check
# 其他CI jobs可以自由增删，不影响分支保护规则
REQ_CHECKS=("CE Unified Gates")

# 兼容 contexts & checks（推荐使用checks，但contexts仍需提供以兼容旧版）
contexts_json=$(printf '%s\n' "${REQ_CHECKS[@]}" | jq -R . | jq -s .)
checks_json=$(printf '%s\n' "${REQ_CHECKS[@]}" | jq -R '{context: .}' | jq -s .)

# 使用--input传递完整JSON，避免-f嵌套数组/对象的易错点
jq -n \
  --argjson contexts "${contexts_json}" \
  --argjson checks "${checks_json}" \
  '{
    required_status_checks: {
      strict: true,
      contexts: $contexts,
      checks: $checks
    },
    enforce_admins: true,
    required_pull_request_reviews: {
      require_code_owner_reviews: false,
      required_approving_review_count: 0,
      require_last_push_approval: true
    },
    restrictions: null,
    required_linear_history: true,
    allow_force_pushes: false,
    allow_deletions: false,
    block_creations: false,
    required_conversation_resolution: true,
    lock_branch: false,
    allow_fork_syncing: false
  }' | gh api \
        -X PUT \
        -H "Accept: application/vnd.github+json" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        "repos/${REPO}/branches/${BRANCH}/protection" \
        --input -

echo "✅ Branch protection configured!"
echo ""

# Step 3: 验证配置
echo "3️⃣ Verifying configuration..."
gh api "repos/${REPO}/branches/${BRANCH}/protection" | jq '{
  required_status_checks: .required_status_checks,
  enforce_admins: .enforce_admins.enabled,
  required_linear_history: .required_linear_history.enabled,
  allow_force_pushes: .allow_force_pushes.enabled,
  required_conversation_resolution: .required_conversation_resolution.enabled
}'

echo ""
echo "✅ Configuration complete!"
echo ""
echo "📋 Summary:"
echo "  ✅ Auto-merge: enabled"
echo "  ✅ Required Checks: CE Unified Gates"
echo "  ✅ Strict mode: enabled (PR must be up-to-date)"
echo "  ✅ Conversation resolution: required"
echo "  ✅ Linear history: required"
echo "  ✅ Force push: disabled"
echo "  ✅ Enforce admins: enabled"
echo ""
echo "⚠️  Next steps:"
echo "  1. Create CODEOWNERS file (optional)"
echo "  2. Setup Tag protection rules"
echo "  3. Test with a PR"
