#!/usr/bin/env python3
"""
Perfect21 Git Integration - 增强版Git集成
智能Git工作流管理，自动化分支策略，性能优化
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
import re
import threading
from concurrent.futures import ThreadPoolExecutor
import aiofiles

from .git_hooks import GitHooksManager, HookType

logger = logging.getLogger("Perfect21GitIntegration")


class WorkflowType(Enum):
    """工作流类型"""
    FEATURE_DEVELOPMENT = "feature_development"
    BUG_FIX = "bug_fix"
    HOTFIX = "hotfix"
    RELEASE_PREPARATION = "release_preparation"
    MAINTENANCE = "maintenance"


class MergeStrategy(Enum):
    """合并策略"""
    FAST_FORWARD = "fast-forward"
    NO_FF = "no-ff"
    SQUASH = "squash"
    REBASE = "rebase"


@dataclass
class WorkflowConfig:
    """工作流配置"""
    name: str
    description: str
    branch_pattern: str
    merge_strategy: MergeStrategy
    require_pr: bool = True
    auto_delete_branch: bool = True
    quality_gates: List[str] = field(default_factory=list)
    notification_channels: List[str] = field(default_factory=list)


@dataclass
class BranchInfo:
    """分支信息"""
    name: str
    hash: str
    upstream: Optional[str]
    last_commit: datetime
    commits_ahead: int = 0
    commits_behind: int = 0
    is_clean: bool = True
    protection_rules: List[str] = field(default_factory=list)


@dataclass
class GitOperation:
    """Git操作记录"""
    operation_type: str
    timestamp: datetime
    branch: str
    success: bool
    details: Dict[str, Any]
    execution_time: float = 0.0
    error_message: Optional[str] = None


class GitHistoryAnalyzer:
    """Git历史分析器"""

    def __init__(self, project_root: str):
        self.project_root = project_root

    async def analyze_commit_patterns(self, days: int = 30) -> Dict[str, Any]:
        """分析提交模式"""
        try:
            # 获取最近的提交历史
            since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            result = await self._run_git_command([
                'git', 'log', '--since', since_date, '--pretty=format:%h|%an|%ad|%s', '--date=iso'
            ])
            
            if result.returncode != 0:
                return {'error': 'Failed to get commit history'}
            
            commits = []
            for line in result.stdout.decode().strip().split('\n'):
                if line:
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        commits.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'date': parts[2],
                            'message': parts[3]
                        })
            
            # 分析模式
            analysis = {
                'total_commits': len(commits),
                'unique_authors': len(set(c['author'] for c in commits)),
                'commit_types': self._analyze_commit_types(commits),
                'activity_pattern': self._analyze_activity_pattern(commits),
                'author_stats': self._analyze_author_stats(commits)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析提交模式失败: {e}")
            return {'error': str(e)}

    def _analyze_commit_types(self, commits: List[Dict]) -> Dict[str, int]:
        """分析提交类型"""
        types = {}
        type_patterns = {
            'feat': r'^(feat|feature)',
            'fix': r'^(fix|bugfix)',
            'docs': r'^(docs|doc)',
            'style': r'^(style|format)',
            'refactor': r'^refactor',
            'test': r'^test',
            'chore': r'^chore'
        }
        
        for commit in commits:
            message = commit['message'].lower()
            matched = False
            
            for commit_type, pattern in type_patterns.items():
                if re.search(pattern, message):
                    types[commit_type] = types.get(commit_type, 0) + 1
                    matched = True
                    break
            
            if not matched:
                types['other'] = types.get('other', 0) + 1
        
        return types

    def _analyze_activity_pattern(self, commits: List[Dict]) -> Dict[str, Any]:
        """分析活动模式"""
        hourly_activity = {str(i): 0 for i in range(24)}
        daily_activity = {}
        
        for commit in commits:
            try:
                # 解析时间戳
                commit_time = datetime.fromisoformat(commit['date'].replace(' ', 'T'))
                hour = str(commit_time.hour)
                date = commit_time.date().isoformat()
                
                hourly_activity[hour] += 1
                daily_activity[date] = daily_activity.get(date, 0) + 1
                
            except Exception:
                continue
        
        return {
            'hourly_distribution': hourly_activity,
            'most_active_hour': max(hourly_activity, key=hourly_activity.get),
            'daily_activity': daily_activity,
            'average_commits_per_day': len(commits) / max(len(daily_activity), 1)
        }

    def _analyze_author_stats(self, commits: List[Dict]) -> Dict[str, Any]:
        """分析作者统计"""
        author_stats = {}
        
        for commit in commits:
            author = commit['author']
            if author not in author_stats:
                author_stats[author] = {
                    'commits': 0,
                    'first_commit': commit['date'],
                    'last_commit': commit['date']
                }
            
            author_stats[author]['commits'] += 1
            # 更新最新提交时间
            if commit['date'] > author_stats[author]['last_commit']:
                author_stats[author]['last_commit'] = commit['date']
        
        # 按提交数排序
        sorted_authors = sorted(author_stats.items(), key=lambda x: x[1]['commits'], reverse=True)
        
        return {
            'top_contributors': dict(sorted_authors[:5]),
            'total_contributors': len(author_stats),
            'most_active_author': sorted_authors[0][0] if sorted_authors else None
        }

    async def detect_code_hotspots(self) -> Dict[str, Any]:
        """检测代码热点（频繁修改的文件）"""
        try:
            # 获取文件修改频率
            result = await self._run_git_command([
                'git', 'log', '--name-only', '--pretty=format:', '--since=3.months'
            ])
            
            if result.returncode != 0:
                return {'error': 'Failed to get file change history'}
            
            file_changes = {}
            for line in result.stdout.decode().strip().split('\n'):
                if line and not line.startswith(' '):
                    file_changes[line] = file_changes.get(line, 0) + 1
            
            # 排序并获取热点文件
            hotspots = sorted(file_changes.items(), key=lambda x: x[1], reverse=True)[:20]
            
            return {
                'total_files_changed': len(file_changes),
                'hotspots': dict(hotspots),
                'analysis_period': '3 months',
                'recommendations': self._generate_hotspot_recommendations(hotspots)
            }
            
        except Exception as e:
            logger.error(f"检测代码热点失败: {e}")
            return {'error': str(e)}

    def _generate_hotspot_recommendations(self, hotspots: List[Tuple[str, int]]) -> List[str]:
        """生成热点代码建议"""
        recommendations = []
        
        if not hotspots:
            return recommendations
        
        top_file, changes = hotspots[0]
        if changes > 50:
            recommendations.append(f"文件 {top_file} 修改频率过高 ({changes} 次)，考虑重构")
        
        config_files = [f for f, c in hotspots if f.endswith(('.json', '.yaml', '.yml', '.ini'))]
        if config_files:
            recommendations.append("配置文件修改频繁，考虑使用环境变量或配置管理工具")
        
        test_files = [f for f, c in hotspots if 'test' in f.lower()]
        if len(test_files) > len(hotspots) * 0.3:
            recommendations.append("测试文件修改较多，这通常是好现象，说明在积极维护测试")
        
        return recommendations

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


class ConflictResolver:
    """冲突解决助手"""

    def __init__(self, project_root: str):
        self.project_root = project_root

    async def detect_potential_conflicts(self, source_branch: str, target_branch: str) -> Dict[str, Any]:
        """检测潜在冲突"""
        try:
            # 获取两个分支的差异文件
            cmd = ['git', 'diff', '--name-only', f'{target_branch}...{source_branch}']
            result = await self._run_git_command(cmd)
            
            if result.returncode != 0:
                return {'error': 'Failed to get branch differences'}
            
            changed_files = [f.strip() for f in result.stdout.decode().split('\n') if f.strip()]
            
            # 检查目标分支中相同文件的最新更改
            conflicts = []
            for file_path in changed_files:
                file_conflicts = await self._check_file_conflicts(file_path, source_branch, target_branch)
                if file_conflicts:
                    conflicts.extend(file_conflicts)
            
            return {
                'potential_conflicts': len(conflicts),
                'changed_files': len(changed_files),
                'conflict_details': conflicts[:10],  # 限制返回数量
                'recommendations': self._generate_conflict_recommendations(conflicts)
            }
            
        except Exception as e:
            logger.error(f"检测潜在冲突失败: {e}")
            return {'error': str(e)}

    async def _check_file_conflicts(self, file_path: str, source_branch: str, target_branch: str) -> List[Dict]:
        """检查单个文件的冲突"""
        conflicts = []
        
        try:
            # 获取文件在两个分支中的最后修改时间
            source_cmd = ['git', 'log', '-1', '--format=%ad', '--date=iso', source_branch, '--', file_path]
            target_cmd = ['git', 'log', '-1', '--format=%ad', '--date=iso', target_branch, '--', file_path]
            
            source_result = await self._run_git_command(source_cmd)
            target_result = await self._run_git_command(target_cmd)
            
            if source_result.returncode == 0 and target_result.returncode == 0:
                source_time = source_result.stdout.decode().strip()
                target_time = target_result.stdout.decode().strip()
                
                # 如果两个分支都修改了同一文件
                if source_time and target_time:
                    conflicts.append({
                        'file': file_path,
                        'type': 'modification_conflict',
                        'source_last_modified': source_time,
                        'target_last_modified': target_time,
                        'risk_level': 'medium'
                    })
            
        except Exception as e:
            logger.warning(f"检查文件 {file_path} 冲突失败: {e}")
        
        return conflicts

    def _generate_conflict_recommendations(self, conflicts: List[Dict]) -> List[str]:
        """生成冲突解决建议"""
        recommendations = []
        
        if not conflicts:
            recommendations.append("未发现潜在冲突，可以安全合并")
            return recommendations
        
        high_risk = [c for c in conflicts if c.get('risk_level') == 'high']
        if high_risk:
            recommendations.append(f"发现 {len(high_risk)} 个高风险冲突，建议人工审查")
        
        config_conflicts = [c for c in conflicts if c['file'].endswith(('.json', '.yaml', '.yml'))]
        if config_conflicts:
            recommendations.append("配置文件存在冲突，请仔细检查配置项")
        
        recommendations.append("建议在本地测试环境中先进行合并测试")
        recommendations.append("考虑使用交互式合并工具解决冲突")
        
        return recommendations

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


class GitWorkflowManager:
    """Git工作流管理器 - 主要类"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        self.git_dir = self.project_root / ".git"
        
        # 组件初始化
        self.hooks_manager = GitHooksManager(str(self.project_root))
        self.history_analyzer = GitHistoryAnalyzer(str(self.project_root))
        self.conflict_resolver = ConflictResolver(str(self.project_root))
        
        # 工作流配置
        self.workflows = self._init_workflows()
        self.operation_history: List[GitOperation] = []
        
        # 性能优化
        self.executor = ThreadPoolExecutor(max_workers=3)
        self._cache = {}
        self._cache_ttl = 300  # 5分钟缓存
        
        logger.info(f"Git工作流管理器初始化完成: {self.project_root}")

    def _init_workflows(self) -> Dict[str, WorkflowConfig]:
        """初始化工作流配置"""
        return {
            'feature': WorkflowConfig(
                name='Feature Development',
                description='功能开发工作流',
                branch_pattern='feature/*',
                merge_strategy=MergeStrategy.NO_FF,
                require_pr=True,
                quality_gates=['pre-commit', 'test', 'security-scan']
            ),
            'bugfix': WorkflowConfig(
                name='Bug Fix',
                description='Bug修复工作流',
                branch_pattern='bugfix/*',
                merge_strategy=MergeStrategy.SQUASH,
                require_pr=True,
                quality_gates=['pre-commit', 'test']
            ),
            'hotfix': WorkflowConfig(
                name='Hotfix',
                description='紧急修复工作流',
                branch_pattern='hotfix/*',
                merge_strategy=MergeStrategy.FAST_FORWARD,
                require_pr=False,
                auto_delete_branch=True,
                quality_gates=['test', 'security-scan']
            ),
            'release': WorkflowConfig(
                name='Release Preparation',
                description='发布准备工作流',
                branch_pattern='release/*',
                merge_strategy=MergeStrategy.NO_FF,
                require_pr=True,
                quality_gates=['pre-commit', 'test', 'security-scan', 'performance']
            )
        }

    async def start_workflow(self, workflow_type: WorkflowType, 
                           task_description: str, 
                           base_branch: str = 'main') -> Dict[str, Any]:
        """启动工作流"""
        start_time = time.time()
        
        try:
            logger.info(f"启动工作流: {workflow_type.value} - {task_description}")
            
            # 获取工作流配置
            workflow_key = workflow_type.value.replace('_development', '').replace('_fix', 'fix').replace('_preparation', '')
            config = self.workflows.get(workflow_key)
            if not config:
                return {
                    'success': False,
                    'error': f'未知的工作流类型: {workflow_type.value}'
                }
            
            # 生成分支名称
            branch_name = await self._generate_branch_name(config, task_description)
            
            # 检查当前Git状态
            git_status = await self._get_git_status()
            if not git_status['is_clean']:
                return {
                    'success': False,
                    'error': '工作目录不干净，请先提交或暂存更改',
                    'git_status': git_status
                }
            
            # 切换到基础分支并更新
            await self._checkout_and_update_branch(base_branch)
            
            # 创建新分支
            result = await self._create_branch(branch_name)
            if not result['success']:
                return result
            
            # 安装相关hooks
            await self._setup_workflow_hooks(config)
            
            execution_time = time.time() - start_time
            
            # 记录操作
            operation = GitOperation(
                operation_type='start_workflow',
                timestamp=datetime.now(),
                branch=branch_name,
                success=True,
                details={
                    'workflow_type': workflow_type.value,
                    'task_description': task_description,
                    'base_branch': base_branch,
                    'config': config.__dict__
                },
                execution_time=execution_time
            )
            self.operation_history.append(operation)
            
            return {
                'success': True,
                'workflow_type': workflow_type.value,
                'branch_name': branch_name,
                'base_branch': base_branch,
                'config': config.__dict__,
                'execution_time': execution_time,
                'next_steps': self._get_workflow_next_steps(workflow_type)
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_operation = GitOperation(
                operation_type='start_workflow',
                timestamp=datetime.now(),
                branch='unknown',
                success=False,
                details={'error': str(e)},
                execution_time=execution_time,
                error_message=str(e)
            )
            self.operation_history.append(error_operation)
            
            logger.error(f"启动工作流失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time
            }

    async def commit_with_smart_message(self, files: List[str] = None, 
                                      custom_message: str = None) -> Dict[str, Any]:
        """智能提交，自动生成提交信息"""
        try:
            # 获取暂存文件
            if files:
                # 添加指定文件
                for file_path in files:
                    await self._run_git_command(['git', 'add', file_path])
            
            staged_files = await self._get_staged_files()
            if not staged_files:
                return {
                    'success': False,
                    'error': '没有暂存的文件'
                }
            
            # 生成或使用提交信息
            if custom_message:
                commit_message = custom_message
            else:
                # 获取diff用于智能生成
                git_diff = await self._get_git_diff(['--cached'])
                commit_message = await self._generate_smart_commit_message(staged_files, git_diff)
            
            # 执行pre-commit hook
            hook_result = await self.hooks_manager.execute_hook(HookType.PRE_COMMIT)
            if not hook_result.get('success', True) and hook_result.get('should_abort', False):
                return {
                    'success': False,
                    'error': 'Pre-commit hook失败',
                    'hook_result': hook_result
                }
            
            # 提交
            result = await self._run_git_command(['git', 'commit', '-m', commit_message])
            
            if result.returncode == 0:
                # 执行post-commit hook
                await self.hooks_manager.execute_hook(HookType.POST_COMMIT)
                
                return {
                    'success': True,
                    'commit_message': commit_message,
                    'staged_files': staged_files,
                    'commit_hash': await self._get_latest_commit_hash()
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr.decode()
                }
        
        except Exception as e:
            logger.error(f"智能提交失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def create_pull_request(self, target_branch: str = 'main', 
                                title: str = None, 
                                description: str = None) -> Dict[str, Any]:
        """创建Pull Request（模拟，实际需要集成GitHub/GitLab API）"""
        try:
            current_branch = await self._get_current_branch()
            if current_branch == target_branch:
                return {
                    'success': False,
                    'error': '不能向当前分支创建PR'
                }
            
            # 执行pre-push检查
            hook_result = await self.hooks_manager.execute_hook(
                HookType.PRE_PUSH, 
                {'remote': 'origin', 'target_branch': target_branch}
            )
            
            if not hook_result.get('success', True):
                return {
                    'success': False,
                    'error': 'Pre-push检查失败',
                    'hook_result': hook_result
                }
            
            # 检测潜在冲突
            conflicts = await self.conflict_resolver.detect_potential_conflicts(
                current_branch, target_branch
            )
            
            # 分析提交历史
            commits = await self._get_branch_commits(current_branch, target_branch)
            
            # 生成PR信息
            if not title:
                title = await self._generate_pr_title(current_branch, commits)
            
            if not description:
                description = await self._generate_pr_description(commits, conflicts)
            
            pr_info = {
                'source_branch': current_branch,
                'target_branch': target_branch,
                'title': title,
                'description': description,
                'commits_count': len(commits),
                'potential_conflicts': conflicts.get('potential_conflicts', 0),
                'quality_checks': hook_result.get('agent_results', [])
            }
            
            # 这里实际应该调用GitHub/GitLab API创建PR
            # 目前只是模拟返回PR信息
            
            return {
                'success': True,
                'pr_info': pr_info,
                'message': 'PR信息已生成，请手动在平台上创建PR',
                'recommendations': self._generate_pr_recommendations(pr_info)
            }
            
        except Exception as e:
            logger.error(f"创建PR失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def merge_branch(self, source_branch: str, target_branch: str, 
                          strategy: MergeStrategy = MergeStrategy.NO_FF) -> Dict[str, Any]:
        """合并分支"""
        try:
            logger.info(f"合并分支: {source_branch} -> {target_branch} ({strategy.value})")
            
            # 切换到目标分支
            await self._checkout_and_update_branch(target_branch)
            
            # 检测冲突
            conflicts = await self.conflict_resolver.detect_potential_conflicts(
                source_branch, target_branch
            )
            
            if conflicts.get('potential_conflicts', 0) > 0:
                return {
                    'success': False,
                    'error': '检测到潜在冲突，建议先解决冲突',
                    'conflicts': conflicts
                }
            
            # 根据策略执行合并
            if strategy == MergeStrategy.FAST_FORWARD:
                cmd = ['git', 'merge', '--ff-only', source_branch]
            elif strategy == MergeStrategy.NO_FF:
                cmd = ['git', 'merge', '--no-ff', source_branch]
            elif strategy == MergeStrategy.SQUASH:
                cmd = ['git', 'merge', '--squash', source_branch]
            else:
                return {
                    'success': False,
                    'error': f'不支持的合并策略: {strategy.value}'
                }
            
            result = await self._run_git_command(cmd)
            
            if result.returncode == 0:
                # 如果是squash合并，需要额外提交
                if strategy == MergeStrategy.SQUASH:
                    squash_message = f"Squash merge from {source_branch}"
                    await self._run_git_command(['git', 'commit', '-m', squash_message])
                
                # 执行post-merge hook
                await self.hooks_manager.execute_hook(HookType.POST_MERGE)
                
                return {
                    'success': True,
                    'source_branch': source_branch,
                    'target_branch': target_branch,
                    'strategy': strategy.value,
                    'merge_commit': await self._get_latest_commit_hash()
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr.decode(),
                    'conflicts_detected': True
                }
        
        except Exception as e:
            logger.error(f"合并分支失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def cleanup_branches(self, dry_run: bool = True) -> Dict[str, Any]:
        """清理已合并的分支"""
        try:
            # 获取所有本地分支
            result = await self._run_git_command(['git', 'branch', '--merged', 'main'])
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': '获取已合并分支失败'
                }
            
            merged_branches = []
            for line in result.stdout.decode().split('\n'):
                branch = line.strip()
                if branch and not branch.startswith('*') and branch not in ['main', 'master', 'develop']:
                    merged_branches.append(branch)
            
            if dry_run:
                return {
                    'success': True,
                    'dry_run': True,
                    'branches_to_delete': merged_branches,
                    'message': f'找到 {len(merged_branches)} 个可删除的分支'
                }
            
            # 实际删除分支
            deleted = []
            failed = []
            
            for branch in merged_branches:
                try:
                    delete_result = await self._run_git_command(['git', 'branch', '-d', branch])
                    if delete_result.returncode == 0:
                        deleted.append(branch)
                    else:
                        failed.append({
                            'branch': branch,
                            'error': delete_result.stderr.decode()
                        })
                except Exception as e:
                    failed.append({
                        'branch': branch,
                        'error': str(e)
                    })
            
            return {
                'success': len(failed) == 0,
                'deleted_branches': deleted,
                'failed_branches': failed,
                'message': f'删除 {len(deleted)} 个分支，{len(failed)} 个失败'
            }
        
        except Exception as e:
            logger.error(f"清理分支失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_project_health(self) -> Dict[str, Any]:
        """获取项目健康度报告"""
        try:
            # 并行获取各种分析数据
            tasks = [
                self.history_analyzer.analyze_commit_patterns(),
                self.history_analyzer.detect_code_hotspots(),
                self._analyze_branch_structure(),
                self._get_repository_stats()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            health_report = {
                'timestamp': datetime.now().isoformat(),
                'commit_analysis': results[0] if not isinstance(results[0], Exception) else {'error': str(results[0])},
                'code_hotspots': results[1] if not isinstance(results[1], Exception) else {'error': str(results[1])},
                'branch_structure': results[2] if not isinstance(results[2], Exception) else {'error': str(results[2])},
                'repository_stats': results[3] if not isinstance(results[3], Exception) else {'error': str(results[3])},
                'hooks_status': await self.hooks_manager.get_hook_status(),
                'workflow_history': self._get_workflow_summary(),
                'health_score': 0  # 将根据各项指标计算
            }
            
            # 计算健康度评分
            health_report['health_score'] = self._calculate_health_score(health_report)
            health_report['recommendations'] = self._generate_health_recommendations(health_report)
            
            return health_report
            
        except Exception as e:
            logger.error(f"获取项目健康度失败: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    # 辅助方法
    async def _generate_branch_name(self, config: WorkflowConfig, description: str) -> str:
        """生成分支名称"""
        # 清理描述
        clean_desc = re.sub(r'[^a-zA-Z0-9\s-]', '', description.lower())
        clean_desc = re.sub(r'\s+', '-', clean_desc.strip())[:30]
        
        # 根据配置生成
        if config.branch_pattern.startswith('feature/'):
            return f"feature/{clean_desc}-{datetime.now().strftime('%Y%m%d')}"
        elif config.branch_pattern.startswith('bugfix/'):
            return f"bugfix/{clean_desc}"
        elif config.branch_pattern.startswith('hotfix/'):
            return f"hotfix/{clean_desc}"
        elif config.branch_pattern.startswith('release/'):
            return f"release/{clean_desc}"
        else:
            return f"{clean_desc}-{datetime.now().strftime('%Y%m%d')}"

    async def _get_git_status(self) -> Dict[str, Any]:
        """获取Git状态"""
        try:
            result = await self._run_git_command(['git', 'status', '--porcelain'])
            
            is_clean = result.returncode == 0 and not result.stdout.decode().strip()
            
            return {
                'is_clean': is_clean,
                'current_branch': await self._get_current_branch(),
                'status_output': result.stdout.decode() if result.returncode == 0 else result.stderr.decode()
            }
        except Exception as e:
            return {
                'is_clean': False,
                'error': str(e)
            }

    async def _get_current_branch(self) -> str:
        """获取当前分支"""
        try:
            result = await self._run_git_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
            if result.returncode == 0:
                return result.stdout.decode().strip()
            return 'unknown'
        except Exception:
            return 'unknown'

    async def _checkout_and_update_branch(self, branch_name: str) -> bool:
        """切换并更新分支"""
        try:
            # 切换分支
            result = await self._run_git_command(['git', 'checkout', branch_name])
            if result.returncode != 0:
                return False
            
            # 拉取最新更改
            pull_result = await self._run_git_command(['git', 'pull', 'origin', branch_name])
            return pull_result.returncode == 0
            
        except Exception as e:
            logger.error(f"切换更新分支失败: {e}")
            return False

    async def _create_branch(self, branch_name: str) -> Dict[str, Any]:
        """创建分支"""
        try:
            result = await self._run_git_command(['git', 'checkout', '-b', branch_name])
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'branch_name': branch_name
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr.decode()
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def _setup_workflow_hooks(self, config: WorkflowConfig):
        """设置工作流钩子"""
        # 根据质量门要求安装相应的hooks
        hook_types = []
        
        if 'pre-commit' in config.quality_gates:
            hook_types.append(HookType.PRE_COMMIT)
        if 'test' in config.quality_gates:
            hook_types.append(HookType.PRE_PUSH)
        
        if hook_types:
            await self.hooks_manager.install_hooks(hook_types)

    def _get_workflow_next_steps(self, workflow_type: WorkflowType) -> List[str]:
        """获取工作流下一步建议"""
        if workflow_type == WorkflowType.FEATURE_DEVELOPMENT:
            return [
                "1. 开始编写功能代码",
                "2. 编写或更新测试",
                "3. 提交更改（将自动运行pre-commit检查）",
                "4. 推送到远程分支",
                "5. 创建Pull Request"
            ]
        elif workflow_type == WorkflowType.BUG_FIX:
            return [
                "1. 重现并定位问题",
                "2. 编写修复代码",
                "3. 添加回归测试",
                "4. 提交并推送更改",
                "5. 创建Pull Request"
            ]
        elif workflow_type == WorkflowType.HOTFIX:
            return [
                "1. 快速修复关键问题",
                "2. 进行基本测试",
                "3. 立即提交和推送",
                "4. 通知相关团队",
                "5. 安排后续完整测试"
            ]
        else:
            return ["根据具体需求进行开发"]

    async def _get_staged_files(self) -> List[str]:
        """获取暂存文件"""
        try:
            result = await self._run_git_command(['git', 'diff', '--cached', '--name-only'])
            if result.returncode == 0:
                return [f.strip() for f in result.stdout.decode().split('\n') if f.strip()]
            return []
        except Exception:
            return []

    async def _get_git_diff(self, args: List[str]) -> str:
        """获取Git差异"""
        try:
            cmd = ['git', 'diff'] + args
            result = await self._run_git_command(cmd)
            if result.returncode == 0:
                return result.stdout.decode()
            return ""
        except Exception:
            return ""

    async def _generate_smart_commit_message(self, staged_files: List[str], git_diff: str) -> str:
        """生成智能提交信息"""
        # 这里可以集成AI模型来生成更智能的提交信息
        # 目前使用简单的规则
        
        if len(staged_files) == 1:
            file_name = Path(staged_files[0]).stem
            if staged_files[0].endswith('.py'):
                return f"feat: update {file_name} implementation"
            elif staged_files[0].endswith(('.md', '.txt')):
                return f"docs: update {file_name} documentation"
            elif staged_files[0].endswith(('.json', '.yaml', '.yml')):
                return f"config: update {file_name} configuration"
            else:
                return f"chore: update {file_name}"
        else:
            return f"feat: update {len(staged_files)} files"

    async def _get_latest_commit_hash(self) -> str:
        """获取最新提交哈希"""
        try:
            result = await self._run_git_command(['git', 'rev-parse', 'HEAD'])
            if result.returncode == 0:
                return result.stdout.decode().strip()[:7]
            return 'unknown'
        except Exception:
            return 'unknown'

    async def _get_branch_commits(self, source_branch: str, target_branch: str) -> List[Dict]:
        """获取分支提交"""
        try:
            result = await self._run_git_command([
                'git', 'log', '--oneline', f'{target_branch}..{source_branch}'
            ])
            
            commits = []
            if result.returncode == 0:
                for line in result.stdout.decode().strip().split('\n'):
                    if line:
                        parts = line.split(' ', 1)
                        if len(parts) >= 2:
                            commits.append({
                                'hash': parts[0],
                                'message': parts[1]
                            })
            return commits
        except Exception:
            return []

    async def _generate_pr_title(self, branch_name: str, commits: List[Dict]) -> str:
        """生成PR标题"""
        if commits:
            # 使用第一个提交的信息
            first_commit = commits[0]['message']
            return first_commit[:60] + ('...' if len(first_commit) > 60 else '')
        else:
            # 基于分支名生成
            return f"Merge {branch_name}"

    async def _generate_pr_description(self, commits: List[Dict], conflicts: Dict[str, Any]) -> str:
        """生成PR描述"""
        description = []
        
        # 添加提交摘要
        if commits:
            description.append("## 更改摘要")
            for commit in commits[:5]:  # 限制显示数量
                description.append(f"- {commit['message']}")
            if len(commits) > 5:
                description.append(f"... 以及其他 {len(commits) - 5} 个提交")
        
        # 添加冲突信息
        if conflicts.get('potential_conflicts', 0) > 0:
            description.append("\n## ⚠️ 潜在冲突")
            description.append(f"检测到 {conflicts['potential_conflicts']} 个潜在冲突，请仔细审查。")
        
        # 添加检查清单
        description.extend([
            "\n## 检查清单",
            "- [ ] 代码已经过测试",
            "- [ ] 文档已更新",
            "- [ ] 通过了所有质量检查"
        ])
        
        return '\n'.join(description)

    def _generate_pr_recommendations(self, pr_info: Dict[str, Any]) -> List[str]:
        """生成PR建议"""
        recommendations = []
        
        if pr_info['commits_count'] > 10:
            recommendations.append("提交数量较多，考虑使用squash合并")
        
        if pr_info['potential_conflicts'] > 0:
            recommendations.append("存在潜在冲突，建议先在本地测试合并")
        
        quality_issues = [r for r in pr_info['quality_checks'] if not r.get('success', True)]
        if quality_issues:
            recommendations.append("存在质量检查失败，请先解决相关问题")
        
        return recommendations

    async def _analyze_branch_structure(self) -> Dict[str, Any]:
        """分析分支结构"""
        try:
            result = await self._run_git_command(['git', 'branch', '-a'])
            
            if result.returncode != 0:
                return {'error': 'Failed to get branch list'}
            
            branches = []
            for line in result.stdout.decode().split('\n'):
                branch = line.strip()
                if branch and not branch.startswith('*'):
                    branches.append(branch.replace('remotes/origin/', ''))
            
            # 分析分支类型分布
            branch_types = {
                'feature': len([b for b in branches if b.startswith('feature/')]),
                'bugfix': len([b for b in branches if b.startswith('bugfix/')]),
                'hotfix': len([b for b in branches if b.startswith('hotfix/')]),
                'release': len([b for b in branches if b.startswith('release/')]),
                'other': len([b for b in branches if not any(b.startswith(prefix) for prefix in ['feature/', 'bugfix/', 'hotfix/', 'release/'])])
            }
            
            return {
                'total_branches': len(branches),
                'branch_types': branch_types,
                'main_branches': [b for b in branches if b in ['main', 'master', 'develop']]
            }
        except Exception as e:
            return {'error': str(e)}

    async def _get_repository_stats(self) -> Dict[str, Any]:
        """获取仓库统计"""
        try:
            # 获取仓库大小
            size_result = await self._run_git_command(['git', 'count-objects', '-vH'])
            
            # 获取提交数量
            commit_count_result = await self._run_git_command(['git', 'rev-list', '--count', 'HEAD'])
            
            # 获取贡献者数量
            contributors_result = await self._run_git_command(['git', 'shortlog', '-sn', '--all'])
            
            stats = {}
            
            if commit_count_result.returncode == 0:
                stats['total_commits'] = int(commit_count_result.stdout.decode().strip())
            
            if contributors_result.returncode == 0:
                contributors = contributors_result.stdout.decode().strip().split('\n')
                stats['total_contributors'] = len([c for c in contributors if c.strip()])
            
            if size_result.returncode == 0:
                # 解析size输出（简化版）
                stats['repository_size'] = 'Size info available'
            
            return stats
        except Exception as e:
            return {'error': str(e)}

    def _get_workflow_summary(self) -> Dict[str, Any]:
        """获取工作流摘要"""
        if not self.operation_history:
            return {'message': 'No workflow history'}
        
        # 统计操作类型
        operations = {}
        for op in self.operation_history:
            op_type = op.operation_type
            if op_type not in operations:
                operations[op_type] = {'count': 0, 'success': 0, 'total_time': 0.0}
            
            operations[op_type]['count'] += 1
            if op.success:
                operations[op_type]['success'] += 1
            operations[op_type]['total_time'] += op.execution_time
        
        return {
            'total_operations': len(self.operation_history),
            'operation_types': operations,
            'success_rate': (sum(1 for op in self.operation_history if op.success) / len(self.operation_history) * 100),
            'last_operation': self.operation_history[-1].__dict__ if self.operation_history else None
        }

    def _calculate_health_score(self, health_data: Dict[str, Any]) -> float:
        """计算健康度评分"""
        score = 0.0
        max_score = 100.0
        
        # 提交活跃度 (20分)
        commit_analysis = health_data.get('commit_analysis', {})
        if 'total_commits' in commit_analysis:
            commits = commit_analysis['total_commits']
            if commits > 50:
                score += 20
            elif commits > 20:
                score += 15
            elif commits > 5:
                score += 10
        
        # Hook状态 (30分)
        hooks_status = health_data.get('hooks_status', {})
        if 'statistics' in hooks_status:
            success_rate = hooks_status['statistics'].get('success_rate', 0)
            score += (success_rate / 100) * 30
        
        # 分支管理 (25分)
        branch_structure = health_data.get('branch_structure', {})
        if 'total_branches' in branch_structure:
            branches = branch_structure['total_branches']
            if branches < 20:  # 合理的分支数量
                score += 25
            elif branches < 50:
                score += 15
            else:
                score += 5
        
        # 工作流使用 (25分)
        workflow_history = health_data.get('workflow_history', {})
        if 'success_rate' in workflow_history:
            wf_success_rate = workflow_history['success_rate']
            score += (wf_success_rate / 100) * 25
        
        return min(score, max_score)

    def _generate_health_recommendations(self, health_data: Dict[str, Any]) -> List[str]:
        """生成健康度建议"""
        recommendations = []
        
        health_score = health_data.get('health_score', 0)
        
        if health_score < 50:
            recommendations.append("项目健康度较低，建议加强代码质量管理")
        
        # Hook相关建议
        hooks_status = health_data.get('hooks_status', {})
        if hooks_status.get('statistics', {}).get('success_rate', 100) < 90:
            recommendations.append("Git Hooks成功率较低，检查hooks配置")
        
        # 提交模式建议
        commit_analysis = health_data.get('commit_analysis', {})
        if commit_analysis.get('total_commits', 0) < 10:
            recommendations.append("提交频率较低，建议增加代码提交频率")
        
        # 分支管理建议
        branch_structure = health_data.get('branch_structure', {})
        if branch_structure.get('total_branches', 0) > 30:
            recommendations.append("分支数量过多，建议清理已合并的分支")
        
        if not recommendations:
            recommendations.append("项目健康状况良好，继续保持！")
        
        return recommendations

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

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)


# 全局实例
_git_workflow_manager: Optional[GitWorkflowManager] = None


def get_git_workflow_manager(project_root: Optional[str] = None) -> GitWorkflowManager:
    """获取Git工作流管理器实例"""
    global _git_workflow_manager
    if _git_workflow_manager is None:
        _git_workflow_manager = GitWorkflowManager(project_root)
    return _git_workflow_manager


# 便捷函数
async def start_feature_workflow(task_description: str, project_root: Optional[str] = None) -> Dict[str, Any]:
    """启动功能开发工作流"""
    manager = get_git_workflow_manager(project_root)
    return await manager.start_workflow(WorkflowType.FEATURE_DEVELOPMENT, task_description)


async def smart_commit(files: List[str] = None, message: str = None, 
                      project_root: Optional[str] = None) -> Dict[str, Any]:
    """智能提交"""
    manager = get_git_workflow_manager(project_root)
    return await manager.commit_with_smart_message(files, message)


if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) < 2:
            print("用法: python git_integration.py <command> [args...]")
            print("命令: start-workflow, commit, merge, cleanup, health, pr")
            return
        
        command = sys.argv[1]
        manager = GitWorkflowManager()
        
        if command == "start-workflow":
            workflow_type = sys.argv[2] if len(sys.argv) > 2 else "feature_development"
            description = sys.argv[3] if len(sys.argv) > 3 else "New feature"
            
            try:
                wf_type = WorkflowType(workflow_type)
                result = await manager.start_workflow(wf_type, description)
                print(json.dumps(result, indent=2, default=str))
            except ValueError:
                print(f"未知工作流类型: {workflow_type}")
        
        elif command == "commit":
            files = sys.argv[2:] if len(sys.argv) > 2 else None
            result = await manager.commit_with_smart_message(files)
            print(json.dumps(result, indent=2, default=str))
        
        elif command == "health":
            result = await manager.get_project_health()
            print(json.dumps(result, indent=2, default=str))
        
        elif command == "cleanup":
            dry_run = "--dry-run" in sys.argv
            result = await manager.cleanup_branches(dry_run)
            print(json.dumps(result, indent=2, default=str))
        
        elif command == "pr":
            target_branch = sys.argv[2] if len(sys.argv) > 2 else "main"
            result = await manager.create_pull_request(target_branch)
            print(json.dumps(result, indent=2, default=str))
        
        else:
            print(f"未知命令: {command}")
    
    asyncio.run(main())