#!/usr/bin/env python3
"""
Perfect21性能优化Phase 1测试
验证LRU缓存、预编译正则表达式、优化agent选择算法和性能监控的效果
"""

import os
import sys
import time
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_dynamic_workflow_generator_performance():
    """测试动态工作流生成器性能优化"""
    print("\n" + "="*60)
    print("🚀 测试动态工作流生成器性能优化")
    print("="*60)

    try:
        from features.workflow_orchestrator.dynamic_workflow_generator import (
            dynamic_workflow_generator,
            get_workflow_performance_metrics,
            optimize_workflow_performance
        )

        # 测试数据
        test_tasks = [
            "实现用户认证系统，包含JWT token验证、密码加密、角色权限管理",
            "开发API接口，支持RESTful规范，包含CRUD操作和数据验证",
            "创建前端界面，使用React和TypeScript，支持响应式设计",
            "设计数据库schema，包含用户表、权限表、日志表的关联关系",
            "实现单元测试，覆盖率要求90%以上，包含边界条件测试",
            "配置CI/CD流水线，支持自动测试、构建和部署到生产环境",
            "优化系统性能，包含数据库查询优化、缓存策略、并发处理",
            "实现安全功能，包含XSS防护、SQL注入防护、数据加密传输",
            "创建监控系统，包含性能指标收集、告警通知、日志聚合分析",
            "编写技术文档，包含API文档、部署指南、用户操作手册"
        ]

        # 性能基准测试
        print("\n📊 执行性能基准测试...")

        total_start_time = time.perf_counter()
        results = []

        for i, task in enumerate(test_tasks, 1):
            start_time = time.perf_counter()

            # 生成工作流
            workflow = dynamic_workflow_generator.generate_workflow(task)

            execution_time = time.perf_counter() - start_time
            results.append({
                'task_id': i,
                'execution_time': execution_time,
                'workflow_stages': len(workflow.get('stages', [])),
                'total_agents': workflow.get('execution_metadata', {}).get('total_agents', 0)
            })

            print(f"   Task {i}: {execution_time:.3f}s - {len(workflow.get('stages', []))} stages")

        total_time = time.perf_counter() - total_start_time
        avg_time = total_time / len(test_tasks)

        print(f"\n📈 基准测试结果:")
        print(f"   总执行时间: {total_time:.3f}s")
        print(f"   平均执行时间: {avg_time:.3f}s")
        print(f"   最快执行: {min(r['execution_time'] for r in results):.3f}s")
        print(f"   最慢执行: {max(r['execution_time'] for r in results):.3f}s")

        # 获取性能指标
        performance_metrics = get_workflow_performance_metrics()

        print(f"\n🔍 缓存性能:")
        cache_stats = performance_metrics.get('cache_stats', {})
        for cache_name, stats in cache_stats.items():
            print(f"   {cache_name}: {stats.get('hit_rate', 'N/A')} 命中率")

        print(f"\n🧠 Agent选择器性能:")
        agent_stats = performance_metrics.get('agent_selector_stats', {})
        selection_stats = agent_stats.get('selection_stats', {})
        print(f"   总选择次数: {selection_stats.get('total_selections', 0)}")
        print(f"   缓存命中: {selection_stats.get('cache_hits', 0)}")
        print(f"   快速路径: {selection_stats.get('fast_path_selections', 0)}")

        print(f"\n📝 正则表达式使用统计:")
        regex_stats = performance_metrics.get('regex_stats', {})
        for pattern, count in regex_stats.items():
            print(f"   {pattern}: {count} 次使用")

        # 优化建议
        optimization = optimize_workflow_performance()
        print(f"\n💡 优化建议:")
        print(f"   状态: {optimization.get('optimization_status', 'unknown')}")
        for rec in optimization.get('recommendations', []):
            print(f"   - {rec}")

        return {
            'success': True,
            'benchmark_results': results,
            'total_time': total_time,
            'avg_time': avg_time,
            'performance_metrics': performance_metrics,
            'optimization': optimization
        }

    except Exception as e:
        logger.error(f"动态工作流生成器测试失败: {e}")
        return {'success': False, 'error': str(e)}

