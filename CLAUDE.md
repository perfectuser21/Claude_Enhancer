# Claude Code 项目指导文档

**项目名称**: Perfect21
**项目类型**: 企业级多Agent协作开发平台
**技术栈**: Python, claude-code-unified-agents, Git Hooks, 语义化版本管理
**目标用户**: 追求极致质量的开发者和团队

## 🎯 项目概述

Perfect21 是一个企业级多Agent协作开发平台，基于claude-code-unified-agents核心，集成了智能Git工作流、统一版本管理、动态功能发现等企业级开发特性。通过SubAgent调用编排器实现智能的开发流程自动化，采用模块化架构，专注于提升开发效率和代码质量。

### 核心理念
- 🎯 **智能协作**: 基于claude-code-unified-agents的56个专业Agent，提供企业级开发能力
- 🏗️ **模块化架构**: capability_discovery动态功能发现，支持热插拔式功能扩展
- 🔧 **统一管理**: version_manager语义化版本控制，确保项目版本一致性
- 🚀 **工作流优化**: git_workflow智能Git操作，标准化开发流程
- ⚡ **动态扩展**: 自动发现和集成新功能，无需手动配置

## 🏗️ 系统架构

### 完整的企业级架构

```
Perfect21/
├── core/                                    # claude-code-unified-agents核心层
│   └── claude-code-unified-agents/
│       ├── .claude/agents/                  # 56个官方Agent配置
│       ├── integrations/                    # Perfect21功能集成
│       └── perfect21_capabilities.json     # 功能注册表
├── features/                               # 功能层(可动态扩展)
│   ├── capability_discovery/              # 元功能：动态功能发现
│   │   ├── scanner.py                     # 功能扫描器
│   │   ├── registry.py                    # 功能注册器
│   │   └── loader.py                      # 动态加载器
│   ├── version_manager/                   # 统一版本管理
│   │   ├── semantic_version.py           # 语义化版本处理
│   │   ├── version_manager.py            # 版本管理核心
│   │   └── capability.py                 # 功能描述
│   └── git_workflow/                     # Git工作流管理
│       ├── hooks_manager.py              # Git钩子管理
│       ├── workflow_manager.py           # 工作流编排
│       └── branch_manager.py             # 分支管理
├── modules/                              # 工具层
│   ├── config.py                        # 配置管理
│   ├── perfect21_logger.py             # 日志系统
│   └── utils.py                         # 工具函数
├── main/                                # 入口层
│   ├── perfect21.py                     # 主程序类
│   ├── cli.py                          # 命令行接口
│   └── perfect21_controller.py         # 控制器
├── api/                                 # API层
│   ├── sdk.py                          # Python SDK
│   └── rest_server.py                  # REST API服务
└── vp.py                               # 程序入口点
```

### SubAgent调用策略

**Perfect21作为智能调用编排器**，不重复实现功能：

| Git操作 | 调用的SubAgent | 功能说明 |
|---------|---------------|----------|
| pre-commit | @code-reviewer, @orchestrator | 代码审查和质量检查 |
| pre-push | @test-engineer | 测试执行和验证 |
| post-checkout | @devops-engineer | 环境配置检查 |
| 安全检查 | @security-auditor | 安全漏洞扫描 |
| 性能分析 | @performance-engineer | 性能优化建议 |

## 🚀 使用方法

### 快速开始
```bash
# 查看系统状态
./vp.py status                                 # 或 python3 main/cli.py status

# 版本管理
./vp.py version                               # 查看当前版本
python3 -c "from features.version_manager import get_global_version_manager; vm = get_global_version_manager(); print(vm.generate_version_report())"

# 功能发现
python3 -c "from features.capability_discovery import bootstrap_capability_discovery; print(bootstrap_capability_discovery())"
```

### Git工作流管理
```bash
# Git钩子管理
python3 main/cli.py hooks list                # 查看可用钩子
python3 main/cli.py hooks install             # 安装Git钩子
python3 main/cli.py hooks uninstall           # 卸载Git钩子

# 工作流操作
python3 main/cli.py workflow list             # 查看工作流操作
python3 main/cli.py workflow branch-info      # 分析当前分支
python3 main/cli.py workflow create-feature --name auth-system  # 创建功能分支
python3 main/cli.py workflow merge-to-main --source feature/auth-system  # 合并到主分支

# 版本管理
python3 -c "from features.version_manager import get_global_version_manager; vm = get_global_version_manager(); result = vm.bump_version('minor'); print(f'新版本: {result}')"
```

### API集成
```python
# 使用Python SDK
from api.sdk import Perfect21SDK

sdk = Perfect21SDK()
result = sdk.execute_task("实现用户登录功能")
print(result.output)

# 检查系统状态
status = sdk.get_status()
print(f"Perfect21版本: {status.version}")
```

### Git工作流集成
Perfect21通过Git钩子自动触发SubAgent调用：

```bash
# 当执行git commit时，自动触发
git commit -m "新功能实现"
# → Perfect21调用 @code-reviewer 进行代码审查
# → 根据分支类型选择检查严格程度

# 当执行git push时，自动触发
git push origin feature/new-auth
# → Perfect21调用 @test-engineer 运行测试
# → 防止直接推送到受保护分支
```

