#!/bin/bash
# Claude Enhancer 性能测试套件 v3.0
# 全面测试所有优化组件的性能提升

set -e

# ==================== 配置区 ====================
TEST_ITERATIONS=10
TIMEOUT_SECONDS=30
RESULTS_DIR="/home/xx/dev/Claude_Enhancer/.claude/performance_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$RESULTS_DIR/performance_test_report_$TIMESTAMP.md"

# 颜色配置
readonly C_RED='\033[0;31m'
readonly C_GREEN='\033[0;32m'
readonly C_YELLOW='\033[1;33m'
readonly C_BLUE='\033[0;34m'
readonly C_CYAN='\033[0;36m'
readonly C_BOLD='\033[1m'
readonly C_RESET='\033[0m'

# ==================== 测试组件路径 ====================
CLEANUP_ORIGINAL="/home/xx/dev/Claude_Enhancer/.claude/scripts/cleanup.sh"
CLEANUP_OPTIMIZED="/home/xx/dev/Claude_Enhancer/.claude/scripts/performance_optimized_cleanup.sh"
CLEANUP_HYPER="/home/xx/dev/Claude_Enhancer/.claude/scripts/hyper_performance_cleanup.sh"

CONFIG_VALIDATOR_ORIGINAL="/home/xx/dev/Claude_Enhancer/.claude/config/config_validator_fixed.py"
CONFIG_VALIDATOR_HYPER="/home/xx/dev/Claude_Enhancer/.claude/config/hyper_config_validator.py"

PERFORMANCE_MONITOR="/home/xx/dev/Claude_Enhancer/.claude/scripts/realtime_performance_monitor.sh"

# ==================== 测试工具函数 ====================
create_test_environment() {
    local test_dir="$1"
    echo "🏗️ 创建测试环境: $test_dir"

    rm -rf "$test_dir" 2>/dev/null || true
    mkdir -p "$test_dir"/{src,lib,temp,build,node_modules,venv}

    cd "$test_dir"

    # 创建测试文件
    for i in {1..200}; do
        # 临时文件
        touch "temp/file${i}.tmp"
        touch "temp/backup${i}.bak"
        touch "temp/swap${i}.swp"
        echo "old content" > "temp/old${i}.orig"
    done

    # JavaScript文件with debug
    for i in {1..100}; do
        cat > "src/component${i}.js" << EOF
console.log('Loading component $i');
console.debug('Debug info');
export default function Component$i() {
    console.info('Info message');
    return <div>Component $i</div>;
}
EOF
    done

    # Python文件with debug
    for i in {1..50}; do
        cat > "lib/module${i}.py" << EOF
print('Module $i loading')
import logging
logging.debug('Debug message')

def function$i():
    print('Executing function')
    return True
EOF
    done

    # Python缓存文件
    mkdir -p lib/__pycache__
    for i in {1..30}; do
        touch "lib/__pycache__/module${i}.cpython-39.pyc"
    done

    # 配置文件 for config validation
    mkdir -p .claude/config
    cat > ".claude/config/main.yaml" << EOF
metadata:
  name: "test-project"
  version: "1.0.0"
  description: "Test project for performance validation"

system:
  cores: 4
  memory: "8GB"
  cache_dir: "/tmp/cache"

workflow:
  phases: [0, 1, 2, 3, 4, 5, 6, 7]
  hooks: true
  validation: true

agents:
  count: 6
  types: ["backend", "frontend", "security", "test", "api", "database"]
  parallel: true
  timeout: 30
EOF

    echo "   ✅ 测试环境创建完成: $(find . -type f | wc -l) 个文件"
}

