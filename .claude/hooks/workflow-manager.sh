#!/bin/bash
# 5-Phase Workflow Manager

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 5-PHASE WORKFLOW STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get current phase from file or default to Phase 1
PHASE_FILE=".claude/.workflow_phase"
if [ -f "$PHASE_FILE" ]; then
    CURRENT_PHASE=$(cat "$PHASE_FILE")
else
    CURRENT_PHASE=1
    echo "1" > "$PHASE_FILE"
fi

# Display workflow phases
echo "
Phase 0: Git Setup       [✓] Complete
Phase 1: Requirements    $([ $CURRENT_PHASE -ge 1 ] && echo '[→] Active' || echo '[ ] Pending')
Phase 2: Architecture    $([ $CURRENT_PHASE -ge 2 ] && echo '[→] Active' || echo '[ ] Pending')
Phase 3: Development     $([ $CURRENT_PHASE -ge 3 ] && echo '[→] Active' || echo '[ ] Pending')
Phase 4: Testing         $([ $CURRENT_PHASE -ge 4 ] && echo '[→] Active' || echo '[ ] Pending')
Phase 5: Deployment      $([ $CURRENT_PHASE -ge 5 ] && echo '[→] Active' || echo '[ ] Pending')
"

# Suggest next actions based on phase
case $CURRENT_PHASE in
    1)
        echo "💡 Next: Analyze requirements with business-analyst, requirements-analyst"
        ;;
    2)
        echo "💡 Next: Design architecture with backend-architect, database-specialist"
        ;;
    3)
        echo "💡 Next: Implement with 3+ development agents in parallel"
        ;;
    4)
        echo "💡 Next: Run tests with test-engineer, e2e-test-specialist"
        ;;
    5)
        echo "💡 Next: Deploy with devops-engineer, create PR"
        ;;
esac

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"