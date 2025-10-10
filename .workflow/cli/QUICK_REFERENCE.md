# Quick Reference: PR Automation & Gate Integration

Fast reference for common operations.

---

## PR Automator Quick Commands

### Create Pull Request
```bash
# Source the library
source .workflow/cli/lib/pr_automator.sh

# Create PR (auto-detects everything)
ce_pr_create

# Create draft PR
ce_pr_create --draft

# Create PR against different base
ce_pr_create --base=develop
```

### Check PR Status
```bash
# Get current branch's PR number
pr_number=$(ce_pr_get_current)

# Check if mergeable
ce_pr_check_mergeable $pr_number

# Check CI status
ce_pr_check_ci_status $pr_number

# Get full PR info (JSON)
ce_pr_get_info $pr_number
```

### Update PR
```bash
# Update PR title and description
ce_pr_update $pr_number

# Add comment
ce_pr_add_comment $pr_number "Updated based on review feedback"

# Update labels
ce_pr_update_labels $pr_number "bug,high-priority"
```

### Generate Content
```bash
# Generate PR title
ce_pr_generate_title

# Generate PR description
ce_pr_generate_description

# Generate quality metrics
ce_pr_add_metrics
```

---

## Gate Integrator Quick Commands

### Validate Gates
```bash
# Source the library
source .workflow/cli/lib/gate_integrator.sh

# Validate all gates
ce_gate_validate_all

# Validate phase-specific gates
ce_gate_validate_phase P3

# Validate single gate
ce_gate_validate_single code-quality
```

### Check Individual Gates
```bash
# Code quality (threshold 85)
ce_gate_check_score code-quality 85

# Test coverage (threshold 80%)
ce_gate_check_coverage 80

# Security scan
ce_gate_check_security

# Performance budget
ce_gate_check_performance

# BDD scenarios
ce_gate_check_bdd

# Signatures
ce_gate_check_signatures
```

### View Results
```bash
# Show summary
ce_gate_show_summary

# Show only failures
ce_gate_show_failures

# Generate full report
ce_gate_generate_report
# Output: .workflow/reports/gates_TIMESTAMP.md
```

### Manage Gates
```bash
# Mark gate as passed
ce_gate_mark_passed 03

# Read gate status
ce_gate_read_status 03

# Sign gate file
ce_gate_sign_gate_file 03.ok
```

---

## Common Workflows

### Workflow 1: Create PR with Quality Checks
```bash
# 1. Source both libraries
source .workflow/cli/lib/pr_automator.sh
source .workflow/cli/lib/gate_integrator.sh

# 2. Validate gates first
if ce_gate_validate_all; then
    echo "✓ All gates passed"

    # 3. Create PR
    pr_url=$(ce_pr_create)
    echo "PR created: $pr_url"
else
    echo "✗ Gates failed, fix issues before creating PR"
    ce_gate_show_failures
fi
```

### Workflow 2: Pre-Push Validation
```bash
source .workflow/cli/lib/gate_integrator.sh

# Run pre-push gates
ce_gate_run_on_push
```

### Workflow 3: CI/CD Integration
```bash
source .workflow/cli/lib/gate_integrator.sh

# Run full CI validation
ce_gate_run_in_ci

# Generate report
ce_gate_generate_report
```

### Workflow 4: Phase Completion
```bash
source .workflow/cli/lib/gate_integrator.sh

# Complete P3 phase
ce_gate_validate_phase P3 && ce_gate_mark_passed 03

# Then create PR
source .workflow/cli/lib/pr_automator.sh
ce_pr_create
```

---

## Integration with Hooks

### Pre-Commit Hook
```bash
#!/usr/bin/env bash
source .workflow/cli/lib/gate_integrator.sh
ce_gate_run_on_commit
```

### Pre-Push Hook
```bash
#!/usr/bin/env bash
source .workflow/cli/lib/gate_integrator.sh
ce_gate_run_on_push
```

---

## Environment Variables

### PR Automator
```bash
# Override PR template location
export CE_PR_TEMPLATE=".github/custom_pr_template.md"

# Override PR config
export CE_PR_CONFIG=".workflow/custom_pr_config.yml"
```

### Gate Integrator
```bash
# Override gates config
export CE_GATES_CONFIG=".workflow/custom_gates.yml"

# Override gates directory
export CE_GATES_DIR=".custom_gates"

# Override final gate script
export CE_FINAL_GATE_SCRIPT=".workflow/lib/custom_final_gate.sh"
```

---

## Output Interpretation

### PR Automator Output
- 🔵 Blue: Information/progress
- 🟢 Green: Success
- 🟡 Yellow: Warning (non-blocking)
- 🔴 Red: Error (blocking)

### Gate Integrator Output
```
✓  = Passed
✗  = Failed
⚠️ = Warning
⏳ = In Progress
```

---

## Troubleshooting

### PR Creation Fails
```bash
# Check if on valid branch
git branch --show-current
# Should NOT be main/master

# Check if commits exist
git log origin/main..HEAD
# Should show commits

# Check for conflicts
ce_pr_check_conflicts main
```

