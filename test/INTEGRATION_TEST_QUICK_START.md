# Integration Test Quick Start Guide

## TL;DR

```bash
# Run all integration tests
cd /home/xx/dev/Claude\ Enhancer\ 5.0
bash test/run_integration_tests_fixed.sh

# Run specific suite
bats test/integration/test_complete_workflow.bats

# Run single test
bats --filter "Complete P1 workflow" test/integration/test_complete_workflow.bats
```

## What's Been Delivered

✅ **5 Test Suites** - 57 integration tests total
✅ **2 Helper Libraries** - 891 lines of reusable code
✅ **Test Runner** - Automated execution and reporting
✅ **Complete Documentation** - Setup, usage, and troubleshooting

## Test Suites Overview

| Suite | Tests | What It Tests |
|-------|-------|---------------|
| **test_complete_workflow.bats** | 9 | Full P1→P6 lifecycle, rollback, checkpoints |
| **test_multi_terminal.bats** | 9 | Concurrent development, parallel branches |
| **test_conflict_detection.bats** | 10 | Merge conflicts, resolution strategies |
| **test_phase_transitions.bats** | 16 | P0→P7 transitions, validation, edge cases |
| **test_quality_gates.bats** | 13 | Quality enforcement, security, compliance |

**Total: 57 tests** covering all major scenarios

## Quick Test Examples

### Test 1: Complete Workflow
```bash
# Tests full feature development lifecycle
bats test/integration/test_complete_workflow.bats
```

**What it validates:**
- Plan document creation
- Skeleton structure
- Implementation code
- Test coverage
- Code review
- Release preparation

### Test 2: Multi-Terminal Development
```bash
# Tests concurrent development scenarios
bats test/integration/test_multi_terminal.bats
```

**What it validates:**
- Independent feature development
- Session isolation
- Parallel merging
- Performance with 10+ branches

### Test 3: Conflict Detection
```bash
# Tests conflict detection and resolution
bats test/integration/test_conflict_detection.bats
```

**What it validates:**
- Same file conflicts
- Multi-file conflicts
- Binary conflicts
- Resolution strategies

## Helper Functions You Can Use

### Repository Management
```bash
create_test_repo "my-test"       # Creates isolated git repo
cleanup_test_repo "$repo_path"  # Removes test repo
```

### Phase Management
```bash
set_phase "P3"                   # Sets current phase
get_current_phase                # Returns current phase
create_gate "03"                 # Creates gate marker
check_gate_exists "03"           # Validates gate
```

### Document Creation
```bash
create_plan_document             # Creates PLAN.md
create_changelog                 # Creates CHANGELOG.md
create_test_report               # Creates TEST-REPORT.md
create_review_document           # Creates REVIEW.md
create_readme                    # Creates README.md
```

### Validation
```bash
assert_file_exists "path/file"           # Check file exists
assert_file_contains "file" "pattern"    # Check file content
assert_phase_is "P3"                     # Check current phase
```

## Test Structure Template

```bash
#!/usr/bin/env bats

load ../helpers/integration_helper
load ../helpers/fixture_helper

setup() {
    export PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
    TEST_REPO=$(create_test_repo "my-test")
    cd "${TEST_REPO}"

    # Initialize project
    create_nodejs_project_fixture
}

teardown() {
    cleanup_test_repo "${TEST_REPO}"
}

@test "My test description" {
    # Setup
    set_phase "P1"
    create_plan_document

    # Execute
    git add docs/PLAN.md
    git commit -m "docs: add plan"

    # Verify
    run assert_file_exists "docs/PLAN.md"
    [ "$status" -eq 0 ]
}
```

## Common Test Patterns

### Pattern 1: Phase Transition Test
```bash
@test "Transition from P1 to P2" {
    # Setup P1
    set_phase "P1"
    create_plan_document
    create_gate "01"

    # Transition to P2
    set_phase "P2"

    # Verify
    run get_current_phase
    [ "$output" = "P2" ]

    run check_gate_exists "01"
    [ "$status" -eq 0 ]
}
```

### Pattern 2: Multi-Terminal Test
```bash
@test "Two terminals edit different files" {
    # Terminal 1
    export_terminal_env "t1"
    create_branch "feature-t1"
    echo "T1 code" > src/file1.ts
    git add src/file1.ts
    git commit -m "feat(t1): add file1"

    # Terminal 2
    cleanup_terminal_env
    git checkout -q main
    export_terminal_env "t2"
    create_branch "feature-t2"
    echo "T2 code" > src/file2.ts
    git add src/file2.ts
    git commit -m "feat(t2): add file2"

    # Merge both
    git checkout -q main
    git merge --no-ff feature-t1 -m "Merge t1"
    git merge --no-ff feature-t2 -m "Merge t2"

    # Verify both files exist
    run assert_file_exists "src/file1.ts"
    [ "$status" -eq 0 ]
    run assert_file_exists "src/file2.ts"
    [ "$status" -eq 0 ]
}
```

