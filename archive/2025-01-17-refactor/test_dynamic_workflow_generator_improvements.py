#!/usr/bin/env python3
"""
测试动态工作流生成器的改进效果
验证agent选择问题的修复情况
"""

import sys
import os
import logging
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from features.dynamic_workflow_generator import DynamicWorkflowGenerator, ComplexityLevel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_agent_selection_improvements():
    """测试agent选择改进"""
    print("🧪 测试动态工作流生成器 - Agent选择改进")
    print("=" * 60)

    generator = DynamicWorkflowGenerator()

    # 测试用例：不同复杂度和领域的任务
    test_cases = [
        {
            "name": "用户认证系统",
            "request": "开发一个完整的用户认证系统，包括登录、注册、密码重置、JWT token管理",
            "expected_min_agents": 3,
            "expected_domains": ["security", "backend", "api"]
        },
        {
            "name": "电商购物车",
            "request": "实现电商平台的购物车功能，支持商品添加、删除、数量修改、价格计算",
            "expected_min_agents": 3,
            "expected_domains": ["backend", "frontend", "business"]
        },
        {
            "name": "性能优化",
            "request": "优化网站首页加载速度，提升用户体验",
            "expected_min_agents": 2,
            "expected_domains": ["performance", "frontend"]
        },
        {
            "name": "微服务架构",
            "request": "设计并实现微服务架构，包括服务发现、配置中心、API网关",
            "expected_min_agents": 4,
            "expected_domains": ["architecture", "devops", "api"]
        },
        {
            "name": "移动端应用",
            "request": "开发一个社交聊天的移动端应用，支持实时消息、文件传输",
            "expected_min_agents": 3,
            "expected_domains": ["mobile", "frontend", "backend"]
        },
        {
            "name": "数据分析系统",
            "request": "构建数据分析平台，包括数据收集、ETL处理、可视化报表",
            "expected_min_agents": 4,
            "expected_domains": ["data", "backend", "frontend"]
        },
        {
            "name": "边界测试-简单任务",
            "request": "修复一个简单的bug",
            "expected_min_agents": 2,
            "expected_domains": ["debug", "test"]
        },
        {
            "name": "边界测试-复杂任务",
            "request": "构建完整的企业级ERP系统，包括财务、人事、库存、销售、客户管理等模块",
            "expected_min_agents": 4,
            "expected_domains": ["enterprise", "fullstack", "business"]
        }
    ]

    results = []

    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 测试用例 {i}: {case['name']}")
        print(f"请求: {case['request']}")
        print("-" * 50)

        try:
            # 生成工作流
            workflow = generator.generate_workflow(case['request'])

            # 分析结果
            analysis_result = {
                "case_name": case['name'],
                "request": case['request'],
                "selected_agents_count": len(workflow.selected_agents),
                "selected_agents": workflow.selected_agents,
                "complexity": workflow.analysis.complexity.value,
                "domain": workflow.analysis.domain,
                "estimated_time": workflow.estimated_time,
                "stages_count": len(workflow.stages),
                "execution_mode": workflow.execution_mode.value,
                "meets_min_requirement": len(workflow.selected_agents) >= case['expected_min_agents']
            }

            results.append(analysis_result)

            # 输出结果
            print(f"✅ 分析结果:")
            print(f"   - 复杂度: {workflow.analysis.complexity.value}")
            print(f"   - 领域: {workflow.analysis.domain}")
            print(f"   - 选中Agents: {len(workflow.selected_agents)}个")
            print(f"   - 最小要求: {case['expected_min_agents']}个")
            print(f"   - 满足要求: {'✅' if analysis_result['meets_min_requirement'] else '❌'}")

            print(f"\n🤖 选中的Agents:")
            for agent in workflow.selected_agents:
                print(f"   - @{agent}")

            print(f"\n⚡ 执行计划:")
            print(f"   - 执行模式: {workflow.execution_mode.value}")
            print(f"   - 阶段数: {len(workflow.stages)}")
            print(f"   - 预估时间: {workflow.estimated_time}小时")

            for j, stage in enumerate(workflow.stages, 1):
                print(f"   阶段{j}: {stage.name} [{stage.mode.value}]")
                for agent in stage.agents:
                    print(f"     └─ @{agent}")
                if stage.sync_point:
                    print(f"     🔴 同步点")
                if stage.quality_gate:
                    print(f"     ✅ 质量门: {stage.quality_gate}")

        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            analysis_result = {
                "case_name": case['name'],
                "error": str(e),
                "meets_min_requirement": False
            }
            results.append(analysis_result)

    # 生成测试报告
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    total_cases = len(test_cases)
    passed_cases = sum(1 for r in results if r.get('meets_min_requirement', False))

    print(f"总测试用例: {total_cases}")
    print(f"通过用例: {passed_cases}")
    print(f"通过率: {passed_cases/total_cases*100:.1f}%")

    # Agent选择统计
    all_agents = set()
    complexity_stats = {"simple": 0, "medium": 0, "complex": 0}

    for result in results:
        if 'selected_agents' in result:
            all_agents.update(result['selected_agents'])
            complexity_stats[result['complexity']] += 1

    print(f"\n🤖 Agent使用统计:")
    print(f"涉及Agent数: {len(all_agents)}")
    print(f"复杂度分布: {complexity_stats}")

    # 详细结果表格
    print(f"\n📋 详细结果:")
    print(f"{'用例名称':<15} {'Agents数':<8} {'复杂度':<8} {'领域':<10} {'时间(h)':<8} {'通过':<6}")
    print("-" * 70)

    for result in results:
        if 'selected_agents_count' in result:
            print(f"{result['case_name'][:14]:<15} "
                  f"{result['selected_agents_count']:<8} "
                  f"{result['complexity']:<8} "
                  f"{result['domain'][:9]:<10} "
                  f"{result['estimated_time']:<8} "
                  f"{'✅' if result['meets_min_requirement'] else '❌':<6}")

    return results

