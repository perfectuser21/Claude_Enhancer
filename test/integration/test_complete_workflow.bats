#!/usr/bin/env bats
# =============================================================================
# Complete Workflow Integration Tests
# Tests full feature development lifecycle from P1 to P6
# =============================================================================

load ../helpers/integration_helper
load ../helpers/fixture_helper

setup() {
    export PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
    TEST_REPO=$(create_test_repo "workflow-test")
    cd "${TEST_REPO}"

    # Initialize project
    create_nodejs_project_fixture
    git add package.json tsconfig.json
    git commit -q -m "chore: setup project"
}

teardown() {
    cleanup_test_repo "${TEST_REPO}"
}

@test "Complete P1 workflow: Plan phase from start to completion" {
    # Start in P1
    run get_current_phase
    assert_output "P1"

    # Create plan document
    create_plan_document
    run assert_file_exists "docs/PLAN.md"
    [ "$status" -eq 0 ]

    # Verify plan content
    run assert_file_contains "docs/PLAN.md" "## 任务清单"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/PLAN.md" "## 受影响文件清单"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/PLAN.md" "## 回滚方案"
    [ "$status" -eq 0 ]

    # Commit plan
    git add docs/PLAN.md
    git commit -m "docs: add feature plan"

    # Create gate marker
    create_gate "01" "P1"
    run check_gate_exists "01"
    [ "$status" -eq 0 ]
}

@test "Complete P1->P2 workflow: Progress from Plan to Skeleton" {
    # Setup P1 complete state
    create_p1_complete_state

    run get_current_phase
    assert_output "P1"

    # Progress to P2
    set_phase "P2"
    run get_current_phase
    assert_output "P2"

    # Create skeleton
    mkdir -p src/auth src/models
    touch src/auth/login.ts src/auth/auth.service.ts
    create_skeleton_notes

    git add src/ docs/SKELETON-NOTES.md
    git commit -m "feat: create skeleton structure"

    # Verify skeleton files
    run assert_file_exists "src/auth/login.ts"
    [ "$status" -eq 0 ]

    run assert_file_exists "docs/SKELETON-NOTES.md"
    [ "$status" -eq 0 ]

    # Mark P2 complete
    create_gate "02" "P2"
    run check_gate_exists "02"
    [ "$status" -eq 0 ]
}

@test "Complete P1->P2->P3 workflow: Full implementation cycle" {
    # Setup P2 complete state
    create_p2_complete_state

    run get_current_phase
    assert_output "P2"

    # Progress to P3
    set_phase "P3"
    run get_current_phase
    assert_output "P3"

    # Implement features
    create_auth_module_fixture
    create_changelog

    git add src/ docs/CHANGELOG.md
    git commit -m "feat: implement authentication module"

    # Verify implementation
    run assert_file_exists "src/auth/login.ts"
    [ "$status" -eq 0 ]

    run assert_file_contains "src/auth/login.ts" "LoginService"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/CHANGELOG.md" "Unreleased"
    [ "$status" -eq 0 ]

    # Mark P3 complete
    create_gate "03" "P3"
    run check_gate_exists "03"
    [ "$status" -eq 0 ]
}

@test "Complete P1->P2->P3->P4 workflow: Add testing" {
    # Setup P3 complete state
    create_p3_complete_state

    run get_current_phase
    assert_output "P3"

    # Progress to P4
    set_phase "P4"
    run get_current_phase
    assert_output "P4"

    # Add tests
    create_test_suite_fixture
    create_test_report

    git add test/ docs/TEST-REPORT.md
    git commit -m "test: add comprehensive test suite"

    # Verify tests
    run assert_file_exists "test/auth/login.test.ts"
    [ "$status" -eq 0 ]

    run assert_file_exists "test/auth/boundary.test.ts"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/TEST-REPORT.md" "测试覆盖率"
    [ "$status" -eq 0 ]

    # Mark P4 complete
    create_gate "04" "P4"
    run check_gate_exists "04"
    [ "$status" -eq 0 ]
}

@test "Complete P1->P2->P3->P4->P5 workflow: Code review" {
    # Setup P4 complete state
    create_p4_complete_state

    run get_current_phase
    assert_output "P4"

    # Progress to P5
    set_phase "P5"
    run get_current_phase
    assert_output "P5"

    # Add review
    create_review_document

    git add docs/REVIEW.md
    git commit -m "docs: add code review"

    # Verify review
    run assert_file_exists "docs/REVIEW.md"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/REVIEW.md" "风格一致性"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/REVIEW.md" "风险清单"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/REVIEW.md" "回滚可行性"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/REVIEW.md" "APPROVE"
    [ "$status" -eq 0 ]

    # Mark P5 complete
    create_gate "05" "P5"
    run check_gate_exists "05"
    [ "$status" -eq 0 ]
}