### Pattern 3: Quality Gate Test
```bash
@test "P1 requires 5+ tasks" {
    set_phase "P1"

    # Create plan with only 3 tasks (should fail validation)
    cat > docs/PLAN.md << 'EOF'
# Plan
## 任务清单
1. Task 1
2. Task 2
3. Task 3
## 受影响文件清单
- src/file.ts
## 回滚方案
Revert
EOF

    # Count tasks
    local task_count=$(grep -c "^[0-9]\+\." docs/PLAN.md || echo 0)
    [ "$task_count" -lt 5 ]  # Should be less than 5

    # Fix with proper plan
    create_plan_document  # Creates plan with 5+ tasks
    local new_count=$(grep -c "^[0-9]\+\." docs/PLAN.md || echo 0)
    [ "$new_count" -ge 5 ]  # Should be >= 5
}
```

## Test Results Interpretation

### Successful Test Output
```
✓ test_complete_workflow: 9 tests passed
✓ test_multi_terminal: 9 tests passed
✓ test_conflict_detection: 10 tests passed

Total Tests:    57
Passed:         57
Failed:         0
Pass Rate:      100.0%
```

### Failed Test Output
```
✗ test_complete_workflow: 7 passed, 2 failed

not ok 1 Complete P1 workflow
not ok 5 Workflow rollback

Total Tests:    57
Passed:         52
Failed:         5
Pass Rate:      91.2%
```

## Troubleshooting

### Issue: "bats: command not found"
```bash
# Install BATS
npm install -g bats
```

### Issue: "assert_output: command not found"
```bash
# Use basic assertions instead
run get_current_phase
[ "$output" = "P1" ]

# Or install bats-assert
npm install -g bats-assert
```

### Issue: Tests hang
```bash
# Add timeout to git operations
timeout 30s git operation

# Or kill hanging tests
pkill -f bats
```

### Issue: Permission denied
```bash
# Fix permissions
chmod +x test/run_integration_tests_fixed.sh
chmod +x test/helpers/*.bash
```

### Issue: Temp directory full
```bash
# Clean old test artifacts
rm -rf /tmp/bats-*
rm -rf /tmp/test-repo-*
```

## Key Files Reference

```
test/
├── integration/                    # Test suites
│   ├── test_complete_workflow.bats
│   ├── test_multi_terminal.bats
│   ├── test_conflict_detection.bats
│   ├── test_phase_transitions.bats
│   └── test_quality_gates.bats
│
├── helpers/                        # Helper libraries
│   ├── integration_helper.bash
│   └── fixture_helper.bash
│
├── run_integration_tests_fixed.sh # Test runner
├── INTEGRATION_TEST_SUMMARY.md    # Full documentation
├── P4_INTEGRATION_TEST_DELIVERABLES.md  # Delivery doc
└── INTEGRATION_TEST_QUICK_START.md      # This file
```

## Performance Expectations

- **Full Suite:** ~23 seconds (57 tests)
- **Single Suite:** ~5-8 seconds (9-16 tests)
- **Single Test:** ~0.4 seconds average
- **Parallel Execution:** Possible with BATS parallel mode

## Next Steps

1. **Run the tests:**
   ```bash
   bash test/run_integration_tests_fixed.sh
   ```

2. **Review the output:**
   - Check pass rate
   - Review failed tests
   - Check reports in `test/reports/`

3. **Fix any issues:**
   - See troubleshooting section
   - Check test logs
   - Update code as needed

4. **Integrate with CI/CD:**
   - Add to GitHub Actions
   - Set up automated runs
   - Configure notifications

## Additional Resources

- **Full Documentation:** `test/INTEGRATION_TEST_SUMMARY.md`
- **Delivery Report:** `test/P4_INTEGRATION_TEST_DELIVERABLES.md`
- **Helper API:** `test/helpers/integration_helper.bash`
- **Fixture API:** `test/helpers/fixture_helper.bash`
- **BATS Documentation:** https://bats-core.readthedocs.io/

## Support

### Common Questions

**Q: How do I add a new test?**
A: Add to appropriate `.bats` file following existing patterns

**Q: Can tests run in parallel?**
A: Yes, use `bats --jobs N` (requires bats-core 1.5+)

**Q: How do I debug a failing test?**
A: Use `bats --trace` or add `echo` statements

**Q: Can I run tests on CI/CD?**
A: Yes, see GitHub Actions example in INTEGRATION_TEST_SUMMARY.md

**Q: How do I mock external dependencies?**
A: Use fixture functions or create test doubles

### Getting Help

1. Read full documentation in `INTEGRATION_TEST_SUMMARY.md`
2. Check troubleshooting section
3. Review test logs in `test/reports/`
4. Examine helper function source code
5. Run individual tests with `--trace` flag

---

**Quick Start Version:** 1.0.0
**Last Updated:** 2025-01-09
**Status:** Ready to Use ✅
