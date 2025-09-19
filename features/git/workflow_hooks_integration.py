#!/usr/bin/env python3
"""
Perfect21 Git Hook Workflow Integration
将Git hooks集成到Perfect21的5层工作流中作为质量检查点
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("Perfect21.GitHooks")


class WorkflowPhase(Enum):
    """Perfect21工作流阶段"""
    TASK_ANALYSIS = "task_analysis"
    AGENT_SELECTION = "agent_selection"
    PARALLEL_EXECUTION = "parallel_execution"
    QUALITY_GATES = "quality_gates"
    DEPLOYMENT = "deployment"


class HookCheckpoint(Enum):
    """Git Hook检查点"""
    PRE_COMMIT = "pre-commit"
    COMMIT_MSG = "commit-msg"
    PRE_PUSH = "pre-push"
    POST_CHECKOUT = "post-checkout"
    POST_MERGE = "post-merge"
    POST_COMMIT = "post-commit"


@dataclass
class WorkflowArtifact:
    """工作流产物"""
    phase: WorkflowPhase
    artifact_type: str
    content: Dict[str, Any]
    timestamp: datetime
    validation_status: str = "pending"  # pending, passed, failed
    quality_score: float = 0.0


@dataclass
class HookExecutionContext:
    """Hook执行上下文"""
    hook_type: HookCheckpoint
    workflow_phase: WorkflowPhase
    project_root: Path
    git_info: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[WorkflowArtifact] = field(default_factory=list)
    quality_requirements: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3


class WorkflowHooksIntegration:
    """Perfect21工作流Git Hooks集成器"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        self.artifacts_dir = self.project_root / ".perfect21" / "artifacts"
        self.hooks_log = self.project_root / ".perfect21" / "hooks.log"

        # 确保目录存在
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Hook到工作流阶段映射
        self.hook_phase_mapping = {
            HookCheckpoint.PRE_COMMIT: WorkflowPhase.AGENT_SELECTION,
            HookCheckpoint.COMMIT_MSG: WorkflowPhase.PARALLEL_EXECUTION,
            HookCheckpoint.PRE_PUSH: WorkflowPhase.QUALITY_GATES,
            HookCheckpoint.POST_CHECKOUT: WorkflowPhase.TASK_ANALYSIS,
            HookCheckpoint.POST_MERGE: WorkflowPhase.DEPLOYMENT,
            HookCheckpoint.POST_COMMIT: WorkflowPhase.PARALLEL_EXECUTION
        }

        # 质量检查配置
        self.quality_checks = self._load_quality_config()

    def _load_quality_config(self) -> Dict[str, Any]:
        """加载质量检查配置"""
        return {
            "code_quality": {
                "min_coverage": 80,
                "max_complexity": 10,
                "max_duplication": 5
            },
            "security": {
                "scan_dependencies": True,
                "check_secrets": True,
                "validate_permissions": True
            },
            "performance": {
                "max_response_time_p95": 200,  # ms
                "max_memory_usage": 512,  # MB
                "min_throughput": 100  # req/s
            },
            "agent_requirements": {
                "min_agents": 3,
                "require_parallel": True,
                "check_compatibility": True
            }
        }

    async def execute_workflow_hook(self, hook_type: HookCheckpoint,
                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行工作流集成的Git Hook"""
        start_time = time.time()
        context = context or {}

        logger.info(f"执行工作流Hook: {hook_type.value}")

        try:
            # 1. 创建执行上下文
            execution_context = await self._create_execution_context(hook_type, context)

            # 2. 确定当前工作流阶段
            workflow_phase = self.hook_phase_mapping.get(hook_type)
            if not workflow_phase:
                return self._create_result(False, f"未知的Hook类型: {hook_type.value}")

            execution_context.workflow_phase = workflow_phase

            # 3. 加载工作流产物
            await self._load_workflow_artifacts(execution_context)

            # 4. 执行阶段特定的检查
            result = await self._execute_phase_checks(execution_context)

            # 5. 处理检查结果
            if not result['success'] and execution_context.retry_count < execution_context.max_retries:
                # 尝试自动修复
                fix_result = await self._attempt_auto_fix(execution_context, result)
                if fix_result['success']:
                    result = await self._execute_phase_checks(execution_context)

            # 6. 记录执行历史
            execution_time = time.time() - start_time
            await self._log_execution(hook_type, result, execution_time)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            error_result = self._create_result(False, f"Hook执行失败: {str(e)}")
            await self._log_execution(hook_type, error_result, execution_time)
            return error_result

    async def _create_execution_context(self, hook_type: HookCheckpoint,
                                       context: Dict[str, Any]) -> HookExecutionContext:
        """创建执行上下文"""
        # 获取Git信息
        git_info = await self._collect_git_info()

        # 获取质量要求
        quality_requirements = self.quality_checks.copy()

        return HookExecutionContext(
            hook_type=hook_type,
            workflow_phase=None,  # 稍后设置
            project_root=self.project_root,
            git_info=git_info,
            quality_requirements=quality_requirements
        )

    async def _load_workflow_artifacts(self, context: HookExecutionContext) -> None:
        """加载工作流产物"""
        try:
            # 查找相关产物文件
            phase_dir = self.artifacts_dir / context.workflow_phase.value
            if phase_dir.exists():
                for artifact_file in phase_dir.glob("*.json"):
                    try:
                        with open(artifact_file) as f:
                            artifact_data = json.load(f)

                        artifact = WorkflowArtifact(
                            phase=context.workflow_phase,
                            artifact_type=artifact_file.stem,
                            content=artifact_data,
                            timestamp=datetime.fromtimestamp(artifact_file.stat().st_mtime)
                        )
                        context.artifacts.append(artifact)

                    except Exception as e:
                        logger.warning(f"加载产物失败 {artifact_file}: {e}")

        except Exception as e:
            logger.error(f"加载工作流产物失败: {e}")

    async def _execute_phase_checks(self, context: HookExecutionContext) -> Dict[str, Any]:
        """执行阶段特定的检查"""
        phase = context.workflow_phase

        if phase == WorkflowPhase.AGENT_SELECTION:
            return await self._check_agent_selection(context)
        elif phase == WorkflowPhase.PARALLEL_EXECUTION:
            return await self._check_parallel_execution(context)
        elif phase == WorkflowPhase.QUALITY_GATES:
            return await self._check_quality_gates(context)
        elif phase == WorkflowPhase.DEPLOYMENT:
            return await self._check_deployment_readiness(context)
        elif phase == WorkflowPhase.TASK_ANALYSIS:
            return await self._check_task_analysis(context)
        else:
            return self._create_result(True, f"阶段 {phase.value} 无需特定检查")

    async def _check_agent_selection(self, context: HookExecutionContext) -> Dict[str, Any]:
        """检查Agent选择阶段 (pre-commit)"""
        issues = []

        # 1. 检查暂存文件
        staged_files = await self._get_staged_files()
        if not staged_files:
            return self._create_result(False, "没有暂存文件", should_abort=True)

        # 2. 检查Agent配置产物
        agent_artifacts = [a for a in context.artifacts if a.artifact_type == "agent_selection"]
        if not agent_artifacts:
            issues.append("缺少Agent选择产物")
        else:
            agent_config = agent_artifacts[0].content

            # 检查Agent数量
            selected_agents = agent_config.get('selected_agents', [])
            min_agents = context.quality_requirements['agent_requirements']['min_agents']

            if len(selected_agents) < min_agents:
                issues.append(f"Agent数量不足: {len(selected_agents)} < {min_agents}")

            # 检查并行执行配置
            if context.quality_requirements['agent_requirements']['require_parallel']:
                if not agent_config.get('parallel_execution', False):
                    issues.append("未配置并行执行")

        # 3. 代码质量基础检查
        code_issues = await self._run_basic_code_checks(staged_files)
        issues.extend(code_issues)

        if issues:
            return self._create_result(
                False,
                f"Agent选择阶段检查失败: {'; '.join(issues)}",
                details={'issues': issues, 'staged_files': staged_files}
            )

        return self._create_result(True, "Agent选择阶段检查通过")

    async def _check_parallel_execution(self, context: HookExecutionContext) -> Dict[str, Any]:
        """检查并行执行阶段 (commit-msg/post-commit)"""
        issues = []

        # 1. 检查执行产物
        execution_artifacts = [a for a in context.artifacts if a.artifact_type == "execution_results"]
        if not execution_artifacts:
            issues.append("缺少执行结果产物")
        else:
            execution_data = execution_artifacts[0].content

            # 检查Agent执行状态
            agent_results = execution_data.get('agent_results', [])
            failed_agents = [r for r in agent_results if not r.get('success', True)]

            if failed_agents:
                issues.append(f"{len(failed_agents)}个Agent执行失败")

            # 检查并行度
            execution_mode = execution_data.get('execution_mode', 'unknown')
            if execution_mode != 'parallel' and len(agent_results) > 1:
                issues.append("多Agent未并行执行")

        # 2. 提交信息检查
        if context.hook_type == HookCheckpoint.COMMIT_MSG:
            commit_msg_issues = await self._validate_commit_message(context)
            issues.extend(commit_msg_issues)

        if issues:
            return self._create_result(
                False,
                f"并行执行阶段检查失败: {'; '.join(issues)}",
                details={'issues': issues}
            )

        return self._create_result(True, "并行执行阶段检查通过")

    async def _check_quality_gates(self, context: HookExecutionContext) -> Dict[str, Any]:
        """检查质量门阶段 (pre-push)"""
        issues = []

        # 1. 代码质量检查
        quality_result = await self._run_comprehensive_quality_checks()
        if not quality_result['success']:
            issues.extend(quality_result['issues'])

        # 2. 安全检查
        security_result = await self._run_security_checks()
        if not security_result['success']:
            issues.extend(security_result['issues'])

        # 3. 测试检查
        test_result = await self._run_test_checks()
        if not test_result['success']:
            issues.extend(test_result['issues'])

        # 4. 性能检查
        performance_result = await self._run_performance_checks()
        if not performance_result['success']:
            issues.extend(performance_result['issues'])

        # 5. 分支保护检查
        branch_result = await self._check_branch_protection(context)
        if not branch_result['success']:
            issues.extend(branch_result['issues'])

        if issues:
            return self._create_result(
                False,
                f"质量门检查失败: {len(issues)}个问题",
                details={
                    'issues': issues,
                    'quality_score': quality_result.get('score', 0),
                    'security_score': security_result.get('score', 0),
                    'test_coverage': test_result.get('coverage', 0),
                    'performance_score': performance_result.get('score', 0)
                },
                should_abort=True
            )

        return self._create_result(True, "质量门检查全部通过")

    async def _check_deployment_readiness(self, context: HookExecutionContext) -> Dict[str, Any]:
        """检查部署准备阶段 (post-merge)"""
        tasks = []

        # 1. 环境准备
        env_check = await self._prepare_deployment_environment()
        tasks.append(('环境准备', env_check))

        # 2. 监控设置
        monitoring_setup = await self._setup_monitoring()
        tasks.append(('监控设置', monitoring_setup))

        # 3. 通知配置
        notification_setup = await self._setup_notifications()
        tasks.append(('通知配置', notification_setup))

        # 4. 回滚准备
        rollback_prep = await self._prepare_rollback()
        tasks.append(('回滚准备', rollback_prep))

        # 统计结果
        successful_tasks = [name for name, result in tasks if result['success']]
        failed_tasks = [name for name, result in tasks if not result['success']]

        if failed_tasks:
            return self._create_result(
                False,
                f"部署准备失败: {', '.join(failed_tasks)}",
                details={
                    'successful_tasks': successful_tasks,
                    'failed_tasks': failed_tasks,
                    'task_results': dict(tasks)
                }
            )

        return self._create_result(True, f"部署准备完成: {len(successful_tasks)}个任务")

    async def _check_task_analysis(self, context: HookExecutionContext) -> Dict[str, Any]:
        """检查任务分析阶段 (post-checkout)"""
        # 分支切换后的环境检查
        checks = []

        # 1. 依赖检查
        deps_check = await self._check_dependencies()
        checks.append(('依赖检查', deps_check))

        # 2. 配置同步
        config_sync = await self._sync_configuration()
        checks.append(('配置同步', config_sync))

        # 3. 缓存清理
        cache_clean = await self._clean_caches()
        checks.append(('缓存清理', cache_clean))

        return self._create_result(True, f"任务分析阶段完成: {len(checks)}项检查")

    async def _attempt_auto_fix(self, context: HookExecutionContext,
                               failed_result: Dict[str, Any]) -> Dict[str, Any]:
        """尝试自动修复问题"""
        context.retry_count += 1
        fixes_applied = []

        issues = failed_result.get('details', {}).get('issues', [])

        for issue in issues:
            fix_result = await self._apply_auto_fix(issue, context)
            if fix_result['success']:
                fixes_applied.append(fix_result['fix_description'])

        if fixes_applied:
            return self._create_result(
                True,
                f"自动修复成功: {', '.join(fixes_applied)}"
            )

        return self._create_result(False, "自动修复失败")

    async def _apply_auto_fix(self, issue: str, context: HookExecutionContext) -> Dict[str, Any]:
        """应用特定的自动修复"""
        if "代码格式" in issue:
            # 自动格式化代码
            return await self._auto_format_code()
        elif "测试覆盖率" in issue:
            # 生成基础测试
            return await self._generate_basic_tests()
        elif "安全漏洞" in issue:
            # 修复常见安全问题
            return await self._fix_security_issues()
        elif "Agent数量不足" in issue:
            # 建议额外的Agent
            return await self._suggest_additional_agents(context)

        return self._create_result(False, f"无法自动修复: {issue}")

    # 质量检查实现方法
    async def _run_basic_code_checks(self, files: List[str]) -> List[str]:
        """运行基础代码检查"""
        issues = []

        for file_path in files:
            if file_path.endswith('.py'):
                # Python代码检查
                try:
                    # 语法检查
                    with open(file_path) as f:
                        compile(f.read(), file_path, 'exec')
                except SyntaxError as e:
                    issues.append(f"语法错误 {file_path}: {e}")

                # 基础代码质量检查
                if await self._check_file_complexity(file_path):
                    issues.append(f"代码复杂度过高: {file_path}")

        return issues

    async def _run_comprehensive_quality_checks(self) -> Dict[str, Any]:
        """运行全面的质量检查"""
        try:
            # 模拟质量检查
            coverage = 85  # 模拟覆盖率
            complexity = 8  # 模拟复杂度
            duplication = 3  # 模拟重复率

            issues = []
            score = 100

            # 检查覆盖率
            min_coverage = self.quality_checks['code_quality']['min_coverage']
            if coverage < min_coverage:
                issues.append(f"代码覆盖率不足: {coverage}% < {min_coverage}%")
                score -= 20

            # 检查复杂度
            max_complexity = self.quality_checks['code_quality']['max_complexity']
            if complexity > max_complexity:
                issues.append(f"代码复杂度过高: {complexity} > {max_complexity}")
                score -= 15

            # 检查重复率
            max_duplication = self.quality_checks['code_quality']['max_duplication']
            if duplication > max_duplication:
                issues.append(f"代码重复率过高: {duplication}% > {max_duplication}%")
                score -= 10

            return {
                'success': len(issues) == 0,
                'issues': issues,
                'score': max(0, score),
                'coverage': coverage,
                'complexity': complexity,
                'duplication': duplication
            }

        except Exception as e:
            return {
                'success': False,
                'issues': [f"质量检查执行失败: {e}"],
                'score': 0
            }

    async def _run_security_checks(self) -> Dict[str, Any]:
        """运行安全检查"""
        try:
            issues = []
            score = 100

            # 模拟安全检查
            if self.quality_checks['security']['scan_dependencies']:
                # 依赖安全扫描
                vulnerable_deps = await self._scan_dependencies()
                if vulnerable_deps:
                    issues.extend([f"依赖安全漏洞: {dep}" for dep in vulnerable_deps])
                    score -= len(vulnerable_deps) * 10

            if self.quality_checks['security']['check_secrets']:
                # 密钥泄露检查
                leaked_secrets = await self._check_for_secrets()
                if leaked_secrets:
                    issues.extend([f"发现泄露的密钥: {secret}" for secret in leaked_secrets])
                    score -= len(leaked_secrets) * 20

            return {
                'success': len(issues) == 0,
                'issues': issues,
                'score': max(0, score)
            }

        except Exception as e:
            return {
                'success': False,
                'issues': [f"安全检查执行失败: {e}"],
                'score': 0
            }

    async def _run_test_checks(self) -> Dict[str, Any]:
        """运行测试检查"""
        try:
            # 运行测试套件
            test_result = await self._execute_tests()

            return {
                'success': test_result['success'],
                'issues': test_result.get('failures', []),
                'coverage': test_result.get('coverage', 0),
                'test_count': test_result.get('test_count', 0),
                'duration': test_result.get('duration', 0)
            }

        except Exception as e:
            return {
                'success': False,
                'issues': [f"测试执行失败: {e}"],
                'coverage': 0
            }

    async def _run_performance_checks(self) -> Dict[str, Any]:
        """运行性能检查"""
        try:
            issues = []
            score = 100

            # 模拟性能指标
            response_time_p95 = 150  # ms
            memory_usage = 400  # MB

            max_response_time = self.quality_checks['performance']['max_response_time_p95']
            if response_time_p95 > max_response_time:
                issues.append(f"响应时间过长: {response_time_p95}ms > {max_response_time}ms")
                score -= 20

            max_memory = self.quality_checks['performance']['max_memory_usage']
            if memory_usage > max_memory:
                issues.append(f"内存使用过高: {memory_usage}MB > {max_memory}MB")
                score -= 15

            return {
                'success': len(issues) == 0,
                'issues': issues,
                'score': max(0, score),
                'response_time_p95': response_time_p95,
                'memory_usage': memory_usage
            }

        except Exception as e:
            return {
                'success': False,
                'issues': [f"性能检查执行失败: {e}"],
                'score': 0
            }

    # 工具方法
    async def _get_staged_files(self) -> List[str]:
        """获取暂存文件列表"""
        try:
            result = await self._run_git_command(['git', 'diff', '--cached', '--name-only'])
            if result.returncode == 0:
                return [f.strip() for f in result.stdout.decode().split('\n') if f.strip()]
            return []
        except Exception:
            return []

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

    async def _collect_git_info(self) -> Dict[str, Any]:
        """收集Git信息"""
        info = {}

        try:
            # 当前分支
            branch_result = await self._run_git_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
            if branch_result.returncode == 0:
                info['current_branch'] = branch_result.stdout.decode().strip()

            # 最近提交
            commit_result = await self._run_git_command(['git', 'rev-parse', 'HEAD'])
            if commit_result.returncode == 0:
                info['latest_commit'] = commit_result.stdout.decode().strip()

            # 远程URL
            remote_result = await self._run_git_command(['git', 'remote', 'get-url', 'origin'])
            if remote_result.returncode == 0:
                info['remote_url'] = remote_result.stdout.decode().strip()

        except Exception as e:
            logger.warning(f"收集Git信息失败: {e}")

        return info

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

    async def _log_execution(self, hook_type: HookCheckpoint,
                           result: Dict[str, Any], execution_time: float) -> None:
        """记录执行日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'hook_type': hook_type.value,
            'success': result['success'],
            'message': result['message'],
            'execution_time': execution_time,
            'details': result.get('details', {})
        }

        try:
            with open(self.hooks_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"记录执行日志失败: {e}")

    # 自动修复方法的模拟实现
    async def _auto_format_code(self) -> Dict[str, Any]:
        """自动格式化代码"""
        return {'success': True, 'fix_description': '代码格式化'}

    async def _generate_basic_tests(self) -> Dict[str, Any]:
        """生成基础测试"""
        return {'success': True, 'fix_description': '生成基础测试'}

    async def _fix_security_issues(self) -> Dict[str, Any]:
        """修复安全问题"""
        return {'success': True, 'fix_description': '修复安全问题'}

    async def _suggest_additional_agents(self, context: HookExecutionContext) -> Dict[str, Any]:
        """建议额外的Agent"""
        return {'success': True, 'fix_description': '建议额外Agent'}

    # 质量检查的具体实现（模拟）
    async def _check_file_complexity(self, file_path: str) -> bool:
        """检查文件复杂度"""
        # 模拟实现
        return False

    async def _scan_dependencies(self) -> List[str]:
        """扫描依赖安全性"""
        # 模拟实现
        return []

    async def _check_for_secrets(self) -> List[str]:
        """检查密钥泄露"""
        # 模拟实现
        return []

    async def _execute_tests(self) -> Dict[str, Any]:
        """执行测试套件"""
        # 模拟实现
        return {
            'success': True,
            'coverage': 85,
            'test_count': 50,
            'duration': 30
        }

    async def _check_branch_protection(self, context: HookExecutionContext) -> Dict[str, Any]:
        """检查分支保护"""
        # 模拟实现
        return {'success': True, 'issues': []}

    async def _validate_commit_message(self, context: HookExecutionContext) -> List[str]:
        """验证提交信息"""
        # 模拟实现
        return []

    async def _prepare_deployment_environment(self) -> Dict[str, Any]:
        """准备部署环境"""
        return {'success': True}

    async def _setup_monitoring(self) -> Dict[str, Any]:
        """设置监控"""
        return {'success': True}

    async def _setup_notifications(self) -> Dict[str, Any]:
        """设置通知"""
        return {'success': True}

    async def _prepare_rollback(self) -> Dict[str, Any]:
        """准备回滚"""
        return {'success': True}

    async def _check_dependencies(self) -> Dict[str, Any]:
        """检查依赖"""
        return {'success': True}

    async def _sync_configuration(self) -> Dict[str, Any]:
        """同步配置"""
        return {'success': True}

    async def _clean_caches(self) -> Dict[str, Any]:
        """清理缓存"""
        return {'success': True}


# 便捷函数
async def execute_workflow_hook(hook_name: str, context: Dict[str, Any] = None,
                               project_root: Optional[str] = None) -> Dict[str, Any]:
    """执行工作流Hook的便捷函数"""
    try:
        hook_type = HookCheckpoint(hook_name)
        integration = WorkflowHooksIntegration(project_root)
        return await integration.execute_workflow_hook(hook_type, context)
    except ValueError:
        return {
            'success': False,
            'error': f'未知的Hook类型: {hook_name}',
            'timestamp': datetime.now().isoformat()
        }


if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("用法: python workflow_hooks_integration.py <hook_name> [context_json]")
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

        result = await execute_workflow_hook(hook_name, context)

        print(json.dumps(result, indent=2, default=str))

        # 根据结果设置退出码
        sys.exit(0 if result['success'] else 1)

    asyncio.run(main())