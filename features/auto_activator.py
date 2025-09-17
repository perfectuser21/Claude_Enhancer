"""
Perfect21自动激活器 - 确保Claude Code默认使用Perfect21模式
"""
import os
import json
from pathlib import Path
from typing import Dict, Any

class Perfect21Activator:
    def __init__(self):
        self.base_path = Path(os.environ.get('PERFECT21_ROOT', '/home/xx/dev/Perfect21'))
        self.config_file = self.base_path / '.perfect21' / 'config.json'
        self.activation_markers = [
            'workflow', 'Perfect21', 'quality_workflow',
            'premium_quality', 'sync_point', 'decision_recorder'
        ]

    def should_activate_perfect21(self, user_input: str) -> bool:
        """智能检测是否应该激活Perfect21模式"""
        user_input_lower = user_input.lower()

        # 显式激活条件
        explicit_triggers = [
            'perfect21', '质量优先', 'quality workflow',
            'premium quality', 'workflow orchestrator'
        ]

        if any(trigger in user_input_lower for trigger in explicit_triggers):
            return True

        # 复杂任务自动激活
        complexity_indicators = [
            '实现', '开发', '构建', '设计', '架构',
            'implement', 'develop', 'build', 'design', 'architect'
        ]

        if any(indicator in user_input_lower for indicator in complexity_indicators):
            return True

        return False

    def get_activation_config(self) -> Dict[str, Any]:
        """获取激活配置"""
        default_config = {
            'auto_activate': True,
            'default_workflow': 'dynamic_workflow',  # 使用动态工作流
            'sync_points_enabled': True,
            'decision_recording_enabled': True,
            'quality_gates_enabled': True
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return {**default_config, **config}
            except Exception:
                pass

        return default_config

    def create_activation_message(self, user_input: str) -> str:
        """创建Perfect21激活消息"""
        if self.should_activate_perfect21(user_input):
            return """
🚀 **Perfect21模式已自动激活**

我将使用Perfect21的智能工作流系统来执行您的任务：
- 🧠 **动态工作流生成**: 根据任务智能选择最佳agents
- ⚡ **分层并行执行**: 优化效率的同时保证质量
- 🔴 **智能同步点**: 关键节点的质量检查和验证
- 📝 **决策记录**: 自动记录到knowledge/decisions/adr
- 🔍 **持续学习**: 从执行中学习并改进

让我开始分析您的需求并制定最佳执行策略...
"""
        return ""

# 全局实例
perfect21_activator = Perfect21Activator()