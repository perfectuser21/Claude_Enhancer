# Claude Code 工作流配置

## 🎯 核心工作流：5阶段执行

### Phase 0: Git Setup (分支准备)
- **操作**: `git checkout -b feature/task-name`
- **说明**: 每个任务都在独立分支开发

### Phase 1: Requirements Analysis (需求分析)
- **Agents**: requirements-analyst, product-strategist, business-analyst
- **输出**: 清晰的需求文档
- **并行执行**: 多个分析师同时工作

### Phase 2: Architecture Design (架构设计)
- **Agents**: backend-architect, cloud-architect, database-specialist
- **输出**: 架构设计方案
- **技术选型**: 根据项目特点选择技术栈

### Phase 3: Parallel Development (并行开发)
- **Agents**: 动态选择，基于任务特征
- **输出**: 功能实现代码
- **Git**: 小步提交，频繁保存进度
- **最少3个Agent并行**

### Phase 4: Integration Testing (集成测试)
- **Agents**: test-engineer, e2e-test-specialist, performance-tester
- **输出**: 测试报告和修复
- **Git**: 修复问题后提交

### Phase 5: Deployment Delivery (部署交付)
- **Agents**: devops-engineer, technical-writer, code-reviewer
- **Git流程**:
  1. 最终提交: `git commit -m "feat: 完成功能"`
  2. 推送分支: `git push -u origin feature/task-name`
  3. 创建PR: `gh pr create`
  4. 合并到主分支

## 🔄 动态Agent选择机制

根据任务关键词动态添加专业Agents：

| 任务特征 | 触发关键词 | 动态添加的Agents |
|---------|-----------|-----------------|
| 安全相关 | auth/JWT/加密 | +security-auditor |
| 性能相关 | 优化/缓存/速度 | +performance-engineer |
| 数据相关 | 数据库/SQL | +database-specialist |
| UI相关 | 界面/组件 | +ux-designer |
| 测试相关 | 测试/TDD | +test-engineer |

## ⚠️ 核心规则

### 1. 多Agent并行执行
- **最少Agent数量**: 3个（简单任务）/ 5个（复杂任务）
- **执行方式**: 必须在同一消息中并行调用
- **违规处理**: Hook会强制阻止执行并要求重新操作

### 2. Git工作流规范

#### 分支管理
```bash
# 1. 创建功能分支
git checkout -b feature/login-system

# 2. 开发过程
- 小步提交，每个提交专注一个改动
- 提交前运行测试
- 遵循commit message规范

# 3. 推送到远程
git push -u origin feature/login-system

# 4. 创建PR
gh pr create
```

#### Commit Message规范
```
类型(范围): 简短描述

类型：
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- test: 测试相关
- refactor: 重构代码
- perf: 性能优化
- chore: 维护任务

示例:
feat(auth): 实现JWT登录功能
fix(api): 修复用户查询错误
```

### 3. 质量检查流程
- **代码提交前**: 运行lint和格式化
- **推送前**: 运行测试套件
- **PR前**: 安全扫描和性能检查

### 4. 上下文容量管理（防止killed）
- **Agent数量限制**: 最多7个并行（超过会被阻止）
- **输出汇总**: 自动压缩多Agent输出到2000行内
- **分批执行**: 大任务自动分成多批
- **Context Pool**: 阶段间共享压缩后的上下文

## 📁 项目结构

```
.claude/
├── agents/              # 56个专业Agents
│   ├── development/     # 开发类
│   ├── infrastructure/ # 基础设施
│   ├── quality/        # 质量保证
│   ├── data-ai/        # 数据和AI
│   ├── business/       # 业务分析
│   └── specialized/    # 特殊领域
├── hooks/              # 工作流Hooks
│   ├── pre-task.sh    # 任务前检查
│   ├── workflow.sh    # 工作流管理
│   └── config.yaml    # Hook配置
└── settings.json      # Claude Code配置

.git/hooks/            # Git集成Hooks
├── pre-commit        # 提交前检查
├── commit-msg        # 消息格式验证
└── pre-push         # 推送前验证
```

## 💡 最佳实践

### 深度思考模式
```
UNDERSTAND (30%) → PLAN (20%) → EXECUTE (40%) → VERIFY (10%)
```

### 任务执行流程
1. **理解需求** - 充分理解用户意图
2. **选择Agents** - 至少3个并行
3. **执行开发** - 遵循5阶段工作流
4. **质量保证** - 测试和验证
5. **交付成果** - 完整的解决方案

### 沟通原则
- 使用简单语言解释技术概念
- 显示进度和状态
- 主动提供选项和建议
- 错误时给出解决方案

## 🚀 快速开始

### 新项目
```bash
# 复制配置
cp -r .claude /new-project/

# 开始开发
"创建一个电商网站"
```

### 现有项目增强
```bash
# 只复制agents增强
cp -r .claude/agents /existing-project/.claude/
```

## 📋 Hook配置激活

确保以下Hooks在settings.json中配置：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "type": "command",
        "command": ".claude/hooks/pre-task.sh"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "type": "command",
        "command": ".claude/hooks/quality-check.sh"
      }
    ]
  }
}
```

---
*通过Hook和Agent配置实现软件工程最佳实践*