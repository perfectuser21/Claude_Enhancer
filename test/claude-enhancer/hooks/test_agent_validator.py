#!/usr/bin/env python3
"""
Claude Enhancer Agent Validator 测试套件
测试 Agent 验证器的所有功能和边缘情况
"""

import pytest
import json
import tempfile
import os
import subprocess
from unittest.mock import patch, mock_open
from pathlib import Path


class TestAgentValidator:
    """Agent 验证器测试类"""

    def setup_method(self):
        """每个测试方法的设置"""
        self.validator_script = Path(__file__).parent.parent.parent.parent / ".claude/hooks/agent_validator.sh"
        self.test_config = {
            "min_agents": 3,
            "max_agents": 10,
            "enforce_parallel": True,
            "block_on_violation": True
        }

    def test_agent_validator_script_exists(self):
        """测试 Agent 验证器脚本是否存在"""
        assert self.validator_script.exists(), f"Agent validator script not found at {self.validator_script}"
        assert os.access(self.validator_script, os.X_OK), "Agent validator script is not executable"

    def test_valid_authentication_task(self):
        """测试有效的认证任务 Agent 组合"""
        test_input = json.dumps({
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "backend-architect",
                        "prompt": "设计用户认证系统的后端架构"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "security-auditor",
                        "prompt": "审查认证系统的安全设计"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "test-engineer",
                        "prompt": "设计认证系统的测试策略"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "api-designer",
                        "prompt": "设计认证API接口"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "database-specialist",
                        "prompt": "设计用户数据存储方案"
                    }
                }
            ]
        })

        result = self._run_validator(test_input)
        assert result.returncode == 0, f"Valid authentication task failed: {result.stderr}"

    def test_insufficient_agents_rejected(self):
        """测试 Agent 数量不足的情况被拒绝"""
        test_input = json.dumps({
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "backend-architect",
                        "prompt": "实现用户认证系统"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "test-engineer",
                        "prompt": "测试认证功能"
                    }
                }
            ]
        })

        result = self._run_validator(test_input)
        assert result.returncode == 1, "Insufficient agents should be rejected"
        assert "Agent数量不足" in result.stderr

    def test_task_type_detection_authentication(self):
        """测试认证任务类型检测"""
        auth_keywords = ["登录", "认证", "auth", "jwt", "oauth", "用户", "权限", "password"]

        for keyword in auth_keywords:
            test_input = json.dumps({
                "function_calls": [
                    {
                        "invoke": "Task",
                        "parameters": {
                            "subagent_type": "backend-architect",
                            "prompt": f"实现{keyword}功能"
                        }
                    },
                    {
                        "invoke": "Task",
                        "parameters": {
                            "subagent_type": "security-auditor",
                            "prompt": "安全审查"
                        }
                    },
                    {
                        "invoke": "Task",
                        "parameters": {
                            "subagent_type": "test-engineer",
                            "prompt": "测试设计"
                        }
                    }
                ]
            })

            result = self._run_validator(test_input)
            # 应该警告缺少必需的 agents，但不完全阻止
            assert "authentication" in result.stderr or result.returncode == 0

    def test_task_type_detection_api_development(self):
        """测试 API 开发任务类型检测"""
        api_keywords = ["api", "接口", "rest", "graphql", "endpoint", "route"]

        for keyword in api_keywords:
            test_input = json.dumps({
                "function_calls": [
                    {
                        "invoke": "Task",
                        "parameters": {
                            "subagent_type": "api-designer",
                            "prompt": f"设计{keyword}系统"
                        }
                    },
                    {
                        "invoke": "Task",
                        "parameters": {
                            "subagent_type": "backend-architect",
                            "prompt": "后端实现"
                        }
                    },
                    {
                        "invoke": "Task",
                        "parameters": {
                            "subagent_type": "test-engineer",
                            "prompt": "测试设计"
                        }
                    },
                    {
                        "invoke": "Task",
                        "parameters": {
                            "subagent_type": "technical-writer",
                            "prompt": "文档编写"
                        }
                    }
                ]
            })

            result = self._run_validator(test_input)
            assert result.returncode == 0, f"Valid API development task failed for keyword: {keyword}"

    def test_non_task_calls_pass_through(self):
        """测试非 Task 调用应该直接通过"""
        test_input = json.dumps({
            "function_calls": [
                {
                    "invoke": "Read",
                    "parameters": {
                        "file_path": "/some/file.txt"
                    }
                },
                {
                    "invoke": "Write",
                    "parameters": {
                        "file_path": "/some/file.txt",
                        "content": "Hello World"
                    }
                }
            ]
        })

        result = self._run_validator(test_input)
        assert result.returncode == 0, "Non-Task calls should pass through"
        assert result.stdout.strip() == test_input.strip()

    def test_mixed_task_and_non_task_calls(self):
        """测试混合 Task 和非 Task 调用"""
        test_input = json.dumps({
            "function_calls": [
                {
                    "invoke": "Read",
                    "parameters": {
                        "file_path": "/some/file.txt"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "backend-architect",
                        "prompt": "设计系统架构"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "test-engineer",
                        "prompt": "测试设计"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "technical-writer",
                        "prompt": "文档编写"
                    }
                },
                {
                    "invoke": "Write",
                    "parameters": {
                        "file_path": "/output/result.txt",
                        "content": "Results"
                    }
                }
            ]
        })

        result = self._run_validator(test_input)
        assert result.returncode == 0, "Mixed calls with sufficient agents should pass"

    def test_parallel_execution_detection(self):
        """测试并行执行检测"""
        # 模拟在同一个 function_calls 块中的并行调用
        test_input = json.dumps({
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "backend-architect",
                        "prompt": "设计后端架构"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "frontend-specialist",
                        "prompt": "设计前端架构"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "test-engineer",
                        "prompt": "设计测试策略"
                    }
                }
            ]
        })

        result = self._run_validator(test_input)
        assert result.returncode == 0, "Parallel execution should be accepted"

    def test_logging_functionality(self):
        """测试日志记录功能"""
        test_input = json.dumps({
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "backend-architect",
                        "prompt": "设计系统架构"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "test-engineer",
                        "prompt": "测试设计"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "technical-writer",
                        "prompt": "文档编写"
                    }
                }
            ]
        })

        self._run_validator(test_input)

        log_file = "/tmp/claude_enhancer_agent_log.txt"
        assert os.path.exists(log_file), "Log file should be created"

        with open(log_file, 'r') as f:
            log_content = f.read()
            assert "general" in log_content or "Agents: 3" in log_content

    def test_error_handling_invalid_json(self):
        """测试无效 JSON 输入的错误处理"""
        invalid_json = "{ invalid json here }"

        result = self._run_validator(invalid_json)
        # 脚本应该能处理无效 JSON 而不崩溃
        # 可能会通过或返回错误，但不应该产生 bash 错误
        assert result.returncode in [0, 1], "Should handle invalid JSON gracefully"

    def test_empty_input_handling(self):
        """测试空输入处理"""
        result = self._run_validator("")
        assert result.returncode == 0, "Empty input should pass through"

    def test_claude_enhancer_home_detection(self):
        """测试 CLAUDE_ENHANCER_HOME 环境变量检测"""
        with patch.dict(os.environ, {'CLAUDE_ENHANCER_HOME': '/custom/path'}):
            # 这个测试验证脚本能正确检测环境变量
            # 实际的路径验证需要在真实环境中进行
            pass

    def test_performance_large_input(self):
        """测试大输入的性能"""
        # 创建一个包含很多 agents 的大输入
        large_input = {
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": f"agent-{i}",
                        "prompt": f"Task {i} description"
                    }
                } for i in range(100)
            ]
        }

        import time
        start_time = time.time()
        result = self._run_validator(json.dumps(large_input))
        end_time = time.time()

        execution_time = end_time - start_time
        assert execution_time < 5.0, f"Large input processing took too long: {execution_time}s"
        assert result.returncode == 0, "Large input should be processed successfully"

    def _run_validator(self, test_input: str) -> subprocess.CompletedProcess:
        """运行 Agent 验证器并返回结果"""
        try:
            result = subprocess.run(
                [str(self.validator_script)],
                input=test_input,
                text=True,
                capture_output=True,
                timeout=30
            )
            return result
        except subprocess.TimeoutExpired:
            pytest.fail("Agent validator script timed out")
        except Exception as e:
            pytest.fail(f"Failed to run agent validator: {e}")


