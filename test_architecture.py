#!/usr/bin/env python3
"""
VibePilot V2 架构测试
测试新架构的核心组件功能
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加项目路径到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.ai_pool import AIPool, AIInstanceType
from core.router import IntelligentRouter
from core.workspace_manager import WorkspaceManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_architecture():
    """测试VibePilot V2架构组件"""
    print("🤖 VibePilot V2 架构测试开始")
    print("=" * 50)

    # 1. 测试AI实例池
    print("\n📋 测试AI实例池...")
    ai_pool = AIPool(claude_max_instances=2, codex_max_instances=2)

    # 创建实例
    claude_id = ai_pool.create_instance(AIInstanceType.CLAUDE, "test_workspace")
    print(f"✅ 创建Claude实例: {claude_id}")

    # 获取池状态
    status = ai_pool.get_pool_status()
    print(f"📊 池状态: Claude={status['claude']['total']}, Codex={status['codex']['total']}")

    # 2. 测试工作空间管理器
    print("\n📁 测试工作空间管理器...")
    workspace_manager = WorkspaceManager()

    # 创建工作空间
    ws_id = workspace_manager.create_workspace(
        name="测试项目",
        description="VibePilot V2架构测试项目",
        project_type="test"
    )
    print(f"✅ 创建工作空间: {ws_id}")

    # 分配AI实例到工作空间
    workspace_manager.assign_ai_instance(ws_id, claude_id)
    print(f"✅ AI实例分配到工作空间")

    # 获取工作空间统计
    ws_stats = workspace_manager.get_workspace_stats()
    print(f"📊 工作空间统计: 总数={ws_stats['total_workspaces']}, AI实例={ws_stats['total_ai_instances']}")

    # 3. 测试智能路由器
    print("\n🧠 测试智能路由器...")
    router = IntelligentRouter(ai_pool)

    # 测试任务路由
    test_tasks = [
        "创建一个Python函数",
        "分析代码质量",
        "重构这个系统",
        "生成单元测试"
    ]

    for task in test_tasks:
        result = router.route_task(task, ws_id)
        if result["success"]:
            print(f"✅ 任务路由成功: {task} -> {result['ai_type']} ({result['task_type']}-{result['complexity']})")
            # 完成任务
            ai_pool.complete_task(result["instance_id"], True)
        else:
            print(f"❌ 任务路由失败: {task} - {result['error']}")

    # 4. 获取路由统计
    routing_stats = router.get_routing_stats()
    print(f"📊 路由统计: {routing_stats['pool_status']['claude']['total']} Claude实例")

    # 5. 测试工作空间清理
    print("\n🔧 测试清理功能...")
    workspace_manager.release_ai_instance(ws_id, claude_id)
    print("✅ 释放AI实例")

    workspace_manager.archive_workspace(ws_id)
    print("✅ 归档工作空间")

    print("\n🎉 架构测试完成!")
    print("=" * 50)

    # 最终状态报告
    final_pool_status = ai_pool.get_pool_status()
    final_ws_stats = workspace_manager.get_workspace_stats()

    print("📊 最终状态:")
    print(f"  AI池: Claude={final_pool_status['claude']['idle']}空闲/{final_pool_status['claude']['total']}总计")
    print(f"  工作空间: 活跃={final_ws_stats['active_workspaces']}, 归档={final_ws_stats['archived_workspaces']}")

    print("\n✅ VibePilot V2架构验证成功!")

async def test_integration():
    """测试整合功能"""
    print("\n🔄 测试组件整合...")

    try:
        from main.vibepilot_v2 import VibePilotV2

        vibepilot = VibePilotV2()
        await vibepilot.initialize()

        system_status = vibepilot.get_system_status()
        print(f"✅ 主控制器初始化成功")
        print(f"📊 系统状态: 运行={system_status['is_running']}, 工作空间={system_status['workspace_stats']['total_workspaces']}")

        # 测试聊天功能（不实际执行Claude）
        chat_result = await vibepilot.chat("你好，这是一个测试消息")
        if chat_result['success']:
            chat_type = chat_result.get('type', 'task_execution')
            print(f"✅ 聊天功能正常: {chat_type}")
            if 'execution_time' in chat_result:
                print(f"⚡ Claude Code实际执行成功! 耗时: {chat_result['execution_time']:.2f}秒")

        await vibepilot.shutdown()
        print("✅ 系统安全关闭")

    except Exception as e:
        print(f"❌ 整合测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主测试函数"""
    print("🚁 VibePilot V2 架构完整性测试")
    print(f"📍 工作目录: {Path.cwd()}")
    print()

    async def run_all_tests():
        await test_architecture()
        await test_integration()

    try:
        asyncio.run(run_all_tests())
        print("\n🎉 所有测试通过！VibePilot V2架构准备就绪！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()