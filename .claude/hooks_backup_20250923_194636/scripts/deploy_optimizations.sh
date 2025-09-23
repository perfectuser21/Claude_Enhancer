#!/bin/bash
# 自动部署性能优化方案并验证效果
# 目标: Hook成功率36%→95%+, 并发成功率70-83%→95%+

set -euo pipefail

# 配置
readonly SCRIPT_DIR="$(dirname "$0")"
readonly CLAUDE_DIR="$(dirname "$SCRIPT_DIR")"
readonly BACKUP_DIR="$CLAUDE_DIR/hooks_backup_$(date +%Y%m%d_%H%M%S)"
readonly TEST_RESULTS_DIR="/tmp/optimization_test_results"
readonly PARALLEL_JOBS=$(nproc)

# 颜色定义
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# 初始化
init_deployment() {
    echo -e "${BLUE}🚀 Claude Enhancer 性能优化部署${NC}"
    echo "=========================================="

    # 创建必要目录
    mkdir -p "$BACKUP_DIR" "$TEST_RESULTS_DIR"

    # 检查系统要求
    echo -e "${YELLOW}📋 检查系统要求...${NC}"

    if ! command -v bc &> /dev/null; then
        echo "安装 bc 计算器..."
        apt-get update && apt-get install -y bc
    fi

    if ! python3 -c "import psutil" 2>/dev/null; then
        echo "安装 Python psutil..."
        pip3 install psutil
    fi

    echo "✅ 系统要求检查完成"
}

# 备份现有配置
backup_current_system() {
    echo -e "\n${YELLOW}📦 备份现有系统...${NC}"

    # 备份Hooks
    cp -r "$CLAUDE_DIR/hooks/" "$BACKUP_DIR/"

    # 备份设置
    cp "$CLAUDE_DIR/settings.json" "$BACKUP_DIR/" 2>/dev/null || true

    # 备份脚本
    if [[ -d "$CLAUDE_DIR/scripts" ]]; then
        cp -r "$CLAUDE_DIR/scripts/" "$BACKUP_DIR/"
    fi

    echo "📁 备份保存到: $BACKUP_DIR"
    echo "✅ 备份完成"
}

# 部署优化Hook
deploy_optimized_hooks() {
    echo -e "\n${YELLOW}⚡ 部署优化后的Hook系统...${NC}"

    # 设置权限
    chmod +x "$CLAUDE_DIR/hooks/"*.sh

    # 更新settings.json以使用优化Hook
    local settings_file="$CLAUDE_DIR/settings.json"
    if [[ -f "$settings_file" ]]; then
        # 备份原设置
        cp "$settings_file" "${settings_file}.backup"

        # 更新Hook配置为优化版本
        python3 << EOF
import json

settings_file = "$settings_file"
try:
    with open(settings_file, 'r') as f:
        settings = json.load(f)

    # 更新Hook配置
    if 'hooks' not in settings:
        settings['hooks'] = {}

    # 配置优化后的Hook
    optimized_hooks = {
        'performance_monitor': {
            'script': 'optimized_performance_monitor.sh',
            'blocking': False,
            'timeout': 100,
            'enabled': True
        },
        'agent_selector': {
            'script': 'ultra_fast_agent_selector.sh',
            'blocking': False,
            'timeout': 50,
            'enabled': True
        },
        'error_recovery': {
            'script': 'smart_error_recovery.sh',
            'blocking': False,
            'timeout': 200,
            'enabled': True
        },
        'concurrent_optimizer': {
            'script': 'concurrent_optimizer.sh',
            'blocking': False,
            'timeout': 150,
            'enabled': True
        }
    }

    settings['hooks'].update(optimized_hooks)

    # 启用并发优化
    settings['performance'] = {
        'max_concurrent_hooks': $PARALLEL_JOBS,
        'hook_timeout_ms': 200,
        'enable_caching': True,
        'enable_parallel_execution': True
    }

    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)

    print("✅ Hook配置已更新")

except Exception as e:
    print(f"❌ 配置更新失败: {e}")
    exit(1)
EOF
    fi

    echo "✅ 优化Hook部署完成"
}

