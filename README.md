# Claude Code 工作流配置

> 让Claude Code自动遵守软件工程最佳实践的配置包

## 这是什么？

一套Claude Code配置文件，包含：
- 🤖 **56个专业Agents** - 覆盖开发、测试、运维、AI等各领域
- 🔄 **5阶段工作流** - 需求→设计→开发→测试→部署
- ✅ **自动质量检查** - 代码规范、安全审查、性能优化
- 🔗 **Git集成** - 提交规范、分支管理

## 快速使用

1. 复制配置到你的项目：
```bash
cp -r .claude /your-project/
```

2. (可选) 安装Git hooks：
```bash
cp .git/hooks/* /your-project/.git/hooks/
```

3. 正常使用Claude Code，配置自动生效

## 包含的56个专业Agents

### 开发 (14个)
`react-pro`, `vue-specialist`, `angular-expert`, `python-pro`, `java-enterprise`, `golang-pro`, `rust-pro`, `backend-architect`, `frontend-specialist`, `fullstack-engineer` 等

### 基础设施 (7个)
`devops-engineer`, `cloud-architect`, `kubernetes-expert`, `monitoring-specialist`, `deployment-manager`, `performance-engineer`, `incident-responder`

### 质量保证 (7个)
`test-engineer`, `e2e-test-specialist`, `security-auditor`, `code-reviewer`, `performance-tester`, `accessibility-auditor`

### 数据/AI (6个)
`data-scientist`, `ai-engineer`, `mlops-engineer`, `data-engineer`, `analytics-engineer`, `prompt-engineer`

### 业务分析 (6个)
`requirements-analyst`, `product-strategist`, `business-analyst`, `project-manager`, `api-designer`, `technical-writer`

### 特殊领域 (11个)
`blockchain-developer`, `fintech-specialist`, `healthcare-dev`, `game-developer`, `mobile-developer` 等

## 使用示例

### Web应用开发
```
"创建一个博客系统，支持用户登录、文章发布、评论功能"
→ Claude自动调用: backend-architect, frontend-specialist, database-specialist等
```

### 移动应用
```
"开发一个跨平台的记账App"
→ Claude自动调用: mobile-developer, ux-designer, test-engineer等
```

### AI项目
```
"构建一个图像识别系统"
→ Claude自动调用: ai-engineer, data-scientist, mlops-engineer等
```

## 工作原理

1. **Claude理解任务** - 分析你的需求
2. **自动选择Agents** - 基于任务类型选择专业团队
3. **并行执行** - 多个Agent同时工作提高效率
4. **质量保证** - 自动进行代码检查和测试
5. **完整交付** - 从需求到部署的端到端解决方案

## 文件结构

```
.claude/
├── agents/          # 56个专业Agents定义
│   ├── development/
│   ├── infrastructure/
│   ├── quality/
│   ├── data-ai/
│   ├── business/
│   └── specialized/
├── hooks/          # 工作流控制
└── settings.json   # 基础配置
```

## License

MIT - 自由使用和修改