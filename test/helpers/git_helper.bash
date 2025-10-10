#!/usr/bin/env bash
# git_helper.bash - Git mocking utilities for BATS tests
# Provides helpers for testing git-dependent functionality

# Initialize mock git repository
git_init_mock() {
    git init --quiet
    git config user.name "Test User"
    git config user.email "test@example.com"

    # Create initial commit
    echo "# Test Repository" > README.md
    git add README.md
    git commit -m "Initial commit" --no-verify --quiet
}

# Create mock branch
git_create_mock_branch() {
    local branch_name="$1"
    local from_branch="${2:-HEAD}"

    git checkout -b "${branch_name}" "${from_branch}" --quiet 2>/dev/null
}

# Create mock remote
git_create_mock_remote() {
    local remote_name="${1:-origin}"
    local remote_url="${2:-https://github.com/test/repo.git}"

    git remote add "${remote_name}" "${remote_url}" 2>/dev/null || true
}

# Mock git status with specific files
git_mock_status() {
    local status_type="${1:-clean}"  # clean, modified, untracked, staged

    case "${status_type}" in
        modified)
            echo "test" >> README.md
            ;;
        untracked)
            echo "new file" > untracked.txt
            ;;
        staged)
            echo "staged" > staged.txt
            git add staged.txt
            ;;
        conflicted)
            # Create conflict scenario
            git checkout -b conflict-branch --quiet
            echo "conflict" > conflict.txt
            git add conflict.txt
            git commit -m "conflict setup" --no-verify --quiet
            ;;
    esac
}

# Get mock git log
git_get_mock_log() {
    git log --oneline --no-decorate
}

# Create mock merge conflict
git_create_mock_conflict() {
    # Create base
    echo "line1" > conflict.txt
    git add conflict.txt
    git commit -m "base" --no-verify --quiet

    # Create branch A
    git checkout -b branch-a --quiet
    echo "line1-a" > conflict.txt
    git add conflict.txt
    git commit -m "change in A" --no-verify --quiet

    # Create branch B
    git checkout - --quiet
    git checkout -b branch-b --quiet
    echo "line1-b" > conflict.txt
    git add conflict.txt
    git commit -m "change in B" --no-verify --quiet

    # Attempt merge (will conflict)
    git merge branch-a --no-commit 2>/dev/null || true
}

# Mock git diff output
git_mock_diff() {
    local file_count="${1:-1}"

    for ((i=1; i<=file_count; i++)); do
        echo "test change $i" >> "file${i}.txt"
    done
}

# Assert git repo exists
assert_git_repo() {
    if ! git rev-parse --git-dir &>/dev/null; then
        echo "Expected git repository to exist"
        return 1
    fi
}

# Assert on specific branch
assert_on_branch() {
    local expected_branch="$1"
    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

    if [[ "${current_branch}" != "${expected_branch}" ]]; then
        echo "Expected branch: ${expected_branch}"
        echo "Current branch: ${current_branch}"
        return 1
    fi
}

# Assert branch exists
assert_branch_exists() {
    local branch="$1"

    if ! git show-ref --verify --quiet "refs/heads/${branch}"; then
        echo "Expected branch to exist: ${branch}"
        return 1
    fi
}

# Assert commit exists
assert_commit_exists() {
    local commit_sha="$1"

    if ! git cat-file -e "${commit_sha}" 2>/dev/null; then
        echo "Expected commit to exist: ${commit_sha}"
        return 1
    fi
}

# Assert clean working tree
assert_clean_worktree() {
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        echo "Expected clean working tree"
        git status
        return 1
    fi
}

# Export git helper functions
export -f git_init_mock
export -f git_create_mock_branch
export -f git_create_mock_remote
export -f git_mock_status
export -f git_get_mock_log
export -f git_create_mock_conflict
export -f git_mock_diff
export -f assert_git_repo
export -f assert_on_branch
export -f assert_branch_exists
export -f assert_commit_exists
export -f assert_clean_worktree
