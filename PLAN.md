# 四层架构分层系统实现计划

## 项目概述

**任务目标**: 为Claude Enhancer建立清晰的四层架构分层系统（Main/Core/Feature/Module），固化核心逻辑，支持灵活扩展。

**版本**: 6.5.1 → 6.6.0（Minor版本升级，新增架构分层功能）

**Impact Radius**: 65分（high-risk）→ 使用6个专业Agent并行

## 架构设计

### 四层架构定义

```
┌─────────────────────────────────────────────┐
│  Layer 1: Main（主控层）                     │
│  - 职责: 入口编排，调用其他层                 │
│  - 位置: /, .claude/                         │
│  - 示例: CLAUDE.md, settings.json           │
│  - 修改权限: 任何时候（用户配置）              │
└─────────────────────────────────────────────┘
              ↓ 调用
┌─────────────────────────────────────────────┐
│  Layer 2: Core（核心层）                     │
│  - 职责: 框架规则，系统核心逻辑                │
│  - 位置: .claude/core/                       │
│  - 示例: phase_definitions.yml, loader.py   │
│  - 修改权限: 仅Major版本升级（如v6→v7）        │
│  - 保护机制: pre-commit hook强制检查          │
└─────────────────────────────────────────────┘
              ↓ 被扩展
┌─────────────────────────────────────────────┐
│  Layer 3: Feature（特性层）                  │
│  - 职责: 可插拔的功能扩展                     │
│  - 位置: .claude/features/, acceptance/     │
│  - 示例: BDD场景，检查项，智能加载             │
│  - 修改权限: Minor版本升级（如v6.5→v6.6）      │
│  - 注册机制: registry.yml集中管理             │
└─────────────────────────────────────────────┘
              ↓ 调用
┌─────────────────────────────────────────────┐
│  Layer 4: Module（模块层）                   │
│  - 职责: 通用工具，无业务逻辑                  │
│  - 位置: scripts/, .claude/modules/         │
│  - 示例: 静态检查，版本验证，清理脚本           │
│  - 修改权限: Patch版本升级（如v6.5.1→v6.5.2）  │
│  - 版本追踪: versions.json记录               │
└─────────────────────────────────────────────┘
```

### 依赖规则

```yaml
依赖关系:
  Main:
    can_depend_on: [Core, Feature, Module]
    description: "主控层可以调用任何层"

  Core:
    can_depend_on: [Module]
    cannot_depend_on: [Feature]
    description: "核心层只能依赖Module，不能依赖Feature（保持核心纯粹）"

  Feature:
    can_depend_on: [Core, Module]
    cannot_depend_on: [Feature]
    description: "Feature可以依赖Core和Module，但Feature之间不互相依赖"

  Module:
    can_depend_on: []
    description: "Module完全独立，不依赖任何层（最底层）"
```

## 实现计划

### Phase 1: 规划与架构（当前）

**产出**:
- PLAN.md（本文件）
- 目录结构设计
- 文件清单

**目录结构**:
```
.claude/
├── ARCHITECTURE_LAYERS.md          # 新增：四层架构完整文档
├── core/
│   ├── phase_definitions.yml       # 新增：6-Phase系统定义
│   ├── workflow_rules.yml          # 新增：11步工作流规则
│   ├── quality_thresholds.yml      # 新增：质量阈值
│   ├── loader.py                   # 现有：懒加载优化器
│   └── ...（其他现有core文件）
├── features/
│   ├── registry.yml                # 新增：Feature注册表
│   ├── basic/                      # 现有
│   ├── standard/                   # 现有
│   └── advanced/                   # 现有
└── modules/
    └── versions.json               # 新增：Module版本追踪

scripts/                            # Module层
├── static_checks.sh               # 现有
├── pre_merge_audit.sh            # 现有
└── check_version_consistency.sh  # 现有

.git/hooks/
└── pre-commit                     # 修改：添加Core保护机制
```