## 💡 设计原则

### 1. 不重复造轮子
- **利用官方Agent**: 使用claude-code-unified-agents的53个专业Agent
- **专注编排价值**: Perfect21只做智能调用和工作流管理
- **保持同步**: core目录直接使用官方代码，自动获得更新

### 2. 最小可行架构
- **13个核心文件**: 从701个文件减少到13个
- **清晰分层**: 每层职责明确，便于理解和维护
- **模块化设计**: 功能独立，易于扩展

### 3. Git工作流专精
- **智能分支管理**: 根据分支类型调整检查策略
- **自动质量门禁**: 主分支严格检查，功能分支基础检查
- **SubAgent协调**: 多个Agent协作完成复杂工作流

## 🔧 技术实现

### SubAgent调用机制
```python
# Perfect21不实现具体功能，而是智能调用SubAgent
def call_subagent(self, agent_name: str, task_description: str):
    """调用claude-code-unified-agents的SubAgent"""
    return {
        'command': f"请在Claude Code中执行: {agent_name} {task_description}",
        'context': {...}
    }

# 示例: 提交前检查
if branch_type == 'main':
    # 主分支严格检查
    result = self.call_subagent(
        '@orchestrator',
        '执行严格的提交前质量检查：代码审查、安全扫描、测试验证'
    )
else:
    # 功能分支基础检查
    result = self.call_subagent(
        '@code-reviewer',
        '执行代码审查：检查代码质量、格式、最佳实践'
    )
```

### 工作流智能决策
```python
# 根据分支类型和操作类型智能选择Agent
branch_mapping = {
    'main': '@orchestrator',        # 完整质量门禁
    'release': '@deployment-manager', # 部署就绪检查
    'hotfix': '@test-engineer',     # 快速测试验证
    'feature': '@code-reviewer'     # 代码质量检查
}
```

## 📊 核心价值

### 对比传统方案

| 特性 | 传统Git工具 | Perfect21 |
|------|------------|-----------|
| 代码审查 | 手动或简单脚本 | @code-reviewer智能分析 |
| 安全检查 | 第三方工具集成 | @security-auditor专业扫描 |
| 测试管理 | 固定测试脚本 | @test-engineer智能策略 |
| 分支策略 | 静态规则 | 动态SubAgent选择 |
| 学习能力 | 无 | Agent持续改进 |

### 扩展能力
- **新功能**: 在features/目录添加新的SubAgent编排器
- **新Agent**: 在core/目录自动获得claude-code-unified-agents更新
- **自定义**: 在modules/目录扩展工具函数
- **集成**: 在main/目录添加新的入口点

## 🎉 核心优势

**Perfect21提供的独特价值**:

1. **🎯 智能编排**: 53个专业Agent + 智能调用策略
2. **🏗️ 架构清晰**: feature/main/core/module标准分层
3. **⚡ 轻量高效**: 98%代码减少，专注核心价值
4. **🔄 官方同步**: 自动获得claude-code-unified-agents更新
5. **🚀 Git专精**: 专为Git工作流优化的智能管理

---

**🎯 Perfect21 = claude-code-unified-agents + 智能Git工作流管理** 🚁

## 📁 文件管理规则 (重要!)

### 🚨 严格遵守的架构原则

#### 核心设计
1. **core/目录不可修改**: 完全使用claude-code-unified-agents官方代码
2. **features/专注功能**: 每个feature只做SubAgent调用编排
3. **modules/纯工具**: 只包含配置、日志、工具函数
4. **main/纯入口**: 只包含程序启动和CLI逻辑

#### 扩展规则
1. **新功能**: 在features/目录创建新的SubAgent编排器
2. **不重复实现**: 优先寻找现有Agent，避免重复开发
3. **保持轻量**: 新增代码必须有明确的编排价值
4. **文档更新**: 重大功能需要更新此CLAUDE.md文档

#### 维护准则
```bash
# 检查架构完整性
python3 main/cli.py status

# 验证Agent可用性
ls core/claude-code-unified-agents/.claude/agents/

# 确认功能正常
python3 main/cli.py hooks list
python3 main/cli.py workflow list
```

## 🎉 v2.1.0 重大更新

### ✨ 新增功能
- **🤖 capability_discovery**: 动态功能发现和集成系统，支持热插拔式功能扩展
- **📊 version_manager**: 统一版本管理系统，SemVer 2.0.0语义化版本控制
- **🔄 工作流标准化**: 企业级Git工作流，支持分支保护和自动合并

### 🎯 系统升级
- **模块化架构**: 从单一Git工作流扩展为完整的开发平台
- **自动化管理**: 版本同步、功能发现、集成注册全自动化
- **企业级特性**: 完整的API、SDK、CLI三重接口支持

### 📊 技术指标
- **功能模块**: 3个核心模块（capability_discovery, version_manager, git_workflow）
- **Agent集成**: 56个claude-code-unified-agents深度集成
- **版本控制**: 统一版本管理，消除版本混乱
- **扩展能力**: 支持动态功能发现和热加载

---

*最后更新: 2025-09-16*
*版本: Perfect21 2.3.0*
*架构: claude-code-unified-agents + 企业级开发平台*
*核心模块: 3个 | Agent集成: 56个 | 系统状态: 生产就绪*
