#!/usr/bin/env python3
"""
Smart Reminder - 智能提示系统
根据上下文和执行历史提供智能提醒
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random

logger = logging.getLogger("SmartReminder")

class ReminderType:
    """提醒类型"""
    ENCOURAGEMENT = "encouragement"  # 鼓励
    WARNING = "warning"              # 警告
    CRITICAL = "critical"            # 严重警告
    GUIDANCE = "guidance"            # 指导
    TIPS = "tips"                    # 技巧

class SmartReminder:
    """
    智能提示系统 - 根据执行情况提供个性化提醒

    主要功能：
    1. 上下文感知提醒
    2. 学习历史模式
    3. 个性化建议
    4. 激励和警告
    """

    def __init__(self):
        self.reminder_history = []
        self.execution_patterns = {}
        self.improvement_suggestions = []
        self.success_patterns = []
        self.failure_patterns = []

        # 激励短语库
        self.encouragements = [
            "💪 加油！保持并行执行的好习惯！",
            "🌟 太棒了！继续保持高效的并行模式！",
            "🚀 完美！这就是Perfect21的精髓！",
            "✨ 出色的工作！并行执行效率很高！",
            "🎯 目标明确！继续这样的执行节奏！"
        ]

        # 警告短语库
        self.warnings = [
            "⚠️ 注意！不要忘记并行执行的重要性！",
            "🚨 警告！检测到串行执行倾向！",
            "❗ 小心！不要退化到串行模式！",
            "⛔ 停止！重新考虑并行方案！",
            "🔴 危险！正在偏离Perfect21最佳实践！"
        ]

        logger.info("SmartReminder初始化 - 智能提醒系统已就绪")

    def get_phase_reminder(self, phase: str, context: Dict[str, Any]) -> str:
        """
        获取阶段个性化提醒

        Args:
            phase: 阶段名称
            context: 执行上下文

        Returns:
            个性化提醒信息
        """
        # 分析上下文
        analysis = self._analyze_context(context)

        # 选择提醒类型
        reminder_type = self._select_reminder_type(analysis)

        # 生成基础提醒
        base_reminder = self._generate_base_reminder(phase, reminder_type)

        # 添加个性化内容
        personalized_content = self._add_personalized_content(phase, context, analysis)

        # 添加具体建议
        specific_suggestions = self._generate_specific_suggestions(phase, context)

        # 组合完整提醒
        full_reminder = f"""
{base_reminder}

{personalized_content}

📌 具体建议：
{specific_suggestions}

💡 智能提示：
{self._get_smart_tip(phase, context)}
"""

        # 记录提醒
        self._record_reminder(phase, reminder_type, full_reminder)

        return full_reminder

    def learn_from_execution(self, phase: str, execution_result: Dict[str, Any]) -> None:
        """
        从执行结果中学习

        Args:
            phase: 阶段名称
            execution_result: 执行结果
        """
        # 识别执行模式
        pattern = self._identify_pattern(execution_result)

        # 更新模式记录
        if phase not in self.execution_patterns:
            self.execution_patterns[phase] = []
        self.execution_patterns[phase].append(pattern)

        # 识别成功和失败模式
        if execution_result.get('success') and pattern.get('is_parallel'):
            self.success_patterns.append({
                'phase': phase,
                'pattern': pattern,
                'timestamp': datetime.now().isoformat()
            })
        elif not execution_result.get('success') or not pattern.get('is_parallel'):
            self.failure_patterns.append({
                'phase': phase,
                'pattern': pattern,
                'timestamp': datetime.now().isoformat()
            })

        # 生成改进建议
        self._generate_improvement_suggestions(phase, pattern)

        logger.info(f"学习{phase}阶段执行模式：{pattern}")

    def get_contextual_tip(self, phase: str, situation: str) -> str:
        """
        获取情境化提示

        Args:
            phase: 阶段名称
            situation: 当前情境

        Returns:
            情境化提示
        """
        tips = {
            'first_phase': "🎯 第一个阶段很重要，设定好并行执行的基调！",
            'after_success': "✅ 上一阶段成功了，保持这个势头！",
            'after_failure': "🔄 上一阶段有问题，这次我们改正它！",
            'complex_task': "🧩 任务复杂，更需要多个agents并行分析！",
            'simple_task': "⚡ 即使简单任务，并行也能提高效率！",
            'final_phase': "🏁 最后阶段了，保持高质量完成！"
        }

        return tips.get(situation, "💪 记住：并行执行是Perfect21的核心！")

    def generate_motivation(self, current_stats: Dict[str, Any]) -> str:
        """
        生成激励信息

        Args:
            current_stats: 当前统计

        Returns:
            激励信息
        """
        parallel_rate = current_stats.get('parallel_rate', 0)

        if parallel_rate >= 80:
            motivation = random.choice(self.encouragements)
            level = "🏆 优秀"
        elif parallel_rate >= 60:
            motivation = "📈 不错的进步！继续提高并行率！"
            level = "🥈 良好"
        elif parallel_rate >= 40:
            motivation = "💪 还有提升空间，加油！"
            level = "🥉 及格"
        else:
            motivation = random.choice(self.warnings)
            level = "⚠️ 需要改进"

        stats_summary = f"""
