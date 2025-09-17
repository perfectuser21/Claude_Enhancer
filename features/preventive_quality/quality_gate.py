#!/usr/bin/env python3
"""
Perfect21 质量门
================

定义和执行各种质量检查，确保代码质量和执行安全
"""

import json
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import logging

class CheckSeverity(Enum):
    """检查严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class CheckStatus(Enum):
    """检查状态"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"

@dataclass
class CheckResult:
    """检查结果"""
    check_name: str
    status: CheckStatus
    severity: CheckSeverity
    message: str
    details: Dict[str, Any]
    suggestions: List[str]
    execution_time: float
    timestamp: str

@dataclass
class QualityCheck:
    """质量检查定义"""
    name: str
    description: str
    category: str
    severity: CheckSeverity
    enabled: bool
    check_function: Callable[[], CheckResult]
    dependencies: List[str]
    applicable_contexts: List[str]  # 适用的上下文

class QualityGate:
    """质量门"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)

        # 注册所有检查
        self.checks = {}
        self._register_all_checks()

    def _register_all_checks(self):
        """注册所有检查"""

        # Git相关检查
        self._register_git_checks()

        # 代码质量检查
        self._register_code_quality_checks()

        # 工作空间检查
        self._register_workspace_checks()

        # 环境检查
        self._register_environment_checks()

        # 依赖检查
        self._register_dependency_checks()

        # 安全检查
        self._register_security_checks()

    def _register_git_checks(self):
        """注册Git相关检查"""

        self.checks["git_status_clean"] = QualityCheck(
            name="git_status_clean",
            description="检查Git工作目录是否干净",
            category="git",
            severity=CheckSeverity.WARNING,
            enabled=True,
            check_function=self._check_git_status_clean,
            dependencies=[],
            applicable_contexts=["all"]
        )

        self.checks["git_branch_valid"] = QualityCheck(
            name="git_branch_valid",
            description="检查当前分支是否有效",
            category="git",
            severity=CheckSeverity.ERROR,
            enabled=True,
            check_function=self._check_git_branch_valid,
            dependencies=[],
            applicable_contexts=["all"]
        )

        self.checks["git_remote_sync"] = QualityCheck(
            name="git_remote_sync",
            description="检查与远程仓库的同步状态",
            category="git",
            severity=CheckSeverity.WARNING,
            enabled=True,
            check_function=self._check_git_remote_sync,
            dependencies=["git_branch_valid"],
            applicable_contexts=["all"]
        )

    def _register_code_quality_checks(self):
        """注册代码质量检查"""

        self.checks["syntax_check"] = QualityCheck(
            name="syntax_check",
            description="检查Python文件语法",
            category="code_quality",
            severity=CheckSeverity.ERROR,
            enabled=True,
            check_function=self._check_python_syntax,
            dependencies=[],
            applicable_contexts=["python", "all"]
        )

        self.checks["import_check"] = QualityCheck(
            name="import_check",
            description="检查Python导入是否正确",
            category="code_quality",
            severity=CheckSeverity.ERROR,
            enabled=True,
            check_function=self._check_python_imports,
            dependencies=["syntax_check"],
            applicable_contexts=["python", "all"]
        )

        self.checks["file_structure"] = QualityCheck(
            name="file_structure",
            description="检查项目文件结构",
            category="code_quality",
            severity=CheckSeverity.WARNING,
            enabled=True,
            check_function=self._check_file_structure,
            dependencies=[],
            applicable_contexts=["all"]
        )

    def _register_workspace_checks(self):
        """注册工作空间检查"""

        self.checks["workspace_conflicts"] = QualityCheck(
            name="workspace_conflicts",
            description="检查工作空间冲突",
            category="workspace",
            severity=CheckSeverity.WARNING,
            enabled=True,
            check_function=self._check_workspace_conflicts,
            dependencies=[],
            applicable_contexts=["workspace"]
        )

        self.checks["workspace_ports"] = QualityCheck(
            name="workspace_ports",
            description="检查工作空间端口可用性",
            category="workspace",
            severity=CheckSeverity.ERROR,
            enabled=True,
            check_function=self._check_workspace_ports,
            dependencies=[],
            applicable_contexts=["workspace"]
        )

    def _register_environment_checks(self):
        """注册环境检查"""

        self.checks["disk_space"] = QualityCheck(
            name="disk_space",
            description="检查磁盘空间",
            category="environment",
            severity=CheckSeverity.WARNING,
            enabled=True,
            check_function=self._check_disk_space,
            dependencies=[],
            applicable_contexts=["all"]
        )

        self.checks["python_version"] = QualityCheck(
            name="python_version",
            description="检查Python版本",
            category="environment",
            severity=CheckSeverity.INFO,
            enabled=True,
            check_function=self._check_python_version,
            dependencies=[],
            applicable_contexts=["python", "all"]
        )

    def _register_dependency_checks(self):
        """注册依赖检查"""

        self.checks["perfect21_structure"] = QualityCheck(
            name="perfect21_structure",
            description="检查Perfect21项目结构",
            category="dependencies",
            severity=CheckSeverity.ERROR,
            enabled=True,
            check_function=self._check_perfect21_structure,
            dependencies=[],
            applicable_contexts=["all"]
        )

        self.checks["core_agents_available"] = QualityCheck(
            name="core_agents_available",
            description="检查核心Agent是否可用",
            category="dependencies",
            severity=CheckSeverity.CRITICAL,
            enabled=True,
            check_function=self._check_core_agents_available,
            dependencies=["perfect21_structure"],
            applicable_contexts=["all"]
        )

    def _register_security_checks(self):
        """注册安全检查"""

        self.checks["sensitive_files"] = QualityCheck(
            name="sensitive_files",
            description="检查敏感文件",
            category="security",
            severity=CheckSeverity.WARNING,
            enabled=True,
            check_function=self._check_sensitive_files,
            dependencies=[],
            applicable_contexts=["all"]
        )

        self.checks["permissions"] = QualityCheck(
            name="permissions",
            description="检查文件权限",
            category="security",
            severity=CheckSeverity.WARNING,
            enabled=True,
            check_function=self._check_file_permissions,
            dependencies=[],
            applicable_contexts=["all"]
        )

    # Git检查实现

    def _check_git_status_clean(self) -> CheckResult:
        """检查Git状态是否干净"""
        start_time = datetime.now()

        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            if result.stdout.strip():
                return CheckResult(
                    check_name="git_status_clean",
                    status=CheckStatus.FAILED,
                    severity=CheckSeverity.WARNING,
                    message="工作目录有未提交的更改",
                    details={"uncommitted_files": result.stdout.strip().split('\n')},
                    suggestions=[
                        "提交或暂存当前更改",
                        "使用 git stash 暂存更改",
                        "检查是否有未跟踪的重要文件"
                    ],
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )
            else:
                return CheckResult(
                    check_name="git_status_clean",
                    status=CheckStatus.PASSED,
                    severity=CheckSeverity.INFO,
                    message="工作目录干净",
                    details={},
                    suggestions=[],
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )

        except subprocess.CalledProcessError as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return CheckResult(
                check_name="git_status_clean",
                status=CheckStatus.FAILED,
                severity=CheckSeverity.ERROR,
                message=f"Git状态检查失败: {e.stderr}",
                details={"error": str(e)},
                suggestions=["检查Git仓库是否正确初始化"],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

    def _check_git_branch_valid(self) -> CheckResult:
        """检查当前分支是否有效"""
        start_time = datetime.now()

        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )

            execution_time = (datetime.now() - start_time).total_seconds()
            current_branch = result.stdout.strip()

            if not current_branch:
                return CheckResult(
                    check_name="git_branch_valid",
                    status=CheckStatus.FAILED,
                    severity=CheckSeverity.ERROR,
                    message="无法获取当前分支",
                    details={},
                    suggestions=["检查Git仓库状态", "确保在正确的分支上"],
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )

            # 检查分支是否符合命名规范
            valid_prefixes = ['feature/', 'bugfix/', 'hotfix/', 'release/', 'main', 'develop']
            is_valid_name = any(
                current_branch.startswith(prefix) or current_branch == prefix.rstrip('/')
                for prefix in valid_prefixes
            )

            if not is_valid_name:
                return CheckResult(
                    check_name="git_branch_valid",
                    status=CheckStatus.FAILED,
                    severity=CheckSeverity.WARNING,
                    message=f"分支名称不符合规范: {current_branch}",
                    details={"current_branch": current_branch, "valid_prefixes": valid_prefixes},
                    suggestions=[
                        "使用规范的分支命名",
                        "考虑重命名分支",
                        f"有效前缀: {', '.join(valid_prefixes)}"
                    ],
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )

            return CheckResult(
                check_name="git_branch_valid",
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message=f"当前分支有效: {current_branch}",
                details={"current_branch": current_branch},
                suggestions=[],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        except subprocess.CalledProcessError as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return CheckResult(
                check_name="git_branch_valid",
                status=CheckStatus.FAILED,
                severity=CheckSeverity.ERROR,
                message=f"分支检查失败: {e.stderr}",
                details={"error": str(e)},
                suggestions=["检查Git仓库是否正确初始化"],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

    def _check_git_remote_sync(self) -> CheckResult:
        """检查与远程仓库的同步状态"""
        start_time = datetime.now()

        try:
            # 获取当前分支
            current_branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = current_branch_result.stdout.strip()

            # 检查远程分支是否存在
            remote_check = subprocess.run(
                ['git', 'rev-parse', '--verify', f'origin/{current_branch}'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            if remote_check.returncode != 0:
                return CheckResult(
                    check_name="git_remote_sync",
                    status=CheckStatus.NOT_APPLICABLE,
                    severity=CheckSeverity.INFO,
                    message="远程分支不存在，跳过同步检查",
                    details={"current_branch": current_branch},
                    suggestions=["如需要，推送分支到远程仓库"],
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )

            # 检查是否有未推送的提交
            ahead_result = subprocess.run(
                ['git', 'rev-list', '--count', f'origin/{current_branch}..HEAD'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )

            # 检查是否有未拉取的提交
            behind_result = subprocess.run(
                ['git', 'rev-list', '--count', f'HEAD..origin/{current_branch}'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )

            commits_ahead = int(ahead_result.stdout.strip())
            commits_behind = int(behind_result.stdout.strip())

            if commits_behind > 0:
                return CheckResult(
                    check_name="git_remote_sync",
                    status=CheckStatus.FAILED,
                    severity=CheckSeverity.WARNING,
                    message=f"本地分支落后远程 {commits_behind} 个提交",
                    details={
                        "commits_ahead": commits_ahead,
                        "commits_behind": commits_behind,
                        "current_branch": current_branch
                    },
                    suggestions=[
                        "执行 git pull 拉取最新更改",
                        "解决可能的合并冲突"
                    ],
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )

            if commits_ahead > 0:
                return CheckResult(
                    check_name="git_remote_sync",
                    status=CheckStatus.PASSED,
                    severity=CheckSeverity.INFO,
                    message=f"本地分支领先远程 {commits_ahead} 个提交",
                    details={
                        "commits_ahead": commits_ahead,
                        "commits_behind": commits_behind,
                        "current_branch": current_branch
                    },
                    suggestions=["考虑推送更改到远程仓库"],
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )

            return CheckResult(
                check_name="git_remote_sync",
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message="本地分支与远程同步",
                details={
                    "commits_ahead": commits_ahead,
                    "commits_behind": commits_behind,
                    "current_branch": current_branch
                },
                suggestions=[],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        except subprocess.CalledProcessError as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return CheckResult(
                check_name="git_remote_sync",
                status=CheckStatus.FAILED,
                severity=CheckSeverity.WARNING,
                message=f"远程同步检查失败: {e.stderr}",
                details={"error": str(e)},
                suggestions=["检查网络连接", "确认远程仓库配置"],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

    # 代码质量检查实现

    def _check_python_syntax(self) -> CheckResult:
        """检查Python文件语法"""
        start_time = datetime.now()

        python_files = list(self.project_root.rglob("*.py"))
        syntax_errors = []

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    compile(f.read(), str(py_file), 'exec')
            except SyntaxError as e:
                syntax_errors.append({
                    "file": str(py_file.relative_to(self.project_root)),
                    "line": e.lineno,
                    "error": str(e)
                })
            except UnicodeDecodeError:
                # 跳过二进制文件
                continue

        execution_time = (datetime.now() - start_time).total_seconds()

        if syntax_errors:
            return CheckResult(
                check_name="syntax_check",
                status=CheckStatus.FAILED,
                severity=CheckSeverity.ERROR,
                message=f"发现 {len(syntax_errors)} 个语法错误",
                details={"syntax_errors": syntax_errors},
                suggestions=[
                    "修复语法错误",
                    "使用IDE或linter检查代码",
                    "运行 python -m py_compile 检查特定文件"
                ],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        return CheckResult(
            check_name="syntax_check",
            status=CheckStatus.PASSED,
            severity=CheckSeverity.INFO,
            message=f"检查了 {len(python_files)} 个Python文件，无语法错误",
            details={"files_checked": len(python_files)},
            suggestions=[],
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )

    def _check_python_imports(self) -> CheckResult:
        """检查Python导入是否正确"""
        start_time = datetime.now()

        import_errors = []
        main_files = [
            self.project_root / "main" / "cli.py",
            self.project_root / "main" / "perfect21.py"
        ]

        for py_file in main_files:
            if not py_file.exists():
                continue

            try:
                result = subprocess.run(
                    ['python3', '-m', 'py_compile', str(py_file)],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    import_errors.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "error": result.stderr
                    })

            except Exception as e:
                import_errors.append({
                    "file": str(py_file.relative_to(self.project_root)),
                    "error": str(e)
                })

        execution_time = (datetime.now() - start_time).total_seconds()

        if import_errors:
            return CheckResult(
                check_name="import_check",
                status=CheckStatus.FAILED,
                severity=CheckSeverity.ERROR,
                message=f"发现 {len(import_errors)} 个导入错误",
                details={"import_errors": import_errors},
                suggestions=[
                    "检查模块路径是否正确",
                    "确认所有依赖都已安装",
                    "检查PYTHONPATH设置"
                ],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        return CheckResult(
            check_name="import_check",
            status=CheckStatus.PASSED,
            severity=CheckSeverity.INFO,
            message="导入检查通过",
            details={"files_checked": len(main_files)},
            suggestions=[],
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )

    def _check_file_structure(self) -> CheckResult:
        """检查项目文件结构"""
        start_time = datetime.now()

        required_dirs = ['main', 'features', 'modules', 'core']
        required_files = ['main/cli.py', 'main/perfect21.py', 'CLAUDE.md']

        missing_dirs = []
        missing_files = []

        for dir_name in required_dirs:
            if not (self.project_root / dir_name).exists():
                missing_dirs.append(dir_name)

        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)

        execution_time = (datetime.now() - start_time).total_seconds()

        if missing_dirs or missing_files:
            return CheckResult(
                check_name="file_structure",
                status=CheckStatus.FAILED,
                severity=CheckSeverity.WARNING,
                message="项目结构不完整",
                details={
                    "missing_dirs": missing_dirs,
                    "missing_files": missing_files
                },
                suggestions=[
                    "创建缺失的目录",
                    "检查文件是否被意外删除",
                    "参考Perfect21标准项目结构"
                ],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        return CheckResult(
            check_name="file_structure",
            status=CheckStatus.PASSED,
            severity=CheckSeverity.INFO,
            message="项目结构完整",
            details={},
            suggestions=[],
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )

    # 工作空间检查实现

    def _check_workspace_conflicts(self) -> CheckResult:
        """检查工作空间冲突"""
        start_time = datetime.now()

        try:
            from features.multi_workspace import WorkspaceManager

            workspace_manager = WorkspaceManager(str(self.project_root))
            active_workspaces = [
                ws for ws in workspace_manager.list_workspaces()
                if ws['status'] == 'active'
            ]

            conflicts = []
            for workspace in active_workspaces:
                workspace_id = workspace['id']
                conflict_info = workspace_manager.detect_conflicts(workspace_id)

                if conflict_info.get('direct_conflicts') or conflict_info.get('potential_conflicts'):
                    conflicts.append({
                        "workspace": workspace_id,
                        "direct_conflicts": conflict_info.get('direct_conflicts', []),
                        "potential_conflicts": conflict_info.get('potential_conflicts', [])
                    })

            execution_time = (datetime.now() - start_time).total_seconds()

            if conflicts:
                return CheckResult(
                    check_name="workspace_conflicts",
                    status=CheckStatus.FAILED,
                    severity=CheckSeverity.WARNING,
                    message=f"发现 {len(conflicts)} 个工作空间冲突",
                    details={"conflicts": conflicts},
                    suggestions=[
                        "解决工作空间冲突",
                        "考虑合并或暂停冲突的工作空间",
                        "使用独立的文件进行开发"
                    ],
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )

            return CheckResult(
                check_name="workspace_conflicts",
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message=f"检查了 {len(active_workspaces)} 个活跃工作空间，无冲突",
                details={"active_workspaces": len(active_workspaces)},
                suggestions=[],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        except ImportError:
            execution_time = (datetime.now() - start_time).total_seconds()
            return CheckResult(
                check_name="workspace_conflicts",
                status=CheckStatus.SKIPPED,
                severity=CheckSeverity.INFO,
                message="工作空间模块未安装，跳过检查",
                details={},
                suggestions=[],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

    def _check_workspace_ports(self) -> CheckResult:
        """检查工作空间端口可用性"""
        start_time = datetime.now()

        try:
            import socket
            from features.multi_workspace import WorkspaceManager

            workspace_manager = WorkspaceManager(str(self.project_root))
            workspaces = workspace_manager.list_workspaces()

            port_conflicts = []
            for workspace in workspaces:
                dev_port = workspace['dev_port']
                api_port = workspace.get('api_port')

                # 检查端口是否被占用
                for port in [dev_port, api_port]:
                    if port and self._is_port_in_use(port):
                        port_conflicts.append({
                            "workspace": workspace['id'],
                            "port": port,
                            "type": "dev" if port == dev_port else "api"
                        })

            execution_time = (datetime.now() - start_time).total_seconds()

            if port_conflicts:
                return CheckResult(
                    check_name="workspace_ports",
                    status=CheckStatus.FAILED,
                    severity=CheckSeverity.ERROR,
                    message=f"发现 {len(port_conflicts)} 个端口冲突",
                    details={"port_conflicts": port_conflicts},
                    suggestions=[
                        "停止占用端口的进程",
                        "重新分配工作空间端口",
                        "检查其他服务是否使用相同端口"
                    ],
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )

            return CheckResult(
                check_name="workspace_ports",
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message=f"检查了 {len(workspaces)} 个工作空间的端口，无冲突",
                details={"workspaces_checked": len(workspaces)},
                suggestions=[],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        except ImportError:
            execution_time = (datetime.now() - start_time).total_seconds()
            return CheckResult(
                check_name="workspace_ports",
                status=CheckStatus.SKIPPED,
                severity=CheckSeverity.INFO,
                message="工作空间模块未安装，跳过检查",
                details={},
                suggestions=[],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

    def _is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('localhost', port))
                return False
        except OSError:
            return True

    # 环境检查实现

    def _check_disk_space(self) -> CheckResult:
        """检查磁盘空间"""
        start_time = datetime.now()

        try:
            import shutil
            total, used, free = shutil.disk_usage(str(self.project_root))

            # 转换为GB
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            usage_percent = (used / total) * 100

            execution_time = (datetime.now() - start_time).total_seconds()

            if free_gb < 1.0:  # 少于1GB
                return CheckResult(
                    check_name="disk_space",
                    status=CheckStatus.FAILED,
                    severity=CheckSeverity.CRITICAL,
                    message=f"磁盘空间不足: 仅剩 {free_gb:.1f}GB",
                    details={
                        "total_gb": round(total_gb, 1),
                        "used_gb": round(used_gb, 1),
                        "free_gb": round(free_gb, 1),
                        "usage_percent": round(usage_percent, 1)
                    },
                    suggestions=[
                        "清理不必要的文件",
                        "删除临时文件和缓存",
                        "考虑扩展存储空间"
                    ],
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )

            elif usage_percent > 90:
                return CheckResult(
                    check_name="disk_space",
                    status=CheckStatus.FAILED,
                    severity=CheckSeverity.WARNING,
                    message=f"磁盘使用率过高: {usage_percent:.1f}%",
                    details={
                        "total_gb": round(total_gb, 1),
                        "used_gb": round(used_gb, 1),
                        "free_gb": round(free_gb, 1),
                        "usage_percent": round(usage_percent, 1)
                    },
                    suggestions=[
                        "清理不必要的文件",
                        "监控磁盘使用情况"
                    ],
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )

            return CheckResult(
                check_name="disk_space",
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message=f"磁盘空间充足: {free_gb:.1f}GB 可用",
                details={
                    "total_gb": round(total_gb, 1),
                    "used_gb": round(used_gb, 1),
                    "free_gb": round(free_gb, 1),
                    "usage_percent": round(usage_percent, 1)
                },
                suggestions=[],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return CheckResult(
                check_name="disk_space",
                status=CheckStatus.FAILED,
                severity=CheckSeverity.WARNING,
                message=f"磁盘空间检查失败: {str(e)}",
                details={"error": str(e)},
                suggestions=["检查文件系统状态"],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

    def _check_python_version(self) -> CheckResult:
        """检查Python版本"""
        start_time = datetime.now()

        try:
            import sys

            version = sys.version_info
            version_str = f"{version.major}.{version.minor}.{version.micro}"

            execution_time = (datetime.now() - start_time).total_seconds()

            if version.major < 3 or (version.major == 3 and version.minor < 8):
                return CheckResult(
                    check_name="python_version",
                    status=CheckStatus.FAILED,
                    severity=CheckSeverity.WARNING,
                    message=f"Python版本过低: {version_str}",
                    details={
                        "current_version": version_str,
                        "recommended_version": "3.8+"
                    },
                    suggestions=[
                        "升级到Python 3.8或更高版本",
                        "某些功能可能不可用"
                    ],
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )

            return CheckResult(
                check_name="python_version",
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message=f"Python版本: {version_str}",
                details={"current_version": version_str},
                suggestions=[],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return CheckResult(
                check_name="python_version",
                status=CheckStatus.FAILED,
                severity=CheckSeverity.ERROR,
                message=f"Python版本检查失败: {str(e)}",
                details={"error": str(e)},
                suggestions=["检查Python安装"],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

    # 依赖检查实现

    def _check_perfect21_structure(self) -> CheckResult:
        """检查Perfect21项目结构"""
        start_time = datetime.now()

        required_components = {
            'core/claude-code-unified-agents': '核心Agent目录',
            'features': '功能模块目录',
            'main': '主程序目录',
            'modules': '工具模块目录',
            'CLAUDE.md': '项目文档'
        }

        missing_components = []
        for component, description in required_components.items():
            if not (self.project_root / component).exists():
                missing_components.append({
                    "component": component,
                    "description": description
                })

        execution_time = (datetime.now() - start_time).total_seconds()

        if missing_components:
            return CheckResult(
                check_name="perfect21_structure",
                status=CheckStatus.FAILED,
                severity=CheckSeverity.ERROR,
                message=f"Perfect21结构不完整，缺少 {len(missing_components)} 个组件",
                details={"missing_components": missing_components},
                suggestions=[
                    "检查Perfect21安装是否完整",
                    "重新初始化Perfect21项目",
                    "参考官方文档补全结构"
                ],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        return CheckResult(
            check_name="perfect21_structure",
            status=CheckStatus.PASSED,
            severity=CheckSeverity.INFO,
            message="Perfect21项目结构完整",
            details={"components_checked": len(required_components)},
            suggestions=[],
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )

    def _check_core_agents_available(self) -> CheckResult:
        """检查核心Agent是否可用"""
        start_time = datetime.now()

        agents_dir = self.project_root / "core" / "claude-code-unified-agents" / ".claude" / "agents"

        if not agents_dir.exists():
            execution_time = (datetime.now() - start_time).total_seconds()
            return CheckResult(
                check_name="core_agents_available",
                status=CheckStatus.FAILED,
                severity=CheckSeverity.CRITICAL,
                message="核心Agent目录不存在",
                details={"agents_dir": str(agents_dir)},
                suggestions=[
                    "检查claude-code-unified-agents是否正确安装",
                    "重新克隆或下载核心Agent",
                    "确认项目结构正确"
                ],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        # 统计可用的Agent
        agent_categories = ['business', 'development', 'infrastructure', 'quality']
        available_agents = 0
        category_counts = {}

        for category in agent_categories:
            category_dir = agents_dir / category
            if category_dir.exists():
                agent_files = list(category_dir.glob("*.md"))
                category_counts[category] = len(agent_files)
                available_agents += len(agent_files)
            else:
                category_counts[category] = 0

        execution_time = (datetime.now() - start_time).total_seconds()

        if available_agents < 20:  # 期望至少有20个Agent
            return CheckResult(
                check_name="core_agents_available",
                status=CheckStatus.FAILED,
                severity=CheckSeverity.WARNING,
                message=f"可用Agent数量不足: {available_agents}个",
                details={
                    "available_agents": available_agents,
                    "category_counts": category_counts
                },
                suggestions=[
                    "检查Agent文件是否完整",
                    "重新下载claude-code-unified-agents",
                    "验证Agent配置文件"
                ],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        return CheckResult(
            check_name="core_agents_available",
            status=CheckStatus.PASSED,
            severity=CheckSeverity.INFO,
            message=f"核心Agent可用: {available_agents}个",
            details={
                "available_agents": available_agents,
                "category_counts": category_counts
            },
            suggestions=[],
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )

    # 安全检查实现

    def _check_sensitive_files(self) -> CheckResult:
        """检查敏感文件"""
        start_time = datetime.now()

        sensitive_patterns = [
            "*.key", "*.pem", "*.p12", "*.pfx",
            "*.env", ".env.*",
            "*.secret", "*_secret*",
            "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
            "*.credentials", "*password*", "*passwd*"
        ]

        sensitive_files = []
        for pattern in sensitive_patterns:
            matches = list(self.project_root.rglob(pattern))
            for match in matches:
                # 排除一些已知的安全文件
                if not any(exclude in str(match) for exclude in ['.git', '__pycache__', '.perfect21']):
                    sensitive_files.append(str(match.relative_to(self.project_root)))

        execution_time = (datetime.now() - start_time).total_seconds()

        if sensitive_files:
            return CheckResult(
                check_name="sensitive_files",
                status=CheckStatus.FAILED,
                severity=CheckSeverity.WARNING,
                message=f"发现 {len(sensitive_files)} 个潜在敏感文件",
                details={"sensitive_files": sensitive_files},
                suggestions=[
                    "检查敏感文件是否应该提交到版本控制",
                    "添加到.gitignore以防止意外提交",
                    "考虑使用环境变量存储敏感信息"
                ],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        return CheckResult(
            check_name="sensitive_files",
            status=CheckStatus.PASSED,
            severity=CheckSeverity.INFO,
            message="未发现明显的敏感文件",
            details={},
            suggestions=[],
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )

    def _check_file_permissions(self) -> CheckResult:
        """检查文件权限"""
        start_time = datetime.now()

        # 检查关键文件的权限
        key_files = [
            'main/cli.py',
            'main/perfect21.py',
            'CLAUDE.md'
        ]

        permission_issues = []

        for file_path in key_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    stat = full_path.stat()
                    mode = oct(stat.st_mode)[-3:]

                    # 检查是否有执行权限（对于.py文件）
                    if file_path.endswith('.py') and not os.access(full_path, os.X_OK):
                        permission_issues.append({
                            "file": file_path,
                            "issue": "缺少执行权限",
                            "current_mode": mode
                        })

                    # 检查是否有过宽的权限
                    if mode.endswith('7'):  # 其他用户有写权限
                        permission_issues.append({
                            "file": file_path,
                            "issue": "权限过宽",
                            "current_mode": mode
                        })

                except Exception as e:
                    permission_issues.append({
                        "file": file_path,
                        "issue": f"权限检查失败: {str(e)}",
                        "current_mode": "unknown"
                    })

        execution_time = (datetime.now() - start_time).total_seconds()

        if permission_issues:
            return CheckResult(
                check_name="permissions",
                status=CheckStatus.FAILED,
                severity=CheckSeverity.WARNING,
                message=f"发现 {len(permission_issues)} 个权限问题",
                details={"permission_issues": permission_issues},
                suggestions=[
                    "调整文件权限",
                    "使用 chmod 命令修正权限",
                    "确保安全性和可执行性平衡"
                ],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        return CheckResult(
            check_name="permissions",
            status=CheckStatus.PASSED,
            severity=CheckSeverity.INFO,
            message=f"检查了 {len(key_files)} 个关键文件，权限正常",
            details={"files_checked": len(key_files)},
            suggestions=[],
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )

    # 质量门执行

    def run_checks(
        self,
        context: str = "all",
        enabled_only: bool = True,
        categories: Optional[List[str]] = None
    ) -> List[CheckResult]:
        """运行质量检查"""

        checks_to_run = []

        for check_name, check in self.checks.items():
            # 过滤条件
            if enabled_only and not check.enabled:
                continue

            if context not in check.applicable_contexts and "all" not in check.applicable_contexts:
                continue

            if categories and check.category not in categories:
                continue

            checks_to_run.append(check)

        # 按依赖关系排序
        sorted_checks = self._sort_checks_by_dependencies(checks_to_run)

        # 执行检查
        results = []
        for check in sorted_checks:
            try:
                result = check.check_function()
                results.append(result)
                self.logger.info(f"质量检查完成: {check.name} - {result.status.value}")
            except Exception as e:
                error_result = CheckResult(
                    check_name=check.name,
                    status=CheckStatus.FAILED,
                    severity=CheckSeverity.ERROR,
                    message=f"检查执行失败: {str(e)}",
                    details={"error": str(e)},
                    suggestions=["检查系统环境", "查看详细错误日志"],
                    execution_time=0.0,
                    timestamp=datetime.now().isoformat()
                )
                results.append(error_result)
                self.logger.error(f"质量检查失败: {check.name} - {str(e)}")

        return results

    def _sort_checks_by_dependencies(self, checks: List[QualityCheck]) -> List[QualityCheck]:
        """按依赖关系排序检查"""
        sorted_checks = []
        remaining_checks = checks.copy()
        check_names = {check.name for check in checks}

        while remaining_checks:
            # 找到没有未满足依赖的检查
            ready_checks = []
            for check in remaining_checks:
                deps_satisfied = all(
                    dep in [c.name for c in sorted_checks] or dep not in check_names
                    for dep in check.dependencies
                )
                if deps_satisfied:
                    ready_checks.append(check)

            if not ready_checks:
                # 存在循环依赖，按原顺序添加剩余检查
                sorted_checks.extend(remaining_checks)
                break

            # 添加就绪的检查
            for check in ready_checks:
                sorted_checks.append(check)
                remaining_checks.remove(check)

        return sorted_checks

    def get_check_summary(self, results: List[CheckResult]) -> Dict[str, Any]:
        """获取检查摘要"""
        if not results:
            return {"message": "无检查结果"}

        total = len(results)
        passed = len([r for r in results if r.status == CheckStatus.PASSED])
        failed = len([r for r in results if r.status == CheckStatus.FAILED])
        skipped = len([r for r in results if r.status == CheckStatus.SKIPPED])

        # 按严重程度统计
        severity_counts = {}
        for result in results:
            if result.status == CheckStatus.FAILED:
                severity = result.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # 按类别统计
        category_counts = {}
        for check_name, check in self.checks.items():
            result = next((r for r in results if r.check_name == check_name), None)
            if result:
                category_counts[check.category] = category_counts.get(check.category, 0) + 1

        total_time = sum(r.execution_time for r in results)

        return {
            "总检查数": total,
            "通过": passed,
            "失败": failed,
            "跳过": skipped,
            "成功率": f"{(passed/total)*100:.1f}%" if total > 0 else "0%",
            "按严重程度统计": severity_counts,
            "按类别统计": category_counts,
            "总执行时间": f"{total_time:.2f}秒",
            "检查时间": datetime.now().isoformat()
        }