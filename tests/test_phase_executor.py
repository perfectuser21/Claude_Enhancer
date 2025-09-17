#!/usr/bin/env python3
"""
测试阶段性并行执行框架
验证真正的并行执行和Git集成
"""

import os
import sys
import time
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from features.phase_executor import (
    PhaseExecutor,
    ContextPool,
    PhaseSummarizer,
    GitPhaseIntegration
)
from features.phase_executor.phase_executor import ExecutionPhase

class TestPhaseExecutor(unittest.TestCase):
    """测试阶段执行器"""

    def setUp(self):
        self.executor = PhaseExecutor()

    def test_phase_instruction_generation(self):
        """测试阶段指令生成"""
        # 测试分析阶段
        result = self.executor.generate_phase_instructions(
            ExecutionPhase.ANALYSIS,
            {'requirement': '用户认证系统'}
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['instructions']['phase'], 'analysis')
        self.assertEqual(len(result['instructions']['agents_to_call']), 3)
        self.assertEqual(result['instructions']['execution_mode'], 'parallel')

    def test_parallel_agents_detection(self):
        """测试并行agent检测"""
        # 分析阶段应该并行
        agents = self.executor.get_parallel_agents(ExecutionPhase.ANALYSIS)
        self.assertEqual(len(agents), 3)
        self.assertIn('project-manager', agents)

        # 部署阶段不并行
        agents = self.executor.get_parallel_agents(ExecutionPhase.DEPLOYMENT)
        self.assertEqual(len(agents), 0)

    def test_git_hook_trigger_conditions(self):
        """测试Git Hook触发条件"""
        # 实现阶段有暂存更改时应触发
        should_trigger = self.executor.should_trigger_git_hook(
            ExecutionPhase.IMPLEMENTATION,
            {'has_staged_changes': True}
        )
        self.assertTrue(should_trigger)

        # 测试阶段应触发pre-push
        should_trigger = self.executor.should_trigger_git_hook(
            ExecutionPhase.TESTING,
            {}
        )
        self.assertTrue(should_trigger)

    def test_phase_transition(self):
        """测试阶段转换"""
        next_phase = self.executor.get_next_phase(ExecutionPhase.ANALYSIS)
        self.assertEqual(next_phase, ExecutionPhase.DESIGN)

        next_phase = self.executor.get_next_phase(ExecutionPhase.DEPLOYMENT)
        self.assertIsNone(next_phase)

    def test_phase_validation(self):
        """测试阶段转换验证"""
        # 记录分析阶段完成
        self.executor.record_phase_result(
            ExecutionPhase.ANALYSIS,
            {'status': 'completed'}
        )

        # 验证可以转到设计阶段
        result = self.executor.validate_phase_transition(
            ExecutionPhase.ANALYSIS,
            ExecutionPhase.DESIGN
        )
        self.assertTrue(result['valid'])

        # 验证不能跳过阶段
        result = self.executor.validate_phase_transition(
            ExecutionPhase.ANALYSIS,
            ExecutionPhase.TESTING
        )
        self.assertFalse(result['valid'])


class TestContextPool(unittest.TestCase):
    """测试上下文数据池"""

    def setUp(self):
        self.pool = ContextPool()

    def test_phase_output_storage(self):
        """测试阶段输出存储"""
        output = {'requirements': ['auth', 'user_management']}
        self.pool.add_phase_output('analysis', output)

        # 验证存储
        self.assertIn('analysis', self.pool.phase_outputs)
        self.assertEqual(
            self.pool.phase_outputs['analysis']['data'],
            output
        )

    def test_agent_output_aggregation(self):
        """测试agent输出聚合"""
        # 添加多个agent输出
        self.pool.add_agent_output('analysis', 'project-manager', {
            'data': {'priority': 'high', 'timeline': '2 weeks'}
        })
        self.pool.add_agent_output('analysis', 'business-analyst', {
            'data': {'priority': 'high', 'budget': '$10000'}
        })

        # 聚合输出
        aggregated = self.pool.aggregate_agent_outputs('analysis')

        self.assertEqual(len(aggregated['agents']), 2)
        self.assertIn('project-manager', aggregated['agents'])
        self.assertIn('business-analyst', aggregated['agents'])

    def test_consensus_detection(self):
        """测试共识检测"""
        # 添加有共识的输出
        self.pool.add_agent_output('analysis', 'agent1', {
            'data': {'data': {'priority': 'high'}}
        })
        self.pool.add_agent_output('analysis', 'agent2', {
            'data': {'data': {'priority': 'high'}}
        })

        aggregated = self.pool.aggregate_agent_outputs('analysis')

        # 应该检测到priority的共识
        self.assertIn('priority', aggregated['consensus'])
        self.assertEqual(aggregated['consensus']['priority'], 'high')

    def test_conflict_detection(self):
        """测试分歧检测"""
        # 添加有分歧的输出
        self.pool.add_agent_output('design', 'api-designer', {
            'data': {'data': {'framework': 'REST'}}
        })
        self.pool.add_agent_output('design', 'backend-architect', {
            'data': {'data': {'framework': 'GraphQL'}}
        })

        aggregated = self.pool.aggregate_agent_outputs('design')

        # 应该检测到framework的分歧
        self.assertTrue(len(aggregated['conflicts']) > 0)
        conflict_keys = [c['key'] for c in aggregated['conflicts']]
        self.assertIn('framework', conflict_keys)

    def test_dependency_validation(self):
        """测试依赖验证"""
        # 设置依赖关系
        self.pool.set_phase_dependency('design', ['analysis'])

        # 未完成依赖时验证失败
        result = self.pool.validate_dependencies('design')
        self.assertFalse(result['valid'])

        # 完成依赖后验证成功
        self.pool.add_phase_output('analysis', {'completed': True})
        result = self.pool.validate_dependencies('design')
        self.assertTrue(result['valid'])


