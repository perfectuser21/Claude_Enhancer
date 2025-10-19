# Claude Enhancer 四层架构分层系统

## 概述

Claude Enhancer采用清晰的四层架构设计，从底层到上层依次为：**Module（模块层）→ Core（核心层）→ Feature（特性层）→ Main（主控层）**。这种分层设计确保了系统的稳定性、可扩展性和可维护性。

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Main（主控层）                                      │
│  职责: 入口编排，用户配置                                      │
│  修改频率: 高（任何时候）                                      │
│  版本影响: 不影响版本号（配置变更）                             │
└─────────────────────────────────────────────────────────────┘
                         ↓ 调用
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Core（核心层）                                      │
│  职责: 框架规则，系统基础                                      │
│  修改频率: 极低（仅Major版本升级）                              │
│  版本影响: Major (v6→v7)                                     │
│  保护机制: ✅ pre-commit强制检查                               │
└─────────────────────────────────────────────────────────────┘
                         ↓ 被扩展
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Feature（特性层）                                   │
│  职责: 可插拔功能扩展                                          │
│  修改频率: 中等（Minor版本升级）                                │
│  版本影响: Minor (v6.5→v6.6)                                 │
│  注册机制: ✅ registry.yml集中管理                             │
└─────────────────────────────────────────────────────────────┘
                         ↓ 调用
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Module（模块层）                                    │
│  职责: 通用工具，无业务逻辑                                     │
│  修改频率: 高（Patch版本升级）                                  │
│  版本影响: Patch (v6.5.1→v6.5.2)                             │
│  版本追踪: ✅ versions.json记录                                │
└─────────────────────────────────────────────────────────────┘
```

## Layer 1: Main（主控层）

### 定义

**职责**: 系统入口，编排调用其他层，管理用户配置

**位置**: 项目根目录和 `.claude/` 顶层

**典型文件**:
- `CLAUDE.md` - AI行为指令
- `.claude/settings.json` - 系统配置
- `README.md` - 用户文档
- `INSTALLATION.md` - 安装指南

### 修改规则

- **修改频率**: 随时可以修改
- **修改权限**: 用户和AI均可修改
- **版本影响**: 不影响版本号（纯配置变更）
- **审查要求**: 无强制审查（但建议review）

### 示例

```yaml
# settings.json修改示例
{
  "version": "6.5.1",
  "permissions": {
    "bypassPermissionsMode": true  # 用户配置，可随时修改
  }
}
```

## Layer 2: Core（核心层）

### 定义

**职责**: 定义系统核心规则和框架逻辑，是整个系统的基础

**位置**: `.claude/core/`

**典型文件**:
- `phase_definitions.yml` - 6-Phase系统定义
- `workflow_rules.yml` - 11步工作流规则
- `quality_thresholds.yml` - 质量门禁阈值
- `loader.py` - 核心加载器
- `safety.sh` - 安全机制

### 修改规则

- **修改频率**: 极低（仅在Major版本升级时）
- **修改权限**: 需要明确的架构变更决策
- **版本影响**: Major版本升级（如v6→v7）
- **审查要求**: 强制代码审查 + 架构评审
- **保护机制**: ✅ pre-commit hook会检测并警告

### 修改触发条件

Core层只在以下情况下修改：

1. **Phase系统变更**（如从6-Phase改为5-Phase）
2. **工作流核心规则变更**（如质量门禁逻辑重构）
3. **架构重大升级**（如引入新的分层）
4. **安全机制升级**（如加密算法变更）

### 保护机制

```bash
# pre-commit hook会检测Core修改
if [[ "$file" =~ ^.claude/core/ ]]; then
  echo "⚠️  WARNING: Core layer modification detected"
  echo "   File: $file"
  echo "   Core modifications should only happen in Major version upgrades"
  # 在自动模式下允许通过，但记录警告
fi
```

### 示例

```yaml
# phase_definitions.yml（Core文件）
# 修改此文件需要Major版本升级（v6→v7）
phases:
  phase_0:
    name: "Discovery"
    mandatory_output: "Acceptance Checklist"
  phase_1:
    name: "Planning & Architecture"
    mandatory_output: "PLAN.md + Directory Structure"
