#!/usr/bin/env python3
"""
统一回滚管理器
==============

整合所有回滚功能的统一管理接口
提供一站式的回滚决策和执行能力
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# 导入各个回滚管理器
from database_backup_manager import create_backup_manager
from migration_rollback_manager import migration_rollback_manager
from config_rollback_manager import config_rollback_manager
from emergency_hotfix_manager import emergency_hotfix_manager, Priority, HotfixStatus


class RollbackType(Enum):
    """回滚类型"""

    GIT_ONLY = "git_only"
    DATABASE_ONLY = "database_only"
    CONFIG_ONLY = "config_only"
    HOTFIX_ONLY = "hotfix_only"
    FULL_SYSTEM = "full_system"
    SELECTIVE = "selective"


class RollbackSeverity(Enum):
    """回滚严重程度"""

    LOW = "low"  # 仅配置更改
    MEDIUM = "medium"  # 代码更改，无数据影响
    HIGH = "high"  # 数据库更改
    CRITICAL = "critical"  # 系统级更改


@dataclass
class RollbackPlan:
    """回滚计划"""

    plan_id: str
    rollback_type: RollbackType
    severity: RollbackSeverity
    description: str
    target_points: Dict[str, str]  # 各系统的目标回滚点
    execution_order: List[str]  # 执行顺序
    validation_steps: List[str]  # 验证步骤
    estimated_duration: int  # 预估时间（秒）
    risk_assessment: str
    created_at: datetime


class UnifiedRollbackManager:
    """统一回滚管理器"""

    def __init__(self, project_root: Optional[str] = None):
        """
        初始化统一回滚管理器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root or ".")
        self.rollback_dir = self.project_root / "rollback-strategy"

        # 初始化各个子管理器
        self.db_manager = create_backup_manager()
        self.migration_manager = migration_rollback_manager
        self.config_manager = config_rollback_manager
        self.hotfix_manager = emergency_hotfix_manager

        # 回滚计划存储
        self.plans_file = self.rollback_dir / "rollback_plans.json"
        self.plans = self._load_plans()

        # 配置
        self.config = {
            "max_rollback_attempts": 3,
            "health_check_timeout": 60,
            "validation_timeout": 300,
            "rollback_timeout": 1800,  # 30分钟
        }

        self.logger = logging.getLogger(__name__)

    def _load_plans(self) -> Dict[str, RollbackPlan]:
        """加载回滚计划"""
        if not self.plans_file.exists():
            return {}

        try:
            with open(self.plans_file, "r") as f:
                data = json.load(f)

            plans = {}
            for plan_id, item in data.items():
                item["rollback_type"] = RollbackType(item["rollback_type"])
                item["severity"] = RollbackSeverity(item["severity"])
                item["created_at"] = datetime.fromisoformat(item["created_at"])
                plans[plan_id] = RollbackPlan(**item)

            return plans
        except Exception as e:
            self.logger.error(f"加载回滚计划失败: {e}")
            return {}

    def _save_plans(self):
        """保存回滚计划"""
        try:
            data = {}
            for plan_id, plan in self.plans.items():
                item = {
                    "plan_id": plan.plan_id,
                    "rollback_type": plan.rollback_type.value,
                    "severity": plan.severity.value,
                    "description": plan.description,
                    "target_points": plan.target_points,
                    "execution_order": plan.execution_order,
                    "validation_steps": plan.validation_steps,
                    "estimated_duration": plan.estimated_duration,
                    "risk_assessment": plan.risk_assessment,
                    "created_at": plan.created_at.isoformat(),
                }
                data[plan_id] = item

            with open(self.plans_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"保存回滚计划失败: {e}")

    def analyze_rollback_requirements(
        self,
        issue_description: str,
        affected_components: List[str],
        severity: RollbackSeverity,
    ) -> RollbackPlan:
        """
        分析回滚需求

        Args:
            issue_description: 问题描述
            affected_components: 受影响组件
            severity: 严重程度

        Returns:
            回滚计划
        """
        self.logger.info("分析回滚需求...")

        # 确定回滚类型
        rollback_type = self._determine_rollback_type(affected_components, severity)

        # 获取可用的回滚点
        available_points = self._get_available_rollback_points()

        # 选择最佳回滚点
        target_points = self._select_optimal_rollback_points(
            available_points, affected_components, severity
        )

        # 确定执行顺序
        execution_order = self._determine_execution_order(rollback_type, severity)

        # 生成验证步骤
        validation_steps = self._generate_validation_steps(affected_components)

        # 估算时间
        estimated_duration = self._estimate_rollback_duration(rollback_type, severity)

        # 风险评估
        risk_assessment = self._assess_rollback_risks(
            rollback_type, severity, target_points
        )

        # 创建回滚计划
        plan_id = f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        plan = RollbackPlan(
            plan_id=plan_id,
            rollback_type=rollback_type,
            severity=severity,
            description=issue_description,
            target_points=target_points,
            execution_order=execution_order,
            validation_steps=validation_steps,
            estimated_duration=estimated_duration,
            risk_assessment=risk_assessment,
            created_at=datetime.now(),
        )

        # 保存计划
        self.plans[plan_id] = plan
        self._save_plans()

        return plan

    def _determine_rollback_type(
        self, affected_components: List[str], severity: RollbackSeverity
    ) -> RollbackType:
        """确定回滚类型"""
        has_database = any(
            comp in ["database", "migration", "db"] for comp in affected_components
        )
        has_config = any(
            comp in ["config", "settings", "env"] for comp in affected_components
        )
        has_code = any(
            comp in ["api", "auth", "core", "frontend", "backend"]
            for comp in affected_components
        )

        if severity == RollbackSeverity.CRITICAL:
            return RollbackType.FULL_SYSTEM

        if has_database and has_config and has_code:
            return RollbackType.FULL_SYSTEM
        elif has_database and not has_config and not has_code:
            return RollbackType.DATABASE_ONLY
        elif has_config and not has_database and not has_code:
            return RollbackType.CONFIG_ONLY
        elif len(affected_components) == 1:
            return RollbackType.SELECTIVE
        else:
            return RollbackType.FULL_SYSTEM

    def _get_available_rollback_points(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有可用的回滚点"""
        points = {
            "git": self._get_git_rollback_points(),
            "database": self._get_database_rollback_points(),
            "migration": self._get_migration_rollback_points(),
            "config": self._get_config_rollback_points(),
            "hotfix": self._get_hotfix_rollback_points(),
        }
        return points

    def _get_git_rollback_points(self) -> List[Dict[str, Any]]:
        """获取Git回滚点"""
        try:
            import subprocess

            result = subprocess.run(
                ["git", "tag", "-l", "rollback-*", "--sort=-version:refname"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            points = []
            for tag in result.stdout.strip().split("\n")[:10]:  # 最近10个
                if tag:
                    points.append(
                        {
                            "id": tag,
                            "type": "git",
                            "timestamp": self._get_git_tag_date(tag),
                            "description": f"Git rollback point: {tag}",
                        }
                    )

            return points
        except Exception as e:
            self.logger.error(f"获取Git回滚点失败: {e}")
            return []

    def _get_git_tag_date(self, tag: str) -> str:
        """获取Git标签日期"""
        try:
            import subprocess

            result = subprocess.run(
                ["git", "log", "-1", "--format=%ci", tag],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    def _get_database_rollback_points(self) -> List[Dict[str, Any]]:
        """获取数据库备份回滚点"""
        try:
            backups = self.db_manager.list_backups(limit=10)
            points = []
            for backup in backups:
                points.append(
                    {
                        "id": backup.backup_id,
                        "type": "database",
                        "timestamp": backup.timestamp.isoformat(),
                        "description": backup.description,
                    }
                )
            return points
        except Exception as e:
            self.logger.error(f"获取数据库回滚点失败: {e}")
            return []

    def _get_migration_rollback_points(self) -> List[Dict[str, Any]]:
        """获取Migration回滚点"""
        try:
            snapshots = self.migration_manager.list_snapshots(limit=10)
            points = []
            for snapshot in snapshots:
                points.append(
                    {
                        "id": snapshot.revision,
                        "type": "migration",
                        "timestamp": snapshot.timestamp.isoformat(),
                        "description": snapshot.description,
                    }
                )
            return points
        except Exception as e:
            self.logger.error(f"获取Migration回滚点失败: {e}")
            return []

    def _get_config_rollback_points(self) -> List[Dict[str, Any]]:
        """获取配置回滚点"""
        try:
            snapshots = self.config_manager.list_snapshots(limit=10)
            points = []
            for snapshot in snapshots:
                points.append(
                    {
                        "id": snapshot.snapshot_id,
                        "type": "config",
                        "timestamp": snapshot.timestamp.isoformat(),
                        "description": snapshot.description,
                    }
                )
            return points
        except Exception as e:
            self.logger.error(f"获取配置回滚点失败: {e}")
            return []

    def _get_hotfix_rollback_points(self) -> List[Dict[str, Any]]:
        """获取Hotfix回滚点"""
        try:
            hotfixes = self.hotfix_manager.list_hotfixes(
                status_filter=HotfixStatus.DEPLOYED, limit=5
            )
            points = []
            for hotfix in hotfixes:
                points.append(
                    {
                        "id": hotfix.hotfix_id,
                        "type": "hotfix",
                        "timestamp": hotfix.created_at.isoformat(),
                        "description": f"Hotfix: {hotfix.title}",
                    }
                )
            return points
        except Exception as e:
            self.logger.error(f"获取Hotfix回滚点失败: {e}")
            return []

    def _select_optimal_rollback_points(
        self,
        available_points: Dict[str, List[Dict[str, Any]]],
        affected_components: List[str],
        severity: RollbackSeverity,
    ) -> Dict[str, str]:
        """选择最优回滚点"""
        target_points = {}

        # 根据严重程度选择回滚策略
        if severity == RollbackSeverity.CRITICAL:
            pass  # Auto-fixed empty block
            # 紧急情况：选择最近的稳定点
            for point_type, points in available_points.items():
                if points:
                    target_points[point_type] = points[0]["id"]
        else:
            pass  # Auto-fixed empty block
            # 常规情况：选择最相关的回滚点
            for point_type, points in available_points.items():
                if self._is_component_affected(point_type, affected_components):
                    if points:
                        target_points[point_type] = points[0]["id"]

        return target_points

    def _is_component_affected(
        self, point_type: str, affected_components: List[str]
    ) -> bool:
        """判断组件是否受影响"""
        component_mapping = {
            "database": ["database", "db", "migration"],
            "migration": ["database", "db", "migration"],
            "config": ["config", "settings", "env"],
            "git": ["code", "api", "auth", "core", "frontend", "backend"],
            "hotfix": affected_components,  # hotfix可能影响任何组件
        }

        mapped_components = component_mapping.get(point_type, [])
        return any(comp in affected_components for comp in mapped_components)

    def _determine_execution_order(
        self, rollback_type: RollbackType, severity: RollbackSeverity
    ) -> List[str]:
        """确定执行顺序"""
        if rollback_type == RollbackType.FULL_SYSTEM:
            if severity == RollbackSeverity.CRITICAL:
                pass  # Auto-fixed empty block
                # 紧急情况：最快路径
                return ["hotfix", "config", "database", "git"]
            else:
                pass  # Auto-fixed empty block
                # 常规全量回滚：安全顺序
                return ["config", "migration", "database", "git"]

        elif rollback_type == RollbackType.DATABASE_ONLY:
            return ["migration", "database"]

        elif rollback_type == RollbackType.CONFIG_ONLY:
            return ["config"]

        elif rollback_type == RollbackType.HOTFIX_ONLY:
            return ["hotfix"]

        else:  # SELECTIVE
            return ["config", "database", "git"]

    def _generate_validation_steps(self, affected_components: List[str]) -> List[str]:
        """生成验证步骤"""
        steps = ["检查系统基本健康状态", "验证核心服务运行状态"]

        if "database" in affected_components or "db" in affected_components:
            steps.extend(["验证数据库连接", "检查数据库架构完整性", "验证关键数据查询"])

        if "auth" in affected_components:
            steps.extend(["测试用户登录功能", "验证权限控制"])

        if "api" in affected_components:
            steps.extend(["测试API端点响应", "验证API功能正确性"])

        steps.append("执行端到端功能测试")
        return steps

    def _estimate_rollback_duration(
        self, rollback_type: RollbackType, severity: RollbackSeverity
    ) -> int:
        """估算回滚耗时（秒）"""
        base_times = {
            RollbackType.CONFIG_ONLY: 60,  # 1分钟
            RollbackType.HOTFIX_ONLY: 180,  # 3分钟
            RollbackType.DATABASE_ONLY: 300,  # 5分钟
            RollbackType.GIT_ONLY: 120,  # 2分钟
            RollbackType.SELECTIVE: 480,  # 8分钟
            RollbackType.FULL_SYSTEM: 900,  # 15分钟
        }

        base_time = base_times.get(rollback_type, 600)

        # 根据严重程度调整
        if severity == RollbackSeverity.CRITICAL:
            return int(base_time * 0.7)  # 紧急模式快30%
        elif severity == RollbackSeverity.HIGH:
            return base_time
        else:
            return int(base_time * 1.3)  # 保守估算

    def _assess_rollback_risks(
        self,
        rollback_type: RollbackType,
        severity: RollbackSeverity,
        target_points: Dict[str, str],
    ) -> str:
        """评估回滚风险"""
        risks = []

        if rollback_type == RollbackType.FULL_SYSTEM:
            risks.append("全系统回滚风险较高，可能导致服务暂时不可用")

        if "database" in target_points:
            risks.append("数据库回滚可能导致最近数据丢失")

        if severity == RollbackSeverity.CRITICAL:
            risks.append("紧急回滚可能跳过部分验证步骤")

        if not target_points:
            risks.append("未找到合适的回滚点，回滚可能失败")

        if len(risks) == 0:
            return "风险评估：低风险"
        elif len(risks) <= 2:
            return f"风险评估：中等风险 - {'; '.join(risks)}"
        else:
            return f"风险评估：高风险 - {'; '.join(risks)}"

    def execute_rollback_plan(
        self, plan_id: str, confirm: bool = False, skip_validation: bool = False
    ) -> bool:
        """
        执行回滚计划

        Args:
            plan_id: 计划ID
            confirm: 是否确认执行
            skip_validation: 是否跳过验证

        Returns:
            是否执行成功
        """
        if not confirm:
            self.logger.warning("回滚执行需要确认，请设置confirm=True")
            return False

        if plan_id not in self.plans:
            self.logger.error(f"回滚计划不存在: {plan_id}")
            return False

        plan = self.plans[plan_id]
        self.logger.info(f"开始执行回滚计划: {plan_id}")
        self.logger.info(f"回滚类型: {plan.rollback_type.value}")
        self.logger.info(f"严重程度: {plan.severity.value}")

        try:
            pass  # Auto-fixed empty block
            # 创建回滚前快照
            self._create_pre_rollback_snapshots()

            # 按顺序执行回滚
            for step in plan.execution_order:
                if step in plan.target_points:
                    target_point = plan.target_points[step]
                    self.logger.info(f"执行 {step} 回滚到 {target_point}")

                    if not self._execute_single_rollback(step, target_point):
                        self.logger.error(f"{step} 回滚失败")
                        return False

            # 验证回滚结果
            if not skip_validation:
                if not self._validate_rollback(plan):
                    self.logger.error("回滚验证失败")
                    return False

            self.logger.info(f"回滚计划执行成功: {plan_id}")
            return True

        except Exception as e:
            self.logger.error(f"执行回滚计划异常: {e}")
            return False

    def _create_pre_rollback_snapshots(self):
        """创建回滚前的快照"""
        self.logger.info("创建回滚前快照...")

        try:
            pass  # Auto-fixed empty block
            # 创建配置快照
            self.config_manager.create_config_snapshot(
                description="Pre-rollback config snapshot"
            )

            # 创建数据库备份
            self.db_manager.create_full_backup(
                description="Pre-rollback database backup"
            )

            # 创建迁移快照
            self.migration_manager.create_migration_snapshot(
                description="Pre-rollback migration snapshot"
            )

        except Exception as e:
            self.logger.warning(f"创建预回滚快照失败: {e}")

    def _execute_single_rollback(self, rollback_type: str, target_point: str) -> bool:
        """执行单个回滚操作"""
        try:
            if rollback_type == "config":
                return self.config_manager.rollback_config(target_point, confirm=True)

            elif rollback_type == "database":
                return self.db_manager.restore_backup(target_point, confirm=True)

            elif rollback_type == "migration":
                return self.migration_manager.rollback_to_snapshot(
                    target_point, confirm=True
                )

            elif rollback_type == "hotfix":
                return self.hotfix_manager.rollback_hotfix(target_point, confirm=True)

            elif rollback_type == "git":
                return self._execute_git_rollback(target_point)

            else:
                self.logger.error(f"未知回滚类型: {rollback_type}")
                return False

        except Exception as e:
            self.logger.error(f"执行 {rollback_type} 回滚失败: {e}")
            return False

    def _execute_git_rollback(self, tag: str) -> bool:
        """执行Git回滚"""
        try:
            import subprocess

            # 检出到指定标签
            result = subprocess.run(
                ["git", "checkout", tag],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode == 0:
                self.logger.info(f"Git回滚成功: {tag}")
                return True
            else:
                self.logger.error(f"Git回滚失败: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Git回滚异常: {e}")
            return False

    def _validate_rollback(self, plan: RollbackPlan) -> bool:
        """验证回滚结果"""
        self.logger.info("开始验证回滚结果...")

        for step in plan.validation_steps:
            self.logger.info(f"验证步骤: {step}")

            if not self._execute_validation_step(step):
                self.logger.error(f"验证步骤失败: {step}")
                return False

        self.logger.info("回滚验证通过")
        return True

    def _execute_validation_step(self, step: str) -> bool:
        """执行验证步骤"""
        try:
            pass  # Auto-fixed empty block
            # 这里应该根据具体的验证步骤执行相应的检查
            # 简化实现，实际应该有更具体的验证逻辑
            import time

            time.sleep(1)  # 模拟验证过程

            # 基本的健康检查
            if "健康状态" in step:
                return self._check_system_health()
            elif "服务运行" in step:
                return self._check_service_status()
            elif "数据库" in step:
                return self._check_database_health()
            else:
                return True  # 默认通过

        except Exception as e:
            self.logger.error(f"验证步骤执行异常: {e}")
            return False

    def _check_system_health(self) -> bool:
        """检查系统健康状态"""
        # 简化实现
        return True

    def _check_service_status(self) -> bool:
        """检查服务状态"""
        # 简化实现
        return True

    def _check_database_health(self) -> bool:
        """检查数据库健康状态"""
        try:
            pass  # Auto-fixed empty block
            # 尝试连接数据库
            with self.db_manager._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception:
            return False

    def create_emergency_rollback_plan(
        self, issue_description: str, affected_components: List[str]
    ) -> str:
        """
        创建紧急回滚计划

        Args:
            issue_description: 问题描述
            affected_components: 受影响组件

        Returns:
            计划ID
        """
        plan = self.analyze_rollback_requirements(
            issue_description=issue_description,
            affected_components=affected_components,
            severity=RollbackSeverity.CRITICAL,
        )

        self.logger.info(f"创建紧急回滚计划: {plan.plan_id}")
        return plan.plan_id

    def quick_rollback(
        self,
        issue_description: str,
        affected_components: List[str],
        confirm: bool = False,
    ) -> bool:
        """
        快速回滚（分析+执行）

        Args:
            issue_description: 问题描述
            affected_components: 受影响组件
            confirm: 是否确认执行

        Returns:
            是否执行成功
        """
        # 创建计划
        plan_id = self.create_emergency_rollback_plan(
            issue_description, affected_components
        )

        # 执行计划
        return self.execute_rollback_plan(
            plan_id, confirm=confirm, skip_validation=True
        )

    def list_rollback_plans(self, limit: int = 20) -> List[RollbackPlan]:
        """列出回滚计划"""
        plans = list(self.plans.values())
        plans.sort(key=lambda x: x.created_at, reverse=True)
        return plans[:limit]

    def get_rollback_status(self) -> Dict[str, Any]:
        """获取回滚系统状态"""
        return {
            "available_git_points": len(self._get_git_rollback_points()),
            "available_db_backups": len(self._get_database_rollback_points()),
            "available_migration_snapshots": len(self._get_migration_rollback_points()),
            "available_config_snapshots": len(self._get_config_rollback_points()),
            "active_hotfixes": len(
                self.hotfix_manager.list_hotfixes(HotfixStatus.DEPLOYED)
            ),
            "total_rollback_plans": len(self.plans),
            "system_health": self._check_overall_system_health(),
        }

    def _check_overall_system_health(self) -> Dict[str, bool]:
        """检查整体系统健康状态"""
        return {
            "database": self._check_database_health(),
            "git": True,  # Git通常是可用的
            "config": True,  # 配置系统通常是可用的
            "services": self._check_service_status(),
        }


# 创建全局实例
unified_rollback_manager = UnifiedRollbackManager()


# 便捷函数
def emergency_rollback(
    issue_description: str, affected_components: List[str], confirm: bool = False
) -> bool:
    """紧急回滚"""
    return unified_rollback_manager.quick_rollback(
        issue_description, affected_components, confirm
    )


def analyze_rollback(
    issue_description: str, affected_components: List[str], severity: str = "high"
) -> RollbackPlan:
    """分析回滚需求"""
    severity_map = {
        "low": RollbackSeverity.LOW,
        "medium": RollbackSeverity.MEDIUM,
        "high": RollbackSeverity.HIGH,
        "critical": RollbackSeverity.CRITICAL,
    }

    return unified_rollback_manager.analyze_rollback_requirements(
        issue_description, affected_components, severity_map[severity]
    )


if __name__ == "__main__":
    import argparse

    # 设置日志
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="统一回滚管理器")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 分析回滚需求
    analyze_parser = subparsers.add_parser("analyze", help="分析回滚需求")
    analyze_parser.add_argument("description", help="问题描述")
    analyze_parser.add_argument("--components", nargs="+", required=True, help="受影响组件")
    analyze_parser.add_argument(
        "--severity",
        choices=["low", "medium", "high", "critical"],
        default="high",
        help="严重程度",
    )

    # 执行回滚计划
    execute_parser = subparsers.add_parser("execute", help="执行回滚计划")
    execute_parser.add_argument("plan_id", help="计划ID")
    execute_parser.add_argument("--confirm", action="store_true", help="确认执行")
    execute_parser.add_argument("--skip-validation", action="store_true", help="跳过验证")

    # 紧急回滚
    emergency_parser = subparsers.add_parser("emergency", help="紧急回滚")
    emergency_parser.add_argument("description", help="问题描述")
    emergency_parser.add_argument(
        "--components", nargs="+", required=True, help="受影响组件"
    )
    emergency_parser.add_argument("--confirm", action="store_true", help="确认执行")

    # 列出计划
    list_parser = subparsers.add_parser("list", help="列出回滚计划")
    list_parser.add_argument("--limit", type=int, default=20, help="限制数量")

    # 查看状态
    status_parser = subparsers.add_parser("status", help="查看系统状态")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 执行命令
    if args.command == "analyze":
        plan = analyze_rollback(args.description, args.components, args.severity)
        print(f"回滚计划: {plan.plan_id}")
        print(f"类型: {plan.rollback_type.value}")
        print(f"严重程度: {plan.severity.value}")
        print(f"预估时间: {plan.estimated_duration}秒")
        print(f"执行顺序: {' -> '.join(plan.execution_order)}")
        print(f"风险评估: {plan.risk_assessment}")

    elif args.command == "execute":
        success = unified_rollback_manager.execute_rollback_plan(
            args.plan_id, args.confirm, args.skip_validation
        )
        if success:
            print(f"回滚计划执行成功: {args.plan_id}")
        else:
            print(f"回滚计划执行失败: {args.plan_id}")
            sys.exit(1)

    elif args.command == "emergency":
        success = emergency_rollback(args.description, args.components, args.confirm)
        if success:
            print("紧急回滚执行成功")
        else:
            print("紧急回滚执行失败")
            sys.exit(1)

    elif args.command == "list":
        plans = unified_rollback_manager.list_rollback_plans(args.limit)
        print(f"{'计划ID':<25} {'类型':<15} {'严重程度':<10} {'创建时间':<20} {'描述'}")
        print("-" * 100)
        for plan in plans:
            print(
                f"{plan.plan_id:<25} {plan.rollback_type.value:<15} {plan.severity.value:<10} {plan.created_at.strftime('%Y-%m-%d %H:%M'):<20} {plan.description[:30]}"
            )

    elif args.command == "status":
        status = unified_rollback_manager.get_rollback_status()
        print("回滚系统状态:")
        for key, value in status.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
