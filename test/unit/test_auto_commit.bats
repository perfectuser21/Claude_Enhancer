#!/usr/bin/env bats
# Unit Tests for auto_commit.sh
# Purpose: Test automated commit functionality

load '../test_helper'

setup() {
    # Setup test environment
    export CE_DRY_RUN=1
    export TEST_REPO_DIR=$(mktemp -d)
    cd "$TEST_REPO_DIR"
    git init
    git config user.email "test@example.com"
    git config user.name "Test User"

    # Source the script
    source "${BATS_TEST_DIRNAME}/../../.workflow/automation/core/auto_commit.sh"
}

teardown() {
    # Cleanup
    cd /
    rm -rf "$TEST_REPO_DIR"
}

@test "auto_commit: check_prerequisites fails when not in git repo" {
    cd /tmp
    run check_prerequisites
    assert_failure
}

@test "auto_commit: check_prerequisites succeeds in git repo" {
    run check_prerequisites
    assert_success
}

@test "auto_commit: validate_commit_message rejects short messages" {
    run validate_commit_message "short"
    assert_failure
}

@test "auto_commit: validate_commit_message accepts valid messages" {
    run validate_commit_message "feat(P2): Add automation scripts"
    assert_success
}

@test "auto_commit: validate_commit_message warns on missing Phase marker" {
    run validate_commit_message "Add some feature without phase"
    # Should succeed but warn
    assert_success
}

@test "auto_commit: stage_changes stages specific files" {
    echo "test" > file1.txt
    echo "test" > file2.txt

    run stage_changes file1.txt
    assert_success

    # Verify only file1.txt is staged
    run git diff --cached --name-only
    assert_output "file1.txt"
}

@test "auto_commit: stage_changes stages all changes when no files specified" {
    echo "test" > file1.txt
    echo "test" > file2.txt

    run stage_changes
    assert_success

    # Verify both files are staged
    run git diff --cached --name-only
    assert_line "file1.txt"
    assert_line "file2.txt"
}

@test "auto_commit: create_commit handles empty changeset" {
    run create_commit "test: Empty commit"
    assert_success
    assert_output --partial "No changes to commit"
}

@test "auto_commit: create_commit succeeds with valid changes (dry run)" {
    echo "test" > testfile.txt

    run create_commit "feat(P2): Add test file" testfile.txt
    assert_success
    assert_output --partial "DRY RUN"
}

@test "auto_commit: create_commit respects CE_DRY_RUN flag" {
    export CE_DRY_RUN=1
    echo "test" > testfile.txt

    run create_commit "feat(P2): Add test file" testfile.txt
    assert_success
    assert_output --partial "DRY RUN"

    # Verify no actual commit was created
    run git log
    assert_output ""
}
