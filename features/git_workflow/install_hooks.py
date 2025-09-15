#!/usr/bin/env python3
"""
Git Hooks安装器
自动安装Perfect21 Git工作流钩子，实现真正的Git自动化
"""

import os
import sys
import stat
import subprocess
from pathlib import Path

class GitHooksInstaller:
    """Git钩子安装器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.git_hooks_dir = os.path.join(self.project_root, '.git', 'hooks')
        self.perfect21_main = os.path.join(self.project_root, 'main')

        # 检查Git仓库
        if not os.path.exists(os.path.join(self.project_root, '.git')):
            raise Exception("不是Git仓库！请在Git项目根目录运行。")

    def create_hook_script(self, hook_name: str, hook_type: str) -> str:
        """创建Git钩子脚本"""

        if hook_type == 'pre-commit':
            script_content = f'''#!/bin/bash
# Perfect21 Pre-commit Hook
# 自动调用Perfect21进行提交前检查

echo "🚀 Perfect21 Pre-commit检查..."

# 调用Perfect21 pre-commit钩子
cd "{self.project_root}"
python3 main/cli.py hooks pre-commit

# 检查结果
if [ $? -eq 0 ]; then
    echo "✅ Perfect21检查通过，允许提交"
    exit 0
else
    echo "❌ Perfect21检查失败，阻止提交"
    echo "请根据上述建议修复问题后重新提交"
    exit 1
fi
'''

        elif hook_type == 'pre-push':
            script_content = f'''#!/bin/bash
# Perfect21 Pre-push Hook
# 自动调用Perfect21进行推送前验证

echo "🚀 Perfect21 Pre-push验证..."

# 获取远程仓库信息
remote="$1"
url="$2"

# 调用Perfect21 pre-push钩子
cd "{self.project_root}"
python3 main/cli.py hooks pre-push --remote "$remote"

# 检查结果
if [ $? -eq 0 ]; then
    echo "✅ Perfect21验证通过，允许推送"
    exit 0
else
    echo "❌ Perfect21验证失败，阻止推送"
    echo "请根据上述建议修复问题后重新推送"
    exit 1
fi
'''

        elif hook_type == 'post-checkout':
            script_content = f'''#!/bin/bash
# Perfect21 Post-checkout Hook
# 自动调用Perfect21进行分支切换后处理

echo "🚀 Perfect21 Post-checkout处理..."

# 获取切换信息
old_ref="$1"
new_ref="$2"
branch_flag="$3"

# 调用Perfect21 post-checkout钩子
cd "{self.project_root}"
python3 main/cli.py hooks post-checkout --old-ref "$old_ref" --new-ref "$new_ref"

echo "✅ Perfect21环境检查完成"
exit 0
'''

        else:
            raise ValueError(f"不支持的钩子类型: {hook_type}")

        return script_content

    def install_hook(self, hook_type: str) -> bool:
        """安装指定的Git钩子"""
        try:
            hook_file = os.path.join(self.git_hooks_dir, hook_type)

            # 创建钩子脚本内容
            script_content = self.create_hook_script(hook_type, hook_type)

            # 备份现有钩子
            if os.path.exists(hook_file):
                backup_file = f"{hook_file}.backup.{int(os.path.getmtime(hook_file))}"
                os.rename(hook_file, backup_file)
                print(f"📦 备份现有钩子: {backup_file}")

            # 写入新钩子
            with open(hook_file, 'w', encoding='utf-8') as f:
                f.write(script_content)

            # 设置可执行权限
            os.chmod(hook_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

            print(f"✅ 安装{hook_type}钩子成功: {hook_file}")
            return True

        except Exception as e:
            print(f"❌ 安装{hook_type}钩子失败: {e}")
            return False

    def install_all_hooks(self) -> dict:
        """安装所有Perfect21 Git钩子"""
        results = {}
        hooks = ['pre-commit', 'pre-push', 'post-checkout']

        print("🔧 开始安装Perfect21 Git钩子...")

        for hook in hooks:
            results[hook] = self.install_hook(hook)

        # 安装总结
        success_count = sum(results.values())
        total_count = len(results)

        print(f"\n📊 安装总结: {success_count}/{total_count} 钩子安装成功")

        if success_count == total_count:
            print("🎉 Perfect21 Git自动化工作流安装完成！")
            print("\n现在Git操作将自动触发Perfect21检查：")
            print("  git commit → 自动调用@orchestrator质量检查")
            print("  git push   → 自动调用@test-engineer验证")
            print("  git checkout → 自动调用@devops-engineer环境配置")
        else:
            print("⚠️  部分钩子安装失败，请检查错误信息")

        return results

    def uninstall_hooks(self) -> bool:
        """卸载Perfect21钩子"""
        try:
            hooks = ['pre-commit', 'pre-push', 'post-checkout']
            removed_count = 0

            for hook in hooks:
                hook_file = os.path.join(self.git_hooks_dir, hook)
                if os.path.exists(hook_file):
                    # 检查是否是Perfect21钩子
                    with open(hook_file, 'r') as f:
                        content = f.read()

                    if 'Perfect21' in content:
                        os.remove(hook_file)
                        removed_count += 1
                        print(f"🗑️  删除{hook}钩子")

            print(f"✅ 卸载完成，删除了{removed_count}个Perfect21钩子")
            return True

        except Exception as e:
            print(f"❌ 卸载失败: {e}")
            return False

    def check_installation(self) -> dict:
        """检查钩子安装状态"""
        hooks = ['pre-commit', 'pre-push', 'post-checkout']
        status = {}

        for hook in hooks:
            hook_file = os.path.join(self.git_hooks_dir, hook)
            if os.path.exists(hook_file):
                with open(hook_file, 'r') as f:
                    content = f.read()
                status[hook] = 'Perfect21' in content
            else:
                status[hook] = False

        return status

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Perfect21 Git钩子安装器')
    parser.add_argument('action', choices=['install', 'uninstall', 'status'],
                       help='操作: install(安装), uninstall(卸载), status(状态)')

    args = parser.parse_args()

    try:
        installer = GitHooksInstaller()

        if args.action == 'install':
            installer.install_all_hooks()
        elif args.action == 'uninstall':
            installer.uninstall_hooks()
        elif args.action == 'status':
            status = installer.check_installation()
            print("📋 Perfect21 Git钩子状态:")
            for hook, installed in status.items():
                status_icon = "✅" if installed else "❌"
                print(f"  {hook}: {status_icon}")

    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()