# Quality Gates Rehearsal Guide
# 质量门禁演练指南

## 📖 Overview / 概述

This guide explains how to test quality gates without modifying repository state using the rehearsal scripts.

本指南说明如何使用演练脚本测试质量门禁，无副作用不修改仓库状态。

---

## 🎯 Purpose / 用途

- **No Side Effects** / **无副作用**: Scripts only read, never modify repository
- **Safe Testing** / **安全测试**: Validate gate logic before deployment
- **Bilingual** / **双语支持**: Chinese (演练) and English (rehearse) aliases

---

## 📝 Usage / 用法

### English Script / 英文脚本

```bash
# Test with mock quality score
MOCK_SCORE=84 bash scripts/rehearse_pre_push_gates.sh

# Test with mock coverage
MOCK_COVERAGE=79 bash scripts/rehearse_pre_push_gates.sh

# Test with invalid signatures on main branch
BRANCH=main MOCK_SIG=invalid bash scripts/rehearse_pre_push_gates.sh

# Combine multiple mocks
MOCK_SCORE=90 MOCK_COVERAGE=85 bash scripts/rehearse_pre_push_gates.sh
```

### Chinese Script / 中文脚本

```bash
# 测试模拟质量分数
MOCK_SCORE=84 bash scripts/演练_pre_push_gates.sh

# 测试模拟覆盖率
MOCK_COVERAGE=79 bash scripts/演练_pre_push_gates.sh

# 测试 main 分支无效签名
BRANCH=main MOCK_SIG=invalid bash scripts/演练_pre_push_gates.sh

# 组合多个模拟
MOCK_SCORE=90 MOCK_COVERAGE=85 bash scripts/演练_pre_push_gates.sh
```

---

## 🎭 Mock Environment Variables / 模拟环境变量

| Variable | Description (English) | 描述（中文） | Example |
|----------|----------------------|-------------|---------|
| `MOCK_SCORE` | Override quality score | 覆盖质量分数 | `MOCK_SCORE=84` |
| `MOCK_COVERAGE` | Override coverage percentage | 覆盖覆盖率百分比 | `MOCK_COVERAGE=79` |
| `MOCK_SIG` | Set to "invalid" for signature failure | 设为 "invalid" 模拟签名失败 | `MOCK_SIG=invalid` |
| `BRANCH` | Override current branch name | 覆盖当前分支名 | `BRANCH=main` |

---

## 🧪 Three Blocking Scenarios / 三种阻止场景

### 1. Quality Score Too Low / 质量分数过低

**Threshold**: Score must be ≥ 85
**阈值**：分数必须 ≥ 85

```bash
# Should BLOCK (84 < 85)
# 应该阻止（84 < 85）
MOCK_SCORE=84 bash scripts/rehearse_pre_push_gates.sh

# Should PASS (90 >= 85)
# 应该通过（90 >= 85）
MOCK_SCORE=90 bash scripts/rehearse_pre_push_gates.sh
```

**Expected Output / 预期输出**:
```
❌ BLOCK: quality score 84 < 85 (minimum required)
❌ REHEARSAL RESULT: Gates would BLOCK
```

---

### 2. Coverage Too Low / 覆盖率过低

**Threshold**: Coverage must be ≥ 80%
**阈值**：覆盖率必须 ≥ 80%

```bash
# Should BLOCK (79% < 80%)
# 应该阻止（79% < 80%）
MOCK_COVERAGE=79 bash scripts/演练_pre_push_gates.sh

# Should PASS (85% >= 80%)
# 应该通过（85% >= 80%）
MOCK_COVERAGE=85 bash scripts/演练_pre_push_gates.sh
```

**Expected Output / 预期输出**:
```
❌ BLOCK: coverage 79% < 80% (minimum required)
❌ 演练结果：门禁会阻止
```

---

### 3. Missing Signatures on Protected Branch / 保护分支缺少签名

**Threshold**: Protected branches (main/master/production) require 8 signatures
**阈值**：保护分支（main/master/production）需要 8 个签名

```bash
# Should BLOCK if < 8 signatures exist
# 如果 < 8 个签名存在应该阻止
BRANCH=main MOCK_SIG=invalid bash scripts/rehearse_pre_push_gates.sh

# Feature branch skips signature check
# Feature 分支跳过签名检查
BRANCH=feature/test bash scripts/rehearse_pre_push_gates.sh
```

**Expected Output / 预期输出** (if signatures insufficient):
```
❌ BLOCK: gate signatures invalid (MOCK)
❌ FINAL GATE: BLOCKED
```

---

## 📊 Understanding Output / 理解输出

### Success Case / 成功案例

```
╔═══════════════════════════════════════════════════════╗
║     PRE-PUSH QUALITY GATES REHEARSAL (No Changes)    ║
╚═══════════════════════════════════════════════════════╝

📋 Rehearsal Configuration:
   Project: Claude Enhancer 5.0
   Real Branch: feature/quality-gates
   Test Branch: feature/quality-gates

📊 Quality Thresholds: Score>=85, Coverage>=80%, Sigs>=8
✅ Quality score: 90 >= 85
✅ Coverage: 85% >= 80%
ℹ️  Skipping gate signature check (not a protected branch)

════════════════════════════════════════════
✅ FINAL GATE: PASSED
════════════════════════════════════════════

✅ REHEARSAL RESULT: Gates would PASS
```

