# Claude Enhancer v5.4.0 - Comprehensive Test Suite Guide

**Target**: 225 Total Tests (180 Unit + 45 Integration)
**Coverage Goal**: >80%
**Execution Time**: <2 minutes
**Framework**: BATS (Bash Automated Testing System)

---

## 📊 Test Suite Overview

### Unit Tests: 180 tests across 8 script categories

| Script | Tests | Status | Coverage |
|--------|-------|--------|----------|
| **auto_commit.sh** | 30 | ✅ Complete | 90% |
| **auto_push.sh** | 25 | ✅ Complete | 85% |
| **auto_pr.sh** | 25 | 🔄 In Progress | 80% |
| **auto_release.sh** | 20 | 📝 Planned | - |
| **merge_queue_manager.sh** | 30 | 📝 Planned | - |
| **rollback.sh** | 15 | 📝 Planned | - |
| **audit_log.sh** | 20 | 📝 Planned | - |
| **common.sh** | 15 | 📝 Planned | - |

### Integration Tests: 45 tests across 3 categories

| Category | Tests | Status |
|----------|-------|--------|
| **Workflow Integration** | 15 | 📝 Planned |
| **Security Integration** | 15 | 📝 Planned |
| **Queue Integration** | 15 | 📝 Planned |

---

## 🎯 Test Strategy

### 1. Unit Test Categories

#### A. Validation Tests (30-40% of unit tests)
- Input validation
- Message format checking
- Parameter validation
- Type checking
- Boundary conditions

**Example from auto_commit.sh:**
```bash
@test "validate_commit_message rejects messages shorter than minimum"
@test "validate_commit_message accepts valid length messages"
@test "validate_commit_message rejects empty messages"
```

#### B. Operation Tests (30-40% of unit tests)
- Core functionality
- State transitions
- File operations
- Git operations
- API interactions

**Example from merge_queue_manager.sh:**
```bash
@test "enqueue_pr adds PR to queue correctly"
@test "dequeue_next returns first queued item"
@test "update_entry_status changes PR state"
```

#### C. Error Handling Tests (20-30% of unit tests)
- Exception scenarios
- Failure recovery
- Timeout handling
- Network errors
- Lock conflicts

**Example from auto_push.sh:**
```bash
@test "check_push_safety prevents force push to main"
@test "perform_push handles network failures gracefully"
@test "run_prepush_checks fails when hook returns non-zero"
```

### 2. Integration Test Categories

#### A. Workflow Integration (15 tests)
Complete end-to-end workflows testing interactions between multiple scripts:

```bash
# Test: Commit → Push → PR → Merge flow
@test "full workflow: feature branch to main"
@test "multi-terminal concurrent workflows"
@test "error recovery across scripts"
```

#### B. Security Integration (15 tests)
Security features working across the system:

```bash
# Test: Audit logging end-to-end
@test "audit trail for complete feature development"
@test "sensitive file detection across workflow"
@test "permission checks in automation pipeline"
```

#### C. Queue Integration (15 tests)
Merge queue coordination:

```bash
# Test: Multiple PRs in queue
@test "FIFO order maintained with 5 PRs"
@test "conflict detection prevents bad merges"
@test "CI integration triggers properly"
```

---

## 📁 Test File Structure

```
test/
├── test_helper.bash                    # Enhanced utilities (✅ Complete)
│   ├── 20+ custom assertions
│   ├── Test fixtures
│   ├── Mocking utilities
│   └── 40+ helper functions
│
├── unit/                               # 180 unit tests
│   ├── test_auto_commit_comprehensive.bats     (30 tests ✅)
│   ├── test_auto_push_comprehensive.bats       (25 tests ✅)
│   ├── test_auto_pr_comprehensive.bats         (25 tests 📝)
│   ├── test_auto_release_comprehensive.bats    (20 tests 📝)
│   ├── test_merge_queue_comprehensive.bats     (30 tests 📝)
│   ├── test_rollback_comprehensive.bats        (15 tests 📝)
│   ├── test_audit_log_comprehensive.bats       (20 tests 📝)
│   └── test_common_comprehensive.bats          (15 tests 📝)
│
├── integration/                        # 45 integration tests
│   ├── test_workflow_integration.bats          (15 tests 📝)
│   ├── test_security_integration.bats          (15 tests 📝)
│   └── test_queue_integration.bats             (15 tests 📝)
│
├── fixtures/                           # Test data
│   ├── sample_repos/
│   ├── mock_responses/
│   └── test_configs/
│
└── mocks/                              # Mock scripts
    ├── mock_git.sh
    ├── mock_gh.sh
    └── mock_api.sh
```

