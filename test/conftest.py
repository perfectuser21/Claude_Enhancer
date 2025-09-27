#!/usr/bin/env python3
"""
Claude Enhancer Plus - Pytest Configuration
Optimized fixtures and utilities for fast test execution
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Generator
import json
import os


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Optimized test configuration for fast execution"""
    return {
        "max_execution_time": 10.0,
        "target_coverage": 0.8,
        "parallel_workers": 4,
        "memory_limit_mb": 500.0,
        "cache_enabled": True,
        "mock_external_services": True,
        "fast_mode": True,
    }


@pytest.fixture(scope="session")
def temp_project_dir():
    """Create temporary project directory for testing"""
    temp_dir = tempfile.mkdtemp(prefix="claude_enhancer_test_")
    project_path = Path(temp_dir)

    # Create basic project structure
    (project_path / "src").mkdir(exist_ok=True)
    (project_path / "test").mkdir(exist_ok=True)
    (project_path / ".claude").mkdir(exist_ok=True)
    (project_path / ".claude" / "hooks").mkdir(exist_ok=True)

    # Create mock configuration files
    mock_settings = {
        "version": "2.0",
        "hooks_enabled": True,
        "performance_mode": True,
        "max_workers": 6,
    }

    with open(project_path / ".claude" / "settings.json", "w") as f:
        json.dump(mock_settings, f)

    yield project_path

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_claude_enhancer():
    """Comprehensive mock for Claude Enhancer system"""
    mock = MagicMock()

    # Mock core components
    mock.phase_manager = MagicMock()
    mock.phase_manager.phases = list(range(8))
    mock.phase_manager.current_phase = 0
    mock.phase_manager.next_phase = MagicMock(return_value=True)
    mock.phase_manager.validate_transition = MagicMock(return_value=True)

    mock.validation_engine = MagicMock()
    mock.validation_engine.validate_agents = MagicMock(return_value=True)
    mock.validation_engine.validate_parallel_execution = MagicMock(return_value=True)

    mock.file_operations = MagicMock()
    mock.file_operations.read_config = MagicMock(return_value={"test": True})
    mock.file_operations.write_config = MagicMock(return_value=True)
    mock.file_operations.backup_files = MagicMock(return_value=True)

    mock.cache_manager = MagicMock()
    mock.cache_manager.get = MagicMock(return_value=None)
    mock.cache_manager.set = MagicMock(return_value=True)
    mock.cache_manager.clear = MagicMock(return_value=True)

    mock.agent_selector = MagicMock()
    mock.agent_selector.select_agents = MagicMock(
        return_value=["agent1", "agent2", "agent3", "agent4"]
    )

    return mock


@pytest.fixture
def mock_performance_monitor():
    """Mock performance monitoring for fast tests"""
    monitor = MagicMock()
    monitor.start_time = 0.0
    monitor.peak_memory = 100.0
    monitor.cpu_usage = 25.0

    # Mock context manager
    monitor.__enter__ = MagicMock(return_value=monitor)
    monitor.__exit__ = MagicMock(return_value=False)

    return monitor


@pytest.fixture
def sample_test_data():
    """Sample test data for various test scenarios"""
    return {
        "agents": {
            "simple_task": [
                "backend-architect",
                "test-engineer",
                "api-designer",
                "technical-writer",
            ],
            "standard_task": [
                "backend-architect",
                "security-auditor",
                "test-engineer",
                "api-designer",
                "database-specialist",
                "performance-engineer",
            ],
            "complex_task": [
                "backend-architect",
                "security-auditor",
                "test-engineer",
                "api-designer",
                "database-specialist",
                "performance-engineer",
                "devops-specialist",
                "frontend-architect",
            ],
        },
        "phases": [
            {"id": 0, "name": "Branch Creation", "duration": 0.1},
            {"id": 1, "name": "Analysis", "duration": 0.5},
            {"id": 2, "name": "Design", "duration": 1.0},
            {"id": 3, "name": "Implementation", "duration": 2.0},
            {"id": 4, "name": "Testing", "duration": 1.5},
            {"id": 5, "name": "Commit", "duration": 0.3},
            {"id": 6, "name": "Review", "duration": 0.8},
            {"id": 7, "name": "Deploy", "duration": 0.2},
        ],
        "performance_benchmarks": {
            "max_execution_time": 10.0,
            "memory_limit_mb": 500.0,
            "cpu_usage_limit": 80.0,
            "parallel_efficiency": 0.85,
        },
    }


