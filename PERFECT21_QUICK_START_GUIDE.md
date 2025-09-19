# 🚀 Perfect21 快速上手指南

> Perfect21是基于Claude Code的智能开发平台，提供多Agent协作、工作流自动化和质量保证功能

## 📋 目录

- [核心概念](#-核心概念)
- [快速安装](#-快速安装)
- [基础使用](#-基础使用)
- [常用命令](#-常用命令)
- [典型场景](#-典型场景)
- [高级功能](#-高级功能)
- [最佳实践](#-最佳实践)
- [故障排除](#-故障排除)

## 🎯 核心概念

### Perfect21 = Claude Code + 智能增强层

```
┌─────────────────────────────────────────┐
│             Perfect21 平台              │
├─────────────────────────────────────────┤
│ • 智能工作流编排                        │
│ • 多Agent并行协作                       │
│ • 质量门自动检查                        │
│ • Git集成和Hooks                        │
│ • 学习反馈循环                          │
├─────────────────────────────────────────┤
│           Claude Code 核心              │
│        (56个专业Agents)                 │
└─────────────────────────────────────────┘
```

### 关键原则

1. **批量并行执行**: 总是同时调用3-5个Agents，而不是串行
2. **质量优先**: 每个环节都有质量门检查
3. **智能学习**: 系统会学习并优化工作流
4. **Git集成**: 深度集成Git工作流和最佳实践

## ⚡ 快速安装

### 1. 检查系统状态

```bash
# 查看Perfect21系统状态
python3 main/cli.py status

# 预期输出：
# 🚀 Perfect21系统状态
# 版本: v4.1
# 模式: production
# 核心Agent: ✅ 可用
# Agent数量: 56
```

### 2. 初始化项目

```bash
# 安装基础Git hooks
python3 main/cli.py hooks install standard

# 配置质量门
python3 main/cli.py quality config --template balanced
```

### 3. 验证安装

```bash
# 运行快速验证
python3 main/cli.py quality check --context quick

# 查看并行执行能力
python3 main/cli.py parallel --status
```

## 🔧 基础使用

### 启动开发任务

Perfect21提供多种启动方式，选择最适合的：

#### 方式1: 开发模式 (推荐新手)
```bash
# 智能开发助手，自动选择最佳工作流
python3 main/cli.py develop "创建用户登录功能"

# 带上下文的开发
python3 main/cli.py develop "优化数据库查询性能" --context '{"database": "postgresql", "tables": ["users", "orders"]}'
```

#### 方式2: 强制并行模式 (推荐专家)
```bash
# 强制使用5个Agent并行执行
python3 main/cli.py parallel "重构用户认证系统" --force-parallel --min-agents 5

# 查看并行执行状态
python3 main/cli.py parallel --status
```

#### 方式3: @orchestrator对话模式
```bash
# 直接与@orchestrator对话，强制并行
python3 main/cli.py orchestrator "使用Perfect21的git_workflow功能进行代码检查"
```

## 📝 常用命令

### 系统状态和监控

```bash
# 系统状态检查
python3 main/cli.py status

# 实时任务监控
python3 main/cli.py monitor --live

# 性能统计
python3 main/cli.py monitor --show-stats
```

### Git工作流管理

```bash
# 查看可用Git hooks
python3 main/cli.py hooks list

# 安装完整Git hooks
python3 main/cli.py hooks install complete

# 查看hooks状态
python3 main/cli.py hooks status

# 手动执行hook测试
python3 main/cli.py hooks execute pre-commit
```

### 质量门管理

```bash
# 运行质量检查
python3 main/cli.py quality check --context commit

# 查看质量趋势
python3 main/cli.py quality trends --days 30

# 查看检查历史
python3 main/cli.py quality history --limit 10

# 生成质量报告
python3 main/cli.py quality check --context all --output html
```

### 工作流管理

```bash
# 创建功能分支
python3 main/cli.py workflow create-feature --name user-auth

# 分支信息分析
python3 main/cli.py branch info

# 清理旧分支
python3 main/cli.py workflow cleanup --days 30
```

### 学习系统

```bash
# 查看学习摘要
python3 main/cli.py learning summary

# 查看改进建议
python3 main/cli.py learning suggestions

# 提供反馈
python3 main/cli.py learning feedback --collect --satisfaction 0.9 --comment "很好的功能"
```

## 🎨 典型场景

### 场景1: 全栈应用开发

```bash
# 步骤1: 使用全栈模板
python3 main/cli.py develop "开发电商网站用户管理系统" \
  --context '{
    "frontend": "React",
    "backend": "Python Flask",
    "database": "PostgreSQL",
    "features": ["注册", "登录", "用户资料", "权限管理"]
  }'

# 系统会自动并行调用：
# - @product-strategist (需求分析)
# - @ux-designer (界面设计)
# - @backend-architect (API设计)
# - @frontend-specialist (前端开发)
# - @test-engineer (测试编写)
```

### 场景2: API开发和文档

```bash
# 步骤1: API设计和实现
python3 main/cli.py parallel "设计和实现RESTful用户API" --min-agents 4

# 系统会并行调用：
# - @api-designer (API规范设计)
# - @backend-architect (API实现)
# - @test-engineer (API测试)
# - @technical-writer (API文档)

# 步骤2: 质量检查
python3 main/cli.py quality check --context commit
```

### 场景3: 代码审查和优化

```bash
# 步骤1: 全面代码审查
python3 main/cli.py parallel "审查用户认证模块代码质量和安全性" --min-agents 4

# 系统会并行调用：
# - @code-reviewer (代码质量)
# - @security-auditor (安全审查)
# - @performance-engineer (性能分析)
# - @test-engineer (测试覆盖率)

# 步骤2: 查看趋势
python3 main/cli.py quality trends --days 7
```

### 场景4: 部署和运维

```bash
# 步骤1: 容器化部署
python3 main/cli.py develop "设置Kubernetes部署管道" \
  --context '{
    "app": "user-service",
    "environment": "production",
    "monitoring": true
  }'

# 步骤2: 监控配置
python3 main/cli.py quality setup monitoring
```

## 🏗️ 高级功能

### 多工作空间管理

```bash
# 创建功能工作空间
python3 main/cli.py workspace create "user-auth" "用户认证功能开发" --type feature

# 列出工作空间
python3 main/cli.py workspace list

# 切换工作空间
python3 main/cli.py workspace switch user-auth-workspace-id

# 冲突检测
python3 main/cli.py workspace conflicts user-auth-workspace-id

# 自动合并
python3 main/cli.py workspace merge user-auth-workspace-id --dry-run
```

### 模板系统

Perfect21提供12个内置工作流模板：

```bash
# 查看可用模板
python3 main/cli.py develop "查看可用的工作流模板"

# 内置模板包括：
# - fullstack_development (全栈开发)
# - api_development (API开发)
# - comprehensive_testing (综合测试)
# - security_audit (安全审计)
# - deployment_pipeline (部署管道)
# - code_review (代码审查)
# - architecture_analysis (架构分析)
# - technology_research (技术调研)
```

### 错误处理和恢复

```bash
# 查看错误统计
python3 main/cli.py error stats

# 运行错误处理测试
python3 main/cli.py error test --type all

# 测试恢复策略
python3 main/cli.py error recovery --category all
```

### 决策记录 (ADR)

系统自动记录重要决策：

```bash
# 查看决策历史 (存储在 knowledge/decisions/)
ls knowledge/decisions/adr/

# 决策会自动记录在：
# - .perfect21/decisions.json
# - knowledge/decisions/index/decisions_index.json
```

## 💡 最佳实践

### 1. 并行优先原则

```bash
# ❌ 避免：单个Agent调用
python3 main/cli.py develop "简单任务"

# ✅ 推荐：强制并行模式
python3 main/cli.py parallel "简单任务" --min-agents 3
```

### 2. 上下文信息丰富

```bash
# ❌ 避免：信息不足
python3 main/cli.py develop "修复bug"

# ✅ 推荐：详细上下文
python3 main/cli.py develop "修复用户登录超时bug" \
  --context '{
    "error": "登录请求超时",
    "module": "auth_service.py",
    "symptoms": ["30秒后超时", "数据库连接缓慢"],
    "environment": "production"
  }'
```

### 3. 质量门集成

```bash
# 设置Git hooks自动质量检查
python3 main/cli.py hooks install complete

# 配置CI/CD质量门
python3 main/cli.py quality setup ci

# 定期检查质量趋势
python3 main/cli.py quality trends --days 30
```

### 4. 学习反馈

```bash
# 定期提供反馈
python3 main/cli.py learning feedback --collect --satisfaction 0.8

# 查看和实施改进建议
python3 main/cli.py learning suggestions --priority high
```

### 5. 监控和观察

```bash
# 使用实时监控
python3 main/cli.py monitor --live

# 查看执行历史
python3 main/cli.py parallel --history --limit 10
```

## 🔧 故障排除

### 常见问题

#### 1. Agent调用失败

```bash
# 症状：Agent无法响应或超时
# 解决方案：
python3 main/cli.py status  # 检查系统状态
python3 main/cli.py monitor --show-stats  # 查看性能
```

#### 2. Git hooks不工作

```bash
# 症状：提交时hooks不执行
# 解决方案：
python3 main/cli.py hooks status  # 检查安装状态
python3 main/cli.py hooks install complete --force  # 重新安装
```

#### 3. 质量门失败

```bash
# 症状：质量检查不通过
# 解决方案：
python3 main/cli.py quality check --context quick  # 快速检查
python3 main/cli.py quality trends --days 7  # 查看趋势
```

#### 4. 并行执行卡住

```bash
# 症状：并行任务不响应
# 解决方案：
python3 main/cli.py monitor --live  # 实时监控
python3 main/cli.py parallel --status  # 检查状态
```

### 日志和调试

```bash
# 查看系统日志
tail -f logs/perfect21.log

# 启用详细输出
python3 main/cli.py develop "任务" --verbose

# 查看配置信息
cat .perfect21/config.json
```

### 重置和清理

```bash
# 清理执行历史
python3 main/cli.py error clear

# 重置学习数据 (谨慎使用)
rm .perfect21/learning_data.json

# 重新初始化hooks
python3 main/cli.py hooks uninstall
python3 main/cli.py hooks install complete
```

## 📚 配置文件说明

### 主配置文件 `.perfect21/config.json`

```json
{
  "auto_activate": true,           // 自动激活功能
  "default_workflow": "dynamic_workflow",  // 默认工作流
  "sync_points_enabled": true,     // 启用同步点
  "decision_recording_enabled": true,      // 启用决策记录
  "quality_gates_enabled": true,   // 启用质量门
  "storage": {
    "decisions_path": "knowledge/decisions",  // 决策存储路径
    "adr_format": "json",          // ADR格式
    "auto_index": true             // 自动索引
  }
}
```

### 质量配置文件 `.perfect21/quality_config.json`

```bash
# 生成质量配置
python3 main/cli.py quality config --template balanced --output .perfect21/quality_config.json
```

## 🎯 下一步

1. **熟悉基础命令**: 从 `status` 和 `develop` 开始
2. **设置Git集成**: 安装hooks和质量门
3. **尝试并行执行**: 使用 `parallel` 命令体验多Agent协作
4. **探索高级功能**: 工作空间、模板、学习系统
5. **建立最佳实践**: 根据团队需求定制工作流

## 📞 获取帮助

```bash
# 查看命令帮助
python3 main/cli.py --help
python3 main/cli.py develop --help
python3 main/cli.py parallel --help

# 查看功能指南
cat FEATURE_GUIDES.md

# 查看架构文档
cat ARCHITECTURE.md
```

---

> 💡 **提示**: Perfect21的核心价值在于AI驱动的多Agent并行协作。始终思考如何将任务分解给多个专业Agent同时处理，而不是串行执行。

> 🚀 **记住**: 批量调用 = 真正的并行执行 = Perfect21的核心能力

**Happy Coding with Perfect21! 🎉**