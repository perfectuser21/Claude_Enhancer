# CI工作流测试指南

## 概述

本指南提供完整的CI工作流测试策略，确保Claude Enhancer的8-Phase工作流系统的所有检查点正确工作。

---

## 快速开始

### 1分钟快速验证

```bash
# 快速检查CI配置是否正常
bash test/ci_quick_validation.sh
```

### 15分钟完整测试

```bash
# 运行完整测试套件（15个测试用例）
bash test/ci_workflow_comprehensive_test.sh
```

### 查看测试报告

```bash
# 打开最新的测试报告
cat test/reports/ci_workflow_test_*.md | tail -1
```

---

## 测试架构

### 三层测试策略

```
┌─────────────────────────────────────────────┐
│  层级1: 快速验证（2分钟）                      │
│  - 配置文件存在性                             │
│  - Hook可执行权限                            │
│  - Gates.yml语法                            │
│  用途：CI的第一道防线                         │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  层级2: 功能测试（15分钟）                     │
│  - Phase顺序验证（4个用例）                   │
│  - 路径白名单（4个用例）                      │
│  - Must_produce（3个用例）                  │
│  - P4测试强制（2个用例）                      │
│  - Linting/安全（2个用例）                   │
│  用途：全面验证CI逻辑                         │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  层级3: 集成测试（可选）                       │
│  - 完整工作流模拟                             │
│  - 多Phase循环测试                           │
│  - 压力测试                                  │
│  用途：生产环境验证                           │
└─────────────────────────────────────────────┘
```

---

## 测试用例详解

### 分类1: Phase顺序与Gate验证

#### TC-001: Phase顺序正确性检查
```bash
# 测试目标：验证Phase转换逻辑
# 前置条件：P2 gate存在
# 操作：在P3提交代码
# 预期：✅ 显示"P2 gate已通过"

# 手动测试
set_phase "P3"
touch .gates/02.ok
git add src/test.js
git commit -m "test"
# 应该通过
```

#### TC-002: Phase跳跃警告
```bash
# 测试目标：检测Phase被跳过
# 前置条件：P4 gate不存在
# 操作：在P5提交
# 预期：⚠️ 警告但不阻塞

# 手动测试
set_phase "P5"
rm -f .gates/04.ok
git add docs/REVIEW.md
git commit -m "test"
# 应该显示警告
```

#### TC-003: P7→P1循环
```bash
# 测试目标：验证工作流循环
# 前置条件：P7完成
# 操作：切换到P1
# 预期：✅ 正常工作

# 手动测试
touch .gates/07.ok
set_phase "P1"
git add docs/PLAN.md
git commit -m "test"
# 应该通过
```

#### TC-004: 非法Phase拒绝
```bash
# 测试目标：拒绝非法Phase
# 操作：设置Phase=P9
# 预期：❌ 显示"非法的Phase 'P9'"

# 手动测试
echo "P9" > .phase/current
git add test.txt
git commit -m "test"
# 应该失败
```

---

### 分类2: 路径白名单验证

#### TC-005: P1修改允许路径
```bash
# 测试目标：验证白名单允许逻辑
# Phase：P1
# 文件：docs/PLAN.md（在白名单中）
# 预期：✅ 通过

# 手动测试
set_phase "P1"
git add docs/PLAN.md
git commit -m "test"
# 应该通过
```

#### TC-006: P1修改禁止路径
```bash
# 测试目标：验证白名单阻止逻辑
# Phase：P1
# 文件：src/auth.ts（不在白名单中）
# 预期：❌ "不在允许路径内"

# 手动测试
set_phase "P1"
git add src/auth.ts
git commit -m "test"
# 应该失败
```

#### TC-007: P3多路径
```bash
# 测试目标：验证多路径匹配
# Phase：P3
# 文件：src/** 和 docs/CHANGELOG.md
# 预期：✅ 都通过

# 手动测试
set_phase "P3"
git add src/feature.js docs/CHANGELOG.md
git commit -m "test"
# 应该通过
```

#### TC-008: Glob模式匹配
```bash
# 测试目标：验证 ** 通配符
# Phase：P2
# 文件：src/auth/controllers/login.ts（深层嵌套）
# 预期：✅ 匹配 src/**

# 手动测试
set_phase "P2"
mkdir -p src/auth/controllers
git add src/auth/controllers/login.ts
git commit -m "test"
# 应该通过
```

