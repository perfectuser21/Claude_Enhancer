#!/usr/bin/env python3
"""
Execution Supervisor - 执行监督器
Claude Code的"管家"，确保并行执行不退化
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger("ExecutionSupervisor")

class ExecutionMode(Enum):
    """执行模式"""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    DEGRADED = "degraded"  # 退化模式（从并行退化到串行）

class ExecutionSupervisor:
    """
    执行监督器 - 监督Claude Code的执行行为

    主要功能：
    1. 阶段开始前提醒
    2. 检查执行计划
    3. 监测执行模式
    4. 发现退化时警告
    """

    def __init__(self):
        self.phase_history = []
        self.parallel_requirements = {
            'analysis': 3,      # 分析阶段至少3个agents
            'design': 3,        # 设计阶段至少3个agents
            'implementation': 2, # 实施阶段至少2个agents
            'testing': 3,       # 测试阶段至少3个agents
            'deployment': 2     # 部署阶段至少2个agents
        }
        self.execution_stats = {
            'total_phases': 0,
            'parallel_phases': 0,
            'sequential_phases': 0,
            'degraded_phases': 0
        }
        logger.info("ExecutionSupervisor初始化 - Claude Code的管家已就位")

    def before_phase(self, phase: str, context: Dict[str, Any] = None) -> str:
        """
        阶段开始前的提醒

        返回给Claude Code的提醒信息
        """
        min_agents = self.parallel_requirements.get(phase, 2)

        # 检查上一阶段的执行情况
        last_phase_feedback = self._get_last_phase_feedback()

        # 获取推荐的agents
        recommended_agents = self._get_recommended_agents(phase)

        reminder = f"""
╔══════════════════════════════════════════════════════════════════╗
║         🎯 Perfect21 执行监督提醒 - {phase.upper()}阶段         ║
╚══════════════════════════════════════════════════════════════════╝

{last_phase_feedback}

📋 当前阶段【{phase}】执行要求：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ 并行要求: 必须并行调用至少 {min_agents} 个agents
🔍 执行模式: PARALLEL（不要退化为串行）
⏱️ 同步点: 所有agents完成后进行汇总

🤖 推荐的Agents组合：
{self._format_agent_list(recommended_agents)}

⚠️ 重要提醒：
1. ❌ 不要自己直接Read/Write文件
2. ❌ 不要串行调用agents
3. ✅ 使用单个消息中的多个Task()调用
4. ✅ 等待所有agents完成后汇总

📝 正确的调用示例：
```python
# 在一个消息中并行调用多个agents
Task(subagent_type='{recommended_agents[0] if recommended_agents else 'agent1'}', prompt='...')
Task(subagent_type='{recommended_agents[1] if len(recommended_agents) > 1 else 'agent2'}', prompt='...')
Task(subagent_type='{recommended_agents[2] if len(recommended_agents) > 2 else 'agent3'}', prompt='...')
```

