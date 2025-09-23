#!/bin/bash
# Claude Enhancer Performance Monitor
# Real-time performance tracking and optimization recommendations

set -e

# Configuration
MONITOR_DIR="/tmp/perfect21_monitor"
LOG_FILE="$MONITOR_DIR/performance.log"
METRICS_FILE="$MONITOR_DIR/metrics.json"
ALERT_THRESHOLD_MS=${ALERT_THRESHOLD_MS:-1000}
ENABLE_REAL_TIME=${ENABLE_REAL_TIME:-false}

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[0;35m'
readonly NC='\033[0m'

# Performance metrics storage
declare -A CURRENT_METRICS
declare -A BASELINE_METRICS
declare -A PERFORMANCE_HISTORY

# Initialize monitoring system
init_monitor() {
    mkdir -p "$MONITOR_DIR"
    touch "$LOG_FILE" "$METRICS_FILE"

    # Load baseline metrics if available
    if [[ -f "$METRICS_FILE" ]]; then
        load_baseline_metrics
    else
        establish_baseline
    fi
}

# Establish performance baseline
establish_baseline() {
    echo -e "${BLUE}📊 建立性能基准线${NC}"

    # Test cleanup script performance
    local cleanup_time=$(test_cleanup_performance)
    BASELINE_METRICS["cleanup_avg"]=$cleanup_time

    # Test agent selector performance
    local agent_time=$(test_agent_selector_performance)
    BASELINE_METRICS["agent_avg"]=$agent_time

    # Test file operations
    local file_ops_time=$(test_file_operations)
    BASELINE_METRICS["file_ops_avg"]=$file_ops_time

    # Save baseline
    save_baseline_metrics

    echo "  ✅ 基准线已建立"
    echo "    清理脚本: ${cleanup_time}ms"
    echo "    Agent选择: ${agent_time}ms"
    echo "    文件操作: ${file_ops_time}ms"
}

# Load baseline metrics
load_baseline_metrics() {
    if [[ -s "$METRICS_FILE" ]]; then
        while IFS='=' read -r key value; do
            BASELINE_METRICS["$key"]="$value"
        done < "$METRICS_FILE"
    fi
}

# Save baseline metrics
save_baseline_metrics() {
    > "$METRICS_FILE"
    for key in "${!BASELINE_METRICS[@]}"; do
        echo "$key=${BASELINE_METRICS[$key]}" >> "$METRICS_FILE"
    done
}

# Test cleanup performance
test_cleanup_performance() {
    local test_dir="/tmp/perf_test_cleanup"
    setup_mini_test_env "$test_dir"

    local start_time=$(date +%s%N)
    bash /home/xx/dev/Claude Enhancer/.claude/scripts/performance_optimized_cleanup.sh 5 >/dev/null 2>&1
    local end_time=$(date +%s%N)

    rm -rf "$test_dir"
    echo $(( (end_time - start_time) / 1000000 ))
}

# Test agent selector performance
test_agent_selector_performance() {
    local test_input='{"prompt": "implement feature", "phase": 3}'

    local start_time=$(date +%s%N)
    echo "$test_input" | bash /home/xx/dev/Claude Enhancer/.claude/hooks/smart_agent_selector.sh >/dev/null 2>&1
    local end_time=$(date +%s%N)

    echo $(( (end_time - start_time) / 1000000 ))
}

# Test file operations
test_file_operations() {
    local test_dir="/tmp/perf_test_files"
    setup_mini_test_env "$test_dir"

    local start_time=$(date +%s%N)
    find "$test_dir" -name "*.tmp" -o -name "*.pyc" >/dev/null 2>&1
    grep -r "console.log" "$test_dir" >/dev/null 2>&1 || true
    local end_time=$(date +%s%N)

    rm -rf "$test_dir"
    echo $(( (end_time - start_time) / 1000000 ))
}

# Setup minimal test environment
setup_mini_test_env() {
    local test_dir="$1"
    mkdir -p "$test_dir"

    # Create minimal test files
    for i in {1..5}; do
        echo "console.log('test $i');" > "$test_dir/test$i.js"
        echo "print('test $i')" > "$test_dir/test$i.py"
        touch "$test_dir/temp$i.tmp"
        touch "$test_dir/cache$i.pyc"
    done
}

# Monitor current performance
monitor_current_performance() {
    echo -e "${CYAN}🔍 监控当前性能${NC}"

    # Test current performance
    CURRENT_METRICS["cleanup_avg"]=$(test_cleanup_performance)
    CURRENT_METRICS["agent_avg"]=$(test_agent_selector_performance)
    CURRENT_METRICS["file_ops_avg"]=$(test_file_operations)
    CURRENT_METRICS["timestamp"]=$(date +%s)

    # Log performance data
    log_performance_data

    # Analyze performance
    analyze_performance_trends

    # Check for alerts
    check_performance_alerts
}

# Log performance data
log_performance_data() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local cleanup_time=${CURRENT_METRICS["cleanup_avg"]}
    local agent_time=${CURRENT_METRICS["agent_avg"]}
    local file_ops_time=${CURRENT_METRICS["file_ops_avg"]}

    echo "[$timestamp] CLEANUP:${cleanup_time}ms AGENT:${agent_time}ms FILEOPS:${file_ops_time}ms" >> "$LOG_FILE"
}

