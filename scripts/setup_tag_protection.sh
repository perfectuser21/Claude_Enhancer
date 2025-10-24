#!/usr/bin/env bash
# Tag保护规则配置 - 使用Repository Rulesets
# 基于ChatGPT审核建议：从旧的Tag Protection迁移到Rulesets
# 日期: 2025-10-24

set -euo pipefail

REPO="${REPO:-perfectuser21/Claude_Enhancer}"

echo "🏷️  Configuring Tag Protection via Repository Rulesets"
echo ""

# Step 1: 获取现有Rulesets（检查是否已存在）
echo "1️⃣ Checking existing rulesets..."
EXISTING=$(gh api "repos/${REPO}/rulesets" 2>/dev/null || echo "[]")
RULESET_ID=$(echo "$EXISTING" | jq -r '.[] | select(.name == "Tag Protection") | .id')

if [ -n "$RULESET_ID" ] && [ "$RULESET_ID" != "null" ]; then
    echo "⚠️  Ruleset 'Tag Protection' already exists (ID: $RULESET_ID)"
    echo "   Updating existing ruleset..."
    METHOD="PUT"
    ENDPOINT="repos/${REPO}/rulesets/${RULESET_ID}"
else
    echo "   No existing ruleset found, creating new one..."
    METHOD="POST"
    ENDPOINT="repos/${REPO}/rulesets"
fi
echo ""

# Step 2: 创建/更新Ruleset配置
echo "2️⃣ Configuring ruleset..."

jq -n \
  '{
    name: "Tag Protection",
    target: "tag",
    enforcement: "active",
    bypass_actors: [
      {
        actor_id: 5,
        actor_type: "RepositoryRole",
        bypass_mode: "always"
      }
    ],
    conditions: {
      ref_name: {
        include: ["refs/tags/v*"],
        exclude: []
      }
    },
    rules: [
      {
        type: "creation"
      },
      {
        type: "update"
      },
      {
        type: "deletion"
      },
      {
        type: "required_signatures"
      }
    ]
  }' | gh api \
        -X "$METHOD" \
        -H "Accept: application/vnd.github+json" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        "$ENDPOINT" \
        --input - > /dev/null

echo "✅ Ruleset configured!"
echo ""

# Step 3: 验证配置
echo "3️⃣ Verifying ruleset..."
gh api "repos/${REPO}/rulesets" | jq '.[] | select(.name == "Tag Protection") | {
  name: .name,
  target: .target,
  enforcement: .enforcement,
  rules: [.rules[].type]
}'

echo ""
echo "✅ Tag Protection configured!"
echo ""
echo "📋 Summary:"
echo "  ✅ Pattern: refs/tags/v*"
echo "  ✅ Protection: creation + update + deletion blocked"
echo "  ✅ Required: Signed tags"
echo "  ✅ Bypass: Repository admins only"
echo ""
echo "💡 Next steps:"
echo "  1. Test creating a tag locally: git tag v0.0.1-test"
echo "  2. Try pushing: git push origin v0.0.1-test (should be blocked)"
echo "  3. Configure GitHub Actions to create tags automatically"
