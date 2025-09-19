# Perfect21 - Simple Rules for Better Claude Code

> **Perfect21 = Behavioral rules that Claude Code should follow**
> Not a framework, just simple guidelines and hooks

## 🎯 Core Philosophy
Perfect21 is NOT an execution system. It's just a set of rules and hooks that help Claude Code work better. Think of it as "coding standards" for AI.

## 📋 Three Simple Rules

### Rule 1: Always Use Multiple Agents (Minimum 3)
Never use just 1-2 agents. Complex tasks need multiple perspectives.

### Rule 2: Always Execute in Parallel
All agents should run in a single `function_calls` block, not sequentially.

### Rule 3: Test Failures Need Feedback Loop
When tests fail, go back to the original implementation agent to fix it.

## 🎯 Agent Selection Guide

### Authentication/Login Tasks
```yaml
Required agents: [backend-architect, security-auditor, test-engineer, api-designer, database-specialist]
Minimum: 5 agents
```

### API Development
```yaml
Required agents: [api-designer, backend-architect, test-engineer, technical-writer]
Minimum: 4 agents
```

### Database Tasks
```yaml
Required agents: [database-specialist, backend-architect, performance-engineer]
Minimum: 3 agents
```

### Frontend Tasks
```yaml
Required agents: [frontend-specialist, ux-designer, test-engineer]
Minimum: 3 agents
```

### Testing Tasks
```yaml
Required agents: [test-engineer, e2e-test-specialist, performance-tester]
Minimum: 3 agents
```

## ⚡ Quick Commands

### /parallel
Execute multiple agents in parallel for any task. This ensures you're following Perfect21 rules.

### /review
Get comprehensive code review from multiple specialized agents.

### /test
Run full test suite with proper feedback loop on failures.

## 🔨 Hooks (Automatic Enforcement)

### Claude Code Hooks (`.claude/hooks/`)
- `check_agents.sh` - Blocks execution if less than 3 agents
- `pre-edit.sh` - Validates before code changes
- `post-task.sh` - Checks health after tasks

### Git Hooks (`.git/hooks/`)
- `pre-commit` - Code quality check
- `commit-msg` - Message format validation
- `pre-push` - Final test before push

## 💡 Examples

### ❌ Wrong Way (Sequential, Few Agents)
```python
# BAD: Only 1 agent
use backend-architect to design API

# BAD: Sequential execution
use backend-architect to design
then use test-engineer to test
```

### ✅ Right Way (Parallel, Multiple Agents)
```xml
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">backend-architect</parameter>
    <parameter name="prompt">Design the API structure</parameter>
  </invoke>
  <invoke name="Task">
    <parameter name="subagent_type">security-auditor</parameter>
    <parameter name="prompt">Review for security issues</parameter>
  </invoke>
  <invoke name="Task">
    <parameter name="subagent_type">test-engineer</parameter>
    <parameter name="prompt">Create comprehensive tests</parameter>
  </invoke>
  <invoke name="Task">
    <parameter name="subagent_type">api-designer</parameter>
    <parameter name="prompt">Design REST endpoints</parameter>
  </invoke>
</function_calls>
```

## 🚀 Getting Started

1. **Hooks are already installed** - They run automatically
2. **Use `/parallel` command** - For any complex task
3. **Let hooks guide you** - They'll block bad patterns

## 📝 Git Commit Format
Always use standard prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Testing
- `refactor:` - Code refactoring
- `perf:` - Performance
- `chore:` - Maintenance

## 🎯 Remember
- Perfect21 is just rules, not a system
- Claude Code does all the work
- Hooks ensure rules are followed
- Simple is better than complex

---
*Version: 2.0 (Simplified) | Date: 2025-01-19*