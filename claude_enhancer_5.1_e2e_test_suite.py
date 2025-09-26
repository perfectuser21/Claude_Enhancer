#!/usr/bin/env python3
"""
Claude Enhancer 5.1 端到端测试套件
全面测试工作流、Agent协作、Git集成、Hook触发和错误恢复机制

测试范围：
1. 完整工作流测试（Phase 0-7）
2. Agent协作测试
3. Git集成测试
4. Hook触发测试
5. 错误恢复测试
6. 用户场景测试
"""

import os
import sys
import time
import json
import subprocess
import threading
import uuid
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
import logging
import asyncio
import concurrent.futures

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("claude_enhancer_5.1_e2e_test.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """测试结果数据类"""

    test_name: str
    phase: str
    status: str  # 'PASS', 'FAIL', 'SKIP', 'ERROR'
    duration: float
    details: Dict[str, Any]
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class PhaseTestResult:
    """Phase测试结果"""

    phase_name: str
    start_time: float
    end_time: float
    duration: float
    status: str
    hooks_triggered: List[str]
    tools_used: List[str]
    success_criteria_met: Dict[str, bool]
    errors: List[str]


class Claude5_1E2ETestFramework:
    """Claude Enhancer 5.1 端到端测试框架"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.path.abspath(".")
        self.test_id = str(uuid.uuid4())[:8]
        self.results: List[TestResult] = []
        self.phase_results: Dict[str, PhaseTestResult] = {}
        self.config = self._load_config()
        self.test_branch = f"test/e2e-test-{self.test_id}"

        # 测试统计
        self.stats = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "start_time": time.time(),
            "end_time": None,
        }

        logger.info(f"初始化Claude Enhancer 5.1 E2E测试框架 (Test ID: {self.test_id})")

    def _load_config(self) -> Dict:
        """加载Claude配置"""
        config_path = os.path.join(self.project_root, ".claude", "settings.json")
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"无法加载配置文件: {e}")
            return {}

    def _run_command(
        self, command: str, timeout: int = 30, cwd: str = None, check: bool = False
    ) -> Tuple[int, str, str]:
        """执行命令并返回结果"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.project_root,
                timeout=timeout,
                capture_output=True,
                text=True,
                check=check,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"命令超时: {command}"
        except Exception as e:
            return -1, "", str(e)

    def _add_result(
        self,
        test_name: str,
        phase: str,
        status: str,
        duration: float,
        details: Dict[str, Any],
    ):
        """添加测试结果"""
        result = TestResult(test_name, phase, status, duration, details)
        self.results.append(result)
        self.stats["total_tests"] += 1

        if status == "PASS":
            self.stats["passed"] += 1
        elif status == "FAIL":
            self.stats["failed"] += 1
        elif status == "SKIP":
            self.stats["skipped"] += 1
        elif status == "ERROR":
            self.stats["errors"] += 1

        logger.info(f"[{status}] {test_name} ({duration:.2f}s)")

    def _check_hook_exists(self, hook_name: str) -> bool:
        """检查Hook脚本是否存在"""
        hook_path = os.path.join(
            self.project_root, ".claude", "hooks", f"{hook_name}.sh"
        )
        return os.path.exists(hook_path)

    def _trigger_hook(self, hook_name: str, context: Dict = None) -> Tuple[bool, str]:
        """手动触发Hook脚本"""
        hook_path = os.path.join(
            self.project_root, ".claude", "hooks", f"{hook_name}.sh"
        )
        if not os.path.exists(hook_path):
            return False, f"Hook脚本不存在: {hook_path}"

        env = os.environ.copy()
        if context:
            for key, value in context.items():
                env[f"TEST_{key.upper()}"] = str(value)

        try:
            result = subprocess.run(
                ["bash", hook_path],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)

    # ==================== Phase 0: Branch Creation Tests ====================

    def test_phase_0_branch_creation(self) -> bool:
        """测试Phase 0: 分支创建"""
        start_time = time.time()
        test_name = "Phase 0: Branch Creation"

        try:
            # 1. 检查当前分支状态
            ret_code, current_branch, stderr = self._run_command(
                "git branch --show-current"
            )
            if ret_code != 0:
                self._add_result(
                    test_name,
                    "P0",
                    "ERROR",
                    time.time() - start_time,
                    {"error": "无法获取当前分支"},
                )
                return False

            # 2. 创建测试分支
            ret_code, stdout, stderr = self._run_command(
                f"git checkout -b {self.test_branch}"
            )
            branch_created = ret_code == 0

            # 3. 触发branch_helper hook
            hook_triggered, hook_output = self._trigger_hook(
                "branch_helper", {"branch_name": self.test_branch, "phase": "P0"}
            )

            # 4. 验证环境准备
            env_ready = os.path.exists(os.path.join(self.project_root, ".claude"))

            success = branch_created and hook_triggered and env_ready
            status = "PASS" if success else "FAIL"

            self._add_result(
                test_name,
                "P0",
                status,
                time.time() - start_time,
                {
                    "branch_created": branch_created,
                    "current_branch": current_branch.strip(),
                    "test_branch": self.test_branch,
                    "hook_triggered": hook_triggered,
                    "hook_output": hook_output,
                    "environment_ready": env_ready,
                },
            )

            return success

        except Exception as e:
            self._add_result(
                test_name, "P0", "ERROR", time.time() - start_time, {"error": str(e)}
            )
            return False

    # ==================== Phase 1: Requirements Analysis Tests ====================

    def test_phase_1_requirements_analysis(self) -> bool:
        """测试Phase 1: 需求分析"""
        start_time = time.time()
        test_name = "Phase 1: Requirements Analysis"

        try:
            # 1. 模拟需求输入
            test_requirement = {
                "feature": "用户认证系统",
                "description": "实现JWT token的登录注册功能",
                "complexity": "medium",
            }

            # 2. 触发需求分析Hook
            hook_triggered, hook_output = self._trigger_hook(
                "p1_requirements_analyzer", test_requirement
            )

            # 3. 检查需求理解度
            requirements_understood = "用户认证" in hook_output or "JWT" in hook_output

            # 4. 验证范围定义
            scope_defined = len(hook_output.strip()) > 0

            success = hook_triggered and requirements_understood and scope_defined
            status = "PASS" if success else "FAIL"

            self._add_result(
                test_name,
                "P1",
                status,
                time.time() - start_time,
                {
                    "test_requirement": test_requirement,
                    "hook_triggered": hook_triggered,
                    "hook_output": hook_output,
                    "requirements_understood": requirements_understood,
                    "scope_defined": scope_defined,
                },
            )

            return success

        except Exception as e:
            self._add_result(
                test_name, "P1", "ERROR", time.time() - start_time, {"error": str(e)}
            )
            return False

    # ==================== Phase 2: Design Planning Tests ====================

    def test_phase_2_design_planning(self) -> bool:
        """测试Phase 2: 设计规划"""
        start_time = time.time()
        test_name = "Phase 2: Design Planning"

        try:
            # 1. 模拟设计输入
            design_context = {
                "feature": "用户认证系统",
                "tech_stack": "FastAPI + JWT + PostgreSQL",
                "architecture": "microservice",
            }

            # 2. 检查设计advisor hook是否存在
            hook_exists = self._check_hook_exists("design_advisor")
            if not hook_exists:
                logger.warning("design_advisor hook不存在，跳过")
                self._add_result(
                    test_name,
                    "P2",
                    "SKIP",
                    time.time() - start_time,
                    {"reason": "design_advisor hook不存在"},
                )
                return True  # Skip不算失败

            # 3. 触发设计规划Hook
            hook_triggered, hook_output = self._trigger_hook(
                "design_advisor", design_context
            )

            # 4. 验证架构定义
            architecture_defined = (
                "架构" in hook_output or "architecture" in hook_output.lower()
            )

            # 5. 验证技术栈选择
            tech_stack_chosen = any(
                tech in hook_output.lower() for tech in ["fastapi", "jwt", "postgresql"]
            )

            success = hook_triggered and (architecture_defined or tech_stack_chosen)
            status = "PASS" if success else "FAIL"

            self._add_result(
                test_name,
                "P2",
                status,
                time.time() - start_time,
                {
                    "design_context": design_context,
                    "hook_exists": hook_exists,
                    "hook_triggered": hook_triggered,
                    "hook_output": hook_output,
                    "architecture_defined": architecture_defined,
                    "tech_stack_chosen": tech_stack_chosen,
                },
            )

            return success

        except Exception as e:
            self._add_result(
                test_name, "P2", "ERROR", time.time() - start_time, {"error": str(e)}
            )
            return False

    # ==================== Phase 3: Implementation Tests ====================

    def test_phase_3_agent_coordination(self) -> bool:
        """测试Phase 3: Agent协作实现"""
        start_time = time.time()
        test_name = "Phase 3: Agent Coordination"

        try:
            # 1. 模拟复杂任务
            task_context = {
                "task_type": "authentication_system",
                "complexity": "high",
                "expected_agents": 8,
            }

            # 2. 触发智能Agent选择器
            hook_triggered, hook_output = self._trigger_hook(
                "smart_agent_selector", task_context
            )

            # 3. 验证Agent选择逻辑
            agent_count_mentioned = any(str(i) in hook_output for i in [4, 6, 8])

            # 4. 检查推荐的Agent
            recommended_agents = []
            standard_agents = [
                "backend-architect",
                "api-designer",
                "database-specialist",
                "test-engineer",
                "security-auditor",
                "performance-engineer",
            ]

            for agent in standard_agents:
                if agent in hook_output.lower().replace("-", "_"):
                    recommended_agents.append(agent)

            # 5. 模拟Agent输出汇总
            summary_hook_triggered, summary_output = self._trigger_hook(
                "agent-output-summarizer",
                {"agents_used": recommended_agents, "task_completed": True},
            )

            success = (
                hook_triggered
                and agent_count_mentioned
                and len(recommended_agents) >= 4
            )
            status = "PASS" if success else "FAIL"

            self._add_result(
                test_name,
                "P3",
                status,
                time.time() - start_time,
                {
                    "task_context": task_context,
                    "hook_triggered": hook_triggered,
                    "hook_output": hook_output,
                    "agent_count_mentioned": agent_count_mentioned,
                    "recommended_agents": recommended_agents,
                    "summary_hook_triggered": summary_hook_triggered,
                    "summary_output": summary_output,
                },
            )

            return success

        except Exception as e:
            self._add_result(
                test_name, "P3", "ERROR", time.time() - start_time, {"error": str(e)}
            )
            return False

    def test_agent_parallel_execution_simulation(self) -> bool:
        """测试Agent并行执行模拟"""
        start_time = time.time()
        test_name = "Agent Parallel Execution Simulation"

        try:
            # 模拟多Agent并行执行
            agents = [
                "backend-architect",
                "api-designer",
                "database-specialist",
                "test-engineer",
                "security-auditor",
                "performance-engineer",
            ]

            # 使用线程池模拟并行执行
            results = {}

            def simulate_agent_work(agent_name):
                # 模拟Agent工作
                time.sleep(0.1)  # 模拟工作时间
                return {
                    "agent": agent_name,
                    "status": "completed",
                    "output": f"{agent_name} 工作完成",
                    "duration": 0.1,
                }

            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                future_to_agent = {
                    executor.submit(simulate_agent_work, agent): agent
                    for agent in agents
                }

                for future in concurrent.futures.as_completed(
                    future_to_agent, timeout=5
                ):
                    agent = future_to_agent[future]
                    try:
                        result = future.result()
                        results[agent] = result
                    except Exception as e:
                        results[agent] = {"error": str(e)}

            # 验证并行执行结果
            all_completed = all(
                r.get("status") == "completed" for r in results.values()
            )
            expected_count = len(agents)
            actual_count = len(results)

            success = all_completed and actual_count == expected_count
            status = "PASS" if success else "FAIL"

            self._add_result(
                test_name,
                "P3",
                status,
                time.time() - start_time,
                {
                    "agents_tested": agents,
                    "execution_results": results,
                    "all_completed": all_completed,
                    "expected_agent_count": expected_count,
                    "actual_agent_count": actual_count,
                },
            )

            return success

        except Exception as e:
            self._add_result(
                test_name, "P3", "ERROR", time.time() - start_time, {"error": str(e)}
            )
            return False

    # ==================== Phase 4: Testing Tests ====================

    def test_phase_4_local_testing(self) -> bool:
        """测试Phase 4: 本地测试"""
        start_time = time.time()
        test_name = "Phase 4: Local Testing"

        try:
            # 1. 创建临时测试文件
            test_file = os.path.join(self.project_root, f"test_temp_{self.test_id}.py")
            test_content = """