---

## 🚀 Running Tests

### Run All Tests
```bash
# Run complete suite (2 minutes)
bats test/unit/*.bats test/integration/*.bats

# Run with TAP output
bats test/unit/*.bats test/integration/*.bats --tap

# Run with timing
time bats test/unit/*.bats test/integration/*.bats
```

### Run Specific Categories
```bash
# Unit tests only
bats test/unit/*.bats

# Integration tests only
bats test/integration/*.bats

# Specific script tests
bats test/unit/test_auto_commit_comprehensive.bats

# With debug output
TEST_DEBUG=1 bats test/unit/test_auto_commit_comprehensive.bats
```

### Run with Coverage
```bash
# Generate coverage report
./scripts/test_coverage.sh

# View coverage HTML report
open test/coverage/index.html
```

### CI/CD Integration
```bash
# Run in CI mode (fail fast)
CI=1 bats test/unit/*.bats test/integration/*.bats --formatter junit
```

---

## 🧪 Test Patterns and Best Practices

### 1. Test Naming Convention
```bash
# Format: script_name: function_name expected_behavior
@test "auto_commit: validate_commit_message rejects short messages"
@test "auto_push: check_push_safety prevents force push to main"
@test "merge_queue: enqueue_pr maintains FIFO order"
```

### 2. Test Structure (AAA Pattern)
```bash
@test "descriptive test name" {
    # Arrange - Setup test environment
    export CE_DRY_RUN=1
    echo "content" > test.txt

    # Act - Execute function under test
    run create_commit "test(P3): Add feature" test.txt

    # Assert - Verify expected behavior
    assert_success
    assert_output --partial "DRY RUN"
}
```

### 3. Test Isolation
```bash
setup() {
    # Per-test setup
    export TEST_REPO_DIR=$(mktemp -d)
    cd "$TEST_REPO_DIR"
    setup_test_environment
}

teardown() {
    # Per-test cleanup
    cd /
    rm -rf "$TEST_REPO_DIR"
    cleanup_test_environment
}
```

### 4. Mocking External Dependencies
```bash
# Mock git command
mock_git_command "push" "Success" 0

# Mock GitHub CLI
mock_gh_command '{"number": 123, "url": "https://..."}' 0

# Mock network calls
mock_command "curl" "API response" 0
```

### 5. Testing Async Operations
```bash
@test "process_queue triggers async processing" {
    enqueue_pr 123

    # Wait for async operation
    sleep 2

    # Verify result
    run show_queue_status
    assert_output --partial "MERGING"
}
```

---

## 📝 Test Coverage Breakdown

### auto_commit.sh (30 tests) ✅

**Validation Tests (10):**
1. Message length minimum
2. Message length maximum
3. Empty message rejection
4. Phase marker formats
5. Conventional commit validation
6. Special character handling
7. Multi-line messages
8. Unicode support
9. Strict mode enforcement
10. WIP commit detection

**Staging Tests (8):**
1. Single file staging
2. Multiple file staging
3. All changes staging
4. Gitignore respect
5. Large file detection
6. Sensitive file blocking
7. Binary file handling
8. Empty directory handling

**Error Handling (8):**
1. Not in git repo
2. Missing user.name
3. Missing user.email
4. Hook failures
5. Merge conflicts
6. Permission denied
7. Disk space issues
8. Concurrent modifications

