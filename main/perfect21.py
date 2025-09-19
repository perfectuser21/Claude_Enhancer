#!/usr/bin/env python3
"""
Perfect21 - Claude Code智能工作流增强层
提供真正的多Agent并行执行和工作流管理能力
"""

import os
import sys
import argparse
import weakref
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.config import config
from modules.utils import setup_logging, get_project_info, format_execution_result
from modules.logger import log_info, log_error, log_git_operation
from modules.error_integration import (
    get_error_handler, with_git_error_handling, with_workflow_error_handling,
    Perfect21ErrorHandler, handle_perfect21_error
)
from modules.exceptions import (
    Perfect21BaseException, GitOperationError, WorkflowError,
    ErrorContext, ErrorSeverity, ErrorCategory
)
from features.git_workflow import GitHooks, WorkflowManager, BranchManager
from features.workflow.engine import WorkflowEngine, WorkflowResult, AgentTask, TaskStatus

# Import optimized systems
try:
    from features.integration.optimized_orchestrator import (
        get_optimized_orchestrator, execute_optimized_parallel_workflow,
        create_instant_parallel_instruction, OptimizedExecutionRequest
    )
    OPTIMIZED_SYSTEMS_AVAILABLE = True
except ImportError as e:
    log_error(f"优化系统导入失败: {e}")
    OPTIMIZED_SYSTEMS_AVAILABLE = False

class Perfect21Core:
    """Perfect21核心类 - 向后兼容"""

    def __init__(self):
        self.project_root = os.getcwd()
        self.config = config
        setup_logging(
            self.config.get('logging.level', 'INFO'),
            self.config.get('logging.file', 'logs/perfect21.log')
        )