def test_performance_improvements():
    """测试性能改进"""
    print("\n🚀 测试性能改进")
    print("=" * 40)

    import time

    generator = DynamicWorkflowGenerator()

    # 测试大量请求的处理速度
    test_requests = [
        "开发API接口",
        "实现用户认证",
        "优化数据库性能",
        "部署应用到云端",
        "编写单元测试",
        "设计前端界面",
        "实现支付功能",
        "添加日志监控",
        "安全漏洞扫描",
        "数据备份恢复"
    ] * 10  # 100个请求

    start_time = time.time()

    for i, request in enumerate(test_requests):
        workflow = generator.generate_workflow(request)
        if (i + 1) % 20 == 0:
            print(f"处理进度: {i + 1}/{len(test_requests)}")

    end_time = time.time()
    duration = end_time - start_time

    print(f"\n⏱️ 性能测试结果:")
    print(f"总请求数: {len(test_requests)}")
    print(f"总耗时: {duration:.2f}秒")
    print(f"平均每请求: {duration/len(test_requests)*1000:.1f}毫秒")
    print(f"吞吐量: {len(test_requests)/duration:.1f} 请求/秒")

def test_edge_cases():
    """测试边界情况"""
    print("\n🔬 测试边界情况")
    print("=" * 40)

    generator = DynamicWorkflowGenerator()

    edge_cases = [
        "",  # 空字符串
        "   ",  # 只有空格
        "abcdefg",  # 无意义字符串
        "Hello World",  # 英文但无技术含义
        "我要做一个东西",  # 模糊需求
        "!" * 100,  # 特殊字符
        "a" * 1000,  # 超长字符串
        "开发" * 50,  # 重复关键词
    ]

    for i, case in enumerate(edge_cases, 1):
        print(f"\n边界用例 {i}: '{case[:50]}{'...' if len(case) > 50 else ''}'")

        try:
            workflow = generator.generate_workflow(case)
            print(f"✅ 处理成功 - {len(workflow.selected_agents)}个agents, 复杂度: {workflow.analysis.complexity.value}")
        except Exception as e:
            print(f"❌ 处理失败: {str(e)}")

if __name__ == "__main__":
    try:
        # 执行所有测试
        print("🎯 Perfect21 动态工作流生成器改进测试")
        print("=" * 60)

        # 1. Agent选择改进测试
        results = test_agent_selection_improvements()

        # 2. 性能改进测试
        test_performance_improvements()

        # 3. 边界情况测试
        test_edge_cases()

        print("\n🎉 所有测试完成!")

    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()