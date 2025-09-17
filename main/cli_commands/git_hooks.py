"""
Git钩子相关命令处理
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from features.git_workflow.hooks_manager import GitHooksManager

def handle_git_hooks(p21, args) -> None:
    """处理Git钩子命令"""
    hooks_manager = GitHooksManager()

    if args.hook_action == 'list':
        list_hooks(hooks_manager)
    elif args.hook_action == 'status':
        hooks_manager.print_status()
    elif args.hook_action == 'install':
        install_hooks(hooks_manager, args)
    elif args.hook_action == 'uninstall':
        uninstall_hooks(hooks_manager, args)
    elif args.hook_action == 'test':
        test_hook(hooks_manager, args)
    elif args.hook_action == 'profile':
        show_profiles(hooks_manager)

def list_hooks(hooks_manager):
    """列出所有Git钩子"""
    print("📋 Perfect21支持的Git钩子:")
    print("=" * 50)

    categories = {
        'commit_workflow': '📝 提交工作流',
        'push_workflow': '🚀 推送工作流',
        'branch_workflow': '🌿 分支工作流',
        'advanced': '🔧 高级钩子',
        'maintenance': '🧹 维护钩子',
        'patch_workflow': '📦 补丁工作流'
    }

    for category, title in categories.items():
        print(f"\n{title}:")
        for hook_name, config in hooks_manager.hooks_config.items():
            if config['category'] == category:
                required_icon = "🔴" if config['required'] else "🟡"
                print(f"  {hook_name}: {config['description']} {required_icon} ({config['subagent']})")

    print(f"\n🔴=必需 🟡=可选")
    print(f"\n📊 钩子组:")
    for group, hooks in hooks_manager.hook_groups.items():
        print(f"  {group}: {len(hooks)}个钩子")

def install_hooks(hooks_manager, args):
    """安装Git钩子"""
    target = args.target or 'standard'

    if target in hooks_manager.hook_groups:
        # 安装钩子组
        hooks_manager.install_hook_group(target, args.force)
    elif target in hooks_manager.hooks_config:
        # 安装单个钩子
        hooks_manager.install_hook(target, args.force)
    elif target == 'all':
        # 安装所有钩子
        for hook_name in hooks_manager.hooks_config:
            hooks_manager.install_hook(hook_name, args.force)
    else:
        print(f"❌ 未知的钩子或钩子组: {target}")
        print("使用 'perfect21 hooks list' 查看可用的钩子")

def uninstall_hooks(hooks_manager, args):
    """卸载Git钩子"""
    target = args.target or 'all'

    if target in hooks_manager.hook_groups:
        # 卸载钩子组
        for hook_name in hooks_manager.hook_groups[target]:
            hooks_manager.uninstall_hook(hook_name, args.force)
    elif target in hooks_manager.hooks_config:
        # 卸载单个钩子
        hooks_manager.uninstall_hook(target, args.force)
    elif target == 'all':
        # 卸载所有钩子
        for hook_name in hooks_manager.hooks_config:
            hooks_manager.uninstall_hook(hook_name, args.force)
    else:
        print(f"❌ 未知的钩子或钩子组: {target}")

def test_hook(hooks_manager, args):
    """测试Git钩子"""
    target = args.target or 'pre-commit'

    if target in hooks_manager.hooks_config:
        hooks_manager.test_hook(target)
    else:
        print(f"❌ 未知的钩子: {target}")

def show_profiles(hooks_manager):
    """显示钩子配置文件"""
    profiles = hooks_manager.get_profiles()
    print("📊 可用的钩子配置文件:")
    print("=" * 50)
    for name, description in profiles.items():
        print(f"  {name}: {description}")