# 🔌 Claude Enhancer API参考文档

> Claude Enhancer系统的完整API参考，包括Hook接口、Agent系统、配置选项和集成接口

## 📚 文档版本信息
- **版本**: v4.1.0
- **更新日期**: 2024年1月
- **状态**: 生产就绪
- **兼容性**: 向后兼容v4.0.x

## 📋 Table of Contents

- [Hook Interface Documentation](#hook-interface-documentation)
- [Agent Interface Specifications](#agent-interface-specifications)
- [Configuration Schema](#configuration-schema)
- [Environment Variables](#environment-variables)
- [Integration APIs](#integration-apis)
- [CLI Commands](#cli-commands)
- [Event System](#event-system)
- [Data Formats](#data-formats)

## 🪝 Hook Interface Documentation

### Overview

Claude Enhancer uses Claude Code's hook system to intercept and enhance development workflows. All hooks follow a standardized interface pattern.

### Hook Types

#### UserPromptSubmit Hook

**Purpose**: Executes when a user submits a prompt to Claude Code
**Trigger**: User interaction with Claude interface

**Interface:**
```bash
# Input: User prompt string via stdin
echo "user input text" | bash .claude/hooks/branch_helper.sh

# Output: Advisory information to stderr, original input to stdout
# Exit Code: 0 (always non-blocking)
```

**Example Implementation:**
```bash
#!/bin/bash
# UserPromptSubmit Hook Example

# Read user input
INPUT=$(cat)

# Process and provide guidance
echo "🎯 Claude Enhancer Workflow Guidance:" >&2
echo "  Current Phase: Analysis" >&2
echo "  Next Phase: Design Planning" >&2

# Pass through original input
echo "$INPUT"
exit 0
```

#### PreToolUse Hook

**Purpose**: Executes before Claude Code uses any tool
**Trigger**: Before tool execution (Task, Edit, Write, etc.)

**Interface:**
```bash
# Input: JSON object with tool information via stdin
echo '{"tool": "Task", "prompt": "description"}' | bash .claude/hooks/smart_agent_selector.sh

# Output: Analysis and recommendations to stderr, original JSON to stdout
# Exit Code: 0 (success), 1 (blocking - prevents tool use)
```

**Input Schema:**
```typescript
interface PreToolUseInput {
  tool: string;           // Tool being used: "Task", "Edit", "Write", etc.
  prompt?: string;        // User's task description
  file_path?: string;     // File being modified (for Edit/Write)
  parameters?: object;    // Tool-specific parameters
  phase?: string;         // Current workflow phase (0-7)
  context?: object;       // Additional context
}
```

**Example Implementation:**
```bash
#!/bin/bash
# PreToolUse Hook Example

INPUT=$(cat)
TOOL=$(echo "$INPUT" | grep -oP '"tool"\s*:\s*"[^"]+' | cut -d'"' -f4)
PROMPT=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4)

if [ "$TOOL" = "Task" ]; then
    echo "🤖 Analyzing task for agent selection..." >&2
    # Perform agent selection logic
    echo "Recommended: 6-agent configuration" >&2
fi

# Pass through input
echo "$INPUT"
exit 0
```

#### PostToolUse Hook

**Purpose**: Executes after tool completion
**Trigger**: After successful or failed tool execution

**Interface:**
```bash
# Input: JSON with execution results
echo '{"tool": "Task", "success": true, "output": "result"}' | bash .claude/hooks/post-task-analyzer.sh

# Output: Analysis and next steps to stderr
# Exit Code: 0 (always non-blocking)
```

### Hook Configuration

**Location**: `.claude/settings.json`

**Schema:**
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "bash .claude/hooks/branch_helper.sh",
        "description": "Workflow guidance and branch management",
        "timeout": 1000
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Task",
        "type": "command",
        "command": "bash .claude/hooks/smart_agent_selector.sh",
        "description": "Intelligent agent selection",
        "timeout": 5000
      }
    ],
    "PostToolUse": [
      {
        "type": "command",
        "command": "bash .claude/hooks/task_summarizer.sh",
        "description": "Task completion analysis",
        "timeout": 2000
      }
    ]
  }
}
```

**Hook Properties:**

| Property | Type | Description | Required |
|----------|------|-------------|----------|
| `type` | string | Hook type: "command" | ✅ |
| `command` | string | Shell command to execute | ✅ |
| `description` | string | Human-readable description | ✅ |
| `timeout` | number | Timeout in milliseconds | ❌ |
| `matcher` | string | Tool name to match (PreToolUse only) | ❌ |
| `env` | object | Environment variables | ❌ |
| `workingDir` | string | Working directory | ❌ |

## 🤖 Agent Interface Specifications

### Agent File Format

All agents are defined in Markdown files under `.claude/agents/`.

**File Structure:**
```markdown
# Agent Name

> Brief description of the agent's role and capabilities

## Core Expertise
- Domain-specific knowledge areas
- Technical skills
- Specialized capabilities

## Responsibilities
- Primary tasks the agent handles
- Decision-making areas
- Output formats

## Interaction Patterns
- How the agent works with other agents
- Communication protocols
- Collaboration patterns

## Quality Standards
- Code quality requirements
- Documentation standards
- Testing expectations

## Examples
- Common use cases
- Sample outputs
- Best practices
```

### Agent Categories

#### Development Agents

**Location**: `.claude/agents/development/`

**Available Agents:**
- `backend-architect.md` - System architecture and design
- `backend-engineer.md` - Implementation and coding
- `frontend-specialist.md` - UI/UX and frontend development
- `database-specialist.md` - Data modeling and optimization
- `api-designer.md` - API design and documentation
- `fullstack-engineer.md` - Full-stack development
- `python-pro.md` - Python expertise
- `typescript-pro.md` - TypeScript expertise
- `react-pro.md` - React framework
- `vue-specialist.md` - Vue.js framework
- `angular-expert.md` - Angular framework
- `nextjs-pro.md` - Next.js framework
- `golang-pro.md` - Go language
- `rust-pro.md` - Rust language
- `java-enterprise.md` - Enterprise Java
- `javascript-pro.md` - JavaScript expertise

#### Quality Agents

**Location**: `.claude/agents/quality/`

**Available Agents:**
- `test-engineer.md` - Testing strategy and implementation
- `security-auditor.md` - Security analysis and hardening
- `performance-engineer.md` - Performance optimization
- `code-reviewer.md` - Code quality and standards

#### Process Agents

**Location**: `.claude/agents/process/`

**Available Agents:**
- `technical-writer.md` - Documentation creation
- `project-manager.md` - Project coordination
- `devops-engineer.md` - Deployment and infrastructure
- `cleanup-specialist.md` - Code maintenance and cleanup

#### Specialized Agents

**Location**: `.claude/agents/specialized/`

**Available Agents:**
- `fintech-specialist.md` - Financial technology
- `healthcare-dev.md` - Healthcare systems
- `embedded-engineer.md` - IoT and embedded systems
- `ai-engineer.md` - AI/ML development
- `blockchain-dev.md` - Blockchain and Web3
- `mobile-specialist.md` - Mobile app development
- `game-developer.md` - Game development
- `data-engineer.md` - Big data processing
- `cloud-architect.md` - Cloud infrastructure

#### Data & AI Agents

**Location**: `.claude/agents/data-ai/`

**Available Agents:**
- `data-scientist.md` - Data analysis and modeling
- `ai-engineer.md` - AI/ML systems
- `data-engineer.md` - Data pipeline engineering
- `analytics-engineer.md` - Business intelligence
- `mlops-engineer.md` - ML operations
- `prompt-engineer.md` - LLM optimization

### Agent Selection API

**Function**: `determine_complexity()`
**Location**: `.claude/hooks/smart_agent_selector.sh`

**Algorithm:**
```bash
determine_complexity() {
    local desc="$1"

    # Complex (8 agents)
    if echo "$desc" | grep -qE "architect|design system|integrate|migrate|refactor entire|complex"; then
        echo "complex"
        return
    fi

    # Simple (4 agents)
    if echo "$desc" | grep -qE "fix bug|typo|minor|quick|simple|small change"; then
        echo "simple"
        return
    fi

    # Standard (6 agents) - default
    echo "standard"
}
```

**Agent Combinations:**

**Simple Tasks (4 agents):**
```bash
agents=(
    "backend-engineer"     # Core implementation
    "test-engineer"        # Quality assurance
    "code-reviewer"        # Code standards
    "technical-writer"     # Documentation
)
```

**Standard Tasks (6 agents):**
```bash
agents=(
    "backend-architect"    # Solution design
    "backend-engineer"     # Implementation
    "test-engineer"        # Testing strategy
    "security-auditor"     # Security review
    "api-designer"         # API specification (if API task)
    "technical-writer"     # Documentation
)
```

**Complex Tasks (8 agents):**
```bash
agents=(
    "backend-architect"      # System architecture
    "api-designer"           # API design
    "database-specialist"    # Data modeling
    "backend-engineer"       # Core implementation
    "security-auditor"       # Security audit
    "test-engineer"          # Comprehensive testing
    "performance-engineer"   # Performance optimization
    "technical-writer"       # Complete documentation
)
```

### Dynamic Agent Selection

**Context-Aware Selection:**
```bash
get_agent_combination() {
    local complexity="$1"
    local task="$2"
    local phase="$3"

    # Base agents for complexity level
    local base_agents=()
    case "$complexity" in
        simple) base_agents=("backend-engineer" "test-engineer" "code-reviewer" "technical-writer") ;;
        standard) base_agents=("backend-architect" "backend-engineer" "test-engineer" "security-auditor") ;;
        complex) base_agents=("backend-architect" "api-designer" "database-specialist" "backend-engineer" "security-auditor" "test-engineer" "performance-engineer" "technical-writer") ;;
    esac

    # Task-specific additions
    if echo "$task" | grep -qE "api|endpoint|rest"; then
        base_agents+=("api-designer")
    elif echo "$task" | grep -qE "database|sql|data"; then
        base_agents+=("database-specialist")
    elif echo "$task" | grep -qE "frontend|ui|react"; then
        base_agents+=("frontend-specialist")
    fi

    # Phase-specific additions
    if [ "$phase" = "5" ] || [ "$phase" = "7" ]; then
        base_agents+=("cleanup-specialist")
    fi

    # Return unique agents
    printf '%s\n' "${base_agents[@]}" | sort | uniq
}
```

## ⚙️ Configuration Schema

### Main Configuration File

**Location**: `.claude/settings.json`

**Complete Schema:**
```typescript
interface Claude EnhancerConfiguration {
  version: string;                    // Semantic version
  project: string;                    // Project name
  description: string;                // Project description

  hooks: {
    UserPromptSubmit?: HookDefinition[];
    PreToolUse?: HookDefinition[];
    PostToolUse?: HookDefinition[];
  };

  environment: {
    CLAUDE_ENHANCER_MODE: 'advisory' | 'enforcement' | 'strict';
    MIN_AGENTS: string;               // Minimum agent count
    MAX_RETRIES: string;              // Maximum hook retries
    ENFORCE_PARALLEL: string;         // "true" | "false"
    CLAUDE_ENHANCER_BACKEND?: string; // Backend mode
    CLAUDE_ENHANCER_API_MODE?: string;// API integration mode
  };

  // Optional advanced configuration
  agentSelection?: {
    complexityKeywords?: {
      simple: string[];
      standard: string[];
      complex: string[];
    };
    customCombinations?: {
      [taskType: string]: string[];
    };
  };

  quality?: {
    gitHooks: boolean;
    codeStandards: string[];
    testRequirements: string[];
  };

  logging?: {
    enabled: boolean;
    level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
    files: {
      agent_selection: string;
      errors: string;
      performance: string;
    };
  };
}

interface HookDefinition {
  type: 'command';
  command: string;
  description: string;
  timeout?: number;
  matcher?: string;                   // For PreToolUse hooks
  env?: Record<string, string>;
  workingDir?: string;
  retries?: number;
  critical?: boolean;                 // If true, failure blocks execution
}
```

**Example Configuration:**
```json
{
  "version": "4.0.0",
  "project": "Claude Enhancer Enhanced Development",
  "description": "AI-driven development with quality enforcement",

  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "bash .claude/hooks/branch_helper.sh",
        "description": "Workflow guidance and phase tracking",
        "timeout": 1000,
        "env": {
          "PHASE_TRACKING": "true"
        }
      }
    ],

    "PreToolUse": [
      {
        "matcher": "Task",
        "type": "command",
        "command": "bash .claude/hooks/smart_agent_selector.sh",
        "description": "4-6-8 agent selection strategy",
        "timeout": 5000,
        "retries": 2,
        "critical": false
      },

      {
        "matcher": "Edit",
        "type": "command",
        "command": "bash .claude/hooks/edit_validator.sh",
        "description": "Pre-edit validation and backup",
        "timeout": 2000
      }
    ],

    "PostToolUse": [
      {
        "type": "command",
        "command": "bash .claude/hooks/task_summarizer.sh",
        "description": "Task completion analysis",
        "timeout": 3000
      }
    ]
  },

  "environment": {
    "CLAUDE_ENHANCER_MODE": "enforcement",
    "MIN_AGENTS": "3",
    "MAX_RETRIES": "3",
    "ENFORCE_PARALLEL": "true",
    "CLAUDE_ENHANCER_LOG_LEVEL": "INFO",
    "CLAUDE_ENHANCER_TIMEOUT": "30"
  },

  "agentSelection": {
    "complexityKeywords": {
      "simple": ["fix", "typo", "minor", "quick", "small"],
      "standard": ["add", "update", "modify", "implement"],
      "complex": ["architect", "design", "refactor", "migrate", "integrate"]
    },

    "customCombinations": {
      "auth": ["security-auditor", "backend-architect", "test-engineer", "api-designer"],
      "database": ["database-specialist", "backend-architect", "performance-engineer", "test-engineer"]
    }
  }
}
```

### Configuration Validation

**JSON Schema Validation:**
```bash
# Validate configuration
validate_config() {
    local config_file="${1:-.claude/settings.json}"

    if ! python3 -c "import json; json.load(open('$config_file'))" 2>/dev/null; then
        echo "❌ Invalid JSON syntax in $config_file"
        return 1
    fi

    # Check required fields
    local required_fields=("version" "project" "hooks" "environment")
    for field in "${required_fields[@]}"; do
        if ! grep -q "\"$field\"" "$config_file"; then
            echo "❌ Missing required field: $field"
            return 1
        fi
    done

    echo "✅ Configuration is valid"
    return 0
}
```

## 🌍 Environment Variables

### Core Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CLAUDE_ENHANCER_MODE` | enum | `"enforcement"` | Operation mode: advisory, enforcement, strict |
| `MIN_AGENTS` | number | `"3"` | Minimum agents required for any task |
| `MAX_RETRIES` | number | `"3"` | Maximum hook retry attempts |
| `ENFORCE_PARALLEL` | boolean | `"true"` | Force parallel agent execution |

