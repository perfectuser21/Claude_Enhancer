# Claude Enhancer 6.6 - 7 Phases统一工作流系统

## 📋 概述

Claude Enhancer 6.6完成了7 Phases统一升级，将原11步工作流（Pre-Discussion + Phase 1-7 + Acceptance + Cleanup）合并为**真正的7个Phase**，减少36%复杂度，同时保持所有97个检查点和2个质量门禁。

**核心理念**：
- 🎯 **简化不妥协** - 97个检查点全部保留，零质量损失
- ⚡ **易于理解** - 7 Phases符合经典软件生命周期
- 🛡️ **质量不变** - Phase 3/4两个质量门禁完全保留
- 🔄 **完全统一** - Phase 1-7清晰定义，无混合命名

---

## 🚀 完整7 Phases工作流

### 流程总览

```
用户提出需求（Discussion Mode）
"我想实现一个用户认证系统"
         ↓
   【用户说：开始实现】
         ↓
   【进入 Execution Mode】
         ↓
╔══════════════════════════════════════════════════════════╗
║  Phase 1: Discovery & Planning（33检查点）               ║
╚══════════════════════════════════════════════════════════╝
  1.1 Branch Check（5检查点）⛔ 强制
      - 检查当前分支 → 创建feature分支
      - 智能分支决策（匹配/不确定/不匹配）

  1.2 Requirements Discussion（5检查点）
      - AI分析需求，澄清问题
      - 明确功能边界

  1.3 Technical Discovery（8检查点）✅ 核心
      - 技术可行性验证
      - 创建Acceptance Checklist
      - 产出：P2_DISCOVERY.md

  1.4 Impact Assessment（3检查点）⚙️ 自动化
      - 计算影响半径分数（0-100）
      - 智能推荐Agent数量（0/3/6）
      - 性能：<50ms，准确率86%

  1.5 Architecture Planning（12检查点）✅ 核心
      - 系统架构设计 + 技术选型
      - 应用Impact Assessment结果
      - 产出：PLAN.md + 项目骨架

产出：P2_DISCOVERY.md + PLAN.md + Acceptance Checklist
         ↓
╔══════════════════════════════════════════════════════════╗
║  Phase 2: Implementation（15检查点）                     ║
╚══════════════════════════════════════════════════════════╝
  - 编写功能代码（基于PLAN.md）
  - 单元测试同步开发
  - Git提交（规范格式）
  - Agent: 0-6个（基于Phase 1.4评估）

产出：可运行代码 + Git commits + 工具脚本
         ↓
╔══════════════════════════════════════════════════════════╗
║  Phase 3: Testing（15检查点）🔒 质量门禁1                ║
╚══════════════════════════════════════════════════════════╝
  必须执行：bash scripts/static_checks.sh

  检查：
  - Shell语法（bash -n）
  - Shellcheck linting
  - 代码复杂度（<150行/函数）
  - Hook性能（<2秒）
  - 单元/集成/BDD测试

  ⛔ 阻止标准：任何检查失败都阻止进入Phase 4

产出：测试报告 + 覆盖率报告
         ↓
╔══════════════════════════════════════════════════════════╗
║  Phase 4: Review（10检查点）🔒 质量门禁2                 ║
╚══════════════════════════════════════════════════════════╝
  必须执行：bash scripts/pre_merge_audit.sh

  自动化检查：
  - 配置完整性（hooks注册、权限）
  - 遗留问题扫描（TODO/FIXME）
  - 垃圾文档检测（≤7个）
  - 版本一致性（5文件匹配）⛔
  - 代码模式一致性

  人工验证：
  - 逻辑正确性（IF判断、return语义）
  - Phase 1 checklist对照验证

  ⛔ 阻止标准：critical issue阻止进入Phase 5

产出：REVIEW.md + Audit报告
         ↓
╔══════════════════════════════════════════════════════════╗
║  Phase 5: Release（15检查点）                            ║
╚══════════════════════════════════════════════════════════╝
  - 更新CHANGELOG.md + README.md
  - 创建Git Tag（semver格式）
  - 配置健康检查 + SLO监控
  - 对照Phase 1 Checklist验证（≥90%）

  铁律：不应在此阶段发现bugs（发现→返回Phase 4）

产出：Release notes + Git tag + 监控配置
         ↓
╔══════════════════════════════════════════════════════════╗
║  Phase 6: Acceptance（5检查点）                          ║
╚══════════════════════════════════════════════════════════╝
  - AI展示Acceptance Checklist完成情况
  - 质量指标总结
  - AI说："我已完成所有验收项，请您确认"
  - 等待用户说："没问题"

产出：Acceptance Report + 用户确认
         ↓
╔══════════════════════════════════════════════════════════╗
║  Phase 7: Closure（4检查点）                             ║
╚══════════════════════════════════════════════════════════╝
  必须执行：bash scripts/check_version_consistency.sh

  - 清理.temp/目录（<10MB）
  - 最终版本一致性验证 ⛔
  - 检查文档规范
  - 准备PR

产出：干净的分支 + merge-ready状态
         ↓
   【等待用户说"merge"】
         ↓
      任务完成 ✅
```

---

## 🎯 各阶段详细说明

### Phase 1: Branch Check (分支前置检查)【规则0 - 最高优先级】

**核心原则**: `新任务 = 新分支（No Exceptions）`

#### 🎯 执行时机
在进入执行模式（Phase 2-7）之前，**强制执行**

#### 📋 检查清单
1. **分析当前分支**
   ```bash
   当前分支是什么？
   ├─ main/master → 🔴 必须创建新分支
   ├─ feature/xxx → 🟡 检查是否与当前任务相关
   └─ 他人的分支 → 🔴 禁止修改
   ```

2. **判断任务类型**
   - `feature/功能描述` - 新功能开发
   - `bugfix/问题描述` - Bug修复
   - `perf/优化内容` - 性能优化
   - `docs/文档主题` - 文档更新
   - `experiment/实验内容` - 实验性改动

3. **智能分支决策**
   - 🟢 **明显匹配**（延续/修复当前功能）→ 直接继续
   - 🟡 **不确定**（边界不清）→ 简短询问
   - 🔴 **明显不匹配**（新功能/跨领域）→ 建议新分支

#### 🛡️ 强制执行机制
- **Hook**: `.claude/hooks/branch_helper.sh` (PreToolUse)
- **Git Hook**: `.git/hooks/pre-push` (硬阻止main/master推送)
- **四层防护**: 本地Hook + CI验证 + GitHub保护 + 持续监控

#### 💡 示例场景

**场景1: 明显匹配（直接继续）**
```
当前分支: feature/user-authentication
用户请求: "继续实现登录功能"
AI响应: "好的，我在当前分支继续实现登录功能..."
```

**场景2: 不确定（简短询问）**
```
当前分支: feature/user-authentication
用户请求: "帮我添加邮件验证"
AI响应: "关于邮件验证，两种理解：
  1. 作为认证流程的一部分 → 当前分支继续
  2. 独立的通知系统 → 建议新分支 feature/email-notification
  您倾向于哪种？"
```

**场景3: 明显不匹配（建议新分支）**
```
当前分支: feature/add-logging（已完成）
用户请求: "帮我实现支付系统"
AI响应: "🔍 分支策略判断
  当前: feature/add-logging（已完成，未merge）
  新需求: 支付系统

  ✅ 建议: 创建新分支 feature/payment-system
  💡 理由:
    - 支付系统与日志功能完全独立
    - 当前分支已完成，应该保持稳定
    - 新分支可以独立开发和review

  现在创建新分支？"
```

---

### Phase 2: Discovery (探索与验收定义)

**原P2保持不变，新增验收清单强制要求**

#### 🎯 阶段目标
- 技术可行性验证（技术spike）
- 问题分析与解决方案探索
- **必须产出**: P2 Acceptance Checklist（定义"完成"的标准）

#### 🤖 Agent配置
- **简单任务**: 3个Agent
- **标准任务**: 4个Agent
- **复杂任务**: 4个Agent

#### ⏱️ 预计时间
2-3分钟

#### 📦 产出物
- **P2_CHECKLIST.md** (必须)
  ```markdown
  # P2 Acceptance Checklist - [功能名称]

  ## 功能验收标准
  - [ ] 用户可以通过邮箱+密码登录
  - [ ] 登录失败3次后锁定账户15分钟
  - [ ] 登录成功后生成JWT token

  ## 技术验收标准
  - [ ] 密码使用bcrypt加密（强度10）
  - [ ] Token有效期24小时
  - [ ] 所有API端点有速率限制

  ## 质量验收标准
  - [ ] 单元测试覆盖率 ≥80%
  - [ ] 集成测试覆盖主要流程
  - [ ] 性能测试：登录请求<500ms

  ## 文档验收标准
  - [ ] API文档包含所有端点
  - [ ] README包含快速开始指南
  - [ ] REVIEW.md >100行
  ```