```

## Layer 3: Feature（特性层）

### 定义

**职责**: 可插拔的功能扩展，增强系统能力但不改变核心逻辑

**位置**: `.claude/features/`, `acceptance/`, 部分hooks

**典型文件**:
- `acceptance/features/*.feature` - BDD场景
- `.claude/features/*/` - 功能模块
- `.claude/hooks/smart_agent_selector.sh` - 智能选择器
- `observability/` - 可观测性配置

### 修改规则

- **修改频率**: 中等（Minor版本升级）
- **修改权限**: Feature Owner或维护者
- **版本影响**: Minor版本升级（如v6.5→v6.6）
- **审查要求**: 代码审查 + 功能测试
- **注册机制**: ✅ 必须在 `registry.yml` 中注册

### Feature注册流程

1. 创建Feature目录和文件
2. 在 `registry.yml` 中注册
3. 添加BDD测试场景
4. 通过Phase 3-4验证
5. 更新Minor版本号

### 示例

```yaml
# .claude/features/registry.yml
features:
  smart_document_loading:
    version: "1.0.0"
    layer: "feature"
    status: "enabled"
    dependencies: ["core.loader"]
    added_in: "6.5.0"

  impact_radius_assessment:
    version: "1.0.0"
    layer: "feature"
    status: "enabled"
    dependencies: ["core.workflow_rules"]
    added_in: "6.5.1"
```

## Layer 4: Module（模块层）

### 定义

**职责**: 通用工具函数，无业务逻辑，完全独立

**位置**: `scripts/`, `.claude/modules/`

**典型文件**:
- `scripts/static_checks.sh` - 静态检查工具
- `scripts/pre_merge_audit.sh` - 合并前审计
- `scripts/check_version_consistency.sh` - 版本一致性检查
- `.claude/modules/` - 通用模块库

### 修改规则

- **修改频率**: 高（Patch版本升级）
- **修改权限**: 任何开发者
- **版本影响**: Patch版本升级（如v6.5.1→v6.5.2）
- **审查要求**: 基础代码审查
- **版本追踪**: ✅ 在 `versions.json` 中记录

### Module版本追踪

```json
// .claude/modules/versions.json
{
  "modules": {
    "static_checks": {
      "version": "2.1.0",
      "last_updated": "2025-10-15",
      "changes": "Added Core protection check"
    },
    "pre_merge_audit": {
      "version": "1.5.0",
      "last_updated": "2025-10-13",
      "changes": "Enhanced version consistency validation"
    }
  }
}
```

### 示例

```bash
# scripts/static_checks.sh（Module文件）
# 修改此文件 → Patch版本升级（v6.5.1→v6.5.2）

# Version: 2.1.0
check_shell_syntax() {
  # 纯工具函数，无业务逻辑
  bash -n "$1"
}
```

## 依赖规则

### 依赖关系图

```
Main ──────┬─────→ Core
           ├─────→ Feature
           └─────→ Module

Core ──────┐
           └─────→ Module  (✅ 允许)
           ✗────→ Feature (❌ 禁止)

Feature ───┬─────→ Core
           └─────→ Module  (✅ 允许)
           ✗────→ Feature (❌ 禁止)

Module ────┘      (完全独立，不依赖任何层)
```

### 依赖规则详解

#### Rule 1: Core不能依赖Feature

**原因**: Core是基础，Feature是扩展。如果Core依赖Feature，会导致循环依赖和系统不稳定。

**错误示例**:
```yaml
# ❌ 错误：Core文件依赖Feature
# .claude/core/workflow_rules.yml
steps:
  step_4:
    name: "Impact Radius Assessment"
    feature: "impact_radius_assessment"  # ❌ Core不应该硬编码Feature名称
```

**正确示例**:
```yaml
# ✅ 正确：Core定义接口，Feature实现
# .claude/core/workflow_rules.yml
steps:
  step_4:
    name: "Pre-Phase-1 Assessment"
    hook_point: "PrePhase1"  # ✅ 定义Hook点，Feature可以注册
```

#### Rule 2: Feature不能互相依赖

**原因**: Feature应该是独立的可插拔模块，互相依赖会导致耦合。

**错误示例**:
```yaml
# ❌ 错误：Feature A依赖Feature B
features:
  feature_a:
    dependencies: ["feature_b"]  # ❌ Feature之间不应该依赖
```

**正确示例**:
```yaml
# ✅ 正确：Feature只依赖Core和Module
features:
  feature_a:
    dependencies: ["core.workflow_rules", "module.static_checks"]
