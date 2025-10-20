# Testing Guide - Claude Enhancer Code Quality Checker

This directory contains the comprehensive test suite for the Code Quality Checker CLI tool.

## Directory Structure

```
tests/
├── README.md                      # This file
├── conftest.py                    # Global fixtures and configuration
├── pytest.ini                     # Pytest configuration (see root pytest.ini)
├── requirements.txt               # Test dependencies
│
├── unit/                          # Unit tests (isolated components)
├── integration/                   # Integration tests (component interactions)
├── e2e/                          # End-to-end tests (full scenarios)
├── performance/                   # Performance tests
│
├── fixtures/                      # Test data and samples
│   ├── valid/                     # Valid configuration samples
│   ├── invalid/                   # Invalid configurations
│   ├── edge_cases/                # Edge case scenarios
│   └── sample_projects/           # Complete test projects
│
└── reports/                       # Test execution reports
    ├── coverage/                  # Coverage reports
    ├── junit/                     # JUnit XML reports
    └── performance/               # Performance metrics
```

## Quick Start

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit -v

# Integration tests only
pytest tests/integration -v

# E2E tests only
pytest tests/e2e -v

# Performance tests
pytest tests/performance -v --benchmark-only
```

### Run with Coverage
```bash
# Generate coverage report
pytest --cov --cov-report=html

# View HTML report
open tests/reports/coverage/html/index.html
```

### Run Specific Tests
```bash
# Run specific test file
pytest tests/unit/test_complexity_calculator.py

# Run specific test function
pytest tests/unit/test_complexity_calculator.py::TestComplexityCalculator::test_simple_function_complexity

# Run tests matching pattern
pytest -k "complexity"
```

## Test Markers

Use markers to categorize and filter tests:

```bash
# Run only unit tests
pytest -m unit

# Run only slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"

# Run critical tests only
pytest -m "unit and critical"
```

Available markers:
- `unit`: Unit tests
- `integration`: Integration tests
- `e2e`: End-to-end tests
- `performance`: Performance tests
- `slow`: Slow tests (>5s)
- `smoke`: Smoke tests (critical paths)
- `core`: Core layer tests
- `feature`: Feature layer tests
- `module`: Module layer tests

## Coverage Targets

| Component | Target | Priority |
|-----------|--------|----------|
| Core parsers | ≥90% | Critical |
| Analyzers | ≥85% | High |
| Validators | ≥80% | Medium |
| Hook integration | ≥75% | Medium |
| Utility scripts | ≥70% | Low |
| **Overall** | **≥80%** | **Critical** |

## Writing Tests

### Test Structure (AAA Pattern)

```python
def test_example():
    # Arrange - Set up test data and preconditions
    calculator = ComplexityCalculator()
    code = "def simple(): return 1"

    # Act - Execute the function under test
    result = calculator.calculate(code)

    # Assert - Verify the expected outcome
    assert result == 1
```

### Using Fixtures

```python
def test_with_fixture(valid_phase_definitions):
    # Fixtures are automatically available
    assert "phases" in valid_phase_definitions
    assert len(valid_phase_definitions["phases"]) == 6
```

### Parametric Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("simple_function", True),
    ("BadFunctionName", False),
    ("_private_method", True),
])
def test_naming(input, expected):
    result = validate_name(input)
    assert result == expected
```

## CI/CD Integration

Tests are automatically run on:
- Push to main branch
- Pull requests
- Pre-commit hooks (unit tests only)

See `.github/workflows/test-quality-checker.yml` for details.

## Debugging Tests

```bash
# Verbose output
pytest -vv

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb

# Print output even for passing tests
pytest -s

# Stop at first failure
pytest -x
```

## Performance Testing

```bash
# Run performance benchmarks
pytest tests/performance --benchmark-only

# Save benchmark results
pytest tests/performance --benchmark-save=baseline

# Compare with baseline
pytest tests/performance --benchmark-compare=baseline
```

## Test Maintenance

### Before Committing
- [ ] All tests pass locally
- [ ] Coverage meets threshold (≥80%)
- [ ] No new warnings introduced
- [ ] Test names are descriptive
- [ ] Documentation is updated

### Adding New Tests
1. Identify the component to test
2. Choose appropriate test category (unit/integration/e2e)
3. Write test following AAA pattern
4. Verify test fails first (TDD)
5. Implement feature
6. Verify test passes
7. Check coverage impact

## References

- [Testing Strategy Document](.temp/analysis/testing_strategy_2025-10-19.md)
- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

**Last Updated**: 2025-10-19
**Maintained by**: test-engineer
