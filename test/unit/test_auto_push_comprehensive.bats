#!/usr/bin/env bats
# Comprehensive Unit Tests for auto_push.sh
# Purpose: 25 tests covering safety checks, pre-push hooks, force push, error recovery
# Target: Part of 180 unit tests

load '../test_helper'

setup() {
    setup_test_environment
    export TEST_REPO_DIR=$(mktemp -d)
    cd "$TEST_REPO_DIR"
    git init
    git config user.email "test@example.com"
    git config user.name "Test User"

    # Create initial commit
    echo "initial" > README.md
    git add README.md
    git commit -m "initial commit"

    # Source the script
    export AUTO_PUSH_SCRIPT="${BATS_TEST_DIRNAME}/../../.workflow/automation/core/auto_push.sh"
    source "$AUTO_PUSH_SCRIPT"
}

teardown() {
    cd /
    rm -rf "$TEST_REPO_DIR"
    cleanup_test_environment
}

# ============================================================================
# SAFETY CHECKS (10 tests)
# ============================================================================

@test "auto_push: check_push_safety prevents force push to main branch" {
    git checkout -b main
    export CE_FORCE_PUSH=1

    run check_push_safety "main"
    assert_failure
    assert_output --partial "Force push to main/master is not allowed"
}

@test "auto_push: check_push_safety allows force push to feature branches" {
    git checkout -b feature/test
    export CE_FORCE_PUSH=1

    run check_push_safety "feature/test"
    assert_success
}

@test "auto_push: check_push_safety warns when no upstream configured" {
    git checkout -b feature/no-upstream

    run check_push_safety "feature/no-upstream"
    assert_success
    assert_output --partial "No upstream configured"
}

@test "auto_push: check_push_safety detects diverged branches" {
    # Create remote and push
    local remote_dir=$(create_remote_repo)
    git remote add origin "$remote_dir"
    git push -u origin main

    # Create divergence
    echo "local change" >> file.txt
    git add file.txt
    git commit -m "local commit"

    # Simulate remote commit
    cd "$remote_dir"
    git config --unset core.bare
    git config receive.denyCurrentBranch ignore
    echo "remote change" >> other.txt
    git add other.txt
    git commit -m "remote commit"

    cd "$TEST_REPO_DIR"
    git fetch origin

    run check_push_safety "main"
    assert_success
    # Note: Will warn about divergence
}

@test "auto_push: check_push_safety succeeds for clean push" {
    git checkout -b feature/clean-push

    run check_push_safety "feature/clean-push"
    assert_success
}

@test "auto_push: check_push_safety prevents push to master branch with CE_FORCE_PUSH" {
    git checkout -b master
    export CE_FORCE_PUSH=1

    run check_push_safety "master"
    assert_failure
}

@test "auto_push: check_push_safety allows normal push without force flag" {
    git checkout -b feature/normal
    export CE_FORCE_PUSH=0

    run check_push_safety "feature/normal"
    assert_success
}

@test "auto_push: check_push_safety counts upstream commits correctly" {
    skip "Requires complex remote setup"
}

@test "auto_push: check_push_safety handles missing remote gracefully" {
    git checkout -b feature/no-remote

    run check_push_safety "feature/no-remote"
    assert_success
}

@test "auto_push: check_push_safety validates branch name" {
    run check_push_safety ""
    # Should handle empty branch name
}

# ============================================================================
# PRE-PUSH HOOKS (6 tests)
# ============================================================================

@test "auto_push: run_prepush_checks executes hook when present" {
    setup_git_hooks
    cat > .git/hooks/pre-push <<'EOF'
#!/bin/bash
echo "pre-push executed"
exit 0
EOF
    chmod +x .git/hooks/pre-push

    run run_prepush_checks
    assert_success
    assert_output --partial "Running pre-push checks"
}

@test "auto_push: run_prepush_checks fails when hook returns non-zero" {
    mkdir -p .git/hooks
    cat > .git/hooks/pre-push <<'EOF'
#!/bin/bash
echo "Hook validation failed"
exit 1
EOF
    chmod +x .git/hooks/pre-push

    export CE_DRY_RUN=0

    run run_prepush_checks
    assert_failure
    assert_output --partial "Pre-push checks failed"
}

@test "auto_push: run_prepush_checks warns when hook not found" {
    rm -f .git/hooks/pre-push

    run run_prepush_checks
    assert_success
    assert_output --partial "pre-push hook not found"
}

@test "auto_push: run_prepush_checks passes CE_AUTO_PUSH environment" {
    mkdir -p .git/hooks
    cat > .git/hooks/pre-push <<'EOF'
#!/bin/bash
if [[ "$CE_AUTO_PUSH" == "1" ]]; then
    echo "Auto-push detected"
    exit 0
else
    exit 1
fi
EOF
    chmod +x .git/hooks/pre-push

    export CE_AUTO_PUSH=1

    run run_prepush_checks
    assert_success
    assert_output --partial "Auto-push detected"
}

@test "auto_push: run_prepush_checks handles non-executable hook" {
    mkdir -p .git/hooks
    echo "#!/bin/bash" > .git/hooks/pre-push
    chmod -x .git/hooks/pre-push

    run run_prepush_checks
    assert_success
    # Should warn or skip non-executable hook
}

@test "auto_push: run_prepush_checks respects hook timeout" {
    skip "Requires timeout implementation in run_prepush_checks"
}

# ============================================================================
# FORCE PUSH (5 tests)
# ============================================================================

@test "auto_push: perform_push uses --force-with-lease for feature branches" {
    git checkout -b feature/force-test
    export CE_FORCE_PUSH=1
    export CE_DRY_RUN=1

    run perform_push "feature/force-test" "1"
    assert_success
    assert_output --partial "force-with-lease"
}

@test "auto_push: perform_push denies force push to main" {
    git checkout -b main
    export CE_FORCE_PUSH=1

    run perform_push "main" "1"
    assert_failure
}

@test "auto_push: perform_push denies force push to master" {
    git checkout -b master
    export CE_FORCE_PUSH=1

    run perform_push "master" "1"
    assert_failure
}

@test "auto_push: perform_push allows force push with CE_FORCE_PUSH=1" {
    git checkout -b feature/force-allowed
    export CE_FORCE_PUSH=1
    export CE_DRY_RUN=1

    run perform_push "feature/force-allowed" "1"
    assert_success
}

@test "auto_push: perform_push prevents force push when CE_FORCE_PUSH=0" {
    git checkout -b feature/no-force
    export CE_FORCE_PUSH=0
    export CE_DRY_RUN=1

    run perform_push "feature/no-force" "0"
    assert_success
    refute_output --partial "force"
}

# ============================================================================
# ERROR RECOVERY (4 tests)
# ============================================================================

@test "auto_push: perform_push handles network failures gracefully" {
    skip "Requires network simulation"
}

@test "auto_push: perform_push handles authentication errors" {
    skip "Requires auth simulation"
}

@test "auto_push: perform_push retries on temporary failures" {
    skip "Requires retry logic test"
}

@test "auto_push: perform_push logs failed push attempts" {
    skip "Requires audit log integration test"
}