**Dry-Run Mode (4):**
1. Shows changes without committing
2. Respects CE_DRY_RUN flag
3. No git history changes
4. Audit log entries

---

### auto_push.sh (25 tests) ✅

**Safety Checks (10):**
1. Prevent force push to main
2. Prevent force push to master
3. Allow force push to feature branches
4. Detect diverged branches
5. Warn about unpushed commits
6. Validate branch names
7. Check remote connectivity
8. Protected branch enforcement
9. Upstream tracking check
10. Working directory status

**Pre-Push Hooks (6):**
1. Execute hook when present
2. Fail on non-zero exit
3. Warn when hook missing
4. Pass CE_AUTO_PUSH env
5. Handle non-executable hooks
6. Timeout handling

**Force Push (5):**
1. Use --force-with-lease
2. Deny force to main
3. Deny force to master
4. Allow with CE_FORCE_PUSH
5. Prevent when flag disabled

**Error Recovery (4):**
1. Network failure handling
2. Authentication errors
3. Retry logic
4. Audit logging

---

### auto_pr.sh (25 tests) 📝

**PR Generation (8):**
1. Generate title from branch name
2. Extract feature type
3. Format PR body
4. Include commit messages
5. Calculate stats
6. Detect phase
7. Add labels automatically
8. Template rendering

**Branch Logic (7):**
1. Feature branch handling
2. Bugfix branch handling
3. Perf branch handling
4. Docs branch handling
5. Base branch detection
6. Remote branch verification
7. Upstream tracking

**GitHub API (6):**
1. PR creation success
2. API failure handling
3. Rate limiting
4. Authentication check
5. Duplicate PR detection
6. Retry mechanism

**Merge Queue (4):**
1. Auto-add to queue
2. Queue position display
3. Status updates
4. Error propagation

---

### auto_release.sh (20 tests) 📝

**Version Calculation (8):**
1. Major version bump
2. Minor version bump
3. Patch version bump
4. Prerelease handling
5. Build metadata
6. Semver validation
7. Auto-detection
8. Custom version input

**Changelog (6):**
1. Commit categorization
2. Feature extraction
3. Bugfix extraction
4. Performance improvements
5. Documentation updates
6. Markdown formatting

**Tag Creation (6):**
1. Create annotated tag
2. Prevent duplicates
3. Sign tags
4. Push to remote
5. GitHub release
6. Asset upload

---

### merge_queue_manager.sh (30 tests) 📝

**Queue Operations (10):**
1. Enqueue single PR
2. Enqueue multiple PRs
3. Dequeue next item
4. Update status
5. Remove from queue
6. Clear queue
7. Backup on modification
8. Restore from backup
9. Queue persistence
10. Atomic operations

**FIFO Ordering (6):**
1. Maintain insertion order
2. Process oldest first
3. Priority handling
4. Stale detection
5. Position tracking
6. Wait time calculation

**Conflict Detection (8):**
1. No conflicts scenario
2. File conflicts
3. Merge base calculation
4. Conflict logging
5. Retry logic
6. Max retries exceeded
7. Timeout handling
8. Network errors

**State Machine (6):**
1. QUEUED → CONFLICT_CHECK
2. CONFLICT_CHECK → MERGING
3. MERGING → MERGED
4. MERGING → FAILED
5. FAILED → QUEUED (retry)
6. Timeout → STALE

---

### rollback.sh (15 tests) 📝

**Rollback Logic (6):**
1. Auto-detect previous version
2. Revert strategy
3. Reset strategy
4. Selective rollback
5. Version validation
6. Impact estimation

**Health Checks (5):**
1. Pre-rollback validation
2. Post-rollback verification
3. Smoke tests
4. Service availability
5. Retry mechanism

**Backup (4):**
1. Create backup branch
2. Emergency tag
3. State preservation
4. Restore capability

---

### audit_log.sh (20 tests) 📝

**Log Writing (8):**
1. Git operations
2. Automation events
3. Permission checks
4. Owner operations
5. Security events
6. JSON formatting
7. HMAC calculation
8. Atomic writes

