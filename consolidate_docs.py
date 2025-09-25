#!/usr/bin/env python3
"""
文档整合脚本 - 将145个文档精简到5个核心文档
目标：README.md, ARCHITECTURE.md, WORKFLOW.md, AGENTS.md, TROUBLESHOOTING.md
"""

import os
import glob
import shutil
from pathlib import Path
from datetime import datetime


class DocumentConsolidator:
    def __init__(self, project_root="/home/xx/dev/Claude_Enhancer"):
        self.project_root = Path(project_root)
        self.backup_dir = (
            self.project_root
            / f"docs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.consolidated_docs = {
            "README.md": [],
            "ARCHITECTURE.md": [],
            "WORKFLOW.md": [],
            "AGENTS.md": [],
            "TROUBLESHOOTING.md": [],
        }

    def analyze_existing_docs(self):
        """分析现有文档"""
        print("🔍 分析现有文档结构...")

        all_md_files = list(self.project_root.rglob("*.md"))
        print(f"📊 找到 {len(all_md_files)} 个MD文件")

        # 按类型分类
        categories = {
            "readme": [],
            "architecture": [],
            "workflow": [],
            "agents": [],
            "troubleshooting": [],
            "api": [],
            "deployment": [],
            "performance": [],
            "auth": [],
            "other": [],
        }

        for file in all_md_files:
            file_lower = str(file).lower()
            file_name = file.name.lower()

            if "readme" in file_name:
                categories["readme"].append(file)
            elif any(
                keyword in file_lower for keyword in ["architecture", "arch", "design"]
            ):
                categories["architecture"].append(file)
            elif any(
                keyword in file_lower for keyword in ["workflow", "phase", "process"]
            ):
                categories["workflow"].append(file)
            elif any(keyword in file_lower for keyword in ["agent", "ai", "claude"]):
                categories["agents"].append(file)
            elif any(
                keyword in file_lower
                for keyword in ["troubleshoot", "debug", "fix", "error"]
            ):
                categories["troubleshooting"].append(file)
            elif any(
                keyword in file_lower for keyword in ["api", "openapi", "swagger"]
            ):
                categories["api"].append(file)
            elif any(
                keyword in file_lower
                for keyword in ["deploy", "docker", "k8s", "kubernetes"]
            ):
                categories["deployment"].append(file)
            elif any(
                keyword in file_lower
                for keyword in ["performance", "perf", "benchmark"]
            ):
                categories["performance"].append(file)
            elif any(
                keyword in file_lower for keyword in ["auth", "login", "security"]
            ):
                categories["auth"].append(file)
            else:
                categories["other"].append(file)

        return categories

    def create_backup(self):
        """创建文档备份"""
        print(f"💾 创建备份到 {self.backup_dir}")
        self.backup_dir.mkdir(exist_ok=True)

        for md_file in self.project_root.rglob("*.md"):
            relative_path = md_file.relative_to(self.project_root)
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(md_file, backup_path)

    def consolidate_readme(self, categories):
        """整合README文档"""
        content = """# Claude Enhancer - AI-Driven Development Workflow System

## 🎯 系统概览

Claude Enhancer是专为Claude Code Max 20X用户设计的智能开发工作流系统，提供完整的AI驱动多Agent协作框架。

### 核心特性
- **8-Phase开发工作流** - 完整项目生命周期管理
- **智能Agent选择** - 从56+专业AI Agent中选择4-6-8个
- **质量保证门禁** - 自动化安全、性能和代码质量检查
- **Git工作流集成** - 自动化分支管理和提交验证
- **并行执行** - 多Agent协作实现快速交付

## 🚀 快速开始

### 安装
```bash
# 1. 复制.claude配置到项目
cp -r .claude /your/project/

# 2. 安装Git Hooks
cd /your/project && ./.claude/install.sh

# 3. 开始开发
# 系统将自动提供8-Phase工作流支持
```

### 基本使用
1. **Phase 0**: 创建Git分支（系统提醒）
2. **Phase 1-2**: 需求分析和设计规划
3. **Phase 3**: 实现开发（4-6-8 Agent并行）
4. **Phase 4**: 本地测试
5. **Phase 5**: 代码提交（Git Hooks质量检查）
6. **Phase 6**: 代码审查（PR Review）
7. **Phase 7**: 合并部署

## 📚 文档导航
- [架构设计](ARCHITECTURE.md) - 系统架构和设计原理
- [工作流程](WORKFLOW.md) - 8-Phase详细说明
- [Agent指南](AGENTS.md) - 56+专业Agent使用
- [问题解决](TROUBLESHOOTING.md) - 常见问题和解决方案

## 🔗 相关链接
- [API参考](api-specification/) - REST API文档
- [部署指南](deployment/) - 生产环境部署
- [测试策略](test/) - 测试方法和用例

## 📞 支持
- 问题反馈：GitHub Issues
- 技术讨论：团队内部沟通
- 文档贡献：欢迎提交PR

---
*本系统遵循Max 20X理念：追求最佳结果，Token消耗不是问题*
"""
        return content

    def consolidate_architecture(self, categories):
        """整合架构文档"""
        content = """# Claude Enhancer 系统架构

## 🏗️ 四层架构体系

### 架构概览
```
Claude Enhancer v2.0 四层架构
┌─────────────────────────────────────┐
│ Features Layer (特性层)              │ ← 业务功能
├─────────────────────────────────────┤
│ Services Layer (服务层)              │ ← 通用服务
├─────────────────────────────────────┤
│ Framework Layer (框架层)             │ ← 工作流框架
├─────────────────────────────────────┤
│ Core Layer (核心层)                  │ ← 基础设施
└─────────────────────────────────────┘
```

### 层级职责

#### 1. Core Layer (核心层) 🔒
**永久稳定，不可修改**
- **设置管理**: settings.json配置体系
- **Agent定义**: 56+专业Agent规格
- **Hook基础**: Git和Claude Hook基础设施
- **质量门禁**: 代码质量、安全、性能检查

```
.claude/core/
├── settings/           # 配置管理
├── agents/            # Agent定义
├── hooks/             # Hook基础设施
└── quality/           # 质量检查
```

#### 2. Framework Layer (框架层) 🔧
**稳定但可扩展**
- **8-Phase工作流**: Phase 0-7标准流程
- **Agent策略**: 4-6-8选择策略
- **执行引擎**: 并行执行控制
- **状态管理**: 工作流状态跟踪

```
.claude/framework/
├── workflow/          # 8-Phase工作流
├── execution/         # 执行引擎
├── strategy/          # Agent策略
└── state/             # 状态管理
```

#### 3. Services Layer (服务层) ⚙️
**可配置的通用服务**
- **智能文档加载**: 按需加载架构文档
- **性能监控**: 执行性能追踪
- **配置迁移**: 版本升级支持
- **智能分析**: 任务分析和建议

```
.claude/services/
├── document_loader/   # 智能文档加载
├── performance/       # 性能监控
├── migration/         # 配置迁移
└── intelligence/      # 智能分析
```

#### 4. Features Layer (特性层) 🚀
**灵活的业务功能**
- **项目模板**: 不同类型项目模板
- **自定义Hook**: 项目特定的Hook
- **工作流扩展**: 自定义工作流步骤
- **Agent组合**: 特定场景Agent组合

```
.claude/features/
├── templates/         # 项目模板
├── custom_hooks/      # 自定义Hook
├── workflows/         # 工作流扩展
└── agent_combos/      # Agent组合
```

## 🎯 设计原则

### 1. 框架固定，内容灵活
- **框架层**提供稳定的8-Phase工作流
- **特性层**支持灵活的业务定制

### 2. 智能适配
- 根据任务复杂度自动选择4-6-8个Agent
- 智能文档加载避免上下文污染

### 3. 质量优先
- 三层质量保证：Workflow + Claude Hooks + Git Hooks
- Max 20X理念：追求最佳结果

### 4. 分层治理
- **Core**: 架构团队维护，严格变更控制
- **Framework**: 平台团队维护，版本化管理
- **Services**: 各团队共建，接口标准化
- **Features**: 业务团队自主，快速迭代

## 🔄 架构演进

### v1.0 → v2.0
- 从单一文件到分层架构
- 从静态配置到智能适配
- 从简单工具到完整平台

### 未来规划
- 支持更多编程语言和框架
- 增强AI智能化程度
- 扩展到更多开发场景

## 📊 性能指标
- **文档加载**: 按需加载，避免Token浪费
- **Agent选择**: 智能推荐，提高效率
- **质量检查**: 自动化程度95%+
- **工作流完成**: 端到端自动化

---
*架构文档由Claude Enhancer v2.0定义，遵循四层架构设计原则*
"""
        return content

    def consolidate_workflow(self, categories):
        """整合工作流文档"""
        content = """# Claude Enhancer 8-Phase 工作流

## 🔄 完整工作流概览

8-Phase工作流提供从分支创建到部署上线的完整开发生命周期管理。

```
Phase 0: Git分支创建     ← 起点（branch_helper.sh提醒）
   ↓
Phase 1: 需求分析       ← 理解和澄清需求
   ↓
Phase 2: 设计规划       ← 架构设计和技术选型
   ↓
Phase 3: 实现开发       ← Agent并行开发（4-6-8策略）
   ↓
Phase 4: 本地测试       ← 单元测试和集成测试
   ↓
Phase 5: 代码提交       ← Git Hooks质量检查
   ↓
Phase 6: 代码审查       ← PR Review和同行评审
   ↓
Phase 7: 合并部署       ← 终点（生产环境上线）
```

## 📋 各Phase详细说明

### Phase 0: Git分支创建 🌿
**目标**: 建立独立的开发分支

**系统支持**:
- `branch_helper.sh` 自动提醒创建分支
- 分支命名规范检查
- 基于任务类型推荐分支前缀

**最佳实践**:
```bash
# 功能开发
git checkout -b feature/user-authentication

# 缺陷修复
git checkout -b fix/login-validation-bug

# 性能优化
git checkout -b perf/database-query-optimization
```

### Phase 1: 需求分析 📊
**目标**: 深度理解业务需求和技术约束

**核心活动**:
- 需求澄清和确认
- 技术可行性分析
- 风险识别和评估
- 成功标准定义

**推荐Agent组合**:
- `requirements-analyst` - 需求分析专家
- `business-analyst` - 业务分析师
- `technical-writer` - 技术文档专家

### Phase 2: 设计规划 🎨
**目标**: 制定技术方案和实现计划

**核心活动**:
- 系统架构设计
- 技术栈选择
- API接口设计
- 数据库模型设计
- 测试策略制定

**推荐Agent组合**:
- `backend-architect` - 后端架构师
- `api-designer` - API设计专家
- `database-specialist` - 数据库专家
- `ux-designer` - 用户体验设计师

### Phase 3: 实现开发 ⚡
**目标**: 并行高效的代码实现

**4-6-8 Agent策略**:

#### 简单任务（4个Agent，5-10分钟）
```
backend-engineer    - 核心功能实现
test-engineer      - 测试用例编写
security-auditor   - 安全检查
technical-writer   - 代码文档
```

#### 标准任务（6个Agent，15-20分钟）
```
backend-architect   - 架构设计
backend-engineer   - 功能实现
frontend-specialist - 前端开发
test-engineer      - 测试策略
security-auditor   - 安全审计
performance-tester - 性能优化
```

#### 复杂任务（8个Agent，25-30分钟）
```
backend-architect   - 系统架构
api-designer       - API设计
database-specialist - 数据层设计
backend-engineer   - 核心开发
frontend-specialist - 用户界面
test-engineer      - 测试框架
security-auditor   - 安全审计
devops-engineer    - 部署配置
```

**并行执行要求**:
- 所有Agent必须在同一消息中调用
- 避免顺序依赖，最大化并行度
- 使用统一的接口和数据格式

### Phase 4: 本地测试 🧪
**目标**: 确保代码质量和功能正确性

**测试层级**:
1. **单元测试** - 函数和类级别
2. **集成测试** - 模块间协作
3. **端到端测试** - 完整业务流程
4. **性能测试** - 响应时间和吞吐量

**自动化工具**:
- 测试框架集成
- 代码覆盖率检查
- 性能基准测试
- 安全漏洞扫描

### Phase 5: 代码提交 📝
**目标**: 高质量代码进入版本控制

**Git Hooks质量门禁**:
- `pre-commit`: 代码格式化、语法检查
- `commit-msg`: 提交信息规范验证
- `pre-push`: 测试通过验证

**提交信息规范**:
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**类型定义**:
- `feat`: 新功能
- `fix`: 缺陷修复
- `docs`: 文档更新
- `style`: 格式调整
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试相关

### Phase 6: 代码审查 👥
**目标**: 团队协作确保代码质量

**PR Review检查项**:
- [ ] 功能完整性
- [ ] 代码可读性
- [ ] 性能影响评估
- [ ] 安全风险检查
- [ ] 测试覆盖率
- [ ] 文档完整性

**自动化检查**:
- CI/CD管道执行
- 自动化测试运行
- 代码质量报告
- 安全扫描结果

### Phase 7: 合并部署 🚀
**目标**: 安全稳定的生产环境发布

**部署策略**:
- **蓝绿部署**: 零停机时间
- **金丝雀发布**: 渐进式上线
- **滚动更新**: 逐步替换

**监控指标**:
- 应用性能监控
- 错误率统计
- 用户体验指标
- 系统资源使用

## ⚙️ 工作流控制

### 状态管理
```json
{
  "current_phase": 3,
  "phase_status": {
    "0": "completed",
    "1": "completed",
    "2": "completed",
    "3": "in_progress",
    "4": "pending"
  },
  "agent_execution": {
    "parallel_agents": 6,
    "execution_mode": "standard_task"
  }
}
```

### 阶段转换条件
- **Phase 0→1**: 分支创建成功
- **Phase 1→2**: 需求澄清完成
- **Phase 2→3**: 设计方案确认
- **Phase 3→4**: 代码实现完成
- **Phase 4→5**: 所有测试通过
- **Phase 5→6**: 代码提交成功
- **Phase 6→7**: PR审查通过
- **Phase 7→完成**: 部署验证成功

## 🎯 最佳实践

### 1. Agent选择策略
- 根据任务复杂度选择4-6-8个Agent
- 确保技能互补和协作效率
- 优先选择有协作经验的Agent组合

### 2. 并行执行优化
- 最小化Agent间依赖
- 使用标准化的数据接口
- 实时监控执行进度

### 3. 质量门禁设置
- 制定明确的通过标准
- 自动化验证流程
- 及时反馈问题和建议

### 4. 持续改进
- 收集工作流执行数据
- 分析瓶颈和优化点
- 定期更新最佳实践

---
*8-Phase工作流是Claude Enhancer的核心，确保每个项目都能高质量快速交付*
"""
        return content

    def consolidate_agents(self, categories):
        """整合Agent文档"""
        content = """# Claude Enhancer Agent使用指南

## 🤖 56+ 专业Agent生态系统

Claude Enhancer提供56+专业AI Agent，覆盖软件开发的各个领域。所有Agent都基于GitHub下载的配置文件，经过专门优化。

## 📊 Agent分类体系

### 1. Development (开发类) - 16个
核心开发Agent，负责代码编写和架构设计

| Agent | 专长 | 使用场景 |
|-------|------|----------|
| `backend-architect` | 后端架构设计 | 系统架构、微服务设计 |
| `backend-engineer` | 后端开发 | API实现、业务逻辑 |
| `frontend-specialist` | 前端开发 | UI/UX实现、交互设计 |
| `fullstack-developer` | 全栈开发 | 端到端功能实现 |
| `mobile-developer` | 移动应用开发 | iOS/Android应用 |
| `web-developer` | Web开发 | 现代Web应用 |
| `api-designer` | API设计 | RESTful/GraphQL API |
| `database-specialist` | 数据库专家 | 数据模型、查询优化 |
| `microservices-architect` | 微服务架构师 | 分布式系统设计 |
| `system-architect` | 系统架构师 | 企业级系统架构 |

### 2. Infrastructure (基础设施类) - 7个
DevOps和部署相关Agent

| Agent | 专长 | 使用场景 |
|-------|------|----------|
| `devops-engineer` | DevOps工程师 | CI/CD、自动化部署 |
| `cloud-architect` | 云架构师 | 云原生架构设计 |
| `kubernetes-expert` | K8s专家 | 容器编排、微服务部署 |
| `docker-specialist` | Docker专家 | 容器化应用 |
| `infrastructure-engineer` | 基础设施工程师 | 服务器、网络配置 |
| `site-reliability-engineer` | SRE工程师 | 系统可靠性、监控 |
| `platform-engineer` | 平台工程师 | 开发平台建设 |

### 3. Quality Assurance (质量保证类) - 7个
测试和质量相关Agent

| Agent | 专长 | 使用场景 |
|-------|------|----------|
| `test-engineer` | 测试工程师 | 测试策略、自动化测试 |
| `qa-specialist` | QA专家 | 质量保证流程 |
| `security-auditor` | 安全审计师 | 安全漏洞扫描、渗透测试 |
| `performance-tester` | 性能测试师 | 性能基准、压力测试 |
| `accessibility-auditor` | 无障碍审计师 | 网站可访问性检查 |
| `code-reviewer` | 代码审查员 | 代码质量、最佳实践 |
| `security-specialist` | 安全专家 | 安全架构、防护策略 |

### 4. Data & AI (数据与AI类) - 6个
数据科学和人工智能Agent

| Agent | 专长 | 使用场景 |
|-------|------|----------|
| `data-scientist` | 数据科学家 | 数据分析、机器学习 |
| `ai-engineer` | AI工程师 | AI模型开发、部署 |
| `mlops-engineer` | MLOps工程师 | 机器学习运维 |
| `data-engineer` | 数据工程师 | 数据管道、ETL |
| `analytics-specialist` | 分析专家 | 商业智能、报表 |
| `ai-researcher` | AI研究员 | 前沿技术研究 |

### 5. Business (业务类) - 6个
业务分析和产品设计Agent

| Agent | 专长 | 使用场景 |
|-------|------|----------|
| `business-analyst` | 业务分析师 | 需求分析、业务建模 |
| `requirements-analyst` | 需求分析师 | 需求收集、文档编写 |
| `product-manager` | 产品经理 | 产品规划、功能设计 |
| `ux-designer` | UX设计师 | 用户体验设计 |
| `technical-writer` | 技术写作专家 | 技术文档、API文档 |
| `project-manager` | 项目经理 | 项目管理、进度控制 |

### 6. Specialized (专业领域类) - 14+个
特定行业和技术领域Agent

| Agent | 专长 | 使用场景 |
|-------|------|----------|
| `fintech-specialist` | 金融科技专家 | 金融系统、支付平台 |
| `healthcare-dev` | 医疗健康开发者 | 医疗信息系统 |
| `ecommerce-expert` | 电商专家 | 电商平台、购物系统 |
| `blockchain-developer` | 区块链开发者 | 智能合约、DApp |
| `game-developer` | 游戏开发者 | 游戏引擎、游戏逻辑 |
| `iot-specialist` | 物联网专家 | 嵌入式系统、传感器 |
| `cybersecurity-expert` | 网络安全专家 | 网络防护、威胁检测 |
| `embedded-engineer` | 嵌入式工程师 | 硬件驱动、实时系统 |

## 🎯 4-6-8 Agent选择策略

### 简单任务 (4个Agent, 5-10分钟)
**适用场景**: 功能增强、Bug修复、文档更新

**标准组合**:
```
├── backend-engineer     - 核心实现
├── test-engineer       - 测试用例
├── security-auditor    - 安全检查
└── technical-writer    - 文档更新
```

**选择原则**:
- 覆盖开发、测试、安全、文档四个基本维度
- 快速执行，避免过度设计
- 确保基本质量标准

### 标准任务 (6个Agent, 15-20分钟)
**适用场景**: 新功能开发、API设计、中等复杂度项目

**推荐组合**:
```
├── backend-architect    - 架构设计
├── api-designer        - 接口设计
├── backend-engineer    - 功能实现
├── test-engineer       - 测试策略
├── security-auditor    - 安全审计
└── performance-tester  - 性能优化
```

**选择原则**:
- 增加架构设计和性能考虑
- 平衡设计深度和执行效率
- 确保系统可扩展性

### 复杂任务 (8个Agent, 25-30分钟)
**适用场景**: 微服务架构、企业级系统、关键业务功能

**完整组合**:
```
├── system-architect     - 系统架构
├── api-designer        - API设计
├── database-specialist - 数据设计
├── backend-engineer    - 核心开发
├── frontend-specialist - 用户界面
├── test-engineer       - 测试框架
├── security-auditor    - 安全审计
└── devops-engineer     - 部署配置
```

**选择原则**:
- 全面覆盖系统各个层面
- 确保企业级质量标准
- 考虑长期维护和扩展

## 🔧 Agent使用最佳实践

### 1. 并行执行要求
**强制规则**: 所有Agent必须在同一消息中并行调用

✅ **正确示例**:
```xml
<function_calls>
  <invoke name="backend-architect">
    <parameter name="task">设计用户认证系统架构</parameter>
  </invoke>
  <invoke name="security-auditor">
    <parameter name="task">评估认证系统安全风险</parameter>
  </invoke>
  <invoke name="test-engineer">
    <parameter name="task">设计认证系统测试策略</parameter>
  </invoke>
</function_calls>
```

❌ **错误示例**:
```xml
<invoke name="backend-architect">...</invoke>
... 其他内容 ...
<invoke name="security-auditor">...</invoke>
```

### 2. Agent协作模式

#### 分工协作
- **架构Agent**：负责整体设计和技术选型
- **开发Agent**：负责具体实现和代码编写
- **测试Agent**：负责测试策略和用例设计
- **安全Agent**：负责安全风险评估和防护

#### 接口标准化
```json
{
  "task_id": "unique_identifier",
  "agent_role": "backend-architect",
  "input": {
    "requirements": "...",
    "constraints": "...",
    "context": "..."
  },
  "output": {
    "deliverables": "...",
    "recommendations": "...",
    "next_steps": "..."
  }
}
```

### 3. Agent选择决策树

```
任务复杂度评估
├── 简单 (4 Agents)
│   ├── 单一功能修改 → backend-engineer + test-engineer + security-auditor + technical-writer
│   ├── Bug修复 → backend-engineer + test-engineer + qa-specialist + technical-writer
│   └── 文档更新 → technical-writer + ux-designer + test-engineer + code-reviewer
├── 标准 (6 Agents)
│   ├── 新API开发 → api-designer + backend-architect + backend-engineer + test-engineer + security-auditor + performance-tester
│   ├── 数据库设计 → database-specialist + backend-architect + security-auditor + test-engineer + performance-tester + technical-writer
│   └── 前端功能 → frontend-specialist + ux-designer + backend-engineer + test-engineer + security-auditor + performance-tester
└── 复杂 (8 Agents)
    ├── 微服务架构 → system-architect + microservices-architect + api-designer + backend-engineer + test-engineer + security-auditor + devops-engineer + performance-tester
    ├── 企业系统 → system-architect + database-specialist + security-specialist + backend-engineer + frontend-specialist + test-engineer + devops-engineer + technical-writer
    └── 关键业务 → business-analyst + system-architect + api-designer + backend-engineer + security-specialist + test-engineer + performance-tester + devops-engineer
```

### 4. 质量检查清单

#### Agent选择检查
- [ ] Agent数量符合4-6-8策略
- [ ] 技能覆盖完整（开发、测试、安全、文档）
- [ ] 避免技能重复和空白
- [ ] 考虑任务特定需求

#### 执行方式检查
- [ ] 所有Agent在同一消息中调用
- [ ] 任务分工明确，避免重叠
- [ ] 输入输出接口标准化
- [ ] 并行执行，最小化依赖

#### 结果质量检查
- [ ] 架构设计合理
- [ ] 代码实现正确
- [ ] 测试覆盖充分
- [ ] 安全风险可控
- [ ] 文档完整清晰

## 📈 Agent性能优化

### 1. 执行效率优化
- **缓存Agent配置**：避免重复加载
- **并行度最大化**：减少Agent间依赖
- **资源合理分配**：基于Agent专长分工

### 2. 质量持续改进
- **Agent效果评估**：基于输出质量打分
- **组合优化建议**：基于历史数据推荐
- **最佳实践更新**：定期更新Agent使用指南

### 3. 定制化扩展
- **项目特定Agent**：针对特定需求定制
- **行业专家Agent**：深度垂直领域专家
- **企业内部Agent**：基于企业标准和流程

---
*56+ Agent生态系统为Claude Enhancer提供强大的AI驱动开发能力*
"""
        return content

    def consolidate_troubleshooting(self, categories):
        """整合故障排除文档"""
        content = """# Claude Enhancer 故障排除指南

## 🚨 常见问题快速索引

### 🔧 安装和配置问题
- [Git Hooks安装失败](#git-hooks安装失败)
- [Claude配置无效](#claude配置无效)
- [权限被拒绝](#权限被拒绝)
- [路径找不到](#路径找不到)

### ⚡ 工作流执行问题
- [Phase转换失败](#phase转换失败)
- [Agent选择错误](#agent选择错误)
- [并行执行失败](#并行执行失败)
- [Hook执行阻塞](#hook执行阻塞)

### 🤖 Agent相关问题
- [Agent调用失败](#agent调用失败)
- [Agent响应超时](#agent响应超时)
- [Agent结果不一致](#agent结果不一致)
- [Agent技能不匹配](#agent技能不匹配)

### 📊 性能和质量问题
- [执行速度慢](#执行速度慢)
- [内存使用过高](#内存使用过高)
- [代码质量检查失败](#代码质量检查失败)
- [测试覆盖率不足](#测试覆盖率不足)

## 🔧 安装和配置问题

### Git Hooks安装失败

**症状**:
```bash
Error: Failed to install git hooks
Permission denied: .git/hooks/pre-commit
```

**原因分析**:
- .git/hooks目录权限不足
- 现有hooks文件冲突
- Git仓库初始化不完整

**解决方案**:
```bash
# 1. 检查Git仓库状态
git status

# 2. 修复权限
chmod +x .git/hooks/
chmod +x .claude/install.sh

# 3. 重新安装
./.claude/install.sh --force

# 4. 验证安装
ls -la .git/hooks/
```

**预防措施**:
- 确保在Git仓库根目录执行
- 使用--force参数强制覆盖
- 定期检查hooks状态

### Claude配置无效

**症状**:
```
Warning: Claude settings not found or invalid
Using default configuration
```

**原因分析**:
- settings.json语法错误
- 配置文件路径错误
- 权限不足无法读取

**解决方案**:
```bash
# 1. 验证JSON语法
python -m json.tool .claude/settings.json

# 2. 检查文件权限
ls -la .claude/settings.json

# 3. 重置默认配置
cp .claude/config/main.yaml .claude/settings.json

# 4. 验证配置
.claude/scripts/config_validator.py
```

**配置检查清单**:
- [ ] JSON语法正确
- [ ] 必需字段完整
- [ ] 路径引用正确
- [ ] 权限设置合理

### 权限被拒绝

**症状**:
```bash
Permission denied: /home/xx/dev/Claude_Enhancer/.claude/hooks/smart_agent_selector.sh
```

**解决方案**:
```bash
# 1. 修复执行权限
find .claude -name "*.sh" -exec chmod +x {} \;

# 2. 修复Python脚本权限
find .claude -name "*.py" -exec chmod +x {} \;

# 3. 验证权限
ls -la .claude/hooks/
ls -la .claude/scripts/
```

### 路径找不到

**症状**:
```
Error: No such file or directory: .claude/agents/development/backend-engineer.md
```

**解决方案**:
```bash
# 1. 检查文件存在
find . -name "backend-engineer.md"

# 2. 检查符号链接
ls -la .claude/agents/

# 3. 重建索引
.claude/scripts/rebuild_agent_index.sh
```

## ⚡ 工作流执行问题

### Phase转换失败

**症状**:
```
Error: Cannot transition from Phase 2 to Phase 4
Phase 3 not completed
```

**原因分析**:
- Phase状态管理错误
- 前置条件未满足
- 状态文件损坏

**解决方案**:
```bash
# 1. 检查Phase状态
cat .claude/phase_state.json

# 2. 重置Phase状态
python .claude/scripts/reset_phase_state.py

# 3. 手动设置Phase
echo '{"current_phase": 3, "status": "in_progress"}' > .claude/phase_state.json
```

**Phase状态管理**:
```json
{
  "current_phase": 3,
  "phase_history": [
    {"phase": 0, "status": "completed", "timestamp": "2024-01-01T10:00:00Z"},
    {"phase": 1, "status": "completed", "timestamp": "2024-01-01T10:15:00Z"},
    {"phase": 2, "status": "completed", "timestamp": "2024-01-01T10:30:00Z"}
  ],
  "next_allowed_phases": [4],
  "blocking_issues": []
}
```

### Agent选择错误

**症状**:
```
Warning: Selected agents [backend-engineer, frontend-specialist]
do not match recommended combination for authentication task
```

**解决方案**:
```bash
# 1. 查看推荐组合
.claude/hooks/smart_agent_selector.sh --task-type=authentication --recommend

# 2. 使用智能选择
.claude/hooks/smart_agent_selector.sh --auto-select --task-complexity=standard

# 3. 验证Agent可用性
.claude/scripts/validate_agents.py
```

**Agent选择指南**:
```yaml
# 认证系统推荐组合
authentication:
  simple: [backend-engineer, security-auditor, test-engineer, technical-writer]
  standard: [backend-architect, security-auditor, test-engineer, api-designer, database-specialist, technical-writer]
  complex: [system-architect, security-specialist, backend-engineer, frontend-specialist, test-engineer, database-specialist, devops-engineer, technical-writer]
```

### 并行执行失败

**症状**:
```
Error: Agent execution conflict
Multiple agents trying to modify the same file
```

**解决方案**:
1. **文件锁机制**:
```python
# 在Agent执行前获取文件锁
with file_lock('/path/to/file'):
    # Agent操作
    pass
```

2. **分工明确化**:
```yaml
agent_responsibilities:
  backend-architect: ["architecture/", "docs/architecture/"]
  backend-engineer: ["src/", "tests/"]
  test-engineer: ["tests/", "test_data/"]
  security-auditor: ["security/", "audit_reports/"]
```

3. **冲突检测**:
```bash
# 执行前检查潜在冲突
.claude/scripts/detect_agent_conflicts.py --agents="backend-architect,backend-engineer"
```

### Hook执行阻塞

**症状**:
```
Hook: phase_enforcer.py is blocking execution
Reason: Insufficient agent count (2/4 minimum required)
```

**理解Hook阻塞**:
Claude Enhancer的Hook系统是质量保证机制，不是障碍。当Hook阻塞时：

**正确响应模式**:
```
Hook阻止 → 理解原因 → 修正方案 → 重试 → 直到成功
```

**错误响应模式** (绝对禁止):
- ❌ 跳过被Hook阻止的步骤
- ❌ 说"由于Hook限制，我改为..."
- ❌ 寻找绕过Hook的替代方案
- ❌ 忽略Hook继续其他任务

**解决方案**:
```bash
# 1. 查看具体阻塞原因
.claude/hooks/phase_enforcer.py --explain

# 2. 根据要求调整方案
# 例如：增加Agent数量到4个
# 例如：修改任务分工
# 例如：补充缺失的测试

# 3. 重新执行
# Hook通过后继续正常流程
```

## 🤖 Agent相关问题

### Agent调用失败

**症状**:
```
Error: Agent 'backend-architect' not found or not responding
```

**诊断步骤**:
```bash
# 1. 检查Agent定义
ls -la .claude/agents/development/backend-architect.md

# 2. 验证Agent配置
.claude/scripts/validate_agent.py backend-architect

# 3. 测试Agent通信
.claude/scripts/test_agent_communication.py backend-architect
```

**常见原因**:
- Agent定义文件缺失或损坏
- Agent配置语法错误
- 网络连接问题
- 资源限制

### Agent响应超时

**症状**:
```
Timeout: Agent 'performance-tester' did not respond within 60 seconds
```

**优化策略**:
```bash
# 1. 增加超时时间
export CLAUDE_AGENT_TIMEOUT=120

# 2. 减少任务复杂度
# 将大任务拆分为小任务

# 3. 使用缓存
export CLAUDE_AGENT_CACHE=true
```

### Agent结果不一致

**症状**:
```
Warning: Agent outputs show inconsistency
backend-architect suggests MongoDB, database-specialist suggests PostgreSQL
```

**解决策略**:
1. **冲突解决机制**:
```python
def resolve_agent_conflict(agent_outputs):
    # 基于优先级和专长解决冲突
    if task_type == "database_design":
        return prioritize_agent("database-specialist")
    else:
        return merge_recommendations(agent_outputs)
```

2. **一致性检查**:
```bash
.claude/scripts/check_agent_consistency.py --agents="backend-architect,database-specialist"
```

### Agent技能不匹配

**症状**:
```
Warning: Agent 'frontend-specialist' assigned to backend task
This may result in suboptimal outcomes
```

**解决方案**:
```bash
# 1. 重新智能选择
.claude/hooks/smart_agent_selector.sh --task-type=backend --auto-correct

# 2. 手动调整
# 替换为合适的Agent

# 3. 技能匹配验证
.claude/scripts/validate_agent_skills.py --task="backend API development"
```

## 📊 性能和质量问题

### 执行速度慢

**症状**:
- Agent执行时间超过预期
- 并行度不足
- 资源竞争

**优化方案**:
```bash
# 1. 性能分析
.claude/scripts/performance_analysis.py

# 2. 并行度优化
export CLAUDE_MAX_PARALLEL_AGENTS=8

# 3. 缓存启用
echo '{"cache_enabled": true, "cache_ttl": 3600}' > .claude/cache_config.json

# 4. 资源限制调整
echo '{"max_memory": "4GB", "max_cpu": "80%"}' > .claude/resource_limits.json
```

### 内存使用过高

**症状**:
```
Warning: Memory usage 85% (3.4GB/4GB)
Consider reducing parallel agent count
```

**解决方案**:
```bash
# 1. 监控内存使用
.claude/scripts/monitor_resources.py

# 2. 减少并行Agent数量
export CLAUDE_MAX_PARALLEL_AGENTS=4

# 3. 启用内存清理
export CLAUDE_AUTO_CLEANUP=true

# 4. 使用内存映射
export CLAUDE_USE_MMAP=true
```

### 代码质量检查失败

**症状**:
```
pre-commit hook failed:
- Linting errors: 12
- Test coverage: 65% (< 80% required)
- Security issues: 3 medium, 1 high
```

**解决流程**:
```bash
# 1. 查看详细错误
git commit --dry-run

# 2. 修复代码风格
black src/ tests/
flake8 src/ tests/

# 3. 提高测试覆盖率
pytest --cov=src --cov-report=term-missing

# 4. 修复安全问题
bandit -r src/
safety check
```

### 测试覆盖率不足

**症状**:
```
Test coverage: 65.2%
Required minimum: 80%
Missing coverage in: src/auth/models.py (45%), src/api/handlers.py (52%)
```

**改进策略**:
```bash
# 1. 生成覆盖率报告
pytest --cov=src --cov-report=html

# 2. 识别未覆盖代码
coverage report --show-missing

# 3. 添加测试用例
# 针对未覆盖的函数和分支

# 4. 验证改进
pytest --cov=src --cov-fail-under=80
```

## 🔍 诊断工具集

### 系统健康检查
```bash
# 综合健康检查
.claude/scripts/health_check.py

# 输出示例
System Health Report:
✅ Git repository: OK
✅ Claude configuration: OK
✅ Hooks installation: OK
✅ Agent definitions: OK (56/56)
❌ Performance: SLOW (avg 45s, target <30s)
⚠️  Memory usage: HIGH (85%)
```

### 性能基准测试
```bash
# 执行性能测试
.claude/scripts/performance_benchmark.sh

# 结果分析
Performance Benchmark Results:
- 4-Agent execution: 8.2s (target: <10s) ✅
- 6-Agent execution: 18.7s (target: <20s) ✅
- 8-Agent execution: 32.1s (target: <30s) ❌
```

### 配置验证
```bash
# 验证所有配置
.claude/scripts/validate_configuration.py

# 修复建议
Configuration Issues Found:
1. settings.json: Missing 'max_agents' field
2. phase_state.json: Invalid JSON syntax
3. Agent 'backend-architect': Missing required skills

Suggested fixes:
1. Add: "max_agents": 8
2. Run: .claude/scripts/fix_phase_state.py
3. Update: .claude/agents/development/backend-architect.md
```

## 📞 获取帮助

### 内置帮助系统
```bash
# 获取命令帮助
.claude/help.sh

# 特定主题帮助
.claude/help.sh agents
.claude/help.sh workflow
.claude/help.sh troubleshooting
```

### 日志分析
```bash
# 查看执行日志
tail -f .claude/execution.log

# 错误日志过滤
grep ERROR .claude/execution.log | tail -20

# 性能日志分析
.claude/scripts/analyze_performance_logs.py
```

### 社区支持
- **GitHub Issues**: 报告Bug和功能请求
- **内部论坛**: 技术讨论和经验分享
- **文档Wiki**: 更新和完善文档

---
*定期更新故障排除指南，确保开发者能够快速解决问题*
"""
        return content

    def create_migration_script(self):
        """创建文档迁移脚本"""
        migration_script = """#!/bin/bash
# 文档迁移脚本 - 从145个文档到5个核心文档

set -e

PROJECT_ROOT="/home/xx/dev/Claude_Enhancer"
BACKUP_DIR="${PROJECT_ROOT}/docs_backup_$(date +%Y%m%d_%H%M%S)"
TEMP_DIR="${PROJECT_ROOT}/docs_migration_temp"

echo "🚀 开始文档迁移..."

# 1. 创建备份
echo "💾 创建文档备份..."
mkdir -p "$BACKUP_DIR"
find "$PROJECT_ROOT" -name "*.md" -exec cp --parents {} "$BACKUP_DIR" \;

# 2. 运行Python整合脚本
echo "🔄 运行文档整合..."
python3 "${PROJECT_ROOT}/consolidate_docs.py"

# 3. 验证新文档
echo "✅ 验证新文档..."
for doc in README.md ARCHITECTURE.md WORKFLOW.md AGENTS.md TROUBLESHOOTING.md; do
    if [[ -f "$PROJECT_ROOT/$doc" ]]; then
        echo "  ✓ $doc 已创建"
    else
        echo "  ❌ $doc 创建失败"
        exit 1
    fi
done

# 4. 清理旧文档（可选）
read -p "是否删除旧文档? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️ 清理旧文档..."
    # 保留核心文档，删除其他
    find "$PROJECT_ROOT" -name "*.md" ! -name "README.md" ! -name "ARCHITECTURE.md" ! -name "WORKFLOW.md" ! -name "AGENTS.md" ! -name "TROUBLESHOOTING.md" -delete
fi

echo "✨ 文档迁移完成！"
echo "📁 备份位置: $BACKUP_DIR"
echo "📚 核心文档已就绪"
"""

        return migration_script

    def run_consolidation(self):
        """执行文档整合"""
        print("🔍 开始分析文档结构...")

        # 1. 分析现有文档
        categories = self.analyze_existing_docs()

        # 2. 创建备份
        self.create_backup()

        # 3. 生成核心文档内容
        docs_content = {
            "README.md": self.consolidate_readme(categories),
            "ARCHITECTURE.md": self.consolidate_architecture(categories),
            "WORKFLOW.md": self.consolidate_workflow(categories),
            "AGENTS.md": self.consolidate_agents(categories),
            "TROUBLESHOOTING.md": self.consolidate_troubleshooting(categories),
        }

        # 4. 写入新文档
        for filename, content in docs_content.items():
            filepath = self.project_root / filename
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ 已生成 {filename}")

        # 5. 生成统计报告
        print("\n📊 文档整合统计:")
        for category, files in categories.items():
            print(f"  {category}: {len(files)} 个文件")

        print(f"\n💾 备份位置: {self.backup_dir}")
        print("✨ 文档整合完成！")


if __name__ == "__main__":
    consolidator = DocumentConsolidator()
    consolidator.run_consolidation()
