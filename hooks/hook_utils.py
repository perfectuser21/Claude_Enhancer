#!/usr/bin/env python3
"""
Perfect21 Hook工具库 - 统一的Hook检查逻辑
供Git Hooks和Claude Code Hooks共享使用
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from features.guardian.rule_guardian import get_rule_guardian, ViolationType
    GUARDIAN_AVAILABLE = True
except ImportError:
    GUARDIAN_AVAILABLE = False
    print("⚠️ Rule Guardian不可用，使用基础检查")

class HookChecker:
    """统一的Hook检查器"""

    def __init__(self):
        self.guardian = get_rule_guardian() if GUARDIAN_AVAILABLE else None
        self.log_dir = project_root / ".perfect21"
        self.log_dir.mkdir(exist_ok=True)

    def check_agent_selection(self, agents: List[str], task_type: str = None) -> Tuple[bool, str]:
        """检查Agent选择是否符合规则"""
        if self.guardian:
            context = {
                "selected_agents": agents,
                "task_type": task_type or "general",
                "execution_mode": "parallel" if len(agents) > 1 else "sequential"
            }
            passed, violations = self.guardian.check_rule("agent_selection", context)

            if not passed:
                messages = []
                for v in violations:
                    messages.append(f"❌ {v.rule_name}: {v.suggestion}")
                return False, "\n".join(messages)
            return True, f"✅ Agent选择通过: {len(agents)}个Agent"
        else:
            # 基础检查
            if len(agents) < 3:
                return False, f"❌ Agent数量不足: {len(agents)}个 (需要至少3个)"
            return True, f"✅ Agent选择通过: {len(agents)}个"

    def check_code_quality(self, files: List[str] = None) -> Tuple[bool, str]:
        """检查代码质量"""
        results = []
        passed = True

        # 检查Python文件语法
        if files:
            for file in files:
                if file.endswith('.py'):
                    result = self._check_python_syntax(file)
                    if not result[0]:
                        passed = False
                        results.append(f"❌ {file}: {result[1]}")

        # 使用Guardian进行额外检查
        if self.guardian:
            context = {"quality_requirements": True}
            g_passed, violations = self.guardian.check_rule("before_execution", context)
            if not g_passed:
                passed = False
                for v in violations:
                    results.append(f"⚠️ {v.suggestion}")

        if passed:
            return True, "✅ 代码质量检查通过"
        return False, "\n".join(results)

    def check_commit_message(self, message: str) -> Tuple[bool, str]:
        """检查提交消息格式"""
        valid_prefixes = ["feat:", "fix:", "docs:", "test:", "refactor:", "perf:", "chore:"]

        if self.guardian:
            context = {"commit_message": message}
            passed, violations = self.guardian.check_rule("before_commit", context)

            if not passed:
                return False, f"❌ 提交消息格式错误。使用: {', '.join(valid_prefixes)}"
            return True, "✅ 提交消息格式正确"
        else:
            # 基础检查
            if any(message.startswith(prefix) for prefix in valid_prefixes):
                return True, "✅ 提交消息格式正确"
            return False, f"❌ 提交消息必须以这些前缀开始: {', '.join(valid_prefixes)}"

    def check_test_results(self, test_failed: bool, feedback_triggered: bool = False) -> Tuple[bool, str]:
        """检查测试结果和反馈循环"""
        if self.guardian:
            context = {
                "test_failed": test_failed,
                "feedback_triggered": feedback_triggered
            }
            passed, violations = self.guardian.check_rule("after_test", context)

            if not passed:
                return False, "❌ 测试失败必须触发反馈循环，让原Agent修复"
            return True, "✅ 测试处理正确"
        else:
            if test_failed and not feedback_triggered:
                return False, "❌ 测试失败但未触发反馈循环"
            return True, "✅ 测试处理正确"

    def get_health_score(self) -> int:
        """获取系统健康分数"""
        if self.guardian:
            status = self.guardian.get_current_status()
            return status.get("health_score", 100)
        return 100

    def log_check_result(self, hook_name: str, passed: bool, message: str):
        """记录检查结果"""
        log_file = self.log_dir / "hook_checks.log"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "hook": hook_name,
            "passed": passed,
            "message": message
        }

        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _check_python_syntax(self, filepath: str) -> Tuple[bool, str]:
        """检查Python文件语法"""
        try:
            with open(filepath, 'r') as f:
                code = f.read()
            compile(code, filepath, 'exec')
            return True, "语法正确"
        except SyntaxError as e:
            return False, f"语法错误: {e}"
        except Exception as e:
            return False, f"检查失败: {e}"

    def suggest_agents(self, task_description: str) -> List[str]:
        """根据任务描述建议Agent组合"""
        task_lower = task_description.lower()

        # 任务类型映射到Agent组合
        suggestions = {
            "auth": ["backend-architect", "security-auditor", "test-engineer",
                    "api-designer", "database-specialist"],
            "api": ["api-designer", "backend-architect", "test-engineer",
                   "technical-writer"],
            "database": ["database-specialist", "backend-architect",
                        "performance-engineer"],
            "frontend": ["frontend-specialist", "ux-designer", "test-engineer"],
            "test": ["test-engineer", "e2e-test-specialist", "performance-tester"]
        }

        # 匹配任务类型
        for keyword, agents in suggestions.items():
            if keyword in task_lower:
                return agents

        # 默认组合
        return ["backend-architect", "test-engineer", "code-reviewer"]


def get_hook_checker() -> HookChecker:
    """获取Hook检查器实例"""
    return HookChecker()


# 便捷函数
def quick_check_agents(agents: List[str], task_type: str = None) -> Tuple[bool, str]:
    """快速检查Agent选择"""
    checker = get_hook_checker()
    return checker.check_agent_selection(agents, task_type)


def quick_check_commit(message: str) -> Tuple[bool, str]:
    """快速检查提交消息"""
    checker = get_hook_checker()
    return checker.check_commit_message(message)


def quick_health_check() -> int:
    """快速健康检查"""
    checker = get_hook_checker()
    return checker.get_health_score()


if __name__ == "__main__":
    # 测试Hook工具库
    print("🧪 测试Hook工具库...")

    checker = get_hook_checker()

    # 测试Agent选择
    print("\n1. 测试Agent选择:")
    passed, msg = checker.check_agent_selection(["backend-architect"], "api")
    print(f"   1个Agent: {msg}")

    passed, msg = checker.check_agent_selection(
        ["backend-architect", "test-engineer", "api-designer"], "api"
    )
    print(f"   3个Agent: {msg}")

    # 测试提交消息
    print("\n2. 测试提交消息:")
    passed, msg = checker.check_commit_message("feat: 添加用户登录功能")
    print(f"   正确格式: {msg}")

    passed, msg = checker.check_commit_message("添加功能")
    print(f"   错误格式: {msg}")

    # 测试健康分数
    print("\n3. 系统健康分数:")
    score = checker.get_health_score()
    print(f"   当前分数: {score}/100")

    print("\n✅ Hook工具库测试完成！")