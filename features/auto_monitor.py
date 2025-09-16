#!/usr/bin/env python3
"""
Perfect21 自动监控和状态显示系统
在用户工作时自动显示Perfect21状态，无需手动输入命令
"""

import os
import time
import threading
import signal
import sys
from typing import Dict, Any
import subprocess
import json

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.parallel_monitor import get_global_monitor
from features.development_orchestrator import get_global_orchestrator

class AutoMonitor:
    """自动监控系统"""

    def __init__(self):
        self.is_running = False
        self.monitor_thread = None
        self.status_file = "/tmp/perfect21_status.json"
        self.last_activity = time.time()

    def start_auto_monitoring(self):
        """启动自动监控"""
        if self.is_running:
            return

        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        # 创建状态指示文件
        self._update_status_file("Perfect21 自动监控已启动")

    def stop_auto_monitoring(self):
        """停止自动监控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)

        # 清理状态文件
        if os.path.exists(self.status_file):
            os.remove(self.status_file)

    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                # 检查Perfect21活动状态
                monitor = get_global_monitor()
                orchestrator = get_global_orchestrator()

                # 获取当前状态
                status = {
                    "timestamp": time.time(),
                    "active_tasks": len(monitor.active_tasks),
                    "total_tasks": len(monitor.tasks),
                    "execution_mode": monitor.detect_execution_mode().value,
                    "recent_activity": self._get_recent_activity(),
                    "perfect21_ready": True
                }

                # 更新状态文件
                self._update_status_file(status)

                # 如果有活动任务，显示实时状态
                if monitor.active_tasks:
                    self._show_activity_banner()

                time.sleep(2)  # 每2秒更新一次

            except Exception as e:
                # 静默处理错误，不中断监控
                pass

    def _update_status_file(self, status):
        """更新状态文件"""
        try:
            with open(self.status_file, 'w') as f:
                if isinstance(status, str):
                    json.dump({"message": status, "timestamp": time.time()}, f)
                else:
                    json.dump(status, f, indent=2)
        except:
            pass

    def _get_recent_activity(self):
        """获取最近活动"""
        try:
            orchestrator = get_global_orchestrator()
            if orchestrator.task_history:
                recent = orchestrator.task_history[-1]
                return {
                    "last_task": recent['task']['description'][:50] + "...",
                    "success": recent['result'].get('success', False),
                    "agents_used": recent['result'].get('agents_count', 0)
                }
        except:
            pass
        return None

    def _show_activity_banner(self):
        """显示活动横幅"""
        try:
            monitor = get_global_monitor()
            running_tasks = [t for t in monitor.active_tasks.values()
                           if hasattr(t, 'status') and t.status.value == 'running']

            if running_tasks:
                print(f"\r🚀 Perfect21 执行中: {len(running_tasks)}个Agent正在工作... ", end="", flush=True)
        except:
            pass

class AutoStarter:
    """自动启动器"""

    def __init__(self):
        self.perfect21_indicator = os.path.expanduser("~/.perfect21_active")

    def activate_perfect21_mode(self):
        """激活Perfect21模式"""
        # 创建激活指示文件
        with open(self.perfect21_indicator, 'w') as f:
            f.write(f"Perfect21 activated at {time.time()}\n")

        # 修改shell提示符显示Perfect21状态
        self._setup_shell_prompt()

        # 启动自动监控
        auto_monitor = AutoMonitor()
        auto_monitor.start_auto_monitoring()

        print("🚀 Perfect21 已激活为默认开发环境")
        print("💡 现在所有开发任务都会自动使用Perfect21多Agent协作")

        return auto_monitor

    def deactivate_perfect21_mode(self):
        """停用Perfect21模式"""
        if os.path.exists(self.perfect21_indicator):
            os.remove(self.perfect21_indicator)
        print("🔄 Perfect21模式已停用")

    def is_perfect21_active(self):
        """检查Perfect21是否激活"""
        return os.path.exists(self.perfect21_indicator)

    def _setup_shell_prompt(self):
        """设置shell提示符"""
        try:
            # 为不同shell设置提示符
            shell_configs = [
                os.path.expanduser("~/.bashrc"),
                os.path.expanduser("~/.zshrc"),
                os.path.expanduser("~/.profile")
            ]

            prompt_line = 'export PS1="🚀[Perfect21] $PS1"'

            for config_file in shell_configs:
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        content = f.read()

                    if 'Perfect21' not in content:
                        with open(config_file, 'a') as f:
                            f.write(f'\n# Perfect21 prompt\n{prompt_line}\n')
        except:
            pass

class SmartDevWrapper:
    """智能开发包装器 - 拦截常见开发命令并自动使用Perfect21"""

    def __init__(self):
        self.wrapper_commands = {
            'implement': self._handle_implement,
            'fix': self._handle_fix,
            'optimize': self._handle_optimize,
            'test': self._handle_test,
            'deploy': self._handle_deploy,
            'design': self._handle_design
        }

    def setup_command_wrappers(self):
        """设置命令包装器"""
        wrapper_dir = os.path.expanduser("~/.perfect21/bin")
        os.makedirs(wrapper_dir, exist_ok=True)

        # 创建包装命令
        for cmd_name, handler in self.wrapper_commands.items():
            wrapper_script = f"""#!/bin/bash
