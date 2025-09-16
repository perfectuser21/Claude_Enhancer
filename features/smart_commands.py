#!/usr/bin/env python3
"""
Perfect21 智能开发命令系统
创建自然语言开发命令，自动调用Perfect21
"""

import os
import sys
import subprocess
import asyncio
from typing import Dict, List

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class SmartCommands:
    """智能开发命令系统"""

    def __init__(self):
        self.command_mappings = {
            # 开发命令
            'build': ('构建项目', 'devops_setup'),
            'create': ('创建功能', 'api_development'),
            'make': ('实现功能', 'api_development'),
            'add': ('添加功能', 'frontend_feature'),
            'implement': ('实现', 'api_development'),
            'develop': ('开发', 'api_development'),

            # 修复命令
            'fix': ('修复', 'bug_fix'),
            'repair': ('修复', 'bug_fix'),
            'debug': ('调试', 'bug_fix'),
            'solve': ('解决', 'bug_fix'),

            # 优化命令
            'optimize': ('优化', 'performance_optimization'),
            'improve': ('改进', 'performance_optimization'),
            'enhance': ('增强', 'performance_optimization'),
            'speed': ('加速', 'performance_optimization'),

            # 测试命令
            'test': ('测试', 'frontend_feature'),
            'check': ('检查', 'security_audit'),
            'verify': ('验证', 'frontend_feature'),
            'validate': ('验证', 'security_audit'),

            # 部署命令
            'deploy': ('部署', 'devops_setup'),
            'release': ('发布', 'devops_setup'),
            'ship': ('发布', 'devops_setup'),

            # 设计命令
            'design': ('设计', 'microservice'),
            'architect': ('架构设计', 'microservice'),
            'plan': ('规划', 'microservice'),

            # 数据命令
            'data': ('数据处理', 'data_pipeline'),
            'etl': ('数据处理', 'data_pipeline'),
            'pipeline': ('数据管道', 'data_pipeline'),

            # AI/ML命令
            'ml': ('机器学习', 'ml_development'),
            'ai': ('AI开发', 'ml_development'),
            'model': ('模型开发', 'ml_development'),
            'train': ('训练模型', 'ml_development'),

            # 移动开发
            'mobile': ('移动开发', 'mobile_app'),
            'app': ('应用开发', 'mobile_app'),
            'ios': ('iOS开发', 'mobile_app'),
            'android': ('Android开发', 'mobile_app'),

            # 前端命令
            'ui': ('界面开发', 'frontend_feature'),
            'frontend': ('前端开发', 'frontend_feature'),
            'component': ('组件开发', 'frontend_feature'),
            'page': ('页面开发', 'frontend_feature'),

            # 后端命令
            'api': ('API开发', 'api_development'),
            'backend': ('后端开发', 'api_development'),
            'server': ('服务器开发', 'api_development'),
            'service': ('服务开发', 'microservice'),

            # 安全命令
            'secure': ('安全加固', 'security_audit'),
            'audit': ('安全审计', 'security_audit'),
            'security': ('安全检查', 'security_audit')
        }

    def setup_smart_commands(self):
        """设置智能命令"""
        # 创建命令目录
        cmd_dir = os.path.expanduser("~/.perfect21/commands")
        os.makedirs(cmd_dir, exist_ok=True)

        # 为每个命令创建可执行文件
        for cmd, (description, template) in self.command_mappings.items():
            self._create_command_script(cmd_dir, cmd, description, template)

        # 添加到PATH
        self._update_path(cmd_dir)

        print(f"🚀 已创建 {len(self.command_mappings)} 个智能开发命令")
        print("📝 示例使用:")
        print("  implement user login          → Perfect21 API开发")
        print("  fix database performance      → Perfect21 Bug修复")
        print("  optimize query speed          → Perfect21 性能优化")
        print("  design microservice           → Perfect21 微服务设计")

    def _create_command_script(self, cmd_dir: str, cmd: str, description: str, template: str):
        """创建命令脚本"""
        script_content = f'''#!/bin/bash
# Perfect21 智能命令: {cmd}
# 自动使用模板: {template}

if [ $# -eq 0 ]; then
    echo "🚀 Perfect21 智能命令: {cmd}"
    echo "用法: {cmd} <描述>"
    echo "示例: {cmd} user authentication system"
    exit 1
fi

TASK_DESC="{description} $*"
PERFECT21_PATH="{os.path.dirname(__file__)}/../main/cli.py"

echo "🚀 Perfect21自动执行: $TASK_DESC"
echo "📋 使用模板: {template}"
echo "🤖 启动多Agent协作..."

python3 "$PERFECT21_PATH" develop "$TASK_DESC" --template {template}
'''

        script_path = os.path.join(cmd_dir, cmd)
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)

    def _update_path(self, cmd_dir: str):
        """更新PATH环境变量"""
        shell_configs = [
            os.path.expanduser("~/.bashrc"),
            os.path.expanduser("~/.zshrc"),
            os.path.expanduser("~/.profile")
        ]

        path_export = f'export PATH="{cmd_dir}:$PATH"'
        comment = "# Perfect21 智能开发命令"

        for config_file in shell_configs:
            if os.path.exists(config_file):
                try:
                    # 读取现有内容
                    with open(config_file, 'r') as f:
                        content = f.read()

                    # 如果还没有添加，则添加
                    if cmd_dir not in content:
                        with open(config_file, 'a') as f:
                            f.write(f'\n{comment}\n{path_export}\n')
                        print(f"✅ 已更新 {config_file}")
                except Exception as e:
                    print(f"⚠️  无法更新 {config_file}: {e}")

    def create_perfect21_alias(self):
        """创建Perfect21别名和快捷方式"""
        aliases = {
            'p21': 'python3 main/cli.py',
            'perfect': 'python3 main/cli.py',
            'dev': 'python3 main/cli.py develop',
            'pdev': 'python3 main/cli.py develop',
            'pmon': 'python3 main/cli.py monitor --live',
            'ptpl': 'python3 main/cli.py templates list',
            'phelp': 'python3 main/cli.py templates recommend'
        }

        shell_configs = [
            os.path.expanduser("~/.bashrc"),
            os.path.expanduser("~/.zshrc")
        ]

        for config_file in shell_configs:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()

                    # 添加别名
                    if 'Perfect21 aliases' not in content:
                        with open(config_file, 'a') as f:
                            f.write('\n# Perfect21 aliases\n')
                            for alias, command in aliases.items():
                                f.write(f'alias {alias}="{command}"\n')
                        print(f"✅ 已添加Perfect21别名到 {config_file}")
                except Exception as e:
                    print(f"⚠️  无法更新 {config_file}: {e}")

        print("🔧 已创建Perfect21快捷别名:")
        for alias, command in aliases.items():
            print(f"  {alias} → {command}")

