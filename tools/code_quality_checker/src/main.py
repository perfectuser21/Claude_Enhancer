#!/usr/bin/env python3
"""
Code Quality Checker - Main Entry Point

Analyzes Python and Shell scripts for code quality issues including:
- Function complexity (line count, nesting depth)
- Naming convention violations
- Generates reports in JSON and Markdown formats
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import json


class CodeQualityChecker:
    """Main orchestrator for code quality checking."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the checker with optional configuration.

        Args:
            config: Quality rules configuration
        """
        self.config = config or self._default_config()
        self.issues = []

    def _default_config(self) -> Dict[str, Any]:
        """Return default quality rules."""
        return {
            'complexity': {
                'max_function_lines': 50,
                'max_nesting_depth': 3,
                'warn_function_lines': 30,
                'warn_nesting_depth': 2
            },
            'naming': {
                'python': {
                    'function': 'snake_case',
                    'class': 'PascalCase',
                    'constant': 'UPPER_CASE'
                },
                'shell': {
                    'function': 'snake_case',
                    'variable': 'snake_case_or_UPPER'
                }
            }
        }

    def check_file(self, filepath: str) -> Dict[str, Any]:
        """
        Check a single file for quality issues.

        Args:
            filepath: Path to the file to check

        Returns:
            Dictionary containing check results
        """
        path = Path(filepath)

        if not path.exists():
            return {'error': f'File not found: {filepath}'}

        if path.suffix == '.py':
            return self._check_python_file(filepath)
        elif path.suffix == '.sh':
            return self._check_shell_file(filepath)
        else:
            return {'error': f'Unsupported file type: {path.suffix}'}

    def _check_python_file(self, filepath: str) -> Dict[str, Any]:
        """Check Python file for quality issues."""
        issues = []

        with open(filepath, 'r') as f:
            lines = f.readlines()

        # Check function complexity
        in_function = False
        function_name = None
        function_start = 0
        function_lines = 0
        nesting_depth = 0
        max_depth = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Detect function definition
            if stripped.startswith('def '):
                if in_function:
                    # Previous function ended
                    issues.extend(self._check_function_metrics(
                        function_name, function_start, i-1,
                        function_lines, max_depth
                    ))

                # New function starts
                function_name = stripped.split('(')[0].replace('def ', '')
                function_start = i
                function_lines = 1
                in_function = True
                nesting_depth = 1
                max_depth = 1

                # Check naming convention
                if not self._is_snake_case(function_name):
                    issues.append({
                        'type': 'naming_violation',
                        'severity': 'warning',
                        'line': i,
                        'message': f'Function "{function_name}" should use snake_case',
                        'suggestion': self._to_snake_case(function_name)
                    })

            elif in_function:
                function_lines += 1

                # Track nesting depth
                if any(stripped.startswith(kw) for kw in ['if ', 'for ', 'while ', 'with ', 'try:']):
                    nesting_depth += 1
                    max_depth = max(max_depth, nesting_depth)

                # Dedent
                if stripped in ['return', 'break', 'continue'] or (stripped == '' and nesting_depth > 1):
                    nesting_depth = max(1, nesting_depth - 1)

        # Check last function
        if in_function:
            issues.extend(self._check_function_metrics(
                function_name, function_start, len(lines),
                function_lines, max_depth
            ))

        return {
            'filepath': filepath,
            'language': 'python',
            'total_lines': len(lines),
            'issues': issues,
            'issue_count': len(issues)
        }

    def _check_shell_file(self, filepath: str) -> Dict[str, Any]:
        """Check Shell file for quality issues."""
        issues = []

        with open(filepath, 'r') as f:
            lines = f.readlines()

        # Simple shell function detection
        in_function = False
        function_name = None
        function_start = 0
        function_lines = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Detect function: function_name() { or function function_name {
            if '()' in stripped and '{' in stripped:
                if in_function:
                    # Previous function ended
                    if function_lines > self.config['complexity']['max_function_lines']:
                        issues.append({
                            'type': 'complexity_high',
                            'severity': 'error',
                            'line': function_start,
                            'message': f'Function "{function_name}" has {function_lines} lines (max: {self.config["complexity"]["max_function_lines"]})'
                        })

                # New function
                function_name = stripped.split('()')[0].strip()
                function_start = i
                function_lines = 1
                in_function = True

                # Check naming
                if not self._is_snake_case(function_name):
                    issues.append({
                        'type': 'naming_violation',
                        'severity': 'warning',
                        'line': i,
                        'message': f'Function "{function_name}" should use snake_case'
                    })

            elif in_function:
                function_lines += 1
                if stripped == '}':
                    in_function = False

        return {
            'filepath': filepath,
            'language': 'shell',
            'total_lines': len(lines),
            'issues': issues,
            'issue_count': len(issues)
        }

    def _check_function_metrics(self, name: str, start: int, end: int,
                                lines: int, depth: int) -> List[Dict]:
        """Check function complexity metrics."""
        issues = []

        # Check line count
        if lines > self.config['complexity']['max_function_lines']:
            issues.append({
                'type': 'complexity_high',
                'severity': 'error',
                'line': start,
                'message': f'Function "{name}" has {lines} lines (max: {self.config["complexity"]["max_function_lines"]})'
            })
        elif lines > self.config['complexity']['warn_function_lines']:
            issues.append({
                'type': 'complexity_medium',
                'severity': 'warning',
                'line': start,
                'message': f'Function "{name}" has {lines} lines (recommended max: {self.config["complexity"]["warn_function_lines"]})'
            })

        # Check nesting depth
        if depth > self.config['complexity']['max_nesting_depth']:
            issues.append({
                'type': 'nesting_deep',
                'severity': 'error',
                'line': start,
                'message': f'Function "{name}" has nesting depth {depth} (max: {self.config["complexity"]["max_nesting_depth"]})'
            })

        return issues

    @staticmethod
    def _is_snake_case(name: str) -> bool:
        """Check if name follows snake_case convention."""
        return name.islower() and '_' in name or name.islower()

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Convert name to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def generate_json_report(self, results: List[Dict]) -> str:
        """Generate JSON format report."""
        report = {
            'version': '1.0.0',
            'summary': {
                'total_files': len(results),
                'total_issues': sum(r['issue_count'] for r in results),
                'errors': sum(1 for r in results for i in r['issues'] if i['severity'] == 'error'),
                'warnings': sum(1 for r in results for i in r['issues'] if i['severity'] == 'warning')
            },
            'files': results
        }

        return json.dumps(report, indent=2)

    def generate_markdown_report(self, results: List[Dict]) -> str:
        """Generate Markdown format report."""
        total_issues = sum(r['issue_count'] for r in results)
        errors = sum(1 for r in results for i in r['issues'] if i['severity'] == 'error')
        warnings = sum(1 for r in results for i in r['issues'] if i['severity'] == 'warning')

        md = f"""# Code Quality Report

