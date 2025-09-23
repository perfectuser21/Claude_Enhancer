# Claude Enhancer 统一配置系统使用指南

## 🎯 概述

Claude Enhancer现在使用统一的配置管理系统，将之前分散在4个不同文件中的配置合并到一个主配置文件中，同时提供环境特定的覆盖配置。

## 📁 新的配置结构

```
.claude/config/
├── unified_main.yaml          # 🔥 主配置 - 单一来源
├── env/
│   ├── development.yaml       # 开发环境覆盖 (宽松模式)
│   ├── testing.yaml          # 测试环境覆盖 (平衡模式)
│   └── production.yaml       # 生产环境覆盖 (严格模式)
├── schemas/
│   ├── config_schema.yaml    # 配置架构验证
│   └── unified_schema.yaml   # 统一架构模式
├── legacy/                   # 归档的旧配置 (备用)
├── migration_backup_*/       # 迁移备份
└── scripts/
    ├── load_config.sh        # 配置加载器
    ├── config_validator.py   # 配置验证器
    └── migrate_config.sh     # 迁移脚本
```

## 🚀 使用方法

### 1. 环境检测和配置加载

```bash
# 自动检测环境并加载适当配置
.claude/scripts/load_config.sh load

# 手动指定环境
PERFECT21_ENV=development .claude/scripts/load_config.sh load
PERFECT21_ENV=testing .claude/scripts/load_config.sh load
PERFECT21_ENV=production .claude/scripts/load_config.sh load

# 检测当前环境
.claude/scripts/load_config.sh env
```

### 2. 配置验证

```bash
# 基本配置验证 (语法检查)
.claude/scripts/load_config.sh validate

# 深度配置验证 (架构 + 业务规则)
python3 .claude/scripts/config_validator.py .claude/config/unified_main.yaml

# 带架构验证
python3 .claude/scripts/config_validator.py \
  .claude/config/unified_main.yaml \
  --schema .claude/config/schemas/config_schema.yaml

# 生成验证报告
python3 .claude/scripts/config_validator.py \
  .claude/config/unified_main.yaml \
  --report config_validation_report.md \
  --strict
```

### 3. 环境配置设置

```bash
# 设置开发环境 (默认)
export PERFECT21_ENV=development

# 设置测试环境
export PERFECT21_ENV=testing

# 设置生产环境
export PERFECT21_ENV=production

# 临时使用特定环境
PERFECT21_ENV=production .claude/scripts/load_config.sh load
```

## 🔧 配置内容说明

### 核心配置区域

| 配置区域 | 说明 | 主要内容 |
|----------|------|----------|
| `metadata` | 配置元信息 | 版本、名称、描述、迁移历史 |
| `system` | 系统设置 | 运行模式、版本、调试选项 |
| `workflow` | 8-Phase工作流 | 阶段定义、Agent要求、质量门控 |
| `agents` | Agent策略 | 4-6-8策略、执行模式、选择规则 |
| `task_types` | 任务类型 | 任务-Agent映射、复杂度、测试要求 |
| `hooks` | Hook配置 | Hook定义、执行策略、超时设置 |
| `quality_gates` | 质量门控 | 检查项目、阻塞规则、阈值设置 |
| `environments` | 环境设置 | 开发/测试/生产环境特定配置 |

### 4-6-8 Agent策略

| 复杂度 | Agent数量 | 时长 | 适用场景 |
|--------|-----------|------|----------|
| **Simple** | 4个Agent | 5-10分钟 | 快速修复、小功能 |
| **Standard** | 6个Agent | 15-20分钟 | 常规功能开发 |
| **Complex** | 8个Agent | 25-30分钟 | 复杂系统实现 |

### 任务类型自动识别

系统会根据关键词自动识别任务类型并推荐相应的Agent组合：

| 任务类型 | 关键词示例 | 推荐Agent | 最小数量 |
|----------|-----------|-----------|----------|
| `authentication` | 登录、认证、auth、jwt、oauth | backend-architect, security-auditor, test-engineer, api-designer, database-specialist | 5 |
| `api_development` | api、接口、rest、graphql、endpoint | api-designer, backend-architect, test-engineer, technical-writer | 4 |
| `database_design` | 数据库、database、schema、sql | database-specialist, backend-architect, performance-engineer | 3 |
| `frontend_development` | 前端、frontend、react、vue、ui | frontend-specialist, ux-designer, test-engineer, accessibility-auditor | 4 |
| `fullstack` | 全栈、fullstack、应用、application | fullstack-engineer, backend-architect, frontend-specialist, database-specialist, test-engineer, devops-engineer | 6 |

## 🌍 环境配置详解

### Development Environment (开发环境)
- **模式**: Advisory (建议模式)
- **Agent要求**: 降低到最低限度 (2-4个)
- **质量门控**: 禁用或警告模式
- **并行执行**: 允许顺序执行用于调试
- **日志级别**: DEBUG
- **特点**: 快速迭代、宽松规则、实验友好

### Testing Environment (测试环境)
- **模式**: Warning (警告模式)
- **Agent要求**: 标准要求
- **质量门控**: 启用但不阻塞
- **测试覆盖**: 要求80%覆盖率
- **日志级别**: INFO
- **特点**: 平衡质量和效率、注重测试

### Production Environment (生产环境)
- **模式**: Enforcement (强制模式)
- **Agent要求**: 提高到最高标准
- **质量门控**: 全部启用且阻塞
- **安全检查**: 强制性安全审计
- **日志级别**: WARN/ERROR
- **特点**: 最高质量标准、安全优先