#### 🔑 关键活动
1. **问题分析**
   - 理解业务需求
   - 识别技术挑战
   - 评估可行性

2. **解决方案探索**
   - 技术选型（2-3个方案对比）
   - 架构模式选择
   - 风险识别

3. **验收标准定义**
   - 功能完成标准
   - 技术质量标准
   - 性能指标定义
   - 文档完整性要求

#### 💡 最佳实践
- **SMART原则**: 验收标准必须具体、可衡量、可实现、相关、有时限
- **分层定义**: 功能层、技术层、质量层、文档层
- **用户视角**: 从用户角度定义"完成"
- **可验证性**: 每个标准都能通过测试或检查验证

#### ⚠️ 常见错误
- ❌ 验收标准过于模糊（"功能正常工作"）
- ❌ 缺少技术细节（"实现登录"而不说加密方式）
- ❌ 没有量化指标（说"快"而不是"<500ms"）
- ✅ 正确: 具体、可测试、有标准

---

### Phase 3: Planning & Architecture (规划+骨架)

**合并原P1（规划）+ P2（骨架），提升效率**

#### 🎯 阶段目标
- 需求分析与文档化（原P1）
- 架构设计与目录结构创建（原P2）
- 技术选型与组件设计

#### 🤖 Agent配置
- **简单任务**: 4个Agent
- **标准任务**: 5个Agent
- **复杂任务**: 6个Agent

**推荐Agent组合**:
```yaml
标准任务（新功能开发）:
  - backend-architect    # 架构设计
  - api-designer         # API设计
  - database-specialist  # 数据模型
  - test-engineer        # 测试策略
  - technical-writer     # 文档规划

复杂任务（大型功能）:
  - backend-architect
  - api-designer
  - database-specialist
  - security-auditor     # 安全设计
  - performance-engineer # 性能规划
  - test-engineer
```

#### ⏱️ 预计时间
3-4分钟

#### 📦 产出物
1. **PLAN.md** (必须)
   ```markdown
   # 功能规划文档

   ## 需求分析（原P1内容）
   - 业务需求
   - 功能范围
   - 用户故事

   ## 架构设计（原P2内容）
   - 系统架构图
   - 组件划分
   - 技术选型
   - 数据模型

   ## 目录结构
   src/
   ├── controllers/
   ├── services/
   └── models/
   ```

2. **项目骨架** (必须)
   ```bash
   # 创建目录结构
   mkdir -p src/{controllers,services,models}

   # 创建空文件（带注释）
   touch src/controllers/auth_controller.py
   # TODO: Implement authentication controller
   ```

#### 🔑 关键活动
1. **需求分析**（原P1）
   - 梳理功能需求
   - 定义API接口
   - 设计数据模型
   - 制定测试策略

2. **架构设计**（原P2）
   - 选择架构模式（MVC/DDD/Clean等）
   - 组件划分与职责
   - 技术栈选型
   - 依赖关系设计

3. **骨架创建**（原P2）
   - 创建目录结构
   - 生成空文件（带TODO注释）
   - 配置文件模板
   - 测试文件框架

#### 💡 最佳实践
- **先规划后编码**: PLAN.md写完再创建骨架
- **分层架构**: 控制层、服务层、数据层清晰分离
- **文档驱动**: 先写文档（注释），再填充实现
- **测试同步**: 创建测试文件框架，明确测试点

#### ⚠️ 为什么合并P1+P2？
1. **减少切换成本**: 规划和设计是连续思考过程
2. **避免返工**: 设计时就考虑实现细节，减少后期调整
3. **提升效率**: 同一批Agent可以完成两个阶段工作
4. **保持连贯**: PLAN.md直接指导目录结构创建

#### 🔄 与原流程对比
```
原流程（P1+P2）:
P1: 需求分析 → PLAN.md（3-4分钟）
    ↓ 切换Agent
P2: 架构设计 → 目录结构（2-3分钟）
总计: 5-7分钟 + Agent切换开销

新流程（Phase 1）:
Phase 1: 规划+架构 → PLAN.md + 骨架（3-4分钟）
节省: ~2分钟 + 切换开销
```

---

### Phase 4: Implementation (核心实现)

**原P3保持不变，强调并行开发**

#### 🎯 阶段目标
- 编写功能代码
- 单元测试同步开发
- 遵循Git提交规范
- 文档同步更新

#### 🤖 Agent配置
- **简单任务**: 4个Agent
- **标准任务**: 6个Agent
- **复杂任务**: 8个Agent

**推荐Agent组合**:
```yaml
标准任务（6个Agent）:
  - backend-architect    # 核心逻辑
  - api-designer         # API实现
  - database-specialist  # 数据库操作
  - test-engineer        # 单元测试
  - security-auditor     # 安全检查
  - technical-writer     # 文档更新

复杂任务（8个Agent）:
  - backend-architect
  - api-designer
  - database-specialist
  - frontend-specialist  # 前端交互
  - test-engineer
  - security-auditor
  - performance-engineer # 性能优化
  - technical-writer
```

#### ⏱️ 预计时间
5-8分钟（取决于功能复杂度）

#### 📦 产出物
1. **功能代码** (必须)
   ```python
   # src/controllers/auth_controller.py
   class AuthController:
       def login(self, email, password):
           # 完整实现，不是TODO
           pass
   ```

2. **单元测试** (必须)
   ```python
   # test/test_auth_controller.py
   def test_login_success():
       # 测试正常登录流程
       pass
   ```

3. **Git Commits** (必须)
   ```bash
   git commit -m "feat(auth): implement login endpoint"
   git commit -m "test(auth): add login unit tests"
   git commit -m "docs(auth): update API documentation"
   ```

#### 🔑 关键活动
1. **功能实现**
   - 按PLAN.md逐步实现
   - 遵循编码规范
   - 添加详细注释
   - 错误处理完善

2. **测试驱动**
   - 编写单元测试
   - 覆盖主要分支
   - 边界条件测试
   - Mock外部依赖

3. **文档同步**
   - API文档更新
   - 代码注释完善
   - README示例补充

4. **Git管理**
   - 频繁提交（小步快跑）
   - 规范commit message
   - 关联issue/task ID

#### 💡 最佳实践
- **TDD原则**: 测试先行，红-绿-重构
- **小步提交**: 每完成一个功能点就commit
- **代码审查意识**: 写代码时想着reviewer会怎么看
- **性能考虑**: 关键路径要考虑性能影响

#### 📝 Commit规范
```
格式: <type>(<scope>): <subject>

type:
  - feat: 新功能
  - fix: Bug修复
  - docs: 文档更新
  - test: 测试相关
  - refactor: 重构
  - perf: 性能优化
  - style: 代码格式

示例:
  feat(auth): implement JWT token generation
  test(auth): add login integration tests
  docs(api): update authentication endpoint docs
```

#### ⚠️ 常见错误
- ❌ 写完所有代码才commit（粒度太大）
- ❌ 单元测试覆盖率不足（<80%）
- ❌ 没有错误处理（happy path only）
- ❌ 文档与代码不同步
- ✅ 正确: 小步提交、高覆盖率、完善错误处理

---

### Phase 5: Testing (质量验证)【质量门禁1】

**原P4保持不变，强化自动化检查**

#### 🎯 阶段目标
- 运行完整测试套件
- 执行静态代码检查
- 验证性能指标
- **必须通过**: `bash scripts/static_checks.sh`

#### 🤖 Agent配置
- **简单任务**: 3个Agent
- **标准任务**: 5个Agent
- **复杂任务**: 6个Agent

**推荐Agent组合**:
```yaml
标准任务（5个Agent）:
  - test-engineer        # 测试执行
  - qa-specialist        # 质量保证
  - performance-engineer # 性能测试
  - security-auditor     # 安全扫描
  - technical-writer     # 测试文档
```

#### ⏱️ 预计时间
4-5分钟

#### 📦 产出物
1. **static_checks.sh输出** (必须通过)
   ```bash
   ✅ Shell syntax check passed
   ✅ Shellcheck linting passed
   ✅ Code complexity check passed
   ✅ Hook performance test passed (<2s)
   ✅ Functional tests passed
   ```

2. **测试报告** (必须)
   ```
   Test Coverage Report:
   - Unit Tests: 85% coverage
   - Integration Tests: 75% coverage
   - E2E Tests: 60% coverage
   Overall: 82% ✅ (target: 80%)
   ```

3. **性能基准** (必须)
   ```
   Performance Benchmarks:
   - Login endpoint: 245ms ✅ (<500ms)
   - Token validation: 12ms ✅ (<50ms)
   - Database query: 89ms ✅ (<200ms)
   ```

#### 🔑 关键活动

