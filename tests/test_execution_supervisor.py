#!/usr/bin/env python3
"""
测试执行监督系统
验证监督、守护、提醒和监控功能
"""

import os
import sys
import time
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from features.execution_supervisor import (
    ExecutionSupervisor,
    WorkflowGuardian,
    SmartReminder,
    ExecutionMonitor
)
from features.execution_supervisor.supervisor import ExecutionMode
from features.execution_supervisor.guardian import QualityLevel

class TestExecutionSupervisor(unittest.TestCase):
    """测试执行监督器"""

    def setUp(self):
        self.supervisor = ExecutionSupervisor()

    def test_before_phase_reminder(self):
        """测试阶段前提醒"""
        reminder = self.supervisor.before_phase('analysis')

        # 验证提醒包含关键信息
        self.assertIn('analysis', reminder.lower())
        self.assertIn('并行', reminder)
        self.assertIn('agents', reminder.lower())
        self.assertIn('Task', reminder)

    def test_execution_plan_check(self):
        """测试执行计划检查"""
        # 测试符合要求的计划
        good_plan = ['agent1', 'agent2', 'agent3']
        result = self.supervisor.check_execution_plan('analysis', good_plan)
        self.assertTrue(result['approved'])
        self.assertEqual(result['execution_mode'], ExecutionMode.PARALLEL)

        # 测试不符合要求的计划
        bad_plan = ['agent1']
        result = self.supervisor.check_execution_plan('analysis', bad_plan)
        self.assertFalse(result['approved'])
        self.assertIn('warning', result)

    def test_degradation_detection(self):
        """测试退化检测"""
        # 记录并行执行
        self.supervisor.record_execution('analysis', {
            'agent_count': 3,
            'is_parallel': True,
            'success': True
        })

        # 检测退化到串行
        warning = self.supervisor.detect_degradation('design', {
            'agent_count': 1,
            'is_parallel': False
        })

        self.assertIsNotNone(warning)
        self.assertIn('退化', warning)

    def test_execution_stats(self):
        """测试执行统计"""
        # 记录多个执行
        self.supervisor.record_execution('phase1', {'agent_count': 3, 'is_parallel': True})
        self.supervisor.record_execution('phase2', {'agent_count': 1, 'is_parallel': False})
        self.supervisor.record_execution('phase3', {'agent_count': 2, 'is_parallel': True})

        report = self.supervisor.get_execution_report()

        self.assertEqual(report['statistics']['total_phases'], 3)
        self.assertEqual(report['statistics']['parallel_phases'], 2)
        self.assertEqual(report['statistics']['sequential_phases'], 1)
        self.assertGreater(report['parallel_rate'], 60)


class TestWorkflowGuardian(unittest.TestCase):
    """测试工作流守护者"""

    def setUp(self):
        self.guardian = WorkflowGuardian()

    def test_checklist_generation(self):
        """测试检查清单生成"""
        checklist = self.guardian.generate_execution_checklist('analysis')

        # 验证包含必要的检查项
        check_ids = [item['id'] for item in checklist]
        self.assertIn('parallel_agents', check_ids)
        self.assertIn('wait_completion', check_ids)
        self.assertIn('sync_point', check_ids)
        self.assertIn('result_summary', check_ids)

    def test_execution_validation(self):
        """测试执行验证"""
        # 好的执行
        good_execution = {
            'agent_count': 3,
            'sync_point_executed': True,
            'summary_generated': True,
            'todos_generated': True,
            'sequential_operations': 2,
            'total_operations': 10,
            'parallel_operations': 8
        }

        result = self.guardian.validate_execution('analysis', good_execution)
        self.assertTrue(result['valid'])
        self.assertIn(result['quality_level'], [QualityLevel.EXCELLENT, QualityLevel.GOOD])

        # 差的执行
        bad_execution = {
            'agent_count': 1,
            'sync_point_executed': False,
            'summary_generated': False,
            'sequential_operations': 10,
            'total_operations': 10,
            'parallel_operations': 0
        }

        result = self.guardian.validate_execution('analysis', bad_execution)
        self.assertFalse(result['valid'])
        self.assertTrue(len(result['violations']) > 0)

    def test_quality_gate_enforcement(self):
        """测试质量门强制"""
        # 高质量通过
        high_quality = {
            'quality_level': QualityLevel.EXCELLENT,
            'violations': []
        }
        gate = self.guardian.enforce_quality_gate('analysis', high_quality)
        self.assertEqual(gate['gate_result'], 'PASSED')

        # 低质量失败
        low_quality = {
            'quality_level': QualityLevel.FAILED,
            'violations': ['并行agent数量不足', '未执行同步点']
        }
        gate = self.guardian.enforce_quality_gate('analysis', low_quality)
        self.assertEqual(gate['gate_result'], 'FAILED')
        self.assertIn('retry_guidance', gate)


