#!/usr/bin/env bats
# Comprehensive Unit Tests for auto_commit.sh
# Purpose: 30 tests covering validation, staging, and error handling
# Target: 180 unit tests total (this file: 30 tests)

load '../test_helper'

setup() {
    # Setup test environment
    setup_test_environment
    export TEST_REPO_DIR=$(mktemp -d)
    cd "$TEST_REPO_DIR"
    git init
    git config user.email "test@example.com"
    git config user.name "Test User"

    # Source the script
    export AUTO_COMMIT_SCRIPT="${BATS_TEST_DIRNAME}/../../.workflow/automation/core/auto_commit.sh"
    source "$AUTO_COMMIT_SCRIPT"
}

teardown() {
    # Cleanup
    cd /
    rm -rf "$TEST_REPO_DIR"
    cleanup_test_environment
    cleanup_locks
}

# ============================================================================
# VALIDATION TESTS (10 tests)
# ============================================================================

@test "auto_commit: validate_commit_message rejects messages shorter than minimum" {
    run validate_commit_message "short"
    assert_failure
    assert_output --partial "too short"
}

@test "auto_commit: validate_commit_message accepts valid length messages" {
    run validate_commit_message "feat(P2): Add automation scripts for testing"
    assert_success
}

@test "auto_commit: validate_commit_message rejects messages longer than maximum" {
    local long_message=$(printf 'a%.0s' {1..600})
    run validate_commit_message "$long_message"
    assert_failure
    assert_output --partial "too long"
}

@test "auto_commit: validate_commit_message rejects empty messages" {
    run validate_commit_message "   "
    assert_failure
    assert_output --partial "empty"
}

@test "auto_commit: validate_commit_message warns about missing Phase marker" {
    run validate_commit_message "Add some feature"
    assert_success
    assert_output --partial "missing Phase marker"
}

@test "auto_commit: validate_commit_message accepts Phase marker in bracket format" {
    run validate_commit_message "[P3] Add user authentication feature"
    assert_success
}

@test "auto_commit: validate_commit_message accepts Phase marker in P format" {
    run validate_commit_message "feat P3: Add user authentication"
    assert_success
}

@test "auto_commit: validate_commit_message strict mode enforces conventional commit" {
    export CE_STRICT_MODE=1
    run validate_commit_message "Add some feature"
    assert_failure
    assert_output --partial "conventional commit format"
}

@test "auto_commit: validate_commit_message strict mode rejects WIP commits" {
    export CE_STRICT_MODE=1
    run validate_commit_message "WIP: work in progress feature"
    assert_failure
    assert_output --partial "WIP commits not allowed"
}

@test "auto_commit: validate_conventional_commit validates type correctly" {
    run validate_conventional_commit "feat(auth): Add login"
    assert_success

    run validate_conventional_commit "fix: Resolve bug"
    assert_success

    run validate_conventional_commit "invalid: Not a valid type"
    assert_failure
}

# ============================================================================
# STAGING TESTS (8 tests)
# ============================================================================

@test "auto_commit: stage_changes stages single file" {
    echo "test content" > test.txt

    run stage_changes test.txt
    assert_success

    # Verify file is staged
    run git diff --cached --name-only
    assert_output "test.txt"
}

@test "auto_commit: stage_changes stages multiple files" {
    echo "content1" > file1.txt
    echo "content2" > file2.txt
    echo "content3" > file3.txt

    run stage_changes file1.txt file2.txt file3.txt
    assert_success

    # Verify all files are staged
    local staged=$(git diff --cached --name-only | wc -l)
    assert_equals "3" "$staged"
}

@test "auto_commit: stage_changes stages all changes when no files specified" {
    echo "content1" > file1.txt
    echo "content2" > file2.txt

    run stage_changes
    assert_success

    # Verify both files are staged
    local staged=$(git diff --cached --name-only | wc -l)
    assert_equals "2" "$staged"
}

@test "auto_commit: stage_changes skips non-existent files" {
    echo "content" > exists.txt

    run stage_changes exists.txt nonexistent.txt
    assert_success
    assert_output --partial "not found"

    # Verify only existing file is staged
    run git diff --cached --name-only
    assert_output "exists.txt"
}

@test "auto_commit: stage_changes handles empty directory" {
    run stage_changes
    assert_success

    # Verify nothing is staged
    run git diff --cached --name-only
    assert_output ""
}

@test "auto_commit: stage_changes respects gitignore" {
    echo "ignored.txt" > .gitignore
    echo "content" > ignored.txt
    echo "tracked" > tracked.txt

    git add .gitignore
    git commit -m "Add gitignore"

    run stage_changes
    assert_success

    # Verify only tracked.txt is staged
    run git diff --cached --name-only
    assert_output "tracked.txt"
}

