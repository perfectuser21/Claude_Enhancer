# 🔗 Perfect21 Git Hook Integration System

> **版本**: 1.0 | **更新时间**: 2025-01-17
> **核心理念**: Git Hooks作为Perfect21工作流的质量检查点

## 🎯 概述

Perfect21 Git Hook Integration System将Git hooks集成到5层工作流中，作为质量强制检查点，确保每个阶段都符合Perfect21标准。

### 核心特性

- ✅ **5层工作流集成**: 将Git hooks映射到工作流的关键检查点
- 🔄 **智能重试机制**: 失败时自动重试和修复
- 📊 **产物管理系统**: 跟踪和验证工作流输出
- 🛡️ **质量门控制**: 强制执行质量标准
- 🚀 **自动修复能力**: 常见问题的自动化修复

## 🏗️ 架构设计

### 5层工作流映射

```
Git Hook          工作流阶段              检查内容
=========================================================
post-checkout  →  Task Analysis        → 环境检查、依赖验证
pre-commit     →  Agent Selection      → Agent配置、代码基础检查
commit-msg     →  Parallel Execution  → 执行结果验证
pre-push       →  Quality Gates       → 全面质量检查
post-merge     →  Deployment         → 部署准备、监控设置
```

### 组件架构

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Interface                        │
│              (features/git/cli_integration.py)         │
├─────────────────────────────────────────────────────────┤
│               Enhanced Hooks Manager                    │
│              (features/git/enhanced_hooks.py)          │
│  • 失败处理策略  • 重试逻辑  • 自动修复                 │
├─────────────────────────────────────────────────────────┤
│             Workflow Hooks Integration                  │
│         (features/git/workflow_hooks_integration.py)   │
│  • 工作流阶段映射  • 质量检查  • 上下文管理             │
├─────────────────────────────────────────────────────────┤
│               Artifact Management                       │
│            (features/git/artifact_management.py)       │
│  • 产物存储  • 质量验证  • 生命周期管理                 │
└─────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 1. 安装Git Hooks

```bash
# 安装所有hooks
python3 features/git/cli_integration.py install

# 安装特定hooks
python3 features/git/cli_integration.py install --hooks pre-commit pre-push

# 强制覆盖已存在的hooks
python3 features/git/cli_integration.py install --force
```

### 2. 查看状态

```bash
# 显示hooks和产物状态
python3 features/git/cli_integration.py status
```

### 3. 测试单个Hook

```bash
# 测试pre-commit hook
python3 features/git/cli_integration.py test pre-commit

# 使用自定义上下文测试
python3 features/git/cli_integration.py test pre-push --context '{"remote":"origin"}'
```

### 4. 运行完整工作流测试

```bash
# 测试完整的5层工作流
python3 features/git/cli_integration.py workflow-test "实现用户登录功能"
```

## 📋 Hook详细说明

### Pre-Commit Hook (Agent Selection阶段)

**触发时机**: `git commit`
**主要检查**:
- ✅ 暂存文件验证
- ✅ Agent配置检查
- ✅ 基础代码质量
- ✅ Perfect21规则合规性

**示例输出**:
```
✅ Agent选择阶段检查通过
  - 使用3个Agent并行执行
  - 代码格式符合标准
  - 安全基础检查通过
```

### Commit-MSG Hook (Parallel Execution阶段)

**触发时机**: `git commit` (提交信息验证)
**主要检查**:
- ✅ 执行结果完整性
- ✅ Agent并行执行验证
- ✅ 提交信息格式

**示例输出**:
```
✅ 并行执行阶段检查通过
  - 3个Agent全部执行成功
  - 平均执行时间: 2.5秒
  - 提交信息格式正确
```

### Pre-Push Hook (Quality Gates阶段)

**触发时机**: `git push`
**主要检查**:
- ✅ 代码覆盖率 (>80%)
- ✅ 安全漏洞扫描
- ✅ 性能指标验证
- ✅ 分支保护检查