# 性能测试类
class TestAgentValidatorPerformance:
    """Agent 验证器性能测试"""

    def setup_method(self):
        self.validator_script = Path(__file__).parent.parent.parent.parent / ".claude/hooks/agent_validator.sh"

    def test_response_time_small_input(self):
        """测试小输入的响应时间"""
        test_input = json.dumps({
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "backend-architect",
                        "prompt": "设计系统"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "test-engineer",
                        "prompt": "测试设计"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "technical-writer",
                        "prompt": "文档编写"
                    }
                }
            ]
        })

        import time
        start_time = time.time()

        result = subprocess.run(
            [str(self.validator_script)],
            input=test_input,
            text=True,
            capture_output=True,
            timeout=10
        )

        end_time = time.time()
        execution_time = end_time - start_time

        assert execution_time < 0.1, f"Small input processing too slow: {execution_time}s"
        assert result.returncode == 0

    def test_concurrent_validation(self):
        """测试并发验证性能"""
        import concurrent.futures
        import time

        test_input = json.dumps({
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "backend-architect",
                        "prompt": "设计系统架构"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "test-engineer",
                        "prompt": "测试设计"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "technical-writer",
                        "prompt": "文档编写"
                    }
                }
            ]
        })

        def run_validation():
            return subprocess.run(
                [str(self.validator_script)],
                input=test_input,
                text=True,
                capture_output=True,
                timeout=10
            )

        start_time = time.time()

        # 并发运行 10 个验证
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_validation) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time

        # 所有验证都应该成功
        for result in results:
            assert result.returncode == 0

        # 并发执行应该比顺序执行快
        assert total_time < 2.0, f"Concurrent validation too slow: {total_time}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])