### Advanced Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CLAUDE_ENHANCER_DEBUG` | boolean | `false` | Enable debug output |
| `CLAUDE_ENHANCER_TRACE` | boolean | `false` | Enable execution tracing |
| `CLAUDE_ENHANCER_LOG_LEVEL` | enum | `"INFO"` | Logging level: DEBUG, INFO, WARN, ERROR |
| `CLAUDE_ENHANCER_LOG_FILE` | string | `null` | Log file path |
| `CLAUDE_ENHANCER_TIMEOUT` | number | `30` | Global timeout in seconds |
| `CLAUDE_ENHANCER_FAST_MODE` | boolean | `false` | Skip complex analysis for simple tasks |

### Runtime Variables

| Variable | Type | Description |
|----------|------|-------------|
| `CURRENT_PHASE` | string | Current workflow phase (0-7) |
| `TASK_COMPLEXITY` | string | Detected task complexity (simple/standard/complex) |
| `SELECTED_AGENTS` | string | Comma-separated list of selected agents |
| `HOOK_EXECUTION_ID` | string | Unique identifier for hook execution |

### Usage Examples

```bash
# Enable debug mode
export CLAUDE_ENHANCER_DEBUG=true
export CLAUDE_ENHANCER_LOG_LEVEL=DEBUG

# Configure timeouts
export CLAUDE_ENHANCER_TIMEOUT=60

# Enable fast mode for development
export CLAUDE_ENHANCER_FAST_MODE=true

# Custom log file
export CLAUDE_ENHANCER_LOG_FILE="/var/log/claude-enhancer.log"
```