@test "Complete P1->P2->P3->P4->P5->P6 workflow: Release preparation" {
    # Setup P5 complete state
    create_p5_complete_state

    run get_current_phase
    assert_output "P5"

    # Progress to P6
    set_phase "P6"
    run get_current_phase
    assert_output "P6"

    # Prepare release
    create_readme

    # Update changelog with version
    cat > docs/CHANGELOG.md << 'EOF'
# Changelog

## v1.1.0 - 2024-01-15
- 添加用户认证功能
- 实现JWT token验证
- 增强安全性

## v1.0.0 - 2024-01-01
- 初始版本
EOF

    git add docs/README.md docs/CHANGELOG.md
    git commit -m "docs: prepare release v1.1.0"

    # Create tag
    git tag v1.1.0

    # Verify release
    run assert_file_exists "docs/README.md"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/README.md" "## 安装"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/README.md" "## 使用"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/README.md" "## 注意事项"
    [ "$status" -eq 0 ]

    run git tag -l "v1.1.0"
    [ "$status" -eq 0 ]
    [[ "${output}" == "v1.1.0" ]]

    # Mark P6 complete
    create_gate "06" "P6"
    run check_gate_exists "06"
    [ "$status" -eq 0 ]
}

@test "Full workflow: Complete lifecycle P1->P6 in single test" {
    log_test_info "Starting complete workflow test"

    # P1: Plan
    log_test_info "Phase 1: Planning"
    create_plan_document
    git add docs/PLAN.md
    git commit -m "docs: add plan"
    create_gate "01"
    set_phase "P2"

    # P2: Skeleton
    log_test_info "Phase 2: Skeleton"
    mkdir -p src/auth
    touch src/auth/login.ts
    create_skeleton_notes
    git add src/ docs/SKELETON-NOTES.md
    git commit -m "feat: skeleton"
    create_gate "02"
    set_phase "P3"

    # P3: Implementation
    log_test_info "Phase 3: Implementation"
    create_auth_module_fixture
    create_changelog
    git add src/ docs/CHANGELOG.md
    git commit -m "feat: implement"
    create_gate "03"
    set_phase "P4"

    # P4: Testing
    log_test_info "Phase 4: Testing"
    create_test_suite_fixture
    create_test_report
    git add test/ docs/TEST-REPORT.md
    git commit -m "test: add tests"
    create_gate "04"
    set_phase "P5"

    # P5: Review
    log_test_info "Phase 5: Review"
    create_review_document
    git add docs/REVIEW.md
    git commit -m "docs: review"
    create_gate "05"
    set_phase "P6"

    # P6: Release
    log_test_info "Phase 6: Release"
    create_readme
    cat > docs/CHANGELOG.md << 'EOF'
# Changelog
## v1.0.0 - 2024-01-01
- Initial release
EOF
    git add docs/
    git commit -m "docs: release"
    git tag v1.0.0
    create_gate "06"

    # Verify all gates created
    for gate in 01 02 03 04 05 06; do
        run check_gate_exists "${gate}"
        [ "$status" -eq 0 ]
    done

    # Verify final phase
    run get_current_phase
    assert_output "P6"

    log_test_info "Complete workflow test passed"
}

@test "Workflow rollback: Revert from P3 to P2" {
    # Setup P3 state
    create_p3_complete_state

    run get_current_phase
    assert_output "P3"

    # Take snapshot before rollback
    take_snapshot "before-rollback"

    # Rollback to P2
    set_phase "P2"
    run get_current_phase
    assert_output "P2"

    # Remove P3 gate
    rm -f .gates/03.ok
    run check_gate_exists "03"
    [ "$status" -ne 0 ]

    # Verify P2 gate still exists
    run check_gate_exists "02"
    [ "$status" -eq 0 ]
}

@test "Workflow checkpoint: Save and restore state" {
    # Create P3 state
    create_p3_complete_state

    # Take snapshot
    take_snapshot "checkpoint-p3"

    # Make changes
    set_phase "P4"
    create_test_suite_fixture
    git add test/
    git commit -m "test: add tests"

    run get_current_phase
    assert_output "P4"

    # Restore snapshot
    restore_snapshot "checkpoint-p3"

    # Verify restoration
    run get_current_phase
    assert_output "P3"

    run assert_file_exists "src/auth/login.ts"
    [ "$status" -eq 0 ]
}