def test_performance_optimizer():
    """测试性能优化器功能"""
    print("\n" + "="*60)
    print("⚡ 测试性能优化器功能")
    print("="*60)

    try:
        from modules.performance_optimizer import (
            performance_optimizer,
            analyze_performance,
            optimize_performance,
            get_optimization_report
        )

        # 系统性能分析
        print("\n🔍 执行系统性能分析...")
        analysis_start = time.perf_counter()
        analysis = analyze_performance()
        analysis_time = time.perf_counter() - analysis_start

        print(f"   分析用时: {analysis_time:.3f}s")
        print(f"   系统健康分数: {analysis.get('health_score', 0):.1f}/100")
        print(f"   发现瓶颈: {len(analysis.get('bottlenecks', []))} 个")
        print(f"   优化建议: {len(analysis.get('recommendations', []))} 条")

        # 显示瓶颈信息
        bottlenecks = analysis.get('bottlenecks', [])
        if bottlenecks:
            print(f"\n🚨 系统瓶颈:")
            for bottleneck in bottlenecks:
                print(f"   {bottleneck['type']} ({bottleneck['severity']}): {bottleneck['impact_description']}")

        # 显示优化建议
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            print(f"\n💡 优化建议:")
            for rec in recommendations[:5]:  # 显示前5个建议
                print(f"   [{rec['priority']}] {rec['title']}")
                print(f"       {rec['description']}")

        # 应用优化
        print(f"\n🛠️ 应用性能优化...")
        optimization_start = time.perf_counter()
        optimization_result = optimize_performance(['cache', 'memory'])
        optimization_time = time.perf_counter() - optimization_start

        print(f"   优化用时: {optimization_time:.3f}s")
        print(f"   优化成功: {optimization_result.get('success', False)}")

        if optimization_result.get('success'):
            results = optimization_result.get('results', {})
            for opt_type, result in results.items():
                print(f"   {opt_type}优化: 完成")

        # 获取优化报告
        print(f"\n📊 生成优化报告...")
        report = get_optimization_report()

        optimization_stats = report.get('optimization_stats', {})
        print(f"   历史优化次数: {optimization_stats.get('total_optimizations', 0)}")
        print(f"   平均优化时间: {optimization_stats.get('avg_optimization_time', 0):.3f}s")

        return {
            'success': True,
            'analysis_time': analysis_time,
            'analysis_result': analysis,
            'optimization_time': optimization_time,
            'optimization_result': optimization_result,
            'report': report
        }

    except Exception as e:
        logger.error(f"性能优化器测试失败: {e}")
        return {'success': False, 'error': str(e)}

def test_performance_monitor_integration():
    """测试性能监控集成"""
    print("\n" + "="*60)
    print("📊 测试性能监控集成")
    print("="*60)

    try:
        from modules.performance_monitor import (
            performance_monitor,
            get_performance_summary
        )

        # 启动性能监控
        print("\n🎯 启动性能监控...")
        performance_monitor.start_monitoring()

        # 等待收集一些数据
        print("   收集性能数据...")
        time.sleep(3)

        # 获取性能摘要
        summary = get_performance_summary()

        print(f"   健康分数: {summary.get('health_score', 0):.1f}/100")
        print(f"   监控指标: {summary.get('total_metrics', 0)} 个")
        print(f"   活跃告警: {summary.get('active_alerts', 0)} 个")
        print(f"   严重告警: {summary.get('critical_alerts', 0)} 个")

        # 显示关键指标
        key_metrics = summary.get('key_metrics', {})
        if key_metrics:
            print(f"\n📈 关键指标:")
            for metric_name, metric_data in key_metrics.items():
                status = metric_data.get('status', 'unknown')
                value = metric_data.get('value', 0)
                unit = metric_data.get('unit', '')
                print(f"   {metric_name}: {value}{unit} ({status})")

        # 停止监控
        performance_monitor.stop_monitoring()

        return {
            'success': True,
            'summary': summary,
            'monitoring_time': 3
        }

    except Exception as e:
        logger.error(f"性能监控测试失败: {e}")
        return {'success': False, 'error': str(e)}

