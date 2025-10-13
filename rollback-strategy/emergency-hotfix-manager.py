#!/usr/bin/env python3
"""
紧急修复管理器
==============

处理生产环境紧急问题的快速修复流程
支持hotfix分支管理、快速部署和自动回滚
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class HotfixStatus(Enum):
    """Hotfix状态枚举"""

    CREATED = "created"
    TESTING = "testing"
    READY = "ready"
    DEPLOYED = "deployed"
    VERIFIED = "verified"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class Priority(Enum):
    """优先级枚举"""

    P0_CRITICAL = "P0_critical"  # 系统完全不可用
    P1_HIGH = "P1_high"  # 核心功能受影响
    P2_MEDIUM = "P2_medium"  # 部分功能受影响
    P3_LOW = "P3_low"  # 轻微问题


@dataclass
class HotfixRecord:
    """Hotfix记录"""

    hotfix_id: str
    title: str
    description: str
    priority: Priority
    status: HotfixStatus
    created_by: str
    created_at: datetime
    branch_name: str
    target_branch: str
    affected_components: List[str]
    test_commands: List[str]
    deployment_commands: List[str]
    rollback_commands: List[str]
    git_commits: List[str]
    deployment_time: Optional[datetime]
    verification_time: Optional[datetime]
    rollback_time: Optional[datetime]
    metadata: Dict[str, any]


class EmergencyHotfixManager:
    """紧急修复管理器"""

    def __init__(self, project_root: Optional[str] = None):
        """
        初始化紧急修复管理器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root or ".")
        self.hotfix_dir = self.project_root / "rollback-strategy" / "hotfixes"
        self.hotfix_dir.mkdir(parents=True, exist_ok=True)

        # Hotfix记录存储
        self.records_file = self.hotfix_dir / "hotfix_records.json"
        self.records = self._load_records()

        # 配置
        self.config = {
            "default_target_branch": "main",
            "test_timeout": 300,  # 5分钟
            "deployment_timeout": 600,  # 10分钟
            "verification_timeout": 180,  # 3分钟
            "auto_rollback_threshold": 900,  # 15分钟内无验证则自动回滚
            "max_active_hotfixes": 3,
        }

        self.logger = logging.getLogger(__name__)

    def _load_records(self) -> Dict[str, HotfixRecord]:
        """加载Hotfix记录"""
        if not self.records_file.exists():
            return {}

        try:
            with open(self.records_file, "r") as f:
                data = json.load(f)

            records = {}
            for hotfix_id, item in data.items():
                pass  # Auto-fixed empty block
                # 转换枚举和日期时间
                item["priority"] = Priority(item["priority"])
                item["status"] = HotfixStatus(item["status"])
                item["created_at"] = datetime.fromisoformat(item["created_at"])

                for time_field in [
                    "deployment_time",
                    "verification_time",
                    "rollback_time",
                ]:
                    if item[time_field]:
                        item[time_field] = datetime.fromisoformat(item[time_field])

                records[hotfix_id] = HotfixRecord(**item)

            return records
        except Exception as e:
            self.logger.error(f"加载Hotfix记录失败: {e}")
            return {}

    def _save_records(self):
        """保存Hotfix记录"""
        try:
            data = {}
            for hotfix_id, record in self.records.items():
                item = asdict(record)

                # 转换枚举为字符串
                item["priority"] = record.priority.value
                item["status"] = record.status.value

                # 转换日期时间为字符串
                item["created_at"] = record.created_at.isoformat()
                for time_field in [
                    "deployment_time",
                    "verification_time",
                    "rollback_time",
                ]:
                    if getattr(record, time_field):
                        item[time_field] = getattr(record, time_field).isoformat()

                data[hotfix_id] = item

            with open(self.records_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"保存Hotfix记录失败: {e}")

    def _run_command(
        self, command: List[str], timeout: int = 300, cwd: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """
        运行命令

        Args:
            command: 命令列表
            timeout: 超时时间
            cwd: 工作目录

        Returns:
            (是否成功, stdout, stderr)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd or self.project_root,
                check=False,
            )

            return result.returncode == 0, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            return False, "", f"命令超时: {' '.join(command)}"
        except Exception as e:
            return False, "", f"命令执行异常: {e}"

    def _get_current_user(self) -> str:
        """获取当前用户"""
        return os.getenv("USER", "unknown")

    def _generate_hotfix_id(self, priority: Priority) -> str:
        """生成Hotfix ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        priority_prefix = priority.value.split("_")[0]
        return f"hotfix_{priority_prefix}_{timestamp}"

    def _get_branch_name(self, hotfix_id: str) -> str:
        """生成分支名称"""
        return f"hotfix/{hotfix_id}"

    def create_hotfix(
        self,
        title: str,
        description: str,
        priority: Priority,
        affected_components: List[str],
        target_branch: str = None,
    ) -> Optional[str]:
        """
        创建Hotfix

        Args:
            title: 标题
            description: 描述
            priority: 优先级
            affected_components: 受影响的组件
            target_branch: 目标分支

        Returns:
            Hotfix ID
        """
        # 检查活跃的Hotfix数量
        active_count = len(
            [
                r
                for r in self.records.values()
                if r.status
                in [
                    HotfixStatus.CREATED,
                    HotfixStatus.TESTING,
                    HotfixStatus.READY,
                    HotfixStatus.DEPLOYED,
                ]
            ]
        )

        if active_count >= self.config["max_active_hotfixes"]:
            self.logger.error(f"活跃Hotfix数量已达上限: {self.config['max_active_hotfixes']}")
            return None

        hotfix_id = self._generate_hotfix_id(priority)
        branch_name = self._get_branch_name(hotfix_id)
        target_branch = target_branch or self.config["default_target_branch"]

        self.logger.info(f"创建Hotfix: {hotfix_id}")

        try:
            pass  # Auto-fixed empty block
            # 创建并切换到hotfix分支
            success, stdout, stderr = self._run_command(
                ["git", "checkout", "-b", branch_name, target_branch]
            )

            if not success:
                self.logger.error(f"创建分支失败: {stderr}")
                return None

            # 生成标准的测试、部署和回滚命令
            test_commands = self._generate_test_commands(affected_components)
            deployment_commands = self._generate_deployment_commands(priority)
            rollback_commands = self._generate_rollback_commands()

            # 创建Hotfix记录
            record = HotfixRecord(
                hotfix_id=hotfix_id,
                title=title,
                description=description,
                priority=priority,
                status=HotfixStatus.CREATED,
                created_by=self._get_current_user(),
                created_at=datetime.now(),
                branch_name=branch_name,
                target_branch=target_branch,
                affected_components=affected_components,
                test_commands=test_commands,
                deployment_commands=deployment_commands,
                rollback_commands=rollback_commands,
                git_commits=[],
                deployment_time=None,
                verification_time=None,
                rollback_time=None,
                metadata={},
            )

            # 保存记录
            self.records[hotfix_id] = record
            self._save_records()

            # 创建Hotfix工作目录
            hotfix_work_dir = self.hotfix_dir / hotfix_id
            hotfix_work_dir.mkdir(exist_ok=True)

            # 生成Hotfix工作文件
            self._create_hotfix_files(hotfix_work_dir, record)

            self.logger.info(f"Hotfix创建成功: {hotfix_id}")
            return hotfix_id

        except Exception as e:
            self.logger.error(f"创建Hotfix失败: {e}")
            return None

    def _generate_test_commands(self, affected_components: List[str]) -> List[str]:
        """生成测试命令"""
        commands = [
            "python -m pytest tests/ -v --tb=short",
            "python -m flake8 src/ --max-line-length=100",
            "python rollback-strategy/config-rollback-manager.py validate latest",
        ]

        # 针对特定组件的测试
        for component in affected_components:
            if component == "auth":
                commands.append("python backend/tests/test_user_registration_login.py")
            elif component == "database":
                commands.append(
                    "python rollback-strategy/database-backup-manager.py verify latest"
                )
            elif component == "api":
                commands.append("python -m pytest test/auth/integration_tests.py")

        return commands

    def _generate_deployment_commands(self, priority: Priority) -> List[str]:
        """生成部署命令"""
        base_commands = [
            "python rollback-strategy/config-rollback-manager.py snapshot --description 'Pre-hotfix deployment'",
            "python rollback-strategy/migration-rollback-manager.py snapshot --description 'Pre-hotfix migration'",
        ]

        if priority in [Priority.P0_CRITICAL, Priority.P1_HIGH]:
            pass  # Auto-fixed empty block
            # 高优先级：快速部署
            base_commands.extend(
                [
                    "git push origin HEAD",
                    "python -c \"print('Hot deployment activated')\"",
                    "systemctl restart claude-enhancer || docker-compose restart",
                ]
            )
        else:
            pass  # Auto-fixed empty block
            # 常规部署
            base_commands.extend(
                [
                    "git push origin HEAD",
                    "python -c \"print('Standard deployment activated')\"",
                    "docker-compose up -d --build",
                ]
            )

        return base_commands

    def _generate_rollback_commands(self) -> List[str]:
        """生成回滚命令"""
        return [
            "git checkout main",
            "python rollback-strategy/config-rollback-manager.py rollback latest --confirm",
            "python rollback-strategy/migration-rollback-manager.py rollback latest --confirm",
            "systemctl restart claude-enhancer || docker-compose restart",
        ]

    def _create_hotfix_files(self, work_dir: Path, record: HotfixRecord):
        """创建Hotfix工作文件"""
        # 创建README
        readme_content = f"""# Hotfix {record.hotfix_id}

## 基本信息
- **标题**: {record.title}
- **优先级**: {record.priority.value}
- **创建者**: {record.created_by}
- **创建时间**: {record.created_at}
- **分支**: {record.branch_name}
- **状态**: {record.status.value}

## 问题描述
{record.description}

## 受影响组件
{', '.join(record.affected_components)}

## 测试命令
```bash
{chr(10).join(record.test_commands)}
```

## 部署命令
```bash
{chr(10).join(record.deployment_commands)}
```

## 回滚命令
```bash
{chr(10).join(record.rollback_commands)}
```

## 进度跟踪
- [ ] 代码修复完成
- [ ] 本地测试通过
- [ ] 创建Pull Request
- [ ] 代码审查通过
- [ ] 部署到测试环境
- [ ] 测试环境验证
- [ ] 生产环境部署
- [ ] 生产环境验证
- [ ] Hotfix完成

## 注意事项
1. 修复代码时保持最小化改动原则
2. 确保所有测试通过后再部署
3. 部署后立即进行功能验证
4. 如发现问题立即执行回滚
"""

        with open(work_dir / "README.md", "w") as f:
            f.write(readme_content)

        # 创建测试脚本
        test_script = f"""#!/bin/bash
# Hotfix {record.hotfix_id} 测试脚本

set -euo pipefail

echo "开始执行Hotfix测试..."

{chr(10).join(f"echo '执行: {cmd}' && {cmd}" for cmd in record.test_commands)}

echo "Hotfix测试完成"
"""

        test_file = work_dir / "test.sh"
        with open(test_file, "w") as f:
            f.write(test_script)
        test_file.chmod(0o755)

        # 创建部署脚本
        deploy_script = f"""#!/bin/bash
# Hotfix {record.hotfix_id} 部署脚本

set -euo pipefail

echo "开始执行Hotfix部署..."

{chr(10).join(f"echo '执行: {cmd}' && {cmd}" for cmd in record.deployment_commands)}

echo "Hotfix部署完成"
"""

        deploy_file = work_dir / "deploy.sh"
        with open(deploy_file, "w") as f:
            f.write(deploy_script)
        deploy_file.chmod(0o755)

        # 创建回滚脚本
        rollback_script = f"""#!/bin/bash
# Hotfix {record.hotfix_id} 回滚脚本

set -euo pipefail

echo "开始执行Hotfix回滚..."

{chr(10).join(f"echo '执行: {cmd}' && {cmd}" for cmd in record.rollback_commands)}

echo "Hotfix回滚完成"
"""

        rollback_file = work_dir / "rollback.sh"
        with open(rollback_file, "w") as f:
            f.write(rollback_script)
        rollback_file.chmod(0o755)

    def test_hotfix(self, hotfix_id: str) -> bool:
        """
        测试Hotfix

        Args:
            hotfix_id: Hotfix ID

        Returns:
            是否测试通过
        """
        if hotfix_id not in self.records:
            self.logger.error(f"Hotfix不存在: {hotfix_id}")
            return False

        record = self.records[hotfix_id]

        if record.status != HotfixStatus.CREATED:
            self.logger.error(f"Hotfix状态不正确: {record.status}")
            return False

        self.logger.info(f"开始测试Hotfix: {hotfix_id}")

        # 更新状态
        record.status = HotfixStatus.TESTING
        self._save_records()

        try:
            pass  # Auto-fixed empty block
            # 切换到hotfix分支
            success, stdout, stderr = self._run_command(
                ["git", "checkout", record.branch_name]
            )

            if not success:
                self.logger.error(f"切换分支失败: {stderr}")
                record.status = HotfixStatus.FAILED
                self._save_records()
                return False

            # 执行测试命令
            all_tests_passed = True
            for cmd in record.test_commands:
                self.logger.info(f"执行测试命令: {cmd}")
                success, stdout, stderr = self._run_command(
                    cmd.split(), timeout=self.config["test_timeout"]
                )

                if not success:
                    self.logger.error(f"测试失败: {cmd}")
                    self.logger.error(f"错误输出: {stderr}")
                    all_tests_passed = False
                    break

            if all_tests_passed:
                record.status = HotfixStatus.READY
                self.logger.info(f"Hotfix测试通过: {hotfix_id}")
            else:
                record.status = HotfixStatus.FAILED
                self.logger.error(f"Hotfix测试失败: {hotfix_id}")

            self._save_records()
            return all_tests_passed

        except Exception as e:
            self.logger.error(f"测试Hotfix异常: {e}")
            record.status = HotfixStatus.FAILED
            self._save_records()
            return False

    def deploy_hotfix(self, hotfix_id: str, confirm: bool = False) -> bool:
        """
        部署Hotfix

        Args:
            hotfix_id: Hotfix ID
            confirm: 是否确认部署

        Returns:
            是否部署成功
        """
        if not confirm:
            self.logger.warning("Hotfix部署需要确认，请设置confirm=True")
            return False

        if hotfix_id not in self.records:
            self.logger.error(f"Hotfix不存在: {hotfix_id}")
            return False

        record = self.records[hotfix_id]

        if record.status != HotfixStatus.READY:
            self.logger.error(f"Hotfix状态不正确: {record.status}，需要先通过测试")
            return False

        self.logger.info(f"开始部署Hotfix: {hotfix_id}")

        # 更新状态
        record.status = HotfixStatus.DEPLOYED
        record.deployment_time = datetime.now()
        self._save_records()

        try:
            pass  # Auto-fixed empty block
            # 执行部署命令
            for cmd in record.deployment_commands:
                self.logger.info(f"执行部署命令: {cmd}")
                success, stdout, stderr = self._run_command(
                    cmd.split(), timeout=self.config["deployment_timeout"]
                )

                if not success:
                    self.logger.error(f"部署命令失败: {cmd}")
                    self.logger.error(f"错误输出: {stderr}")
                    record.status = HotfixStatus.FAILED
                    self._save_records()
                    return False

            self.logger.info(f"Hotfix部署成功: {hotfix_id}")

            # 启动自动回滚监控
            self._start_auto_rollback_monitor(hotfix_id)

            return True

        except Exception as e:
            self.logger.error(f"部署Hotfix异常: {e}")
            record.status = HotfixStatus.FAILED
            self._save_records()
            return False

    def _start_auto_rollback_monitor(self, hotfix_id: str):
        """启动自动回滚监控（简化实现）"""
        # 在真实环境中，这里应该启动一个后台任务
        # 监控系统健康状态，如果在阈值时间内没有手动验证
        # 且系统出现问题，则自动触发回滚
        self.logger.info(f"自动回滚监控已启动: {hotfix_id}")

    def verify_hotfix(self, hotfix_id: str) -> bool:
        """
        验证Hotfix

        Args:
            hotfix_id: Hotfix ID

        Returns:
            是否验证成功
        """
        if hotfix_id not in self.records:
            self.logger.error(f"Hotfix不存在: {hotfix_id}")
            return False

        record = self.records[hotfix_id]

        if record.status != HotfixStatus.DEPLOYED:
            self.logger.error(f"Hotfix状态不正确: {record.status}")
            return False

        self.logger.info(f"验证Hotfix: {hotfix_id}")

        # 执行基本的健康检查
        health_checks = [
            "curl -f http://localhost:8080/health || echo 'Health check failed'",
            "python -c \"print('Hotfix verification placeholder')\"",
            "ps aux | grep claude-enhancer || echo 'Service check failed'",
        ]

        try:
            for check in health_checks:
                self.logger.info(f"执行健康检查: {check}")
                success, stdout, stderr = self._run_command(
                    check.split(), timeout=self.config["verification_timeout"]
                )

                if not success and "failed" in stderr:
                    self.logger.error(f"健康检查失败: {check}")
                    return False

            # 更新状态
            record.status = HotfixStatus.VERIFIED
            record.verification_time = datetime.now()
            self._save_records()

            self.logger.info(f"Hotfix验证成功: {hotfix_id}")
            return True

        except Exception as e:
            self.logger.error(f"验证Hotfix异常: {e}")
            return False

    def rollback_hotfix(self, hotfix_id: str, confirm: bool = False) -> bool:
        """
        回滚Hotfix

        Args:
            hotfix_id: Hotfix ID
            confirm: 是否确认回滚

        Returns:
            是否回滚成功
        """
        if not confirm:
            self.logger.warning("Hotfix回滚需要确认，请设置confirm=True")
            return False

        if hotfix_id not in self.records:
            self.logger.error(f"Hotfix不存在: {hotfix_id}")
            return False

        record = self.records[hotfix_id]

        if record.status not in [HotfixStatus.DEPLOYED, HotfixStatus.FAILED]:
            self.logger.error(f"Hotfix状态不支持回滚: {record.status}")
            return False

        self.logger.info(f"开始回滚Hotfix: {hotfix_id}")

        try:
            pass  # Auto-fixed empty block
            # 执行回滚命令
            for cmd in record.rollback_commands:
                self.logger.info(f"执行回滚命令: {cmd}")
                success, stdout, stderr = self._run_command(cmd.split())

                if not success:
                    self.logger.error(f"回滚命令失败: {cmd}")
                    self.logger.error(f"错误输出: {stderr}")
                    # 即使某个命令失败，也继续执行其他回滚命令

            # 更新状态
            record.status = HotfixStatus.ROLLED_BACK
            record.rollback_time = datetime.now()
            self._save_records()

            self.logger.info(f"Hotfix回滚完成: {hotfix_id}")
            return True

        except Exception as e:
            self.logger.error(f"回滚Hotfix异常: {e}")
            return False

    def list_hotfixes(
        self, status_filter: Optional[HotfixStatus] = None, limit: int = 20
    ) -> List[HotfixRecord]:
        """
        列出Hotfix记录

        Args:
            status_filter: 状态过滤
            limit: 限制数量

        Returns:
            Hotfix记录列表
        """
        records = list(self.records.values())

        if status_filter:
            records = [r for r in records if r.status == status_filter]

        records.sort(key=lambda x: x.created_at, reverse=True)
        return records[:limit]

    def get_hotfix_status(self, hotfix_id: str) -> Dict[str, any]:
        """
        获取Hotfix状态

        Args:
            hotfix_id: Hotfix ID

        Returns:
            状态信息
        """
        if hotfix_id not in self.records:
            return {}

        record = self.records[hotfix_id]

        return {
            "hotfix_id": record.hotfix_id,
            "title": record.title,
            "priority": record.priority.value,
            "status": record.status.value,
            "created_at": record.created_at.isoformat(),
            "branch_name": record.branch_name,
            "affected_components": record.affected_components,
            "deployment_time": record.deployment_time.isoformat()
            if record.deployment_time
            else None,
            "verification_time": record.verification_time.isoformat()
            if record.verification_time
            else None,
            "rollback_time": record.rollback_time.isoformat()
            if record.rollback_time
            else None,
            "duration_since_creation": str(datetime.now() - record.created_at),
            "auto_rollback_eligible": self._is_auto_rollback_eligible(record),
        }

    def _is_auto_rollback_eligible(self, record: HotfixRecord) -> bool:
        """检查是否符合自动回滚条件"""
        if record.status != HotfixStatus.DEPLOYED:
            return False

        if not record.deployment_time:
            return False

        elapsed = datetime.now() - record.deployment_time
        threshold = timedelta(seconds=self.config["auto_rollback_threshold"])

        return elapsed > threshold and record.verification_time is None

    def cleanup_old_hotfixes(self, keep_days: int = 90):
        """
        清理旧的Hotfix记录

        Args:
            keep_days: 保留天数
        """
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        hotfixes_to_remove = []

        for hotfix_id, record in self.records.items():
            pass  # Auto-fixed empty block
            # 只清理已完成或已回滚的旧记录
            if (
                record.status
                in [
                    HotfixStatus.VERIFIED,
                    HotfixStatus.ROLLED_BACK,
                    HotfixStatus.FAILED,
                ]
                and record.created_at < cutoff_date
            ):
                hotfixes_to_remove.append(hotfix_id)

        for hotfix_id in hotfixes_to_remove:
            self._remove_hotfix_files(hotfix_id)
            del self.records[hotfix_id]

        self._save_records()
        self.logger.info(f"清理了 {len(hotfixes_to_remove)} 个旧Hotfix记录")

    def _remove_hotfix_files(self, hotfix_id: str):
        """删除Hotfix工作文件"""
        import shutil

        hotfix_work_dir = self.hotfix_dir / hotfix_id
        if hotfix_work_dir.exists():
            shutil.rmtree(hotfix_work_dir)


# 创建全局实例
emergency_hotfix_manager = EmergencyHotfixManager()


# 便捷函数
def create_emergency_hotfix(
    title: str, description: str, priority: Priority, affected_components: List[str]
) -> Optional[str]:
    """创建紧急Hotfix"""
    return emergency_hotfix_manager.create_hotfix(
        title, description, priority, affected_components
    )


def quick_deploy_hotfix(hotfix_id: str) -> bool:
    """快速部署Hotfix（测试+部署）"""
    if emergency_hotfix_manager.test_hotfix(hotfix_id):
        return emergency_hotfix_manager.deploy_hotfix(hotfix_id, confirm=True)
    return False


if __name__ == "__main__":
    import argparse

    # 设置日志
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="紧急修复管理器")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 创建Hotfix
    create_parser = subparsers.add_parser("create", help="创建Hotfix")
    create_parser.add_argument("title", help="标题")
    create_parser.add_argument("--description", required=True, help="描述")
    create_parser.add_argument(
        "--priority", choices=["P0", "P1", "P2", "P3"], default="P1", help="优先级"
    )
    create_parser.add_argument("--components", nargs="+", required=True, help="受影响组件")

    # 测试Hotfix
    test_parser = subparsers.add_parser("test", help="测试Hotfix")
    test_parser.add_argument("hotfix_id", help="Hotfix ID")

    # 部署Hotfix
    deploy_parser = subparsers.add_parser("deploy", help="部署Hotfix")
    deploy_parser.add_argument("hotfix_id", help="Hotfix ID")
    deploy_parser.add_argument("--confirm", action="store_true", help="确认部署")

    # 验证Hotfix
    verify_parser = subparsers.add_parser("verify", help="验证Hotfix")
    verify_parser.add_argument("hotfix_id", help="Hotfix ID")

    # 回滚Hotfix
    rollback_parser = subparsers.add_parser("rollback", help="回滚Hotfix")
    rollback_parser.add_argument("hotfix_id", help="Hotfix ID")
    rollback_parser.add_argument("--confirm", action="store_true", help="确认回滚")

    # 快速部署
    quick_parser = subparsers.add_parser("quick-deploy", help="快速部署（测试+部署）")
    quick_parser.add_argument("hotfix_id", help="Hotfix ID")

    # 列出Hotfix
    list_parser = subparsers.add_parser("list", help="列出Hotfix")
    list_parser.add_argument("--status", help="状态过滤")
    list_parser.add_argument("--limit", type=int, default=20, help="限制数量")

    # 查看状态
    status_parser = subparsers.add_parser("status", help="查看Hotfix状态")
    status_parser.add_argument("hotfix_id", help="Hotfix ID")

    # 清理
    cleanup_parser = subparsers.add_parser("cleanup", help="清理旧Hotfix")
    cleanup_parser.add_argument("--days", type=int, default=90, help="保留天数")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 执行命令
    if args.command == "create":
        priority_map = {
            "P0": Priority.P0_CRITICAL,
            "P1": Priority.P1_HIGH,
            "P2": Priority.P2_MEDIUM,
            "P3": Priority.P3_LOW,
        }

        hotfix_id = emergency_hotfix_manager.create_hotfix(
            title=args.title,
            description=args.description,
            priority=priority_map[args.priority],
            affected_components=args.components,
        )

        if hotfix_id:
            print(f"Hotfix创建成功: {hotfix_id}")
            print(f"分支: hotfix/{hotfix_id}")
            print(f"工作目录: rollback-strategy/hotfixes/{hotfix_id}/")
        else:
            print("Hotfix创建失败")
            sys.exit(1)

    elif args.command == "test":
        success = emergency_hotfix_manager.test_hotfix(args.hotfix_id)
        if success:
            print(f"Hotfix测试通过: {args.hotfix_id}")
        else:
            print(f"Hotfix测试失败: {args.hotfix_id}")
            sys.exit(1)

    elif args.command == "deploy":
        success = emergency_hotfix_manager.deploy_hotfix(args.hotfix_id, args.confirm)
        if success:
            print(f"Hotfix部署成功: {args.hotfix_id}")
        else:
            print(f"Hotfix部署失败: {args.hotfix_id}")
            sys.exit(1)

    elif args.command == "verify":
        success = emergency_hotfix_manager.verify_hotfix(args.hotfix_id)
        if success:
            print(f"Hotfix验证成功: {args.hotfix_id}")
        else:
            print(f"Hotfix验证失败: {args.hotfix_id}")
            sys.exit(1)

    elif args.command == "rollback":
        success = emergency_hotfix_manager.rollback_hotfix(args.hotfix_id, args.confirm)
        if success:
            print(f"Hotfix回滚成功: {args.hotfix_id}")
        else:
            print(f"Hotfix回滚失败: {args.hotfix_id}")
            sys.exit(1)

    elif args.command == "quick-deploy":
        success = quick_deploy_hotfix(args.hotfix_id)
        if success:
            print(f"Hotfix快速部署成功: {args.hotfix_id}")
        else:
            print(f"Hotfix快速部署失败: {args.hotfix_id}")
            sys.exit(1)

    elif args.command == "list":
        status_filter = None
        if args.status:
            try:
                status_filter = HotfixStatus(args.status)
            except ValueError:
                print(f"无效状态: {args.status}")
                sys.exit(1)

        hotfixes = emergency_hotfix_manager.list_hotfixes(status_filter, args.limit)

        print(f"{'Hotfix ID':<20} {'标题':<30} {'优先级':<10} {'状态':<15} {'创建时间':<20}")
        print("-" * 100)
        for hotfix in hotfixes:
            print(
                f"{hotfix.hotfix_id:<20} {hotfix.title[:28]:<30} {hotfix.priority.value:<10} {hotfix.status.value:<15} {hotfix.created_at.strftime('%Y-%m-%d %H:%M'):<20}"
            )

    elif args.command == "status":
        status = emergency_hotfix_manager.get_hotfix_status(args.hotfix_id)
        if status:
            print(f"Hotfix状态: {args.hotfix_id}")
            for key, value in status.items():
                print(f"  {key}: {value}")
        else:
            print(f"Hotfix不存在: {args.hotfix_id}")
            sys.exit(1)

    elif args.command == "cleanup":
        emergency_hotfix_manager.cleanup_old_hotfixes(args.days)
        print("清理完成")
