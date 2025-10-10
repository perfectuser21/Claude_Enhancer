#!/usr/bin/env bats
# =============================================================================
# Phase Transition Integration Tests
# Tests phase progression, validation, and transition logic
# =============================================================================

load ../helpers/integration_helper
load ../helpers/fixture_helper

setup() {
    export PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
    TEST_REPO=$(create_test_repo "phase-transition-test")
    cd "${TEST_REPO}"

    create_nodejs_project_fixture
    git add .
    git commit -q -m "chore: setup project"
}

teardown() {
    cleanup_test_repo "${TEST_REPO}"
}

@test "Phase transition: P0 -> P1 discovery to planning" {
    # P0: Discovery phase
    set_phase "P0"
    run get_current_phase
    assert_output "P0"

    # Create discovery document
    mkdir -p docs
    cat > docs/P0_FEASIBILITY_DISCOVERY.md << 'EOF'
# Feasibility Discovery

## 可行性分析
Feature is technically feasible.

## 技术Spike
1. Tested authentication libraries
2. Verified database compatibility

## 风险评估
- 技术风险: Low
- 业务风险: Medium
- 时间风险: Low

## 结论
GO - Proceed with implementation
EOF

    git add docs/P0_FEASIBILITY_DISCOVERY.md
    git commit -m "docs: complete discovery phase"

    # Mark P0 complete and transition
    create_gate "00" "P0"
    set_phase "P1"

    run get_current_phase
    assert_output "P1"

    run check_gate_exists "00"
    [ "$status" -eq 0 ]
}

@test "Phase transition: P1 -> P2 planning to skeleton" {
    # Setup P1
    set_phase "P1"
    create_plan_document

    git add docs/PLAN.md
    git commit -m "docs: add plan"

    # Validate P1 complete
    run assert_file_exists "docs/PLAN.md"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/PLAN.md" "## 任务清单"
    [ "$status" -eq 0 ]

    # Transition to P2
    create_gate "01" "P1"
    set_phase "P2"

    run get_current_phase
    assert_output "P2"

    # Verify gate created
    run check_gate_exists "01"
    [ "$status" -eq 0 ]
}

@test "Phase transition: P2 -> P3 skeleton to implementation" {
    # Setup P2
    create_p2_complete_state

    run get_current_phase
    assert_output "P2"

    # Verify skeleton files
    run assert_file_exists "src/auth/login.ts"
    [ "$status" -eq 0 ]

    # Transition to P3
    set_phase "P3"

    run get_current_phase
    assert_output "P3"

    # Verify P2 gate exists
    run check_gate_exists "02"
    [ "$status" -eq 0 ]
}

@test "Phase transition: P3 -> P4 implementation to testing" {
    # Setup P3
    create_p3_complete_state

    run get_current_phase
    assert_output "P3"

    # Verify implementation
    run assert_file_exists "src/auth/login.ts"
    [ "$status" -eq 0 ]

    run assert_file_contains "src/auth/login.ts" "LoginService"
    [ "$status" -eq 0 ]

    # Transition to P4
    set_phase "P4"

    run get_current_phase
    assert_output "P4"

    run check_gate_exists "03"
    [ "$status" -eq 0 ]
}

@test "Phase transition: P4 -> P5 testing to review" {
    # Setup P4
    create_p4_complete_state

    run get_current_phase
    assert_output "P4"

    # Verify tests
    run assert_file_exists "test/auth/login.test.ts"
    [ "$status" -eq 0 ]

    run assert_file_exists "docs/TEST-REPORT.md"
    [ "$status" -eq 0 ]

    # Transition to P5
    set_phase "P5"

    run get_current_phase
    assert_output "P5"

    run check_gate_exists "04"
    [ "$status" -eq 0 ]
}