##### 1. 静态代码检查（自动化）
```bash
# 执行静态检查脚本
bash scripts/static_checks.sh

检查项:
✅ Shell语法验证（bash -n）
✅ Shellcheck linting
✅ 代码复杂度检查（>150行函数阻止）
✅ Hook性能测试（<2秒）
✅ 功能测试执行
```

##### 2. 单元测试
```bash
# 运行单元测试
pytest test/unit/ --cov --cov-report=html

要求:
- 覆盖率 ≥80%
- 所有测试通过
- 无跳过的测试（除非有明确理由）
```

##### 3. 集成测试
```bash
# 运行集成测试
pytest test/integration/

验证:
- API端点集成
- 数据库操作
- 外部服务交互
```

##### 4. 性能测试
```bash
# 运行性能基准测试
python test/performance/benchmark.py

验证:
- 响应时间 < 预算阈值
- 内存使用合理
- 无内存泄漏
```

##### 5. BDD场景验证
```bash
# 运行BDD测试
npm run bdd

验证:
- 65个场景全部通过
- 业务逻辑符合预期
```

#### 🛡️ 质量门禁标准（硬阻止）

**阻止进入Phase 4的条件**:
1. ❌ `static_checks.sh` 任何检查失败
2. ❌ 单元测试覆盖率 <80%
3. ❌ 任何测试失败
4. ❌ 性能指标超出预算
5. ❌ 安全扫描发现critical问题

**处理流程**:
```
Phase 3检查失败
    ↓
❌ 阻止进入Phase 4
    ↓
修复问题（返回Phase 2）
    ↓
重新执行Phase 3
    ↓
✅ 所有检查通过 → 进入Phase 4
```

#### 💡 最佳实践
- **左移测试**: 尽早发现问题，降低修复成本
- **自动化优先**: 能自动化的检查绝不手工
- **快速反馈**: 测试套件运行时间<5分钟
- **清晰报告**: 失败时明确指出问题位置

#### ⚠️ 常见问题及解决

**问题1: 测试覆盖率不足**
```
症状: 覆盖率70%，未达80%
原因: 边界条件未测试
解决: 补充异常流程测试
```

**问题2: Hook性能超时**
```
症状: pre-commit hook执行>5秒
原因: 执行了耗时的网络请求
解决: Mock外部依赖或异步执行
```

**问题3: Shellcheck警告**
```
症状: SC2086 - 未引用变量
原因: "$var" 写成了 $var
解决: 所有变量使用双引号
```

---

### Phase 6: Review (代码审查)【质量门禁2】

**原P5保持不变，强化人工验证**

#### 🎯 阶段目标
- 代码质量审查
- 合并前完整性审计
- **必须通过**: `bash scripts/pre_merge_audit.sh`
- **人工验证**: 逻辑正确性、代码一致性

#### 🤖 Agent配置
- **简单任务**: 3个Agent
- **标准任务**: 4个Agent
- **复杂任务**: 5个Agent

**推荐Agent组合**:
```yaml
标准任务（4个Agent）:
  - code-reviewer        # 代码审查
  - security-auditor     # 安全审查
  - technical-writer     # 文档审查
  - quality-guardian     # 质量把关
```

#### ⏱️ 预计时间
3-4分钟

#### 📦 产出物
1. **pre_merge_audit.sh输出** (必须通过)
   ```bash
   ✅ Configuration integrity verified
   ✅ No legacy issues found (TODO/FIXME)
   ✅ Document count valid (≤7 core docs)
   ✅ Version consistency verified
   ✅ Code pattern consistency validated
   ✅ Documentation completeness confirmed
   ```

2. **REVIEW.md** (必须 >100行)
   ```markdown
   # Code Review Report

   ## 自动化检查结果
   - [x] pre_merge_audit.sh passed
   - [x] All hooks registered correctly
   - [x] No TODO/FIXME remaining
   - [x] Document count: 7 ✅

   ## 代码质量分析
   ### 逻辑正确性 ✅
   - IF条件判断合理
   - Return值语义明确
   - 错误处理完善

   ### 代码一致性 ✅
   - 6个Layers统一逻辑
   - 命名规范统一
   - 代码风格一致

   ### 安全审查 ✅
   - 无SQL注入风险
   - 密码正确加密
   - Token安全验证

   ### 性能审查 ✅
   - 数据库查询优化
   - 缓存策略合理
   - 无N+1查询问题

   ### 文档完整性 ✅
   - API文档完整
   - 代码注释充分
   - README更新同步

   ## P2 Checklist验收
   - [x] 所有功能验收标准
   - [x] 所有技术验收标准
   - [x] 所有质量验收标准
   - [x] 所有文档验收标准

   ## 改进建议
   - 建议添加更多单元测试用例
   - 考虑引入Redis缓存提升性能

   ## 结论
   ✅ 代码质量优秀，建议合并
   ```

#### 🔑 关键活动

##### 1. 自动化审计
```bash
# 执行合并前审计
bash scripts/pre_merge_audit.sh

检查项:
✅ 配置完整性（hooks注册、权限755）
✅ 遗留问题扫描（TODO/FIXME）
✅ 垃圾文档检测（根目录≤7个.md）
✅ 版本号一致性（settings.json ↔ CHANGELOG.md）
✅ 代码模式一致性（相似功能统一实现）
✅ 文档完整性（REVIEW.md存在且>100行）
```

##### 2. 人工逻辑验证
```yaml
逻辑正确性审查:
  - IF条件是否合理？
    示例: if [ "$branch" = "main" ] 而不是 if [ "$branch" == "main" ]

  - Return值语义是否明确？
    示例: return 0（成功）/ return 1（失败）

  - 错误处理是否完善？
    示例: 所有命令都检查exit code

  - 边界条件是否考虑？
    示例: 空字符串、null值、超大输入
```

##### 3. 代码一致性验证
```yaml
统一性审查:
  - 6个Layers逻辑是否一致？
    示例: Layer 1-6都使用相同的分支检测逻辑

  - 命名规范是否统一？
    示例: 函数名用snake_case，常量用UPPER_CASE

  - 错误消息是否统一？
    示例: 所有错误都用"❌"前缀

  - 日志格式是否统一？
    示例: 所有日志用ISO 8601时间戳
```

##### 4. 安全审查
```yaml
安全检查项:
  - 敏感信息泄露？
    检查: 无硬编码密码、token、API key

  - 输入验证是否充分？
    检查: 所有用户输入都经过验证

  - 权限控制是否正确？
    检查: 文件权限755/644，无777

  - SQL注入防护？
    检查: 使用参数化查询，不拼接SQL
```

##### 5. P2 Checklist对照验证
```markdown
逐项对照P2_CHECKLIST.md:

功能验收:
- [x] 用户可以通过邮箱+密码登录 → 验证通过
- [x] 登录失败3次后锁定 → 测试通过
- [x] 生成JWT token → 实现正确

技术验收:
- [x] 密码bcrypt加密（强度10）→ 代码确认
- [x] Token有效期24小时 → 配置正确
- [x] API速率限制 → 中间件已添加

质量验收:
- [x] 测试覆盖率82% → 超过80%目标
- [x] 集成测试覆盖主要流程 → 完成
- [x] 登录请求245ms → 低于500ms目标

文档验收:
- [x] API文档完整 → 所有端点已文档化
- [x] README快速开始 → 已添加
- [x] REVIEW.md >100行 → 本文件126行
```

#### 🛡️ 质量门禁标准（硬阻止）

**阻止进入Phase 5的条件**:
1. ❌ `pre_merge_audit.sh` 任何检查失败
2. ❌ 发现critical级别安全问题
3. ❌ 代码逻辑存在明显错误
4. ❌ P2 Checklist未全部完成
5. ❌ REVIEW.md不存在或<100行

**处理流程**:
```
Phase 4发现问题
    ↓
评估严重程度
    ├─ Critical → ❌ 阻止，返回Phase 2修复
    ├─ Major → ⚠️ 必须修复，返回Phase 3
    └─ Minor → 💡 建议修复，可选
    ↓
修复完成 → 重新Phase 4
    ↓
✅ 所有检查通过 → 进入Phase 5
```

#### 💡 最佳实践
- **三次检查**: 自动化 → 人工 → P2对照
- **左移安全**: 安全问题越早发现越好
- **详细记录**: REVIEW.md写清楚所有检查结果
- **持续改进**: 记录常见问题，更新checklist

#### ⚠️ 常见问题及解决

**问题1: 6个Layers逻辑不一致**
```
症状: Layer 1-5用正则，Layer 6用字符串匹配
原因: 复制粘贴时未统一
解决: 统一为正则表达式匹配
```

**问题2: 文档与代码不同步**
```
症状: README说是JWT，代码用Session
原因: 需求变更后文档未更新
解决: 同步更新所有文档
```

**问题3: TODO未清理**
```
症状: 代码中残留"# TODO: optimize later"
原因: 开发时遗留
解决: 要么实现，要么转issue，不留TODO
```