📊 当前执行统计：
- 并行执行率: {parallel_rate:.1f}%
- 评级: {level}
- {motivation}
"""
        return stats_summary

    def _analyze_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析上下文"""
        analysis = {
            'has_previous_phase': 'last_phase' in context,
            'previous_was_parallel': context.get('last_phase', {}).get('was_parallel', False),
            'task_complexity': context.get('task_complexity', 'medium'),
            'time_pressure': context.get('time_pressure', False),
            'quality_requirement': context.get('quality_requirement', 'high')
        }

        # 分析趋势
        if self.execution_patterns:
            recent_patterns = []
            for patterns in self.execution_patterns.values():
                recent_patterns.extend(patterns[-3:])  # 最近3个

            parallel_count = sum(1 for p in recent_patterns if p.get('is_parallel'))
            analysis['parallel_trend'] = parallel_count / len(recent_patterns) if recent_patterns else 0
        else:
            analysis['parallel_trend'] = 0

        return analysis

    def _select_reminder_type(self, analysis: Dict[str, Any]) -> str:
        """选择提醒类型"""
        if not analysis['has_previous_phase']:
            return ReminderType.GUIDANCE

        if analysis['previous_was_parallel'] and analysis['parallel_trend'] > 0.7:
            return ReminderType.ENCOURAGEMENT
        elif not analysis['previous_was_parallel'] or analysis['parallel_trend'] < 0.3:
            return ReminderType.WARNING
        elif analysis['parallel_trend'] < 0.5:
            return ReminderType.CRITICAL
        else:
            return ReminderType.TIPS

    def _generate_base_reminder(self, phase: str, reminder_type: str) -> str:
        """生成基础提醒"""
        templates = {
            ReminderType.ENCOURAGEMENT: f"🌟 【{phase}阶段】执行得很好，继续保持！",
            ReminderType.WARNING: f"⚠️ 【{phase}阶段】注意保持并行执行！",
            ReminderType.CRITICAL: f"🚨 【{phase}阶段】必须恢复并行执行模式！",
            ReminderType.GUIDANCE: f"📖 【{phase}阶段】遵循Perfect21最佳实践",
            ReminderType.TIPS: f"💡 【{phase}阶段】优化执行的小技巧"
        }

        return templates.get(reminder_type, f"📋 【{phase}阶段】执行提醒")

    def _add_personalized_content(self, phase: str, context: Dict[str, Any],
                                 analysis: Dict[str, Any]) -> str:
        """添加个性化内容"""
        content = []

        # 基于历史模式的建议
        if phase in self.execution_patterns and self.execution_patterns[phase]:
            last_pattern = self.execution_patterns[phase][-1]
            if not last_pattern.get('is_parallel'):
                content.append("📝 上次这个阶段未能并行，这次要改进！")

        # 基于趋势的建议
        if analysis['parallel_trend'] < 0.5:
            content.append("📉 并行执行率下降，需要立即纠正！")
        elif analysis['parallel_trend'] > 0.8:
            content.append("📈 并行执行率优秀，保持这个水平！")

        # 基于任务复杂度的建议
        if analysis['task_complexity'] == 'high':
            content.append("🧩 复杂任务更需要多agents协作！")

        return '\n'.join(content) if content else "继续保持良好的执行习惯！"

    def _generate_specific_suggestions(self, phase: str, context: Dict[str, Any]) -> str:
        """生成具体建议"""
        suggestions = {
            'analysis': """
1. 并行调用 @project-manager, @business-analyst, @technical-writer
2. 等待所有分析完成
3. 对比和整合不同视角
4. 生成统一的需求文档""",

            'design': """
1. 并行调用 @api-designer, @backend-architect, @database-specialist
2. 创建feature分支
3. 设计评审和同步
4. 提交设计文档""",

            'implementation': """
1. 并行调用 @backend-architect, @frontend-specialist, @test-engineer
2. 代码实现和测试并行
3. 触发pre-commit hooks
4. 代码审查和优化""",

            'testing': """
1. 并行调用 @test-engineer, @security-auditor, @performance-engineer
2. 多维度测试覆盖
3. 生成测试报告
4. 触发pre-push hooks""",

            'deployment': """
1. 调用 @devops-engineer, @deployment-manager
2. 环境准备和部署
3. 监控配置
4. 合并到main分支"""
        }

        return suggestions.get(phase, "1. 识别需要的agents\n2. 并行执行\n3. 汇总结果\n4. 生成TODO")

    def _get_smart_tip(self, phase: str, context: Dict[str, Any]) -> str:
        """获取智能提示"""
        tips = [
            "使用 Task() 在一个消息中调用多个agents",
            "同步点是质量保证的关键",
            "汇总能发现agents间的共识和分歧",
            "TODO生成让下一阶段有明确方向",
            "Git操作要在合适的时机执行"
        ]

        # 根据阶段选择相关提示
        phase_specific_tips = {
            'analysis': "需求理解的一致性比速度更重要",
            'design': "好的架构设计能避免后续大量返工",
            'implementation': "代码和测试并行能更快发现问题",
            'testing': "多维度测试能提高代码质量",
            'deployment': "部署前的检查能避免生产事故"
        }

        general_tip = random.choice(tips)
        specific_tip = phase_specific_tips.get(phase, general_tip)

        return f"{specific_tip}\n提示：{general_tip}"

    def _identify_pattern(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """识别执行模式"""
        return {
            'is_parallel': execution_result.get('agent_count', 0) >= 2,
            'agent_count': execution_result.get('agent_count', 0),
            'duration': execution_result.get('duration', 0),
            'has_sync_point': execution_result.get('sync_point_executed', False),
            'has_summary': execution_result.get('summary_generated', False),
            'success': execution_result.get('success', False)
        }

    def _generate_improvement_suggestions(self, phase: str, pattern: Dict[str, Any]) -> None:
        """生成改进建议"""
        if not pattern['is_parallel']:
            self.improvement_suggestions.append(
                f"{phase}阶段: 需要增加并行agent数量"
            )

        if not pattern['has_sync_point']:
            self.improvement_suggestions.append(
                f"{phase}阶段: 添加同步点检查"
            )

        if not pattern['has_summary']:
            self.improvement_suggestions.append(
                f"{phase}阶段: 确保生成结果汇总"
            )

    def _record_reminder(self, phase: str, reminder_type: str, content: str) -> None:
        """记录提醒"""
        self.reminder_history.append({
            'phase': phase,
            'type': reminder_type,
            'timestamp': datetime.now().isoformat(),
            'content_preview': content[:100]  # 只保存预览
        })

        # 保持历史记录在合理范围
        if len(self.reminder_history) > 100:
            self.reminder_history = self.reminder_history[-100:]