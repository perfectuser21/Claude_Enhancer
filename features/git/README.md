# Perfect21 Git Integration 🚀

> 个人编程助手的智能Git工作流管理系统

## ✨ 特性概览

### 🎯 核心功能
- **智能Git Hooks**: 自动化代码质量检查和团队协作
- **工作流管理**: 支持多种开发工作流（Feature/Bugfix/Hotfix）
- **任务追踪**: 个人任务管理和进度追踪
- **生产力分析**: 编程习惯分析和效率优化建议
- **智能提交**: AI辅助的提交信息生成
- **分支管理**: 自动化分支清理和冲突检测

### 🛠 技术特点
- **异步执行**: 高性能的并发操作
- **多Agent并行**: 智能选择和并行执行多个检查代理
- **缓存优化**: Git操作缓存，提升响应速度
- **个性化**: 基于个人习惯的智能推荐

## 🚀 快速开始

### 1. 初始化Perfect21 Git工作流

```bash
# 初始化Git工作流
python -m features.git.cli init

# 安装Git Hooks
python -m features.git.cli hooks install --all

# 查看仪表板
python -m features.git.cli dashboard
```

### 2. 创建开发任务

```bash
# 创建新的功能开发任务
python -m features.git.cli task create \"实现用户登录功能\" \\
  --priority high \\
  --type feature \\
  --hours 8 \\
  --tags auth user-management

# 查看所有任务
python -m features.git.cli task list
```

### 3. 开始编程会话

```bash
# 开始编程会话
python -m features.git.cli session start task_20250917_120000

# 进行开发工作...
# 编辑文件、编写代码

# 智能提交
python -m features.git.cli commit --smart --push

# 结束会话
python -m features.git.cli session end --notes \"完成登录API实现\"
```

### 4. 创建Pull Request

```bash
# 为任务创建PR
python -m features.git.cli pr --task task_20250917_120000 --target main

# 或者手动创建PR
python -m features.git.cli pr --target main --title \"实现用户登录功能\"
```

## 📋 详细使用指南

### Git Hooks管理

```bash
# 查看hooks状态
python -m features.git.cli hooks status

# 安装特定hooks
python -m features.git.cli hooks install --types pre-commit pre-push

# 测试hooks
python -m features.git.cli hooks test pre-commit

# 卸载hooks
python -m features.git.cli hooks uninstall --all
```

### 任务管理

```bash
# 更新任务进度
python -m features.git.cli task update task_20250917_120000 \\
  --progress 75 \\
  --stage testing \\
  --notes \"功能开发完成，开始测试\"

# 查看任务详情
python -m features.git.cli task show task_20250917_120000
```

### 分支管理

```bash
# 查看所有分支
python -m features.git.cli branch list

# 清理已合并分支（预览模式）
python -m features.git.cli branch cleanup --dry-run

# 自动清理安全的分支
python -m features.git.cli branch cleanup --auto
```

### 生产力分析

```bash
# 查看7天生产力报告
python -m features.git.cli productivity --days 7

# 查看项目健康度
python -m features.git.cli health --full

# 生成性能报告
python -m features.git.cli report --type performance --output my_report.json
```

### 系统维护

```bash
# 清理已合并分支和缓存
python -m features.git.cli cleanup --all --dry-run

# 查看配置
python -m features.git.cli config show

# 设置配置项
python -m features.git.cli config set auto_push true
```

## 🔧 配置说明

### 配置文件位置
- 全局配置: `~/.perfect21/git/config.yaml`
- 项目配置: `.perfect21/config.json`

### 主要配置项

```yaml
# Git Hooks配置
hooks:
  enabled:
    - pre-commit
    - pre-push
  execution:
    parallel: true
    timeout: 300

# 工作流配置
workflows:
  feature:
    branch_pattern: \"feature/*\"
    merge_strategy: \"no-ff\"
    require_pr: true

# 智能提交配置
smart_commits:
  enabled: true
  type_keywords:
    feat: [\"add\", \"new\", \"create\"]
    fix: [\"fix\", \"resolve\", \"correct\"]
```

## 📊 个人仪表板

运行 `python -m features.git.cli dashboard` 查看：

```
📊 Perfect21 个人开发仪表板
==================================================
📝 任务指标:
  总任务: 15
  已完成: 12
  活跃任务: 3
  生产力分数: 87.5

⚡ 生产力洞察:
  编程会话: 45
  总时长: 127.5h
  平均分数: 78.2

🏅 项目健康度: 92.3/100

💡 个性化建议:
  1. 最佳工作时间段：9-11点和14-16点
  2. 建议增加单次编程会话时间至45分钟
  3. 可以清理3个已合并的分支

⚡ 快速操作:
  ➕ 创建新任务
  ▶️ 开始编程
  💾 智能提交
  🧹 清理分支
  📊 查看分析
```

## 🔄 工作流类型

