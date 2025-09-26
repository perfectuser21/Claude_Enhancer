# Claude Enhancer 5.1 配置指南

## 📋 概述

Claude Enhancer 5.1 提供了灵活的配置系统，支持自检优化、性能监控、错误恢复等新特性。本指南详细介绍了所有配置选项和最佳实践。

### 配置文件结构
```
.claude/
├── settings.json              # 主配置文件
├── monitoring.json            # 监控配置 (5.1新增)
├── optimization.json          # 优化配置 (5.1新增)
├── recovery.json             # 错误恢复配置 (5.1新增)
├── hooks/                    # Hook脚本配置
├── templates/                # 配置模板
└── secrets/                  # 敏感信息配置
```

## 🔧 主配置文件 (settings.json)

### 基础配置
```json
{
  "version": "5.1.0",
  "project": "Claude Enhancer 5.1 - Self-Optimization System",
  "description": "自检优化系统，智能错误恢复和性能监控",
  "architecture": {
    "version": "v2.1",
    "lazy_loading": true,
    "self_optimization": true,
    "real_time_monitoring": true,
    "documentation": ".claude/ARCHITECTURE/INDEX.md",
    "auto_load_docs": [
      ".claude/ARCHITECTURE_LOADER.md",
      ".claude/ARCHITECTURE/INDEX.md"
    ]
  }
}
```

