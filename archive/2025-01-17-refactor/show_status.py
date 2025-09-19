#!/usr/bin/env python3
"""
Perfect21 状态显示脚本
在终端中持续显示Perfect21工作状态
"""

import os
import sys
import time
import json
from datetime import datetime

def clear_screen():
    """清屏"""
    os.system('clear' if os.name == 'posix' else 'cls')

def show_perfect21_status():
    """显示Perfect21状态"""
    clear_screen()

    print("🚀 Perfect21 智能开发平台 - 实时状态")
    print("=" * 60)
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查Perfect21是否激活
    perfect21_indicator = os.path.expanduser("~/.perfect21_active")
    if os.path.exists(perfect21_indicator):
        print("✅ Perfect21模式: 已激活")

        # 读取活动状态
        try:
            with open("/tmp/perfect21_status.json", 'r') as f:
                status = json.load(f)

            print(f"🤖 活跃任务: {status.get('active_tasks', 0)}个")
            print(f"📊 总任务数: {status.get('total_tasks', 0)}个")
            print(f"⚡ 执行模式: {status.get('execution_mode', '待机')}")

            # 显示最近活动
            recent = status.get('recent_activity')
            if recent:
                print(f"📋 最近任务: {recent.get('last_task', 'N/A')}")
                print(f"✅ 执行状态: {'成功' if recent.get('success') else '失败'}")
                print(f"🤖 使用Agent: {recent.get('agents_used', 0)}个")

        except FileNotFoundError:
            print("⏳ Perfect21监控正在启动...")
        except Exception as e:
            print(f"⚠️  状态读取异常: {e}")
    else:
        print("💤 Perfect21模式: 未激活")
        print("💡 激活命令: python3 features/auto_monitor.py --activate")

    print()
    print("🔧 可用智能命令:")
    print("  auto_dev <任务描述>      → 智能开发")
    print("  implement <功能>        → 实现功能")
    print("  fix <问题>             → 修复问题")
    print("  optimize <目标>        → 性能优化")
    print("  design <架构>          → 架构设计")
    print("  dev <任务>             → 快捷开发")
    print("  pmon                   → 实时监控")

    print()
    print("📊 Perfect21统计:")

    # 统计智能命令数量
    cmd_dir = os.path.expanduser("~/.perfect21/commands")
    if os.path.exists(cmd_dir):
        cmd_count = len([f for f in os.listdir(cmd_dir) if os.path.isfile(os.path.join(cmd_dir, f))])
        print(f"  智能命令: {cmd_count}个")

    # 检查模板数量
    try:
        sys.path.append(os.path.dirname(__file__))
        from features.dev_templates_simple import DevTemplates
        templates = DevTemplates.get_all_templates()
        print(f"  开发模板: {len(templates)}个")

        categories = DevTemplates.list_by_category()
        print(f"  模板类别: {len(categories)}个")
    except:
        print("  开发模板: 加载中...")

    print()
    print("🎯 Perfect21 = 你的个人56人开发团队")
    print("💫 一个命令，多Agent协作，智能开发")

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--loop":
        # 循环显示模式
        try:
            while True:
                show_perfect21_status()
                print("\n⏱️  自动刷新中... (Ctrl+C退出)")
                time.sleep(3)
        except KeyboardInterrupt:
            clear_screen()
            print("👋 Perfect21状态监控已退出")
    else:
        # 单次显示模式
        show_perfect21_status()

if __name__ == "__main__":
    main()