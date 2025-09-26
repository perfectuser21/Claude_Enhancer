# Claude Enhancer 5.0

> AI-Driven Development Framework with 8-Phase Workflow and Multi-Agent Architecture

Claude Enhancer 5.0 is a comprehensive development framework designed to enhance AI-assisted programming through structured workflows, intelligent agent orchestration, and quality assurance systems.

## 🚀 Quick Start

### 安装 (Installation)

1. **系统要求**:
   - Git 2.0+, Bash 4.0+, Python 3.x
   - Node.js (可选，用于构建测试)
   - Linux/MacOS (Windows请使用WSL)

2. **自动安装** (推荐):
   ```bash
   # 克隆仓库
   git clone [repository-url]
   cd Claude\ Enhancer\ 5.0

   # 运行安装脚本
   bash .claude/install.sh

   # 初始化P1-P6 Workflow系统
   ./.workflow/executor.sh init
   ```

3. **验证安装**:
   ```bash
   # 检查workflow状态
   ./.workflow/executor.sh status

   # 检查Git Hooks
   ls -la .git/hooks/ | grep -E "(pre-commit|commit-msg|pre-push)"

   # 检查版本
   grep "version" .claude/settings.json
   ```

4. **故障排除**:
   ```bash
   # 如果executor.sh不存在
   bash src/workflow/install_auto_trigger.sh

   # 如果hooks未生效
   cp .claude/git-hooks/* .git/hooks/
   chmod +x .git/hooks/*
   ```

### 使用方法 (Usage)

1. **P1-P6 Workflow自动化流程**:
   ```bash
   # 1. 提供需求给Claude Code (P1)
   cat .workflow/prompts/P1.txt
   # Claude将生成 docs/PLAN.md

   # 2. 系统自动推进
   ./.workflow/executor.sh validate  # 验证并推进到下一阶段
   ./.workflow/executor.sh next      # 强制进入下一阶段

   # 3. 监控进度
   src/workflow/dashboard.sh         # 实时监控面板
   ```