### Hook系统配置
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "type": "command",
        "command": "bash .claude/hooks/system_health_check.sh",
        "description": "系统健康检查",
        "timeout": 500,
        "blocking": false,
        "priority": 1,
        "enabled": true,
        "retry": {
          "attempts": 3,
          "delay": 100
        }
      },
      {
        "matcher": "Task",
        "type": "command",
        "command": "bash .claude/hooks/smart_agent_selector_v2.sh",
        "description": "增强Agent选择策略",
        "timeout": 2000,
        "blocking": false,
        "priority": 2,
        "enabled": true,
        "cache": {
          "enabled": true,
          "ttl": 300
        }
      }
    ],
    "PostToolUse": [
      {
        "matcher": ".*",
        "type": "command",
        "command": "python3 .claude/hooks/performance_monitor.py",
        "description": "性能监控和优化",
        "timeout": 200,
        "blocking": false,
        "priority": 1,
        "enabled": true,
        "async": true
      }
    ],
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "bash .claude/hooks/workflow_phase_initializer.sh",
        "description": "工作流阶段初始化",
        "timeout": 1500,
        "blocking": false,
        "enabled": true
      }
    ]
  }
}
```

#### Hook配置选项详解
| 配置项 | 类型 | 描述 | 默认值 |
|--------|------|------|--------|
| `matcher` | string | 匹配规则（正则表达式） | `.*` |
| `type` | string | Hook类型 (command, function) | `command` |
| `command` | string | 执行命令 | - |
| `description` | string | Hook描述 | - |
| `timeout` | number | 超时时间(ms) | 3000 |
| `blocking` | boolean | 是否阻塞执行 | false |
| `priority` | number | 执行优先级 (1-10) | 5 |
| `enabled` | boolean | 是否启用 | true |
| `retry.attempts` | number | 重试次数 | 0 |
| `retry.delay` | number | 重试延迟(ms) | 100 |
| `cache.enabled` | boolean | 是否启用缓存 | false |
| `cache.ttl` | number | 缓存时间(秒) | 300 |
| `async` | boolean | 是否异步执行 | false |

### 工作流配置
```json
{
  "workflow_config": {
    "phases": {
      "P0": {
        "name": "Branch Creation",
        "description": "创建feature分支，准备开发环境",
        "required_tools": ["Bash"],
        "success_criteria": ["branch_created", "environment_ready"],
        "timeout": 120,
        "retry_attempts": 3
      },
      "P1": {
        "name": "Requirements Analysis",
        "description": "理解要做什么，为什么要做",
        "required_tools": ["Read", "Grep"],
        "success_criteria": ["requirements_understood", "scope_defined"],
        "timeout": 300,
        "quality_gates": ["requirement_completeness", "business_alignment"]
      },
      "P2": {
        "name": "Design Planning",
        "description": "如何实现，技术选型，架构设计",
        "required_tools": ["Read", "Write"],
        "success_criteria": ["architecture_defined", "tech_stack_chosen"],
        "timeout": 600,
        "templates": ["architecture_template", "design_document"]
      },
      "P3": {
        "name": "Implementation",
        "description": "编写代码，实现功能 - 4-6-8 Agent策略",
        "required_tools": ["Task", "Write", "MultiEdit"],
        "success_criteria": ["code_implemented", "agents_coordinated"],
        "timeout": 1800,
        "agent_strategies": {
          "simple": {"count": 4, "duration": "5-10分钟"},
          "standard": {"count": 6, "duration": "15-20分钟"},
          "complex": {"count": 8, "duration": "25-30分钟"}
        }
      },
      "P4": {
        "name": "Local Testing",
        "description": "单元测试，集成测试，功能验证",
        "required_tools": ["Bash", "Read"],
        "success_criteria": ["tests_passed", "functionality_verified"],
        "timeout": 900,
        "coverage_threshold": 80
      },
      "P5": {
        "name": "Code Commit",
        "description": "Git提交，触发质量检查",
        "required_tools": ["Bash"],
        "success_criteria": ["code_committed", "quality_checks_passed"],
        "timeout": 300,
        "git_hooks": ["pre-commit", "commit-msg"]
      },
      "P6": {
        "name": "Code Review",
        "description": "创建PR，团队review，反馈修改",
        "required_tools": ["Bash"],
        "success_criteria": ["pr_created", "review_ready"],
        "timeout": 180,
        "review_templates": ["pr_template", "review_checklist"]
      }
    }
  }
}
```

### Agent策略配置
```json
{
  "agent_strategies": {
    "simple_task": {
      "agent_count": 4,
      "duration_estimate": "5-10分钟",
      "complexity": "low",
      "recommended_agents": [
        "backend-architect",
        "test-engineer",
        "security-auditor",
        "technical-writer"
      ],
      "selection_criteria": {
        "max_complexity_score": 3,
        "max_word_count": 10,
        "preferred_domains": ["bug_fix", "minor_feature"]
      }
    },
    "standard_task": {
      "agent_count": 6,
      "duration_estimate": "15-20分钟",
      "complexity": "medium",
      "recommended_agents": [
        "backend-architect",
        "api-designer",
        "database-specialist",
        "test-engineer",
        "security-auditor",
        "performance-engineer"
      ],
      "selection_criteria": {
        "max_complexity_score": 6,
        "max_word_count": 20,
        "preferred_domains": ["feature_development", "api_creation"]
      }
    },
    "complex_task": {
      "agent_count": 8,
      "duration_estimate": "25-30分钟",
      "complexity": "high",
      "recommended_agents": [
        "backend-architect",
        "api-designer",
        "database-specialist",
        "frontend-specialist",
        "test-engineer",
        "security-auditor",
        "performance-engineer",
        "devops-engineer"
      ],
      "selection_criteria": {
        "max_complexity_score": 10,
        "preferred_domains": ["full_application", "system_integration"]
      }
    }
  }
}
```

### 安全配置
```json
{
  "security": {
    "hook_security_enabled": true,
    "api_key_required": true,
    "forbidden_operations": [
      "modify_user_input",
      "block_execution",
      "hijack_workflow",
      "infinite_loops",
      "file_system_access_outside_project"
    ],
    "allowed_hook_types": [
      "advisory",
      "validation",
      "notification",
      "workflow_tracking",
      "performance_monitoring"
    ],
    "sandbox": {
      "enabled": true,
      "allowed_commands": [
        "bash", "python3", "node", "npm", "git"
      ],
      "blocked_paths": [
        "/etc", "/usr", "/root", "~/.ssh"
      ]
    }
  }
}
```

## 📊 监控配置 (monitoring.json)

### 基础监控配置
```json
{
  "enabled": true,
  "version": "5.1.0",
  "endpoints": {
    "health": "/api/v1/health",
    "metrics": "/api/v1/metrics",
    "performance": "/api/v1/performance",
    "events": "/api/v1/events"
  },
  "server": {
    "host": "localhost",
    "port": 8080,
    "cors": {
      "enabled": true,
      "origins": ["http://localhost:3000", "http://localhost:8080"]
    },
    "ssl": {
      "enabled": false,
      "cert": "/path/to/cert.pem",
      "key": "/path/to/key.pem"
    }
  }
}
```

### 系统指标配置
```json
{
  "system_metrics": {
    "cpu": {
      "enabled": true,
      "threshold": 80,
      "alert_threshold": 90,
      "collection_interval": 5
    },
    "memory": {
      "enabled": true,
      "threshold": 85,
      "alert_threshold": 95,
      "collection_interval": 5,
      "gc_trigger_threshold": 80
    },
    "disk": {
      "enabled": true,
      "threshold": 90,
      "alert_threshold": 95,
      "collection_interval": 30,
      "paths": ["/", "/tmp"]
    },
    "network": {
      "enabled": true,
      "collection_interval": 10,
      "interfaces": ["eth0", "wlan0"]
    }
  }
}
```

### 性能监控配置
```json
{
  "performance_monitoring": {
    "hook_execution": {
      "enabled": true,
      "track_all": true,
      "slow_threshold": 1000,
      "very_slow_threshold": 5000,
      "histogram_buckets": [10, 50, 100, 500, 1000, 5000]
    },
    "agent_performance": {
      "enabled": true,
      "response_time_tracking": true,
      "success_rate_tracking": true,
      "load_balancing": true
    },
    "workflow_tracking": {
      "enabled": true,
      "phase_duration_tracking": true,
      "bottleneck_detection": true,
      "optimization_suggestions": true
    }
  }
}
```

### 告警配置
```json
{
  "alerts": {
    "enabled": true,
    "channels": {
      "console": {
        "enabled": true,
        "level": "warning"
      },
      "file": {
        "enabled": true,
        "path": ".claude/logs/alerts.log",
        "level": "error",
        "max_size": "10MB",
        "max_files": 5
      },
      "webhook": {
        "enabled": false,
        "url": "https://hooks.slack.com/your/webhook/url",
        "level": "critical"
      }
    },
    "rules": [
      {
        "name": "high_cpu_usage",
        "condition": "cpu > 90",
        "level": "warning",
        "cooldown": 300
      },
      {
        "name": "memory_exhausted",
        "condition": "memory > 95",
        "level": "critical",
        "cooldown": 60
      },
      {
        "name": "hook_failure_rate",
        "condition": "hook_failure_rate > 10",
        "level": "error",
        "cooldown": 180
      }
    ]
  }
}
```

## 🚀 优化配置 (optimization.json)

### 懒加载配置
```json
{
  "lazy_loading": {
    "enabled": true,
    "strategies": {
      "documentation": {
        "enabled": true,
        "load_on_demand": true,
        "cache_loaded_docs": true,
        "cache_ttl": 3600,
        "preload_patterns": [
          "README.md",
          "ARCHITECTURE.md"
        ]
      },
      "agents": {
        "enabled": true,
        "pool_size": 8,
        "warm_up_agents": [
          "backend-architect",
          "test-engineer"
        ],
        "load_balancing": "round_robin"
      },
      "hooks": {
        "enabled": true,
        "defer_non_critical": true,
        "batch_execution": true,
        "max_batch_size": 5
      }
    }
  }
}
```

### 缓存配置
```json
{
  "caching": {
    "enabled": true,
    "strategy": "lru",
    "max_memory": "128MB",
    "ttl_default": 300,
    "cache_types": {
      "agent_results": {
        "enabled": true,
        "ttl": 600,
        "max_entries": 1000
      },
      "hook_results": {
        "enabled": true,
        "ttl": 300,
        "max_entries": 2000
      },
      "file_contents": {
        "enabled": true,
        "ttl": 1800,
        "max_entries": 500
      },
      "performance_metrics": {
        "enabled": true,
        "ttl": 60,
        "max_entries": 10000
      }
    }
  }
}
```

### 资源池配置
```json
{
  "resource_pooling": {
    "enabled": true,
    "pools": {
      "agent_pool": {
        "min_size": 2,
        "max_size": 16,
        "idle_timeout": 300,
        "health_check_interval": 60
      },
      "hook_pool": {
        "min_size": 1,
        "max_size": 12,
        "idle_timeout": 180,
        "health_check_interval": 30
      },
      "connection_pool": {
        "min_size": 5,
        "max_size": 50,
        "idle_timeout": 120,
        "max_wait_time": 5000
      }
    }
  }
}
```

### 自适应优化
```json
{
  "adaptive_optimization": {
    "enabled": true,
    "learning_mode": true,
    "optimization_interval": 300,
    "strategies": {
      "auto_scaling": {
        "enabled": true,
        "scale_up_threshold": 80,
        "scale_down_threshold": 30,
        "min_instances": 1,
        "max_instances": 10
      },
      "load_balancing": {
        "enabled": true,
        "algorithm": "least_connections",
        "health_check_enabled": true,
        "failover_enabled": true
      },
      "performance_tuning": {
        "enabled": true,
        "auto_tune_timeouts": true,
        "auto_adjust_concurrency": true,
        "memory_optimization": true
      }
    }
  }
}
```

## 🛠️ 错误恢复配置 (recovery.json)

### 基础恢复配置
```json
{
  "enabled": true,
  "version": "5.1.0",
  "global_settings": {
    "max_recovery_attempts": 3,
    "recovery_timeout": 30000,
    "backoff_strategy": "exponential",
    "base_delay": 1000,
    "max_delay": 10000,
    "jitter": true
  }
}
```

### 错误类型和恢复策略
```json
{
  "recovery_strategies": {
    "hook_failure": {
      "enabled": true,
      "max_attempts": 3,
      "strategies": [
        {
          "name": "restart_hook",
          "priority": 1,
          "conditions": ["timeout", "execution_error"],
          "action": "restart",
          "timeout": 5000
        },
        {
          "name": "skip_hook",
          "priority": 2,
          "conditions": ["persistent_failure"],
          "action": "skip",
          "notify": true
        }
      ]
    },
    "memory_exhausted": {
      "enabled": true,
      "max_attempts": 2,
      "strategies": [
        {
          "name": "garbage_collection",
          "priority": 1,
          "conditions": ["memory_usage > 90"],
          "action": "gc",
          "aggressive": false
        },
        {
          "name": "aggressive_cleanup",
          "priority": 2,
          "conditions": ["memory_usage > 95"],
          "action": "aggressive_gc",
          "clear_caches": true
        }
      ]
    },
    "agent_communication_failed": {
      "enabled": true,
      "max_attempts": 3,
      "strategies": [
        {
          "name": "retry_connection",
          "priority": 1,
          "conditions": ["network_error", "timeout"],
          "action": "reconnect",
          "delay": 1000
        },
        {
          "name": "fallback_agent",
          "priority": 2,
          "conditions": ["persistent_failure"],
          "action": "switch_agent",
          "agent_selection": "backup"
        }
      ]
    },
    "workflow_deadlock": {
      "enabled": true,
      "max_attempts": 2,
      "strategies": [
        {
          "name": "reset_workflow_state",
          "priority": 1,
          "conditions": ["state_inconsistency"],
          "action": "reset_state",
          "preserve_progress": true
        },
        {
          "name": "rollback_phase",
          "priority": 2,
          "conditions": ["unrecoverable_state"],
          "action": "rollback",
          "target_phase": "previous"
        }
      ]
    }
  }
}
```

### 健康检查配置
```json
{
  "health_checks": {
    "enabled": true,
    "interval": 30,
    "timeout": 5000,
    "checks": {
      "system_resources": {
        "enabled": true,
        "cpu_threshold": 95,
        "memory_threshold": 90,
        "disk_threshold": 95
      },
      "hook_system": {
        "enabled": true,
        "response_time_threshold": 5000,
        "error_rate_threshold": 10
      },
      "agent_pool": {
        "enabled": true,
        "min_healthy_agents": 2,
        "response_time_threshold": 10000
      },
      "workflow_engine": {
        "enabled": true,
        "state_consistency_check": true,
        "phase_transition_check": true
      }
    }
  }
}
```

## 🔐 敏感信息配置 (secrets/)

### API密钥配置
```json
{
  "api_keys": {
    "monitoring": {
      "key": "${CLAUDE_ENHANCER_MONITORING_KEY}",
      "permissions": ["read:metrics", "read:health"]
    },
    "admin": {
      "key": "${CLAUDE_ENHANCER_ADMIN_KEY}",
      "permissions": ["admin:*"]
    },
    "webhook": {
      "slack": "${SLACK_WEBHOOK_URL}",
      "discord": "${DISCORD_WEBHOOK_URL}"
    }
  }
}
```

### 数据库配置
```json
{
  "database": {
    "connection": {
      "host": "${DB_HOST}",
      "port": "${DB_PORT}",
      "database": "${DB_NAME}",
      "username": "${DB_USER}",
      "password": "${DB_PASSWORD}",
      "ssl": true
    },
    "pool": {
      "min": 2,
      "max": 10,
      "idle_timeout": 30000
    }
  }
}
```

## 🎯 环境变量

### 核心环境变量
```bash
# 系统配置
export CLAUDE_ENHANCER_VERSION="5.1"
export CLAUDE_ENHANCER_MODE="self_optimization"
export NODE_ENV="production"

