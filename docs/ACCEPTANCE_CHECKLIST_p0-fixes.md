# Acceptance Checklist - P0 Fixes from ChatGPT Audit

## 📋 总体目标

修复 ChatGPT 审计发现的 6 个 P0 关键问题，提升 Claude Enhancer 工作流系统的可靠性和安全性。

---

## ✅ P0-1: Phase Detection Bug（Phase 检测修复）

### 功能验收

- [ ] **测试 1：normalize_phase 函数**
  ```bash
  source .git/hooks/lib/ce_common.sh

  # 测试各种格式
  normalize_phase "Phase 3"    # 期望: "phase3"
  normalize_phase "P3"         # 期望: "phase3"
  normalize_phase "phase3"     # 期望: "phase3"
  normalize_phase "3"          # 期望: "phase3"
  normalize_phase "Closure"    # 期望: "phase7"
  normalize_phase ""           # 期望: ""
  normalize_phase "invalid"    # 期望: "" + warning
  ```
  结果: ___________

- [ ] **测试 2：read_phase 函数**
  ```bash
  # 测试从 .workflow/current 读取
  echo "phase: Phase 3" > .workflow/current
  read_phase                   # 期望: "phase3"

  echo "phase: P3" > .workflow/current
  read_phase                   # 期望: "phase3"

  # 测试分支推断
  rm .workflow/current
  git checkout -b feature/test
  read_phase                   # 期望: "phase2"
  git checkout feature/p0-fixes-chatgpt-audit
  ```
  结果: ___________

- [ ] **测试 3：Pre-commit 集成**
  ```bash
  # 创建测试 commit
  echo "test" > test.txt
  git add test.txt
  git commit -m "test: phase detection"

  # 检查 commit 输出
  # 应该显示: "Current phase: phaseX"
  # 不应该有 Phase 检测错误
  ```
  结果: ___________

### 技术验收

- [ ] **代码检查**
  - [ ] `.git/hooks/lib/ce_common.sh` 文件存在
  - [ ] `normalize_phase()` 函数实现正确
  - [ ] `read_phase()` 函数实现正确
  - [ ] 不依赖 COMMIT_EDITMSG
  - [ ] awk 解析处理空格和大小写

- [ ] **错误处理**
  - [ ] 无效格式返回空字符串 + 警告
  - [ ] 文件不存在时有 fallback

- [ ] **性能检查**
  - [ ] Phase 检测耗时 < 50ms

---

## ✅ P0-2: Fail-Closed Strategy（失败关闭策略）

### 功能验收

- [ ] **测试 1：脚本缺失时硬阻止**
  ```bash
  # 备份脚本
  mv scripts/static_checks.sh scripts/static_checks.sh.bak

  # 尝试 commit
  echo "phase: Phase3" > .workflow/current
  echo "test" >> test.txt
  git add test.txt
  git commit -m "test: should fail"

  # 期望: ❌ HARD BLOCK - Script missing
  # 实际: ___________

  # 恢复脚本
  mv scripts/static_checks.sh.bak scripts/static_checks.sh
  ```

- [ ] **测试 2：一次性覆盖机制**
  ```bash
  # 删除脚本
  mv scripts/static_checks.sh scripts/static_checks.sh.bak

  # 创建覆盖文件
  mkdir -p .workflow/override
  echo "test override" > .workflow/override/allow-missing-phase3-check.once

  # 尝试 commit
  git commit -m "test: should pass with override"

  # 期望: ⚠️  One-time override applied + 成功
  # 覆盖文件应该被删除
  ls .workflow/override/allow-missing-phase3-check.once  # 应该不存在

  # 恢复
  mv scripts/static_checks.sh.bak scripts/static_checks.sh
  ```

- [ ] **测试 3：覆盖不能重复使用**
  ```bash
  # 创建覆盖后第二次 commit
  echo "override" > .workflow/override/allow-missing-phase3-check.once
  git commit -m "test1"  # 成功
  git commit -m "test2"  # 应该失败
  ```

- [ ] **测试 4：审计日志**
  ```bash
  cat .git/ce/logs/overrides.log
  # 应该包含覆盖记录和时间戳
  ```

### 技术验收

- [ ] **代码检查**
  - [ ] `check_phase_quality_gates()` 函数实现
  - [ ] Fail-closed 逻辑正确
  - [ ] `check_override()` 函数实现
  - [ ] 覆盖文件使用后自动删除
  - [ ] 审计日志写入

- [ ] **Phase 覆盖**
  - [ ] Phase 3: `allow-missing-phase3-check.once`
  - [ ] Phase 4: `allow-missing-phase4-check.once`
  - [ ] Phase 7: `allow-missing-phase7-cleanup.once`

---

## ✅ P0-3: State Migration（状态迁移）

### 功能验收

- [ ] **测试 1：状态文件位置**
  ```bash
  # 创建状态标记
  source .git/hooks/lib/ce_common.sh
  mark_gate_passed "phase3_gate_passed"

  # 检查文件位置
  ls -la .git/ce/.phase3_gate_passed     # 应该存在
  ls -la .workflow/.phase3_gate_passed   # 不应该存在
  ```

