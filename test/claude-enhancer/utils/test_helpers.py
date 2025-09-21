#!/usr/bin/env python3
"""
Claude Enhancer 测试辅助工具
提供测试所需的通用功能和工具函数
"""

import json
import time
import tempfile
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import patch
import yaml


class TestDataGenerator:
    """测试数据生成器"""

    @staticmethod
    def create_task_input(agents: List[str], task_description: str = None) -> str:
        """创建Task工具调用输入"""
        if not task_description:
            task_description = "测试任务描述"

        function_calls = []
        for i, agent in enumerate(agents):
            function_calls.append({
                "invoke": "Task",
                "parameters": {
                    "subagent_type": agent,
                    "prompt": f"{task_description} - Agent {i+1}: {agent}"
                }
            })

        return json.dumps({"function_calls": function_calls})

    @staticmethod
    def create_authentication_task() -> str:
        """创建认证系统任务输入"""
        agents = [
            "backend-architect",
            "security-auditor",
            "test-engineer",
            "api-designer",
            "database-specialist"
        ]
        return TestDataGenerator.create_task_input(
            agents,
            "实现用户认证系统，包括注册、登录、JWT令牌管理和权限控制"
        )

    @staticmethod
    def create_api_development_task() -> str:
        """创建API开发任务输入"""
        agents = [
            "api-designer",
            "backend-architect",
            "test-engineer",
            "technical-writer"
        ]
        return TestDataGenerator.create_task_input(
            agents,
            "开发RESTful API系统，包括用户管理、数据CRUD操作和API文档"
        )

    @staticmethod
    def create_database_task() -> str:
        """创建数据库设计任务输入"""
        agents = [
            "database-specialist",
            "backend-architect",
            "performance-engineer"
        ]
        return TestDataGenerator.create_task_input(
            agents,
            "设计企业级数据库系统，包括用户、订单、产品、库存管理"
        )

    @staticmethod
    def create_large_task(agent_count: int = 50) -> str:
        """创建大型任务输入（用于性能测试）"""
        agents = [f"agent-{i}" for i in range(agent_count)]
        return TestDataGenerator.create_task_input(
            agents,
            "大型复杂任务，用于性能和扩展性测试"
        )

    @staticmethod
    def create_malicious_input() -> List[str]:
        """创建恶意输入列表（用于安全测试）"""
        return [
            # 命令注入
            '{"function_calls": [{"invoke": "$(rm -rf /)", "parameters": {}}]}',

            # JSON注入
            '{"function_calls": [{"invoke": "Task", "parameters": {"subagent_type": "test; rm -rf /tmp", "prompt": "test"}}]}',

            # 路径遍历
            '{"function_calls": [{"invoke": "Task", "parameters": {"subagent_type": "../../../etc/passwd", "prompt": "test"}}]}',

            # 代码注入
            '{"function_calls": [{"invoke": "Task", "parameters": {"subagent_type": "test`whoami`", "prompt": "test"}}]}',

            # 长度攻击
            '{"function_calls": [{"invoke": "Task", "parameters": {"subagent_type": "' + "A" * 10000 + '", "prompt": "test"}}]}'
        ]


class MockPhaseManager:
    """模拟阶段管理器（用于测试）"""

    def __init__(self, temp_dir: str):
        self.temp_dir = temp_dir
        self.state_file = os.path.join(temp_dir, "mock_state.json")
        self.current_phase = None
        self.phase_history = []
        self.context_pool = {}

    def reset_phases(self):
        """重置阶段"""
        self.current_phase = None
        self.phase_history = []
        self.context_pool = {}

    def advance_to_next_phase(self):
        """推进到下一阶段"""
        from phase_manager import ExecutionPhase

        phase_order = [
            ExecutionPhase.ANALYSIS,
            ExecutionPhase.DESIGN,
            ExecutionPhase.IMPLEMENTATION,
            ExecutionPhase.TESTING,
            ExecutionPhase.DEPLOYMENT
        ]

        if not self.current_phase:
            self.current_phase = ExecutionPhase.ANALYSIS
        else:
            current_idx = phase_order.index(self.current_phase)
            if current_idx < len(phase_order) - 1:
                self.current_phase = phase_order[current_idx + 1]
            else:
                return None

        return self.current_phase

    def save_phase_results(self, phase, results):
        """保存阶段结果"""
        self.context_pool[phase.value] = {
            "timestamp": time.time(),
            "results": results
        }
        self.phase_history.append({
            "phase": phase.value,
            "completed_at": time.time(),
            "results_summary": len(results) if isinstance(results, dict) else 0
        })

    def get_context_for_phase(self, phase):
        """获取阶段上下文"""
        context = {}
        for phase_value, phase_data in self.context_pool.items():
            if phase_value != phase.value:
                context[phase_value] = phase_data
        return context


