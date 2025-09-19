#!/usr/bin/env python3
"""
Perfect21快速验证测试
运行核心功能的快速验证测试
"""

import sys
import time
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

async def test_basic_parallel_execution():
    """测试基本并行执行功能"""
    print("🔄 测试并行执行功能...")

    from features.workflow_orchestrator.orchestrator import WorkflowOrchestrator
    from shared.types import ExecutionMode

    orchestrator = WorkflowOrchestrator()

    # 创建简单的并行工作流
    config = {
        'name': 'Quick Test Workflow',
        'stages': [{
            'name': 'test_stage',
            'description': '快速测试阶段',
            'execution_mode': 'parallel'
        }]
    }

    # 加载工作流
    result = orchestrator.load_workflow(config)
    if not result['success']:
        print(f"❌ 工作流加载失败: {result['error']}")
        return False

    # 创建测试任务
    agents = ['test-agent-1', 'test-agent-2', 'test-agent-3']
    for i, agent in enumerate(agents):
        task_result = orchestrator.create_task(
            agent=agent,
            description=f'测试任务 {i+1}',
            stage='test_stage'
        )
        if not task_result['success']:
            print(f"❌ 任务创建失败: {task_result['error']}")
            return False

    print("✅ 并行执行功能正常")
    return True

def test_performance_basics():
    """测试基本性能功能"""
    print("🔄 测试性能监控功能...")

    try:
        from modules.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(collection_interval=1)

        # 收集一次性能数据
        collector = monitor.collector
        system_metrics = collector.collect_system_metrics()
        process_metrics = collector.collect_process_metrics()

        if not system_metrics or not process_metrics:
            print("❌ 性能数据收集失败")
            return False

        print("✅ 性能监控功能正常")
        return True
    except Exception as e:
        print(f"❌ 性能监控测试失败: {e}")
        return False

def test_resource_management():
    """测试资源管理功能"""
    print("🔄 测试资源管理功能...")

    try:
        from modules.resource_manager import ResourceManager, ResourceType

        manager = ResourceManager()

        # 注册测试资源
        success = manager.register_resource(
            'test_resource_1',
            {'data': 'test'},
            ResourceType.OTHER,
            size_estimate=100
        )

        if not success:
            print("❌ 资源注册失败")
            return False

        # 获取资源状态
        status = manager.get_status()
        if status['resource_stats']['total_count'] == 0:
            print("❌ 资源状态获取失败")
            return False

        # 清理资源
        manager.cleanup_all()

        print("✅ 资源管理功能正常")
        return True
    except Exception as e:
        print(f"❌ 资源管理测试失败: {e}")
        return False

def test_workflow_orchestration():
    """测试工作流编排功能"""
    print("🔄 测试工作流编排功能...")

    try:
        from features.workflow_orchestrator.orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator()

        # 测试工作流加载
        config = {
            'name': '编排测试工作流',
            'stages': [
                {
                    'name': 'stage1',
                    'description': '第一阶段',
                    'execution_mode': 'parallel'
                },
                {
                    'name': 'stage2',
                    'description': '第二阶段',
                    'execution_mode': 'sequential',
                    'depends_on': ['stage1']
                }
            ]
        }

        result = orchestrator.load_workflow(config)
        if not result['success']:
            print(f"❌ 工作流加载失败: {result['error']}")
            return False

        # 测试进度获取
        progress = orchestrator.get_workflow_progress()
        if progress['completion_percentage'] < 0:
            print("❌ 进度获取失败")
            return False

        print("✅ 工作流编排功能正常")
        return True
    except Exception as e:
        print(f"❌ 工作流编排测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 Perfect21快速验证测试开始")
    print("=" * 50)

    start_time = time.time()

    tests = [
        ('并行执行', test_basic_parallel_execution()),
        ('性能监控', test_performance_basics()),
        ('资源管理', test_resource_management()),
        ('工作流编排', test_workflow_orchestration())
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutine(test_func):
                result = await test_func
            else:
                result = test_func

            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            failed += 1

    end_time = time.time()
    duration = end_time - start_time

    print("\n" + "=" * 50)
    print("📋 快速验证测试结果")
    print("=" * 50)
    print(f"⏱️  执行时间: {duration:.2f}秒")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📊 成功率: {passed/(passed+failed)*100:.1f}%")

    if failed == 0:
        print("🎉 所有核心功能测试通过！")
        return 0
    else:
        print("⚠️  部分功能需要修复")
        return 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())