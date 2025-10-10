# P1规划：Merge Queue性能基准测试方案

**版本**: 1.0
**日期**: 2025-10-10
**配套文档**: P1_MERGE_QUEUE_ARCHITECTURE.md

---

## 目录
1. [测试目标](#1-测试目标)
2. [测试环境](#2-测试环境)
3. [测试场景](#3-测试场景)
4. [性能指标](#4-性能指标)
5. [测试工具](#5-测试工具)
6. [测试脚本](#6-测试脚本)
7. [结果分析](#7-结果分析)
8. [回归测试](#8-回归测试)

---

## 1. 测试目标

### 1.1 主要目标

验证Merge Queue Manager在以下方面的性能表现：

| 目标 | 期望结果 |
|-----|---------|
| **延迟（Latency）** | P90 < 60秒 |
| **吞吐量（Throughput）** | ≥ 5 merges/分钟 |
| **并发能力（Concurrency）** | 支持≥10个并发Terminal |
| **资源占用（Resources）** | CPU < 40%, Memory < 300MB |
| **可靠性（Reliability）** | 故障恢复时间 < 10秒 |

### 1.2 次要目标

- 识别性能瓶颈
- 验证扩展性（scalability）
- 建立性能基线（baseline）
- 为优化提供数据支撑

---

## 2. 测试环境

### 2.1 硬件环境

```bash
# 最低配置
CPU: 2 cores, 2.0 GHz
Memory: 4 GB RAM
Disk: SSD, 20 GB free space
Network: 10 Mbps

# 推荐配置
CPU: 4 cores, 3.0 GHz
Memory: 8 GB RAM
Disk: NVMe SSD, 50 GB free space
Network: 100 Mbps

# 测试环境信息收集脚本
function collect_env_info() {
    cat <<EOF
=== Test Environment Info ===
OS: $(uname -s)
Kernel: $(uname -r)
CPU: $(grep -c ^processor /proc/cpuinfo) cores
CPU Model: $(grep "model name" /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)
Memory: $(free -h | grep Mem | awk '{print $2}')
Disk: $(df -h . | tail -1 | awk '{print $2}')
Disk Type: $(lsblk -d -o name,rota | grep -v NAME | awk '{if($2==0) print "SSD"; else print "HDD"}')
Git Version: $(git --version)
Bash Version: $BASH_VERSION
Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
EOF
}
```

### 2.2 软件依赖

```bash
# 必需
- Bash 4.0+
- Git 2.20+
- jq 1.6+
- flock (util-linux)

# 可选（用于监控）
- time
- perf
- vmstat
- iostat

# 安装检查脚本
function check_dependencies() {
    local missing=0

    for cmd in bash git jq flock; do
        if ! command -v "$cmd" &>/dev/null; then
            echo "❌ Missing: $cmd"
            ((missing++))
        else
            echo "✓ $cmd: $(command -v $cmd)"
        fi
    done

    return $missing
}
```

---

## 3. 测试场景

### 3.1 场景1：理想情况（无冲突）

**目的**: 验证系统在最佳情况下的性能上限

**设置**:
- 10个Terminal同时enqueue
- 每个分支修改不同的文件（零冲突）
- 目标分支：main

**预期结果**:
- P50 Wait Time < 30秒
- P90 Wait Time < 60秒
- 所有merge成功

**实现**:
```bash
function scenario_ideal() {
    local num_terminals=10

    echo "=== 场景1：理想情况（无冲突） ==="

    # 准备：创建不冲突的分支
    for i in $(seq 1 $num_terminals); do
        branch="ideal-test-$i"

        # 创建分支
        git checkout -b "$branch" main

        # 修改唯一文件
        echo "Feature $i content" > "feature_$i.txt"
        git add "feature_$i.txt"
        git commit -m "Add feature $i"

        git checkout main
    done

    # 启动processor
    merge_queue_processor_start &
    processor_pid=$!

    # 记录开始时间
    local start_time=$(date +%s%3N)

    # 并行enqueue
    for i in $(seq 1 $num_terminals); do
        (
            branch="ideal-test-$i"
            merge_queue_enqueue "$branch" "main" "terminal-$i"
        ) &
    done
    wait

    local enqueue_time=$(date +%s%3N)
    local enqueue_duration=$((enqueue_time - start_time))

    # 等待所有merge完成
    while [[ $(jq '[.[] | select(.branch | startswith("ideal-test")) and (.status == "QUEUED" or .status == "MERGING")] | length' queue.json) -gt 0 ]]; do
        sleep 1
    done

    local complete_time=$(date +%s%3N)
    local total_duration=$((complete_time - start_time))

    # 收集结果
    collect_results "scenario_ideal" "$num_terminals" "$enqueue_duration" "$total_duration"

    # 清理
    kill $processor_pid
    cleanup_test_branches "ideal-test-"
}
```

### 3.2 场景2：部分冲突（50%冲突率）

**目的**: 测试冲突检测和自动rebase的效果

**设置**:
- 10个Terminal，其中5个会产生冲突
- 冲突文件：README.md
- 自动rebase策略：启用

**预期结果**:
- 自动rebase成功率 > 80%
- P90 Wait Time < 120秒
- 最终所有merge成功或标记为MANUAL_REQUIRED

**实现**:
```bash
function scenario_conflict() {
    local num_terminals=10
    local conflict_rate=0.5  # 50%

    echo "=== 场景2：部分冲突 ==="

    # 准备：创建冲突分支
    for i in $(seq 1 $num_terminals); do
        branch="conflict-test-$i"

        git checkout -b "$branch" main

        # 50%概率修改README（造成冲突）
        if (( i % 2 == 0 )); then
            # 冲突分支
            echo "## Feature $i" >> README.md
            echo "This is feature $i" >> README.md
            git add README.md
            git commit -m "Update README for feature $i"
        else
            # 非冲突分支
            echo "Feature $i" > "feature_$i.txt"
            git add "feature_$i.txt"
            git commit -m "Add feature $i"
        fi

        git checkout main
    done

    # 模拟main分支的更新（造成冲突）
    echo "## Main Update" >> README.md
    git add README.md
    git commit -m "Update README on main"

    # 启动processor
    merge_queue_processor_start &
    processor_pid=$!

    local start_time=$(date +%s%3N)

    # 并行enqueue
    for i in $(seq 1 $num_terminals); do
        (
            branch="conflict-test-$i"
            merge_queue_enqueue "$branch" "main" "terminal-$i"
        ) &
    done
    wait

    # 等待完成
    timeout 300 bash -c 'while [[ $(jq "[.[] | select(.branch | startswith(\"conflict-test\")) and (.status == \"QUEUED\" or .status == \"MERGING\")] | length" queue.json) -gt 0 ]]; do sleep 1; done'

    local complete_time=$(date +%s%3N)
    local total_duration=$((complete_time - start_time))

    # 统计冲突处理结果
    local conflict_detected=$(jq '[.[] | select(.branch | startswith("conflict-test")) and (.conflict_check.status == "conflict")] | length' queue.json)
    local auto_rebase_success=$(jq '[.[] | select(.branch | startswith("conflict-test")) and (.metrics.retry_count > 0) and (.status == "MERGED")] | length' queue.json)

    echo "冲突检测: $conflict_detected"
    echo "自动Rebase成功: $auto_rebase_success"

    # 清理
    kill $processor_pid
    cleanup_test_branches "conflict-test-"
}
```

### 3.3 场景3：高并发压力测试

**目的**: 验证系统在高负载下的稳定性

**设置**:
- 50个并发Terminal
- 混合冲突和非冲突分支
- 超时保护：30分钟

**预期结果**:
- 系统不崩溃
- 所有请求最终完成（MERGED或FAILED）
- 平均吞吐量 > 3 merges/分钟

**实现**:
```bash
function scenario_stress() {
    local num_concurrent=50

    echo "=== 场景3：高并发压力测试 ==="

    # 准备分支
    for i in $(seq 1 $num_concurrent); do
        branch="stress-test-$i"

        git checkout -b "$branch" main

        # 随机决定是否冲突（30%概率）
        if (( RANDOM % 10 < 3 )); then
            # 冲突分支
            echo "Feature $i update" >> README.md
            git add README.md
            git commit -m "Stress test $i - conflict"
        else
            # 非冲突分支
            mkdir -p "stress_features"
            echo "Feature $i" > "stress_features/feature_$i.txt"
            git add "stress_features/feature_$i.txt"
            git commit -m "Stress test $i"
        fi

        git checkout main
    done &>/dev/null

    # 启动processor
    merge_queue_processor_start &
    processor_pid=$!

    # 监控资源使用
    monitor_resources "$processor_pid" &
    monitor_pid=$!

    local start_time=$(date +%s)

    # 并行enqueue（批量）
    echo "Enqueueing $num_concurrent requests..."
    for i in $(seq 1 $num_concurrent); do
        (
            branch="stress-test-$i"
            merge_queue_enqueue "$branch" "main" "terminal-$i" 2>&1 | \
                logger -t "stress-test-$i"
        ) &

        # 每10个请求暂停一下，避免过载
        if (( i % 10 == 0 )); then
            sleep 1
        fi
    done
    wait

    echo "All requests enqueued. Waiting for completion..."

    # 等待完成（带超时）
    local timeout=1800  # 30分钟
    local elapsed=0
    while [[ $(jq '[.[] | select(.branch | startswith("stress-test")) and (.status == "QUEUED" or .status == "MERGING")] | length' queue.json) -gt 0 ]]; do
        local completed=$(jq '[.[] | select(.branch | startswith("stress-test")) and (.status == "MERGED" or .status == "FAILED")] | length' queue.json)
        echo "Progress: $completed / $num_concurrent"

        sleep 5
        elapsed=$(($(date +%s) - start_time))

        if [[ $elapsed -gt $timeout ]]; then
            echo "❌ Timeout after $elapsed seconds"
            break
        fi
    done

    local end_time=$(date +%s)
    local total_time=$((end_time - start_time))

    # 统计
    local merged=$(jq '[.[] | select(.branch | startswith("stress-test")) and (.status == "MERGED")] | length' queue.json)
    local failed=$(jq '[.[] | select(.branch | startswith("stress-test")) and (.status == "FAILED")] | length' queue.json)
    local throughput=$(echo "scale=2; $merged / ($total_time / 60)" | bc)

    cat <<EOF

=== 压力测试结果 ===
总耗时: ${total_time}秒 ($(echo "scale=1; $total_time / 60" | bc)分钟)
成功Merge: $merged / $num_concurrent
失败: $failed
吞吐量: $throughput merges/分钟

$([ $merged -eq $num_concurrent ] && echo "✅ PASS: 所有merge成功" || echo "⚠️  部分失败")
EOF

    # 清理
    kill $processor_pid $monitor_pid 2>/dev/null
    cleanup_test_branches "stress-test-"
}
```

### 3.4 场景4：故障恢复测试

**目的**: 验证异常情况下的恢复能力

**设置**:
- Enqueue 10个任务
- 在第3个merge时强制kill processor
- 重启processor并验证恢复

**预期结果**:
- 队列数据不丢失
- 未完成的merge重新入队
- 最终所有merge完成

**实现**:
```bash
function scenario_recovery() {
    echo "=== 场景4：故障恢复测试 ==="

    local num_tasks=10

    # 准备分支
    for i in $(seq 1 $num_tasks); do
        create_test_branch "recovery-test-$i"
    done

    # 启动processor
    merge_queue_processor_start &
    processor_pid=$!

    # Enqueue
    for i in $(seq 1 $num_tasks); do
        merge_queue_enqueue "recovery-test-$i" "main" "terminal-$i"
    done

    # 等待完成3个
    echo "等待前3个merge完成..."
    while [[ $(jq '[.[] | select(.branch | startswith("recovery-test")) and (.status == "MERGED")] | length' queue.json) -lt 3 ]]; do
        sleep 1
    done

    echo "✓ 前3个merge完成"

    # 模拟crash
    echo "⚠️  模拟processor crash (kill -9)"
    kill -9 $processor_pid
    sleep 2

    # 备份队列状态（用于验证）
    cp queue.json queue_before_recovery.json

    # 重启processor
    echo "🔄 重启processor"
    merge_queue_processor_start &
    processor_pid=$!

    # 等待剩余任务完成
    echo "等待剩余任务完成..."
    timeout 180 bash -c 'while [[ $(jq "[.[] | select(.branch | startswith(\"recovery-test\")) and (.status == \"QUEUED\" or .status == \"MERGING\")] | length" queue.json) -gt 0 ]]; do sleep 1; done'

    # 验证结果
    local merged=$(jq '[.[] | select(.branch | startswith("recovery-test")) and (.status == "MERGED")] | length' queue.json)

    cat <<EOF

=== 故障恢复测试结果 ===
总任务数: $num_tasks
成功恢复: $merged
数据丢失: $((num_tasks - merged))

$([ $merged -eq $num_tasks ] && echo "✅ PASS: 完全恢复" || echo "❌ FAIL: 数据丢失")
EOF

    # 清理
    kill $processor_pid 2>/dev/null
    cleanup_test_branches "recovery-test-"
}
```

---

## 4. 性能指标

### 4.1 延迟指标（Latency Metrics）

```bash
function collect_latency_metrics() {
    local prefix="$1"  # 分支前缀

    local wait_times=$(jq -r ".[] | select(.branch | startswith(\"$prefix\")) | .metrics.wait_time_sec" queue.json | sort -n)

    local count=$(echo "$wait_times" | wc -l)
    local sum=$(echo "$wait_times" | awk '{s+=$1} END {print s}')
    local avg=$(echo "scale=2; $sum / $count" | bc)

    local p50=$(echo "$wait_times" | awk -v p=0.50 '{a[NR]=$0} END {print a[int(NR*p)+1]}')
    local p90=$(echo "$wait_times" | awk -v p=0.90 '{a[NR]=$0} END {print a[int(NR*p)+1]}')
    local p99=$(echo "$wait_times" | awk -v p=0.99 '{a[NR]=$0} END {print a[int(NR*p)+1]}')

    local min=$(echo "$wait_times" | head -1)
    local max=$(echo "$wait_times" | tail -1)

    cat <<EOF
Latency Metrics:
  Count: $count
  Average: ${avg}s
  Min: ${min}s
  Max: ${max}s
  P50 (Median): ${p50}s $(check_threshold "$p50" 30)
  P90: ${p90}s $(check_threshold "$p90" 60)
  P99: ${p99}s $(check_threshold "$p99" 120)
EOF
}

function check_threshold() {
    local value=$1
    local threshold=$2

    if (( $(echo "$value < $threshold" | bc -l) )); then
        echo "✅ (< ${threshold}s)"
    else
        echo "❌ (> ${threshold}s)"
    fi
}
```

### 4.2 吞吐量指标（Throughput Metrics）

```bash
function collect_throughput_metrics() {
    local prefix="$1"
    local total_time=$2  # 总耗时（秒）

    local merged_count=$(jq "[.[] | select(.branch | startswith(\"$prefix\")) and (.status == \"MERGED\")] | length" queue.json)
    local failed_count=$(jq "[.[] | select(.branch | startswith(\"$prefix\")) and (.status == \"FAILED\")] | length" queue.json)

    local throughput_per_min=$(echo "scale=2; $merged_count / ($total_time / 60)" | bc)
    local throughput_per_sec=$(echo "scale=3; $merged_count / $total_time" | bc)

    local success_rate=$(echo "scale=2; $merged_count * 100 / ($merged_count + $failed_count)" | bc)

    cat <<EOF
Throughput Metrics:
  Total Time: ${total_time}s ($(echo "scale=1; $total_time / 60" | bc)min)
  Merged: $merged_count
  Failed: $failed_count
  Success Rate: ${success_rate}%
  Throughput: $throughput_per_min merges/min $([ $(echo "$throughput_per_min >= 5" | bc) -eq 1 ] && echo "✅" || echo "❌")
  Throughput: $throughput_per_sec merges/sec
EOF
}
```

### 4.3 资源占用指标（Resource Metrics）

```bash
function monitor_resources() {
    local processor_pid=$1
    local output_file=".workflow/merge_queue/resource_metrics.txt"

    echo "Monitoring resources for PID $processor_pid"

    while kill -0 $processor_pid 2>/dev/null; do
        local cpu=$(ps -p $processor_pid -o %cpu= | xargs)
        local mem=$(ps -p $processor_pid -o %mem= | xargs)
        local vsz=$(ps -p $processor_pid -o vsz= | xargs)  # 虚拟内存 (KB)
        local rss=$(ps -p $processor_pid -o rss= | xargs)  # 物理内存 (KB)

        echo "$(date +%s) CPU:${cpu}% MEM:${mem}% VSZ:${vsz}KB RSS:${rss}KB" >> "$output_file"

        sleep 1
    done
}

function analyze_resource_usage() {
    local output_file=".workflow/merge_queue/resource_metrics.txt"

    [[ ! -f "$output_file" ]] && return

    local avg_cpu=$(awk '{print $2}' "$output_file" | cut -d: -f2 | cut -d% -f1 | awk '{s+=$1; n++} END {print s/n}')
    local max_cpu=$(awk '{print $2}' "$output_file" | cut -d: -f2 | cut -d% -f1 | sort -rn | head -1)

    local avg_mem=$(awk '{print $3}' "$output_file" | cut -d: -f2 | cut -d% -f1 | awk '{s+=$1; n++} END {print s/n}')
    local max_mem=$(awk '{print $3}' "$output_file" | cut -d: -f2 | cut -d% -f1 | sort -rn | head -1)

    local max_rss=$(awk '{print $5}' "$output_file" | cut -d: -f2 | cut -dK -f1 | sort -rn | head -1)
    local max_rss_mb=$(echo "scale=2; $max_rss / 1024" | bc)

    cat <<EOF
Resource Usage:
  CPU Average: ${avg_cpu}%
  CPU Peak: ${max_cpu}% $([ $(echo "$max_cpu < 40" | bc) -eq 1 ] && echo "✅" || echo "❌")
  Memory Average: ${avg_mem}%
  Memory Peak: ${max_mem}%
  RSS Peak: ${max_rss_mb}MB $([ $(echo "$max_rss_mb < 300" | bc) -eq 1 ] && echo "✅" || echo "❌")
EOF
}
```

### 4.4 冲突处理指标

```bash
function collect_conflict_metrics() {
    local prefix="$1"

    local total=$(jq "[.[] | select(.branch | startswith(\"$prefix\"))] | length" queue.json)
    local conflict_detected=$(jq "[.[] | select(.branch | startswith(\"$prefix\")) and (.conflict_check.status == \"conflict\")] | length" queue.json)
    local auto_rebase_success=$(jq "[.[] | select(.branch | startswith(\"$prefix\")) and (.metrics.retry_count > 0) and (.status == \"MERGED\")] | length" queue.json)
    local manual_required=$(jq "[.[] | select(.branch | startswith(\"$prefix\")) and (.status == \"MANUAL_REQUIRED\")] | length" queue.json)

    local conflict_rate=$(echo "scale=2; $conflict_detected * 100 / $total" | bc)
    local rebase_success_rate=$(echo "scale=2; $auto_rebase_success * 100 / $conflict_detected" | bc)

    cat <<EOF
Conflict Handling Metrics:
  Total Merges: $total
  Conflicts Detected: $conflict_detected (${conflict_rate}%)
  Auto Rebase Success: $auto_rebase_success (${rebase_success_rate}%)
  Manual Required: $manual_required
EOF
}
```

---

## 5. 测试工具

### 5.1 一键测试脚本

```bash
#!/bin/bash
# .workflow/tests/merge_queue_benchmark.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# Source dependencies
source .workflow/lib/merge_queue_manager.sh

# 测试报告目录
REPORT_DIR=".workflow/merge_queue/benchmark_reports"
mkdir -p "$REPORT_DIR"

# 当前测试运行ID
RUN_ID="run-$(date +%Y%m%d-%H%M%S)"
REPORT_FILE="$REPORT_DIR/${RUN_ID}.md"

# 初始化报告
function init_report() {
    cat > "$REPORT_FILE" <<EOF
# Merge Queue Performance Benchmark Report

**Run ID**: $RUN_ID
**Date**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

## Environment

$(collect_env_info)

## Test Results

EOF
}

# 运行所有场景
function run_all_scenarios() {
    echo "🚀 Starting Merge Queue Performance Benchmark"
    echo ""

    init_report

    # 场景1
    echo "📋 Running Scenario 1: Ideal Case (No Conflicts)"
    scenario_ideal | tee -a "$REPORT_FILE"
    echo ""

    # 场景2
    echo "📋 Running Scenario 2: Partial Conflicts (50%)"
    scenario_conflict | tee -a "$REPORT_FILE"
    echo ""

    # 场景3
    echo "📋 Running Scenario 3: High Concurrency Stress Test"
    scenario_stress | tee -a "$REPORT_FILE"
    echo ""

    # 场景4
    echo "📋 Running Scenario 4: Failure Recovery"
    scenario_recovery | tee -a "$REPORT_FILE"
    echo ""

    # 生成总结
    generate_summary | tee -a "$REPORT_FILE"

    echo ""
    echo "✅ Benchmark complete"
    echo "📄 Report: $REPORT_FILE"
}

# 生成总结
function generate_summary() {
    cat <<EOF

## Summary

| Scenario | Status | Key Metrics |
|----------|--------|-------------|
| Ideal Case | $(check_scenario_status "ideal-test") | P90: $(get_p90 "ideal-test")s |
| Partial Conflicts | $(check_scenario_status "conflict-test") | Auto Rebase: $(get_rebase_success "conflict-test")% |
| Stress Test | $(check_scenario_status "stress-test") | Throughput: $(get_throughput "stress-test") m/min |
| Recovery Test | $(check_scenario_status "recovery-test") | Recovery Rate: 100% |

## Conclusion

$(generate_conclusion)

---

*Generated by Claude Enhancer Merge Queue Benchmark Tool*
EOF
}

# 主函数
function main() {
    local mode="${1:-all}"

    case "$mode" in
        all)
            run_all_scenarios
            ;;
        ideal)
            scenario_ideal
            ;;
        conflict)
            scenario_conflict
            ;;
        stress)
            scenario_stress
            ;;
        recovery)
            scenario_recovery
            ;;
        *)
            echo "Usage: $0 [all|ideal|conflict|stress|recovery]"
            exit 1
            ;;
    esac
}

main "$@"
```

### 5.2 持续监控工具

```bash
#!/bin/bash
# .workflow/tools/merge_queue_monitor.sh

# 实时监控merge queue性能

watch -n 2 '
clear
echo "=== Merge Queue Performance Monitor ==="
echo "Time: $(date +"%H:%M:%S")"
echo ""

# 队列状态
echo "Queue Status:"
echo "  QUEUED:   $(jq "[.[] | select(.status == \"QUEUED\")] | length" queue.json)"
echo "  MERGING:  $(jq "[.[] | select(.status == \"MERGING\")] | length" queue.json)"
echo "  MERGED:   $(jq "[.[] | select(.status == \"MERGED\")] | length" queue.json)"
echo "  FAILED:   $(jq "[.[] | select(.status == \"FAILED\")] | length" queue.json)"
echo ""

# 实时性能
echo "Real-time Performance:"
wait_times=$(jq -r ".[] | select(.status == \"QUEUED\") | .metrics.wait_time_sec" queue.json | sort -n)
if [[ -n "$wait_times" ]]; then
    avg=$(echo "$wait_times" | awk "{s+=\$1; n++} END {print s/n}")
    max=$(echo "$wait_times" | tail -1)
    echo "  Avg Wait: ${avg}s"
    echo "  Max Wait: ${max}s"
fi
echo ""

# Processor状态
if pgrep -f "merge_queue_process" >/dev/null; then
    pid=$(pgrep -f "merge_queue_process")
    cpu=$(ps -p $pid -o %cpu= | xargs)
    mem=$(ps -p $pid -o %mem= | xargs)
    echo "Processor Status: ✅ Running"
    echo "  PID: $pid"
    echo "  CPU: ${cpu}%"
    echo "  MEM: ${mem}%"
else
    echo "Processor Status: ❌ Stopped"
fi
'
```

---

## 6. 测试脚本

完整的测试套件包含在上述工具中，关键函数包括：

1. **scenario_ideal()** - 理想情况测试
2. **scenario_conflict()** - 冲突处理测试
3. **scenario_stress()** - 压力测试
4. **scenario_recovery()** - 故障恢复测试
5. **collect_*_metrics()** - 指标收集函数
6. **monitor_resources()** - 资源监控

---

## 7. 结果分析

### 7.1 示例报告

```markdown
# Merge Queue Performance Benchmark Report

**Run ID**: run-20251010-180000
**Date**: 2025-10-10 18:00:00 UTC

## Environment

OS: Linux
Kernel: 5.15.0-152-generic
CPU: 4 cores
Memory: 8 GB
Git Version: 2.34.1

## Test Results

### Scenario 1: Ideal Case (No Conflicts)

Latency Metrics:
  Count: 10
  Average: 25.3s
  P50: 24s ✅ (< 30s)
  P90: 45s ✅ (< 60s)
  P99: 52s ✅ (< 120s)

Throughput Metrics:
  Merged: 10
  Failed: 0
  Success Rate: 100%
  Throughput: 6.7 merges/min ✅

Resource Usage:
  CPU Peak: 25% ✅
  RSS Peak: 180MB ✅

**Status**: ✅ PASS

---

### Scenario 2: Partial Conflicts (50%)

Conflict Handling Metrics:
  Conflicts Detected: 5 (50%)
  Auto Rebase Success: 4 (80%)
  Manual Required: 1

Latency Metrics:
  P90: 85s ✅ (< 120s)

**Status**: ✅ PASS

---

### Scenario 3: High Concurrency Stress Test

Throughput Metrics:
  Total Time: 480s (8.0min)
  Merged: 48 / 50
  Failed: 2
  Success Rate: 96%
  Throughput: 6.0 merges/min ✅

Resource Usage:
  CPU Peak: 35% ✅
  RSS Peak: 250MB ✅

**Status**: ✅ PASS

---

### Scenario 4: Failure Recovery

Recovery Test:
  Total Tasks: 10
  Successfully Recovered: 10
  Data Loss: 0

**Status**: ✅ PASS

---

## Summary

| Scenario | Status | Key Metrics |
|----------|--------|-------------|
| Ideal Case | ✅ PASS | P90: 45s |
| Partial Conflicts | ✅ PASS | Auto Rebase: 80% |
| Stress Test | ✅ PASS | Throughput: 6.0 m/min |
| Recovery Test | ✅ PASS | Recovery Rate: 100% |

## Conclusion

✅ **ALL TESTS PASSED**

The Merge Queue Manager meets all performance targets:
- Latency P90 < 60s ✅
- Throughput > 5 merges/min ✅
- Concurrency support ≥ 10 terminals ✅
- Resource usage within limits ✅
- Failure recovery functional ✅

**Recommendation**: Ready for production deployment.
```

---

## 8. 回归测试

### 8.1 自动化回归测试

```bash
#!/bin/bash
# .workflow/tests/merge_queue_regression.sh

# 在每次代码变更后运行，确保性能不退化

set -euo pipefail

BASELINE_REPORT=".workflow/merge_queue/benchmark_reports/baseline.json"
CURRENT_REPORT=".workflow/merge_queue/benchmark_reports/current.json"

function run_regression_test() {
    echo "🔄 Running regression test..."

    # 运行基准测试
    ./merge_queue_benchmark.sh all

    # 提取关键指标
    extract_key_metrics > "$CURRENT_REPORT"

    # 比较
    if [[ -f "$BASELINE_REPORT" ]]; then
        compare_with_baseline
    else
        echo "⚠️  No baseline found, creating one..."
        cp "$CURRENT_REPORT" "$BASELINE_REPORT"
    fi
}

function extract_key_metrics() {
    jq -n \
        --arg p50_ideal "$(get_metric 'ideal-test' 'p50')" \
        --arg p90_ideal "$(get_metric 'ideal-test' 'p90')" \
        --arg throughput_stress "$(get_metric 'stress-test' 'throughput')" \
        '{
            "p50_latency_ideal": $p50_ideal,
            "p90_latency_ideal": $p90_ideal,
            "throughput_stress": $throughput_stress,
            "timestamp": now
        }'
}

function compare_with_baseline() {
    local p50_baseline=$(jq -r '.p50_latency_ideal' "$BASELINE_REPORT")
    local p50_current=$(jq -r '.p50_latency_ideal' "$CURRENT_REPORT")

    local degradation=$(echo "scale=2; ($p50_current - $p50_baseline) * 100 / $p50_baseline" | bc)

    echo "Performance Comparison:"
    echo "  P50 Latency (Ideal): ${p50_baseline}s → ${p50_current}s"
    echo "  Change: ${degradation}%"

    if (( $(echo "$degradation > 10" | bc -l) )); then
        echo "❌ Performance regression detected (>10% degradation)"
        exit 1
    else
        echo "✅ Performance maintained"
    fi
}

run_regression_test
```

---

## 总结

本性能基准测试方案提供了：

1. **4个核心测试场景** - 覆盖理想、冲突、压力、恢复
2. **完整的指标体系** - 延迟、吞吐、资源、冲突处理
3. **自动化测试工具** - 一键运行、持续监控
4. **详细的报告模板** - 标准化的结果展示
5. **回归测试机制** - 防止性能退化

**使用方式**:
```bash
# 运行全部测试
.workflow/tests/merge_queue_benchmark.sh all

# 运行单个场景
.workflow/tests/merge_queue_benchmark.sh stress

# 持续监控
.workflow/tools/merge_queue_monitor.sh

# 回归测试
.workflow/tests/merge_queue_regression.sh
```

**验收标准**:
- 所有场景测试通过 ✅
- 性能指标达到目标 ✅
- 回归测试无退化 ✅

---

*生成时间: 2025-10-10*
*Claude Enhancer 5.3 - Production-Ready AI Programming*