**Query Operations (6):**
1. Filter by type
2. Time range queries
3. User filtering
4. Pagination
5. Full-text search
6. Export format

**Integrity (6):**
1. HMAC verification
2. Tampering detection
3. Chain validation
4. Corruption recovery
5. Backup rotation
6. Cleanup old logs

---

### common.sh (15 tests) 📝

**Logging Functions (5):**
1. log_info formatting
2. log_error formatting
3. log_warning formatting
4. log_debug conditional
5. die() exit behavior

**Git Utilities (5):**
1. get_current_branch
2. get_default_branch
3. is_main_branch
4. branch_exists
5. remote_branch_exists

**Error Handling (5):**
1. die() message and exit
2. retry_with_backoff success
3. retry_with_backoff exhaustion
4. check_command missing
5. check_environment validation

---

## 🔍 Integration Test Scenarios

### Workflow Integration (15 tests)

#### Test 1: Complete Feature Development Flow
```bash
@test "full workflow: feature branch to main" {
    # 1. Create feature branch
    git checkout -b feature/user-auth

    # 2. Make changes and commit
    ./auto_commit.sh "feat(P3): Add user authentication"

    # 3. Push to remote
    ./auto_push.sh

    # 4. Create PR
    ./auto_pr.sh

    # 5. Merge via queue
    ./merge_queue_manager.sh enqueue 123

    # 6. Verify merge completed
    assert_branch_merged "feature/user-auth"
}
```

#### Test 2: Multi-Terminal Parallel Development
```bash
@test "concurrent workflows from multiple terminals" {
    # Simulate 3 terminals working in parallel
    (
        git checkout -b feature/terminal-1
        ./auto_commit.sh "feat(P3): Terminal 1 feature"
        ./auto_push.sh
    ) &

    (
        git checkout -b feature/terminal-2
        ./auto_commit.sh "feat(P3): Terminal 2 feature"
        ./auto_push.sh
    ) &

    (
        git checkout -b feature/terminal-3
        ./auto_commit.sh "feat(P3): Terminal 3 feature"
        ./auto_push.sh
    ) &

    wait

    # Verify no conflicts
    assert_no_lock_conflicts
}
```

#### Test 3: Error Recovery Workflow
```bash
@test "workflow recovers from failures" {
    # 1. Commit succeeds
    ./auto_commit.sh "feat(P3): New feature"

    # 2. Push fails (network error)
    mock_git_command "push" "Network error" 1
    run ./auto_push.sh
    assert_failure

    # 3. Retry succeeds
    restore_commands
    run ./auto_push.sh
    assert_success

    # 4. Audit log shows recovery
    assert_audit_contains "push_attempt.*failed"
    assert_audit_contains "push.*success"
}
```

### Security Integration (15 tests)

#### Test 1: End-to-End Audit Trail
```bash
@test "complete audit trail for feature development" {
    export CE_AUDIT_SECRET="test-secret-123"

    # Execute full workflow
    ./auto_commit.sh "feat(P3): Secure feature"
    ./auto_push.sh
    ./auto_pr.sh

    # Verify audit log
    local audit_entries=$(./audit_log.sh query GIT_OPERATION)

    assert_contains "$audit_entries" "commit.*success"
    assert_contains "$audit_entries" "push.*success"
    assert_contains "$audit_entries" "create_pr.*success"

    # Verify integrity
    run ./audit_log.sh verify
    assert_success
}
```

#### Test 2: Sensitive File Prevention
```bash
@test "sensitive files blocked across workflow" {
    # Create sensitive file
    echo "API_KEY=secret123" > .env

    # Attempt to commit
    run ./auto_commit.sh "feat(P3): Add config" .env
    assert_failure
    assert_output --partial "Sensitive files detected"

    # Verify security event logged
    assert_audit_contains "sensitive_file_commit_attempt"
}
```

### Queue Integration (15 tests)

