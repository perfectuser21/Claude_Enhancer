#!/usr/bin/env python3
"""
Comprehensive integration tests for workflow orchestration
Target: High coverage for workflow execution and coordination
"""

import pytest
import asyncio
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from features.workflow_orchestrator.orchestrator import WorkflowOrchestrator
from features.sync_point_manager.manager import SyncPointManager
from features.decision_recorder.recorder import DecisionRecorder


class TestWorkflowOrchestrator:
    """Test WorkflowOrchestrator integration"""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create WorkflowOrchestrator for testing"""
        config = {
            'workspace_path': str(tmp_path),
            'max_parallel_tasks': 5,
            'timeout': 300,
            'quality_gates_enabled': True
        }
        return WorkflowOrchestrator(config)

    @pytest.fixture
    def mock_agents(self):
        """Mock agent implementations"""
        agents = {}
        agent_names = [
            'project-manager', 'business-analyst', 'technical-writer',
            'api-designer', 'backend-architect', 'database-specialist',
            'frontend-specialist', 'test-engineer', 'security-auditor'
        ]

        for name in agent_names:
            mock_agent = MagicMock()
            mock_agent.execute = MagicMock(return_value={
                'success': True,
                'output': f'Mock output from {name}',
                'execution_time': 1.0,
                'quality_score': 0.95
            })
            agents[name] = mock_agent

        return agents

    def test_simple_workflow_execution(self, orchestrator, mock_agents):
        """Test simple sequential workflow execution"""
        with patch.object(orchestrator, '_get_agent') as mock_get_agent:
            mock_get_agent.side_effect = lambda name: mock_agents[name]

            workflow_definition = {
                'name': 'simple_workflow',
                'stages': [
                    {
                        'name': 'analysis',
                        'agents': ['business-analyst'],
                        'execution_mode': 'sequential'
                    },
                    {
                        'name': 'design',
                        'agents': ['api-designer'],
                        'execution_mode': 'sequential'
                    }
                ]
            }

            result = orchestrator.execute_workflow(
                workflow_definition,
                task_description="Test simple workflow"
            )

            assert result['success'] is True
            assert len(result['stage_results']) == 2
            assert result['stage_results'][0]['stage'] == 'analysis'
            assert result['stage_results'][1]['stage'] == 'design'

    def test_parallel_workflow_execution(self, orchestrator, mock_agents):
        """Test parallel workflow execution"""
        with patch.object(orchestrator, '_get_agent') as mock_get_agent:
            mock_get_agent.side_effect = lambda name: mock_agents[name]

            workflow_definition = {
                'name': 'parallel_workflow',
                'stages': [
                    {
                        'name': 'parallel_analysis',
                        'agents': ['business-analyst', 'technical-writer', 'project-manager'],
                        'execution_mode': 'parallel'
                    }
                ]
            }

            start_time = time.time()
            result = orchestrator.execute_workflow(
                workflow_definition,
                task_description="Test parallel workflow"
            )
            execution_time = time.time() - start_time

            assert result['success'] is True
            assert len(result['stage_results']) == 1
            stage_result = result['stage_results'][0]
            assert len(stage_result['agent_results']) == 3

            # Parallel execution should be faster than sequential
            assert execution_time < 2.0  # Should complete in reasonable time

    def test_workflow_with_sync_points(self, orchestrator, mock_agents):
        """Test workflow with synchronization points"""
        with patch.object(orchestrator, '_get_agent') as mock_get_agent:
            mock_get_agent.side_effect = lambda name: mock_agents[name]

            workflow_definition = {
                'name': 'sync_workflow',
                'stages': [
                    {
                        'name': 'initial_analysis',
                        'agents': ['business-analyst', 'project-manager'],
                        'execution_mode': 'parallel'
                    },
                    {
                        'name': 'sync_point_1',
                        'type': 'sync_point',
                        'validation_type': 'consensus_check',
                        'required_consensus': 0.8
                    },
                    {
                        'name': 'design_phase',
                        'agents': ['api-designer', 'backend-architect'],
                        'execution_mode': 'parallel'
                    }
                ]
            }

            result = orchestrator.execute_workflow(
                workflow_definition,
                task_description="Test workflow with sync points"
            )

            assert result['success'] is True
            assert len(result['stage_results']) == 3
            # Check that sync point was processed
            sync_result = result['stage_results'][1]
            assert sync_result['stage'] == 'sync_point_1'
            assert 'validation_result' in sync_result

    def test_workflow_with_quality_gates(self, orchestrator, mock_agents):
        """Test workflow with quality gates"""
        with patch.object(orchestrator, '_get_agent') as mock_get_agent:
            mock_get_agent.side_effect = lambda name: mock_agents[name]

            workflow_definition = {
                'name': 'quality_workflow',
                'quality_gates': {
                    'enabled': True,
                    'min_quality_score': 0.9,
                    'coverage_threshold': 0.85
                },
                'stages': [
                    {
                        'name': 'implementation',
                        'agents': ['backend-architect'],
                        'execution_mode': 'sequential'
                    },
                    {
                        'name': 'quality_gate',
                        'type': 'quality_gate',
                        'checks': ['code_quality', 'test_coverage', 'security_scan']
                    },
                    {
                        'name': 'testing',
                        'agents': ['test-engineer'],
                        'execution_mode': 'sequential'
                    }
                ]
            }

            result = orchestrator.execute_workflow(
                workflow_definition,
                task_description="Test workflow with quality gates"
            )

            assert result['success'] is True
            # Check quality gate execution
            quality_gate_result = result['stage_results'][1]
            assert quality_gate_result['stage'] == 'quality_gate'
            assert 'quality_checks' in quality_gate_result

    def test_workflow_error_handling(self, orchestrator, mock_agents):
        """Test workflow error handling and recovery"""
        # Set up one agent to fail
        mock_agents['api-designer'].execute.return_value = {
            'success': False,
            'error': 'Mock failure in API design',
            'execution_time': 0.5
        }

        with patch.object(orchestrator, '_get_agent') as mock_get_agent:
            mock_get_agent.side_effect = lambda name: mock_agents[name]

            workflow_definition = {
                'name': 'error_workflow',
                'error_handling': {
                    'retry_attempts': 2,
                    'timeout': 30,
                    'continue_on_failure': True
                },
                'stages': [
                    {
                        'name': 'analysis',
                        'agents': ['business-analyst'],
                        'execution_mode': 'sequential'
                    },
                    {
                        'name': 'failing_design',
                        'agents': ['api-designer'],
                        'execution_mode': 'sequential'
                    },
                    {
                        'name': 'recovery',
                        'agents': ['backend-architect'],
                        'execution_mode': 'sequential'
                    }
                ]
            }

            result = orchestrator.execute_workflow(
                workflow_definition,
                task_description="Test error handling workflow"
            )

            # Workflow should complete despite failure
            assert result['success'] is True  # continue_on_failure = True
            assert len(result['stage_results']) == 3
            assert result['stage_results'][1]['success'] is False
            assert result['stage_results'][2]['success'] is True

    def test_workflow_timeout_handling(self, orchestrator, mock_agents):
        """Test workflow timeout handling"""
        # Set up agent with long execution time
        def slow_execute(*args, **kwargs):
            time.sleep(2)  # Simulate slow operation
            return {
                'success': True,
                'output': 'Slow operation completed',
                'execution_time': 2.0
            }

        mock_agents['backend-architect'].execute = slow_execute

        with patch.object(orchestrator, '_get_agent') as mock_get_agent:
            mock_get_agent.side_effect = lambda name: mock_agents[name]

            workflow_definition = {
                'name': 'timeout_workflow',
                'timeout': 1,  # Very short timeout
                'stages': [
                    {
                        'name': 'slow_stage',
                        'agents': ['backend-architect'],
                        'execution_mode': 'sequential'
                    }
                ]
            }

            result = orchestrator.execute_workflow(
                workflow_definition,
                task_description="Test timeout workflow"
            )

            # Should fail due to timeout
            assert result['success'] is False
            assert 'timeout' in result.get('error', '').lower()

    def test_complex_multi_stage_workflow(self, orchestrator, mock_agents):
        """Test complex multi-stage workflow"""
        with patch.object(orchestrator, '_get_agent') as mock_get_agent:
            mock_get_agent.side_effect = lambda name: mock_agents[name]

            workflow_definition = {
                'name': 'complex_workflow',
                'stages': [
                    {
                        'name': 'deep_understanding',
                        'agents': ['project-manager', 'business-analyst', 'technical-writer'],
                        'execution_mode': 'parallel'
                    },
                    {
                        'name': 'sync_point_1',
                        'type': 'sync_point',
                        'validation_type': 'requirement_consensus'
                    },
                    {
                        'name': 'architecture_design',
                        'agents': ['api-designer', 'backend-architect', 'database-specialist'],
                        'execution_mode': 'sequential'
                    },
                    {
                        'name': 'sync_point_2',
                        'type': 'sync_point',
                        'validation_type': 'architecture_review'
                    },
                    {
                        'name': 'parallel_implementation',
                        'agents': ['backend-architect', 'frontend-specialist'],
                        'execution_mode': 'parallel'
                    },
                    {
                        'name': 'quality_gate',
                        'type': 'quality_gate',
                        'checks': ['code_quality', 'security_scan']
                    },
                    {
                        'name': 'testing_phase',
                        'agents': ['test-engineer'],
                        'execution_mode': 'sequential'
                    },
                    {
                        'name': 'final_validation',
                        'type': 'sync_point',
                        'validation_type': 'final_verification'
                    }
                ]
            }

            result = orchestrator.execute_workflow(
                workflow_definition,
                task_description="Complex multi-stage workflow"
            )

            assert result['success'] is True
            assert len(result['stage_results']) == 8

            # Verify all stages completed
            stage_names = [stage['stage'] for stage in result['stage_results']]
            expected_stages = [
                'deep_understanding', 'sync_point_1', 'architecture_design',
                'sync_point_2', 'parallel_implementation', 'quality_gate',
                'testing_phase', 'final_validation'
            ]
            assert stage_names == expected_stages

    def test_workflow_context_passing(self, orchestrator, mock_agents):
        """Test context passing between workflow stages"""
        context_data = []

        def context_aware_execute(task_description, context=None, **kwargs):
            context_data.append(context)
            return {
                'success': True,
                'output': f'Processed with context: {context}',
                'execution_time': 0.5,
                'context_update': {'processed_by': task_description.split()[0]}
            }

        for agent in mock_agents.values():
            agent.execute = context_aware_execute

        with patch.object(orchestrator, '_get_agent') as mock_get_agent:
            mock_get_agent.side_effect = lambda name: mock_agents[name]

            workflow_definition = {
                'name': 'context_workflow',
                'stages': [
                    {
                        'name': 'stage1',
                        'agents': ['business-analyst'],
                        'execution_mode': 'sequential'
                    },
                    {
                        'name': 'stage2',
                        'agents': ['api-designer'],
                        'execution_mode': 'sequential'
                    }
                ]
            }

            initial_context = {'project_type': 'api_development'}

            result = orchestrator.execute_workflow(
                workflow_definition,
                task_description="Test context passing",
                initial_context=initial_context
            )

            assert result['success'] is True
            # Verify context was passed and updated
            assert len(context_data) == 2
            assert context_data[0]['project_type'] == 'api_development'
            # Second stage should receive updated context from first stage
            assert 'processed_by' in context_data[1]


class TestSyncPointManager:
    """Test SyncPointManager integration"""

    @pytest.fixture
    def sync_manager(self):
        """Create SyncPointManager for testing"""
        return SyncPointManager()

    def test_consensus_check_sync_point(self, sync_manager):
        """Test consensus check synchronization point"""
        agent_outputs = [
            {
                'agent': 'business-analyst',
                'output': 'User authentication system with email/password login',
                'confidence': 0.9
            },
            {
                'agent': 'project-manager',
                'output': 'Authentication system supporting email and password',
                'confidence': 0.85
            },
            {
                'agent': 'technical-writer',
                'output': 'Login system using email and password authentication',
                'confidence': 0.95
            }
        ]

        result = sync_manager.execute_consensus_check(
            agent_outputs,
            consensus_threshold=0.8
        )

        assert result['success'] is True
        assert result['consensus_achieved'] is True
        assert result['consensus_score'] >= 0.8

    def test_architecture_review_sync_point(self, sync_manager):
        """Test architecture review synchronization point"""
        architecture_outputs = [
            {
                'agent': 'api-designer',
                'output': 'REST API with JWT authentication endpoints',
                'quality_score': 0.92
            },
            {
                'agent': 'backend-architect',
                'output': 'Python FastAPI with SQLAlchemy ORM and PostgreSQL',
                'quality_score': 0.88
            },
            {
                'agent': 'security-auditor',
                'output': 'Secure password hashing with bcrypt, JWT with refresh tokens',
                'quality_score': 0.95
            }
        ]

        result = sync_manager.execute_architecture_review(
            architecture_outputs,
            quality_threshold=0.85
        )

        assert result['success'] is True
        assert result['review_passed'] is True
        assert result['overall_quality'] >= 0.85

    def test_quality_gate_sync_point(self, sync_manager):
        """Test quality gate synchronization point"""
        quality_metrics = {
            'code_coverage': 0.92,
            'complexity_score': 0.85,
            'security_score': 0.90,
            'performance_score': 0.88,
            'documentation_score': 0.89
        }

        quality_thresholds = {
            'code_coverage': 0.85,
            'complexity_score': 0.80,
            'security_score': 0.85,
            'performance_score': 0.85,
            'documentation_score': 0.80
        }

        result = sync_manager.execute_quality_gate(
            quality_metrics,
            quality_thresholds
        )

        assert result['success'] is True
        assert result['gate_passed'] is True
        assert all(result['check_results'].values())

    def test_sync_point_failure_handling(self, sync_manager):
        """Test sync point failure handling"""
        # Low consensus scenario
        agent_outputs = [
            {
                'agent': 'business-analyst',
                'output': 'OAuth authentication system',
                'confidence': 0.7
            },
            {
                'agent': 'project-manager',
                'output': 'Simple username/password login',
                'confidence': 0.8
            }
        ]

        result = sync_manager.execute_consensus_check(
            agent_outputs,
            consensus_threshold=0.9  # High threshold
        )

        assert result['success'] is False
        assert result['consensus_achieved'] is False
        assert 'retry_suggestions' in result

    def test_sync_point_with_retries(self, sync_manager):
        """Test sync point with retry mechanism"""
        attempt_count = 0

        def mock_quality_check():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                return {
                    'success': False,
                    'quality_score': 0.7,  # Below threshold
                    'issues': ['Code coverage too low']
                }
            else:
                return {
                    'success': True,
                    'quality_score': 0.9,  # Above threshold
                    'issues': []
                }

        with patch.object(sync_manager, '_execute_quality_check', side_effect=mock_quality_check):
            result = sync_manager.execute_quality_gate_with_retries(
                quality_threshold=0.85,
                max_retries=3
            )

            assert result['success'] is True
            assert attempt_count == 3
            assert result['attempts'] == 3


class TestDecisionRecorder:
    """Test DecisionRecorder integration"""

    @pytest.fixture
    def decision_recorder(self, tmp_path):
        """Create DecisionRecorder for testing"""
        return DecisionRecorder(storage_path=str(tmp_path))

    def test_decision_recording(self, decision_recorder):
        """Test decision recording functionality"""
        decision = {
            'title': 'Authentication Method Selection',
            'context': 'Need to choose authentication method for API',
            'options': [
                {
                    'name': 'JWT with refresh tokens',
                    'pros': ['Stateless', 'Scalable', 'Secure'],
                    'cons': ['Complex refresh logic']
                },
                {
                    'name': 'Session-based authentication',
                    'pros': ['Simple', 'Well-understood'],
                    'cons': ['Requires session storage', 'Less scalable']
                }
            ],
            'decision': 'JWT with refresh tokens',
            'reasoning': 'Better scalability and security for API use case',
            'consequences': ['Need to implement refresh token rotation'],
            'decision_maker': 'security-auditor',
            'stakeholders': ['backend-architect', 'api-designer']
        }

        decision_id = decision_recorder.record_decision(decision)
        assert decision_id is not None

        # Retrieve and verify decision
        retrieved = decision_recorder.get_decision(decision_id)
        assert retrieved['title'] == decision['title']
        assert retrieved['decision'] == decision['decision']

    def test_decision_search_and_filtering(self, decision_recorder):
        """Test decision search and filtering"""
        # Record multiple decisions
        decisions = [
            {
                'title': 'Database Choice',
                'decision': 'PostgreSQL',
                'tags': ['database', 'backend'],
                'decision_maker': 'backend-architect'
            },
            {
                'title': 'Authentication Method',
                'decision': 'JWT',
                'tags': ['security', 'authentication'],
                'decision_maker': 'security-auditor'
            },
            {
                'title': 'Frontend Framework',
                'decision': 'React',
                'tags': ['frontend', 'ui'],
                'decision_maker': 'frontend-specialist'
            }
        ]

        decision_ids = []
        for decision in decisions:
            decision_id = decision_recorder.record_decision(decision)
            decision_ids.append(decision_id)

        # Search by tag
        backend_decisions = decision_recorder.search_decisions(tags=['backend'])
        assert len(backend_decisions) == 1
        assert backend_decisions[0]['title'] == 'Database Choice'

        # Search by decision maker
        security_decisions = decision_recorder.search_decisions(
            decision_maker='security-auditor'
        )
        assert len(security_decisions) == 1
        assert security_decisions[0]['title'] == 'Authentication Method'

    def test_decision_impact_tracking(self, decision_recorder):
        """Test decision impact tracking"""
        # Record initial decision
        initial_decision = {
            'title': 'API Rate Limiting',
            'decision': 'Token bucket algorithm',
            'reasoning': 'Good balance of flexibility and protection'
        }

        decision_id = decision_recorder.record_decision(initial_decision)

        # Record impact
        impact = {
            'type': 'implementation',
            'description': 'Successfully implemented rate limiting with Redis',
            'outcome': 'positive',
            'metrics': {
                'performance_impact': 'minimal',
                'complexity_added': 'low',
                'security_improvement': 'high'
            }
        }

        decision_recorder.record_decision_impact(decision_id, impact)

        # Retrieve decision with impact
        decision_with_impact = decision_recorder.get_decision_with_impact(decision_id)
        assert len(decision_with_impact['impacts']) == 1
        assert decision_with_impact['impacts'][0]['outcome'] == 'positive'

    def test_decision_analytics(self, decision_recorder):
        """Test decision analytics and insights"""
        # Record multiple decisions over time
        decisions = [
            {
                'title': 'Decision 1',
                'decision_maker': 'backend-architect',
                'tags': ['backend', 'performance']
            },
            {
                'title': 'Decision 2',
                'decision_maker': 'backend-architect',
                'tags': ['backend', 'security']
            },
            {
                'title': 'Decision 3',
                'decision_maker': 'frontend-specialist',
                'tags': ['frontend', 'performance']
            }
        ]

        for decision in decisions:
            decision_recorder.record_decision(decision)

        # Get analytics
        analytics = decision_recorder.get_decision_analytics()

        assert 'decision_makers' in analytics
        assert 'common_tags' in analytics
        assert 'decision_frequency' in analytics

        # Check decision maker stats
        assert analytics['decision_makers']['backend-architect'] == 2
        assert analytics['decision_makers']['frontend-specialist'] == 1

        # Check tag frequency
        assert analytics['common_tags']['backend'] == 2
        assert analytics['common_tags']['performance'] == 2


@pytest.mark.integration
class TestWorkflowIntegration:
    """Integration tests for complete workflow system"""

    @pytest.fixture
    def integrated_system(self, tmp_path):
        """Create integrated workflow system"""
        orchestrator_config = {
            'workspace_path': str(tmp_path),
            'max_parallel_tasks': 3,
            'timeout': 60,
            'quality_gates_enabled': True
        }

        orchestrator = WorkflowOrchestrator(orchestrator_config)
        sync_manager = SyncPointManager()
        decision_recorder = DecisionRecorder(storage_path=str(tmp_path))

        return {
            'orchestrator': orchestrator,
            'sync_manager': sync_manager,
            'decision_recorder': decision_recorder
        }

    def test_end_to_end_workflow_execution(self, integrated_system, mock_agents):
        """Test complete end-to-end workflow execution"""
        orchestrator = integrated_system['orchestrator']

        with patch.object(orchestrator, '_get_agent') as mock_get_agent:
            mock_get_agent.side_effect = lambda name: mock_agents[name]

            # Premium quality workflow definition
            workflow_definition = {
                'name': 'premium_quality_workflow',
                'description': 'High-quality development workflow with multiple validation points',
                'stages': [
                    {
                        'name': 'deep_understanding',
                        'agents': ['project-manager', 'business-analyst', 'technical-writer'],
                        'execution_mode': 'parallel',
                        'timeout': 30
                    },
                    {
                        'name': 'requirements_consensus',
                        'type': 'sync_point',
                        'validation_type': 'consensus_check',
                        'required_consensus': 0.85
                    },
                    {
                        'name': 'architecture_design',
                        'agents': ['api-designer'],
                        'execution_mode': 'sequential'
                    },
                    {
                        'name': 'detailed_design',
                        'agents': ['backend-architect', 'database-specialist'],
                        'execution_mode': 'sequential'
                    },
                    {
                        'name': 'architecture_review',
                        'type': 'sync_point',
                        'validation_type': 'architecture_review',
                        'reviewers': ['security-auditor']
                    },
                    {
                        'name': 'parallel_implementation',
                        'agents': ['backend-architect', 'frontend-specialist', 'test-engineer'],
                        'execution_mode': 'parallel'
                    },
                    {
                        'name': 'quality_gate',
                        'type': 'quality_gate',
                        'checks': ['code_quality', 'test_coverage', 'security_scan'],
                        'thresholds': {
                            'code_quality': 0.9,
                            'test_coverage': 0.85,
                            'security_scan': 0.95
                        }
                    },
                    {
                        'name': 'final_validation',
                        'type': 'sync_point',
                        'validation_type': 'final_verification'
                    }
                ]
            }

            result = orchestrator.execute_workflow(
                workflow_definition,
                task_description="Implement user authentication API with high quality standards"
            )

            assert result['success'] is True
            assert len(result['stage_results']) == 8

            # Verify all stages completed successfully
            for stage_result in result['stage_results']:
                assert stage_result['success'] is True

            # Check execution metrics
            assert 'total_execution_time' in result
            assert 'quality_metrics' in result
            assert 'decisions_recorded' in result

    def test_workflow_failure_recovery(self, integrated_system, mock_agents):
        """Test workflow failure and recovery mechanisms"""
        orchestrator = integrated_system['orchestrator']

        # Simulate failure in one agent
        mock_agents['backend-architect'].execute.return_value = {
            'success': False,
            'error': 'Database connection failed',
            'execution_time': 1.0
        }

        with patch.object(orchestrator, '_get_agent') as mock_get_agent:
            mock_get_agent.side_effect = lambda name: mock_agents[name]

            workflow_definition = {
                'name': 'recovery_workflow',
                'error_handling': {
                    'retry_attempts': 2,
                    'recovery_strategies': {
                        'backend-architect': ['database-specialist']  # Fallback agent
                    }
                },
                'stages': [
                    {
                        'name': 'implementation',
                        'agents': ['backend-architect'],
                        'execution_mode': 'sequential'
                    }
                ]
            }

            result = orchestrator.execute_workflow(
                workflow_definition,
                task_description="Test failure recovery"
            )

            # Should have attempted recovery
            assert 'recovery_attempts' in result
            assert result['recovery_attempts'] > 0

    def test_workflow_performance_monitoring(self, integrated_system, mock_agents):
        """Test workflow performance monitoring"""
        orchestrator = integrated_system['orchestrator']

        # Add timing to mock agents
        def timed_execute(*args, **kwargs):
            import random
            execution_time = random.uniform(0.5, 2.0)
            time.sleep(execution_time / 10)  # Simulate work (scaled down for tests)
            return {
                'success': True,
                'output': 'Mock output',
                'execution_time': execution_time,
                'memory_usage': random.uniform(50, 200),  # MB
                'cpu_usage': random.uniform(20, 80)  # Percentage
            }

        for agent in mock_agents.values():
            agent.execute = timed_execute

        with patch.object(orchestrator, '_get_agent') as mock_get_agent:
            mock_get_agent.side_effect = lambda name: mock_agents[name]

            workflow_definition = {
                'name': 'performance_monitoring_workflow',
                'monitoring': {
                    'track_performance': True,
                    'resource_limits': {
                        'max_memory_mb': 500,
                        'max_cpu_percent': 90
                    }
                },
                'stages': [
                    {
                        'name': 'monitored_stage',
                        'agents': ['business-analyst', 'api-designer', 'backend-architect'],
                        'execution_mode': 'parallel'
                    }
                ]
            }

            result = orchestrator.execute_workflow(
                workflow_definition,
                task_description="Test performance monitoring"
            )

            assert result['success'] is True
            assert 'performance_metrics' in result
            performance = result['performance_metrics']
            assert 'total_execution_time' in performance
            assert 'peak_memory_usage' in performance
            assert 'average_cpu_usage' in performance

    def test_workflow_decision_recording(self, integrated_system):
        """Test automatic decision recording during workflow"""
        orchestrator = integrated_system['orchestrator']
        decision_recorder = integrated_system['decision_recorder']

        # Mock agent that makes decisions
        def decision_making_execute(task_description, **kwargs):
            decisions = [
                {
                    'title': 'API Authentication Method',
                    'options': ['JWT', 'Session-based', 'OAuth'],
                    'decision': 'JWT',
                    'reasoning': 'Best for stateless API architecture'
                }
            ]
            return {
                'success': True,
                'output': 'Selected JWT authentication',
                'execution_time': 1.0,
                'decisions': decisions
            }

        mock_agent = MagicMock()
        mock_agent.execute = decision_making_execute

        with patch.object(orchestrator, '_get_agent') as mock_get_agent:
            mock_get_agent.return_value = mock_agent

            workflow_definition = {
                'name': 'decision_recording_workflow',
                'decision_recording': {
                    'enabled': True,
                    'auto_record': True
                },
                'stages': [
                    {
                        'name': 'decision_stage',
                        'agents': ['security-auditor'],
                        'execution_mode': 'sequential'
                    }
                ]
            }

            result = orchestrator.execute_workflow(
                workflow_definition,
                task_description="Make authentication decisions"
            )

            assert result['success'] is True
            assert 'decisions_recorded' in result
            assert result['decisions_recorded'] > 0

            # Verify decision was recorded
            decisions = decision_recorder.search_decisions(
                title_contains='API Authentication Method'
            )
            assert len(decisions) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])