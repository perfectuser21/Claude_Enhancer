#!/usr/bin/env bash
# Incident Report Generator
# Creates a comprehensive post-rollback analysis report

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

REPORT_DATE=$(date +%Y%m%d)
REPORT_FILE="docs/INCIDENT_REPORT_${REPORT_DATE}.md"

echo "Generating incident report..."

# Collect metrics
METRICS_FILE=".workflow/metrics.jsonl"
if [[ -f "$METRICS_FILE" ]]; then
    HOOK_TIME_P50=$(jq -s '[.[] | select(.enforcement_hook_time_ms != null) | .enforcement_hook_time_ms] | sort | .[length/2 | floor]' "$METRICS_FILE" 2>/dev/null || echo "N/A")
    HOOK_TIME_P95=$(jq -s '[.[] | select(.enforcement_hook_time_ms != null) | .enforcement_hook_time_ms] | sort | .[(length*0.95) | floor]' "$METRICS_FILE" 2>/dev/null || echo "N/A")
    ERROR_RATE=$(jq -s '[.[] | select(.error != null)] | length / input | . * 100' "$METRICS_FILE" 2>/dev/null || echo "N/A")
else
    HOOK_TIME_P50="N/A"
    HOOK_TIME_P95="N/A"
    ERROR_RATE="N/A"
fi

# Create report
cat > "$REPORT_FILE" <<EOF
# Enforcement Rollback Incident Report

## Summary
- **Date**: $(date)
- **Enforcement Version**: v6.2 → v6.1
- **Rollback Trigger**: [Manual/Automated]
- **Root Cause**: [To be determined]

## Timeline
- **Deploy**: 2025-10-11 00:00 UTC
- **First Alert**: [Timestamp of first issue]
- **Rollback Started**: [When emergency_rollback.sh ran]
- **Rollback Completed**: [When verification passed]
- **Total Duration**: [Deployment live time]

## Metrics at Rollback

### Performance
\`\`\`yaml
hook_execution:
  p50: ${HOOK_TIME_P50}ms (target: <300ms)
  p95: ${HOOK_TIME_P95}ms (target: <500ms)

cache:
  hit_ratio: N/A (target: >80%)
\`\`\`

### Quality
\`\`\`yaml
errors:
  rate: ${ERROR_RATE}% (target: <10%)

user_satisfaction:
  score: N/A (target: >=3.0/5.0)

adoption:
  rate: N/A (target: >40%)
\`\`\`

## Evidence Collected

### Logs
- Metrics: \`.workflow/metrics.jsonl\`
- Hook logs: \`.workflow/logs/enforcement_*.log\`
- Git logs: \`git log --oneline -20\`

### Artifacts
- Archived infrastructure: \`.workflow/archives/enforcement_*\`
- Rollback backup: \`.workflow/backups/rollback_*\`

### User Feedback
[Collect from]:
- Slack: #claude-enhancer
- GitHub Issues: [links]
- Support tickets: [IDs]

## Root Cause Analysis

### What Happened
[Detailed technical description of the issue]

### Why It Happened
- **Direct Cause**: [Immediate technical cause]
- **Contributing Factors**: [Environmental/design factors]
- **Prevention Missed**: [Why testing didn't catch it]

### Impact Assessment
- **Users Affected**: [Number/percentage]
- **Workflows Blocked**: [Which workflows]
- **Data Loss**: None (all evidence preserved)
- **Downtime**: [Duration if any]

## Corrective Actions

### Immediate (Done)
- [x] Rollback completed
- [x] Evidence preserved
- [x] Users notified

### Short-term (Next 1-2 weeks)
- [ ] Fix root cause
- [ ] Add regression test
- [ ] Update documentation
- [ ] Performance optimization

### Long-term (Next month)
- [ ] Improve testing strategy
- [ ] Enhance monitoring
- [ ] Review deployment process
- [ ] User training/communication

## Lessons Learned

### What Went Well
- [Positive aspects of response]

### What Went Wrong
- [Issues in detection/response]

### How to Prevent
- [Specific prevention strategies]

## Re-Deployment Plan

### Prerequisites
\`\`\`yaml
must_fix:
  - [ ] Root cause resolved
  - [ ] Regression tests added
  - [ ] Performance optimized (<500ms p95)
  - [ ] Documentation updated

must_verify:
  - [ ] All tests pass
  - [ ] Peer review approved
  - [ ] Canary deployment successful

must_communicate:
  - [ ] Release notes published
  - [ ] Training materials ready
  - [ ] Support team briefed
\`\`\`

### Timeline
- **Week 1**: Root cause fix + testing
- **Week 2**: Canary deployment (10% users)
- **Week 3**: Beta deployment (50% users)
- **Week 4+**: Full deployment (100% users)

## Appendix

### Related Documents
- Rollback plan: \`docs/AFFECTED_FILES_AND_ROLLBACK_PLAN.md\`
- Rollback notice: \`ROLLBACK_NOTICE.md\`
- Capability snapshot: \`scripts/capability_snapshot.sh\`

### Contact Information
- On-call: [Contact]
- Engineering Manager: [Contact]
- VP Engineering: [Contact]

---
*Report generated: $(date)*
*Author: [Your name]*
EOF

echo "✓ Incident report created: $REPORT_FILE"
echo ""
echo "Next steps:"
echo "  1. Fill in [bracketed] sections"
echo "  2. Attach logs and evidence"
echo "  3. Share with team"
echo "  4. Schedule post-mortem meeting"