# 基准性能测试
run_baseline_test() {
    echo -e "\n${YELLOW}📊 运行基准性能测试...${NC}"

    local test_output="$TEST_RESULTS_DIR/baseline_test.json"

    # 运行压力测试
    timeout 60 python3 << EOF > "$test_output" 2>&1 || true
import json
import time
import subprocess
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_hook_performance(hook_script, iterations=10):
    """测试单个Hook性能"""
    times = []
    success_count = 0

    for i in range(iterations):
        start_time = time.time()
        try:
            result = subprocess.run(
                ['bash', '$CLAUDE_DIR/hooks/' + hook_script],
                input='{"tool": "test", "prompt": "test performance"}',
                text=True,
                capture_output=True,
                timeout=1
            )
            end_time = time.time()

            if result.returncode == 0:
                success_count += 1

            times.append((end_time - start_time) * 1000)

        except subprocess.TimeoutExpired:
            times.append(1000)  # 超时计为1000ms
        except Exception:
            times.append(1000)

    return {
        'avg_time': statistics.mean(times) if times else 1000,
        'success_rate': success_count / iterations * 100,
        'times': times
    }

def test_concurrent_performance(workers_list=[5, 10, 20]):
    """测试并发性能"""
    results = {}

    for workers in workers_list:
        print(f"Testing with {workers} workers...")
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for i in range(workers * 2):  # 每个worker处理2个任务
                future = executor.submit(
                    test_hook_performance,
                    'optimized_performance_monitor.sh',
                    1
                )
                futures.append(future)

            success_count = 0
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=5)
                    if result['success_rate'] > 0:
                        success_count += 1
                except Exception:
                    pass

        end_time = time.time()
        total_time = end_time - start_time
        success_rate = success_count / len(futures) * 100

        results[f'{workers}_workers'] = {
            'total_time': total_time,
            'success_rate': success_rate,
            'throughput': len(futures) / total_time
        }

    return results

# 执行测试
print("🧪 运行基准测试...")

baseline_results = {
    'timestamp': time.time(),
    'hook_tests': {},
    'concurrent_tests': {}
}

# 测试各个Hook
hooks_to_test = [
    'optimized_performance_monitor.sh',
    'ultra_fast_agent_selector.sh',
    'smart_error_recovery.sh',
    'concurrent_optimizer.sh'
]

for hook in hooks_to_test:
    print(f"Testing {hook}...")
    try:
        baseline_results['hook_tests'][hook] = test_hook_performance(hook)
    except Exception as e:
        print(f"Error testing {hook}: {e}")
        baseline_results['hook_tests'][hook] = {
            'avg_time': 1000,
            'success_rate': 0,
            'times': []
        }

# 测试并发性能
print("Testing concurrent performance...")
try:
    baseline_results['concurrent_tests'] = test_concurrent_performance()
except Exception as e:
    print(f"Error testing concurrent performance: {e}")

print(json.dumps(baseline_results, indent=2))
EOF

    echo "📄 基准测试结果保存到: $test_output"
}