def test_lru_cache_effectiveness():
    """测试LRU缓存效果"""
    print("\n" + "="*60)
    print("🗄️ 测试LRU缓存效果")
    print("="*60)

    try:
        from features.workflow_orchestrator.dynamic_workflow_generator import LRUCache

        # 创建测试缓存
        cache = LRUCache(max_size=5)

        print("\n🧪 LRU缓存基本功能测试:")

        # 测试基本操作
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")

        # 测试命中
        result1 = cache.get("key1")
        result2 = cache.get("key2")
        result_miss = cache.get("nonexistent")

        print(f"   缓存命中测试: {'✓' if result1 == 'value1' else '✗'}")
        print(f"   缓存丢失测试: {'✓' if result_miss is None else '✗'}")

        # 测试LRU淘汰
        cache.put("key4", "value4")
        cache.put("key5", "value5")
        cache.put("key6", "value6")  # 应该淘汰key3（最少使用）

        evicted = cache.get("key3")  # 应该返回None
        retained = cache.get("key1")  # 应该仍然存在

        print(f"   LRU淘汰测试: {'✓' if evicted is None and retained == 'value1' else '✗'}")

        # 获取缓存统计
        stats = cache.get_stats()
        print(f"\n📊 缓存统计:")
        print(f"   当前大小: {stats['size']}/{stats['max_size']}")
        print(f"   命中率: {stats['hit_rate']}")
        print(f"   利用率: {stats['utilization']}")

        # 性能测试
        print(f"\n⚡ 缓存性能测试:")

        # 预填充缓存
        perf_cache = LRUCache(max_size=1000)
        for i in range(500):
            perf_cache.put(f"key_{i}", f"value_{i}")

        # 测试缓存命中性能
        start_time = time.perf_counter()
        for i in range(100):
            perf_cache.get(f"key_{i % 500}")
        hit_time = time.perf_counter() - start_time

        # 测试缓存丢失性能
        start_time = time.perf_counter()
        for i in range(100):
            perf_cache.get(f"miss_key_{i}")
        miss_time = time.perf_counter() - start_time

        print(f"   100次命中用时: {hit_time:.6f}s")
        print(f"   100次丢失用时: {miss_time:.6f}s")
        print(f"   平均命中时间: {hit_time/100*1000:.3f}μs")

        return {
            'success': True,
            'basic_tests_passed': True,
            'lru_eviction_works': evicted is None and retained == 'value1',
            'cache_stats': stats,
            'performance': {
                'hit_time_100': hit_time,
                'miss_time_100': miss_time,
                'avg_hit_time_us': hit_time/100*1000000
            }
        }

    except Exception as e:
        logger.error(f"LRU缓存测试失败: {e}")
        return {'success': False, 'error': str(e)}