class TestSmartReminder(unittest.TestCase):
    """测试智能提醒系统"""

    def setUp(self):
        self.reminder = SmartReminder()

    def test_phase_reminder_generation(self):
        """测试阶段提醒生成"""
        context = {
            'task_complexity': 'high',
            'quality_requirement': 'high'
        }

        reminder = self.reminder.get_phase_reminder('analysis', context)

        # 验证包含个性化内容
        self.assertIn('analysis', reminder.lower())
        self.assertIn('建议', reminder)
        self.assertIn('智能提示', reminder)

    def test_learning_from_execution(self):
        """测试从执行中学习"""
        # 记录成功的并行执行
        success_result = {
            'agent_count': 3,
            'is_parallel': True,
            'success': True,
            'sync_point_executed': True,
            'summary_generated': True
        }

        self.reminder.learn_from_execution('analysis', success_result)

        # 验证学习了成功模式
        self.assertEqual(len(self.reminder.success_patterns), 1)
        self.assertEqual(self.reminder.success_patterns[0]['phase'], 'analysis')

        # 记录失败的串行执行
        failure_result = {
            'agent_count': 1,
            'is_parallel': False,
            'success': False
        }

        self.reminder.learn_from_execution('design', failure_result)

        # 验证学习了失败模式
        self.assertEqual(len(self.reminder.failure_patterns), 1)

    def test_contextual_tips(self):
        """测试情境化提示"""
        tip = self.reminder.get_contextual_tip('analysis', 'first_phase')
        self.assertIn('第一个阶段', tip)

        tip = self.reminder.get_contextual_tip('testing', 'after_success')
        self.assertIn('成功', tip)

    def test_motivation_generation(self):
        """测试激励信息生成"""
        # 高并行率
        high_stats = {'parallel_rate': 85}
        motivation = self.reminder.generate_motivation(high_stats)
        self.assertIn('优秀', motivation)

        # 低并行率
        low_stats = {'parallel_rate': 30}
        motivation = self.reminder.generate_motivation(low_stats)
        self.assertIn('需要改进', motivation)


class TestExecutionMonitor(unittest.TestCase):
    """测试执行监控器"""

    def setUp(self):
        self.monitor = ExecutionMonitor()

    def test_phase_monitoring(self):
        """测试阶段监控"""
        # 开始监控
        self.monitor.start_phase_monitoring('analysis')
        self.assertTrue(self.monitor.monitoring_active)
        self.assertEqual(self.monitor.current_phase, 'analysis')

        # 记录agent调用
        self.monitor.record_agent_call('project-manager', is_parallel=True)
        self.monitor.record_agent_call('business-analyst', is_parallel=True)

        # 记录同步点
        self.monitor.record_sync_point('requirement_consensus', duration=5.0)

        # 结束监控
        report = self.monitor.end_phase_monitoring('analysis', success=True)

        self.assertFalse(self.monitor.monitoring_active)
        self.assertEqual(report['phase'], 'analysis')
        self.assertEqual(report['agent_summary']['total'], 2)
        self.assertEqual(report['agent_summary']['parallel'], 2)

    def test_real_time_status(self):
        """测试实时状态"""
        # 未监控时
        status = self.monitor.get_real_time_status()
        self.assertFalse(status['monitoring'])

        # 监控中
        self.monitor.start_phase_monitoring('design')
        self.monitor.record_agent_call('api-designer')

        status = self.monitor.get_real_time_status()
        self.assertTrue(status['monitoring'])
        self.assertEqual(status['current_phase'], 'design')
        self.assertEqual(status['agent_count'], 1)

    def test_quality_score_calculation(self):
        """测试质量分数计算"""
        # 高质量执行
        good_metrics = {
            'parallel_rate': 0.9,
            'agent_count': 3,
            'execution_time': 50,
            'success_rate': 1.0
        }

        score = self.monitor._calculate_quality_score(good_metrics)
        self.assertGreater(score, 80)

        # 低质量执行
        bad_metrics = {
            'parallel_rate': 0.2,
            'agent_count': 1,
            'execution_time': 300,
            'success_rate': 0.5
        }

        score = self.monitor._calculate_quality_score(bad_metrics)
        self.assertLess(score, 50)

    def test_alert_generation(self):
        """测试警报生成"""
        self.monitor.start_phase_monitoring('implementation')

        # 记录串行调用触发警报
        self.monitor.record_agent_call('backend-architect', is_parallel=False)

        # 验证生成了警报
        self.assertEqual(len(self.monitor.alerts), 1)
        self.assertEqual(self.monitor.alerts[0]['type'], 'SEQUENTIAL_CALL')

        # 记录慢同步点触发警报
        self.monitor.record_sync_point('code_review', duration=60)

        self.assertEqual(len(self.monitor.alerts), 2)
        self.assertEqual(self.monitor.alerts[1]['type'], 'SLOW_SYNC_POINT')


class TestIntegration(unittest.TestCase):
    """测试集成功能"""

    def test_supervisor_system_integration(self):
        """测试监督系统集成"""
        # 创建所有组件
        supervisor = ExecutionSupervisor()
        guardian = WorkflowGuardian()
        reminder = SmartReminder()
        monitor = ExecutionMonitor()

        # 模拟完整的阶段执行流程
        phase = 'analysis'

        # 1. 获取提醒
        reminder_msg = supervisor.before_phase(phase)
        self.assertIsNotNone(reminder_msg)

        # 2. 生成检查清单
        checklist = guardian.generate_execution_checklist(phase)
        self.assertTrue(len(checklist) > 0)

        # 3. 开始监控
        monitor.start_phase_monitoring(phase)

        # 4. 模拟执行
        agents = ['project-manager', 'business-analyst', 'technical-writer']
        for agent in agents:
            monitor.record_agent_call(agent, is_parallel=True)

        # 5. 执行结果
        execution_result = {
            'agent_count': 3,
            'is_parallel': True,
            'sync_point_executed': True,
            'summary_generated': True,
            'success': True,
            'total_operations': 10,
            'parallel_operations': 8
        }

        # 6. 验证执行
        validation = guardian.validate_execution(phase, execution_result)
        self.assertTrue(validation['valid'])

        # 7. 学习模式
        reminder.learn_from_execution(phase, execution_result)

        # 8. 结束监控
        report = monitor.end_phase_monitoring(phase, success=True)
        self.assertIn('quality_score', report)

        # 9. 获取报告
        exec_report = supervisor.get_execution_report()
        self.assertEqual(exec_report['statistics']['total_phases'], 0)  # 还未记录

        guardian_report = guardian.get_guardian_report()
        self.assertIn('total_checks', guardian_report)


if __name__ == '__main__':
    unittest.main()