@pytest.fixture
def fast_mock_environment(temp_project_dir, mock_claude_enhancer):
    """Complete fast mock environment for testing"""
    environment = {
        "project_dir": temp_project_dir,
        "claude_enhancer": mock_claude_enhancer,
        "settings": {
            "fast_mode": True,
            "mock_external_calls": True,
            "parallel_enabled": True,
            "cache_enabled": True,
        },
    }
    return environment


@pytest.fixture(autouse=True)
def optimize_test_environment():
    """Auto-optimize test environment for speed"""
    # Disable slow operations
    os.environ["CLAUDE_ENHANCER_FAST_MODE"] = "1"
    os.environ["CLAUDE_ENHANCER_MOCK_EXTERNAL"] = "1"
    os.environ["PYTEST_CURRENT_TEST"] = "1"

    yield

    # Cleanup environment
    os.environ.pop("CLAUDE_ENHANCER_FAST_MODE", None)
    os.environ.pop("CLAUDE_ENHANCER_MOCK_EXTERNAL", None)
    os.environ.pop("PYTEST_CURRENT_TEST", None)


def pytest_configure(config):
    """Configure pytest for optimal performance"""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests (fast execution)")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance benchmarks")
    config.addinivalue_line("markers", "critical: Critical path tests")
    config.addinivalue_line("markers", "parallel: Parallel execution tests")
    config.addinivalue_line("markers", "async: Asynchronous tests")


def pytest_collection_modifyitems(config, items):
    """Optimize test collection and execution order"""
    # Prioritize fast tests
    unit_tests = []
    integration_tests = []
    performance_tests = []
    other_tests = []

    for item in items:
        if "unit" in item.keywords:
            unit_tests.append(item)
        elif "integration" in item.keywords:
            integration_tests.append(item)
        elif "performance" in item.keywords:
            performance_tests.append(item)
        else:
            other_tests.append(item)

    # Reorder: unit tests first (fastest), then others
    items[:] = unit_tests + other_tests + integration_tests + performance_tests

    # Add fast execution marker to appropriate tests
    for item in items:
        if not any(
            marker.name in ["performance", "integration"]
            for marker in item.iter_markers()
        ):
            item.add_marker(pytest.mark.fast)


@pytest.fixture
def performance_benchmark():
    """Benchmark utilities for performance testing"""
    import time
    import psutil

    class PerformanceBenchmark:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.process = psutil.Process()

        def start(self):
            self.start_time = time.perf_counter()
            self.start_memory = self.process.memory_info().rss / 1024 / 1024

        def stop(self):
            if self.start_time is None:
                return None

            end_time = time.perf_counter()
            end_memory = self.process.memory_info().rss / 1024 / 1024

            return {
                "duration": end_time - self.start_time,
                "memory_delta": end_memory - self.start_memory,
                "peak_memory": end_memory,
            }

    return PerformanceBenchmark()


# Async test utilities
@pytest.fixture
async def async_mock_claude_enhancer():
    """Async version of Claude Enhancer mock"""
    mock = MagicMock()

    async def mock_async_operation(*args, **kwargs):
        await asyncio.sleep(0.01)  # Minimal async delay
        return {"success": True, "data": "mock_result"}

    mock.async_execute = mock_async_operation
    mock.async_validate = mock_async_operation
    mock.async_optimize = mock_async_operation

    return mock


@pytest.mark.asyncio
async def async_test_helper(coroutine_func, *args, **kwargs):
    """Helper for async test execution"""
    try:
        result = await asyncio.wait_for(coroutine_func(*args, **kwargs), timeout=5.0)
        return result
    except asyncio.TimeoutError:
        pytest.fail("Async test timed out")
    except Exception as e:
        pytest.fail(f"Async test failed: {e}")


# Performance assertion helpers
def assert_execution_time(func, max_time=1.0):
    """Assert function executes within time limit"""
    import time

    start = time.perf_counter()
    result = func()
    duration = time.perf_counter() - start
    assert (
        duration <= max_time
    ), f"Execution took {duration:.3f}s, expected <= {max_time}s"
    return result


def assert_memory_usage(func, max_memory_mb=100.0):
    """Assert function memory usage within limit"""
    import psutil

    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024

    result = func()

    final_memory = process.memory_info().rss / 1024 / 1024
    memory_used = final_memory - initial_memory

    assert (
        memory_used <= max_memory_mb
    ), f"Memory usage {memory_used:.1f}MB exceeded limit {max_memory_mb}MB"
    return result