## 🛠 自定义配置

### 1. 修改Agent策略

编辑 `unified_main.yaml` 中的 `agents.strategy` 部分：

```yaml
agents:
  strategy:
    simple_tasks:
      agent_count: 4
      duration: "5-10 minutes"
      complexity_threshold: 20
    # ... 其他配置
```

### 2. 添加新任务类型

在 `task_types` 部分添加新定义：

```yaml
task_types:
  your_custom_task:
    keywords: ["关键词1", "关键词2"]
    required_agents: ["agent1", "agent2", "agent3"]
    minimum_count: 3
    complexity: "simple"
```

### 3. 环境特定覆盖

在 `env/` 目录下的环境文件中添加覆盖配置：

```yaml
# env/your_env.yaml
environment: "your_env"
extends: "../unified_main.yaml"

# 覆盖特定设置
system:
  mode: "advisory"

agents:
  execution:
    enforce_parallel: false
```

## 🔍 故障排除

### 常见问题

1. **配置加载失败**
   ```bash
   # 检查语法
   .claude/scripts/load_config.sh validate

   # 检查环境变量
   echo $PERFECT21_ENV

   # 查看详细错误
   PERFECT21_DEBUG=true .claude/scripts/load_config.sh load
   ```

2. **Hook执行错误**
   ```bash
   # 验证Hook配置
   python3 .claude/scripts/config_validator.py .claude/config/unified_main.yaml

   # 检查Hook超时设置
   grep -n "timeout" .claude/config/unified_main.yaml
   ```

3. **Agent选择问题**
   ```bash
   # 测试Agent选择器
   echo '{"prompt": "创建用户认证系统"}' | bash .claude/hooks/smart_agent_selector.sh

   # 检查任务类型映射
   python3 -c "
   import yaml
   config = yaml.safe_load(open('.claude/config/unified_main.yaml'))
   print('任务类型:', list(config['task_types'].keys()))
   "
   ```

### 配置回滚

如果需要回滚到旧配置：

```bash
# 方法1: 使用备份恢复
cp .claude/config/migration_backup_*/config.yaml .claude/hooks/
cp .claude/config/migration_backup_*/enhancer_config.yaml .claude/hooks/
cp .claude/config/migration_backup_*/task_agent_mapping.yaml .claude/hooks/
cp .claude/config/migration_backup_*/settings.json .claude/

# 方法2: 使用legacy配置
cp .claude/config/legacy/legacy_*.yaml .claude/hooks/
# 需要手动重命名文件
```

## 📊 配置监控和维护

### 配置健康检查

```bash
# 每日检查脚本
#!/bin/bash
echo "=== Claude Enhancer 配置健康检查 ==="

# 1. 配置语法检查
echo "1. 语法检查..."
.claude/scripts/load_config.sh validate

# 2. 深度验证
echo "2. 深度验证..."
python3 .claude/scripts/config_validator.py .claude/config/unified_main.yaml

# 3. 环境配置检查
echo "3. 环境配置检查..."
for env in development testing production; do
    echo "  检查 $env 环境..."
    PERFECT21_ENV=$env .claude/scripts/load_config.sh load > /dev/null
    if [ $? -eq 0 ]; then
        echo "  ✅ $env 环境正常"
    else
        echo "  ❌ $env 环境有问题"
    fi
done

echo "=== 检查完成 ==="
```

### 配置版本管理

```bash
# 配置变更提交
git add .claude/config/unified_main.yaml
git commit -m "config: update unified configuration

- 修改Agent策略
- 更新质量门控设置
- 调整环境特定配置"

# 配置备份
cp .claude/config/unified_main.yaml .claude/config/backups/unified_main_$(date +%Y%m%d_%H%M%S).yaml
```

## 🎯 最佳实践

### 1. 配置修改流程
1. 在开发环境测试配置变更
2. 使用验证工具检查配置
3. 在测试环境验证功能
4. 提交配置变更到版本控制
5. 部署到生产环境

### 2. 环境隔离
- 开发: 宽松配置，快速迭代
- 测试: 平衡配置，重点测试
- 生产: 严格配置，质量优先

### 3. 配置安全
- 敏感信息使用环境变量
- 定期备份配置文件
- 使用版本控制跟踪变更
- 限制生产配置的修改权限

## 📞 支持和资源

### 文档资源
- **迁移报告**: `.claude/config/migration_report.md`
- **详细分析**: `.claude/config/migration_analysis.md`
- **映射关系**: `.claude/config/migration_mapping.yaml`

### 工具资源
- **配置加载器**: `.claude/scripts/load_config.sh --help`
- **配置验证器**: `python3 .claude/scripts/config_validator.py --help`
- **迁移脚本**: `.claude/scripts/migrate_config.sh --help`

### 日志文件
- **迁移日志**: `.claude/config/migration.log`
- **运行日志**: `/tmp/perfect21-unified.log`
- **验证日志**: 配置验证器输出

---

## 🎉 总结

Claude Enhancer的统一配置系统提供了：

✅ **单一配置来源** - 所有配置都在 `unified_main.yaml`
✅ **环境特定覆盖** - 开发/测试/生产环境灵活配置
✅ **自动化验证** - 语法检查、架构验证、业务规则检查
✅ **向后兼容** - 保留所有旧配置功能
✅ **强大工具** - 配置加载、验证、迁移工具齐全

使用统一配置系统，你可以更简单、更安全、更高效地管理Claude Enhancer的所有配置需求。