# Quality Gates Quick Reference
# 质量门禁快速参考

## 🚀 Quick Test Commands / 快速测试命令

### Test Low Score (Should BLOCK) / 测试低分（应阻止）
```bash
MOCK_SCORE=84 bash scripts/rehearse_pre_push_gates.sh
```

### Test Low Coverage (Should BLOCK) / 测试低覆盖率（应阻止）
```bash
MOCK_COVERAGE=79 bash scripts/演练_pre_push_gates.sh
```

### Test Invalid Signatures on Main (Should BLOCK) / 测试主分支无效签名（应阻止）
```bash
BRANCH=main MOCK_SIG=invalid bash scripts/rehearse_pre_push_gates.sh
```

### Test Passing Scenario / 测试通过场景
```bash
MOCK_SCORE=90 MOCK_COVERAGE=85 bash scripts/rehearse_pre_push_gates.sh
```

---

## 📊 Thresholds / 阈值

| Gate | Threshold | Override Variable |
|------|-----------|-------------------|
| Quality Score / 质量分数 | ≥ 85 | `QUALITY_MIN=XX` |
| Coverage / 覆盖率 | ≥ 80% | `COVERAGE_MIN=XX` |
| Signatures (Protected) / 签名（保护分支） | ≥ 8 | `REQUIRED_SIGS=XX` |

---

## 🎭 Mock Variables / 模拟变量

```bash
MOCK_SCORE=XX        # Override quality score (覆盖质量分数)
MOCK_COVERAGE=XX     # Override coverage % (覆盖覆盖率)
MOCK_SIG=invalid     # Simulate signature failure (模拟签名失败)
BRANCH=main          # Override branch name (覆盖分支名)
```

---

## 📁 Script Locations / 脚本位置

- **English**: `scripts/rehearse_pre_push_gates.sh`
- **中文**: `scripts/演练_pre_push_gates.sh`
- **Library**: `.workflow/lib/final_gate.sh`
- **Config**: `.workflow/gates.yml`

---

## ✅ Expected Results / 预期结果

### PASS Scenario / 通过场景
```
✅ Quality score: 90 >= 85
✅ Coverage: 85% >= 80%
✅ FINAL GATE: PASSED
```

### BLOCK Scenario / 阻止场景
```
❌ BLOCK: quality score 84 < 85 (minimum required)
❌ FINAL GATE: BLOCKED
```

---

## 🔧 One-Liner Full Test / 一键完整测试

```bash
# Run all 3 blocking tests
echo "=== Test 1: Low Score ===" && \
MOCK_SCORE=84 bash scripts/rehearse_pre_push_gates.sh; \
echo -e "\n=== Test 2: Low Coverage ===" && \
MOCK_COVERAGE=79 bash scripts/rehearse_pre_push_gates.sh; \
echo -e "\n=== Test 3: Invalid Sig on Main ===" && \
BRANCH=main MOCK_SIG=invalid bash scripts/rehearse_pre_push_gates.sh
```

---

## 📚 Full Documentation / 完整文档

See `scripts/REHEARSAL_GUIDE.md` for detailed documentation.

详见 `scripts/REHEARSAL_GUIDE.md` 获取详细文档。
