#!/usr/bin/env python3
"""
Perfect21并行执行测试脚本
测试多Agent并行调用的效果和性能
"""

import time
import subprocess
import json
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_command(cmd, description):
    """执行命令并记录时间"""
    print(f"\n🚀 {description}")
    print(f"命令: {cmd}")

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        end_time = time.time()
        duration = end_time - start_time

        print(f"⏱️  耗时: {duration:.2f}秒")
        if result.returncode == 0:
            print(f"✅ 成功")
            print(f"输出长度: {len(result.stdout)} 字符")
        else:
            print(f"❌ 失败 (返回码: {result.returncode})")
            if result.stderr:
                print(f"错误: {result.stderr[:200]}...")

        return {
            'cmd': cmd,
            'description': description,
            'duration': duration,
            'success': result.returncode == 0,
            'stdout_length': len(result.stdout),
            'stderr': result.stderr[:200] if result.stderr else ''
        }
    except subprocess.TimeoutExpired:
        print(f"⏰ 超时 (>120秒)")
        return {
            'cmd': cmd,
            'description': description,
            'duration': 120,
            'success': False,
            'error': 'timeout'
        }

def test_sequential_execution():
    """测试顺序执行"""
    print("=" * 60)
    print("📊 测试1: 顺序执行 (无并行)")
    print("=" * 60)

    commands = [
        ("timeout 60s python3 main/cli.py develop '创建用户注册API' --no-parallel", "创建用户注册API (顺序)"),
        ("timeout 60s python3 main/cli.py develop '实现数据验证功能' --no-parallel", "实现数据验证功能 (顺序)")
    ]

    results = []
    total_start = time.time()

    for cmd, desc in commands:
        result = run_command(cmd, desc)
        results.append(result)

    total_time = time.time() - total_start
    print(f"\n📈 顺序执行总耗时: {total_time:.2f}秒")

    return results, total_time

def test_parallel_execution():
    """测试并行执行"""
    print("=" * 60)
    print("🚀 测试2: 并行执行 (强制并行)")
    print("=" * 60)

    commands = [
        ("timeout 60s python3 main/cli.py develop '创建用户登录API' --parallel", "创建用户登录API (并行)"),
        ("timeout 60s python3 main/cli.py develop '实现权限验证功能' --parallel", "实现权限验证功能 (并行)")
    ]

    results = []
    total_start = time.time()

    # 使用线程池并行执行
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_cmd = {
            executor.submit(run_command, cmd, desc): (cmd, desc)
            for cmd, desc in commands
        }

        for future in as_completed(future_to_cmd):
            result = future.result()
            results.append(result)

    total_time = time.time() - total_start
    print(f"\n🚀 并行执行总耗时: {total_time:.2f}秒")

    return results, total_time

def test_complex_task():
    """测试复杂任务的并行处理"""
    print("=" * 60)
    print("🔥 测试3: 复杂任务并行处理")
    print("=" * 60)

    cmd = "timeout 120s python3 main/cli.py develop '实现完整的用户管理系统，包括注册、登录、权限验证和数据管理' --parallel"
    result = run_command(cmd, "复杂用户管理系统 (并行)")

    return [result], result.get('duration', 0)

def analyze_results(seq_results, seq_time, par_results, par_time, complex_results, complex_time):
    """分析测试结果"""
    print("=" * 60)
    print("📊 测试结果分析")
    print("=" * 60)

    # 计算性能提升
    if seq_time > 0:
        speedup = seq_time / par_time
        print(f"🚀 并行执行性能提升: {speedup:.2f}x")
        print(f"⏱️  时间节省: {seq_time - par_time:.2f}秒 ({((seq_time - par_time)/seq_time*100):.1f}%)")

    # 成功率统计
    seq_success = sum(1 for r in seq_results if r.get('success', False))
    par_success = sum(1 for r in par_results if r.get('success', False))
    complex_success = sum(1 for r in complex_results if r.get('success', False))

    print(f"\n📈 执行成功率:")
    print(f"  顺序执行: {seq_success}/{len(seq_results)} ({seq_success/len(seq_results)*100:.1f}%)")
    print(f"  并行执行: {par_success}/{len(par_results)} ({par_success/len(par_results)*100:.1f}%)")
    print(f"  复杂任务: {complex_success}/{len(complex_results)} ({complex_success/len(complex_results)*100:.1f}%)")

    # 输出详情
    print(f"\n📝 输出质量比较:")
    seq_avg = sum(r.get('stdout_length', 0) for r in seq_results) / len(seq_results)
    par_avg = sum(r.get('stdout_length', 0) for r in par_results) / len(par_results)

    print(f"  顺序执行平均输出: {seq_avg:.0f} 字符")
    print(f"  并行执行平均输出: {par_avg:.0f} 字符")

    # 生成报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'tests': {
            'sequential': {
                'results': seq_results,
                'total_time': seq_time,
                'success_rate': seq_success/len(seq_results)
            },
            'parallel': {
                'results': par_results,
                'total_time': par_time,
                'success_rate': par_success/len(par_results)
            },
            'complex': {
                'results': complex_results,
                'total_time': complex_time,
                'success_rate': complex_success/len(complex_results)
            }
        },
        'analysis': {
            'speedup': seq_time / par_time if seq_time > 0 else 0,
            'time_saved': seq_time - par_time,
            'parallel_efficiency': (seq_success + par_success + complex_success) / (len(seq_results) + len(par_results) + len(complex_results))
        }
    }

    return report

def main():
    """主测试流程"""
    print("🎯 Perfect21并行执行测试开始")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 测试1: 顺序执行
        seq_results, seq_time = test_sequential_execution()

        # 等待一下，避免资源冲突
        time.sleep(2)

        # 测试2: 并行执行
        par_results, par_time = test_parallel_execution()

        # 等待一下
        time.sleep(2)

        # 测试3: 复杂任务
        complex_results, complex_time = test_complex_task()

        # 分析结果
        report = analyze_results(seq_results, seq_time, par_results, par_time, complex_results, complex_time)

        # 保存报告
        report_file = f"parallel_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n📄 测试报告已保存: {report_file}")

        # 显示结论
        print("\n" + "=" * 60)
        print("🎯 测试结论")
        print("=" * 60)

        if report['analysis']['speedup'] > 1.2:
            print("✅ 并行执行显著提升性能")
        elif report['analysis']['speedup'] > 1.0:
            print("✅ 并行执行轻微提升性能")
        else:
            print("⚠️  并行执行未显著提升性能")

        if report['analysis']['parallel_efficiency'] > 0.8:
            print("✅ 系统稳定性良好")
        else:
            print("⚠️  系统稳定性需要改进")

    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")

if __name__ == "__main__":
    main()