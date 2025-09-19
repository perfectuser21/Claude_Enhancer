"""
Sync Point Manager - Mock Implementation for Testing
"""

from typing import Dict, Any, Optional
import sys
import os

# Add project path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.types import SyncPointData, SyncPointType


class SyncPointManager:
    """同步点管理器 - 测试用Mock实现"""

    def __init__(self) -> None:
        self.sync_points: Dict[str, SyncPointData] = {}
        self.sync_counter: int = 0

    def create_sync_point(self, sync_config: Dict[str, Any]) -> SyncPointData:
        """创建同步点"""
        self.sync_counter += 1
        sync_id = f"sync_{self.sync_counter}"

        from datetime import datetime

        sync_point: SyncPointData = {
            'sync_id': sync_id,
            'name': sync_config.get('name', 'Unnamed Sync Point'),
            'type': SyncPointType(sync_config.get('type', 'validation')),
            'validation_criteria': sync_config.get('criteria', {}),
            'timeout': sync_config.get('timeout', 300),
            'must_pass': sync_config.get('must_pass', True),
            'created_at': datetime.now().isoformat(),
            'status': 'waiting'
        }

        self.sync_points[sync_id] = sync_point
        return sync_point

    def validate_sync_point(self, sync_point: Dict[str, Any], validation_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证同步点 - 支持直接传入sync_point配置"""
        # 处理两种调用方式：直接传入配置或使用ID
        if isinstance(sync_point, str):
            sync_id = sync_point
            if sync_id not in self.sync_points:
                return {'success': False, 'error': 'Sync point not found'}
            sync_point_config = self.sync_points[sync_id]
        else:
            sync_point_config = sync_point
            sync_id = sync_point_config.get('sync_id', 'direct_validation')

        criteria = sync_point_config.get('validation_criteria', {})

        # 检查所有条件是否满足
        failed_criteria = []
        validation_details = {}

        for criterion_name, criterion_rule in criteria.items():
            actual_value = validation_data.get(criterion_name)
            validation_result = self._evaluate_criterion(criterion_name, criterion_rule, actual_value)
            validation_details[criterion_name] = validation_result

            if not validation_result['passed']:
                failed_criteria.append({
                    'criterion': criterion_name,
                    'rule': criterion_rule,
                    'actual': actual_value,
                    'reason': validation_result.get('reason', 'Criterion not met')
                })

        all_met = len(failed_criteria) == 0

        if sync_id in self.sync_points:
            self.sync_points[sync_id]['status'] = 'passed' if all_met else 'failed'

        return {
            'success': all_met,
            'all_criteria_met': all_met,
            'failed_criteria': failed_criteria,
            'validation_details': validation_details,
            'sync_id': sync_id,
            'sync_point_type': sync_point_config.get('type', 'unknown')
        }

    def wait_for_sync_point(self, sync_id: str) -> Dict[str, Any]:
        """等待同步点"""
        if sync_id not in self.sync_points:
            return {'success': False, 'error': 'Sync point not found'}

        # 模拟等待
        sync_point = self.sync_points[sync_id]
        return {
            'success': True,
            'sync_point': sync_point,
            'waited': True
        }

    def get_sync_point(self, sync_id: str) -> Optional[SyncPointData]:
        """获取同步点信息"""
        return self.sync_points.get(sync_id)

    def list_sync_points(self) -> Dict[str, SyncPointData]:
        """获取所有同步点"""
        return self.sync_points.copy()

    def delete_sync_point(self, sync_id: str) -> bool:
        """删除同步点"""
        if sync_id in self.sync_points:
            del self.sync_points[sync_id]
            return True
        return False

    def _evaluate_criterion(self, criterion_name: str, criterion_rule: str, actual_value: Any) -> Dict[str, Any]:
        """评估单个验证条件"""
        try:
            # 布尔值直接比较
            if isinstance(actual_value, bool):
                if criterion_rule == 'true' or criterion_rule is True:
                    return {'passed': actual_value, 'value': actual_value}
                elif criterion_rule == 'false' or criterion_rule is False:
                    return {'passed': not actual_value, 'value': actual_value}

            # 数值比较
            if isinstance(actual_value, (int, float)):
                if isinstance(criterion_rule, str) and '>' in criterion_rule:
                    threshold = float(criterion_rule.split('>')[-1].strip())
                    passed = actual_value > threshold
                    return {'passed': passed, 'value': actual_value, 'threshold': threshold}
                elif isinstance(criterion_rule, str) and '<' in criterion_rule:
                    threshold = float(criterion_rule.split('<')[-1].strip())
                    passed = actual_value < threshold
                    return {'passed': passed, 'value': actual_value, 'threshold': threshold}
                elif isinstance(criterion_rule, (int, float)):
                    passed = actual_value >= criterion_rule
                    return {'passed': passed, 'value': actual_value, 'expected': criterion_rule}

            # 字符串相等比较
            if isinstance(criterion_rule, str) and not any(op in criterion_rule for op in ['>', '<', '>=', '<=']):
                passed = str(actual_value) == criterion_rule
                return {'passed': passed, 'value': actual_value, 'expected': criterion_rule}

            # 默认相等比较
            passed = actual_value == criterion_rule
            return {'passed': passed, 'value': actual_value, 'expected': criterion_rule}

        except Exception as e:
            return {'passed': False, 'reason': f'Evaluation error: {str(e)}'}