- [ ] **测试 2：工作目录干净**
  ```bash
  git status
  # 不应该显示 .phase*_gate_passed 文件
  ```

- [ ] **测试 3：日志目录**
  ```bash
  ls -la .git/ce/logs/
  # 目录应该存在
  ```

- [ ] **测试 4：check_gate_passed 函数**
  ```bash
  mark_gate_passed "test_gate"
  check_gate_passed "test_gate"  # 应该返回 0
  check_gate_passed "not_exist"  # 应该返回 1
  ```

### 技术验收

- [ ] **代码检查**
  - [ ] `STATE_DIR=.git/ce/`
  - [ ] `LOG_DIR=.git/ce/logs/`
  - [ ] `mkdir -p` 确保目录存在
  - [ ] `mark_gate_passed()` 写入正确位置
  - [ ] `check_gate_passed()` 读取正确位置

- [ ] **清理验证**
  - [ ] .gitignore 包含备份保护规则
  - [ ] 旧位置的文件已删除或移除

---

## ✅ P0-4: Enhanced Tag Protection（增强 Tag 保护）

### 功能验收

- [ ] **测试 1：Lightweight tag 被拒绝**
  ```bash
  # 创建 lightweight tag
  git tag v9.9.9-test
  git push origin v9.9.9-test

  # 期望: ❌ Must be annotated tag
  # 实际: ___________

  # 清理
  git tag -d v9.9.9-test
  ```

- [ ] **测试 2：Annotated tag 被接受**
  ```bash
  git checkout main
  git tag -a v9.9.9-test -m "Test tag"
  git push origin v9.9.9-test

  # 期望: ✅ All validations passed
  # 实际: ___________

  # 清理
  git push --delete origin v9.9.9-test
  git tag -d v9.9.9-test
  git checkout feature/p0-fixes-chatgpt-audit
  ```

- [ ] **测试 3：从 feature 分支拒绝**
  ```bash
  # 在 feature 分支创建 tag
  git tag -a v9.9.9-test -m "Test"
  git push origin v9.9.9-test

  # 期望: ❌ Can only push from main/master
  # 实际: ___________

  git tag -d v9.9.9-test
  ```

- [ ] **测试 4：Ancestor 检查**
  ```bash
  # 创建独立分支（不是 main 的后代）
  git checkout --orphan isolated
  git commit --allow-empty -m "isolated"
  git checkout main
  git tag -a v9.9.9-test -m "Test" isolated
  git push origin v9.9.9-test

  # 期望: ❌ Not descendant of origin/main
  # 实际: ___________

  # 清理
  git tag -d v9.9.9-test
  git branch -D isolated
  git checkout feature/p0-fixes-chatgpt-audit
  ```

- [ ] **测试 5：可选签名验证**
  ```bash
  # 启用签名要求
  mkdir -p .workflow/config
  touch .workflow/config/require_signed_tags

  # 创建未签名 tag
  git checkout main
  git tag -a v9.9.9-test -m "Test"
  git push origin v9.9.9-test

  # 期望: ❌ Signature verification failed
  # 实际: ___________

  # 清理
  rm .workflow/config/require_signed_tags
  git tag -d v9.9.9-test
  git checkout feature/p0-fixes-chatgpt-audit
  ```

### 技术验收

- [ ] **代码检查**
  - [ ] `git cat-file -t` 检查 tag 类型
  - [ ] `git merge-base --is-ancestor` 检查祖先关系
  - [ ] `git fetch origin main` 更新远程引用
  - [ ] `git tag -v` 签名验证
  - [ ] 配置文件控制签名要求

- [ ] **错误提示**
  - [ ] 每种错误有清晰的提示
  - [ ] 提供修复建议

---

## ✅ P0-5: CE Gates Workflow（CI 工作流）

### 功能验收

- [ ] **测试 1：工作流文件存在**
  ```bash
  ls -la .github/workflows/ce-gates.yml
  # 文件应该存在
  ```

- [ ] **测试 2：PR 触发工作流**
  ```bash
  # 推送分支
  git push origin feature/p0-fixes-chatgpt-audit

  # 创建 PR
  gh pr create --title "Test CE Gates" --body "Test"

  # 检查工作流
  gh pr checks
  # 应该显示:
  # - ce/phase3-static-checks
  # - ce/phase4-pre-merge-audit
  # - ce/phase7-final-validation
  # - ce/gates-summary
  ```

- [ ] **测试 3：工作流成功运行**
  ```bash
  gh run list --workflow=ce-gates.yml
  # 应该有运行记录

  gh run view [run-id]
  # 查看详细结果
  ```

- [ ] **测试 4：Fallback 逻辑**
  ```bash
  # 删除某个脚本
  mv scripts/static_checks.sh scripts/static_checks.sh.bak
  git add .
  git commit -m "test: missing script"
  git push

  # 检查 CI
  # 期望: ⚠️  Script not found + Pass
  # (因为有 fallback 逻辑)

  # 恢复
  git reset HEAD~1
  mv scripts/static_checks.sh.bak scripts/static_checks.sh
  ```