---

### 分类3: Must_produce检查

#### TC-009: P1任务不足
```bash
# 测试目标：检测产出不足
# Phase：P1结束（提交.gates/01.ok）
# PLAN.md：只有3条任务（需要≥5条）
# 预期：❌ "必须产出未完成"

# 手动测试
# 1. 创建只有3条任务的PLAN.md
cat > docs/PLAN.md <<EOF
## 任务清单
- T1
- T2
- T3
EOF

# 2. 尝试提交gate
git add docs/PLAN.md .gates/01.ok
git commit -m "test"
# 应该失败
```

#### TC-010: P1任务充足
```bash
# 测试目标：验证产出充足通过
# Phase：P1结束
# PLAN.md：5条任务
# 预期：✅ "Phase结束验证通过"

# 手动测试
cat > docs/PLAN.md <<EOF
## 任务清单
- T1: 实现登录
- T2: 实现注册
- T3: 实现密码重置
- T4: 实现会话管理
- T5: 实现权限验证

## 受影响文件清单
- src/auth.ts

## 回滚方案
git revert
EOF

git add docs/PLAN.md .gates/01.ok
git commit -m "test"
# 应该通过
```

#### TC-011: P4缺少测试报告
```bash
# 测试目标：检测P4产出缺失
# Phase：P4结束
# 文件：docs/TEST-REPORT.md不存在
# 预期：❌ 失败

# 手动测试
set_phase "P4"
git add .gates/04.ok  # 没有添加TEST-REPORT.md
git commit -m "test"
# 应该失败
```

---

### 分类4: P4测试强制运行

#### TC-012: 测试失败阻止
```bash
# 测试目标：P4测试失败阻止提交
# Phase：P4
# 操作：npm test返回非0
# 预期：❌ "P4阶段必须所有测试通过"

# 手动测试（需要package.json）
set_phase "P4"
# 修改测试使其失败
git add tests/
git commit -m "test"
# 应该失败（如果有npm test）
```

#### TC-013: 测试通过
```bash
# 测试目标：P4测试通过允许提交
# Phase：P4
# 操作：npm test成功
# 预期：✅ "P4测试验证通过"

# 手动测试
set_phase "P4"
# 确保所有测试通过
git add docs/TEST-REPORT.md
git commit -m "test"
# 应该通过
```

---

### 分类5: Linting和安全检查

#### TC-014: Shellcheck警告
```bash
# 测试目标：Shellcheck检测代码问题
# 文件：包含SC2086等警告的脚本
# 预期：❌ "有shellcheck警告"

# 手动测试（需要shellcheck）
cat > src/bad.sh <<'EOF'
#!/bin/bash
echo $undefined_var  # SC2086
EOF

git add src/bad.sh
git commit -m "test"
# 应该失败
```

#### TC-015: 硬编码密码
```bash
# 测试目标：安全扫描检测密码
# 文件：包含 password="secret"
# 预期：❌ "检测到硬编码密码"

# 手动测试
cat > src/config.js <<EOF
const config = {
    password: "secret123"
};
EOF

git add src/config.js
git commit -m "test"
# 应该失败
```

---

## CI集成方法

### 方法1: GitHub Actions集成

```yaml
# .github/workflows/ci-test.yml
name: CI Workflow Tests

on: [push, pull_request]

jobs:
  quick-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Quick Validation
        run: bash test/ci_quick_validation.sh

  full-test:
    runs-on: ubuntu-latest
    needs: quick-check
    steps:
      - uses: actions/checkout@v3
      - name: Install Dependencies
        run: |
          sudo apt-get install -y shellcheck
          npm install
      - name: Comprehensive Test
        run: bash test/ci_workflow_comprehensive_test.sh
      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-report
          path: test/reports/ci_workflow_test_*.md
```

### 方法2: GitLab CI集成

```yaml
# .gitlab-ci.yml
stages:
  - quick-check
  - full-test

quick-validation:
  stage: quick-check
  script:
    - bash test/ci_quick_validation.sh

comprehensive-test:
  stage: full-test
  script:
    - apt-get install -y shellcheck
    - bash test/ci_workflow_comprehensive_test.sh
  artifacts:
    paths:
      - test/reports/
    when: always
```

