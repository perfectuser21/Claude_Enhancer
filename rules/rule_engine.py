#!/usr/bin/env python3
"""
Perfect21 规则引擎 - 简化版
专注于规则匹配和执行指导，而非复杂的工作流生成
"""

import re
import yaml
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger("Perfect21.RuleEngine")


class Perfect21RuleEngine:
    """Perfect21规则引擎 - 提供执行指导而非执行"""

    def __init__(self, rules_file: str = None):
        """初始化规则引擎"""
        if rules_file is None:
            rules_file = Path(__file__).parent / "perfect21_rules.yaml"

        self.rules = self._load_rules(rules_file)
        self.logger = logger

    def _load_rules(self, rules_file: str) -> Dict[str, Any]:
        """加载规则配置"""
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载规则失败: {e}")
            return {}

    def analyze_task(self, task_description: str) -> Dict[str, Any]:
        """
        分析任务并返回执行指导

        返回的是指导建议，而不是执行计划
        """
        # 1. 识别任务类型
        task_type = self._identify_task_type(task_description)

        # 2. 获取对应的Agent组合规则
        agent_pattern = self._get_agent_pattern(task_type)

        # 3. 判断执行模式
        execution_mode = self._determine_execution_mode(task_description, agent_pattern)

        # 4. 识别质量要求
        quality_requirements = self._get_quality_requirements(task_type)

        # 5. 构建执行指导
        guidance = {
            'task_type': task_type,
            'task_description': task_description,
            'execution_guidance': {
                'agents_to_use': agent_pattern.get('required_agents', []),
                'execution_mode': execution_mode,
                'parallel_execution': execution_mode == 'parallel',
                'quality_requirements': quality_requirements,
            },
            'instructions_for_claude': self._generate_instructions(
                task_type, agent_pattern, execution_mode
            ),
            'best_practices': self._get_best_practices(task_type),
        }

        return guidance

    def _identify_task_type(self, task_description: str) -> str:
        """识别任务类型"""
        task_recognition = self.rules.get('task_recognition', {}).get('patterns', [])

        for pattern_config in task_recognition:
            pattern = pattern_config.get('pattern', '')
            if re.search(pattern, task_description, re.IGNORECASE):
                return pattern_config.get('type', 'general')

        # 默认类型
        return 'general'

    def _get_agent_pattern(self, task_type: str) -> Dict[str, Any]:
        """获取Agent组合模式"""
        agent_patterns = self.rules.get('agent_patterns', {})
        return agent_patterns.get(task_type, {
            'required_agents': ['fullstack-engineer'],
            'execution_mode': 'sequential',
            'quality_requirements': []
        })

    def _determine_execution_mode(self, task_description: str,
                                  agent_pattern: Dict[str, Any]) -> str:
        """判断执行模式（并行或顺序）"""
        # 如果规则中指定了模式，使用规则
        if 'execution_mode' in agent_pattern:
            return agent_pattern['execution_mode']

        # 根据Agent数量判断
        agent_count = len(agent_pattern.get('required_agents', []))
        if agent_count >= 3:
            return 'parallel'

        # 检查是否有紧急关键词
        urgent_keywords = ['紧急', 'urgent', 'ASAP', '立即', '马上']
        if any(keyword in task_description for keyword in urgent_keywords):
            return 'parallel'

        return 'sequential'

    def _get_quality_requirements(self, task_type: str) -> List[str]:
        """获取质量要求"""
        agent_pattern = self.rules.get('agent_patterns', {}).get(task_type, {})
        return agent_pattern.get('quality_requirements', [])

    def _generate_instructions(self, task_type: str,
                              agent_pattern: Dict[str, Any],
                              execution_mode: str) -> str:
        """生成给Claude Code的执行指导"""
        agents = agent_pattern.get('required_agents', [])

        if execution_mode == 'parallel' and len(agents) > 1:
            instructions = f"""
## 执行指导

任务类型识别为: **{task_type}**

### 必须并行调用以下Agents:
请在一个function_calls消息中同时调用所有agents：

```xml
<function_calls>
"""
            for agent in agents:
                instructions += f"""  <invoke name="Task">
    <parameter name="subagent_type">{agent}</parameter>
    <parameter name="prompt">根据任务要求完成{agent}的工作</parameter>
  </invoke>
"""
            instructions += """</function_calls>
```

**重要**:
- 必须在同一个消息中并行调用所有agents
- 不要分开调用，必须批量执行
- 每个agent负责自己领域的工作
"""
        else:
            instructions = f"""
## 执行指导

任务类型识别为: **{task_type}**

### 顺序调用以下Agents:
"""
            for i, agent in enumerate(agents, 1):
                instructions += f"{i}. {agent}\n"

        return instructions

    def _get_best_practices(self, task_type: str) -> List[str]:
        """获取最佳实践"""
        general_practices = self.rules.get('best_practices', {}).get('general', [])

        # 根据任务类型添加特定的最佳实践
        if 'auth' in task_type.lower():
            security_practices = self.rules.get('best_practices', {}).get('security', [])
            return general_practices + security_practices

        return general_practices

    def get_hook_guidance(self, hook_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取Git Hook执行指导
        """
        hook_config = self.rules.get('hook_triggers', {}).get(hook_name, {})

        if not hook_config:
            return {
                'should_trigger': False,
                'message': f'No rules defined for {hook_name}'
            }

        # 构建Hook执行指导
        guidance = {
            'hook_name': hook_name,
            'should_trigger': True,
            'required_agents': hook_config.get('required_agents', []),
            'optional_agents': hook_config.get('optional_agents', []),
            'rules': hook_config.get('rules', []),
            'description': hook_config.get('description', ''),
        }

        # 根据上下文调整
        branch = context.get('branch', 'main')
        if branch in ['main', 'master']:
            # 主分支需要更严格的检查
            guidance['optional_agents'] = []  # 可选变必选
            guidance['strict_mode'] = True

        return guidance

    def check_quality_gates(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查质量门标准

        返回是否通过和具体要求
        """
        quality_gates = self.rules.get('quality_gates', {})
        results = {
            'passed': True,
            'checks': [],
            'failed_checks': []
        }

        for gate_name, gate_config in quality_gates.items():
            gate_metrics = gate_config.get('metrics', [])
            gate_checks = gate_config.get('checks', [])

            # 检查度量标准
            for metric in gate_metrics:
                metric_name = metric.get('name')
                metric_value = metrics.get(metric_name)

                if metric_value is not None:
                    if 'minimum' in metric and metric_value < metric['minimum']:
                        results['failed_checks'].append(
                            f"{metric_name}: {metric_value} < {metric['minimum']}"
                        )
                        results['passed'] = False
                    elif 'maximum' in metric and metric_value > metric['maximum']:
                        results['failed_checks'].append(
                            f"{metric_name}: {metric_value} > {metric['maximum']}"
                        )
                        results['passed'] = False
                    else:
                        results['checks'].append(f"{metric_name}: ✓")

            # 记录必须通过的检查
            for check in gate_checks:
                results['checks'].append(f"Required: {check}")

        return results


def get_rule_engine() -> Perfect21RuleEngine:
    """获取规则引擎实例"""
    return Perfect21RuleEngine()


if __name__ == "__main__":
    # 测试规则引擎
    engine = get_rule_engine()

    # 测试任务分析
    test_tasks = [
        "实现用户登录系统",
        "开发RESTful API接口",
        "优化数据库查询性能",
        "创建React前端组件",
    ]

    for task in test_tasks:
        print(f"\n{'='*60}")
        print(f"任务: {task}")
        print(f"{'='*60}")

        guidance = engine.analyze_task(task)

        print(f"任务类型: {guidance['task_type']}")
        print(f"需要Agents: {guidance['execution_guidance']['agents_to_use']}")
        print(f"执行模式: {guidance['execution_guidance']['execution_mode']}")
        print("\n执行指导:")
        print(guidance['instructions_for_claude'])
        print("\n最佳实践:")
        for practice in guidance['best_practices']:
            print(f"  - {practice}")