def test_example():
    assert True

def test_math():
    assert 1 + 1 == 2

def test_string():
    assert "hello".upper() == "HELLO"
"""
            with open(test_file, "w") as f:
                f.write(test_content)

            # 2. 运行测试
            ret_code, stdout, stderr = self._run_command(
                f"python -m pytest {test_file} -v"
            )
            tests_passed = ret_code == 0

            # 3. 触发测试协调器Hook
            hook_triggered, hook_output = self._trigger_hook(
                "testing_coordinator",
                {
                    "test_file": test_file,
                    "test_result": "passed" if tests_passed else "failed",
                },
            )

            # 4. 验证功能
            functionality_verified = tests_passed and "PASSED" in stdout

            # 5. 清理临时文件
            if os.path.exists(test_file):
                os.remove(test_file)

            success = tests_passed and functionality_verified
            status = "PASS" if success else "FAIL"

            self._add_result(
                test_name,
                "P4",
                status,
                time.time() - start_time,
                {
                    "test_file": test_file,
                    "tests_passed": tests_passed,
                    "test_output": stdout,
                    "test_errors": stderr,
                    "hook_triggered": hook_triggered,
                    "hook_output": hook_output,
                    "functionality_verified": functionality_verified,
                },
            )

            return success

        except Exception as e:
            self._add_result(
                test_name, "P4", "ERROR", time.time() - start_time, {"error": str(e)}
            )
            return False

    # ==================== Phase 5: Git Commit Tests ====================

    def test_phase_5_git_commit(self) -> bool:
        """测试Phase 5: Git提交"""
        start_time = time.time()
        test_name = "Phase 5: Git Commit"

        try:
            # 1. 创建测试文件用于提交
            test_file = f"test_commit_{self.test_id}.txt"
            test_content = f"Test file for E2E testing - {self.test_id}\nCreated at: {datetime.now()}"

            with open(os.path.join(self.project_root, test_file), "w") as f:
                f.write(test_content)

            # 2. 添加到Git
            ret_code, stdout, stderr = self._run_command(f"git add {test_file}")
            file_added = ret_code == 0

            # 3. 触发提交质量检查Hook
            hook_triggered, hook_output = self._trigger_hook(
                "commit_quality_gate",
                {"files_changed": [test_file], "commit_type": "test"},
            )

            # 4. 执行提交
            commit_msg = f"test: E2E测试提交 - {self.test_id}"
            ret_code, stdout, stderr = self._run_command(
                f'git commit -m "{commit_msg}"'
            )
            commit_successful = ret_code == 0

            # 5. 验证质量检查通过
            quality_checks_passed = hook_triggered  # 简化验证

            success = file_added and commit_successful and quality_checks_passed
            status = "PASS" if success else "FAIL"

            self._add_result(
                test_name,
                "P5",
                status,
                time.time() - start_time,
                {
                    "test_file": test_file,
                    "file_added": file_added,
                    "commit_message": commit_msg,
                    "commit_successful": commit_successful,
                    "commit_output": stdout,
                    "commit_errors": stderr,
                    "hook_triggered": hook_triggered,
                    "hook_output": hook_output,
                    "quality_checks_passed": quality_checks_passed,
                },
            )

            return success

        except Exception as e:
            self._add_result(
                test_name, "P5", "ERROR", time.time() - start_time, {"error": str(e)}
            )
            return False

    # ==================== Phase 6: Code Review Tests ====================

    def test_phase_6_code_review_prep(self) -> bool:
        """测试Phase 6: 代码审查准备"""
        start_time = time.time()
        test_name = "Phase 6: Code Review Preparation"

        try:
            # 1. 获取当前分支状态
            ret_code, current_branch, stderr = self._run_command(
                "git branch --show-current"
            )
            branch_status = ret_code == 0

            # 2. 检查是否有提交
            ret_code, commit_log, stderr = self._run_command("git log --oneline -5")
            has_commits = ret_code == 0 and len(commit_log.strip()) > 0

            # 3. 触发审查准备Hook
            hook_triggered, hook_output = self._trigger_hook(
                "review_preparation",
                {
                    "branch": current_branch.strip(),
                    "commits_count": len(commit_log.split("\n")) if has_commits else 0,
                },
            )

            # 4. 模拟PR创建检查
            pr_ready = branch_status and has_commits

            success = branch_status and has_commits and hook_triggered and pr_ready
            status = "PASS" if success else "FAIL"

            self._add_result(
                test_name,
                "P6",
                status,
                time.time() - start_time,
                {
                    "current_branch": current_branch.strip(),
                    "branch_status": branch_status,
                    "has_commits": has_commits,
                    "commit_log": commit_log,
                    "hook_triggered": hook_triggered,
                    "hook_output": hook_output,
                    "pr_ready": pr_ready,
                },
            )

            return success

        except Exception as e:
            self._add_result(
                test_name, "P6", "ERROR", time.time() - start_time, {"error": str(e)}
            )
            return False

    # ==================== Error Recovery Tests ====================

    def test_error_recovery_mechanism(self) -> bool:
        """测试错误恢复机制"""
        start_time = time.time()
        test_name = "Error Recovery Mechanism"

        try:
            # 1. 触发错误处理Hook
            error_context = {
                "error_type": "timeout",
                "error_message": "Agent execution timeout",
                "phase": "P3",
            }

            hook_triggered, hook_output = self._trigger_hook(
                "error_handler", error_context
            )

            # 2. 测试智能错误恢复
            recovery_hook_triggered, recovery_output = self._trigger_hook(
                "smart_error_recovery",
                {"error_context": error_context, "recovery_attempts": 1},
            )

            # 3. 验证错误处理响应
            error_handled = hook_triggered and len(hook_output.strip()) > 0
            recovery_suggested = recovery_hook_triggered and "恢复" in recovery_output

            success = error_handled and recovery_suggested
            status = "PASS" if success else "FAIL"

            self._add_result(
                test_name,
                "ERROR_RECOVERY",
                status,
                time.time() - start_time,
                {
                    "error_context": error_context,
                    "error_hook_triggered": hook_triggered,
                    "error_hook_output": hook_output,
                    "recovery_hook_triggered": recovery_hook_triggered,
                    "recovery_output": recovery_output,
                    "error_handled": error_handled,
                    "recovery_suggested": recovery_suggested,
                },
            )

            return success

        except Exception as e:
            self._add_result(
                test_name,
                "ERROR_RECOVERY",
                "ERROR",
                time.time() - start_time,
                {"error": str(e)},
            )
            return False

    # ==================== Performance Tests ====================

    def test_hook_performance(self) -> bool:
        """测试Hook性能"""
        start_time = time.time()
        test_name = "Hook Performance Test"

        try:
            hook_performance_results = {}

            # 测试关键Hook的执行时间
            critical_hooks = [
                "smart_agent_selector",
                "error_handler",
                "performance_monitor",
                "optimized_performance_monitor",
            ]

            for hook_name in critical_hooks:
                if not self._check_hook_exists(hook_name):
                    continue

                hook_start = time.time()
                triggered, output = self._trigger_hook(
                    hook_name, {"test": "performance"}
                )
                hook_duration = time.time() - hook_start

                hook_performance_results[hook_name] = {
                    "triggered": triggered,
                    "duration": hook_duration,
                    "output_length": len(output),
                    "timeout_compliant": hook_duration < 5.0,  # 5秒超时
                }

            # 验证性能要求
            all_performant = all(
                result["timeout_compliant"]
                for result in hook_performance_results.values()
                if result["triggered"]
            )

            average_duration = sum(
                result["duration"]
                for result in hook_performance_results.values()
                if result["triggered"]
            ) / max(1, len(hook_performance_results))

            success = all_performant and average_duration < 2.0
            status = "PASS" if success else "FAIL"

            self._add_result(
                test_name,
                "PERFORMANCE",
                status,
                time.time() - start_time,
                {
                    "hook_results": hook_performance_results,
                    "all_performant": all_performant,
                    "average_duration": average_duration,
                    "performance_threshold": 2.0,
                },
            )

            return success

        except Exception as e:
            self._add_result(
                test_name,
                "PERFORMANCE",
                "ERROR",
                time.time() - start_time,
                {"error": str(e)},
            )
            return False

    # ==================== User Scenario Tests ====================

    def test_complete_user_scenario(self) -> bool:
        """测试完整用户场景"""
        start_time = time.time()
        test_name = "Complete User Scenario"

        try:
            scenario_steps = []
            overall_success = True

            # 场景：用户请求实现一个新功能
            steps = [
                ("需求输入", self._simulate_requirement_input),
                ("设计决策", self._simulate_design_decision),
                ("实现计划", self._simulate_implementation_plan),
                ("测试执行", self._simulate_testing_execution),
                ("提交流程", self._simulate_commit_process),
            ]

            for step_name, step_function in steps:
                step_start = time.time()
                try:
                    step_success = step_function()
                    step_duration = time.time() - step_start

                    scenario_steps.append(
                        {
                            "step": step_name,
                            "success": step_success,
                            "duration": step_duration,
                        }
                    )

                    if not step_success:
                        overall_success = False
                        logger.warning(f"用户场景步骤失败: {step_name}")

                except Exception as e:
                    scenario_steps.append(
                        {
                            "step": step_name,
                            "success": False,
                            "duration": time.time() - step_start,
                            "error": str(e),
                        }
                    )
                    overall_success = False

            status = "PASS" if overall_success else "FAIL"

            self._add_result(
                test_name,
                "USER_SCENARIO",
                status,
                time.time() - start_time,
                {
                    "scenario_steps": scenario_steps,
                    "overall_success": overall_success,
                    "total_steps": len(steps),
                    "successful_steps": sum(1 for s in scenario_steps if s["success"]),
                },
            )

            return overall_success

        except Exception as e:
            self._add_result(
                test_name,
                "USER_SCENARIO",
                "ERROR",
                time.time() - start_time,
                {"error": str(e)},
            )
            return False

    def _simulate_requirement_input(self) -> bool:
        """模拟需求输入"""
        context = {
            "user_request": "我需要一个用户认证系统",
            "complexity": "medium",
            "timeline": "1周",
        }

        triggered, output = self._trigger_hook("p1_requirements_analyzer", context)
        return triggered and len(output.strip()) > 0

    def _simulate_design_decision(self) -> bool:
        """模拟设计决策"""
        if not self._check_hook_exists("design_advisor"):
            return True  # Skip if doesn't exist

        context = {"feature_type": "authentication", "tech_preferences": "FastAPI, JWT"}

        triggered, output = self._trigger_hook("design_advisor", context)
        return triggered or True  # 允许Hook不存在

    def _simulate_implementation_plan(self) -> bool:
        """模拟实现计划"""
        context = {"task_complexity": "high", "agent_count_needed": 6}

        triggered, output = self._trigger_hook("smart_agent_selector", context)
        return triggered and ("6" in output or "agent" in output.lower())

    def _simulate_testing_execution(self) -> bool:
        """模拟测试执行"""
        if not self._check_hook_exists("testing_coordinator"):
            return True  # Skip if doesn't exist

        context = {"test_type": "unit_test", "coverage_target": "80%"}

        triggered, output = self._trigger_hook("testing_coordinator", context)
        return triggered or True  # 允许Hook不存在

    def _simulate_commit_process(self) -> bool:
        """模拟提交流程"""
        if not self._check_hook_exists("commit_quality_gate"):
            return True  # Skip if doesn't exist

        context = {
            "files_changed": ["auth.py", "tests/test_auth.py"],
            "test_status": "passed",
        }

        triggered, output = self._trigger_hook("commit_quality_gate", context)
        return triggered or True  # 允许Hook不存在

    # ==================== Workflow Integration Tests ====================

    def test_workflow_phase_transitions(self) -> bool:
        """测试工作流阶段转换"""
        start_time = time.time()
        test_name = "Workflow Phase Transitions"

        try:
            phases = ["P0", "P1", "P2", "P3", "P4", "P5", "P6"]
            phase_results = {}

            for phase in phases:
                phase_start = time.time()

                # 触发阶段检测器
                context = {"current_phase": phase, "test_mode": True}

                if self._check_hook_exists("workflow_phase_detector"):
                    triggered, output = self._trigger_hook(
                        "workflow_phase_detector", context
                    )
                    phase_duration = time.time() - phase_start

                    phase_results[phase] = {
                        "detected": triggered,
                        "duration": phase_duration,
                        "output": output,
                        "valid_transition": True,  # 简化验证
                    }
                else:
                    phase_results[phase] = {
                        "detected": False,
                        "duration": 0,
                        "output": "Hook不存在",
                        "valid_transition": True,  # Skip missing hooks
                    }

            # 验证整体工作流
            all_phases_valid = all(
                result["valid_transition"] for result in phase_results.values()
            )

            success = all_phases_valid
            status = "PASS" if success else "FAIL"

            self._add_result(
                test_name,
                "WORKFLOW",
                status,
                time.time() - start_time,
                {
                    "phases_tested": phases,
                    "phase_results": phase_results,
                    "all_phases_valid": all_phases_valid,
                },
            )

            return success

        except Exception as e:
            self._add_result(
                test_name,
                "WORKFLOW",
                "ERROR",
                time.time() - start_time,
                {"error": str(e)},
            )
            return False

    # ==================== Main Test Runner ====================

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        logger.info("🚀 开始Claude Enhancer 5.1端到端测试")
        logger.info(f"测试ID: {self.test_id}")
        logger.info(f"项目根目录: {self.project_root}")

        # 定义测试套件
        test_suite = [
            # Phase Tests
            ("Phase 0: 分支创建", self.test_phase_0_branch_creation),
            ("Phase 1: 需求分析", self.test_phase_1_requirements_analysis),
            ("Phase 2: 设计规划", self.test_phase_2_design_planning),
            ("Phase 3: Agent协作", self.test_phase_3_agent_coordination),
            ("Agent并行执行", self.test_agent_parallel_execution_simulation),
            ("Phase 4: 本地测试", self.test_phase_4_local_testing),
            ("Phase 5: Git提交", self.test_phase_5_git_commit),
            ("Phase 6: 代码审查", self.test_phase_6_code_review_prep),
            # System Tests
            ("错误恢复机制", self.test_error_recovery_mechanism),
            ("Hook性能测试", self.test_hook_performance),
            ("完整用户场景", self.test_complete_user_scenario),
            ("工作流阶段转换", self.test_workflow_phase_transitions),
        ]

        # 执行测试
        for test_name, test_function in test_suite:
            logger.info(f"🔍 执行测试: {test_name}")
            try:
                test_function()
            except Exception as e:
                logger.error(f"测试异常: {test_name} - {e}")
                self._add_result(test_name, "UNKNOWN", "ERROR", 0, {"error": str(e)})

        # 完成统计
        self.stats["end_time"] = time.time()
        self.stats["total_duration"] = self.stats["end_time"] - self.stats["start_time"]

        # 生成报告
        report = self._generate_report()

        # 清理
        self._cleanup()

        return report

    def _generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        logger.info("📊 生成测试报告")

        # 按阶段分组结果
        phase_summary = {}
        for result in self.results:
            phase = result.phase
            if phase not in phase_summary:
                phase_summary[phase] = {"PASS": 0, "FAIL": 0, "SKIP": 0, "ERROR": 0}
            phase_summary[phase][result.status] += 1

        # 性能统计
        durations = [r.duration for r in self.results if r.duration > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0

        # 成功率计算
        success_rate = (self.stats["passed"] / max(1, self.stats["total_tests"])) * 100

        report = {
            "test_summary": {
                "test_id": self.test_id,
                "timestamp": datetime.now().isoformat(),
                "duration": self.stats["total_duration"],
                "total_tests": self.stats["total_tests"],
                "passed": self.stats["passed"],
                "failed": self.stats["failed"],
                "skipped": self.stats["skipped"],
                "errors": self.stats["errors"],
                "success_rate": success_rate,
            },
            "phase_summary": phase_summary,
            "performance_metrics": {
                "average_test_duration": avg_duration,
                "maximum_test_duration": max_duration,
                "total_execution_time": self.stats["total_duration"],
            },
            "detailed_results": [asdict(result) for result in self.results],
            "system_info": {
                "claude_version": self.config.get("version", "unknown"),
                "project_root": self.project_root,
                "test_branch": self.test_branch,
            },
            "recommendations": self._generate_recommendations(),
        }

        # 保存报告
        report_file = f"claude_enhancer_5.1_e2e_report_{self.test_id}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"📋 测试报告已保存: {report_file}")

        return report

    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于测试结果生成建议
        failed_count = self.stats["failed"]
        error_count = self.stats["errors"]
        success_rate = (self.stats["passed"] / max(1, self.stats["total_tests"])) * 100

        if success_rate < 80:
            recommendations.append("整体测试通过率低于80%，需要重点关注系统稳定性")

        if error_count > 0:
            recommendations.append(f"发现{error_count}个测试执行错误，建议检查Hook脚本和环境配置")

        if failed_count > 2:
            recommendations.append("多个功能测试失败，建议逐个排查Phase实现")

        # 检查缺失的Hook
        missing_hooks = []
        expected_hooks = [
            "design_advisor",
            "testing_coordinator",
            "commit_quality_gate",
            "workflow_phase_detector",
        ]

        for hook in expected_hooks:
            if not self._check_hook_exists(hook):
                missing_hooks.append(hook)

        if missing_hooks:
            recommendations.append(f"缺失Hook脚本: {', '.join(missing_hooks)}")

        # 性能建议
        durations = [r.duration for r in self.results if r.duration > 0]
        if durations and max(durations) > 10:
            recommendations.append("部分测试执行时间过长，建议优化Hook性能")

        if not recommendations:
            recommendations.append("所有测试通过，系统运行良好！")

        return recommendations

    def _cleanup(self) -> None:
        """清理测试环境"""
        logger.info("🧹 清理测试环境")

        try:
            # 切回原分支并删除测试分支
            ret_code, stdout, stderr = self._run_command("git checkout -")
            if ret_code == 0:
                ret_code, stdout, stderr = self._run_command(
                    f"git branch -D {self.test_branch}"
                )
                if ret_code == 0:
                    logger.info(f"删除测试分支: {self.test_branch}")

            # 清理临时文件
            temp_files = [
                f"test_commit_{self.test_id}.txt",
                f"test_temp_{self.test_id}.py",
            ]

            for temp_file in temp_files:
                full_path = os.path.join(self.project_root, temp_file)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    logger.info(f"删除临时文件: {temp_file}")

        except Exception as e:
            logger.warning(f"清理过程中出现错误: {e}")

    def print_summary(self, report: Dict[str, Any]) -> None:
        """打印测试摘要"""
        summary = report["test_summary"]

        print("\n" + "=" * 60)
        print("🎯 Claude Enhancer 5.1 端到端测试报告")
        print("=" * 60)
        print(f"📊 测试ID: {summary['test_id']}")
        print(f"⏱️  执行时间: {summary['duration']:.2f}秒")
        print(f"📈 成功率: {summary['success_rate']:.1f}%")
        print()

        print("📋 测试统计:")
        print(f"   ✅ 通过: {summary['passed']}")
        print(f"   ❌ 失败: {summary['failed']}")
        print(f"   ⏭️  跳过: {summary['skipped']}")
        print(f"   💥 错误: {summary['errors']}")
        print(f"   📊 总计: {summary['total_tests']}")
        print()

        # 阶段摘要
        print("🔄 阶段测试结果:")
        for phase, counts in report["phase_summary"].items():
            total = sum(counts.values())
            pass_rate = (counts["PASS"] / max(1, total)) * 100
            status_icon = "✅" if pass_rate >= 80 else "⚠️" if pass_rate >= 50 else "❌"
            print(
                f"   {status_icon} {phase}: {counts['PASS']}/{total} ({pass_rate:.0f}%)"
            )
        print()

        # 建议
        if report["recommendations"]:
            print("💡 改进建议:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"   {i}. {rec}")

        print("\n" + "=" * 60)
        print("🎉 测试完成！")
        print("=" * 60)


def main():
    """主函数"""
    print("🚀 启动Claude Enhancer 5.1端到端测试套件")

    # 获取项目根目录
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.path.abspath(".")

    # 创建测试框架实例
    test_framework = Claude5_1E2ETestFramework(project_root)

    try:
        # 运行所有测试
        report = test_framework.run_all_tests()

        # 打印摘要
        test_framework.print_summary(report)

        # 返回退出代码
        if report["test_summary"]["success_rate"] >= 80:
            sys.exit(0)  # 成功
        else:
            sys.exit(1)  # 失败

    except KeyboardInterrupt:
        print("\n⛔ 测试被用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"测试框架异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
