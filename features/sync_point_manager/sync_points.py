#!/usr/bin/env python3
"""
Perfect21 同步点管理器
管理工作流中的同步点，确保Claude Code在关键节点进行质量检查
"""

import os
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger("SyncPointManager")

class SyncPointType(Enum):
    """同步点类型"""
    VALIDATION = "validation"           # 验证检查
    CROSS_VALIDATION = "cross_validation"  # 交叉验证
    MULTI_AGENT_REVIEW = "multi_agent_review"  # 多agent评审
    COMPREHENSIVE_CHECK = "comprehensive_check"  # 综合检查
    FINAL_VALIDATION = "final_validation"  # 最终验证
    QUALITY_GATE = "quality_gate"      # 质量门

class SyncPointStatus(Enum):
    """同步点状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"

@dataclass
class ValidationCriteria:
    """验证标准"""
    name: str
    description: str
    threshold: str
    measurement_method: str
    required: bool = True

@dataclass
class SyncPointResult:
    """同步点执行结果"""
    criteria_name: str
    actual_value: Any
    expected_value: str
    passed: bool
    message: str
    evidence: List[str] = None  # 证据文件或链接

@dataclass
class SyncPoint:
    """同步点定义"""
    id: str
    name: str
    type: SyncPointType
    stage_name: str
    description: str

    # 验证配置
    validation_criteria: List[ValidationCriteria]
    instruction: str
    timeout_minutes: int = 30
    required: bool = True

    # 执行状态
    status: SyncPointStatus = SyncPointStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    results: List[SyncPointResult] = None
    failure_reason: Optional[str] = None

    # 执行上下文
    execution_id: Optional[str] = None
    agents_involved: List[str] = None

class SyncPointManager:
    """同步点管理器"""

    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(__file__))
        self.workspace_path = os.path.join(self.base_path, "..", ".perfect21", "sync_points")

        # 确保目录存在
        os.makedirs(self.workspace_path, exist_ok=True)

        # 活跃的同步点
        self.active_sync_points: Dict[str, SyncPoint] = {}

        # 历史记录
        self.sync_point_history: List[SyncPoint] = []

        # 预定义的同步点模板
        self.sync_point_templates = self._load_sync_point_templates()

        logger.info("同步点管理器初始化完成")

    def _load_sync_point_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载同步点模板"""
        return {
            "requirements_consensus": {
                "name": "需求共识检查",
                "type": SyncPointType.CROSS_VALIDATION,
                "description": "确保多个agents对需求理解一致",
                "default_criteria": [
                    {
                        "name": "requirement_consistency",
                        "description": "三方理解一致性",
                        "threshold": "> 95%",
                        "measurement_method": "语义相似度分析",
                        "required": True
                    },
                    {
                        "name": "scope_clarity",
                        "description": "功能边界清晰明确",
                        "threshold": "明确定义",
                        "measurement_method": "边界条件检查",
                        "required": True
                    }
                ],
                "instruction": """
请对比所有参与agents的输出，进行需求共识检查：

1. **一致性分析**：
   - 识别共同理解的核心需求
   - 找出理解分歧和差异点
   - 分析分歧的根本原因

2. **分歧解决**：
   如果发现重大分歧：
   - 组织agents进行交叉评审
   - 召开"虚拟需求澄清会议"
   - 通过讨论达成统一理解

3. **输出确认**：
   - 生成统一的需求文档
   - 确保所有agents对此无异议
   - 明确功能边界和验收标准

**通过标准**: 所有参与agents必须对核心需求达成100%共识
"""
            },

            "architecture_review": {
                "name": "架构设计评审",
                "type": SyncPointType.MULTI_AGENT_REVIEW,
                "description": "多角度专业评审架构设计",
                "default_criteria": [
                    {
                        "name": "security_approval",
                        "description": "安全评审通过",
                        "threshold": "无高风险项",
                        "measurement_method": "安全专家评审",
                        "required": True
                    },
                    {
                        "name": "performance_approval",
                        "description": "性能评审通过",
                        "threshold": "满足目标指标",
                        "measurement_method": "性能专家评估",
                        "required": True
                    },
                    {
                        "name": "design_consistency",
                        "description": "架构一致性",
                        "threshold": "各层级架构匹配",
                        "measurement_method": "架构一致性检查",
                        "required": True
                    }
                ],
                "instruction": """
请召集多个领域专家对架构设计进行交叉评审：

**评审团队**：
- @security-auditor: 从安全角度评审
- @performance-engineer: 从性能角度评审
- @devops-engineer: 从运维角度评审

**评审流程**：
1. 每个reviewer独立评审各自领域
2. 提出具体改进建议和风险点
3. 架构师响应评审意见并调整设计
4. 所有reviewer确认修改后的方案

**通过标准**: 所有专业reviewer都必须approve最终架构
"""
            },

            "integration_readiness": {
                "name": "集成准备度检查",
                "type": SyncPointType.COMPREHENSIVE_CHECK,
                "description": "全面检查集成前的准备状态",
                "default_criteria": [
                    {
                        "name": "api_consistency",
                        "description": "API接口一致性",
                        "threshold": "100%一致",
                        "measurement_method": "接口契约比对",
                        "required": True
                    },
                    {
                        "name": "test_coverage",
                        "description": "测试覆盖率",
                        "threshold": ">= 90%",
                        "measurement_method": "代码覆盖率报告",
                        "required": True
                    },
                    {
                        "name": "security_scan",
                        "description": "安全扫描结果",
                        "threshold": "无高危漏洞",
                        "measurement_method": "SAST扫描报告",
                        "required": True
                    }
                ],
                "instruction": """
进行集成前的全面检查：

**检查维度**：
1. **接口一致性**: 前后端API调用与规范100%匹配
2. **功能完整性**: 所有需求功能点都已实现
3. **代码质量**: 通过所有质量扫描
4. **测试准备**: 单元测试和集成测试就绪

**检查方法**：
- 运行自动化检查脚本
- 对比设计文档和实现代码
- 验证测试覆盖率报告
- 确认安全扫描通过

**通过标准**: 所有检查项必须100%通过
"""
            },

            "comprehensive_quality_gate": {
                "name": "综合质量门",
                "type": SyncPointType.QUALITY_GATE,
                "description": "多维度质量门验证",
                "default_criteria": [
                    {
                        "name": "functional_quality",
                        "description": "功能测试通过率",
                        "threshold": "100%",
                        "measurement_method": "功能测试报告",
                        "required": True
                    },
                    {
                        "name": "performance_quality",
                        "description": "性能指标达标",
                        "threshold": "P95 < 200ms",
                        "measurement_method": "性能测试报告",
                        "required": True
                    },
                    {
                        "name": "security_quality",
                        "description": "安全测试通过",
                        "threshold": "无高危漏洞",
                        "measurement_method": "安全测试报告",
                        "required": True
                    },
                    {
                        "name": "code_quality",
                        "description": "代码质量达标",
                        "threshold": "质量分数 > 90",
                        "measurement_method": "代码质量报告",
                        "required": True
                    }
                ],
                "instruction": """
进行多维度综合质量门验证：

**质量维度**：
1. **功能质量**: 所有功能测试100%通过
2. **性能质量**: API响应时间、吞吐量达标
3. **安全质量**: 无高危安全漏洞
4. **代码质量**: 代码规范、复杂度、覆盖率
5. **用户体验**: 易用性、无障碍性合规

**验证方法**：
- 汇总所有测试报告
- 对比质量标准阈值
- 评估整体质量水平
- 确认生产发布就绪

**放行标准**: 所有质量维度都必须达到优秀水平
"""
            },

            "production_readiness": {
                "name": "生产就绪验证",
                "type": SyncPointType.FINAL_VALIDATION,
                "description": "生产环境发布前最终验证",
                "default_criteria": [
                    {
                        "name": "deployment_ready",
                        "description": "部署配置就绪",
                        "threshold": "配置验证通过",
                        "measurement_method": "部署脚本测试",
                        "required": True
                    },
                    {
                        "name": "monitoring_ready",
                        "description": "监控配置生效",
                        "threshold": "监控指标正常",
                        "measurement_method": "监控系统验证",
                        "required": True
                    },
                    {
                        "name": "backup_verified",
                        "description": "备份恢复验证",
                        "threshold": "备份恢复成功",
                        "measurement_method": "备份恢复测试",
                        "required": True
                    }
                ],
                "instruction": """
进行生产发布前的最终验证：

**验证清单**：
1. **部署环境**: 容器、配置、网络就绪
2. **数据层**: 数据库、备份、恢复验证
3. **监控运维**: 监控、告警、日志配置
4. **安全合规**: 安全加固、证书、权限
5. **应急预案**: 回滚方案、故障处理

**确认方法**：
- 执行预发布检查清单
- 验证所有基础设施组件
- 测试应急响应流程
- 确认团队和文档就绪

**放行标准**: 所有生产要素100%就绪，无风险点
"""
            }
        }

    def create_sync_point(self, template_name: str, stage_name: str,
                         execution_id: str, **kwargs) -> str:
        """
        创建同步点

        Args:
            template_name: 同步点模板名称
            stage_name: 所属工作流阶段名称
            execution_id: 执行ID
            **kwargs: 其他自定义参数

        Returns:
            同步点ID
        """
        if template_name not in self.sync_point_templates:
            raise ValueError(f"未知的同步点模板: {template_name}")

        template = self.sync_point_templates[template_name]

        # 生成同步点ID
        sync_point_id = f"sync_{stage_name}_{execution_id}_{int(time.time())}"

        # 创建验证标准
        criteria = []
        for crit in template["default_criteria"]:
            criteria.append(ValidationCriteria(
                name=crit["name"],
                description=crit["description"],
                threshold=crit["threshold"],
                measurement_method=crit["measurement_method"],
                required=crit.get("required", True)
            ))

        # 添加自定义标准
        if "additional_criteria" in kwargs:
            for crit in kwargs["additional_criteria"]:
                criteria.append(ValidationCriteria(**crit))

        # 创建同步点
        sync_point = SyncPoint(
            id=sync_point_id,
            name=template["name"],
            type=template["type"],
            stage_name=stage_name,
            description=template["description"],
            validation_criteria=criteria,
            instruction=template["instruction"],
            timeout_minutes=kwargs.get("timeout_minutes", 30),
            required=kwargs.get("required", True),
            execution_id=execution_id,
            agents_involved=kwargs.get("agents_involved", []),
            results=[]
        )

        # 注册同步点
        self.active_sync_points[sync_point_id] = sync_point

        logger.info(f"创建同步点: {sync_point_id} - {template['name']}")
        return sync_point_id

    def start_sync_point(self, sync_point_id: str) -> bool:
        """开始执行同步点"""
        if sync_point_id not in self.active_sync_points:
            logger.error(f"同步点不存在: {sync_point_id}")
            return False

        sync_point = self.active_sync_points[sync_point_id]
        sync_point.status = SyncPointStatus.IN_PROGRESS
        sync_point.start_time = datetime.now()

        logger.info(f"开始执行同步点: {sync_point_id}")
        return True

    def validate_criteria(self, sync_point_id: str, criteria_name: str,
                         actual_value: Any, evidence: List[str] = None) -> bool:
        """
        验证单个标准

        Args:
            sync_point_id: 同步点ID
            criteria_name: 标准名称
            actual_value: 实际值
            evidence: 验证证据

        Returns:
            验证是否通过
        """
        if sync_point_id not in self.active_sync_points:
            logger.error(f"同步点不存在: {sync_point_id}")
            return False

        sync_point = self.active_sync_points[sync_point_id]

        # 找到对应的验证标准
        criteria = None
        for c in sync_point.validation_criteria:
            if c.name == criteria_name:
                criteria = c
                break

        if not criteria:
            logger.error(f"验证标准不存在: {criteria_name}")
            return False

        # 执行验证逻辑
        passed, message = self._evaluate_criteria(criteria, actual_value)

        # 记录验证结果
        result = SyncPointResult(
            criteria_name=criteria_name,
            actual_value=actual_value,
            expected_value=criteria.threshold,
            passed=passed,
            message=message,
            evidence=evidence or []
        )

        sync_point.results.append(result)

        logger.info(f"验证标准 {criteria_name}: {'通过' if passed else '失败'}")
        return passed

    def _evaluate_criteria(self, criteria: ValidationCriteria,
                          actual_value: Any) -> Tuple[bool, str]:
        """评估验证标准"""
        threshold = criteria.threshold

        try:
            # 数值比较
            if ">=" in threshold:
                expected = float(threshold.replace(">=", "").replace("%", "").strip())
                actual = float(str(actual_value).replace("%", ""))
                passed = actual >= expected
                message = f"实际值 {actual} {'≥' if passed else '<'} 期望值 {expected}"
                return passed, message

            elif ">" in threshold:
                expected = float(threshold.replace(">", "").replace("%", "").strip())
                actual = float(str(actual_value).replace("%", ""))
                passed = actual > expected
                message = f"实际值 {actual} {'>' if passed else '≤'} 期望值 {expected}"
                return passed, message

            elif "<=" in threshold:
                expected = float(threshold.replace("<=", "").replace("ms", "").strip())
                actual = float(str(actual_value).replace("ms", ""))
                passed = actual <= expected
                message = f"实际值 {actual} {'≤' if passed else '>'} 期望值 {expected}"
                return passed, message

            elif "<" in threshold:
                expected = float(threshold.replace("<", "").replace("ms", "").strip())
                actual = float(str(actual_value).replace("ms", ""))
                passed = actual < expected
                message = f"实际值 {actual} {'<' if passed else '≥'} 期望值 {expected}"
                return passed, message

            elif "100%" in threshold or "完全" in threshold or "全部" in threshold:
                # 完全匹配检查
                passed = str(actual_value) in ["100%", "完全通过", "全部通过", "True", "true", "1"]
                message = f"完全匹配检查: {'通过' if passed else '未通过'}"
                return passed, message

            elif "无" in threshold:
                # 无问题检查
                passed = str(actual_value) in ["0", "无", "None", "空", ""]
                message = f"无问题检查: {'通过' if passed else '有问题'}"
                return passed, message

            else:
                # 字符串匹配
                passed = str(actual_value).strip() == threshold.strip()
                message = f"字符串匹配: {'匹配' if passed else '不匹配'}"
                return passed, message

        except Exception as e:
            logger.error(f"评估验证标准失败: {e}")
            return False, f"评估失败: {str(e)}"

    def complete_sync_point(self, sync_point_id: str) -> bool:
        """完成同步点验证"""
        if sync_point_id not in self.active_sync_points:
            logger.error(f"同步点不存在: {sync_point_id}")
            return False

        sync_point = self.active_sync_points[sync_point_id]
        sync_point.end_time = datetime.now()

        # 检查所有必需标准是否都已验证
        required_criteria = [c for c in sync_point.validation_criteria if c.required]
        verified_criteria = [r.criteria_name for r in sync_point.results]

        missing_criteria = []
        for criteria in required_criteria:
            if criteria.name not in verified_criteria:
                missing_criteria.append(criteria.name)

        if missing_criteria:
            sync_point.status = SyncPointStatus.FAILED
            sync_point.failure_reason = f"缺少验证: {', '.join(missing_criteria)}"
            logger.error(f"同步点失败: 缺少必需的验证标准")
            return False

        # 检查是否所有必需标准都通过
        failed_required = []
        for result in sync_point.results:
            if not result.passed:
                # 检查这个标准是否是必需的
                for criteria in sync_point.validation_criteria:
                    if criteria.name == result.criteria_name and criteria.required:
                        failed_required.append(result.criteria_name)

        if failed_required:
            sync_point.status = SyncPointStatus.FAILED
            sync_point.failure_reason = f"必需标准验证失败: {', '.join(failed_required)}"
            logger.error(f"同步点失败: 必需标准验证失败")
            return False

        # 所有验证通过
        sync_point.status = SyncPointStatus.PASSED
        logger.info(f"同步点通过: {sync_point_id}")

        # 保存结果
        self._save_sync_point_result(sync_point)

        # 移动到历史记录
        self.sync_point_history.append(sync_point)
        del self.active_sync_points[sync_point_id]

        return True

    def fail_sync_point(self, sync_point_id: str, reason: str) -> bool:
        """标记同步点失败"""
        if sync_point_id not in self.active_sync_points:
            logger.error(f"同步点不存在: {sync_point_id}")
            return False

        sync_point = self.active_sync_points[sync_point_id]
        sync_point.status = SyncPointStatus.FAILED
        sync_point.end_time = datetime.now()
        sync_point.failure_reason = reason

        logger.error(f"同步点失败: {sync_point_id} - {reason}")

        # 保存结果
        self._save_sync_point_result(sync_point)

        # 移动到历史记录
        self.sync_point_history.append(sync_point)
        del self.active_sync_points[sync_point_id]

        return True

    def get_sync_point_status(self, sync_point_id: str) -> Optional[Dict[str, Any]]:
        """获取同步点状态"""
        sync_point = None

        # 先在活跃列表中查找
        if sync_point_id in self.active_sync_points:
            sync_point = self.active_sync_points[sync_point_id]
        else:
            # 在历史记录中查找
            for sp in self.sync_point_history:
                if sp.id == sync_point_id:
                    sync_point = sp
                    break

        if not sync_point:
            return None

        return {
            "id": sync_point.id,
            "name": sync_point.name,
            "status": sync_point.status.value,
            "stage_name": sync_point.stage_name,
            "start_time": sync_point.start_time.isoformat() if sync_point.start_time else None,
            "end_time": sync_point.end_time.isoformat() if sync_point.end_time else None,
            "duration_minutes": (
                (sync_point.end_time - sync_point.start_time).total_seconds() / 60
                if sync_point.start_time and sync_point.end_time else None
            ),
            "total_criteria": len(sync_point.validation_criteria),
            "verified_criteria": len(sync_point.results),
            "passed_criteria": len([r for r in sync_point.results if r.passed]),
            "failed_criteria": len([r for r in sync_point.results if not r.passed]),
            "failure_reason": sync_point.failure_reason,
            "results": [
                {
                    "criteria": r.criteria_name,
                    "passed": r.passed,
                    "message": r.message,
                    "evidence_count": len(r.evidence) if r.evidence else 0
                }
                for r in sync_point.results
            ]
        }

    def get_active_sync_points(self) -> List[Dict[str, Any]]:
        """获取所有活跃同步点状态"""
        return [
            self.get_sync_point_status(sp_id)
            for sp_id in self.active_sync_points.keys()
        ]

    def generate_sync_point_report(self, execution_id: str) -> Dict[str, Any]:
        """生成特定执行的同步点报告"""
        execution_sync_points = []

        # 从活跃和历史记录中收集
        for sp in list(self.active_sync_points.values()) + self.sync_point_history:
            if sp.execution_id == execution_id:
                execution_sync_points.append(sp)

        if not execution_sync_points:
            return {"message": f"没有找到执行ID {execution_id} 的同步点"}

        # 统计信息
        total_sync_points = len(execution_sync_points)
        passed_sync_points = len([sp for sp in execution_sync_points if sp.status == SyncPointStatus.PASSED])
        failed_sync_points = len([sp for sp in execution_sync_points if sp.status == SyncPointStatus.FAILED])
        in_progress_sync_points = len([sp for sp in execution_sync_points if sp.status == SyncPointStatus.IN_PROGRESS])

        # 详细结果
        sync_point_details = []
        for sp in execution_sync_points:
            details = {
                "name": sp.name,
                "type": sp.type.value,
                "stage": sp.stage_name,
                "status": sp.status.value,
                "duration": (
                    (sp.end_time - sp.start_time).total_seconds() / 60
                    if sp.start_time and sp.end_time else None
                ),
                "criteria_summary": {
                    "total": len(sp.validation_criteria),
                    "passed": len([r for r in sp.results if r.passed]),
                    "failed": len([r for r in sp.results if not r.passed])
                }
            }

            if sp.status == SyncPointStatus.FAILED:
                details["failure_reason"] = sp.failure_reason

            sync_point_details.append(details)

        return {
            "execution_id": execution_id,
            "summary": {
                "total_sync_points": total_sync_points,
                "passed": passed_sync_points,
                "failed": failed_sync_points,
                "in_progress": in_progress_sync_points,
                "success_rate": (passed_sync_points / total_sync_points * 100) if total_sync_points > 0 else 0
            },
            "sync_points": sync_point_details
        }

    def _save_sync_point_result(self, sync_point: SyncPoint):
        """保存同步点结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sync_point_{sync_point.id}_{timestamp}.json"
        filepath = os.path.join(self.workspace_path, filename)

        try:
            result_data = {
                "sync_point": {
                    "id": sync_point.id,
                    "name": sync_point.name,
                    "type": sync_point.type.value,
                    "stage_name": sync_point.stage_name,
                    "status": sync_point.status.value,
                    "start_time": sync_point.start_time.isoformat() if sync_point.start_time else None,
                    "end_time": sync_point.end_time.isoformat() if sync_point.end_time else None,
                    "execution_id": sync_point.execution_id,
                    "agents_involved": sync_point.agents_involved
                },
                "validation_criteria": [
                    {
                        "name": c.name,
                        "description": c.description,
                        "threshold": c.threshold,
                        "required": c.required
                    }
                    for c in sync_point.validation_criteria
                ],
                "results": [
                    {
                        "criteria_name": r.criteria_name,
                        "actual_value": r.actual_value,
                        "expected_value": r.expected_value,
                        "passed": r.passed,
                        "message": r.message,
                        "evidence": r.evidence
                    }
                    for r in sync_point.results
                ],
                "failure_reason": sync_point.failure_reason
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            logger.info(f"同步点结果已保存: {filepath}")

        except Exception as e:
            logger.error(f"保存同步点结果失败: {e}")

# 全局实例
_sync_point_manager = None

def get_sync_point_manager() -> SyncPointManager:
    """获取同步点管理器实例"""
    global _sync_point_manager
    if _sync_point_manager is None:
        _sync_point_manager = SyncPointManager()
    return _sync_point_manager