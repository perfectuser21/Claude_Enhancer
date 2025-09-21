#!/usr/bin/env python3
"""
Claude Enhancer 5阶段执行工作流测试套件
测试完整的5阶段开发工作流程
"""

import pytest
import json
import tempfile
import os
import sys
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


class TestFivePhaseExecution:
    """5阶段执行工作流测试"""

    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "workflow_state.json")

    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_authentication_system_workflow(self):
        """测试用户认证系统的完整5阶段工作流"""
        with patch.object(PhaseManager, 'state_file', self.state_file):
            manager = get_phase_manager()
            manager.reset_phases()

            # 模拟用户请求：实现用户认证系统
            user_request = "实现用户认证系统，包括注册、登录、JWT令牌管理和权限控制"

            # 阶段1：需求分析
            self._execute_analysis_phase(manager, user_request)

            # 阶段2：架构设计
            self._execute_design_phase(manager)

            # 阶段3：实现开发
            self._execute_implementation_phase(manager)

            # 阶段4：测试验证
            self._execute_testing_phase(manager)

            # 阶段5：部署上线
            self._execute_deployment_phase(manager)

            # 验证完整工作流
            assert manager.current_phase == ExecutionPhase.DEPLOYMENT
            assert len(manager.phase_history) == 5

            # 验证所有阶段都有结果
            for phase in ExecutionPhase:
                assert phase.value in manager.context_pool

            # 生成摘要
            summary = manager.generate_phase_summary()
            assert "需求分析" in summary
            assert "架构设计" in summary
            assert "实现开发" in summary
            assert "测试验证" in summary
            assert "部署上线" in summary

    def test_api_development_workflow(self):
        """测试API开发的5阶段工作流"""
        with patch.object(PhaseManager, 'state_file', self.state_file):
            manager = get_phase_manager()
            manager.reset_phases()

            user_request = "开发RESTful API，包括用户管理、数据CRUD操作和API文档"

            # 执行所有阶段
            phase_results = {}
            for phase in ExecutionPhase:
                current_phase = manager.advance_to_next_phase()
                assert current_phase == phase

                # 获取阶段配置
                config = manager.phase_config[phase]

                # 模拟agent执行
                agents_used = config["agents"][:config["min_agents"]]
                is_valid, errors = manager.validate_agent_execution(agents_used)
                assert is_valid, f"Phase {phase.value} validation failed: {errors}"

                # 模拟阶段结果
                phase_result = self._generate_mock_phase_result(phase, user_request)
                manager.save_phase_results(phase, phase_result)
                phase_results[phase.value] = phase_result

            # 验证上下文传递
            final_context = manager.get_context_for_phase(ExecutionPhase.DEPLOYMENT)
            assert "analysis" in final_context
            assert "design" in final_context
            assert "impl" in final_context
            assert "testing" in final_context

    def test_database_design_workflow(self):
        """测试数据库设计的5阶段工作流"""
        with patch.object(PhaseManager, 'state_file', self.state_file):
            manager = get_phase_manager()
            manager.reset_phases()

            user_request = "设计用户管理数据库，包括用户表、角色权限、审计日志"

            # 测试数据库相关的工作流
            workflow_results = self._execute_complete_workflow(manager, user_request)

            # 验证数据库特定的结果
            design_results = workflow_results[ExecutionPhase.DESIGN.value]
            assert "database_schema" in design_results
            assert "entity_relationships" in design_results

            impl_results = workflow_results[ExecutionPhase.IMPLEMENTATION.value]
            assert "migration_scripts" in impl_results
            assert "database_setup" in impl_results

    def test_frontend_development_workflow(self):
        """测试前端开发的5阶段工作流"""
        with patch.object(PhaseManager, 'state_file', self.state_file):
            manager = get_phase_manager()
            manager.reset_phases()

            user_request = "开发React前端应用，包括用户界面、状态管理、组件设计"

            workflow_results = self._execute_complete_workflow(manager, user_request)

            # 验证前端特定的结果
            design_results = workflow_results[ExecutionPhase.DESIGN.value]
            assert "component_architecture" in design_results
            assert "ui_design" in design_results

            impl_results = workflow_results[ExecutionPhase.IMPLEMENTATION.value]
            assert "react_components" in impl_results
            assert "state_management" in impl_results

    def test_workflow_interruption_and_recovery(self):
        """测试工作流中断和恢复"""
        with patch.object(PhaseManager, 'state_file', self.state_file):
            manager = get_phase_manager()
            manager.reset_phases()

            # 执行前3个阶段
            for i in range(3):
                phase = manager.advance_to_next_phase()
                result = self._generate_mock_phase_result(phase, "测试中断恢复")
                manager.save_phase_results(phase, result)

            # 保存状态
            manager.save_state()
            assert manager.current_phase == ExecutionPhase.IMPLEMENTATION

            # 模拟系统重启 - 创建新的管理器
            new_manager = get_phase_manager()
            new_manager.state_file = self.state_file
            new_manager.load_state()

            # 验证状态恢复
            assert new_manager.current_phase == ExecutionPhase.IMPLEMENTATION
            assert len(new_manager.phase_history) == 3
            assert len(new_manager.context_pool) == 3

            # 继续执行剩余阶段
            for i in range(2):  # TESTING 和 DEPLOYMENT
                phase = new_manager.advance_to_next_phase()
                result = self._generate_mock_phase_result(phase, "恢复后执行")
                new_manager.save_phase_results(phase, result)

            # 验证完整性
            assert new_manager.current_phase == ExecutionPhase.DEPLOYMENT
            assert len(new_manager.phase_history) == 5

    def test_workflow_error_handling(self):
        """测试工作流错误处理"""
        with patch.object(PhaseManager, 'state_file', self.state_file):
            manager = get_phase_manager()
            manager.reset_phases()

            # 测试阶段验证失败
            manager.current_phase = ExecutionPhase.ANALYSIS

            # 使用不足的agents
            insufficient_agents = ["requirements-analyst"]  # 需要3个，只提供1个
            is_valid, errors = manager.validate_agent_execution(insufficient_agents)

            assert not is_valid
            assert len(errors) > 0
            assert "需要至少3个agents" in errors[0]

            # 测试缺少必需agents
            wrong_agents = ["wrong-agent-1", "wrong-agent-2", "wrong-agent-3"]
            is_valid, errors = manager.validate_agent_execution(wrong_agents)

            assert not is_valid
            assert any("缺少必需的agents" in error for error in errors)

    def test_workflow_performance(self):
        """测试工作流执行性能"""
        with patch.object(PhaseManager, 'state_file', self.state_file):
            manager = get_phase_manager()

            start_time = time.time()

            # 执行10个完整的工作流周期
            for cycle in range(10):
                manager.reset_phases()

                for phase in ExecutionPhase:
                    current_phase = manager.advance_to_next_phase()
                    assert current_phase == phase

                    result = {"cycle": cycle, "phase": phase.value, "timestamp": time.time()}
                    manager.save_phase_results(phase, result)

            end_time = time.time()
            execution_time = end_time - start_time

            # 10个完整周期应该在5秒内完成
            assert execution_time < 5.0, f"Workflow execution too slow: {execution_time}s"

    def _execute_analysis_phase(self, manager, user_request):
        """执行需求分析阶段"""
        phase = manager.advance_to_next_phase()
        assert phase == ExecutionPhase.ANALYSIS

        # 获取阶段指令
        instructions = manager.generate_phase_instructions(phase, {})
        assert len(instructions["agents_to_call"]) >= 3

        # 验证agents
        required_agents = ["requirements-analyst", "business-analyst", "project-manager"]
        is_valid, errors = manager.validate_agent_execution(required_agents)
        assert is_valid

        # 模拟分析结果
        analysis_results = {
            "user_stories": [
                "作为用户，我希望能够注册账户",
                "作为用户，我希望能够安全登录",
                "作为管理员，我希望能够管理用户权限"
            ],
            "functional_requirements": [
                "用户注册功能",
                "用户登录/登出功能",
                "JWT令牌管理",
                "角色权限控制"
            ],
            "non_functional_requirements": {
                "security": "密码加密存储，JWT令牌过期机制",
                "performance": "登录响应时间<2秒",
                "scalability": "支持1000+并发用户"
            },
            "acceptance_criteria": {
                "registration": "用户能够使用邮箱和密码注册",
                "login": "用户能够使用凭据登录并获得令牌",
                "authorization": "受保护的端点需要有效令牌"
            }
        }

        manager.save_phase_results(phase, analysis_results)
        return analysis_results

    def _execute_design_phase(self, manager):
        """执行架构设计阶段"""
        context = manager.get_context_for_phase(ExecutionPhase.DESIGN)
        phase = manager.advance_to_next_phase()
        assert phase == ExecutionPhase.DESIGN

        # 验证agents
        required_agents = ["api-designer", "backend-architect", "database-specialist", "frontend-specialist"]
        is_valid, errors = manager.validate_agent_execution(required_agents)
        assert is_valid

        # 模拟设计结果
        design_results = {
            "api_design": {
                "endpoints": [
                    "POST /api/auth/register",
                    "POST /api/auth/login",
                    "POST /api/auth/refresh",
                    "POST /api/auth/logout"
                ],
                "authentication": "JWT Bearer Token",
                "response_format": "JSON"
            },
            "backend_architecture": {
                "pattern": "MVC",
                "layers": ["Controller", "Service", "Repository"],
                "database": "PostgreSQL",
                "caching": "Redis"
            },
            "database_schema": {
                "tables": ["users", "roles", "user_roles", "refresh_tokens"],
                "relationships": "users -> user_roles <- roles"
            },
            "frontend_architecture": {
                "framework": "React",
                "state_management": "Redux Toolkit",
                "routing": "React Router",
                "ui_library": "Material-UI"
            }
        }

        manager.save_phase_results(phase, design_results)
        return design_results

    def _execute_implementation_phase(self, manager):
        """执行实现开发阶段"""
        context = manager.get_context_for_phase(ExecutionPhase.IMPLEMENTATION)
        phase = manager.advance_to_next_phase()
        assert phase == ExecutionPhase.IMPLEMENTATION

        # 验证agents
        required_agents = ["fullstack-engineer", "backend-architect", "frontend-specialist", "database-specialist", "test-engineer"]
        is_valid, errors = manager.validate_agent_execution(required_agents)
        assert is_valid

        # 模拟实现结果
        implementation_results = {
            "backend_implementation": {
                "controllers": ["AuthController", "UserController"],
                "services": ["AuthService", "UserService", "TokenService"],
                "models": ["User", "Role", "RefreshToken"],
                "middleware": ["Authentication", "Authorization", "RateLimit"]
            },
            "frontend_implementation": {
                "components": ["LoginForm", "RegisterForm", "Dashboard"],
                "pages": ["Login", "Register", "Profile"],
                "hooks": ["useAuth", "useApi"],
                "context": ["AuthContext"]
            },
            "database_implementation": {
                "migrations": ["001_create_users", "002_create_roles", "003_create_refresh_tokens"],
                "seeders": ["default_roles", "admin_user"],
                "indexes": ["users_email_idx", "refresh_tokens_user_id_idx"]
            },
            "tests_implemented": {
                "unit_tests": 25,
                "integration_tests": 15,
                "coverage": "85%"
            }
        }

        manager.save_phase_results(phase, implementation_results)
        return implementation_results

    def _execute_testing_phase(self, manager):
        """执行测试验证阶段"""
        context = manager.get_context_for_phase(ExecutionPhase.TESTING)
        phase = manager.advance_to_next_phase()
        assert phase == ExecutionPhase.TESTING

        # 验证agents
        required_agents = ["test-engineer", "e2e-test-specialist", "performance-tester", "security-auditor"]
        is_valid, errors = manager.validate_agent_execution(required_agents)
        assert is_valid

        # 模拟测试结果
        testing_results = {
            "unit_tests": {
                "total": 40,
                "passed": 38,
                "failed": 2,
                "coverage": "87%"
            },
            "integration_tests": {
                "total": 20,
                "passed": 19,
                "failed": 1,
                "api_tests": "通过",
                "database_tests": "通过"
            },
            "e2e_tests": {
                "user_registration_flow": "通过",
                "user_login_flow": "通过",
                "token_refresh_flow": "通过",
                "logout_flow": "通过"
            },
            "performance_tests": {
                "login_response_time": "1.2s",
                "concurrent_users": "500",
                "throughput": "100 req/s"
            },
            "security_audit": {
                "vulnerabilities": 0,
                "security_score": "A+",
                "recommendations": ["定期更新依赖", "实施安全头部"]
            }
        }

        manager.save_phase_results(phase, testing_results)
        return testing_results

    def _execute_deployment_phase(self, manager):
        """执行部署上线阶段"""
        context = manager.get_context_for_phase(ExecutionPhase.DEPLOYMENT)
        phase = manager.advance_to_next_phase()
        assert phase == ExecutionPhase.DEPLOYMENT

        # 验证agents
        required_agents = ["devops-engineer", "monitoring-specialist", "technical-writer"]
        is_valid, errors = manager.validate_agent_execution(required_agents)
        assert is_valid

        # 模拟部署结果
        deployment_results = {
            "deployment_config": {
                "environment": "production",
                "platform": "AWS ECS",
                "containers": ["api-server", "redis", "postgres"],
                "load_balancer": "ALB"
            },
            "monitoring_setup": {
                "metrics": ["CPU", "Memory", "Request Count", "Response Time"],
                "alerts": ["High Error Rate", "High Response Time"],
                "dashboards": ["System Health", "Business Metrics"]
            },
            "documentation": {
                "api_docs": "已更新",
                "deployment_guide": "已创建",
                "user_manual": "已完成",
                "troubleshooting": "已提供"
            },
            "deployment_status": {
                "status": "成功",
                "url": "https://api.example.com",
                "health_check": "通过"
            }
        }

        manager.save_phase_results(phase, deployment_results)
        return deployment_results

    def _execute_complete_workflow(self, manager, user_request):
        """执行完整的工作流并返回所有结果"""
        workflow_results = {}

        # 执行分析阶段
        analysis_results = self._execute_analysis_phase(manager, user_request)
        workflow_results[ExecutionPhase.ANALYSIS.value] = analysis_results

        # 执行设计阶段
        design_results = self._execute_design_phase(manager)
        workflow_results[ExecutionPhase.DESIGN.value] = design_results

        # 执行实现阶段
        impl_results = self._execute_implementation_phase(manager)
        workflow_results[ExecutionPhase.IMPLEMENTATION.value] = impl_results

        # 执行测试阶段
        testing_results = self._execute_testing_phase(manager)
        workflow_results[ExecutionPhase.TESTING.value] = testing_results

        # 执行部署阶段
        deployment_results = self._execute_deployment_phase(manager)
        workflow_results[ExecutionPhase.DEPLOYMENT.value] = deployment_results

        return workflow_results

    def _generate_mock_phase_result(self, phase, user_request):
        """生成模拟的阶段结果"""
        base_result = {
            "phase": phase.value,
            "user_request": user_request,
            "timestamp": time.time(),
            "status": "completed"
        }

        if phase == ExecutionPhase.ANALYSIS:
            base_result.update({
                "requirements": ["需求1", "需求2"],
                "user_stories": ["故事1", "故事2"]
            })
        elif phase == ExecutionPhase.DESIGN:
            base_result.update({
                "architecture": "微服务架构",
                "database_schema": "已设计",
                "api_design": "RESTful"
            })
        elif phase == ExecutionPhase.IMPLEMENTATION:
            base_result.update({
                "code_files": 25,
                "functions": 45,
                "tests_written": 30
            })
        elif phase == ExecutionPhase.TESTING:
            base_result.update({
                "tests_run": 50,
                "tests_passed": 48,
                "coverage": "85%"
            })
        elif phase == ExecutionPhase.DEPLOYMENT:
            base_result.update({
                "deployment_status": "成功",
                "environment": "production",
                "monitoring": "已配置"
            })

        return base_result


