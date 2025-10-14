# Claude Enhancer v2.0 架构重构测试套件

**作者**: Test Engineer Professional
**版本**: v2.0
**日期**: 2025-10-14
**分支**: feature/architecture-v2.0

---

## 📋 概述

这是Claude Enhancer v2.0架构重构的完整测试套件，包含60个测试用例，覆盖6个关键测试领域：

1. **迁移正确性测试** - 验证核心文件迁移
2. **锁定机制测试** - 验证core/保护机制
3. **Feature系统测试** - 验证enable/disable功能
4. **Hook增强测试** - 验证5层检测机制
5. **兼容性测试** - 验证向后兼容性
6. **性能测试** - 验证无性能退化

---

## 🚀 快速开始

### 1. 快速验证（5分钟）

```bash
# 运行核心测试，快速验证架构迁移状态
./test/架构v2.0/quick_test.sh
```

**适用场景**：
- 开发过程中快速验证
- CI/CD pipeline的smoke test
- 验证基本功能正常

**测试内容**：
- 核心文件存在性
- Python/YAML语法
- Git hooks安装
- 软链接兼容性
- 基本导入性能

### 2. 完整测试套件（4-5小时）

```bash
# 运行所有60个测试用例
./test/架构v2.0/run_all_tests.sh
```

**适用场景**：
- 架构迁移完成后的完整验证
- 发布前的最终检查
- 周期性的回归测试

**测试内容**：
- 6个Phase的所有测试
- 性能基准测试
- 压力测试
- 集成测试

### 3. Python单元测试（30分钟）

```bash
# 运行Python unittest套件
python3 ./test/架构v2.0/test_architecture_v2.py
```

**适用场景**：
- 开发过程中的单元测试
- 特定功能的验证
- CI/CD的单元测试阶段

**测试内容**：
- Python模块的单元测试
- Feature系统测试
- 性能测试
- 集成测试

### 4. 生成测试报告

```bash
# 运行测试并生成Markdown报告
./test/架构v2.0/run_all_tests.sh --report

# 查看报告
cat test/架构v2.0/reports/test_report_*.md
```

---

## 📁 目录结构

```
test/架构v2.0/
├── README.md                        # 本文件
├── TEST_PLAN_v2.0.md               # 详细测试计划（设计文档）
│
├── run_all_tests.sh                # 主测试运行器（Bash）
├── quick_test.sh                   # 快速验证测试
├── test_architecture_v2.py         # Python单元测试
│
├── data/                           # 测试数据
│   ├── README.md
│   ├── sample_core_files/         # 测试用核心文件
│   ├── sample_features/           # 测试用Feature
│   ├── sample_configs/            # 测试用配置
│   └── integrity_hashes/          # 测试用Hash
│
├── fixtures/                       # 测试fixtures
│   ├── mock_workflow_state.json   # Mock workflow状态
│   ├── mock_git_status.txt        # Mock git状态
│   └── mock_user_inputs.txt       # Mock用户输入
│
├── expected/                       # 预期结果
│   ├── migration_results.json     # 预期迁移结果
│   ├── locking_behaviors.json     # 预期锁定行为
│   └── performance_benchmarks.json # 预期性能指标
│
├── reports/                        # 测试报告（自动生成）
│   ├── test_report_*.md           # Markdown报告
│   └── test_results_*.json        # JSON结果
│
└── scripts/                        # 辅助脚本
    └── (待添加)
```

---

## 🧪 测试用例清单

### Phase 1: 迁移正确性测试（9个用例）

| ID | 测试用例 | 优先级 | 预计耗时 |
|----|---------|--------|---------|
| 1.1.1 | 核心文件存在性检查 | P0 | 2min |
| 1.1.2 | 旧位置文件已删除 | P0 | 2min |
| 1.1.3 | 核心文件行数检查 | P0 | 2min |
| 1.2.1 | Hash完整性验证 | P0 | 3min |
| 1.2.2 | Python语法检查 | P0 | 2min |
| 1.2.3 | YAML语法检查 | P0 | 2min |
| 1.3.1 | 软链接存在性 | P1 | 2min |
| 1.3.2 | 通过软链接访问文件 | P1 | 2min |
| 1.3.3 | 软链接在Git中的状态 | P1 | 2min |

### Phase 2: 锁定机制测试（12个用例）