## 🔧 Integration APIs

### Git Hook Integration

Claude Enhancer integrates with Git hooks for quality enforcement.

**Pre-commit Hook API:**
```bash
# Location: .git/hooks/pre-commit
# Called by: git commit
# Purpose: Quality checks before commit

# Interface
INPUT: staged files (via git diff --cached)
OUTPUT: validation results
EXIT_CODE: 0 (allow commit), 1 (block commit)

# Example usage
git commit -m "feat: add new feature"
# Triggers pre-commit hook
# Validates code quality, tests, documentation
# Allows or blocks commit based on checks
```

**Commit Message Hook API:**
```bash
# Location: .git/hooks/commit-msg
# Called by: git commit
# Purpose: Validate commit message format

# Interface
INPUT: commit message file path
OUTPUT: validation feedback
EXIT_CODE: 0 (valid), 1 (invalid)

# Example usage
git commit -m "invalid message format"
# Triggers commit-msg hook
# Validates against conventional commit format
# Blocks commit if format is invalid
```

### Claude Code Integration

**Hook Registration:**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "type": "command",
        "command": "bash .claude/hooks/smart_agent_selector.sh"
      }
    ]
  }
}
```

**Data Flow:**
```
User Input → Claude Code → PreToolUse Hook → Agent Selection → Tool Execution
                                ↓
                        Advisory Output to User
