# Claude Code 项目指导文档

**项目名称**: Perfect21
**项目类型**: AI驱动的开发工作流协作平台  
**技术栈**: Python, MCP, Claude Opus 4.1, GPT-5, Shell Script  
**目标用户**: 追求极致质量的开发者和团队  

## 🎯 项目概述

Perfect21 是一个企业级的AI驱动开发工作流协作平台，通过主-Agent智能协调13个专业SubAgent分工合作，结合MCP路由系统和多模型协作，让用户通过自然语言对话获得最高质量的软件开发服务。

### 核心理念
- 🚀 **MCP多模型并行协作**: 13个SubAgent + 智能模型路由 + 并行处理
- 🤖 **质量优先策略**: 所有任务默认使用最高质量协作模式
- 💰 **智能成本优化**: 节省40-60%成本，质量不打折扣
- ⚡ **真正并行处理**: 多Agent同时工作，效率与质量双重保证

## 🏗️ 系统架构

### 完整的13个SubAgent专业分工

#### 📋 需求与架构阶段
1. **spec-planner**: 需求分析和规划 (Claude Opus 4.1 + GPT-5 协作)
2. **spec-architect**: 系统架构和技术设计 (Claude Opus 4.1 + GPT-5 协作)

#### 💻 开发实现阶段  
3. **developer-primary**: 主开发和核心实现 (GPT-5 + Claude Opus 协作)
4. **developer-parallel**: 替代实现方案 (GPT-5 独立)

#### 🧪 测试验证阶段
5. **test-generator**: 测试用例设计和策略 (GPT-5 独立)
6. **test-runner**: 测试执行和验证 (GPT-5-mini 成本优化)

#### 🔒 审查与安全阶段
7. **code-reviewer**: 代码质量和最佳实践审查 (Claude Opus 4.1 + GPT-5 协作)
8. **security-auditor**: 安全漏洞评估 (Claude Opus 4.1 + GPT-5 协作)
9. **performance-analyzer**: 性能优化分析 (Claude Opus 4.1 + GPT-5 协作)

#### ✅ 质量保证阶段
10. **cross-validator**: 交叉验证和一致性检查 (Claude Opus 4.1 独立)
11. **quality-gatekeeper**: 质量门禁执行 (Claude Opus 4.1 独立)
12. **coach-qa**: 流程改进和指导 (Claude Opus 4.1 独立)
13. **commit-bot**: Git操作和版本管理 (GPT-5 独立)

### MCP智能路由系统
- **协作模式**: 重要Agent自动启用多模型协作
- **成本优化**: 自动选择最佳模型组合
- **质量保证**: 关键审查环节多模型共识验证
- **并行处理**: 真正的并行执行，最大化效率

## 🎯 质量优先策略

### 默认行为
**所有任务都使用完整的13个SubAgent MCP并行协作**，包括：
- 简单的Hello World函数
- 复杂的微服务架构系统
- API接口开发
- 代码重构和优化

### 质量保证特性
- ✅ **多层审查**: code-reviewer + security-auditor + performance-analyzer
- ✅ **交叉验证**: cross-validator确保一致性
- ✅ **质量门禁**: quality-gatekeeper严格把关
- ✅ **双重实现**: developer-primary + developer-parallel提供选择
- ✅ **全面测试**: test-generator + test-runner完整覆盖

## 🚀 使用方法

### 基本使用
```bash
# 启动任何任务都会自动使用13个SubAgent并行协作
./vp "创建用户登录API"
./vp "重构支付系统"  
./vp "优化数据库查询性能"
```

### 系统状态
```bash
./vp status          # 查看MCP系统状态
./vp health          # 系统健康检查
./vp --help          # 查看使用帮助
```

## 💰 成本与效率优化

### 智能成本控制
- **节省40-60%**: MCP智能路由优化模型选择
- **质量不打折**: 协作模式确保输出质量
- **并行处理**: 真正的多Agent并行，提升效率

### 模型分配策略
- **Claude Opus 4.1**: 深度推理、安全分析、架构设计
- **GPT-5**: 代码生成、算法优化、快速实现  
- **GPT-5-mini**: 测试执行、成本敏感任务
- **智能协作**: 重要任务自动启用多模型协作

