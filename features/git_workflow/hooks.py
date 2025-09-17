#!/usr/bin/env python3
"""
Git Hooks - SubAgent调用编排器
不重复实现功能，智能调用claude-code-unified-agents的现有SubAgent
"""

import os
import sys
import subprocess
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# 添加项目路径以导入git_cache
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from modules.git_cache import get_git_cache

logger = logging.getLogger("GitHooks")

class GitHooks:
    """Git钩子 - SubAgent调用编排器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()

        # SubAgent映射 - 调用claude-code-unified-agents的现有Agent
        self.subagent_mapping = {
            'code_review': '@code-reviewer',
            'security_audit': '@security-auditor',
            'test_execution': '@test-engineer',
            'performance_check': '@performance-engineer',
            'deployment_check': '@devops-engineer',
            'quality_gate': '@orchestrator'
        }

        logger.info("Git Hooks初始化完成 - 基于claude-code-unified-agents")

    def _get_parallel_agents(self, primary_agent: str, context: Dict[str, Any] = None) -> list:
        """根据主Agent和上下文决定并行执行的Agent列表"""
        # 基础并行Agent配置
        base_parallel_agents = {
            '@orchestrator': ['@orchestrator', '@code-reviewer', '@security-auditor', '@test-engineer'],
            '@code-reviewer': ['@code-reviewer', '@security-auditor', '@test-engineer'],
            '@security-auditor': ['@security-auditor', '@test-engineer', '@devops-engineer'],
            '@test-engineer': ['@test-engineer', '@code-reviewer', '@devops-engineer'],
            '@devops-engineer': ['@devops-engineer', '@security-auditor', '@test-engineer']
        }

        # 获取默认并行Agent
        agents = base_parallel_agents.get(primary_agent, [primary_agent, '@code-reviewer', '@test-engineer'])

        # 根据上下文调整
        if context:
            branch = context.get('branch', '')
            if branch == 'main':
                # 主分支需要最严格的检查
                agents = ['@orchestrator', '@code-reviewer', '@security-auditor', '@test-engineer', '@devops-engineer']
            elif 'feature' in branch:
                # 功能分支
                agents = ['@code-reviewer', '@test-engineer', '@security-auditor']
            elif 'hotfix' in branch:
                # 热修复分支
                agents = ['@test-engineer', '@code-reviewer', '@devops-engineer']

        return list(set(agents))  # 去重

    def _build_mandatory_parallel_prompt(self, primary_agent: str, task_description: str,
                                       parallel_agents: list, context: Dict[str, Any] = None) -> str:
        """构建强制并行执行的提示词"""

        # 基础任务描述
        prompt_parts = [task_description]

        # 添加Git工作流上下文
        if context:
            prompt_parts.append("\nGit工作流上下文:")
            for key, value in context.items():
                prompt_parts.append(f"- {key}: {value}")

        # 强制并行执行指令
        prompt_parts.extend([
            "\n🚀 PERFECT21 强制并行执行模式",
            f"主要协调Agent: {primary_agent}",
            f"必须并行调用的Agent: {', '.join(parallel_agents)}",
            "",
            "⚠️ 重要指令:",
            "1. 你必须在单个消息中同时调用所有指定的Agent",
            "2. 禁止串行执行，必须使用并行Task调用",
            "3. 每个Agent都有不同的专业职责，需要协作完成任务",
            "4. 这是Perfect21的强制并行模式，必须严格执行",
            "",
            "💡 示例格式:",
            "<function_calls>",
            "<invoke name=\"Task\">",
            "<parameter name=\"subagent_type\">code-reviewer</parameter>",
            "</invoke>",
            "</function_calls>"
        ])

        try:
            # 获取当前分支
            branch_result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            # 获取暂存文件
            staged_result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            # 获取修改文件
            modified_result = subprocess.run(
                ['git', 'diff', '--name-only'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            return {
                'current_branch': branch_result.stdout.strip(),
                'staged_files': [f for f in staged_result.stdout.strip().split('\n') if f],
                'modified_files': [f for f in modified_result.stdout.strip().split('\n') if f],
                'has_staged_changes': bool(staged_result.stdout.strip())
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"获取Git状态失败: {e}")
            return {
                'current_branch': 'unknown',
                'staged_files': [],
                'modified_files': [],
                'has_staged_changes': False,
                'error': str(e)
            }

    def generate_parallel_agents_instruction(self, agents_to_call: list, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """生成需要Claude Code并行调用的agents指令

        重要：SubAgent不能调用SubAgent，所有调用必须由Claude Code执行
        这个方法只是生成执行建议，实际调用需要Claude Code完成
        """
        try:
            logger.info(f"生成并行调用指令: {len(agents_to_call)}个agents")
            logger.info(f"Agents列表: {', '.join(agents_to_call)}")

            # 构建并行执行指令
            parallel_instructions = []
            for agent in agents_to_call:
                agent_name = agent.replace('@', '')
                parallel_instructions.append(f"Task(subagent_type='{agent_name}', ...)")

            # 返回给Claude Code的执行指令
            return {
                'success': True,
                'agents_to_call': agents_to_call,
                'task_description': task_description,  # 统一字段名
                'execution_mode': 'parallel' if len(agents_to_call) > 1 else 'sequential',  # 添加执行模式
                'instruction': f"""请在一个消息中并行调用以下agents进行{task_description}：

