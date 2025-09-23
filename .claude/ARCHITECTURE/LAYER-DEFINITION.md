# Claude Enhancer 层级定义详解

## 📐 层级架构图

```
┌─────────────────────────────────────────────┐
│            L3: Features (60%+)              │ ← 快速变化
│  basic/ | standard/ | advanced/             │   每天都可能新增
├─────────────────────────────────────────────┤
│            L2: Services (20%)               │ ← 中速变化
│  validation/ | formatting/ | analysis/      │   每周可能优化
├─────────────────────────────────────────────┤
│           L1: Framework (15%)               │ ← 缓慢变化
│    workflow/ | strategies/ | hooks/         │   每月可能调整
├─────────────────────────────────────────────┤
│             L0: Core (5%)                   │ ← 极少变化
│        engine.py | orchestrator.py          │   每年可能重构
└─────────────────────────────────────────────┘
         ↑                      ↑
      最稳定                最灵活
```

## 🔍 L0: Core Layer（内核层）

### 定义
系统的心脏，包含最基础、最稳定的核心逻辑。

### 包含内容
```
core/
├── engine.py           # 8-Phase工作流引擎
├── orchestrator.py     # Agent协调器
├── loader.py          # 模块加载器
└── config.yaml        # 核心配置
```

### 设计准则
- **最小化原则**：只包含绝对必要的代码
- **零依赖原则**：不依赖任何上层代码
- **稳定性原则**：API几乎永不改变

### 代码示例
```python
# core/engine.py
class WorkflowEngine:
    """核心工作流引擎，永恒不变的执行逻辑"""
    def execute_phase(self, phase_id: int):
        # 核心执行逻辑
        pass
```

## 🔧 L1: Framework Layer（框架层）

### 定义
在Core之上构建的主要工作框架，定义了系统的工作模式。

### 包含内容
```
framework/
├── workflow/
│   ├── phase0_branch.py      # Phase 0: 分支管理
│   ├── phase1_analysis.py    # Phase 1: 需求分析
│   ├── phase2_design.py       # Phase 2: 设计规划
│   ├── phase3_implement.py    # Phase 3: 实现开发
│   ├── phase4_test.py         # Phase 4: 本地测试
│   ├── phase5_commit.py       # Phase 5: 代码提交
│   ├── phase6_review.py       # Phase 6: 代码审查
│   └── phase7_deploy.py       # Phase 7: 合并部署
├── strategies/
│   ├── agent_468.yaml         # 4-6-8 Agent策略
│   └── smart_selector.py      # 智能选择器
└── hooks/
    ├── pre_commit.sh          # 提交前检查
    └── pre_push.sh            # 推送前验证
```

### 设计准则
- **标准化原则**：提供统一的工作模式
- **可配置原则**：通过配置调整行为
- **框架性原则**：定义结构，不限制实现

## 🛠️ L2: Services Layer（服务层）

### 定义
提供可复用的服务组件，被Features层调用。

### 包含内容
```
services/
├── validation/
│   ├── code_validator.py     # 代码验证
│   ├── security_checker.py   # 安全检查
│   └── quality_analyzer.py   # 质量分析
├── formatting/
│   ├── code_formatter.py     # 代码格式化
│   ├── doc_generator.py      # 文档生成
│   └── report_builder.py     # 报告构建
├── analysis/
│   ├── complexity.py         # 复杂度分析
│   ├── performance.py        # 性能分析
│   └── dependencies.py       # 依赖分析
└── utils/
    ├── file_ops.py           # 文件操作
    ├── git_helper.py         # Git辅助
    └── logger.py             # 日志工具
```

### 设计准则
- **服务化原则**：每个模块是独立服务
- **无状态原则**：服务不保存状态
- **通用性原则**：可被任何Feature使用

## 🚀 L3: Features Layer（特性层）

### 定义
所有具体功能实现，系统的主要价值所在。

### 三级分类

#### Basic Features（基础特性）
**特点**：简单、独立、单文件
```
features/basic/
├── quick_fix.py              # 快速修复
├── auto_format.py            # 自动格式化
├── simple_check.py           # 简单检查
└── git_helper.py             # Git辅助
```

#### Standard Features（标准特性）
**特点**：中等复杂、有组织、文件夹结构
```
features/standard/
├── agents/                   # Agent系统
│   ├── registry.py          # 注册中心
│   ├── loader.py            # 加载器
│   └── library/             # Agent库
│       ├── development/     # 开发类
│       ├── testing/         # 测试类
│       └── deployment/      # 部署类
├── testing/                  # 测试框架
│   ├── unit/               # 单元测试
│   ├── integration/        # 集成测试
│   └── e2e/                # 端到端测试
└── documentation/           # 文档系统
    ├── generator/          # 生成器
    └── templates/          # 模板
```

#### Advanced Features（高级特性）
**特点**：复杂系统、内部分层、独立架构
```
features/advanced/
├── ai_workflow/             # AI工作流系统
│   ├── core/               # AI核心
│   │   ├── engine.py      # AI引擎
│   │   └── models.py      # AI模型
│   ├── main/               # 主要功能
│   │   ├── assistant.py   # AI助手
│   │   └── analyzer.py    # AI分析
│   └── modules/            # 辅助模块
│       ├── prompts/       # 提示词
│       └── training/      # 训练
└── deployment_platform/     # 部署平台
    ├── core/               # 部署核心
    ├── main/               # 主要功能
    └── modules/            # 辅助模块
```

### Feature成长路径
```
1. 开始：basic/my_tool.py (10行)
   ↓
2. 增长：standard/my_tool/ (100行)
   - my_tool.py
   - config.yaml
   - utils.py
   ↓
3. 成熟：advanced/my_platform/
   - core/
   - main/
   - modules/
```

## 🔗 层级间的依赖规则

### 允许的依赖
```
L3 → L2 ✅ (Features可以调用Services)
L3 → L1 ✅ (Features可以使用Framework)
L3 → L0 ✅ (Features可以访问Core)
L2 → L1 ✅ (Services可以使用Framework)
L2 → L0 ✅ (Services可以访问Core)
L1 → L0 ✅ (Framework依赖Core)
```

### 禁止的依赖
```
L0 → L1/L2/L3 ❌ (Core不能依赖上层)
L1 → L2/L3 ❌ (Framework不能依赖上层)
L2 → L3 ❌ (Services不能依赖Features)
```

### 同层依赖
```
L3 ↔ L3 ✅ (Features之间可以互相调用)
L2 ↔ L2 ✅ (Services之间可以互相调用)
L1 ↔ L1 ⚠️ (Framework组件间谨慎依赖)
L0 ↔ L0 ⚠️ (Core组件间最小依赖)
```

## 📊 层级容量预期

| 层级 | 当前 | 6个月后 | 1年后 | 2年后 |
|------|------|---------|-------|-------|
| L0 Core | 4文件 | 4文件 | 5文件 | 5文件 |
| L1 Framework | 15文件 | 20文件 | 25文件 | 30文件 |
| L2 Services | 30文件 | 50文件 | 80文件 | 120文件 |
| L3 Features | 60文件 | 150文件 | 300文件 | 600文件 |

## 🎯 设计哲学

> **稳定的核心，灵活的外围**
>
> L0-L1提供坚实的基础，
> L2提供丰富的工具，
> L3实现无限的可能。

---
*层级定义版本：v2.0*
*最后更新：2025-09-23*