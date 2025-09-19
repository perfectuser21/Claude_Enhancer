# 🎯 Perfect21 Feature专项指南

> 本文档包含各个feature的专门指导，当处理特定feature时参考

## 📦 Feature清单和专项规则

### 1. git_workflow - Git工作流
**批量调用组合**：
```python
["code-reviewer", "security-auditor", "test-engineer"]  # pre-commit
["devops-engineer", "deployment-manager", "monitoring-specialist"]  # pre-push
```
**特殊规则**：
- Git操作必须加timeout（10秒）
- 永远不要用git -i（交互式命令）
- commit message必须包含Perfect21标记

### 2. auth_system - 认证系统
**批量调用组合**：
```python
["security-auditor", "backend-architect", "test-engineer", "api-designer"]
```
**特殊规则**：
- 密码必须用bcrypt加密
- JWT token必须设置过期时间
- 所有认证端点必须有rate limiting

### 3. dynamic_workflow_generator - 工作流生成
**批量调用组合**：
```python
["orchestrator", "project-manager", "business-analyst"]  # 需求分析
["backend-architect", "frontend-specialist", "database-specialist"]  # 设计
```
**特殊规则**：
- 必须选择3-5个agents
- 优先使用成功模式
- 复杂任务必须有同步点

### 4. error_handling - 错误处理
**批量调用组合**：
```python
["code-reviewer", "test-engineer", "monitoring-specialist"]
```
**特殊规则**：
- 所有异常必须记录context
- 提供recovery建议
- 不要吞掉异常

### 5. performance监控
**批量调用组合**：
```python
["performance-engineer", "monitoring-specialist", "devops-engineer"]
```
**特殊规则**：
- 定期清理metrics数据
- 使用rolling window统计
- 异常检测阈值动态调整

### 6. capability_discovery - 能力发现
**批量调用组合**：
```python
["orchestrator", "code-reviewer", "backend-architect"]
```
**特殊规则**：
- 缓存扫描结果
- 支持热加载
- 自动注册新功能

### 7. decision_recorder - 决策记录
**批量调用组合**：
```python
["technical-writer", "backend-architect", "project-manager"]
```
**特殊规则**：
- 使用ADR格式
- 包含context、decision、consequences
- 支持决策查询

### 8. learning_feedback - 学习反馈
**批量调用组合**：
```python
["data-scientist", "backend-architect", "performance-engineer"]
```
**特殊规则**：
- 记录成功和失败模式
- 定期分析和优化
- 反馈到工作流生成器

### 9. quality_gates - 质量门
**批量调用组合**：
```python
["test-engineer", "code-reviewer", "security-auditor", "performance-engineer"]
```
**特殊规则**：
- 质量标准不可协商
- 失败必须修复才能继续
- 记录每次检查结果

### 10. sync_point_manager - 同步点管理
**批量调用组合**：
```python
["orchestrator", "test-engineer", "code-reviewer"]
```
**特殊规则**：
- 验证所有agents输出一致性
- 失败要rollback
- 记录同步点状态

## 🚀 使用方式

### 当处理特定feature时：
1. 查看该feature的专项规则
2. 使用推荐的agent组合
3. 遵循特殊规则

### 示例：
```python
# 处理auth_system时
if "auth" in task or "认证" in task:
    # 查看auth_system规则
    agents = ["security-auditor", "backend-architect", "test-engineer", "api-designer"]
    # 应用特殊规则：bcrypt加密、JWT过期、rate limiting
```

## 📝 维护指南

### 添加新feature时：
1. 在本文档添加新章节
2. 定义推荐的agent组合
3. 列出特殊规则
4. 更新主CLAUDE.md引用

### 更新现有feature：
1. 只需修改本文档对应章节
2. 不需要创建多个CLAUDE.md文件
3. 保持集中管理

---

> 💡 这样既有专项指导，又避免了文件分散的问题！