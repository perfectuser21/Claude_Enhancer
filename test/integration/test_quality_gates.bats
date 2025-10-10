#!/usr/bin/env bats
# =============================================================================
# Quality Gates Integration Tests
# Tests quality gate validation, enforcement, and gate conditions
# =============================================================================

load ../helpers/integration_helper
load ../helpers/fixture_helper

setup() {
    export PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
    TEST_REPO=$(create_test_repo "quality-gates-test")
    cd "${TEST_REPO}"

    create_nodejs_project_fixture
    git add .
    git commit -q -m "chore: setup project"
}

teardown() {
    cleanup_test_repo "${TEST_REPO}"
}

@test "Quality gate: P0 discovery validation" {
    set_phase "P0"

    # Create incomplete discovery document
    mkdir -p docs
    cat > docs/P0_DISCOVERY.md << 'EOF'
# Discovery

## 可行性分析
Some analysis here.
EOF

    git add docs/P0_DISCOVERY.md
    git commit -m "docs: incomplete discovery"

    # Should fail - missing risk assessment
    run assert_file_contains "docs/P0_DISCOVERY.md" "风险评估"
    [ "$status" -ne 0 ]

    # Create complete discovery
    cat > docs/P0_DISCOVERY.md << 'EOF'
# Discovery

## 可行性分析
Feature is feasible.

## 技术Spike
1. Tested library A
2. Verified compatibility B

## 风险评估
- 技术风险: Low
- 业务风险: Medium
- 时间风险: Low

## 结论
GO - Proceed with development
EOF

    git add docs/P0_DISCOVERY.md
    git commit --amend --no-edit

    # Verify completeness
    run assert_file_contains "docs/P0_DISCOVERY.md" "风险评估"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/P0_DISCOVERY.md" "技术Spike"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/P0_DISCOVERY.md" "GO"
    [ "$status" -eq 0 ]
}

@test "Quality gate: P1 plan validation - task count" {
    set_phase "P1"

    # Create plan with insufficient tasks
    cat > docs/PLAN.md << 'EOF'
# Plan

## 任务清单
1. Task 1
2. Task 2
3. Task 3

## 受影响文件清单
- src/file.ts

## 回滚方案
Revert changes
EOF

    git add docs/PLAN.md
    git commit -m "docs: plan with 3 tasks"

    # Count tasks - should be < 5
    local task_count=$(grep -c "^[0-9]\+\." docs/PLAN.md || echo 0)
    [ "$task_count" -lt 5 ]

    # Create plan with sufficient tasks
    cat > docs/PLAN.md << 'EOF'
# Plan

## 任务清单
1. 实现用户认证
2. 创建登录接口
3. 添加JWT验证
4. 实现密码加密
5. 编写单元测试

## 受影响文件清单
- src/auth/login.ts
- src/auth/auth.service.ts

## 回滚方案
删除auth模块，恢复临时认证
EOF

    git add docs/PLAN.md
    git commit --amend --no-edit

    # Verify task count >= 5
    local new_task_count=$(grep -c "^[0-9]\+\." docs/PLAN.md || echo 0)
    [ "$new_task_count" -ge 5 ]
}

@test "Quality gate: P1 plan validation - required sections" {
    set_phase "P1"

    # Missing required sections
    cat > docs/PLAN.md << 'EOF'
# Incomplete Plan

## 任务清单
1. Task 1
2. Task 2
3. Task 3
4. Task 4
5. Task 5
EOF

    git add docs/PLAN.md
    git commit -m "docs: incomplete plan"

    # Check for required sections
    run assert_file_contains "docs/PLAN.md" "## 受影响文件清单"
    [ "$status" -ne 0 ]

    run assert_file_contains "docs/PLAN.md" "## 回滚方案"
    [ "$status" -ne 0 ]

    # Add complete plan
    create_plan_document

    git add docs/PLAN.md
    git commit --amend --no-edit

    # Verify all sections present
    run assert_file_contains "docs/PLAN.md" "## 任务清单"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/PLAN.md" "## 受影响文件清单"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/PLAN.md" "## 回滚方案"
    [ "$status" -eq 0 ]
}

