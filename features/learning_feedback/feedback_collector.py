#!/usr/bin/env python3
"""
Perfect21 反馈收集器
===================

收集用户反馈和系统执行反馈，为学习引擎提供数据
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import logging

class FeedbackType(Enum):
    """反馈类型"""
    USER_SATISFACTION = "user_satisfaction"      # 用户满意度
    EXECUTION_QUALITY = "execution_quality"      # 执行质量
    PERFORMANCE_METRIC = "performance_metric"    # 性能指标
    ERROR_REPORT = "error_report"                # 错误报告
    SUGGESTION = "suggestion"                    # 改进建议
    BUG_REPORT = "bug_report"                   # Bug报告

class FeedbackSeverity(Enum):
    """反馈严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Feedback:
    """反馈数据结构"""
    feedback_id: str
    feedback_type: FeedbackType
    severity: FeedbackSeverity
    source: str  # 'user', 'system', 'agent'
    execution_id: Optional[str]
    content: str
    metadata: Dict[str, Any]
    timestamp: str
    processed: bool = False

class FeedbackCollector:
    """反馈收集器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.feedback_dir = self.project_root / ".perfect21" / "feedback"
        self.feedback_file = self.feedback_dir / "feedback_data.json"
        self.user_preferences_file = self.feedback_dir / "user_preferences.json"

        self._ensure_directories()
        self._load_data()

        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # 反馈回调函数
        self.feedback_callbacks: List[Callable[[Feedback], None]] = []

    def _ensure_directories(self):
        """确保目录结构存在"""
        self.feedback_dir.mkdir(parents=True, exist_ok=True)

    def _load_data(self):
        """加载反馈数据"""
        # 反馈数据
        if self.feedback_file.exists():
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)
                self.feedback_history = [
                    self._dict_to_feedback(data) for data in feedback_data
                ]
        else:
            self.feedback_history = []

        # 用户偏好
        if self.user_preferences_file.exists():
            with open(self.user_preferences_file, 'r', encoding='utf-8') as f:
                self.user_preferences = json.load(f)
        else:
            self.user_preferences = {
                "preferred_agents": [],
                "preferred_templates": [],
                "preferred_execution_style": "balanced",  # fast, balanced, quality
                "feedback_frequency": "normal",  # minimal, normal, detailed
                "auto_feedback": True,
                "quality_threshold": 0.7,
                "performance_threshold": 300  # 秒
            }

    def _save_data(self):
        """保存反馈数据"""
        # 反馈数据
        feedback_data = [self._feedback_to_dict(feedback) for feedback in self.feedback_history]
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)

        # 用户偏好
        with open(self.user_preferences_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_preferences, f, indent=2, ensure_ascii=False)

    def _dict_to_feedback(self, data: Dict) -> Feedback:
        """将字典转换为Feedback对象"""
        return Feedback(
            feedback_id=data['feedback_id'],
            feedback_type=FeedbackType(data['feedback_type']),
            severity=FeedbackSeverity(data['severity']),
            source=data['source'],
            execution_id=data.get('execution_id'),
            content=data['content'],
            metadata=data['metadata'],
            timestamp=data['timestamp'],
            processed=data.get('processed', False)
        )

    def _feedback_to_dict(self, feedback: Feedback) -> Dict:
        """将Feedback对象转换为字典"""
        return {
            'feedback_id': feedback.feedback_id,
            'feedback_type': feedback.feedback_type.value,
            'severity': feedback.severity.value,
            'source': feedback.source,
            'execution_id': feedback.execution_id,
            'content': feedback.content,
            'metadata': feedback.metadata,
            'timestamp': feedback.timestamp,
            'processed': feedback.processed
        }

    def register_callback(self, callback: Callable[[Feedback], None]):
        """注册反馈回调函数"""
        self.feedback_callbacks.append(callback)

    def collect_user_feedback(
        self,
        execution_id: str,
        satisfaction_score: float,
        feedback_text: Optional[str] = None,
        improvement_suggestions: Optional[List[str]] = None
    ) -> str:
        """收集用户反馈"""

        feedback_id = f"user_{execution_id}_{int(time.time())}"

        # 确定严重程度
        if satisfaction_score < 0.3:
            severity = FeedbackSeverity.HIGH
        elif satisfaction_score < 0.6:
            severity = FeedbackSeverity.MEDIUM
        else:
            severity = FeedbackSeverity.LOW

        metadata = {
            "satisfaction_score": satisfaction_score,
            "improvement_suggestions": improvement_suggestions or [],
            "collection_method": "explicit"
        }

        feedback = Feedback(
            feedback_id=feedback_id,
            feedback_type=FeedbackType.USER_SATISFACTION,
            severity=severity,
            source="user",
            execution_id=execution_id,
            content=feedback_text or f"用户满意度评分: {satisfaction_score}",
            metadata=metadata,
            timestamp=datetime.now().isoformat()
        )

        self._add_feedback(feedback)
        return feedback_id

    def collect_execution_feedback(
        self,
        execution_id: str,
        quality_score: float,
        performance_metrics: Dict[str, Any],
        errors: List[str],
        warnings: List[str]
    ) -> str:
        """收集执行反馈"""

        feedback_id = f"exec_{execution_id}_{int(time.time())}"

        # 确定严重程度
        if errors or quality_score < 0.3:
            severity = FeedbackSeverity.HIGH
        elif warnings or quality_score < 0.6:
            severity = FeedbackSeverity.MEDIUM
        else:
            severity = FeedbackSeverity.LOW

        metadata = {
            "quality_score": quality_score,
            "performance_metrics": performance_metrics,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "auto_collected": True
        }

        content = f"执行质量评分: {quality_score}"
        if errors:
            content += f", 错误数量: {len(errors)}"
        if warnings:
            content += f", 警告数量: {len(warnings)}"

        feedback = Feedback(
            feedback_id=feedback_id,
            feedback_type=FeedbackType.EXECUTION_QUALITY,
            severity=severity,
            source="system",
            execution_id=execution_id,
            content=content,
            metadata=metadata,
            timestamp=datetime.now().isoformat()
        )

        self._add_feedback(feedback)
        return feedback_id

    def collect_performance_feedback(
        self,
        execution_id: str,
        duration_seconds: float,
        token_usage: int,
        agents_used: List[str],
        parallel_execution: bool
    ) -> str:
        """收集性能反馈"""

        feedback_id = f"perf_{execution_id}_{int(time.time())}"

        # 根据性能阈值确定严重程度
        performance_threshold = self.user_preferences.get("performance_threshold", 300)
        if duration_seconds > performance_threshold * 2:
            severity = FeedbackSeverity.HIGH
        elif duration_seconds > performance_threshold:
            severity = FeedbackSeverity.MEDIUM
        else:
            severity = FeedbackSeverity.LOW

        metadata = {
            "duration_seconds": duration_seconds,
            "token_usage": token_usage,
            "agents_used": agents_used,
            "parallel_execution": parallel_execution,
            "efficiency_score": self._calculate_efficiency_score(duration_seconds, token_usage, len(agents_used))
        }

        content = f"执行时间: {duration_seconds:.1f}秒, Token使用: {token_usage}, Agents: {len(agents_used)}"

        feedback = Feedback(
            feedback_id=feedback_id,
            feedback_type=FeedbackType.PERFORMANCE_METRIC,
            severity=severity,
            source="system",
            execution_id=execution_id,
            content=content,
            metadata=metadata,
            timestamp=datetime.now().isoformat()
        )

        self._add_feedback(feedback)
        return feedback_id

    def collect_error_feedback(
        self,
        execution_id: Optional[str],
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """收集错误反馈"""

        feedback_id = f"error_{int(time.time())}"

        # 根据错误类型确定严重程度
        critical_errors = ["timeout", "crash", "data_loss", "security"]
        if any(critical in error_type.lower() for critical in critical_errors):
            severity = FeedbackSeverity.CRITICAL
        else:
            severity = FeedbackSeverity.HIGH

        metadata = {
            "error_type": error_type,
            "stack_trace": stack_trace,
            "context": context or {},
            "auto_collected": True
        }

        feedback = Feedback(
            feedback_id=feedback_id,
            feedback_type=FeedbackType.ERROR_REPORT,
            severity=severity,
            source="system",
            execution_id=execution_id,
            content=f"{error_type}: {error_message}",
            metadata=metadata,
            timestamp=datetime.now().isoformat()
        )

        self._add_feedback(feedback)
        return feedback_id

    def collect_suggestion_feedback(
        self,
        suggestion_text: str,
        category: str,
        priority: str = "medium",
        execution_id: Optional[str] = None
    ) -> str:
        """收集改进建议反馈"""

        feedback_id = f"suggestion_{int(time.time())}"

        severity_map = {
            "low": FeedbackSeverity.LOW,
            "medium": FeedbackSeverity.MEDIUM,
            "high": FeedbackSeverity.HIGH,
            "critical": FeedbackSeverity.CRITICAL
        }
        severity = severity_map.get(priority.lower(), FeedbackSeverity.MEDIUM)

        metadata = {
            "category": category,
            "priority": priority,
            "source_type": "user_suggestion"
        }

        feedback = Feedback(
            feedback_id=feedback_id,
            feedback_type=FeedbackType.SUGGESTION,
            severity=severity,
            source="user",
            execution_id=execution_id,
            content=suggestion_text,
            metadata=metadata,
            timestamp=datetime.now().isoformat()
        )

        self._add_feedback(feedback)
        return feedback_id

    def _add_feedback(self, feedback: Feedback):
        """添加反馈到历史记录"""
        self.feedback_history.append(feedback)

        # 保持历史记录在合理范围内
        if len(self.feedback_history) > 1000:
            self.feedback_history = self.feedback_history[-1000:]

        # 触发回调
        for callback in self.feedback_callbacks:
            try:
                callback(feedback)
            except Exception as e:
                self.logger.error(f"反馈回调执行失败: {e}")

        self._save_data()
        self.logger.info(f"收集反馈: {feedback.feedback_id}")

    def _calculate_efficiency_score(self, duration: float, tokens: int, agent_count: int) -> float:
        """计算效率分数"""
        # 基础分数
        base_score = 1.0

        # 时间效率 (目标: 5分钟内)
        time_efficiency = max(0.1, min(1.0, 300 / max(duration, 30)))

        # Token效率 (目标: 1000 tokens内)
        token_efficiency = max(0.1, min(1.0, 1000 / max(tokens, 100)))

        # Agent使用效率 (目标: 3个agents内)
        agent_efficiency = max(0.1, min(1.0, 3 / max(agent_count, 1)))

        # 综合效率分数
        efficiency_score = (time_efficiency * 0.4 + token_efficiency * 0.3 + agent_efficiency * 0.3) * base_score

        return round(efficiency_score, 3)

    def update_user_preferences(self, preferences: Dict[str, Any]):
        """更新用户偏好"""
        self.user_preferences.update(preferences)
        self._save_data()
        self.logger.info("用户偏好已更新")

    def get_feedback_summary(self, days: int = 30) -> Dict[str, Any]:
        """获取反馈摘要"""

        cutoff_date = datetime.now() - timedelta(days=days)
        recent_feedback = [
            fb for fb in self.feedback_history
            if datetime.fromisoformat(fb.timestamp.replace('Z', '+00:00')) > cutoff_date
        ]

        if not recent_feedback:
            return {"message": f"最近{days}天无反馈数据"}

        # 按类型统计
        type_counts = {}
        for fb in recent_feedback:
            type_counts[fb.feedback_type.value] = type_counts.get(fb.feedback_type.value, 0) + 1

        # 按严重程度统计
        severity_counts = {}
        for fb in recent_feedback:
            severity_counts[fb.severity.value] = severity_counts.get(fb.severity.value, 0) + 1

        # 用户满意度统计
        satisfaction_scores = []
        for fb in recent_feedback:
            if fb.feedback_type == FeedbackType.USER_SATISFACTION:
                score = fb.metadata.get("satisfaction_score")
                if score is not None:
                    satisfaction_scores.append(score)

        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else None

        # 质量分数统计
        quality_scores = []
        for fb in recent_feedback:
            if fb.feedback_type == FeedbackType.EXECUTION_QUALITY:
                score = fb.metadata.get("quality_score")
                if score is not None:
                    quality_scores.append(score)

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None

        # 最常见问题
        error_types = []
        for fb in recent_feedback:
            if fb.feedback_type == FeedbackType.ERROR_REPORT:
                error_types.append(fb.metadata.get("error_type", "unknown"))

        common_errors = {}
        for error_type in error_types:
            common_errors[error_type] = common_errors.get(error_type, 0) + 1

        top_errors = sorted(common_errors.items(), key=lambda x: x[1], reverse=True)[:3]

        # 改进建议统计
        suggestions = []
        for fb in recent_feedback:
            if fb.feedback_type == FeedbackType.SUGGESTION:
                suggestions.append({
                    "content": fb.content,
                    "category": fb.metadata.get("category", "general"),
                    "priority": fb.metadata.get("priority", "medium")
                })

        return {
            "时间范围": f"最近{days}天",
            "总反馈数": len(recent_feedback),
            "按类型统计": type_counts,
            "按严重程度统计": severity_counts,
            "平均用户满意度": f"{avg_satisfaction:.2f}" if avg_satisfaction else "无数据",
            "平均执行质量": f"{avg_quality:.2f}" if avg_quality else "无数据",
            "最常见错误": [f"{error}({count}次)" for error, count in top_errors],
            "改进建议数": len(suggestions),
            "用户偏好": self.user_preferences
        }

    def get_unprocessed_feedback(self) -> List[Feedback]:
        """获取未处理的反馈"""
        return [fb for fb in self.feedback_history if not fb.processed]

    def mark_feedback_processed(self, feedback_ids: List[str]):
        """标记反馈为已处理"""
        for feedback in self.feedback_history:
            if feedback.feedback_id in feedback_ids:
                feedback.processed = True

        self._save_data()
        self.logger.info(f"标记{len(feedback_ids)}条反馈为已处理")

    def generate_feedback_report(self, output_path: str) -> bool:
        """生成反馈报告"""
        try:
            summary = self.get_feedback_summary(30)
            unprocessed = self.get_unprocessed_feedback()

            report = {
                "报告生成时间": datetime.now().isoformat(),
                "反馈摘要": summary,
                "未处理反馈": [self._feedback_to_dict(fb) for fb in unprocessed],
                "用户偏好": self.user_preferences,
                "改进建议": self._generate_improvement_suggestions()
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            self.logger.info(f"反馈报告已生成: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"生成反馈报告失败: {e}")
            return False

    def _generate_improvement_suggestions(self) -> List[str]:
        """基于反馈生成改进建议"""
        suggestions = []

        # 分析最近的反馈
        recent_feedback = self.feedback_history[-50:]  # 最近50条反馈

        # 检查性能问题
        slow_executions = [
            fb for fb in recent_feedback
            if fb.feedback_type == FeedbackType.PERFORMANCE_METRIC
            and fb.metadata.get("duration_seconds", 0) > 300
        ]
        if len(slow_executions) > 5:
            suggestions.append("检测到多次执行时间较长，建议优化parallel execution策略")

        # 检查质量问题
        low_quality = [
            fb for fb in recent_feedback
            if fb.feedback_type == FeedbackType.EXECUTION_QUALITY
            and fb.metadata.get("quality_score", 1.0) < 0.5
        ]
        if len(low_quality) > 3:
            suggestions.append("检测到质量分数偏低，建议加强quality gates检查")

        # 检查用户满意度
        low_satisfaction = [
            fb for fb in recent_feedback
            if fb.feedback_type == FeedbackType.USER_SATISFACTION
            and fb.metadata.get("satisfaction_score", 1.0) < 0.6
        ]
        if len(low_satisfaction) > 2:
            suggestions.append("用户满意度需要改善，建议收集更详细的用户需求")

        # 检查错误模式
        error_feedback = [fb for fb in recent_feedback if fb.feedback_type == FeedbackType.ERROR_REPORT]
        if len(error_feedback) > 5:
            suggestions.append("错误频率较高，建议增强错误处理和预防机制")

        return suggestions

    def auto_collect_system_feedback(self, execution_result) -> List[str]:
        """自动收集系统反馈"""
        feedback_ids = []

        if not self.user_preferences.get("auto_feedback", True):
            return feedback_ids

        # 收集执行质量反馈
        quality_id = self.collect_execution_feedback(
            execution_result.execution_id,
            execution_result.quality_score,
            {
                "duration": execution_result.execution_metrics.duration_seconds,
                "agents_count": len(execution_result.execution_metrics.agents_used),
                "parallel": execution_result.execution_metrics.parallel_execution
            },
            execution_result.errors,
            execution_result.warnings
        )
        feedback_ids.append(quality_id)

        # 收集性能反馈
        perf_id = self.collect_performance_feedback(
            execution_result.execution_id,
            execution_result.execution_metrics.duration_seconds,
            execution_result.execution_metrics.token_usage,
            execution_result.execution_metrics.agents_used,
            execution_result.execution_metrics.parallel_execution
        )
        feedback_ids.append(perf_id)

        # 如果有错误，收集错误反馈
        for error in execution_result.errors:
            error_id = self.collect_error_feedback(
                execution_result.execution_id,
                "execution_error",
                error
            )
            feedback_ids.append(error_id)

        return feedback_ids