{chr(10).join(['- ' + inst for inst in parallel_instructions])}

重要：
1. 这些agents必须在同一个消息中并行调用
2. 不能串行执行，必须使用多个Task调用
3. 每个agent独立完成自己的任务，不能相互调用""",
                'context': context,
                'message': f"需要并行调用{len(agents_to_call)}个agents",
                'parallel_execution_required': len(agents_to_call) > 1
            }

        except Exception as e:
            logger.error(f"生成并行指令失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"生成并行执行指令失败"
            }

    def pre_commit_hook(self) -> Dict[str, Any]:
        """提交前钩子 - 调用代码审查和质量检查"""
        logger.info("执行pre-commit钩子")

        git_status = self.get_git_status()

        # 修复: 使用实际的字段名
        has_staged = git_status.get('staged_files', 0) > 0
        if not has_staged:
            return {
                'success': False,
                'message': '没有暂存的文件，无法提交',
                'should_abort': True
            }

        # 分析分支类型决定检查级别
        branch = git_status['current_branch']
        if branch in ['main', 'master', 'release']:
            # 严格检查 - 需要多个agents并行检查
            agents = ['@code-reviewer', '@security-auditor', '@test-engineer']
            return self.generate_parallel_agents_instruction(
                agents,
                f"对{branch}分支执行严格的提交前质量检查",
                {
                    'branch': branch,
                    'staged_files': git_status.get('staged_files', 0),
                    'check_level': 'strict'
                }
            )
        else:
            # 基础检查 - 只需代码审查和基础测试
            agents = ['@code-reviewer']
            # 修复: staged_files现在是数字而不是列表
            if git_status.get('staged_files', 0) > 5:
                # 如果文件较多，加入测试检查
                agents.append('@test-engineer')

            return self.generate_parallel_agents_instruction(
                agents,
                f"对{branch}分支执行标准代码检查",
                {
                    'branch': branch,
                    'staged_files': git_status.get('staged_files', 0),
                    'check_level': 'basic'
                }
            )

    def pre_push_hook(self, remote: str = 'origin', branch: str = None) -> Dict[str, Any]:
        """推送前钩子 - 调用测试和部署检查"""
        logger.info(f"执行pre-push钩子: {remote}")

        git_status = self.get_git_status()
        current_branch = branch or git_status['current_branch']

        # 保护主分支
        if current_branch in ['main', 'master']:
            return {
                'success': False,
                'message': '禁止直接推送到主分支，请使用Pull Request流程',
                'should_abort': True,
                'branch_protection': True
            }

        # 根据分支类型选择检查策略
        if current_branch.startswith('release/'):
            # 发布分支 - 完整检查，需要多个agents并行验证
            agents = ['@test-engineer', '@performance-engineer', '@devops-engineer']
            return self.generate_parallel_agents_instruction(
                agents,
                f"对发布分支{current_branch}执行推送前完整检查",
                {
                    'branch': current_branch,
                    'remote': remote,
                    'check_type': 'release'
                }
            )
        elif current_branch.startswith('hotfix/'):
            # 热修复分支 - 快速验证
            agents = ['@test-engineer']  # 只需要测试验证
            return self.generate_parallel_agents_instruction(
                agents,
                f"对热修复分支{current_branch}执行快速测试验证",
                {
                    'branch': current_branch,
                    'remote': remote,
                    'check_type': 'hotfix',
                    'priority': 'high'
                }
            )
        else:
            # 功能分支 - 标准检查
            agents = ['@test-engineer']
            # 如果是大型功能分支，增加代码审查
            if 'feature/' in current_branch:
                agents.append('@code-reviewer')

            return self.generate_parallel_agents_instruction(
                agents,
                f"对功能分支{current_branch}执行标准检查",
                {
                    'branch': current_branch,
                    'remote': remote,
                    'check_type': 'feature'
                }
            )

    def post_checkout_hook(self, old_ref: str, new_ref: str, branch_flag: str) -> Dict[str, Any]:
        """分支切换后钩子 - 调用环境配置和依赖检查"""
        logger.info("执行post-checkout钩子")

        # 只处理分支切换
        if branch_flag != "1":
            return {'success': True, 'message': '非分支切换，跳过处理'}

        git_status = self.get_git_status()
        current_branch = git_status['current_branch']

        # 生成DevOps Engineer执行建议
        return self.generate_parallel_agents_instruction(
            [self.subagent_mapping['deployment_check']],
            f"分支切换到{current_branch}，检查开发环境配置、依赖状态、工具链设置",
            {
                'branch': current_branch,
                'old_ref': old_ref,
                'new_ref': new_ref,
                'action': 'branch_switch',
                'checks': ['dependencies', 'environment', 'configuration']
            }
        )

    def prepare_commit_msg_hook(self, commit_msg_file: str) -> Dict[str, Any]:
        """准备提交消息钩子 - 自动优化提交消息格式"""
        logger.info("执行prepare-commit-msg钩子")

        git_status = self.get_git_status()
        current_branch = git_status['current_branch']

        # 获取暂存文件信息
        try:
            staged_files = subprocess.check_output(
                ['git', 'diff', '--cached', '--name-only'],
                cwd=self.project_root,
                text=True,
                encoding='utf-8'
            ).strip().split('\n')
            staged_files = [f for f in staged_files if f]  # 过滤空行
        except:
            staged_files = []

        # 生成Business Analyst执行建议
        return self.generate_parallel_agents_instruction(
            ['@business-analyst'],
            f"分析分支{current_branch}的提交内容，优化提交消息格式和语义",
            {
                'branch': current_branch,
                'staged_files': staged_files,
                'commit_msg_file': commit_msg_file,
                'action': 'prepare_commit_message',
                'requirements': ['semantic_format', 'clear_description', 'change_summary']
            }
        )

    def commit_msg_hook(self, commit_msg_file: str) -> Dict[str, Any]:
        """提交消息验证钩子 - 验证提交消息格式和质量"""
        logger.info("执行commit-msg钩子")

        git_status = self.get_git_status()
        current_branch = git_status['current_branch']

        # 读取提交消息
        try:
            with open(commit_msg_file, 'r', encoding='utf-8') as f:
                commit_message = f.read().strip()
        except:
            commit_message = ""

        # 生成Business Analyst执行建议
        return self.generate_parallel_agents_instruction(
            ['@business-analyst'],
            f"验证分支{current_branch}的提交消息格式、语义化标准、描述质量",
            {
                'branch': current_branch,
                'commit_message': commit_message,
                'commit_msg_file': commit_msg_file,
                'action': 'validate_commit_message',
                'validation_rules': ['semantic_format', 'length_check', 'description_quality', 'no_fixup']
            }
        )

    def post_commit_hook(self) -> Dict[str, Any]:
        """提交后钩子 - 提交统计和通知"""
        logger.info("执行post-commit钩子")

        git_status = self.get_git_status()
        current_branch = git_status['current_branch']

        # 获取最新提交信息
        try:
            latest_commit = subprocess.check_output(
                ['git', 'log', '-1', '--pretty=format:%H|%s|%an'],
                cwd=self.project_root,
                text=True,
                encoding='utf-8'
            ).strip()
            commit_hash, commit_msg, author = latest_commit.split('|', 2)
        except:
            commit_hash, commit_msg, author = "unknown", "unknown", "unknown"

        # 生成DevOps Engineer执行建议
        return self.generate_parallel_agents_instruction(
            ['@devops-engineer'],
            f"处理分支{current_branch}的提交后统计、通知和持续集成触发",
            {
                'branch': current_branch,
                'commit_hash': commit_hash,
                'commit_message': commit_msg,
                'author': author,
                'action': 'post_commit_processing',
                'tasks': ['commit_stats', 'notification', 'ci_trigger', 'deployment_check']
            }
        )

    def get_hook_status(self) -> Dict[str, Any]:
        """获取钩子状态"""
        git_status = self.get_git_status()

        return {
            'git_status': git_status,
            'available_subagents': self.subagent_mapping,
            'core_path': os.path.join(self.project_root, 'core/claude-code-unified-agents/.claude/agents'),
            'hooks_active': True
        }

    def cleanup(self) -> None:
        """清理GitHooks实例，释放内存"""
        try:
            # 清理映射配置
            if hasattr(self, 'subagent_mapping'):
                self.subagent_mapping.clear()

            # 清理项目根路径引用
            self.project_root = None

            # 强制垃圾回收
            import gc
            gc.collect()

            logger.info("GitHooks清理完成")

        except Exception as e:
            logger.error(f"GitHooks清理失败: {e}")

    def __del__(self):
        """析构函数，确保资源被清理"""
        try:
            self.cleanup()
        except:
            pass
    def get_installed_hooks(self):
        """获取已安装的Git钩子列表"""
        installed = []
        git_hooks_dir = os.path.join(self.project_root, '.git', 'hooks')

        if not os.path.exists(git_hooks_dir):
            return installed

        # 检查支持的钩子类型
        supported_hooks = [
            'pre-commit', 'commit-msg', 'pre-push',
            'post-checkout', 'post-merge', 'post-commit'
        ]

        for hook_name in supported_hooks:
            hook_path = os.path.join(git_hooks_dir, hook_name)
            if os.path.exists(hook_path) and os.path.isfile(hook_path):
                installed.append(hook_name)

        return installed

    def get_git_status(self) -> Dict[str, Any]:
        """获取Git状态信息 - 使用缓存优化版本"""
        try:
            # 使用Git缓存批量获取状态，减少subprocess调用
            git_cache = get_git_cache(self.project_root)
            cached_status = git_cache.batch_git_status()

            # 记录缓存统计
            stats = git_cache.get_stats()
            if stats['cache_hits'] > 0:
                logger.debug(f"Git缓存命中率: {stats['hit_rate']}")

            # 确保返回所有测试需要的字段
            return {
                'current_branch': cached_status.get('current_branch', 'unknown'),
                'is_clean': cached_status.get('is_clean', False),
                'has_staged_changes': cached_status.get('has_staged_changes', False),
                'has_unstaged_changes': cached_status.get('has_unstaged_changes', False),
                'modified_files': len(cached_status.get('modified_files', [])),
                'staged_files': len(cached_status.get('staged_files', [])),
                'untracked_files': len(cached_status.get('untracked_files', [])),
                'status_lines': [],  # 兼容旧接口
                # 新增的详细信息
                'staged_file_list': cached_status.get('staged_files', []),
                'modified_file_list': cached_status.get('modified_files', []),
                'untracked_file_list': cached_status.get('untracked_files', []),
                'ahead_count': cached_status.get('ahead_count', 0),
                'behind_count': cached_status.get('behind_count', 0)
            }

        except Exception as e:
            logger.error(f"Git状态检查异常: {e}")
            return {
                'current_branch': 'unknown',
                'is_clean': False,
                'has_staged_changes': False,
                'has_unstaged_changes': False,
                'modified_files': 0,
                'staged_files': 0,
                'untracked_files': 0,
                'status_lines': [],
                'staged_file_list': [],
                'modified_file_list': [],
                'untracked_file_list': [],
                'ahead_count': 0,
                'behind_count': 0,
                'error': str(e)
            }

class GitHookManager:
    """面向测试的Git Hook管理器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.git_hooks = GitHooks(project_root)
        self.installed_hooks = {}
        self._load_hooks_config()

    def get_hooks_status(self) -> Dict[str, Any]:
        """获取Git Hooks状态"""
        return self.git_hooks.get_hook_status()

    def is_hook_installed(self, hook_name: str) -> bool:
        """检查钩子是否安装"""
        installed_hooks = self.git_hooks.get_installed_hooks()
        return hook_name in installed_hooks

    def is_hook_enabled(self, hook_name: str) -> bool:
        """检查钩子是否启用"""
        # 模拟检查钩子是否启用
        config = self.installed_hooks.get(hook_name, {})
        return config.get('enabled', True)

    def get_hook_config(self, hook_name: str) -> Dict[str, Any]:
        """获取钩子配置"""
        return self.installed_hooks.get(hook_name, {
            'enabled': True,
            'script_path': f'.git/hooks/{hook_name}',
            'description': f'{hook_name} hook configuration'
        })

    def install_hook(self, hook_name: str, config: Dict[str, Any] = None) -> bool:
        """安装钩子（模拟）"""
        hook_config = config or {
            'enabled': True,
            'script_path': f'.git/hooks/{hook_name}',
            'install_time': os.path.getmtime('.')
        }

        self.installed_hooks[hook_name] = hook_config
        self._save_hooks_config()
        return True

    def uninstall_hook(self, hook_name: str) -> bool:
        """卸载钩子（模拟）"""
        if hook_name in self.installed_hooks:
            del self.installed_hooks[hook_name]
            self._save_hooks_config()
            return True
        return False

    def _load_hooks_config(self) -> None:
        """加载钩子配置"""
        # 模拟默认安装的钩子
        default_hooks = [
            'pre-commit', 'commit-msg', 'pre-push',
            'post-commit', 'post-merge'
        ]

        for hook in default_hooks:
            self.installed_hooks[hook] = {
                'enabled': True,
                'script_path': f'.git/hooks/{hook}',
                'description': f'{hook} hook for Perfect21'
            }

    def _save_hooks_config(self) -> None:
        """保存钩子配置（模拟）"""
        # 在实际实现中，这里会保存到文件
        pass
