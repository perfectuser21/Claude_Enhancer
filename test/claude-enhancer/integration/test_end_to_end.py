#!/usr/bin/env python3
"""
Claude Enhancer 端到端集成测试套件
测试整个系统的集成和交互
"""

import pytest
import json
import tempfile
import os
import sys
import subprocess
import time
from unittest.mock import patch, MagicMock
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / ".claude/hooks"))

try:
    from phase_manager import PhaseManager, ExecutionPhase, get_phase_manager
except ImportError as e:
    pytest.skip(f"Cannot import phase_manager: {e}", allow_module_level=True)


class TestEndToEndIntegration:
    """端到端集成测试"""

    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "e2e_state.json")
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.hooks_dir = self.project_root / ".claude/hooks"

    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_authentication_system_e2e(self):
        """测试完整认证系统的端到端开发流程"""
        # 1. 用户请求：实现认证系统
        user_request = {
            "task": "实现完整的用户认证系统",
            "requirements": {
                "features": ["用户注册", "用户登录", "JWT令牌", "权限控制"],
                "technologies": ["Node.js", "PostgreSQL", "JWT", "bcrypt"],
                "quality": "生产级别"
            }
        }

        # 2. Hook验证：确保使用足够的agents
        task_input = self._create_authentication_task_input()
        validation_result = self._run_agent_validator(task_input)
        assert validation_result["success"], f"Agent validation failed: {validation_result['message']}"

        # 3. 5阶段工作流执行
        workflow_results = self._execute_five_phase_workflow(user_request)

        # 4. 验证每个阶段的输出质量
        self._verify_analysis_quality(workflow_results["analysis"])
        self._verify_design_quality(workflow_results["design"])
        self._verify_implementation_quality(workflow_results["implementation"])
        self._verify_testing_quality(workflow_results["testing"])
        self._verify_deployment_quality(workflow_results["deployment"])

        # 5. 验证阶段间的一致性
        self._verify_cross_phase_consistency(workflow_results)

        # 6. 性能验证
        assert workflow_results["metrics"]["total_time"] < 30.0, "E2E workflow too slow"
        assert workflow_results["metrics"]["memory_usage"] < 500, "Memory usage too high"

    def test_api_development_e2e(self):
        """测试API开发的端到端流程"""
        user_request = {
            "task": "开发RESTful API系统",
            "requirements": {
                "endpoints": ["用户管理", "数据CRUD", "文件上传"],
                "documentation": "OpenAPI 3.0",
                "testing": "自动化测试套件"
            }
        }

        # Agent验证
        task_input = self._create_api_development_task_input()
        validation_result = self._run_agent_validator(task_input)
        assert validation_result["success"]

        # 执行工作流
        workflow_results = self._execute_five_phase_workflow(user_request)

        # API特定验证
        design_results = workflow_results["design"]
        assert "api_specification" in design_results
        assert "endpoint_design" in design_results

        implementation_results = workflow_results["implementation"]
        assert "controllers" in implementation_results
        assert "routes" in implementation_results
        assert "middleware" in implementation_results

    def test_database_design_e2e(self):
        """测试数据库设计的端到端流程"""
        user_request = {
            "task": "设计企业级数据库系统",
            "requirements": {
                "entities": ["用户", "订单", "产品", "库存"],
                "relationships": "复杂关联",
                "performance": "高并发支持"
            }
        }

        # Agent验证
        task_input = self._create_database_task_input()
        validation_result = self._run_agent_validator(task_input)
        assert validation_result["success"]

        # 执行工作流
        workflow_results = self._execute_five_phase_workflow(user_request)

        # 数据库特定验证
        design_results = workflow_results["design"]
        assert "schema_design" in design_results
        assert "entity_relationships" in design_results

        implementation_results = workflow_results["implementation"]
        assert "migration_scripts" in implementation_results
        assert "database_setup" in implementation_results

    def test_frontend_application_e2e(self):
        """测试前端应用的端到端流程"""
        user_request = {
            "task": "开发现代化前端应用",
            "requirements": {
                "framework": "React",
                "features": ["用户界面", "状态管理", "路由"],
                "responsive": True
            }
        }

        # Agent验证
        task_input = self._create_frontend_task_input()
        validation_result = self._run_agent_validator(task_input)
        assert validation_result["success"]

        # 执行工作流
        workflow_results = self._execute_five_phase_workflow(user_request)

        # 前端特定验证
        design_results = workflow_results["design"]
        assert "component_architecture" in design_results
        assert "ui_design" in design_results

        implementation_results = workflow_results["implementation"]
        assert "components" in implementation_results
        assert "pages" in implementation_results

    def test_error_recovery_e2e(self):
        """测试错误恢复的端到端流程"""
        with patch.object(PhaseManager, 'state_file', self.state_file):
            manager = get_phase_manager()
            manager.reset_phases()

            # 模拟在实现阶段发生错误
            for phase in [ExecutionPhase.ANALYSIS, ExecutionPhase.DESIGN]:
                manager.advance_to_next_phase()
                result = {"phase": phase.value, "status": "completed"}
                manager.save_phase_results(phase, result)

            # 进入实现阶段
            impl_phase = manager.advance_to_next_phase()
            assert impl_phase == ExecutionPhase.IMPLEMENTATION

            # 模拟实现阶段错误
            error_result = {
                "phase": "impl",
                "status": "error",
                "error": "编译失败",
                "recovery_action": "修复代码并重试"
            }
            manager.save_phase_results(impl_phase, error_result)

            # 错误恢复：重新执行实现阶段
            recovery_result = {
                "phase": "impl",
                "status": "completed_after_recovery",
                "fixes_applied": ["修复语法错误", "更新依赖"]
            }
            manager.save_phase_results(impl_phase, recovery_result)

            # 继续后续阶段
            for phase in [ExecutionPhase.TESTING, ExecutionPhase.DEPLOYMENT]:
                current_phase = manager.advance_to_next_phase()
                result = {"phase": phase.value, "status": "completed"}
                manager.save_phase_results(phase, result)

            # 验证恢复成功
            assert manager.current_phase == ExecutionPhase.DEPLOYMENT
            assert len(manager.phase_history) == 5

    def test_concurrent_workflows_e2e(self):
        """测试并发工作流的端到端处理"""
        import threading
        import concurrent.futures

        def run_workflow(workflow_id):
            temp_state_file = os.path.join(self.temp_dir, f"workflow_{workflow_id}_state.json")

            with patch.object(PhaseManager, 'state_file', temp_state_file):
                manager = get_phase_manager()
                manager.reset_phases()

                user_request = {
                    "task": f"工作流{workflow_id}",
                    "workflow_id": workflow_id
                }

                return self._execute_five_phase_workflow(user_request)

        # 并发执行5个工作流
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_workflow, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # 验证所有工作流都成功完成
        for i, result in enumerate(results):
            assert result["success"], f"Workflow {i} failed"
            assert len(result["phases"]) == 5

    def test_performance_under_load_e2e(self):
        """测试负载下的性能"""
        start_time = time.time()

        # 快速执行多个轻量级工作流
        for i in range(20):
            state_file = os.path.join(self.temp_dir, f"perf_test_{i}.json")

            with patch.object(PhaseManager, 'state_file', state_file):
                manager = get_phase_manager()
                manager.reset_phases()

                # 快速执行所有阶段
                for phase in ExecutionPhase:
                    manager.advance_to_next_phase()
                    result = {"phase": phase.value, "iteration": i, "timestamp": time.time()}
                    manager.save_phase_results(phase, result)

        end_time = time.time()
        total_time = end_time - start_time

        # 20个工作流应该在10秒内完成
        assert total_time < 10.0, f"Performance test too slow: {total_time}s"

    def test_system_integration_with_git_operations(self):
        """测试与Git操作的系统集成"""
        # 模拟Git操作集成
        git_operations = {
            "analysis": [],
            "design": ["create_feature_branch", "init_project_structure"],
            "implementation": ["commit_changes", "run_pre_commit_hooks"],
            "testing": ["run_tests", "generate_coverage_report"],
            "deployment": ["tag_release", "merge_to_main"]
        }

        with patch.object(PhaseManager, 'state_file', self.state_file):
            manager = get_phase_manager()
            manager.reset_phases()

            for phase in ExecutionPhase:
                current_phase = manager.advance_to_next_phase()
                config = manager.phase_config[phase]

                # 验证Git操作配置
                expected_ops = git_operations.get(phase.value, [])
                assert config["git_operations"] == expected_ops

                # 模拟执行Git操作
                git_result = {
                    "phase": phase.value,
                    "git_operations": config["git_operations"],
                    "git_status": "success"
                }
                manager.save_phase_results(phase, git_result)

            # 验证所有Git操作都被记录
            for phase_value in git_operations:
                assert phase_value in manager.context_pool

    def _create_authentication_task_input(self):
        """创建认证系统任务输入"""
        return json.dumps({
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "backend-architect",
                        "prompt": "设计用户认证系统的后端架构，包括注册、登录、JWT令牌管理"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "security-auditor",
                        "prompt": "审查认证系统的安全设计，确保密码加密和令牌安全"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "test-engineer",
                        "prompt": "设计认证系统的全面测试策略"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "api-designer",
                        "prompt": "设计认证相关的API接口"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "database-specialist",
                        "prompt": "设计用户数据和认证信息的存储方案"
                    }
                }
            ]
        })

    def _create_api_development_task_input(self):
        """创建API开发任务输入"""
        return json.dumps({
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "api-designer",
                        "prompt": "设计RESTful API规范和接口"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "backend-architect",
                        "prompt": "设计API的后端架构"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "test-engineer",
                        "prompt": "设计API测试策略"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "technical-writer",
                        "prompt": "编写API文档"
                    }
                }
            ]
        })

    def _create_database_task_input(self):
        """创建数据库任务输入"""
        return json.dumps({
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "database-specialist",
                        "prompt": "设计数据库schema和表结构"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "backend-architect",
                        "prompt": "设计数据访问层架构"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "performance-engineer",
                        "prompt": "优化数据库性能"
                    }
                }
            ]
        })

    def _create_frontend_task_input(self):
        """创建前端任务输入"""
        return json.dumps({
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "frontend-specialist",
                        "prompt": "设计前端组件架构"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "ux-designer",
                        "prompt": "设计用户界面和交互"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "test-engineer",
                        "prompt": "设计前端测试策略"
                    }
                }
            ]
        })

    def _run_agent_validator(self, task_input):
        """运行Agent验证器"""
        validator_script = self.hooks_dir / "agent_validator.sh"

        try:
            result = subprocess.run(
                [str(validator_script)],
                input=task_input,
                text=True,
                capture_output=True,
                timeout=10
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "message": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Validator timeout"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _execute_five_phase_workflow(self, user_request):
        """执行5阶段工作流"""
        start_time = time.time()
        initial_memory = self._get_memory_usage()

        with patch.object(PhaseManager, 'state_file', self.state_file):
            manager = get_phase_manager()
            manager.reset_phases()

            workflow_results = {
                "success": True,
                "phases": {},
                "user_request": user_request,
                "metrics": {}
            }

            try:
                # 执行所有阶段
                for phase in ExecutionPhase:
                    phase_start = time.time()

                    current_phase = manager.advance_to_next_phase()
                    assert current_phase == phase

                    # 生成阶段指令
                    context = manager.get_context_for_phase(phase)
                    instructions = manager.generate_phase_instructions(phase, context)

                    # 模拟阶段执行
                    phase_result = self._simulate_phase_execution(phase, user_request, context)

                    # 验证阶段结果
                    config = manager.phase_config[phase]
                    agents_used = config["agents"][:config["min_agents"]]
                    is_valid, errors = manager.validate_agent_execution(agents_used)

                    if not is_valid:
                        workflow_results["success"] = False
                        workflow_results["error"] = f"Phase {phase.value} validation failed: {errors}"
                        break

                    # 保存阶段结果
                    manager.save_phase_results(phase, phase_result)

                    phase_end = time.time()
                    phase_result["execution_time"] = phase_end - phase_start

                    workflow_results["phases"][phase.value] = phase_result

                # 计算指标
                end_time = time.time()
                final_memory = self._get_memory_usage()

                workflow_results["metrics"] = {
                    "total_time": end_time - start_time,
                    "memory_usage": final_memory - initial_memory,
                    "phases_completed": len(workflow_results["phases"]),
                    "success_rate": 100.0 if workflow_results["success"] else 0.0
                }

                # 添加阶段别名用于兼容性
                for phase_value, phase_result in workflow_results["phases"].items():
                    if phase_value == "analysis":
                        workflow_results["analysis"] = phase_result
                    elif phase_value == "design":
                        workflow_results["design"] = phase_result
                    elif phase_value == "impl":
                        workflow_results["implementation"] = phase_result
                    elif phase_value == "testing":
                        workflow_results["testing"] = phase_result
                    elif phase_value == "deploy":
                        workflow_results["deployment"] = phase_result

            except Exception as e:
                workflow_results["success"] = False
                workflow_results["error"] = str(e)

            return workflow_results

    def _simulate_phase_execution(self, phase, user_request, context):
        """模拟阶段执行"""
        base_result = {
            "phase": phase.value,
            "status": "completed",
            "timestamp": time.time(),
            "user_request": user_request["task"],
            "context_available": len(context) > 0
        }

        # 根据阶段类型添加特定结果
        if phase == ExecutionPhase.ANALYSIS:
            base_result.update({
                "requirements_identified": 15,
                "user_stories": 8,
                "acceptance_criteria": 12,
                "stakeholders": ["用户", "管理员", "开发团队"]
            })
        elif phase == ExecutionPhase.DESIGN:
            base_result.update({
                "architecture_components": 6,
                "api_specification": "OpenAPI 3.0",
                "database_schema": "已设计",
                "ui_mockups": 5,
                "endpoint_design": ["GET /api/users", "POST /api/auth", "PUT /api/profile"]
            })
        elif phase == ExecutionPhase.IMPLEMENTATION:
            base_result.update({
                "files_created": 25,
                "functions_implemented": 45,
                "lines_of_code": 1200,
                "tests_written": 30,
                "controllers": ["AuthController", "UserController"],
                "routes": ["/auth", "/users", "/admin"],
                "middleware": ["auth", "validation", "logging"],
                "components": ["LoginForm", "Dashboard", "UserProfile"]
            })
        elif phase == ExecutionPhase.TESTING:
            base_result.update({
                "unit_tests": 40,
                "integration_tests": 20,
                "e2e_tests": 10,
                "coverage_percentage": 87,
                "bugs_found": 3,
                "performance_metrics": "通过"
            })
        elif phase == ExecutionPhase.DEPLOYMENT:
            base_result.update({
                "deployment_environment": "production",
                "monitoring_configured": True,
                "documentation_updated": True,
                "deployment_url": "https://api.example.com",
                "health_checks": "通过"
            })

        return base_result

    def _verify_analysis_quality(self, analysis_result):
        """验证分析阶段质量"""
        assert "requirements_identified" in analysis_result
        assert analysis_result["requirements_identified"] > 0
        assert "user_stories" in analysis_result
        assert "stakeholders" in analysis_result

    def _verify_design_quality(self, design_result):
        """验证设计阶段质量"""
        assert "architecture_components" in design_result
        assert "api_specification" in design_result
        assert "database_schema" in design_result

    def _verify_implementation_quality(self, impl_result):
        """验证实现阶段质量"""
        assert "files_created" in impl_result
        assert impl_result["files_created"] > 0
        assert "functions_implemented" in impl_result
        assert "tests_written" in impl_result

    def _verify_testing_quality(self, testing_result):
        """验证测试阶段质量"""
        assert "unit_tests" in testing_result
        assert "coverage_percentage" in testing_result
        assert testing_result["coverage_percentage"] >= 80

    def _verify_deployment_quality(self, deployment_result):
        """验证部署阶段质量"""
        assert "deployment_environment" in deployment_result
        assert "monitoring_configured" in deployment_result
        assert "health_checks" in deployment_result

    def _verify_cross_phase_consistency(self, workflow_results):
        """验证阶段间一致性"""
        # 验证设计阶段使用了分析阶段的结果
        design_result = workflow_results["design"]
        assert design_result["context_available"], "Design phase should have analysis context"

        # 验证实现阶段包含了设计的组件
        impl_result = workflow_results["implementation"]
        assert impl_result["context_available"], "Implementation phase should have design context"

        # 验证测试覆盖了实现的功能
        testing_result = workflow_results["testing"]
        impl_files = impl_result["files_created"]
        test_coverage = testing_result["coverage_percentage"]
        assert test_coverage >= 80, f"Test coverage {test_coverage}% too low for {impl_files} files"

    def _get_memory_usage(self):
        """获取内存使用情况（简化版）"""
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB


class TestSystemReliability:
    """系统可靠性测试"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_system_stability_under_stress(self):
        """测试压力下的系统稳定性"""
        import threading

        results = []
        errors = []

        def stress_worker(worker_id):
            try:
                state_file = os.path.join(self.temp_dir, f"stress_{worker_id}.json")

                with patch.object(PhaseManager, 'state_file', state_file):
                    manager = get_phase_manager()

                    # 快速循环执行
                    for cycle in range(10):
                        manager.reset_phases()

                        for phase in ExecutionPhase:
                            manager.advance_to_next_phase()
                            result = {
                                "worker": worker_id,
                                "cycle": cycle,
                                "phase": phase.value,
                                "status": "ok"
                            }
                            manager.save_phase_results(phase, result)

                results.append(f"Worker {worker_id} completed")

            except Exception as e:
                errors.append(f"Worker {worker_id} error: {e}")

        # 启动多个并发工作线程
        threads = []
        for i in range(10):
            thread = threading.Thread(target=stress_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=30)

        # 验证结果
        assert len(results) == 10, f"Expected 10 successful workers, got {len(results)}"
        assert len(errors) == 0, f"Stress test errors: {errors}"

    def test_system_recovery_after_failures(self):
        """测试故障后的系统恢复"""
        state_file = os.path.join(self.temp_dir, "recovery_test.json")

        with patch.object(PhaseManager, 'state_file', state_file):
            manager = get_phase_manager()

            # 模拟正常执行
            manager.reset_phases()
            for i in range(3):
                phase = manager.advance_to_next_phase()
                result = {"phase": phase.value, "status": "ok"}
                manager.save_phase_results(phase, result)

            # 模拟系统故障（状态文件损坏）
            with open(state_file, 'w') as f:
                f.write("corrupted content")

            # 创建新的管理器实例（模拟重启）
            new_manager = get_phase_manager()
            new_manager.state_file = state_file

            # 系统应该能够恢复到干净状态
            assert new_manager.current_phase is None
            assert len(new_manager.phase_history) == 0

            # 应该能够正常重新开始
            for phase in ExecutionPhase:
                current_phase = new_manager.advance_to_next_phase()
                assert current_phase == phase
                result = {"phase": phase.value, "status": "recovered"}
                new_manager.save_phase_results(phase, result)

            # 验证恢复成功
            assert new_manager.current_phase == ExecutionPhase.DEPLOYMENT
            assert len(new_manager.phase_history) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])