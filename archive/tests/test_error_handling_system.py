#!/usr/bin/env python3
"""
Perfect21 Error Handling System Test
Comprehensive test suite for the error handling system
"""

import sys
import os
import time
import traceback
from datetime import datetime
from typing import Dict, Any, List

# Add project path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from modules.exceptions import (
    Perfect21BaseException, ValidationError, NetworkError, AuthenticationError,
    PermissionError, TimeoutError, ResourceError, ExternalAPIError,
    GitOperationError, AgentExecutionError, WorkflowError, DatabaseError,
    FileSystemError, ConfigurationError, ErrorAggregator, ErrorLogger,
    ErrorRecoveryManager, RetryHandler, ErrorSeverity, ErrorCategory,
    ErrorContext, RetryConfig, handle_exceptions, safe_execute, retry_on_failure
)
from modules.error_integration import (
    Perfect21ErrorHandler, get_error_handler, with_git_error_handling,
    with_agent_error_handling, with_workflow_error_handling
)
from modules.logger import Perfect21Logger

# Test logger
test_logger = Perfect21Logger("ErrorHandlingTest")

class ErrorHandlingSystemTest:
    """Test suite for Perfect21 error handling system"""

    def __init__(self):
        self.test_results = []
        self.error_handler = get_error_handler()

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all error handling tests"""
        print("🧪 Starting Perfect21 Error Handling System Tests")
        print("=" * 60)

        tests = [
            self.test_basic_exceptions,
            self.test_error_aggregation,
            self.test_retry_mechanism,
            self.test_error_recovery,
            self.test_decorators,
            self.test_parallel_error_handling,
            self.test_git_error_handling,
            self.test_agent_error_handling,
            self.test_workflow_error_handling,
            self.test_error_logging_integration
        ]

        total_tests = len(tests)
        passed_tests = 0
        failed_tests = 0

        for test in tests:
            try:
                print(f"\n🔍 Running: {test.__name__}")
                result = test()
                if result.get('success', False):
                    print(f"✅ {test.__name__}: PASSED")
                    passed_tests += 1
                else:
                    print(f"❌ {test.__name__}: FAILED - {result.get('error', 'Unknown error')}")
                    failed_tests += 1
                self.test_results.append(result)
            except Exception as e:
                print(f"💥 {test.__name__}: CRASHED - {str(e)}")
                failed_tests += 1
                self.test_results.append({
                    'test_name': test.__name__,
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })

        # Summary
        print(f"\n📊 Test Summary:")
        print(f"=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'test_results': self.test_results
        }

    def test_basic_exceptions(self) -> Dict[str, Any]:
        """Test basic exception creation and handling"""
        try:
            # Test different exception types
            exceptions_to_test = [
                ValidationError("Invalid input", field_name="username"),
                NetworkError("Connection timeout", status_code=408),
                AuthenticationError("Invalid credentials"),
                GitOperationError("Git command failed", git_command="git push"),
                AgentExecutionError("Agent timeout", agent_name="backend-architect", task_description="Create API"),
                WorkflowError("Step failed", workflow_name="deployment", step="build")
            ]

            for exception in exceptions_to_test:
                # Test exception properties
                assert exception.error_code is not None
                assert exception.category is not None
                assert exception.severity is not None
                assert exception.user_friendly_message is not None
                assert isinstance(exception.recovery_suggestions, list)

                # Test conversion to dict
                error_dict = exception.to_dict()
                assert 'error_code' in error_dict
                assert 'message' in error_dict
                assert 'category' in error_dict
                assert 'severity' in error_dict

            return {'test_name': 'test_basic_exceptions', 'success': True}

        except Exception as e:
            return {'test_name': 'test_basic_exceptions', 'success': False, 'error': str(e)}

    def test_error_aggregation(self) -> Dict[str, Any]:
        """Test error aggregation for parallel operations"""
        try:
            aggregator = ErrorAggregator()

            # Add multiple errors
            errors = [
                AgentExecutionError("Agent 1 failed", agent_name="agent1"),
                AgentExecutionError("Agent 2 timeout", agent_name="agent2"),
                NetworkError("Connection lost"),
                ValidationError("Invalid parameter", field_name="config")
            ]

            for error in errors:
                aggregator.add_error(error)

            # Add warnings
            aggregator.add_warning("Performance degraded")
            aggregator.add_warning("Memory usage high")

            # Test aggregation methods
            assert aggregator.has_errors() == True
            assert len(aggregator.errors) == 4
            assert len(aggregator.warnings) == 2

            summary = aggregator.get_error_summary()
            assert summary['total_errors'] == 4
            assert summary['warnings'] == 2
            assert len(summary['error_categories']) > 0

            return {'test_name': 'test_error_aggregation', 'success': True}

        except Exception as e:
            return {'test_name': 'test_error_aggregation', 'success': False, 'error': str(e)}

    def test_retry_mechanism(self) -> Dict[str, Any]:
        """Test retry mechanism with exponential backoff"""
        try:
            retry_config = RetryConfig(
                max_attempts=3,
                base_delay=0.1,  # Short delay for testing
                exponential_multiplier=2.0,
                jitter=False  # Disable for predictable testing
            )

            retry_handler = RetryHandler(retry_config)

            # Test successful retry
            attempt_count = 0

            def failing_function():
                nonlocal attempt_count
                attempt_count += 1
                if attempt_count < 3:
                    raise NetworkError("Temporary failure")
                return "Success"

            result = retry_handler._execute_with_retry(failing_function)
            assert result == "Success"
            assert attempt_count == 3

            # Test exhausted retries
            attempt_count = 0

            def always_failing_function():
                nonlocal attempt_count
                attempt_count += 1
                raise NetworkError("Permanent failure")

            try:
                retry_handler._execute_with_retry(always_failing_function)
                assert False, "Should have raised exception"
            except NetworkError:
                pass  # Expected

            assert attempt_count == 3

            return {'test_name': 'test_retry_mechanism', 'success': True}

        except Exception as e:
            return {'test_name': 'test_retry_mechanism', 'success': False, 'error': str(e)}

    def test_error_recovery(self) -> Dict[str, Any]:
        """Test error recovery strategies"""
        try:
            recovery_manager = ErrorRecoveryManager()

            # Register a test recovery strategy
            def test_recovery(error):
                return error.category == ErrorCategory.NETWORK

            recovery_manager.register_recovery_strategy(ErrorCategory.NETWORK, test_recovery)

            # Test recovery
            network_error = NetworkError("Connection failed")
            result = recovery_manager.attempt_recovery(network_error)
            assert result == True

            # Test no recovery for other categories
            git_error = GitOperationError("Git failed")
            result = recovery_manager.attempt_recovery(git_error)
            assert result == False

            return {'test_name': 'test_error_recovery', 'success': True}

        except Exception as e:
            return {'test_name': 'test_error_recovery', 'success': False, 'error': str(e)}

    def test_decorators(self) -> Dict[str, Any]:
        """Test error handling decorators"""
        try:
            # Test handle_exceptions decorator
            @handle_exceptions(
                exceptions=(ValueError,),
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW
            )
            def test_function_with_decorator():
                raise ValueError("Test error")

            try:
                test_function_with_decorator()
                assert False, "Should have raised Perfect21BaseException"
            except Perfect21BaseException as e:
                assert e.category == ErrorCategory.VALIDATION
                assert e.severity == ErrorSeverity.LOW

            # Test safe_execute
            def failing_function():
                raise ValueError("Test error")

            result = safe_execute(failing_function, default_return="default")
            assert result == "default"

            return {'test_name': 'test_decorators', 'success': True}

        except Exception as e:
            return {'test_name': 'test_decorators', 'success': False, 'error': str(e)}

    def test_parallel_error_handling(self) -> Dict[str, Any]:
        """Test error handling in parallel execution scenarios"""
        try:
            # Simulate parallel agent execution with errors
            agent_results = [
                {"agent_name": "agent1", "success": True, "output": "Success"},
                {"agent_name": "agent2", "success": False, "error": "Timeout"},
                {"agent_name": "agent3", "success": False, "error": "Network error"},
                {"agent_name": "agent4", "success": True, "output": "Success"}
            ]

            errors = []
            for result in agent_results:
                if not result["success"]:
                    error = AgentExecutionError(
                        message=f"Agent {result['agent_name']} failed: {result['error']}",
                        agent_name=result["agent_name"]
                    )
                    errors.append(error)

            # Test multiple error handling
            if errors:
                result = self.error_handler.handle_multiple_errors(errors)
                assert result['multiple_errors_handled'] == True
                assert 'error_summary' in result
                assert 'recommendations' in result

            return {'test_name': 'test_parallel_error_handling', 'success': True}

        except Exception as e:
            return {'test_name': 'test_parallel_error_handling', 'success': False, 'error': str(e)}

    def test_git_error_handling(self) -> Dict[str, Any]:
        """Test Git-specific error handling"""
        try:
            @with_git_error_handling("test_operation")
            def test_git_function():
                raise Exception("Git permission denied")

            try:
                test_git_function()
                assert False, "Should have raised GitOperationError"
            except GitOperationError as e:
                assert e.category == ErrorCategory.GIT_OPERATION
                assert "test_operation" in str(e.message)

            return {'test_name': 'test_git_error_handling', 'success': True}

        except Exception as e:
            return {'test_name': 'test_git_error_handling', 'success': False, 'error': str(e)}

    def test_agent_error_handling(self) -> Dict[str, Any]:
        """Test Agent-specific error handling"""
        try:
            @with_agent_error_handling("test-agent", "test_task")
            def test_agent_function():
                raise Exception("Agent execution failed")

            try:
                test_agent_function()
                assert False, "Should have raised AgentExecutionError"
            except AgentExecutionError as e:
                assert e.category == ErrorCategory.AGENT_EXECUTION
                assert "test-agent" in str(e.message)

            return {'test_name': 'test_agent_error_handling', 'success': True}

        except Exception as e:
            return {'test_name': 'test_agent_error_handling', 'success': False, 'error': str(e)}

    def test_workflow_error_handling(self) -> Dict[str, Any]:
        """Test Workflow-specific error handling"""
        try:
            @with_workflow_error_handling("test-workflow", "test_step")
            def test_workflow_function():
                raise Exception("Workflow step failed")

            try:
                test_workflow_function()
                assert False, "Should have raised WorkflowError"
            except WorkflowError as e:
                assert e.category == ErrorCategory.WORKFLOW
                assert "test-workflow" in str(e.message)

            return {'test_name': 'test_workflow_error_handling', 'success': True}

        except Exception as e:
            return {'test_name': 'test_workflow_error_handling', 'success': False, 'error': str(e)}

    def test_error_logging_integration(self) -> Dict[str, Any]:
        """Test integration with logging system"""
        try:
            # Create a test error
            test_error = ValidationError(
                "Test validation error",
                field_name="test_field",
                context=ErrorContext(
                    component="TestComponent",
                    operation="test_operation"
                )
            )

            # Test error logging
            error_logger = ErrorLogger()
            error_logger.log_error(test_error)

            # Test error handling with context
            result = self.error_handler.handle_error(test_error, {"test": "context"})
            assert result['error_handled'] == True
            assert result['error_code'] == test_error.error_code

            return {'test_name': 'test_error_logging_integration', 'success': True}

        except Exception as e:
            return {'test_name': 'test_error_logging_integration', 'success': False, 'error': str(e)}

    def demonstrate_error_scenarios(self):
        """Demonstrate various error scenarios"""
        print("\n🎭 Demonstrating Error Scenarios:")
        print("=" * 60)

        scenarios = [
            self._demo_validation_error,
            self._demo_network_error,
            self._demo_agent_execution_error,
            self._demo_multiple_errors,
            self._demo_retry_mechanism
        ]

        for scenario in scenarios:
            try:
                print(f"\n📋 {scenario.__name__.replace('_demo_', '').replace('_', ' ').title()}:")
                scenario()
            except Exception as e:
                print(f"❌ Scenario failed: {e}")

    def _demo_validation_error(self):
        """Demonstrate validation error handling"""
        try:
            raise ValidationError(
                "Username must be between 3 and 20 characters",
                field_name="username"
            )
        except ValidationError as e:
            result = self.error_handler.handle_error(e)
            print(f"   💡 User Message: {e.user_friendly_message}")
            print(f"   🔧 Suggestions: {', '.join(e.recovery_suggestions)}")

    def _demo_network_error(self):
        """Demonstrate network error handling"""
        try:
            raise NetworkError(
                "Failed to connect to external API",
                status_code=503
            )
        except NetworkError as e:
            result = self.error_handler.handle_error(e)
            print(f"   💡 User Message: {e.user_friendly_message}")
            print(f"   🔧 Suggestions: {', '.join(e.recovery_suggestions)}")

    def _demo_agent_execution_error(self):
        """Demonstrate agent execution error handling"""
        try:
            raise AgentExecutionError(
                "Backend architect agent timed out during API design",
                agent_name="backend-architect",
                task_description="Design REST API for user management"
            )
        except AgentExecutionError as e:
            result = self.error_handler.handle_error(e)
            print(f"   💡 User Message: {e.user_friendly_message}")
            print(f"   🤖 Agent: {e.agent_name}")
            print(f"   📋 Task: {e.task_description}")

    def _demo_multiple_errors(self):
        """Demonstrate multiple error handling"""
        errors = [
            AgentExecutionError("Agent 1 failed", agent_name="agent1"),
            AgentExecutionError("Agent 2 timed out", agent_name="agent2"),
            NetworkError("API unavailable"),
            ValidationError("Invalid config", field_name="timeout")
        ]

        result = self.error_handler.handle_multiple_errors(errors)
        print(f"   📊 Total Errors: {result['error_summary']['total_errors']}")
        print(f"   📈 Categories: {', '.join(result['error_summary']['error_categories'])}")
        print(f"   💡 Recommendations: {len(result['recommendations'])} suggestions")

    def _demo_retry_mechanism(self):
        """Demonstrate retry mechanism"""
        @retry_on_failure(RetryConfig(max_attempts=3, base_delay=0.1))
        def unreliable_function():
            import random
            if random.random() < 0.7:  # 70% chance of failure
                raise NetworkError("Temporary network issue")
            return "Success after retry"

        try:
            result = unreliable_function()
            print(f"   ✅ Function succeeded: {result}")
        except NetworkError as e:
            print(f"   ❌ Function failed after retries: {e.user_friendly_message}")


def main():
    """Main test execution"""
    print("🚀 Perfect21 Error Handling System Test Suite")
    print("=" * 60)

    # Create test instance
    test_suite = ErrorHandlingSystemTest()

    # Run all tests
    results = test_suite.run_all_tests()

    # Demonstrate error scenarios
    test_suite.demonstrate_error_scenarios()

    # Save test results
    import json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"error_handling_test_results_{timestamp}.json"

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Test results saved to: {results_file}")

    # Exit with appropriate code
    exit_code = 0 if results['failed_tests'] == 0 else 1
    print(f"\n🏁 Tests completed with exit code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)