# Perfect21 智能开发包装器
echo "🚀 Perfect21 自动处理: {cmd_name} $*"
python3 {os.path.abspath(__file__)} {cmd_name} "$@"
"""
            wrapper_path = os.path.join(wrapper_dir, cmd_name)
            with open(wrapper_path, 'w') as f:
                f.write(wrapper_script)
            os.chmod(wrapper_path, 0o755)

        # 添加到PATH
        self._add_to_path(wrapper_dir)

        print(f"🔧 Perfect21智能命令已设置: {', '.join(self.wrapper_commands.keys())}")

    def _add_to_path(self, wrapper_dir):
        """添加到PATH"""
        shell_configs = [
            os.path.expanduser("~/.bashrc"),
            os.path.expanduser("~/.zshrc")
        ]

        path_line = f'export PATH="{wrapper_dir}:$PATH"'

        for config_file in shell_configs:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()

                if wrapper_dir not in content:
                    with open(config_file, 'a') as f:
                        f.write(f'\n# Perfect21 智能命令\n{path_line}\n')

    def _handle_implement(self, args):
        """处理 implement 命令"""
        task_desc = " ".join(args)
        return self._call_perfect21(f"实现{task_desc}", "api_development")

    def _handle_fix(self, args):
        """处理 fix 命令"""
        task_desc = " ".join(args)
        return self._call_perfect21(f"修复{task_desc}", "bug_fix")

    def _handle_optimize(self, args):
        """处理 optimize 命令"""
        task_desc = " ".join(args)
        return self._call_perfect21(f"优化{task_desc}", "performance_optimization")

    def _handle_test(self, args):
        """处理 test 命令"""
        task_desc = " ".join(args)
        return self._call_perfect21(f"测试{task_desc}", "frontend_feature")

    def _handle_deploy(self, args):
        """处理 deploy 命令"""
        task_desc = " ".join(args)
        return self._call_perfect21(f"部署{task_desc}", "devops_setup")

    def _handle_design(self, args):
        """处理 design 命令"""
        task_desc = " ".join(args)
        return self._call_perfect21(f"设计{task_desc}", "microservice")

    def _call_perfect21(self, description, template):
        """调用Perfect21"""
        cmd = [
            "python3",
            f"{os.path.dirname(__file__)}/../main/cli.py",
            "develop",
            description,
            "--template",
            template
        ]

        print(f"🚀 Perfect21自动执行: {description}")
        return subprocess.run(cmd)

def main():
    """主函数 - 处理命令行调用"""
    if len(sys.argv) < 2:
        # 启动自动监控模式
        auto_starter = AutoStarter()

        if "--activate" in sys.argv:
            auto_monitor = auto_starter.activate_perfect21_mode()

            # 设置智能命令包装器
            wrapper = SmartDevWrapper()
            wrapper.setup_command_wrappers()

            try:
                # 保持运行直到收到信号
                def signal_handler(signum, frame):
                    print("\n🔄 正在停止Perfect21自动监控...")
                    auto_monitor.stop_auto_monitoring()
                    auto_starter.deactivate_perfect21_mode()
                    sys.exit(0)

                signal.signal(signal.SIGINT, signal_handler)
                signal.signal(signal.SIGTERM, signal_handler)

                print("🔍 Perfect21自动监控运行中... (Ctrl+C停止)")
                while True:
                    time.sleep(1)

            except KeyboardInterrupt:
                auto_monitor.stop_auto_monitoring()
                auto_starter.deactivate_perfect21_mode()

        elif "--deactivate" in sys.argv:
            auto_starter.deactivate_perfect21_mode()

        elif "--status" in sys.argv:
            if auto_starter.is_perfect21_active():
                print("🚀 Perfect21 当前已激活")
                try:
                    with open("/tmp/perfect21_status.json", 'r') as f:
                        status = json.load(f)
                    print(f"📊 状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
                except:
                    print("📊 状态文件不存在")
            else:
                print("💤 Perfect21 当前未激活")

        else:
            print("🚀 Perfect21 自动监控系统")
            print("使用方法:")
            print("  python3 features/auto_monitor.py --activate    # 激活Perfect21模式")
            print("  python3 features/auto_monitor.py --deactivate  # 停用Perfect21模式")
            print("  python3 features/auto_monitor.py --status      # 查看状态")

    else:
        # 处理智能命令包装器调用
        wrapper = SmartDevWrapper()
        command = sys.argv[1]
        args = sys.argv[2:]

        if command in wrapper.wrapper_commands:
            handler = wrapper.wrapper_commands[command]
            handler(args)

if __name__ == "__main__":
    main()