### 技术验收

- [ ] **工作流结构**
  - [ ] 3 个主要 job (phase3, phase4, phase7)
  - [ ] 1 个汇总 job (ce_gates_summary)
  - [ ] 正确的依赖关系 (needs)
  - [ ] 超时设置 (timeout-minutes)

- [ ] **Branch Protection**
  - [ ] GitHub 设置中要求这些检查通过
  - [ ] 文档说明如何配置

- [ ] **错误处理**
  - [ ] 脚本不存在时有 fallback
  - [ ] 错误有清晰提示

---

## ✅ P0-6: Parsing Robustness（解析健壮性）

### 功能验收

- [ ] **测试 1：脚本位置**
  ```bash
  ls -la scripts/verify-phase-consistency.sh  # 应该存在
  ls -la tools/verify-phase-consistency.sh    # 不应该存在
  ```

- [ ] **测试 2：文档引用**
  ```bash
  grep -r "tools/verify-phase-consistency" .
  # 不应该有结果

  grep -r "scripts/verify-phase-consistency" CLAUDE.md docs/ .claude/
  # 应该找到引用
  ```

- [ ] **测试 3：LOG_DIR 创建**
  ```bash
  rm -rf .git/ce/logs
  source .git/hooks/lib/ce_common.sh
  ls -la .git/ce/logs/
  # 目录应该自动创建
  ```

- [ ] **测试 4：Awk 解析**
  ```bash
  # 测试带空格的 YAML
  echo "phase:  Phase 3  " > /tmp/test.yaml
  awk -F: '/^[[:space:]]*phase[[:space:]]*:/ {print $2}' /tmp/test.yaml
  # 应该正确提取 "  Phase 3  "
  ```

### 技术验收

- [ ] **文件组织**
  - [ ] 所有验证脚本在 `scripts/`
  - [ ] `tools/` 只用于工具性脚本

- [ ] **文档一致性**
  - [ ] 所有文档统一使用 "6 files"
  - [ ] 所有引用已更新

- [ ] **健壮性**
  - [ ] LOG_DIR 在使用前创建
  - [ ] Awk 处理空格和换行

---

## 🎯 整体集成测试

### 端到端测试场景

- [ ] **场景 1：正常提交流程**
  ```bash
  # 1. 切换到 Phase 3
  echo "phase: Phase 3" > .workflow/current

  # 2. 修改文件
  echo "test" >> test.txt
  git add test.txt

  # 3. Commit
  git commit -m "test: normal flow"

  # 期望:
  # - Phase 检测正确
  # - Quality gate 执行
  # - 状态写入 .git/ce/
  # - Commit 成功
  ```

- [ ] **场景 2：质量门禁失败**
  ```bash
  # 删除脚本，不使用覆盖
  mv scripts/static_checks.sh scripts/static_checks.sh.bak
  git commit -m "test: should fail"

  # 期望: ❌ HARD BLOCK

  mv scripts/static_checks.sh.bak scripts/static_checks.sh
  ```

- [ ] **场景 3：完整 PR 流程**
  ```bash
  # 1. 推送分支
  git push origin feature/p0-fixes-chatgpt-audit

  # 2. 创建 PR
  gh pr create

  # 3. CI 运行
  gh pr checks --watch

  # 4. 所有检查通过
  gh pr merge --auto --squash
  ```

---

## 📊 质量指标

### 可靠性指标

- [ ] Phase 检测成功率 = 100%（10次测试）
- [ ] 质量门禁执行率 = 100%（无绕过）
- [ ] CI 通过率 ≥ 95%

### 性能指标

- [ ] Pre-commit hook 执行时间 < 5s
- [ ] Phase 检测耗时 < 50ms
- [ ] CI workflow 总耗时 < 10 分钟

### 安全指标

- [ ] Tag 保护覆盖率 = 100%（3层验证）
- [ ] 工作目录无状态污染
- [ ] 无法通过常规手段绕过质量门禁

---

## ✅ 最终验收标准

### 必须全部通过

- [ ] 所有 P0-1 到 P0-6 的功能测试通过
- [ ] 所有技术验收项通过
- [ ] 3 个集成测试场景通过
- [ ] 所有质量指标达标

### 文档完整性

- [ ] P1_DISCOVERY.md 完整
- [ ] ACCEPTANCE_CHECKLIST.md 完整（本文件）
- [ ] PLAN.md 详细
- [ ] REVIEW.md 创建（Phase 4）

### 无遗留问题

- [ ] 没有 TODO/FIXME 标记
- [ ] 没有测试用文件残留
- [ ] Git 工作目录干净
- [ ] 所有临时分支已删除

---

## 📝 验收签字

**测试执行人：** ________________
**执行日期：** ________________
**结果：** ☐ 通过  ☐ 不通过

**备注：**
_______________________________________________
_______________________________________________
_______________________________________________
