# PR模板使用指南

## 目录
- [概述](#概述)
- [使用流程](#使用流程)
- [各Phase使用示例](#各phase使用示例)
- [常见场景](#常见场景)
- [最佳实践](#最佳实践)
- [自动化技巧](#自动化技巧)

---

## 概述

Claude Enhancer的PR模板是一个**动态模板**，会根据当前Phase自动显示相应的质量要求和检查清单。

### 模板特点

1. **Phase感知**: 自动识别当前Phase（P0-P7）
2. **动态产出**: 根据Phase显示对应的must_produce要求
3. **质量门禁**: 集成Claude Enhancer的4层质量保障体系
4. **回滚方案**: 强制要求提供可执行的回滚步骤
5. **测试证据**: 要求提供测试通过的证明

### 模板位置

```
.github/PULL_REQUEST_TEMPLATE.md
```

当你创建PR时，GitHub会自动加载此模板。

---

## 使用流程

### 完整的PR工作流

```
┌─────────────────────────────────────────┐
│ 1. 开发功能（遵循8-Phase工作流）         │
│    - 创建feature分支                     │
│    - 按Phase开发                        │
│    - 本地测试通过                        │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 2. 推送分支                             │
│    git push origin feature/your-feature │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 3. 创建PR（模板自动加载）                │
│    gh pr create                         │
│    或在GitHub Web界面创建                │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 4. 填写PR模板                           │
│    - 检查当前Phase                      │
│    - 勾选must_produce清单               │
│    - 填写测试证据                        │
│    - 提供回滚方案                        │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 5. CI/CD自动运行                        │
│    - Phase gates验证                    │
│    - 测试套件运行                        │
│    - 安全扫描                           │
│    - 性能检查                           │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 6. Code Review                          │
│    - CODEOWNERS自动添加                 │
│    - Reviewers审查代码                  │
│    - 反馈和修改                         │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 7. 所有检查通过 + Approve               │
│    - CI全绿                             │
│    - 2+ approvals                       │
│    - 对话已解决                         │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 8. 合并PR                               │
│    - Squash merge（推荐）               │
│    - 删除feature分支                    │
│    - 自动部署（如配置）                  │
└─────────────────────────────────────────┘
```

---

## 各Phase使用示例

### P0 Discovery - 技术探索

```markdown
# Pull Request - Claude Enhancer Workflow

## Phase信息
**当前Phase**: P0
**Phase名称**: Discovery (探索)

## PR概述

### 任务描述
探索使用Redis作为会话存储的可行性

### 相关Issue
Related to #123 - 改善会话管理性能

### 变更类型
- [x] feat: 新功能
- [ ] fix: Bug修复

---

## Phase产出要求

### P0 Discovery - 必须产出
- [x] `docs/SPIKE.md`: 技术探索报告
  - [x] 包含GO/NO-GO决策：✅ GO - Redis可行
  - [x] 识别技术风险：连接池管理、数据持久化
  - [x] 可行性分析结论：性能提升预计40%，成本增加可接受

---

## 质量门禁检查

### 自动化检查（Git Hooks）
- [x] pre-commit检查通过
  - [x] 分支保护
  - [x] 路径白名单验证（P0允许所有路径）
  - [x] 安全检查（仅关键安全）

### Phase Gate验证
- [x] 当前Phase的gate文件存在（`.gates/00.ok`）
- [x] SPIKE.md包含GO/NO-GO决策

---

## 测试证据

### P0阶段测试
探索阶段主要是可行性验证，包含：
- [x] 原型代码可运行
- [x] 基准测试完成
- [x] 风险识别完成

---

## 回滚方案

### 问题场景
如果决定不采用Redis方案

### 回滚步骤
```bash
# 探索分支可以直接删除，不影响主线
git branch -D feature/redis-exploration
```

---

## 影响范围

### 修改文件清单
- `docs/SPIKE.md` (新增)
- `experiments/redis-prototype.js` (新增，临时)

### 依赖变更
- [ ] 无依赖变更（探索阶段）

---

## 审查清单

### Code Review要点
- [x] GO/NO-GO决策清晰
- [x] 风险识别充分
- [x] 成本收益分析合理

---

## 签名确认
- [x] 我已阅读并遵循Claude Enhancer工作流规范
- [x] 我已完成P0的探索和决策
- [x] 本PR可以安全合并

**审查者签字**: @tech-lead
**审查日期**: 2025-01-15
```

### P1 Plan - 规划

```markdown
# Pull Request - Claude Enhancer Workflow

## Phase信息
**当前Phase**: P1
**Phase名称**: Plan (规划)

## PR概述

### 任务描述
完成Redis会话存储功能的详细规划

### 相关Issue
Closes #124 - Redis会话存储实现规划

### 变更类型
- [ ] feat: 新功能
- [x] docs: 文档更新

---

## Phase产出要求

### P1 Plan - 必须产出
- [x] `docs/PLAN.md`: 完整规划文档
  - [x] 包含三级标题：任务清单、受影响文件清单、回滚方案 ✅
  - [x] 任务清单 8 条（≥5条要求）✅
    1. 创建RedisSessionStore类 (src/session/RedisStore.ts)
    2. 实现连接池管理 (src/session/ConnectionPool.ts)
    3. 添加序列化/反序列化逻辑 (src/session/Serializer.ts)
    4. 配置Redis客户端 (src/config/redis.ts)
    5. 迁移现有会话数据 (scripts/migrate_sessions.sh)
    6. 添加健康检查端点 (src/api/health.ts)
    7. 更新环境变量配置 (.env.example)
    8. 编写迁移文档 (docs/REDIS_MIGRATION.md)
  - [x] 受影响文件清单为具体路径 ✅
  - [x] 回滚方案具体可执行 ✅

---

## 质量门禁检查

### 自动化检查（Git Hooks）
- [x] pre-commit检查通过
  - [x] 路径白名单验证（P1只允许修改docs/PLAN.md）
  - [x] 安全检查通过

### Phase Gate验证
- [x] 当前Phase的gate文件存在（`.gates/01.ok`）
- [x] 上一个Phase（P0）的gate已通过 ✅
- [x] PLAN.md包含必需的三个标题 ✅
- [x] 任务清单≥5条 ✅

---

## 回滚方案

### 问题场景
1. Redis方案不可行（发现新的技术障碍）
2. 成本超出预期

### 回滚步骤
```bash
# 1. 回退到内存会话存储
git revert <redis-commits>

# 2. 恢复原有配置
git checkout HEAD~1 -- src/config/session.ts

# 3. 验证系统正常
npm test
npm run health-check
```

### 回滚验证
- [x] 回滚步骤已在测试环境验证
- [x] 回滚时间 < 2分钟
- [x] 无数据丢失风险

---

## 影响范围

### 修改文件清单
- `docs/PLAN.md` (新增)

### 依赖变更
- [ ] 无依赖变更（规划阶段）

---

## 审查清单

### Code Review要点
- [x] 任务分解合理
- [x] 文件路径准确
- [x] 回滚方案可行
- [x] 无遗漏关键任务

### 架构审查
- [x] 符合系统架构
- [x] 模块划分清晰
- [x] 接口设计合理

---

## 签名确认
- [x] 我已阅读并遵循Claude Enhancer工作流规范
- [x] 我已完成P1的规划文档
- [x] 所有任务清单明确且可执行
- [x] 本PR可以安全合并

**审查者签字**: @product-manager @architect
**审查日期**: 2025-01-16
```

### P3 Implementation - 实现

```markdown
# Pull Request - Claude Enhancer Workflow

## Phase信息
**当前Phase**: P3
**Phase名称**: Implementation (实现)

## PR概述

### 任务描述
实现Redis会话存储核心功能

### 相关Issue
Closes #125 - Redis会话存储实现

### 变更类型
- [x] feat: 新功能

---

## Phase产出要求

### P3 Implementation - 必须产出
- [x] 功能代码实现（可构建）✅
  - [x] 代码符合项目规范
  - [x] 构建/编译通过 `npm run build` ✅
- [x] `docs/CHANGELOG.md`: Unreleased段新增条目 ✅
  - [x] 简述变更范围：添加Redis会话存储支持
  - [x] 说明影响面：替换内存存储，需要Redis服务
- [x] 变更点清单（见commits）

---

## 质量门禁检查

### 自动化检查（Git Hooks）
- [x] pre-commit检查通过
  - [x] 路径白名单验证（P3允许src/**和docs/CHANGELOG.md）
  - [x] 安全检查（无硬编码密钥）
  - [x] 代码Linting（ESLint通过）
  - [x] TypeScript编译通过

### Phase Gate验证
- [x] 构建/编译通过 ✅
- [x] CHANGELOG Unreleased段存在新增条目 ✅
- [x] 未改动非白名单目录 ✅

### 代码质量
- [x] 代码符合项目风格指南（Prettier格式化）
- [x] 无ESLint警告或错误
- [x] 代码复杂度合理（圈复杂度 < 10）
- [x] 无安全漏洞（npm audit通过）

---

## 测试证据

### 测试覆盖
```
测试执行摘要：
- Total: 0 tests (P3不运行测试，P4阶段进行)
- 手动验证: ✅ 代码可编译，接口定义正确
```

**注**: P3阶段focus在实现，完整测试在P4阶段进行

---

## 回滚方案

### 问题场景
1. Redis连接失败导致服务不可用
2. 会话数据迁移失败
3. 性能不达预期

### 回滚步骤
```bash
# 1. 立即回滚到上一个版本
git revert HEAD

# 2. 切换回内存会话存储
export SESSION_STORE=memory
systemctl restart app-service

# 3. 验证服务恢复
curl http://localhost:3000/health
# 预期: {"status": "ok", "session_store": "memory"}

# 4. 通知团队
echo "已回滚Redis会话存储，当前使用内存存储" | slack-notify
```

### 回滚验证
- [x] 回滚步骤已在staging环境测试
- [x] 回滚时间 < 3分钟
- [x] 数据一致性保证（会话自动重建）
- [x] 无需手动干预

### 应急联系
- 负责人: @backend-lead
- 备用联系: @devops-oncall

---

## 影响范围

### 修改文件清单
- `src/session/RedisStore.ts` (新增)
- `src/session/ConnectionPool.ts` (新增)
- `src/session/Serializer.ts` (新增)
- `src/config/redis.ts` (新增)
- `src/config/session.ts` (修改 - 添加Redis选项)
- `docs/CHANGELOG.md` (修改 - 添加条目)

### 依赖变更
- [x] 新增依赖:
  - `ioredis@5.3.2` - Redis客户端
  - `@types/ioredis@5.0.0` - TypeScript类型定义

### 配置变更
- [x] 环境变量:
  ```
  REDIS_HOST=localhost
  REDIS_PORT=6379
  REDIS_PASSWORD=<secret>
  REDIS_DB=0
  REDIS_KEY_PREFIX=sess:
  SESSION_STORE=redis  # 默认memory
  ```

### 数据库变更
- [ ] 无数据库schema变更

---

## 部署说明

### 部署前准备
- [x] Redis服务部署（使用现有实例）
- [x] 配置文件更新（.env.production）
- [x] 依赖包安装 `npm ci`

### 部署步骤
1. 部署Redis（如未部署）
   ```bash
   docker run -d --name redis \
     -p 6379:6379 \
     redis:7-alpine
   ```

2. 更新应用配置
   ```bash
   cp .env.example .env.production
   # 编辑 .env.production 设置 REDIS_* 变量
   ```

3. 构建应用
   ```bash
   npm run build
   ```

4. 重启服务
   ```bash
   pm2 restart app-service
   ```

### 部署验证
- [ ] 健康检查通过
- [ ] 会话创建/读取正常
- [ ] Redis连接状态正常
- [ ] 无错误日志

---

## 文档更新

### 文档清单
- [x] CHANGELOG更新
- [ ] README更新（P6阶段）
- [ ] API文档更新（P6阶段）

---

## 审查清单

### Code Review要点
- [x] 代码逻辑正确
- [x] 错误处理完善（连接失败、超时处理）
- [x] 性能考虑充分（连接池、序列化优化）
- [x] 安全性审查通过（无密码硬编码）
- [x] 可维护性良好（清晰的接口，充分的注释）

### 架构审查
- [x] 符合系统架构（分层清晰）
- [x] 无架构劣化
- [x] 接口设计合理（ISessionStore接口）
- [x] 依赖关系清晰（松耦合设计）

### 安全审查
- [x] 无硬编码密钥
- [x] 输入验证充分（sessionId验证）
- [x] 权限控制正确
- [x] 数据加密（序列化时可选加密）

---

## 额外信息

### 性能影响
- [x] 性能提升: 预计40-60%
  - 内存存储: ~1ms per op
  - Redis存储: ~2-3ms per op（但支持分布式）
  - 整体吞吐量提升：支持水平扩展

### 兼容性
- [x] 完全向后兼容
  - 默认使用memory存储
  - 通过环境变量切换到Redis
  - 会话数据格式不变

### 已知问题
- [x] 问题1: Redis连接断开时会回退到内存存储
  - 计划在 P7 监控阶段添加告警

### 后续工作
- [ ] P4: 添加完整测试套件
- [ ] P6: 更新部署文档
- [ ] P7: 配置监控和SLO

---

## 签名确认
- [x] 我已阅读并遵循Claude Enhancer工作流规范
- [x] 我已完成P3的功能实现
- [x] 代码可构建且无Linting错误
- [x] CHANGELOG已更新
- [x] 回滚方案已验证
- [x] 本PR可以安全合并

**审查者签字**: @backend-lead @security-lead
**审查日期**: 2025-01-18
```

### P4 Testing - 测试

```markdown
# Pull Request - Claude Enhancer Workflow

## Phase信息
**当前Phase**: P4
**Phase名称**: Testing (测试)

## PR概述

### 任务描述
为Redis会话存储添加完整测试套件

### 相关Issue
Closes #126 - Redis会话存储测试

### 变更类型
- [x] test: 测试相关

---

## Phase产出要求

### P4 Testing - 必须产出
- [x] 测试用例（新增 12 条，≥2条要求）✅
  - [x] 单元测试: 8条
  - [x] 边界/负例测试: 4条 ✅
  - [x] 所有测试通过 ✅
- [x] `docs/TEST-REPORT.md`: 测试报告 ✅
  - [x] 列出覆盖的模块/函数
  - [x] 测试结果汇总
- [x] 测试证据（见下方）

---

## 质量门禁检查

### 自动化检查（Git Hooks）
- [x] pre-commit检查通过
  - [x] 路径白名单验证（P4允许tests/**）
  - [x] 安全检查通过
  - [x] 代码Linting通过

- [x] pre-push检查通过（P4强制）
  - [x] unit + boundary + smoke 必须全绿 ✅

### Phase Gate验证
- [x] 当前Phase的gate文件存在（`.gates/04.ok`）
- [x] 测试报告存在并含覆盖点清单 ✅

---

## 测试证据

### 测试覆盖
```
测试执行摘要：
Jest Test Summary
  Test Suites: 4 passed, 4 total
  Tests:       12 passed, 12 total
  Snapshots:   0 total
  Time:        3.421s
  Coverage:    94.2%

模块覆盖:
- RedisStore: 96% (48/50 lines)
- ConnectionPool: 92% (35/38 lines)
- Serializer: 95% (20/21 lines)
- redis config: 90% (9/10 lines)
```

### 测试类型
- [x] 单元测试（Unit）- 8条
  - RedisStore基本操作（set/get/delete）
  - ConnectionPool管理
  - Serializer序列化/反序列化
  - 配置加载

- [x] 边界测试（Boundary）- 4条
  - 空session处理
  - 超大session数据
  - 并发访问
  - 过期session清理

- [x] 冒烟测试（Smoke）- 集成在单元测试中
  - Redis连接测试
  - 基本读写验证

- [x] 集成测试（Integration）- 包含在test suite中
  - 完整会话生命周期
  - 多实例session共享

### 测试日志
<details>
<summary>点击展开完整测试日志</summary>

```
PASS tests/unit/RedisStore.test.ts
  RedisStore
    ✓ should create session (45ms)
    ✓ should get session (12ms)
    ✓ should update session (18ms)
    ✓ should delete session (10ms)
    ✓ should return null for non-existent session (8ms)
    ✓ should handle connection errors gracefully (25ms)

PASS tests/unit/ConnectionPool.test.ts
  ConnectionPool
    ✓ should create connection pool (15ms)
    ✓ should reuse connections (22ms)
    ✓ should handle max connections (35ms)
    ✓ should reconnect on failure (45ms)

PASS tests/unit/Serializer.test.ts
  Serializer
    ✓ should serialize session data (5ms)
    ✓ should deserialize session data (6ms)

PASS tests/boundary/RedisStore.boundary.test.ts
  RedisStore Boundary Cases
    ✓ should handle empty session (8ms)
    ✓ should handle large session data (>1MB) (120ms)
    ✓ should handle concurrent access (150ms)
    ✓ should clean expired sessions (200ms)

Test Suites: 4 passed, 4 total
Tests:       12 passed, 12 total
```

</details>

### 性能测试结果
```
Benchmark Results:
- Session Create: avg 2.3ms (< 5ms target) ✅
- Session Get: avg 1.8ms (< 3ms target) ✅
- Session Update: avg 2.1ms (< 5ms target) ✅
- Session Delete: avg 1.5ms (< 3ms target) ✅
- Concurrent Operations (100): avg 45ms (< 100ms target) ✅
```

---

## 回滚方案

### 问题场景
如果测试发现严重bug

### 回滚步骤
```bash
# 1. 回滚到上一个commit（P3实现）
git revert HEAD

# 2. 删除新增的测试（如需要）
git rm tests/unit/RedisStore.test.ts
# ... 其他测试文件

# 3. 重新运行验证
npm test
```

### 回滚验证
- [x] 回滚后P3代码仍然可用
- [x] 原有测试不受影响

---

## 影响范围

### 修改文件清单
- `tests/unit/RedisStore.test.ts` (新增)
- `tests/unit/ConnectionPool.test.ts` (新增)
- `tests/unit/Serializer.test.ts` (新增)
- `tests/boundary/RedisStore.boundary.test.ts` (新增)
- `tests/integration/session-flow.test.ts` (修改 - 添加Redis场景)
- `docs/TEST-REPORT.md` (新增)

### 依赖变更
- [x] 新增依赖:
  - `@testcontainers/redis@10.2.1` - Redis测试容器
  - `jest-mock-extended@3.0.5` - Mock辅助

---

## 审查清单

### Code Review要点
- [x] 测试覆盖充分（94.2%）
- [x] 边界情况考虑完整
- [x] Mock使用合理
- [x] 测试可维护性好

### 测试质量
- [x] 测试独立性（不依赖执行顺序）
- [x] 测试稳定性（可重复运行）
- [x] 测试清晰性（命名清晰，结构合理）
- [x] 性能测试合理

---

## 签名确认
- [x] 我已阅读并遵循Claude Enhancer工作流规范
- [x] 我已完成P4的测试编写
- [x] 所有测试通过（12/12）
- [x] 测试覆盖率达标（94.2% > 80%）
- [x] 测试报告已生成
- [x] 本PR可以安全合并

**审查者签字**: @qa-lead @test-engineer
**审查日期**: 2025-01-19
```

---

## 常见场景

### 场景1: Hotfix紧急修复

```markdown
# Pull Request - Hotfix: 修复Redis连接泄漏

## Phase信息
**当前Phase**: P3 (紧急修复，简化流程)
**Phase名称**: Implementation (实现)

## PR概述

### 任务描述
修复Redis连接未正确释放导致的连接泄漏问题

### 相关Issue
Closes #CRITICAL-127 - 生产环境Redis连接耗尽

### 变更类型
- [x] fix: Bug修复

---

## 紧急修复说明

**严重程度**: 🔴 Critical
**影响范围**: 生产环境所有实例
**用户影响**: 会话创建失败，用户无法登录
**修复紧急度**: 立即

---

## Phase产出要求（简化）

### 核心修复
- [x] 问题根因分析: ConnectionPool未在错误时释放连接
- [x] 修复代码实现: 添加finally块确保连接释放
- [x] 快速验证: 本地重现并验证修复

---

## 质量门禁检查（简化）

### 快速验证
- [x] 构建通过
- [x] Smoke测试通过
- [x] 本地验证成功

**注**: Hotfix跳过完整测试套件，部署后立即补充

---

## 测试证据

### 快速验证
```
1. 重现问题:
   - 模拟连接错误
   - 观察连接池耗尽
   ✅ 已重现

2. 验证修复:
   - 应用patch
   - 重新测试
   - 连接正常释放
   ✅ 修复生效

3. Smoke测试:
   - Session create/get/delete
   - 所有操作正常
   ✅ 通过
```

---

## 回滚方案

### 立即回滚
```bash
# 如果修复导致新问题
git revert <commit-hash>
kubectl rollout undo deployment/app-service
# 预计回滚时间: < 2分钟
```

### 验证
- [x] 回滚脚本已准备
- [x] 监控已配置
- [x] Oncall团队已待命

---

## 部署计划

### 金丝雀部署（加速）
- [x] 10% 流量（观察10分钟）
- [x] 如无异常 → 50% 流量（观察10分钟）
- [x] 如无异常 → 100% 流量

### 监控指标
- Redis连接数
- 错误率
- 响应时间
- Session成功率

---

## 后续工作

- [ ] 补充完整测试套件（明天）
- [ ] 更新文档
- [ ] Root cause分析报告
- [ ] 添加监控告警（防止再次发生）

---

## 签名确认
- [x] 紧急修复，已验证可行
- [x] 回滚方案已准备
- [x] 监控已配置
- [x] 可以立即部署

**审查者**: @oncall-lead @senior-dev
**审查时间**: 15分钟（紧急简化流程）
**部署时间**: 立即
```

### 场景2: 多Phase合并PR

有时一个PR可能跨越多个Phase（不推荐，但允许）：

```markdown
# Pull Request - Redis会话存储完整实现

## Phase信息
**Phase范围**: P2 → P3 → P4
**主要Phase**: P3 (Implementation)

## PR概述

### 任务描述
完整实现Redis会话存储（包含骨架、实现、测试）

**注意**: 通常应该拆分为3个独立PR，此次合并是因为POC性质

---

## Phase产出要求

### P2 Skeleton - 已完成
- [x] 目录结构创建
- [x] 接口定义

### P3 Implementation - 已完成
- [x] 功能代码实现
- [x] CHANGELOG更新

### P4 Testing - 已完成
- [x] 测试用例 ≥2条
- [x] 测试报告

---

## 质量门禁检查

### 多Phase验证
- [x] P2 gate通过（`.gates/02.ok`）
- [x] P3 gate通过（`.gates/03.ok`）
- [x] P4 gate通过（`.gates/04.ok`）

---

（其余部分与标准PR相同）
```

### 场景3: 文档更新PR（P6）

```markdown
# Pull Request - Redis会话存储文档更新

## Phase信息
**当前Phase**: P6
**Phase名称**: Release (发布)

## PR概述

### 任务描述
更新Redis会话存储相关文档，准备v2.0.0发布

---

## Phase产出要求

### P6 Release - 必须产出
- [x] `docs/README.md`: 文档更新 ✅
  - [x] 安装说明（包含Redis依赖）
  - [x] 使用说明（配置Redis）
  - [x] 注意事项（Redis最低版本要求）
- [x] `docs/CHANGELOG.md`: 版本信息 ✅
  - [x] 版本号递增: v1.5.0 → v2.0.0
  - [x] 影响面说明: Breaking change - 需要Redis
- [x] Release Notes ✅
  - [x] Git tag: v2.0.0
  - [x] 发布说明完整

---

## 发布内容

### 新功能
- Redis会话存储支持
- 分布式会话共享
- 性能提升40-60%

### Breaking Changes
- 环境变量: 新增 `REDIS_*` 配置
- 依赖: 需要 Redis 6.0+
- 迁移: 需要运行迁移脚本

### 升级指南
```bash
# 1. 安装Redis
docker run -d redis:7-alpine

# 2. 更新环境变量
cat >> .env << EOF
REDIS_HOST=localhost
REDIS_PORT=6379
SESSION_STORE=redis
EOF

# 3. 升级应用
npm install
npm run build
npm run migrate:sessions

# 4. 重启服务
pm2 restart app
```

---

## 文档更新

### 文档清单
- [x] README.md（新增Redis章节）
- [x] CHANGELOG.md（v2.0.0条目）
- [x] MIGRATION.md（升级指南）
- [x] API.md（会话相关API更新）

---

## 签名确认
- [x] 文档准确且完整
- [x] 版本号正确递增
- [x] Release notes清晰
- [x] 升级指南可执行
- [x] 本PR可以安全合并

**审查者**: @tech-writer @release-manager
**审查日期**: 2025-01-22
```

---

## 最佳实践

### 1. PR大小控制

```
推荐PR大小：
- 单个Phase的产出
- < 500行代码变更
- 完成时间 < 2天

如果超出：
- 拆分为多个PR
- 每个PR对应一个清晰的功能点
```

### 2. Commit消息规范

```bash
# 良好的commit消息
feat(session): implement Redis session store
test(session): add boundary tests for Redis store
docs(readme): add Redis configuration guide

# 遵循约定式提交（Conventional Commits）
<type>(<scope>): <subject>

type: feat|fix|docs|test|refactor|perf|chore
scope: 功能模块
subject: 简短描述（50字以内）
```

### 3. PR描述技巧

```markdown
## 好的描述特征：

1. **上下文清晰**
   - 为什么做这个改动？
   - 解决什么问题？

2. **变更明确**
   - 改了什么？
   - 如何验证？

3. **影响可评估**
   - 影响哪些模块？
   - 有没有Breaking changes？

4. **可操作性强**
   - 回滚步骤清晰
   - 部署步骤明确
```

### 4. Review策略

```
Review分工：

Phase     | Primary Reviewer        | Secondary Reviewer
----------|------------------------|-------------------
P0        | Tech Lead              | Architect
P1        | Product Manager        | Tech Lead
P2        | Architect              | Senior Dev
P3        | Code Owner             | Senior Dev
P4        | QA Lead                | Test Engineer
P5        | Senior Dev             | Security Lead
P6        | Tech Writer            | Release Manager
P7        | SRE Lead               | DevOps Lead
```

### 5. CI/CD集成

```yaml
# 在PR中显示CI状态
Required status checks:
✅ validate-phase-gates     # Phase门禁
✅ run-unit-tests          # 单元测试
✅ run-boundary-tests      # 边界测试
✅ check-security          # 安全扫描
⏳ validate-openapi        # API契约（运行中）
⏳ check-performance       # 性能检查（运行中）

在PR评论中自动显示：
- 测试覆盖率报告
- 性能对比
- 安全扫描结果
```

---

## 自动化技巧

### 1. 自动填充Phase信息

创建脚本自动检测当前Phase：

```bash
#!/bin/bash
# scripts/create_pr_with_phase.sh

CURRENT_PHASE=$(cat .phase/current 2>/dev/null || echo "P0")

# 读取模板
TEMPLATE=$(cat .github/PULL_REQUEST_TEMPLATE.md)

# 替换Phase占位符
TEMPLATE="${TEMPLATE//<!-- 从 .phase\/current 自动读取 --> P0-P7/$CURRENT_PHASE}"

# 创建PR
gh pr create --body "$TEMPLATE"
```

### 2. 自动验证must_produce

PR提交后自动检查：

```yaml
# .github/workflows/pr-validation.yml
name: PR Validation

on:
  pull_request:
    types: [opened, edited, synchronize]

jobs:
  validate-must-produce:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Get current phase
        id: phase
        run: echo "current=$(cat .phase/current)" >> $GITHUB_OUTPUT

      - name: Validate must_produce
        run: |
          ./scripts/validate_must_produce.sh ${{ steps.phase.outputs.current }}

      - name: Comment on PR
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '❌ Must_produce验证失败，请检查PR模板中的产出清单'
            })
```

### 3. 自动添加标签

根据Phase自动添加PR标签：

```yaml
name: Auto Label PR

on:
  pull_request:
    types: [opened]

jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Add phase label
        uses: actions/github-script@v6
        with:
          script: |
            const phase = require('fs').readFileSync('.phase/current', 'utf8').trim();
            const labels = [phase, 'claude-enhancer'];

            await github.rest.issues.addLabels({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              labels: labels
            });
```

### 4. PR模板变体

针对不同Phase创建专用模板：

```
.github/
  PULL_REQUEST_TEMPLATE/
    p0_discovery.md
    p1_plan.md
    p3_implementation.md
    p4_testing.md
    hotfix.md
```

使用时：
```bash
# 创建PR时选择模板
gh pr create --template p3_implementation.md
```

---

## 总结

### PR模板核心价值

1. **标准化**: 统一的PR格式，提升团队效率
2. **质量保证**: 强制检查清单，确保质量
3. **可追溯性**: 完整记录变更原因和影响
4. **可回滚性**: 明确的回滚方案
5. **知识传递**: PR本身就是文档

### 成功的PR应该

- ✅ 明确说明"为什么"和"是什么"
- ✅ 完成所有Phase的must_produce
- ✅ 通过所有自动化检查
- ✅ 提供可执行的回滚方案
- ✅ 包含充分的测试证据
- ✅ 文档和代码同步更新

### 下一步

1. 熟悉PR模板结构
2. 实践创建一个完整的PR
3. 理解各Phase的产出要求
4. 配置自动化工具
5. 持续改进流程

---

**相关文档**：
- [Branch Protection配置指南](BRANCH_PROTECTION_SETUP.md)
- [CODEOWNERS配置](.github/CODEOWNERS)
- [8-Phase工作流](.claude/WORKFLOW.md)
- [质量保障体系](WORKFLOW_QUALITY_ASSURANCE.md)
