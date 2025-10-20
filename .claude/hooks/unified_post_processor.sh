#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer - 统一后处理器
# 智能结果分析、进度跟踪、性能优化

# 统一日志记录（激活追踪）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/claude_hooks.log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date +'%F %T') [unified_post_processor.sh] triggered by ${USER:-claude}" >> "$LOG_FILE"

set -e

readonly PROGRESS_FILE="/tmp/claude_phase_progress"
readonly RESULTS_CACHE="/tmp/claude_results_cache"
readonly METRICS_FILE="/tmp/claude_execution_metrics"

# Quick result analysis
analyze_execution_result() {
    local tool_name="$1"
    local success_pattern="$2"

    local status="unknown"
    local phase_progress=""

    # Determine execution status and phase progression
    case "$tool_name" in
        "Task")
            status="agent_coordination"
            phase_progress="P4_implementation_active"
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo "🤖 Agent并行执行完成" >&2
            elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
                echo "[Post] Agent执行完成" >&2
            fi
            ;;
        "Write"|"Edit"|"MultiEdit")
            status="code_generation"
            phase_progress="P4_implementation_progress"
            local files_modified=$(git diff --name-only 2>/dev/null | wc -l)
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo "📝 代码修改: ${files_modified} 个文件" >&2
            elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
                echo "[Post] 修改${files_modified}文件" >&2
            fi
            ;;
        "Bash")
            if echo "$success_pattern" | grep -q "git.*commit"; then
                status="commit_completed"
                phase_progress="P6_commit_done"
                if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                    echo "📝 代码提交完成" >&2
                elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
                    echo "[Post] 提交完成" >&2
                fi
            elif echo "$success_pattern" | grep -q "test\|pytest\|jest"; then
                status="testing_completed"
                phase_progress="P5_testing_done"
                if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                    echo "🧪 测试执行完成" >&2
                elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
                    echo "[Post] 测试完成" >&2
                fi
            elif echo "$success_pattern" | grep -q "git.*push"; then
                status="push_completed"
                phase_progress="P7_review_ready"
                if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                    echo "🚀 代码推送完成" >&2
                elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
                    echo "[Post] 推送完成" >&2
                fi
            else
                status="command_executed"
                if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                    echo "⚡ 命令执行完成" >&2
                elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
                    echo "[Post] 执行完成" >&2
                fi
            fi
            ;;
        "Read"|"Grep"|"Glob")
            status="analysis_completed"
            phase_progress="P2_analysis_progress"
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo "🔍 分析完成" >&2
            elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
                echo "[Post] 分析完成" >&2
            fi
            ;;
    esac

    # Update progress tracking
    if [[ -n "$phase_progress" ]]; then
        echo "$(date +%s),$phase_progress,$tool_name" >> "$PROGRESS_FILE" 2>/dev/null || true
    fi

    # Update execution metrics
    echo "$(date +%s),$tool_name,$status" >> "$METRICS_FILE" 2>/dev/null || true
}

# Smart progress tracking
update_workflow_progress() {
    local current_phase="P2_discovery"  # Default

    # Detect current phase from recent activity
    if [[ -f "$PROGRESS_FILE" ]]; then
        local recent_activity=$(tail -5 "$PROGRESS_FILE" 2>/dev/null | cut -d',' -f2)

        # Determine phase from recent patterns
        if echo "$recent_activity" | grep -q "P6_commit_done"; then
            current_phase="P7_release"
        elif echo "$recent_activity" | grep -q "P5_testing"; then
            current_phase="P6_review"
        elif echo "$recent_activity" | grep -q "P4_implementation"; then
            current_phase="P5_testing"
        elif echo "$recent_activity" | grep -q "P3_planning"; then
            current_phase="P4_implementation"
        elif echo "$recent_activity" | grep -q "P2_analysis"; then
            current_phase="P3_planning"
        fi
    fi

    # Provide phase-specific guidance
    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
        case "$current_phase" in
            "P2_discovery")
                echo "🔍 Phase 2: 探索发现中..." >&2
                ;;
            "P3_planning")
                echo "🎨 Phase 3: 规划+架构阶段" >&2
                ;;
            "P4_implementation")
                echo "⚙️ Phase 4: 实现开发中..." >&2
                ;;
            "P5_testing")
                echo "🧪 Phase 5: 测试验证阶段（质量门禁1）" >&2
                echo "💡 建议: 运行 npm test 或 pytest" >&2
                ;;
            "P6_review")
                echo "👀 Phase 6: 代码审查阶段（质量门禁2）" >&2
                echo "💡 建议: 创建 Pull Request" >&2
                ;;
            "P7_release")
                echo "🚀 Phase 7: 发布+监控阶段" >&2
                echo "💡 建议: 更新文档并部署" >&2
                ;;
        esac
    elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
        echo "[Post] Phase: $current_phase" >&2
    fi
}

