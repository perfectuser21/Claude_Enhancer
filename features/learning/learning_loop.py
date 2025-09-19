"""
Learning Loop - Mock Implementation for Testing
学习反馈循环 - 记录执行经验并生成改进建议
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import statistics


class LearningLoop:
    """学习反馈循环"""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or ".perfect21/learning_data.json")
        self.storage_path.parent.mkdir(exist_ok=True)
        self.experiences: List[Dict[str, Any]] = []
        self.patterns: List[Dict[str, Any]] = []
        self.suggestions_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._load_learning_data()

    def record_experience(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """记录执行经验"""
        try:
            experience_id = f"exp_{int(time.time())}"

            experience_record = {
                'experience_id': experience_id,
                'workflow': experience.get('workflow', 'unknown'),
                'stage': experience.get('stage', 'unknown'),
                'action': experience.get('action', 'unknown'),
                'outcome': experience.get('outcome', 'unknown'),
                'duration': experience.get('duration', 0),
                'quality_score': experience.get('quality_score', 0),
                'success': experience.get('outcome') == 'success',
                'lessons': experience.get('lessons', []),
                'context': experience.get('context', {}),
                'metrics': experience.get('metrics', {}),
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'environment': experience.get('environment', 'development'),
                    'complexity': experience.get('complexity', 'medium'),
                    'team_size': experience.get('team_size', 1),
                    'technologies': experience.get('technologies', [])
                }
            }

            self.experiences.append(experience_record)
            self._save_learning_data()

            # 清除缓存以强制重新分析
            self.suggestions_cache.clear()

            # 触发模式识别
            self._update_patterns()

            return {
                'success': True,
                'experience_id': experience_id,
                'patterns_updated': True,
                'message': 'Experience recorded and patterns updated'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to record experience: {str(e)}'
            }

    def get_suggestions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取基于历史经验的建议"""
        try:
            context_key = self._generate_context_key(context)

            # 检查缓存
            if context_key in self.suggestions_cache:
                return self.suggestions_cache[context_key]

            workflow = context.get('workflow', '')
            stage = context.get('stage', '')

            # 查找相关经验
            relevant_experiences = [
                exp for exp in self.experiences
                if exp['workflow'].lower() == workflow.lower() and
                exp['stage'].lower() == stage.lower()
            ]

            suggestions = []

            if relevant_experiences:
                # 分析成功和失败的经验
                successful_experiences = [exp for exp in relevant_experiences if exp['success']]
                failed_experiences = [exp for exp in relevant_experiences if not exp['success']]

                # 基于成功经验生成建议
                if successful_experiences:
                    success_suggestions = self._generate_success_based_suggestions(successful_experiences)
                    suggestions.extend(success_suggestions)

                # 基于失败经验生成避免建议
                if failed_experiences:
                    failure_suggestions = self._generate_failure_based_suggestions(failed_experiences)
                    suggestions.extend(failure_suggestions)

                # 基于性能数据生成优化建议
                performance_suggestions = self._generate_performance_suggestions(relevant_experiences)
                suggestions.extend(performance_suggestions)

            else:
                # 没有相关经验时，提供通用建议
                suggestions = self._generate_general_suggestions(context)

            # 添加模式匹配建议
            pattern_suggestions = self._get_pattern_based_suggestions(context)
            suggestions.extend(pattern_suggestions)

            # 缓存结果
            self.suggestions_cache[context_key] = suggestions

            return suggestions

        except Exception as e:
            return [{
                'type': 'error',
                'priority': 'high',
                'suggestion': f'Failed to generate suggestions: {str(e)}',
                'confidence': 0.0
            }]

    def identify_patterns(self) -> List[Dict[str, Any]]:
        """识别执行模式"""
        try:
            patterns = []

            if len(self.experiences) < 3:
                return patterns

            # 分析工作流模式
            workflow_patterns = self._analyze_workflow_patterns()
            patterns.extend(workflow_patterns)

            # 分析性能模式
            performance_patterns = self._analyze_performance_patterns()
            patterns.extend(performance_patterns)

            # 分析错误模式
            error_patterns = self._analyze_error_patterns()
            patterns.extend(error_patterns)

            # 分析时间模式
            time_patterns = self._analyze_time_patterns()
            patterns.extend(time_patterns)

            # 更新模式缓存
            self.patterns = patterns
            self._save_learning_data()

            return patterns

        except Exception as e:
            return [{
                'type': 'error',
                'pattern': f'Pattern identification failed: {str(e)}',
                'confidence': 0.0
            }]

    def get_learning_analytics(self) -> Dict[str, Any]:
        """获取学习分析数据"""
        if not self.experiences:
            return {
                'total_experiences': 0,
                'success_rate': 0,
                'average_duration': 0,
                'average_quality': 0
            }

        total_experiences = len(self.experiences)
        successful_experiences = [exp for exp in self.experiences if exp['success']]
        success_rate = len(successful_experiences) / total_experiences

        durations = [exp['duration'] for exp in self.experiences if exp['duration'] > 0]
        average_duration = statistics.mean(durations) if durations else 0

        quality_scores = [exp['quality_score'] for exp in self.experiences if exp['quality_score'] > 0]
        average_quality = statistics.mean(quality_scores) if quality_scores else 0

        # 分析趋势
        recent_experiences = [
            exp for exp in self.experiences
            if datetime.fromisoformat(exp['timestamp']) > datetime.now() - timedelta(days=30)
        ]

        recent_success_rate = 0
        if recent_experiences:
            recent_successful = [exp for exp in recent_experiences if exp['success']]
            recent_success_rate = len(recent_successful) / len(recent_experiences)

        # 最常见的工作流和阶段
        workflow_counts = {}
        stage_counts = {}

        for exp in self.experiences:
            workflow = exp['workflow']
            stage = exp['stage']

            workflow_counts[workflow] = workflow_counts.get(workflow, 0) + 1
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        return {
            'total_experiences': total_experiences,
            'success_rate': round(success_rate * 100, 2),
            'recent_success_rate': round(recent_success_rate * 100, 2),
            'average_duration': round(average_duration, 2),
            'average_quality': round(average_quality, 2),
            'total_patterns': len(self.patterns),
            'most_common_workflows': sorted(workflow_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'most_common_stages': sorted(stage_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'learning_velocity': len(recent_experiences),
            'improvement_opportunities': self._identify_improvement_opportunities()
        }

    def _generate_context_key(self, context: Dict[str, Any]) -> str:
        """生成上下文缓存键"""
        workflow = context.get('workflow', '')
        stage = context.get('stage', '')
        return f"{workflow}:{stage}"

    def _generate_success_based_suggestions(self, successful_experiences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于成功经验生成建议"""
        suggestions = []

        # 分析成功因素
        common_actions = {}
        quality_scores = []

        for exp in successful_experiences:
            action = exp['action']
            common_actions[action] = common_actions.get(action, 0) + 1
            quality_scores.append(exp['quality_score'])

        # 推荐最常见的成功行为
        if common_actions:
            best_action = max(common_actions.items(), key=lambda x: x[1])
            suggestions.append({
                'type': 'best_practice',
                'priority': 'high',
                'suggestion': f'建议使用 "{best_action[0]}" 方法，成功率较高',
                'confidence': min(1.0, best_action[1] / len(successful_experiences)),
                'evidence_count': best_action[1]
            })

        # 基于质量分数的建议
        if quality_scores:
            avg_quality = statistics.mean(quality_scores)
            if avg_quality > 8.0:
                suggestions.append({
                    'type': 'quality_insight',
                    'priority': 'medium',
                    'suggestion': f'此阶段平均质量分数为 {avg_quality:.1f}，建议继续保持高标准',
                    'confidence': 0.8
                })

        return suggestions

    def _generate_failure_based_suggestions(self, failed_experiences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于失败经验生成避免建议"""
        suggestions = []

        # 分析失败原因
        failed_actions = {}
        for exp in failed_experiences:
            action = exp['action']
            failed_actions[action] = failed_actions.get(action, 0) + 1

        # 警告容易失败的行为
        if failed_actions:
            worst_action = max(failed_actions.items(), key=lambda x: x[1])
            suggestions.append({
                'type': 'warning',
                'priority': 'high',
                'suggestion': f'避免使用 "{worst_action[0]}" 方法，失败率较高',
                'confidence': min(1.0, worst_action[1] / len(failed_experiences)),
                'evidence_count': worst_action[1]
            })

        return suggestions

    def _generate_performance_suggestions(self, experiences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成性能优化建议"""
        suggestions = []

        durations = [exp['duration'] for exp in experiences if exp['duration'] > 0]
        if len(durations) >= 3:
            avg_duration = statistics.mean(durations)
            median_duration = statistics.median(durations)

            if avg_duration > median_duration * 1.5:
                suggestions.append({
                    'type': 'performance',
                    'priority': 'medium',
                    'suggestion': f'平均执行时间 {avg_duration:.1f}分钟偏高，建议优化性能',
                    'confidence': 0.7
                })

        return suggestions

    def _generate_general_suggestions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成通用建议"""
        workflow = context.get('workflow', '')
        stage = context.get('stage', '')

        suggestions = [
            {
                'type': 'general',
                'priority': 'medium',
                'suggestion': f'首次执行 {workflow} 的 {stage} 阶段，建议仔细规划和测试',
                'confidence': 0.6
            },
            {
                'type': 'monitoring',
                'priority': 'medium',
                'suggestion': '建议密切监控执行过程，记录详细的性能指标',
                'confidence': 0.8
            }
        ]

        return suggestions

    def _get_pattern_based_suggestions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于模式生成建议"""
        suggestions = []

        for pattern in self.patterns:
            if pattern.get('applicable_to', {}).get('workflow') == context.get('workflow'):
                suggestions.append({
                    'type': 'pattern_based',
                    'priority': 'medium',
                    'suggestion': pattern.get('recommendation', ''),
                    'confidence': pattern.get('confidence', 0.5),
                    'pattern_type': pattern.get('type', 'unknown')
                })

        return suggestions

    def _analyze_workflow_patterns(self) -> List[Dict[str, Any]]:
        """分析工作流模式"""
        patterns = []

        # 分析工作流成功率
        workflow_stats = {}
        for exp in self.experiences:
            workflow = exp['workflow']
            if workflow not in workflow_stats:
                workflow_stats[workflow] = {'total': 0, 'successful': 0}

            workflow_stats[workflow]['total'] += 1
            if exp['success']:
                workflow_stats[workflow]['successful'] += 1

        for workflow, stats in workflow_stats.items():
            if stats['total'] >= 3:
                success_rate = stats['successful'] / stats['total']
                if success_rate > 0.8:
                    patterns.append({
                        'type': 'workflow_success',
                        'pattern': f'{workflow} 工作流具有高成功率 ({success_rate:.1%})',
                        'confidence': min(1.0, stats['total'] / 10),
                        'applicable_to': {'workflow': workflow},
                        'recommendation': f'推荐在类似项目中使用 {workflow} 工作流'
                    })

        return patterns

    def _analyze_performance_patterns(self) -> List[Dict[str, Any]]:
        """分析性能模式"""
        patterns = []

        # 分析阶段性能
        stage_durations = {}
        for exp in self.experiences:
            stage = exp['stage']
            duration = exp['duration']

            if stage not in stage_durations:
                stage_durations[stage] = []
            stage_durations[stage].append(duration)

        for stage, durations in stage_durations.items():
            if len(durations) >= 3:
                avg_duration = statistics.mean(durations)
                patterns.append({
                    'type': 'performance',
                    'pattern': f'{stage} 阶段平均执行时间为 {avg_duration:.1f} 分钟',
                    'confidence': min(1.0, len(durations) / 10),
                    'applicable_to': {'stage': stage},
                    'recommendation': f'为 {stage} 阶段分配约 {avg_duration * 1.2:.1f} 分钟时间'
                })

        return patterns

    def _analyze_error_patterns(self) -> List[Dict[str, Any]]:
        """分析错误模式"""
        patterns = []

        failed_experiences = [exp for exp in self.experiences if not exp['success']]
        if len(failed_experiences) >= 2:
            patterns.append({
                'type': 'error',
                'pattern': f'检测到 {len(failed_experiences)} 次失败，需要关注',
                'confidence': 0.8,
                'recommendation': '建议增加错误处理和监控机制'
            })

        return patterns

    def _analyze_time_patterns(self) -> List[Dict[str, Any]]:
        """分析时间模式"""
        patterns = []

        # 分析执行时间趋势
        recent_experiences = sorted(
            [exp for exp in self.experiences if exp['duration'] > 0],
            key=lambda x: x['timestamp']
        )

        if len(recent_experiences) >= 5:
            recent_durations = [exp['duration'] for exp in recent_experiences[-5:]]
            early_durations = [exp['duration'] for exp in recent_experiences[:5]]

            recent_avg = statistics.mean(recent_durations)
            early_avg = statistics.mean(early_durations)

            if recent_avg < early_avg * 0.8:
                patterns.append({
                    'type': 'improvement',
                    'pattern': '执行效率正在提升',
                    'confidence': 0.7,
                    'recommendation': '继续优化流程，保持改进趋势'
                })

        return patterns

    def _identify_improvement_opportunities(self) -> List[str]:
        """识别改进机会"""
        opportunities = []

        if not self.experiences:
            return opportunities

        # 分析失败率
        failed_count = len([exp for exp in self.experiences if not exp['success']])
        failure_rate = failed_count / len(self.experiences)

        if failure_rate > 0.2:
            opportunities.append('降低失败率：当前失败率过高，需要改进流程稳定性')

        # 分析性能
        durations = [exp['duration'] for exp in self.experiences if exp['duration'] > 0]
        if durations:
            avg_duration = statistics.mean(durations)
            if avg_duration > 60:  # 超过60分钟
                opportunities.append('优化执行时间：平均执行时间过长，需要性能优化')

        # 分析质量
        quality_scores = [exp['quality_score'] for exp in self.experiences if exp['quality_score'] > 0]
        if quality_scores:
            avg_quality = statistics.mean(quality_scores)
            if avg_quality < 7:
                opportunities.append('提升质量标准：平均质量分数偏低，需要质量改进')

        return opportunities

    def _update_patterns(self) -> None:
        """更新模式识别"""
        self.patterns = self.identify_patterns()

    def _load_learning_data(self) -> None:
        """加载学习数据"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.experiences = data.get('experiences', [])
                    self.patterns = data.get('patterns', [])
        except Exception:
            self.experiences = []
            self.patterns = []

    def _save_learning_data(self) -> None:
        """保存学习数据"""
        try:
            data = {
                'metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'total_experiences': len(self.experiences),
                    'total_patterns': len(self.patterns),
                    'format_version': '1.0'
                },
                'experiences': self.experiences,
                'patterns': self.patterns
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception:
            # 静默失败
            pass