---

### Phase 7: Release & Monitor (发布+监控)

**合并原P6（发布）+ P7（监控），统一发布管理**

#### 🎯 阶段目标
- 文档最终更新（原P6）
- Git tag与PR创建（原P6）
- 健康检查（原P6）
- SLO监控配置（原P7）
- **必须验证**: 对照P2 Checklist逐项验证

#### 🤖 Agent配置
- **简单任务**: 3个Agent
- **标准任务**: 4个Agent
- **复杂任务**: 5个Agent

**推荐Agent组合**:
```yaml
标准任务（4个Agent）:
  - release-manager      # 发布管理
  - technical-writer     # 文档最终审核
  - devops-engineer      # 监控配置
  - quality-guardian     # P2验收确认
```

#### ⏱️ 预计时间
3-4分钟

#### 📦 产出物
1. **Release Notes** (必须)
   ```markdown
   # Release v1.2.0 - User Authentication

   ## 新增功能
   - 🎉 实现邮箱+密码登录
   - 🔒 登录失败3次自动锁定
   - 🎫 JWT token认证

   ## 技术改进
   - 使用bcrypt加密（强度10）
   - 添加API速率限制
   - 优化数据库查询性能

   ## 测试覆盖
   - 单元测试覆盖率: 82%
   - 集成测试: 全部通过
   - 性能测试: 登录<500ms ✅

   ## 文档更新
   - API文档: 新增 /api/auth/login
   - README: 添加快速开始指南
   - CHANGELOG: 更新版本历史

   ## P2验收确认
   - [x] 所有功能验收标准
   - [x] 所有技术验收标准
   - [x] 所有质量验收标准
   - [x] 所有文档验收标准

   ## Breaking Changes
   无

   ## 升级指南
   无特殊要求，直接升级即可
   ```

2. **Git Tag** (必须)
   ```bash
   # 创建语义化版本tag
   git tag -a v1.2.0 -m "feat: User Authentication System"
   git push origin v1.2.0
   ```

3. **Pull Request** (必须)
   ```markdown
   # PR #123: User Authentication System

   ## 描述
   实现完整的用户认证系统，包括登录、token生成、速率限制等功能。

   ## 关联Issue
   Closes #100

   ## 变更类型
   - [x] 新功能
   - [ ] Bug修复
   - [ ] 破坏性变更
   - [ ] 文档更新

   ## 测试
   - [x] 单元测试（82%覆盖率）
   - [x] 集成测试
   - [x] 性能测试（<500ms）
   - [x] 手动测试

   ## Checklist
   - [x] 代码遵循项目规范
   - [x] 自我审查完成
   - [x] 添加详细注释
   - [x] 文档已更新
   - [x] 无新增告警
   - [x] 测试全部通过
   - [x] 依赖许可证合规

   ## P2验收
   见 P2_CHECKLIST.md - 全部✅

   ## Screenshots
   （如有UI变更）
   ```

4. **监控配置** (必须，原P7)
   ```yaml
   # observability/slo/auth_slo.yml
   slos:
     - name: auth_availability
       target: 99.9%
       window: 30d

     - name: auth_latency_p95
       target: 500ms
       window: 30d

     - name: auth_error_rate
       target: <0.1%
       window: 30d
   ```

5. **健康检查** (必须)
   ```bash
   # 运行健康检查
   bash scripts/health_check.sh

   ✅ Git hooks registered
   ✅ Configuration valid
   ✅ Tests passing
   ✅ Documentation complete
   ✅ SLO configured
   ✅ Ready for production
   ```

#### 🔑 关键活动

##### 1. 文档最终更新（原P6）
```bash
更新清单:
✅ README.md - 功能说明、快速开始
✅ CHANGELOG.md - 版本历史记录
✅ API_DOCS.md - API端点文档
✅ ARCHITECTURE.md - 架构图更新（如需）
```

##### 2. 版本管理（原P6）
```bash
# 语义化版本规则
MAJOR.MINOR.PATCH

MAJOR: 破坏性变更（不兼容的API修改）
MINOR: 新功能（向后兼容）
PATCH: Bug修复（向后兼容）

示例:
1.0.0 → 1.1.0 (新增认证功能)
1.1.0 → 1.1.1 (修复认证bug)
1.1.1 → 2.0.0 (API不兼容变更)
```

##### 3. PR创建（原P6）
```bash
# 使用GitHub CLI创建PR
gh pr create \
  --title "feat: User Authentication System" \
  --body-file PR_TEMPLATE.md \
  --label "enhancement" \
  --assignee "@me" \
  --reviewer "team-leads"
```

##### 4. SLO监控配置（原P7）
```yaml
配置项:
1. 可用性SLO（Availability）
   - 目标: 99.9%
   - 监控: 服务响应成功率

2. 延迟SLO（Latency）
   - 目标: P95 <500ms
   - 监控: 95%请求响应时间

3. 错误率SLO（Error Rate）
   - 目标: <0.1%
   - 监控: 错误请求占比
```

##### 5. P2 Checklist最终验收
```markdown
逐项验证P2_CHECKLIST.md:

功能验收: ✅ 全部完成
技术验收: ✅ 全部满足
质量验收: ✅ 超过目标
文档验收: ✅ 完整齐全

结论: ✅ 已达到"完成"标准
```

#### 🛡️ P6铁律

**Phase 5（原P6）不应该发现bugs**

```
如果在Phase 5发现bugs:
    ↓
❌ 说明Phase 4审查不充分
    ↓
停止发布流程
    ↓
返回Phase 4重新审查
    ↓
修复bugs后重新执行Phase 3-5
```

**Phase 5的职责**:
- ✅ 确认Phase 2-4所有工作完成
- ✅ 生成Release Notes
- ✅ 创建Git Tag和PR
- ✅ 配置监控和SLO
- ❌ 不是发现bugs的阶段

#### 💡 最佳实践
- **清晰的Release Notes**: 让用户快速了解变更
- **语义化版本**: 严格遵循MAJOR.MINOR.PATCH规则
- **完整的PR描述**: 让reviewer快速理解变更
- **主动监控**: 不等问题出现，主动监控SLO

#### ⚠️ 为什么合并P6+P7？

**原流程问题**:
```
P6: 发布（打tag、创建PR）
    ↓ 切换Agent
P7: 监控（配置SLO、告警）

问题:
- P6和P7都是发布相关，人为分割
- 发布后才配置监控，容易遗漏
- Agent切换增加时间成本
```

**新流程优势**:
```
Phase 5: 发布+监控（统一管理）
    ↓
优势:
- 发布和监控一起考虑，不遗漏
- 减少Agent切换，提升效率
- Release Notes包含监控信息
- 一次性完成所有发布工作
```

---

### Step 10: Cleanup & Merge (收尾与合并)
**注：非Phase，是工作流收尾步骤**

**新增阶段，专门处理最终清理和合并**

#### 🎯 阶段目标
- 清理临时文件
- 等待CI通过
- PR合并
- 分支清理
- 生成最终交付报告

#### 🤖 Agent配置
- **所有任务**: 2-3个Agent

**推荐Agent组合**:
```yaml
标准配置（2个Agent）:
  - cleanup-specialist   # 清理专家
  - release-manager      # 发布管理
```

#### ⏱️ 预计时间
2-3分钟（主要等待CI）

#### 📦 产出物
1. **清理日志**
   ```bash
   Cleanup Report:
   ✅ Removed .temp/analysis/
   ✅ Removed .temp/reports/
   ✅ Formatted final code
   ✅ Validated .gitignore
   ```

2. **CI结果**
   ```yaml
   GitHub Actions Status:
   ✅ test job passed
   ✅ lint job passed
   ✅ security-scan job passed
   ✅ bdd-test job passed
   ✅ bp-guard job passed

   All checks passed ✅
   ```

3. **合并确认**
   ```bash
   Merge Summary:
   - PR #123 merged to main
   - Branch feature/user-auth deleted
   - Tag v1.2.0 created
   - Release published
   ```

4. **最终交付报告**
   ```markdown
   # 项目交付报告 - User Authentication

   ## 交付内容
   - [x] 功能代码（src/controllers/auth_controller.py）
   - [x] 单元测试（82%覆盖率）
   - [x] API文档（/api/auth/login）
   - [x] Release Notes（v1.2.0）

   ## 质量指标
   - 测试覆盖率: 82% ✅ (目标80%)
   - 性能: 登录245ms ✅ (目标500ms)
   - 安全: 无critical问题 ✅
   - 文档: 完整 ✅

   ## 监控配置
   - 可用性SLO: 99.9%
   - 延迟SLO: P95 <500ms
   - 错误率SLO: <0.1%

   ## 下一步建议
   - 监控SLO指标
   - 收集用户反馈
   - 考虑添加OAuth集成

   ## 总结
   ✅ 项目成功交付，质量优秀
   ```