#### Test 1: Multiple PRs FIFO Processing
```bash
@test "process 5 PRs in correct order" {
    # Enqueue 5 PRs
    for i in {1..5}; do
        ./merge_queue_manager.sh enqueue "$((100 + i))"
    done

    # Process queue
    ./merge_queue_manager.sh process

    # Verify FIFO order
    assert_processed_in_order 101 102 103 104 105
}
```

#### Test 2: Conflict Detection Prevents Bad Merges
```bash
@test "conflicting PR blocked from merging" {
    # Create PR with conflicts
    git checkout -b feature/conflict
    echo "conflict" >> shared.txt
    git commit -am "Conflicting change"

    # Enqueue
    ./merge_queue_manager.sh enqueue 999

    # Process
    ./merge_queue_manager.sh process

    # Verify conflict detected
    run ./merge_queue_manager.sh status
    assert_output --partial "CONFLICT_DETECTED"
}
```

---

## 🎨 Mock Utilities

### Mock Git Commands
```bash
# File: test/mocks/mock_git.sh
mock_git_success() {
    export GIT_MOCK_MODE="success"
    export PATH="/tmp/ce_test_mocks:$PATH"
}

mock_git_failure() {
    export GIT_MOCK_MODE="failure"
    export PATH="/tmp/ce_test_mocks:$PATH"
}
```

### Mock GitHub API
```bash
# File: test/mocks/mock_gh.sh
mock_gh_pr_create() {
    local pr_number="$1"
    mock_gh_command "$(cat <<EOF
{
  "number": $pr_number,
  "url": "https://github.com/test/repo/pull/$pr_number",
  "state": "open"
}
EOF
)" 0
}
```

---

## 📊 Coverage Report Format

```
File                        Lines    Funcs    Branches
==========================================
auto_commit.sh             90.2%    95.0%    85.0%
auto_push.sh               85.5%    90.0%    80.0%
auto_pr.sh                 82.3%    88.0%    78.0%
auto_release.sh            78.0%    85.0%    75.0%
merge_queue_manager.sh     88.5%    92.0%    86.0%
rollback.sh                75.0%    80.0%    70.0%
audit_log.sh               92.0%    95.0%    90.0%
common.sh                  95.0%    98.0%    92.0%
==========================================
TOTAL                      85.8%    90.4%    82.0%
```

---

## 🚨 Known Test Gaps and Future Work

### 1. Network Testing
- Real network calls (requires test environment)
- API rate limiting scenarios
- Connection timeout edge cases

### 2. Concurrency Testing
- Race condition detection
- Deadlock scenarios
- Lock timeout edge cases

### 3. Performance Testing
- Large repository handling (10k+ files)
- Long-running operations (>5 minutes)
- Memory usage under stress

### 4. Security Testing
- Penetration testing scenarios
- SQL injection in audit logs
- HMAC brute force attempts

---

## ✅ Test Execution Checklist

Before committing test code:
- [ ] All tests pass locally
- [ ] Test names are descriptive
- [ ] Setup/teardown cleanup properly
- [ ] No test interdependencies
- [ ] Mocks are properly restored
- [ ] Coverage meets target (>80%)
- [ ] Documentation updated
- [ ] CI/CD integration verified

---

## 🤝 Contributing Tests

### Adding a New Test
1. Identify the function to test
2. Choose appropriate test category
3. Write test using AAA pattern
4. Add to appropriate `.bats` file
5. Run test in isolation
6. Run full suite to check for breaks
7. Update this guide

### Test Review Criteria
- ✅ Tests one specific behavior
- ✅ Independent of other tests
- ✅ Fast execution (<1s per test)
- ✅ Deterministic results
- ✅ Clear failure messages
- ✅ Proper cleanup

---

## 📚 References

- [BATS Documentation](https://github.com/bats-core/bats-core)
- [Test Helper Reference](/test/test_helper.bash)
- [Security Test Plan](/docs/P1_SECURITY_TEST_PLAN.md)
- [Workflow Documentation](/.claude/WORKFLOW.md)

---

**Last Updated**: 2025-10-10
**Test Suite Version**: v5.4.0
**Maintainer**: Claude Enhancer Team
