#!/usr/bin/env python3
"""
Basic tests for Code Quality Checker.

测试覆盖：
- 基本功能测试
- 命名规范检查
- 复杂度检测
- 报告生成
"""

import sys
import os
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import CodeQualityChecker


class TestCodeQualityChecker:
    """Test suite for CodeQualityChecker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = CodeQualityChecker()

    def test_default_config(self):
        """Test default configuration is loaded."""
        assert self.checker.config is not None
        assert 'complexity' in self.checker.config
        assert 'naming' in self.checker.config

    def test_is_snake_case_valid(self):
        """Test snake_case validation - valid names."""
        assert self.checker._is_snake_case('calculate_average')
        assert self.checker._is_snake_case('process_data')
        assert self.checker._is_snake_case('get_user_info')

    def test_is_snake_case_invalid(self):
        """Test snake_case validation - invalid names."""
        assert not self.checker._is_snake_case('CalculateSum')
        assert not self.checker._is_snake_case('BadFunctionName')
        assert not self.checker._is_snake_case('processData')

    def test_to_snake_case(self):
        """Test conversion to snake_case."""
        assert self.checker._to_snake_case('CalculateSum') == 'calculate_sum'
        assert self.checker._to_snake_case('BadFunctionName') == 'bad_function_name'
        assert self.checker._to_snake_case('getUserInfo') == 'get_user_info'

    def test_check_file_not_found(self):
        """Test error handling for non-existent file."""
        result = self.checker.check_file('nonexistent.py')
        assert 'error' in result
        assert 'not found' in result['error'].lower()

    def test_check_file_unsupported_type(self):
        """Test error handling for unsupported file type."""
        # Create a temporary .txt file
        test_file = '/tmp/test_unsupported.txt'
        with open(test_file, 'w') as f:
            f.write('test content')

        result = self.checker.check_file(test_file)
        assert 'error' in result
        assert 'unsupported' in result['error'].lower()

        # Cleanup
        os.remove(test_file)

    def test_check_python_file(self):
        """Test checking a Python file."""
        # Create a temporary test file
        test_file = '/tmp/test_quality.py'
        with open(test_file, 'w') as f:
            f.write('''def BadName():
    pass

def good_function():
    # This is a very long function that should trigger complexity warning
    line1 = 1
    line2 = 2
    # ... (imagine many more lines)
''')

        result = self.checker.check_file(test_file)

        assert result['language'] == 'python'
        assert result['issue_count'] >= 1  # At least the naming issue
        assert any(i['type'] == 'naming_violation' for i in result['issues'])

        # Cleanup
        os.remove(test_file)

    def test_generate_json_report(self):
        """Test JSON report generation."""
        results = [{
            'filepath': 'test.py',
            'language': 'python',
            'total_lines': 10,
            'issues': [
                {
                    'type': 'naming_violation',
                    'severity': 'warning',
                    'line': 1,
                    'message': 'Bad naming'
                }
            ],
            'issue_count': 1
        }]

        report = self.checker.generate_json_report(results)

        assert '"version"' in report
        assert '"summary"' in report
        assert '"total_files": 1' in report

    def test_generate_markdown_report(self):
        """Test Markdown report generation."""
        results = [{
            'filepath': 'test.py',
            'language': 'python',
            'total_lines': 10,
            'issues': [],
            'issue_count': 0
        }]

        report = self.checker.generate_markdown_report(results)

        assert '# Code Quality Report' in report
        assert '## Summary' in report
        assert 'test.py' in report
        assert '✅ No issues found!' in report


def test_example_file():
    """Integration test: Check the example file."""
    checker = CodeQualityChecker()

    example_file = os.path.join(
        os.path.dirname(__file__),
        '..',
        'examples',
        'sample_code.py'
    )

    if os.path.exists(example_file):
        result = checker.check_file(example_file)

        # The example file has intentional issues
        assert result['issue_count'] > 0
        assert result['language'] == 'python'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
