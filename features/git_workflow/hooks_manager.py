#!/usr/bin/env python3
"""
Perfect21 Git Hooks Manager
完整的Git hooks集成管理器，支持14个客户端钩子 + 智能SubAgent调用
"""

import os
import stat
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .hooks import GitHooks
from .config_loader import HooksConfigLoader
from .plugins.plugin_manager import PluginManager
from .plugins.base_plugin import PluginResult, PluginStatus

logger = logging.getLogger("Perfect21.HooksManager")

class GitHooksManager:
    """完整的Git钩子管理器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.git_hooks_dir = os.path.join(self.project_root, '.git', 'hooks')
        self.git_hooks = GitHooks(project_root)

        # 加载配置
        self.config_loader = HooksConfigLoader(project_root)

        # 验证配置
        validation = self.config_loader.validate_config()
        if not validation['valid']:
            logger.warning("Hooks配置验证失败，使用默认配置")
            for error in validation['errors']:
                logger.error(f"配置错误: {error}")

        # Git hooks配置映射（从YAML配置构建）
        self.hooks_config = self._build_hooks_config_from_yaml()

        # 钩子分组（从配置加载器获取）
        self.hook_groups = self._build_hook_groups_from_yaml()

        # 初始化插件管理器
        plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        self.plugin_manager = PluginManager(
            plugins_dir=plugins_dir,
            config=self.config_loader._config
        )

        # 加载所有插件
        self._initialize_plugins()

    def _build_hooks_config_from_yaml(self) -> Dict[str, Any]:
        """从YAML配置构建hooks配置映射"""
        hooks_config = {}
        yaml_hooks = self.config_loader._config.get('hooks', {})

        for hook_name, yaml_config in yaml_hooks.items():
            hooks_config[hook_name] = {
                'category': yaml_config.get('category', 'unknown'),
                'priority': yaml_config.get('priority', 'medium'),
                'subagent': yaml_config.get('agent', '@orchestrator'),
                'description': yaml_config.get('description', f'{hook_name}钩子'),
                'triggers': yaml_config.get('triggers', []),
                'required': yaml_config.get('enabled', False),
                'timeout': yaml_config.get('timeout', 120),
                'parallel': yaml_config.get('parallel', False),
                'plugins': yaml_config.get('plugins', [])
            }

        return hooks_config

    def _build_hook_groups_from_yaml(self) -> Dict[str, List[str]]:
        """从YAML配置构建钩子分组"""
        yaml_groups = self.config_loader._config.get('hook_groups', {})
        hook_groups = {}

        for group_name, group_config in yaml_groups.items():
            hook_groups[group_name] = group_config.get('hooks', [])

        return hook_groups

    def get_hook_agent_for_branch(self, hook_name: str, branch: str = None) -> str:
        """根据分支获取hook对应的Agent"""
        return self.config_loader.get_hook_agent(hook_name, branch)

    def is_hook_enabled(self, hook_name: str) -> bool:
        """检查hook是否启用"""
        return self.config_loader.is_hook_enabled(hook_name)

    def get_enabled_hooks(self, group_name: str = None) -> List[str]:
        """获取启用的hooks列表"""
        return self.config_loader.get_enabled_hooks(group_name)

    def get_hook_timeout(self, hook_name: str) -> int:
        """获取hook超时时间"""
        return self.config_loader.get_hook_timeout(hook_name)

    def is_parallel_enabled(self, hook_name: str = None) -> bool:
        """检查是否启用并行执行"""
        return self.config_loader.is_parallel_enabled(hook_name)

    def get_hook_plugins(self, hook_name: str) -> List[str]:
        """获取hook的插件列表"""
        return self.config_loader.get_enabled_plugins(hook_name)

    def _initialize_plugins(self) -> None:
        """初始化插件系统"""
        try:
            logger.info("初始化Git Hooks插件系统...")

            # 加载所有插件
            load_results = self.plugin_manager.load_all_plugins()

            loaded_count = sum(1 for success in load_results.values() if success)
            total_count = len(load_results)

            logger.info(f"插件加载完成: {loaded_count}/{total_count}")

            if loaded_count < total_count:
                failed_plugins = [name for name, success in load_results.items() if not success]
                logger.warning(f"插件加载失败: {', '.join(failed_plugins)}")

        except Exception as e:
            logger.error(f"插件系统初始化失败: {e}")

    def execute_hook_plugins(self, hook_name: str, context: Dict[str, Any]) -> Dict[str, PluginResult]:
        """执行Hook的所有插件"""
        plugins = self.get_hook_plugins(hook_name)

        if not plugins:
            logger.info(f"Hook {hook_name} 没有配置插件")
            return {}

        # 检查并行执行设置
        parallel = self.is_parallel_enabled(hook_name)
        max_workers = self.config_loader.get_max_workers()

        logger.info(f"执行Hook {hook_name} 的 {len(plugins)} 个插件 (并行: {parallel})")

        # 执行插件
        results = self.plugin_manager.execute_plugins(
            plugin_names=plugins,
            context=context,
            parallel=parallel,
            max_workers=max_workers
        )

        return results

    def get_plugin_manager(self) -> PluginManager:
        """获取插件管理器实例"""
        return self.plugin_manager

    def get_plugin_status(self) -> Dict[str, Any]:
        """获取插件状态信息"""
        return {
            "plugins": self.plugin_manager.get_all_plugins_info(),
            "stats": self.plugin_manager.get_execution_stats(),
            "enabled_plugins": list(self.plugin_manager.get_enabled_plugins().keys()),
            "total_plugins": len(self.plugin_manager.plugins)
        }

    def enable_hook(self, hook_name: str) -> bool:
        """启用hook"""
        success = self.config_loader.enable_hook(hook_name)
        if success:
            # 重新构建配置
            self.hooks_config = self._build_hooks_config_from_yaml()
        return success

    def disable_hook(self, hook_name: str) -> bool:
        """禁用hook"""
        success = self.config_loader.disable_hook(hook_name)
        if success:
            # 重新构建配置
            self.hooks_config = self._build_hooks_config_from_yaml()
        return success

    def reload_config(self) -> bool:
        """重新加载配置"""
        success = self.config_loader.reload_config()
        if success:
            # 重新构建配置
            self.hooks_config = self._build_hooks_config_from_yaml()
            self.hook_groups = self._build_hook_groups_from_yaml()
        return success

    def get_config_summary(self) -> str:
        """获取配置摘要"""
        return self.config_loader.get_config_summary()

    def create_hook_script(self, hook_name: str) -> str:
        """生成Git钩子脚本"""
        hook_config = self.hooks_config.get(hook_name, {})
        subagent = hook_config.get('subagent', '@orchestrator')
        description = hook_config.get('description', f'{hook_name}钩子')

        # 基础脚本模板
        script_template = f'''#!/bin/bash
# Perfect21 {hook_name.title()} Hook
# {description}
# 自动调用Perfect21 SubAgent进行智能处理

set -e  # 遇到错误立即退出

echo "🚀 Perfect21 {hook_name}检查..."

# 设置项目路径
PROJECT_ROOT="{self.project_root}"
cd "$PROJECT_ROOT"

# 检查Perfect21是否可用
if [ ! -f "main/cli.py" ]; then
    echo "❌ Perfect21未找到，跳过钩子处理"
    exit 0
fi

'''

        # 根据钩子类型添加特定逻辑
        if hook_name == 'pre-commit':
            script_template += '''
# 获取暂存文件
STAGED_FILES=$(git diff --cached --name-only)
if [ -z "$STAGED_FILES" ]; then
    echo "ℹ️  没有暂存文件，跳过检查"
    exit 0
fi

# 调用Perfect21 pre-commit钩子
python3 main/cli.py hooks pre-commit
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Perfect21提交前检查通过"
else
    echo "❌ Perfect21提交前检查失败，请根据建议修复后重新提交"
    exit 1
fi
'''

        elif hook_name == 'pre-push':
            script_template += '''
# 获取推送信息
REMOTE="$1"
URL="$2"

# 调用Perfect21 pre-push钩子
python3 main/cli.py hooks pre-push --remote "${REMOTE:-origin}"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Perfect21推送前验证通过"
else
    echo "❌ Perfect21推送前验证失败，请根据建议修复后重新推送"
    exit 1
fi
'''

        elif hook_name == 'post-checkout':
            script_template += '''
# 获取切换信息
OLD_REF="$1"
NEW_REF="$2"
BRANCH_FLAG="$3"

# 调用Perfect21 post-checkout钩子
python3 main/cli.py hooks post-checkout --old-ref "$OLD_REF" --new-ref "$NEW_REF"

echo "✅ Perfect21分支切换处理完成"
'''

        elif hook_name == 'commit-msg':
            script_template += '''
# 获取提交消息文件
COMMIT_MSG_FILE="$1"

# 验证提交消息格式
python3 main/cli.py hooks commit-msg --file "$COMMIT_MSG_FILE"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 提交消息格式验证通过"
else
    echo "❌ 提交消息格式验证失败"
    exit 1
fi
'''

        elif hook_name == 'post-merge':
            script_template += '''
# 获取合并信息
SQUASH_MERGE="$1"

# 调用Perfect21 post-merge处理
python3 main/cli.py hooks post-merge --squash "$SQUASH_MERGE"

echo "✅ Perfect21合并后处理完成"
'''

        elif hook_name == 'post-commit':
            script_template += '''
# 调用Perfect21 post-commit处理
python3 main/cli.py hooks post-commit

echo "✅ Perfect21提交后处理完成"
'''

        else:
            # 其他钩子的通用处理
            script_template += f'''
# 调用Perfect21 {hook_name}钩子
python3 main/cli.py hooks {hook_name} "$@"

echo "✅ Perfect21 {hook_name}处理完成"
'''

        return script_template

    def install_hook(self, hook_name: str, force: bool = False) -> bool:
        """安装单个Git钩子"""
        try:
            if hook_name not in self.hooks_config:
                print(f"❌ 不支持的钩子: {hook_name}")
                return False

            hook_file = os.path.join(self.git_hooks_dir, hook_name)

            # 检查现有钩子
            if os.path.exists(hook_file) and not force:
                print(f"⚠️  {hook_name}钩子已存在，使用--force覆盖")
                return False

            # 备份现有钩子
            if os.path.exists(hook_file):
                backup_file = f"{hook_file}.backup.perfect21"
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                os.rename(hook_file, backup_file)
                print(f"📦 备份现有钩子: {os.path.basename(backup_file)}")

            # 创建钩子脚本
            script_content = self.create_hook_script(hook_name)

            # 写入钩子文件
            with open(hook_file, 'w', encoding='utf-8') as f:
                f.write(script_content)

            # 设置可执行权限
            os.chmod(hook_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

            config = self.hooks_config[hook_name]
            print(f"✅ 安装{hook_name}钩子成功")
            print(f"   📋 {config['description']}")
            print(f"   🤖 SubAgent: {config['subagent']}")

            return True

        except Exception as e:
            print(f"❌ 安装{hook_name}钩子失败: {e}")
            return False

    def install_hook_group(self, group: str = 'standard', force: bool = False) -> Dict[str, bool]:
        """安装钩子组"""
        if group not in self.hook_groups:
            print(f"❌ 不支持的钩子组: {group}")
            print(f"可用组: {', '.join(self.hook_groups.keys())}")
            return {}

        hooks = self.hook_groups[group]
        results = {}

        print(f"🔧 安装{group}钩子组 ({len(hooks)}个钩子)...")

        for hook in hooks:
            results[hook] = self.install_hook(hook, force)

        # 安装总结
        success_count = sum(results.values())
        total_count = len(results)

        print(f"\n📊 安装总结: {success_count}/{total_count} 钩子安装成功")

        if success_count == total_count:
            print(f"🎉 {group}钩子组安装完成！")
            self._print_usage_guide(group)
        else:
            print("⚠️  部分钩子安装失败，请检查错误信息")

        return results

    def _print_usage_guide(self, group: str):
        """打印使用指南"""
        print(f"\n📖 Perfect21 Git工作流已激活 ({group}模式):")

        if group in ['essential', 'standard', 'advanced', 'complete']:
            print("  🔍 git commit   → 自动代码质量检查 (@orchestrator/@code-reviewer)")
            print("  🚀 git push     → 自动测试验证 (@test-engineer)")
            print("  🌿 git checkout → 自动环境配置 (@devops-engineer)")

        if group in ['standard', 'advanced', 'complete']:
            print("  💬 commit消息   → 自动格式验证 (@business-analyst)")
            print("  🔄 git merge    → 自动集成测试 (@test-engineer)")

        if group in ['advanced', 'complete']:
            print("  📝 git rebase   → 自动冲突预检 (@code-reviewer)")
            print("  🧹 git gc       → 自动备份清理 (@devops-engineer)")

        print(f"\n🎯 使用 'python3 main/cli.py hooks status' 查看钩子状态")

    def uninstall_hooks(self, hook_names: List[str] = None) -> bool:
        """卸载Perfect21钩子"""
        try:
            if hook_names is None:
                hook_names = list(self.hooks_config.keys())

            removed_count = 0

            for hook_name in hook_names:
                hook_file = os.path.join(self.git_hooks_dir, hook_name)

                if os.path.exists(hook_file):
                    # 检查是否是Perfect21钩子
                    with open(hook_file, 'r') as f:
                        content = f.read()

                    if 'Perfect21' in content:
                        # 恢复备份钩子
                        backup_file = f"{hook_file}.backup.perfect21"
                        if os.path.exists(backup_file):
                            os.remove(hook_file)
                            os.rename(backup_file, hook_file)
                            print(f"🔄 恢复{hook_name}备份钩子")
                        else:
                            os.remove(hook_file)
                            print(f"🗑️  删除{hook_name}钩子")

                        removed_count += 1

            print(f"✅ 卸载完成，处理了{removed_count}个Perfect21钩子")
            return True

        except Exception as e:
            print(f"❌ 卸载失败: {e}")
            return False

    def get_hook_status(self) -> Dict[str, Any]:
        """获取钩子安装状态"""
        status = {
            'hooks': {},
            'groups': {},
            'summary': {}
        }

        # 检查各个钩子状态
        for hook_name, config in self.hooks_config.items():
            hook_file = os.path.join(self.git_hooks_dir, hook_name)

            if os.path.exists(hook_file):
                with open(hook_file, 'r') as f:
                    content = f.read()
                is_perfect21 = 'Perfect21' in content

                status['hooks'][hook_name] = {
                    'installed': True,
                    'is_perfect21': is_perfect21,
                    'priority': config['priority'],
                    'category': config['category'],
                    'required': config['required']
                }
            else:
                status['hooks'][hook_name] = {
                    'installed': False,
                    'is_perfect21': False,
                    'priority': config['priority'],
                    'category': config['category'],
                    'required': config['required']
                }

        # 检查钩子组状态
        for group_name, hook_list in self.hook_groups.items():
            installed_count = sum(
                1 for hook in hook_list
                if status['hooks'][hook]['is_perfect21']
            )
            total_count = len(hook_list)

            status['groups'][group_name] = {
                'installed': installed_count,
                'total': total_count,
                'percentage': (installed_count / total_count) * 100
            }

        # 总体状态
        total_hooks = len(self.hooks_config)
        installed_hooks = sum(
            1 for hook_status in status['hooks'].values()
            if hook_status['is_perfect21']
        )

        status['summary'] = {
            'total_hooks': total_hooks,
            'installed_hooks': installed_hooks,
            'coverage_percentage': (installed_hooks / total_hooks) * 100
        }

        return status

    def print_status(self):
        """打印钩子状态"""
        status = self.get_hook_status()

        print("📋 Perfect21 Git钩子状态:")
        print("=" * 50)

        # 总体状态
        summary = status['summary']
        print(f"总体: {summary['installed_hooks']}/{summary['total_hooks']} "
              f"({summary['coverage_percentage']:.1f}%)")

        # 钩子组状态
        print(f"\n📊 钩子组状态:")
        for group, info in status['groups'].items():
            percentage = info['percentage']
            status_icon = "✅" if percentage == 100 else "🔄" if percentage > 0 else "❌"
            print(f"  {group}: {status_icon} {info['installed']}/{info['total']} "
                  f"({percentage:.1f}%)")

        # 详细钩子状态
        print(f"\n🔧 详细钩子状态:")
        for hook_name, hook_info in status['hooks'].items():
            if hook_info['is_perfect21']:
                status_icon = "✅"
                status_text = "已安装"
            elif hook_info['installed']:
                status_icon = "⚠️"
                status_text = "其他钩子"
            else:
                status_icon = "❌"
                status_text = "未安装"

            config = self.hooks_config[hook_name]
            required_icon = "🔴" if config['required'] else "🟡"

            # 显示插件信息
            plugins = self.get_hook_plugins(hook_name)
            plugin_info = f" [{len(plugins)}个插件]" if plugins else ""

            print(f"  {hook_name}: {status_icon} {status_text} "
                  f"{required_icon} ({config['priority']}){plugin_info} - {config['description']}")

        print(f"\n🔴=必需 🟡=可选")

        # 插件系统状态
        plugin_status = self.get_plugin_status()
        print(f"\n🔌 插件系统状态:")
        print(f"  总插件: {plugin_status['total_plugins']}")
        print(f"  启用插件: {len(plugin_status['enabled_plugins'])}")

        # 插件执行统计
        stats = plugin_status['stats']
        if stats['total_executions'] > 0:
            print(f"  执行统计: {stats['successful_executions']}/{stats['total_executions']} "
                  f"({stats['success_rate']:.1f}% 成功率)")
            print(f"  平均耗时: {stats['average_execution_time']:.2f}s")

        # 显示启用的插件
        if plugin_status['enabled_plugins']:
            print(f"\n  启用插件:")
            for plugin_name in plugin_status['enabled_plugins'][:10]:  # 最多显示10个
                plugin_info = plugin_status['plugins'][plugin_name]
                if plugin_info:
                    print(f"    - {plugin_name} ({plugin_info['metadata']['version']}) "
                          f"- {plugin_info['metadata']['description']}")

            if len(plugin_status['enabled_plugins']) > 10:
                print(f"    ... 还有 {len(plugin_status['enabled_plugins']) - 10} 个插件")

    def cleanup(self) -> None:
        """清理GitHooksManager实例，释放内存"""
        try:
            # 清理插件管理器
            if hasattr(self, 'plugin_manager') and self.plugin_manager:
                self.plugin_manager.cleanup()

            # 清理配置加载器
            if hasattr(self, 'config_loader') and self.config_loader:
                if hasattr(self.config_loader, 'cleanup'):
                    self.config_loader.cleanup()

            # 清理GitHooks实例
            if hasattr(self, 'git_hooks') and self.git_hooks:
                if hasattr(self.git_hooks, 'cleanup'):
                    self.git_hooks.cleanup()

            # 清理配置缓存
            if hasattr(self, 'hooks_config'):
                self.hooks_config.clear()
            if hasattr(self, 'hook_groups'):
                self.hook_groups.clear()

            # 强制垃圾回收
            import gc
            gc.collect()

            logger.info("GitHooksManager清理完成")

        except Exception as e:
            logger.error(f"GitHooksManager清理失败: {e}")

    def __del__(self):
        """析构函数，确保资源被清理"""
        try:
            self.cleanup()
        except:
            pass