# 比较性能改进
compare_performance() {
    echo -e "\n${YELLOW}📈 性能改进对比...${NC}"

    local baseline_file="$TEST_RESULTS_DIR/baseline_test.json"
    local comparison_output="$TEST_RESULTS_DIR/performance_comparison.md"

    if [[ ! -f "$baseline_file" ]]; then
        echo "❌ 未找到基准测试结果"
        return 1
    fi

    python3 << EOF > "$comparison_output"
import json
import sys

try:
    with open('$baseline_file', 'r') as f:
        baseline = json.load(f)

    print("# Claude Enhancer 性能优化效果报告")
    print(f"**生成时间**: $(date)")
    print("")

    print("## 🎯 优化目标 vs 实际效果")
    print("")
    print("| 指标 | 优化前目标 | 优化后目标 | 实际效果 | 达成状态 |")
    print("|------|------------|------------|----------|----------|")

    # Hook性能分析
    hook_success_rates = []
    hook_avg_times = []

    for hook_name, results in baseline.get('hook_tests', {}).items():
        success_rate = results.get('success_rate', 0)
        avg_time = results.get('avg_time', 1000)
        hook_success_rates.append(success_rate)
        hook_avg_times.append(avg_time)

    overall_hook_success = sum(hook_success_rates) / len(hook_success_rates) if hook_success_rates else 0
    overall_hook_time = sum(hook_avg_times) / len(hook_avg_times) if hook_avg_times else 1000

    # Hook成功率
    hook_status = "✅ 达成" if overall_hook_success >= 95 else "🔄 进行中" if overall_hook_success >= 80 else "❌ 需改进"
    print(f"| Hook成功率 | 36% | 95%+ | {overall_hook_success:.1f}% | {hook_status} |")

    # Hook响应时间
    time_status = "✅ 达成" if overall_hook_time <= 200 else "🔄 进行中" if overall_hook_time <= 500 else "❌ 需改进"
    print(f"| Hook响应时间 | 677ms | <200ms | {overall_hook_time:.0f}ms | {time_status} |")

    # 并发性能分析
    concurrent_results = baseline.get('concurrent_tests', {})
    if concurrent_results:
        # 取20个worker的成功率作为参考
        worker_20_result = concurrent_results.get('20_workers', {})
        concurrent_success = worker_20_result.get('success_rate', 0)
        concurrent_status = "✅ 达成" if concurrent_success >= 95 else "🔄 进行中" if concurrent_success >= 85 else "❌ 需改进"
        print(f"| 并发成功率 | 70% | 95%+ | {concurrent_success:.1f}% | {concurrent_status} |")

    print("")
    print("## 📊 详细测试结果")
    print("")

    # Hook详细结果
    print("### Hook性能测试")
    print("")
    print("| Hook名称 | 平均响应时间 | 成功率 | 状态 |")
    print("|----------|--------------|--------|------|")

    for hook_name, results in baseline.get('hook_tests', {}).items():
        success_rate = results.get('success_rate', 0)
        avg_time = results.get('avg_time', 1000)
        status = "🟢 优秀" if success_rate >= 95 and avg_time <= 200 else "🟡 良好" if success_rate >= 80 else "🔴 需优化"
        clean_name = hook_name.replace('.sh', '').replace('_', ' ').title()
        print(f"| {clean_name} | {avg_time:.0f}ms | {success_rate:.1f}% | {status} |")

    print("")

    # 并发详细结果
    print("### 并发性能测试")
    print("")
    if concurrent_results:
        print("| Worker数量 | 总时间 | 成功率 | 吞吐量 |")
        print("|------------|--------|--------|--------|")

        for workers, results in concurrent_results.items():
            total_time = results.get('total_time', 0)
            success_rate = results.get('success_rate', 0)
            throughput = results.get('throughput', 0)
            worker_count = workers.replace('_workers', '')
            print(f"| {worker_count} | {total_time:.2f}s | {success_rate:.1f}% | {throughput:.1f}/s |")

    print("")
    print("## 💡 优化建议")
    print("")

    if overall_hook_success < 95:
        print("- 🔧 Hook成功率仍需提升，建议启用更多错误重试机制")

    if overall_hook_time > 200:
        print("- ⚡ Hook响应时间仍需优化，建议进一步缓存优化")

    if concurrent_results:
        worst_concurrent = min(concurrent_results.values(), key=lambda x: x.get('success_rate', 0))
        if worst_concurrent.get('success_rate', 0) < 95:
            print("- 🔄 并发成功率需要进一步优化，建议调整资源限制")

    print("")
    print("## 🚀 下一步行动")
    print("")
    print("1. 监控系统运行24小时收集更多数据")
    print("2. 根据实际使用情况微调参数")
    print("3. 继续优化性能瓶颈点")
    print("4. 定期执行性能回归测试")

except Exception as e:
    print(f"生成报告时出错: {e}")
    sys.exit(1)
EOF

    echo "📄 性能对比报告: $comparison_output"

    # 显示关键指标
    echo -e "\n${GREEN}🎉 优化部署完成！${NC}"
    echo -e "${CYAN}关键改进:${NC}"

    if [[ -f "$baseline_file" ]]; then
        python3 << EOF
import json
try:
    with open('$baseline_file', 'r') as f:
        data = json.load(f)

    hook_results = data.get('hook_tests', {})
    if hook_results:
        success_rates = [r.get('success_rate', 0) for r in hook_results.values()]
        avg_times = [r.get('avg_time', 1000) for r in hook_results.values()]

        overall_success = sum(success_rates) / len(success_rates)
        overall_time = sum(avg_times) / len(avg_times)

        print(f"  🎯 Hook成功率: {overall_success:.1f}% (目标: 95%+)")
        print(f"  ⚡ 平均响应时间: {overall_time:.0f}ms (目标: <200ms)")

    concurrent_results = data.get('concurrent_tests', {})
    if concurrent_results and '20_workers' in concurrent_results:
        concurrent_success = concurrent_results['20_workers'].get('success_rate', 0)
        print(f"  🔄 并发成功率: {concurrent_success:.1f}% (目标: 95%+)")

except Exception as e:
    print(f"  ❌ 无法解析测试结果: {e}")
EOF
    fi
}