### Phase 2: 实现

**任务分解**:

1. **创建Core层定义文件**（api-designer负责）
   - phase_definitions.yml: 定义Phase 0-5的详细规则
   - workflow_rules.yml: 定义11步工作流的转折点
   - quality_thresholds.yml: 定义质量门禁的阈值

2. **创建Feature注册表**（system-architect负责）
   - registry.yml: 注册所有现有Features
   - 定义Feature元数据（版本、依赖、启用状态）

3. **创建Module版本追踪**（devops-engineer负责）
   - versions.json: 记录所有Module的版本
   - 定义Module更新规则

4. **编写架构文档**（technical-writer负责）
   - ARCHITECTURE_LAYERS.md: 完整的四层架构文档
   - 包含：定义、规则、示例、FAQ

5. **修改保护机制**（devops-engineer负责）
   - 在pre-commit中添加Core保护检查
   - 符合Bypass Permissions Mode要求

6. **代码审查**（code-reviewer负责）
   - 验证所有配置文件格式
   - 确保文档完整性

### Phase 3: 测试验证

**测试项**:
1. YAML/JSON文件语法验证
2. Core保护机制功能测试
3. 版本一致性检查
4. 依赖规则验证

### Phase 4: 代码审查

**审查重点**:
1. 配置文件的完整性和正确性
2. 文档的清晰度和准确性
3. 保护机制的有效性
4. 与现有系统的兼容性

### Phase 5: 发布与监控

**发布清单**:
1. 更新VERSION: 6.5.1 → 6.6.0
2. 更新CHANGELOG.md
3. 更新settings.json
4. 创建git tag
5. 验收清单对照

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|-----|------|---------|
| Core定义过于严格 | 限制灵活性 | 提供Feature扩展机制 |
| 保护机制阻碍开发 | 开发效率降低 | 支持Bypass Mode，重大升级时可临时禁用 |
| 现有文件分类混乱 | 实施困难 | 先建立分层规则，再逐步迁移 |
| 版本号冲突 | 版本管理混乱 | 使用统一的版本一致性检查 |

## 技术决策

### 决策1: Core层修改权限

**选择**: 仅在Major版本升级时允许修改Core

**理由**:
- Core层是系统基础，频繁修改会导致不稳定
- Major版本允许Breaking Changes，符合语义化版本规范
- 通过Feature层扩展可以满足大部分需求

### 决策2: 保护机制实现方式

**选择**: 在pre-commit中添加检查，支持自动模式bypass

**理由**:
- 符合现有的Bypass Permissions Mode设计
- 不阻碍自动化流程
- 给用户明确的警告信息

### 决策3: 配置文件格式

**选择**: YAML用于定义类配置，JSON用于数据追踪

**理由**:
- YAML更易读，适合人工编辑（phase_definitions.yml）
- JSON更规范，适合程序解析（versions.json）
- 符合业界最佳实践

## Agent分工

| Agent | 职责 | 产出 |
|-------|------|------|
| technical-writer | 编写ARCHITECTURE_LAYERS.md | 完整架构文档 |
| requirements-analyst | 分析需求，创建PLAN.md | 本文件 |
| api-designer | 设计Core层配置文件 | 3个yml文件 |
| system-architect | 设计Feature注册机制 | registry.yml |
| devops-engineer | 修改Hook，创建Module追踪 | 更新的pre-commit + versions.json |
| code-reviewer | 审查所有产出 | REVIEW.md |

## 时间估计

- Phase 0: 已完成（30分钟）
- Phase 1: 进行中（20分钟）
- Phase 2: 预计40分钟（6个Agent并行）
- Phase 3: 预计15分钟
- Phase 4: 预计20分钟
- Phase 5: 预计10分钟

**总计**: 约2.5小时

## 验收标准

参考Phase 0创建的Acceptance Checklist，所有项必须✅才能完成。

---

**规划完成**: 准备进入Phase 2实现阶段