# 功能开关
export MONITORING_ENABLED="true"
export SELF_OPTIMIZATION="true"
export LAZY_LOADING="true"
export ERROR_RECOVERY="true"

# 性能配置
export MAX_CONCURRENT_HOOKS="12"
export MAX_CONCURRENT_AGENTS="16"
export DEFAULT_HOOK_TIMEOUT="5000"
export DEFAULT_AGENT_TIMEOUT="30000"

# 监控配置
export MONITOR_PORT="8080"
export METRICS_RETENTION="7d"
export LOG_LEVEL="info"

# 安全配置
export HOOK_SECURITY="enabled"
export API_KEY_REQUIRED="true"
export SANDBOX_MODE="true"
```

### 开发环境配置
```bash
# 开发模式
export NODE_ENV="development"
export DEBUG="claude-enhancer:*"
export VERBOSE_LOGGING="true"

# 测试配置
export TEST_MODE="true"
export MOCK_AGENTS="true"
export BYPASS_HOOKS="false"

# 性能调试
export ENABLE_PROFILING="true"
export MEMORY_MONITORING="true"
export PERFORMANCE_LOGGING="true"
```

## 📁 配置模板

### 开发环境模板
```json
{
  "extends": "base",
  "overrides": {
    "environment": {
      "NODE_ENV": "development",
      "DEBUG": "claude-enhancer:*"
    },
    "monitoring": {
      "enabled": true,
      "detailed_logging": true
    },
    "hooks": {
      "timeout": 10000,
      "verbose": true
    }
  }
}
```

### 生产环境模板
```json
{
  "extends": "base",
  "overrides": {
    "environment": {
      "NODE_ENV": "production"
    },
    "monitoring": {
      "enabled": true,
      "alerts": {
        "webhook": {
          "enabled": true
        }
      }
    },
    "performance": {
      "caching": {
        "enabled": true,
        "aggressive": true
      },
      "optimization": {
        "enabled": true,
        "auto_scaling": true
      }
    }
  }
}
```

### 测试环境模板
```json
{
  "extends": "development",
  "overrides": {
    "environment": {
      "TEST_MODE": "true"
    },
    "hooks": {
      "timeout": 1000,
      "mock_mode": true
    },
    "agents": {
      "mock_responses": true,
      "fast_mode": true
    }
  }
}
```

## 🔧 配置验证

### 配置验证脚本
```bash
#!/bin/bash
# validate-config.sh