#### 🔑 关键活动

##### 1. 清理临时文件
```bash
# 清理.temp/目录
rm -rf .temp/analysis/
rm -rf .temp/reports/
rm -rf .temp/cache/

# 保留evidence/（30天后自动归档）
# 保留核心文档（7个）
```

##### 2. 代码格式化
```bash
# 最终代码格式化
black src/
isort src/
prettier --write "**/*.{js,json,md}"
```

##### 3. 等待CI通过
```bash
# 监控CI状态
gh pr checks

等待所有checks通过:
✅ test
✅ lint
✅ security-scan
✅ bdd-test
✅ bp-guard
```

##### 4. PR合并
```bash
# 自动合并（如CI全过）
gh pr merge --auto --squash

# 或手动合并（需review）
gh pr merge --squash
```

##### 5. 分支清理
```bash
# 删除本地分支
git branch -d feature/user-auth

# 删除远程分支（GitHub自动）
# git push origin --delete feature/user-auth
```

##### 6. 最终验证
```bash
# 验证main分支
git checkout main
git pull

# 验证tag
git tag -l v1.2.0

# 验证release
gh release view v1.2.0
```

#### 💡 最佳实践
- **自动化清理**: 使用脚本而不是手工
- **验证后删除**: 确认合并成功后再删分支
- **保留证据**: evidence/目录保留30天
- **最终检查**: 确认所有产出物都已归档

#### ⚠️ 常见问题

**问题1: CI失败导致无法合并**
```
症状: PR blocked by failing checks
原因: 测试在本地过但CI失败
解决:
  1. 查看CI日志定位问题
  2. 本地复现CI环境
  3. 修复后重新push
  4. 等待CI重新运行
```

**问题2: 合并冲突**
```
症状: Merge conflict with main
原因: main分支有新提交
解决:
  1. git checkout feature/xxx
  2. git pull origin main
  3. 解决冲突
  4. git push
```

**问题3: 临时文件未清理**
```
症状: .temp/目录仍有文件
原因: 清理脚本未正确执行
解决: 手动运行清理脚本
```

---

## 📊 Agent策略（4-6-8原则）

### 策略概述

根据任务复杂度动态调整Agent数量，而不是固定配置。

```
简单任务（Bug修复、小改动）→ 4个Agent
标准任务（新功能、重构）→ 6个Agent
复杂任务（架构设计、大型功能）→ 8个Agent
```

### 各Phase Agent配置表

| Phase | 简单任务 | 标准任务 | 复杂任务 | 备注 |
|-------|---------|---------|---------|------|
| Phase 2 | 3 | 4 | 4 | 探索阶段 |
| Phase 1 | 4 | 5 | 6 | 规划+架构 |
| Phase 2 | 4 | 6 | 8 | 核心实现 |
| Phase 3 | 3 | 5 | 6 | 测试验证 |
| Phase 4 | 3 | 4 | 5 | 代码审查 |
| Phase 5 | 3 | 4 | 5 | 发布+监控 |
| Phase 6 | 2 | 2 | 3 | 清理合并 |
| **总计** | **22** | **30** | **37** | - |

### 详细配置

#### 简单任务示例（Bug修复）

**场景**: 修复登录表单验证bug

```yaml
Phase 2（3 Agents）:
  - backend-architect    # 分析bug原因
  - test-engineer        # 复现bug
  - technical-writer     # 记录问题

Phase 1（4 Agents）:
  - backend-architect    # 设计修复方案
  - test-engineer        # 测试策略
  - security-auditor     # 安全影响评估
  - technical-writer     # 更新文档

Phase 2（4 Agents）:
  - backend-architect    # 实现修复
  - test-engineer        # 编写测试
  - code-reviewer        # 即时审查
  - technical-writer     # 同步文档

Phase 3（3 Agents）:
  - test-engineer        # 执行测试
  - qa-specialist        # 质量验证
  - performance-engineer # 性能回归测试

Phase 4（3 Agents）:
  - code-reviewer        # 代码审查
  - security-auditor     # 安全复查
  - quality-guardian     # 质量把关

Phase 5（3 Agents）:
  - release-manager      # 发布管理
  - technical-writer     # Release Notes
  - devops-engineer      # 监控确认

Phase 6（2 Agents）:
  - cleanup-specialist   # 清理
  - release-manager      # 合并

总计: 22 Agents
预计时间: ~20分钟
```

#### 标准任务示例（新功能开发）

**场景**: 实现用户认证系统

```yaml
Phase 2（4 Agents）:
  - backend-architect    # 技术可行性
  - security-auditor     # 安全要求
  - database-specialist  # 数据模型
  - api-designer         # API设计

Phase 1（5 Agents）:
  - backend-architect    # 架构设计
  - api-designer         # API规划
  - database-specialist  # 数据库设计
  - test-engineer        # 测试策略
  - technical-writer     # 文档规划

Phase 2（6 Agents）:
  - backend-architect    # 核心逻辑
  - api-designer         # API实现
  - database-specialist  # 数据库操作
  - test-engineer        # 单元测试
  - security-auditor     # 安全实现
  - technical-writer     # 文档更新

Phase 3（5 Agents）:
  - test-engineer        # 测试执行
  - qa-specialist        # 质量验证
  - performance-engineer # 性能测试
  - security-auditor     # 安全扫描
  - technical-writer     # 测试文档

Phase 4（4 Agents）:
  - code-reviewer        # 代码审查
  - security-auditor     # 安全审查
  - technical-writer     # 文档审查
  - quality-guardian     # P2验收

Phase 5（4 Agents）:
  - release-manager      # 发布管理
  - technical-writer     # Release Notes
  - devops-engineer      # SLO配置
  - quality-guardian     # 最终确认

Phase 6（2 Agents）:
  - cleanup-specialist   # 清理
  - release-manager      # 合并

总计: 30 Agents
预计时间: ~25分钟
```

#### 复杂任务示例（架构重构）

**场景**: 微服务架构迁移

```yaml
Phase 2（4 Agents）:
  - backend-architect    # 架构分析
  - system-designer      # 系统设计
  - database-specialist  # 数据迁移策略
  - performance-engineer # 性能评估

Phase 1（6 Agents）:
  - backend-architect    # 微服务设计
  - api-designer         # API网关
  - database-specialist  # 数据分片
  - infrastructure-engineer # 基础设施
  - test-engineer        # 测试策略
  - technical-writer     # 架构文档

Phase 2（8 Agents）:
  - backend-architect    # 服务实现
  - api-designer         # API开发
  - database-specialist  # 数据迁移
  - frontend-specialist  # 前端适配
  - infrastructure-engineer # 部署配置
  - test-engineer        # 测试开发
  - security-auditor     # 安全加固
  - technical-writer     # 文档同步

Phase 3（6 Agents）:
  - test-engineer        # 全面测试
  - qa-specialist        # 质量保证
  - performance-engineer # 压力测试
  - security-auditor     # 安全测试
  - infrastructure-engineer # 基础设施验证
  - technical-writer     # 测试报告

Phase 4（5 Agents）:
  - code-reviewer        # 代码审查
  - architecture-reviewer # 架构审查
  - security-auditor     # 安全审查
  - performance-engineer # 性能审查
  - quality-guardian     # 综合把关

Phase 5（5 Agents）:
  - release-manager      # 发布管理
  - technical-writer     # 详细文档
  - devops-engineer      # 监控配置
  - infrastructure-engineer # 部署验证
  - quality-guardian     # 最终确认

Phase 6（3 Agents）:
  - cleanup-specialist   # 清理
  - release-manager      # 合并
  - devops-engineer      # 监控启动

总计: 37 Agents
预计时间: ~35分钟
```

### Agent选择原则

#### 必选Agents（所有任务）
- **backend-architect**: 核心技术决策
- **test-engineer**: 质量保证
- **technical-writer**: 文档维护

#### 按需选择Agents
- **api-designer**: 涉及API时必选
- **database-specialist**: 涉及数据库时必选
- **security-auditor**: 涉及认证/授权/敏感数据时必选
- **performance-engineer**: 高性能要求时必选
- **frontend-specialist**: 涉及前端时必选

#### 特殊Agents
- **cleanup-specialist**: Phase 6自动加入
- **quality-guardian**: Phase 4-5负责P2验收

---

## 🛡️ 质量门禁保持不变

### 门禁概述

6-Phase系统保留了所有质量门禁，仅阶段编号变化。

```
原P4门禁 → Phase 3门禁（static_checks.sh）
原P5门禁 → Phase 4门禁（pre_merge_audit.sh）
原P6验收 → Phase 5验收（P2 Checklist）
```

### Phase 3质量门禁（技术质量）

#### 工具
```bash
bash scripts/static_checks.sh
```

#### 检查项
1. **Shell语法检查**
   ```bash
   bash -n *.sh
   # 检查所有shell脚本语法
   ```

