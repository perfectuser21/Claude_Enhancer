#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# update-lock.sh - 唯一LOCK.json更新入口
# Version: 1.0.0
# Purpose: 更新.workflow/LOCK.json指纹锁定文件
# Author: Claude Code (Lockdown Mechanism)
# Date: 2025-10-20
# Usage: bash tools/update-lock.sh
# ═══════════════════════════════════════════════════════════
set -euo pipefail

# ═══════════════════════════════════════════════════════════
# 依赖检查
# ═══════════════════════════════════════════════════════════
need() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "ERROR: Missing dependency: $1"
        echo "Install: sudo apt-get install $1  # or brew install $1"
        exit 2
    }
}

need jq
need yq

# 检测sha256命令
if command -v sha256sum >/dev/null 2>&1; then
    SHA_CMD="sha256sum"
elif command -v shasum >/dev/null 2>&1; then
    SHA_CMD="shasum -a 256"
else
    echo "ERROR: Missing sha256sum or shasum command"
    exit 2
fi

# ═══════════════════════════════════════════════════════════
# 计算文件指纹
# ═══════════════════════════════════════════════════════════
sha() {
    if [ ! -f "$1" ]; then
        echo "ERROR: File not found: $1" >&2
        exit 1
    fi
    $SHA_CMD "$1" | awk '{print $1}'
}

# ═══════════════════════════════════════════════════════════
# 验证必需文件存在
# ═══════════════════════════════════════════════════════════
required_files=(
    ".workflow/SPEC.yaml"
    ".workflow/gates.yml"
    "docs/CHECKS_INDEX.json"
    "scripts/workflow_validator_v97.sh"
    "scripts/pre_merge_audit.sh"
    "scripts/static_checks.sh"
    "tools/verify-core-structure.sh"
)

echo "Checking required files..."
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: Required file not found: $file"
        exit 1
    fi
    echo "  ✓ $file"
done

# ═══════════════════════════════════════════════════════════
# 读取当前版本
# ═══════════════════════════════════════════════════════════
if [ ! -f "VERSION" ]; then
    echo "ERROR: VERSION file not found"
    exit 1
fi

VERSION=$(cat VERSION | tr -d '\n')
echo "Current version: $VERSION"

# ═══════════════════════════════════════════════════════════
# 计算所有关键文件的指纹
# ═══════════════════════════════════════════════════════════
echo ""
echo "Calculating file fingerprints..."

spec_sha=$(sha ".workflow/SPEC.yaml")
echo "  SPEC.yaml: $spec_sha"

gates_sha=$(sha ".workflow/gates.yml")
echo "  gates.yml: $gates_sha"

checks_sha=$(sha "docs/CHECKS_INDEX.json")
echo "  CHECKS_INDEX.json: $checks_sha"

validator_sha=$(sha "scripts/workflow_validator_v97.sh")
echo "  workflow_validator_v97.sh: $validator_sha"

audit_sha=$(sha "scripts/pre_merge_audit.sh")
echo "  pre_merge_audit.sh: $audit_sha"

static_sha=$(sha "scripts/static_checks.sh")
echo "  static_checks.sh: $static_sha"

verify_sha=$(sha "tools/verify-core-structure.sh")
echo "  verify-core-structure.sh: $verify_sha"

# ═══════════════════════════════════════════════════════════
# 生成LOCK.json
# ═══════════════════════════════════════════════════════════
echo ""
echo "Generating .workflow/LOCK.json..."

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

jq -n \
  --arg spec_sha "$spec_sha" \
  --arg gates_sha "$gates_sha" \
  --arg checks_sha "$checks_sha" \
  --arg validator_sha "$validator_sha" \
  --arg audit_sha "$audit_sha" \
  --arg static_sha "$static_sha" \
  --arg verify_sha "$verify_sha" \
  --arg timestamp "$TIMESTAMP" \
  --arg version "$VERSION" \
  '{
    "spec_sha256": $spec_sha,
    "generated_at": $timestamp,
    "generated_by": "tools/update-lock.sh",
    "core_structure": {
      "total_phases": 7,
      "total_checkpoints": 97,
      "quality_gates": 2,
      "hard_blocks": 8
    },
    "key_files_sha256": {
      ".workflow/SPEC.yaml": $spec_sha,
      ".workflow/gates.yml": $gates_sha,
      "docs/CHECKS_INDEX.json": $checks_sha,
      "scripts/workflow_validator_v97.sh": $validator_sha,
      "scripts/pre_merge_audit.sh": $audit_sha,
      "scripts/static_checks.sh": $static_sha,
      "tools/verify-core-structure.sh": $verify_sha
    },
    "version": $version,
    "lock_mode": "soft",
    "lock_mode_comment": "观测期使用soft模式，7天后切换为strict"
  }' > .workflow/LOCK.json

echo "✓ LOCK.json generated successfully"

# ═══════════════════════════════════════════════════════════
# 验证生成的LOCK.json格式
# ═══════════════════════════════════════════════════════════
echo ""
echo "Validating LOCK.json format..."

if ! jq empty .workflow/LOCK.json 2>/dev/null; then
    echo "ERROR: Generated LOCK.json is not valid JSON"
    exit 1
fi

# 验证必需字段
required_fields=(
    "spec_sha256"
    "generated_at"
    "core_structure"
    "key_files_sha256"
    "version"
    "lock_mode"
)

for field in "${required_fields[@]}"; do
    value=$(jq -r ".$field" .workflow/LOCK.json 2>/dev/null || echo "")
    if [ -z "$value" ] || [ "$value" == "null" ]; then
        echo "ERROR: Missing required field: $field"
        exit 1
    fi
done

echo "✓ LOCK.json validation passed"

# ═══════════════════════════════════════════════════════════
# 显示结果
# ═══════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  LOCK.json Updated Successfully"
echo "═══════════════════════════════════════════════════════"
echo "Version: $VERSION"
echo "Timestamp: $TIMESTAMP"
echo "Lock mode: soft (观测期)"
echo "Files locked: 7"
echo ""
echo "Next steps:"
echo "  1. Review .workflow/LOCK.json"
echo "  2. Run: bash tools/verify-core-structure.sh"
echo "  3. Add to git: git add .workflow/LOCK.json"
echo "  4. Commit: git commit -m 'chore: Update LOCK.json'"
echo "═══════════════════════════════════════════════════════"