```

### External Tool Integration

**Shell Command Integration:**
```bash
# Claude Enhancer can be triggered from any shell environment

# Direct hook invocation
echo '{"prompt": "task description"}' | bash .claude/hooks/smart_agent_selector.sh

# Integration with CI/CD
if bash .claude/hooks/pre_deploy_check.sh; then
    echo "Deployment approved"
else
    echo "Deployment blocked"
    exit 1
fi
```

**API Wrapper Functions:**
```bash
# Convenience functions for integration

claude-enhancer_analyze_task() {
    local task="$1"
    echo "{\"prompt\": \"$task\"}" | bash .claude/hooks/smart_agent_selector.sh
}

claude-enhancer_check_quality() {
    bash .git/hooks/pre-commit
}

claude-enhancer_validate_commit() {
    local message="$1"
    echo "$message" | bash .git/hooks/commit-msg /dev/stdin
}
```

## 💻 CLI Commands

### Installation Commands

```bash
# Install Claude Enhancer system
bash .claude/install.sh

# Install with custom options
SKIP_GIT_HOOKS=true bash .claude/install.sh

# Reinstall (clean install)
bash .claude/install.sh --force
```

### Diagnostic Commands

```bash
# Quick health check
bash .claude/hooks/health_check.sh

# Detailed system analysis
bash .claude/scripts/system_analysis.sh

