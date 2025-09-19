#!/usr/bin/env python3
"""
Perfect21 Git Workflow Manager - 高级工作流管理
个人编程助手专用的Git自动化工作流
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import aiofiles
import threading

from .git_hooks import GitHooksManager, HookType
from .git_integration import GitWorkflowManager, WorkflowType

logger = logging.getLogger("Perfect21GitWorkflowManager")


class TaskPriority(Enum):
    """任务优先级"""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class WorkflowStage(Enum):
    """工作流阶段"""
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"


@dataclass
class WorkflowTask:
    """工作流任务"""
    id: str
    title: str
    description: str
    priority: TaskPriority
    workflow_type: WorkflowType
    branch_name: str
    stage: WorkflowStage = WorkflowStage.PLANNING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowMetrics:
    """工作流指标"""
    total_tasks: int
    completed_tasks: int
    active_tasks: int
    average_completion_time: float
    productivity_score: float
    quality_score: float
    velocity: float  # 任务完成速度
    burndown_data: List[Tuple[datetime, int]]  # (日期, 剩余任务数)


class PersonalProductivityAnalyzer:
    """个人生产力分析器"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.data_dir = Path(project_root) / ".perfect21" / "productivity"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def track_coding_session(self, task_id: str, duration_minutes: int, 
                                 lines_changed: int, files_modified: int) -> Dict[str, Any]:
        """记录编程会话"""
        session_data = {
            'task_id': task_id,
            'timestamp': datetime.now().isoformat(),
            'duration_minutes': duration_minutes,
            'lines_changed': lines_changed,
            'files_modified': files_modified,
            'productivity_score': self._calculate_session_productivity(
                duration_minutes, lines_changed, files_modified
            )
        }
        
        # 保存到文件
        session_file = self.data_dir / f"session_{datetime.now().strftime('%Y%m%d')}.jsonl"
        async with aiofiles.open(session_file, 'a') as f:
            await f.write(json.dumps(session_data) + '\n')
        
        return session_data

    def _calculate_session_productivity(self, duration: int, lines: int, files: int) -> float:
        """计算会话生产力分数"""
        if duration == 0:
            return 0.0
        
        # 简单的生产力计算公式
        lines_per_minute = lines / duration
        files_factor = min(files / 5.0, 1.0)  # 文件数越多越复杂
        
        base_score = lines_per_minute * 10
        complexity_bonus = files_factor * 20
        
        return min(base_score + complexity_bonus, 100.0)

    async def get_productivity_insights(self, days: int = 7) -> Dict[str, Any]:
        """获取生产力洞察"""
        sessions = await self._load_recent_sessions(days)
        
        if not sessions:
            return {
                'message': '没有足够的数据进行分析',
                'sessions_count': 0
            }
        
        # 分析数据
        total_duration = sum(s['duration_minutes'] for s in sessions)
        total_lines = sum(s['lines_changed'] for s in sessions)
        avg_productivity = sum(s['productivity_score'] for s in sessions) / len(sessions)
        
        # 按天统计
        daily_stats = self._group_sessions_by_day(sessions)
        
        # 最佳时间段分析
        best_hours = self._analyze_best_working_hours(sessions)
        
        return {
            'analysis_period': f'{days} days',
            'total_sessions': len(sessions),
            'total_hours': round(total_duration / 60, 1),
            'total_lines_changed': total_lines,
            'average_productivity_score': round(avg_productivity, 1),
            'daily_stats': daily_stats,
            'best_working_hours': best_hours,
            'recommendations': self._generate_productivity_recommendations(sessions)
        }

    async def _load_recent_sessions(self, days: int) -> List[Dict[str, Any]]:
        """加载最近的编程会话"""
        sessions = []
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            session_file = self.data_dir / f"session_{date.strftime('%Y%m%d')}.jsonl"
            
            if session_file.exists():
                try:
                    async with aiofiles.open(session_file, 'r') as f:
                        content = await f.read()
                        for line in content.strip().split('\n'):
                            if line:
                                sessions.append(json.loads(line))
                except Exception as e:
                    logger.warning(f"加载会话数据失败: {e}")
        
        return sessions

    def _group_sessions_by_day(self, sessions: List[Dict]) -> Dict[str, Any]:
        """按天统计会话"""
        daily_stats = {}
        
        for session in sessions:
            date = session['timestamp'][:10]  # YYYY-MM-DD
            if date not in daily_stats:
                daily_stats[date] = {
                    'sessions': 0,
                    'total_minutes': 0,
                    'lines_changed': 0,
                    'avg_productivity': 0
                }
            
            stats = daily_stats[date]
            stats['sessions'] += 1
            stats['total_minutes'] += session['duration_minutes']
            stats['lines_changed'] += session['lines_changed']
        
        # 计算平均值
        for date, stats in daily_stats.items():
            if stats['sessions'] > 0:
                session_list = [s for s in sessions if s['timestamp'][:10] == date]
                stats['avg_productivity'] = sum(s['productivity_score'] for s in session_list) / len(session_list)
        
        return daily_stats

    def _analyze_best_working_hours(self, sessions: List[Dict]) -> List[int]:
        """分析最佳工作时间"""
        hourly_productivity = {}
        
        for session in sessions:
            try:
                timestamp = datetime.fromisoformat(session['timestamp'])
                hour = timestamp.hour
                
                if hour not in hourly_productivity:
                    hourly_productivity[hour] = []
                hourly_productivity[hour].append(session['productivity_score'])
            except Exception:
                continue
        
        # 计算每小时平均生产力
        avg_hourly = {}
        for hour, scores in hourly_productivity.items():
            avg_hourly[hour] = sum(scores) / len(scores)
        
        # 返回最佳的3个时间段
        sorted_hours = sorted(avg_hourly.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, _ in sorted_hours[:3]]

    def _generate_productivity_recommendations(self, sessions: List[Dict]) -> List[str]:
        """生成生产力建议"""
        recommendations = []
        
        if not sessions:
            return recommendations
        
        avg_duration = sum(s['duration_minutes'] for s in sessions) / len(sessions)
        avg_productivity = sum(s['productivity_score'] for s in sessions) / len(sessions)
        
        if avg_duration < 25:
            recommendations.append("建议增加单次编程会话时间，25-45分钟是理想区间")
        
        if avg_duration > 90:
            recommendations.append("单次编程时间过长，建议适当休息以保持效率")
        
        if avg_productivity < 30:
            recommendations.append("生产力分数较低，考虑减少干扰或优化开发环境")
        
        # 分析工作模式
        recent_sessions = sessions[-7:]  # 最近7次会话
        if len(recent_sessions) >= 3:
            recent_durations = [s['duration_minutes'] for s in recent_sessions]
            if all(d < 15 for d in recent_durations):
                recommendations.append("最近的编程会话都较短，可能需要更长的专注时间")
        
        if not recommendations:
            recommendations.append("保持当前的工作节奏，生产力表现良好！")
        
        return recommendations