### GitHub CLI Not Working
```bash
# Check if gh is installed
ce_pr_check_gh_installed

# If not installed, fallback is automatic
# PR URL will be generated for browser
```

### Gate Validation Fails
```bash
# Show detailed failures
ce_gate_show_failures

# Check individual gates
ce_gate_check_score code-quality 85
ce_gate_check_coverage 80
ce_gate_check_security

# View full report
ce_gate_generate_report
```

### Coverage Data Missing
```bash
# Check if coverage file exists
ls -la coverage/coverage.xml

# Check format (should be JaCoCo XML)
head -20 coverage/coverage.xml
```

---

## Files and Paths

### Required Files
```
.workflow/cli/lib/pr_automator.sh      ✅ PR automation
.workflow/cli/lib/gate_integrator.sh   ✅ Gate validation
.workflow/lib/final_gate.sh            ✅ Core gate check
.workflow/gates.yml                     ✅ Gate config
```

### Optional Files
```
.github/PULL_REQUEST_TEMPLATE.md       ⭕ PR template
.github/CODEOWNERS                      ⭕ Reviewer mapping
coverage/coverage.xml                   ⭕ Coverage report
.workflow/_reports/quality_score.txt    ⭕ Quality score
metrics/perf_budget.yml                 ⭕ Performance budgets
acceptance/features/                    ⭕ BDD tests
```

### Generated Files
```
.gates/*.ok                            📝 Gate pass markers
.gates/*.ok.sig                        📝 Gate signatures
.workflow/reports/gates_*.md           📝 Gate reports
```

---

## Function Count

### PR Automator: 31 Functions
- Creation: 6
- Content: 8
- Metadata: 3
- Management: 5
- Status: 4
- Templates: 3
- Automation: 2

### Gate Integrator: 33 Functions
- Validation: 4
- Score: 3
- Coverage: 4
- Security: 3
- Performance: 3
- BDD: 2
- Signatures: 3
- Custom: 2
- Reporting: 3
- Config: 4
- Hooks: 3
- File Ops: 2

**Total: 64 Functions**

---

## Performance Tips

1. **PR Creation**: Use `gh` CLI for faster creation
2. **Gate Validation**: Run quick gates first (signatures, score)
3. **Coverage Parsing**: Cache coverage data if running multiple checks
4. **BDD Tests**: Run BDD in parallel when possible
5. **Reports**: Generate reports only when needed

---

## Best Practices

1. ✅ Always validate gates before creating PR
2. ✅ Use meaningful branch names (affects PR title)
3. ✅ Write descriptive commit messages (used in PR description)
4. ✅ Keep PRs focused and small (better reviews)
5. ✅ Run pre-push gates before pushing
6. ✅ Generate reports for audit trail
7. ✅ Sign gate files for production branches

---

## Examples

### Example 1: Full PR Workflow
```bash
# Start feature work
git checkout -b feature/user-auth-20251009-t1

# ... do development work ...

# Before creating PR
source .workflow/cli/lib/gate_integrator.sh
ce_gate_validate_all

# If gates pass, create PR
source .workflow/cli/lib/pr_automator.sh
ce_pr_create

# Output:
# Creating Pull Request...
# Validating branch readiness...
# ✓ Branch ready for PR
# Checking for conflicts with main...
# ✓ No conflicts detected
# Creating PR with GitHub CLI...
# ✓ PR created successfully
# PR URL: https://github.com/owner/repo/pull/123
```

### Example 2: Gate Report Generation
```bash
source .workflow/cli/lib/gate_integrator.sh

# Generate comprehensive report
report_file=$(ce_gate_generate_report)

# View report
cat "$report_file"

# Output:
# # Quality Gates Report
#
# **Generated:** 2025-10-09T12:34:56Z
# **Branch:** feature/user-auth-20251009-t1
#
# ## Overall Status
# **Status:** ✅ PASSED
# ...
```

### Example 3: PR Update After Changes
```bash
source .workflow/cli/lib/pr_automator.sh

# Get current PR number
pr_num=$(ce_pr_get_current)

# Update PR with latest changes
ce_pr_update $pr_num

# Add comment about changes
ce_pr_add_comment $pr_num "Updated based on review feedback"
```

---

## Quick Diagnostic

```bash
# Run this to check system status
echo "=== PR Automator Status ==="
source .workflow/cli/lib/pr_automator.sh
echo "Current branch: $(git rev-parse --abbrev-ref HEAD)"
echo "GitHub CLI: $(ce_pr_check_gh_installed && echo '✓ Available' || echo '✗ Not available')"
echo "Remote: $(ce_pr_parse_remote "$(git remote get-url origin)")"

echo -e "\n=== Gate Integrator Status ==="
source .workflow/cli/lib/gate_integrator.sh
ce_gate_show_summary
```

---

**Quick Reference Version**: 1.0
**Last Updated**: 2025-10-09
**Module**: PR Automation & Gate Integration
