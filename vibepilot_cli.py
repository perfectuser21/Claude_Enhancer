#!/usr/bin/env python3
"""
VibePilot V2 命令行版本
直接在服务器上使用，不依赖Web浏览器
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from main.vibepilot_v2 import VibePilotV2

class VibePilotCLI:
    def __init__(self):
        self.vibepilot = VibePilotV2()
        self.running = False

    async def start(self):
        """启动CLI界面"""
        print("🚁 VibePilot V2 命令行界面")
        print("=" * 50)

        await self.vibepilot.initialize()

        # 显示系统状态
        status = self.vibepilot.get_system_status()
        print(f"📊 系统状态: {'🟢 运行中' if status['is_running'] else '🔴 停止'}")
        print(f"🧠 AI池: Claude={status['ai_pool_status']['claude']['total']}")
        print(f"📁 工作空间: {status['workspace_stats']['total_workspaces']}个")

        print("\n💡 使用方法:")
        print("- 直接输入任务描述，我会自动执行")
        print("- 输入 'status' 查看系统状态")
        print("- 输入 'quit' 或 'exit' 退出")
        print("- 输入 'help' 查看帮助")
        print("=" * 50)

        self.running = True

        while self.running:
            try:
                # 获取用户输入
                user_input = input("\n💬 您: ").strip()

                if not user_input:
                    continue

                # 处理特殊命令
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("👋 再见！")
                    break
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                elif user_input.lower() == 'status':
                    await self.show_status()
                    continue

                # 处理普通任务
                print("🤖 处理中...")
                result = await self.vibepilot.chat(user_input)

                if result['success']:
                    print(f"\n✅ 任务完成!")

                    # 显示响应内容
                    if 'response' in result:
                        print("📝 响应:")
                        print("-" * 40)
                        print(result['response'])
                        print("-" * 40)

                    # 显示执行信息
                    if 'execution_time' in result:
                        print(f"⏱️ 执行时间: {result['execution_time']:.2f}秒")

                else:
                    print(f"\n❌ 处理失败: {result.get('error', '未知错误')}")

            except KeyboardInterrupt:
                print("\n\n👋 程序被中断，正在退出...")
                break
            except EOFError:
                print("\n\n👋 输入结束，正在退出...")
                break
            except Exception as e:
                print(f"\n❌ 异常: {e}")

        await self.vibepilot.shutdown()
        print("✅ VibePilot V2 已关闭")

    def show_help(self):
        """显示帮助信息"""
        help_text = """
🚁 VibePilot V2 命令行帮助

📋 基本命令:
  help          显示此帮助信息
  status        显示系统详细状态
  quit/exit     退出程序

💬 任务执行:
  直接输入任务描述，系统会自动:
  1. 分析任务类型和复杂度
  2. 选择合适的AI实例
  3. 调用Claude Code执行
  4. 返回执行结果

🎯 示例任务:
  "创建一个Python函数计算斐波那契数列"
  "分析当前目录的代码结构"
  "重构main.py文件"
  "生成单元测试"

✨ 特色功能:
  - 🧠 智能任务路由
  - ⚡ 并行AI实例管理
  - 📊 实时执行统计
  - 🔄 自动错误恢复
"""
        print(help_text)

    async def show_status(self):
        """显示系统状态"""
        status = self.vibepilot.get_system_status()

        print("\n📊 VibePilot V2 系统状态")
        print("=" * 40)
        print(f"系统状态: {'🟢 运行中' if status['is_running'] else '🔴 停止'}")
        print(f"任务计数: {status['task_counter']}")

        # AI池状态
        ai_status = status['ai_pool_status']
        print(f"\n🧠 AI实例池:")
        print(f"  Claude: {ai_status['claude']['idle']}空闲 / {ai_status['claude']['busy']}忙碌 / {ai_status['claude']['total']}总计")
        print(f"  Codex:  {ai_status['codex']['idle']}空闲 / {ai_status['codex']['busy']}忙碌 / {ai_status['codex']['total']}总计")

        # 工作空间状态
        ws_status = status['workspace_stats']
        print(f"\n📁 工作空间:")
        print(f"  总数: {ws_status['total_workspaces']}")
        print(f"  活跃: {ws_status['active_workspaces']}")
        print(f"  归档: {ws_status['archived_workspaces']}")

        # 执行统计
        claude_stats = status['claude_executor_stats']
        if claude_stats['total_executions'] > 0:
            print(f"\n⚡ Claude执行统计:")
            print(f"  执行次数: {claude_stats['total_executions']}")
            print(f"  成功率: {claude_stats['success_rate']:.1%}")
            print(f"  平均耗时: {claude_stats['avg_execution_time']:.2f}秒")

async def main():
    """主函数"""
    cli = VibePilotCLI()
    await cli.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()