### 方法3: 本地Pre-push Hook

```bash
# .git/hooks/pre-push
#!/bin/bash

echo "Running CI workflow tests..."
bash test/ci_quick_validation.sh

if [ $? -ne 0 ]; then
    echo "❌ CI tests failed. Fix issues before pushing."
    exit 1
fi

echo "✅ CI tests passed"
```

---

## 验证CI检查点的方法

### 方法A: 输出解析验证

```bash
# 验证特定检查点是否执行
verify_checkpoint() {
    local checkpoint="$1"
    local output_file="/tmp/commit_output.txt"

    git commit -m "test" > "$output_file" 2>&1 || true

    case "$checkpoint" in
        "phase_order")
            grep -q "Phase顺序验证通过" "$output_file" ;;
        "path_validation")
            grep -q "所有文件路径验证通过" "$output_file" ;;
        "security")
            grep -q "安全检查通过" "$output_file" ;;
        *)
            return 1 ;;
    esac
}
```

### 方法B: 退出码验证

```bash
# 验证应该失败的场景确实失败
test_should_fail() {
    local scenario="$1"

    if git commit -m "$scenario" >/dev/null 2>&1; then
        echo "❌ FAIL: $scenario should be blocked but passed"
        return 1
    else
        echo "✅ PASS: $scenario correctly blocked"
        return 0
    fi
}
```

### 方法C: 文件系统验证

```bash
# 验证gate文件是否正确创建
verify_gate_created() {
    local phase_num="$1"

    if [ -f ".gates/$(printf '%02d' $phase_num).ok" ]; then
        echo "✅ Gate $phase_num created"
        return 0
    else
        echo "❌ Gate $phase_num missing"
        return 1
    fi
}
```

---

## 预期CI运行结果

### 场景1: 所有检查通过

```
═══════════════════════════════════════════════════════════════
  Claude Enhancer - CI工作流综合测试
═══════════════════════════════════════════════════════════════

▶ 分类1: Phase顺序与Gate验证

[TC-001] Phase顺序正确性检查（P3提交时P2 gate存在）
    ✅ PASS P2 gate存在，P3提交通过

[TC-002] Phase跳跃警告（P5提交时P4 gate不存在）
    ✅ PASS 正确显示警告信息

[TC-003] P7→P1循环验证
    ✅ PASS P7→P1循环正常工作

[TC-004] 非法Phase拒绝（P9）
    ✅ PASS 正确拒绝非法Phase

...

═══════════════════════════════════════════════════════════════
测试汇总
═══════════════════════════════════════════════════════════════

   总数: 15
   通过: 15
   失败: 0
   跳过: 0
   成功率: 100.0%

════════════════════════════════════════════════════════════
   🎉 所有测试通过！CI工作流验证成功！
════════════════════════════════════════════════════════════

   📊 详细报告: test/reports/ci_workflow_test_20251008_120000.md
```

### 场景2: 部分检查失败

```
[TC-006] P1修改禁止路径（src/）失败
    ❌ FAIL 禁止路径应该被阻止

...

═══════════════════════════════════════════════════════════════
测试汇总
═══════════════════════════════════════════════════════════════

   总数: 15
   通过: 12
   失败: 3
   跳过: 0
   成功率: 80.0%

════════════════════════════════════════════════════════════
   ⚠️  部分测试失败，需要修复
════════════════════════════════════════════════════════════
```

---

## 故障排查

### 问题1: Pre-commit hook未触发

**症状**: 测试直接通过，没有任何检查

**解决方案**:
```bash
# 1. 检查hook是否安装
ls -la .git/hooks/pre-commit

# 2. 检查可执行权限
chmod +x .git/hooks/pre-commit

# 3. 重新安装
.claude/install.sh
```

### 问题2: Gates.yml规则不生效

**症状**: 应该被阻止的路径可以提交

**解决方案**:
```bash
# 1. 验证gates.yml语法
grep -A5 "^  P1:" .workflow/gates.yml

# 2. 检查allow_paths格式
# 正确格式：allow_paths: ["path1", "path2"]

# 3. 测试glob匹配
bash -c 'source .git/hooks/pre-commit; match_glob "src/test.js" "src/**"'
```

### 问题3: Must_produce检查不工作

