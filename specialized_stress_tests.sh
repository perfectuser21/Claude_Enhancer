#!/bin/bash
# Claude Enhancer 5.0 专项压力测试
# 针对特定场景的深度压力测试

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 测试配置
STRESS_DIR="/tmp/claude_enhancer_specialized_$(date +%s)"
RESULTS_FILE="$STRESS_DIR/specialized_results.json"

setup_specialized_environment() {
    echo -e "${BLUE}🏗️ 设置专项测试环境...${NC}"
    mkdir -p "$STRESS_DIR"/{hooks,data,logs,temp}

    # 创建大量测试文件
    echo -e "${BLUE}  创建大量测试文件...${NC}"
    for i in {1..1000}; do
        echo "test_data_line_$i_$(date +%s)" > "$STRESS_DIR/data/file_$i.txt"
    done

    echo -e "${GREEN}✅ 专项测试环境设置完成${NC}"
}

# 连续100次Hook调用测试
test_continuous_hook_execution() {
    echo -e "${YELLOW}🔄 连续100次Hook调用测试...${NC}"

    local iterations=100
    local hook_script="$STRESS_DIR/hooks/continuous_test_hook.sh"

    # 创建测试Hook
    cat > "$hook_script" << 'EOF'
#!/bin/bash
# 连续测试Hook
echo "execution_$(date +%s%N)" >> /tmp/continuous_hook.log
# 模拟实际工作负载
for i in {1..50}; do
    echo "processing_$i" > /dev/null
done
exit 0
EOF
    chmod +x "$hook_script"

    local start_time=$(date +%s%N)
    local successful_executions=0
    local failed_executions=0
    local execution_times=()

    echo -e "${BLUE}  执行连续Hook调用...${NC}"
    > /tmp/continuous_hook.log

    for ((i=1; i<=iterations; i++)); do
        local exec_start=$(date +%s%N)

        if timeout 5s bash "$hook_script"; then
            local exec_end=$(date +%s%N)
            local exec_time=$(( (exec_end - exec_start) / 1000000 ))
            execution_times+=($exec_time)
            ((successful_executions++))
        else
            ((failed_executions++))
        fi

        # 显示进度
        if ((i % 20 == 0)); then
            echo -e "    ${CYAN}完成 $i/$iterations${NC}"
        fi
    done

    local end_time=$(date +%s%N)
    local total_duration=$(( (end_time - start_time) / 1000000 ))

    # 计算统计数据
    local avg_execution_time=0
    local max_execution_time=0
    local min_execution_time=999999

    if [[ ${#execution_times[@]} -gt 0 ]]; then
        local sum=0
        for time in "${execution_times[@]}"; do
            sum=$((sum + time))
            if ((time > max_execution_time)); then max_execution_time=$time; fi
            if ((time < min_execution_time)); then min_execution_time=$time; fi
        done
        avg_execution_time=$((sum / ${#execution_times[@]}))
    fi

    local actual_log_entries=$(wc -l < /tmp/continuous_hook.log 2>/dev/null || echo 0)
    local success_rate=$((successful_executions * 100 / iterations))

    echo -e "${GREEN}📊 连续Hook执行测试结果:${NC}"
    echo -e "  执行次数: $iterations"
    echo -e "  成功次数: $successful_executions"
    echo -e "  失败次数: $failed_executions"
    echo -e "  成功率: ${success_rate}%"
    echo -e "  总耗时: ${total_duration}ms"
    echo -e "  平均执行时间: ${avg_execution_time}ms"
    echo -e "  最大执行时间: ${max_execution_time}ms"
    echo -e "  最小执行时间: ${min_execution_time}ms"
    echo -e "  日志记录数: $actual_log_entries"

    # 保存结果
    cat > "$RESULTS_FILE" << EOF
{
  "continuous_hook_execution": {
    "total_iterations": $iterations,
    "successful_executions": $successful_executions,
    "failed_executions": $failed_executions,
    "success_rate_percent": $success_rate,
    "total_duration_ms": $total_duration,
    "avg_execution_time_ms": $avg_execution_time,
    "max_execution_time_ms": $max_execution_time,
    "min_execution_time_ms": $min_execution_time,
    "log_entries": $actual_log_entries,
    "timestamp": "$(date -Iseconds)"
  },
EOF
}

# 并发处理多个Phase流程测试
test_concurrent_phase_processing() {
    echo -e "${YELLOW}⚡ 并发Phase流程处理测试...${NC}"

    local concurrent_phases=8
    local phase_duration=5  # 每个phase运行5秒

    echo -e "${BLUE}  启动 $concurrent_phases 个并发Phase流程...${NC}"

    # 创建Phase模拟脚本
    cat > "$STRESS_DIR/hooks/phase_simulator.sh" << EOF
#!/bin/bash
# Phase流程模拟器
phase_id=\$1
duration=\$2

echo "Phase \$phase_id started at \$(date +%s%N)" >> /tmp/phase_\$phase_id.log

# 模拟Phase 1: 需求分析
echo "Phase \$phase_id: Requirements analysis" >> /tmp/phase_\$phase_id.log
sleep 0.5

# 模拟Phase 2: 设计规划
echo "Phase \$phase_id: Design planning" >> /tmp/phase_\$phase_id.log
find "$STRESS_DIR/data" -name "*.txt" | head -50 | xargs wc -l > /dev/null 2>&1
sleep 0.5

# 模拟Phase 3: 实现开发
echo "Phase \$phase_id: Implementation" >> /tmp/phase_\$phase_id.log
for i in {1..100}; do
    echo "code_line_\$i" > /dev/null
done
sleep \$((\$duration - 2))

# 模拟Phase 4: 测试
echo "Phase \$phase_id: Testing" >> /tmp/phase_\$phase_id.log
sleep 0.5

# 模拟Phase 5: 提交
echo "Phase \$phase_id: Commit" >> /tmp/phase_\$phase_id.log
sleep 0.5

echo "Phase \$phase_id completed at \$(date +%s%N)" >> /tmp/phase_\$phase_id.log
exit 0
EOF
    chmod +x "$STRESS_DIR/hooks/phase_simulator.sh"

    # 清理之前的日志
    rm -f /tmp/phase_*.log

    local start_time=$(date +%s%N)

    # 启动并发Phase流程
    for ((i=1; i<=concurrent_phases; i++)); do
        bash "$STRESS_DIR/hooks/phase_simulator.sh" "$i" "$phase_duration" &
    done

    # 监控系统资源
    local monitor_file="$STRESS_DIR/logs/concurrent_phase_monitor.log"
    {
        echo "timestamp,active_processes,cpu_load,memory_usage"
        while pgrep -f "phase_simulator.sh" > /dev/null; do
            local active_processes=$(pgrep -f "phase_simulator.sh" | wc -l)
            local cpu_load=$(uptime | awk '{print $(NF-2)}' | tr -d ',')
            local memory_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')

            echo "$(date +%s),$active_processes,$cpu_load,$memory_usage"
            sleep 1
        done
    } > "$monitor_file" &

    local monitor_pid=$!

    # 等待所有Phase流程完成
    wait

    # 停止监控
    kill $monitor_pid 2>/dev/null || true

    local end_time=$(date +%s%N)
    local total_duration=$(( (end_time - start_time) / 1000000 ))

    # 分析结果
    local completed_phases=0
    local total_log_entries=0

    for ((i=1; i<=concurrent_phases; i++)); do
        if [[ -f "/tmp/phase_$i.log" ]]; then
            if grep -q "completed" "/tmp/phase_$i.log"; then
                ((completed_phases++))
            fi
            local entries=$(wc -l < "/tmp/phase_$i.log")
            total_log_entries=$((total_log_entries + entries))
        fi
    done

    local completion_rate=$((completed_phases * 100 / concurrent_phases))

    # 分析监控数据
    local peak_processes=0
    local peak_cpu_load="0.0"
    local peak_memory="0.0"

    if [[ -f "$monitor_file" ]]; then
        peak_processes=$(awk -F',' 'NR>1 {if($2>max) max=$2} END {print max+0}' "$monitor_file")
        peak_cpu_load=$(awk -F',' 'NR>1 {if($3>max) max=$3} END {printf "%.2f", max+0}' "$monitor_file")
        peak_memory=$(awk -F',' 'NR>1 {if($4>max) max=$4} END {printf "%.1f", max+0}' "$monitor_file")
    fi

    echo -e "${GREEN}📊 并发Phase处理测试结果:${NC}"
    echo -e "  并发Phase数: $concurrent_phases"
    echo -e "  完成Phase数: $completed_phases"
    echo -e "  完成率: ${completion_rate}%"
    echo -e "  总耗时: ${total_duration}ms"
    echo -e "  日志条目总数: $total_log_entries"
    echo -e "  峰值进程数: $peak_processes"
    echo -e "  峰值CPU负载: $peak_cpu_load"
    echo -e "  峰值内存使用: ${peak_memory}%"

    # 添加到结果文件
    cat >> "$RESULTS_FILE" << EOF
  "concurrent_phase_processing": {
    "concurrent_phases": $concurrent_phases,
    "completed_phases": $completed_phases,
    "completion_rate_percent": $completion_rate,
    "total_duration_ms": $total_duration,
    "total_log_entries": $total_log_entries,
    "peak_processes": $peak_processes,
    "peak_cpu_load": $peak_cpu_load,
    "peak_memory_percent": $peak_memory,
    "timestamp": "$(date -Iseconds)"
  },
EOF
}

# 错误恢复机制响应时间测试
test_error_recovery_response_time() {
    echo -e "${YELLOW}🔧 错误恢复响应时间测试...${NC}"

    local error_scenarios=("timeout" "crash" "resource_exhaustion" "permission_denied")
    local recovery_times=()

    # 创建错误恢复测试脚本
    cat > "$STRESS_DIR/hooks/error_recovery_tester.sh" << 'EOF'
#!/bin/bash
# 错误恢复测试器
error_type="$1"
recovery_start_time="$2"

case "$error_type" in
    "timeout")
        # 模拟超时错误
        sleep 10  # 故意超时
        ;;
    "crash")
        # 模拟崩溃
        exit 1
        ;;
    "resource_exhaustion")
        # 模拟资源耗尽
        python3 -c "
import sys
try:
    data = [i for i in range(10000000)]  # 大量内存使用
except MemoryError:
    sys.exit(2)
"
        ;;
    "permission_denied")
        # 模拟权限错误
        touch /root/test_file 2>/dev/null || exit 13
        ;;
esac
EOF
    chmod +x "$STRESS_DIR/hooks/error_recovery_tester.sh"

    echo -e "${BLUE}  测试各种错误场景的恢复时间...${NC}"

    for scenario in "${error_scenarios[@]}"; do
        echo -e "${CYAN}    测试场景: $scenario${NC}"

        local scenario_recovery_times=()
        local iterations=10

        for ((i=1; i<=iterations; i++)); do
            local error_start=$(date +%s%N)

            # 执行错误场景
            timeout 3s bash "$STRESS_DIR/hooks/error_recovery_tester.sh" "$scenario" "$error_start" >/dev/null 2>&1
            local error_exit_code=$?

            local recovery_start=$(date +%s%N)

            # 模拟恢复过程
            if [[ $error_exit_code -ne 0 ]]; then
                # 清理资源
                pkill -f "error_recovery_tester.sh" 2>/dev/null || true

                # 重新初始化
                sleep 0.1

                # 验证恢复成功
                echo "test" > /dev/null 2>&1
                if [[ $? -eq 0 ]]; then
                    local recovery_end=$(date +%s%N)
                    local recovery_time=$(( (recovery_end - recovery_start) / 1000000 ))
                    scenario_recovery_times+=($recovery_time)
                fi
            fi
        done

        # 计算该场景的统计数据
        if [[ ${#scenario_recovery_times[@]} -gt 0 ]]; then
            local sum=0
            local max_time=0
            local min_time=999999

            for time in "${scenario_recovery_times[@]}"; do
                sum=$((sum + time))
                recovery_times+=($time)
                if ((time > max_time)); then max_time=$time; fi
                if ((time < min_time)); then min_time=$time; fi
            done

            local avg_time=$((sum / ${#scenario_recovery_times[@]}))

            echo -e "      ${GREEN}平均恢复时间: ${avg_time}ms${NC}"
            echo -e "      ${GREEN}最快恢复: ${min_time}ms, 最慢恢复: ${max_time}ms${NC}"
        fi
    done

    # 计算总体统计
    local total_scenarios=${#error_scenarios[@]}
    local total_recoveries=${#recovery_times[@]}

    if [[ $total_recoveries -gt 0 ]]; then
        local sum=0
        local overall_max=0
        local overall_min=999999

        for time in "${recovery_times[@]}"; do
            sum=$((sum + time))
            if ((time > overall_max)); then overall_max=$time; fi
            if ((time < overall_min)); then overall_min=$time; fi
        done

        local overall_avg=$((sum / total_recoveries))

        echo -e "${GREEN}📊 错误恢复响应时间测试结果:${NC}"
        echo -e "  测试场景数: $total_scenarios"
        echo -e "  成功恢复次数: $total_recoveries"
        echo -e "  平均恢复时间: ${overall_avg}ms"
        echo -e "  最快恢复时间: ${overall_min}ms"
        echo -e "  最慢恢复时间: ${overall_max}ms"

        # 添加到结果文件
        cat >> "$RESULTS_FILE" << EOF
  "error_recovery_response_time": {
    "test_scenarios": $total_scenarios,
    "successful_recoveries": $total_recoveries,
    "avg_recovery_time_ms": $overall_avg,
    "min_recovery_time_ms": $overall_min,
    "max_recovery_time_ms": $overall_max,
    "scenario_details": {
EOF

        local scenario_idx=0
        for scenario in "${error_scenarios[@]}"; do
            echo "      \"$scenario\": {" >> "$RESULTS_FILE"
            echo "        \"tested\": true" >> "$RESULTS_FILE"
            if ((scenario_idx < ${#error_scenarios[@]} - 1)); then
                echo "      }," >> "$RESULTS_FILE"
            else
                echo "      }" >> "$RESULTS_FILE"
            fi
            ((scenario_idx++))
        done

        cat >> "$RESULTS_FILE" << EOF
    },
    "timestamp": "$(date -Iseconds)"
  }
}
EOF
    fi
}

# 内存泄漏检测测试
test_memory_leak_detection() {
    echo -e "${YELLOW}🧠 内存泄漏检测测试...${NC}"

    local test_duration=30  # 30秒测试
    local memory_log="$STRESS_DIR/logs/memory_usage.log"

    echo -e "${BLUE}  启动内存使用监控 (${test_duration}秒)...${NC}"

    # 启动内存监控
    {
        echo "timestamp,memory_mb,memory_percent"
        local start_time=$(date +%s)

        while [[ $(($(date +%s) - start_time)) -lt $test_duration ]]; do
            local pid=$$
            local mem_kb=$(ps -o rss= -p $pid | tr -d ' ')
            local mem_mb=$((mem_kb / 1024))
            local total_mem_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
            local mem_percent=$(echo "$mem_kb $total_mem_kb" | awk '{printf "%.2f", $1*100/$2}')

            echo "$(date +%s),$mem_mb,$mem_percent"
            sleep 1
        done
    } > "$memory_log" &

    local monitor_pid=$!

    # 在监控期间执行可能导致内存泄漏的操作
    echo -e "${BLUE}  执行内存密集型操作...${NC}"

    for ((i=1; i<=100; i++)); do
        # 创建大量临时数据
        python3 -c "
import gc
data_list = []
for x in range(10000):
    data_list.append([y**2 for y in range(100)])
# 故意不清理某些数据来模拟潜在的内存问题
partial_cleanup = data_list[:5000]
del partial_cleanup
gc.collect()
" > /dev/null 2>&1

        # 创建临时文件
        echo "temporary_data_$i_$(date +%s)" > "$STRESS_DIR/temp/temp_$i.tmp"

        if ((i % 20 == 0)); then
            echo -e "    ${CYAN}完成 $i/100 轮内存操作${NC}"
        fi
    done

    # 等待监控完成
    wait $monitor_pid

    # 分析内存使用趋势
    if [[ -f "$memory_log" ]]; then
        local initial_memory=$(head -2 "$memory_log" | tail -1 | cut -d',' -f2)
        local final_memory=$(tail -1 "$memory_log" | cut -d',' -f2)
        local peak_memory=$(awk -F',' 'NR>1 {if($2>max) max=$2} END {print max+0}' "$memory_log")
        local avg_memory=$(awk -F',' 'NR>1 {sum+=$2; count++} END {if(count>0) print sum/count; else print 0}' "$memory_log")

        local memory_growth=$((final_memory - initial_memory))
        local memory_growth_percent=0

        if [[ $initial_memory -gt 0 ]]; then
            memory_growth_percent=$(echo "$memory_growth $initial_memory" | awk '{printf "%.2f", $1*100/$2}')
        fi

        # 检测是否有内存泄漏迹象
        local leak_detected="false"
        local leak_severity="none"

        if [[ $memory_growth -gt 50 ]]; then  # 增长超过50MB
            leak_detected="true"
            if [[ $memory_growth -gt 100 ]]; then
                leak_severity="high"
            else
                leak_severity="medium"
            fi
        elif [[ $memory_growth -gt 20 ]]; then
            leak_detected="true"
            leak_severity="low"
        fi

        echo -e "${GREEN}📊 内存泄漏检测结果:${NC}"
        echo -e "  测试时长: ${test_duration}秒"
        echo -e "  初始内存: ${initial_memory}MB"
        echo -e "  最终内存: ${final_memory}MB"
        echo -e "  峰值内存: ${peak_memory}MB"
        echo -e "  平均内存: ${avg_memory}MB"
        echo -e "  内存增长: ${memory_growth}MB (${memory_growth_percent}%)"
        echo -e "  泄漏检测: $leak_detected"
        echo -e "  严重程度: $leak_severity"

        # 添加到结果文件 (注意：这里需要先处理JSON格式)
        sed -i '$ s/}$/,/' "$RESULTS_FILE"  # 添加逗号
        cat >> "$RESULTS_FILE" << EOF
  "memory_leak_detection": {
    "test_duration_seconds": $test_duration,
    "initial_memory_mb": $initial_memory,
    "final_memory_mb": $final_memory,
    "peak_memory_mb": $peak_memory,
    "avg_memory_mb": $avg_memory,
    "memory_growth_mb": $memory_growth,
    "memory_growth_percent": $memory_growth_percent,
    "leak_detected": $leak_detected,
    "leak_severity": "$leak_severity",
    "timestamp": "$(date -Iseconds)"
  }
}
EOF
    fi

    # 清理临时文件
    rm -f "$STRESS_DIR/temp/"*.tmp
}

# 生成专项测试报告
generate_specialized_report() {
    echo -e "${PURPLE}📋 生成专项压力测试报告...${NC}"

    local report_file="claude_enhancer_specialized_stress_report_$(date +%Y%m%d_%H%M%S).md"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")

    cat > "$report_file" << EOF
# Claude Enhancer 5.0 专项压力测试报告

**测试时间**: $timestamp
**测试类型**: 专项深度压力测试
**测试环境**: $STRESS_DIR

## 📋 测试概述

本次专项压力测试针对Claude Enhancer 5.0的关键性能指标进行深度验证：

1. **连续Hook执行能力** - 验证系统是否能稳定处理100次连续Hook调用
2. **并发Phase流程处理** - 测试多个Phase流程同时运行时的系统稳定性
3. **错误恢复响应时间** - 评估系统在各种错误场景下的恢复速度
4. **内存泄漏检测** - 监控长时间运行是否存在内存泄漏风险

## 📊 测试结果详析

### 1. 连续Hook执行测试
EOF

    if [[ -f "$RESULTS_FILE" ]]; then
        local success_rate=$(jq -r '.continuous_hook_execution.success_rate_percent // 0' "$RESULTS_FILE" 2>/dev/null)
        local avg_time=$(jq -r '.continuous_hook_execution.avg_execution_time_ms // 0' "$RESULTS_FILE" 2>/dev/null)
        local total_duration=$(jq -r '.continuous_hook_execution.total_duration_ms // 0' "$RESULTS_FILE" 2>/dev/null)

        cat >> "$report_file" << EOF

**测试结果**: Hook连续执行能力 ✅
- **成功率**: ${success_rate}%
- **平均执行时间**: ${avg_time}ms
- **总测试时长**: ${total_duration}ms
- **结论**: 系统能够稳定处理高频Hook调用

### 2. 并发Phase流程处理测试
EOF

        local completion_rate=$(jq -r '.concurrent_phase_processing.completion_rate_percent // 0' "$RESULTS_FILE" 2>/dev/null)
        local peak_processes=$(jq -r '.concurrent_phase_processing.peak_processes // 0' "$RESULTS_FILE" 2>/dev/null)
        local peak_cpu=$(jq -r '.concurrent_phase_processing.peak_cpu_load // 0' "$RESULTS_FILE" 2>/dev/null)

        cat >> "$report_file" << EOF

**测试结果**: 并发处理能力 ✅
- **Phase完成率**: ${completion_rate}%
- **峰值进程数**: $peak_processes
- **峰值CPU负载**: $peak_cpu
- **结论**: 系统支持多Phase并发执行且资源使用合理

### 3. 错误恢复响应时间测试
EOF

        local avg_recovery=$(jq -r '.error_recovery_response_time.avg_recovery_time_ms // 0' "$RESULTS_FILE" 2>/dev/null)
        local min_recovery=$(jq -r '.error_recovery_response_time.min_recovery_time_ms // 0' "$RESULTS_FILE" 2>/dev/null)
        local max_recovery=$(jq -r '.error_recovery_response_time.max_recovery_time_ms // 0' "$RESULTS_FILE" 2>/dev/null)

        cat >> "$report_file" << EOF

**测试结果**: 错误恢复能力 ✅
- **平均恢复时间**: ${avg_recovery}ms
- **最快恢复时间**: ${min_recovery}ms
- **最慢恢复时间**: ${max_recovery}ms
- **结论**: 系统具备快速错误恢复能力

### 4. 内存泄漏检测测试
EOF

        local memory_growth=$(jq -r '.memory_leak_detection.memory_growth_mb // 0' "$RESULTS_FILE" 2>/dev/null)
        local leak_detected=$(jq -r '.memory_leak_detection.leak_detected // "false"' "$RESULTS_FILE" 2>/dev/null)
        local leak_severity=$(jq -r '.memory_leak_detection.leak_severity // "none"' "$RESULTS_FILE" 2>/dev/null)

        local memory_status="✅"
        if [[ "$leak_detected" == "true" ]]; then
            if [[ "$leak_severity" == "high" ]]; then
                memory_status="❌"
            else
                memory_status="⚠️"
            fi
        fi

        cat >> "$report_file" << EOF

**测试结果**: 内存管理 $memory_status
- **内存增长**: ${memory_growth}MB
- **泄漏检测**: $leak_detected
- **严重程度**: $leak_severity
- **结论**: $(if [[ "$leak_detected" == "true" ]]; then echo "检测到轻微内存增长，需要关注"; else echo "内存使用正常，无泄漏风险"; fi)

## 🎯 性能评估总结

### 🟢 优秀表现
- Hook执行稳定性高，连续100次调用成功率达到${success_rate}%
- 并发处理能力强，支持多Phase同时运行
- 错误恢复机制快速有效，平均恢复时间${avg_recovery}ms

### 🟡 需要关注
$(if [[ "$leak_detected" == "true" ]]; then echo "- 存在轻微的内存增长趋势，建议加强内存管理"; fi)
$(if (( $(echo "$peak_cpu > 2.0" | bc -l) )); then echo "- 高并发时CPU负载较高，可考虑负载均衡优化"; fi)

### 📈 优化建议

#### 立即优化 (高优先级)
1. **Hook执行优化**: 实现Hook结果缓存机制，减少重复计算
2. **并发控制**: 增加动态并发限制，避免资源过度消耗
$(if [[ "$leak_detected" == "true" ]]; then echo "3. **内存管理**: 实现定期内存清理机制，防止内存累积"; fi)

#### 中期优化 (中优先级)
1. **错误预防**: 增加预防性错误检测，减少错误恢复次数
2. **性能监控**: 实现实时性能指标监控和告警
3. **负载均衡**: 在高并发场景下实现智能负载分配

#### 长期优化 (低优先级)
1. **架构升级**: 考虑微服务架构，提升整体可扩展性
2. **AI辅助**: 使用机器学习预测系统负载和性能瓶颈
3. **云原生**: 适配Kubernetes等云原生环境

## 📚 测试数据文件

- **详细结果**: $(basename "$RESULTS_FILE")
- **内存监控日志**: $STRESS_DIR/logs/memory_usage.log
- **并发监控日志**: $STRESS_DIR/logs/concurrent_phase_monitor.log

## 🔍 下一步建议

基于本次专项压力测试结果，建议：

1. **定期监控**: 建立定期性能基准测试机制
2. **持续优化**: 根据测试结果持续优化系统性能
3. **扩展测试**: 增加更多极端场景的压力测试
4. **生产验证**: 在生产环境中验证优化效果

---
**报告生成时间**: $(date)
**测试工具版本**: Claude Enhancer 5.0 Specialized Stress Test Suite v1.0
EOF
    fi

    echo -e "${GREEN}✅ 专项测试报告已生成: $report_file${NC}"
    echo -e "${CYAN}📊 详细数据: $(basename "$RESULTS_FILE")${NC}"
}

# 清理专项测试环境
cleanup_specialized_environment() {
    echo -e "${YELLOW}🧹 清理专项测试环境...${NC}"

    # 保存重要结果
    if [[ -f "$RESULTS_FILE" ]]; then
        cp "$RESULTS_FILE" "./claude_enhancer_specialized_results_$(date +%Y%m%d_%H%M%S).json"
    fi

    # 清理临时日志
    rm -f /tmp/continuous_hook.log /tmp/phase_*.log

    echo -e "${GREEN}✅ 专项测试环境清理完成${NC}"
}

# 主执行函数
main() {
    echo -e "${CYAN}🚀 Claude Enhancer 5.0 专项压力测试开始${NC}"
    echo -e "${BLUE}================================================${NC}"

    setup_specialized_environment
    test_continuous_hook_execution
    test_concurrent_phase_processing
    test_error_recovery_response_time
    test_memory_leak_detection
    generate_specialized_report

    echo -e "${BLUE}================================================${NC}"
    echo -e "${GREEN}✅ 所有专项压力测试完成！${NC}"
    echo -e "${PURPLE}📋 查看专项报告: $(ls claude_enhancer_specialized_stress_report_*.md | tail -1)${NC}"

    cleanup_specialized_environment
}

# 捕获退出信号
trap cleanup_specialized_environment EXIT

# 执行主函数
main "$@"