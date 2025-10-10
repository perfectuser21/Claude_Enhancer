#!/usr/bin/env bats
# =============================================================================
# Multi-Terminal Parallel Development Tests
# Tests concurrent development workflows across multiple terminals
# =============================================================================

load ../helpers/integration_helper
load ../helpers/fixture_helper

setup() {
    export PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
    TEST_REPO=$(create_test_repo "multi-terminal-test")
    cd "${TEST_REPO}"

    create_nodejs_project_fixture
    git add .
    git commit -q -m "chore: setup project"

    # Create base structure
    create_p1_complete_state
}

teardown() {
    cleanup_terminal_env
    cleanup_test_repo "${TEST_REPO}"
}

@test "Multi-terminal: Two terminals develop different features independently" {
    log_test_info "Starting multi-terminal independent development test"

    # Terminal 1: Login feature
    export_terminal_env "t1"
    create_branch "feature-login"

    mkdir -p src/auth
    cat > src/auth/login.ts << 'EOF'
export class LoginService {
    login(email: string, password: string): Promise<string> {
        // Login implementation
        return Promise.resolve('token');
    }
}
EOF

    git add src/auth/login.ts
    git commit -m "feat(t1): implement login service"

    local t1_commit=$(git rev-parse HEAD)
    log_test_info "Terminal 1 commit: ${t1_commit}"

    # Terminal 2: Payment feature (different files)
    cleanup_terminal_env
    git checkout -q main 2>&1
    export_terminal_env "t2"
    create_branch "feature-payment"

    mkdir -p src/payment
    cat > src/payment/processor.ts << 'EOF'
export class PaymentProcessor {
    processPayment(amount: number): Promise<boolean> {
        // Payment implementation
        return Promise.resolve(true);
    }
}
EOF

    git add src/payment/processor.ts
    git commit -m "feat(t2): implement payment processor"

    local t2_commit=$(git rev-parse HEAD)
    log_test_info "Terminal 2 commit: ${t2_commit}"

    # Verify no conflicts (different files)
    git checkout -q main 2>&1
    git merge --no-ff feature-login -m "Merge login feature" 2>&1
    local merge1_status=$?

    git merge --no-ff feature-payment -m "Merge payment feature" 2>&1
    local merge2_status=$?

    [ "$merge1_status" -eq 0 ]
    [ "$merge2_status" -eq 0 ]

    # Verify both features exist
    run assert_file_exists "src/auth/login.ts"
    [ "$status" -eq 0 ]

    run assert_file_exists "src/payment/processor.ts"
    [ "$status" -eq 0 ]

    log_test_info "Multi-terminal independent development successful"
}

@test "Multi-terminal: Three terminals develop features in parallel" {
    # Terminal 1: Authentication
    export_terminal_env "t1"
    create_branch "feature-t1-auth"

    mkdir -p src/auth
    echo "// Auth module" > src/auth/auth.ts
    git add src/auth/auth.ts
    git commit -m "feat(t1): auth module"

    # Terminal 2: Database
    cleanup_terminal_env
    git checkout -q main 2>&1
    export_terminal_env "t2"
    create_branch "feature-t2-db"

    mkdir -p src/database
    echo "// Database module" > src/database/connection.ts
    git add src/database/connection.ts
    git commit -m "feat(t2): database module"

    # Terminal 3: API
    cleanup_terminal_env
    git checkout -q main 2>&1
    export_terminal_env "t3"
    create_branch "feature-t3-api"

    mkdir -p src/api
    echo "// API module" > src/api/routes.ts
    git add src/api/routes.ts
    git commit -m "feat(t3): api module"

    # Merge all features
    git checkout -q main 2>&1
    git merge --no-ff feature-t1-auth -m "Merge t1" 2>&1
    git merge --no-ff feature-t2-db -m "Merge t2" 2>&1
    git merge --no-ff feature-t3-api -m "Merge t3" 2>&1

    # Verify all modules exist
    run assert_file_exists "src/auth/auth.ts"
    [ "$status" -eq 0 ]

    run assert_file_exists "src/database/connection.ts"
    [ "$status" -eq 0 ]

    run assert_file_exists "src/api/routes.ts"
    [ "$status" -eq 0 ]

    cleanup_terminal_env
}