🔴 记住：你是Claude Code，应该调用agents而不是自己做所有工作！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        logger.info(f"已向Claude Code发送{phase}阶段执行提醒")
        return reminder

    def check_execution_plan(self, phase: str, execution_plan: List[str]) -> Dict[str, Any]:
        """
        检查执行计划是否符合并行要求

        Args:
            phase: 阶段名称
            execution_plan: 计划调用的agents列表

        Returns:
            检查结果
        """
        min_agents = self.parallel_requirements.get(phase, 2)
        agent_count = len(execution_plan)

        result = {
            'phase': phase,
            'planned_agents': agent_count,
            'required_agents': min_agents,
            'approved': agent_count >= min_agents,
            'execution_mode': ExecutionMode.PARALLEL if agent_count >= min_agents else ExecutionMode.SEQUENTIAL
        }

        if not result['approved']:
            result['warning'] = f"""
⚠️ 执行计划不符合要求！
- 当前计划: {agent_count}个agents
- 最低要求: {min_agents}个agents
- 缺少: {min_agents - agent_count}个agents

建议添加以下agents到执行计划：
{self._suggest_additional_agents(phase, execution_plan)}
"""
            logger.warning(f"{phase}阶段执行计划不符合并行要求")
        else:
            result['message'] = f"✅ 执行计划符合要求，将并行调用{agent_count}个agents"
            logger.info(f"{phase}阶段执行计划已通过检查")

        return result

    def record_execution(self, phase: str, actual_execution: Dict[str, Any]) -> None:
        """
        记录实际执行情况

        Args:
            phase: 阶段名称
            actual_execution: 实际执行信息
        """
        execution_record = {
            'phase': phase,
            'timestamp': datetime.now().isoformat(),
            'agent_count': actual_execution.get('agent_count', 0),
            'execution_mode': self._determine_execution_mode(actual_execution),
            'duration': actual_execution.get('duration', 0),
            'success': actual_execution.get('success', False)
        }

        self.phase_history.append(execution_record)

        # 更新统计
        self.execution_stats['total_phases'] += 1

        if execution_record['execution_mode'] == ExecutionMode.PARALLEL:
            self.execution_stats['parallel_phases'] += 1
        elif execution_record['execution_mode'] == ExecutionMode.SEQUENTIAL:
            self.execution_stats['sequential_phases'] += 1
        elif execution_record['execution_mode'] == ExecutionMode.DEGRADED:
            self.execution_stats['degraded_phases'] += 1

        logger.info(f"记录{phase}阶段执行：{execution_record['execution_mode'].value}模式")

    def detect_degradation(self, phase: str, current_execution: Dict[str, Any]) -> Optional[str]:
        """
        检测执行退化

        Returns:
            如果发现退化，返回警告信息
        """
        if not self.phase_history:
            return None

        last_phase = self.phase_history[-1]
        current_mode = self._determine_execution_mode(current_execution)

        if (last_phase['execution_mode'] == ExecutionMode.PARALLEL and
            current_mode != ExecutionMode.PARALLEL):

            warning = f"""
🚨 执行退化警告！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
上一阶段: {last_phase['phase']} - {last_phase['execution_mode'].value}模式
当前阶段: {phase} - {current_mode.value}模式

⚠️ 检测到从并行退化为串行执行！

立即采取行动：
1. 停止当前的串行执行
2. 重新规划并行执行方案
3. 使用多个Task()调用agents

记住：Perfect21的核心优势是并行执行！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            logger.warning(f"检测到执行退化：{phase}阶段从并行退化为{current_mode.value}")
            return warning

        return None

    def get_execution_report(self) -> Dict[str, Any]:
        """
        获取执行报告
        """
        if self.execution_stats['total_phases'] == 0:
            parallel_rate = 0
        else:
            parallel_rate = (self.execution_stats['parallel_phases'] /
                           self.execution_stats['total_phases']) * 100

        report = {
            'statistics': self.execution_stats,
            'parallel_rate': parallel_rate,
            'phase_history': self.phase_history[-5:],  # 最近5个阶段
            'recommendations': self._generate_recommendations()
        }

        return report

    def _get_last_phase_feedback(self) -> str:
        """获取上一阶段的执行反馈"""
        if not self.phase_history:
            return "📊 这是第一个阶段，请确保并行执行！"

        last_phase = self.phase_history[-1]

        if last_phase['execution_mode'] == ExecutionMode.PARALLEL:
            return f"✅ 上一阶段【{last_phase['phase']}】并行执行良好，请继续保持！"
        else:
            return f"⚠️ 上一阶段【{last_phase['phase']}】未能并行执行，本阶段必须改进！"

    def _get_recommended_agents(self, phase: str) -> List[str]:
        """获取推荐的agents列表"""
        recommendations = {
            'analysis': ['project-manager', 'business-analyst', 'technical-writer'],
            'design': ['api-designer', 'backend-architect', 'database-specialist'],
            'implementation': ['backend-architect', 'frontend-specialist', 'test-engineer'],
            'testing': ['test-engineer', 'security-auditor', 'performance-engineer'],
            'deployment': ['devops-engineer', 'deployment-manager', 'monitoring-specialist']
        }

        return recommendations.get(phase, ['backend-architect', 'frontend-specialist', 'test-engineer'])

    def _format_agent_list(self, agents: List[str]) -> str:
        """格式化agent列表"""
        return '\n'.join([f"   {i+1}. @{agent}" for i, agent in enumerate(agents)])

    def _suggest_additional_agents(self, phase: str, current_agents: List[str]) -> str:
        """建议额外的agents"""
        all_agents = self._get_recommended_agents(phase)
        missing = [a for a in all_agents if a not in current_agents]

        if missing:
            return "建议添加: " + ", ".join([f"@{a}" for a in missing])
        return "建议添加更多相关的agents"

    def _determine_execution_mode(self, execution: Dict[str, Any]) -> ExecutionMode:
        """判断执行模式"""
        agent_count = execution.get('agent_count', 0)
        is_parallel = execution.get('is_parallel', False)

        if agent_count >= 2 and is_parallel:
            return ExecutionMode.PARALLEL
        elif agent_count >= 2 and not is_parallel:
            return ExecutionMode.DEGRADED
        else:
            return ExecutionMode.SEQUENTIAL

    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        if self.execution_stats['parallel_phases'] < self.execution_stats['total_phases']:
            recommendations.append("增加并行执行的阶段数量")

        if self.execution_stats['degraded_phases'] > 0:
            recommendations.append("避免从并行退化为串行")

        if self.execution_stats['sequential_phases'] > self.execution_stats['parallel_phases']:
            recommendations.append("将更多串行执行改为并行")

        return recommendations