# Analyze performance trends
analyze_performance_trends() {
    echo ""
    echo "📈 性能分析:"

    # Compare with baseline
    for metric in "cleanup_avg" "agent_avg" "file_ops_avg"; do
        local current=${CURRENT_METRICS[$metric]}
        local baseline=${BASELINE_METRICS[$metric]:-0}

        if [[ $baseline -gt 0 ]]; then
            local change=$(( (current - baseline) * 100 / baseline ))
            local status=""

            if [[ $change -lt -10 ]]; then
                status="${GREEN}↑ 提升 ${change#-}%${NC}"
            elif [[ $change -gt 10 ]]; then
                status="${RED}↓ 下降 ${change}%${NC}"
            else
                status="${YELLOW}→ 稳定 (${change}%)${NC}"
            fi

            case "$metric" in
                "cleanup_avg") echo "  清理脚本: ${current}ms (基准: ${baseline}ms) $status" ;;
                "agent_avg") echo "  Agent选择: ${current}ms (基准: ${baseline}ms) $status" ;;
                "file_ops_avg") echo "  文件操作: ${current}ms (基准: ${baseline}ms) $status" ;;
            esac
        else
            case "$metric" in
                "cleanup_avg") echo "  清理脚本: ${current}ms (无基准)" ;;
                "agent_avg") echo "  Agent选择: ${current}ms (无基准)" ;;
                "file_ops_avg") echo "  文件操作: ${current}ms (无基准)" ;;
            esac
        fi
    done
}

# Check for performance alerts
check_performance_alerts() {
    local alerts=()

    # Check if any metric exceeds threshold
    for metric in "cleanup_avg" "agent_avg" "file_ops_avg"; do
        local current=${CURRENT_METRICS[$metric]}
        if [[ $current -gt $ALERT_THRESHOLD_MS ]]; then
            alerts+=("$metric:${current}ms")
        fi
    done

    if [[ ${#alerts[@]} -gt 0 ]]; then
        echo ""
        echo -e "${RED}🚨 性能警告${NC}"
        for alert in "${alerts[@]}"; do
            IFS=':' read -r metric_name time <<< "$alert"
            case "$metric_name" in
                "cleanup_avg") echo "  ⚠️ 清理脚本执行时间过长: $time (阈值: ${ALERT_THRESHOLD_MS}ms)" ;;
                "agent_avg") echo "  ⚠️ Agent选择时间过长: $time (阈值: ${ALERT_THRESHOLD_MS}ms)" ;;
                "file_ops_avg") echo "  ⚠️ 文件操作时间过长: $time (阈值: ${ALERT_THRESHOLD_MS}ms)" ;;
            esac
        done

        # Provide optimization suggestions
        suggest_optimizations "${alerts[@]}"
    else
        echo ""
        echo -e "${GREEN}✅ 所有性能指标正常${NC}"
    fi
}

