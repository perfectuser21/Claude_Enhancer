# Perfect21 Installation Guide

> Complete setup guide for the Perfect21 AI-driven development workflow system

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Quick Installation](#quick-installation)
- [Step-by-Step Setup](#step-by-step-setup)
- [Configuration Verification](#configuration-verification)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)

## 🔧 System Requirements

### Prerequisites
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Git**: Version 2.20 or higher
- **Claude Code**: Latest version with Max 20X subscription
- **Shell**: Bash 4.0+ (default on most systems)
- **Python**: 3.8+ (optional, for advanced hooks)

### Recommended Setup
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 2GB free space for Perfect21 and dependencies
- **Network**: Stable internet for Claude API calls
- **Terminal**: Modern terminal with Unicode support

### Compatibility Matrix

| Platform | Status | Notes |
|----------|--------|-------|
| Linux Ubuntu 20.04+ | ✅ Fully Supported | Primary development platform |
| macOS 11+ | ✅ Fully Supported | All features work |
| Windows WSL2 | ✅ Supported | Use Ubuntu WSL distribution |
| Windows Native | ⚠️ Limited | Some hooks may not work |

## ⚡ Quick Installation

For experienced users who want to get started immediately:

```bash
# Clone or copy Perfect21 to your project
cp -r /path/to/Perfect21/.claude ./

# Run the installer
bash .claude/install.sh

# Verify installation
bash .claude/hooks/smart_agent_selector.sh < /dev/null
```

**That's it!** Perfect21 is now installed and ready to use.

## 📖 Step-by-Step Setup

### Step 1: Project Preparation

#### 1.1 Initialize Git Repository (if needed)
```bash
# Create new project
mkdir my-project && cd my-project
git init

# Or use existing project
cd existing-project
git status  # Verify it's a git repo
```

#### 1.2 Backup Existing Claude Configuration
```bash
# Check for existing .claude folder
if [ -d .claude ]; then
    echo "Existing .claude configuration found"
    mv .claude .claude.backup.$(date +%Y%m%d_%H%M%S)
    echo "Backed up to .claude.backup.*"
fi
```

### Step 2: Install Perfect21

#### 2.1 Copy Perfect21 Framework
```bash
# Option A: Copy from another project
cp -r /path/to/perfect21-project/.claude ./

# Option B: Download from repository
git clone https://github.com/your-org/perfect21-framework.git temp
cp -r temp/.claude ./
rm -rf temp
```

#### 2.2 Run Installation Script
```bash
# Execute the installer
bash .claude/install.sh
```

The installer will:
1. **Check System**: Verify git repository and permissions
2. **Clean Garbage**: Remove temporary files and caches
3. **Set Permissions**: Make all scripts executable
4. **Install Git Hooks**: Copy pre-commit and commit-msg hooks
5. **Configure Claude**: Ensure settings.json is properly configured

#### 2.3 Installation Output Example
```
🚀 Claude Enhancer 安装
========================

📝 设置执行权限...
📌 安装Git Hooks...
  备份: pre-commit → pre-commit.backup
  ✅ Git Hooks已安装
✅ Claude配置已就绪

✨ 安装完成！

📋 使用方法：
  1. Claude会自动分析任务并选择4-6-8个Agent
  2. Git提交时会自动检查代码质量
  3. 查看 .claude/README.md 了解详情

💡 工作流程：
  Phase 0-2: 需求分析和设计
  Phase 3: Agent并行开发
  Phase 4-7: 测试、提交、审查、部署

🎯 Agent策略：
  简单任务：4个Agent
  标准任务：6个Agent
  复杂任务：8个Agent

Happy coding with Claude Enhancer! 🚀
```

### Step 3: Configuration Setup

#### 3.1 Verify Settings File
```bash
# Check settings.json
cat .claude/settings.json
```

Expected content:
```json
{
  "version": "4.0.0",
  "project": "Claude Enhancer - Enforcement Loop System",
  "description": "强制循环直到符合标准",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "type": "command",
        "command": "bash .claude/hooks/smart_agent_selector.sh",
        "description": "智能Agent选择器 - 4-6-8策略",
        "timeout": 5000
      }
    ],
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "bash .claude/hooks/branch_helper.sh",
        "description": "Branch检查和工作流提醒",
        "timeout": 1000
      }
    ]
  },
  "environment": {
    "CLAUDE_ENHANCER_MODE": "enforcement",
    "MIN_AGENTS": "3",
    "MAX_RETRIES": "3",
    "ENFORCE_PARALLEL": "true"
  }
}
```

#### 3.2 Customize Environment Variables
```bash
# Edit environment settings in .claude/settings.json
nano .claude/settings.json

# Available options:
# - CLAUDE_ENHANCER_MODE: "advisory" | "enforcement" | "strict"
# - MIN_AGENTS: Minimum number of agents (default: 3)
# - MAX_RETRIES: Maximum hook retries (default: 3)
# - ENFORCE_PARALLEL: Force parallel agent execution (default: true)
```

### Step 4: Agent Configuration

#### 4.1 Review Available Agents
```bash
# List all available agents
find .claude/agents -name "*.md" | sort
```

You should see 56 specialized agents across categories:
- **Development**: backend-architect, frontend-specialist, database-specialist
- **Quality**: test-engineer, security-auditor, performance-engineer
- **Specialized**: fintech-specialist, healthcare-dev, embedded-engineer
- **Process**: technical-writer, code-reviewer, cleanup-specialist

#### 4.2 Verify Agent Selection Logic
```bash
# Test the smart agent selector
echo '{"prompt": "Create a simple bug fix", "phase": "3"}' | bash .claude/hooks/smart_agent_selector.sh
```

Expected output:
```
🤖 Claude Enhancer Agent智能选择 (4-6-8策略)
═══════════════════════════════════════════

📝 任务: Create a simple bug fix...

📊 复杂度: 🟢 简单任务
⚡ 执行模式: 快速模式 (4 Agents)
⏱️  预计时间: 5-10分钟

👥 推荐Agent组合:
  4个Agent组合：
    1. backend-engineer - 实现修复
    2. test-engineer - 验证测试
    3. code-reviewer - 代码审查
    4. technical-writer - 更新文档
```

## ✅ Configuration Verification

### Test 1: Hook Execution
```bash
# Test UserPromptSubmit hook
echo "test prompt" | bash .claude/hooks/branch_helper.sh
```

### Test 2: Agent Selection
```bash
# Test different complexity levels
echo '{"prompt": "fix typo"}' | bash .claude/hooks/smart_agent_selector.sh
echo '{"prompt": "design new microservice architecture"}' | bash .claude/hooks/smart_agent_selector.sh
```

### Test 3: Git Hooks
```bash
# Test pre-commit hook
.git/hooks/pre-commit

# Test commit-msg hook (if file exists)
echo "test: sample commit" | .git/hooks/commit-msg /dev/stdin
```

### Test 4: File Permissions
```bash
# Verify all scripts are executable
find .claude -name "*.sh" -not -executable
# Should return empty (no results)
```

### Verification Checklist

- [ ] ✅ Git repository initialized
- [ ] ✅ .claude folder copied successfully
- [ ] ✅ settings.json exists and valid
- [ ] ✅ All .sh files are executable
- [ ] ✅ Git hooks installed in .git/hooks/
- [ ] ✅ Agent selector responds correctly
- [ ] ✅ Branch helper runs without errors
- [ ] ✅ Pre-commit hook works
- [ ] ✅ 56 agent files present

## ⚙️ Advanced Configuration

### Custom Agent Selection Rules

Create custom complexity detection:

```bash
# Edit smart_agent_selector.sh
nano .claude/hooks/smart_agent_selector.sh

# Add custom keywords to determine_complexity function
# Example: Add "machine learning" → complex
```

### Environment-Specific Settings

```bash
# Create environment-specific configs
cp .claude/settings.json .claude/settings.production.json
cp .claude/settings.json .claude/settings.development.json

# Switch based on environment
if [ "$NODE_ENV" = "production" ]; then
    cp .claude/settings.production.json .claude/settings.json
fi
```

### Custom Hook Integration

```bash
# Add custom pre-task hook
cat > .claude/hooks/custom-pre-task.sh << 'EOF'
#!/bin/bash
echo "🎯 Custom pre-task validation"
# Add your custom logic here
EOF

chmod +x .claude/hooks/custom-pre-task.sh

# Update settings.json to include custom hook
```

### Git Hook Customization

```bash
# Customize pre-commit checks
nano .claude/git-hooks/pre-commit

# Add project-specific validations:
# - Code style enforcement
# - Test coverage requirements
# - Custom security scans
# - Performance benchmarks
```

## 🚀 Post-Installation Setup

### 1. Create Initial Branch Structure
```bash
# Set up recommended branch structure
git checkout -b feature/setup-perfect21
git add .claude/
git commit -m "feat: setup Perfect21 workflow system

- Install Claude Enhancer framework
- Configure 8-phase workflow
- Add 4-6-8 agent strategy
- Setup git hooks for quality gates"
```

### 2. Configure Team Settings
```bash
# Share Perfect21 configuration with team
echo ".claude/" >> .gitignore  # Don't ignore - share with team
git add .gitignore

# Document for team
echo "Perfect21 is configured for this project" >> README.md
echo "Run: bash .claude/install.sh after cloning" >> README.md
```

### 3. Test Full Workflow
```bash
# Test complete workflow
echo "Let's test Perfect21 with a simple task" > test-perfect21.md
git add test-perfect21.md
git commit -m "test: validate Perfect21 installation"

# This should trigger:
# 1. Branch helper (Phase 0)
# 2. Agent selector (Phase 3)
# 3. Pre-commit hooks (Phase 5)
```

## 📊 Performance Optimization

### Resource Management
```bash
# Configure resource limits
export CLAUDE_ENHANCER_TIMEOUT=30  # seconds
export CLAUDE_ENHANCER_MAX_AGENTS=8
export CLAUDE_ENHANCER_LOG_LEVEL=INFO
```

### Logging Configuration
```bash
# Enable detailed logging
mkdir -p .claude/logs
export CLAUDE_ENHANCER_LOG_FILE=".claude/logs/enhancer.log"

# Rotate logs weekly
echo "0 0 * * 0 find .claude/logs -name '*.log' -mtime +7 -delete" | crontab -
```

## 🔍 Validation Commands

### Quick Health Check
```bash
# Run comprehensive health check
bash << 'EOF'
echo "🏥 Perfect21 Health Check"
echo "========================"

# Check git
if git status &>/dev/null; then echo "✅ Git repository"; else echo "❌ Not a git repo"; fi

# Check .claude
if [ -d .claude ]; then echo "✅ .claude folder"; else echo "❌ Missing .claude"; fi

# Check settings
if [ -f .claude/settings.json ]; then echo "✅ settings.json"; else echo "❌ Missing settings"; fi

# Check executables
EXEC_COUNT=$(find .claude -name "*.sh" -executable | wc -l)
echo "✅ Executable scripts: $EXEC_COUNT"

# Check git hooks
if [ -f .git/hooks/pre-commit ]; then echo "✅ Git hooks installed"; else echo "❌ Git hooks missing"; fi

# Check agents
AGENT_COUNT=$(find .claude/agents -name "*.md" 2>/dev/null | wc -l)
echo "✅ Available agents: $AGENT_COUNT"

echo "========================"
if [ -f .claude/settings.json ] && [ -d .claude/agents ] && [ $AGENT_COUNT -gt 50 ]; then
    echo "🎉 Perfect21 is ready!"
else
    echo "⚠️  Installation may be incomplete"
fi
EOF
```

### Test Agent Selection
```bash
# Test all complexity levels
for task in "fix typo" "add new feature" "refactor entire system"; do
    echo "Testing: $task"
    echo "{\"prompt\": \"$task\"}" | bash .claude/hooks/smart_agent_selector.sh 2>&1 | grep "复杂度"
    echo ""
done
```

## 🆘 Common Issues

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for detailed problem resolution.

### Quick Fixes

**Permission denied on hooks:**
```bash
chmod +x .claude/hooks/*.sh
chmod +x .git/hooks/*
```

**Git hooks not triggering:**
```bash
# Reinstall git hooks
bash .claude/install.sh
```

**Agent selector not working:**
```bash
# Check if bash and jq are available
which bash jq
# Reinstall dependencies if needed
```

---

## 📚 Next Steps

1. **Read the User Guide**: [CLAUDE.md](./CLAUDE.md)
2. **Explore Agents**: Browse `.claude/agents/` directory
3. **Customize Workflow**: Edit `.claude/settings.json`
4. **Check Troubleshooting**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
5. **API Reference**: [API_REFERENCE.md](./API_REFERENCE.md)

## 🎯 Success Criteria

After successful installation, you should be able to:

✅ **Execute Tasks**: Claude automatically selects 4-6-8 agents based on complexity
✅ **Quality Gates**: Git hooks prevent low-quality commits
✅ **Workflow Guidance**: Phase reminders keep you on track
✅ **Smart Automation**: Cleanup and optimization happen automatically
✅ **Team Collaboration**: Consistent workflow across all team members

Perfect21 is now ready to accelerate your development with AI-driven workflows! 🚀