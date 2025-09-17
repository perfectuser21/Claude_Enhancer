"""
Perfect21 学习反馈循环系统
=========================

从每次执行中学习，持续改进Perfect21的智能决策能力
"""

from .learning_engine import LearningEngine, LearningData, ExecutionResult
from .feedback_collector import FeedbackCollector, FeedbackType
from .pattern_analyzer import PatternAnalyzer, ExecutionPattern
from .improvement_suggester import ImprovementSuggester

__all__ = [
    'LearningEngine', 'LearningData', 'ExecutionResult',
    'FeedbackCollector', 'FeedbackType',
    'PatternAnalyzer', 'ExecutionPattern',
    'ImprovementSuggester'
]