@test "Multi-terminal: Parallel development with phase progression" {
    # Terminal 1 progresses through phases
    export_terminal_env "t1"
    create_branch "feature-t1"

    # T1: P2 -> P3
    set_phase "P2"
    mkdir -p src/feature1
    echo "// Feature 1" > src/feature1/index.ts
    git add src/feature1/
    git commit -m "feat(t1): skeleton"

    set_phase "P3"
    cat > src/feature1/index.ts << 'EOF'
export class Feature1 {
    execute(): void {
        console.log('Feature 1 executing');
    }
}
EOF
    git add src/feature1/index.ts
    git commit -m "feat(t1): implement feature1"

    local t1_phase=$(get_current_phase)

    # Terminal 2 works independently
    cleanup_terminal_env
    git checkout -q main 2>&1
    export_terminal_env "t2"
    create_branch "feature-t2"

    # T2: Also P2 -> P3
    set_phase "P2"
    mkdir -p src/feature2
    echo "// Feature 2" > src/feature2/index.ts
    git add src/feature2/
    git commit -m "feat(t2): skeleton"

    set_phase "P3"
    cat > src/feature2/index.ts << 'EOF'
export class Feature2 {
    execute(): void {
        console.log('Feature 2 executing');
    }
}
EOF
    git add src/feature2/index.ts
    git commit -m "feat(t2): implement feature2"

    local t2_phase=$(get_current_phase)

    # Both should be in P3
    [ "${t1_phase}" = "P3" ]
    [ "${t2_phase}" = "P3" ]

    # Verify independent development
    git checkout -q main 2>&1
    git merge --no-ff feature-t1 -m "Merge feature-t1" 2>&1
    git merge --no-ff feature-t2 -m "Merge feature-t2" 2>&1

    run assert_file_exists "src/feature1/index.ts"
    [ "$status" -eq 0 ]

    run assert_file_exists "src/feature2/index.ts"
    [ "$status" -eq 0 ]

    cleanup_terminal_env
}

@test "Multi-terminal: Session isolation verification" {
    # Terminal 1 session
    export_terminal_env "t1"
    create_branch "feature-t1"

    mkdir -p "${CE_SESSION_DIR}"
    echo "Session data for t1" > "${CE_SESSION_DIR}/session.dat"
    echo "t1-state" > "${CE_SESSION_DIR}/state.txt"

    run assert_file_exists "${CE_SESSION_DIR}/session.dat"
    [ "$status" -eq 0 ]

    # Terminal 2 session (different directory)
    cleanup_terminal_env
    export_terminal_env "t2"
    create_branch "feature-t2"

    mkdir -p "${CE_SESSION_DIR}"
    echo "Session data for t2" > "${CE_SESSION_DIR}/session.dat"
    echo "t2-state" > "${CE_SESSION_DIR}/state.txt"

    run assert_file_exists "${CE_SESSION_DIR}/session.dat"
    [ "$status" -eq 0 ]

    # Verify session isolation
    run cat "${CE_SESSION_DIR}/state.txt"
    assert_output "t2-state"

    # Check t1 session still exists
    cleanup_terminal_env
    export_terminal_env "t1"
    run cat "${CE_SESSION_DIR}/state.txt"
    assert_output "t1-state"

    cleanup_terminal_env
}

@test "Multi-terminal: Concurrent PLAN.md edits (same phase, different features)" {
    # Setup: Both terminals in P1, editing different sections

    # Terminal 1: Feature A planning
    export_terminal_env "t1"
    create_branch "plan-feature-a"

    cat > docs/PLAN.md << 'EOF'
# Feature A Plan

## 任务清单
1. 实现Feature A - Task 1
2. 实现Feature A - Task 2
3. 实现Feature A - Task 3
4. 实现Feature A - Task 4
5. 实现Feature A - Task 5

## 受影响文件清单
- src/featureA/module.ts

## 回滚方案
Revert Feature A changes
EOF

    git add docs/PLAN.md
    git commit -m "docs(t1): plan feature A"

    # Terminal 2: Feature B planning
    cleanup_terminal_env
    git checkout -q main 2>&1
    export_terminal_env "t2"
    create_branch "plan-feature-b"

    cat > docs/PLAN.md << 'EOF'
# Feature B Plan

## 任务清单
1. 实现Feature B - Task 1
2. 实现Feature B - Task 2
3. 实现Feature B - Task 3
4. 实现Feature B - Task 4
5. 实现Feature B - Task 5

## 受影响文件清单
- src/featureB/module.ts

## 回滚方案
Revert Feature B changes
EOF

    git add docs/PLAN.md
    git commit -m "docs(t2): plan feature B"

    # Attempt to merge - should have conflict
    git checkout -q main 2>&1

    # First merge succeeds
    git merge --no-ff plan-feature-a -m "Merge plan A" 2>&1
    [ "$?" -eq 0 ]

    # Second merge will conflict
    git merge --no-ff plan-feature-b -m "Merge plan B" 2>&1 || true

    # Check for conflict markers
    if git diff --name-only --diff-filter=U | grep -q "docs/PLAN.md"; then
        log_test_info "Conflict detected as expected"
    fi

    # Abort merge to cleanup
    git merge --abort 2>&1 || true

    cleanup_terminal_env
}