# Performance monitoring
monitor_execution_performance() {
    local start_time_file="/tmp/claude_exec_start_$$"

    # Calculate execution duration if start time available
    if [[ -f "$start_time_file" ]]; then
        local start_time=$(cat "$start_time_file")
        local end_time=$(date +%s%N)
        local duration_ms=$(( (end_time - start_time) / 1000000 ))

        if [[ $duration_ms -gt 1000 ]]; then
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo "⏱️ 执行时间: ${duration_ms}ms" >&2
            elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
                echo "[Post] ${duration_ms}ms" >&2
            fi

            # Log slow executions for optimization
            if [[ $duration_ms -gt 5000 ]]; then
                echo "$(date +%s),$duration_ms,slow_execution" >> "/tmp/claude_slow_ops" 2>/dev/null || true
            fi
        fi

        rm -f "$start_time_file" 2>/dev/null || true
    fi
}

# Intelligent suggestions based on execution patterns
provide_smart_suggestions() {
    local tool_name="$1"
    local execution_context="$2"

    # Check recent execution patterns
    if [[ -f "$METRICS_FILE" ]]; then
        local recent_tools=$(tail -10 "$METRICS_FILE" 2>/dev/null | cut -d',' -f2)
        local tool_count=$(echo "$recent_tools" | sort | uniq -c | sort -rn)

        # Detect repetitive patterns
        local most_used_tool=$(echo "$tool_count" | head -1 | awk '{print $2}')
        local usage_count=$(echo "$tool_count" | head -1 | awk '{print $1}')

        if [[ $usage_count -gt 3 ]]; then
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                case "$most_used_tool" in
                    "Read")
                        echo "💡 优化建议: 考虑使用 Grep 进行更精准的搜索" >&2
                        ;;
                    "Edit")
                        echo "💡 优化建议: 多次编辑可考虑使用 MultiEdit" >&2
                        ;;
                    "Bash")
                        echo "💡 优化建议: 频繁命令执行，考虑写成脚本" >&2
                        ;;
                esac
            fi
        fi
    fi

    # Context-specific suggestions
    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
        case "$tool_name" in
            "Task")
                echo "💡 下一步建议: 使用 Write/Edit 实现Agent建议" >&2
                ;;
            "Write"|"Edit")
                echo "💡 下一步建议: 运行测试验证代码" >&2
                ;;
            "Bash")
                if echo "$execution_context" | grep -q "test"; then
                    echo "💡 下一步建议: 如果测试通过，可以提交代码" >&2
                fi
                ;;
        esac
    fi
}

# Error pattern detection
detect_error_patterns() {
    local tool_name="$1"
    local output_content="$2"

    # Check for common error indicators
    if echo "$output_content" | grep -qi "error\|failed\|exception"; then
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "⚠️ 检测到可能的错误信息" >&2
            echo "🔧 建议: 查看详细错误信息并进行调试" >&2
        elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
            echo "[Post] ⚠️ 错误检测" >&2
        fi

        # Log error pattern for analysis
        echo "$(date +%s),$tool_name,error_detected" >> "/tmp/claude_error_patterns" 2>/dev/null || true
    fi
}

# Resource usage optimization
optimize_resource_usage() {
    local tool_name="$1"

    # Clean up old cache files
    if [[ $(find /tmp -name "claude_*" -type f 2>/dev/null | wc -l) -gt 50 ]]; then
        find /tmp -name "claude_*" -type f -mtime +1 -delete 2>/dev/null || true
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "🧹 清理了过期缓存文件" >&2
        elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
            echo "[Post] 缓存清理" >&2
        fi
    fi

    # Rotate large log files
    for logfile in "$PROGRESS_FILE" "$METRICS_FILE" "/tmp/claude_error_patterns"; do
        if [[ -f "$logfile" && $(wc -l < "$logfile") -gt 1000 ]]; then
            tail -500 "$logfile" > "${logfile}.tmp" 2>/dev/null || true
            mv "${logfile}.tmp" "$logfile" 2>/dev/null || true
        fi
    done
}

# Main processing function
main() {
    local input=$(cat)

    # Extract tool information from input/context
    local tool_name=$(echo "$input" | grep -oP '"name"\s*:\s*"\K[^"]+' | head -1)
    local execution_context=$(echo "$input" | head -c 200)  # First 200 chars for context

    # Skip processing if no meaningful tool detected
    if [[ -z "$tool_name" || ${#input} -lt 20 ]]; then
        echo "$input"
        exit 0
    fi

    # Record start time for performance tracking
    echo "$(date +%s%N)" > "/tmp/claude_exec_start_$$"

    # Execute post-processing tasks in parallel where possible
    (
        analyze_execution_result "$tool_name" "$execution_context"
        update_workflow_progress
        provide_smart_suggestions "$tool_name" "$execution_context"
        detect_error_patterns "$tool_name" "$input"
    ) &

    # Background optimization
    (
        monitor_execution_performance
        optimize_resource_usage "$tool_name"
    ) &

    # Wait for background tasks
    wait

    # Output original input unchanged
    echo "$input"
}

# Cleanup on exit
cleanup() {
    rm -f "/tmp/claude_exec_start_$$" 2>/dev/null || true
}

trap cleanup EXIT

# Execute main function
main "$@"