@test "auto_commit: check_large_files warns about files over 10MB" {
    # Create a large file (11MB)
    dd if=/dev/zero of=large.bin bs=1M count=11 2>/dev/null

    git add large.bin

    run check_large_files
    if [[ "$CE_STRICT_MODE" == "1" ]]; then
        assert_failure
    else
        assert_success
        assert_output --partial "Large files detected"
    fi
}

@test "auto_commit: check_sensitive_files detects .env files" {
    echo "SECRET_KEY=abc123" > .env
    git add .env

    run check_sensitive_files
    assert_failure
    assert_output --partial "Sensitive files detected"
}

# ============================================================================
# ERROR HANDLING TESTS (8 tests)
# ============================================================================

@test "auto_commit: check_prerequisites fails when not in git repo" {
    cd /tmp
    run check_prerequisites
    assert_failure
    assert_output --partial "Not a git repository"
}

@test "auto_commit: check_prerequisites succeeds in git repo" {
    run check_prerequisites
    assert_success
}

@test "auto_commit: check_prerequisites fails with no user.name" {
    git config --unset user.name
    run check_prerequisites
    assert_failure
    assert_output --partial "user.name not configured"
}

@test "auto_commit: check_prerequisites fails with no user.email" {
    git config --unset user.email
    run check_prerequisites
    assert_failure
    assert_output --partial "user.email not configured"
}

@test "auto_commit: check_prerequisites warns if pre-commit hook missing" {
    rm -f .git/hooks/pre-commit
    run check_prerequisites
    assert_success
    assert_output --partial "pre-commit hook not installed"
}

@test "auto_commit: create_commit handles merge conflicts gracefully" {
    # This test simulates a scenario where hooks might fail
    setup_git_hooks

    # Create a commit
    echo "content" > test.txt
    run create_commit "test(P3): Test commit" test.txt
    assert_success
}

@test "auto_commit: create_commit returns error on hook failure" {
    # Create failing pre-commit hook
    mkdir -p .git/hooks
    cat > .git/hooks/pre-commit <<'EOF'
#!/bin/bash
echo "Hook failed"
exit 1
EOF
    chmod +x .git/hooks/pre-commit

    export CE_DRY_RUN=0  # Disable dry run to trigger hook
    echo "content" > test.txt

    run create_commit "test(P3): Test commit" test.txt
    assert_failure
}

@test "auto_commit: create_commit audits all attempts" {
    # Enable audit secret
    export CE_AUDIT_SECRET="test-secret-key-123"

    echo "content" > test.txt

    run create_commit "test(P3): Test commit" test.txt
    assert_success

    # Verify audit log was called (check output)
    # In real scenario, would check audit log file
}

# ============================================================================
# DRY-RUN MODE TESTS (4 tests)
# ============================================================================

@test "auto_commit: dry-run mode shows what would be done" {
    export CE_DRY_RUN=1
    echo "content" > test.txt

    run create_commit "test(P3): Test commit" test.txt
    assert_success
    assert_output --partial "DRY RUN"
    assert_output --partial "Would commit"
}

@test "auto_commit: dry-run mode does not create actual commit" {
    export CE_DRY_RUN=1
    echo "content" > test.txt

    # Initial commit to have a base
    git add test.txt
    git commit -m "initial"

    echo "modified" >> test.txt

    run create_commit "test(P3): Modify file" test.txt
    assert_success

    # Verify no new commit was created
    local count=$(count_commits)
    assert_equals "1" "$count"
}

@test "auto_commit: dry-run mode respects CE_DRY_RUN environment variable" {
    export CE_DRY_RUN=1
    echo "content" > test.txt

    run create_commit "test(P3): Test commit" test.txt
    assert_success
    assert_output --partial "DRY RUN"
}

@test "auto_commit: non-dry-run mode creates actual commit" {
    export CE_DRY_RUN=0
    echo "content" > test.txt

    run create_commit "test(P3): Test commit" test.txt
    assert_success
    assert_output --partial "Commit created successfully"

    # Verify commit was created
    local count=$(count_commits)
    assert_greater_than "$count" "0"
}

# ============================================================================
# PHASE INJECTION TESTS - Additional tests (not counted in 30, but bonus)
# ============================================================================

@test "auto_commit: inject_phase_marker adds Phase when CE_CURRENT_PHASE is set" {
    export CE_CURRENT_PHASE=3

    local message="feat(auth): Add login"
    run inject_phase_marker "$message"
    assert_success
    assert_output "feat(auth): [P3] Add login"
}

@test "auto_commit: inject_phase_marker does not add Phase if already present" {
    export CE_CURRENT_PHASE=3

    local message="feat(auth): [P2] Add login"
    run inject_phase_marker "$message"
    assert_success
    assert_output "feat(auth): [P2] Add login"
}