# ==================== 性能测试器 ====================
run_performance_test() {
    local test_name="$1"
    local command="$2"
    local iterations="${3:-$TEST_ITERATIONS}"

    echo -e "\n${C_CYAN}🧪 测试: $test_name${C_RESET}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    local times=()
    local success_count=0
    local total_time=0

    for ((i=1; i<=iterations; i++)); do
        echo -n "   🔄 迭代 $i/$iterations: "

        local start_time=$(date +%s.%N)
        local exit_code=0

        # 执行命令并捕获退出状态
        if timeout $TIMEOUT_SECONDS bash -c "$command" &>/dev/null; then
            exit_code=0
            ((success_count++))
        else
            exit_code=$?
        fi

        local end_time=$(date +%s.%N)
        local duration=$(echo "$end_time - $start_time" | bc)

        times+=($duration)
        total_time=$(echo "$total_time + $duration" | bc)

        if [[ $exit_code -eq 0 ]]; then
            echo -e "${C_GREEN}✅ ${duration}s${C_RESET}"
        else
            echo -e "${C_RED}❌ ${duration}s (exit: $exit_code)${C_RESET}"
        fi

        # 每次测试后短暂休息
        sleep 0.1
    done

    # 计算统计信息
    local avg_time=$(echo "$total_time / $iterations" | bc -l)
    local success_rate=$(echo "scale=1; $success_count * 100 / $iterations" | bc)

    # 排序时间计算百分位数
    local sorted_times=($(printf '%s\n' "${times[@]}" | sort -n))
    local min_time="${sorted_times[0]}"
    local max_time="${sorted_times[-1]}"

    # 计算百分位数
    local p50_idx=$((iterations / 2))
    local p95_idx=$((iterations * 95 / 100))
    local p99_idx=$((iterations * 99 / 100))

    local p50_time="${sorted_times[$p50_idx]:-$avg_time}"
    local p95_time="${sorted_times[$p95_idx]:-$max_time}"
    local p99_time="${sorted_times[$p99_idx]:-$max_time}"

    # 显示结果
    echo ""
    echo "📊 测试结果:"
    echo "   🔢 迭代次数: $iterations"
    echo "   ✅ 成功率: ${success_rate}%"
    echo "   ⏱️  平均时间: $(printf "%.3f" "$avg_time")s"
    echo "   ⚡ 最快时间: ${min_time}s"
    echo "   🐌 最慢时间: ${max_time}s"
    echo "   📈 P50: ${p50_time}s | P95: ${p95_time}s | P99: ${p99_time}s"
    echo "   🏆 吞吐量: $(echo "scale=1; $iterations / $total_time" | bc) 次/秒"

    # 返回测试结果数据
    echo "$test_name,$avg_time,$min_time,$max_time,$p50_time,$p95_time,$p99_time,$success_rate,$total_time"
}

# ==================== 主测试套件 ====================
run_cleanup_performance_tests() {
    echo -e "${C_BOLD}${C_BLUE}🧹 清理脚本性能测试${C_RESET}"
    echo "════════════════════════════════════════════════════════════════════════════════"

    local test_env="/tmp/cleanup_test_env"
    local results=()

    # 测试所有清理脚本版本
    local cleanup_tests=(
        "cleanup_hyper_v3:$CLEANUP_HYPER"
        "cleanup_optimized:$CLEANUP_OPTIMIZED"
        "cleanup_original:$CLEANUP_ORIGINAL"
    )

    for test_info in "${cleanup_tests[@]}"; do
        local test_name=$(echo "$test_info" | cut -d: -f1)
        local script_path=$(echo "$test_info" | cut -d: -f2)

        if [[ -f "$script_path" ]]; then
            # 为每个测试创建新的环境
            create_test_environment "$test_env"

            # 运行性能测试
            local result=$(run_performance_test "$test_name" "cd '$test_env' && bash '$script_path'")
            results+=("$result")

            # 清理测试环境
            rm -rf "$test_env"
        else
            echo "⚠️ 跳过测试 $test_name: 脚本不存在 ($script_path)"
        fi
    done

    echo ""
    echo "results:cleanup:${results[@]}"
}

run_config_validation_tests() {
    echo -e "\n${C_BOLD}${C_BLUE}⚙️ 配置验证性能测试${C_RESET}"
    echo "════════════════════════════════════════════════════════════════════════════════"

    local test_env="/tmp/config_test_env"
    local results=()

    # 创建配置测试环境
    create_test_environment "$test_env"

    local config_tests=(
        "config_validator_hyper:python3 '$CONFIG_VALIDATOR_HYPER' validate '$test_env/.claude/config/main.yaml'"
        "config_validator_original:python3 '$CONFIG_VALIDATOR_ORIGINAL' validate"
    )

    for test_info in "${config_tests[@]}"; do
        local test_name=$(echo "$test_info" | cut -d: -f1)
        local command=$(echo "$test_info" | cut -d: -f2-)

        if [[ -f "$(echo "$command" | awk '{print $2}')" ]]; then
            local result=$(run_performance_test "$test_name" "cd '$test_env' && $command")
            results+=("$result")
        else
            echo "⚠️ 跳过测试 $test_name: 验证器不存在"
        fi
    done

    # 清理测试环境
    rm -rf "$test_env"

    echo ""
    echo "results:config:${results[@]}"
}