| ID | 测试用例 | 优先级 | 预计耗时 |
|----|---------|--------|---------|
| 2.1.1 | 直接修改core/文件被阻止 | P0 | 3min |
| 2.1.2 | 批量修改core/文件被阻止 | P0 | 3min |
| 2.1.3 | 删除core/文件被阻止 | P0 | 3min |
| 2.2.1 | Hash生成 | P0 | 2min |
| 2.2.2 | Hash验证通过 | P0 | 2min |
| 2.2.3 | Hash验证失败（篡改检测） | P0 | 3min |
| 2.3.1 | Pre-commit hook存在 | P0 | 2min |
| 2.3.2 | Hook包含core/保护逻辑 | P0 | 2min |
| 2.3.3 | Hook允许正常提交 | P0 | 3min |
| 2.4.1 | Claude PreToolUse hook存在 | P0 | 2min |
| 2.4.2 | Hook检测Write工具调用core/ | P0 | 3min |
| 2.4.3 | Hook允许修改非core/文件 | P0 | 3min |

### Phase 3: Feature系统测试（9个用例）

| ID | 测试用例 | 优先级 | 预计耗时 |
|----|---------|--------|---------|
| 3.1.1 | Feature配置文件存在 | P0 | 2min |
| 3.1.2 | 禁用Feature | P0 | 3min |
| 3.1.3 | 启用Feature | P0 | 3min |
| 3.2.1 | 禁用Feature不加载 | P0 | 3min |
| 3.2.2 | 启用Feature正常加载 | P0 | 3min |
| 3.2.3 | 加载性能测试 | P0 | 3min |
| 3.3.1 | 检测缺失依赖 | P1 | 3min |
| 3.3.2 | 检测循环依赖 | P1 | 3min |
| 3.3.3 | 依赖顺序加载 | P1 | 3min |

### Phase 4: Hook增强测试（12个用例）

| ID | 测试用例 | 优先级 | 预计耗时 |
|----|---------|--------|---------|
| 4.1.1 | 检测"继续"关键词 | P0 | 3min |
| 4.1.2 | 检测"continue"关键词 | P0 | 3min |
| 4.1.3 | 检测其他绕过词 | P0 | 5min |
| 4.1.4 | 允许正常的continue用法 | P0 | 3min |
| 4.2.1 | P1未完成不能进入P2 | P0 | 3min |
| 4.2.2 | Phase完成标记检查 | P0 | 3min |
| 4.2.3 | Phase状态回溯检测 | P0 | 3min |
| 4.3.1 | main分支禁止直接开发 | P0 | 3min |
| 4.3.2 | Feature分支主题匹配检查 | P0 | 3min |
| 4.3.3 | 建议创建新分支 | P0 | 3min |
| 4.4.1 | 全部5层都触发 | P0 | 5min |
| 4.4.2 | 正常流程所有层都通过 | P0 | 5min |

### Phase 5: 兼容性测试（9个用例）

| ID | 测试用例 | 优先级 | 预计耗时 |
|----|---------|--------|---------|
| 5.1.1 | 旧的import路径工作 | P0 | 3min |
| 5.1.2 | 旧的配置路径工作 | P0 | 3min |
| 5.1.3 | 旧的CLI命令工作 | P0 | 3min |
| 5.2.1 | P0-P7 workflow完整执行 | P0 | 5min |
| 5.2.2 | Workflow状态文件格式兼容 | P0 | 3min |
| 5.2.3 | Agent选择逻辑兼容 | P0 | 3min |
| 5.3.1 | 旧配置文件自动迁移 | P1 | 3min |
| 5.3.2 | 配置向后兼容 | P1 | 3min |
| 5.3.3 | 环境变量兼容 | P1 | 3min |

### Phase 6: 性能测试（9个用例）

| ID | 测试用例 | 优先级 | 预计耗时 |
|----|---------|--------|---------|
| 6.1.1 | 冷启动时间 | P0 | 3min |
| 6.1.2 | 热启动时间 | P0 | 3min |
| 6.1.3 | Feature加载时间 | P0 | 3min |
| 6.2.1 | Hash验证性能 | P0 | 3min |
| 6.2.2 | Pre-commit hook性能 | P0 | 3min |
| 6.2.3 | Claude hook性能 | P0 | 3min |
| 6.3.1 | 正常commit性能 | P0 | 3min |
| 6.3.2 | 大量文件commit性能 | P0 | 3min |
| 6.3.3 | Commit with/without hooks对比 | P1 | 3min |

**总计**: 60个测试用例 | 预计总耗时: 4-5小时