### Feature Development (功能开发)
- 分支模式: `feature/task-name-MMDD`
- 质量检查: 代码审查 + 安全扫描 + 测试
- 合并策略: no-ff
- 要求PR: 是

### Bug Fix (错误修复)
- 分支模式: `bugfix/issue-description`
- 质量检查: 代码审查 + 测试
- 合并策略: squash
- 要求PR: 是

### Hotfix (热修复)
- 分支模式: `hotfix/urgent-fix`
- 质量检查: 测试 + 安全扫描
- 合并策略: fast-forward
- 要求PR: 否（紧急情况）

## 🎯 智能特性

### 1. 智能提交信息生成
- 基于文件变更分析提交类型
- 自动检测影响范围
- 遵循Conventional Commits规范

### 2. 个人生产力分析
- 编程会话时间追踪
- 最佳工作时段识别
- 生产力趋势分析
- 个性化改进建议

### 3. 智能分支管理
- 自动检测可清理分支
- 合并冲突预测
- 分支保护规则
- 分支命名建议

### 4. 代码质量检查
- 多Agent并行检查
- 智能错误修复建议
- 安全漏洞检测
- 性能影响评估

## 🔌 API使用

### Python API

```python
import asyncio
from features.git import get_advanced_workflow_manager, TaskPriority, WorkflowType

async def main():
    # 获取管理器
    manager = get_advanced_workflow_manager()

    # 创建任务
    task = await manager.create_task(
        title=\"实现用户注册\",
        description=\"添加用户注册功能\",
        priority=TaskPriority.HIGH,
        workflow_type=WorkflowType.FEATURE_DEVELOPMENT
    )

    # 开始编程会话
    session = await manager.start_coding_session(task['task_id'])

    # 智能提交
    commit_result = await manager.smart_commit_and_push(
        task['task_id'],
        \"feat: 添加用户注册API\"
    )

    # 获取仪表板数据
    dashboard = await manager.get_dashboard_data()
    print(f\"当前活跃任务: {dashboard['task_metrics'].active_tasks}\")

if __name__ == \"__main__\":
    asyncio.run(main())
```

### 快捷函数

```python
from features.git import quick_start, smart_commit, start_feature_workflow

# 快速启动
result = quick_start()

# 启动功能工作流
workflow = await start_feature_workflow(\"新功能开发\")

# 智能提交
commit = await smart_commit(files=[\"src/auth.py\", \"tests/test_auth.py\"])
```

## 🧪 测试

运行完整的集成测试：

```bash
python test_git_integration.py
```

测试覆盖：
- Git Hooks管理器
- 工作流管理器
- 高级功能（任务管理、生产力分析）
- CLI接口
- 智能分支管理

## 🎨 自定义配置

### 添加自定义Hook

```python
from features.git import GitHooksManager

manager = GitHooksManager()

# 添加自定义hook配置
custom_config = {
    'name': 'custom-hook',
    'enabled': True,
    'agents': ['custom-agent'],
    'custom_script': '/path/to/custom/script.sh'
}

manager.hooks_config['custom-hook'] = custom_config
```

### 自定义工作流

```yaml
workflows:
  custom_workflow:
    branch_pattern: \"custom/*\"
    merge_strategy: \"rebase\"
    require_pr: true
    quality_gates:
      - custom-check
      - security-scan
    notification_channels:
      - slack
      - email
```

## 🚨 故障排除

### 常见问题

1. **Hooks执行失败**
   ```bash
   # 检查hooks状态
   python -m features.git.cli hooks status

   # 重新安装hooks
   python -m features.git.cli hooks install --all --force
   ```

2. **任务创建失败**
   ```bash
   # 检查Git状态
   git status

   # 确保工作目录干净
   git add . && git commit -m \"WIP\"
   ```

3. **性能问题**
   ```bash
   # 清理缓存
   python -m features.git.cli cleanup --cache

   # 检查配置
   python -m features.git.cli config show
   ```

### 调试模式

```bash
# 启用详细日志
export PERFECT21_DEBUG=1
python -m features.git.cli dashboard

# 查看执行历史
python -m features.git.cli report --type performance
```

## 📈 路线图

### v1.1 计划功能
- [ ] GitHub/GitLab API集成
- [ ] VS Code扩展
- [ ] 智能代码审查建议
- [ ] 团队协作功能

### v1.2 计划功能
- [ ] AI驱动的代码生成
- [ ] 自动化测试生成
- [ ] 性能基准测试集成
- [ ] 多语言支持

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -m 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 创建Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](../../LICENSE) 文件

## 🆘 支持

- 📧 邮件: support@perfect21.dev
- 💬 讨论: [GitHub Discussions](https://github.com/perfect21/discussions)
- 🐛 问题反馈: [GitHub Issues](https://github.com/perfect21/issues)

---

**Perfect21 Git Integration** - 让Git工作流变得智能和高效 🚀