2. **完整的Phase流程**:
   - **P1 Plan**: 需求分析 → docs/PLAN.md
   - **P2 Skeleton**: 搭建骨架 → src/**目录结构
   - **P3 Implement**: 8个Agent并行开发 → 功能实现
   - **P4 Test**: 测试验证 → TEST-REPORT.md
   - **P5 Review**: 代码审查 → REVIEW.md (APPROVE/REWORK)
   - **P6 Docs & Release**: 文档和发布 → 打tag发布

3. **并行Agent策略**:
   ```bash
   # 查看当前phase允许的agent数量
   cat .limits/$(cat .phase/current)/max

   # P1-P6对应的并行限制
   # P1: 4个agent (规划)
   # P2: 6个agent (设计)
   # P3: 8个agent (实现)
   # P4: 6个agent (测试)
   # P5: 4个agent (审查)
   # P6: 2个agent (发布)
   ```

## 🏗️ Architecture Overview

### Core Components

```
Claude Enhancer 5.0/
├── .claude/                    # Framework configuration
│   ├── settings.json           # Claude settings
│   ├── WORKFLOW.md            # 8-Phase workflow guide
│   ├── AGENT_STRATEGY.md      # 4-6-8 agent strategy
│   ├── hooks/                 # Claude hooks (non-blocking)
│   └── git-hooks/             # Git hooks (quality gates)
├── docs/                      # Documentation templates
├── src/                       # Source code
└── tests/                     # Test files
```

### Agent System

**61 Professional Agents**:
- **56 Standard Agents**: Covering full-stack development
- **5 System Agents**: Core orchestration and enhancement
- **Dynamic Selection**: Choose 4-6-8 agents based on task complexity

### Quality Assurance

**Three-Layer Quality System**:
1. **Workflow Layer**: 8-Phase structured development
2. **Claude Hooks**: Real-time assistance (non-blocking)
3. **Git Hooks**: Code quality gates

## 🛠️ Features

### 8-Phase Workflow System
- **Phase 0**: Automated branch creation
- **Phase 1-2**: Requirements analysis and design
- **Phase 3**: Multi-agent implementation
- **Phase 4**: Comprehensive testing
- **Phase 5**: Quality-assured commits
- **Phase 6**: Structured code review
- **Phase 7**: Deployment with cleanup

### Smart Agent Orchestration
- **4-Agent Mode**: Quick tasks (5-10 minutes)
- **6-Agent Mode**: Standard development (15-20 minutes)
- **8-Agent Mode**: Complex features (25-30 minutes)
- **Parallel Execution**: All agents work simultaneously

### Intelligent Features
- **Smart Document Loading**: Prevents context pollution
- **Non-Blocking Hooks**: Assistance without interruption
- **Automatic Cleanup**: Code formatting and optimization
- **Performance Monitoring**: Real-time system monitoring

## 📖 Usage Examples

### Example 1: Simple Bug Fix (4 Agents)
```bash
# Phase 0: Create branch
git checkout -b bugfix/login-validation

# Phase 1-2: Analyze and design
# Use Claude Code to understand the issue and plan fix

# Phase 3: Implement with 4 agents
# bug-hunter, code-optimizer, test-engineer, security-auditor

# Phase 4-7: Test, commit, review, deploy
```

### Example 2: New Feature (6 Agents)
```bash
# Phase 0: Create branch
git checkout -b feature/user-dashboard

# Phase 3: Implement with 6 agents
# frontend-developer, backend-architect, database-specialist,
# ui-designer, test-engineer, technical-writer

# Follow through all phases
```

### Example 3: Major Refactoring (8 Agents)
```bash
# Phase 0: Create branch
git checkout -b refactor/api-restructure

# Phase 3: Implement with 8 agents
# backend-architect, api-designer, database-specialist,
# security-auditor, performance-engineer, test-engineer,
# technical-writer, code-optimizer

# Complete full workflow
```

## ⚙️ Configuration

### Claude Hooks Configuration
Located in `.claude/hooks/`:
- `branch_helper.sh`: Branch creation assistance
- `smart_agent_selector.sh`: Intelligent agent selection
- `quality_gate.sh`: Quality recommendations
- `performance_monitor.sh`: Performance tracking
- `error_handler.sh`: Error resolution assistance

### Git Hooks Configuration
Located in `.claude/git-hooks/` (installed to `.git/hooks/`):
- `pre-commit`: Code quality checks
- `commit-msg`: Message formatting
- `pre-push`: Pre-deployment validation

### Agent Configuration
Located in `.claude/agents/`:
- 56 standard agents for various development tasks
- 5 system agents for framework management
- Dynamic selection based on task requirements

## 🔧 Customization

### Adding Custom Agents
1. Create agent file in `.claude/agents/`
2. Follow the agent template structure
3. Update agent selection logic in hooks

### Modifying Workflows
1. Edit `.claude/WORKFLOW.md` for process changes
2. Update hooks in `.claude/hooks/` directory
3. Modify git hooks in `.claude/git-hooks/`

### Adjusting Quality Gates
1. Modify quality criteria in `quality_gate.sh`
2. Update git hook validation rules
3. Adjust performance thresholds in monitoring

## 🔍 注意事项 (Important Notes)

### 核心限制
1. **Agent调用规则**:
   - ✅ 只有主Claude Code可以调用SubAgent
   - ❌ SubAgent不能调用其他SubAgent（防止死循环）
   - ✅ 支持最多8个Agent并行执行

2. **Hook特性**:
   - 所有Claude Hooks都是**非阻塞的** (blocking: false)
   - 超时自动跳过，不影响主流程
   - Git Hooks可以配置为强制阻塞

3. **P1-P6 Workflow强制规则**:
   - Gates验证失败会阻止phase推进
   - 每个phase只能修改白名单内的文件
   - 3次重试失败后系统暂停，需人工介入

### 性能考虑
- Dashboard刷新间隔: 2秒（可配置）
- Hook超时: 500-3000ms
- 并行Agent内存限制: 每个<100MB
- 日志文件自动轮转: 100MB/天

### 安全注意
- 不要使用`--force`绕过Gates验证（除非紧急）
- 定期检查`permission_violations.log`
- 敏感信息不要提交到仓库
- 使用环境变量管理配置

### 故障恢复
```bash
# Phase回滚
./.workflow/executor.sh reset

# 清除失败状态
rm -f FAILED-REPORT.md
./.workflow/executor.sh goto P1

# 完全卸载
rm -rf .workflow src/workflow tests/workflow
git checkout -- .
```

### Performance Considerations
- Smart document loading prevents context overflow
- Agent selection impacts processing time
- Hook timeouts prevent system delays
- Automatic cleanup optimizes performance

### Security Notes
- Git hooks validate code before commits
- Security auditing integrated in agent system
- Sensitive data protection in all phases
- Secure hook installation process

### Max 20X Optimization
- Designed for quality over token efficiency
- Intelligent loading prevents Claude being killed
- No artificial limitations on processing
- Focus on best results regardless of computational cost

## 🤝 Contributing

1. Fork the repository
2. Create feature branch following Phase 0
3. Follow the 8-Phase development workflow
4. Use appropriate agent count (4-6-8)
5. Ensure all quality gates pass
6. Submit pull request with comprehensive review

## 📝 Documentation

- **Framework Guide**: `.claude/WORKFLOW.md`
- **Agent Strategy**: `.claude/AGENT_STRATEGY.md`
- **Architecture Docs**: `.claude/ARCHITECTURE/`
- **API Documentation**: `docs/api/`
- **Test Reports**: `docs/TEST-REPORT.md`
- **Change Log**: `docs/CHANGELOG.md`

## 📊 Project Status

Current Version: **5.0.0**
Development Phase: **Active Development**
Quality Status: **Production Ready**
Test Coverage: **Comprehensive**

## 📞 Support

- **Framework Issues**: Check `.claude/hooks/error_handler.sh`
- **Documentation**: Refer to `docs/` directory
- **Quality Issues**: Review `.claude/hooks/quality_gate.sh`
- **Performance**: Monitor with `performance_monitor.sh`

---

*Claude Enhancer 5.0 - Empowering AI-Driven Development with Structure, Intelligence, and Quality*