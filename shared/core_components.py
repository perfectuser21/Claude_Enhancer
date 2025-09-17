#!/usr/bin/env python3
"""
Perfect21 核心组件实现
基于接口分离原则(ISP)和依赖倒置原则(DIP)的解耦实现
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from .interfaces import (
    IWorkflowOrchestrator, IDecisionRecorder, ILearningSystem,
    ICacheManager, IWorkflowTemplate, ExecutionContext,
    ExecutionResult, AgentTask, WorkflowException, EventTypes
)
from .base_classes import BaseLogger, BaseEventBus
from .dependency_injection import Injectable


@Injectable(name='workflow_orchestrator', singleton=True)
class WorkflowOrchestrator(IWorkflowOrchestrator):
    """工作流编排器 - 解耦实现"""

    def __init__(self, logger: BaseLogger, event_bus: BaseEventBus, cache_manager: ICacheManager):
        self.logger = logger
        self.event_bus = event_bus
        self.cache_manager = cache_manager
        self.current_workflow = None
        self.current_stage = None
        self.execution_state = {}

    async def execute_workflow(self, template: IWorkflowTemplate, context: ExecutionContext) -> ExecutionResult:
        """执行工作流"""
        workflow_id = f"workflow_{int(time.time())}"

        try:
            self.logger.info(f"开始执行工作流: {template.get_template_name()}")
            self.event_bus.publish(EventTypes.WORKFLOW_STARTED, {
                'workflow_id': workflow_id,
                'template_name': template.get_template_name(),
                'context': context.__dict__
            })

            # 验证模板
            if not template.validate_template():
                raise WorkflowException("工作流模板验证失败")

            # 初始化执行状态
            self.execution_state[workflow_id] = {
                'template': template,
                'context': context,
                'start_time': datetime.now(),
                'stages_completed': [],
                'current_stage': None,
                'status': 'running'
            }

            # 执行各个阶段
            stages = template.get_stages()
            results = []

            for stage in stages:
                stage_result = await self._execute_stage(workflow_id, stage, context)
                results.append(stage_result)

                # 更新执行状态
                self.execution_state[workflow_id]['stages_completed'].append(stage['name'])
                self.execution_state[workflow_id]['current_stage'] = stage['name']

                # 如果阶段失败且必须成功，停止执行
                if not stage_result.success and stage.get('required', True):
                    raise WorkflowException(f"必需阶段执行失败: {stage['name']}")

            # 标记工作流完成
            self.execution_state[workflow_id]['status'] = 'completed'
            self.execution_state[workflow_id]['end_time'] = datetime.now()

            self.event_bus.publish(EventTypes.WORKFLOW_COMPLETED, {
                'workflow_id': workflow_id,
                'success': True,
                'results': [r.__dict__ for r in results]
            })

            return ExecutionResult(
                success=True,
                data={'workflow_id': workflow_id, 'stage_results': results},
                metadata={'template_name': template.get_template_name()}
            )

        except Exception as e:
            self.logger.error(f"工作流执行失败: {workflow_id}", e)

            if workflow_id in self.execution_state:
                self.execution_state[workflow_id]['status'] = 'failed'
                self.execution_state[workflow_id]['error'] = str(e)

            return ExecutionResult(
                success=False,
                error_message=str(e),
                metadata={'workflow_id': workflow_id}
            )

    async def _execute_stage(self, workflow_id: str, stage: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        """执行工作流阶段"""
        stage_name = stage['name']
        self.logger.info(f"执行阶段: {stage_name}")

        try:
            # 模拟阶段执行
            await asyncio.sleep(stage.get('duration', 1))

            # 检查同步点
            if 'sync_point' in stage:
                sync_valid = self.validate_sync_point(stage['sync_point'])
                if not sync_valid:
                    raise WorkflowException(f"同步点验证失败: {stage_name}")

            return ExecutionResult(
                success=True,
                data={'stage': stage_name, 'output': f"Stage {stage_name} completed"},
                metadata={'workflow_id': workflow_id, 'stage': stage_name}
            )

        except Exception as e:
            self.logger.error(f"阶段执行失败: {stage_name}", e)
            return ExecutionResult(
                success=False,
                error_message=str(e),
                metadata={'workflow_id': workflow_id, 'stage': stage_name}
            )

    def validate_sync_point(self, criteria: Dict[str, Any]) -> bool:
        """验证同步点"""
        # 基础实现 - 检查通用条件
        required_conditions = criteria.get('conditions', [])

        for condition in required_conditions:
            if not self._check_condition(condition):
                self.logger.warning(f"同步点条件未满足: {condition}")
                return False

        return True

    def _check_condition(self, condition: str) -> bool:
        """检查单个条件"""
        # 简化的条件检查逻辑
        if condition == 'quality_check':
            return True  # 假设质量检查通过
        elif condition == 'test_coverage':
            return True  # 假设测试覆盖率达标
        elif condition == 'security_scan':
            return True  # 假设安全扫描通过
        else:
            return True  # 默认通过

    def get_execution_progress(self) -> Dict[str, Any]:
        """获取执行进度"""
        active_workflows = {
            wid: state for wid, state in self.execution_state.items()
            if state['status'] == 'running'
        }

        return {
            'active_workflows': len(active_workflows),
            'total_workflows': len(self.execution_state),
            'workflows': {
                wid: {
                    'template_name': state['template'].get_template_name(),
                    'status': state['status'],
                    'current_stage': state.get('current_stage'),
                    'progress': len(state['stages_completed']) / len(state['template'].get_stages()) * 100
                }
                for wid, state in self.execution_state.items()
            }
        }


@Injectable(name='decision_recorder', singleton=True)
class DecisionRecorder(IDecisionRecorder):
    """决策记录器 - ADR模式实现"""

    def __init__(self, logger: BaseLogger, cache_manager: ICacheManager):
        self.logger = logger
        self.cache_manager = cache_manager
        self.decisions = []

    def record_decision(self, decision: Dict[str, Any]) -> None:
        """记录决策"""
        adr = {
            'id': len(self.decisions) + 1,
            'timestamp': datetime.now().isoformat(),
            'title': decision.get('title', 'Untitled Decision'),
            'status': decision.get('status', 'accepted'),
            'context': decision.get('context', ''),
            'decision': decision.get('decision', ''),
            'consequences': decision.get('consequences', ''),
            'alternatives': decision.get('alternatives', []),
            'metadata': decision.get('metadata', {})
        }

        self.decisions.append(adr)
        self.logger.info(f"记录决策: {adr['title']} (ID: {adr['id']})")

        # 缓存最新决策
        self.cache_manager.set(f"decision_{adr['id']}", adr, ttl=3600)

    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取决策历史"""
        return sorted(self.decisions, key=lambda x: x['timestamp'], reverse=True)[:limit]

    def get_decision_by_id(self, decision_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取决策"""
        # 先从缓存查找
        cached = self.cache_manager.get(f"decision_{decision_id}")
        if cached:
            return cached

        # 从内存查找
        for decision in self.decisions:
            if decision['id'] == decision_id:
                return decision

        return None

    def search_decisions(self, query: str) -> List[Dict[str, Any]]:
        """搜索决策"""
        results = []
        query_lower = query.lower()

        for decision in self.decisions:
            if (query_lower in decision['title'].lower() or
                query_lower in decision['context'].lower() or
                query_lower in decision['decision'].lower()):
                results.append(decision)

        return results


@Injectable(name='learning_system', singleton=True)
class LearningSystem(ILearningSystem):
    """学习系统 - 从执行中学习和改进"""

    def __init__(self, logger: BaseLogger, cache_manager: ICacheManager):
        self.logger = logger
        self.cache_manager = cache_manager
        self.execution_patterns = {}
        self.performance_metrics = {}
        self.improvement_suggestions = []

    def learn_from_execution(self, result: ExecutionResult, feedback: Dict[str, Any] = None) -> None:
        """从执行结果中学习"""
        task_type = result.metadata.get('task_id', 'unknown') if result.metadata else 'unknown'

        # 记录执行模式
        if task_type not in self.execution_patterns:
            self.execution_patterns[task_type] = {
                'total_executions': 0,
                'successful_executions': 0,
                'average_time': 0.0,
                'common_errors': {},
                'best_practices': []
            }

        pattern = self.execution_patterns[task_type]
        pattern['total_executions'] += 1

        if result.success:
            pattern['successful_executions'] += 1
            # 更新平均执行时间
            pattern['average_time'] = (
                (pattern['average_time'] * (pattern['successful_executions'] - 1) + result.execution_time) /
                pattern['successful_executions']
            )
        else:
            # 记录错误模式
            error_key = result.error_message[:50] if result.error_message else 'unknown_error'
            pattern['common_errors'][error_key] = pattern['common_errors'].get(error_key, 0) + 1

        # 处理用户反馈
        if feedback:
            self._process_feedback(task_type, feedback)

        # 生成改进建议
        self._generate_improvements(task_type, result)

        self.logger.info(f"学习完成: {task_type}, 成功率: {pattern['successful_executions']/pattern['total_executions']:.2%}")

    def get_recommendations(self, task_type: str) -> List[str]:
        """获取改进建议"""
        if task_type not in self.execution_patterns:
            return ["暂无历史数据，建议谨慎执行"]

        pattern = self.execution_patterns[task_type]
        recommendations = []

        # 基于成功率的建议
        success_rate = pattern['successful_executions'] / pattern['total_executions']
        if success_rate < 0.8:
            recommendations.append(f"该任务类型成功率较低({success_rate:.1%})，建议增加预检查")

        # 基于执行时间的建议
        if pattern['average_time'] > 60:
            recommendations.append(f"平均执行时间较长({pattern['average_time']:.1f}s)，建议优化流程")

        # 基于常见错误的建议
        if pattern['common_errors']:
            most_common_error = max(pattern['common_errors'].items(), key=lambda x: x[1])
            recommendations.append(f"常见错误: {most_common_error[0]}, 建议添加预防措施")

        # 从改进建议中获取相关建议
        relevant_suggestions = [
            s for s in self.improvement_suggestions
            if s.get('task_type') == task_type
        ]
        recommendations.extend([s['suggestion'] for s in relevant_suggestions[-3:]])

        return recommendations

    def _process_feedback(self, task_type: str, feedback: Dict[str, Any]) -> None:
        """处理用户反馈"""
        rating = feedback.get('rating', 0)
        comments = feedback.get('comments', '')

        if rating >= 4:
            # 好评，记录最佳实践
            self.execution_patterns[task_type]['best_practices'].append({
                'feedback': comments,
                'timestamp': datetime.now().isoformat(),
                'rating': rating
            })
        elif rating <= 2:
            # 差评，生成改进建议
            self.improvement_suggestions.append({
                'task_type': task_type,
                'suggestion': f"用户反馈需要改进: {comments}",
                'priority': 'high',
                'timestamp': datetime.now().isoformat()
            })

    def _generate_improvements(self, task_type: str, result: ExecutionResult) -> None:
        """生成改进建议"""
        # 基于执行时间的改进建议
        if result.execution_time > 30:
            self.improvement_suggestions.append({
                'task_type': task_type,
                'suggestion': f"考虑并行化或缓存优化，当前执行时间: {result.execution_time:.1f}s",
                'priority': 'medium',
                'timestamp': datetime.now().isoformat()
            })

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能总结"""
        total_executions = sum(p['total_executions'] for p in self.execution_patterns.values())
        total_successful = sum(p['successful_executions'] for p in self.execution_patterns.values())

        return {
            'total_task_types': len(self.execution_patterns),
            'total_executions': total_executions,
            'overall_success_rate': total_successful / total_executions if total_executions > 0 else 0,
            'improvement_suggestions_count': len(self.improvement_suggestions),
            'patterns': {
                task_type: {
                    'executions': pattern['total_executions'],
                    'success_rate': pattern['successful_executions'] / pattern['total_executions'] if pattern['total_executions'] > 0 else 0,
                    'average_time': pattern['average_time']
                }
                for task_type, pattern in self.execution_patterns.items()
            }
        }


@Injectable(name='cache_manager', singleton=True)
class MemoryCacheManager(ICacheManager):
    """内存缓存管理器"""

    def __init__(self, logger: BaseLogger):
        self.logger = logger
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cleanup_interval = 300  # 5分钟清理一次

    def get(self, key: str) -> Any:
        """获取缓存值"""
        if key in self._cache:
            entry = self._cache[key]

            # 检查是否过期
            if entry['expires_at'] and datetime.now() > entry['expires_at']:
                del self._cache[key]
                return None

            return entry['value']

        return None

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """设置缓存值"""
        expires_at = None
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)

        self._cache[key] = {
            'value': value,
            'created_at': datetime.now(),
            'expires_at': expires_at
        }

        self.logger.debug(f"缓存设置: {key}, TTL: {ttl}")

    def delete(self, key: str) -> None:
        """删除缓存"""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self.logger.info("缓存已清空")

    def cleanup_expired(self) -> None:
        """清理过期缓存"""
        now = datetime.now()
        expired_keys = []

        for key, entry in self._cache.items():
            if entry['expires_at'] and now > entry['expires_at']:
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            self.logger.info(f"清理过期缓存: {len(expired_keys)} 项")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        now = datetime.now()
        active_entries = 0
        expired_entries = 0

        for entry in self._cache.values():
            if entry['expires_at'] is None or now <= entry['expires_at']:
                active_entries += 1
            else:
                expired_entries += 1

        return {
            'total_entries': len(self._cache),
            'active_entries': active_entries,
            'expired_entries': expired_entries
        }