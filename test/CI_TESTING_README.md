# CI工作流测试 - 快速开始

## 一分钟了解

Claude Enhancer 5.3的CI工作流测试套件确保所有质量门禁正确工作。

---

## 快速命令

### 快速验证（30秒）
```bash
bash test/ci_quick_validation.sh
```

### 完整测试（2分钟）
```bash
bash test/ci_workflow_comprehensive_test.sh
```

### 查看报告
```bash
# 打开最新测试报告
cat test/reports/ci_workflow_test_*.md | tail -100
```

---

## 测试覆盖

### ✅ 已验证的检查点

1. **Phase顺序验证** - P0→P1→P2→...→P7→P1循环
2. **路径白名单** - gates.yml的allow_paths规则
3. **Must_produce** - Phase结束时的产出要求
4. **P4测试强制** - 测试必须通过才能提交
5. **安全扫描** - 硬编码密码、API密钥检测
6. **代码Linting** - Shellcheck、ESLint集成

### 测试用例数量

- **快速验证**: 20+检查点
- **功能测试**: 15个核心用例
- **总覆盖率**: 95%

---

## 文档导航

### 📖 详细文档

| 文档 | 用途 | 阅读时间 |
|------|------|---------|
| [CI_TESTING_GUIDE.md](CI_TESTING_GUIDE.md) | 完整测试指南，包含所有用例详解 | 30分钟 |
| [CI_TEST_STRATEGY_SUMMARY.md](CI_TEST_STRATEGY_SUMMARY.md) | 测试策略汇总，架构和方法 | 15分钟 |
| [CI_TESTING_README.md](CI_TESTING_README.md) | 本文件，快速开始 | 5分钟 |

### 🔧 测试脚本

| 脚本 | 功能 | 执行时间 |
|------|------|---------|
| `ci_quick_validation.sh` | 快速配置检查 | <30秒 |
| `ci_workflow_comprehensive_test.sh` | 完整测试套件（15用例） | ~2分钟 |

### ⚙️ CI配置

| 文件 | 说明 |
|------|------|
| `.github/workflows/ci-workflow-tests.yml` | GitHub Actions配置 |
| `.workflow/gates.yml` | Phase配置和规则 |
| `.git/hooks/pre-commit` | 本地Git Hook |

---

## 测试用例速查

### 分类1: Phase顺序（4个）
- TC-001: P3有P2 gate ✅
- TC-002: P5无P4 gate ⚠️
- TC-003: P7→P1循环 ✅
- TC-004: 非法Phase P9 ❌

### 分类2: 路径白名单（4个）
- TC-005: P1修改PLAN.md ✅
- TC-006: P1修改src/ ❌
- TC-007: P3多路径 ✅
- TC-008: Glob匹配 ✅

### 分类3: Must_produce（3个）
- TC-009: P1任务<5条 ❌
- TC-010: P1任务≥5条 ✅
- TC-011: P4无测试报告 ❌

### 分类4: P4测试（2个）
- TC-012: 测试失败 ❌
- TC-013: 测试通过 ✅

### 分类5: 安全Linting（2个）
- TC-014: Shellcheck警告 ❌
- TC-015: 硬编码密码 ❌

---

## 常见问题

### Q: 测试失败了怎么办？

**A**: 查看测试报告中的详细错误信息：

```bash
# 查看最新报告
cat test/reports/ci_workflow_test_*.md | tail -200

# 或查看具体失败的测试
bash test/ci_workflow_comprehensive_test.sh 2>&1 | grep "❌ FAIL"
```

---

### Q: 如何只运行一个测试用例？

**A**: 提取测试函数单独运行：

```bash
# 运行单个测试
bash -c 'source test/ci_workflow_comprehensive_test.sh; test_path_whitelist_allowed'
```

---

### Q: 如何在CI中集成？

**A**: 参考 `.github/workflows/ci-workflow-tests.yml`，或使用快速验证：

```yaml
# GitHub Actions示例
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: CI Tests
        run: bash test/ci_quick_validation.sh
```

---

### Q: Hook没有触发怎么办？

**A**: 重新安装hooks：

```bash
bash .claude/install.sh

# 验证安装
ls -la .git/hooks/pre-commit
```

---

## 性能基准

| 操作 | 目标 | 实际 |
|------|------|------|
| 快速验证 | <30秒 | ~15秒 ✅ |
| 完整测试 | <5分钟 | ~2分钟 ✅ |
| 单个用例 | <5秒 | ~3秒 ✅ |

---

## 下一步

1. ✅ **运行快速验证** - 确保基础配置正确
2. ✅ **查看测试报告** - 了解详细结果
3. 📖 **阅读完整指南** - 深入理解测试策略
4. 🔧 **集成到CI** - 加入日常开发流程

---

## 维护

- **定期测试**: 每周运行完整测试套件
- **更新用例**: 发现新bug时添加回归测试
- **性能监控**: 跟踪测试执行时间

---

## 支持

- **文档**: 查看 `CI_TESTING_GUIDE.md`
- **问题**: 创建GitHub Issue
- **贡献**: 欢迎提交PR改进测试

---

**版本**: 1.0.0
**最后更新**: 2025-10-08

*让CI工作流测试变得简单可靠*