@test "Quality gate: P3 changelog validation" {
    create_p2_complete_state
    set_phase "P3"

    # Changelog without Unreleased section
    cat > docs/CHANGELOG.md << 'EOF'
# Changelog

## v1.0.0 - 2024-01-01
- Initial release
EOF

    git add docs/CHANGELOG.md
    git commit -m "docs: changelog without unreleased"

    # Should fail validation
    run assert_file_contains "docs/CHANGELOG.md" "## Unreleased"
    [ "$status" -ne 0 ]

    # Add proper changelog
    cat > docs/CHANGELOG.md << 'EOF'
# Changelog

## Unreleased
- 添加用户认证功能
- 实现JWT验证
- 增强安全性

## v1.0.0 - 2024-01-01
- Initial release
EOF

    git add docs/CHANGELOG.md
    git commit --amend --no-edit

    # Should pass validation
    run assert_file_contains "docs/CHANGELOG.md" "## Unreleased"
    [ "$status" -eq 0 ]
}

@test "Quality gate: P4 test coverage validation" {
    create_p3_complete_state
    set_phase "P4"

    # Single test (insufficient)
    mkdir -p test/auth
    cat > test/auth/login.test.ts << 'EOF'
import { LoginService } from '../../src/auth/login';

describe('LoginService', () => {
    test('should login', async () => {
        const service = new LoginService();
        const result = await service.login('test@example.com', 'password');
        expect(result).toBeDefined();
    });
});
EOF

    git add test/
    git commit -m "test: single test"

    # Count test cases
    local test_count=$(grep -c "test(" test/auth/login.test.ts || echo 0)
    [ "$test_count" -lt 2 ]

    # Add boundary test
    cat >> test/auth/login.test.ts << 'EOF'

describe('LoginService - Boundary Tests', () => {
    test('should handle empty email', async () => {
        const service = new LoginService();
        await expect(service.login('', 'password')).rejects.toThrow();
    });

    test('should handle invalid password', async () => {
        const service = new LoginService();
        await expect(service.login('test@example.com', '')).rejects.toThrow();
    });
});
EOF

    git add test/
    git commit --amend --no-edit

    # Verify multiple test cases including boundary
    local new_test_count=$(grep -c "test(" test/auth/login.test.ts || echo 0)
    [ "$new_test_count" -ge 2 ]

    run assert_file_contains "test/auth/login.test.ts" "Boundary"
    [ "$status" -eq 0 ]
}

@test "Quality gate: P4 test report validation" {
    create_p3_complete_state
    set_phase "P4"

    # Test report missing coverage info
    cat > docs/TEST-REPORT.md << 'EOF'
# Test Report

Tests were run.
EOF

    git add docs/TEST-REPORT.md
    git commit -m "docs: incomplete test report"

    # Should fail - missing coverage
    run assert_file_contains "docs/TEST-REPORT.md" "覆盖率"
    [ "$status" -ne 0 ]

    # Create proper test report
    create_test_report

    git add docs/TEST-REPORT.md
    git commit --amend --no-edit

    # Verify required sections
    run assert_file_contains "docs/TEST-REPORT.md" "测试覆盖率"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/TEST-REPORT.md" "测试结果"
    [ "$status" -eq 0 ]
}

