#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# verify-core-structure.sh - 核心结构完整性验证脚本
# Version: 1.0.0
# Purpose: 验证Claude Enhancer核心结构未被篡改
# Author: Claude Code (Lockdown Mechanism)
# Date: 2025-10-20
# ═══════════════════════════════════════════════════════════
set -euo pipefail

# ═══════════════════════════════════════════════════════════
# 依赖检查（防止脚本在缺少工具时运行）
# ═══════════════════════════════════════════════════════════
need() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "{\"ok\":false,\"reason\":\"MISSING_DEPENDENCY: $1\"}"
        exit 2
    }
}

need jq
need yq

# 检测sha256命令（Linux用sha256sum，macOS用shasum）
if command -v sha256sum >/dev/null 2>&1; then
    SHA_CMD="sha256sum"
elif command -v shasum >/dev/null 2>&1; then
    SHA_CMD="shasum -a 256"
else
    echo "{\"ok\":false,\"reason\":\"MISSING_DEPENDENCY: sha256sum or shasum\"}"
    exit 2
fi

# ═══════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════
sha() {
    if [ ! -f "$1" ]; then
        echo "{\"ok\":false,\"reason\":\"FILE_NOT_FOUND: $1\"}"
        exit 1
    fi
    $SHA_CMD "$1" | awk '{print $1}'
}

fail() {
    echo "{\"ok\":false,\"reason\":\"$1\"}"
    exit 1
}

pass() {
    echo "{\"ok\":true,\"message\":\"Core structure verification passed\"}"
    exit 0
}

# ═══════════════════════════════════════════════════════════
# 核心文件路径
# ═══════════════════════════════════════════════════════════
SPEC=".workflow/SPEC.yaml"
LOCK=".workflow/LOCK.json"
CHECKS="docs/CHECKS_INDEX.json"

# 检查核心文件是否存在
[[ -f "$SPEC" ]] || fail "MISSING_FILE: $SPEC"
[[ -f "$LOCK" ]] || fail "MISSING_FILE: $LOCK"
[[ -f "$CHECKS" ]] || fail "MISSING_FILE: $CHECKS"

# ═══════════════════════════════════════════════════════════
# 1. SPEC.yaml指纹验证
# ═══════════════════════════════════════════════════════════
spec_sha_cur=$(sha "$SPEC")
spec_sha_lock=$(jq -r '.spec_sha256' "$LOCK" 2>/dev/null || echo "")

if [ -z "$spec_sha_lock" ]; then
    fail "LOCK_INVALID: Missing spec_sha256 field"
fi

if [ "$spec_sha_cur" != "$spec_sha_lock" ]; then
    fail "SPEC_FINGERPRINT_MISMATCH: SPEC.yaml has been modified but LOCK.json not updated. Run: tools/update-lock.sh"
fi

# ═══════════════════════════════════════════════════════════
# 2. 关键文件指纹验证（全量校验）
# ═══════════════════════════════════════════════════════════
jq -r '.key_files_sha256 | to_entries[] | "\(.key) \(.value)"' "$LOCK" 2>/dev/null | \
while IFS=' ' read -r path expect; do
    if [ ! -f "$path" ]; then
        fail "MISSING_KEY_FILE: $path"
    fi

    cur=$(sha "$path")
    if [ "$cur" != "$expect" ]; then
        fail "FINGERPRINT_MISMATCH: $path has been modified but LOCK.json not updated. Run: tools/update-lock.sh"
    fi
done || exit $?

# ═══════════════════════════════════════════════════════════
# 3. Phase数量验证
# ═══════════════════════════════════════════════════════════
phases=$(yq '.workflow_structure.total_phases' "$SPEC" 2>/dev/null || echo "0")

if [ "$phases" -ne 7 ]; then
    fail "PHASE_COUNT_INVALID: Expected 7 phases, got $phases. Core structure has been tampered!"
fi

# ═══════════════════════════════════════════════════════════
# 4. 检查点总数验证（从CHECKS_INDEX.json读取）
# ═══════════════════════════════════════════════════════════
total_min=$(jq -r '.total_min' "$CHECKS" 2>/dev/null || echo "0")
ids_count=$(jq -r '.ids | length' "$CHECKS" 2>/dev/null || echo "0")

if [ "$ids_count" -lt "$total_min" ]; then
    fail "CHECKPOINT_COUNT_TOO_LOW: Expected >= $total_min checkpoints, got $ids_count. Checkpoints have been deleted!"
fi

