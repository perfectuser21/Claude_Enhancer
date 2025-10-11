#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer - 统一工作流调度器
# 智能Hook批处理，减少重复检查，优化执行效率

set -e

# Performance configuration
readonly CACHE_TTL=300  # 5 minutes
readonly CONTEXT_CACHE="/tmp/claude_context_cache"
readonly PHASE_STATE_FILE="/tmp/claude_current_phase"
readonly HOOK_METRICS="/tmp/claude_hook_metrics"

# Context analysis cache
declare -A CONTEXT_CACHE_MAP
declare -A EXECUTION_STATS

# Initialize performance tracking
init_performance_tracking() {
    local start_time=$(date +%s%N)
    echo "$start_time" > "/tmp/orchestrator_start_$$"
}

# Smart context analysis - only parse once
analyze_context_smart() {
    local input="$1"
    local cache_key=$(echo "$input" | md5sum | cut -d' ' -f1)

    # Check cache first
    local cache_file="$CONTEXT_CACHE/$cache_key"
    if [[ -f "$cache_file" && $(( $(date +%s) - $(stat -f %m "$cache_file" 2>/dev/null || stat -c %Y "$cache_file") )) -lt $CACHE_TTL ]]; then
        cat "$cache_file"
        return 0
    fi

    # Parse context
    local tool_name=$(echo "$input" | grep -oP '"name"\s*:\s*"\K[^"]+' | head -1)
    local prompt_text=$(echo "$input" | grep -oP '"prompt"\s*:\s*"\K[^"]+' | head -1)
    local task_description=$(echo "$input" | grep -oP '"description"\s*:\s*"\K[^"]+' | head -1)

    # Determine current phase from git and task context
    local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    local git_status=$(git status --porcelain 2>/dev/null | wc -l)

    local phase="P1_analysis"  # Default

    # Smart phase detection
    case "$current_branch" in
        main|master) phase="P0_branch_creation" ;;
        feature/*|fix/*|refactor/*)
            if [[ $git_status -eq 0 ]]; then
                phase="P6_review"
            elif [[ "$tool_name" == "Task" ]]; then
                phase="P3_implementation"
            elif [[ "$tool_name" =~ ^(Write|Edit|MultiEdit)$ ]]; then
                phase="P3_implementation"
            elif [[ "$tool_name" == "Bash" && "$prompt_text" =~ test ]]; then
                phase="P4_testing"
            elif [[ "$tool_name" == "Bash" && "$prompt_text" =~ git ]]; then
                phase="P5_commit"
            else
                phase="P2_design"
            fi
            ;;
    esac

    # Task complexity analysis
    local complexity="standard"
    if [[ -n "$prompt_text$task_description" ]]; then
        local combined_text=$(echo "$prompt_text $task_description" | tr '[:upper:]' '[:lower:]')
        local complex_indicators=$(echo "$combined_text" | grep -oE "(architect|design system|migrate|refactor entire|microservices|distributed)" | wc -l)
        local simple_indicators=$(echo "$combined_text" | grep -oE "(fix bug|typo|minor|quick|simple)" | wc -l)

        if [[ $complex_indicators -gt 1 ]]; then
            complexity="complex"
        elif [[ $simple_indicators -gt 0 && $complex_indicators -eq 0 ]]; then
            complexity="simple"
        fi
    fi

    # Cache and output result
    local context_result="{\"tool\":\"$tool_name\",\"phase\":\"$phase\",\"complexity\":\"$complexity\",\"branch\":\"$current_branch\",\"git_changes\":$git_status,\"prompt\":\"$(echo "$prompt_text" | head -c 50)\"}"

    mkdir -p "$CONTEXT_CACHE"
    echo "$context_result" > "$cache_file"
    echo "$context_result"
}

# Batch hook execution based on context
execute_hooks_batch() {
    local context="$1"
    local phase=$(echo "$context" | grep -oP '"phase"\s*:\s*"\K[^"]+')
    local tool=$(echo "$context" | grep -oP '"tool"\s*:\s*"\K[^"]+')
    local complexity=$(echo "$context" | grep -oP '"complexity"\s*:\s*"\K[^"]+')

    local hooks_to_run=()
    local messages=()

    # Smart hook selection based on phase and tool
    case "$phase" in
        "P0_branch_creation")
            if [[ "$tool" != "Bash" ]]; then
                hooks_to_run+=("branch_helper")
                messages+=("🌿 Branch创建建议")
            fi
            ;;
        "P1_analysis"|"P2_design")
            hooks_to_run+=("task_analyzer")
            messages+=("📊 任务分析")
            ;;
        "P3_implementation")
            if [[ "$tool" == "Task" ]]; then
                hooks_to_run+=("agent_selector")
                messages+=("🤖 Agent选择: $complexity 任务")
            fi
            if [[ "$tool" =~ ^(Write|Edit|MultiEdit)$ ]]; then
                hooks_to_run+=("quality_gate")
                messages+=("🎯 代码质量预检")
            fi
            ;;
        "P4_testing")
            hooks_to_run+=("test_monitor")
            messages+=("🧪 测试监控")
            ;;
        "P5_commit"|"P6_review")
            if [[ "$tool" == "Bash" && $(echo "$context" | grep -c "git") -gt 0 ]]; then
                hooks_to_run+=("git_workflow")
                messages+=("📝 Git工作流")
            fi
            ;;
    esac

    # Execute selected hooks efficiently
    for i in "${!hooks_to_run[@]}"; do
        local hook="${hooks_to_run[$i]}"
        local message="${messages[$i]}"

        case "$hook" in
            "branch_helper")
                execute_branch_helper_fast "$context"
                ;;
            "agent_selector")
                execute_agent_selector_fast "$context" "$complexity"
                ;;
            "quality_gate")
                execute_quality_gate_fast "$context"
                ;;
            "git_workflow")
                execute_git_workflow_fast "$context"
                ;;
            *)
                echo "$message" >&2
                ;;
        esac
    done
}

# Fast hook implementations
execute_branch_helper_fast() {
    local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

    if [[ "$current_branch" == "main" || "$current_branch" == "master" ]]; then
        echo "🌿 建议创建feature分支进行开发" >&2
        echo "  git checkout -b feature/your-feature" >&2
    else
        echo "🌿 当前分支: $current_branch ✅" >&2
    fi
}

execute_agent_selector_fast() {
    local context="$1"
    local complexity="$2"

    local agent_count
    case "$complexity" in
        "simple") agent_count="4" ;;
        "complex") agent_count="8" ;;
        *) agent_count="6" ;;
    esac

    echo "🤖 推荐 $agent_count 个Agent ($complexity 任务)" >&2

    # Log for metrics
    echo "$(date +%s),$complexity,$agent_count" >> "$HOOK_METRICS" 2>/dev/null || true
}

execute_quality_gate_fast() {
    local context="$1"
    local prompt=$(echo "$context" | grep -oP '"prompt"\s*:\s*"\K[^"]+')

    local score=100
    local warnings=()

    # Quick quality checks
    if [[ ${#prompt} -lt 10 ]]; then
        warnings+=("⚠️ 任务描述偏短")
        ((score-=10))
    fi

    if echo "$prompt" | grep -qE "(删除全部|rm -rf|格式化)"; then
        warnings+=("🚨 潜在危险操作")
        ((score-=30))
    fi

    if [[ ${#warnings[@]} -gt 0 ]]; then
        echo "🎯 质量评分: $score/100" >&2
        printf "  %s\n" "${warnings[@]}" >&2
    else
        echo "✅ 质量检查通过" >&2
    fi
}

execute_git_workflow_fast() {
    local git_status=$(git status --porcelain 2>/dev/null | wc -l)

    if [[ $git_status -gt 0 ]]; then
        echo "📝 检测到 $git_status 个文件变更" >&2
        echo "💡 提交前记得运行测试" >&2
    else
        echo "📝 工作区干净 ✅" >&2
    fi
}

# Performance monitoring
track_performance() {
    local start_file="/tmp/orchestrator_start_$$"
    if [[ -f "$start_file" ]]; then
        local start_time=$(cat "$start_file")
        local end_time=$(date +%s%N)
        local duration_ms=$(( (end_time - start_time) / 1000000 ))

        echo "⚡ 统一调度器执行时间: ${duration_ms}ms" >&2

        # Update performance stats
        echo "$(date +%s),$duration_ms" >> "/tmp/orchestrator_perf" 2>/dev/null || true

        rm -f "$start_file" 2>/dev/null || true
    fi
}

# Main execution
main() {
    local input=$(cat)

    # Skip if input is too small (likely not a real task)
    if [[ ${#input} -lt 20 ]]; then
        echo "$input"
        exit 0
    fi

    init_performance_tracking

    # Smart context analysis (cached)
    local context=$(analyze_context_smart "$input")

    # Batch hook execution
    execute_hooks_batch "$context"

    # Performance tracking
    track_performance

    # Output original input unchanged
    echo "$input"
}

# Cleanup function for cache management
cleanup_cache() {
    if [[ -d "$CONTEXT_CACHE" ]]; then
        find "$CONTEXT_CACHE" -type f -mtime +1 -delete 2>/dev/null || true
    fi

    # Keep hook metrics file reasonable size
    if [[ -f "$HOOK_METRICS" && $(wc -l < "$HOOK_METRICS") -gt 1000 ]]; then
        tail -500 "$HOOK_METRICS" > "${HOOK_METRICS}.tmp" 2>/dev/null || true
        mv "${HOOK_METRICS}.tmp" "$HOOK_METRICS" 2>/dev/null || true
    fi
}

# Handle script termination
trap cleanup_cache EXIT

# Execute main function
main "$@"