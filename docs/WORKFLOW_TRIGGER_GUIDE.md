# Claude Enhancer 工作流触发指南

## 🎯 核心理念：双模式协作

Claude Enhancer 支持两种工作模式，简单清晰：

### 💭 讨论模式（默认）
**特点**：
- 自由讨论、分析、规划
- 不会自动创建分支
- 不会触发工作流
- 适合需求澄清、方案设计

**触发**：默认模式，无需任何操作

**示例**：
```
你: "这个功能应该怎么实现？"
Claude: [分析并提供建议，保持讨论模式]

你: "帮我分析一下代码结构"
Claude: [阅读代码，提供分析，不触发工作流]
```

### 🚀 执行模式（显式触发）
**特点**：
- 自动创建分支（Phase 0）
- 启动8-Phase工作流
- 智能选择Agent数量
- 适合实际开发任务

**触发词**（5个明确触发词）：
1. `现在开始实现`
2. `现在开始执行`
3. `开始工作流`
4. `let's implement`
5. `let's start`

**示例**：
```
你: "现在开始实现用户登录功能"
Claude:
  ✅ 自动创建分支: P3/20251001-user-login
  ✅ 进入Phase 3（实现阶段）
  ✅ 推荐6个Agent并行执行
```

## 🌿 智能分支命名系统

### 命名格式
```
{Phase}/{YYYYMMDD}-{task-slug}
```

### Phase自动检测
- **P1规划**: 包含"规划、计划、分析、需求"
- **P2骨架**: 包含"架构、骨架、结构、框架"
- **P3实现**: 包含"实现、开发、编写、修复"（默认）
- **P4测试**: 包含"测试、验证、检查"

### 示例

| 任务描述 | 生成分支 |
|---------|----------|
| 现在开始实现用户认证系统 | `P3/20251001-user-auth-system` |
| 现在开始执行数据库优化 | `P3/20251001-database-optimize` |
| 开始工作流，规划API设计 | `P1/20251001-plan-api-design` |
| let's implement dashboard | `P3/20251001-implement-dashboard` |

## 🤖 Agent自动选择策略

### 4-6-8原则

**简单任务（4个Agent）**：
- 触发词包含：简单、修复、bug
- Agent组合：
  - backend-architect
  - test-engineer
  - code-reviewer
  - documentation-writer

**标准任务（6个Agent，默认）**：
- 大部分开发任务
- Agent组合：
  - backend-architect
  - database-specialist
  - test-engineer
  - security-auditor
  - code-reviewer
  - documentation-writer

**复杂任务（8个Agent）**：
- 触发词包含：系统、架构、复杂、完整
- Agent组合：
  - backend-architect
  - database-specialist
  - security-auditor
  - performance-engineer
  - test-engineer
  - api-designer
  - code-reviewer
  - documentation-writer

## 📋 完整工作流（8 Phases）

```
✅ P0: 分支创建 - 自动完成
   ↓
→ P1: 规划 - 需求分析，生成PLAN.md
   ↓
→ P2: 骨架 - 架构设计，创建目录结构
   ↓
→ P3: 实现 - 编码开发（多Agent并行）
   ↓
→ P4: 测试 - 单元/集成/性能/BDD测试
   ↓
→ P5: 审查 - 代码审查，生成REVIEW.md
   ↓
→ P6: 发布 - 文档更新，打tag，健康检查
   ↓
→ P7: 监控 - 生产监控，SLO跟踪
```

## 🎮 使用示例

### 场景1：快速修复bug
```
用户: "现在开始实现修复登录按钮bug"

Claude:
  🚀 Phase 0: 自动创建工作分支
  📍 任务描述：修复登录按钮bug
  🎯 检测Phase：P3
  🌿 分支名称：P3/20251001-fix-login-button
  ✅ 成功创建分支

  🤖 Agent策略（4-6-8原则）：
  • 简单任务（4个Agent）：
    - backend-architect, test-engineer
    - code-reviewer, documentation-writer
```

### 场景2：开发新功能
```
用户: "现在开始执行用户认证系统"

Claude:
  🚀 Phase 0: 自动创建工作分支
  📍 任务描述：用户认证系统
  🎯 检测Phase：P3
  🌿 分支名称：P3/20251001-user-auth-system
  ✅ 成功创建分支

  🤖 Agent策略（4-6-8原则）：
  • 标准任务（6个Agent）：
    - backend-architect, database-specialist
    - test-engineer, security-auditor
    - code-reviewer, documentation-writer
```

### 场景3：架构设计
```
用户: "开始工作流，完整的电商系统架构"

Claude:
  🚀 Phase 0: 自动创建工作分支
  📍 任务描述：完整的电商系统架构
  🎯 检测Phase：P3
  🌿 分支名称：P3/20251001-complete-ecommerce-arch
  ✅ 成功创建分支

  🤖 Agent策略（4-6-8原则）：
  • 复杂任务（8个Agent）：
    - backend-architect, database-specialist
    - security-auditor, performance-engineer
    - test-engineer, api-designer
    - code-reviewer, documentation-writer
```

## 🔧 故障排查

### Phase状态不一致？
```bash
# 运行同步工具
./scripts/sync_phase_state.sh
```

### 测试触发逻辑
```bash
# 运行完整测试
./scripts/test_workflow_trigger.sh
```

### 手动检查状态
```bash
# 查看当前分支
git branch

# 查看Phase状态
cat .phase/current
cat .workflow/ACTIVE
```

## 📝 最佳实践

1. **明确触发**：使用5个触发词之一，清晰表达意图
2. **描述任务**：简短描述任务内容，帮助生成有意义的分支名
3. **Phase匹配**：任务描述中包含Phase关键词（规划/实现/测试等）
4. **复杂度提示**：复杂任务在描述中包含"系统"、"架构"等词

## 🚀 从讨论到执行的流程

```
1. 讨论模式（默认）
   用户: "用户登录功能应该怎么设计？"
   Claude: [分析需求，提供方案建议]
   ↓
   用户: "好的，这个方案不错"
   Claude: [继续讨论细节]
   ↓

2. 切换到执行模式
   用户: "现在开始实现用户登录功能"
   Claude:
   ✅ 创建分支 P3/20251001-user-login
   ✅ 启动工作流
   ✅ 6个Agent并行执行
   ↓

3. 开始实际开发
   [多Agent并行工作]
   [遵循8-Phase流程]
   [质量门禁验证]
```

---

**记住**：
- 💭 讨论时不用触发词 = 保持讨论模式
- 🚀 准备干活时说触发词 = 自动启动工作流
- 简单、清晰、高效！
