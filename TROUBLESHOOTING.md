# Claude Enhancer 故障排除指南

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
Permission denied: /home/xx/dev/Claude Enhancer/.claude/hooks/smart_agent_selector.sh
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