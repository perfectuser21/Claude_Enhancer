#!/bin/bash
# 分析hooks，识别重复和过时的文件

cd "/home/xx/dev/Claude Enhancer 5.0/.claude/hooks"

echo "🔍 Claude Enhancer Hooks分析"
echo "============================="
echo

# 1. 识别重复的hooks
echo "📋 重复/变体的hooks："
echo

# Agent selector系列
echo "【Agent Selector系列】"
echo "主版本: smart_agent_selector.sh (已修复)"
echo "重复版本:"
for f in smart_agent_selector_*.sh ultra_fast_agent_selector.sh user_friendly_agent_selector.sh; do
    [[ -f "$f" ]] && echo "  - $f ($(wc -l < "$f")行)"
done
echo

# Performance monitor系列
echo "【Performance Monitor系列】"
echo "可能的主版本: performance_monitor.sh"
echo "重复版本:"
for f in performance_monitor_*.sh optimized_performance_monitor.sh performance_optimized_hooks*.sh; do
    [[ -f "$f" ]] && echo "  - $f ($(wc -l < "$f")行)"
done
echo

# Error recovery系列
echo "【Error Recovery系列】"
echo "主版本: agent_error_recovery.sh (已修复)"
echo "可能重复:"
for f in error_recovery.sh smart_error_recovery.sh; do
    [[ -f "$f" ]] && echo "  - $f ($(wc -l < "$f")行)"
done
echo

# Workflow enforcer系列
echo "【Workflow Enforcer系列】"
echo "主版本: workflow_enforcer.sh (已修复)"
echo "可能重复:"
for f in enforce_workflow.sh system_prompt_workflow_enforcer.sh unified_workflow_orchestrator.sh; do
    [[ -f "$f" ]] && echo "  - $f ($(wc -l < "$f")行)"
done
echo

# 2. 系统提示系列（可能是实验性的）
echo "📋 System Prompt系列（实验性？）："
ls -1 system_prompt_*.sh 2>/dev/null | while read f; do
    echo "  - $f ($(wc -l < "$f")行)"
done
echo

# 3. 简单版本系列
echo "📋 Simple系列（简化版？）："
ls -1 simple_*.sh 2>/dev/null | while read f; do
    echo "  - $f ($(wc -l < "$f")行)"
done
echo

# 4. 工具/安装脚本（非hooks）
echo "📋 工具脚本（非hooks）："
for f in install.sh fix_git_hooks.sh hook_wrapper.sh; do
    [[ -f "$f" ]] && echo "  - $f"
done
echo

# 5. 统计
echo "📊 统计："
TOTAL=$(ls -1 *.sh | wc -l)
FIXED=$(grep -l "CE_SILENT_MODE.*!=" *.sh 2>/dev/null | wc -l)
echo "  总hooks数: $TOTAL"
echo "  已修复: $FIXED"
echo "  待处理: $((TOTAL - FIXED))"
echo

# 6. 建议保留的核心hooks
echo "✅ 建议保留的核心hooks："
cat << 'EOF'
1. smart_agent_selector.sh - Agent选择器（已修复）
2. workflow_enforcer.sh - 工作流强制器（已修复）
3. branch_helper.sh - 分支助手（已修复）
4. quality_gate.sh - 质量门禁（已修复）
5. gap_scan.sh - 差距扫描（已修复）
6. unified_post_processor.sh - 后处理器（已修复）
7. workflow_auto_start.sh - 自动启动（已修复）
8. agent_error_recovery.sh - 错误恢复（已修复）
9. auto_cleanup_check.sh - 清理检查（已修复）
10. code_writing_check.sh - 代码检查（已修复）
11. concurrent_optimizer.sh - 并发优化（已修复）
12. error_handler.sh - 错误处理（已修复）

待修复的重要hooks：
13. commit_quality_gate.sh - 提交质量检查
14. design_advisor.sh - 设计顾问
15. git_status_monitor.sh - Git状态监控
16. implementation_orchestrator.sh - 实现协调器
17. parallel_agent_highlighter.sh - 并行Agent高亮
18. requirements_validator.sh - 需求验证器
19. review_preparation.sh - 审查准备
20. smart_cleanup_advisor.sh - 清理顾问
21. smart_git_workflow.sh - Git工作流
22. task_type_detector.sh - 任务类型检测
23. testing_coordinator.sh - 测试协调器
24. workflow_auto_trigger_integration.sh - 工作流触发集成
25. workflow_executor_integration.sh - 工作流执行集成
EOF
echo

echo "❌ 建议删除的重复/过时hooks："
cat << 'EOF'
1. smart_agent_selector_fixed.sh - 重复
2. smart_agent_selector_optimized.sh - 重复
3. smart_agent_selector_simple.sh - 重复
4. ultra_fast_agent_selector.sh - 重复
5. user_friendly_agent_selector.sh - 重复
6. performance_monitor.sh - 被optimized版本替代
7. performance_monitor_optimized.sh - 重复
8. performance_optimized_hooks.sh - 重复
9. performance_optimized_hooks_SECURE.sh - 重复
10. error_recovery.sh - 被agent_error_recovery替代
11. smart_error_recovery.sh - 重复
12. enforce_workflow.sh - 重复
13. unified_workflow_orchestrator.sh - 重复
14. system_prompt_*.sh (5个) - 实验性，可删除
15. simple_*.sh (3个) - 简化版，可删除
16. fix_git_hooks.sh - 临时脚本
17. install.sh - 安装脚本，非hook
18. hook_wrapper.sh - 包装器，不需要
19. start_high_performance_engine.sh - 实验性
EOF