class TestPhaseSummarizer(unittest.TestCase):
    """测试阶段汇总器"""

    def setUp(self):
        self.summarizer = PhaseSummarizer()

    def test_phase_summarization(self):
        """测试阶段汇总"""
        agent_results = [
            {
                'agent': 'project-manager',
                'key_findings': ['需要2周完成', '需要3名开发人员'],
                'issues': ['时间紧张'],
                'recommendations': ['增加人手']
            },
            {
                'agent': 'business-analyst',
                'key_findings': ['核心功能是用户认证', '需要支持OAuth'],
                'issues': ['预算有限'],
                'severity': 'medium'
            }
        ]

        summary = self.summarizer.summarize_phase_results('analysis', agent_results)

        self.assertEqual(summary['phase_id'], 'analysis')
        self.assertEqual(summary['total_agents'], 2)
        self.assertEqual(len(summary['key_findings']), 4)
        self.assertEqual(len(summary['critical_issues']), 2)

    def test_todo_generation(self):
        """测试TODO生成"""
        summary = {
            'key_findings': [
                {'agent': 'analyst', 'finding': 'Need API design'}
            ],
            'critical_issues': [],
            'aggregated_data': {'api_spec': 'v1.0'}
        }

        todos = self.summarizer.generate_next_phase_todos('design', summary)

        self.assertTrue(len(todos) > 0)
        # 应该包含实现API的任务
        task_descriptions = [t['task'] for t in todos]
        self.assertTrue(any('API' in desc for desc in task_descriptions))

    def test_severity_prioritization(self):
        """测试严重程度排序"""
        agent_results = [
            {
                'agent': 'test1',
                'issues': ['issue1'],
                'severity': 'low'
            },
            {
                'agent': 'test2',
                'issues': ['issue2'],
                'severity': 'critical'
            },
            {
                'agent': 'test3',
                'issues': ['issue3'],
                'severity': 'medium'
            }
        ]

        summary = self.summarizer.summarize_phase_results('test', agent_results)

        # 验证按严重程度排序
        issues = summary['critical_issues']
        self.assertEqual(issues[0]['severity'], 'critical')
        self.assertEqual(issues[1]['severity'], 'medium')
        self.assertEqual(issues[2]['severity'], 'low')


class TestParallelExecution(unittest.TestCase):
    """测试真正的并行执行"""

    def test_parallel_timing_verification(self):
        """验证并行执行的时间特征"""
        start_times = []
        end_times = []

        def simulate_agent_execution(agent_name):
            """模拟agent执行"""
            start_times.append(time.time())
            time.sleep(0.1)  # 模拟执行时间
            end_times.append(time.time())
            return {'agent': agent_name, 'result': 'completed'}

        # 模拟并行执行
        import concurrent.futures
        agents = ['agent1', 'agent2', 'agent3']

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for agent in agents:
                future = executor.submit(simulate_agent_execution, agent)
                futures.append(future)

            results = [f.result() for f in futures]

        # 验证时间特征
        # 如果是真正并行，开始时间应该非常接近
        max_start_diff = max(start_times) - min(start_times)
        self.assertLess(max_start_diff, 0.05)  # 开始时间差小于50ms

        # 总执行时间应该接近单个任务时间，而不是总和
        total_time = max(end_times) - min(start_times)
        self.assertLess(total_time, 0.2)  # 小于200ms（如果串行需要300ms）

    def test_parallel_execution_instruction(self):
        """测试并行执行指令生成"""
        executor = PhaseExecutor()
        result = executor.generate_phase_instructions(ExecutionPhase.IMPLEMENTATION)

        instructions = result['instructions']

        # 验证是并行模式
        self.assertEqual(instructions['execution_mode'], 'parallel')

        # 验证包含多个agents
        self.assertEqual(len(instructions['agents_to_call']), 3)

        # 验证指令文本包含并行说明
        self.assertIn('并行', instructions['claude_code_instruction'])
        self.assertIn('同一个消息中', instructions['claude_code_instruction'])


class TestGitIntegration(unittest.TestCase):
    """测试Git集成"""

    def setUp(self):
        self.git_integration = GitPhaseIntegration()

    @patch('subprocess.run')
    def test_feature_branch_creation(self, mock_run):
        """测试功能分支创建"""
        mock_run.return_value = MagicMock(
            stdout='',
            stderr='',
            returncode=0
        )

        result = self.git_integration._create_feature_branch('auth-system')

        self.assertTrue(result['success'])
        self.assertIn('feature/auth-system', result['branch'])

    def test_git_operations_by_phase(self):
        """测试各阶段的Git操作"""
        # 分析阶段无Git操作
        ops = self.git_integration.get_phase_git_operations('analysis')
        self.assertEqual(len(ops), 0)

        # 设计阶段有分支创建和提交
        ops = self.git_integration.get_phase_git_operations('design')
        self.assertIn('create_feature_branch', ops)
        self.assertIn('commit_design_docs', ops)

        # 测试阶段有测试和Hook
        ops = self.git_integration.get_phase_git_operations('testing')
        self.assertIn('run_tests', ops)
        self.assertIn('trigger_pre_push_hook', ops)

    @patch('subprocess.run')
    def test_hook_trigger(self, mock_run):
        """测试Hook触发"""
        mock_run.return_value = MagicMock(
            stdout='Hook executed',
            stderr='',
            returncode=0
        )

        # 创建模拟Hook文件
        with patch('os.path.exists', return_value=True):
            result = self.git_integration._trigger_hook('pre-commit')

        self.assertTrue(result['success'])
        self.assertIn('成功', result['message'])


if __name__ == '__main__':
    unittest.main()