#!/usr/bin/env python3
"""
Quality Checker: Programmatic validation before file writes
Part of Claude Enhancer 6.0 - AI Self-Validation System

This module provides Python-based quality checks that can be
integrated into AI workflows for pre-write validation.
"""

import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Represents the result of a validation check"""
    passed: bool
    message: str
    duration_ms: float
    details: Optional[str] = None


class QualityChecker:
    """Main quality checker class"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.min_coverage_threshold = 80.0
        self.validation_results: List[ValidationResult] = []

    def validate_before_write(
        self, file_path: str, content: str
    ) -> Tuple[bool, List[ValidationResult]]:
        """
        Main validation entry point

        Args:
            file_path: Path to the file being written
            content: Content to be written

        Returns:
            Tuple of (success: bool, results: List[ValidationResult])
        """
        print(f"🔍 Pre-write validation: {file_path}")

        self.validation_results = []

        # Run all validations
        checks = [
            ("Syntax", self.check_syntax),
            ("Security", self.check_security),
            ("Test Existence", self.check_test_exists),
            ("Code Quality", self.check_code_quality),
        ]

        overall_success = True

        for check_name, check_func in checks:
            start = time.time()
            try:
                result = check_func(file_path, content)
                duration = (time.time() - start) * 1000

                if result is True:
                    vr = ValidationResult(True, f"{check_name} passed", duration)
                    print(f"  ✅ {check_name}: PASSED ({duration:.0f}ms)")
                elif isinstance(result, tuple):
                    passed, msg = result
                    vr = ValidationResult(passed, msg, duration)
                    if passed:
                        print(f"  ✅ {check_name}: PASSED ({duration:.0f}ms)")
                    else:
                        print(f"  ❌ {check_name}: FAILED - {msg}")
                        overall_success = False
                else:
                    vr = ValidationResult(False, f"{check_name} failed", duration)
                    print(f"  ❌ {check_name}: FAILED ({duration:.0f}ms)")
                    overall_success = False

                self.validation_results.append(vr)

            except Exception as e:
                duration = (time.time() - start) * 1000
                vr = ValidationResult(False, f"{check_name} error: {str(e)}", duration)
                self.validation_results.append(vr)
                print(f"  ⚠️  {check_name}: ERROR - {str(e)}")

        return overall_success, self.validation_results

    def check_syntax(self, file_path: str, content: str) -> Tuple[bool, str]:
        """Validate syntax by file type"""

        if file_path.endswith('.sh'):
            return self._check_shell_syntax(content)
        elif file_path.endswith('.py'):
            return self._check_python_syntax(file_path, content)
        elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
            return self._check_javascript_syntax(file_path, content)
        else:
            return True, "No syntax check for this file type"

    def _check_shell_syntax(self, content: str) -> Tuple[bool, str]:
        """Check shell script syntax"""
        try:
            pass  # Auto-fixed empty block
            # First try shellcheck if available
            if self._command_exists('shellcheck'):
                result = subprocess.run(
                    ['shellcheck', '-'],
                    input=content.encode(),
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 0:
                    error_msg = result.stdout.decode() or result.stderr.decode()
                    return False, f"Shellcheck errors:\n{error_msg[:200]}"

            # Fallback to bash -n
            result = subprocess.run(
                ['bash', '-n'],
                input=content.encode(),
                capture_output=True,
                timeout=5
            )

            if result.returncode == 0:
                return True, "Shell syntax valid"
            else:
                error_msg = result.stderr.decode()
                return False, f"Bash syntax error: {error_msg[:200]}"

        except subprocess.TimeoutExpired:
            return False, "Syntax check timed out"
        except Exception as e:
            return False, f"Syntax check error: {str(e)}"

    def _check_python_syntax(self, file_path: str, content: str) -> Tuple[bool, str]:
        """Check Python syntax"""
        try:
            pass  # Auto-fixed empty block
            # Compile check
            compile(content, file_path, 'exec')

            # Pylint check (if available)
            if self._command_exists('pylint'):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(content)
                    temp_path = f.name

                try:
                    result = subprocess.run(
                        ['pylint', '--disable=all', '--enable=E,F',
                         '--score=no', temp_path],
                        capture_output=True,
                        timeout=10
                    )

                    if result.returncode != 0:
                        errors = result.stdout.decode()
                        if errors.strip():
                            return False, f"Pylint errors:\n{errors[:200]}"
                finally:
                    os.unlink(temp_path)

            return True, "Python syntax valid"

        except SyntaxError as e:
            return False, f"Python syntax error: Line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"Python validation error: {str(e)}"

    def _check_javascript_syntax(self, file_path: str, content: str) -> Tuple[bool, str]:
        """Check JavaScript/TypeScript syntax"""
        try:
            if self._command_exists('node'):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                    f.write(content)
                    temp_path = f.name

                try:
                    result = subprocess.run(
                        ['node', '--check', temp_path],
                        capture_output=True,
                        timeout=5
                    )

                    if result.returncode == 0:
                        return True, "JavaScript syntax valid"
                    else:
                        error_msg = result.stderr.decode()
                        return False, f"JavaScript syntax error: {error_msg[:200]}"
                finally:
                    os.unlink(temp_path)

            return True, "No JavaScript validator available (skipped)"

        except Exception as e:
            return False, f"JavaScript validation error: {str(e)}"

    def check_security(self, file_path: str, content: str) -> Tuple[bool, str]:
        """Check for security issues"""
        issues = []

        # Check for hardcoded secrets
        secret_patterns = [
            r'(?i)(password|secret|api[_-]?key|token)\s*[=:]\s*["\'][^"\'\s]{8,}',
            r'(?i)aws_access_key_id\s*[=:]',
            r'(?i)private[_-]?key\s*[=:]\s*["\']',
        ]

        for pattern in secret_patterns:
            if re.search(pattern, content):
                issues.append("Potential hardcoded secret detected")
                break

        # Check for SQL injection patterns
        if re.search(r'execute\s*\([^)]*\+[^)]*\)|query\s*\([^)]*\+[^)]*\)', content):
            issues.append("Potential SQL injection vulnerability (string concatenation)")

        # Check for dangerous functions
        dangerous_funcs = [
            (r'\beval\s*\(', 'eval()'),
            (r'\bexec\s*\(', 'exec()'),
            (r'os\.system\s*\(', 'os.system()'),
            (r'subprocess\.shell\s*=\s*True', 'subprocess shell=True'),
        ]

        for pattern, func_name in dangerous_funcs:
            if re.search(pattern, content):
                issues.append(f"Dangerous function usage: {func_name}")

        if issues:
            return False, "Security issues found:\n  - " + "\n  - ".join(issues)

        return True, "No security issues detected"

    def check_test_exists(self, file_path: str, content: str = None) -> Tuple[bool, str]:
        """Verify test file exists for source files"""

        if not self._is_source_file(file_path):
            return True, "Not a source file (test not required)"

        test_file = self._infer_test_file(file_path)

        if test_file.exists():
            return True, f"Test file exists: {test_file}"

        return False, f"Missing test file: {test_file}\nCreate test first or use .temp/ for prototypes"

    def check_code_quality(self, file_path: str, content: str) -> Tuple[bool, str]:
        """Check general code quality metrics"""

        # Check file size
        line_count = content.count('\n')
        if line_count > 500:
            return False, f"File too large: {line_count} lines (max 500)"

        # Check for very long lines
        max_line_length = 120
        for i, line in enumerate(content.split('\n'), 1):
            if len(line) > max_line_length:
                return False, f"Line {i} too long: {len(line)} chars (max {max_line_length})"

        # Check for TODO/FIXME without context
        if re.search(r'(TODO|FIXME):\s*$', content, re.MULTILINE):
            return False, "Empty TODO/FIXME found (add description)"

        return True, "Code quality checks passed"

    def _is_source_file(self, file_path: str) -> bool:
        """Check if file is a source file requiring tests"""
        path = Path(file_path)

        # Check extension
        source_exts = {'.js', '.ts', '.jsx', '.tsx', '.py', '.go', '.rs'}
        if path.suffix not in source_exts:
            return False

        # Exclude test files
        if any(pattern in path.name for pattern in ['.test.', '.spec.', '_test.']):
            return False

        # Exclude temp files
        if '.temp' in path.parts:
            return False

        return True

    def _infer_test_file(self, source_file: str) -> Path:
        """Infer the expected test file location"""
        path = Path(source_file)

        # Try multiple patterns
        patterns = [
            path.with_name(f"{path.stem}.test{path.suffix}"),
            path.with_name(f"{path.stem}.spec{path.suffix}"),
            path.parent / '__tests__' / f"{path.stem}.test{path.suffix}",
            Path('test') / path.relative_to(self.project_root) if path.is_relative_to(self.project_root) else None,
            Path('tests') / path.relative_to(self.project_root) if path.is_relative_to(self.project_root) else None,
        ]

        for pattern in patterns:
            if pattern and pattern.exists():
                return pattern

        # Return first pattern as suggestion
        return patterns[0]

    @staticmethod
    def _command_exists(command: str) -> bool:
        """Check if a command exists in PATH"""
        return subprocess.run(
            ['which', command],
            capture_output=True
        ).returncode == 0


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: quality_checker.py <file_path>", file=sys.stderr)
        print("Content should be provided via stdin", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    content = sys.stdin.read()

    checker = QualityChecker('.')
    success, results = checker.validate_before_write(file_path, content)

    # Print summary
    print("\n" + "="*50)
    print(f"Validation: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"Total checks: {len(results)}")
    print(f"Total time: {sum(r.duration_ms for r in results):.0f}ms")
    print("="*50)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