# Hook testing
bash .claude/scripts/test_hooks.sh

# Agent availability check
bash .claude/scripts/check_agents.sh
```

### Maintenance Commands

```bash
# Clean temporary files
bash .claude/scripts/cleanup.sh

# Rotate logs
bash .claude/scripts/rotate_logs.sh

# Update agent cache
bash .claude/scripts/update_agent_cache.sh

# Backup configuration
bash .claude/scripts/backup_config.sh
```

### Development Commands

```bash
# Enable debug mode
bash .claude/scripts/enable_debug.sh

# Generate test data
bash .claude/scripts/generate_test_data.sh

# Performance profiling
bash .claude/scripts/profile_performance.sh
```

## 📡 Event System

### Event Types

Claude Enhancer generates events for monitoring and integration:

```typescript
interface Claude EnhancerEvent {
  timestamp: string;
  type: EventType;
  source: string;
  data: object;
  correlationId?: string;
}

enum EventType {
  HOOK_EXECUTED = 'hook_executed',
  AGENT_SELECTED = 'agent_selected',
  TASK_COMPLETED = 'task_completed',
  ERROR_OCCURRED = 'error_occurred',
  PHASE_CHANGED = 'phase_changed',
  QUALITY_CHECK = 'quality_check'
}
```

### Event Examples

**Agent Selection Event:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "type": "agent_selected",
  "source": "smart_agent_selector.sh",
  "data": {
    "task": "implement user authentication",
    "complexity": "standard",
    "agents": ["backend-architect", "security-auditor", "test-engineer", "api-designer", "backend-engineer", "technical-writer"],
    "estimatedDuration": "15-20 minutes"
  },
  "correlationId": "task-auth-001"
}
```

**Quality Check Event:**
```json
{
  "timestamp": "2024-01-15T10:45:00.000Z",
  "type": "quality_check",
  "source": "pre-commit",
  "data": {
    "checks": {
      "tests": "passed",
      "documentation": "passed",
      "formatting": "passed",
      "security": "passed"
    },
    "filesChanged": 5,
    "result": "approved"
  }
}
```