# Suggest optimizations
suggest_optimizations() {
    local alerts=("$@")

    echo ""
    echo -e "${YELLOW}💡 优化建议${NC}"

    for alert in "${alerts[@]}"; do
        IFS=':' read -r metric_name time <<< "$alert"
        case "$metric_name" in
            "cleanup_avg")
                echo "  🧹 清理脚本优化:"
                echo "    • 使用Ultra优化版本"
                echo "    • 增加并行度: PARALLEL_JOBS=$(nproc)"
                echo "    • 启用缓存: CACHE_DIR=/tmp/perfect21_cache"
                ;;
            "agent_avg")
                echo "  🤖 Agent选择优化:"
                echo "    • 启用缓存: CACHE_TTL=600"
                echo "    • 使用Ultra版本"
                echo "    • 启用预测: ENABLE_PREDICTION=true"
                ;;
            "file_ops_avg")
                echo "  📁 文件操作优化:"
                echo "    • 使用SSD存储"
                echo "    • 优化文件系统 (ext4, btrfs)"
                echo "    • 增加系统缓存"
                ;;
        esac
    done
}

# Performance report generation
generate_performance_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local report_file="$MONITOR_DIR/performance_report_$(date +%Y%m%d_%H%M).md"

    cat > "$report_file" << EOF
# Claude Enhancer 性能监控报告

**生成时间**: $timestamp
**监控周期**: 实时监控
**性能阈值**: ${ALERT_THRESHOLD_MS}ms

## 📊 当前性能指标

### 清理脚本性能
- **执行时间**: ${CURRENT_METRICS["cleanup_avg"]}ms
- **基准对比**: vs ${BASELINE_METRICS["cleanup_avg"]:-"N/A"}ms
- **状态**: $(get_performance_status "cleanup_avg")

### Agent选择性能
- **执行时间**: ${CURRENT_METRICS["agent_avg"]}ms
- **基准对比**: vs ${BASELINE_METRICS["agent_avg"]:-"N/A"}ms
- **状态**: $(get_performance_status "agent_avg")

### 文件操作性能
- **执行时间**: ${CURRENT_METRICS["file_ops_avg"]}ms
- **基准对比**: vs ${BASELINE_METRICS["file_ops_avg"]:-"N/A"}ms
- **状态**: $(get_performance_status "file_ops_avg")

## 📈 性能趋势分析

$(analyze_performance_history)

## 🎯 优化建议

$(get_optimization_recommendations)

## 📋 监控配置

- **监控目录**: $MONITOR_DIR
- **日志文件**: $LOG_FILE
- **指标文件**: $METRICS_FILE
- **警告阈值**: ${ALERT_THRESHOLD_MS}ms

## 🔧 下一步行动

1. 定期检查性能指标
2. 根据建议进行优化
3. 更新性能基准线
4. 监控优化效果

---
*性能监控报告 - Claude Enhancer Performance Team*
EOF

    echo "  📄 性能报告: $report_file"
}

# Get performance status
get_performance_status() {
    local metric="$1"
    local current=${CURRENT_METRICS[$metric]}
    local baseline=${BASELINE_METRICS[$metric]:-0}

    if [[ $baseline -gt 0 ]]; then
        local change=$(( (current - baseline) * 100 / baseline ))
        if [[ $change -lt -10 ]]; then
            echo "优秀 (提升 ${change#-}%)"
        elif [[ $change -gt 10 ]]; then
            echo "需要关注 (下降 ${change}%)"
        else
            echo "正常 (变化 ${change}%)"
        fi
    else
        echo "新建立基准"
    fi
}