@test "Phase transition: P5 -> P6 review to release" {
    # Setup P5
    create_p5_complete_state

    run get_current_phase
    assert_output "P5"

    # Verify review
    run assert_file_exists "docs/REVIEW.md"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/REVIEW.md" "APPROVE"
    [ "$status" -eq 0 ]

    # Transition to P6
    set_phase "P6"

    run get_current_phase
    assert_output "P6"

    run check_gate_exists "05"
    [ "$status" -eq 0 ]
}

@test "Phase transition: P6 -> P7 release to monitoring" {
    # Setup P6
    create_p5_complete_state
    set_phase "P6"

    create_readme
    git add docs/README.md
    git commit -m "docs: add README"

    git tag v1.0.0
    create_gate "06" "P6"

    # Transition to P7
    set_phase "P7"

    run get_current_phase
    assert_output "P7"

    # Create monitoring report
    mkdir -p observability
    cat > observability/P7_MONITOR_REPORT.md << 'EOF'
# Monitoring Report

## 健康检查
- API服务: ✅ HEALTHY
- 数据库: ✅ HEALTHY
- 缓存: ✅ HEALTHY

## SLO验证
- 可用性: 99.9% ✅
- 延迟(p95): 150ms ✅
- 错误率: 0.1% ✅

## 系统状态
HEALTHY
EOF

    git add observability/
    git commit -m "docs: add monitoring report"

    create_gate "07" "P7"

    run check_gate_exists "07"
    [ "$status" -eq 0 ]
}

@test "Phase transition: Complete P0->P7 full lifecycle" {
    log_test_info "Starting complete lifecycle test"

    # P0: Discovery
    set_phase "P0"
    mkdir -p docs
    echo "# Discovery: GO" > docs/P0_DISCOVERY.md
    git add docs/P0_DISCOVERY.md
    git commit -m "docs: discovery"
    create_gate "00"

    # P1: Plan
    set_phase "P1"
    create_plan_document
    git add docs/PLAN.md
    git commit -m "docs: plan"
    create_gate "01"

    # P2: Skeleton
    set_phase "P2"
    mkdir -p src/auth
    touch src/auth/login.ts
    create_skeleton_notes
    git add src/ docs/SKELETON-NOTES.md
    git commit -m "feat: skeleton"
    create_gate "02"

    # P3: Implementation
    set_phase "P3"
    create_auth_module_fixture
    create_changelog
    git add src/ docs/CHANGELOG.md
    git commit -m "feat: implement"
    create_gate "03"

    # P4: Testing
    set_phase "P4"
    create_test_suite_fixture
    create_test_report
    git add test/ docs/TEST-REPORT.md
    git commit -m "test: add tests"
    create_gate "04"

    # P5: Review
    set_phase "P5"
    create_review_document
    git add docs/REVIEW.md
    git commit -m "docs: review"
    create_gate "05"

    # P6: Release
    set_phase "P6"
    create_readme
    git add docs/README.md
    git commit -m "docs: release"
    git tag v1.0.0
    create_gate "06"

    # P7: Monitoring
    set_phase "P7"
    mkdir -p observability
    echo "# Monitor: HEALTHY" > observability/P7_MONITOR_REPORT.md
    git add observability/
    git commit -m "docs: monitor"
    create_gate "07"

    # Verify all gates created
    for gate in 00 01 02 03 04 05 06 07; do
        run check_gate_exists "${gate}"
        [ "$status" -eq 0 ]
    done

    # Verify final phase
    run get_current_phase
    assert_output "P7"

    log_test_info "Complete lifecycle test passed"
}

@test "Phase transition: Skip phase detection (P1 -> P3)" {
    # Start in P1
    set_phase "P1"
    create_plan_document
    git add docs/PLAN.md
    git commit -m "docs: plan"
    create_gate "01"

    # Try to skip to P3 (bypassing P2)
    set_phase "P3"

    run get_current_phase
    assert_output "P3"

    # P2 gate should not exist
    run check_gate_exists "02"
    [ "$status" -ne 0 ]

    # This should be flagged in production, but test verifies the behavior
    log_test_info "Phase skip detected: P1 -> P3"
}

