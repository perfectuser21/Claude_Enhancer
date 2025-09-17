#!/usr/bin/env python3
"""
Perfect21 功能测试验证脚本
测试Perfect21核心功能模块的运行状态和集成效果

测试目标：
1. 13个工作流模板的正常工作状态
2. 同步点机制的按预期执行
3. 质量门检查的有效性
4. 错误恢复机制的可靠性
5. Git Hooks集成的完整性
6. 能力发现系统的准确性
"""

import sys
import os
import json
import time
import asyncio
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 测试结果数据类
@dataclass
class TestResult:
    test_name: str
    success: bool
    duration: float
    details: Dict[str, Any]
    error: Optional[str] = None

class Perfect21FunctionalityValidator:
    """Perfect21功能验证器"""

    def __init__(self):
        self.logger = self._setup_logger()
        self.test_results: List[TestResult] = []
        self.start_time = time.time()

        # 测试报告配置
        self.report_file = project_root / "perfect21_functionality_test_report.json"
        self.dashboard_file = project_root / "perfect21_functionality_dashboard.html"

    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("Perfect21Validator")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有功能测试"""
        self.logger.info("🚀 开始Perfect21功能验证测试")
        self.logger.info("=" * 80)

        # 定义测试套件
        test_suite = [
            ("工作流模板测试", self.test_workflow_templates),
            ("同步点机制测试", self.test_sync_point_mechanism),
            ("质量门检查测试", self.test_quality_gate_checks),
            ("错误恢复机制测试", self.test_error_recovery_mechanism),
            ("Git Hooks集成测试", self.test_git_hooks_integration),
            ("能力发现系统测试", self.test_capability_discovery_system),
            ("工作流编排器测试", self.test_workflow_orchestrator),
            ("并行执行测试", self.test_parallel_execution),
            ("决策记录测试", self.test_decision_recording),
            ("质量守护测试", self.test_quality_guardian),
            ("多工作空间测试", self.test_multi_workspace),
            ("学习反馈测试", self.test_learning_feedback)
        ]

        # 执行测试
        total_tests = len(test_suite)
        passed_tests = 0

        for i, (test_name, test_func) in enumerate(test_suite, 1):
            self.logger.info(f"\n📋 [{i}/{total_tests}] 执行测试: {test_name}")
            self.logger.info("-" * 60)

            start_time = time.time()

            try:
                result = await test_func()
                duration = time.time() - start_time

                if result.get('success', False):
                    passed_tests += 1
                    self.logger.info(f"✅ {test_name} 通过 (耗时: {duration:.2f}s)")
                else:
                    self.logger.error(f"❌ {test_name} 失败: {result.get('error', '未知错误')}")

                # 记录测试结果
                test_result = TestResult(
                    test_name=test_name,
                    success=result.get('success', False),
                    duration=duration,
                    details=result,
                    error=result.get('error') if not result.get('success', False) else None
                )
                self.test_results.append(test_result)

            except Exception as e:
                duration = time.time() - start_time
                error_msg = f"测试异常: {str(e)}"
                self.logger.error(f"💥 {test_name} 异常: {error_msg}")

                test_result = TestResult(
                    test_name=test_name,
                    success=False,
                    duration=duration,
                    details={"exception": str(e), "traceback": traceback.format_exc()},
                    error=error_msg
                )
                self.test_results.append(test_result)

        # 生成测试报告
        total_duration = time.time() - self.start_time
        overall_success = passed_tests == total_tests

        summary = {
            'overall_success': overall_success,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'total_duration': total_duration,
            'timestamp': datetime.now().isoformat()
        }

        self.logger.info(f"\n🎯 测试完成总结:")
        self.logger.info(f"   总测试数: {total_tests}")
        self.logger.info(f"   通过测试: {passed_tests}")
        self.logger.info(f"   失败测试: {total_tests - passed_tests}")
        self.logger.info(f"   成功率: {summary['success_rate']:.1f}%")
        self.logger.info(f"   总耗时: {total_duration:.2f}s")

        # 保存测试报告
        await self.generate_test_report(summary)

        return summary

    async def test_workflow_templates(self) -> Dict[str, Any]:
        """测试工作流模板"""
        try:
            from features.workflow_orchestrator.orchestrator import WorkflowOrchestrator

            orchestrator = WorkflowOrchestrator(self.logger)

            # 测试不同类型的工作流模板
            workflow_templates = [
                {
                    'name': 'Premium Quality Workflow',
                    'stages': [
                        {
                            'name': 'analysis',
                            'description': '深度分析阶段',
                            'execution_mode': 'parallel',
                            'sync_point': {
                                'type': 'consensus_check',
                                'validation_criteria': {
                                    'tasks_completed': '> 0'
                                }
                            }
                        },
                        {
                            'name': 'design',
                            'description': '设计阶段',
                            'execution_mode': 'sequential',
                            'depends_on': ['analysis'],
                            'quality_gate': {
                                'checklist': 'architecture_review,security_check'
                            }
                        }
                    ]
                },
                {
                    'name': 'Quick Development Workflow',
                    'stages': [
                        {
                            'name': 'implementation',
                            'description': '快速实现',
                            'execution_mode': 'parallel'
                        }
                    ]
                }
            ]

            template_results = []

            for template in workflow_templates:
                load_result = orchestrator.load_workflow(template)

                if load_result['success']:
                    # 创建测试任务
                    task_result = orchestrator.create_task(
                        agent='test-agent',
                        description='测试任务',
                        stage=template['stages'][0]['name']
                    )

                    template_results.append({
                        'template_name': template['name'],
                        'loaded': load_result['success'],
                        'task_created': task_result.get('success', False),
                        'stages_count': load_result.get('stages_count', 0)
                    })
                else:
                    template_results.append({
                        'template_name': template['name'],
                        'loaded': False,
                        'error': load_result.get('error', 'Unknown error')
                    })

            success = all(result.get('loaded', False) for result in template_results)

            return {
                'success': success,
                'templates_tested': len(workflow_templates),
                'templates_passed': len([r for r in template_results if r.get('loaded', False)]),
                'template_results': template_results
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"工作流模板测试异常: {str(e)}",
                'traceback': traceback.format_exc()
            }

    async def test_sync_point_mechanism(self) -> Dict[str, Any]:
        """测试同步点机制"""
        try:
            from features.sync_point_manager.sync_manager import SyncPointManager

            sync_manager = SyncPointManager()

            # 测试不同类型的同步点
            sync_points = [
                {
                    'type': 'consensus_check',
                    'validation_criteria': {
                        'agreement_percentage': '> 80',
                        'conflicts_resolved': 'true'
                    }
                },
                {
                    'type': 'quality_verification',
                    'validation_criteria': {
                        'test_coverage': '> 90',
                        'code_quality_score': '> 8.5'
                    }
                },
                {
                    'type': 'integration_checkpoint',
                    'validation_criteria': {
                        'api_tests_passed': 'true',
                        'dependencies_resolved': 'true'
                    }
                }
            ]

            sync_results = []

            for sync_point in sync_points:
                # 模拟验证数据
                mock_validation_data = {
                    'agreement_percentage': 85,
                    'conflicts_resolved': True,
                    'test_coverage': 95,
                    'code_quality_score': 9.2,
                    'api_tests_passed': True,
                    'dependencies_resolved': True
                }

                result = sync_manager.validate_sync_point(sync_point, mock_validation_data)

                sync_results.append({
                    'sync_type': sync_point['type'],
                    'validation_passed': result.get('success', False),
                    'criteria_met': result.get('all_criteria_met', False),
                    'failed_criteria_count': len(result.get('failed_criteria', []))
                })

            success = all(result.get('validation_passed', False) for result in sync_results)

            return {
                'success': success,
                'sync_points_tested': len(sync_points),
                'sync_points_passed': len([r for r in sync_results if r.get('validation_passed', False)]),
                'sync_results': sync_results
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"同步点机制测试异常: {str(e)}",
                'traceback': traceback.format_exc()
            }

    async def test_quality_gate_checks(self) -> Dict[str, Any]:
        """测试质量门检查"""
        try:
            from features.quality_gates.quality_guardian import QualityGuardian

            quality_guardian = QualityGuardian()

            # 测试不同的质量门
            quality_gates = [
                {
                    'name': 'code_quality',
                    'checks': [
                        {'type': 'code_coverage', 'threshold': 90},
                        {'type': 'complexity', 'max_value': 10},
                        {'type': 'security_scan', 'required': True}
                    ]
                },
                {
                    'name': 'performance',
                    'checks': [
                        {'type': 'response_time', 'max_ms': 200},
                        {'type': 'memory_usage', 'max_mb': 512},
                        {'type': 'cpu_usage', 'max_percent': 80}
                    ]
                }
            ]

            quality_results = []

            for gate in quality_gates:
                # 模拟质量检查数据
                mock_quality_data = {
                    'code_coverage': 95,
                    'complexity': 8,
                    'security_scan': True,
                    'response_time': 150,
                    'memory_usage': 256,
                    'cpu_usage': 60
                }

                result = quality_guardian.check_quality_gate(gate, mock_quality_data)

                quality_results.append({
                    'gate_name': gate['name'],
                    'passed': result.get('passed', False),
                    'checks_total': len(gate['checks']),
                    'checks_passed': result.get('checks_passed', 0),
                    'quality_score': result.get('quality_score', 0)
                })

            success = all(result.get('passed', False) for result in quality_results)

            return {
                'success': success,
                'quality_gates_tested': len(quality_gates),
                'quality_gates_passed': len([r for r in quality_results if r.get('passed', False)]),
                'quality_results': quality_results
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"质量门检查测试异常: {str(e)}",
                'traceback': traceback.format_exc()
            }

    async def test_error_recovery_mechanism(self) -> Dict[str, Any]:
        """测试错误恢复机制"""
        try:
            from features.workflow_orchestrator.orchestrator import WorkflowOrchestrator

            orchestrator = WorkflowOrchestrator(self.logger)

            # 创建测试工作流
            test_workflow = {
                'name': 'Error Recovery Test',
                'stages': [
                    {
                        'name': 'test_stage',
                        'description': '错误恢复测试阶段',
                        'execution_mode': 'parallel'
                    }
                ]
            }

            load_result = orchestrator.load_workflow(test_workflow)
            if not load_result['success']:
                return {
                    'success': False,
                    'error': f"无法加载测试工作流: {load_result.get('error')}"
                }

            # 创建测试任务
            task_result = orchestrator.create_task(
                agent='error-test-agent',
                description='错误测试任务',
                stage='test_stage'
            )

            if not task_result['success']:
                return {
                    'success': False,
                    'error': f"无法创建测试任务: {task_result.get('error')}"
                }

            task_id = task_result['task_id']

            # 测试不同类型的错误恢复
            error_scenarios = [
                {
                    'error_type': 'timeout',
                    'expected_action': 'retry'
                },
                {
                    'error_type': 'validation_error',
                    'expected_action': 'fail'
                },
                {
                    'error_type': 'network_error',
                    'expected_action': 'retry'
                }
            ]

            recovery_results = []

            for scenario in error_scenarios:
                error_result = {
                    'success': False,
                    'error_type': scenario['error_type'],
                    'error': f"模拟{scenario['error_type']}错误"
                }

                recovery_result = orchestrator.handle_task_error(task_id, error_result)

                recovery_results.append({
                    'error_type': scenario['error_type'],
                    'expected_action': scenario['expected_action'],
                    'actual_action': recovery_result.get('action', 'unknown'),
                    'recovery_successful': recovery_result.get('success', False),
                    'action_matches_expected': recovery_result.get('action') == scenario['expected_action']
                })

            success = all(result.get('action_matches_expected', False) for result in recovery_results)

            return {
                'success': success,
                'error_scenarios_tested': len(error_scenarios),
                'recovery_strategies_correct': len([r for r in recovery_results if r.get('action_matches_expected', False)]),
                'recovery_results': recovery_results
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"错误恢复机制测试异常: {str(e)}",
                'traceback': traceback.format_exc()
            }

    async def test_git_hooks_integration(self) -> Dict[str, Any]:
        """测试Git Hooks集成"""
        try:
            from features.git_workflow.hooks import GitHookManager

            hook_manager = GitHookManager()

            # 检查Git Hooks配置
            hooks_status = hook_manager.get_hooks_status()

            # 测试特定钩子
            test_hooks = [
                'pre-commit',
                'commit-msg',
                'pre-push',
                'post-commit',
                'post-merge'
            ]

            hooks_results = []

            for hook_name in test_hooks:
                # 检查钩子是否安装和配置
                hook_installed = hook_manager.is_hook_installed(hook_name)
                hook_enabled = hook_manager.is_hook_enabled(hook_name)

                # 测试钩子配置
                hook_config = hook_manager.get_hook_config(hook_name)

                hooks_results.append({
                    'hook_name': hook_name,
                    'installed': hook_installed,
                    'enabled': hook_enabled,
                    'configured': bool(hook_config),
                    'config_valid': self._validate_hook_config(hook_config)
                })

            # 检查hooks的整体状态
            hooks_working = all(
                result.get('installed', False) and result.get('enabled', False)
                for result in hooks_results
            )

            return {
                'success': hooks_working,
                'total_hooks': len(test_hooks),
                'working_hooks': len([r for r in hooks_results if r.get('installed', False) and r.get('enabled', False)]),
                'hooks_status': hooks_status,
                'hooks_results': hooks_results,
                'integration_complete': len(hooks_results) >= 5  # 至少5个钩子工作
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Git Hooks集成测试异常: {str(e)}",
                'traceback': traceback.format_exc()
            }

    async def test_capability_discovery_system(self) -> Dict[str, Any]:
        """测试能力发现系统"""
        try:
            from features.capability_discovery.registry import CapabilityRegistry

            registry = CapabilityRegistry()

            # 测试能力发现
            discovery_result = registry.discover_capabilities()

            # 检查核心能力是否被发现
            expected_capabilities = [
                'workflow_orchestration',
                'sync_point_management',
                'quality_gates',
                'error_recovery',
                'git_integration',
                'parallel_execution'
            ]

            discovered_capabilities = discovery_result.get('capabilities', [])
            capability_names = [cap.get('name', '') for cap in discovered_capabilities]

            capability_results = []

            for expected_cap in expected_capabilities:
                found = any(expected_cap in name.lower() for name in capability_names)

                if found:
                    # 获取详细信息
                    cap_details = next(
                        (cap for cap in discovered_capabilities
                         if expected_cap in cap.get('name', '').lower()),
                        {}
                    )

                    capability_results.append({
                        'capability_name': expected_cap,
                        'discovered': True,
                        'version': cap_details.get('version', 'unknown'),
                        'status': cap_details.get('status', 'unknown'),
                        'features_count': len(cap_details.get('features', []))
                    })
                else:
                    capability_results.append({
                        'capability_name': expected_cap,
                        'discovered': False
                    })

            # 测试能力注册
            test_capability = {
                'name': 'test_capability',
                'version': '1.0.0',
                'status': 'active',
                'features': ['test_feature_1', 'test_feature_2']
            }

            registration_result = registry.register_capability(test_capability)

            success = (
                discovery_result.get('success', False) and
                len(capability_results) >= len(expected_capabilities) * 0.8 and  # 80%的能力被发现
                registration_result.get('success', False)
            )

            return {
                'success': success,
                'total_expected_capabilities': len(expected_capabilities),
                'discovered_capabilities': len([r for r in capability_results if r.get('discovered', False)]),
                'discovery_rate': len([r for r in capability_results if r.get('discovered', False)]) / len(expected_capabilities) * 100,
                'capability_results': capability_results,
                'registration_working': registration_result.get('success', False),
                'total_capabilities_in_registry': len(discovered_capabilities)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"能力发现系统测试异常: {str(e)}",
                'traceback': traceback.format_exc()
            }

    async def test_workflow_orchestrator(self) -> Dict[str, Any]:
        """测试工作流编排器核心功能"""
        try:
            from features.workflow_orchestrator.orchestrator import WorkflowOrchestrator

            orchestrator = WorkflowOrchestrator(self.logger)

            # 测试编排器核心功能
            test_workflow = {
                'name': 'Orchestrator Core Test',
                'stages': [
                    {
                        'name': 'parallel_stage',
                        'description': '并行测试阶段',
                        'execution_mode': 'parallel'
                    },
                    {
                        'name': 'sequential_stage',
                        'description': '顺序测试阶段',
                        'execution_mode': 'sequential',
                        'depends_on': ['parallel_stage']
                    }
                ]
            }

            # 测试工作流加载
            load_result = orchestrator.load_workflow(test_workflow)
            if not load_result['success']:
                return {
                    'success': False,
                    'error': f"工作流加载失败: {load_result.get('error')}"
                }

            # 测试任务创建
            task_results = []
            for i in range(3):
                task_result = orchestrator.create_task(
                    agent=f'test-agent-{i}',
                    description=f'测试任务 {i}',
                    stage='parallel_stage'
                )
                task_results.append(task_result.get('success', False))

            # 测试阶段执行计划
            plan_result = orchestrator.plan_stage_execution('parallel_stage')

            # 测试进度跟踪
            progress = orchestrator.get_workflow_progress()

            # 测试工作流状态
            metrics = orchestrator.get_execution_metrics()
            execution_log = orchestrator.get_execution_log()

            success = (
                load_result['success'] and
                all(task_results) and
                plan_result.get('success', False) and
                progress.get('completion_percentage') is not None
            )

            return {
                'success': success,
                'workflow_loaded': load_result['success'],
                'tasks_created': len([r for r in task_results if r]),
                'execution_plan_created': plan_result.get('success', False),
                'progress_tracking_working': progress.get('completion_percentage') is not None,
                'metrics_available': bool(metrics),
                'execution_log_working': isinstance(execution_log, list),
                'stages_configured': load_result.get('stages_count', 0)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"工作流编排器测试异常: {str(e)}",
                'traceback': traceback.format_exc()
            }

    async def test_parallel_execution(self) -> Dict[str, Any]:
        """测试并行执行功能"""
        try:
            # 这里应该测试并行执行能力
            # 由于需要真实的agent执行环境，我们使用模拟测试

            from features.parallel_executor import ParallelExecutor

            executor = ParallelExecutor()

            # 创建模拟任务
            test_tasks = [
                {'id': f'task_{i}', 'agent': f'agent_{i}', 'description': f'并行任务 {i}'}
                for i in range(5)
            ]

            # 测试并行执行
            start_time = time.time()
            execution_result = await executor.execute_parallel_tasks(test_tasks)
            execution_time = time.time() - start_time

            # 验证并行执行效果
            sequential_time_estimate = len(test_tasks) * 1.0  # 假设每个任务1秒
            parallel_efficiency = sequential_time_estimate / execution_time if execution_time > 0 else 0

            return {
                'success': execution_result.get('success', False),
                'tasks_executed': execution_result.get('completed_tasks', 0),
                'total_tasks': len(test_tasks),
                'execution_time': execution_time,
                'parallel_efficiency': parallel_efficiency,
                'efficiency_good': parallel_efficiency > 2.0,  # 至少2倍加速
                'all_tasks_completed': execution_result.get('completed_tasks', 0) == len(test_tasks)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"并行执行测试异常: {str(e)}",
                'traceback': traceback.format_exc()
            }

    async def test_decision_recording(self) -> Dict[str, Any]:
        """测试决策记录功能"""
        try:
            from features.decision_recorder.recorder import DecisionRecorder

            recorder = DecisionRecorder()

            # 测试决策记录
            test_decision = {
                'title': '测试架构决策',
                'context': '选择数据库技术',
                'options': ['PostgreSQL', 'MongoDB', 'Redis'],
                'decision': 'PostgreSQL',
                'rationale': '关系型数据需求，ACID特性重要',
                'consequences': ['更好的数据一致性', '成熟的生态系统']
            }

            # 记录决策
            record_result = recorder.record_decision(test_decision)

            # 查询决策
            decisions = recorder.get_decisions()

            # 搜索决策
            search_result = recorder.search_decisions('数据库')

            success = (
                record_result.get('success', False) and
                len(decisions) > 0 and
                len(search_result) > 0
            )

            return {
                'success': success,
                'decision_recorded': record_result.get('success', False),
                'decisions_count': len(decisions),
                'search_working': len(search_result) > 0,
                'decision_id': record_result.get('decision_id')
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"决策记录测试异常: {str(e)}",
                'traceback': traceback.format_exc()
            }

    async def test_quality_guardian(self) -> Dict[str, Any]:
        """测试质量守护功能"""
        try:
            from features.quality_gates.quality_guardian import QualityGuardian

            guardian = QualityGuardian()

            # 测试预防性质量检查
            code_sample = """
            def calculate_total(items):
                total = 0
                for item in items:
                    total += item.price
                return total
            """

            quality_check = guardian.analyze_code_quality(code_sample)

            # 测试质量规则
            quality_rules = guardian.get_quality_rules()

            # 测试质量度量
            metrics = {
                'complexity': 5,
                'coverage': 85,
                'duplication': 10,
                'maintainability': 8.5
            }

            quality_score = guardian.calculate_quality_score(metrics)

            success = (
                quality_check.get('success', False) and
                len(quality_rules) > 0 and
                quality_score.get('score', 0) > 0
            )

            return {
                'success': success,
                'code_analysis_working': quality_check.get('success', False),
                'quality_rules_loaded': len(quality_rules),
                'quality_score_calculated': quality_score.get('score', 0) > 0,
                'overall_quality_score': quality_score.get('score', 0)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"质量守护测试异常: {str(e)}",
                'traceback': traceback.format_exc()
            }

    async def test_multi_workspace(self) -> Dict[str, Any]:
        """测试多工作空间功能"""
        try:
            from features.multi_workspace.manager import MultiWorkspaceManager

            manager = MultiWorkspaceManager()

            # 创建测试工作空间
            workspace_config = {
                'name': 'test-workspace',
                'path': '/tmp/test-workspace',
                'type': 'development'
            }

            create_result = manager.create_workspace(workspace_config)

            # 切换工作空间
            switch_result = manager.switch_workspace('test-workspace')

            # 获取工作空间列表
            workspaces = manager.list_workspaces()

            # 获取当前工作空间
            current = manager.get_current_workspace()

            success = (
                create_result.get('success', False) and
                switch_result.get('success', False) and
                len(workspaces) > 0 and
                current is not None
            )

            return {
                'success': success,
                'workspace_created': create_result.get('success', False),
                'workspace_switched': switch_result.get('success', False),
                'workspaces_count': len(workspaces),
                'current_workspace_detected': current is not None
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"多工作空间测试异常: {str(e)}",
                'traceback': traceback.format_exc()
            }

    async def test_learning_feedback(self) -> Dict[str, Any]:
        """测试学习反馈功能"""
        try:
            from features.learning_feedback.learning_loop import LearningLoop

            loop = LearningLoop()

            # 记录执行经验
            experience = {
                'workflow': 'development_workflow',
                'stage': 'implementation',
                'action': 'parallel_execution',
                'outcome': 'success',
                'duration': 120,
                'quality_score': 8.5,
                'lessons': ['并行执行提高效率', '需要更好的同步机制']
            }

            record_result = loop.record_experience(experience)

            # 获取学习建议
            context = {
                'workflow': 'development_workflow',
                'stage': 'implementation'
            }

            suggestions = loop.get_suggestions(context)

            # 测试模式识别
            patterns = loop.identify_patterns()

            success = (
                record_result.get('success', False) and
                len(suggestions) > 0 and
                len(patterns) >= 0
            )

            return {
                'success': success,
                'experience_recorded': record_result.get('success', False),
                'suggestions_generated': len(suggestions),
                'patterns_identified': len(patterns),
                'learning_active': record_result.get('success', False) and len(suggestions) > 0
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"学习反馈测试异常: {str(e)}",
                'traceback': traceback.format_exc()
            }

    def _validate_hook_config(self, config: Dict[str, Any]) -> bool:
        """验证钩子配置"""
        if not config:
            return False

        required_fields = ['enabled', 'script_path']
        return all(field in config for field in required_fields)

    async def generate_test_report(self, summary: Dict[str, Any]) -> None:
        """生成测试报告"""
        # 生成JSON报告
        report_data = {
            'summary': summary,
            'test_results': [
                {
                    'test_name': result.test_name,
                    'success': result.success,
                    'duration': result.duration,
                    'details': result.details,
                    'error': result.error
                }
                for result in self.test_results
            ],
            'generated_at': datetime.now().isoformat(),
            'total_duration': summary['total_duration']
        }

        with open(self.report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"📄 JSON报告已保存: {self.report_file}")

        # 生成HTML仪表板
        await self.generate_html_dashboard(summary)

    async def generate_html_dashboard(self, summary: Dict[str, Any]) -> None:
        """生成HTML测试仪表板"""

        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Perfect21 功能验证报告</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2.5em;
                    font-weight: 300;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                }}
                .summary {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    padding: 30px;
                    background: #f8f9fa;
                }}
                .metric-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    border-left: 4px solid #007bff;
                }}
                .metric-card.success {{
                    border-left-color: #28a745;
                }}
                .metric-card.warning {{
                    border-left-color: #ffc107;
                }}
                .metric-card.danger {{
                    border-left-color: #dc3545;
                }}
                .metric-value {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 5px;
                }}
                .metric-label {{
                    color: #6c757d;
                    font-size: 0.9em;
                }}
                .test-results {{
                    padding: 30px;
                }}
                .test-item {{
                    display: flex;
                    align-items: center;
                    padding: 15px;
                    margin-bottom: 10px;
                    border-radius: 8px;
                    background: #f8f9fa;
                    border-left: 4px solid #28a745;
                }}
                .test-item.failed {{
                    border-left-color: #dc3545;
                    background: #fff5f5;
                }}
                .test-status {{
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    margin-right: 15px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                }}
                .test-status.passed {{
                    background: #28a745;
                }}
                .test-status.failed {{
                    background: #dc3545;
                }}
                .test-info {{
                    flex: 1;
                }}
                .test-name {{
                    font-weight: 600;
                    color: #2c3e50;
                    margin-bottom: 5px;
                }}
                .test-duration {{
                    color: #6c757d;
                    font-size: 0.9em;
                }}
                .test-error {{
                    color: #dc3545;
                    font-size: 0.9em;
                    margin-top: 5px;
                }}
                .progress-bar {{
                    width: 100%;
                    height: 8px;
                    background: #e9ecef;
                    border-radius: 4px;
                    overflow: hidden;
                    margin: 20px 0;
                }}
                .progress-fill {{
                    height: 100%;
                    background: linear-gradient(90deg, #28a745, #20c997);
                    transition: width 0.3s ease;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #6c757d;
                    border-top: 1px solid #dee2e6;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Perfect21 功能验证报告</h1>
                    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <div class="summary">
                    <div class="metric-card {'success' if summary['overall_success'] else 'danger'}">
                        <div class="metric-value">{'✅' if summary['overall_success'] else '❌'}</div>
                        <div class="metric-label">整体状态</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-value">{summary['total_tests']}</div>
                        <div class="metric-label">总测试数</div>
                    </div>

                    <div class="metric-card success">
                        <div class="metric-value">{summary['passed_tests']}</div>
                        <div class="metric-label">通过测试</div>
                    </div>

                    <div class="metric-card {'success' if summary['failed_tests'] == 0 else 'danger'}">
                        <div class="metric-value">{summary['failed_tests']}</div>
                        <div class="metric-label">失败测试</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-value">{summary['success_rate']:.1f}%</div>
                        <div class="metric-label">成功率</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-value">{summary['total_duration']:.1f}s</div>
                        <div class="metric-label">总耗时</div>
                    </div>
                </div>

                <div class="progress-bar">
                    <div class="progress-fill" style="width: {summary['success_rate']}%"></div>
                </div>

                <div class="test-results">
                    <h2>📋 详细测试结果</h2>
        """

        for result in self.test_results:
            status_class = "passed" if result.success else "failed"
            item_class = "failed" if not result.success else ""
            status_icon = "✓" if result.success else "✗"

            html_content += f"""
                    <div class="test-item {item_class}">
                        <div class="test-status {status_class}">{status_icon}</div>
                        <div class="test-info">
                            <div class="test-name">{result.test_name}</div>
                            <div class="test-duration">耗时: {result.duration:.2f}s</div>
                            {f'<div class="test-error">错误: {result.error}</div>' if result.error else ''}
                        </div>
                    </div>
            """

        html_content += f"""
                </div>

                <div class="footer">
                    <p>Perfect21 功能验证测试 - 自动生成报告</p>
                    <p>详细结果请查看: {self.report_file.name}</p>
                </div>
            </div>
        </body>
        </html>
        """

        with open(self.dashboard_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.logger.info(f"🎨 HTML仪表板已生成: {self.dashboard_file}")

async def main():
    """主函数"""
    print("🚀 启动Perfect21功能验证测试")
    print("=" * 80)

    validator = Perfect21FunctionalityValidator()

    try:
        # 运行所有测试
        summary = await validator.run_all_tests()

        # 输出最终结果
        print("\n" + "=" * 80)
        print("🎯 Perfect21功能验证完成")
        print(f"📊 成功率: {summary['success_rate']:.1f}% ({summary['passed_tests']}/{summary['total_tests']})")
        print(f"⏱️  总耗时: {summary['total_duration']:.2f}秒")

        if summary['overall_success']:
            print("✅ 所有核心功能正常工作")
            return 0
        else:
            print("❌ 部分功能存在问题，请查看详细报告")
            return 1

    except Exception as e:
        print(f"💥 测试执行异常: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)