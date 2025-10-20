# tests/conftest.py
"""
Global test configuration and fixtures for Claude Enhancer Code Quality Checker.

This file provides:
- Shared fixtures for all tests
- Pytest configuration hooks
- Common test utilities
"""

import pytest
import yaml
import json
from pathlib import Path
import tempfile
import subprocess
import os

# ============================================================================
# Directory Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def fixtures_dir():
    """Get fixtures directory path."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture(scope="session")
def reports_dir():
    """Get test reports directory path."""
    reports = Path(__file__).parent / "reports"
    reports.mkdir(exist_ok=True)
    return reports

@pytest.fixture(scope="session")
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent

# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def valid_phase_definitions(fixtures_dir):
    """Load valid phase_definitions.yml."""
    path = fixtures_dir / "valid" / "phase_definitions.yml"
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f)
    return None

@pytest.fixture
def valid_workflow_rules(fixtures_dir):
    """Load valid workflow_rules.yml."""
    path = fixtures_dir / "valid" / "workflow_rules.yml"
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f)
    return None

@pytest.fixture
def valid_quality_thresholds(fixtures_dir):
    """Load valid quality_thresholds.yml."""
    path = fixtures_dir / "valid" / "quality_thresholds.yml"
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f)
    return None

@pytest.fixture
def valid_versions_json(fixtures_dir):
    """Load valid versions.json."""
    path = fixtures_dir / "valid" / "versions.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None

@pytest.fixture
def invalid_yaml_samples(fixtures_dir):
    """Load all invalid YAML samples."""
    invalid_dir = fixtures_dir / "invalid"
    if not invalid_dir.exists():
        return []

    samples = []
    for yaml_file in invalid_dir.glob("*.yml"):
        samples.append({
            "name": yaml_file.stem,
            "path": yaml_file,
            "content": yaml_file.read_text()
        })
    return samples

# ============================================================================
# Git Repository Fixtures
# ============================================================================

@pytest.fixture
def temp_git_repo():
    """Create temporary Git repository with basic configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Initialize Git
        subprocess.run(
            ["git", "init"],
            cwd=repo_path,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            capture_output=True
        )

        yield repo_path

@pytest.fixture
def git_repo_with_hooks(temp_git_repo, project_root):
    """Create Git repository with pre-commit hooks installed."""
    repo = temp_git_repo

    # Install hooks
    hooks_dir = repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Copy pre-commit hook if exists
    source_hook = project_root / ".git" / "hooks" / "pre-commit"
    if source_hook.exists():
        target_hook = hooks_dir / "pre-commit"
        target_hook.write_text(source_hook.read_text())
        target_hook.chmod(0o755)

    return repo

# ============================================================================
# Threshold Fixtures
# ============================================================================

@pytest.fixture
def quality_thresholds():
    """Quality thresholds configuration."""
    return {
        "complexity": {
            "max_cyclomatic": 10,
            "max_function_length": 50,
            "max_nesting_depth": 4,
            "max_parameters": 5
        },
        "coverage": {
            "min_line_coverage": 80,
            "min_branch_coverage": 75,
            "min_function_coverage": 85
        },
        "performance": {
            "max_hook_execution_time": 2.0,
            "max_test_execution_time": 300.0
        },
        "naming": {
            "enforce_snake_case": True,
            "enforce_pascal_case": True,
            "allow_single_char_vars": False
        }
    }

@pytest.fixture
def complexity_threshold(quality_thresholds):
    """Get complexity threshold."""
    return quality_thresholds["complexity"]["max_cyclomatic"]

@pytest.fixture
def coverage_threshold(quality_thresholds):
    """Get coverage threshold."""
    return quality_thresholds["coverage"]["min_line_coverage"]

# ============================================================================
# Sample Code Fixtures
# ============================================================================

@pytest.fixture
def sample_simple_function():
    """Simple function with low complexity."""
    return """
def calculate_sum(a, b):
    '''Calculate sum of two numbers.'''
    return a + b
"""

@pytest.fixture
def sample_complex_function():
    """Complex function exceeding threshold."""
    return """
def complex_logic(x, y, z, a, b):
    '''Overly complex function.'''
    if x > 0:
        if y > 0:
            if z > 0:
                if a > 0:
                    if b > 0:
                        return x + y + z + a + b
                    else:
                        return x + y + z + a
                else:
                    return x + y + z
            else:
                return x + y
        else:
            return x
    else:
        return 0
"""

@pytest.fixture
def sample_naming_violations():
    """Code with naming convention violations."""
    return """
def BadFunctionName():  # Should be snake_case
    pass

class snake_case_class:  # Should be PascalCase
    pass

MyVariable = 10  # Should be snake_case
constant_value = 20  # Should be UPPER_CASE
"""

# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture
def temp_workspace():
    """Create temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_python_file(temp_workspace):
    """Create sample Python file."""
    file_path = temp_workspace / "sample.py"
    file_path.write_text("""
def hello_world():
    '''Say hello.'''
    print("Hello, World!")
""")
    return file_path

@pytest.fixture
def sample_shell_file(temp_workspace):
    """Create sample shell script."""
    file_path = temp_workspace / "sample.sh"
    file_path.write_text("""#!/bin/bash
# Sample shell script

echo "Hello from shell"
""")
    file_path.chmod(0o755)
    return file_path

# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_subprocess_run(mocker):
    """Mock subprocess.run for testing."""
    return mocker.patch("subprocess.run")

@pytest.fixture
def mock_file_system(mocker):
    """Mock file system operations."""
    return mocker.patch("pathlib.Path.read_text")

# ============================================================================
# Pytest Configuration Hooks
# ============================================================================

def pytest_configure(config):
    """Pytest configuration hook - called before test collection."""
    # Create reports directories
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    (reports_dir / "coverage").mkdir(exist_ok=True)
    (reports_dir / "junit").mkdir(exist_ok=True)
    (reports_dir / "performance").mkdir(exist_ok=True)

    # Register custom markers
    config.addinivalue_line(
        "markers",
        "unit: Unit tests (isolated components)"
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests (component interactions)"
    )
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests (full workflows)"
    )
    config.addinivalue_line(
        "markers",
        "performance: Performance and benchmark tests"
    )
    config.addinivalue_line(
        "markers",
        "slow: Slow-running tests (>5 seconds)"
    )
    config.addinivalue_line(
        "markers",
        "smoke: Smoke tests (critical paths only)"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection - add markers, skip tests, etc."""
    for item in items:
        # Auto-mark slow tests
        if "slow" not in item.keywords:
            # Add slow marker to performance tests
            if "performance" in str(item.fspath):
                item.add_marker(pytest.mark.slow)

        # Auto-mark test categories based on directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)

# ============================================================================
# Helper Functions
# ============================================================================

def load_fixture_file(fixtures_dir, category, filename):
    """Load a fixture file from fixtures directory."""
    path = fixtures_dir / category / filename
    if not path.exists():
        return None

    if path.suffix in ['.yml', '.yaml']:
        with open(path) as f:
            return yaml.safe_load(f)
    elif path.suffix == '.json':
        with open(path) as f:
            return json.load(f)
    else:
        return path.read_text()

@pytest.fixture
def load_fixture(fixtures_dir):
    """Fixture factory for loading fixture files."""
    def _load(category, filename):
        return load_fixture_file(fixtures_dir, category, filename)
    return _load
