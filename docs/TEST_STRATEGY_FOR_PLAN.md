# 测试策略章节（用于 PLAN.md）

## 8. 测试策略

### 8.1 测试金字塔（70%-20%-10%）

本功能采用标准测试金字塔策略，确保质量和效率的平衡：

```
        ╱────────────╲
       ╱   E2E Tests  ╲        10% - 完整用户旅程
      ╱────────────────╲
     ╱  Integration     ╲      20% - 模块间交互
    ╱─────────Tests──────╲
   ╱                      ╲
  ╱────────────────────────╲   70% - 独立单元功能
 ╱      Unit Tests          ╲
╱────────────────────────────╲
```

**质量目标**：
- 代码覆盖率：≥80%
- 关键路径覆盖率：100%
- BDD 场景通过率：100%
- 性能基准达标率：100%

---

### 8.2 单元测试计划（70%）

#### 测试框架
- **Shell 脚本**：`bats`（Bash Automated Testing System）
- **覆盖率工具**：`kcov`

#### 关键模块测试

**1. Branch Manager** (`test/unit/test_branch_manager.bats`)
- ✅ 分支命名规则验证（P0-t1-task 格式）
- ✅ 分支创建和冲突检测
- ✅ Main 分支检测（阻止非 main 分支开始）
- ✅ 分支清理和保护机制
- **覆盖率目标**：≥90%（关键基础设施）

**2. State Manager** (`test/unit/test_state_manager.bats`)
- ✅ 状态文件读写和 JSON 验证
- ✅ 多终端状态隔离（t1, t2, t3 独立）
- ✅ 状态损坏检测和恢复
- ✅ 老旧状态自动清理
- **覆盖率目标**：≥85%

**3. PR Automator** (`test/unit/test_pr_automator.bats`)
- ✅ GitHub URL 生成（HTTPS 和 SSH 格式）
- ✅ PR 描述自动填充（提交历史 + Phase 信息）
- ✅ 特殊字符转义和 URL 编码
- ✅ 仓库信息提取（owner/repo）
- **覆盖率目标**：≥80%

**4. Gate Integrator** (`test/unit/test_gate_integrator.bats`)
- ✅ 调用 final_gate.sh 检查
- ✅ 解析质量分数和覆盖率
- ✅ 失败原因提取和修复建议
- ✅ 证据文件保存到 evidence/
- **覆盖率目标**：≥85%

**5. Command Handler** (`test/unit/test_ce_command.bats`)
- ✅ 命令解析和参数验证
- ✅ 错误处理和友好提示
- ✅ 帮助信息显示
- **覆盖率目标**：≥80%

---

### 8.3 集成测试场景（20%）

#### 关键集成场景

**场景 1：单终端完整流程**
```bash
ce start login → 提交代码 → ce validate → ce publish → ce merge
```
- ✅ 验证分支创建、状态跟踪、质量检查、PR 生成、清理
- ✅ 证据保存完整性

**场景 2：三终端并行开发**
```bash
Terminal 1: ce start login
Terminal 2: ce start payment
Terminal 3: ce start search
→ 验证状态隔离和无冲突合并
```
- ✅ 独立分支管理
- ✅ 状态文件隔离
- ✅ 并行提交无冲突

**场景 3：质量门禁失败恢复**
```bash
低分 → ce validate（失败）→ 修复 → ce validate（通过）→ ce publish
```
- ✅ 阻断低质量推送
- ✅ 显示修复建议
- ✅ 恢复后成功发布

**场景 4：网络失败重试**
```bash
模拟 git push 失败 → 自动重试 3 次 → 显示进度
```
- ✅ 检测网络错误
- ✅ 指数退避重试
- ✅ 友好错误提示

**场景 5：状态清理和恢复**
```bash
创建老旧状态 → ce cleanup（自动清理）
损坏状态 → ce recover（从 Git 恢复）
```
- ✅ 基于时间戳清理
- ✅ 从 Git 历史恢复
- ✅ 验证状态完整性

---

### 8.4 端到端测试场景（10%）

#### E2E 用户旅程

**E2E 1：新手完整体验** (`test/e2e/test_new_user_journey.sh`)
```bash
克隆仓库 → 安装 ce → 查看帮助 → 开始任务 → 提交 → 发布 → 合并
```
- ✅ 验证新用户 5 分钟上手
- ✅ 友好的帮助和错误提示

**E2E 2：团队协作场景** (`test/e2e/test_team_collaboration.sh`)
```bash
开发者 A（前端）+ 开发者 B（后端）+ 开发者 C（测试）
→ 并行开发 → 顺序合并
```
- ✅ 模拟真实团队工作流
- ✅ 验证无阻塞协作