class Perfect21:
    """Perfect21主程序"""

    # 类级实例跟踪
    _instances = weakref.WeakSet()

    def __init__(self):
        self.project_root = os.getcwd()
        self.config = config
        self._cleanup_callbacks = []
        self._is_cleaned_up = False

        # 添加到实例跟踪
        self._instances.add(self)

        # 设置日志
        setup_logging(
            self.config.get('logging.level', 'INFO'),
            self.config.get('logging.file', 'logs/perfect21.log')
        )

        # 初始化错误处理系统
        self.error_handler = get_error_handler()

        # 初始化组件（带错误处理）
        try:
            # 传统组件
            self.git_hooks = GitHooks(self.project_root)
            self.workflow_manager = WorkflowManager(self.project_root)
            self.branch_manager = BranchManager(self.project_root)

            # Perfect21核心工作流引擎
            self.workflow_engine = WorkflowEngine(max_workers=10)

            # 初始化优化系统
            self.optimized_orchestrator = None
            if OPTIMIZED_SYSTEMS_AVAILABLE:
                try:
                    self.optimized_orchestrator = get_optimized_orchestrator()
                    log_info("Perfect21优化系统初始化完成")
                except Exception as e:
                    log_error(f"优化系统初始化失败: {e}")

            log_info("Perfect21工作流引擎初始化完成")
        except Exception as e:
            error = Perfect21BaseException(
                message=f"Failed to initialize Perfect21 components: {str(e)}",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                context=ErrorContext(
                    component="Perfect21Core",
                    operation="initialization",
                    metadata={"project_root": self.project_root}
                ),
                original_exception=e,
                recovery_suggestions=[
                    "Check project directory permissions",
                    "Verify git repository is valid",
                    "Check system dependencies"
                ]
            )
            self.error_handler.handle_error(error)
            raise

        # 注册清理回调
        self._register_cleanup_callbacks()

        # 添加工作流引擎到清理回调
        self._cleanup_callbacks.append(lambda: setattr(self, 'workflow_engine', None))

        log_info("Perfect21初始化完成")

    def _register_cleanup_callbacks(self):
        """注册清理回调"""
        self._cleanup_callbacks.extend([
            lambda: setattr(self, 'git_hooks', None),
            lambda: setattr(self, 'workflow_manager', None),
            lambda: setattr(self, 'branch_manager', None),
        ])

    def cleanup(self):
        """清理资源"""
        if self._is_cleaned_up:
            return

        try:
            log_info("Perfect21开始清理资源...")

            # 执行清理回调
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    log_error(f"清理回调执行失败: {e}")

            self._is_cleaned_up = True
            log_info("Perfect21资源清理完成")

        except Exception as e:
            log_error(f"Perfect21资源清理失败: {e}")

    def __del__(self):
        """析构函数"""
        try:
            self.cleanup()
        except Exception:
            pass  # 在析构函数中忽略所有异常

    @classmethod
    def cleanup_all_instances(cls):
        """清理所有实例"""
        instances = list(cls._instances)
        for instance in instances:
            try:
                instance.cleanup()
            except Exception as e:
                log_error(f"实例清理失败: {e}")

    def status(self) -> Dict[str, Any]:
        """获取系统状态"""
        if self._is_cleaned_up:
            return {
                'success': False,
                'error': 'Perfect21实例已被清理'
            }

        try:
            project_info = get_project_info(self.project_root)
            hook_status = self.git_hooks.get_hook_status() if self.git_hooks else {}
            workflow_status = self.workflow_manager.get_workflow_status() if self.workflow_manager else {}
            branch_status = self.branch_manager.get_branch_status() if self.branch_manager else {}

            status_info = {
                'perfect21': {
                    'version': self.config.get('perfect21.version'),
                    'mode': self.config.get('perfect21.mode'),
                    'core_agents_available': project_info.get('has_core_agents', False),
                    'agent_count': project_info.get('agent_count', 0),
                    'cleanup_status': 'active' if not self._is_cleaned_up else 'cleaned'
                },
                'project': project_info,
                'git_hooks': hook_status,
                'workflow': workflow_status,
                'branches': branch_status
            }

            return {
                'success': True,
                'status': status_info
            }

        except Exception as e:
            log_error("获取系统状态失败", e)
            return {
                'success': False,
                'error': str(e)
            }

    def git_hook_handler(self, hook_type: str, *args) -> Dict[str, Any]:
        """Git钩子处理器"""
        try:
            log_git_operation(f"触发{hook_type}钩子", {'args': args})

            if hook_type == 'pre-commit':
                result = self.git_hooks.pre_commit_hook()
            elif hook_type == 'pre-push':
                remote = args[0] if args else 'origin'
                result = self.git_hooks.pre_push_hook(remote)
            elif hook_type == 'post-checkout':
                old_ref, new_ref, branch_flag = args[:3] if len(args) >= 3 else ('', '', '1')
                result = self.git_hooks.post_checkout_hook(old_ref, new_ref, branch_flag)
            elif hook_type == 'prepare-commit-msg':
                commit_msg_file = args[0] if args else '.git/COMMIT_EDITMSG'
                result = self.git_hooks.prepare_commit_msg_hook(commit_msg_file)
            elif hook_type == 'commit-msg':
                commit_msg_file = args[0] if args else '.git/COMMIT_EDITMSG'
                result = self.git_hooks.commit_msg_hook(commit_msg_file)
            elif hook_type == 'post-commit':
                result = self.git_hooks.post_commit_hook()
            else:
                return {
                    'success': False,
                    'message': f"不支持的钩子类型: {hook_type}"
                }

            log_git_operation(f"{hook_type}钩子完成", result)
            return result

        except Exception as e:
            log_error(f"Git钩子处理失败: {hook_type}", e)
            return {
                'success': False,
                'error': str(e),
                'message': f"{hook_type}钩子执行失败"
            }

    def workflow_command(self, action: str, *args) -> Dict[str, Any]:
        """工作流命令处理"""
        try:
            if action == 'create-feature':
                if not args:
                    return {'success': False, 'message': '请提供功能名称'}
                feature_name = args[0]
                from_branch = args[1] if len(args) > 1 else 'develop'
                result = self.workflow_manager.create_feature_branch(feature_name, from_branch)

            elif action == 'create-release':
                if not args:
                    return {'success': False, 'message': '请提供版本号'}
                version = args[0]
                from_branch = args[1] if len(args) > 1 else 'develop'
                result = self.workflow_manager.create_release_branch(version, from_branch)

            elif action == 'merge-to-main':
                if not args:
                    return {'success': False, 'message': '请提供源分支名称'}
                source_branch = args[0]
                delete_source = len(args) < 2 or args[1].lower() != 'keep'
                result = self.workflow_manager.merge_to_main(source_branch, delete_source)

            elif action == 'branch-info':
                branch_name = args[0] if args else None
                if branch_name:
                    result = self.branch_manager.validate_branch_name(branch_name)
                else:
                    result = self.branch_manager.get_branch_status()

            elif action == 'cleanup':
                days = int(args[0]) if args else 30
                result = self.branch_manager.cleanup_old_branches(days)

            else:
                return {
                    'success': False,
                    'message': f"不支持的工作流操作: {action}"
                }

            log_git_operation(f"工作流操作: {action}", result)
            return result

        except Exception as e:
            log_error(f"工作流命令失败: {action}", e)
            return {
                'success': False,
                'error': str(e),
                'message': f"工作流操作{action}失败"
            }

    def execute_parallel_workflow(self, agents: List[str], base_prompt: str,
                                 task_description: str = None) -> Dict[str, Any]:
        """
        执行并行工作流 - Perfect21核心功能

        Args:
            agents: Agent列表
            base_prompt: 基础提示词
            task_description: 任务描述

        Returns:
            Dict: 包含批量执行指令的结果
        """
        try:
            log_info(f"Perfect21执行并行工作流: {len(agents)}个agents")

            # 如果优化系统可用，优先使用优化执行
            if self.optimized_orchestrator and OPTIMIZED_SYSTEMS_AVAILABLE:
                return self.execute_optimized_parallel_workflow(agents, base_prompt, task_description)

            # 备用：使用传统执行方式
            # 准备任务数据
            tasks = []
            for agent in agents:
                task_data = {
                    'agent_name': agent,
                    'description': task_description or f"{agent}任务执行",
                    'prompt': base_prompt,
                    'timeout': 300,
                    'critical': False
                }
                tasks.append(task_data)

            # 使用工作流引擎执行并行任务
            workflow_result = self.workflow_engine.execute_parallel_tasks(tasks)

            # 返回结果和执行指令
            return {
                'success': True,
                'workflow_id': workflow_result.workflow_id,
                'status': workflow_result.status.value,
                'execution_time': workflow_result.execution_time,
                'agents_count': len(agents),
                'success_count': workflow_result.success_count,
                'failure_count': workflow_result.failure_count,
                'batch_instruction': getattr(workflow_result, 'batch_execution_instruction', None),
                'claude_code_ready': workflow_result.success_count > 0,
                'message': f'并行工作流已完成，生成{workflow_result.success_count}个Agent执行指令'
            }

        except Exception as e:
            log_error("并行工作流执行失败", e)
            return {
                'success': False,
                'error': str(e),
                'message': '并行工作流执行失败'
            }

    def execute_sequential_workflow(self, pipeline: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        执行顺序工作流

        Args:
            pipeline: 任务管道，按顺序执行

        Returns:
            Dict: 执行结果
        """
        try:
            log_info(f"Perfect21执行顺序工作流: {len(pipeline)}个阶段")

            # 使用工作流引擎执行顺序任务
            workflow_result = self.workflow_engine.execute_sequential_pipeline(pipeline)

            return {
                'success': True,
                'workflow_id': workflow_result.workflow_id,
                'status': workflow_result.status.value,
                'execution_time': workflow_result.execution_time,
                'stages_count': len(pipeline),
                'success_count': workflow_result.success_count,
                'failure_count': workflow_result.failure_count,
                'sequential_instruction': getattr(workflow_result, 'batch_execution_instruction', None),
                'message': f'顺序工作流已完成，生成{workflow_result.success_count}个阶段执行指令'
            }

        except Exception as e:
            log_error("顺序工作流执行失败", e)
            return {
                'success': False,
                'error': str(e),
                'message': '顺序工作流执行失败'
            }

    def create_instant_parallel_instruction(self, agents: List[str], prompt: str) -> Dict[str, Any]:
        """
        创建即时并行执行指令 - 无需等待工作流处理

        Args:
            agents: Agent列表
            prompt: 提示词

        Returns:
            Dict: 包含直接可用的Claude Code执行指令
        """
        try:
            log_info(f"Perfect21生成即时并行指令: {len(agents)}个agents")

            # 使用工作流引擎的实时指令生成功能
            instruction = self.workflow_engine.create_real_time_parallel_instruction(agents, prompt)

            return {
                'success': True,
                'instruction': instruction,
                'agents_count': len(agents),
                'ready_for_execution': True,
                'message': f'即时并行指令已生成，可直接在Claude Code中执行'
            }

        except Exception as e:
            log_error("即时并行指令生成失败", e)
            return {
                'success': False,
                'error': str(e),
                'message': '即时并行指令生成失败'
            }

    def get_workflow_status(self, workflow_id: str = None) -> Dict[str, Any]:
        """
        获取工作流执行状态

        Args:
            workflow_id: 工作流ID，可选

        Returns:
            Dict: 执行状态信息
        """
        try:
            if workflow_id:
                # 获取特定工作流状态
                status = self.workflow_engine.monitor_execution(workflow_id)
                return {
                    'success': True,
                    'workflow_status': status
                }
            else:
                # 获取所有活跃工作流
                active_workflows = list(self.workflow_engine.active_workflows.keys())
                history = self.workflow_engine.get_execution_history(5)

                return {
                    'success': True,
                    'active_workflows': active_workflows,
                    'recent_history': [
                        {
                            'workflow_id': w.workflow_id,
                            'status': w.status.value,
                            'agents_count': len(w.tasks),
                            'success_count': w.success_count,
                            'execution_time': w.execution_time
                        }
                        for w in history
                    ]
                }

        except Exception as e:
            log_error("获取工作流状态失败", e)
            return {
                'success': False,
                'error': str(e),
                'message': '获取工作流状态失败'
            }

    # ========================================
    # 优化执行方法
    # ========================================

    def execute_optimized_parallel_workflow(self, agents: List[str], base_prompt: str,
                                           task_description: str = None) -> Dict[str, Any]:
        """
        执行优化的并行工作流，使用智能Agent选择和优化引擎

        Args:
            agents: Agent列表（可以为空，由智能选择器决定）
            base_prompt: 基础提示词
            task_description: 任务描述

        Returns:
            Dict: 优化执行结果
        """
        try:
            if not self.optimized_orchestrator:
                return {
                    'success': False,
                    'message': '优化系统不可用，使用传统方式'
                }

            log_info(f"Perfect21执行优化并行工作流: {task_description or base_prompt[:50]}")

            # 如果没有指定agents，由智能选择器决定
            if not agents:
                task_for_analysis = task_description or base_prompt
                selection_result = create_instant_parallel_instruction(task_for_analysis)
                if not selection_result['success']:
                    return {
                        'success': False,
                        'message': f"Agent选择失败: {selection_result.get('error', 'Unknown error')}"
                    }
                agents = selection_result['selected_agents']

            # 使用优化执行
            result = execute_optimized_parallel_workflow(
                task_description or base_prompt,
                max_agents=len(agents) if agents else 10,
                context={'base_prompt': base_prompt, 'specified_agents': agents}
            )

            return result

        except Exception as e:
            log_error(f"优化并行执行失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '优化执行失败，请尝试传统方式'
            }

    def create_smart_parallel_instruction(self, task_description: str, max_agents: int = 10) -> Dict[str, Any]:
        """
        创建智能并行指令，由AI选择最优Agent组合

        Args:
            task_description: 任务描述
            max_agents: 最大Agent数量

        Returns:
            Dict: 包含执行指令和分析结果
        """
        try:
            if not OPTIMIZED_SYSTEMS_AVAILABLE:
                return {
                    'success': False,
                    'message': '优化系统不可用'
                }

            log_info(f"Perfect21生成智能并行指令: {task_description[:50]}")

            result = create_instant_parallel_instruction(task_description, max_agents)

            if result['success']:
                return {
                    'success': True,
                    'instruction': result['instruction'],
                    'selected_agents': result['selected_agents'],
                    'execution_mode': result['execution_mode'],
                    'estimated_time': result.get('estimated_time', 0),
                    'confidence': result.get('confidence', 0),
                    'reasoning': result.get('reasoning', ''),
                    'agents_count': len(result['selected_agents']),
                    'ready_for_execution': True,
                    'message': f'智能选择了{len(result["selected_agents"])}个Agent，可直接在Claude Code中执行'
                }
            else:
                return result

        except Exception as e:
            log_error(f"智能指令生成失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '智能指令生成失败'
            }

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """
        获取优化系统统计信息

        Returns:
            Dict: 统计信息
        """
        try:
            if not self.optimized_orchestrator:
                return {
                    'success': False,
                    'message': '优化系统不可用'
                }

            stats = self.optimized_orchestrator.get_orchestrator_statistics()
            return {
                'success': True,
                'optimization_stats': stats,
                'optimized_systems_available': OPTIMIZED_SYSTEMS_AVAILABLE
            }

        except Exception as e:
            log_error(f"获取优化统计失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def cleanup_optimization_data(self, max_age_days: int = 7) -> Dict[str, Any]:
        """
        清理优化系统的旧数据

        Args:
            max_age_days: 最大保留天数

        Returns:
            Dict: 清理结果
        """
        try:
            if not self.optimized_orchestrator:
                return {
                    'success': False,
                    'message': '优化系统不可用'
                }

            cleanup_stats = self.optimized_orchestrator.cleanup_old_data(max_age_days)
            return {
                'success': True,
                'cleanup_stats': cleanup_stats,
                'message': f'已清理{max_age_days}天前的旧数据'
            }

        except Exception as e:
            log_error(f"清理优化数据失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def run_command(self, command: str, args: list = None) -> Dict[str, Any]:
        """运行命令"""
        args = args or []

        try:
            if command == 'status':
                return self.status()
            elif command == 'git-hook':
                if not args:
                    return {'success': False, 'message': '请指定钩子类型'}
                return self.git_hook_handler(args[0], *args[1:])
            elif command == 'workflow':
                if not args:
                    return {'success': False, 'message': '请指定工作流操作'}
                return self.workflow_command(args[0], *args[1:])
            elif command == 'parallel':
                # Perfect21核心功能：并行执行
                if len(args) < 2:
                    return {'success': False, 'message': '请提供agent列表和提示词'}
                agents = args[0].split(',') if isinstance(args[0], str) else args[0]
                prompt = args[1]
                task_desc = args[2] if len(args) > 2 else None
                return self.execute_parallel_workflow(agents, prompt, task_desc)
            elif command == 'sequential':
                # Perfect21核心功能：顺序执行
                if not args:
                    return {'success': False, 'message': '请提供任务管道定义'}
                pipeline = args[0] if isinstance(args[0], list) else []
                return self.execute_sequential_workflow(pipeline)
            elif command == 'instant-parallel':
                # Perfect21即时指令生成
                if len(args) < 2:
                    return {'success': False, 'message': '请提供agent列表和提示词'}
                agents = args[0].split(',') if isinstance(args[0], str) else args[0]
                prompt = args[1]
                return self.create_instant_parallel_instruction(agents, prompt)
            elif command == 'workflow-status':
                # 获取工作流状态
                workflow_id = args[0] if args else None
                return self.get_workflow_status(workflow_id)
            elif command == 'optimized-parallel':
                # 优化并行执行：使用智能Agent选择
                if not args:
                    return {'success': False, 'message': '请提供任务描述'}
                task_description = args[0]
                agents = args[1].split(',') if len(args) > 1 and args[1] else []
                base_prompt = args[2] if len(args) > 2 else task_description
                return self.execute_optimized_parallel_workflow(agents, base_prompt, task_description)
            elif command == 'smart-instruction':
                # 智能指令生成：AI选择最优Agent组合
                if not args:
                    return {'success': False, 'message': '请提供任务描述'}
                task_description = args[0]
                max_agents = int(args[1]) if len(args) > 1 else 10
                return self.create_smart_parallel_instruction(task_description, max_agents)
            elif command == 'optimization-stats':
                # 获取优化统计
                return self.get_optimization_statistics()
            elif command == 'cleanup-optimization':
                # 清理优化数据
                max_age_days = int(args[0]) if args else 7
                return self.cleanup_optimization_data(max_age_days)
            else:
                return {
                    'success': False,
                    'message': f"未知命令: {command}"
                }

        except Exception as e:
            log_error(f"命令执行失败: {command}", e)
            return {
                'success': False,
                'error': str(e),
                'message': f"命令{command}执行失败"
            }

    # 删除重复的cleanup方法和__del__方法，因为已经在102-128行定义过了

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Perfect21 - 基于claude-code-unified-agents的Git工作流管理')
    parser.add_argument('command', help='命令: status, git-hook, workflow')
    parser.add_argument('args', nargs='*', help='命令参数')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    # 创建Perfect21实例
    p21 = Perfect21()

    # 执行命令
    result = p21.run_command(args.command, args.args)

    # 输出结果
    if args.verbose:
        print(format_execution_result(result))
    else:
        if result.get('success'):
            print(result.get('message', '操作成功'))
        else:
            print(f"错误: {result.get('message', '操作失败')}")
            if result.get('error'):
                print(f"详情: {result['error']}")

    # 返回退出码
    sys.exit(0 if result.get('success') else 1)

# 向后兼容导出
__all__ = ['Perfect21', 'Perfect21Core']

if __name__ == '__main__':
    main()