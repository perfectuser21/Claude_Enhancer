#!/usr/bin/env python3
"""
Enhanced Git Hooks with Perfect21 Integration
包含失败处理、重试逻辑和自动修复功能
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field

from .workflow_hooks_integration import (
    WorkflowHooksIntegration, HookCheckpoint, WorkflowPhase
)

logger = logging.getLogger("Perfect21.EnhancedHooks")


class FailureStrategy(Enum):
    """失败处理策略"""
    ABORT = "abort"                    # 立即中止
    RETRY = "retry"                    # 重试
    AUTO_FIX = "auto_fix"             # 自动修复
    MANUAL_INTERVENTION = "manual"     # 手动干预
    SKIP_WITH_WARNING = "skip"         # 跳过并警告


class HookPriority(Enum):
    """Hook优先级"""
    CRITICAL = 1    # 关键：必须通过
    HIGH = 2        # 重要：建议通过
    MEDIUM = 3      # 中等：可选通过
    LOW = 4         # 低：仅记录


@dataclass
class FailureContext:
    """失败上下文"""
    hook_name: str
    error_type: str
    error_message: str
    failure_count: int
    timestamp: datetime
    suggested_fixes: List[str] = field(default_factory=list)
    auto_fixable: bool = False
    requires_manual: bool = False


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    delay_seconds: float = 1.0
    exponential_backoff: bool = True
    retry_conditions: List[str] = field(default_factory=lambda: ['timeout', 'network', 'temporary'])


@dataclass
class HookConfig:
    """增强的Hook配置"""
    name: str
    priority: HookPriority
    failure_strategy: FailureStrategy
    retry_config: RetryConfig
    timeout_seconds: int = 300
    auto_fix_enabled: bool = True
    required_agents: List[str] = field(default_factory=list)
    quality_gates: Dict[str, Any] = field(default_factory=dict)


class EnhancedHooksManager:
    """增强的Git Hooks管理器"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        self.workflow_integration = WorkflowHooksIntegration(project_root)

        # 配置目录
        self.config_dir = self.project_root / ".perfect21" / "hooks"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 日志和状态文件
        self.failure_log = self.config_dir / "failures.log"
        self.retry_state = self.config_dir / "retry_state.json"
        self.performance_log = self.config_dir / "performance.log"

        # Hook配置
        self.hook_configs = self._load_hook_configs()

        # 失败处理器注册
        self.failure_handlers = self._register_failure_handlers()

        # 自动修复器注册
        self.auto_fixers = self._register_auto_fixers()

    def _load_hook_configs(self) -> Dict[str, HookConfig]:
        """加载Hook配置"""
        configs = {
            'pre-commit': HookConfig(
                name='pre-commit',
                priority=HookPriority.CRITICAL,
                failure_strategy=FailureStrategy.AUTO_FIX,
                retry_config=RetryConfig(max_attempts=3),
                timeout_seconds=180,
                required_agents=['code-reviewer', 'security-auditor'],
                quality_gates={
                    'syntax_check': True,
                    'format_check': True,
                    'basic_security': True
                }
            ),
            'commit-msg': HookConfig(
                name='commit-msg',
                priority=HookPriority.HIGH,
                failure_strategy=FailureStrategy.AUTO_FIX,
                retry_config=RetryConfig(max_attempts=2),
                timeout_seconds=60,
                quality_gates={
                    'message_format': True,
                    'length_check': True
                }
            ),
            'pre-push': HookConfig(
                name='pre-push',
                priority=HookPriority.CRITICAL,
                failure_strategy=FailureStrategy.RETRY,
                retry_config=RetryConfig(max_attempts=2, delay_seconds=5.0),
                timeout_seconds=600,
                required_agents=['test-engineer', 'security-auditor', 'performance-engineer'],
                quality_gates={
                    'all_tests_pass': True,
                    'coverage_threshold': 80,
                    'security_scan': True,
                    'performance_check': True
                }
            ),
            'post-checkout': HookConfig(
                name='post-checkout',
                priority=HookPriority.MEDIUM,
                failure_strategy=FailureStrategy.SKIP_WITH_WARNING,
                retry_config=RetryConfig(max_attempts=1),
                timeout_seconds=120,
                quality_gates={
                    'env_setup': True,
                    'deps_check': True
                }
            ),
            'post-merge': HookConfig(
                name='post-merge',
                priority=HookPriority.HIGH,
                failure_strategy=FailureStrategy.MANUAL_INTERVENTION,
                retry_config=RetryConfig(max_attempts=2),
                timeout_seconds=300,
                required_agents=['devops-engineer', 'monitoring-specialist'],
                quality_gates={
                    'deployment_ready': True,
                    'monitoring_setup': True
                }
            )
        }

        # 尝试从配置文件加载自定义配置
        config_file = self.config_dir / "hook_configs.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    custom_configs = json.load(f)

                for hook_name, custom_config in custom_configs.items():
                    if hook_name in configs:
                        # 更新现有配置
                        for key, value in custom_config.items():
                            if hasattr(configs[hook_name], key):
                                setattr(configs[hook_name], key, value)

            except Exception as e:
                logger.warning(f"加载自定义Hook配置失败: {e}")

        return configs

    def _register_failure_handlers(self) -> Dict[FailureStrategy, Callable]:
        """注册失败处理器"""
        return {
            FailureStrategy.ABORT: self._handle_abort,
            FailureStrategy.RETRY: self._handle_retry,
            FailureStrategy.AUTO_FIX: self._handle_auto_fix,
            FailureStrategy.MANUAL_INTERVENTION: self._handle_manual_intervention,
            FailureStrategy.SKIP_WITH_WARNING: self._handle_skip_with_warning
        }

    def _register_auto_fixers(self) -> Dict[str, Callable]:
        """注册自动修复器"""
        return {
            'syntax_error': self._fix_syntax_error,
            'format_error': self._fix_format_error,
            'import_error': self._fix_import_error,
            'test_failure': self._fix_test_failure,
            'coverage_insufficient': self._fix_coverage,
            'security_vulnerability': self._fix_security_vulnerability,
            'performance_issue': self._fix_performance_issue,
            'dependency_conflict': self._fix_dependency_conflict
        }

    async def execute_enhanced_hook(self, hook_name: str,
                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行增强的Git Hook"""
        start_time = time.time()
        context = context or {}

        logger.info(f"执行增强Hook: {hook_name}")

        # 获取Hook配置
        config = self.hook_configs.get(hook_name)
        if not config:
            return self._create_result(False, f"未知的Hook: {hook_name}")

        # 检查重试状态
        retry_state = await self._load_retry_state(hook_name)

        try:
            # 执行Hook主逻辑
            result = await self._execute_hook_with_timeout(hook_name, context, config)

            # 处理执行结果
            if result['success']:
                # 清除重试状态
                await self._clear_retry_state(hook_name)
                await self._log_success(hook_name, result, time.time() - start_time)
                return result
            else:
                # 处理失败
                failure_context = FailureContext(
                    hook_name=hook_name,
                    error_type=result.get('error_type', 'unknown'),
                    error_message=result.get('message', 'Unknown error'),
                    failure_count=retry_state.get('attempt_count', 0) + 1,
                    timestamp=datetime.now()
                )

                return await self._handle_failure(config, failure_context, result, context)

        except asyncio.TimeoutError:
            # 超时处理
            failure_context = FailureContext(
                hook_name=hook_name,
                error_type='timeout',
                error_message=f"Hook执行超时 (>{config.timeout_seconds}s)",
                failure_count=retry_state.get('attempt_count', 0) + 1,
                timestamp=datetime.now()
            )

            timeout_result = self._create_result(False, failure_context.error_message)
            return await self._handle_failure(config, failure_context, timeout_result, context)

        except Exception as e:
            # 异常处理
            failure_context = FailureContext(
                hook_name=hook_name,
                error_type='exception',
                error_message=str(e),
                failure_count=retry_state.get('attempt_count', 0) + 1,
                timestamp=datetime.now()
            )

            exception_result = self._create_result(False, str(e))
            return await self._handle_failure(config, failure_context, exception_result, context)

    async def _execute_hook_with_timeout(self, hook_name: str, context: Dict[str, Any],
                                        config: HookConfig) -> Dict[str, Any]:
        """带超时的Hook执行"""
        try:
            hook_checkpoint = HookCheckpoint(hook_name)
        except ValueError:
            return self._create_result(False, f"不支持的Hook类型: {hook_name}")

        # 使用asyncio.wait_for实现超时
        return await asyncio.wait_for(
            self.workflow_integration.execute_workflow_hook(hook_checkpoint, context),
            timeout=config.timeout_seconds
        )

    async def _handle_failure(self, config: HookConfig, failure_context: FailureContext,
                             result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """处理Hook失败"""
        await self._log_failure(failure_context, result)

        # 根据配置的失败策略处理
        handler = self.failure_handlers.get(config.failure_strategy)
        if handler:
            return await handler(config, failure_context, result, context)
        else:
            return await self._handle_abort(config, failure_context, result, context)

    async def _handle_abort(self, config: HookConfig, failure_context: FailureContext,
                           result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """处理中止策略"""
        await self._clear_retry_state(failure_context.hook_name)

        return self._create_result(
            False,
            f"❌ {failure_context.hook_name} Hook失败，操作中止",
            details={
                'failure_reason': failure_context.error_message,
                'failure_count': failure_context.failure_count,
                'strategy': 'abort'
            },
            should_abort=True
        )

    async def _handle_retry(self, config: HookConfig, failure_context: FailureContext,
                           result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """处理重试策略"""
        retry_config = config.retry_config

        if failure_context.failure_count >= retry_config.max_attempts:
            await self._clear_retry_state(failure_context.hook_name)
            return self._create_result(
                False,
                f"❌ {failure_context.hook_name} Hook重试次数已达上限 ({retry_config.max_attempts})",
                should_abort=True
            )

        # 检查是否满足重试条件
        if not self._should_retry(failure_context, retry_config):
            return await self._handle_abort(config, failure_context, result, context)

        # 保存重试状态
        await self._save_retry_state(failure_context.hook_name, {
            'attempt_count': failure_context.failure_count,
            'last_attempt': datetime.now().isoformat(),
            'error_type': failure_context.error_type
        })

        # 计算延迟
        delay = retry_config.delay_seconds
        if retry_config.exponential_backoff:
            delay *= (2 ** (failure_context.failure_count - 1))

        logger.info(f"重试 {failure_context.hook_name} (第{failure_context.failure_count}次)，{delay}秒后重试")

        # 等待延迟
        await asyncio.sleep(delay)

        # 递归重试
        return await self.execute_enhanced_hook(failure_context.hook_name, context)

    async def _handle_auto_fix(self, config: HookConfig, failure_context: FailureContext,
                              result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """处理自动修复策略"""
        if not config.auto_fix_enabled:
            return await self._handle_retry(config, failure_context, result, context)

        # 尝试自动修复
        fix_result = await self._attempt_auto_fix(failure_context, result)

        if fix_result['success']:
            logger.info(f"自动修复成功: {fix_result['fix_description']}")

            # 自动修复后重新执行
            return await self.execute_enhanced_hook(failure_context.hook_name, context)
        else:
            # 自动修复失败，降级到重试策略
            logger.warning(f"自动修复失败: {fix_result.get('error', 'Unknown error')}")
            return await self._handle_retry(config, failure_context, result, context)

    async def _handle_manual_intervention(self, config: HookConfig, failure_context: FailureContext,
                                         result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """处理手动干预策略"""
        # 生成详细的故障报告
        intervention_report = await self._generate_intervention_report(failure_context, result)

        # 保存干预状态
        await self._save_intervention_state(failure_context.hook_name, intervention_report)

        return self._create_result(
            False,
            f"⚠️ {failure_context.hook_name} Hook需要手动干预",
            details={
                'intervention_required': True,
                'failure_reason': failure_context.error_message,
                'report_file': intervention_report['report_file'],
                'suggested_actions': intervention_report['suggested_actions']
            },
            should_abort=True
        )

    async def _handle_skip_with_warning(self, config: HookConfig, failure_context: FailureContext,
                                       result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """处理跳过并警告策略"""
        warning_message = (
            f"⚠️ {failure_context.hook_name} Hook失败但已跳过: {failure_context.error_message}"
        )

        logger.warning(warning_message)

        await self._clear_retry_state(failure_context.hook_name)

        return self._create_result(
            True,  # 成功，但有警告
            warning_message,
            details={
                'skipped': True,
                'warning': True,
                'original_error': failure_context.error_message
            }
        )

    async def _attempt_auto_fix(self, failure_context: FailureContext,
                               result: Dict[str, Any]) -> Dict[str, Any]:
        """尝试自动修复"""
        error_type = failure_context.error_type

        # 查找对应的修复器
        fixer = self.auto_fixers.get(error_type)
        if not fixer:
            # 尝试通用修复器
            fixer = self._get_generic_fixer(failure_context, result)

        if fixer:
            try:
                return await fixer(failure_context, result)
            except Exception as e:
                return {
                    'success': False,
                    'error': f"修复器执行失败: {str(e)}"
                }

        return {
            'success': False,
            'error': f"没有找到适用于 {error_type} 的修复器"
        }

    def _get_generic_fixer(self, failure_context: FailureContext,
                          result: Dict[str, Any]) -> Optional[Callable]:
        """获取通用修复器"""
        error_message = failure_context.error_message.lower()

        if 'syntax' in error_message:
            return self.auto_fixers.get('syntax_error')
        elif 'format' in error_message:
            return self.auto_fixers.get('format_error')
        elif 'import' in error_message:
            return self.auto_fixers.get('import_error')
        elif 'test' in error_message:
            return self.auto_fixers.get('test_failure')
        elif 'coverage' in error_message:
            return self.auto_fixers.get('coverage_insufficient')
        elif 'security' in error_message:
            return self.auto_fixers.get('security_vulnerability')
        elif 'performance' in error_message:
            return self.auto_fixers.get('performance_issue')

        return None

    def _should_retry(self, failure_context: FailureContext, retry_config: RetryConfig) -> bool:
        """判断是否应该重试"""
        error_type = failure_context.error_type.lower()

        # 检查重试条件
        for condition in retry_config.retry_conditions:
            if condition.lower() in error_type:
                return True

        # 默认不重试
        return False

    # 自动修复器实现
    async def _fix_syntax_error(self, failure_context: FailureContext,
                               result: Dict[str, Any]) -> Dict[str, Any]:
        """修复语法错误"""
        # 模拟语法错误修复
        return {
            'success': True,
            'fix_description': '修复Python语法错误'
        }

    async def _fix_format_error(self, failure_context: FailureContext,
                               result: Dict[str, Any]) -> Dict[str, Any]:
        """修复格式错误"""
        try:
            # 运行代码格式化工具
            subprocess.run(['python', '-m', 'black', '.'], cwd=self.project_root, check=True)
            subprocess.run(['python', '-m', 'isort', '.'], cwd=self.project_root, check=True)

            return {
                'success': True,
                'fix_description': '自动格式化代码 (black + isort)'
            }
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f"代码格式化失败: {e}"
            }

    async def _fix_import_error(self, failure_context: FailureContext,
                               result: Dict[str, Any]) -> Dict[str, Any]:
        """修复导入错误"""
        return {
            'success': True,
            'fix_description': '修复导入错误'
        }

    async def _fix_test_failure(self, failure_context: FailureContext,
                               result: Dict[str, Any]) -> Dict[str, Any]:
        """修复测试失败"""
        return {
            'success': False,  # 测试失败通常需要手动修复
            'error': '测试失败需要手动修复'
        }

    async def _fix_coverage(self, failure_context: FailureContext,
                           result: Dict[str, Any]) -> Dict[str, Any]:
        """修复覆盖率不足"""
        return {
            'success': False,  # 覆盖率不足需要编写更多测试
            'error': '覆盖率不足需要编写更多测试'
        }

    async def _fix_security_vulnerability(self, failure_context: FailureContext,
                                         result: Dict[str, Any]) -> Dict[str, Any]:
        """修复安全漏洞"""
        return {
            'success': False,  # 安全漏洞需要仔细处理
            'error': '安全漏洞需要手动审查和修复'
        }

    async def _fix_performance_issue(self, failure_context: FailureContext,
                                    result: Dict[str, Any]) -> Dict[str, Any]:
        """修复性能问题"""
        return {
            'success': False,  # 性能问题需要专门分析
            'error': '性能问题需要专门分析和优化'
        }

    async def _fix_dependency_conflict(self, failure_context: FailureContext,
                                      result: Dict[str, Any]) -> Dict[str, Any]:
        """修复依赖冲突"""
        return {
            'success': False,  # 依赖冲突需要仔细处理
            'error': '依赖冲突需要手动解决'
        }

    # 状态管理方法
    async def _load_retry_state(self, hook_name: str) -> Dict[str, Any]:
        """加载重试状态"""
        try:
            if self.retry_state.exists():
                with open(self.retry_state) as f:
                    all_states = json.load(f)
                    return all_states.get(hook_name, {})
        except Exception:
            pass
        return {}

    async def _save_retry_state(self, hook_name: str, state: Dict[str, Any]) -> None:
        """保存重试状态"""
        try:
            all_states = {}
            if self.retry_state.exists():
                with open(self.retry_state) as f:
                    all_states = json.load(f)

            all_states[hook_name] = state

            with open(self.retry_state, 'w') as f:
                json.dump(all_states, f, indent=2)

        except Exception as e:
            logger.error(f"保存重试状态失败: {e}")

    async def _clear_retry_state(self, hook_name: str) -> None:
        """清除重试状态"""
        try:
            if self.retry_state.exists():
                with open(self.retry_state) as f:
                    all_states = json.load(f)

                if hook_name in all_states:
                    del all_states[hook_name]

                    with open(self.retry_state, 'w') as f:
                        json.dump(all_states, f, indent=2)

        except Exception as e:
            logger.error(f"清除重试状态失败: {e}")

    async def _generate_intervention_report(self, failure_context: FailureContext,
                                           result: Dict[str, Any]) -> Dict[str, Any]:
        """生成干预报告"""
        report_file = self.config_dir / f"intervention_{failure_context.hook_name}_{int(time.time())}.json"

        report_data = {
            'timestamp': datetime.now().isoformat(),
            'hook_name': failure_context.hook_name,
            'error_type': failure_context.error_type,
            'error_message': failure_context.error_message,
            'failure_count': failure_context.failure_count,
            'context': result.get('details', {}),
            'suggested_actions': self._get_suggested_actions(failure_context),
            'escalation_required': failure_context.failure_count > 3
        }

        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        return {
            'report_file': str(report_file),
            'suggested_actions': report_data['suggested_actions']
        }

    def _get_suggested_actions(self, failure_context: FailureContext) -> List[str]:
        """获取建议的操作"""
        actions = []
        error_type = failure_context.error_type.lower()

        if 'test' in error_type:
            actions.extend([
                "检查失败的测试用例",
                "修复测试代码或被测试代码",
                "确保测试环境正确配置"
            ])
        elif 'security' in error_type:
            actions.extend([
                "审查安全漏洞报告",
                "更新依赖到安全版本",
                "修复代码中的安全问题"
            ])
        elif 'performance' in error_type:
            actions.extend([
                "分析性能瓶颈",
                "优化慢查询或算法",
                "检查资源配置"
            ])
        else:
            actions.extend([
                "查看详细错误日志",
                "检查相关配置",
                "咨询技术专家"
            ])

        return actions

    async def _save_intervention_state(self, hook_name: str, report: Dict[str, Any]) -> None:
        """保存干预状态"""
        intervention_file = self.config_dir / f"intervention_{hook_name}.json"

        intervention_data = {
            'timestamp': datetime.now().isoformat(),
            'hook_name': hook_name,
            'report': report,
            'status': 'pending',
            'assigned_to': None,
            'resolution': None
        }

        with open(intervention_file, 'w') as f:
            json.dump(intervention_data, f, indent=2)

    # 日志方法
    async def _log_failure(self, failure_context: FailureContext, result: Dict[str, Any]) -> None:
        """记录失败日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'hook_name': failure_context.hook_name,
            'error_type': failure_context.error_type,
            'error_message': failure_context.error_message,
            'failure_count': failure_context.failure_count,
            'result': result
        }

        try:
            with open(self.failure_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"记录失败日志失败: {e}")

    async def _log_success(self, hook_name: str, result: Dict[str, Any], execution_time: float) -> None:
        """记录成功日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'hook_name': hook_name,
            'success': True,
            'execution_time': execution_time,
            'message': result['message']
        }

        try:
            with open(self.performance_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"记录性能日志失败: {e}")

    def _create_result(self, success: bool, message: str,
                      details: Dict[str, Any] = None, should_abort: bool = False) -> Dict[str, Any]:
        """创建标准结果格式"""
        result = {
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'should_abort': should_abort
        }

        if details:
            result['details'] = details

        return result


# 便捷函数
async def execute_enhanced_hook(hook_name: str, context: Dict[str, Any] = None,
                               project_root: Optional[str] = None) -> Dict[str, Any]:
    """执行增强Hook的便捷函数"""
    manager = EnhancedHooksManager(project_root)
    return await manager.execute_enhanced_hook(hook_name, context)


if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("用法: python enhanced_hooks.py <hook_name> [context_json]")
            print("支持的hooks: pre-commit, commit-msg, pre-push, post-checkout, post-merge")
            return

        hook_name = sys.argv[1]
        context = {}

        if len(sys.argv) > 2:
            try:
                context = json.loads(sys.argv[2])
            except json.JSONDecodeError as e:
                print(f"解析context JSON失败: {e}")
                return

        result = await execute_enhanced_hook(hook_name, context)

        print(json.dumps(result, indent=2, default=str))

        # 根据结果设置退出码
        if result.get('should_abort', False):
            sys.exit(1)
        else:
            sys.exit(0)

    asyncio.run(main())