**症状**: Phase结束时没有验证产出

**解决方案**:
```bash
# 1. 确认提交了gate文件
git status | grep ".gates/"

# 2. 检查must_produce配置
grep -A10 "must_produce:" .workflow/gates.yml

# 3. 查看hook日志
tail .workflow/logs/hooks.log
```

---

## 测试最佳实践

### 1. 测试隔离原则

```bash
# ✅ 好的做法：使用临时工作区
test_in_isolation() {
    local workspace="/tmp/test_$$"
    git clone . "$workspace"
    cd "$workspace"
    # 运行测试
    cd -
    rm -rf "$workspace"
}

# ❌ 不好的做法：直接在项目目录测试
git add .
git commit -m "test"  # 可能污染项目
```

### 2. 状态恢复

```bash
# ✅ 好的做法：保存和恢复状态
test_with_restore() {
    local original_phase=$(cat .phase/current)
    # 测试...
    echo "$original_phase" > .phase/current
}

# ❌ 不好的做法：不恢复状态
# 测试后Phase被改变，影响后续测试
```

### 3. 清晰的错误消息

```bash
# ✅ 好的做法：提供详细的失败信息
if ! test_something; then
    echo "❌ FAIL: Expected X but got Y"
    echo "   Context: Phase=$PHASE, Files=$FILES"
fi

# ❌ 不好的做法：只说"失败"
echo "Test failed"
```

---

## 性能基准

### 测试执行时间目标

| 测试类型 | 目标时间 | 实际时间 | 状态 |
|---------|---------|---------|------|
| 快速验证 | < 30秒 | ~15秒 | ✅ |
| 单个用例 | < 5秒 | ~3秒 | ✅ |
| 完整测试套件 | < 5分钟 | ~2分钟 | ✅ |
| CI全流程 | < 10分钟 | ~8分钟 | ✅ |

### 优化建议

1. **并行执行**: 独立的测试用例可以并行运行
2. **增量测试**: 只测试变更相关的检查点
3. **缓存结果**: 缓存shellcheck等工具的结果

---

## 扩展测试场景

### 压力测试

```bash
# 测试大量文件提交
test_large_commit() {
    for i in {1..100}; do
        echo "test" > "src/file$i.js"
    done
    git add src/
    git commit -m "Large commit test"
}
```

### 并发测试

```bash
# 模拟多人同时提交
test_concurrent_commits() {
    for i in {1..5}; do
        (
            git checkout -b "test-$i"
            echo "test" > "test$i.txt"
            git add .
            git commit -m "Concurrent test $i"
        ) &
    done
    wait
}
```

### 回归测试

```bash
# 验证修复后的bug不再出现
test_regression_issue_123() {
    # 重现之前的bug场景
    set_phase "P1"
    echo "bug" > src/test.js
    git add src/test.js

    # 应该被阻止（之前可能通过了）
    if git commit -m "test" 2>&1 | grep -q "不在允许路径"; then
        echo "✅ Issue #123 fixed"
    else
        echo "❌ Issue #123 regression detected"
    fi
}
```

---

## 总结

### 关键要点

1. **分层测试**: 快速验证 → 功能测试 → 集成测试
2. **自动化优先**: 所有测试都可以自动运行
3. **隔离原则**: 测试不应污染项目状态
4. **清晰反馈**: 失败时提供明确的修复建议

### 维护清单

- [ ] 每次修改gates.yml后运行完整测试
- [ ] 每周运行一次回归测试
- [ ] 每月更新测试用例覆盖新功能
- [ ] 记录新发现的边界情况

### 相关文件

- 测试脚本: `/home/xx/dev/Claude Enhancer 5.0/test/ci_workflow_comprehensive_test.sh`
- 快速验证: `/home/xx/dev/Claude Enhancer 5.0/test/ci_quick_validation.sh`
- Gates配置: `/home/xx/dev/Claude Enhancer 5.0/.workflow/gates.yml`
- Pre-commit hook: `/home/xx/dev/Claude Enhancer 5.0/.git/hooks/pre-commit`
- 测试报告: `/home/xx/dev/Claude Enhancer 5.0/test/reports/`

---

*Generated by Claude Code - Test Engineering Specialist*
*Version: 1.0.0*
*Last Updated: 2025-10-08*