def create_auto_dev_function():
    """创建自动开发函数"""
    function_content = '''
# Perfect21 自动开发函数
auto_dev() {
    if [ $# -eq 0 ]; then
        echo "🚀 Perfect21 自动开发"
        echo "用法: auto_dev <任务描述>"
        echo "示例: auto_dev implement user login API"
        return 1
    fi

    local task_desc="$*"
    local perfect21_path="''' + os.path.dirname(__file__) + '''/../main/cli.py"

    echo "🚀 Perfect21自动分析任务: $task_desc"

    # 获取推荐模板
    local template=$(python3 "$perfect21_path" templates recommend "$task_desc" | grep "使用:" | head -1 | awk '{print $NF}')

    if [ -n "$template" ]; then
        echo "📋 推荐模板: $template"
        python3 "$perfect21_path" develop "$task_desc" --template "$template"
    else
        echo "🤖 使用智能Agent选择"
        python3 "$perfect21_path" develop "$task_desc"
    fi
}

# Perfect21 智能监控函数
auto_monitor() {
    echo "🔍 启动Perfect21自动监控..."
    python3 "''' + os.path.dirname(__file__) + '''/auto_monitor.py" --activate
}

# Perfect21 快速状态函数
p21status() {
    python3 "''' + os.path.dirname(__file__) + '''/auto_monitor.py" --status
}
'''

    shell_configs = [
        os.path.expanduser("~/.bashrc"),
        os.path.expanduser("~/.zshrc")
    ]

    for config_file in shell_configs:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    content = f.read()

                if 'auto_dev()' not in content:
                    with open(config_file, 'a') as f:
                        f.write('\n# Perfect21 自动开发函数\n')
                        f.write(function_content)
                    print(f"✅ 已添加自动开发函数到 {config_file}")
            except Exception as e:
                print(f"⚠️  无法更新 {config_file}: {e}")

    print("🎯 已创建自动开发函数:")
    print("  auto_dev <任务描述>  → 智能选择模板并执行")
    print("  auto_monitor         → 启动自动监控")
    print("  p21status           → 查看Perfect21状态")

def main():
    """主安装函数"""
    print("🚀 Perfect21 智能开发命令安装器")
    print("=" * 50)

    # 创建智能命令
    smart_commands = SmartCommands()
    smart_commands.setup_smart_commands()

    print()
    # 创建别名
    smart_commands.create_perfect21_alias()

    print()
    # 创建自动开发函数
    create_auto_dev_function()

    print()
    print("🎉 Perfect21智能开发环境安装完成！")
    print()
    print("📋 重新加载shell配置:")
    print("  source ~/.bashrc    # 或")
    print("  source ~/.zshrc")
    print()
    print("🚀 现在你可以使用:")
    print("  auto_dev implement user login     → 自动开发")
    print("  fix database performance          → 自动修复")
    print("  optimize query speed              → 自动优化")
    print("  design microservice architecture  → 自动设计")
    print("  dev <任务描述>                     → 快捷开发")
    print("  pmon                              → 实时监控")

if __name__ == "__main__":
    main()