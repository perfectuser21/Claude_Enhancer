#!/bin/bash
# Claude Enhancer - Immutable Kernel Guard (PreToolUse Hook)
# Version: 1.0.0
# Purpose: Hard-block modifications to kernel files outside RFC process
# Hook Type: PreToolUse (before Write/Edit/git rm operations)

# This hook provides PROACTIVE protection (before modification attempt)
# vs CI Sentinel which provides REACTIVE protection (after push)

set -euo pipefail

# Get tool name and parameters
TOOL_NAME="${1:-}"
shift || true
ARGS=("$@")

# Extract file path from args
FILE_PATH=""
case "$TOOL_NAME" in
  Write|Edit)
    # For Write/Edit, file_path is usually the first argument
    FILE_PATH="${1:-}"
    ;;
  Bash)
    # For Bash, check if it's "git rm" or "rm" command
    BASH_CMD="${1:-}"
    if [[ "$BASH_CMD" =~ ^git[[:space:]]+rm || "$BASH_CMD" =~ ^rm[[:space:]]+ ]]; then
      # Extract file path from command
      FILE_PATH=$(echo "$BASH_CMD" | grep -oP '(?<=(git rm|rm) ).*' || true)
    fi
    ;;
  *)
    # Not a file-modifying tool, allow
    exit 0
    ;;
esac

# If no file path detected, allow (might be other operation)
[[ -z "$FILE_PATH" ]] && exit 0

# Define immutable kernel files
# These files CANNOT be modified without RFC process
KERNEL_FILES=(
  ".workflow/SPEC.yaml"
  ".workflow/manifest.yml"
  ".workflow/gates.yml"
  "docs/CHECKS_INDEX.json"
  "docs/PARALLEL_SUBAGENT_STRATEGY.md"
  "VERSION"
  ".claude/settings.json"
  "package.json"
  "CHANGELOG.md"
  ".workflow/LOCK.json"
)

# Check if file is in kernel list
is_kernel_file() {
  local file="$1"
  for kernel_file in "${KERNEL_FILES[@]}"; do
    if [[ "$file" == "$kernel_file" ]] || [[ "$file" == *"/$kernel_file" ]]; then
      return 0
    fi
  done
  return 1
}

# If not a kernel file, allow
if ! is_kernel_file "$FILE_PATH"; then
  exit 0
fi

# Get current branch
current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# Check if on RFC branch
if [[ "$current_branch" =~ ^rfc/ ]]; then
  # On RFC branch, allow modification (but remind user about RFC process)
  cat >&2 <<EOF

📋 Immutable Kernel Modification Detected

File: $FILE_PATH (kernel file ${KERNEL_FILES[@]/*$FILE_PATH*/found})
Branch: $current_branch ✓ (RFC branch)

✅ Modification allowed on RFC branch

💡 Remember to:
   1. Document changes in RFC document
   2. Explain Why/What/Impact
   3. Get user approval before merging
   4. Update .workflow/LOCK.json after changes

EOF
  exit 0
fi

# Not on RFC branch - HARD BLOCK
cat >&2 <<EOF

╔═══════════════════════════════════════════════════════════════╗
║  🛡️  IMMUTABLE KERNEL PROTECTION                            ║
╚═══════════════════════════════════════════════════════════════╝

❌ OPERATION BLOCKED: Cannot modify kernel file outside RFC process

📋 File: $FILE_PATH
🔒 Status: Immutable kernel file (10 protected files)
🌿 Current branch: $current_branch (must be rfc/*)

════════════════════════════════════════════════════════════════

📚 Protected Kernel Files (10):
   1. .workflow/SPEC.yaml
   2. .workflow/manifest.yml
   3. .workflow/gates.yml
   4. docs/CHECKS_INDEX.json
   5. docs/PARALLEL_SUBAGENT_STRATEGY.md  ← This prevents deletion!
   6. VERSION
   7. .claude/settings.json
   8. package.json
   9. CHANGELOG.md
  10. .workflow/LOCK.json

════════════════════════════════════════════════════════════════

🚨 To modify this file, you MUST follow RFC process:

   Step 1: Create RFC branch
      $ git checkout -b rfc/describe-your-change

   Step 2: Write RFC document explaining:
      - Why: Reason for modification
      - What: Specific changes to be made
      - Impact: Who/what will be affected
      - Rollback: How to undo if needed

   Step 3: Make your changes
      (Now the hook will allow modifications)

   Step 4: Get user approval
      User must explicitly approve RFC

   Step 5: Update .workflow/LOCK.json
      $ bash tools/update-lock.sh

   Step 6: Merge via PR
      Regular PR process with CI validation

════════════════════════════════════════════════════════════════

💡 Why this protection exists:
   These files define the core system structure. Modifications
   without proper planning and approval could break the system.

🔗 Learn more: .workflow/SPEC.yaml (immutable_kernel section)

════════════════════════════════════════════════════════════════

EOF

exit 1  # Hard block

