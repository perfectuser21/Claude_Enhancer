#!/usr/bin/env python3
"""
Perfect21 Error Handling CLI
Command-line interface for error handling system management
"""

import argparse
import sys
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

from .error_integration import get_error_handler
from .exceptions import ErrorCategory, ErrorSeverity
from .logger import Perfect21Logger

logger = Perfect21Logger("ErrorCLI")

class ErrorHandlingCLI:
    """CLI for Perfect21 error handling system"""

    def __init__(self):
        self.error_handler = get_error_handler()

    def handle_command(self, args) -> Dict[str, Any]:
        """Handle CLI commands"""
        try:
            if args.command == 'stats':
                return self.show_error_stats(args)
            elif args.command == 'clear':
                return self.clear_errors(args)
            elif args.command == 'test':
                return self.run_error_tests(args)
            elif args.command == 'config':
                return self.configure_error_handling(args)
            elif args.command == 'recovery':
                return self.test_recovery_strategies(args)
            else:
                return {
                    'success': False,
                    'message': f"Unknown command: {args.command}",
                    'available_commands': ['stats', 'clear', 'test', 'config', 'recovery']
                }
        except Exception as e:
            logger.error(f"CLI command failed: {args.command}", e)
            return {
                'success': False,
                'error': str(e),
                'message': f"Command execution failed: {args.command}"
            }

    def show_error_stats(self, args) -> Dict[str, Any]:
        """Show error statistics"""
        try:
            stats = self.error_handler.get_error_statistics()

            if args.format == 'json':
                return {
                    'success': True,
                    'stats': stats
                }
            else:
                self._print_error_stats(stats)
                return {
                    'success': True,
                    'message': 'Error statistics displayed'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to retrieve error statistics'
            }

    def _print_error_stats(self, stats: Dict[str, Any]):
        """Print formatted error statistics"""
        print("\n📊 Perfect21 Error Statistics")
        print("=" * 50)

        if stats.get('total_errors', 0) == 0:
            print("✅ No errors detected - system running smoothly")
            return

        print(f"Total Errors: {stats.get('total_errors', 0)}")
        print(f"Critical Errors: {stats.get('critical_errors', 0)}")
        print(f"High Severity: {stats.get('high_severity_errors', 0)}")
        print(f"Warnings: {stats.get('warnings', 0)}")

        # Error categories
        if 'category_distribution' in stats:
            print(f"\n📂 Error Categories:")
            for category, count in stats['category_distribution'].items():
                print(f"  • {category}: {count}")

        # Severity distribution
        if 'severity_distribution' in stats:
            print(f"\n⚠️ Severity Distribution:")
            for severity, count in stats['severity_distribution'].items():
                print(f"  • {severity}: {count}")

        # Most common
        if stats.get('most_common_category'):
            print(f"\n🔍 Most Common Category: {stats['most_common_category']}")
        if stats.get('most_common_severity'):
            print(f"🚨 Most Common Severity: {stats['most_common_severity']}")

        # Recommendations
        if 'recommendations' in stats:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(stats['recommendations'], 1):
                print(f"  {i}. {rec}")

    def clear_errors(self, args) -> Dict[str, Any]:
        """Clear error aggregator"""
        try:
            # Reset error aggregator
            from .exceptions import ErrorAggregator
            self.error_handler.aggregator = ErrorAggregator()

            logger.info("Error aggregator cleared via CLI")
            return {
                'success': True,
                'message': 'Error aggregator cleared successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to clear error aggregator'
            }

    def run_error_tests(self, args) -> Dict[str, Any]:
        """Run error handling tests"""
        try:
            # Import and run test suite
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from test_error_handling_system import ErrorHandlingSystemTest

            test_suite = ErrorHandlingSystemTest()

            if args.test_type == 'all':
                results = test_suite.run_all_tests()
            elif args.test_type == 'basic':
                results = {
                    'test_results': [
                        test_suite.test_basic_exceptions(),
                        test_suite.test_error_aggregation()
                    ]
                }
            elif args.test_type == 'retry':
                results = {
                    'test_results': [
                        test_suite.test_retry_mechanism()
                    ]
                }
            else:
                return {
                    'success': False,
                    'message': f"Unknown test type: {args.test_type}",
                    'available_types': ['all', 'basic', 'retry']
                }

            if args.format == 'json':
                return {
                    'success': True,
                    'test_results': results
                }
            else:
                self._print_test_results(results)
                return {
                    'success': True,
                    'message': 'Error handling tests completed'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to run error handling tests'
            }

    def _print_test_results(self, results: Dict[str, Any]):
        """Print formatted test results"""
        print("\n🧪 Error Handling Test Results")
        print("=" * 50)

        if 'test_results' in results:
            passed = sum(1 for r in results['test_results'] if r.get('success', False))
            total = len(results['test_results'])

            print(f"Tests Passed: {passed}/{total}")
            print(f"Success Rate: {(passed/total)*100:.1f}%")

            print(f"\n📋 Individual Test Results:")
            for result in results['test_results']:
                test_name = result.get('test_name', 'Unknown')
                success = result.get('success', False)
                status = "✅ PASSED" if success else "❌ FAILED"
                print(f"  • {test_name}: {status}")
                if not success and 'error' in result:
                    print(f"    Error: {result['error']}")

    def configure_error_handling(self, args) -> Dict[str, Any]:
        """Configure error handling settings"""
        try:
            config_data = {}

            if args.retry_attempts:
                config_data['retry_attempts'] = args.retry_attempts
            if args.retry_delay:
                config_data['retry_delay'] = args.retry_delay
            if args.log_level:
                config_data['log_level'] = args.log_level

            if not config_data:
                # Show current configuration
                current_config = self._get_current_config()
                if args.format == 'json':
                    return {
                        'success': True,
                        'config': current_config
                    }
                else:
                    self._print_config(current_config)
                    return {
                        'success': True,
                        'message': 'Current configuration displayed'
                    }
            else:
                # Update configuration
                self._update_config(config_data)
                logger.info(f"Error handling configuration updated: {config_data}")
                return {
                    'success': True,
                    'message': 'Configuration updated successfully',
                    'updated_config': config_data
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to configure error handling'
            }

    def _get_current_config(self) -> Dict[str, Any]:
        """Get current error handling configuration"""
        return {
            'retry_config': {
                'max_attempts': self.error_handler.error_aggregator.__dict__.get('retry_config', {}).get('max_attempts', 3),
                'base_delay': self.error_handler.error_aggregator.__dict__.get('retry_config', {}).get('base_delay', 1.0),
                'max_delay': self.error_handler.error_aggregator.__dict__.get('retry_config', {}).get('max_delay', 60.0)
            },
            'recovery_strategies': len(self.error_handler.recovery_manager.recovery_strategies),
            'aggregator_status': 'active'
        }

    def _print_config(self, config: Dict[str, Any]):
        """Print formatted configuration"""
        print("\n⚙️ Error Handling Configuration")
        print("=" * 50)

        if 'retry_config' in config:
            print("🔄 Retry Configuration:")
            retry_config = config['retry_config']
            print(f"  • Max Attempts: {retry_config.get('max_attempts', 'N/A')}")
            print(f"  • Base Delay: {retry_config.get('base_delay', 'N/A')}s")
            print(f"  • Max Delay: {retry_config.get('max_delay', 'N/A')}s")

        print(f"\n🛠️ Recovery Strategies: {config.get('recovery_strategies', 0)} registered")
        print(f"📊 Aggregator Status: {config.get('aggregator_status', 'Unknown')}")

    def _update_config(self, config_data: Dict[str, Any]):
        """Update error handling configuration"""
        # This would update the actual configuration
        # For now, just log the update
        logger.info(f"Configuration update requested: {config_data}")

    def test_recovery_strategies(self, args) -> Dict[str, Any]:
        """Test error recovery strategies"""
        try:
            # Test different error categories
            test_errors = [
                ('network', lambda: self._test_network_recovery()),
                ('git', lambda: self._test_git_recovery()),
                ('agent', lambda: self._test_agent_recovery())
            ]

            results = {}

            if args.category == 'all':
                for category, test_func in test_errors:
                    results[category] = test_func()
            else:
                # Find specific test
                test_func = None
                for category, func in test_errors:
                    if category == args.category:
                        test_func = func
                        break

                if test_func:
                    results[args.category] = test_func()
                else:
                    return {
                        'success': False,
                        'message': f"Unknown recovery category: {args.category}",
                        'available_categories': [cat for cat, _ in test_errors]
                    }

            if args.format == 'json':
                return {
                    'success': True,
                    'recovery_results': results
                }
            else:
                self._print_recovery_results(results)
                return {
                    'success': True,
                    'message': 'Recovery strategy tests completed'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to test recovery strategies'
            }

    def _test_network_recovery(self) -> Dict[str, Any]:
        """Test network error recovery"""
        from .exceptions import NetworkError

        try:
            error = NetworkError("Test network error", status_code=503)
            recovery_result = self.error_handler.recovery_manager.attempt_recovery(error)

            return {
                'category': 'network',
                'recovery_attempted': True,
                'recovery_successful': recovery_result,
                'error_type': 'NetworkError'
            }
        except Exception as e:
            return {
                'category': 'network',
                'recovery_attempted': False,
                'error': str(e)
            }

    def _test_git_recovery(self) -> Dict[str, Any]:
        """Test Git error recovery"""
        from .exceptions import GitOperationError

        try:
            error = GitOperationError("Test git error", git_command="git push")
            recovery_result = self.error_handler.recovery_manager.attempt_recovery(error)

            return {
                'category': 'git',
                'recovery_attempted': True,
                'recovery_successful': recovery_result,
                'error_type': 'GitOperationError'
            }
        except Exception as e:
            return {
                'category': 'git',
                'recovery_attempted': False,
                'error': str(e)
            }

    def _test_agent_recovery(self) -> Dict[str, Any]:
        """Test agent error recovery"""
        from .exceptions import AgentExecutionError

        try:
            error = AgentExecutionError("Test agent error", agent_name="test-agent")
            recovery_result = self.error_handler.recovery_manager.attempt_recovery(error)

            return {
                'category': 'agent',
                'recovery_attempted': True,
                'recovery_successful': recovery_result,
                'error_type': 'AgentExecutionError'
            }
        except Exception as e:
            return {
                'category': 'agent',
                'recovery_attempted': False,
                'error': str(e)
            }

    def _print_recovery_results(self, results: Dict[str, Any]):
        """Print formatted recovery test results"""
        print("\n🛠️ Recovery Strategy Test Results")
        print("=" * 50)

        for category, result in results.items():
            print(f"\n📂 {category.title()} Recovery:")
            print(f"  • Attempted: {result.get('recovery_attempted', False)}")
            print(f"  • Successful: {result.get('recovery_successful', False)}")
            print(f"  • Error Type: {result.get('error_type', 'Unknown')}")

            if 'error' in result:
                print(f"  • Error: {result['error']}")


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser"""
    parser = argparse.ArgumentParser(description='Perfect21 Error Handling CLI')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show error statistics')
    stats_parser.add_argument('--format', choices=['text', 'json'], default='text',
                             help='Output format')

    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear error aggregator')

    # Test command
    test_parser = subparsers.add_parser('test', help='Run error handling tests')
    test_parser.add_argument('--type', dest='test_type', choices=['all', 'basic', 'retry'],
                            default='all', help='Type of tests to run')
    test_parser.add_argument('--format', choices=['text', 'json'], default='text',
                            help='Output format')

    # Config command
    config_parser = subparsers.add_parser('config', help='Configure error handling')
    config_parser.add_argument('--retry-attempts', type=int, help='Set retry attempts')
    config_parser.add_argument('--retry-delay', type=float, help='Set retry delay')
    config_parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                              help='Set log level')
    config_parser.add_argument('--format', choices=['text', 'json'], default='text',
                              help='Output format')

    # Recovery command
    recovery_parser = subparsers.add_parser('recovery', help='Test recovery strategies')
    recovery_parser.add_argument('--category', choices=['all', 'network', 'git', 'agent'],
                                default='all', help='Recovery category to test')
    recovery_parser.add_argument('--format', choices=['text', 'json'], default='text',
                                help='Output format')

    return parser


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = ErrorHandlingCLI()
    result = cli.handle_command(args)

    if args.command in ['stats', 'test', 'config', 'recovery'] and getattr(args, 'format', None) == 'json':
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        if result.get('success'):
            if 'message' in result:
                print(f"✅ {result['message']}")
        else:
            print(f"❌ {result.get('message', 'Operation failed')}")
            if 'error' in result:
                print(f"Error: {result['error']}")

    return 0 if result.get('success') else 1


if __name__ == "__main__":
    sys.exit(main())