### Failure Case / 失败案例

```
╔═══════════════════════════════════════════════════════╗
║         PRE-PUSH 质量门禁演练（无副作用）           ║
╚═══════════════════════════════════════════════════════╝

📋 演练配置：
   项目：Claude Enhancer 5.0
   真实分支：feature/quality-gates
   测试分支：feature/quality-gates

🎭 模拟模式激活：
   MOCK_SCORE=84

🔍 执行质量门禁检查...

📊 Quality Thresholds: Score>=85, Coverage>=80%, Sigs>=8
❌ BLOCK: quality score 84 < 85 (minimum required)

════════════════════════════════════════════
❌ FINAL GATE: BLOCKED
════════════════════════════════════════════

❌ 演练结果：门禁会阻止
```

---

## 🔧 Configuration / 配置

Quality gate thresholds are defined in `.workflow/gates.yml`:

质量门禁阈值定义在 `.workflow/gates.yml`:

```yaml
quality:
  quality_min: 85        # Minimum quality score
  coverage_min: 80       # Minimum coverage percentage
  required_signatures: 8 # Required signatures for protected branches
```

You can also override using environment variables:

也可以使用环境变量覆盖：

```bash
QUALITY_MIN=90 COVERAGE_MIN=85 REQUIRED_SIGS=10 bash scripts/rehearse_pre_push_gates.sh
```

---

## 🚀 VPS Rehearsal / VPS 演练

On a VPS or CI environment, run all three blocking tests:

在 VPS 或 CI 环境中，运行全部三个阻止测试：

```bash
#!/bin/bash
# Complete rehearsal - should see 3 BLOCKS
# 完整演练 - 应看到 3 次阻止

echo "Test 1: Low Score"
MOCK_SCORE=84 bash scripts/rehearse_pre_push_gates.sh
echo ""

echo "Test 2: Low Coverage"
MOCK_COVERAGE=79 bash scripts/rehearse_pre_push_gates.sh
echo ""

echo "Test 3: Invalid Signatures on Main"
BRANCH=main MOCK_SIG=invalid bash scripts/rehearse_pre_push_gates.sh
```

---

## 📦 Files Structure / 文件结构

```
scripts/
├── rehearse_pre_push_gates.sh     # English rehearsal script
├── 演练_pre_push_gates.sh         # Chinese rehearsal script (equivalent)
└── REHEARSAL_GUIDE.md             # This guide

.workflow/
├── lib/
│   └── final_gate.sh              # Shared quality gate logic
└── gates.yml                      # Quality thresholds configuration
```

---

## ✅ Verification Checklist / 验证清单

Before running rehearsal / 运行演练前：

- [ ] Ensure `.workflow/lib/final_gate.sh` exists
- [ ] 确保 `.workflow/lib/final_gate.sh` 存在
- [ ] Scripts have execute permissions (`chmod +x`)
- [ ] 脚本有执行权限（`chmod +x`）
- [ ] Quality score file exists: `.workflow/_reports/quality_score.txt`
- [ ] 质量分数文件存在：`.workflow/_reports/quality_score.txt`
- [ ] Coverage file exists: `coverage/coverage.xml` or `coverage/lcov.info`
- [ ] 覆盖率文件存在：`coverage/coverage.xml` 或 `coverage/lcov.info`

---

## 🐛 Troubleshooting / 故障排除

### Issue: "final_gate.sh library not found"
### 问题："找不到 final_gate.sh 库文件"

**Solution / 解决方案**:
```bash
# Ensure library exists
ls -la .workflow/lib/final_gate.sh

# Ensure PROJECT_ROOT is correct
git rev-parse --show-toplevel
```

---

### Issue: Python3 not found error
### 问题：找不到 Python3 错误

**Solution / 解决方案**:
```bash
# Install python3
sudo apt-get install python3  # Ubuntu/Debian
brew install python3          # macOS

# Verify installation
which python3
python3 --version
```

---

### Issue: Coverage parsing returns 0
### 问题：覆盖率解析返回 0

**Solution / 解决方案**:
```bash
# Check coverage file format
cat coverage/coverage.xml | head -20
# or
cat coverage/lcov.info | head -20

# Generate coverage if missing
npm test -- --coverage
```

---

## 📚 Related Documentation / 相关文档

- `.workflow/lib/final_gate.sh` - Quality gate implementation
- `.workflow/gates.yml` - Quality thresholds configuration
- `.githooks/pre-push` - Actual pre-push hook using final_gate.sh
- `HARDENING_PLAN.md` - Overall hardening strategy

---

**Last Updated / 最后更新**: 2024-01-XX
**Version / 版本**: 1.0
