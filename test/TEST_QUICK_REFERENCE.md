# CE 命令测试快速参考

## 🚀 快速开始

### 运行所有测试
```bash
./test/run_all_tests.sh
```

### 按层级运行测试

```bash
# 单元测试（快速，< 2分钟）
bats test/unit/*.bats

# 集成测试（中速，< 5分钟）
bats test/integration/*.bats

# E2E 测试（慢速，< 10分钟）
./test/e2e/run_all_e2e_tests.sh

# BDD 验收测试
npm run bdd
```

### 运行特定模块测试

```bash
# 只测试分支管理
bats test/unit/test_branch_manager.bats

# 只测试状态管理
bats test/unit/test_state_manager.bats

# 只测试 PR 自动化
bats test/unit/test_pr_automator.bats

# 只测试质量闸门
bats test/unit/test_gate_integrator.bats
```

---

## 📊 覆盖率报告

### 生成覆盖率报告
```bash
# 安装 kcov（如果未安装）
sudo apt-get install -y kcov

# 生成覆盖率
kcov coverage/ bats test/unit/*.bats

# 查看覆盖率
cat coverage/coverage.json | jq '.percent_covered'
```

### 覆盖率目标
- 总体覆盖率：≥ 80%
- 关键模块：≥ 85%

---

## ⚡ 性能基准测试

```bash
# 运行性能基准
./test/performance/benchmark_ce_commands.sh

# 查看性能报告
cat test/performance/perf_report.json
```

### 性能目标
| 命令 | 目标 |
|------|------|
| ce start | < 3s |
| ce status | < 2s |
| ce validate | < 10s |
| ce publish | < 60s |

---

## 🧪 测试开发工作流

### 1. 编写新测试
```bash
# 创建测试文件
vim test/unit/test_new_module.bats

# 使用模板
@test "module: should do something" {
  run my_function "arg"
  [ "$status" -eq 0 ]
  [[ "$output" =~ "expected" ]]
}
```

### 2. 运行新测试
```bash
bats test/unit/test_new_module.bats
```

### 3. 调试失败测试
```bash
# 显示详细输出
bats -t test/unit/test_new_module.bats

# 运行单个测试
bats -f "should do something" test/unit/test_new_module.bats
```

---

## 🎯 CI/CD 集成

### 本地模拟 CI
```bash
# 模拟 GitHub Actions
act -j unit-tests

# 或使用 Docker
docker run --rm -v $(pwd):/workspace bats/bats:latest test/unit/*.bats
```

### 检查质量门禁
```bash
export MOCK_SCORE=90
export MOCK_COVERAGE=85
bash .workflow/lib/final_gate.sh
```

---

## 📝 测试证据

### 查看测试证据
```bash
ls -la evidence/

# 查看最新门禁检查
tail evidence/gate_t1_*.log
```

### 保存测试报告
```bash
# 生成 HTML 报告
bats --formatter junit test/unit/*.bats > test-results.xml

# 转换为 HTML
xsltproc test-results.xml > test-report.html
```

---

## 🔍 常见测试场景

### 测试分支管理
```bash
# 测试 main 分支检测
@test "detects main branch" {
  git checkout main
  run is_on_main_branch
  [ "$status" -eq 0 ]
}
```

### 测试状态隔离
```bash
# 测试多终端状态
@test "isolates terminal states" {
  write_state "t1" "branch" "feature/P0-t1-login"
  write_state "t2" "branch" "feature/P0-t2-payment"

  b1=$(read_state "t1" "branch")
  b2=$(read_state "t2" "branch")

  [ "$b1" != "$b2" ]
}
```

### 测试质量门禁
```bash
# 测试低分阻断
@test "blocks low quality score" {
  export MOCK_SCORE=75
  run ce validate
  [ "$status" -eq 1 ]
}
```

---

## 🛠️ 测试辅助工具

### 创建测试仓库
```bash
setup_test_repo() {
  temp_dir=$(mktemp -d)
  cd "$temp_dir"
  git init
  git config user.name "Test User"
  git config user.email "test@example.com"
  git commit --allow-empty -m "Initial commit"
}
```

### Mock Git 命令
```bash
mock_git_push_failure() {
  git() {
    if [[ "$1" == "push" ]]; then
      echo "fatal: Network error"
      return 1
    fi
    command git "$@"
  }
  export -f git
}
```

### 清理测试数据
```bash
teardown() {
  cd /
  rm -rf "$temp_dir"
  unset -f git
}
```

---

## 📚 参考文档

- **完整测试策略**：`docs/TEST_STRATEGY_AI_PARALLEL_DEV.md`
- **测试计划章节**：`docs/TEST_STRATEGY_FOR_PLAN.md`
- **Bats 文档**：https://github.com/bats-core/bats-core
- **BDD 指南**：https://cucumber.io/docs/bdd/

---

## 🎓 测试最佳实践

### ✅ 应该做的
- 每个测试独立运行（不依赖其他测试）
- 使用描述性的测试名称
- 每个测试只验证一件事
- 清理测试数据（使用 teardown）
- Mock 外部依赖（网络、文件系统）

### ❌ 不应该做的
- 测试之间共享状态
- 依赖特定的执行顺序
- 硬编码路径或时间戳
- 测试实现细节（只测试行为）
- 忽略失败的测试

---

## 🐛 故障排查

### 测试失败常见原因

**1. Git 配置缺失**
```bash
# 修复
git config --global user.name "Test User"
git config --global user.email "test@example.com"
```

**2. 权限问题**
```bash
# 修复
chmod +x test/unit/*.bats
chmod +x test/e2e/*.sh
```

**3. 依赖缺失**
```bash
# 安装依赖
sudo apt-get install -y bats jq
npm install -g @cucumber/cucumber
```

**4. 临时目录清理**
```bash
# 清理僵尸测试目录
rm -rf /tmp/ce-test-*
```

---

## 💡 提示和技巧

### 快速迭代开发
```bash
# 监控文件变化，自动运行测试
fswatch -o lib/*.sh | xargs -n1 -I{} bats test/unit/*.bats
```

### 只运行失败的测试
```bash
# 第一次运行，记录失败
bats test/unit/*.bats 2>&1 | tee test-output.log

# 提取失败的测试，重新运行
grep "not ok" test-output.log
```

### 并行运行测试
```bash
# 使用 GNU parallel
ls test/unit/*.bats | parallel -j4 bats {}
```

---

## 📈 测试指标追踪

### 每日测试报告
```bash
# 生成每日报告
./test/generate_daily_report.sh

# 报告内容
- 测试通过率
- 覆盖率变化
- 性能基准对比
- 新增/修复的测试
```

### 测试趋势
```bash
# 追踪覆盖率趋势
git log --all --pretty=format:"%h %ad" --date=short | \
  while read commit date; do
    git checkout $commit
    coverage=$(kcov coverage/ bats test/unit/*.bats 2>&1 | grep "percent_covered" | jq '.percent_covered')
    echo "$date,$coverage"
  done > coverage-trend.csv
```

---

*最后更新: 2025-10-09*
*维护者: Test Engineer*