class TestEnvironmentManager:
    """测试环境管理器"""

    def __init__(self):
        self.temp_dir = None
        self.cleanup_callbacks = []

    def __enter__(self):
        """进入测试环境"""
        self.temp_dir = tempfile.mkdtemp(prefix="claude_enhancer_test_")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出测试环境，清理资源"""
        self.cleanup()

    def create_temp_file(self, content: str, suffix: str = ".json") -> str:
        """创建临时文件"""
        fd, temp_file = tempfile.mkstemp(dir=self.temp_dir, suffix=suffix)
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(content)
        except:
            os.close(fd)
            raise

        self.cleanup_callbacks.append(lambda: self._safe_remove(temp_file))
        return temp_file

    def create_temp_dir(self) -> str:
        """创建临时目录"""
        temp_subdir = tempfile.mkdtemp(dir=self.temp_dir)
        self.cleanup_callbacks.append(lambda: self._safe_remove_dir(temp_subdir))
        return temp_subdir

    def get_temp_path(self, filename: str) -> str:
        """获取临时文件路径"""
        return os.path.join(self.temp_dir, filename)

    def cleanup(self):
        """清理测试环境"""
        # 执行清理回调
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception:
                pass

        # 清理主临时目录
        if self.temp_dir and os.path.exists(self.temp_dir):
            self._safe_remove_dir(self.temp_dir)

    @staticmethod
    def _safe_remove(file_path: str):
        """安全删除文件"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass

    @staticmethod
    def _safe_remove_dir(dir_path: str):
        """安全删除目录"""
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
        except Exception:
            pass


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_samples = []

    def start(self):
        """开始监控"""
        self.start_time = time.time()
        self._sample_memory()

    def end(self):
        """结束监控"""
        self.end_time = time.time()
        self._sample_memory()

    def get_execution_time(self) -> float:
        """获取执行时间"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0

    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        if len(self.memory_samples) >= 2:
            return {
                "initial": self.memory_samples[0],
                "final": self.memory_samples[-1],
                "increase": self.memory_samples[-1] - self.memory_samples[0],
                "peak": max(self.memory_samples)
            }
        return {"initial": 0, "final": 0, "increase": 0, "peak": 0}

    def _sample_memory(self):
        """采样内存使用"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_samples.append(memory_mb)
        except ImportError:
            # 如果psutil不可用，使用虚拟值
            self.memory_samples.append(0)


class TestConfigLoader:
    """测试配置加载器"""

    @staticmethod
    def load_test_scenarios(config_file: Optional[str] = None) -> Dict[str, Any]:
        """加载测试场景配置"""
        if not config_file:
            config_file = Path(__file__).parent.parent / "fixtures" / "test_scenarios.yaml"

        if not os.path.exists(config_file):
            return {}

        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @staticmethod
    def get_scenario(scenario_name: str) -> Dict[str, Any]:
        """获取特定测试场景"""
        scenarios = TestConfigLoader.load_test_scenarios()
        return scenarios.get("test_scenarios", {}).get(scenario_name, {})

    @staticmethod
    def get_performance_benchmarks() -> Dict[str, Any]:
        """获取性能基准"""
        config = TestConfigLoader.load_test_scenarios()
        return config.get("performance_benchmarks", {})

    @staticmethod
    def get_security_test_data() -> Dict[str, Any]:
        """获取安全测试数据"""
        config = TestConfigLoader.load_test_scenarios()
        return config.get("security_test_data", {})