class TestWorkflowEdgeCases:
    """工作流边缘情况测试"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "edge_case_state.json")

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_workflow_without_previous_context(self):
        """测试没有前序上下文的工作流"""
        with patch.object(PhaseManager, 'state_file', self.state_file):
            manager = get_phase_manager()
            manager.reset_phases()

            # 直接跳到设计阶段（不常见但可能发生）
            manager.current_phase = ExecutionPhase.DESIGN

            # 获取上下文应该为空但不崩溃
            context = manager.get_context_for_phase(ExecutionPhase.DESIGN)
            assert isinstance(context, dict)
            assert len(context) == 0

            # 生成指令应该正常工作
            instructions = manager.generate_phase_instructions(ExecutionPhase.DESIGN, context)
            assert instructions["phase"] == "design"

    def test_workflow_with_corrupted_state(self):
        """测试状态文件损坏的情况"""
        # 创建损坏的状态文件
        with open(self.state_file, 'w') as f:
            f.write("corrupted json content {")

        with patch.object(PhaseManager, 'state_file', self.state_file):
            manager = get_phase_manager()

            # 应该重置到干净状态
            assert manager.current_phase is None
            assert len(manager.phase_history) == 0
            assert len(manager.context_pool) == 0

    def test_workflow_with_missing_state_directory(self):
        """测试状态目录不存在的情况"""
        missing_dir = os.path.join(self.temp_dir, "missing", "deep", "path")
        missing_state_file = os.path.join(missing_dir, "state.json")

        with patch.object(PhaseManager, 'state_file', missing_state_file):
            manager = get_phase_manager()

            # 保存状态时应该创建目录
            manager.current_phase = ExecutionPhase.ANALYSIS
            manager.save_state()

            assert os.path.exists(missing_state_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])