run_integrated_performance_test() {
    echo -e "\n${C_BOLD}${C_BLUE}🔄 集成性能测试${C_RESET}"
    echo "════════════════════════════════════════════════════════════════════════════════"

    local test_env="/tmp/integrated_test_env"
    create_test_environment "$test_env"

    # 集成测试：配置验证 + 清理
    local integrated_command="
        cd '$test_env' &&
        python3 '$CONFIG_VALIDATOR_HYPER' validate '.claude/config/main.yaml' &&
        bash '$CLEANUP_HYPER'
    "

    local result=$(run_performance_test "integrated_workflow" "$integrated_command" 5)

    # 清理测试环境
    rm -rf "$test_env"

    echo ""
    echo "results:integrated:$result"
}

# ==================== 报告生成器 ====================
generate_performance_report() {
    local cleanup_results=("$@")

    mkdir -p "$RESULTS_DIR"

    cat > "$REPORT_FILE" << EOF
# Claude Enhancer 性能测试报告 v3.0

**测试时间**: $(date)
**测试环境**: $(uname -a)
**CPU核心**: $(nproc)
**内存总量**: $(free -m | awk '/^Mem:/{print $2}')MB
**测试迭代**: $TEST_ITERATIONS 次

## 📊 测试总结

### 🚀 主要性能提升

EOF

    # 解析结果并生成对比
    local cleanup_results_parsed=()
    local config_results_parsed=()
    local integrated_results_parsed=()

    for line in "${cleanup_results[@]}"; do
        if [[ "$line" == results:cleanup:* ]]; then
            cleanup_results_parsed=($(echo "$line" | sed 's/results:cleanup://'))
        elif [[ "$line" == results:config:* ]]; then
            config_results_parsed=($(echo "$line" | sed 's/results:config://'))
        elif [[ "$line" == results:integrated:* ]]; then
            integrated_results_parsed=($(echo "$line" | sed 's/results:integrated://'))
        fi
    done

    # 清理脚本对比表
    if [[ ${#cleanup_results_parsed[@]} -gt 0 ]]; then
        cat >> "$REPORT_FILE" << EOF
### 🧹 清理脚本性能对比

| 版本 | 平均时间 | 最快时间 | P95时间 | 成功率 | 吞吐量 |
|------|----------|----------|---------|--------|--------|
EOF

        for result in "${cleanup_results_parsed[@]}"; do
            IFS=',' read -r name avg_time min_time max_time p50 p95 p99 success_rate throughput <<< "$result"
            local throughput_val=$(echo "$TEST_ITERATIONS / $throughput" | bc -l)
            printf "| %s | %.3fs | %.3fs | %.3fs | %.1f%% | %.1f/s |\n" \
                "$name" "$avg_time" "$min_time" "$p95" "$success_rate" "$throughput_val" >> "$REPORT_FILE"
        done
    fi

    # 配置验证对比表
    if [[ ${#config_results_parsed[@]} -gt 0 ]]; then
        cat >> "$REPORT_FILE" << EOF

### ⚙️ 配置验证性能对比

| 版本 | 平均时间 | 最快时间 | P95时间 | 成功率 |
|------|----------|----------|---------|--------|
EOF

        for result in "${config_results_parsed[@]}"; do
            IFS=',' read -r name avg_time min_time max_time p50 p95 p99 success_rate throughput <<< "$result"
            printf "| %s | %.3fs | %.3fs | %.3fs | %.1f%% |\n" \
                "$name" "$avg_time" "$min_time" "$p95" "$success_rate" >> "$REPORT_FILE"
        done
    fi

    # 计算性能提升
    if [[ ${#cleanup_results_parsed[@]} -ge 2 ]]; then
        local original_time=$(echo "${cleanup_results_parsed[-1]}" | cut -d, -f2)
        local hyper_time=$(echo "${cleanup_results_parsed[0]}" | cut -d, -f2)
        local improvement=$(echo "scale=1; $original_time / $hyper_time" | bc)

        cat >> "$REPORT_FILE" << EOF

## 🎯 性能提升分析

### 清理脚本优化效果
- **原始版本**: ${original_time}s
- **超高性能版本**: ${hyper_time}s
- **性能提升**: ${improvement}x

### 🚀 技术创新

- ✅ **SIMD操作模拟**: 向量化文件处理
- ✅ **内存池管理**: 零分配文件系统
- ✅ **锁自由并发**: 分区并行处理
- ✅ **智能缓存**: TTL缓存避免重复计算
- ✅ **零拷贝I/O**: 内存文件系统优化

### 📈 优化策略

1. **并行处理**: 利用多核CPU进行并行任务执行
2. **内存优化**: 使用/dev/shm内存文件系统
3. **I/O优化**: 批量处理减少系统调用
4. **算法优化**: 预编译正则表达式和模式匹配
5. **缓存策略**: 智能结果缓存减少重复计算

EOF
    fi

    cat >> "$REPORT_FILE" << EOF

## 📊 详细测试数据

### 系统信息
- **操作系统**: $(uname -s) $(uname -r)
- **处理器**: $(grep "model name" /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)
- **CPU核心数**: $(nproc)
- **内存容量**: $(free -h | awk '/^Mem:/{print $2}')
- **磁盘类型**: $(lsblk -o NAME,ROTA | grep -v NAME | head -1 | awk '{print ($2=="0"?"SSD":"HDD")}')

### 测试配置
- **迭代次数**: $TEST_ITERATIONS
- **超时限制**: ${TIMEOUT_SECONDS}s
- **测试目录**: /tmp/test_env
- **缓存目录**: /dev/shm/perfect21_*

**生成时间**: $(date)
**报告文件**: $REPORT_FILE
EOF

    echo -e "${C_GREEN}📄 性能测试报告已生成: $REPORT_FILE${C_RESET}"
}

# ==================== 主执行函数 ====================
main() {
    echo -e "${C_BOLD}${C_CYAN}┌──────────────────────────────────────────────────────────────────┐${C_RESET}"
    echo -e "${C_BOLD}${C_CYAN}│              Claude Enhancer 性能测试套件 v3.0                   │${C_RESET}"
    echo -e "${C_BOLD}${C_CYAN}└──────────────────────────────────────────────────────────────────┘${C_RESET}"

    local test_type="${1:-all}"

    case "$test_type" in
        "cleanup")
            run_cleanup_performance_tests
            ;;
        "config")
            run_config_validation_tests
            ;;
        "integrated")
            run_integrated_performance_test
            ;;
        "all")
            echo "🔍 开始全面性能测试..."
            local all_results=()

            # 运行所有测试
            all_results+=($(run_cleanup_performance_tests))
            all_results+=($(run_config_validation_tests))
            all_results+=($(run_integrated_performance_test))

            # 生成综合报告
            generate_performance_report "${all_results[@]}"
            ;;
        "help"|"-h"|"--help")
            echo "Claude Enhancer 性能测试套件 v3.0"
            echo ""
            echo "用法: $0 [test_type]"
            echo ""
            echo "测试类型:"
            echo "  all        - 运行所有性能测试 (默认)"
            echo "  cleanup    - 只测试清理脚本性能"
            echo "  config     - 只测试配置验证性能"
            echo "  integrated - 只测试集成工作流性能"
            echo "  help       - 显示此帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                  # 运行全部测试"
            echo "  $0 cleanup          # 只测试清理脚本"
            echo "  $0 config           # 只测试配置验证"
            ;;
        *)
            echo -e "${C_RED}❌ 未知测试类型: $test_type${C_RESET}"
            echo "使用 '$0 help' 查看帮助信息"
            exit 1
            ;;
    esac

    echo ""
    echo -e "${C_GREEN}🎉 性能测试完成!${C_RESET}"
}

# 检查依赖
if ! command -v bc &> /dev/null; then
    echo "❌ 需要安装 bc: sudo apt-get install bc"
    exit 1
fi

# 执行主函数
main "$@"