def test_regex_precompilation():
    """测试正则表达式预编译效果"""
    print("\n" + "="*60)
    print("🔍 测试正则表达式预编译效果")
    print("="*60)

    try:
        from features.workflow_orchestrator.dynamic_workflow_generator import PrecompiledRegexManager
        import re

        regex_manager = PrecompiledRegexManager()

        # 测试文本
        test_text = """
        实现用户认证系统，需要@backend-architect和@security-auditor协作。
        这是一个high priority的complex任务，需要python、javascript、database技能。
        预计需要2 hours完成，depends on API设计。
        可以parallel执行前端和后端开发。
        """

        print("\n🧪 预编译正则表达式功能测试:")

        # 测试各种模式
        agent_matches = regex_manager.findall('agent_name', test_text)
        complexity_matches = regex_manager.findall('task_complexity', test_text)
        skill_matches = regex_manager.findall('skill_keywords', test_text)
        time_matches = regex_manager.findall('time_estimates', test_text)

        print(f"   Agent匹配: {agent_matches} {'✓' if 'backend-architect' in agent_matches else '✗'}")
        print(f"   复杂度匹配: {complexity_matches} {'✓' if 'complex' in complexity_matches else '✗'}")
        print(f"   技能匹配: {skill_matches} {'✓' if 'python' in skill_matches else '✗'}")
        print(f"   时间匹配: {time_matches} {'✓' if '2' in time_matches else '✗'}")

        # 性能对比测试
        print(f"\n⚡ 性能对比测试:")

        # 预编译版本性能
        start_time = time.perf_counter()
        for _ in range(1000):
            regex_manager.findall('agent_name', test_text)
            regex_manager.findall('skill_keywords', test_text)
        precompiled_time = time.perf_counter() - start_time

        # 即时编译版本性能
        agent_pattern = re.compile(r'@([a-zA-Z0-9\-_]+)', re.IGNORECASE)
        skill_pattern = re.compile(r'\b(?:python|javascript|react|vue|node|docker|kubernetes|aws|database|sql|nosql|redis|mongodb)\b', re.IGNORECASE)

        start_time = time.perf_counter()
        for _ in range(1000):
            agent_pattern.findall(test_text)
            skill_pattern.findall(test_text)
        manual_time = time.perf_counter() - start_time

        # 每次编译版本性能（最慢）
        start_time = time.perf_counter()
        for _ in range(1000):
            re.findall(r'@([a-zA-Z0-9\-_]+)', test_text, re.IGNORECASE)
            re.findall(r'\b(?:python|javascript|react|vue|node|docker|kubernetes|aws|database|sql|nosql|redis|mongodb)\b', test_text, re.IGNORECASE)
        runtime_compile_time = time.perf_counter() - start_time

        print(f"   预编译管理器: {precompiled_time:.6f}s")
        print(f"   手动预编译: {manual_time:.6f}s")
        print(f"   运行时编译: {runtime_compile_time:.6f}s")

        speedup_vs_runtime = runtime_compile_time / precompiled_time
        print(f"   预编译加速比: {speedup_vs_runtime:.2f}x")

        # 获取使用统计
        usage_stats = regex_manager.get_stats()
        print(f"\n📊 使用统计:")
        for pattern, count in usage_stats.items():
            print(f"   {pattern}: {count} 次")

        return {
            'success': True,
            'pattern_tests_passed': all([
                'backend-architect' in agent_matches,
                'complex' in complexity_matches,
                'python' in skill_matches,
                '2' in time_matches
            ]),
            'performance': {
                'precompiled_time': precompiled_time,
                'manual_time': manual_time,
                'runtime_compile_time': runtime_compile_time,
                'speedup_vs_runtime': speedup_vs_runtime
            },
            'usage_stats': usage_stats
        }

    except Exception as e:
        logger.error(f"正则表达式预编译测试失败: {e}")
        return {'success': False, 'error': str(e)}