### Event Consumption

**Log File Integration:**
```bash
# Events are written to structured log files
tail -f .claude/logs/events.log | jq '.'
```

**Webhook Integration:**
```bash
# Configure webhook in .claude/hooks/webhook_notifier.sh
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "$EVENT_JSON"
```

## 📊 Data Formats

### Task Description Format

**Input to Agent Selector:**
```json
{
  "prompt": "string",           // Task description
  "tool": "string",            // Tool being used
  "phase": "string",           // Workflow phase (0-7)
  "context": {
    "files": ["string"],       // Related files
    "branch": "string",        // Git branch
    "author": "string",        // Task author
    "priority": "string"       // Task priority
  }
}
```

### Agent Selection Output

**Standard Format:**
```json
{
  "analysis": {
    "complexity": "simple|standard|complex",
    "estimatedDuration": "string",
    "keyTechnologies": ["string"],
    "riskFactors": ["string"]
  },
  "recommendation": {
    "agents": [
      {
        "name": "string",
        "role": "string",
        "rationale": "string"
      }
    ],
    "executionMode": "parallel|sequential",
    "phaseGuidance": "string"
  },
  "alternatives": [
    {
      "scenario": "string",
      "agents": ["string"]
    }
  ]
}
```

### Quality Check Results

**Git Hook Output:**
```json
{
  "timestamp": "string",
  "checks": {
    "tests": {
      "status": "passed|failed|skipped",
      "details": "string",
      "files": ["string"]
    },
    "documentation": {
      "status": "passed|failed|skipped",
      "details": "string",
      "coverage": "number"
    },
    "formatting": {
      "status": "passed|failed|skipped",
      "details": "string",
      "violations": ["string"]
    },
    "security": {
      "status": "passed|failed|skipped",
      "details": "string",
      "issues": ["string"]
    }
  },
  "overall": {
    "result": "approved|blocked",
    "score": "number",
    "recommendations": ["string"]
  }
}
```

### Performance Metrics

**Execution Metrics:**
```json
{
  "hook": "string",
  "execution": {
    "startTime": "string",
    "endTime": "string",
    "duration": "number",
    "memoryUsed": "number",
    "cpuTime": "number"
  },
  "analysis": {
    "inputSize": "number",
    "outputSize": "number",
    "complexityScore": "number"
  },
  "resources": {
    "fileReads": "number",
    "fileWrites": "number",
    "networkCalls": "number"
  }
}
```

## 🔍 API Usage Examples

### Basic Agent Selection

```bash
# Simple task
curl -X POST http://localhost:8080/api/claude-enhancer/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "fix typo in documentation",
    "phase": "3"
  }'

# Response
{
  "complexity": "simple",
  "agents": ["backend-engineer", "test-engineer", "code-reviewer", "technical-writer"],
  "duration": "5-10 minutes"
}
```

### Advanced Configuration

```bash
# Custom agent selection with constraints
curl -X POST http://localhost:8080/api/claude-enhancer/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "implement OAuth2 authentication",
    "phase": "3",
    "constraints": {
      "maxAgents": 6,
      "requiredAgents": ["security-auditor"],
      "excludeAgents": ["performance-engineer"]
    }
  }'
```

### Quality Gate Integration

```bash
# Run quality checks via API
curl -X POST http://localhost:8080/api/claude-enhancer/quality-check \
  -H "Content-Type: application/json"
  -d '{
    "files": ["src/auth.py", "tests/test_auth.py"],
    "checks": ["tests", "security", "formatting"]
  }'
```

---

## 📚 Additional Resources

- **Installation Guide**: [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Project Documentation**: [CLAUDE.md](./CLAUDE.md)

## 🔄 API Versioning

Claude Enhancer follows semantic versioning for its APIs:

- **Major Version**: Breaking changes to hook interfaces
- **Minor Version**: New features, backward compatible
- **Patch Version**: Bug fixes, no interface changes

Current API Version: `4.0.0`

## 🛡️ Security Considerations

- All hook scripts should be reviewed before execution
- Environment variables may contain sensitive information
- Git hooks run with repository access permissions
- Log files may contain task descriptions and file paths
- Network calls from hooks should use authentication

Claude Enhancer provides comprehensive APIs for integration, customization, and monitoring. All interfaces are designed for stability and backward compatibility. 🚀