#!/usr/bin/env python3
"""
Perfect21 Git Hooks Manager
完整的Git hooks集成管理器，支持14个客户端钩子 + 智能SubAgent调用
"""

import os
import stat
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from .hooks import GitHooks

class GitHooksManager:
    """完整的Git钩子管理器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.git_hooks_dir = os.path.join(self.project_root, '.git', 'hooks')
        self.git_hooks = GitHooks(project_root)

        # Git hooks配置映射
        self.hooks_config = {
            # 提交工作流钩子 (核心)
            'pre-commit': {
                'category': 'commit_workflow',
                'priority': 'high',
                'subagent': 'auto',  # 自动根据分支选择
                'description': '提交前代码质量检查',
                'triggers': ['linting', 'testing', 'security_scan'],
                'required': True
            },
            'commit-msg': {
                'category': 'commit_workflow',
                'priority': 'medium',
                'subagent': '@business-analyst',
                'description': '提交消息格式验证',
                'triggers': ['message_format', 'issue_linking'],
                'required': True
            },
            'post-commit': {
                'category': 'commit_workflow',
                'priority': 'low',
                'subagent': '@devops-engineer',
                'description': '提交后通知和统计',
                'triggers': ['notifications', 'metrics'],
                'required': False
            },
            'prepare-commit-msg': {
                'category': 'commit_workflow',
                'priority': 'low',
                'subagent': '@business-analyst',
                'description': '自动生成提交消息模板',
                'triggers': ['message_template', 'branch_context'],
                'required': False
            },

            # 推送工作流钩子 (重要)
            'pre-push': {
                'category': 'push_workflow',
                'priority': 'high',
                'subagent': 'auto',  # 根据分支和目标选择
                'description': '推送前完整验证',
                'triggers': ['full_testing', 'security_audit', 'build_check'],
                'required': True
            },

            # 分支工作流钩子 (必要)
            'post-checkout': {
                'category': 'branch_workflow',
                'priority': 'medium',
                'subagent': '@devops-engineer',
                'description': '分支切换后环境配置',
                'triggers': ['environment_setup', 'dependency_check'],
                'required': True
            },
            'post-merge': {
                'category': 'branch_workflow',
                'priority': 'medium',
                'subagent': '@test-engineer',
                'description': '合并后集成测试',
                'triggers': ['integration_testing', 'conflict_resolution'],
                'required': True
            },
            'post-rewrite': {
                'category': 'branch_workflow',
                'priority': 'low',
                'subagent': '@devops-engineer',
                'description': '重写操作后清理',
                'triggers': ['cleanup', 'cache_invalidation'],
                'required': False
            },

            # 高级钩子 (可选)
            'pre-rebase': {
                'category': 'advanced',
                'priority': 'medium',
                'subagent': '@code-reviewer',
                'description': '变基前冲突预检查',
                'triggers': ['conflict_detection', 'history_validation'],
                'required': False
            },
            'pre-auto-gc': {
                'category': 'maintenance',
                'priority': 'low',
                'subagent': '@devops-engineer',
                'description': '垃圾回收前备份',
                'triggers': ['backup', 'cleanup_validation'],
                'required': False
            },

            # 补丁工作流钩子 (邮件工作流)
            'applypatch-msg': {
                'category': 'patch_workflow',
                'priority': 'low',
                'subagent': '@business-analyst',
                'description': '补丁消息验证',
                'triggers': ['patch_message_validation'],
                'required': False
            },
            'pre-applypatch': {
                'category': 'patch_workflow',
                'priority': 'low',
                'subagent': '@code-reviewer',
                'description': '应用补丁前检查',
                'triggers': ['patch_validation'],
                'required': False
            },
            'post-applypatch': {
                'category': 'patch_workflow',
                'priority': 'low',
                'subagent': '@test-engineer',
                'description': '应用补丁后测试',
                'triggers': ['patch_testing'],
                'required': False
            }
        }

        # 钩子分组
        self.hook_groups = {
            'essential': ['pre-commit', 'pre-push', 'post-checkout'],
            'standard': ['pre-commit', 'commit-msg', 'pre-push', 'post-checkout', 'post-merge'],
            'advanced': ['pre-commit', 'commit-msg', 'post-commit', 'pre-push', 'post-checkout',
                        'post-merge', 'pre-rebase', 'post-rewrite'],
            'complete': list(self.hooks_config.keys())
        }

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

            print(f"  {hook_name}: {status_icon} {status_text} "
                  f"{required_icon} ({config['priority']}) - {config['description']}")

        print(f"\n🔴=必需 🟡=可选")