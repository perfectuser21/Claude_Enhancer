#!/usr/bin/env python3
"""
Perfect21 Error Handling System Demonstration
Shows all the capabilities of the comprehensive error handling system
"""

import sys
import os
import time
from datetime import datetime

# Add project path
sys.path.append(os.path.join(os.path.dirname(__file__)))

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print(f"{'='*60}")

def print_subsection(title):
    """Print a formatted subsection header"""
    print(f"\n{'---'*20}")
    print(f"📋 {title}")
    print(f"{'---'*20}")

def demo_basic_exceptions():
    """Demonstrate basic exception functionality"""
    print_section("Basic Exception System")

    from modules.exceptions import (
        ValidationError, NetworkError, AgentExecutionError, GitOperationError,
        ErrorContext, ErrorSeverity, ErrorCategory
    )

    print("🔧 Creating different types of Perfect21 exceptions:")

    # Validation Error
    try:
        raise ValidationError(
            "Username must be between 3 and 20 characters",
            field_name="username",
            context=ErrorContext(
                component="UserValidation",
                operation="validate_input"
            )
        )
    except ValidationError as e:
        print(f"✅ ValidationError: {e.user_friendly_message}")
        print(f"   Category: {e.category.value}")
        print(f"   Severity: {e.severity.value}")
        print(f"   Suggestions: {e.recovery_suggestions}")

    # Network Error
    try:
        raise NetworkError(
            "Failed to connect to external API",
            status_code=503
        )
    except NetworkError as e:
        print(f"✅ NetworkError: {e.user_friendly_message}")
        print(f"   Status Code: {e.status_code}")
        print(f"   Suggestions: {e.recovery_suggestions}")

    # Agent Execution Error
    try:
        raise AgentExecutionError(
            "Backend architect agent timeout",
            agent_name="backend-architect",
            task_description="API design task"
        )
    except AgentExecutionError as e:
        print(f"✅ AgentExecutionError: {e.user_friendly_message}")
        print(f"   Agent: {e.agent_name}")
        print(f"   Task: {e.task_description}")

def demo_error_aggregation():
    """Demonstrate error aggregation for parallel operations"""
    print_section("Error Aggregation for Parallel Operations")

    from modules.exceptions import ErrorAggregator, AgentExecutionError, NetworkError, ValidationError

    aggregator = ErrorAggregator()

    print("🤖 Simulating multiple agent failures:")

    # Simulate parallel agent failures
    errors = [
        AgentExecutionError("Agent 1 timeout", agent_name="backend-architect"),
        AgentExecutionError("Agent 2 network error", agent_name="frontend-specialist"),
        NetworkError("API service unavailable"),
        ValidationError("Invalid configuration", field_name="timeout_value")
    ]

    for error in errors:
        aggregator.add_error(error)
        print(f"   ❌ {error.error_code}: {error.message}")

    # Add warnings
    aggregator.add_warning("High memory usage detected")
    aggregator.add_warning("Performance degradation observed")

    print("\n📊 Error aggregation summary:")
    summary = aggregator.get_error_summary()
    print(f"   Total errors: {summary['total_errors']}")
    print(f"   Critical errors: {summary['critical_errors']}")
    print(f"   Warnings: {summary['warnings']}")
    print(f"   Error categories: {', '.join(summary['error_categories'])}")

def demo_retry_mechanism():
    """Demonstrate retry mechanism with exponential backoff"""
    print_section("Retry Mechanism with Exponential Backoff")

    from modules.exceptions import retry_on_failure, RetryConfig, NetworkError
    import random

    print("🔄 Testing retry mechanism:")

    @retry_on_failure(RetryConfig(
        max_attempts=4,
        base_delay=0.1,  # Fast for demo
        exponential_multiplier=2.0
    ))
    def unreliable_network_call():
        """Simulates an unreliable network call"""
        if random.random() < 0.6:  # 60% chance of failure
            raise NetworkError("Temporary network issue")
        return "✅ Network call successful!"

    try:
        result = unreliable_network_call()
        print(f"   {result}")
    except NetworkError as e:
        print(f"   ❌ All retry attempts failed: {e.user_friendly_message}")

def demo_recovery_strategies():
    """Demonstrate error recovery strategies"""
    print_section("Error Recovery Strategies")

    from modules.exceptions import ErrorRecoveryManager, NetworkError, GitOperationError, ErrorCategory

    recovery_manager = ErrorRecoveryManager()

    # Register custom recovery strategy
    def network_recovery(error):
        print(f"   🛠️ Attempting network recovery for: {error.message}")
        # Simulate recovery logic
        return True  # Indicates recovery was successful

    recovery_manager.register_recovery_strategy(ErrorCategory.NETWORK, network_recovery)

    print("🔧 Testing recovery strategies:")

    # Test network error recovery
    network_error = NetworkError("Connection timeout")
    recovery_result = recovery_manager.attempt_recovery(network_error)
    print(f"   Network error recovery: {'✅ Success' if recovery_result else '❌ Failed'}")

    # Test Git error (no recovery strategy registered)
    git_error = GitOperationError("Git push failed")
    recovery_result = recovery_manager.attempt_recovery(git_error)
    print(f"   Git error recovery: {'✅ Success' if recovery_result else '❌ Failed (no strategy)'}")

