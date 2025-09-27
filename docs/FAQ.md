# 🤔 Claude Enhancer 5.1 常见问题解答

> **快速找到你需要的答案**

## 📚 目录

- [🚀 安装和配置](#安装和配置)
- [⚡ 基础使用](#基础使用)
- [🔧 工作流问题](#工作流问题)
- [🤖 Agent相关](#agent相关)
- [🛡️ 质量和安全](#质量和安全)
- [⚠️ 故障排除](#故障排除)
- [🎯 性能优化](#性能优化)
- [🔗 集成问题](#集成问题)
- [📊 监控和日志](#监控和日志)
- [🆘 获取帮助](#获取帮助)

---

## 🚀 安装和配置

### Q: Claude Enhancer 5.1 的系统要求是什么？
**A:**
- **操作系统**: Windows 10+, macOS 10.15+, Linux (Ubuntu 18.04+)
- **Node.js**: 16.x 或更高版本
- **Python**: 3.9 或更高版本
- **Claude Code CLI**: 最新版本
- **内存**: 最少 4GB RAM，推荐 8GB+
- **存储**: 至少 2GB 可用空间

### Q: 如何验证安装是否成功？
**A:**
```bash
# 检查核心组件
node --version          # 应显示 v16.x+
python --version        # 应显示 Python 3.9+
claude --version        # 应显示 Claude Code CLI 版本

# 检查 Claude Enhancer
ls .claude/             # 应显示配置文件
cat .claude/settings.json  # 检查配置内容

# 测试工作流
echo "P1" > .phase/current
cat .phase/current      # 应显示 P1
```

### Q: 安装后Hook不工作怎么办？
**A:**
```bash
# 重新安装Git Hooks
./.claude/install.sh

# 检查Hook权限
ls -la .git/hooks/
chmod +x .git/hooks/*

# 验证Hook功能
git add .
git commit -m "test"    # 应该触发pre-commit检查
```

### Q: 可以在现有项目中安装Claude Enhancer吗？
**A:** 可以！按以下步骤操作：
```bash
# 1. 备份现有配置
cp -r .git/hooks .git/hooks.backup

# 2. 复制Claude Enhancer配置
cp -r /path/to/claude-enhancer/.claude ./

# 3. 选择性安装Hook（避免覆盖现有Hook）
./.claude/install.sh --merge

# 4. 手动合并冲突的Hook
# 编辑 .git/hooks/ 中的文件，合并你的自定义Hook
```

---

## ⚡ 基础使用

### Q: 如何开始第一个项目？
**A:** 最简单的方式：
```bash
# 创建项目目录
mkdir my-project && cd my-project

# 初始化Claude Enhancer
cp -r .claude ./
./.claude/install.sh

# 在Claude Code中说：
"帮我创建一个简单的网站，包含首页和联系页面"
```

### Q: Claude Enhancer支持哪些编程语言？
**A:**
- **前端**: JavaScript, TypeScript, React, Vue, Angular
- **后端**: Python (FastAPI/Django), Node.js, Go, Java
- **数据库**: PostgreSQL, MySQL, MongoDB, Redis
- **移动端**: React Native, Flutter
- **其他**: Docker, Kubernetes, CI/CD配置

### Q: 如何指定技术栈？
**A:** 在请求中明确说明：
```
"使用Python FastAPI和PostgreSQL创建一个用户管理API"
"用React TypeScript做一个现代化的仪表板界面"
"构建一个基于微服务架构的电商平台，使用Docker和Kubernetes"
```

### Q: 可以中途改变技术栈吗？
**A:** 可以，但最好在早期Phase（P1-P2）进行：
```
"我想把后端从Node.js改为Python FastAPI，请帮我重新设计架构"
```

---

## 🔧 工作流问题

### Q: 6-Phase工作流是强制的吗？
**A:** 不是强制的，但强烈推荐：
- **灵活模式**: 可以跳过某些Phase或合并执行
- **严格模式**: 按顺序完成所有Phase（推荐新手）
- **自定义模式**: 根据项目需要调整Phase内容

配置方式：
```json
{
  "workflow": {
    "mode": "flexible",     // strict|flexible|custom
    "required_phases": ["P1", "P3", "P6"],
    "auto_progression": true
  }
}
```

### Q: 如何查看当前Phase状态？
**A:**
```bash
# 查看当前Phase
cat .phase/current

# 查看Phase历史
ls .phase/history/

# 查看详细状态
.claude/scripts/status.sh
```

### Q: Phase推进失败怎么办？
**A:**
```bash
# 1. 查看错误信息
cat .claude/logs/workflow.log

# 2. 检查Phase要求
cat .phase/requirements/P3.md  # 例如检查P3要求

# 3. 手动修复问题后推进
echo "P4" > .phase/current

# 4. 或者重新开始当前Phase
.claude/scripts/reset_phase.sh P3
```

### Q: 可以同时运行多个项目吗？
**A:** 可以，每个项目独立管理：
```bash
# 项目A
cd project-a
cat .phase/current  # 可能是P3

# 项目B
cd ../project-b
cat .phase/current  # 可能是P1

# 每个项目有独立的配置和状态
```

---

## 🤖 Agent相关

### Q: 如何知道选择哪些Agent？
**A:** 系统提供三种方式：
1. **自动选择**: 系统根据任务描述智能选择
2. **推荐系统**: 运行 `.claude/hooks/smart_agent_selector.sh`
3. **手动指定**: 明确说明需要的Agent

```bash
# 查看可用Agent
ls .claude/agents/

# 获取推荐
"分析这个任务需要哪些类型的专家"

# 手动指定
"使用database-specialist、api-designer、test-engineer来处理这个API设计任务"
```

### Q: Agent数量有限制吗？
**A:**
- **技术限制**: 最多同时8个Agent
- **性能考虑**: 4-6个Agent是最佳实践
- **复杂度匹配**:
  - 简单任务: 4个Agent
  - 标准任务: 6个Agent
  - 复杂任务: 8个Agent

### Q: 可以创建自定义Agent吗？
**A:** 目前不支持，但可以：
```bash
# 1. 定制现有Agent行为
编辑 .claude/agents/[agent-name]/config.json

# 2. 组合多个Agent
"让frontend-dev和ui-designer协作设计用户界面"

# 3. 使用专业Agent替代
"需要区块链开发 → 使用backend-architect + security-auditor"
```

### Q: Agent执行失败怎么办？
**A:**
```bash
# 1. 查看Agent日志
cat .claude/logs/agents/[agent-name].log

# 2. 重试失败的Agent
"重新运行test-engineer进行测试"

# 3. 更换Agent
"用performance-engineer替换刚才的backend-architect"
```

---

## 🛡️ 质量和安全

### Q: 如何确保代码质量？
**A:** Claude Enhancer提供三层质量保证：

**1. Workflow层质量门禁**:
```bash
# 每个Phase都有质量要求
cat .phase/gates/P3.yaml  # P3阶段的质量门禁
```

**2. Claude Hooks智能检查**:
```bash
# 运行质量检查
.claude/hooks/quality_gate.sh

# 查看建议
cat .claude/temp/quality_suggestions.md
```

**3. Git Hooks强制验证**:
```bash
# 提交前自动检查
git add .
git commit -m "feat: add user auth"  # 自动触发质量检查
```

### Q: 如何配置代码规范？
**A:**
```bash
# 编辑代码规范配置
vim .claude/config/coding_standards.json

# 示例配置
{
  "linting": {
    "javascript": "eslint",
    "python": "flake8",
    "typescript": "tslint"
  },
  "formatting": {
    "javascript": "prettier",
    "python": "black"
  },
  "testing": {
    "coverage_threshold": 80,
    "required_test_types": ["unit", "integration"]
  }
}
```

### Q: 如何处理安全漏洞？
**A:**
```bash
# 1. 运行安全扫描
.claude/scripts/security_scan.sh

# 2. 查看安全报告
cat .claude/reports/security_audit.json

# 3. 修复高危漏洞
"使用security-auditor修复刚才发现的SQL注入漏洞"

# 4. 重新扫描验证
.claude/scripts/security_scan.sh --verify
```

---

## ⚠️ 故障排除

### Q: Claude Enhancer无响应怎么办？
**A:**
```bash
# 1. 检查Claude Code连接
claude auth status

# 2. 重启Claude Code会话
# 在Claude Code中输入: /restart

# 3. 检查配置文件
cat .claude/settings.json | jq .  # 验证JSON格式

# 4. 查看系统日志
tail -f .claude/logs/system.log
```

### Q: Hook执行超时怎么解决？
**A:**
```bash
# 1. 调整Hook超时设置
vim .claude/config/hooks.json
{
  "timeout": 5000,        # 增加到5秒
  "retry_count": 3,
  "fallback_mode": true   # 启用回退模式
}

# 2. 禁用特定Hook（临时）
mv .claude/hooks/slow_hook.sh .claude/hooks/slow_hook.sh.disabled

# 3. 优化Hook性能
.claude/scripts/optimize_hooks.sh
```

### Q: 内存不足错误如何处理？
**A:**
```bash
# 1. 启用懒加载模式
vim .claude/settings.json
{
  "performance": {
    "lazy_loading": true,
    "cache_limit": 100,
    "memory_threshold": 0.8
  }
}

# 2. 清理缓存
.claude/scripts/clear_cache.sh

# 3. 减少并发Agent数量
"这次只使用4个Agent而不是8个"
```

### Q: Git冲突怎么解决？
**A:**
```bash
# 1. 自动解决简单冲突
git status
git add .
git commit -m "resolve conflicts"

# 2. 让Claude Enhancer协助
"帮我解决Git合并冲突，保留用户认证相关的修改"

# 3. 重置到安全状态
git reset --hard HEAD~1  # 回退到冲突前状态
```

---

## 🎯 性能优化

### Q: 如何提升Claude Enhancer性能？
**A:**

**1. 硬件优化**:
```bash
# 检查系统资源
htop
df -h

# 推荐配置
- CPU: 4核心以上
- 内存: 8GB以上
- 存储: SSD硬盘
```

**2. 配置优化**:
```json
{
  "performance": {
    "lazy_loading": true,
    "parallel_agents": 6,
    "cache_enabled": true,
    "memory_limit": "4GB"
  }
}
```

**3. 项目优化**:
```bash
# 清理无用文件
.claude/scripts/cleanup.sh

# 压缩日志文件
.claude/scripts/compress_logs.sh

# 优化依赖
npm prune
pip autoremove
```

### Q: Agent执行速度慢怎么办？
**A:**
```bash
# 1. 启用Agent缓存
vim .claude/config/agents.json
{
  "cache_results": true,
  "cache_duration": 3600,
  "parallel_execution": true
}

# 2. 减少Agent数量
"这个简单任务只用frontend-dev和test-engineer两个Agent"

# 3. 使用专门的性能Agent
"用performance-engineer分析和优化系统性能"
```

---

## 🔗 集成问题

### Q: 如何与现有CI/CD集成？
**A:**

**GitHub Actions集成**:
```yaml
# .github/workflows/claude-enhancer.yml
name: Claude Enhancer CI
on: [push, pull_request]
jobs:
  claude-check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Run Claude Enhancer Checks
      run: |
        .claude/scripts/ci_check.sh
        .claude/scripts/quality_gate.sh
```

**Jenkins集成**:
```groovy
pipeline {
    agent any
    stages {
        stage('Claude Enhancer Check') {
            steps {
                sh '.claude/scripts/ci_check.sh'
            }
        }
    }
}
```

### Q: 如何与IDE集成？
**A:**
```bash
# VS Code集成
cp .claude/integrations/vscode/* .vscode/

# JetBrains集成
cp .claude/integrations/jetbrains/* .idea/

# Vim/Neovim集成
cp .claude/integrations/vim/.vimrc ~/
```

### Q: 如何与Docker集成？
**A:**
```dockerfile
# Dockerfile
FROM node:16
COPY .claude /app/.claude
RUN chmod +x /app/.claude/scripts/*
WORKDIR /app
CMD [".claude/scripts/docker_start.sh"]
```

---

## 📊 监控和日志

### Q: 如何查看系统运行状态？
**A:**
```bash
# 实时状态监控
.claude/scripts/status.sh --live

# 性能仪表板
.claude/scripts/dashboard.sh

# 生成状态报告
.claude/scripts/health_check.sh > status_report.txt
```

### Q: 日志文件太大怎么办？
**A:**
```bash
# 配置日志轮转
vim .claude/config/logging.json
{
  "log_rotation": {
    "max_size": "100MB",
    "max_files": 10,
    "compress": true
  }
}

# 手动清理日志
.claude/scripts/clean_logs.sh --older-than 7days

# 实时日志过滤
tail -f .claude/logs/system.log | grep ERROR
```

### Q: 如何监控Agent性能？
**A:**
```bash
# Agent性能报告
.claude/scripts/agent_performance.sh

# 实时Agent监控
watch -n 5 '.claude/scripts/agent_status.sh'

# 生成性能图表
.claude/scripts/generate_charts.sh
```

---

## 🆘 获取帮助

### Q: 遇到问题时应该怎么做？
**A:**
**1. 自助排查**:
```bash
# 运行诊断脚本
.claude/scripts/diagnose.sh

# 查看系统健康状态
.claude/scripts/health_check.sh

# 收集错误信息
.claude/scripts/collect_logs.sh
```

**2. 查看文档**:
- [用户指南](./USER_GUIDE.md) - 详细使用说明
- [API参考](./API_REFERENCE_v1.0.md) - 开发者文档
- [部署指南](./DEPLOYMENT_GUIDE.md) - 部署相关问题

**3. 社区支持**:
- GitHub Issues - 报告Bug和功能请求
- 官方论坛 - 社区讨论
- Discord/Slack - 实时聊天支持

### Q: 如何报告Bug？
**A:**
```bash
# 1. 收集诊断信息
.claude/scripts/bug_report.sh

# 2. 准备以下信息：
- Claude Enhancer版本
- 操作系统和版本
- 重现步骤
- 错误日志
- 期望行为 vs 实际行为

# 3. 提交到GitHub Issues
# 使用模板: .claude/templates/bug_report.md
```

### Q: 如何请求新功能？
**A:**
```bash
# 1. 检查是否已存在类似功能
grep -r "功能关键词" .claude/

# 2. 使用功能请求模板
cp .claude/templates/feature_request.md new_feature.md

# 3. 详细描述：
- 使用场景
- 期望功能
- 实现建议
- 优先级
```

### Q: 如何获得技术支持？
**A:**
- **紧急问题**: support@claude-enhancer.com
- **一般咨询**: help@claude-enhancer.com
- **功能建议**: feature@claude-enhancer.com
- **文档反馈**: docs@claude-enhancer.com

---

## 🎉 快速链接

- **[快速开始](./QUICK_START.md)** - 5分钟上手指南
- **[用户指南](./USER_GUIDE.md)** - 完整使用文档
- **[API参考](./API_REFERENCE_v1.0.md)** - 开发者文档
- **[发布说明](./RELEASE_NOTES_v1.0.md)** - 版本更新内容
- **[部署指南](./DEPLOYMENT_GUIDE.md)** - 生产环境部署

---

**💡 提示**: 这个FAQ文档会持续更新，如果你的问题没有在这里找到答案，请通过上述方式联系我们！

*最后更新: 2025-09-27*