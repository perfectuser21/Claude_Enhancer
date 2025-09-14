#!/usr/bin/env python3
"""
VibePilot V2 统一入口
使用新架构的AI管家和工作空间管理系统
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加项目路径到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from main.vibepilot_v2 import VibePilotV2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class VibePilotV2CLI:
    """VibePilot V2 命令行界面"""

    def __init__(self):
        self.vibepilot = VibePilotV2()

    async def run_command(self, args):
        """运行命令"""
        await self.vibepilot.initialize()

        if not args:
            print("VibePilot V2 - 新一代AI协作开发环境")
            print("使用方法: python vp_v2.py [命令] [参数]")
            print()
            print("命令:")
            print("  status     - 显示系统状态")
            print("  workspaces - 列出工作空间")
            print("  chat       - 启动聊天模式")
            print("  task <描述> - 执行任务")
            print("  help       - 显示帮助信息")
            return

        command = args[0].lower()

        if command == "status":
            await self.show_status()
        elif command == "workspaces":
            await self.show_workspaces()
        elif command == "chat":
            await self.start_chat_mode()
        elif command == "task":
            if len(args) < 2:
                print("错误: 请提供任务描述")
                return
            task_description = " ".join(args[1:])
            await self.execute_task(task_description)
        elif command == "help":
            await self.show_help()
        else:
            print(f"未知命令: {command}")
            print("使用 'python vp_v2.py help' 查看帮助")

    async def show_status(self):
        """显示系统状态"""
        status = self.vibepilot.get_system_status()

        print("🤖 VibePilot V2 系统状态")
        print("=" * 50)
        print(f"系统运行状态: {'✅ 运行中' if status['is_running'] else '❌ 停止'}")
        print(f"处理任务数量: {status['task_counter']}")
        print()

        # AI池状态
        ai_status = status['ai_pool_status']
        print("🧠 AI实例池状态:")
        print(f"  Claude: {ai_status['claude']['idle']}空闲 / {ai_status['claude']['busy']}忙碌 / {ai_status['claude']['total']}总计")
        print(f"  Codex:  {ai_status['codex']['idle']}空闲 / {ai_status['codex']['busy']}忙碌 / {ai_status['codex']['total']}总计")
        print()

        # 工作空间状态
        ws_status = status['workspace_stats']
        print("📁 工作空间状态:")
        print(f"  总工作空间: {ws_status['total_workspaces']}")
        print(f"  活跃空间: {ws_status['active_workspaces']}")
        print(f"  已归档: {ws_status['archived_workspaces']}")
        print()

        # Claude执行器状态
        claude_stats = status['claude_executor_stats']
        if claude_stats['total_executions'] > 0:
            print("⚡ Claude执行统计:")
            print(f"  执行次数: {claude_stats['total_executions']}")
            print(f"  成功率: {claude_stats['success_rate']:.1%}")
            print(f"  平均耗时: {claude_stats['avg_execution_time']:.2f}秒")

    async def show_workspaces(self):
        """显示工作空间列表"""
        workspaces = self.vibepilot.list_workspaces()

        print("📁 工作空间列表")
        print("=" * 50)

        if not workspaces:
            print("暂无工作空间")
            return

        for ws in workspaces:
            status_emoji = "🟢" if ws['status'] == 'active' else "🟡"
            print(f"{status_emoji} {ws['name']} ({ws['workspace_id']})")
            print(f"   类型: {ws['project_type']}")
            print(f"   描述: {ws['description']}")
            print(f"   AI实例: {len(ws['ai_instances'])}个")
            print(f"   路径: {ws['path']}")
            print()

    async def start_chat_mode(self):
        """启动聊天模式"""
        print("🤖 VibePilot V2 聊天模式")
        print("输入 'quit' 或 'exit' 退出")
        print("=" * 50)

        while True:
            try:
                user_input = input("\n💬 您: ").strip()

                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("👋 再见！")
                    break

                if not user_input:
                    continue

                print("🤖 处理中...")
                result = await self.vibepilot.chat(user_input)

                if result['success']:
                    print(f"🤖 VibePilot: {result['response']}")

                    # 如果有执行详情，显示简要信息
                    if 'execution_time' in result:
                        print(f"   ⏱️ 执行时间: {result['execution_time']:.2f}秒")
                else:
                    print(f"❌ 错误: {result.get('error', '未知错误')}")

            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 异常: {e}")

    async def execute_task(self, task_description):
        """执行单个任务"""
        print(f"🎯 执行任务: {task_description}")
        print("=" * 50)

        result = await self.vibepilot.process_task(task_description)

        if result['success']:
            print("✅ 任务执行成功!")
            print(f"🤖 AI类型: {result.get('ai_type', 'unknown')}")
            print(f"⏱️ 执行时间: {result.get('execution_time', 0):.2f}秒")
            print()
            print("📋 输出结果:")
            print("-" * 30)
            print(result['output'])
        else:
            print("❌ 任务执行失败!")
            print(f"错误: {result.get('error', '未知错误')}")

            if 'stderr' in result:
                print()
                print("错误详情:")
                print("-" * 30)
                print(result['stderr'])

    async def show_help(self):
        """显示帮助信息"""
        help_text = """
🤖 VibePilot V2 - 新一代AI协作开发环境

核心特性:
• 🧠 智能AI实例池管理 (Claude + Codex)
• 🎯 智能任务路由和执行
• 📁 多工作空间并行开发
• 💬 自然语言交互界面

命令详解:

基础命令:
  status                显示系统完整状态
  workspaces           列出所有工作空间
  help                 显示此帮助信息

交互模式:
  chat                 启动聊天交互模式
                      支持任务执行和普通对话

任务执行:
  task "任务描述"       直接执行单个任务

示例:
  python vp_v2.py task "创建一个Python函数计算斐波那契数列"
  python vp_v2.py task "分析当前目录的代码质量"
  python vp_v2.py task "重构main.py文件，提高可读性"

特色功能:
• 🔍 智能任务分析和AI选择
• ⚡ 并行AI实例管理
• 📊 执行性能统计
• 🛡️ 工作空间隔离
• 🔄 自动错误恢复

技术栈:
• Claude Code (非交互模式)
• 智能路由算法
• 异步任务处理
• 工作空间管理

开始使用:
  python vp_v2.py chat    # 推荐的交互方式
  python vp_v2.py status  # 检查系统状态
        """
        print(help_text)

async def main():
    """主函数"""
    try:
        cli = VibePilotV2CLI()
        await cli.run_command(sys.argv[1:])
        await cli.vibepilot.shutdown()
    except KeyboardInterrupt:
        print("\n👋 程序被中断，正在安全退出...")
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())