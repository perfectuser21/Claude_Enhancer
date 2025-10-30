#!/bin/bash
# Claude Hook: 版本号强制升级检查
# 触发时机: PreCommit (Git提交前)
# 目的: 强制每次修改都升级版本号
# 优先级: 最高 - 硬阻止

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
VERSION_FILE="${PROJECT_ROOT}/VERSION"

# 比较版本号大小 (semver: major.minor.patch)
version_greater() {
    local ver1="$1"
    local ver2="$2"

    # 提取版本号部分 (去掉v前缀)
    ver1="${ver1#v}"
    ver2="${ver2#v}"

    # 分解为数组
    IFS='.' read -ra V1 <<< "$ver1"
    IFS='.' read -ra V2 <<< "$ver2"

    # 比较major
    if [[ ${V1[0]:-0} -gt ${V2[0]:-0} ]]; then
        return 0
    elif [[ ${V1[0]:-0} -lt ${V2[0]:-0} ]]; then
        return 1
    fi

    # major相同，比较minor
    if [[ ${V1[1]:-0} -gt ${V2[1]:-0} ]]; then
        return 0
    elif [[ ${V1[1]:-0} -lt ${V2[1]:-0} ]]; then
        return 1
    fi

    # major和minor相同，比较patch
    if [[ ${V1[2]:-0} -gt ${V2[2]:-0} ]]; then
        return 0
    else
        return 1
    fi
}

# 获取当前分支名
current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# 如果在main/master分支，跳过检查（防止循环）
if [[ "$current_branch" == "main" ]] || [[ "$current_branch" == "master" ]]; then
    exit 0
fi

# 如果VERSION文件不存在，跳过检查
if [[ ! -f "$VERSION_FILE" ]]; then
    echo "⚠️  WARNING: VERSION file not found, skipping version check"
    exit 0
fi

# 获取main分支的VERSION（如果存在）
git fetch origin main 2>/dev/null || true
MAIN_VERSION=$(git show origin/main:VERSION 2>/dev/null || echo "0.0.0")

# 获取当前分支的VERSION
CURRENT_VERSION=$(cat "$VERSION_FILE" 2>/dev/null || echo "0.0.0")

# 清理版本号（去掉空格、换行）
MAIN_VERSION=$(echo "$MAIN_VERSION" | tr -d '[:space:]')
CURRENT_VERSION=$(echo "$CURRENT_VERSION" | tr -d '[:space:]')

# 如果版本号相同，阻止提交
if [[ "$CURRENT_VERSION" == "$MAIN_VERSION" ]]; then
    echo "════════════════════════════════════════════════════════════"
    echo "❌ ERROR: Version must be incremented"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Main branch version: $MAIN_VERSION"
    echo "Your branch version: $CURRENT_VERSION"
    echo ""
    echo "🚨 RULE: Every code change requires version increment!"
    echo ""
    echo "📋 Update these 6 files with new version:"
    echo "   1. VERSION"
    echo "   2. .claude/settings.json"
    echo "   3. .workflow/manifest.yml"
    echo "   4. package.json"
    echo "   5. CHANGELOG.md"
    echo "   6. .workflow/SPEC.yaml"
    echo ""
    echo "💡 Recommended commands:"
    echo "   # Patch version (bug fix): 8.5.1 → 8.5.2"
    echo "   bash scripts/bump_version.sh patch"
    echo ""
    echo "   # Minor version (new feature): 8.5.1 → 8.6.0"
    echo "   bash scripts/bump_version.sh minor"
    echo ""
    echo "   # Major version (breaking change): 8.5.1 → 9.0.0"
    echo "   bash scripts/bump_version.sh major"
    echo ""
    echo "🔍 Or manually update all 6 files to the same new version"
    echo "════════════════════════════════════════════════════════════"
    exit 1
fi

# 版本号必须大于main（防止版本倒退）
if ! version_greater "$CURRENT_VERSION" "$MAIN_VERSION"; then
    echo "════════════════════════════════════════════════════════════"
    echo "❌ ERROR: New version must be greater than main branch"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Main branch version: $MAIN_VERSION"
    echo "Your branch version: $CURRENT_VERSION"
    echo ""
    echo "🚨 Version cannot go backwards or stay the same!"
    echo ""
    echo "💡 To fix:"
    echo "   Use bump_version.sh to increment version correctly"
    echo "   bash scripts/bump_version.sh [patch|minor|major]"
    echo ""
    exit 1
fi

# 全部通过
echo "✅ Version incremented: $MAIN_VERSION → $CURRENT_VERSION"
exit 0