@test "Multi-terminal: Sequential merging of parallel work" {
    # Create 5 parallel feature branches
    for i in {1..5}; do
        git checkout -q main 2>&1
        export_terminal_env "t${i}"
        create_branch "feature-${i}"

        mkdir -p "src/feature${i}"
        echo "// Feature ${i}" > "src/feature${i}/index.ts"

        git add "src/feature${i}/"
        git commit -m "feat(t${i}): add feature ${i}"
    done

    cleanup_terminal_env

    # Merge all features sequentially
    git checkout -q main 2>&1

    for i in {1..5}; do
        git merge --no-ff "feature-${i}" -m "Merge feature ${i}" 2>&1
        [ "$?" -eq 0 ]

        # Verify feature exists
        run assert_file_exists "src/feature${i}/index.ts"
        [ "$status" -eq 0 ]
    done

    # Verify all 5 features merged successfully
    for i in {1..5}; do
        run assert_file_exists "src/feature${i}/index.ts"
        [ "$status" -eq 0 ]
    done
}

@test "Multi-terminal: Performance - 10 concurrent branches" {
    local start_time=$(date +%s)

    # Create 10 branches in parallel
    for i in {1..10}; do
        git checkout -q main 2>&1
        export_terminal_env "perf-t${i}"
        create_branch "perf-feature-${i}"

        mkdir -p "src/perf${i}"
        for j in {1..5}; do
            echo "// File ${j}" > "src/perf${i}/file${j}.ts"
        done

        git add "src/perf${i}/"
        git commit -q -m "feat(perf-t${i}): add feature ${i}"
    done

    cleanup_terminal_env

    # Merge all
    git checkout -q main 2>&1
    for i in {1..10}; do
        git merge --no-ff "perf-feature-${i}" -m "Merge perf ${i}" 2>&1
    done

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_test_info "Created and merged 10 branches in ${duration} seconds"

    # Verify all branches merged
    for i in {1..10}; do
        run assert_file_exists "src/perf${i}/file1.ts"
        [ "$status" -eq 0 ]
    done

    # Performance assertion: should complete in reasonable time
    [ "$duration" -lt 60 ]  # Should complete in under 60 seconds
}

@test "Multi-terminal: Branch cleanup after merge" {
    # Create multiple feature branches
    for i in {1..3}; do
        git checkout -q main 2>&1
        export_terminal_env "t${i}"
        create_branch "cleanup-feature-${i}"

        echo "// Feature ${i}" > "feature${i}.txt"
        git add "feature${i}.txt"
        git commit -m "feat(t${i}): feature ${i}"
    done

    cleanup_terminal_env
    git checkout -q main 2>&1

    # Merge all branches
    for i in {1..3}; do
        git merge --no-ff "cleanup-feature-${i}" -m "Merge cleanup-feature-${i}" 2>&1
    done

    # Verify branches still exist
    for i in {1..3}; do
        run git rev-parse --verify "cleanup-feature-${i}"
        [ "$status" -eq 0 ]
    done

    # Delete merged branches
    for i in {1..3}; do
        git branch -d "cleanup-feature-${i}" 2>&1
    done

    # Verify branches deleted
    for i in {1..3}; do
        run git rev-parse --verify "cleanup-feature-${i}"
        [ "$status" -ne 0 ]
    done

    # Verify files still exist on main
    for i in {1..3}; do
        run assert_file_exists "feature${i}.txt"
        [ "$status" -eq 0 ]
    done
}
