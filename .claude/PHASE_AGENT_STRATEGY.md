# 8-Phase Agent并行策略

## 强制并行规则：每个Phase最少3个Agent

### Phase 0: Git分支创建 (3 Agents)
```yaml
agents:
  - project-manager: 验证分支命名规范
  - workflow-optimizer: 检查工作流状态
  - context-manager: 保存分支上下文
```

### Phase 1: 需求分析 (5 Agents)
```yaml
agents:
  - requirements-analyst: 需求文档
  - business-analyst: 业务流程
  - api-designer: 接口设计
  - security-auditor: 安全需求
  - technical-writer: 文档整理
```

### Phase 2: 设计规划 (6 Agents)
```yaml
agents:
  - backend-architect: 系统架构
  - database-specialist: 数据库设计
  - api-designer: API规范
  - frontend-specialist: 前端设计
  - devops-engineer: 部署架构
  - performance-engineer: 性能规划
```

### Phase 3: 实现开发 (8 Agents)
```yaml
agents:
  - fullstack-engineer: 核心代码实现
  - backend-architect: 后端服务
  - database-specialist: 数据层实现
  - frontend-specialist: 前端实现
  - test-engineer: 测试代码
  - security-auditor: 安全检查
  - performance-engineer: 性能优化
  - devops-engineer: 容器化
```

### Phase 4: 本地测试 (4 Agents)
```yaml
agents:
  - test-engineer: 执行测试
  - performance-tester: 性能测试
  - security-auditor: 安全扫描
  - e2e-test-specialist: 端到端测试
```

### Phase 5: 代码提交 (3 Agents)
```yaml
agents:
  - code-reviewer: 代码质量检查
  - technical-writer: commit message
  - workflow-optimizer: 流程验证
```

### Phase 6: 代码审查 (5 Agents)
```yaml
agents:
  - code-reviewer: 代码审查
  - security-auditor: 安全审计
  - performance-engineer: 性能分析
  - test-engineer: 测试覆盖
  - technical-writer: 审查报告
```

### Phase 7: 合并部署 (4 Agents)
```yaml
agents:
  - deployment-manager: 部署执行
  - devops-engineer: 环境配置
  - monitoring-specialist: 监控设置
  - incident-responder: 应急准备
```

## 总计：40个Agent调用（8个Phase）
平均每Phase: 5个Agents