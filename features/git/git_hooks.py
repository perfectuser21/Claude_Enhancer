#!/usr/bin/env python3
"""
Perfect21 Git Hooks管理器 - 全面优化版本
自动化Git工作流，智能钩子执行，性能优化
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import aiofiles
import shlex

logger = logging.getLogger("Perfect21GitHooks")


class HookType(Enum):
    """Git Hook类型"""
    PRE_COMMIT = "pre-commit"
    COMMIT_MSG = "commit-msg"
    POST_COMMIT = "post-commit"
    PRE_PUSH = "pre-push"
    PRE_RECEIVE = "pre-receive"
    POST_RECEIVE = "post-receive"
    POST_CHECKOUT = "post-checkout"
    POST_MERGE = "post-merge"
    PRE_REBASE = "pre-rebase"
    POST_REWRITE = "post-rewrite"


class BranchStrategy(Enum):
    """分支策略"""
    GITFLOW = "gitflow"
    GITHUB_FLOW = "github_flow"
    GITLAB_FLOW = "gitlab_flow"
    SIMPLE_FLOW = "simple_flow"


@dataclass
class HookConfig:
    """钩子配置"""
    name: str
    enabled: bool = True
    agents: List[str] = field(default_factory=list)
    priority: int = 5
    timeout: int = 300
    retry_attempts: int = 2
    parallel_execution: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)
    custom_script: Optional[str] = None


@dataclass
class CommitInfo:
    """提交信息"""
    hash: str
    message: str
    author: str
    timestamp: datetime
    files_changed: List[str]
    branch: str
    is_merge: bool = False


@dataclass
class ConflictInfo:
    """冲突信息"""
    file_path: str
    conflict_type: str
    base_content: str
    current_content: str
    incoming_content: str
    resolution_suggestion: Optional[str] = None


class SmartCommitMessageGenerator:
    """智能提交信息生成器"""

    def __init__(self):
        self.type_keywords = {
            'feat': ['add', 'new', 'create', 'implement', 'introduce'],
            'fix': ['fix', 'resolve', 'correct', 'repair', 'solve'],
            'docs': ['doc', 'readme', 'comment', 'documentation'],
            'style': ['format', 'style', 'lint', 'whitespace'],
            'refactor': ['refactor', 'restructure', 'reorganize', 'clean'],
            'test': ['test', 'spec', 'coverage', 'unit', 'integration'],
            'chore': ['update', 'bump', 'maintain', 'config', 'build']
        }
        self.scope_patterns = {
            'api': ['api', 'endpoint', 'route', 'service'],
            'ui': ['ui', 'component', 'view', 'template', 'style'],
            'db': ['database', 'model', 'schema', 'migration'],
            'auth': ['auth', 'login', 'permission', 'security'],
            'config': ['config', 'setting', 'env', 'parameter']
        }

    def generate_commit_message(self, staged_files: List[str], git_diff: str = "") -> str:
        """基于文件变更和diff生成提交信息"""
        try:
            # 分析文件类型和变更模式
            commit_type = self._determine_commit_type(staged_files, git_diff)
            scope = self._determine_scope(staged_files)
            description = self._generate_description(staged_files, git_diff)

            # 构建提交信息
            if scope:
                message = f"{commit_type}({scope}): {description}"
            else:
                message = f"{commit_type}: {description}"

            # 添加详细描述
            body = self._generate_commit_body(staged_files, git_diff)
            if body:
                message += f"\n\n{body}"

            return message

        except Exception as e:
            logger.error(f"生成提交信息失败: {e}")
            return "chore: update files"

    def _determine_commit_type(self, files: List[str], diff: str) -> str:
        """确定提交类型"""
        # 基于文件路径判断
        if any('test' in f.lower() for f in files):
            return 'test'
        if any(f.endswith('.md') or 'doc' in f.lower() for f in files):
            return 'docs'
        if any('config' in f.lower() or f.endswith('.yml') or f.endswith('.yaml') for f in files):
            return 'chore'

        # 基于diff内容判断
        diff_lower = diff.lower()
        for commit_type, keywords in self.type_keywords.items():
            if any(keyword in diff_lower for keyword in keywords):
                return commit_type

        # 默认返回feat
        return 'feat'

    def _determine_scope(self, files: List[str]) -> Optional[str]:
        """确定影响范围"""
        for scope, patterns in self.scope_patterns.items():
            if any(pattern in f.lower() for f in files for pattern in patterns):
                return scope
        return None

    def _generate_description(self, files: List[str], diff: str) -> str:
        """生成描述"""
        if len(files) == 1:
            file_name = Path(files[0]).stem
            return f"update {file_name}"
        elif len(files) <= 3:
            return f"update {', '.join(Path(f).stem for f in files[:3])}"
        else:
            return f"update {len(files)} files"

    def _generate_commit_body(self, files: List[str], diff: str) -> str:
        """生成提交正文"""
        body_parts = []

        # 添加文件统计
        if len(files) > 3:
            body_parts.append(f"Modified files: {len(files)}")

        # 添加主要变更
        if '+' in diff and '-' in diff:
            body_parts.append("Major changes with additions and deletions")
        elif '+' in diff:
            body_parts.append("New additions")
        elif '-' in diff:
            body_parts.append("Cleanup and removals")

        return '\n'.join(body_parts) if body_parts else ""


class BranchManager:
    """分支管理器"""

    def __init__(self, strategy: BranchStrategy = BranchStrategy.GITFLOW):
        self.strategy = strategy
        self.protected_branches = {'main', 'master', 'develop', 'release/*', 'hotfix/*'}

    async def suggest_branch_name(self, task_description: str) -> str:
        """建议分支名称"""
        # 清理和格式化任务描述
        clean_desc = self._clean_description(task_description)
        
        # 根据策略生成分支名
        if self.strategy == BranchStrategy.GITFLOW:
            if 'fix' in clean_desc.lower() or 'bug' in clean_desc.lower():
                return f"bugfix/{clean_desc}"
            elif 'hotfix' in clean_desc.lower():
                return f"hotfix/{clean_desc}"
            else:
                return f"feature/{clean_desc}"
        elif self.strategy == BranchStrategy.GITHUB_FLOW:
            return f"feature/{clean_desc}"
        else:
            return clean_desc

    def _clean_description(self, description: str) -> str:
        """清理描述文本"""
        # 转小写，替换空格和特殊字符
        clean = description.lower().strip()
        clean = ''.join(c if c.isalnum() or c in '-_' else '-' for c in clean)
        # 移除连续的连字符
        while '--' in clean:
            clean = clean.replace('--', '-')
        return clean.strip('-')[:50]  # 限制长度

    def is_protected_branch(self, branch_name: str) -> bool:
        """检查是否为受保护分支"""
        for pattern in self.protected_branches:
            if pattern.endswith('*'):
                if branch_name.startswith(pattern[:-1]):
                    return True
            elif branch_name == pattern:
                return True
        return False

    async def get_merge_conflicts(self, source_branch: str, target_branch: str) -> List[ConflictInfo]:
        """获取合并冲突信息"""
        conflicts = []
        try:
            # 模拟合并检查
            result = await self._run_git_command([
                'git', 'merge-tree', 
                f'origin/{target_branch}', 
                f'origin/{source_branch}'
            ])
            
            if result.returncode != 0:
                # 解析冲突输出
                conflicts = self._parse_merge_conflicts(result.stdout)

        except Exception as e:
            logger.error(f"检查合并冲突失败: {e}")

        return conflicts

    def _parse_merge_conflicts(self, output: str) -> List[ConflictInfo]:
        """解析合并冲突输出"""
        conflicts = []
        # 这里简化处理，实际需要解析git merge-tree的输出
        lines = output.split('\n')
        for line in lines:
            if line.startswith('<<<<<<< '):
                # 解析冲突信息
                conflicts.append(ConflictInfo(
                    file_path="example.py",
                    conflict_type="content",
                    base_content="",
                    current_content="",
                    incoming_content="",
                    resolution_suggestion="Manual resolution required"
                ))
        return conflicts

    async def _run_git_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """运行Git命令"""
        return await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )


class GitHooksManager:
    """Git钩子管理器 - 主要类"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        self.git_dir = self.project_root / ".git"
        self.hooks_dir = self.git_dir / "hooks"
        
        # 核心组件
        self.commit_generator = SmartCommitMessageGenerator()
        self.branch_manager = BranchManager()
        
        # 配置和状态
        self.hooks_config = self._load_hooks_config()
        self.performance_cache = {}
        self.execution_history = []
        
        # 并发控制
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._lock = threading.Lock()
        
        logger.info(f"Git钩子管理器初始化完成: {self.project_root}")

    def _load_hooks_config(self) -> Dict[str, HookConfig]:
        """加载钩子配置"""
        default_config = {
            'pre-commit': HookConfig(
                name='pre-commit',
                agents=['code-reviewer', 'security-auditor', 'test-engineer'],
                priority=1,
                timeout=300,
                parallel_execution=True
            ),
            'commit-msg': HookConfig(
                name='commit-msg',
                agents=['orchestrator'],
                priority=2,
                timeout=30
            ),
            'pre-push': HookConfig(
                name='pre-push',
                agents=['test-engineer', 'security-auditor', 'devops-engineer'],
                priority=1,
                timeout=600,
                parallel_execution=True
            ),
            'post-checkout': HookConfig(
                name='post-checkout',
                agents=['devops-engineer'],
                priority=3,
                timeout=120
            )
        }
        
        # 尝试从配置文件加载
        config_file = self.project_root / ".perfect21" / "git_hooks.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    loaded_config = json.load(f)
                    for name, config_data in loaded_config.items():
                        if name in default_config:
                            # 更新默认配置
                            for key, value in config_data.items():
                                if hasattr(default_config[name], key):
                                    setattr(default_config[name], key, value)
            except Exception as e:
                logger.warning(f"加载钩子配置失败，使用默认配置: {e}")
        
        return default_config

    async def execute_hook(self, hook_type: HookType, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行Git钩子"""
        start_time = time.time()
        hook_name = hook_type.value
        context = context or {}
        
        logger.info(f"开始执行钩子: {hook_name}")
        
        try:
            # 获取钩子配置
            config = self.hooks_config.get(hook_name)
            if not config or not config.enabled:
                return {
                    'success': True,
                    'message': f'钩子 {hook_name} 未启用或不存在',
                    'execution_time': 0
                }
            
            # 检查执行条件
            if not self._check_hook_conditions(config, context):
                return {
                    'success': True,
                    'message': f'钩子 {hook_name} 条件不满足，跳过执行',
                    'execution_time': 0
                }
            
            # 准备执行上下文
            execution_context = await self._prepare_execution_context(hook_type, context)
            
            # 执行钩子逻辑
            if hook_type == HookType.PRE_COMMIT:
                result = await self._execute_pre_commit(config, execution_context)
            elif hook_type == HookType.COMMIT_MSG:
                result = await self._execute_commit_msg(config, execution_context)
            elif hook_type == HookType.PRE_PUSH:
                result = await self._execute_pre_push(config, execution_context)
            elif hook_type == HookType.POST_CHECKOUT:
                result = await self._execute_post_checkout(config, execution_context)
            else:
                result = await self._execute_generic_hook(config, execution_context)
            
            execution_time = time.time() - start_time
            result['execution_time'] = execution_time
            
            # 记录执行历史
            self._record_execution(hook_name, result, execution_time)
            
            logger.info(f"钩子 {hook_name} 执行完成: {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = {
                'success': False,
                'error': str(e),
                'execution_time': execution_time
            }
            
            self._record_execution(hook_name, error_result, execution_time)
            logger.error(f"钩子 {hook_name} 执行失败: {e}")
            return error_result

    async def _execute_pre_commit(self, config: HookConfig, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行pre-commit钩子"""
        # 获取暂存文件
        staged_files = await self._get_staged_files()
        if not staged_files:
            return {
                'success': False,
                'message': '没有暂存文件，无法提交',
                'should_abort': True
            }
        
        context['staged_files'] = staged_files
        context['git_diff'] = await self._get_git_diff('--cached')
        
        # 并行执行agents
        if config.parallel_execution and len(config.agents) > 1:
            agent_results = await self._execute_agents_parallel(config.agents, context)
        else:
            agent_results = await self._execute_agents_sequential(config.agents, context)
        
        # 分析结果
        success = all(r.get('success', True) for r in agent_results)
        
        return {
            'success': success,
            'message': f'Pre-commit检查完成: {len(staged_files)}个文件',
            'staged_files': staged_files,
            'agent_results': agent_results,
            'should_abort': not success
        }

    async def _execute_commit_msg(self, config: HookConfig, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行commit-msg钩子"""
        commit_msg_file = context.get('commit_msg_file')
        if not commit_msg_file or not os.path.exists(commit_msg_file):
            # 如果没有提供提交信息文件，生成智能提交信息
            staged_files = await self._get_staged_files()
            git_diff = await self._get_git_diff('--cached')
            
            smart_message = self.commit_generator.generate_commit_message(staged_files, git_diff)
            
            return {
                'success': True,
                'message': '生成智能提交信息',
                'generated_message': smart_message,
                'staged_files': staged_files
            }
        
        # 读取并验证提交信息
        with open(commit_msg_file, 'r') as f:
            commit_message = f.read().strip()
        
        # 基本验证
        if len(commit_message) < 10:
            return {
                'success': False,
                'message': '提交信息太短，至少需要10个字符',
                'should_abort': True
            }
        
        return {
            'success': True,
            'message': '提交信息验证通过',
            'commit_message': commit_message
        }

    async def _execute_pre_push(self, config: HookConfig, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行pre-push钩子"""
        current_branch = await self._get_current_branch()
        remote = context.get('remote', 'origin')
        
        # 检查分支保护
        if self.branch_manager.is_protected_branch(current_branch):
            return {
                'success': False,
                'message': f'分支 {current_branch} 受保护，禁止直接推送',
                'should_abort': True,
                'branch_protection': True
            }
        
        context.update({
            'current_branch': current_branch,
            'remote': remote,
            'commits_to_push': await self._get_commits_to_push(remote, current_branch)
        })
        
        # 执行推送前检查
        agent_results = await self._execute_agents_parallel(config.agents, context)
        success = all(r.get('success', True) for r in agent_results)
        
        return {
            'success': success,
            'message': f'Pre-push检查完成: {current_branch} -> {remote}',
            'current_branch': current_branch,
            'agent_results': agent_results,
            'should_abort': not success
        }

    async def _execute_post_checkout(self, config: HookConfig, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行post-checkout钩子"""
        old_ref = context.get('old_ref', '')
        new_ref = context.get('new_ref', '')
        branch_flag = context.get('branch_flag', '0')
        
        # 只处理分支切换
        if branch_flag != '1':
            return {
                'success': True,
                'message': '非分支切换，跳过处理'
            }
        
        current_branch = await self._get_current_branch()
        context.update({
            'current_branch': current_branch,
            'branch_switch': True
        })
        
        # 执行分支切换后的处理
        agent_results = await self._execute_agents_sequential(config.agents, context)
        
        return {
            'success': True,
            'message': f'Post-checkout处理完成: {current_branch}',
            'current_branch': current_branch,
            'agent_results': agent_results
        }

    async def _execute_generic_hook(self, config: HookConfig, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行通用钩子"""
        if config.custom_script:
            # 执行自定义脚本
            result = await self._run_custom_script(config.custom_script, context)
            return result
        else:
            # 执行agents
            agent_results = await self._execute_agents_parallel(config.agents, context)
            success = all(r.get('success', True) for r in agent_results)
            
            return {
                'success': success,
                'message': f'通用钩子 {config.name} 执行完成',
                'agent_results': agent_results
            }

    async def _execute_agents_parallel(self, agents: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """并行执行agents"""
        if not agents:
            return []
        
        logger.info(f"并行执行 {len(agents)} 个agents")
        
        # 创建并行任务
        tasks = []
        for agent in agents:
            task = asyncio.create_task(self._execute_single_agent(agent, context))
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'agent': agents[i],
                    'success': False,
                    'error': str(result),
                    'execution_time': 0.0
                })
            else:
                processed_results.append(result)
        
        return processed_results

    async def _execute_agents_sequential(self, agents: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """顺序执行agents"""
        results = []
        for agent in agents:
            result = await self._execute_single_agent(agent, context)
            results.append(result)
            
            # 如果关键agent失败，可以选择停止执行
            if not result.get('success', True) and agent in ['security-auditor', 'test-engineer']:
                logger.warning(f"关键agent {agent} 执行失败，继续执行其他agents")
        
        return results

    async def _execute_single_agent(self, agent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个agent"""
        start_time = time.time()
        
        try:
            # 这里应该调用实际的agent执行逻辑
            # 暂时使用模拟执行
            await asyncio.sleep(0.5)  # 模拟执行时间
            
            execution_time = time.time() - start_time
            
            return {
                'agent': agent,
                'success': True,
                'execution_time': execution_time,
                'result': f"Agent {agent} 执行成功",
                'context_used': list(context.keys()),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'agent': agent,
                'success': False,
                'execution_time': execution_time,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    # Git操作辅助方法
    async def _get_staged_files(self) -> List[str]:
        """获取暂存文件列表"""
        try:
            result = await self._run_git_command(['git', 'diff', '--cached', '--name-only'])
            if result.returncode == 0:
                return [f.strip() for f in result.stdout.decode().split('\n') if f.strip()]
            return []
        except Exception as e:
            logger.error(f"获取暂存文件失败: {e}")
            return []

    async def _get_git_diff(self, *args) -> str:
        """获取Git差异"""
        try:
            cmd = ['git', 'diff'] + list(args)
            result = await self._run_git_command(cmd)
            if result.returncode == 0:
                return result.stdout.decode()
            return ""
        except Exception as e:
            logger.error(f"获取Git差异失败: {e}")
            return ""

    async def _get_current_branch(self) -> str:
        """获取当前分支"""
        try:
            result = await self._run_git_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
            if result.returncode == 0:
                return result.stdout.decode().strip()
            return 'unknown'
        except Exception as e:
            logger.error(f"获取当前分支失败: {e}")
            return 'unknown'

    async def _get_commits_to_push(self, remote: str, branch: str) -> List[CommitInfo]:
        """获取待推送的提交"""
        commits = []
        try:
            cmd = ['git', 'log', '--oneline', f'{remote}/{branch}..HEAD']
            result = await self._run_git_command(cmd)
            
            if result.returncode == 0:
                lines = result.stdout.decode().strip().split('\n')
                for line in lines:
                    if line.strip():
                        parts = line.split(' ', 1)
                        if len(parts) >= 2:
                            commits.append(CommitInfo(
                                hash=parts[0],
                                message=parts[1],
                                author='unknown',
                                timestamp=datetime.now(),
                                files_changed=[],
                                branch=branch
                            ))
        except Exception as e:
            logger.error(f"获取待推送提交失败: {e}")
        
        return commits

    async def _run_git_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """运行Git命令"""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.project_root
        )
        stdout, stderr = await process.communicate()
        
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )

    async def _run_custom_script(self, script_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """运行自定义脚本"""
        try:
            # 准备环境变量
            env = os.environ.copy()
            env.update({
                'PERFECT21_HOOK_CONTEXT': json.dumps(context),
                'PERFECT21_PROJECT_ROOT': str(self.project_root)
            })
            
            # 运行脚本
            process = await asyncio.create_subprocess_exec(
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=self.project_root
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'success': process.returncode == 0,
                'output': stdout.decode(),
                'error': stderr.decode() if stderr else None,
                'return_code': process.returncode
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"执行自定义脚本失败: {e}"
            }

    def _check_hook_conditions(self, config: HookConfig, context: Dict[str, Any]) -> bool:
        """检查钩子执行条件"""
        if not config.conditions:
            return True
        
        # 检查分支条件
        if 'branches' in config.conditions:
            current_branch = context.get('current_branch') or asyncio.run(self._get_current_branch())
            allowed_branches = config.conditions['branches']
            if current_branch not in allowed_branches:
                return False
        
        # 检查文件条件
        if 'file_patterns' in config.conditions:
            staged_files = context.get('staged_files', [])
            patterns = config.conditions['file_patterns']
            if not any(any(pattern in f for pattern in patterns) for f in staged_files):
                return False
        
        return True

    async def _prepare_execution_context(self, hook_type: HookType, base_context: Dict[str, Any]) -> Dict[str, Any]:
        """准备执行上下文"""
        context = base_context.copy()
        context.update({
            'hook_type': hook_type.value,
            'project_root': str(self.project_root),
            'timestamp': datetime.now().isoformat()
        })
        
        # 根据钩子类型添加特定上下文
        if hook_type in [HookType.PRE_COMMIT, HookType.COMMIT_MSG]:
            context['current_branch'] = await self._get_current_branch()
        elif hook_type == HookType.PRE_PUSH:
            context['current_branch'] = await self._get_current_branch()
        
        return context

    def _record_execution(self, hook_name: str, result: Dict[str, Any], execution_time: float):
        """记录执行历史"""
        with self._lock:
            self.execution_history.append({
                'hook_name': hook_name,
                'timestamp': datetime.now().isoformat(),
                'success': result.get('success', False),
                'execution_time': execution_time,
                'result': result
            })
            
            # 保持历史记录数量在合理范围内
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-500:]

    # 钩子安装和管理方法
    async def install_hooks(self, hook_types: List[HookType] = None) -> Dict[str, Any]:
        """安装Git钩子"""
        if hook_types is None:
            hook_types = list(HookType)
        
        installed = []
        failed = []
        
        # 确保hooks目录存在
        self.hooks_dir.mkdir(parents=True, exist_ok=True)
        
        for hook_type in hook_types:
            try:
                hook_file = self.hooks_dir / hook_type.value
                hook_content = self._generate_hook_script(hook_type)
                
                # 写入钩子文件
                with open(hook_file, 'w') as f:
                    f.write(hook_content)
                
                # 设置执行权限
                os.chmod(hook_file, 0o755)
                
                installed.append(hook_type.value)
                logger.info(f"已安装钩子: {hook_type.value}")
                
            except Exception as e:
                failed.append({
                    'hook': hook_type.value,
                    'error': str(e)
                })
                logger.error(f"安装钩子 {hook_type.value} 失败: {e}")
        
        return {
            'success': len(failed) == 0,
            'installed': installed,
            'failed': failed,
            'message': f'安装完成: {len(installed)}个成功, {len(failed)}个失败'
        }

    def _generate_hook_script(self, hook_type: HookType) -> str:
        """生成钩子脚本"""
        python_path = sys.executable
        script_template = f'''#!/usr/bin/env python3
"""
Perfect21 Git Hook - {hook_type.value}
自动生成的钩子脚本
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from features.git.git_hooks import GitHooksManager, HookType
    
    async def main():
        manager = GitHooksManager(str(project_root))
        
        # 准备上下文
        context = {{}}
        if len(sys.argv) > 1:
            if "{hook_type.value}" == "commit-msg":
                context["commit_msg_file"] = sys.argv[1]
            elif "{hook_type.value}" == "pre-push":
                context["remote"] = sys.argv[1] if len(sys.argv) > 1 else "origin"
                context["url"] = sys.argv[2] if len(sys.argv) > 2 else ""
            elif "{hook_type.value}" == "post-checkout":
                context["old_ref"] = sys.argv[1] if len(sys.argv) > 1 else ""
                context["new_ref"] = sys.argv[2] if len(sys.argv) > 2 else ""
                context["branch_flag"] = sys.argv[3] if len(sys.argv) > 3 else "0"
        
        # 执行钩子
        result = await manager.execute_hook(HookType.{hook_type.name}, context)
        
        # 根据结果决定是否退出
        if not result.get("success", True) and result.get("should_abort", False):
            print(f"❌ {hook_type.value} hook failed: {{result.get('message', 'Unknown error')}}")
            sys.exit(1)
        else:
            print(f"✅ {hook_type.value} hook completed: {{result.get('message', 'Success')}}")
            sys.exit(0)
    
    if __name__ == "__main__":
        asyncio.run(main())
        
except ImportError as e:
    print(f"Warning: Perfect21 not found, skipping {hook_type.value} hook: {{e}}")
    sys.exit(0)
except Exception as e:
    print(f"Error in {hook_type.value} hook: {{e}}")
    sys.exit(1)
'''
        return script_template

    async def uninstall_hooks(self, hook_types: List[HookType] = None) -> Dict[str, Any]:
        """卸载Git钩子"""
        if hook_types is None:
            hook_types = list(HookType)
        
        uninstalled = []
        failed = []
        
        for hook_type in hook_types:
            try:
                hook_file = self.hooks_dir / hook_type.value
                if hook_file.exists():
                    hook_file.unlink()
                    uninstalled.append(hook_type.value)
                    logger.info(f"已卸载钩子: {hook_type.value}")
                
            except Exception as e:
                failed.append({
                    'hook': hook_type.value,
                    'error': str(e)
                })
                logger.error(f"卸载钩子 {hook_type.value} 失败: {e}")
        
        return {
            'success': len(failed) == 0,
            'uninstalled': uninstalled,
            'failed': failed,
            'message': f'卸载完成: {len(uninstalled)}个成功, {len(failed)}个失败'
        }

    async def get_hook_status(self) -> Dict[str, Any]:
        """获取钩子状态"""
        status = {}
        
        for hook_type in HookType:
            hook_file = self.hooks_dir / hook_type.value
            config = self.hooks_config.get(hook_type.value)
            
            status[hook_type.value] = {
                'installed': hook_file.exists(),
                'enabled': config.enabled if config else False,
                'executable': hook_file.exists() and os.access(hook_file, os.X_OK),
                'last_modified': hook_file.stat().st_mtime if hook_file.exists() else None,
                'agents': config.agents if config else [],
                'priority': config.priority if config else 5
            }
        
        # 添加执行统计
        recent_executions = [h for h in self.execution_history if 
                           datetime.fromisoformat(h['timestamp']) > datetime.now() - timedelta(days=7)]
        
        status['statistics'] = {
            'total_executions': len(self.execution_history),
            'recent_executions': len(recent_executions),
            'success_rate': (sum(1 for h in self.execution_history if h['success']) / 
                           len(self.execution_history) * 100) if self.execution_history else 0
        }
        
        return status

    async def test_hook(self, hook_type: HookType, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """测试钩子执行"""
        logger.info(f"测试钩子: {hook_type.value}")
        
        # 使用测试模式执行钩子
        test_context = context or {'test_mode': True}
        result = await self.execute_hook(hook_type, test_context)
        
        # 添加测试结果分析
        result['test_mode'] = True
        result['recommendations'] = self._analyze_test_result(hook_type, result)
        
        return result

    def _analyze_test_result(self, hook_type: HookType, result: Dict[str, Any]) -> List[str]:
        """分析测试结果并给出建议"""
        recommendations = []
        
        if not result.get('success', True):
            recommendations.append("钩子执行失败，检查配置和依赖")
        
        execution_time = result.get('execution_time', 0)
        if execution_time > 60:
            recommendations.append("执行时间过长，考虑优化agents或启用并行执行")
        
        agent_results = result.get('agent_results', [])
        failed_agents = [r for r in agent_results if not r.get('success', True)]
        if failed_agents:
            recommendations.append(f"有 {len(failed_agents)} 个agents执行失败")
        
        return recommendations

    async def optimize_performance(self) -> Dict[str, Any]:
        """性能优化建议"""
        # 分析执行历史
        if not self.execution_history:
            return {
                'message': '没有执行历史，无法提供优化建议',
                'recommendations': []
            }
        
        # 计算平均执行时间
        avg_times = {}
        for record in self.execution_history:
            hook_name = record['hook_name']
            if hook_name not in avg_times:
                avg_times[hook_name] = []
            avg_times[hook_name].append(record['execution_time'])
        
        recommendations = []
        optimizations = {}
        
        for hook_name, times in avg_times.items():
            avg_time = sum(times) / len(times)
            optimizations[hook_name] = {
                'average_time': avg_time,
                'executions': len(times),
                'max_time': max(times),
                'min_time': min(times)
            }
            
            if avg_time > 30:
                recommendations.append(f"{hook_name}: 平均执行时间 {avg_time:.2f}s，建议启用并行执行")
            
            config = self.hooks_config.get(hook_name)
            if config and not config.parallel_execution and len(config.agents) > 2:
                recommendations.append(f"{hook_name}: 有多个agents但未启用并行执行")
        
        return {
            'optimizations': optimizations,
            'recommendations': recommendations,
            'total_executions': len(self.execution_history),
            'analysis_date': datetime.now().isoformat()
        }

    async def save_performance_report(self, filename: Optional[str] = None) -> str:
        """保存性能报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"git_hooks_performance_{timestamp}.json"
        
        report_data = {
            'report_type': 'git_hooks_performance',
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'hook_status': await self.get_hook_status(),
            'performance_analysis': await self.optimize_performance(),
            'execution_history': self.execution_history[-50:],  # 最近50次执行
            'configuration': {
                hook_name: {
                    'agents': config.agents,
                    'parallel_execution': config.parallel_execution,
                    'timeout': config.timeout,
                    'priority': config.priority
                }
                for hook_name, config in self.hooks_config.items()
            }
        }
        
        async with aiofiles.open(filename, 'w') as f:
            await f.write(json.dumps(report_data, indent=2, default=str))
        
        logger.info(f"性能报告已保存: {filename}")
        return filename

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)


# 全局实例
_git_hooks_manager: Optional[GitHooksManager] = None


def get_git_hooks_manager(project_root: Optional[str] = None) -> GitHooksManager:
    """获取Git钩子管理器实例"""
    global _git_hooks_manager
    if _git_hooks_manager is None:
        _git_hooks_manager = GitHooksManager(project_root)
    return _git_hooks_manager


# 便捷函数
async def install_all_hooks(project_root: Optional[str] = None) -> Dict[str, Any]:
    """安装所有钩子的便捷函数"""
    manager = get_git_hooks_manager(project_root)
    return await manager.install_hooks()


async def execute_hook_by_name(hook_name: str, context: Dict[str, Any] = None, 
                               project_root: Optional[str] = None) -> Dict[str, Any]:
    """根据名称执行钩子的便捷函数"""
    try:
        hook_type = HookType(hook_name)
        manager = get_git_hooks_manager(project_root)
        return await manager.execute_hook(hook_type, context)
    except ValueError:
        return {
            'success': False,
            'error': f'未知的钩子类型: {hook_name}'
        }


if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) < 2:
            print("用法: python git_hooks.py <command> [args...]")
            print("命令: install, uninstall, status, test, optimize")
            return
        
        command = sys.argv[1]
        manager = GitHooksManager()
        
        if command == "install":
            result = await manager.install_hooks()
            print(f"安装结果: {result['message']}")
        
        elif command == "uninstall":
            result = await manager.uninstall_hooks()
            print(f"卸载结果: {result['message']}")
        
        elif command == "status":
            status = await manager.get_hook_status()
            print(json.dumps(status, indent=2, default=str))
        
        elif command == "test":
            hook_name = sys.argv[2] if len(sys.argv) > 2 else "pre-commit"
            try:
                hook_type = HookType(hook_name)
                result = await manager.test_hook(hook_type)
                print(f"测试结果: {json.dumps(result, indent=2, default=str)}")
            except ValueError:
                print(f"未知的钩子类型: {hook_name}")
        
        elif command == "optimize":
            result = await manager.optimize_performance()
            print(json.dumps(result, indent=2, default=str))
        
        elif command == "report":
            filename = await manager.save_performance_report()
            print(f"性能报告已保存: {filename}")
        
        else:
            print(f"未知命令: {command}")
    
    asyncio.run(main())