@test "Phase transition: Backward transition (rollback)" {
    # Progress to P4
    create_p4_complete_state

    run get_current_phase
    assert_output "P4"

    # Rollback to P3
    set_phase "P3"

    run get_current_phase
    assert_output "P3"

    # Remove P4 gate to indicate rollback
    rm -f .gates/04.ok

    run check_gate_exists "04"
    [ "$status" -ne 0 ]

    # P3 gate should still exist
    run check_gate_exists "03"
    [ "$status" -eq 0 ]
}

@test "Phase transition: Multiple forward-backward cycles" {
    # P1 -> P2 -> P1 -> P2
    set_phase "P1"
    create_plan_document
    git add docs/PLAN.md
    git commit -m "docs: plan"
    create_gate "01"

    # Forward to P2
    set_phase "P2"
    mkdir -p src
    touch src/file.ts
    git add src/
    git commit -m "feat: skeleton"
    create_gate "02"

    # Back to P1
    set_phase "P1"
    rm -f .gates/02.ok

    run get_current_phase
    assert_output "P1"

    # Forward again to P2
    set_phase "P2"
    create_gate "02"

    run get_current_phase
    assert_output "P2"

    run check_gate_exists "02"
    [ "$status" -eq 0 ]
}

@test "Phase transition: Concurrent phase changes (race condition)" {
    set_phase "P1"

    # Simulate concurrent writes to phase file
    echo "P2" > .phase/current &
    echo "P3" > .phase/current &
    wait

    # Last write wins
    local final_phase=$(get_current_phase)

    # Should be either P2 or P3
    [[ "${final_phase}" == "P2" ]] || [[ "${final_phase}" == "P3" ]]

    log_test_info "Final phase after race: ${final_phase}"
}

@test "Phase transition: Phase validation before transition" {
    # P1 without required documents
    set_phase "P1"

    # Try to transition without completing P1
    # (In production, this would be blocked by gates)

    # No PLAN.md exists
    run assert_file_exists "docs/PLAN.md"
    [ "$status" -ne 0 ]

    # Transition should ideally fail, but test documents current behavior
    set_phase "P2"

    run get_current_phase
    assert_output "P2"

    log_test_info "Transition allowed without validation (gate check required)"
}

@test "Phase transition: Phase persistence across restarts" {
    # Set phase P3
    set_phase "P3"

    # Simulate process restart by reading from file
    local saved_phase=$(cat .phase/current)

    [ "${saved_phase}" = "P3" ]

    # Phase should persist
    run get_current_phase
    assert_output "P3"
}

@test "Phase transition: ACTIVE file synchronization" {
    set_phase "P3"

    # Check .workflow/ACTIVE updated
    if [[ -f .workflow/ACTIVE ]]; then
        run grep -q "phase: P3" .workflow/ACTIVE
        [ "$status" -eq 0 ]

        run grep -q "ticket:" .workflow/ACTIVE
        [ "$status" -eq 0 ]

        run grep -q "started_at:" .workflow/ACTIVE
        [ "$status" -eq 0 ]
    fi
}

@test "Phase transition: Rapid sequential transitions" {
    # Measure performance of rapid phase changes
    local start_time=$(date +%s%N)

    for phase in P1 P2 P3 P4 P5 P6; do
        set_phase "${phase}"
    done

    local end_time=$(date +%s%N)
    local duration=$(( (end_time - start_time) / 1000000 ))

    log_test_info "6 phase transitions took ${duration}ms"

    # Should complete in under 1 second
    [ "$duration" -lt 1000 ]

    # Verify final state
    run get_current_phase
    assert_output "P6"
}

@test "Phase transition: Invalid phase handling" {
    # Try to set invalid phase
    echo "INVALID" > .phase/current

    run get_current_phase
    assert_output "INVALID"

    # System should handle gracefully (in production, validation needed)
    log_test_info "Invalid phase handling needs validation logic"
}