```

#### Rule 3: Module完全独立

**原因**: Module是最底层的工具，必须完全独立才能被所有层调用。

**正确示例**:
```bash
# ✅ 正确：Module函数完全独立
# scripts/check_syntax.sh
check_yaml_syntax() {
  local file="$1"
  python3 -c "import yaml; yaml.safe_load(open('$file'))"
}
```

## 修改工作流

### 修改Core层（Major版本升级）

```
1. 创建新分支: git checkout -b feature/core-upgrade-v7
2. 修改Core文件
3. 更新Major版本: 6.x.x → 7.0.0
4. 完整回归测试（所有BDD场景）
5. 架构评审会议
6. 创建Migration Guide
7. 合并到main
```

### 修改Feature层（Minor版本升级）

```
1. 创建新分支: git checkout -b feature/new-feature
2. 创建/修改Feature文件
3. 在registry.yml中注册
4. 添加BDD测试场景
5. 更新Minor版本: 6.5.x → 6.6.0
6. 代码审查
7. 合并到main
```

### 修改Module层（Patch版本升级）

```
1. 创建新分支: git checkout -b feature/fix-script
2. 修改Module文件
3. 在versions.json中更新版本
4. 更新Patch版本: 6.5.1 → 6.5.2
5. 基础测试
6. 合并到main
```

## 版本管理策略

### 语义化版本规范

```
版本号格式: MAJOR.MINOR.PATCH

MAJOR: Core层修改（破坏性变更）
MINOR: Feature层修改（新增功能）
PATCH: Module层修改（Bug修复、工具优化）
```

### 版本升级示例

| 变更内容 | 当前版本 | 新版本 | 理由 |
|---------|---------|--------|------|
| 修改Phase定义 | 6.5.1 | 7.0.0 | Core层变更 → Major |
| 添加新Feature | 6.5.1 | 6.6.0 | Feature层变更 → Minor |
| 修复脚本bug | 6.5.1 | 6.5.2 | Module层变更 → Patch |
| 更新文档 | 6.5.1 | 6.5.1 | Main层变更 → 不升级 |

## 实践指南

### 如何判断修改属于哪一层？

**决策树**:

```
修改的是什么？
├─ 用户配置、文档 → Main层（不升级版本）
├─ Phase定义、工作流规则 → Core层（Major升级）
├─ BDD场景、新功能 → Feature层（Minor升级）
└─ 脚本工具、Bug修复 → Module层（Patch升级）
```

### 如何避免违反依赖规则？

**检查清单**:

- [ ] Core文件中是否引用了Feature名称？（❌ 禁止）
- [ ] Feature A是否导入Feature B的代码？（❌ 禁止）
- [ ] Module是否调用了Core/Feature的逻辑？（❌ 禁止）
- [ ] 所有依赖都在允许的范围内？（✅ 必须）

### 如何添加新Feature？

**步骤**:

1. 在 `.claude/features/` 创建Feature目录
2. 编写Feature代码
3. 在 `registry.yml` 中注册
4. 添加BDD测试场景到 `acceptance/features/`
5. 运行 `npm run bdd` 验证
6. 更新Minor版本号（如6.5→6.6）
7. 提交PR并通过审查

## FAQ

### Q1: 为什么Core层修改需要Major版本升级？

**A**: Core层定义了系统的基础规则，修改可能导致破坏性变更。按照语义化版本规范，破坏性变更必须升级Major版本，给用户明确的信号。

### Q2: 如果我只是修复Core层的一个小bug，也要升级Major版本吗？

**A**: 不一定。如果修复不改变Core的行为（如修正注释、优化性能），可以Patch升级。但如果修复改变了Core的逻辑（如修改Phase规则），则需要Major升级。

### Q3: Feature之间真的完全不能依赖吗？

**A**: 原则上不能。如果两个Feature确实需要共享逻辑，应该将共享部分提取到Module层，或者考虑将它们合并为一个Feature。

### Q4: Module层的脚本可以调用Core层的配置吗？

**A**: 可以读取Core层的配置文件（如phase_definitions.yml），但不能调用Core层的逻辑代码。Module应该是纯工具，不应该包含业务逻辑。

### Q5: 如何知道某个文件属于哪一层？

**A**: 查看文件路径：
- `/`, `/.claude/` 顶层 → Main
- `/.claude/core/` → Core
- `/.claude/features/`, `/acceptance/` → Feature
- `/scripts/`, `/.claude/modules/` → Module

### Q6: pre-commit hook会阻止Core修改吗？

**A**: 不会硬阻止，但会给出警告。在Bypass Permissions Mode下，系统会记录警告日志但允许提交通过，信任AI的判断。

## 总结

四层架构的核心价值：

1. **稳定性**: Core层受保护，系统基础稳定
2. **扩展性**: Feature层可插拔，灵活添加功能
3. **可维护性**: 清晰的分层和依赖规则，降低维护成本
4. **版本管理**: 与语义化版本完美结合，版本号有意义

**核心原则**:
- Core固定，Feature扩展
- 低层不依赖高层
- 版本号反映变更层级
- 保护机制确保规则执行

---

**文档版本**: 1.0.0
**创建日期**: 2025-10-19
**适用版本**: Claude Enhancer 6.6.0+
