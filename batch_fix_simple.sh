#!/bin/bash
# 批量修复剩余的简单hooks

cd "/home/xx/dev/Claude Enhancer 5.0/.claude/hooks"

echo "🔧 批量修复剩余hooks"
echo "==================="
echo

# 修复implementation_orchestrator.sh
echo "修复 implementation_orchestrator.sh..."
cat > implementation_orchestrator.sh.tmp << 'EOF'
#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 实现协调器

if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "🎭 Implementation Orchestrator Active"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 协调多个Agent并行工作："
    echo "  • backend-architect - 架构设计"
    echo "  • fullstack-engineer - 全栈开发"
    echo "  • test-engineer - 测试实现"
    echo "  • code-reviewer - 代码审查"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    echo "[Orchestrator] Active"
fi

exit 0
EOF
[[ -f implementation_orchestrator.sh ]] && mv implementation_orchestrator.sh.tmp implementation_orchestrator.sh && echo "  ✅ 完成"

# 修复parallel_agent_highlighter.sh
echo "修复 parallel_agent_highlighter.sh..."
cat > parallel_agent_highlighter.sh.tmp << 'EOF'
#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 并行Agent高亮器

if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "🌈 Parallel Agent Highlighter"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "💡 提醒：所有Agent应该并行执行"
    echo "  ✅ 正确：在同一function_calls块中"
    echo "  ❌ 错误：分开调用Agent"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    echo "[Parallel] Agents并行提醒"
fi

exit 0
EOF
[[ -f parallel_agent_highlighter.sh ]] && mv parallel_agent_highlighter.sh.tmp parallel_agent_highlighter.sh && echo "  ✅ 完成"

# 修复requirements_validator.sh
echo "修复 requirements_validator.sh..."
cat > requirements_validator.sh.tmp << 'EOF'
#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 需求验证器

if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "📋 Requirements Validator"
    echo "━━━━━━━━━━━━━━━━━━━━━━━"
    echo "检查需求文档完整性："
    if [[ -f "docs/PLAN.md" ]]; then
        echo "  ✅ PLAN.md 存在"
    else
        echo "  ❌ PLAN.md 缺失"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    if [[ -f "docs/PLAN.md" ]]; then
        echo "[Requirements] ✅ PLAN.md"
    else
        echo "[Requirements] ❌ 缺少PLAN.md"
    fi
fi

exit 0
EOF
[[ -f requirements_validator.sh ]] && mv requirements_validator.sh.tmp requirements_validator.sh && echo "  ✅ 完成"

# 修复review_preparation.sh
echo "修复 review_preparation.sh..."
cat > review_preparation.sh.tmp << 'EOF'
#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 审查准备

if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "👀 Review Preparation"
    echo "━━━━━━━━━━━━━━━━━━━"
    echo "📋 代码审查准备清单："
    echo "  • 代码格式化"
    echo "  • 测试通过"
    echo "  • 文档更新"
    echo "  • PR描述完整"
    echo "━━━━━━━━━━━━━━━━━━━"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    echo "[Review] 准备中"
fi

exit 0
EOF
[[ -f review_preparation.sh ]] && mv review_preparation.sh.tmp review_preparation.sh && echo "  ✅ 完成"

# 修复smart_cleanup_advisor.sh
echo "修复 smart_cleanup_advisor.sh..."
cat > smart_cleanup_advisor.sh.tmp << 'EOF'
#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 智能清理顾问

TEMP_FILES=$(find . -name "*.tmp" -o -name "*.log" -o -name "*~" 2>/dev/null | wc -l)

if [[ $TEMP_FILES -gt 20 ]]; then
    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
        echo "🧹 Smart Cleanup Advisor"
        echo "━━━━━━━━━━━━━━━━━━━━━"
        echo "发现 $TEMP_FILES 个临时文件"
        echo "建议运行清理脚本"
        echo "━━━━━━━━━━━━━━━━━━━━━"
    elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
        echo "[Cleanup] ${TEMP_FILES}个临时文件"
    fi
fi

exit 0
EOF
[[ -f smart_cleanup_advisor.sh ]] && mv smart_cleanup_advisor.sh.tmp smart_cleanup_advisor.sh && echo "  ✅ 完成"

# 修复smart_git_workflow.sh
echo "修复 smart_git_workflow.sh..."
cat > smart_git_workflow.sh.tmp << 'EOF'
#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 智能Git工作流

CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)

if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "🔀 Smart Git Workflow"
    echo "━━━━━━━━━━━━━━━━━━━"
    echo "当前分支: $CURRENT_BRANCH"

    if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
        echo "⚠️ 在主分支上，建议创建feature分支"
    else
        echo "✅ 在feature分支上"
    fi
    echo "━━━━━━━━━━━━━━━━━━━"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
        echo "[Git] ⚠️ 主分支"
    else
        echo "[Git] ✅ $CURRENT_BRANCH"
    fi
fi

exit 0
EOF
[[ -f smart_git_workflow.sh ]] && mv smart_git_workflow.sh.tmp smart_git_workflow.sh && echo "  ✅ 完成"

# 修复testing_coordinator.sh
echo "修复 testing_coordinator.sh..."
cat > testing_coordinator.sh.tmp << 'EOF'
#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 测试协调器

if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "🧪 Testing Coordinator"
    echo "━━━━━━━━━━━━━━━━━━━"
    echo "📋 测试策略："
    echo "  • 单元测试"
    echo "  • 集成测试"
    echo "  • 性能测试"
    echo "  • 端到端测试"
    echo "━━━━━━━━━━━━━━━━━━━"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    echo "[Test] 协调中"
fi

exit 0
EOF
[[ -f testing_coordinator.sh ]] && mv testing_coordinator.sh.tmp testing_coordinator.sh && echo "  ✅ 完成"

# 修复workflow_auto_trigger_integration.sh
echo "修复 workflow_auto_trigger_integration.sh..."
cat > workflow_auto_trigger_integration.sh.tmp << 'EOF'
#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 工作流自动触发集成

if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "⚡ Workflow Auto Trigger"
    echo "━━━━━━━━━━━━━━━━━━━━━"
    echo "监控工作流触发条件..."
    echo "━━━━━━━━━━━━━━━━━━━━━"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    echo "[Trigger] 监控中"
fi

exit 0
EOF
[[ -f workflow_auto_trigger_integration.sh ]] && mv workflow_auto_trigger_integration.sh.tmp workflow_auto_trigger_integration.sh && echo "  ✅ 完成"

# 修复workflow_executor_integration.sh
echo "修复 workflow_executor_integration.sh..."
cat > workflow_executor_integration.sh.tmp << 'EOF'
#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 工作流执行集成

if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "🚀 Workflow Executor Integration"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "执行8-Phase工作流..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    echo "[Executor] 执行中"
fi

exit 0
EOF
[[ -f workflow_executor_integration.sh ]] && mv workflow_executor_integration.sh.tmp workflow_executor_integration.sh && echo "  ✅ 完成"

echo
echo "✨ 批量修复完成！"