class ValidationHelpers:
    """验证辅助函数"""

    @staticmethod
    def validate_agent_count(agents: List[str], min_count: int, max_count: int = None) -> bool:
        """验证Agent数量"""
        count = len(agents)
        if count < min_count:
            return False
        if max_count and count > max_count:
            return False
        return True

    @staticmethod
    def validate_required_agents(used_agents: List[str], required_agents: List[str]) -> bool:
        """验证必需的Agents"""
        used_set = set(used_agents)
        required_set = set(required_agents)
        return required_set.issubset(used_set)

    @staticmethod
    def validate_phase_results(results: Dict[str, Any], required_fields: List[str]) -> bool:
        """验证阶段结果"""
        for field in required_fields:
            if field not in results:
                return False
        return True

    @staticmethod
    def validate_execution_time(actual_time: float, max_time: float) -> bool:
        """验证执行时间"""
        return actual_time <= max_time

    @staticmethod
    def validate_memory_usage(actual_memory: float, max_memory: float) -> bool:
        """验证内存使用"""
        return actual_memory <= max_memory


class MockScriptRunner:
    """模拟脚本运行器"""

    def __init__(self, success: bool = True, output: str = "", error: str = ""):
        self.success = success
        self.output = output
        self.error = error

    def run_script(self, script_path: str, input_data: str) -> Dict[str, Any]:
        """模拟运行脚本"""
        time.sleep(0.01)  # 模拟执行时间

        return {
            "returncode": 0 if self.success else 1,
            "stdout": self.output,
            "stderr": self.error
        }


class AssertionHelpers:
    """断言辅助函数"""

    @staticmethod
    def assert_workflow_completed(workflow_results: Dict[str, Any]):
        """断言工作流完成"""
        assert "success" in workflow_results
        assert workflow_results["success"] is True
        assert "phases" in workflow_results
        assert len(workflow_results["phases"]) == 5

    @staticmethod
    def assert_phase_quality(phase_result: Dict[str, Any], phase_name: str):
        """断言阶段质量"""
        assert "phase" in phase_result
        assert phase_result["phase"] == phase_name
        assert "status" in phase_result
        assert phase_result["status"] in ["completed", "completed_after_recovery"]

    @staticmethod
    def assert_performance_metrics(metrics: Dict[str, Any], benchmarks: Dict[str, Any]):
        """断言性能指标"""
        if "execution_time" in metrics and "max_execution_time" in benchmarks:
            assert metrics["execution_time"] <= benchmarks["max_execution_time"]

        if "memory_usage" in metrics and "max_memory_usage" in benchmarks:
            assert metrics["memory_usage"] <= benchmarks["max_memory_usage"]

    @staticmethod
    def assert_security_compliance(test_result: Dict[str, Any]):
        """断言安全合规性"""
        # 验证没有执行恶意命令
        output = test_result.get("stdout", "") + test_result.get("stderr", "")

        dangerous_patterns = ["rm -rf", "cat /etc/passwd", "curl", "nc "]
        for pattern in dangerous_patterns:
            assert pattern not in output, f"Dangerous command detected: {pattern}"

        # 验证返回码在安全范围内
        assert test_result.get("returncode", 1) in [0, 1], "Unexpected return code"


# 测试装饰器
def performance_test(max_time: float = 1.0, max_memory: float = 100.0):
    """性能测试装饰器"""
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            monitor = PerformanceMonitor()
            monitor.start()

            try:
                result = test_func(*args, **kwargs)
            finally:
                monitor.end()

            # 验证性能指标
            execution_time = monitor.get_execution_time()
            memory_usage = monitor.get_memory_usage()

            assert execution_time <= max_time, f"Test too slow: {execution_time}s > {max_time}s"

            if memory_usage["increase"] > max_memory:
                assert False, f"Memory usage too high: {memory_usage['increase']}MB > {max_memory}MB"

            return result
        return wrapper
    return decorator


def requires_environment(*requirements):
    """环境要求装饰器"""
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            for requirement in requirements:
                if requirement == "hooks_directory":
                    hooks_dir = Path(__file__).parent.parent.parent.parent / ".claude" / "hooks"
                    if not hooks_dir.exists():
                        import pytest
                        pytest.skip("Hooks directory not found")

                elif requirement == "agent_validator":
                    validator_script = Path(__file__).parent.parent.parent.parent / ".claude" / "hooks" / "agent_validator.sh"
                    if not validator_script.exists():
                        import pytest
                        pytest.skip("Agent validator script not found")

            return test_func(*args, **kwargs)
        return wrapper
    return decorator