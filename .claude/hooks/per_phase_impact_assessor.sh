#!/bin/bash
# Per-Phase Impact Assessment Hook
# Triggers: PrePrompt (before each Phase starts)
# Purpose: Dynamically assess agent requirements for Phase2/3/4
#
# This implements per-phase dynamic assessment instead of global Phase 1.4 assessment.
# Each major phase (2, 3, 4) gets its own impact evaluation.

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
WORKFLOW_DIR="$PROJECT_ROOT/.workflow"
ASSESSOR_SCRIPT="$PROJECT_ROOT/.claude/scripts/impact_radius_assessor.sh"
IMPACT_DIR="$WORKFLOW_DIR/impact_assessments"

mkdir -p "$IMPACT_DIR"

# Get current phase
get_current_phase() {
    if [[ -f "$WORKFLOW_DIR/current" ]]; then
        grep "^phase:" "$WORKFLOW_DIR/current" | awk '{print $2}' || echo "Phase1"
    else
        echo "Phase1"
    fi
}

# Main logic
CURRENT_PHASE=$(get_current_phase)

# Only assess Phase2, Phase3, Phase4
# These are the phases where dynamic agent allocation is most valuable
case "$CURRENT_PHASE" in
    "Phase2"|"Phase3"|"Phase4")
        echo "📊 Running per-phase Impact Assessment for $CURRENT_PHASE..." >&2

        # Check if assessor script exists
        if [[ ! -f "$ASSESSOR_SCRIPT" ]]; then
            echo "⚠️  Warning: impact_radius_assessor.sh not found at $ASSESSOR_SCRIPT" >&2
            echo "   Per-phase assessment will be skipped (graceful degradation)" >&2
            exit 0
        fi

        # Run assessment
        OUTPUT_FILE="$IMPACT_DIR/${CURRENT_PHASE}_assessment.json"

        # Call assessor with phase-specific flag
        # Note: impact_radius_assessor.sh v1.4.0 supports --phase flag
        if bash "$ASSESSOR_SCRIPT" --phase "$CURRENT_PHASE" --output "$OUTPUT_FILE" 2>&1; then
            # Read and display recommendation
            if [[ -f "$OUTPUT_FILE" ]]; then
                RECOMMENDED_AGENTS=$(jq -r '.recommended_agents // 0' "$OUTPUT_FILE" 2>/dev/null || echo "0")
                RISK_SCORE=$(jq -r '.impact_radius_score // 0' "$OUTPUT_FILE" 2>/dev/null || echo "0")

                echo "" >&2
                echo "💡 $CURRENT_PHASE Impact Assessment Results:" >&2
                echo "   - Risk Score: $RISK_SCORE/100" >&2
                echo "   - Recommended Agents: $RECOMMENDED_AGENTS" >&2
                echo "" >&2
            fi
        else
            echo "⚠️  Assessment failed for $CURRENT_PHASE (non-critical)" >&2
            echo "   Continuing without per-phase assessment..." >&2
        fi
        ;;
    *)
        # Other phases don't need per-phase assessment
        # Phase1 does its own assessment manually in Phase 1.4
        # Phase5-7 are typically lower risk and don't need dynamic assessment
        ;;
esac

exit 0
