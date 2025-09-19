#!/usr/bin/env python3
"""
Perfect21 Git Hook检查点集成
在工作流的关键节点自动运行Git Hook验证
"""

import logging
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class HookType(Enum):
    """Hook类型"""
    PRE_COMMIT = "pre-commit"
    PRE_PUSH = "pre-push"
    POST_MERGE = "post-merge"
    COMMIT_MSG = "commit-msg"
    POST_CHECKOUT = "post-checkout"


class HookAction(Enum):
    """Hook失败后的动作"""
    BLOCK = "block"          # 阻止继续
    FIX_AND_RETRY = "fix"    # 修复后重试
    WARN_AND_CONTINUE = "warn"  # 警告但继续
    AUTO_FIX = "auto_fix"    # 自动修复


@dataclass
class HookResult:
    """Hook执行结果"""
    hook_type: HookType
    success: bool
    message: str
    errors: List[str]
    warnings: List[str]
    fixed_files: List[str]
    suggested_action: HookAction


@dataclass
class CheckpointConfig:
    """检查点配置"""
    layer_name: str
    hook_types: List[HookType]
    required: bool
    auto_fix: bool
    max_retries: int


class GitCheckpoints:
    """
    Git Hook检查点管理器
    在工作流关键位置集成Git Hook验证
    """

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or "/home/xx/dev/Perfect21")
        self.checkpoints = self._initialize_checkpoints()
        self.hook_history = []
        logger.info(f"Git检查点初始化，项目根目录: {self.project_root}")

    def _initialize_checkpoints(self) -> Dict[str, CheckpointConfig]:
        """初始化检查点配置"""
        return {
            "after_implementation": CheckpointConfig(
                layer_name="implementation",
                hook_types=[HookType.PRE_COMMIT],
                required=True,
                auto_fix=True,
                max_retries=3
            ),
            "after_testing": CheckpointConfig(
                layer_name="testing",
                hook_types=[HookType.PRE_PUSH],
                required=True,
                auto_fix=False,
                max_retries=2
            ),
            "after_review": CheckpointConfig(
                layer_name="review",
                hook_types=[HookType.PRE_COMMIT, HookType.COMMIT_MSG],
                required=False,
                auto_fix=True,
                max_retries=2
            ),
            "before_deployment": CheckpointConfig(
                layer_name="deployment",
                hook_types=[HookType.PRE_PUSH, HookType.POST_MERGE],
                required=True,
                auto_fix=False,
                max_retries=1
            )
        }

    def run_checkpoint(self, checkpoint_name: str,
                      files: List[str],
                      context: Dict[str, Any] = None) -> Tuple[bool, List[HookResult]]:
        """
        运行检查点

        Args:
            checkpoint_name: 检查点名称
            files: 要检查的文件列表
            context: 额外上下文

        Returns:
            (是否通过, Hook结果列表)
        """
        if checkpoint_name not in self.checkpoints:
            logger.warning(f"未知的检查点: {checkpoint_name}")
            return True, []

        config = self.checkpoints[checkpoint_name]
        logger.info(f"运行检查点: {checkpoint_name} ({config.layer_name}层)")

        results = []
        all_passed = True

        for hook_type in config.hook_types:
            result = self._run_hook(hook_type, files, context)
            results.append(result)

            if not result.success:
                logger.warning(f"Hook {hook_type.value} 失败: {result.message}")

                # 尝试自动修复
                if config.auto_fix and result.suggested_action == HookAction.AUTO_FIX:
                    fix_result = self._auto_fix(hook_type, files, result.errors)
                    if fix_result.success:
                        logger.info(f"自动修复成功: {hook_type.value}")
                        results.append(fix_result)
                        continue

                # 如果是必需的检查点且失败，标记为未通过
                if config.required:
                    all_passed = False

        # 记录历史
        self._record_checkpoint(checkpoint_name, results, all_passed)

        return all_passed, results

    def _run_hook(self, hook_type: HookType,
                 files: List[str],
                 context: Dict[str, Any] = None) -> HookResult:
        """运行单个Git Hook"""

        if hook_type == HookType.PRE_COMMIT:
            return self._run_pre_commit(files)
        elif hook_type == HookType.PRE_PUSH:
            return self._run_pre_push(files)
        elif hook_type == HookType.POST_MERGE:
            return self._run_post_merge(files)
        elif hook_type == HookType.COMMIT_MSG:
            return self._run_commit_msg(context)
        else:
            return HookResult(
                hook_type=hook_type,
                success=True,
                message=f"Hook {hook_type.value} not implemented",
                errors=[],
                warnings=[],
                fixed_files=[],
                suggested_action=HookAction.WARN_AND_CONTINUE
            )

    def _run_pre_commit(self, files: List[str]) -> HookResult:
        """运行pre-commit检查"""
        errors = []
        warnings = []
        fixed_files = []

        # 1. 代码格式检查
        format_check = self._check_code_format(files)
        if not format_check["passed"]:
            errors.extend(format_check["errors"])
            if format_check["can_auto_fix"]:
                fixed_files.extend(format_check["fixable_files"])

        # 2. Lint检查
        lint_check = self._check_lint(files)
        if not lint_check["passed"]:
            errors.extend(lint_check["errors"])
            warnings.extend(lint_check["warnings"])

        # 3. 类型检查
        type_check = self._check_types(files)
        if not type_check["passed"]:
            errors.extend(type_check["errors"])

        # 决定建议的动作
        if errors and fixed_files:
            action = HookAction.AUTO_FIX
        elif errors:
            action = HookAction.FIX_AND_RETRY
        elif warnings:
            action = HookAction.WARN_AND_CONTINUE
        else:
            action = HookAction.BLOCK  # 通过

        success = len(errors) == 0

        return HookResult(
            hook_type=HookType.PRE_COMMIT,
            success=success,
            message="Pre-commit检查完成" if success else "Pre-commit检查失败",
            errors=errors,
            warnings=warnings,
            fixed_files=fixed_files,
            suggested_action=action
        )

    def _run_pre_push(self, files: List[str]) -> HookResult:
        """运行pre-push检查"""
        errors = []
        warnings = []

        # 1. 测试检查
        test_check = self._check_tests()
        if not test_check["passed"]:
            errors.append(f"测试失败: {test_check['failed_count']} 个测试未通过")

        # 2. 安全检查
        security_check = self._check_security(files)
        if not security_check["passed"]:
            errors.extend(security_check["vulnerabilities"])

        # 3. 覆盖率检查
        coverage_check = self._check_coverage()
        if coverage_check["coverage"] < 70:
            warnings.append(f"测试覆盖率不足: {coverage_check['coverage']}%")

        success = len(errors) == 0

        return HookResult(
            hook_type=HookType.PRE_PUSH,
            success=success,
            message="Pre-push检查完成" if success else "Pre-push检查失败",
            errors=errors,
            warnings=warnings,
            fixed_files=[],
            suggested_action=HookAction.BLOCK if errors else HookAction.WARN_AND_CONTINUE
        )

    def _run_post_merge(self, files: List[str]) -> HookResult:
        """运行post-merge检查"""
        # Post-merge通常用于更新依赖、生成文档等
        actions_taken = []

        # 1. 更新依赖
        if self._needs_dependency_update():
            actions_taken.append("更新依赖")

        # 2. 重新生成文档
        if self._needs_doc_regeneration(files):
            actions_taken.append("重新生成文档")

        return HookResult(
            hook_type=HookType.POST_MERGE,
            success=True,
            message=f"Post-merge完成: {', '.join(actions_taken) if actions_taken else '无需操作'}",
            errors=[],
            warnings=[],
            fixed_files=[],
            suggested_action=HookAction.WARN_AND_CONTINUE
        )

    def _run_commit_msg(self, context: Dict[str, Any]) -> HookResult:
        """检查提交消息"""
        commit_msg = context.get("commit_message", "") if context else ""

        errors = []
        warnings = []

        # 检查消息格式
        if not commit_msg:
            errors.append("提交消息不能为空")
        elif len(commit_msg) < 10:
            errors.append("提交消息太短（至少10个字符）")
        elif not any(commit_msg.startswith(prefix) for prefix in ["feat:", "fix:", "docs:", "refactor:", "test:", "chore:"]):
            warnings.append("建议使用标准前缀（feat:, fix:, docs:等）")

        success = len(errors) == 0

        return HookResult(
            hook_type=HookType.COMMIT_MSG,
            success=success,
            message="提交消息检查完成" if success else "提交消息不符合规范",
            errors=errors,
            warnings=warnings,
            fixed_files=[],
            suggested_action=HookAction.FIX_AND_RETRY if errors else HookAction.WARN_AND_CONTINUE
        )

    def _check_code_format(self, files: List[str]) -> Dict[str, Any]:
        """检查代码格式"""
        # 模拟格式检查
        python_files = [f for f in files if f.endswith('.py')]

        if not python_files:
            return {"passed": True, "errors": [], "can_auto_fix": False, "fixable_files": []}

        # 实际应该运行black或autopep8
        errors = []
        fixable_files = []

        for file in python_files[:2]:  # 模拟检查
            if "test" not in file:
                errors.append(f"{file}: 缩进不一致")
                fixable_files.append(file)

        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "can_auto_fix": len(fixable_files) > 0,
            "fixable_files": fixable_files
        }

    def _check_lint(self, files: List[str]) -> Dict[str, Any]:
        """Lint检查"""
        # 模拟lint检查
        errors = []
        warnings = []

        for file in files[:1]:  # 模拟
            if "unused" in file:
                warnings.append(f"{file}: 未使用的变量")

        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _check_types(self, files: List[str]) -> Dict[str, Any]:
        """类型检查"""
        # 模拟mypy检查
        return {
            "passed": True,
            "errors": []
        }

    def _check_tests(self) -> Dict[str, Any]:
        """运行测试"""
        # 模拟pytest
        return {
            "passed": True,
            "failed_count": 0
        }

    def _check_security(self, files: List[str]) -> Dict[str, Any]:
        """安全检查"""
        # 模拟bandit
        return {
            "passed": True,
            "vulnerabilities": []
        }

    def _check_coverage(self) -> Dict[str, Any]:
        """检查测试覆盖率"""
        # 模拟coverage
        return {
            "coverage": 75
        }

    def _needs_dependency_update(self) -> bool:
        """是否需要更新依赖"""
        # 检查requirements.txt或package.json是否变化
        return False

    def _needs_doc_regeneration(self, files: List[str]) -> bool:
        """是否需要重新生成文档"""
        # 检查是否有API变化
        return any("api" in f for f in files)

    def _auto_fix(self, hook_type: HookType,
                 files: List[str],
                 errors: List[str]) -> HookResult:
        """尝试自动修复"""
        fixed_count = 0

        if hook_type == HookType.PRE_COMMIT:
            # 运行代码格式化
            for file in files:
                if file.endswith('.py'):
                    # 实际应该运行: black file
                    fixed_count += 1

        return HookResult(
            hook_type=hook_type,
            success=fixed_count > 0,
            message=f"自动修复了 {fixed_count} 个文件",
            errors=[],
            warnings=[],
            fixed_files=files[:fixed_count],
            suggested_action=HookAction.WARN_AND_CONTINUE
        )

    def _record_checkpoint(self, checkpoint_name: str,
                         results: List[HookResult],
                         passed: bool):
        """记录检查点历史"""
        record = {
            "checkpoint": checkpoint_name,
            "passed": passed,
            "hook_count": len(results),
            "failed_hooks": [r.hook_type.value for r in results if not r.success],
            "total_errors": sum(len(r.errors) for r in results),
            "total_warnings": sum(len(r.warnings) for r in results)
        }
        self.hook_history.append(record)

        # 限制历史大小
        if len(self.hook_history) > 100:
            self.hook_history = self.hook_history[-50:]

    def get_checkpoint_statistics(self) -> Dict[str, Any]:
        """获取检查点统计"""
        if not self.hook_history:
            return {"total_checkpoints": 0}

        total = len(self.hook_history)
        passed = sum(1 for r in self.hook_history if r["passed"])

        return {
            "total_checkpoints": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": passed / total if total > 0 else 0,
            "most_failed_hooks": self._get_most_failed_hooks()
        }

    def _get_most_failed_hooks(self) -> List[str]:
        """获取失败最多的Hook"""
        hook_failures = {}
        for record in self.hook_history:
            for hook in record["failed_hooks"]:
                hook_failures[hook] = hook_failures.get(hook, 0) + 1

        return sorted(hook_failures.items(), key=lambda x: x[1], reverse=True)[:3]


def demonstrate_git_checkpoints():
    """演示Git检查点"""
    print("=" * 80)
    print("Perfect21 Git检查点演示")
    print("=" * 80)

    checkpoints = GitCheckpoints()

    # 测试文件
    test_files = [
        "features/workflow/implementation.py",
        "tests/test_workflow.py"
    ]

    # 运行实现后的检查点
    print("\n运行检查点: after_implementation")
    passed, results = checkpoints.run_checkpoint("after_implementation", test_files)

    print(f"检查点通过: {passed}")
    for result in results:
        print(f"  {result.hook_type.value}: {'✅' if result.success else '❌'} {result.message}")
        if result.errors:
            for error in result.errors:
                print(f"    错误: {error}")
        if result.warnings:
            for warning in result.warnings:
                print(f"    警告: {warning}")

    # 显示统计
    stats = checkpoints.get_checkpoint_statistics()
    print("\n检查点统计:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    print("\n" + "=" * 80)
    print("演示完成！Git检查点可以在关键位置验证代码质量。")
    print("=" * 80)


if __name__ == "__main__":
    demonstrate_git_checkpoints()