# Get optimization recommendations
get_optimization_recommendations() {
    local recommendations=""

    # Check each metric and provide specific recommendations
    for metric in "cleanup_avg" "agent_avg" "file_ops_avg"; do
        local current=${CURRENT_METRICS[$metric]}
        if [[ $current -gt $ALERT_THRESHOLD_MS ]]; then
            case "$metric" in
                "cleanup_avg")
                    recommendations="$recommendations\n### 清理脚本优化\n- 使用Ultra优化版本\n- 启用并行处理\n- 配置智能缓存\n"
                    ;;
                "agent_avg")
                    recommendations="$recommendations\n### Agent选择优化\n- 启用预测缓存\n- 使用Ultra版本\n- 优化正则表达式\n"
                    ;;
                "file_ops_avg")
                    recommendations="$recommendations\n### 文件操作优化\n- 升级存储设备\n- 优化文件系统\n- 增加系统内存\n"
                    ;;
            esac
        fi
    done

    if [[ -z "$recommendations" ]]; then
        echo "所有性能指标表现良好，无需特殊优化。"
    else
        echo -e "$recommendations"
    fi
}

# Analyze performance history
analyze_performance_history() {
    if [[ -f "$LOG_FILE" && -s "$LOG_FILE" ]]; then
        local lines=$(wc -l < "$LOG_FILE")
        echo "- **历史记录**: $lines 个数据点"
        echo "- **监控期间**: $(head -1 "$LOG_FILE" | cut -d' ' -f1-2) 至 $(tail -1 "$LOG_FILE" | cut -d' ' -f1-2)"

        # Simple trend analysis
        local latest_cleanup=$(tail -1 "$LOG_FILE" | grep -oP 'CLEANUP:\K\d+')
        local earliest_cleanup=$(head -1 "$LOG_FILE" | grep -oP 'CLEANUP:\K\d+')

        if [[ -n "$latest_cleanup" && -n "$earliest_cleanup" && $earliest_cleanup -gt 0 ]]; then
            local trend=$(( (latest_cleanup - earliest_cleanup) * 100 / earliest_cleanup ))
            if [[ $trend -lt 0 ]]; then
                echo "- **清理脚本趋势**: 性能提升 ${trend#-}%"
            elif [[ $trend -gt 0 ]]; then
                echo "- **清理脚本趋势**: 性能下降 ${trend}%"
            else
                echo "- **清理脚本趋势**: 稳定"
            fi
        fi
    else
        echo "- **历史记录**: 无数据"
    fi
}

# Real-time monitoring mode
real_time_monitor() {
    echo -e "${CYAN}🔄 启动实时性能监控${NC}"
    echo "按 Ctrl+C 停止监控"
    echo ""

    while true; do
        clear
        echo -e "${BLUE}📊 Claude Enhancer 实时性能监控${NC}"
        echo "========================================"
        echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""

        monitor_current_performance

        echo ""
        echo "========================================"
        echo "下次更新: 30秒后 (Ctrl+C 停止)"

        sleep 30
    done
}

# Main function
main() {
    echo -e "${BLUE}🚀 Claude Enhancer 性能监控系统${NC}"
    echo "========================================"
    echo ""

    # Initialize monitoring
    init_monitor

    # Check mode
    if [[ "$ENABLE_REAL_TIME" == "true" ]]; then
        real_time_monitor
    else
        # Single run monitoring
        monitor_current_performance
        echo ""
        generate_performance_report
    fi

    echo ""
    echo "========================================"
    echo -e "${GREEN}✅ 性能监控完成${NC}"
    echo -e "${GREEN}📊 监控数据: $MONITOR_DIR${NC}"
}

# Signal handling for real-time mode
trap 'echo -e "\n${YELLOW}🛑 实时监控已停止${NC}"; exit 0' INT

# Execute main function
main "$@"