# 启动监控系统
start_monitoring() {
    echo -e "\n${YELLOW}📊 启动实时监控系统...${NC}"

    # 启动性能监控仪表板
    local monitor_script="$SCRIPT_DIR/realtime_performance_dashboard.py"
    if [[ -f "$monitor_script" ]]; then
        echo "🖥️ 启动实时监控仪表板..."
        echo "   使用命令查看: python3 $monitor_script"
        echo "   生成报告: python3 $monitor_script report 1"
    fi

    # 创建监控启动脚本
    cat > "$CLAUDE_DIR/start_monitoring.sh" << 'EOF'
#!/bin/bash
# 快速启动性能监控

echo "🚀 启动Claude Enhancer性能监控..."

SCRIPT_DIR="$(dirname "$0")/scripts"

if [[ -f "$SCRIPT_DIR/realtime_performance_dashboard.py" ]]; then
    python3 "$SCRIPT_DIR/realtime_performance_dashboard.py"
else
    echo "❌ 监控脚本未找到"
    exit 1
fi
EOF

    chmod +x "$CLAUDE_DIR/start_monitoring.sh"

    echo "✅ 监控系统已配置"
    echo "   启动命令: ./start_monitoring.sh"
}

# 创建回滚脚本
create_rollback_script() {
    echo -e "\n${YELLOW}🔄 创建回滚脚本...${NC}"

    cat > "$CLAUDE_DIR/rollback_optimizations.sh" << EOF
#!/bin/bash
# 回滚性能优化到原始状态

set -euo pipefail

echo "🔄 回滚Claude Enhancer到优化前状态..."

BACKUP_DIR="$BACKUP_DIR"

if [[ ! -d "\$BACKUP_DIR" ]]; then
    echo "❌ 备份目录不存在: \$BACKUP_DIR"
    exit 1
fi

# 恢复Hooks
if [[ -d "\$BACKUP_DIR/hooks" ]]; then
    echo "📂 恢复Hook文件..."
    cp -r "\$BACKUP_DIR/hooks/"* "$CLAUDE_DIR/hooks/"
fi

# 恢复设置
if [[ -f "\$BACKUP_DIR/settings.json" ]]; then
    echo "⚙️ 恢复设置文件..."
    cp "\$BACKUP_DIR/settings.json" "$CLAUDE_DIR/settings.json"
fi

# 恢复脚本
if [[ -d "\$BACKUP_DIR/scripts" ]]; then
    echo "📜 恢复脚本文件..."
    cp -r "\$BACKUP_DIR/scripts/"* "$CLAUDE_DIR/scripts/"
fi

echo "✅ 回滚完成"
echo "📁 备份保留在: \$BACKUP_DIR"
EOF

    chmod +x "$CLAUDE_DIR/rollback_optimizations.sh"
    echo "✅ 回滚脚本已创建: $CLAUDE_DIR/rollback_optimizations.sh"
}

# 主执行函数
main() {
    local action="${1:-deploy}"

    case "$action" in
        deploy)
            init_deployment
            backup_current_system
            deploy_optimized_hooks
            run_baseline_test
            compare_performance
            start_monitoring
            create_rollback_script

            echo -e "\n${GREEN}🎉 性能优化部署完成！${NC}"
            echo -e "${CYAN}快速指令:${NC}"
            echo "  📊 查看实时监控: ./start_monitoring.sh"
            echo "  📄 生成性能报告: python3 .claude/scripts/realtime_performance_dashboard.py report"
            echo "  🔄 回滚优化: ./rollback_optimizations.sh"
            echo "  🧪 再次测试: $0 test"
            ;;
        test)
            run_baseline_test
            compare_performance
            ;;
        rollback)
            if [[ -f "$CLAUDE_DIR/rollback_optimizations.sh" ]]; then
                bash "$CLAUDE_DIR/rollback_optimizations.sh"
            else
                echo "❌ 回滚脚本不存在"
                exit 1
            fi
            ;;
        *)
            echo "用法: $0 {deploy|test|rollback}"
            echo "  deploy  - 部署所有优化"
            echo "  test    - 仅运行性能测试"
            echo "  rollback - 回滚到优化前状态"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"