2. **Shellcheck Linting**
   ```bash
   shellcheck --severity=warning *.sh
   # 检查常见bug模式
   ```

3. **代码复杂度检查**
   ```bash
   # 函数长度>150行 → 阻止
   # 嵌套深度>5层 → 警告
   ```

4. **Hook性能测试**
   ```bash
   # pre-commit执行时间<2秒
   # pre-push执行时间<2秒
   ```

5. **功能测试执行**
   ```bash
   pytest test/unit/
   pytest test/integration/
   npm run bdd
   ```

#### 阻止标准
```yaml
任何检查失败 → ❌ 阻止进入Phase 4
处理流程:
  1. 定位失败原因
  2. 返回Phase 2修复
  3. 重新执行Phase 3
  4. 直到所有检查通过
```

#### 通过标准
```bash
✅ Shell syntax check passed
✅ Shellcheck linting passed (0 warnings)
✅ Code complexity check passed
✅ Hook performance test passed (<2s)
✅ All tests passed (82% coverage)

→ 允许进入Phase 4
```

---

### Phase 4质量门禁（代码质量）

#### 工具
```bash
bash scripts/pre_merge_audit.sh
```

#### 检查项

1. **配置完整性验证**
   ```bash
   检查项:
   - .git/hooks/pre-commit 存在且可执行（755）
   - .git/hooks/commit-msg 存在且可执行
   - .git/hooks/pre-push 存在且可执行
   - .claude/hooks/ 所有hooks注册正确
   ```

2. **遗留问题扫描**
   ```bash
   扫描范围: src/**/*.py
   禁止模式:
   - TODO
   - FIXME
   - HACK
   - XXX

   结果: 0个遗留问题 ✅
   ```

3. **垃圾文档检测**
   ```bash
   检查根目录.md文件数量
   允许: 7个核心文档
   - README.md
   - CLAUDE.md
   - INSTALLATION.md
   - ARCHITECTURE.md
   - CONTRIBUTING.md
   - CHANGELOG.md
   - LICENSE.md

   结果: ≤7个 ✅
   ```

4. **版本号一致性检查**
   ```bash
   比较:
   - .claude/settings.json "version"
   - CHANGELOG.md 最新版本号

   结果: 1.2.0 = 1.2.0 ✅
   ```

5. **代码模式一致性验证**
   ```bash
   验证:
   - 6个Layers使用相同分支检测逻辑
   - 错误处理模式统一
   - 日志格式一致
   - 命名规范统一

   结果: 100%一致 ✅
   ```

6. **文档完整性检查**
   ```bash
   检查:
   - REVIEW.md存在
   - REVIEW.md >100行
   - 包含必要章节（自动化检查、人工验证、P2对照）

   结果: 完整 ✅（126行）
   ```

#### 人工验证（必须完成）

1. **逻辑正确性**
   ```yaml
   审查项:
   - IF条件判断合理？
   - Return值语义明确？
   - 错误处理完善？
   - 边界条件考虑？

   示例错误:
   ❌ if [ "$var" == "value" ]  # 应该用 =
   ✅ if [ "$var" = "value" ]
   ```

2. **代码一致性**
   ```yaml
   审查项:
   - 6个Layers逻辑统一？
   - 命名规范一致？
   - 错误消息格式统一？
   - 日志格式一致？

   示例:
   Layer 1-6都应该用：
   if [[ "$branch" =~ ^(main|master|production)$ ]]
   ```

3. **P2 Checklist对照**
   ```markdown
   逐项对照P2_CHECKLIST.md:
   - [ ] 功能验收标准 → 全部✅
   - [ ] 技术验收标准 → 全部✅
   - [ ] 质量验收标准 → 全部✅
   - [ ] 文档验收标准 → 全部✅
   ```

#### 阻止标准
```yaml
任何critical issue → ❌ 阻止进入Phase 5

Critical级别:
- 配置完整性失败（hooks未注册）
- 安全问题（密码泄露、SQL注入）
- 逻辑严重错误（返回值相反）
- P2 Checklist未完成

处理流程:
  1. 评估问题严重度
  2. Critical → 返回Phase 2修复
  3. Major → 返回Phase 3修复
  4. Minor → 建议修复，可选
```

#### 通过标准
```bash
✅ Configuration integrity verified
✅ No legacy issues found (0 TODO/FIXME)
✅ Document count valid (7 core docs)
✅ Version consistency verified (1.2.0)
✅ Code pattern consistency validated
✅ Documentation completeness confirmed (126 lines)
✅ Logic correctness verified (human)
✅ Code consistency validated (human)
✅ P2 Checklist 100% complete

→ 允许进入Phase 5
```

---

### Phase 5验收确认（最终验收）

#### 核心原则
**Phase 5不应该发现bugs**

```
Phase 5职责:
  ✅ 确认Phase 2-4所有工作完成
  ✅ 生成Release Notes
  ✅ 创建Git Tag和PR
  ✅ 配置监控和SLO

  ❌ 不是发现bugs的阶段
```

#### P2 Checklist最终验收

```markdown
对照P2_CHECKLIST.md逐项验证:

## 功能验收标准
- [x] 用户可以通过邮箱+密码登录
  验证: 手动测试通过，单元测试覆盖
- [x] 登录失败3次后锁定账户15分钟
  验证: 集成测试覆盖，行为正确
- [x] 登录成功后生成JWT token
  验证: API测试通过，token格式正确

## 技术验收标准
- [x] 密码使用bcrypt加密（强度10）
  验证: 代码审查确认，配置正确
- [x] Token有效期24小时
  验证: 配置文件确认
- [x] 所有API端点有速率限制
  验证: 中间件已添加，测试通过

## 质量验收标准
- [x] 单元测试覆盖率 ≥80%
  验证: 82%，超过目标
- [x] 集成测试覆盖主要流程
  验证: 5个主要场景全部覆盖
- [x] 性能测试：登录请求<500ms
  验证: 实测245ms，远低于目标

## 文档验收标准
- [x] API文档包含所有端点
  验证: /api/auth/login已文档化
- [x] README包含快速开始指南
  验证: 已添加完整示例
- [x] REVIEW.md >100行
  验证: 126行，内容完整

## 最终结论
✅ 所有验收标准达成，项目完成！
```

#### 发现bugs的处理

```
如果在Phase 5发现bugs:
    ↓
❌ 说明Phase 4审查不充分
    ↓
立即停止发布流程
    ↓
记录问题到Phase 4改进清单
    ↓
返回Phase 4重新审查
    ↓
修复bugs后重新执行Phase 3-5
```

#### 通过标准
```bash
✅ P2 Checklist 100% complete
✅ Release Notes generated
✅ Git Tag created (v1.2.0)
✅ PR created (#123)
✅ Health check passed
✅ SLO configured
✅ No bugs found in Phase 5

→ 项目完成，等待用户确认
```

---

## 🔄 从P2-P7迁移指南

### 阶段映射关系

```
┌─────────────────────────────────────────────────────────┐
│ 原8-Phase系统（P2-P7）                                   │
└─────────────────────────────────────────────────────────┘
    P2: Discovery（探索）
    ↓
    P1: Plan（规划）
    ↓
    P2: Skeleton（骨架）
    ↓
    P3: Implementation（实现）
    ↓
    P4: Testing（测试）
    ↓
    P5: Review（审查）
    ↓
    P6: Release（发布）
    ↓
    P7: Monitor（监控）

┌─────────────────────────────────────────────────────────┐
│ 新6-Phase系统（Phase 2-5）                              │
└─────────────────────────────────────────────────────────┘
    Phase 2: Discovery（探索）← P2（无变化）
    ↓
    Phase 1: Planning & Architecture（规划+骨架）← P1+P2（合并）
    ↓
    Phase 2: Implementation（实现）← P3（重新编号）
    ↓
    Phase 3: Testing（测试）← P4（重新编号）
    ↓
    Phase 4: Review（审查）← P5（重新编号）
    ↓
    Phase 5: Release & Monitor（发布+监控）← P6+P7（合并）
    ↓
    Phase 6 (P9): Cleanup & Merge（清理合并）← 新增
```

### 详细映射表

| 原Phase | 原名称 | 新Phase | 新名称 | 变化类型 |
|---------|--------|---------|--------|----------|
| P2 | Discovery | Phase 2 | Discovery | 无变化 |
| P1 | Plan | Phase 1 | Planning & Architecture | 合并到Phase 1 |
| P2 | Skeleton | Phase 1 | Planning & Architecture | 合并到Phase 1 |
| P3 | Implementation | Phase 2 | Implementation | 重新编号 |
| P4 | Testing | Phase 3 | Testing | 重新编号 |
| P5 | Review | Phase 4 | Review | 重新编号 |
| P6 | Release | Phase 5 | Release & Monitor | 合并到Phase 5 |
| P7 | Monitor | Phase 5 | Release & Monitor | 合并到Phase 5 |
| - | - | Phase 6 | Cleanup & Merge | 新增 |