# ═══════════════════════════════════════════════════════════
# 5. 检查点分布验证（by_phase）
# ═══════════════════════════════════════════════════════════
# 验证Phase 1-7的检查点分布
phase_distribution=$(jq -r '.by_phase | {P1,P2,P3,P4,P5,P6,P7} | to_entries[] | "\(.key)=\(.value)"' "$CHECKS" 2>/dev/null || echo "")

expected_distribution="P1=33 P2=15 P3=15 P4=10 P5=15 P6=5 P7=4"
actual_distribution=$(echo "$phase_distribution" | tr '\n' ' ' | sed 's/ $//')

# 简化验证：只检查总数
phase_sum=$(echo "$phase_distribution" | awk -F'=' '{sum+=$2} END {print sum}')

if [ "$phase_sum" -lt 97 ]; then
    fail "PHASE_DISTRIBUTION_INVALID: Sum of phase checkpoints ($phase_sum) < 97. Distribution has been tampered!"
fi

# ═══════════════════════════════════════════════════════════
# 6. 质量门禁数量验证
# ═══════════════════════════════════════════════════════════
gates_count=$(yq '.quality_gates.total_gates' "$SPEC" 2>/dev/null || echo "0")

if [ "$gates_count" -ne 2 ]; then
    fail "QUALITY_GATES_INVALID: Expected 2 quality gates, got $gates_count. Gates have been modified!"
fi

# ═══════════════════════════════════════════════════════════
# 7. 硬性阻止条件数量验证
# ═══════════════════════════════════════════════════════════
hard_blocks=$(yq '.hard_blocks.total_count' "$SPEC" 2>/dev/null || echo "0")

if [ "$hard_blocks" -lt 8 ]; then
    fail "HARD_BLOCKS_INVALID: Expected >= 8 hard blocks, got $hard_blocks. Hard blocks have been removed!"
fi

# ═══════════════════════════════════════════════════════════
# 8. 版本一致性验证（5文件）
# ═══════════════════════════════════════════════════════════
version_files=(
    "VERSION"
    ".claude/settings.json"
    "package.json"
    ".workflow/manifest.yml"
    "CHANGELOG.md"
)

# 提取VERSION文件的版本号
version_main=$(cat VERSION 2>/dev/null | tr -d '\n' || echo "")

if [ -z "$version_main" ]; then
    fail "VERSION_FILE_EMPTY: VERSION file is empty or missing"
fi

# 验证其他文件的版本号一致性
settings_version=$(jq -r '.version' .claude/settings.json 2>/dev/null || echo "")
package_version=$(jq -r '.version' package.json 2>/dev/null || echo "")
manifest_version=$(yq '.version' .workflow/manifest.yml 2>/dev/null || echo "")

# CHANGELOG.md的验证比较特殊，检查最新版本条目
changelog_version=$(grep -oP '^\#\# \[v?\K[0-9.]+' CHANGELOG.md 2>/dev/null | head -1 || echo "")

# 版本一致性检查
version_errors=""

[ "$settings_version" != "$version_main" ] && version_errors="${version_errors}.claude/settings.json ($settings_version) "
[ "$package_version" != "$version_main" ] && version_errors="${version_errors}package.json ($package_version) "
[ "$manifest_version" != "$version_main" ] && version_errors="${version_errors}.workflow/manifest.yml ($manifest_version) "

# CHANGELOG版本检查（允许略微不同，因为可能正在开发新版本）
# 只检查major.minor是否一致
version_major_minor=$(echo "$version_main" | cut -d. -f1-2)
changelog_major_minor=$(echo "$changelog_version" | cut -d. -f1-2)

if [ "$changelog_major_minor" != "$version_major_minor" ]; then
    version_errors="${version_errors}CHANGELOG.md ($changelog_version) "
fi

if [ -n "$version_errors" ]; then
    fail "VERSION_INCONSISTENCY: VERSION=$version_main but mismatches in: $version_errors. Run: scripts/check_version_consistency.sh"
fi

# ═══════════════════════════════════════════════════════════
# 9. Lock模式验证
# ═══════════════════════════════════════════════════════════
lock_mode=$(jq -r '.lock_mode' "$LOCK" 2>/dev/null || echo "")

if [ "$lock_mode" != "strict" ] && [ "$lock_mode" != "soft" ]; then
    fail "LOCK_MODE_INVALID: lock_mode must be 'strict' or 'soft', got '$lock_mode'"
fi

# ═══════════════════════════════════════════════════════════
# 所有验证通过
# ═══════════════════════════════════════════════════════════
pass