class SmartBranchManager:
    """智能分支管理器"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.branch_patterns = {
            'feature': r'^feature/[a-zA-Z0-9\-_]+$',
            'bugfix': r'^bugfix/[a-zA-Z0-9\-_]+$',
            'hotfix': r'^hotfix/[a-zA-Z0-9\-_]+$',
            'release': r'^release/v?\d+\.\d+(\.\d+)?$'
        }
        self.protected_branches = {'main', 'master', 'develop'}

    async def suggest_branch_cleanup(self) -> Dict[str, Any]:
        """建议分支清理方案"""
        try:
            # 获取所有分支
            result = await self._run_git_command(['git', 'branch', '-a', '--merged', 'main'])
            
            if result.returncode != 0:
                return {'error': 'Failed to get branch information'}
            
            branches = []
            for line in result.stdout.decode().split('\n'):
                branch = line.strip().replace('remotes/origin/', '')
                if branch and not branch.startswith('*') and branch not in self.protected_branches:
                    branches.append(branch)
            
            # 分类分支
            cleanup_suggestions = {
                'safe_to_delete': [],
                'review_required': [],
                'keep': []
            }
            
            for branch in branches:
                age_days = await self._get_branch_age(branch)
                last_activity = await self._get_last_activity(branch)
                
                if age_days > 30 and last_activity > 14:
                    cleanup_suggestions['safe_to_delete'].append({
                        'name': branch,
                        'age_days': age_days,
                        'last_activity_days': last_activity
                    })
                elif age_days > 7:
                    cleanup_suggestions['review_required'].append({
                        'name': branch,
                        'age_days': age_days,
                        'last_activity_days': last_activity
                    })
                else:
                    cleanup_suggestions['keep'].append(branch)
            
            return {
                'total_branches': len(branches),
                'cleanup_suggestions': cleanup_suggestions,
                'estimated_cleanup_time': len(cleanup_suggestions['safe_to_delete']) * 0.5,  # 分钟
                'space_savings': f"{len(cleanup_suggestions['safe_to_delete']) * 0.1} MB"  # 估计
            }
        
        except Exception as e:
            logger.error(f"分析分支清理失败: {e}")
            return {'error': str(e)}

    async def auto_cleanup_branches(self, dry_run: bool = True) -> Dict[str, Any]:
        """自动清理分支"""
        suggestions = await self.suggest_branch_cleanup()
        
        if 'error' in suggestions:
            return suggestions
        
        safe_branches = suggestions['cleanup_suggestions']['safe_to_delete']
        
        if dry_run:
            return {
                'dry_run': True,
                'would_delete': [b['name'] for b in safe_branches],
                'count': len(safe_branches)
            }
        
        # 实际删除
        deleted = []
        failed = []
        
        for branch_info in safe_branches:
            branch_name = branch_info['name']
            try:
                result = await self._run_git_command(['git', 'branch', '-d', branch_name])
                if result.returncode == 0:
                    deleted.append(branch_name)
                else:
                    failed.append({
                        'branch': branch_name,
                        'error': result.stderr.decode()
                    })
            except Exception as e:
                failed.append({
                    'branch': branch_name,
                    'error': str(e)
                })
        
        return {
            'deleted': deleted,
            'failed': failed,
            'success_count': len(deleted),
            'total_processed': len(safe_branches)
        }

    async def _get_branch_age(self, branch_name: str) -> int:
        """获取分支年龄（天数）"""
        try:
            result = await self._run_git_command([
                'git', 'log', '-1', '--format=%ct', branch_name
            ])
            
            if result.returncode == 0:
                timestamp = int(result.stdout.decode().strip())
                creation_date = datetime.fromtimestamp(timestamp)
                return (datetime.now() - creation_date).days
            return 0
        except Exception:
            return 0

    async def _get_last_activity(self, branch_name: str) -> int:
        """获取最后活动时间（天数）"""
        try:
            result = await self._run_git_command([
                'git', 'log', '-1', '--format=%ct', branch_name
            ])
            
            if result.returncode == 0:
                timestamp = int(result.stdout.decode().strip())
                last_commit = datetime.fromtimestamp(timestamp)
                return (datetime.now() - last_commit).days
            return 999  # 很久没有活动
        except Exception:
            return 999

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


class AdvancedGitWorkflowManager:
    """高级Git工作流管理器 - 主要类"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        
        # 组件初始化
        self.git_workflow = GitWorkflowManager(str(self.project_root))
        self.hooks_manager = GitHooksManager(str(self.project_root))
        self.productivity_analyzer = PersonalProductivityAnalyzer(str(self.project_root))
        self.branch_manager = SmartBranchManager(str(self.project_root))
        
        # 任务管理
        self.tasks: Dict[str, WorkflowTask] = {}
        self.task_history: List[Dict[str, Any]] = []
        
        # 数据存储
        self.data_dir = self.project_root / ".perfect21" / "workflow"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 性能优化
        self.executor = ThreadPoolExecutor(max_workers=3)
        self._lock = threading.Lock()
        
        logger.info(f"高级Git工作流管理器初始化: {self.project_root}")

    async def create_task(self, title: str, description: str, 
                        priority: TaskPriority = TaskPriority.MEDIUM,
                        workflow_type: WorkflowType = WorkflowType.FEATURE_DEVELOPMENT,
                        estimated_hours: Optional[float] = None,
                        tags: List[str] = None) -> Dict[str, Any]:
        """创建新任务"""
        try:
            # 生成任务ID
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 生成分支名称
            branch_name = await self._generate_task_branch_name(workflow_type, title)
            
            # 创建任务对象
            task = WorkflowTask(
                id=task_id,
                title=title,
                description=description,
                priority=priority,
                workflow_type=workflow_type,
                branch_name=branch_name,
                estimated_hours=estimated_hours,
                tags=tags or []
            )
            
            # 启动工作流
            workflow_result = await self.git_workflow.start_workflow(
                workflow_type, description
            )
            
            if workflow_result['success']:
                task.stage = WorkflowStage.DEVELOPMENT
                task.branch_name = workflow_result['branch_name']
                task.metadata['workflow_start'] = workflow_result
            
            # 保存任务
            with self._lock:
                self.tasks[task_id] = task
            
            await self._save_task(task)
            
            logger.info(f"创建任务: {task_id} - {title}")
            
            return {
                'success': True,
                'task_id': task_id,
                'task': task.__dict__,
                'workflow_result': workflow_result
            }
            
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def update_task_progress(self, task_id: str, progress: float, 
                                 stage: Optional[WorkflowStage] = None,
                                 notes: str = "") -> Dict[str, Any]:
        """更新任务进度"""
        try:
            if task_id not in self.tasks:
                return {
                    'success': False,
                    'error': f'任务 {task_id} 不存在'
                }
            
            task = self.tasks[task_id]
            old_progress = task.progress
            old_stage = task.stage
            
            # 更新任务
            task.progress = min(100.0, max(0.0, progress))
            if stage:
                task.stage = stage
            task.updated_at = datetime.now()
            
            # 记录更新历史
            update_record = {
                'timestamp': datetime.now().isoformat(),
                'task_id': task_id,
                'old_progress': old_progress,
                'new_progress': progress,
                'old_stage': old_stage.value,
                'new_stage': stage.value if stage else old_stage.value,
                'notes': notes
            }
            
            self.task_history.append(update_record)
            
            # 保存更新
            await self._save_task(task)
            
            # 如果任务完成，执行完成逻辑
            if task.progress >= 100.0 and task.stage != WorkflowStage.COMPLETED:
                await self._complete_task(task_id)
            
            return {
                'success': True,
                'task': task.__dict__,
                'update_record': update_record
            }
            
        except Exception as e:
            logger.error(f"更新任务进度失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def start_coding_session(self, task_id: str) -> Dict[str, Any]:
        """开始编程会话"""
        try:
            if task_id not in self.tasks:
                return {
                    'success': False,
                    'error': f'任务 {task_id} 不存在'
                }
            
            task = self.tasks[task_id]
            
            # 切换到任务分支
            await self._ensure_on_task_branch(task)
            
            # 记录会话开始
            session_start = {
                'task_id': task_id,
                'start_time': datetime.now().isoformat(),
                'branch': task.branch_name
            }
            
            # 保存会话信息
            session_file = self.data_dir / "current_session.json"
            async with aiofiles.open(session_file, 'w') as f:
                await f.write(json.dumps(session_start))
            
            return {
                'success': True,
                'session_start': session_start,
                'task': task.__dict__,
                'recommendations': await self._get_coding_recommendations(task)
            }
            
        except Exception as e:
            logger.error(f"开始编程会话失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def end_coding_session(self, notes: str = "") -> Dict[str, Any]:
        """结束编程会话"""
        try:
            session_file = self.data_dir / "current_session.json"
            
            if not session_file.exists():
                return {
                    'success': False,
                    'error': '没有活跃的编程会话'
                }
            
            # 加载会话信息
            async with aiofiles.open(session_file, 'r') as f:
                session_data = json.loads(await f.read())
            
            # 计算会话统计
            start_time = datetime.fromisoformat(session_data['start_time'])
            end_time = datetime.now()
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
            
            # 获取代码变更统计
            stats = await self._get_session_stats()
            
            # 记录生产力数据
            productivity_data = await self.productivity_analyzer.track_coding_session(
                session_data['task_id'],
                duration_minutes,
                stats['lines_changed'],
                stats['files_modified']
            )
            
            # 清理会话文件
            session_file.unlink()
            
            # 更新任务实际时间
            task_id = session_data['task_id']
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.actual_hours is None:
                    task.actual_hours = 0
                task.actual_hours += duration_minutes / 60
                await self._save_task(task)
            
            session_summary = {
                'task_id': task_id,
                'duration_minutes': duration_minutes,
                'start_time': session_data['start_time'],
                'end_time': end_time.isoformat(),
                'statistics': stats,
                'productivity_score': productivity_data['productivity_score'],
                'notes': notes
            }
            
            return {
                'success': True,
                'session_summary': session_summary,
                'recommendations': self._generate_session_recommendations(session_summary)
            }
            
        except Exception as e:
            logger.error(f"结束编程会话失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def smart_commit_and_push(self, task_id: str, message: str = None) -> Dict[str, Any]:
        """智能提交和推送"""
        try:
            if task_id not in self.tasks:
                return {
                    'success': False,
                    'error': f'任务 {task_id} 不存在'
                }
            
            task = self.tasks[task_id]
            
            # 智能提交
            commit_result = await self.git_workflow.commit_with_smart_message(
                custom_message=message
            )
            
            if not commit_result['success']:
                return commit_result
            
            # 推送到远程
            push_result = await self._push_to_remote(task.branch_name)
            
            # 更新任务进度
            await self.update_task_progress(
                task_id, 
                task.progress + 10,  # 每次提交增加10%进度
                notes=f"Committed: {commit_result['commit_message']}"
            )
            
            return {
                'success': True,
                'commit_result': commit_result,
                'push_result': push_result,
                'task_updated': True
            }
            
        except Exception as e:
            logger.error(f"智能提交失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def create_pull_request_for_task(self, task_id: str, 
                                         target_branch: str = 'main') -> Dict[str, Any]:
        """为任务创建PR"""
        try:
            if task_id not in self.tasks:
                return {
                    'success': False,
                    'error': f'任务 {task_id} 不存在'
                }
            
            task = self.tasks[task_id]
            
            # 生成PR标题和描述
            pr_title = f"[{task.priority.value.upper()}] {task.title}"
            pr_description = self._generate_task_pr_description(task)
            
            # 创建PR
            pr_result = await self.git_workflow.create_pull_request(
                target_branch, pr_title, pr_description
            )
            
            if pr_result['success']:
                # 更新任务状态
                task.stage = WorkflowStage.REVIEW
                task.metadata['pr_created'] = pr_result
                await self._save_task(task)
            
            return pr_result
            
        except Exception as e:
            logger.error(f"创建PR失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """获取个人仪表板数据"""
        try:
            # 并行获取各种数据
            tasks = [
                self._get_task_metrics(),
                self.productivity_analyzer.get_productivity_insights(),
                self.branch_manager.suggest_branch_cleanup(),
                self.git_workflow.get_project_health()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            dashboard = {
                'timestamp': datetime.now().isoformat(),
                'task_metrics': results[0] if not isinstance(results[0], Exception) else {'error': str(results[0])},
                'productivity_insights': results[1] if not isinstance(results[1], Exception) else {'error': str(results[1])},
                'branch_cleanup': results[2] if not isinstance(results[2], Exception) else {'error': str(results[2])},
                'project_health': results[3] if not isinstance(results[3], Exception) else {'error': str(results[3])},
                'quick_actions': self._get_quick_actions(),
                'recommendations': []
            }
            
            # 生成个性化建议
            dashboard['recommendations'] = self._generate_dashboard_recommendations(dashboard)
            
            return dashboard
            
        except Exception as e:
            logger.error(f"获取仪表板数据失败: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    # 私有辅助方法
    async def _generate_task_branch_name(self, workflow_type: WorkflowType, title: str) -> str:
        """为任务生成分支名称"""
        import re
        
        # 清理标题
        clean_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
        clean_title = re.sub(r'\s+', '-', clean_title.strip())[:30]
        
        # 根据工作流类型生成前缀
        if workflow_type == WorkflowType.FEATURE_DEVELOPMENT:
            prefix = "feature"
        elif workflow_type == WorkflowType.BUG_FIX:
            prefix = "bugfix"
        elif workflow_type == WorkflowType.HOTFIX:
            prefix = "hotfix"
        else:
            prefix = "task"
        
        timestamp = datetime.now().strftime('%m%d')
        return f"{prefix}/{clean_title}-{timestamp}"

    async def _ensure_on_task_branch(self, task: WorkflowTask):
        """确保在任务分支上"""
        current_branch = await self._get_current_branch()
        if current_branch != task.branch_name:
            await self._run_git_command(['git', 'checkout', task.branch_name])

    async def _get_current_branch(self) -> str:
        """获取当前分支"""
        try:
            result = await self._run_git_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
            if result.returncode == 0:
                return result.stdout.decode().strip()
            return 'unknown'
        except Exception:
            return 'unknown'

    async def _get_coding_recommendations(self, task: WorkflowTask) -> List[str]:
        """获取编程建议"""
        recommendations = []
        
        # 根据任务优先级
        if task.priority == TaskPriority.URGENT:
            recommendations.append("紧急任务，建议保持专注，减少干扰")
        
        # 根据任务类型
        if task.workflow_type == WorkflowType.BUG_FIX:
            recommendations.append("修复Bug时请先理解问题根本原因")
            recommendations.append("记得添加回归测试")
        
        # 根据估计时间
        if task.estimated_hours and task.estimated_hours > 4:
            recommendations.append("大型任务，建议分解为小的可管理的任务")
        
        return recommendations

    async def _get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        try:
            # 获取未提交的更改
            diff_result = await self._run_git_command(['git', 'diff', '--stat'])
            staged_result = await self._run_git_command(['git', 'diff', '--cached', '--stat'])
            
            lines_changed = 0
            files_modified = 0
            
            # 解析diff统计
            for result in [diff_result, staged_result]:
                if result.returncode == 0:
                    output = result.stdout.decode()
                    # 简单解析，实际应该更精确
                    lines = output.split('\n')
                    for line in lines:
                        if '+' in line or '-' in line:
                            files_modified += 1
                        if 'insertion' in line or 'deletion' in line:
                            # 提取数字
                            import re
                            numbers = re.findall(r'\d+', line)
                            if numbers:
                                lines_changed += sum(int(n) for n in numbers)
            
            return {
                'lines_changed': lines_changed,
                'files_modified': files_modified
            }
        
        except Exception as e:
            logger.warning(f"获取会话统计失败: {e}")
            return {
                'lines_changed': 0,
                'files_modified': 0
            }

    def _generate_session_recommendations(self, session: Dict[str, Any]) -> List[str]:
        """生成会话建议"""
        recommendations = []
        
        duration = session['duration_minutes']
        productivity = session['productivity_score']
        
        if duration < 15:
            recommendations.append("会话时间较短，下次可以尝试更长时间的专注开发")
        
        if productivity < 30:
            recommendations.append("生产力较低，考虑是否有干扰因素")
        elif productivity > 80:
            recommendations.append("生产力非常高，保持这个状态！")
        
        if session['statistics']['files_modified'] > 10:
            recommendations.append("修改了较多文件，记得做好测试")
        
        return recommendations

    async def _push_to_remote(self, branch_name: str) -> Dict[str, Any]:
        """推送分支到远程"""
        try:
            result = await self._run_git_command(['git', 'push', 'origin', branch_name])
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout.decode() if result.returncode == 0 else result.stderr.decode()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_task_pr_description(self, task: WorkflowTask) -> str:
        """为任务生成PR描述"""
        description_parts = [
            f"## {task.title}",
            "",
            task.description,
            "",
            f"**优先级**: {task.priority.value}",
            f"**类型**: {task.workflow_type.value}",
            f"**进度**: {task.progress}%"
        ]
        
        if task.estimated_hours:
            description_parts.append(f"**估计时间**: {task.estimated_hours}h")
        
        if task.actual_hours:
            description_parts.append(f"**实际时间**: {task.actual_hours:.1f}h")
        
        if task.tags:
            description_parts.extend([
                "",
                f"**标签**: {', '.join(task.tags)}"
            ])
        
        description_parts.extend([
            "",
            "## 检查清单",
            "- [ ] 代码已测试",
            "- [ ] 文档已更新",
            "- [ ] 符合编码规范",
            "- [ ] 通过所有检查"
        ])
        
        return "\n".join(description_parts)

    async def _complete_task(self, task_id: str):
        """完成任务的后续处理"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.stage = WorkflowStage.COMPLETED
        task.updated_at = datetime.now()
        
        # 记录完成时间
        if not task.actual_hours and task.estimated_hours:
            # 如果没有记录实际时间，使用估计时间
            task.actual_hours = task.estimated_hours
        
        await self._save_task(task)
        logger.info(f"任务已完成: {task_id} - {task.title}")

    async def _get_task_metrics(self) -> WorkflowMetrics:
        """获取任务指标"""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.stage == WorkflowStage.COMPLETED)
        active_tasks = sum(1 for t in self.tasks.values() if t.stage != WorkflowStage.COMPLETED)
        
        # 计算平均完成时间
        completed_task_list = [t for t in self.tasks.values() if t.stage == WorkflowStage.COMPLETED and t.actual_hours]
        avg_completion_time = 0.0
        if completed_task_list:
            avg_completion_time = sum(t.actual_hours for t in completed_task_list) / len(completed_task_list)
        
        # 计算质量分数（简化）
        quality_score = 85.0  # 默认分数，实际应该根据代码质量指标计算
        
        # 计算生产力分数
        productivity_score = min(completed_tasks * 10, 100.0)
        
        # 计算速度（任务/天）
        velocity = 0.0
        if completed_task_list:
            # 简化计算，实际应该根据时间区间计算
            velocity = len(completed_task_list) / 7  # 假设7天内完成
        
        return WorkflowMetrics(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            active_tasks=active_tasks,
            average_completion_time=avg_completion_time,
            productivity_score=productivity_score,
            quality_score=quality_score,
            velocity=velocity,
            burndown_data=[]  # TODO: 实际应该根据历史数据生成
        )

    def _get_quick_actions(self) -> List[Dict[str, str]]:
        """获取快速操作列表"""
        actions = [
            {'name': 'create_task', 'label': '创建新任务', 'icon': '➕'},
            {'name': 'start_session', 'label': '开始编程', 'icon': '▶️'},
            {'name': 'smart_commit', 'label': '智能提交', 'icon': '💾'},
            {'name': 'cleanup_branches', 'label': '清理分支', 'icon': '🧚'},
            {'name': 'view_analytics', 'label': '查看分析', 'icon': '📊'}
        ]
        
        # 根据当前状态调整可用操作
        session_file = self.data_dir / "current_session.json"
        if session_file.exists():
            actions.append({'name': 'end_session', 'label': '结束会话', 'icon': '⏹️'})
        
        return actions

    def _generate_dashboard_recommendations(self, dashboard: Dict[str, Any]) -> List[str]:
        """生成仪表板建议"""
        recommendations = []
        
        # 任务相关建议
        task_metrics = dashboard.get('task_metrics', {})
        if hasattr(task_metrics, 'active_tasks') and task_metrics.active_tasks > 5:
            recommendations.append("活跃任务较多，考虑优先完成现有任务")
        
        # 生产力相关建议
        productivity = dashboard.get('productivity_insights', {})
        if 'average_productivity_score' in productivity and productivity['average_productivity_score'] < 40:
            recommendations.append("生产力有提升空间，考虑优化工作环境")
        
        # 分支清理建议
        branch_cleanup = dashboard.get('branch_cleanup', {})
        if 'cleanup_suggestions' in branch_cleanup:
            safe_count = len(branch_cleanup['cleanup_suggestions'].get('safe_to_delete', []))
            if safe_count > 0:
                recommendations.append(f"可以清理 {safe_count} 个已合并的分支")
        
        if not recommendations:
            recommendations.append("目前状态良好，继续保持！")
        
        return recommendations

    async def _save_task(self, task: WorkflowTask):
        """保存任务到文件"""
        task_file = self.data_dir / f"{task.id}.json"
        async with aiofiles.open(task_file, 'w') as f:
            await f.write(json.dumps(task.__dict__, indent=2, default=str))

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
_advanced_workflow_manager: Optional[AdvancedGitWorkflowManager] = None


def get_advanced_workflow_manager(project_root: Optional[str] = None) -> AdvancedGitWorkflowManager:
    """获取高级工作流管理器实例"""
    global _advanced_workflow_manager
    if _advanced_workflow_manager is None:
        _advanced_workflow_manager = AdvancedGitWorkflowManager(project_root)
    return _advanced_workflow_manager


if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) < 2:
            print("用法: python workflow_manager.py <command> [args...]")
            print("命令: create-task, start-session, end-session, commit, dashboard")
            return
        
        command = sys.argv[1]
        manager = AdvancedGitWorkflowManager()
        
        if command == "create-task":
            title = sys.argv[2] if len(sys.argv) > 2 else "New Task"
            description = sys.argv[3] if len(sys.argv) > 3 else "Task description"
            result = await manager.create_task(title, description)
            print(json.dumps(result, indent=2, default=str))
        
        elif command == "dashboard":
            result = await manager.get_dashboard_data()
            print(json.dumps(result, indent=2, default=str))
        
        elif command == "start-session":
            task_id = sys.argv[2] if len(sys.argv) > 2 else ""
            if not task_id:
                print("需要提供任务ID")
                return
            result = await manager.start_coding_session(task_id)
            print(json.dumps(result, indent=2, default=str))
        
        elif command == "end-session":
            result = await manager.end_coding_session()
            print(json.dumps(result, indent=2, default=str))
        
        else:
            print(f"未知命令: {command}")
    
    asyncio.run(main())