---

## 🎯 性能基准

### 启动性能

| 指标 | 目标 | 可接受 | 说明 |
|-----|------|--------|------|
| 冷启动 | <200ms | <300ms | 首次导入LazyOrchestrator |
| 热启动 | <100ms | <150ms | 后续导入LazyOrchestrator |
| Feature加载 | <100ms | <150ms | 加载所有enabled features |

### Hook性能

| 指标 | 目标 | 可接受 | 说明 |
|-----|------|--------|------|
| Hash验证 | <50ms | <100ms | SHA256验证（单次） |
| Pre-commit hook | <3s | <5s | 完整执行时间 |
| Claude hook | <100ms | <200ms | PreToolUse执行时间 |
| 5层检测 | <50ms | <100ms | 完整5层检测时间 |

### Commit性能

| 指标 | 目标 | 可接受 | 说明 |
|-----|------|--------|------|
| 正常commit | <3s | <5s | 单文件commit |
| 批量commit | <5s | <8s | 10个文件commit |
| Hooks开销 | <1s | <2s | 相对于无hooks |

---

## ✅ 验收标准

### 必须通过（P0）

- [ ] 所有60个测试用例通过率100%
- [ ] 4个核心文件成功迁移到core/
- [ ] 锁定机制100%阻止修改core/
- [ ] 5层检测机制全部工作
- [ ] 旧命令100%兼容
- [ ] 启动时间<200ms
- [ ] Commit时间<3s
- [ ] 无性能退化（与v1.0对比）

### 建议通过（P1）

- [ ] 测试覆盖率>90%
- [ ] 文档完整性100%
- [ ] CI集成完成

### 可选优化（P2）

- [ ] 性能提升>10%
- [ ] 测试执行时间<2小时（并行）
- [ ] 自动化回归测试

---

## 🔧 故障排除

### 常见问题

#### 1. "Core file missing"错误

**原因**: 核心文件尚未迁移到`.claude/core/`

**解决**:
```bash
# 检查核心文件位置
ls -la .claude/core/

# 如果不存在，可能需要先执行迁移
# （迁移脚本待实现）
```

#### 2. "Pre-commit hook not installed"错误

**原因**: Git hooks未安装

**解决**:
```bash
# 安装hooks
./.claude/install.sh

# 验证安装
ls -la .git/hooks/pre-commit
```

#### 3. "Hash verification failed"错误

**原因**: 核心文件被修改或Hash文件不存在

**解决**:
```bash
# 重新生成Hash
cd .claude/core
sha256sum *.py config.yaml > .integrity.sha256

# 验证Hash
sha256sum -c .integrity.sha256
```

#### 4. Python导入错误

**原因**: Python路径未正确设置

**解决**:
```bash
# 检查Python版本
python3 --version  # 需要3.9+

# 检查路径
export PYTHONPATH=".claude/core:$PYTHONPATH"
```

#### 5. 测试跳过过多

**原因**: 某些功能尚未实现（迁移进行中）

**说明**: 测试套件设计为渐进式，未实现的功能会被跳过（SKIP），这是正常的。迁移完成后，所有测试应该执行（不跳过）。

---

## 📊 测试报告

测试完成后，报告会自动生成在：

```
test/架构v2.0/reports/
├── test_report_20251014_100000.md    # Markdown格式
└── test_results_20251014_100000.json # JSON格式
```

**报告内容**：
- 测试摘要（通过/失败/跳过）
- 每个Phase的详细结果
- 性能指标
- 失败测试的详细信息
- 改进建议

---

## 🤝 贡献测试

如果你想添加新的测试用例：

1. 在`TEST_PLAN_v2.0.md`中添加测试用例设计
2. 在`run_all_tests.sh`或`test_architecture_v2.py`中实现
3. 添加测试数据到`data/`目录
4. 更新预期结果到`expected/`目录
5. 运行测试验证
6. 提交PR

---

## 📞 联系与支持

**测试工程师**: Test Engineer Professional
**分支**: feature/architecture-v2.0
**文档版本**: v1.0
**最后更新**: 2025-10-14

如有问题，请：
1. 查看`TEST_PLAN_v2.0.md`了解详细设计
2. 检查`expected/`目录的预期结果
3. 运行`quick_test.sh`快速诊断
4. 查看测试报告获取详细错误信息

---

*本测试套件遵循Test Engineer专业标准，确保架构v2.0迁移的零回归和高质量交付。*
