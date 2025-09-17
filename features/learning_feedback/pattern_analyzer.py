#!/usr/bin/env python3
"""
Perfect21 模式分析器
===================

分析执行模式，识别成功和失败模式，提取可学习的知识
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, Counter

class PatternType(Enum):
    """模式类型"""
    SUCCESS_PATTERN = "success_pattern"
    FAILURE_PATTERN = "failure_pattern"
    PERFORMANCE_PATTERN = "performance_pattern"
    AGENT_USAGE_PATTERN = "agent_usage_pattern"
    TEMPORAL_PATTERN = "temporal_pattern"
    COMPLEXITY_PATTERN = "complexity_pattern"

@dataclass
class ExecutionPattern:
    """执行模式"""
    pattern_id: str
    pattern_type: PatternType
    name: str
    description: str
    confidence_score: float
    support_count: int
    conditions: Dict[str, Any]
    outcomes: Dict[str, Any]
    recommendations: List[str]
    examples: List[str]
    last_updated: str

class PatternAnalyzer:
    """模式分析器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.patterns_dir = self.project_root / ".perfect21" / "patterns"
        self.patterns_file = self.patterns_dir / "identified_patterns.json"

        self._ensure_directories()
        self._load_patterns()

        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # 模式识别阈值
        self.min_support_count = 3  # 最少支持数量
        self.min_confidence = 0.7   # 最小置信度

    def _ensure_directories(self):
        """确保目录结构存在"""
        self.patterns_dir.mkdir(parents=True, exist_ok=True)

    def _load_patterns(self):
        """加载已识别的模式"""
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                patterns_data = json.load(f)
                self.identified_patterns = [
                    self._dict_to_pattern(data) for data in patterns_data
                ]
        else:
            self.identified_patterns = []

    def _save_patterns(self):
        """保存识别的模式"""
        patterns_data = [self._pattern_to_dict(pattern) for pattern in self.identified_patterns]
        with open(self.patterns_file, 'w', encoding='utf-8') as f:
            json.dump(patterns_data, f, indent=2, ensure_ascii=False)

    def _dict_to_pattern(self, data: Dict) -> ExecutionPattern:
        """将字典转换为ExecutionPattern对象"""
        return ExecutionPattern(
            pattern_id=data['pattern_id'],
            pattern_type=PatternType(data['pattern_type']),
            name=data['name'],
            description=data['description'],
            confidence_score=data['confidence_score'],
            support_count=data['support_count'],
            conditions=data['conditions'],
            outcomes=data['outcomes'],
            recommendations=data['recommendations'],
            examples=data['examples'],
            last_updated=data['last_updated']
        )

    def _pattern_to_dict(self, pattern: ExecutionPattern) -> Dict:
        """将ExecutionPattern对象转换为字典"""
        return {
            'pattern_id': pattern.pattern_id,
            'pattern_type': pattern.pattern_type.value,
            'name': pattern.name,
            'description': pattern.description,
            'confidence_score': pattern.confidence_score,
            'support_count': pattern.support_count,
            'conditions': pattern.conditions,
            'outcomes': pattern.outcomes,
            'recommendations': pattern.recommendations,
            'examples': pattern.examples,
            'last_updated': pattern.last_updated
        }

    def analyze_execution_history(self, execution_history: List) -> List[ExecutionPattern]:
        """分析执行历史，识别模式"""
        new_patterns = []

        # 1. 分析成功模式
        success_patterns = self._analyze_success_patterns(execution_history)
        new_patterns.extend(success_patterns)

        # 2. 分析失败模式
        failure_patterns = self._analyze_failure_patterns(execution_history)
        new_patterns.extend(failure_patterns)

        # 3. 分析性能模式
        performance_patterns = self._analyze_performance_patterns(execution_history)
        new_patterns.extend(performance_patterns)

        # 4. 分析Agent使用模式
        agent_patterns = self._analyze_agent_usage_patterns(execution_history)
        new_patterns.extend(agent_patterns)

        # 5. 分析时间模式
        temporal_patterns = self._analyze_temporal_patterns(execution_history)
        new_patterns.extend(temporal_patterns)

        # 6. 分析复杂度模式
        complexity_patterns = self._analyze_complexity_patterns(execution_history)
        new_patterns.extend(complexity_patterns)

        # 更新已识别的模式
        self._update_patterns(new_patterns)

        return new_patterns

    def _analyze_success_patterns(self, execution_history: List) -> List[ExecutionPattern]:
        """分析成功模式"""
        patterns = []

        # 筛选成功的执行
        from .learning_engine import ExecutionStatus
        successful_executions = [
            exec_result for exec_result in execution_history
            if exec_result.status == ExecutionStatus.SUCCESS and exec_result.quality_score > 0.8
        ]

        if len(successful_executions) < self.min_support_count:
            return patterns

        # 按任务类型分组分析
        task_groups = defaultdict(list)
        for exec_result in successful_executions:
            task_type = exec_result.task_context.task_type
            task_groups[task_type].append(exec_result)

        for task_type, executions in task_groups.items():
            if len(executions) >= self.min_support_count:
                pattern = self._extract_success_pattern(task_type, executions)
                if pattern:
                    patterns.append(pattern)

        return patterns

    def _extract_success_pattern(self, task_type: str, executions: List) -> Optional[ExecutionPattern]:
        """提取成功模式"""

        # 分析共同特征
        common_agents = self._find_common_agents(executions)
        common_features = self._find_common_features(executions)

        # 计算平均指标
        avg_duration = np.mean([e.execution_metrics.duration_seconds for e in executions])
        avg_quality = np.mean([e.quality_score for e in executions])
        parallel_ratio = np.mean([e.execution_metrics.parallel_execution for e in executions])

        # 如果没有明显的共同特征，不创建模式
        if not common_agents and not common_features:
            return None

        pattern_id = f"success_{task_type}_{len(executions)}"

        conditions = {
            "task_type": task_type,
            "min_quality_score": 0.8,
            "common_agents": common_agents,
            "features": common_features
        }

        outcomes = {
            "avg_duration": round(avg_duration, 2),
            "avg_quality": round(avg_quality, 3),
            "parallel_ratio": round(parallel_ratio, 3),
            "success_rate": 1.0
        }

        recommendations = self._generate_success_recommendations(common_agents, common_features, outcomes)

        examples = [e.execution_id for e in executions[:3]]  # 前3个例子

        return ExecutionPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.SUCCESS_PATTERN,
            name=f"{task_type}高质量执行模式",
            description=f"针对{task_type}任务的高质量执行模式，平均质量分数{avg_quality:.2f}",
            confidence_score=self._calculate_confidence(len(executions), common_features),
            support_count=len(executions),
            conditions=conditions,
            outcomes=outcomes,
            recommendations=recommendations,
            examples=examples,
            last_updated=datetime.now().isoformat()
        )

    def _analyze_failure_patterns(self, execution_history: List) -> List[ExecutionPattern]:
        """分析失败模式"""
        patterns = []

        from .learning_engine import ExecutionStatus
        failed_executions = [
            exec_result for exec_result in execution_history
            if exec_result.status == ExecutionStatus.FAILURE or exec_result.quality_score < 0.3
        ]

        if len(failed_executions) < self.min_support_count:
            return patterns

        # 按错误类型分组
        error_groups = defaultdict(list)
        for exec_result in failed_executions:
            # 分析主要错误类型
            main_error = self._extract_main_error(exec_result.errors)
            error_groups[main_error].append(exec_result)

        for error_type, executions in error_groups.items():
            if len(executions) >= self.min_support_count:
                pattern = self._extract_failure_pattern(error_type, executions)
                if pattern:
                    patterns.append(pattern)

        return patterns

    def _extract_failure_pattern(self, error_type: str, executions: List) -> Optional[ExecutionPattern]:
        """提取失败模式"""

        # 分析失败特征
        common_agents = self._find_common_agents(executions)
        common_features = self._find_common_features(executions)

        # 计算平均指标
        avg_duration = np.mean([e.execution_metrics.duration_seconds for e in executions])
        avg_quality = np.mean([e.quality_score for e in executions])

        pattern_id = f"failure_{error_type}_{len(executions)}"

        conditions = {
            "error_type": error_type,
            "common_agents": common_agents,
            "features": common_features
        }

        outcomes = {
            "avg_duration": round(avg_duration, 2),
            "avg_quality": round(avg_quality, 3),
            "failure_rate": 1.0
        }

        recommendations = self._generate_failure_recommendations(error_type, common_features)

        examples = [e.execution_id for e in executions[:3]]

        return ExecutionPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.FAILURE_PATTERN,
            name=f"{error_type}失败模式",
            description=f"导致{error_type}错误的执行模式",
            confidence_score=self._calculate_confidence(len(executions), common_features),
            support_count=len(executions),
            conditions=conditions,
            outcomes=outcomes,
            recommendations=recommendations,
            examples=examples,
            last_updated=datetime.now().isoformat()
        )

    def _analyze_performance_patterns(self, execution_history: List) -> List[ExecutionPattern]:
        """分析性能模式"""
        patterns = []

        # 按性能分组
        fast_executions = [e for e in execution_history if e.execution_metrics.duration_seconds < 120]  # 2分钟内
        slow_executions = [e for e in execution_history if e.execution_metrics.duration_seconds > 600]  # 10分钟以上

        # 分析快速执行模式
        if len(fast_executions) >= self.min_support_count:
            fast_pattern = self._extract_performance_pattern("fast", fast_executions)
            if fast_pattern:
                patterns.append(fast_pattern)

        # 分析慢速执行模式
        if len(slow_executions) >= self.min_support_count:
            slow_pattern = self._extract_performance_pattern("slow", slow_executions)
            if slow_pattern:
                patterns.append(slow_pattern)

        return patterns

    def _extract_performance_pattern(self, performance_type: str, executions: List) -> Optional[ExecutionPattern]:
        """提取性能模式"""

        common_agents = self._find_common_agents(executions)
        common_features = self._find_common_features(executions)

        avg_duration = np.mean([e.execution_metrics.duration_seconds for e in executions])
        avg_quality = np.mean([e.quality_score for e in executions])
        parallel_ratio = np.mean([e.execution_metrics.parallel_execution for e in executions])

        pattern_id = f"performance_{performance_type}_{len(executions)}"

        conditions = {
            "performance_type": performance_type,
            "common_agents": common_agents,
            "features": common_features
        }

        outcomes = {
            "avg_duration": round(avg_duration, 2),
            "avg_quality": round(avg_quality, 3),
            "parallel_ratio": round(parallel_ratio, 3)
        }

        if performance_type == "fast":
            recommendations = [
                "维持并行执行策略",
                "优先使用已验证的高效Agent组合",
                "保持任务复杂度适中"
            ]
        else:
            recommendations = [
                "考虑拆分复杂任务",
                "启用并行执行",
                "优化Agent选择策略"
            ]

        examples = [e.execution_id for e in executions[:3]]

        return ExecutionPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.PERFORMANCE_PATTERN,
            name=f"{performance_type}执行性能模式",
            description=f"{performance_type}执行的典型模式，平均时间{avg_duration:.1f}秒",
            confidence_score=self._calculate_confidence(len(executions), common_features),
            support_count=len(executions),
            conditions=conditions,
            outcomes=outcomes,
            recommendations=recommendations,
            examples=examples,
            last_updated=datetime.now().isoformat()
        )

    def _analyze_agent_usage_patterns(self, execution_history: List) -> List[ExecutionPattern]:
        """分析Agent使用模式"""
        patterns = []

        # 分析Agent组合的效果
        agent_combinations = defaultdict(list)
        for exec_result in execution_history:
            agents_key = tuple(sorted(exec_result.execution_metrics.agents_used))
            agent_combinations[agents_key].append(exec_result)

        # 找出高频且效果好的组合
        for agents, executions in agent_combinations.items():
            if len(executions) >= self.min_support_count:
                avg_quality = np.mean([e.quality_score for e in executions])
                if avg_quality > 0.7:  # 高质量组合
                    pattern = self._extract_agent_pattern(agents, executions)
                    if pattern:
                        patterns.append(pattern)

        return patterns

    def _extract_agent_pattern(self, agents: Tuple[str, ...], executions: List) -> Optional[ExecutionPattern]:
        """提取Agent使用模式"""

        avg_duration = np.mean([e.execution_metrics.duration_seconds for e in executions])
        avg_quality = np.mean([e.quality_score for e in executions])

        # 分析这个组合适用的任务类型
        task_types = [e.task_context.task_type for e in executions]
        most_common_task = Counter(task_types).most_common(1)[0][0]

        pattern_id = f"agent_combo_{'_'.join(agents)}_{len(executions)}"

        conditions = {
            "agents": list(agents),
            "task_types": list(set(task_types)),
            "primary_task_type": most_common_task
        }

        outcomes = {
            "avg_duration": round(avg_duration, 2),
            "avg_quality": round(avg_quality, 3),
            "usage_count": len(executions)
        }

        recommendations = [
            f"优先用于{most_common_task}类型任务",
            f"期望质量分数: {avg_quality:.2f}",
            f"期望执行时间: {avg_duration:.1f}秒"
        ]

        examples = [e.execution_id for e in executions[:3]]

        return ExecutionPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.AGENT_USAGE_PATTERN,
            name=f"Agent组合: {', '.join(agents)}",
            description=f"高效Agent组合模式，适用于{most_common_task}",
            confidence_score=self._calculate_confidence(len(executions), conditions),
            support_count=len(executions),
            conditions=conditions,
            outcomes=outcomes,
            recommendations=recommendations,
            examples=examples,
            last_updated=datetime.now().isoformat()
        )

    def _analyze_temporal_patterns(self, execution_history: List) -> List[ExecutionPattern]:
        """分析时间模式"""
        patterns = []

        # 按时间段分组（工作时间 vs 非工作时间）
        work_hours_executions = []
        off_hours_executions = []

        for exec_result in execution_history:
            exec_time = datetime.fromisoformat(exec_result.execution_metrics.start_time.replace('Z', '+00:00'))
            hour = exec_time.hour

            if 9 <= hour <= 17:  # 工作时间
                work_hours_executions.append(exec_result)
            else:
                off_hours_executions.append(exec_result)

        # 分析工作时间模式
        if len(work_hours_executions) >= self.min_support_count:
            work_pattern = self._extract_temporal_pattern("work_hours", work_hours_executions)
            if work_pattern:
                patterns.append(work_pattern)

        # 分析非工作时间模式
        if len(off_hours_executions) >= self.min_support_count:
            off_pattern = self._extract_temporal_pattern("off_hours", off_hours_executions)
            if off_pattern:
                patterns.append(off_pattern)

        return patterns

    def _extract_temporal_pattern(self, time_type: str, executions: List) -> Optional[ExecutionPattern]:
        """提取时间模式"""

        avg_duration = np.mean([e.execution_metrics.duration_seconds for e in executions])
        avg_quality = np.mean([e.quality_score for e in executions])

        from .learning_engine import ExecutionStatus
        success_rate = len([e for e in executions if e.status == ExecutionStatus.SUCCESS]) / len(executions)

        pattern_id = f"temporal_{time_type}_{len(executions)}"

        conditions = {
            "time_type": time_type,
            "execution_count": len(executions)
        }

        outcomes = {
            "avg_duration": round(avg_duration, 2),
            "avg_quality": round(avg_quality, 3),
            "success_rate": round(success_rate, 3)
        }

        if time_type == "work_hours":
            recommendations = [
                "工作时间内执行效果良好",
                "可以进行复杂任务开发"
            ]
        else:
            recommendations = [
                "非工作时间执行模式",
                "适合后台处理任务"
            ]

        examples = [e.execution_id for e in executions[:3]]

        return ExecutionPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.TEMPORAL_PATTERN,
            name=f"{time_type}时间执行模式",
            description=f"{time_type}的执行特征模式",
            confidence_score=self._calculate_confidence(len(executions), conditions),
            support_count=len(executions),
            conditions=conditions,
            outcomes=outcomes,
            recommendations=recommendations,
            examples=examples,
            last_updated=datetime.now().isoformat()
        )

    def _analyze_complexity_patterns(self, execution_history: List) -> List[ExecutionPattern]:
        """分析复杂度模式"""
        patterns = []

        # 按复杂度分组
        from .learning_engine import TaskComplexity
        complexity_groups = defaultdict(list)
        for exec_result in execution_history:
            complexity = exec_result.task_context.complexity
            complexity_groups[complexity].append(exec_result)

        for complexity, executions in complexity_groups.items():
            if len(executions) >= self.min_support_count:
                pattern = self._extract_complexity_pattern(complexity, executions)
                if pattern:
                    patterns.append(pattern)

        return patterns

    def _extract_complexity_pattern(self, complexity, executions: List) -> Optional[ExecutionPattern]:
        """提取复杂度模式"""

        avg_duration = np.mean([e.execution_metrics.duration_seconds for e in executions])
        avg_quality = np.mean([e.quality_score for e in executions])
        avg_agents = np.mean([len(e.execution_metrics.agents_used) for e in executions])

        pattern_id = f"complexity_{complexity.value}_{len(executions)}"

        conditions = {
            "complexity": complexity.value,
            "execution_count": len(executions)
        }

        outcomes = {
            "avg_duration": round(avg_duration, 2),
            "avg_quality": round(avg_quality, 3),
            "avg_agents": round(avg_agents, 1)
        }

        recommendations = self._generate_complexity_recommendations(complexity, outcomes)

        examples = [e.execution_id for e in executions[:3]]

        return ExecutionPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.COMPLEXITY_PATTERN,
            name=f"{complexity.value}复杂度执行模式",
            description=f"{complexity.value}复杂度任务的执行特征",
            confidence_score=self._calculate_confidence(len(executions), conditions),
            support_count=len(executions),
            conditions=conditions,
            outcomes=outcomes,
            recommendations=recommendations,
            examples=examples,
            last_updated=datetime.now().isoformat()
        )

    # 辅助方法

    def _find_common_agents(self, executions: List) -> List[str]:
        """找出共同使用的Agents"""
        if not executions:
            return []

        agent_counter = Counter()
        for exec_result in executions:
            agent_counter.update(exec_result.execution_metrics.agents_used)

        # 找出在80%以上执行中出现的agents
        threshold = len(executions) * 0.8
        common_agents = [agent for agent, count in agent_counter.items() if count >= threshold]

        return common_agents

    def _find_common_features(self, executions: List) -> Dict[str, Any]:
        """找出共同特征"""
        if not executions:
            return {}

        features = {}

        # 检查并行执行比例
        parallel_count = sum(1 for e in executions if e.execution_metrics.parallel_execution)
        if parallel_count / len(executions) > 0.8:
            features["parallel_execution"] = True

        # 检查模板使用
        templates = [e.task_context.template_used for e in executions if e.task_context.template_used]
        if templates:
            template_counter = Counter(templates)
            most_common_template = template_counter.most_common(1)[0]
            if most_common_template[1] / len(executions) > 0.6:
                features["common_template"] = most_common_template[0]

        # 检查工作空间使用
        workspaces = [e.task_context.workspace_id for e in executions if e.task_context.workspace_id]
        if workspaces:
            workspace_counter = Counter(workspaces)
            if len(workspace_counter) == 1:  # 都使用同一个工作空间
                features["dedicated_workspace"] = True

        return features

    def _extract_main_error(self, errors: List[str]) -> str:
        """提取主要错误类型"""
        if not errors:
            return "unknown"

        # 简单的错误分类
        for error in errors:
            error_lower = error.lower()
            if "timeout" in error_lower:
                return "timeout"
            elif "conflict" in error_lower:
                return "conflict"
            elif "permission" in error_lower:
                return "permission"
            elif "not found" in error_lower:
                return "not_found"
            elif "syntax" in error_lower:
                return "syntax"

        return "general_error"

    def _calculate_confidence(self, support_count: int, features: Any) -> float:
        """计算模式置信度"""
        # 基础置信度基于支持数量
        base_confidence = min(support_count / 10, 1.0)

        # 特征复杂度调整
        feature_bonus = 0.0
        if isinstance(features, dict):
            feature_bonus = min(len(features) * 0.1, 0.3)
        elif isinstance(features, list):
            feature_bonus = min(len(features) * 0.05, 0.2)

        confidence = base_confidence + feature_bonus
        return min(confidence, 1.0)

    def _generate_success_recommendations(self, agents: List[str], features: Dict, outcomes: Dict) -> List[str]:
        """生成成功模式的建议"""
        recommendations = []

        if agents:
            recommendations.append(f"推荐使用Agent组合: {', '.join(agents)}")

        if features.get("parallel_execution"):
            recommendations.append("启用并行执行以提高效率")

        if features.get("common_template"):
            recommendations.append(f"使用模板: {features['common_template']}")

        if outcomes.get("avg_duration", 0) < 300:
            recommendations.append("保持当前执行策略以维持快速完成")

        return recommendations

    def _generate_failure_recommendations(self, error_type: str, features: Dict) -> List[str]:
        """生成失败模式的建议"""
        recommendations = []

        if error_type == "timeout":
            recommendations.extend([
                "增加执行超时时间",
                "考虑拆分复杂任务",
                "检查网络连接"
            ])
        elif error_type == "conflict":
            recommendations.extend([
                "使用独立工作空间",
                "检查Git状态",
                "避免并发修改同一文件"
            ])
        elif error_type == "permission":
            recommendations.extend([
                "检查文件权限",
                "确认工作目录访问权限"
            ])

        return recommendations

    def _generate_complexity_recommendations(self, complexity, outcomes: Dict) -> List[str]:
        """生成复杂度模式的建议"""
        recommendations = []

        from .learning_engine import TaskComplexity

        if complexity == TaskComplexity.TRIVIAL:
            recommendations.append("简单任务，可以快速单Agent处理")
        elif complexity == TaskComplexity.SIMPLE:
            recommendations.append("中等任务，建议使用2-3个Agent")
        elif complexity == TaskComplexity.MODERATE:
            recommendations.extend([
                "中等复杂度，建议并行执行",
                "使用3-5个专业Agent"
            ])
        elif complexity == TaskComplexity.COMPLEX:
            recommendations.extend([
                "复杂任务，必须使用并行执行",
                "分阶段执行，使用质量门控制"
            ])
        elif complexity == TaskComplexity.EXPERT:
            recommendations.extend([
                "专家级任务，需要详细规划",
                "使用多阶段工作流",
                "严格质量控制"
            ])

        return recommendations

    def _update_patterns(self, new_patterns: List[ExecutionPattern]):
        """更新模式库"""
        # 合并新模式
        for new_pattern in new_patterns:
            # 检查是否已存在相似模式
            existing_pattern = self._find_similar_pattern(new_pattern)
            if existing_pattern:
                # 更新现有模式
                self._merge_patterns(existing_pattern, new_pattern)
            else:
                # 添加新模式
                self.identified_patterns.append(new_pattern)

        # 保存更新的模式
        self._save_patterns()
        self.logger.info(f"更新了{len(new_patterns)}个模式")

    def _find_similar_pattern(self, pattern: ExecutionPattern) -> Optional[ExecutionPattern]:
        """查找相似的模式"""
        for existing in self.identified_patterns:
            if (existing.pattern_type == pattern.pattern_type and
                self._patterns_similar(existing, pattern)):
                return existing
        return None

    def _patterns_similar(self, pattern1: ExecutionPattern, pattern2: ExecutionPattern) -> bool:
        """判断两个模式是否相似"""
        # 简单的相似性检查
        return (pattern1.pattern_type == pattern2.pattern_type and
                pattern1.conditions.get("task_type") == pattern2.conditions.get("task_type"))

    def _merge_patterns(self, existing: ExecutionPattern, new: ExecutionPattern):
        """合并模式"""
        # 更新支持数量
        existing.support_count += new.support_count

        # 更新置信度（取平均）
        existing.confidence_score = (existing.confidence_score + new.confidence_score) / 2

        # 合并示例
        existing.examples.extend(new.examples)
        existing.examples = existing.examples[:5]  # 保持最多5个示例

        # 更新时间
        existing.last_updated = datetime.now().isoformat()

    def get_applicable_patterns(self, task_context: Dict[str, Any]) -> List[ExecutionPattern]:
        """获取适用的模式"""
        applicable = []

        for pattern in self.identified_patterns:
            if self._pattern_applies(pattern, task_context):
                applicable.append(pattern)

        # 按置信度排序
        applicable.sort(key=lambda p: p.confidence_score, reverse=True)
        return applicable

    def _pattern_applies(self, pattern: ExecutionPattern, task_context: Dict[str, Any]) -> bool:
        """检查模式是否适用于给定上下文"""
        conditions = pattern.conditions

        # 检查任务类型
        if "task_type" in conditions:
            if conditions["task_type"] != task_context.get("task_type"):
                return False

        # 检查复杂度
        if "complexity" in conditions:
            if conditions["complexity"] != task_context.get("complexity"):
                return False

        return True

    def get_pattern_summary(self) -> Dict[str, Any]:
        """获取模式摘要"""
        if not self.identified_patterns:
            return {"message": "暂无识别的模式"}

        type_counts = Counter(p.pattern_type.value for p in self.identified_patterns)
        avg_confidence = np.mean([p.confidence_score for p in self.identified_patterns])
        total_support = sum(p.support_count for p in self.identified_patterns)

        # 最有价值的模式
        top_patterns = sorted(
            self.identified_patterns,
            key=lambda p: p.confidence_score * p.support_count,
            reverse=True
        )[:5]

        return {
            "总模式数": len(self.identified_patterns),
            "按类型统计": dict(type_counts),
            "平均置信度": f"{avg_confidence:.3f}",
            "总支持数": total_support,
            "最有价值模式": [
                {
                    "名称": p.name,
                    "类型": p.pattern_type.value,
                    "置信度": p.confidence_score,
                    "支持数": p.support_count
                }
                for p in top_patterns
            ]
        }