## Summary

- **Total Files**: {len(results)}
- **Total Issues**: {total_issues}
- **Errors**: {errors}
- **Warnings**: {warnings}

---

## Detailed Results

"""

        for result in results:
            md += f"### {result['filepath']}\n\n"
            md += f"- Language: {result['language']}\n"
            md += f"- Total Lines: {result['total_lines']}\n"
            md += f"- Issues Found: {result['issue_count']}\n\n"

            if result['issues']:
                md += "**Issues**:\n\n"
                for issue in result['issues']:
                    severity_icon = '🔴' if issue['severity'] == 'error' else '⚠️'
                    md += f"{severity_icon} **Line {issue['line']}**: {issue['message']}\n"
                md += "\n"
            else:
                md += "✅ No issues found!\n\n"

            md += "---\n\n"

        return md


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Code Quality Checker - Analyze Python and Shell scripts'
    )
    parser.add_argument(
        'files',
        nargs='+',
        help='Files or directories to check'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'markdown', 'both'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    parser.add_argument(
        '--output',
        help='Output file path (default: stdout)'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='Code Quality Checker 1.0.0'
    )

    args = parser.parse_args()

    # Initialize checker
    checker = CodeQualityChecker()

    # Collect files to check
    files_to_check = []
    for path_str in args.files:
        path = Path(path_str)
        if path.is_file():
            if path.suffix in ['.py', '.sh']:
                files_to_check.append(str(path))
        elif path.is_dir():
            files_to_check.extend([str(f) for f in path.rglob('*.py')])
            files_to_check.extend([str(f) for f in path.rglob('*.sh')])

    if not files_to_check:
        print("Error: No Python or Shell files found", file=sys.stderr)
        return 1

    # Check all files
    results = []
    for filepath in files_to_check:
        print(f"Checking {filepath}...", file=sys.stderr)
        result = checker.check_file(filepath)
        results.append(result)

    # Generate report
    if args.format == 'json' or args.format == 'both':
        report = checker.generate_json_report(results)
        if args.output:
            with open(args.output if args.format == 'json' else args.output + '.json', 'w') as f:
                f.write(report)
        else:
            print(report)

    if args.format == 'markdown' or args.format == 'both':
        report = checker.generate_markdown_report(results)
        if args.output:
            with open(args.output if args.format == 'markdown' else args.output + '.md', 'w') as f:
                f.write(report)
        else:
            print(report)

    # Return exit code based on errors
    error_count = sum(1 for r in results for i in r['issues'] if i['severity'] == 'error')
    return 1 if error_count > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