**示例输出**:
```
✅ 质量门检查全部通过
  - 代码覆盖率: 85%
  - 安全评分: 90/100
  - 性能评分: 80/100
  - P95响应时间: 180ms
```

### Post-Checkout Hook (Task Analysis阶段)

**触发时机**: `git checkout` (分支切换)
**主要检查**:
- ✅ 依赖环境检查
- ✅ 配置同步
- ✅ 缓存清理

### Post-Merge Hook (Deployment阶段)

**触发时机**: `git merge` / PR合并
**主要检查**:
- ✅ 部署环境准备
- ✅ 监控配置设置
- ✅ 通知系统配置
- ✅ 回滚方案准备

## 🔧 失败处理机制

### 失败策略

1. **ABORT** - 立即中止操作
2. **RETRY** - 自动重试 (支持指数退避)
3. **AUTO_FIX** - 尝试自动修复
4. **MANUAL_INTERVENTION** - 需要手动干预
5. **SKIP_WITH_WARNING** - 跳过并警告

### 自动修复能力

| 问题类型 | 修复方案 | 成功率 |
|---------|---------|--------|
| 代码格式错误 | black + isort | 95% |
| 语法错误 | 基础修复 | 70% |
| 导入错误 | 路径修复 | 60% |
| 测试失败 | 需手动修复 | 0% |
| 安全漏洞 | 需手动审查 | 0% |

### 重试配置示例

```python
RetryConfig(
    max_attempts=3,           # 最大重试次数
    delay_seconds=1.0,        # 基础延迟
    exponential_backoff=True, # 指数退避
    retry_conditions=['timeout', 'network', 'temporary']
)
```

## 📊 产物管理

### 产物类型

- **TASK_ANALYSIS** - 任务分析结果
- **AGENT_SELECTION** - Agent选择配置
- **EXECUTION_RESULTS** - 执行结果
- **QUALITY_REPORT** - 质量报告
- **TEST_RESULTS** - 测试结果
- **SECURITY_SCAN** - 安全扫描结果
- **PERFORMANCE_METRICS** - 性能指标
- **DEPLOYMENT_CONFIG** - 部署配置
- **MONITORING_CONFIG** - 监控配置

### 产物管理命令

```bash
# 列出所有产物
python3 features/git/cli_integration.py artifacts list

# 列出特定类型的产物
python3 features/git/cli_integration.py artifacts list --type execution_results

# 验证产物质量
python3 features/git/cli_integration.py artifacts validate <artifact_id>

# 清理过期产物 (预览)
python3 features/git/cli_integration.py artifacts cleanup

# 执行实际清理
python3 features/git/cli_integration.py artifacts cleanup --force
```

### 质量评估

产物质量基于4个维度评估:
- **完整性** (40%) - 必需字段是否完整
- **准确性** (30%) - 内容是否准确详细
- **一致性** (20%) - 格式是否一致
- **及时性** (10%) - 是否及时生成

质量等级:
- **EXCELLENT** (90-100分) - 优秀
- **GOOD** (80-89分) - 良好
- **ACCEPTABLE** (70-79分) - 可接受
- **POOR** (60-69分) - 较差
- **FAILED** (<60分) - 失败

## ⚙️ 配置选项

### Hook配置文件

位置: `.perfect21/hooks/hook_configs.json`

```json
{
  "pre-commit": {
    "priority": "CRITICAL",
    "failure_strategy": "AUTO_FIX",
    "timeout_seconds": 180,
    "auto_fix_enabled": true,
    "retry_config": {
      "max_attempts": 3,
      "delay_seconds": 1.0,
      "exponential_backoff": true
    }
  }
}
```

### 产物仓库配置

位置: `.perfect21/config.yaml`

```yaml
artifact_repository:
  max_storage_mb: 1024
  retention_days: 30
  compression_enabled: true
  versioning_enabled: true
  auto_cleanup_enabled: true
```