## 📊 预期效果

### 质量提升
- **多模型协作**: 重要环节双重验证
- **专业分工**: 每个Agent专注特定领域
- **全面覆盖**: 从需求到部署的完整流程

### 效率提升  
- **并行处理**: 多Agent同时工作
- **智能路由**: 自动选择最佳模型
- **成本优化**: 40-60%成本节省

### 开发体验
- **零配置**: 开箱即用的质量优先模式
- **全自动**: 智能分析和执行
- **透明度**: 详细的执行过程和成本报告

## 🔧 技术实现

### MCP集成
- **统一路由器**: `core/model_router.py`
- **任务调度**: 智能分配和并行执行
- **成本跟踪**: 实时成本监控和优化

### 质量保证
- **证据文件**: tests.json + review.md + 执行日志
- **门禁机制**: 90分质量标准
- **持续改进**: 自动学习和优化

## 🎉 核心价值

**VibePilot Enhanced V2提供企业级的AI辅助开发体验:**

1. **🚀 最高质量**: 13个SubAgent专业协作，多模型验证
2. **💰 成本效率**: 智能优化，节省40-60%成本
3. **⚡ 真正并行**: 多Agent同时工作，效率最大化
4. **🎯 质量优先**: 所有任务都获得最高标准处理
5. **🤖 智能自动**: 零配置，自动分析和执行

---

**🎯 立即开始使用VibePilot Enhanced V2，体验13个SubAgent MCP并行协作带来的质量革命！** 🚁

## 📁 文件管理规则 (重要!)

### 🚨 严格遵守的文件管理规范

#### 禁止行为
1. **禁止创建版本文件**: 永远不要创建 `*_v2.py`, `*_new.py`, `*_final.py`, `*_backup.py` 等版本文件
2. **禁止重写已存在文件**: 不要用Write工具覆盖现有文件
3. **禁止在文件名中管理版本**: 版本控制交给Git，不在文件名体现

#### 必须行为  
1. **使用Edit工具**: 修改现有文件时，必须使用Edit工具，不用Write
2. **直接修改原文件**: 有问题直接改原文件，不创建新版本
3. **依赖Git管理版本**: 历史版本由Git管理，可随时回滚
4. **清理后再工作**: 每次开始前运行 `vp clean` 检查版本混乱

#### 工作流程
```bash
# 1. 开始工作前
vp clean --report                    # 检查版本文件情况
vp clean --auto                      # 自动清理安全的版本文件
vp clean --interactive               # 手动处理复杂情况

# 2. 修改代码时
# ✅ 正确方式: 直接编辑现有文件
Edit(/path/to/existing_file.py, old_text, new_text)

# ❌ 错误方式: 创建新版本
Write(/path/to/existing_file_v2.py, content)

# 3. 完成工作后
git add -A && git commit -m "描述修改内容"
vp clean --auto                      # 再次检查清理
```

#### 异常情况处理
- **需要对比版本**: 使用 `git diff` 查看差异
- **需要备份**: 让Git创建分支，不要创建文件副本  
- **临时测试**: 在 `/tmp` 目录创建，不在项目内
- **实验功能**: 创建新的功能模块，不修改文件名版本

#### 自动化支持
- **Git钩子**: 自动检测并阻止版本文件提交
- **vp clean命令**: 智能清理版本文件混乱
- **实时监控**: VibePilot自动检测版本文件创建

### 🔧 使用VibePilot文件清理工具

```bash
# 查看版本文件情况
python -m modules.version_cleaner --report report.md

# 自动清理安全的版本文件  
python -m modules.version_cleaner --auto

# 交互式清理模式
python -m modules.version_cleaner --interactive

# 空运行模式(查看将执行的操作)
python -m modules.version_cleaner --dry-run

# 集成到VibePilot工作流
vp clean                             # 清理版本文件
vp clean --auto                      # 自动模式
vp clean --report                    # 生成清理报告
```

---

*最后更新: 2025-09-06*  
*版本: VibePilot Enhanced V2.12.0*  
*维护者: MCP多模型协作团队*  
*文件管理: VibePilot Version Cleaner System*