echo "🔍 验证Claude Enhancer 5.1配置..."

# 检查必需文件
required_files=(".claude/settings.json" ".claude/monitoring.json" ".claude/optimization.json")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少必需文件: $file"
        exit 1
    fi
done

# 验证JSON格式
for file in .claude/*.json; do
    if ! jq empty "$file" 2>/dev/null; then
        echo "❌ JSON格式错误: $file"
        exit 1
    fi
done

# 验证版本一致性
version=$(jq -r '.version' .claude/settings.json)
if [ "$version" != "5.1.0" ]; then
    echo "❌ 版本不匹配: 期望5.1.0, 实际$version"
    exit 1
fi

# 验证Hook脚本
hook_scripts=$(jq -r '.hooks.PreToolUse[].command' .claude/settings.json | grep -o '[^[:space:]]*\.sh')
for script in $hook_scripts; do
    if [ ! -x "$script" ]; then
        echo "❌ Hook脚本不可执行: $script"
        exit 1
    fi
done

echo "✅ 配置验证通过!"
```

### 配置优化建议脚本
```bash
#!/bin/bash
# optimize-config.sh

echo "🚀 Claude Enhancer 5.1配置优化建议..."

# 检查系统资源
total_memory=$(free -m | awk 'NR==2{print $2}')
cpu_cores=$(nproc)

echo "📊 系统信息:"
echo "  内存: ${total_memory}MB"
echo "  CPU核心: ${cpu_cores}"

# 内存优化建议
if [ "$total_memory" -lt 4096 ]; then
    echo "💾 建议: 内存不足4GB，启用激进缓存清理"
    echo "  设置: caching.aggressive_cleanup = true"
fi

# 并发配置建议
max_hooks=$((cpu_cores * 2))
max_agents=$((cpu_cores * 3))

echo "⚙️ 推荐并发配置:"
echo "  max_concurrent_hooks: $max_hooks"
echo "  max_concurrent_agents: $max_agents"

# Hook超时建议
echo "⏱️ 推荐超时配置:"
echo "  系统检查Hook: 500ms"
echo "  Agent选择Hook: 2000ms"
echo "  性能监控Hook: 200ms"
```

## 📋 配置最佳实践

### 1. 分环境配置
```bash
# 使用配置继承
.claude/
├── settings.base.json          # 基础配置
├── settings.development.json   # 开发环境
├── settings.production.json    # 生产环境
└── settings.test.json         # 测试环境
```

### 2. 敏感信息管理
```bash
# 使用环境变量
export CLAUDE_ENHANCER_CONFIG_DIR="/secure/path"
export CLAUDE_ENHANCER_SECRETS_FILE="/secure/secrets.json"

# 配置文件权限
chmod 600 .claude/secrets/*.json
```

### 3. 配置版本控制
```bash
# 忽略敏感文件
echo ".claude/secrets/" >> .gitignore
echo ".claude/*.local.json" >> .gitignore

# 提供模板文件
cp .claude/secrets/secrets.json .claude/secrets/secrets.json.template
```

### 4. 配置监控
```json
{
  "config_monitoring": {
    "enabled": true,
    "watch_files": true,
    "auto_reload": true,
    "validation": {
      "on_change": true,
      "strict_mode": true
    }
  }
}
```

### 5. 性能调优
```json
{
  "performance_tuning": {
    "memory_based": {
      "low_memory": {
        "threshold": "2GB",
        "optimizations": ["reduce_cache", "limit_concurrency"]
      },
      "high_memory": {
        "threshold": "8GB",
        "optimizations": ["increase_cache", "enable_preloading"]
      }
    },
    "cpu_based": {
      "low_cpu": {
        "cores": 2,
        "optimizations": ["reduce_parallelism", "defer_non_critical"]
      },
      "high_cpu": {
        "cores": 8,
        "optimizations": ["increase_parallelism", "enable_batching"]
      }
    }
  }
}
```

## 🔄 配置升级

### 从5.0升级到5.1
```bash
# 1. 备份现有配置
cp .claude/settings.json .claude/settings.json.bak

# 2. 运行配置迁移
node .claude/scripts/migrate-config-5.0-to-5.1.js

# 3. 验证新配置
bash .claude/scripts/validate-config.sh

# 4. 测试功能
npm run test:config
```

## 🆘 故障排除

### 常见配置问题
1. **Hook超时** - 增加timeout值或优化Hook脚本
2. **内存不足** - 启用激进垃圾回收，减少缓存大小
3. **Agent连接失败** - 检查网络配置和防火墙设置
4. **配置文件格式错误** - 使用JSON验证工具检查语法

### 配置诊断命令
```bash
# 配置健康检查
npm run config:health

# 配置性能分析
npm run config:analyze

# 配置重置
npm run config:reset

# 配置导出
npm run config:export > my-config-backup.json
```

---

**Claude Enhancer 5.1 配置指南**
*版本: v5.1.0 | 更新时间: 2025-01-26*

需要帮助？访问：
- 📚 [完整文档](https://docs.claude-enhancer.com/config/)
- 💬 [配置支持](https://support.claude-enhancer.com/config)
- 🛠️ [配置工具](https://tools.claude-enhancer.com/config-builder)