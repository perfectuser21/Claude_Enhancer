#!/bin/bash
# Claude Enhancer - Main Branch Write Blocker (PreToolUse Hook)
# Version: 1.0.0
# Purpose: Hard-block Write/Edit operations on main/master branches
# Hook Type: PreToolUse (before Write/Edit operations)
#
# This hook upgrades force_branch_check.sh from warn-only to hard-block mode
# It prevents accidental modifications to main branch by blocking Write/Edit tools

set -euo pipefail

# Get tool name
TOOL_NAME="${1:-}"

# Only intercept Write/Edit tools
if [[ ! "$TOOL_NAME" =~ ^(Write|Edit)$ ]]; then
  exit 0  # Not a write operation, allow
fi

# Get current branch
current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# Check if on protected branch (main/master)
if [[ ! "$current_branch" =~ ^(main|master)$ ]]; then
  exit 0  # Not on protected branch, allow
fi

# Get file path being modified (for better error message)
FILE_PATH="${2:-unknown file}"

# HARD BLOCK: Cannot Write/Edit on main/master
cat >&2 <<EOF

╔═══════════════════════════════════════════════════════════════╗
║  🛡️  MAIN BRANCH WRITE PROTECTION                           ║
╚═══════════════════════════════════════════════════════════════╝

❌ OPERATION BLOCKED: Cannot write/edit files on main branch

🔧 Tool: $TOOL_NAME
📁 File: $FILE_PATH
🌿 Branch: $current_branch (protected)

════════════════════════════════════════════════════════════════

🚨 All work must be done on feature branches, not main/master.

💡 To proceed:

   Step 1: Create a feature branch
      $ git checkout -b feature/your-task-name

   Step 2: Start from Phase 1
      The workflow will automatically guide you through:
        • Phase 1: Discovery & Planning
        • Phase 2: Implementation (← you can make changes here)
        • Phase 3-7: Testing → Review → Release → Acceptance → Closure

   Step 3: Make your changes
      Now Write/Edit operations will be allowed

   Step 4: Commit and create PR
      $ git add .
      $ git commit -m "Your commit message"
      $ git push -u origin feature/your-task-name
      $ gh pr create

════════════════════════════════════════════════════════════════

💡 Why this protection exists:
   The main branch should only receive changes through PR merge.
   Direct modifications bypass the 7-Phase workflow, code review,
   and CI validation, which could break the system.

🔗 Learn more: CLAUDE.md (Phase 1-7 workflow section)

════════════════════════════════════════════════════════════════

EOF

exit 1  # Hard block