### 工具和脚本兼容性

#### ✅ 完全兼容（无需修改）

```yaml
Git Hooks:
  - .git/hooks/pre-commit      ✅ 继续工作
  - .git/hooks/commit-msg      ✅ 继续工作
  - .git/hooks/pre-push        ✅ 继续工作

质量门禁脚本:
  - scripts/static_checks.sh   ✅ 继续工作（Phase 3调用）
  - scripts/pre_merge_audit.sh ✅ 继续工作（Phase 4调用）

测试工具:
  - pytest                     ✅ 继续工作
  - npm run bdd               ✅ 继续工作
  - shellcheck                ✅ 继续工作

CI/CD:
  - .github/workflows/*.yml   ✅ 继续工作
```

#### 📝 仅术语更新（逻辑不变）

```yaml
文档更新:
  - CLAUDE.md                 📝 更新Phase术语
  - .claude/WORKFLOW.md       📝 本文件（已更新）
  - README.md                 📝 可选更新

Agent配置:
  - .claude/hooks/smart_agent_selector.sh
    📝 更新Phase 2-5术语（逻辑不变）
```

#### ❌ 不兼容（需要适配）

**无** - 所有工具向后兼容！

### 术语对照表

#### 代码中的术语替换

```bash
# 原术语 → 新术语
P2 → Phase 2（探索）
P1 → Phase 1（规划+骨架的规划部分）
P2 → Phase 1（规划+骨架的骨架部分）
P3 → Phase 2（实现）
P4 → Phase 3（测试）
P5 → Phase 4（审查）
P6 → Phase 5（发布+监控的发布部分）
P7 → Phase 5（发布+监控的监控部分）
```

#### 文档中的术语替换

```markdown
# 原表述 → 新表述
"P2-P7的8阶段系统" → "Phase 2-5的6阶段系统"
"P1规划，P2骨架" → "Phase 1规划+架构"
"P6发布，P7监控" → "Phase 5发布+监控"
"8个Phase" → "6个Phase"
"经过P2-P7的完整验证" → "经过Phase 2-5的完整验证"
```

### 迁移清单

#### 对于AI（Claude）

```markdown
- [ ] 理解Phase 2-5的新术语
- [ ] 理解合并后的Phase职责
  - Phase 1 = 原P1+P2
  - Phase 5 = 原P6+P7
- [ ] 使用新术语与用户沟通
- [ ] 继续使用所有现有工具（无变化）
- [ ] 质量门禁标准不变
  - Phase 3 → static_checks.sh
  - Phase 4 → pre_merge_audit.sh
  - Phase 5 → P2 Checklist验收
```

#### 对于用户

```markdown
- [ ] 了解新的6-Phase术语
- [ ] 理解Phase合并的原因（提升效率）
- [ ] 质量标准不变，放心使用
- [ ] 所有Git Hooks继续工作
- [ ] CI/CD流程不受影响
```

#### 对于文档维护者

```markdown
- [ ] 更新CLAUDE.md中的Phase术语
- [ ] 更新.claude/WORKFLOW.md（已完成）
- [ ] 更新README.md（可选）
- [ ] 更新相关脚本中的注释
- [ ] 保持CHANGELOG.md记录变更
```

### 向后兼容性承诺

```yaml
承诺:
  - ✅ 所有Git Hooks继续工作
  - ✅ 所有质量门禁工具继续工作
  - ✅ 所有测试脚本继续工作
  - ✅ 所有CI/CD pipeline继续工作
  - ✅ 质量标准保持不变
  - ✅ 仅术语变化，流程本质不变

不影响:
  - ✅ 分支保护机制
  - ✅ 代码质量标准
  - ✅ 测试覆盖率要求
  - ✅ 性能预算
  - ✅ SLO监控
```

### 常见问题

**Q1: 为什么要从8-Phase改成6-Phase？**
```
A: 提升效率17%，减少Agent切换开销
   - P1规划 + P2骨架 → 自然连续过程，合并更高效
   - P6发布 + P7监控 → 发布时就应该考虑监控，合并更合理
   - 质量门禁不变，保持标准
```

**Q2: 合并Phase会降低质量吗？**
```
A: 不会
   - 质量门禁完全保留（static_checks.sh, pre_merge_audit.sh）
   - P2 Checklist验收标准不变
   - 仅减少阶段切换，不减少检查项
   - 实际上更合理（规划和设计本就连续）
```

**Q3: 现有项目需要修改吗？**
```
A: 仅需更新术语，无需修改代码
   - Git Hooks → 无需修改
   - 测试脚本 → 无需修改
   - CI/CD → 无需修改
   - 文档 → 可选更新术语
```

**Q4: Phase编号变化会混乱吗？**
```
A: 不会
   - 文档清晰标注新旧对照
   - Agent会使用新术语
   - 迁移期可以新旧术语并用
   - 很快会习惯新术语（更简洁）
```

---

## 📊 优化效果

### 时间节省

```
原8-Phase系统（P2-P7）:
  P2: 2-3分钟（探索）
  P1: 3-4分钟（规划）
  P2: 2-3分钟（骨架）← Agent切换开销
  P3: 5-8分钟（实现）
  P4: 4-5分钟（测试）
  P5: 3-4分钟（审查）
  P6: 2-3分钟（发布）
  P7: 2-3分钟（监控）← Agent切换开销
  ─────────────────
  总计: 24-33分钟

新6-Phase系统（Phase 2-5）:
  Phase 2: 2-3分钟（探索）
  Phase 1: 3-4分钟（规划+骨架）← 合并，省切换
  Phase 2: 5-8分钟（实现）
  Phase 3: 4-5分钟（测试）
  Phase 4: 3-4分钟（审查）
  Phase 5: 3-4分钟（发布+监控）← 合并，省切换
  Phase 6: 2-3分钟（清理合并）
  ─────────────────
  总计: 22-31分钟

节省: 2-2分钟 + Agent切换开销 ≈ 5分钟
效率提升: ~17%
```

### Agent使用优化

```
原8-Phase系统:
  简单任务: ~24 Agents（8个阶段）
  标准任务: ~32 Agents
  复杂任务: ~40 Agents

新6-Phase系统:
  简单任务: ~22 Agents（7个阶段，含Phase 6）
  标准任务: ~30 Agents
  复杂任务: ~37 Agents

节省: 2-3个Agent调用 + 减少上下文切换
```

### 质量保持

```
质量指标对比:
  测试覆盖率要求: 80% → 80%（不变）
  代码复杂度限制: 150行 → 150行（不变）
  Hook性能要求: <2秒 → <2秒（不变）
  文档完整性: REVIEW.md >100行 → >100行（不变）
  P2验收标准: 100%完成 → 100%完成（不变）

质量门禁:
  Phase 3门禁: static_checks.sh（保留）
  Phase 4门禁: pre_merge_audit.sh（保留）
  Phase 5验收: P2 Checklist（保留）

结论: 质量标准完全保持，甚至更严格（新增Phase 6清理）
```

### 用户体验提升

```
原体验:
  - P1规划后要等P2骨架，感觉断档
  - P6发布后还要P7监控，步骤繁琐
  - 8个阶段记忆负担大

新体验:
  - Phase 1规划+骨架一气呵成，流畅
  - Phase 5发布+监控统一管理，清晰
  - 6个阶段更容易理解和记忆
  - 总时间更短，反馈更快
```

### 合并合理性分析

#### Phase 1合并（P1+P2）的合理性

**原问题**:
```
P1: 写PLAN.md（需求、API设计、数据模型）
    ↓ 切换Agent，上下文重建
P2: 根据PLAN.md创建目录结构

问题:
- P1的架构设计和P2的目录创建是连续思考
- Agent切换导致重新理解PLAN.md
- 时间浪费在上下文切换
```

**合并后优势**:
```
Phase 1: 规划+架构
- 设计时就考虑目录结构
- 目录结构直接反映架构设计
- 同一批Agent完成，上下文连续
- PLAN.md直接指导目录创建
- 节省2-3分钟切换时间
```

**实际效果**:
```
原P1+P2: 5-7分钟
新Phase 1: 3-4分钟
节省: 1-3分钟 + 上下文切换成本
```

#### Phase 5合并（P6+P7）的合理性

**原问题**:
```
P6: 发布（打tag、创建PR、更新文档）
    ↓ 切换Agent
P7: 监控（配置SLO、设置告警）

问题:
- 发布时应该就考虑监控
- 先发布再监控容易遗漏
- SLO配置应该在Release Notes中体现
```

**合并后优势**:
```
Phase 5: 发布+监控
- 发布时就配置好监控
- Release Notes包含SLO信息
- 不会遗漏监控配置
- 统一发布管理视角
- 节省2-3分钟切换时间
```

