#!/usr/bin/env python3
"""
智能路由器
根据任务类型和实例可用性进行智能路由
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

from core.ai_pool import AIPool, AIInstanceType

logger = logging.getLogger("Router")

class TaskComplexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"

class TaskType(Enum):
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"

class IntelligentRouter:
    """智能任务路由器"""

    def __init__(self, ai_pool: AIPool):
        """初始化路由器"""
        self.ai_pool = ai_pool
        self.task_patterns = self._initialize_task_patterns()
        self.performance_history: Dict[str, List[float]] = {}
        logger.info("智能路由器初始化完成")

    def _initialize_task_patterns(self) -> Dict[TaskType, List[str]]:
        """初始化任务模式识别"""
        return {
            TaskType.CODE_GENERATION: [
                '创建', '实现', '开发', '生成', '写', '构建', '搭建',
                'create', 'implement', 'develop', 'generate', 'build', 'write'
            ],
            TaskType.CODE_REVIEW: [
                '审查', '检查', '评估', '分析代码', '代码质量',
                'review', 'check', 'evaluate', 'assess', 'code quality'
            ],
            TaskType.DEBUGGING: [
                '修复', '调试', '解决bug', '找错误', '排查',
                'debug', 'fix', 'solve', 'troubleshoot', 'bug'
            ],
            TaskType.REFACTORING: [
                '重构', '优化代码', '改进', '整理', '清理',
                'refactor', 'optimize code', 'improve', 'clean up'
            ],
            TaskType.TESTING: [
                '测试', '验证', 'test', 'verify', 'validate', '单元测试', '集成测试'
            ],
            TaskType.DOCUMENTATION: [
                '文档', '说明', '注释', 'documentation', 'comment', 'readme'
            ],
            TaskType.ANALYSIS: [
                '分析', '理解', '解读', 'analyze', 'understand', 'explain'
            ],
            TaskType.OPTIMIZATION: [
                '优化', '性能', '加速', 'optimize', 'performance', 'speed up'
            ]
        }

    def analyze_task(self, task_description: str) -> Tuple[TaskType, TaskComplexity]:
        """分析任务类型和复杂度"""
        task_lower = task_description.lower()

        # 识别任务类型
        task_type = TaskType.CODE_GENERATION  # 默认
        max_matches = 0

        for t_type, patterns in self.task_patterns.items():
            matches = sum(1 for pattern in patterns if pattern in task_lower)
            if matches > max_matches:
                max_matches = matches
                task_type = t_type

        # 评估复杂度
        complexity_indicators = {
            'simple': ['简单', '基础', 'hello world', '示例', 'simple', 'basic', 'example'],
            'complex': ['复杂', '系统', '架构', '微服务', '数据库', '复合', 'complex', 'system',
                       'architecture', 'microservice', 'database', 'enterprise']
        }

        complexity = TaskComplexity.MEDIUM  # 默认中等

        # 检查简单任务标记
        if any(indicator in task_lower for indicator in complexity_indicators['simple']):
            complexity = TaskComplexity.SIMPLE
        # 检查复杂任务标记
        elif any(indicator in task_lower for indicator in complexity_indicators['complex']):
            complexity = TaskComplexity.COMPLEX

        # 根据任务描述长度调整复杂度
        if len(task_description) > 200:
            if complexity == TaskComplexity.SIMPLE:
                complexity = TaskComplexity.MEDIUM
            elif complexity == TaskComplexity.MEDIUM:
                complexity = TaskComplexity.COMPLEX

        logger.info(f"任务分析结果: {task_type.value} - {complexity.value}")
        return task_type, complexity

    def recommend_ai_instance(self, task_type: TaskType, complexity: TaskComplexity,
                             workspace: str = None) -> Optional[AIInstanceType]:
        """根据任务推荐AI实例类型"""

        # Claude优势领域
        claude_preferred = [
            TaskType.CODE_REVIEW,
            TaskType.ANALYSIS,
            TaskType.REFACTORING,
            TaskType.DOCUMENTATION
        ]

        # Codex优势领域 (暂时禁用，优先使用Claude)
        codex_preferred = [
            # TaskType.CODE_GENERATION,
            # TaskType.TESTING,
            # TaskType.DEBUGGING
        ]

        # 基于任务类型的推荐 (暂时全部使用Claude)
        if task_type in claude_preferred:
            preferred = AIInstanceType.CLAUDE
            fallback = AIInstanceType.CLAUDE
        elif task_type in codex_preferred:
            preferred = AIInstanceType.CODEX
            fallback = AIInstanceType.CLAUDE
        else:
            # 暂时全部使用Claude
            preferred = AIInstanceType.CLAUDE
            fallback = AIInstanceType.CLAUDE

        # 检查推荐实例的可用性
        preferred_instance = self.ai_pool.get_available_instance(preferred, workspace)
        if preferred_instance:
            return preferred

        # 尝试备选
        fallback_instance = self.ai_pool.get_available_instance(fallback, workspace)
        if fallback_instance:
            return fallback

        logger.warning(f"无可用AI实例用于任务类型: {task_type.value}")
        return None

    def route_task(self, task_description: str, workspace: str = None) -> Dict[str, Any]:
        """路由任务到合适的AI实例"""

        # 分析任务
        task_type, complexity = self.analyze_task(task_description)

        # 推荐AI类型
        recommended_ai = self.recommend_ai_instance(task_type, complexity, workspace)

        if not recommended_ai:
            return {
                "success": False,
                "error": "没有可用的AI实例",
                "task_type": task_type.value,
                "complexity": complexity.value
            }

        # 获取实例
        instance_id = self.ai_pool.get_available_instance(recommended_ai, workspace)

        if not instance_id:
            return {
                "success": False,
                "error": f"无法获取{recommended_ai.value}实例",
                "task_type": task_type.value,
                "complexity": complexity.value
            }

        # 分配任务
        success = self.ai_pool.assign_task(instance_id, task_description)

        if success:
            return {
                "success": True,
                "instance_id": instance_id,
                "ai_type": recommended_ai.value,
                "task_type": task_type.value,
                "complexity": complexity.value,
                "workspace": workspace
            }
        else:
            return {
                "success": False,
                "error": "任务分配失败",
                "instance_id": instance_id
            }

    def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        pool_status = self.ai_pool.get_pool_status()

        return {
            "pool_status": pool_status,
            "performance_history": {
                ai_type: {
                    "total_tasks": len(times),
                    "avg_time": sum(times) / len(times) if times else 0,
                    "min_time": min(times) if times else 0,
                    "max_time": max(times) if times else 0
                }
                for ai_type, times in self.performance_history.items()
            },
            "routing_preferences": {
                "claude_preferred": [t.value for t in [
                    TaskType.CODE_REVIEW, TaskType.ANALYSIS,
                    TaskType.REFACTORING, TaskType.DOCUMENTATION
                ]],
                "codex_preferred": [t.value for t in [
                    TaskType.CODE_GENERATION, TaskType.TESTING, TaskType.DEBUGGING
                ]]
            }
        }

    def record_task_performance(self, ai_type: str, execution_time: float):
        """记录任务执行性能"""
        if ai_type not in self.performance_history:
            self.performance_history[ai_type] = []

        self.performance_history[ai_type].append(execution_time)

        # 保持历史记录在合理范围内
        if len(self.performance_history[ai_type]) > 100:
            self.performance_history[ai_type] = self.performance_history[ai_type][-50:]

        logger.debug(f"记录性能: {ai_type} - {execution_time:.2f}秒")