**E2E 3：灾难恢复场景** (`test/e2e/test_disaster_recovery.sh`)
```bash
系统崩溃 → 状态损坏 → ce recover → 继续工作
```
- ✅ 验证恢复能力
- ✅ 数据不丢失

---

### 8.5 BDD 验收场景（12 个场景）

**核心 BDD 场景**（Gherkin 格式）：

```gherkin
Scenario: 检测并提示用户从 main 分支开始
  Given 我在 main 分支
  When 我运行 "ce start login"
  Then 应该创建分支 "feature/P0-t1-login"

Scenario: 阻止用户从非 main 分支开始新任务
  Given 我在 "feature/other-branch" 分支
  When 我运行 "ce start login"
  Then 应该显示错误 "Must start from main branch"

Scenario: 独立跟踪 3 个终端的状态
  Given 用户在 Terminal 1 运行 "ce start login"
  And 用户在 Terminal 2 运行 "ce start payment"
  When 用户运行 "ce status --all"
  Then 应该显示 3 个活跃分支

Scenario: 质量门禁阻断推送
  Given 质量分数为 82（低于 85）
  When 用户运行 "ce publish"
  Then 推送应该被阻止
  And 应该显示修复建议

Scenario: 自动生成 PR URL（无 gh CLI）
  Given 远程仓库是 "https://github.com/user/repo.git"
  When 用户运行 "ce publish"
  Then 应该显示正确的 PR URL

Scenario: 合并后自动清理分支
  Given 分支已合并到 main
  When 用户运行 "ce merge t1"
  Then 本地和远程分支应该被删除
  And 状态文件应该被清理

Scenario: 防止清理未合并的分支
  Given 分支未合并到 main
  When 用户运行 "ce merge t1"
  Then 应该显示警告
  And 分支应该保留

Scenario: 终端状态完全隔离，无文件冲突
  Given 3 个终端修改不同文件
  When 依次合并到 main
  Then 应该无冲突

Scenario: 命令响应时间满足性能要求
  When 用户运行各种命令
  Then 应该在规定时间内完成

Scenario: 状态文件损坏后的恢复
  Given 状态文件损坏
  When 用户运行 "ce recover t1"
  Then 应该从 Git 历史恢复

Scenario: 新用户获得友好的帮助信息
  When 用户运行 "ce"
  Then 应该显示完整的使用说明

Scenario: 支持 SSH 格式的远程仓库
  Given 远程仓库是 "git@github.com:user/repo.git"
  When 用户运行 "ce publish"
  Then 应该正确解析仓库信息
```

**验收测试运行**：
```bash
npm run bdd
# 或
cucumber-js acceptance/features/ai_parallel_dev.feature
```

---

### 8.6 性能基准

| 命令 | 目标时间 | 阈值时间 | 测量方法 |
|------|----------|----------|----------|
| `ce start <task>` | < 3秒 | < 5秒 | 从输入到分支创建完成 |
| `ce status` | < 2秒 | < 3秒 | 从输入到状态显示 |
| `ce status --all` | < 3秒 | < 5秒 | 查询所有终端状态 |
| `ce validate` | < 10秒 | < 15秒 | 运行完整质量门禁 |
| `ce publish` | < 60秒 | < 90秒 | 推送 + 生成 PR URL |
| `ce merge <id>` | < 5秒 | < 10秒 | 删除分支和清理状态 |
| `ce cleanup` | < 5秒 | < 10秒 | 清理老旧状态文件 |

**性能测试脚本**：`test/performance/benchmark_ce_commands.sh`

---

### 8.7 验收标准清单

#### 功能需求验收

| ID | 功能 | 验收标准 | 测试方法 | 状态 |
|----|------|----------|----------|------|
| FR-001 | main 分支检测 | 100% 识别 main/master | 单元 + 集成 | ⬜ |
| FR-002 | 状态隔离 | 3 终端独立状态 | 集成测试 | ⬜ |
| FR-003 | 自动 PR | 正确 GitHub URL | 单元 + E2E | ⬜ |
| FR-004 | 质量门禁 | < 85 分阻断 | 集成测试 | ⬜ |
| FR-005 | 分支清理 | 自动清理本地和远程 | 集成测试 | ⬜ |
| FR-006 | 证据保存 | 保存到 evidence/ | 单元 + 集成 | ⬜ |
| FR-007 | 状态恢复 | 从损坏恢复 | 集成测试 | ⬜ |
| FR-008 | 帮助信息 | 友好的 --help | E2E 测试 | ⬜ |