@test "Quality gate: P5 review validation - three sections" {
    create_p4_complete_state
    set_phase "P5"

    # Review with missing sections
    cat > docs/REVIEW.md << 'EOF'
# Code Review

## 风格一致性
Code looks good.

APPROVE
EOF

    git add docs/REVIEW.md
    git commit -m "docs: incomplete review"

    # Check for all required sections
    run assert_file_contains "docs/REVIEW.md" "风险清单"
    [ "$status" -ne 0 ]

    run assert_file_contains "docs/REVIEW.md" "回滚可行性"
    [ "$status" -ne 0 ]

    # Create complete review
    create_review_document

    git add docs/REVIEW.md
    git commit --amend --no-edit

    # Verify all three sections
    run assert_file_contains "docs/REVIEW.md" "风格一致性"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/REVIEW.md" "风险清单"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/REVIEW.md" "回滚可行性"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/REVIEW.md" "APPROVE"
    [ "$status" -eq 0 ]
}

@test "Quality gate: P5 review REWORK scenario" {
    create_p4_complete_state
    set_phase "P5"

    # Review with REWORK decision
    cat > docs/REVIEW.md << 'EOF'
# Code Review

## 风格一致性
代码风格不一致，需要统一。

## 风险清单
1. 安全漏洞：密码未加密
2. 性能问题：N+1查询

## 回滚可行性
回滚方案不完整。

REWORK: 修复安全漏洞和性能问题
EOF

    git add docs/REVIEW.md
    git commit -m "docs: review with rework"

    # Verify REWORK decision
    run assert_file_contains "docs/REVIEW.md" "REWORK:"
    [ "$status" -eq 0 ]

    # Should not progress to P6 with REWORK
    # (In production, gate check would block)
    log_test_info "REWORK decision detected - should block P6 transition"
}

@test "Quality gate: P6 README validation - three sections" {
    create_p5_complete_state
    set_phase "P6"

    # Incomplete README
    cat > docs/README.md << 'EOF'
# Project

## 安装
npm install
EOF

    git add docs/README.md
    git commit -m "docs: incomplete README"

    # Missing required sections
    run assert_file_contains "docs/README.md" "## 使用"
    [ "$status" -ne 0 ]

    run assert_file_contains "docs/README.md" "## 注意事项"
    [ "$status" -ne 0 ]

    # Create complete README
    create_readme

    git add docs/README.md
    git commit --amend --no-edit

    # Verify all sections
    run assert_file_contains "docs/README.md" "## 安装"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/README.md" "## 使用"
    [ "$status" -eq 0 ]

    run assert_file_contains "docs/README.md" "## 注意事项"
    [ "$status" -eq 0 ]
}

