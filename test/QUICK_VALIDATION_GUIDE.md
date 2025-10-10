# 🚀 Stop-Ship Fixes 快速验证指南

## 一键运行所有测试

```bash
# 进入项目目录
cd "/home/xx/dev/Claude Enhancer 5.0"

# 运行完整验证
bash test/validate_stop_ship_fixes.sh
```

## 📋 预检查清单

在运行测试前确保：

```bash
# 1. 检查BATS是否安装
which bats || npm install -g bats

# 2. 检查Phase文件
ls -la .phase/current

# 3. 检查Hooks
ls -la .git/hooks/

# 4. 创建日志目录
mkdir -p .workflow/logs
```

## 🎯 单独测试每个修复

### P0: rm -rf 安全保护
```bash
bats test/stop_ship_01_rm_rf_safety.bats
```
**验证点**: 路径白名单、Dry-run、符号链接保护

### P1-1: commit-msg 阻断
```bash
bats test/stop_ship_02_commit_msg_block.bats
```
**验证点**: Phase文件检查、exit 1执行、错误消息

### P1-2: 覆盖率阈值
```bash
bats test/stop_ship_03_coverage_threshold.bats
```
**验证点**: 80%阈值、报告生成、回归检测

### P1-3: 并行任务互斥
```bash
bats test/stop_ship_04_parallel_mutex.bats
```
**验证点**: 锁机制、超时、死锁检测

### P1-4: 签名验证
```bash
bats test/stop_ship_05_signature_verification.bats
```
**验证点**: SHA-256、防篡改、时间戳

### P1-5: 版本一致性
```bash
bats test/stop_ship_06_version_consistency.bats
```
**验证点**: VERSION/manifest/settings同步

### P1-6: Hooks 激活
```bash
bats test/stop_ship_07_hooks_activation.bats
```
**验证点**: 日志记录、触发统计、性能监控

## 📊 查看测试报告

```bash
# 查看最新报告
ls -lt test/reports/stop_ship_fixes_*.md | head -1 | xargs cat

# 或使用浏览器打开
open test/reports/stop_ship_fixes_*.md  # macOS
xdg-open test/reports/stop_ship_fixes_*.md  # Linux
```

## ✅ 成功标志

测试通过时你会看到：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🎉 All Stop-Ship Fixes Validated Successfully!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Total Tests:   85
   ✅ Passed:      85
   ❌ Failed:      0
   ⊘  Skipped:     0

   Success Rate:  100.0%
```

## 🐛 故障排除

### 测试失败？

1. **检查错误输出**：
   ```bash
   bats test/stop_ship_XX_xxx.bats -t
   ```

2. **查看详细日志**：
   ```bash
   cat .workflow/logs/hooks.log
   ```

3. **验证环境**：
   ```bash
   # Phase文件
   cat .phase/current

   # Hooks权限
   ls -la .git/hooks/

   # 版本文件
   cat VERSION
   ```

### 常见错误

#### Error: bats: command not found
```bash
npm install -g bats
```

#### Error: .phase/current not found
```bash
mkdir -p .phase
echo "P3" > .phase/current
```

#### Error: Permission denied
```bash
chmod +x .git/hooks/*
chmod +x test/*.sh
chmod +x test/*.bats
```

## 🔄 在CI中运行

测试会自动在GitHub Actions中运行：

1. 创建PR或push代码
2. 查看Actions标签页
3. 点击"Stop-Ship Validation"工作流
4. 查看各个job的结果

### 手动触发CI
1. 进入Actions标签页
2. 选择"Stop-Ship Validation"
3. 点击"Run workflow"
4. 选择分支并运行

## 📈 测试统计

运行测试后，你会得到：

- **测试报告**: `test/reports/stop_ship_fixes_YYYYMMDD_HHMMSS.md`
- **总测试数**: 85个测试用例
- **覆盖范围**: 7个Stop-Ship修复
- **成功率**: 目标100%

## 🎓 理解输出

### BATS输出格式

```bash
✓ test name          # 通过
✗ test name          # 失败
- test name (skipped) # 跳过
```

### 颜色编码

- 🟢 绿色 = 通过
- 🔴 红色 = 失败
- 🟡 黄色 = 警告/跳过
- 🔵 蓝色 = 信息

## 🚦 下一步

测试全部通过后：

1. ✅ 提交测试报告到PR
2. ✅ 更新CHANGELOG
3. ✅ 请求代码审查
4. ✅ 合并到主分支

测试失败时：

1. 🔍 查看失败的测试
2. 🐛 修复相关问题
3. 🔄 重新运行测试
4. 📝 更新文档

## 📚 更多信息

- 详细测试报告: [STOP_SHIP_FIXES_TEST_REPORT.md](./STOP_SHIP_FIXES_TEST_REPORT.md)
- 问题清单: [../docs/CE_ISSUES_FINAL_SUMMARY.md](../docs/CE_ISSUES_FINAL_SUMMARY.md)
- CI配置: [../.github/workflows/stop-ship-validation.yml](../.github/workflows/stop-ship-validation.yml)

---

**💡 提示**: 第一次运行可能需要几分钟来安装依赖。后续运行会更快。

**🆘 需要帮助?** 查看 [STOP_SHIP_FIXES_TEST_REPORT.md](./STOP_SHIP_FIXES_TEST_REPORT.md) 中的故障排除章节。
