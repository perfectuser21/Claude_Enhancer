#!/usr/bin/env python3
"""
Perfect21 - 主程序入口
基于claude-code-unified-agents的智能开发助手
"""

import os
import sys
import asyncio
import argparse

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

from main.perfect21_controller import Perfect21Controller

class Perfect21CLI:
    """Perfect21命令行接口"""

    def __init__(self):
        self.controller = None

    async def initialize(self):
        """初始化Perfect21系统"""
        print("🚀 正在启动Perfect21...")
        self.controller = Perfect21Controller()
        await self.controller.initialize()

    async def execute_task(self, task_description: str, **options):
        """执行开发任务"""
        if not self.controller:
            await self.initialize()

        print(f"📝 任务: {task_description}")
        print("⚡ 正在处理...")

        result = await self.controller.process_task(
            task_description,
            context=options
        )

        if result['success']:
            print("✅ 任务完成!")
            if result.get('output'):
                print(f"📄 输出:\n{result['output']}")
        else:
            print("❌ 任务失败!")
            if result.get('error'):
                print(f"🚨 错误: {result['error']}")

        return result

    async def show_status(self):
        """显示系统状态"""
        if not self.controller:
            await self.initialize()

        status = self.controller.get_system_status()

        print("📊 Perfect21系统状态")
        print("=" * 50)
        print(f"系统运行: {'✅' if status['is_running'] else '❌'}")
        print(f"已处理任务: {status['task_counter']}")
        print(f"AI池状态: {status['ai_pool_status']}")
        print(f"工作空间: {status['workspace_stats']}")

    async def chat(self, message: str):
        """聊天模式"""
        if not self.controller:
            await self.initialize()

        result = await self.controller.chat(message)

        if result.get('type') == 'chat':
            print(f"💬 {result['response']}")
        else:
            return await self.execute_task(message)

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Perfect21 - 智能开发助手')
    parser.add_argument('task', nargs='?', help='开发任务描述')
    parser.add_argument('--status', action='store_true', help='显示系统状态')
    parser.add_argument('--chat', action='store_true', help='聊天模式')
    parser.add_argument('--workspace', help='指定工作空间')
    parser.add_argument('--timeout', type=int, default=300, help='任务超时时间(秒)')

    args = parser.parse_args()

    cli = Perfect21CLI()

    try:
        if args.status:
            await cli.show_status()
        elif args.chat:
            print("💬 Perfect21聊天模式 (输入'exit'退出)")
            while True:
                try:
                    message = input("\n🤖 您: ")
                    if message.lower() in ['exit', 'quit', '退出']:
                        break
                    await cli.chat(message)
                except KeyboardInterrupt:
                    break
        elif args.task:
            options = {
                'workspace_id': args.workspace,
                'timeout': args.timeout
            }
            await cli.execute_task(args.task, **options)
        else:
            print("🎯 Perfect21 - 智能开发助手")
            print("\n使用方法:")
            print("  ./vp.py '开发任务描述'")
            print("  ./vp.py --status")
            print("  ./vp.py --chat")
            print("\n示例:")
            print("  ./vp.py '创建用户登录API接口'")
            print("  ./vp.py '重构支付系统模块'")
            print("  ./vp.py '优化数据库查询性能'")

    except Exception as e:
        print(f"❌ 错误: {e}")
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())