### 质量门配置

```yaml
quality_gates:
  code_quality:
    min_coverage: 80
    max_complexity: 10
    max_duplication: 5

  security:
    scan_dependencies: true
    check_secrets: true
    validate_permissions: true

  performance:
    max_response_time_p95: 200
    max_memory_usage: 512
    min_throughput: 100
```

## 🧪 测试和验证

### 单元测试

```bash
# 运行Git hooks相关测试
python3 -m pytest tests/git/ -v

# 运行产物管理测试
python3 -m pytest tests/git/test_artifact_management.py -v

# 运行集成测试
python3 -m pytest tests/integration/test_git_hooks_integration.py -v
```

### 端到端测试

```bash
# 完整工作流测试
python3 features/git/cli_integration.py workflow-test "开发新功能"

# 测试所有hooks
for hook in pre-commit commit-msg pre-push post-checkout post-merge; do
    python3 features/git/cli_integration.py test $hook
done
```

## 📝 日志和监控

### 日志位置

- **Hook执行日志**: `.perfect21/hooks.log`
- **失败日志**: `.perfect21/hooks/failures.log`
- **性能日志**: `.perfect21/hooks/performance.log`
- **产物操作日志**: `.perfect21/artifacts/operations.log`

### 监控指标

- Hook执行成功率
- 平均执行时间
- 自动修复成功率
- 产物质量分布
- 存储空间使用

## 🚨 故障排除

### 常见问题

**1. Hook执行失败**
```bash
# 查看详细错误信息
python3 features/git/cli_integration.py test pre-commit --verbose

# 检查hook文件权限
ls -la .git/hooks/
```

**2. 产物存储问题**
```bash
# 检查存储空间
python3 features/git/cli_integration.py artifacts list

# 清理过期产物
python3 features/git/cli_integration.py artifacts cleanup --force
```

**3. 质量检查失败**
```bash
# 验证特定产物
python3 features/git/cli_integration.py artifacts validate <artifact_id>

# 查看质量报告详情
cat .perfect21/artifacts/quality_reports/latest.json
```

### 调试模式

```bash
# 启用详细日志
export PERFECT21_LOG_LEVEL=DEBUG

# 运行带详细输出的命令
python3 features/git/cli_integration.py status --verbose
```

## 🔄 升级和迁移

### 升级Hook系统

```bash
# 备份现有配置
cp -r .perfect21/hooks .perfect21/hooks.backup

# 重新安装hooks
python3 features/git/cli_integration.py uninstall
python3 features/git/cli_integration.py install --force
```

### 数据迁移

```bash
# 导出产物数据
python3 -c "
import asyncio
from features.git.artifact_management import ArtifactManager
async def export():
    manager = ArtifactManager()
    stats = await manager.get_repository_stats()
    print(stats)
asyncio.run(export())
"
```

## 📚 最佳实践

### 1. Hook配置优化

- 根据项目规模调整超时时间
- 为不同环境设置不同的失败策略
- 定期清理过期产物

### 2. 质量标准调整

- 根据团队能力调整质量门标准
- 为关键项目设置更严格的标准
- 新项目可适当放宽标准

### 3. 监控和警报

- 设置Hook失败率警报
- 监控产物质量趋势
- 定期审查自动修复效果

### 4. 团队协作

- 建立Hook失败处理流程
- 培训团队使用产物管理功能
- 定期分享最佳实践和经验

## 🔗 相关文档

- [Perfect21 Core Documentation](./CLAUDE.md)
- [Perfect21 Architecture](./ARCHITECTURE.md)
- [Feature Development Guide](./FEATURE_GUIDES.md)
- [Git Workflow Best Practices](./docs/git-workflow.md)

---

> 💡 **提示**: Git Hook Integration是Perfect21质量保证的核心组件。正确配置和使用可以显著提升开发效率和代码质量。