**实际效果**:
```
原P6+P7: 4-6分钟
新Phase 5: 3-4分钟
节省: 1-2分钟 + 避免遗漏监控
```

---

## 💡 最佳实践

### 工作流执行建议

#### 1. Phase 1永远第一步
```
收到用户需求时:
  ├─ ❌ 错误: 直接开始Phase 2
  └─ ✅ 正确: 先Phase 1分支检查
      ├─ 当前在main? → 创建新分支
      ├─ feature分支匹配? → 继续
      └─ feature分支不匹配? → 新分支
```

#### 2. Phase 2必须产出Checklist
```
Phase 2完成标准:
  ❌ 错误: 分析完就进Phase 1
  ✅ 正确: 必须有P2_CHECKLIST.md
      ├─ 功能验收标准（具体、可测试）
      ├─ 技术验收标准（量化指标）
      ├─ 质量验收标准（覆盖率、性能）
      └─ 文档验收标准（完整性）
```

#### 3. Phase 1规划和架构同步
```
Phase 1执行顺序:
  1. 需求分析 → PLAN.md（需求部分）
  2. 架构设计 → PLAN.md（架构部分）
  3. 目录结构 → 直接创建（基于架构）

  ✅ 优势: 连续思考，不断档
```

#### 4. Phase 2测试驱动开发
```
实现顺序:
  1. 写单元测试框架
  2. 实现功能（让测试通过）
  3. 重构优化
  4. 再写测试（覆盖边界）
  5. Git commit（小步快跑）

  ✅ 优势: TDD保证质量
```

#### 5. Phase 3门禁硬阻止
```
检查失败处理:
  ❌ 错误: 忽略warning，继续Phase 4
  ✅ 正确: 修复所有问题，重新Phase 3
      ├─ Shell语法错误 → 立即修复
      ├─ Shellcheck warning → 不忽略
      ├─ 测试失败 → 必须修复
      ├─ 性能超标 → 优化后重测
      └─ 覆盖率不足 → 补充测试
```

#### 6. Phase 4人工验证不可少
```
自动化 + 人工 = 完整审查
  ✅ pre_merge_audit.sh（自动）
  ✅ 逻辑正确性（人工）
  ✅ 代码一致性（人工）
  ✅ P2 Checklist对照（人工）

  ❌ 错误: 只依赖自动化
  ✅ 正确: 自动化 + 人工双保险
```

#### 7. Phase 5不应该发现bugs
```
Phase 5发现bugs说明什么:
  ❌ Phase 4审查不充分
  ❌ Phase 3测试覆盖不足
  ❌ Phase 2实现有缺陷

  处理方式:
  1. 立即停止发布
  2. 分析bug在哪个Phase应该被发现
  3. 返回对应Phase修复
  4. 更新Phase的检查清单
  5. 重新执行后续Phases
```

#### 8. Phase 6自动化清理
```
手动清理 vs 自动化:
  ❌ 手动: rm -rf .temp/（容易遗漏）
  ✅ 自动: scripts/cleanup.sh
      ├─ 清理.temp/
      ├─ 格式化代码
      ├─ 验证.gitignore
      └─ 生成清理报告
```

### 质量保证建议

#### 1. 左移测试思维
```
越早发现问题，修复成本越低:
  Phase 3发现 > Phase 4发现 > Phase 5发现

  策略:
  - Phase 2实现时就写测试
  - Phase 3全面测试覆盖
  - Phase 4人工逻辑验证
  - Phase 5只做确认，不找bugs
```

#### 2. 自动化优先
```
能自动化的绝不手工:
  ✅ static_checks.sh（自动）
  ✅ pre_merge_audit.sh（自动）
  ✅ pytest --cov（自动）
  ✅ shellcheck（自动）

  ⚠️ 人工验证（必要）:
  - 逻辑正确性
  - 代码一致性
  - P2 Checklist对照
```

#### 3. 质量指标追踪
```
持续改进:
  短期目标: Phase 5发现bugs <10%
  中期目标: 90%的bugs在Phase 3-4发现
  长期目标: Phase 5变成纯确认阶段

  追踪方式:
  - 每次记录bug在哪个Phase发现
  - 月度统计Phase分布
  - 分析原因，改进检查
```

### Agent使用建议

#### 1. 根据复杂度选择数量
```
不要固定配置，要动态评估:
  简单任务（Bug修复）→ 4-6-8规则的下限
  标准任务（新功能）→ 4-6-8规则的标准
  复杂任务（重构）→ 4-6-8规则的上限

  示例:
  - 修改文案 → 3个Agent就够
  - 新增API → 6个Agent标准
  - 架构迁移 → 8个Agent必要
```

#### 2. 并行执行优先
```
能并行就不串行:
  ❌ 错误: Agent1 → Agent2 → Agent3
  ✅ 正确: Agent1 + Agent2 + Agent3（同时）

  优势:
  - 节省时间（3个Agent并行 = 1个时间）
  - 多视角审视（避免盲点）
  - 相互校验（发现不一致）
```

#### 3. 特殊Agent按需加入
```
不是所有任务都需要:
  - api-designer → 涉及API时必选
  - database-specialist → 涉及数据库时必选
  - security-auditor → 涉及认证/授权时必选
  - performance-engineer → 高性能要求时必选

  示例:
  - 纯前端改动 → 不需要database-specialist
  - 静态页面 → 不需要api-designer
```

### 文档管理建议

#### 1. 核心文档白名单严格遵守
```
根目录只允许7个核心文档:
  ✅ README.md
  ✅ CLAUDE.md
  ✅ INSTALLATION.md
  ✅ ARCHITECTURE.md
  ✅ CONTRIBUTING.md
  ✅ CHANGELOG.md
  ✅ LICENSE.md

  ❌ 禁止创建其他.md文件
```

#### 2. 临时分析放.temp/
```
AI生成的分析、报告:
  ✅ .temp/analysis/code_review.md
  ✅ .temp/reports/test_results.json

  ❌ CODE_REVIEW_REPORT.md（根目录）

  生命周期: 7天后自动删除
```

#### 3. 文档更新与代码同步
```
代码变更时必须更新文档:
  Phase 2实现:
  - [x] 代码实现
  - [x] API文档更新（同步）
  - [x] README示例更新（同步）

  Phase 5发布:
  - [x] CHANGELOG.md追加
  - [x] Release Notes生成
```

### Git工作流建议

#### 1. 小步提交（Atomic Commits）
```
每完成一个功能点就commit:
  ✅ feat(auth): implement login logic
  ✅ test(auth): add login unit tests
  ✅ docs(auth): update API documentation

  ❌ feat(auth): implement entire auth system
```

#### 2. 规范Commit Message
```
格式: <type>(<scope>): <subject>

type:
  - feat: 新功能
  - fix: Bug修复
  - docs: 文档
  - test: 测试
  - refactor: 重构
  - perf: 性能优化
  - style: 格式

示例:
  feat(auth): add JWT token generation
  fix(auth): correct password validation logic
  test(auth): increase coverage to 85%
```

#### 3. PR描述详细
```
包含内容:
  - [x] 功能描述
  - [x] 关联Issue
  - [x] 测试情况
  - [x] P2 Checklist确认
  - [x] Screenshots（如有UI）
  - [x] Breaking Changes（如有）
```

---

## 🎯 总结

### 6-Phase系统核心优势

1. **更高效**
   - 合并相关阶段（P1+P2, P6+P7）
   - 减少Agent切换开销
   - 节省约17%时间（5分钟）

2. **更合理**
   - 规划+架构连续思考
   - 发布+监控统一管理
   - 新增Phase 6专门清理

3. **质量不变**
   - 所有质量门禁保留
   - P2 Checklist验收标准不变
   - 测试覆盖率要求不变

4. **更易用**
   - 6个阶段更容易记忆
   - 术语更清晰（Planning & Architecture）
   - 流程更流畅

### 向后兼容性

- ✅ Git Hooks无需修改
- ✅ 测试脚本继续工作
- ✅ CI/CD流程不受影响
- ✅ 质量标准完全保持
- 📝 仅需更新术语（可选）

### 迁移路径

```
1. 理解Phase 2-5新术语
2. 理解合并的合理性
3. 继续使用所有现有工具
4. 可选更新文档术语
5. 享受更高效的工作流
```

### 最终目标

**让AI编程达到专业级标准，同时提升效率**

- 🎯 质量: 100/100保障力评分
- ⚡ 效率: 17%时间节省
- 🛡️ 安全: 4层分支保护
- 📊 可观测: SLO实时监控
- 🤖 自主: 95%自动化率

---

**Claude Enhancer 6.3 - 让AI编程更专业、更高效**

*版本: 6.3.0*
*更新日期: 2025-10-15*
*下一版本: 6.4（计划中，更多AI自主化特性）*