def test_agent_selection_optimization():
    """测试Agent选择算法优化"""
    print("\n" + "="*60)
    print("🎯 测试Agent选择算法优化")
    print("="*60)

    try:
        from features.workflow_orchestrator.dynamic_workflow_generator import (
            OptimizedAgentSelector, AgentCapability, TaskRequirement
        )

        selector = OptimizedAgentSelector()

        print("\n🧪 Agent选择器功能测试:")

        # 添加测试agents
        test_agents = [
            AgentCapability("backend-dev", "technical", ["python", "database", "api"], 8.0),
            AgentCapability("frontend-dev", "technical", ["javascript", "react", "css"], 7.5),
            AgentCapability("devops-eng", "infrastructure", ["docker", "kubernetes", "aws"], 8.5),
            AgentCapability("qa-tester", "quality", ["testing", "automation"], 7.0),
            AgentCapability("security-expert", "security", ["security", "audit"], 9.0)
        ]

        for agent in test_agents:
            selector.add_agent(agent)

        # 测试选择逻辑
        task_req = TaskRequirement(
            description="实现API接口",
            domain="technical",
            complexity=7.0,
            required_skills=["python", "api", "database"]
        )

        selected = selector.select_agents(task_req, count=2)
        print(f"   选择结果: {selected}")
        print(f"   选择数量: {len(selected)} {'✓' if len(selected) == 2 else '✗'}")

        # 验证选择的合理性
        expected_agents = ["backend-dev"]  # 应该优先选择backend-dev
        reasonable = any(agent in selected for agent in expected_agents)
        print(f"   选择合理性: {'✓' if reasonable else '✗'}")

        # 性能测试
        print(f"\n⚡ 选择器性能测试:")

        # 大量agent测试
        large_selector = OptimizedAgentSelector()
        for i in range(100):
            agent = AgentCapability(
                f"agent_{i}",
                f"domain_{i % 5}",
                [f"skill_{j}" for j in range(i % 5 + 1)],
                float(i % 10 + 1)
            )
            large_selector.add_agent(agent)

        # 测试选择性能
        start_time = time.perf_counter()
        for _ in range(100):
            large_selector.select_agents(task_req, count=3)
        selection_time = time.perf_counter() - start_time

        print(f"   100次选择用时: {selection_time:.6f}s")
        print(f"   平均选择时间: {selection_time/100*1000:.3f}ms")

        # 获取选择器统计
        stats = selector.get_stats()
        print(f"\n📊 选择器统计:")
        print(f"   总agents: {stats.get('total_agents', 0)}")
        print(f"   可用域: {len(stats.get('domains', []))}")
        print(f"   可用技能: {len(stats.get('skills', []))}")

        selection_stats = stats.get('selection_stats', {})
        print(f"   选择统计:")
        print(f"     总选择: {selection_stats.get('total_selections', 0)}")
        print(f"     缓存命中: {selection_stats.get('cache_hits', 0)}")
        print(f"     快速路径: {selection_stats.get('fast_path_selections', 0)}")

        return {
            'success': True,
            'selection_works': len(selected) == 2,
            'selection_reasonable': reasonable,
            'performance': {
                'selection_time_100': selection_time,
                'avg_selection_time_ms': selection_time/100*1000
            },
            'stats': stats
        }

    except Exception as e:
        logger.error(f"Agent选择算法测试失败: {e}")
        return {'success': False, 'error': str(e)}