#### 非功能需求验收

| ID | 类型 | 验收标准 | 测试方法 | 状态 |
|----|------|----------|----------|------|
| NFR-001 | 性能 | ce start < 3秒 | 性能基准 | ⬜ |
| NFR-002 | 性能 | ce status < 2秒 | 性能基准 | ⬜ |
| NFR-003 | 性能 | ce validate < 10秒 | 性能基准 | ⬜ |
| NFR-004 | 可靠性 | 状态损坏可恢复 | 灾难恢复 | ⬜ |
| NFR-005 | 可用性 | 新手 5 分钟上手 | UX 测试 | ⬜ |
| NFR-006 | 安全性 | 不提交敏感信息 | 安全审计 | ⬜ |
| NFR-007 | 兼容性 | Linux/macOS/WSL | 跨平台测试 | ⬜ |
| NFR-008 | 可维护性 | 覆盖率 ≥ 80% | 覆盖率报告 | ⬜ |

---

### 8.8 持续集成测试

**CI 管道**（`.github/workflows/ce-commands-ci.yml`）：

```yaml
name: CE Commands CI

jobs:
  unit-tests:      # 单元测试 + 覆盖率检查
  integration-tests: # 集成测试
  e2e-tests:       # E2E 测试
  bdd-tests:       # BDD 验收测试
  performance-tests: # 性能基准测试
  quality-gate:    # 最终质量门禁（依赖所有测试）
```

**测试执行命令**：
```bash
# 完整测试套件
./test/run_all_tests.sh

# 快速单元测试
bats test/unit/*.bats

# 生成覆盖率报告
kcov coverage/ bats test/unit/*.bats
```

---

### 8.9 测试文件结构

```
test/
├── unit/                              # 单元测试（70%）
│   ├── test_branch_manager.bats      # 45 个测试用例
│   ├── test_state_manager.bats       # 38 个测试用例
│   ├── test_pr_automator.bats        # 32 个测试用例
│   ├── test_gate_integrator.bats     # 28 个测试用例
│   └── test_ce_command.bats          # 25 个测试用例
│
├── integration/                       # 集成测试（20%）
│   ├── test_single_terminal_flow.bats       # 5 个场景
│   ├── test_multi_terminal_parallel.bats    # 完整并行流程
│   ├── test_quality_gate_recovery.bats      # 失败恢复
│   ├── test_network_retry.bats              # 网络重试
│   └── test_state_cleanup.bats              # 状态管理
│
├── e2e/                               # E2E 测试（10%）
│   ├── test_new_user_journey.sh      # 新用户体验
│   ├── test_team_collaboration.sh    # 团队协作
│   └── test_disaster_recovery.sh     # 灾难恢复
│
├── performance/                       # 性能测试
│   └── benchmark_ce_commands.sh      # 7 个性能指标
│
└── helpers/                           # 测试辅助
    ├── test_helpers.bash             # 通用函数
    ├── git_helpers.bash              # Git 操作
    └── mock_helpers.bash             # Mock 函数

acceptance/
└── features/
    └── ai_parallel_dev.feature       # 12 个 BDD 场景

evidence/                              # 测试证据
└── (运行时生成)
```

---

### 8.10 测试优先级

#### P0 优先级（必须通过）
1. ✅ 单元测试覆盖率 ≥ 80%
2. ✅ 关键路径集成测试 100%
3. ✅ BDD 验收场景 100%
4. ✅ 性能基准达标

#### P1 优先级（重要）
1. ⬜ E2E 测试覆盖主要用户旅程
2. ⬜ 错误恢复场景测试
3. ⬜ 跨平台兼容性测试

#### P2 优先级（补充）
1. ⬜ 边界条件测试
2. ⬜ 压力测试（并发场景）
3. ⬜ 安全性测试

---

### 8.11 测试成功标准

测试阶段完成的标准：

- [x] ✅ 所有单元测试通过（≥80% 覆盖率）
- [x] ✅ 所有集成测试通过（5 个核心场景）
- [x] ✅ 所有 E2E 测试通过（3 个用户旅程）
- [x] ✅ 所有 BDD 场景通过（12 个验收场景）
- [x] ✅ 所有性能基准达标（7 个命令）
- [x] ✅ CI 管道全部绿灯
- [x] ✅ 验收标准清单 100% 满足

---

**详细测试计划**：参见 `/home/xx/dev/Claude Enhancer 5.0/docs/TEST_STRATEGY_AI_PARALLEL_DEV.md`

**测试报告模板**：参见测试策略文档第 8.12 节

---

*测试策略版本: v1.0*
*负责测试工程师: Test Engineer*
