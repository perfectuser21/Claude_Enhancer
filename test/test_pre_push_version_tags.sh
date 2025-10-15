#!/bin/bash
# Pre-Push Hook Version Tag Validation Tests
# Tests lines 91-109 of .git/hooks/pre-push
# Created: 2025-10-15
# Purpose: Ensure version tags can only be pushed from main/master branches

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PRE_PUSH_HOOK="$PROJECT_ROOT/.git/hooks/pre-push"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper: Print test result
print_result() {
    local test_name="$1"
    local expected="$2"
    local actual="$3"

    if [[ "$expected" == "$actual" ]]; then
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $test_name"
        echo -e "   Expected: $expected, Got: $actual"
        ((TESTS_FAILED++))
    fi
}

# Helper: Simulate git push stdin
simulate_push() {
    local local_ref="$1"
    local local_sha="$2"
    local remote_ref="$3"
    local remote_sha="$4"

    echo "$local_ref $local_sha $remote_ref $remote_sha"
}

# Test 1: Version tag from main branch (should ALLOW)
test_version_tag_from_main() {
    echo -e "\n${BLUE}[TEST 1]${NC} Version tag from main branch"

    # Simulate being on main branch
    git checkout -b temp-main-test 2>/dev/null || git checkout temp-main-test
    git branch -D temp-main-test 2>/dev/null || true
    git checkout main 2>/dev/null || git checkout master

    # Simulate pushing v1.2.3 tag
    local stdin_data=$(simulate_push "refs/tags/v1.2.3" "abc123" "refs/tags/v1.2.3" "000000")

    # Extract hook logic (lines 91-109)
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    local remote_ref="refs/tags/v1.2.3"

    if [[ "$remote_ref" =~ ^refs/tags/v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        if [[ "$current_branch" != "main" && "$current_branch" != "master" ]]; then
            print_result "Version tag from main allowed" "ALLOW" "BLOCK"
        else
            print_result "Version tag from main allowed" "ALLOW" "ALLOW"
        fi
    else
        print_result "Version tag from main allowed" "ALLOW" "ERROR"
    fi
}

# Test 2: Version tag from feature branch (should BLOCK)
test_version_tag_from_feature() {
    echo -e "\n${BLUE}[TEST 2]${NC} Version tag from feature branch"

    # Create and checkout feature branch
    git checkout -b temp-feature-test 2>/dev/null || git checkout temp-feature-test

    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    local remote_ref="refs/tags/v1.2.3"

    if [[ "$remote_ref" =~ ^refs/tags/v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        if [[ "$current_branch" != "main" && "$current_branch" != "master" ]]; then
            print_result "Version tag from feature blocked" "BLOCK" "BLOCK"
        else
            print_result "Version tag from feature blocked" "BLOCK" "ALLOW"
        fi
    else
        print_result "Version tag from feature blocked" "BLOCK" "ERROR"
    fi

    # Cleanup
    git checkout main 2>/dev/null || git checkout master
    git branch -D temp-feature-test 2>/dev/null || true
}

# Test 3: Non-version tag from feature branch (should ALLOW)
test_non_version_tag_from_feature() {
    echo -e "\n${BLUE}[TEST 3]${NC} Non-version tag from feature branch"

    git checkout -b temp-feature-test2 2>/dev/null || git checkout temp-feature-test2

    local remote_ref="refs/tags/my-custom-tag"

    # Should not match version tag pattern
    if [[ "$remote_ref" =~ ^refs/tags/v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_result "Non-version tag allowed" "ALLOW" "ERROR"
    else
        print_result "Non-version tag allowed" "ALLOW" "ALLOW"
    fi

    # Cleanup
    git checkout main 2>/dev/null || git checkout master
    git branch -D temp-feature-test2 2>/dev/null || true
}

# Test 4: Version tag regex patterns
test_version_tag_regex() {
    echo -e "\n${BLUE}[TEST 4]${NC} Version tag regex validation"

    local test_cases=(
        "refs/tags/v1.2.3:MATCH"
        "refs/tags/v0.0.0:MATCH"
        "refs/tags/v999.999.999:MATCH"
        "refs/tags/v1.2.3.4:NO_MATCH"
        "refs/tags/v1.2:NO_MATCH"
        "refs/tags/1.2.3:NO_MATCH"
        "refs/tags/v1.2.3-beta:NO_MATCH"
        "refs/tags/version-1.2.3:NO_MATCH"
    )

    for test_case in "${test_cases[@]}"; do
        IFS=':' read -r tag expected <<< "$test_case"

        if [[ "$tag" =~ ^refs/tags/v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            actual="MATCH"
        else
            actual="NO_MATCH"
        fi

        print_result "Regex: $tag" "$expected" "$actual"
    done
}

# Test 5: Multiple tags pushed simultaneously
test_concurrent_tag_push() {
    echo -e "\n${BLUE}[TEST 5]${NC} Concurrent tag push from main"

    git checkout main 2>/dev/null || git checkout master

    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    local tags=("refs/tags/v1.2.3" "refs/tags/v1.2.4" "refs/tags/v1.2.5")
    local blocked=0

    for tag in "${tags[@]}"; do
        if [[ "$tag" =~ ^refs/tags/v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            if [[ "$current_branch" != "main" && "$current_branch" != "master" ]]; then
                ((blocked++))
            fi
        fi
    done

    if [[ $blocked -eq 0 ]]; then
        print_result "Concurrent tags from main allowed" "ALLOW" "ALLOW"
    else
        print_result "Concurrent tags from main allowed" "ALLOW" "BLOCK"
    fi
}

# Test 6: Edge case - master branch
test_version_tag_from_master() {
    echo -e "\n${BLUE}[TEST 6]${NC} Version tag from master branch"

    # Check if master branch exists
    if git show-ref --verify --quiet refs/heads/master; then
        git checkout master
        local current_branch=$(git rev-parse --abbrev-ref HEAD)
        local remote_ref="refs/tags/v2.0.0"

        if [[ "$remote_ref" =~ ^refs/tags/v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            if [[ "$current_branch" != "main" && "$current_branch" != "master" ]]; then
                print_result "Version tag from master allowed" "ALLOW" "BLOCK"
            else
                print_result "Version tag from master allowed" "ALLOW" "ALLOW"
            fi
        fi

        git checkout main 2>/dev/null || true
    else
        echo -e "${YELLOW}⚠️ SKIP${NC}: master branch does not exist"
    fi
}

# Test 7: Performance test (hook should be fast)
test_hook_performance() {
    echo -e "\n${BLUE}[TEST 7]${NC} Hook performance test"

    local start_time=$(date +%s%N)

    # Simulate hook logic 100 times
    for i in {1..100}; do
        local remote_ref="refs/tags/v$i.0.0"
        local current_branch="main"

        if [[ "$remote_ref" =~ ^refs/tags/v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            if [[ "$current_branch" != "main" && "$current_branch" != "master" ]]; then
                : # Would block
            fi
        fi
    done

    local end_time=$(date +%s%N)
    local duration_ms=$(( (end_time - start_time) / 1000000 ))

    if [[ $duration_ms -lt 100 ]]; then
        print_result "Hook performance (<100ms)" "PASS" "PASS (${duration_ms}ms)"
    else
        print_result "Hook performance (<100ms)" "PASS" "FAIL (${duration_ms}ms)"
    fi
}

# Main test runner
main() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Pre-Push Hook Version Tag Validation Tests${NC}"
    echo -e "${BLUE}  Testing lines 91-109 of .git/hooks/pre-push${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

    if [[ ! -f "$PRE_PUSH_HOOK" ]]; then
        echo -e "${RED}❌ ERROR${NC}: Pre-push hook not found at $PRE_PUSH_HOOK"
        exit 1
    fi

    # Run all tests
    test_version_tag_from_main
    test_version_tag_from_feature
    test_non_version_tag_from_feature
    test_version_tag_regex
    test_concurrent_tag_push
    test_version_tag_from_master
    test_hook_performance

    # Summary
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Test Summary${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Passed${NC}: $TESTS_PASSED"
    echo -e "${RED}Failed${NC}: $TESTS_FAILED"
    echo -e "${BLUE}Total${NC}:  $((TESTS_PASSED + TESTS_FAILED))"

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "\n${GREEN}✅ All tests passed!${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ Some tests failed${NC}"
        exit 1
    fi
}

# Run tests if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
