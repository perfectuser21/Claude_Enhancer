# Anti-Hollow Contract Tests

## Overview

Contract tests that verify critical features **actually WORK**, not just exist.

This is different from unit tests or integration tests - these tests verify that advertised functionality delivers on its promises.

## Location

```
/home/xx/dev/Claude Enhancer/tests/contract/test_anti_hollow.sh
```

## Test Cases (4 Total)

### Contract Test 1: parallel_subagent_suggester.sh Execution
**What it verifies:** The parallel subagent suggester hook actually executes and produces output.

**Assertions:**
- Hook runs without fatal error (exit code 0)
- Log file created at `.workflow/logs/subagent/suggester.log`
- Log contains current phase name ("Phase2")
- Log contains timestamp (proving it actually ran)
- Output includes suggestion markers

### Contract Test 2: phase_manager.sh Transitions
**What it verifies:** Phase transitions actually work and update state correctly.

**Assertions:**
- `phase_manager.sh` can be sourced
- `ce_phase_transition()` function exists
- Transition from P2 to P3 succeeds
- `.phase/current` file updated correctly
- Output confirms the transition
- Invalid phase codes are rejected properly

### Contract Test 3: Bypass Permissions Configuration
**What it verifies:** Bypass permissions are configured correctly in settings.json.

**Assertions:**
- `settings.json` exists
- `defaultMode` equals `"bypassPermissions"`
- Critical tools are in allow list: Bash, Read, Write, Edit, Glob, Grep

### Contract Test 4: Critical Hooks Registration
**What it verifies:** All P0 (priority 0) hooks are registered and executable.

**Assertions:**
- PrePrompt hooks registered: force_branch_check, workflow_enforcer, parallel_subagent_suggester
- PreToolUse hooks registered: task_branch_enforcer, code_writing_check, quality_gate
- Hook files exist and are executable

## Usage

### Run All Tests

```bash
cd /home/xx/dev/Claude\ Enhancer
bash tests/contract/test_anti_hollow.sh
```

### Expected Output (Success)

```
***********************************************************************
*                    ANTI-HOLLOW CONTRACT TESTS                      *
***********************************************************************

[INFO] Setting up test environment...
[PASS] Test environment ready

======================================================================
CONTRACT TEST 1: parallel_subagent_suggester.sh Actually Executes
======================================================================
[PASS] Assert: Hook should exit successfully (exit code 0)
[PASS] Assert: Suggester log should be created
...

======================================================================
                        TEST SUMMARY
======================================================================

Total Tests:  4
Passed:       4
Failed:       0

========================================
  ALL CONTRACT TESTS PASSED!
  Features are ACTUALLY working!
========================================
```

### Exit Codes

- **0**: All contracts passed ✅
- **1**: Some contracts failed ❌

## Features

- ✅ **Clear PASS/FAIL output** with color coding
- ✅ **Well-documented** with inline comments
- ✅ **Setup and teardown** functions
- ✅ **Backup and restore** of `.phase/current`
- ✅ **27+ comprehensive assertions**
- ✅ **Exit code 0** only if ALL contracts pass
- ✅ **Test summary** with counts

## Philosophy

These tests answer the question: **"Does this feature actually work, or is it just hollow documentation?"**

Unlike traditional tests:
- We don't mock - we test the real thing
- We verify outputs, not just function calls
- We check side effects (files created, state updated)
- We test the happy path AND error handling

## Adding New Contract Tests

Template:

```bash
test_your_feature() {
    echo ""
    echo "======================================================================"
    echo "CONTRACT TEST N: Your Feature Name"
    echo "======================================================================"
    echo ""

    local test_passed=true

    # Setup
    log_info "Setup: ..."

    # Run
    log_info "Running: ..."

    # Assert
    if ! assert_something; then
        test_passed=false
    fi

    # Report
    echo ""
    if $test_passed; then
        log_success "CONTRACT TEST N: PASSED"
        ((PASSED_CONTRACTS++))
    else
        log_failure "CONTRACT TEST N: FAILED"
        ((FAILED_CONTRACTS++))
    fi
}
```

## Maintenance

- Update when critical features are added
- Keep test count in sync with README
- Run before major releases
- Run when refactoring core features

## Version History

- **1.0.0** (2025-10-30): Initial version with 4 contract tests
