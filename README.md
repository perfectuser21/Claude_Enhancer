# Perfect21 - Simple Rules for Better AI Coding

> Making Claude Code work smarter, not harder

## What is Perfect21?

Perfect21 is a simple set of rules and hooks that help Claude Code write better code. It's not a framework or system - just guidelines that get automatically enforced.

Think of it as "coding standards" but for AI.

## The 3 Core Rules

1. **Use Multiple Agents** - Never use just 1-2 agents, always 3+
2. **Execute in Parallel** - All agents run together, not one by one
3. **Feedback Loop on Failures** - When tests fail, fix them properly

## Quick Start

Perfect21 is already configured. Just use Claude Code normally and the hooks will guide you:

```bash
# Good - triggers parallel execution with multiple agents
"Help me build a login system"

# The hooks will ensure Claude Code:
# - Uses 5 agents (backend, security, test, api, database)
# - Runs them in parallel
# - Fixes any test failures properly
```

## Project Structure

```
Perfect21/
├── .claude/
│   ├── hooks/          # Automatic rule enforcement
│   └── commands/       # Quick commands (/parallel, /review, /test)
├── rules/
│   └── agent_rules.yaml  # Agent selection rules
├── CLAUDE.md           # Rules for Claude Code to follow
└── README.md           # This file
```

## Commands

- `/parallel` - Execute task with multiple agents in parallel
- `/review` - Get comprehensive code review
- `/test` - Run tests with feedback loop

## How It Works

1. **You ask Claude Code to do something**
2. **Hooks check if the approach follows the rules**
3. **If not, hooks block and suggest the right way**
4. **Claude Code executes with proper agent selection**

## Examples

### Wrong Way ❌
```
Claude Code: I'll use backend-architect to design this...
Hook: ⚠️ You need at least 3 agents!
```

### Right Way ✅
```
Claude Code: I'll use 5 agents in parallel:
- backend-architect (design)
- security-auditor (security)
- test-engineer (tests)
- api-designer (endpoints)
- database-specialist (schema)
```

## Agent Combinations

Perfect21 knows which agents work best together:

| Task Type | Required Agents | Count |
|-----------|----------------|-------|
| Authentication | backend, security, test, api, database | 5 |
| API Development | api, backend, test, docs | 4 |
| Database | database, backend, performance | 3 |
| Frontend | frontend, ux, test | 3 |
| Testing | test, e2e, performance | 3 |

## Why Perfect21?

- **Better Code Quality** - Multiple perspectives catch more issues
- **Faster Development** - Parallel execution saves time
- **Automatic Standards** - Hooks enforce best practices
- **Zero Configuration** - Already set up and ready

## Installation

Already installed! Just start using Claude Code.

## License

MIT

---

*Perfect21 v2.0 - Simplified and effective*