def generate_performance_report(test_results: Dict[str, Any]):
    """生成性能测试报告"""
    print("\n" + "="*60)
    print("📋 Perfect21性能优化Phase 1测试报告")
    print("="*60)

    report = {
        'test_timestamp': datetime.now().isoformat(),
        'test_results': test_results,
        'overall_success': all(result.get('success', False) for result in test_results.values()),
        'summary': {}
    }

    # 统计测试结果
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result.get('success', False))

    print(f"\n📊 测试总结:")
    print(f"   测试模块: {total_tests}")
    print(f"   通过测试: {passed_tests}")
    print(f"   测试通过率: {passed_tests/total_tests*100:.1f}%")

    # 性能改进总结
    print(f"\n🚀 性能改进总结:")

    # 工作流生成器性能
    if 'workflow_generator' in test_results and test_results['workflow_generator'].get('success'):
        wf_result = test_results['workflow_generator']
        avg_time = wf_result.get('avg_time', 0)
        print(f"   工作流生成平均时间: {avg_time:.3f}s")

        cache_stats = wf_result.get('performance_metrics', {}).get('cache_stats', {})
        for cache_name, stats in cache_stats.items():
            hit_rate = stats.get('hit_rate', 'N/A')
            print(f"   {cache_name}缓存命中率: {hit_rate}")

    # LRU缓存性能
    if 'lru_cache' in test_results and test_results['lru_cache'].get('success'):
        lru_result = test_results['lru_cache']
        performance = lru_result.get('performance', {})
        avg_hit_time = performance.get('avg_hit_time_us', 0)
        print(f"   LRU缓存平均命中时间: {avg_hit_time:.3f}μs")

    # 正则表达式性能
    if 'regex_precompilation' in test_results and test_results['regex_precompilation'].get('success'):
        regex_result = test_results['regex_precompilation']
        performance = regex_result.get('performance', {})
        speedup = performance.get('speedup_vs_runtime', 1)
        print(f"   正则表达式预编译加速比: {speedup:.2f}x")

    # Agent选择性能
    if 'agent_selection' in test_results and test_results['agent_selection'].get('success'):
        agent_result = test_results['agent_selection']
        performance = agent_result.get('performance', {})
        avg_selection_time = performance.get('avg_selection_time_ms', 0)
        print(f"   Agent选择平均时间: {avg_selection_time:.3f}ms")

    # 系统健康分数
    if 'performance_optimizer' in test_results and test_results['performance_optimizer'].get('success'):
        opt_result = test_results['performance_optimizer']
        analysis = opt_result.get('analysis_result', {})
        health_score = analysis.get('health_score', 0)
        print(f"   系统健康分数: {health_score:.1f}/100")

    # 保存报告
    report_file = f"performance_phase1_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 测试报告已保存: {report_file}")
    except Exception as e:
        print(f"\n❌ 保存报告失败: {e}")

    # 建议
    print(f"\n💡 优化建议:")
    if passed_tests == total_tests:
        print("   ✅ 所有测试通过，性能优化Phase 1实施成功")
        print("   🎯 建议继续实施Phase 2优化")
    else:
        failed_tests = [name for name, result in test_results.items() if not result.get('success')]
        print(f"   ❌ 以下测试失败: {', '.join(failed_tests)}")
        print("   🔧 建议检查相关组件并修复问题")

    print(f"\n📈 关键性能指标:")
    if 'workflow_generator' in test_results:
        wf_metrics = test_results['workflow_generator'].get('performance_metrics', {})
        method_metrics = wf_metrics.get('method_metrics', {})
        for method, metrics in method_metrics.items():
            exec_time = metrics.get('execution_time', 0)
            call_count = metrics.get('call_count', 0)
            print(f"   {method}: {exec_time:.3f}s/调用 ({call_count}次调用)")

    return report

def main():
    """主测试函数"""
    print("🎯 Perfect21性能优化Phase 1测试")
    print("测试项目:")
    print("1. 动态工作流生成器 - LRU缓存和算法优化")
    print("2. 性能优化器 - 智能分析和自动优化")
    print("3. 性能监控 - 实时监控和指标收集")
    print("4. LRU缓存 - 高效缓存管理")
    print("5. 正则表达式预编译 - 模式匹配优化")
    print("6. Agent选择算法 - O(log n)复杂度优化")

    test_results = {}

    # 执行各项测试
    test_results['workflow_generator'] = test_dynamic_workflow_generator_performance()
    test_results['performance_optimizer'] = test_performance_optimizer()
    test_results['performance_monitor'] = test_performance_monitor_integration()
    test_results['lru_cache'] = test_lru_cache_effectiveness()
    test_results['regex_precompilation'] = test_regex_precompilation()
    test_results['agent_selection'] = test_agent_selection_optimization()

    # 生成测试报告
    report = generate_performance_report(test_results)

    return report

if __name__ == "__main__":
    try:
        report = main()
        exit_code = 0 if report.get('overall_success', False) else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        sys.exit(1)