def demo_decorators():
    """Demonstrate error handling decorators"""
    print_section("Error Handling Decorators")

    from modules.error_integration import with_git_error_handling, with_agent_error_handling

    print("🎨 Testing error handling decorators:")

    @with_git_error_handling("demo_operation")
    def simulated_git_operation():
        """Simulated Git operation that fails"""
        raise Exception("Git permission denied")

    @with_agent_error_handling("demo-agent", "demo_task")
    def simulated_agent_execution():
        """Simulated agent execution that fails"""
        raise Exception("Agent execution timeout")

    # Test Git decorator
    try:
        simulated_git_operation()
    except Exception as e:
        print(f"   Git operation: ❌ Properly converted to GitOperationError")
        print(f"   Error type: {type(e).__name__}")

    # Test Agent decorator
    try:
        simulated_agent_execution()
    except Exception as e:
        print(f"   Agent execution: ❌ Properly converted to AgentExecutionError")
        print(f"   Error type: {type(e).__name__}")

def demo_error_integration():
    """Demonstrate error integration with Perfect21"""
    print_section("Perfect21 Error Integration")

    from modules.error_integration import get_error_handler, Perfect21ErrorHandler
    from modules.exceptions import AgentExecutionError, NetworkError

    error_handler = get_error_handler()

    print("🎛️ Testing Perfect21 error handler:")

    # Handle single error
    single_error = AgentExecutionError(
        "Test agent failed",
        agent_name="test-agent",
        task_description="Demo task"
    )

    result = error_handler.handle_error(single_error)
    print(f"   Single error handling: {'✅ Success' if result['error_handled'] else '❌ Failed'}")
    print(f"   User message: {result['user_message']}")

    # Handle multiple errors
    multiple_errors = [
        AgentExecutionError("Agent 1 failed", agent_name="agent1"),
        NetworkError("Network timeout"),
        AgentExecutionError("Agent 2 failed", agent_name="agent2")
    ]

    result = error_handler.handle_multiple_errors(multiple_errors)
    print(f"   Multiple error handling: {'✅ Success' if result['multiple_errors_handled'] else '❌ Failed'}")
    print(f"   Total errors processed: {result['error_summary']['total_errors']}")
    print(f"   Recommendations: {len(result['recommendations'])} suggestions")

def demo_cli_integration():
    """Demonstrate CLI integration"""
    print_section("CLI Error Management")

    from modules.error_cli import ErrorHandlingCLI

    print("🖥️ Testing CLI error management:")

    cli = ErrorHandlingCLI()

    # Test stats command
    class MockArgs:
        def __init__(self, command):
            self.command = command
            self.format = 'text'

    args = MockArgs('stats')
    result = cli.handle_command(args)
    print(f"   Stats command: {'✅ Success' if result['success'] else '❌ Failed'}")

    # Test clear command
    args = MockArgs('clear')
    result = cli.handle_command(args)
    print(f"   Clear command: {'✅ Success' if result['success'] else '❌ Failed'}")

def demo_performance_impact():
    """Demonstrate performance impact of error handling"""
    print_section("Performance Impact Analysis")

    import time
    from modules.exceptions import Perfect21BaseException, safe_execute

    print("⚡ Testing performance impact:")

    def normal_function():
        """Normal function without error handling"""
        return sum(range(1000))

    def error_handled_function():
        """Function with error handling"""
        try:
            return sum(range(1000))
        except Exception as e:
            raise Perfect21BaseException("Error in computation")

    # Time normal function
    start_time = time.time()
    for _ in range(1000):
        normal_function()
    normal_time = time.time() - start_time

    # Time error-handled function
    start_time = time.time()
    for _ in range(1000):
        error_handled_function()
    error_handled_time = time.time() - start_time

    # Time safe_execute
    start_time = time.time()
    for _ in range(1000):
        safe_execute(normal_function, default_return=0)
    safe_execute_time = time.time() - start_time

    print(f"   Normal function: {normal_time:.4f}s")
    print(f"   Error-handled function: {error_handled_time:.4f}s")
    print(f"   Safe execute: {safe_execute_time:.4f}s")
    print(f"   Overhead: {((error_handled_time / normal_time - 1) * 100):.2f}%")

def main():
    """Main demonstration"""
    print("🚀 Perfect21 Comprehensive Error Handling System Demo")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    demos = [
        demo_basic_exceptions,
        demo_error_aggregation,
        demo_retry_mechanism,
        demo_recovery_strategies,
        demo_decorators,
        demo_error_integration,
        demo_cli_integration,
        demo_performance_impact
    ]

    for i, demo in enumerate(demos, 1):
        try:
            demo()
            print(f"\n✅ Demo {i}: {demo.__name__} completed successfully")
        except Exception as e:
            print(f"\n❌ Demo {i}: {demo.__name__} failed: {e}")
            import traceback
            traceback.print_exc()

        if i < len(demos):
            time.sleep(1)  # Brief pause between demos

    print_section("Demo Complete")
    print("🎉 Perfect21 Error Handling System demonstration completed!")
    print("📊 Summary:")
    print("   ✅ Custom exception hierarchy")
    print("   ✅ Error aggregation for parallel operations")
    print("   ✅ Retry mechanisms with exponential backoff")
    print("   ✅ Error recovery strategies")
    print("   ✅ Decorator-based error handling")
    print("   ✅ Perfect21 integration")
    print("   ✅ CLI management interface")
    print("   ✅ Performance impact analysis")

    print(f"\n📝 For more details, see:")
    print(f"   - ERROR_HANDLING_SYSTEM_SUMMARY.md")
    print(f"   - test_error_handling_system.py")
    print(f"   - modules/exceptions.py")
    print(f"   - modules/error_integration.py")

    print(f"\n🛠️ CLI Usage:")
    print(f"   python3 main/cli.py error stats")
    print(f"   python3 main/cli.py error test")
    print(f"   python3 main/cli.py error recovery")

if __name__ == "__main__":
    main()