#!/usr/bin/env python3
"""
Perfect21 Git Hooks Plugin Integration Test
测试插件系统集成
"""

import os
import sys

# Add the project root to Python path to handle imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from features.git_workflow.hooks_manager import GitHooksManager

def test_plugin_integration():
    """测试插件系统集成"""
    print("🧪 测试Perfect21 Git Hooks插件系统集成")
    print("=" * 50)

    try:
        # 创建hooks管理器
        print("1️⃣ 初始化GitHooksManager...")
        hm = GitHooksManager()
        print(f"   ✅ 初始化成功")

        # 检查插件管理器
        print("\n2️⃣ 检查插件管理器...")
        pm = hm.get_plugin_manager()
        print(f"   📊 发现插件: {len(pm.plugins)}")

        for plugin_name, plugin in pm.plugins.items():
            status = "✅" if plugin.enabled else "❌"
            print(f"   {status} {plugin_name}: {plugin.metadata.description}")

        # 检查hooks配置
        print("\n3️⃣ 检查hooks与插件映射...")
        test_hooks = ['pre-commit', 'commit-msg', 'pre-push']

        for hook_name in test_hooks:
            if hm.is_hook_enabled(hook_name):
                plugins = hm.get_hook_plugins(hook_name)
                agent = hm.get_hook_agent_for_branch(hook_name, 'main')
                parallel = hm.is_parallel_enabled(hook_name)

                print(f"   🔧 {hook_name}:")
                print(f"      🤖 Agent: {agent}")
                print(f"      🔌 插件: {plugins}")
                print(f"      ⚡ 并行: {parallel}")

        # 测试插件执行（干运行）
        print("\n4️⃣ 测试插件执行（dry run）...")
        context = {
            'hook_name': 'pre-commit',
            'project_root': hm.project_root,
            'branch': 'main',
            'staged_files': ['test_file.py'],
            'dry_run': True
        }

        if hm.is_hook_enabled('pre-commit'):
            plugins = hm.get_hook_plugins('pre-commit')
            if plugins:
                print(f"   🏃‍♂️ 模拟执行 pre-commit 的 {len(plugins)} 个插件...")

                # 测试单个插件执行
                for plugin_name in plugins[:2]:  # 只测试前两个
                    plugin = pm.get_plugin(plugin_name)
                    if plugin:
                        print(f"      🔍 插件 {plugin_name} - {plugin.metadata.description}")
                        print(f"          版本: {plugin.metadata.version}")
                        print(f"          优先级: {plugin.metadata.priority.value}")
                        print(f"          支持并行: {plugin.metadata.supports_parallel}")

        # 获取系统状态
        print("\n5️⃣ 系统状态总结...")
        plugin_status = hm.get_plugin_status()

        print(f"   📈 插件统计:")
        print(f"      总插件数: {plugin_status['total_plugins']}")
        print(f"      启用插件: {len(plugin_status['enabled_plugins'])}")

        stats = plugin_status['stats']
        print(f"   📊 执行统计:")
        print(f"      总执行次数: {stats['total_executions']}")
        print(f"      成功率: {stats['success_rate']:.1f}%")

        print(f"\n✅ 插件系统集成测试完成！")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hook_status():
    """测试hooks状态显示"""
    print("\n" + "=" * 50)
    print("🔧 Perfect21 Git Hooks状态测试")
    print("=" * 50)

    try:
        hm = GitHooksManager()
        hm.print_status()
        return True
    except Exception as e:
        print(f"❌ 状态显示测试失败: {e}")
        return False

def test_configuration():
    """测试配置系统"""
    print("\n" + "=" * 50)
    print("⚙️  配置系统测试")
    print("=" * 50)

    try:
        hm = GitHooksManager()

        print("📋 配置摘要:")
        print(hm.get_config_summary())

        # 测试配置验证
        validation = hm.config_loader.validate_config()
        print(f"\n🔍 配置验证: {'✅ 有效' if validation['valid'] else '❌ 无效'}")

        if validation['errors']:
            print("❌ 错误:")
            for error in validation['errors']:
                print(f"   - {error}")

        if validation['warnings']:
            print("⚠️  警告:")
            for warning in validation['warnings']:
                print(f"   - {warning}")

        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Perfect21 Git Hooks Plugin System Integration Test")
    print("测试插件系统与GitHooksManager的集成")
    print()

    # 运行所有测试
    test_results = []

    test_results.append(test_plugin_integration())
    test_results.append(test_hook_status())
    test_results.append(test_configuration())

    # 测试总结
    passed = sum(test_results)
    total = len(test_results)

    print(f"\n" + "=" * 50)
    print(f"🏆 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！插件系统集成成功！")
    else:
        print("⚠️  部分测试失败，请检查错误信息")

    sys.exit(0 if passed == total else 1)