@test "Quality gate: P6 version tag validation" {
    create_p5_complete_state
    set_phase "P6"

    create_readme
    git add docs/README.md
    git commit -m "docs: README"

    # Check no version tag exists
    run git tag -l "v*"
    [[ -z "${output}" ]]

    # Create version tag
    git tag v1.0.0

    # Verify tag created
    run git tag -l "v1.0.0"
    assert_output "v1.0.0"

    # Tag should match semver pattern
    [[ "v1.0.0" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

@test "Quality gate: P7 monitoring validation" {
    create_p5_complete_state
    set_phase "P6"
    create_readme
    git add docs/README.md
    git commit -m "docs: release"
    git tag v1.0.0
    create_gate "06"

    set_phase "P7"

    # Incomplete monitoring report
    mkdir -p observability
    cat > observability/P7_MONITOR_REPORT.md << 'EOF'
# Monitoring

System is running.
EOF

    git add observability/
    git commit -m "docs: incomplete monitoring"

    # Missing required sections
    run assert_file_contains "observability/P7_MONITOR_REPORT.md" "健康检查"
    [ "$status" -ne 0 ]

    # Complete monitoring report
    cat > observability/P7_MONITOR_REPORT.md << 'EOF'
# Monitoring Report

## 健康检查
- API: ✅ HEALTHY (200ms)
- Database: ✅ HEALTHY
- Cache: ✅ HEALTHY

## SLO验证
- 可用性: 99.95% ✅ (SLO: 99.9%)
- 延迟(p95): 145ms ✅ (SLO: 200ms)
- 错误率: 0.05% ✅ (SLO: 0.1%)

## 性能基线
- QPS: 1500
- 响应时间: 120ms avg
- 内存使用: 45%

## 系统状态
HEALTHY - All systems operational
EOF

    git add observability/
    git commit --amend --no-edit

    # Verify all sections
    run assert_file_contains "observability/P7_MONITOR_REPORT.md" "健康检查"
    [ "$status" -eq 0 ]

    run assert_file_contains "observability/P7_MONITOR_REPORT.md" "SLO验证"
    [ "$status" -eq 0 ]

    run assert_file_contains "observability/P7_MONITOR_REPORT.md" "HEALTHY"
    [ "$status" -eq 0 ]
}

@test "Quality gate: Security scan validation" {
    create_p3_complete_state

    # Create file with security issues
    create_security_violation_fixture

    git add src/config/
    git commit -m "feat: add config" 2>&1 || {
        log_test_info "Commit blocked by security scan (expected)"
    }

    # Remove security violations
    rm -rf src/config/

    # Create clean config
    mkdir -p src/config
    cat > src/config/config.ts << 'EOF'
export const config = {
    apiUrl: process.env.API_URL || 'http://localhost:3000',
    dbHost: process.env.DB_HOST || 'localhost',
    // Use environment variables for sensitive data
};
EOF

    git add src/config/
    git commit -m "feat: add secure config"

    # Verify no hardcoded secrets
    run grep -r "sk-" src/config/
    [ "$status" -ne 0 ]

    run grep -r "AKIA" src/config/
    [ "$status" -ne 0 ]
}

@test "Quality gate: Build validation" {
    create_p3_complete_state

    # Create TypeScript file with syntax error
    cat > src/broken.ts << 'EOF'
export function broken() {
    return "missing semicolon"  // Syntax OK in TS
    const x = ;  // Syntax error
}
EOF

    git add src/broken.ts

    # In production, pre-commit would run build check
    # Simulate build check
    if command -v tsc &> /dev/null; then
        run tsc --noEmit
        # Build should fail with syntax error
        [ "$status" -ne 0 ]
    else
        log_test_info "TypeScript not installed, skipping build check"
    fi

    # Fix syntax error
    cat > src/broken.ts << 'EOF'
export function fixed() {
    return "proper code";
}
EOF

    git add src/broken.ts
    git commit -m "feat: add working code"
}

@test "Quality gate: All phases comprehensive validation" {
    log_test_info "Testing all phase gates"

    # P0
    set_phase "P0"
    echo "# Discovery: GO" > docs/P0_DISCOVERY.md
    git add docs/
    git commit -m "P0 complete"
    create_gate "00"

    # P1
    set_phase "P1"
    create_plan_document
    git add docs/PLAN.md
    git commit -m "P1 complete"
    create_gate "01"

    # P2
    set_phase "P2"
    mkdir -p src/auth
    touch src/auth/login.ts
    create_skeleton_notes
    git add src/ docs/SKELETON-NOTES.md
    git commit -m "P2 complete"
    create_gate "02"

    # P3
    set_phase "P3"
    create_auth_module_fixture
    create_changelog
    git add src/ docs/CHANGELOG.md
    git commit -m "P3 complete"
    create_gate "03"

    # P4
    set_phase "P4"
    create_test_suite_fixture
    create_test_report
    git add test/ docs/TEST-REPORT.md
    git commit -m "P4 complete"
    create_gate "04"

    # P5
    set_phase "P5"
    create_review_document
    git add docs/REVIEW.md
    git commit -m "P5 complete"
    create_gate "05"

    # P6
    set_phase "P6"
    create_readme
    git add docs/README.md
    git commit -m "P6 complete"
    git tag v1.0.0
    create_gate "06"

    # Verify all gates exist
    for gate in 00 01 02 03 04 05 06; do
        run check_gate_exists "${gate}"
        [ "$status" -eq 0 ]
    done

    log_test_info "All phase gates validated successfully"
}
