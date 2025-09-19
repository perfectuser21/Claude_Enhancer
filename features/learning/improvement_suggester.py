#!/usr/bin/env python3
"""
Perfect21 改进建议器
===================

基于学习到的模式和反馈数据，生成具体的改进建议
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import Counter

class ImprovementCategory(Enum):
    """改进类别"""
    PERFORMANCE = "performance"           # 性能改进
    QUALITY = "quality"                  # 质量改进
    RELIABILITY = "reliability"          # 可靠性改进
    USER_EXPERIENCE = "user_experience"   # 用户体验改进
    AGENT_OPTIMIZATION = "agent_optimization"  # Agent优化
    WORKFLOW = "workflow"                # 工作流改进
    CONFIGURATION = "configuration"      # 配置优化

class Priority(Enum):
    """优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ImprovementSuggestion:
    """改进建议"""
    suggestion_id: str
    category: ImprovementCategory
    priority: Priority
    title: str
    description: str
    impact_analysis: Dict[str, Any]
    implementation_steps: List[str]
    success_metrics: List[str]
    related_patterns: List[str]
    evidence: List[str]
    effort_estimate: str  # "low", "medium", "high"
    created_at: str
    status: str = "proposed"  # proposed, in_progress, completed, rejected

class ImprovementSuggester:
    """改进建议器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.suggestions_dir = self.project_root / ".perfect21" / "improvements"
        self.suggestions_file = self.suggestions_dir / "suggestions.json"
        self.implemented_file = self.suggestions_dir / "implemented.json"

        self._ensure_directories()
        self._load_suggestions()

        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _ensure_directories(self):
        """确保目录结构存在"""
        self.suggestions_dir.mkdir(parents=True, exist_ok=True)

    def _load_suggestions(self):
        """加载建议数据"""
        # 活跃建议
        if self.suggestions_file.exists():
            with open(self.suggestions_file, 'r', encoding='utf-8') as f:
                suggestions_data = json.load(f)
                self.active_suggestions = [
                    self._dict_to_suggestion(data) for data in suggestions_data
                ]
        else:
            self.active_suggestions = []

        # 已实施建议
        if self.implemented_file.exists():
            with open(self.implemented_file, 'r', encoding='utf-8') as f:
                implemented_data = json.load(f)
                self.implemented_suggestions = [
                    self._dict_to_suggestion(data) for data in implemented_data
                ]
        else:
            self.implemented_suggestions = []

    def _save_suggestions(self):
        """保存建议数据"""
        # 活跃建议
        suggestions_data = [self._suggestion_to_dict(s) for s in self.active_suggestions]
        with open(self.suggestions_file, 'w', encoding='utf-8') as f:
            json.dump(suggestions_data, f, indent=2, ensure_ascii=False)

        # 已实施建议
        implemented_data = [self._suggestion_to_dict(s) for s in self.implemented_suggestions]
        with open(self.implemented_file, 'w', encoding='utf-8') as f:
            json.dump(implemented_data, f, indent=2, ensure_ascii=False)

    def _dict_to_suggestion(self, data: Dict) -> ImprovementSuggestion:
        """将字典转换为ImprovementSuggestion对象"""
        return ImprovementSuggestion(
            suggestion_id=data['suggestion_id'],
            category=ImprovementCategory(data['category']),
            priority=Priority(data['priority']),
            title=data['title'],
            description=data['description'],
            impact_analysis=data['impact_analysis'],
            implementation_steps=data['implementation_steps'],
            success_metrics=data['success_metrics'],
            related_patterns=data['related_patterns'],
            evidence=data['evidence'],
            effort_estimate=data['effort_estimate'],
            created_at=data['created_at'],
            status=data.get('status', 'proposed')
        )

    def _suggestion_to_dict(self, suggestion: ImprovementSuggestion) -> Dict:
        """将ImprovementSuggestion对象转换为字典"""
        return {
            'suggestion_id': suggestion.suggestion_id,
            'category': suggestion.category.value,
            'priority': suggestion.priority.value,
            'title': suggestion.title,
            'description': suggestion.description,
            'impact_analysis': suggestion.impact_analysis,
            'implementation_steps': suggestion.implementation_steps,
            'success_metrics': suggestion.success_metrics,
            'related_patterns': suggestion.related_patterns,
            'evidence': suggestion.evidence,
            'effort_estimate': suggestion.effort_estimate,
            'created_at': suggestion.created_at,
            'status': suggestion.status
        }

    def generate_suggestions(
        self,
        execution_history: List,
        feedback_data: List,
        patterns: List,
        knowledge_base: Dict[str, Any]
    ) -> List[ImprovementSuggestion]:
        """生成改进建议"""

        suggestions = []

        # 1. 基于性能数据的建议
        performance_suggestions = self._analyze_performance_issues(execution_history)
        suggestions.extend(performance_suggestions)

        # 2. 基于质量数据的建议
        quality_suggestions = self._analyze_quality_issues(execution_history, feedback_data)
        suggestions.extend(quality_suggestions)

        # 3. 基于用户反馈的建议
        feedback_suggestions = self._analyze_user_feedback(feedback_data)
        suggestions.extend(feedback_suggestions)

        # 4. 基于失败模式的建议
        failure_suggestions = self._analyze_failure_patterns(patterns)
        suggestions.extend(failure_suggestions)

        # 5. 基于Agent性能的建议
        agent_suggestions = self._analyze_agent_performance(knowledge_base)
        suggestions.extend(agent_suggestions)

        # 6. 基于工作流效率的建议
        workflow_suggestions = self._analyze_workflow_efficiency(execution_history, patterns)
        suggestions.extend(workflow_suggestions)

        # 去重和优先级排序
        unique_suggestions = self._deduplicate_suggestions(suggestions)
        prioritized_suggestions = self._prioritize_suggestions(unique_suggestions)

        # 更新建议列表
        self._update_suggestions(prioritized_suggestions)

        return prioritized_suggestions

    def _analyze_performance_issues(self, execution_history: List) -> List[ImprovementSuggestion]:
        """分析性能问题"""
        suggestions = []

        if not execution_history:
            return suggestions

        # 分析执行时间趋势
        recent_executions = execution_history[-50:]  # 最近50次执行
        durations = [e.execution_metrics.duration_seconds for e in recent_executions]
        avg_duration = sum(durations) / len(durations)

        # 如果平均执行时间超过5分钟
        if avg_duration > 300:
            suggestions.append(self._create_performance_suggestion(
                "optimize_execution_time",
                "优化执行时间",
                f"当前平均执行时间为{avg_duration:.1f}秒，建议优化",
                avg_duration,
                recent_executions
            ))

        # 分析并行执行使用率
        parallel_executions = [e for e in recent_executions if e.execution_metrics.parallel_execution]
        parallel_rate = len(parallel_executions) / len(recent_executions)

        if parallel_rate < 0.6:  # 并行执行率低于60%
            suggestions.append(self._create_parallel_suggestion(
                "increase_parallel_usage",
                "增加并行执行使用",
                f"当前并行执行率仅为{parallel_rate:.1%}，建议提高",
                parallel_rate,
                recent_executions
            ))

        # 分析Token使用效率
        token_usages = [e.execution_metrics.token_usage for e in recent_executions if e.execution_metrics.token_usage > 0]
        if token_usages:
            avg_tokens = sum(token_usages) / len(token_usages)
            if avg_tokens > 2000:  # Token使用量过高
                suggestions.append(self._create_token_suggestion(
                    "optimize_token_usage",
                    "优化Token使用",
                    f"平均Token使用量为{avg_tokens:.0f}，建议优化",
                    avg_tokens,
                    recent_executions
                ))

        return suggestions

    def _create_performance_suggestion(
        self,
        suggestion_id: str,
        title: str,
        description: str,
        avg_duration: float,
        executions: List
    ) -> ImprovementSuggestion:
        """创建性能改进建议"""

        # 分析慢执行的原因
        slow_executions = [e for e in executions if e.execution_metrics.duration_seconds > avg_duration * 1.5]

        # 分析慢执行的共同特征
        common_agents = self._find_common_agents_in_slow_executions(slow_executions)

        impact_analysis = {
            "current_avg_duration": avg_duration,
            "target_duration": 180,  # 目标3分钟
            "potential_time_savings": f"{avg_duration - 180:.1f}秒",
            "affected_executions": len(slow_executions)
        }

        implementation_steps = [
            "分析慢执行的具体原因",
            "识别性能瓶颈Agent或步骤",
            "优化Agent选择策略",
            "启用更多并行执行",
            "考虑任务分解策略"
        ]

        if common_agents:
            implementation_steps.append(f"特别关注以下Agent的性能: {', '.join(common_agents)}")

        success_metrics = [
            "平均执行时间降低至3分钟以内",
            "95%的执行在5分钟内完成",
            "用户满意度提升"
        ]

        evidence = [
            f"最近50次执行的平均时间: {avg_duration:.1f}秒",
            f"超过平均时间1.5倍的执行: {len(slow_executions)}次"
        ]

        return ImprovementSuggestion(
            suggestion_id=suggestion_id,
            category=ImprovementCategory.PERFORMANCE,
            priority=Priority.HIGH if avg_duration > 600 else Priority.MEDIUM,
            title=title,
            description=description,
            impact_analysis=impact_analysis,
            implementation_steps=implementation_steps,
            success_metrics=success_metrics,
            related_patterns=[],
            evidence=evidence,
            effort_estimate="medium",
            created_at=datetime.now().isoformat()
        )

    def _create_parallel_suggestion(
        self,
        suggestion_id: str,
        title: str,
        description: str,
        parallel_rate: float,
        executions: List
    ) -> ImprovementSuggestion:
        """创建并行执行建议"""

        sequential_executions = [e for e in executions if not e.execution_metrics.parallel_execution]

        impact_analysis = {
            "current_parallel_rate": f"{parallel_rate:.1%}",
            "target_parallel_rate": "80%",
            "potential_speedup": "20-40%",
            "sequential_executions": len(sequential_executions)
        }

        implementation_steps = [
            "分析顺序执行的任务类型",
            "识别可以并行化的任务",
            "更新任务分解策略",
            "优化Agent选择逻辑",
            "更新用户指导文档"
        ]

        success_metrics = [
            "并行执行率提升至80%以上",
            "平均执行时间减少20%",
            "复杂任务完成效率提升"
        ]

        evidence = [
            f"当前并行执行率: {parallel_rate:.1%}",
            f"顺序执行的次数: {len(sequential_executions)}",
            f"潜在可优化任务: {len(sequential_executions)}"
        ]

        return ImprovementSuggestion(
            suggestion_id=suggestion_id,
            category=ImprovementCategory.PERFORMANCE,
            priority=Priority.MEDIUM,
            title=title,
            description=description,
            impact_analysis=impact_analysis,
            implementation_steps=implementation_steps,
            success_metrics=success_metrics,
            related_patterns=[],
            evidence=evidence,
            effort_estimate="medium",
            created_at=datetime.now().isoformat()
        )

    def _create_token_suggestion(
        self,
        suggestion_id: str,
        title: str,
        description: str,
        avg_tokens: float,
        executions: List
    ) -> ImprovementSuggestion:
        """创建Token优化建议"""

        impact_analysis = {
            "current_avg_tokens": avg_tokens,
            "target_tokens": 1000,
            "potential_savings": f"{avg_tokens - 1000:.0f} tokens per execution",
            "cost_impact": "减少API调用成本"
        }

        implementation_steps = [
            "分析高Token使用的Agent和操作",
            "优化prompt设计",
            "减少不必要的上下文传递",
            "实施更智能的Agent选择",
            "考虑本地缓存策略"
        ]

        success_metrics = [
            "平均Token使用量降低至1000以下",
            "保持相同的输出质量",
            "降低运行成本"
        ]

        evidence = [
            f"平均Token使用量: {avg_tokens:.0f}",
            f"超过2000 Token的执行比例: {len([e for e in executions if e.execution_metrics.token_usage > 2000])/len(executions):.1%}"
        ]

        return ImprovementSuggestion(
            suggestion_id=suggestion_id,
            category=ImprovementCategory.PERFORMANCE,
            priority=Priority.MEDIUM,
            title=title,
            description=description,
            impact_analysis=impact_analysis,
            implementation_steps=implementation_steps,
            success_metrics=success_metrics,
            related_patterns=[],
            evidence=evidence,
            effort_estimate="low",
            created_at=datetime.now().isoformat()
        )

    def _analyze_quality_issues(self, execution_history: List, feedback_data: List) -> List[ImprovementSuggestion]:
        """分析质量问题"""
        suggestions = []

        if not execution_history:
            return suggestions

        # 分析质量分数趋势
        recent_executions = execution_history[-50:]
        quality_scores = [e.quality_score for e in recent_executions]
        avg_quality = sum(quality_scores) / len(quality_scores)

        if avg_quality < 0.7:  # 平均质量分数低于0.7
            suggestions.append(self._create_quality_suggestion(
                "improve_output_quality",
                "提升输出质量",
                f"当前平均质量分数为{avg_quality:.2f}，需要改进",
                avg_quality,
                recent_executions
            ))

        # 分析错误率
        executions_with_errors = [e for e in recent_executions if e.errors]
        error_rate = len(executions_with_errors) / len(recent_executions)

        if error_rate > 0.2:  # 错误率超过20%
            suggestions.append(self._create_error_reduction_suggestion(
                "reduce_error_rate",
                "降低错误率",
                f"当前错误率为{error_rate:.1%}，需要改进",
                error_rate,
                executions_with_errors
            ))

        return suggestions

    def _analyze_user_feedback(self, feedback_data: List) -> List[ImprovementSuggestion]:
        """分析用户反馈"""
        suggestions = []

        if not feedback_data:
            return suggestions

        from .feedback_collector import FeedbackType

        # 分析用户满意度
        satisfaction_feedback = [
            fb for fb in feedback_data
            if fb.feedback_type == FeedbackType.USER_SATISFACTION
        ]

        if satisfaction_feedback:
            avg_satisfaction = sum(
                fb.metadata.get("satisfaction_score", 0.5)
                for fb in satisfaction_feedback
            ) / len(satisfaction_feedback)

            if avg_satisfaction < 0.6:
                suggestions.append(self._create_user_experience_suggestion(
                    "improve_user_satisfaction",
                    "提升用户满意度",
                    f"当前用户满意度为{avg_satisfaction:.2f}，需要改进",
                    avg_satisfaction,
                    satisfaction_feedback
                ))

        # 分析用户建议
        user_suggestions = [
            fb for fb in feedback_data
            if fb.feedback_type == FeedbackType.SUGGESTION
        ]

        if user_suggestions:
            # 按类别统计用户建议
            suggestion_categories = Counter(
                fb.metadata.get("category", "general")
                for fb in user_suggestions
            )

            for category, count in suggestion_categories.most_common(3):
                suggestions.append(self._create_user_suggestion_response(
                    f"address_user_suggestions_{category}",
                    f"处理{category}类用户建议",
                    f"收到{count}条关于{category}的用户建议",
                    category,
                    count,
                    user_suggestions
                ))

        return suggestions

    def _analyze_failure_patterns(self, patterns: List) -> List[ImprovementSuggestion]:
        """分析失败模式"""
        suggestions = []

        from .pattern_analyzer import PatternType

        failure_patterns = [
            p for p in patterns
            if p.pattern_type == PatternType.FAILURE_PATTERN
        ]

        for pattern in failure_patterns:
            if pattern.support_count >= 3:  # 至少出现3次的失败模式
                suggestions.append(self._create_failure_pattern_suggestion(
                    f"fix_failure_pattern_{pattern.pattern_id}",
                    f"修复{pattern.name}",
                    pattern.description,
                    pattern
                ))

        return suggestions

    def _analyze_agent_performance(self, knowledge_base: Dict[str, Any]) -> List[ImprovementSuggestion]:
        """分析Agent性能"""
        suggestions = []

        agent_prefs = knowledge_base.get("agent_preferences", {})

        # 找出表现不佳的Agent
        poor_agents = []
        for agent, stats in agent_prefs.items():
            if (stats.get("success_rate", 1.0) < 0.6 or
                stats.get("avg_performance", 1.0) < 0.5):
                poor_agents.append((agent, stats))

        if poor_agents:
            suggestions.append(self._create_agent_optimization_suggestion(
                "optimize_poor_performing_agents",
                "优化表现不佳的Agent",
                f"发现{len(poor_agents)}个表现不佳的Agent",
                poor_agents
            ))

        return suggestions

    def _analyze_workflow_efficiency(self, execution_history: List, patterns: List) -> List[ImprovementSuggestion]:
        """分析工作流效率"""
        suggestions = []

        if not execution_history:
            return suggestions

        # 分析模板使用效果
        template_usage = Counter(
            e.task_context.template_used for e in execution_history
            if e.task_context.template_used
        )

        no_template_count = len([
            e for e in execution_history
            if not e.task_context.template_used
        ])

        if no_template_count > len(execution_history) * 0.5:  # 超过50%没使用模板
            suggestions.append(self._create_template_usage_suggestion(
                "increase_template_usage",
                "增加模板使用",
                f"{no_template_count}次执行未使用模板，可能影响效率",
                no_template_count,
                len(execution_history)
            ))

        return suggestions

    def _find_common_agents_in_slow_executions(self, slow_executions: List) -> List[str]:
        """找出慢执行中的常见Agent"""
        if not slow_executions:
            return []

        agent_counter = Counter()
        for exec_result in slow_executions:
            agent_counter.update(exec_result.execution_metrics.agents_used)

        # 找出在多次慢执行中出现的Agent
        threshold = max(2, len(slow_executions) * 0.5)
        common_agents = [
            agent for agent, count in agent_counter.items()
            if count >= threshold
        ]

        return common_agents

    def _create_quality_suggestion(
        self,
        suggestion_id: str,
        title: str,
        description: str,
        avg_quality: float,
        executions: List
    ) -> ImprovementSuggestion:
        """创建质量改进建议"""

        impact_analysis = {
            "current_avg_quality": avg_quality,
            "target_quality": 0.8,
            "quality_gap": f"{0.8 - avg_quality:.2f}",
            "affected_executions": len([e for e in executions if e.quality_score < 0.7])
        }

        implementation_steps = [
            "分析低质量输出的原因",
            "加强质量门检查",
            "优化Agent指令和Prompt",
            "增加输出验证步骤",
            "建立质量评估标准"
        ]

        success_metrics = [
            "平均质量分数提升至0.8以上",
            "低质量输出比例降低至10%以下",
            "用户满意度改善"
        ]

        evidence = [
            f"当前平均质量分数: {avg_quality:.2f}",
            f"低质量输出比例: {len([e for e in executions if e.quality_score < 0.5])/len(executions):.1%}"
        ]

        return ImprovementSuggestion(
            suggestion_id=suggestion_id,
            category=ImprovementCategory.QUALITY,
            priority=Priority.HIGH,
            title=title,
            description=description,
            impact_analysis=impact_analysis,
            implementation_steps=implementation_steps,
            success_metrics=success_metrics,
            related_patterns=[],
            evidence=evidence,
            effort_estimate="medium",
            created_at=datetime.now().isoformat()
        )

    def _create_error_reduction_suggestion(
        self,
        suggestion_id: str,
        title: str,
        description: str,
        error_rate: float,
        executions_with_errors: List
    ) -> ImprovementSuggestion:
        """创建错误减少建议"""

        # 分析常见错误类型
        all_errors = []
        for exec_result in executions_with_errors:
            all_errors.extend(exec_result.errors)

        common_error_types = self._categorize_errors(all_errors)

        impact_analysis = {
            "current_error_rate": f"{error_rate:.1%}",
            "target_error_rate": "10%",
            "executions_with_errors": len(executions_with_errors),
            "common_error_types": common_error_types
        }

        implementation_steps = [
            "分析常见错误类型和原因",
            "增强错误预防机制",
            "改进错误处理逻辑",
            "添加更多验证步骤",
            "建立错误监控和告警"
        ]

        for error_type in common_error_types[:3]:  # 前3种常见错误
            implementation_steps.append(f"特别关注{error_type}类错误的预防")

        success_metrics = [
            "错误率降低至10%以下",
            "减少重复性错误",
            "提高执行可靠性"
        ]

        evidence = [
            f"当前错误率: {error_rate:.1%}",
            f"最常见错误类型: {', '.join(common_error_types[:3])}"
        ]

        return ImprovementSuggestion(
            suggestion_id=suggestion_id,
            category=ImprovementCategory.RELIABILITY,
            priority=Priority.HIGH,
            title=title,
            description=description,
            impact_analysis=impact_analysis,
            implementation_steps=implementation_steps,
            success_metrics=success_metrics,
            related_patterns=[],
            evidence=evidence,
            effort_estimate="medium",
            created_at=datetime.now().isoformat()
        )

    def _categorize_errors(self, errors: List[str]) -> List[str]:
        """对错误进行分类"""
        error_categories = {
            "timeout": ["timeout", "超时"],
            "permission": ["permission", "权限", "access"],
            "network": ["network", "连接", "connection"],
            "syntax": ["syntax", "语法", "parse"],
            "not_found": ["not found", "找不到", "missing"],
            "conflict": ["conflict", "冲突", "collision"]
        }

        category_counts = Counter()

        for error in errors:
            error_lower = error.lower()
            for category, keywords in error_categories.items():
                if any(keyword in error_lower for keyword in keywords):
                    category_counts[category] += 1
                    break
            else:
                category_counts["other"] += 1

        return [category for category, _ in category_counts.most_common()]

    def _create_user_experience_suggestion(
        self,
        suggestion_id: str,
        title: str,
        description: str,
        avg_satisfaction: float,
        feedback_data: List
    ) -> ImprovementSuggestion:
        """创建用户体验改进建议"""

        # 分析不满意的原因
        low_satisfaction_feedback = [
            fb for fb in feedback_data
            if fb.metadata.get("satisfaction_score", 1.0) < 0.5
        ]

        suggestions_from_users = []
        for fb in low_satisfaction_feedback:
            user_suggestions = fb.metadata.get("improvement_suggestions", [])
            suggestions_from_users.extend(user_suggestions)

        impact_analysis = {
            "current_satisfaction": avg_satisfaction,
            "target_satisfaction": 0.8,
            "satisfaction_gap": f"{0.8 - avg_satisfaction:.2f}",
            "dissatisfied_users": len(low_satisfaction_feedback)
        }

        implementation_steps = [
            "深入分析用户不满意的具体原因",
            "改进用户界面和交互体验",
            "优化响应时间和质量",
            "增加用户指导和帮助",
            "建立更好的反馈机制"
        ]

        if suggestions_from_users:
            implementation_steps.append(f"特别关注用户提出的建议: {'; '.join(set(suggestions_from_users[:3]))}")

        success_metrics = [
            "用户满意度提升至0.8以上",
            "负面反馈减少50%",
            "用户活跃度提升"
        ]

        evidence = [
            f"当前平均满意度: {avg_satisfaction:.2f}",
            f"不满意用户比例: {len(low_satisfaction_feedback)/len(feedback_data):.1%}"
        ]

        return ImprovementSuggestion(
            suggestion_id=suggestion_id,
            category=ImprovementCategory.USER_EXPERIENCE,
            priority=Priority.HIGH,
            title=title,
            description=description,
            impact_analysis=impact_analysis,
            implementation_steps=implementation_steps,
            success_metrics=success_metrics,
            related_patterns=[],
            evidence=evidence,
            effort_estimate="high",
            created_at=datetime.now().isoformat()
        )

    def _create_user_suggestion_response(
        self,
        suggestion_id: str,
        title: str,
        description: str,
        category: str,
        count: int,
        user_suggestions: List
    ) -> ImprovementSuggestion:
        """创建用户建议响应"""

        # 提取该类别的具体建议
        category_suggestions = [
            fb.content for fb in user_suggestions
            if fb.metadata.get("category") == category
        ]

        impact_analysis = {
            "user_requests": count,
            "category": category,
            "priority_from_users": "medium",
            "user_engagement": "high"
        }

        implementation_steps = [
            f"详细分析{category}类用户建议",
            "评估实施的技术可行性",
            "制定实施计划和时间表",
            "与用户沟通进展情况",
            "收集实施后的用户反馈"
        ]

        success_metrics = [
            f"解决{category}类用户关注的问题",
            "提高用户参与度",
            "增强用户忠诚度"
        ]

        evidence = [
            f"收到{count}条{category}类建议",
            f"具体建议包括: {'; '.join(category_suggestions[:2])}"
        ]

        return ImprovementSuggestion(
            suggestion_id=suggestion_id,
            category=ImprovementCategory.USER_EXPERIENCE,
            priority=Priority.MEDIUM,
            title=title,
            description=description,
            impact_analysis=impact_analysis,
            implementation_steps=implementation_steps,
            success_metrics=success_metrics,
            related_patterns=[],
            evidence=evidence,
            effort_estimate="medium",
            created_at=datetime.now().isoformat()
        )

    def _create_failure_pattern_suggestion(
        self,
        suggestion_id: str,
        title: str,
        description: str,
        pattern
    ) -> ImprovementSuggestion:
        """创建失败模式修复建议"""

        impact_analysis = {
            "failure_count": pattern.support_count,
            "confidence": pattern.confidence_score,
            "pattern_type": pattern.pattern_type.value,
            "risk_level": "high" if pattern.support_count > 5 else "medium"
        }

        implementation_steps = [
            "深入分析失败模式的根本原因",
            "设计针对性的预防措施",
            "更新相关的检查和验证逻辑",
            "改进错误处理机制",
            "建立监控和早期预警"
        ]

        # 添加模式特定的建议
        implementation_steps.extend(pattern.recommendations)

        success_metrics = [
            f"消除或显著减少{pattern.name}",
            "相关错误率降低80%以上",
            "提高系统可靠性"
        ]

        evidence = [
            f"失败模式出现次数: {pattern.support_count}",
            f"模式置信度: {pattern.confidence_score:.2f}",
            f"相关条件: {pattern.conditions}"
        ]

        return ImprovementSuggestion(
            suggestion_id=suggestion_id,
            category=ImprovementCategory.RELIABILITY,
            priority=Priority.HIGH if pattern.support_count > 5 else Priority.MEDIUM,
            title=title,
            description=description,
            impact_analysis=impact_analysis,
            implementation_steps=implementation_steps,
            success_metrics=success_metrics,
            related_patterns=[pattern.pattern_id],
            evidence=evidence,
            effort_estimate="medium",
            created_at=datetime.now().isoformat()
        )

    def _create_agent_optimization_suggestion(
        self,
        suggestion_id: str,
        title: str,
        description: str,
        poor_agents: List[Tuple[str, Dict]]
    ) -> ImprovementSuggestion:
        """创建Agent优化建议"""

        agent_names = [agent for agent, _ in poor_agents]

        impact_analysis = {
            "affected_agents": len(poor_agents),
            "agent_list": agent_names,
            "performance_impact": "high",
            "optimization_potential": "significant"
        }

        implementation_steps = [
            "分析每个表现不佳Agent的具体问题",
            "评估是否需要替换Agent或调整使用方式",
            "优化Agent选择算法",
            "更新Agent性能评估标准",
            "建立Agent性能持续监控"
        ]

        for agent, stats in poor_agents[:3]:  # 前3个需要关注的Agent
            success_rate = stats.get("success_rate", 0)
            performance = stats.get("avg_performance", 0)
            implementation_steps.append(
                f"特别优化{agent} (成功率:{success_rate:.1%}, 性能:{performance:.2f})"
            )

        success_metrics = [
            "所有Agent成功率提升至70%以上",
            "平均Agent性能提升至0.7以上",
            "整体执行质量改善"
        ]

        evidence = [
            f"表现不佳的Agent数量: {len(poor_agents)}",
            f"影响的执行次数: {sum(stats.get('total_uses', 0) for _, stats in poor_agents)}"
        ]

        return ImprovementSuggestion(
            suggestion_id=suggestion_id,
            category=ImprovementCategory.AGENT_OPTIMIZATION,
            priority=Priority.MEDIUM,
            title=title,
            description=description,
            impact_analysis=impact_analysis,
            implementation_steps=implementation_steps,
            success_metrics=success_metrics,
            related_patterns=[],
            evidence=evidence,
            effort_estimate="medium",
            created_at=datetime.now().isoformat()
        )

    def _create_template_usage_suggestion(
        self,
        suggestion_id: str,
        title: str,
        description: str,
        no_template_count: int,
        total_executions: int
    ) -> ImprovementSuggestion:
        """创建模板使用建议"""

        no_template_rate = no_template_count / total_executions

        impact_analysis = {
            "no_template_executions": no_template_count,
            "no_template_rate": f"{no_template_rate:.1%}",
            "efficiency_loss": "potential",
            "standardization_gap": "high"
        }

        implementation_steps = [
            "分析未使用模板的任务类型",
            "为常见任务类型创建专用模板",
            "改进模板推荐算法",
            "增强模板易用性",
            "教育用户模板的价值"
        ]

        success_metrics = [
            "模板使用率提升至80%以上",
            "标准化任务执行效率提升",
            "减少重复性工作"
        ]

        evidence = [
            f"未使用模板的执行: {no_template_count}次",
            f"未使用模板的比例: {no_template_rate:.1%}"
        ]

        return ImprovementSuggestion(
            suggestion_id=suggestion_id,
            category=ImprovementCategory.WORKFLOW,
            priority=Priority.MEDIUM,
            title=title,
            description=description,
            impact_analysis=impact_analysis,
            implementation_steps=implementation_steps,
            success_metrics=success_metrics,
            related_patterns=[],
            evidence=evidence,
            effort_estimate="low",
            created_at=datetime.now().isoformat()
        )

    def _deduplicate_suggestions(self, suggestions: List[ImprovementSuggestion]) -> List[ImprovementSuggestion]:
        """去重建议"""
        seen_ids = set()
        unique_suggestions = []

        for suggestion in suggestions:
            if suggestion.suggestion_id not in seen_ids:
                seen_ids.add(suggestion.suggestion_id)
                unique_suggestions.append(suggestion)

        return unique_suggestions

    def _prioritize_suggestions(self, suggestions: List[ImprovementSuggestion]) -> List[ImprovementSuggestion]:
        """对建议进行优先级排序"""

        def priority_score(suggestion: ImprovementSuggestion) -> int:
            priority_values = {
                Priority.CRITICAL: 4,
                Priority.HIGH: 3,
                Priority.MEDIUM: 2,
                Priority.LOW: 1
            }

            base_score = priority_values[suggestion.priority]

            # 根据证据数量调整分数
            evidence_bonus = min(len(suggestion.evidence) * 0.1, 0.5)

            # 根据实施难度调整分数
            effort_penalty = {
                "low": 0,
                "medium": -0.2,
                "high": -0.5
            }.get(suggestion.effort_estimate, 0)

            return base_score + evidence_bonus + effort_penalty

        return sorted(suggestions, key=priority_score, reverse=True)

    def _update_suggestions(self, new_suggestions: List[ImprovementSuggestion]):
        """更新建议列表"""
        # 移除重复的建议
        existing_ids = {s.suggestion_id for s in self.active_suggestions}
        truly_new_suggestions = [
            s for s in new_suggestions
            if s.suggestion_id not in existing_ids
        ]

        # 添加新建议
        self.active_suggestions.extend(truly_new_suggestions)

        # 保存更新
        self._save_suggestions()

        if truly_new_suggestions:
            self.logger.info(f"生成了{len(truly_new_suggestions)}个新的改进建议")

    def get_suggestions_by_priority(self, priority: Priority) -> List[ImprovementSuggestion]:
        """按优先级获取建议"""
        return [s for s in self.active_suggestions if s.priority == priority]

    def get_suggestions_by_category(self, category: ImprovementCategory) -> List[ImprovementSuggestion]:
        """按类别获取建议"""
        return [s for s in self.active_suggestions if s.category == category]

    def mark_suggestion_implemented(self, suggestion_id: str, implementation_notes: str = ""):
        """标记建议为已实施"""
        for suggestion in self.active_suggestions:
            if suggestion.suggestion_id == suggestion_id:
                suggestion.status = "completed"
                # 移动到已实施列表
                self.implemented_suggestions.append(suggestion)
                self.active_suggestions.remove(suggestion)
                break

        self._save_suggestions()
        self.logger.info(f"建议 {suggestion_id} 已标记为已实施")

    def get_improvement_summary(self) -> Dict[str, Any]:
        """获取改进摘要"""
        if not self.active_suggestions:
            return {"message": "暂无改进建议"}

        # 按优先级统计
        priority_counts = Counter(s.priority.value for s in self.active_suggestions)

        # 按类别统计
        category_counts = Counter(s.category.value for s in self.active_suggestions)

        # 按实施难度统计
        effort_counts = Counter(s.effort_estimate for s in self.active_suggestions)

        # 最高优先级建议
        high_priority_suggestions = [
            s for s in self.active_suggestions
            if s.priority in [Priority.CRITICAL, Priority.HIGH]
        ]

        return {
            "活跃建议总数": len(self.active_suggestions),
            "已实施建议数": len(self.implemented_suggestions),
            "按优先级统计": dict(priority_counts),
            "按类别统计": dict(category_counts),
            "按实施难度统计": dict(effort_counts),
            "高优先级建议": [
                {
                    "标题": s.title,
                    "优先级": s.priority.value,
                    "类别": s.category.value,
                    "实施难度": s.effort_estimate
                }
                for s in high_priority_suggestions[:5]
            ],
            "最后更新": datetime.now().isoformat()
        }