#!/bin/bash
# Phase 1 Completion Enforcer Hook
# Purpose: Hard block if Phase 1 is complete but user hasn't confirmed
# Trigger: PreToolUse (before Write/Edit/Bash)
# Part of: Skills + Hooks dual-layer protection system

set -euo pipefail

TOOL_NAME="${TOOL_NAME:-unknown}"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Only check for Write/Edit/Bash tools (coding operations)
if [[ "$TOOL_NAME" != "Write" && "$TOOL_NAME" != "Edit" && "$TOOL_NAME" != "Bash" ]]; then
    exit 0
fi

# Check if Phase 1 is complete but unconfirmed
if [[ -f "$PROJECT_ROOT/.phase/current" ]]; then
    CURRENT_PHASE=$(tr -d '[:space:]' < "$PROJECT_ROOT/.phase/current")

    # Phase 1 complete detection:
    # - .phase/current shows Phase1
    # - All Phase 1 documents exist
    # - But no confirmation marker
    if [[ "$CURRENT_PHASE" == "Phase1" ]] && \
       [[ -f "$PROJECT_ROOT/docs/P1_DISCOVERY.md" ]] && \
       [[ -f "$PROJECT_ROOT/.workflow/ACCEPTANCE_CHECKLIST.md" ]] && \
       [[ -f "$PROJECT_ROOT/docs/PLAN.md" ]] && \
       [[ ! -f "$PROJECT_ROOT/.phase/phase1_confirmed" ]]; then

        # Phase 1 complete but user hasn't confirmed → HARD BLOCK
        echo "════════════════════════════════════════════════════════════"
        echo "❌ ERROR: Phase 1 completion requires user confirmation"
        echo "════════════════════════════════════════════════════════════"
        echo ""
        echo "📋 Phase 1 documents detected:"
        echo "   ✓ docs/P1_DISCOVERY.md"
        echo "   ✓ .workflow/ACCEPTANCE_CHECKLIST.md"
        echo "   ✓ docs/PLAN.md"
        echo ""
        echo "⚠️  But no user confirmation marker found!"
        echo ""
        echo "🔒 You MUST complete Phase 1 confirmation workflow:"
        echo ""
        echo "   Step 1: Display 7-Phase checklist to user"
        echo "           Show complete Phase 1-7 workflow with current status"
        echo ""
        echo "   Step 2: Explain implementation in plain language"
        echo "           No technical jargon, use before/after examples"
        echo ""
        echo "   Step 3: Wait for explicit user confirmation"
        echo "           User must say: 'I understand, start Phase 2'"
        echo "           OR similar clear confirmation"
        echo ""
        echo "   Step 4: Create confirmation marker"
        echo "           touch .phase/phase1_confirmed"
        echo ""
        echo "   Step 5: Update phase status"
        echo "           echo Phase2 > .phase/current"
        echo ""
        echo "💡 This is MANDATORY, not optional"
        echo "💡 See .claude/phase1_confirmation.yml for detailed spec"
        echo "════════════════════════════════════════════════════════════"

        exit 1  # Hard block
    fi
fi

# All checks passed
exit 0
