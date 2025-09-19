#!/usr/bin/env python3
"""
Context Pool - 阶段间数据传递池
管理各阶段的输入输出，确保数据在阶段间正确传递
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("ContextPool")

class ContextPool:
    """
    阶段间数据传递池

    功能：
    1. 存储各阶段的输出
    2. 为下一阶段提供上下文
    3. 管理阶段间的依赖关系
    4. 支持数据版本控制
    """

    def __init__(self):
        self.shared_context = {}      # 全局共享上下文
        self.phase_outputs = {}        # 各阶段输出
        self.agent_outputs = {}        # 各agent输出
        self.dependencies = {}         # 依赖关系图
        self.metadata = {}            # 元数据（时间戳等）
        logger.info("ContextPool初始化完成")

    def add_phase_output(self, phase_id: str, output: Dict[str, Any]) -> None:
        """
        添加阶段输出

        Args:
            phase_id: 阶段标识
            output: 阶段输出数据
        """
        self.phase_outputs[phase_id] = {
            'data': output,
            'timestamp': datetime.now().isoformat(),
            'status': 'completed'
        }

        # 更新共享上下文
        self._update_shared_context(phase_id, output)

        logger.info(f"添加{phase_id}阶段输出，包含{len(output)}个数据项")

    def add_agent_output(self, phase_id: str, agent_name: str, output: Dict[str, Any]) -> None:
        """
        添加单个agent的输出

        Args:
            phase_id: 阶段标识
            agent_name: agent名称
            output: agent输出数据
        """
        if phase_id not in self.agent_outputs:
            self.agent_outputs[phase_id] = {}

        self.agent_outputs[phase_id][agent_name] = {
            'data': output,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"添加{phase_id}阶段{agent_name}的输出")

    def get_context_for_phase(self, phase_id: str) -> Dict[str, Any]:
        """
        获取阶段所需上下文

        Args:
            phase_id: 阶段标识

        Returns:
            该阶段可用的上下文数据
        """
        context = {
            'shared': self.shared_context.copy(),
            'previous_phases': {},
            'dependencies': self.get_phase_dependencies(phase_id)
        }

        # 添加前置阶段的输出
        for prev_phase_id, prev_output in self.phase_outputs.items():
            if self._is_predecessor(prev_phase_id, phase_id):
                context['previous_phases'][prev_phase_id] = prev_output['data']

        logger.info(f"为{phase_id}阶段准备上下文，包含{len(context['previous_phases'])}个前置阶段")

        return context

    def aggregate_agent_outputs(self, phase_id: str) -> Dict[str, Any]:
        """
        聚合某阶段所有agent的输出

        Args:
            phase_id: 阶段标识

        Returns:
            聚合后的输出数据
        """
        if phase_id not in self.agent_outputs:
            return {}

        aggregated = {
            'phase': phase_id,
            'agents': {},
            'summary': {},
            'consensus': {},
            'conflicts': []
        }

        phase_agents = self.agent_outputs[phase_id]

        # 收集所有agent输出
        for agent_name, agent_data in phase_agents.items():
            aggregated['agents'][agent_name] = agent_data['data']

        # 识别共识和分歧
        aggregated['consensus'] = self._find_consensus(phase_agents)
        aggregated['conflicts'] = self._find_conflicts(phase_agents)

        # 生成汇总
        aggregated['summary'] = self._generate_summary(phase_agents)

        logger.info(f"聚合{phase_id}阶段{len(phase_agents)}个agent的输出")

        return aggregated

    def _find_consensus(self, agent_outputs: Dict) -> Dict[str, Any]:
        """找出agents的共识点"""
        consensus = {}

        # 简化实现：查找所有agent都包含的键值对
        if not agent_outputs:
            return consensus

        # 收集所有agent的数据
        all_data = []
        for agent_data in agent_outputs.values():
            if 'data' in agent_data:
                # 处理嵌套的data结构
                data = agent_data['data']
                # 递归处理嵌套的data
                while isinstance(data, dict) and 'data' in data and len(data) == 1:
                    data = data['data']
                all_data.append(data)

        if not all_data:
            return consensus

        # 查找共识
        first_data = all_data[0]
        for key in first_data:
            values = []
            for data in all_data:
                if key in data:
                    values.append(data[key])

            # 如果所有agent都有这个key且值相同
            if len(values) == len(all_data) and len(set(map(str, values))) == 1:
                consensus[key] = values[0]

        return consensus

    def _find_conflicts(self, agent_outputs: Dict) -> List[Dict]:
        """找出agents的分歧点"""
        conflicts = []

        # 简化实现：查找有不同值的键
        keys_seen = {}

        for agent_name, agent_data in agent_outputs.items():
            if 'data' not in agent_data:
                continue

            # 处理嵌套的data结构
            data_to_check = agent_data['data']
            # 递归处理嵌套的data
            while isinstance(data_to_check, dict) and 'data' in data_to_check and len(data_to_check) == 1:
                data_to_check = data_to_check['data']

            if isinstance(data_to_check, dict):

                for key, value in data_to_check.items():
                    if key not in keys_seen:
                        keys_seen[key] = []
                    keys_seen[key].append({
                        'agent': agent_name,
                        'value': value
                    })

        # 找出有不同值的键
        for key, agent_values in keys_seen.items():
            unique_values = set(str(av['value']) for av in agent_values)
            if len(unique_values) > 1:
                conflicts.append({
                    'key': key,
                    'agents_opinions': agent_values
                })

        return conflicts

    def _generate_summary(self, agent_outputs: Dict) -> Dict[str, Any]:
        """生成阶段汇总"""
        summary = {
            'total_agents': len(agent_outputs),
            'completed_at': datetime.now().isoformat(),
            'key_findings': [],
            'next_steps': []
        }

        # 从agent输出中提取关键信息
        for agent_name, agent_data in agent_outputs.items():
            if 'data' in agent_data and isinstance(agent_data['data'], dict):
                # 提取关键发现
                if 'key_findings' in agent_data['data']:
                    summary['key_findings'].extend(agent_data['data']['key_findings'])

                # 提取建议的下一步
                if 'next_steps' in agent_data['data']:
                    summary['next_steps'].extend(agent_data['data']['next_steps'])

        # 去重
        summary['key_findings'] = list(set(summary['key_findings']))
        summary['next_steps'] = list(set(summary['next_steps']))

        return summary

    def validate_dependencies(self, phase_id: str) -> Dict[str, Any]:
        """
        验证阶段依赖是否满足

        Args:
            phase_id: 阶段标识

        Returns:
            验证结果
        """
        if phase_id not in self.dependencies:
            return {
                'valid': True,
                'message': f'{phase_id}没有依赖'
            }

        missing_deps = []
        for dep in self.dependencies[phase_id]:
            if dep not in self.phase_outputs:
                missing_deps.append(dep)

        if missing_deps:
            return {
                'valid': False,
                'message': f'{phase_id}缺少依赖: {", ".join(missing_deps)}',
                'missing': missing_deps
            }

        return {
            'valid': True,
            'message': f'{phase_id}的所有依赖已满足'
        }

    def set_phase_dependency(self, phase_id: str, depends_on: List[str]) -> None:
        """设置阶段依赖"""
        self.dependencies[phase_id] = depends_on
        logger.info(f"设置{phase_id}依赖于{depends_on}")

    def get_phase_dependencies(self, phase_id: str) -> List[str]:
        """获取阶段依赖"""
        return self.dependencies.get(phase_id, [])

    def _update_shared_context(self, phase_id: str, output: Dict) -> None:
        """更新共享上下文"""
        # 将重要数据添加到共享上下文
        if isinstance(output, dict):
            for key, value in output.items():
                if key in ['requirements', 'architecture', 'api_spec', 'test_results']:
                    self.shared_context[f"{phase_id}_{key}"] = value

    def _is_predecessor(self, phase1: str, phase2: str) -> bool:
        """判断phase1是否是phase2的前置阶段"""
        # 简化的阶段顺序判断
        phase_order = ['analysis', 'design', 'implementation', 'testing', 'deployment']

        try:
            idx1 = phase_order.index(phase1)
            idx2 = phase_order.index(phase2)
            return idx1 < idx2
        except ValueError:
            return False

    def clear(self) -> None:
        """清空所有数据"""
        self.shared_context.clear()
        self.phase_outputs.clear()
        self.agent_outputs.clear()
        self.dependencies.clear()
        self.metadata.clear()
        logger.info("ContextPool已清空")

    def export_context(self) -> Dict[str, Any]:
        """导出完整上下文（用于调试或持久化）"""
        return {
            'shared_context': self.shared_context,
            'phase_outputs': self.phase_outputs,
            'agent_outputs': self.agent_outputs,
            'dependencies': self.dependencies,
            'metadata': self.metadata,
            'exported_at': datetime.now().isoformat()
        }

    def import_context(self, context_data: Dict[str, Any]) -> None:
        """导入上下文数据"""
        self.shared_context = context_data.get('shared_context', {})
        self.phase_outputs = context_data.get('phase_outputs', {})
        self.agent_outputs = context_data.get('agent_outputs', {})
        self.dependencies = context_data.get('dependencies', {})
        self.metadata = context_data.get('metadata', {})
        logger.info("导入上下文数据完成")