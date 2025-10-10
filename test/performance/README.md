# Performance Testing Suite

Comprehensive performance benchmarking and load testing for Claude Enhancer 5.0 CLI.

## Overview

This test suite validates the **75% performance improvement** claim and ensures the system meets all performance budgets defined in `metrics/perf_budget.yml`.

### Key Objectives

1. ✅ Validate 75% speed improvement (17.4s → 4.3s)
2. ✅ Verify 85%+ cache hit rate
3. ✅ Benchmark individual operations
4. ✅ Test scalability under load
5. ✅ Detect performance regressions
6. ✅ Profile memory usage

## Test Categories

### 1. Command Benchmarks (`benchmark_commands.sh`)

Measures performance of individual CLI commands:

- `ce status` - Display workflow status
- `ce validate` - Quality gate validation
- `ce start` - Branch creation
- `ce next` - Phase transition
- `ce publish` - PR creation
- `ce merge` - Branch merging
- `ce clean` - Cleanup operations

**Tool:** hyperfine (installed via apt)
**Metrics:** Mean time, min/max, standard deviation
**Budget Compliance:** Checks against `metrics/perf_budget.yml`

```bash
./test/performance/benchmark_commands.sh
```

### 2. Workflow Benchmarks (`benchmark_workflows.sh`)

Tests complete end-to-end workflows:

- **Complete Development Cycle**: start → validate → next → publish → merge
- **Multi-Terminal Workflow**: 3 concurrent terminals
- **Conflict Detection**: Cross-terminal file analysis
- **Cache Performance**: Cold vs warm cache
- **Large State**: Performance with 100+ sessions

**Target:** Complete cycle < 5s (was 17.4s)
**Metrics:** Total time, per-step time, throughput

```bash
./test/performance/benchmark_workflows.sh
```

### 3. Load Testing (`load_test.sh`)

Simulates heavy concurrent usage:

- **Concurrent Terminals**: 5, 10, 20 simultaneous operations
- **Rapid Commands**: 100, 1000 commands in quick succession
- **State Stress**: 100, 500, 1000 session files
- **Lock Contention**: Concurrent state access
- **Memory Pressure**: Large state with many operations

**Metrics:** Throughput, failure rate, system metrics (CPU, memory, load)

```bash
./test/performance/load_test.sh
```

### 4. Cache Performance (`cache_performance.sh`)

Validates caching effectiveness:

- **Cold vs Warm**: Performance comparison
- **Hit Rate Analysis**: Measure cache hit percentage
- **TTL Testing**: Cache invalidation behavior
- **Memory Efficiency**: Cache size and overhead
- **Concurrent Access**: Race condition testing
- **Category Performance**: Per-category analysis

**Target:** 85%+ cache hit rate
**TTL:** 5 minutes (300s)

```bash
./test/performance/cache_performance.sh
```

### 5. Stress Testing (`stress_test.sh`)

Pushes system to limits:

- **Maximum Concurrent Terminals**: Find breaking point (10, 20, 50, 100, 200)
- **Rapid Fire Commands**: 10,000 commands as fast as possible
- **Memory Exhaustion**: Create massive state (1000, 5000, 10000 sessions)
- **Cache Thrashing**: Rapid invalidation and rebuild
- **Disk I/O Saturation**: Heavy concurrent file operations

**Warning:** This test is resource-intensive and disabled by default.

```bash
./test/performance/stress_test.sh
```

### 6. Memory Profiling (`memory_profiling.sh`)

Analyzes memory consumption:

- **Command Memory Usage**: Peak and average RSS per command
- **Memory Leak Detection**: 100 iterations to detect leaks
- **Large State Impact**: Memory scaling with state size
- **Cache Memory**: Cache overhead analysis

**Tools:** `/usr/bin/time -v`, `ps`, `/proc` filesystem
**Budget:** 256MB per process (from `metrics/perf_budget.yml`)

```bash
./test/performance/memory_profiling.sh
```

### 7. Regression Detection (`regression_check.sh`)

Compares current performance against baseline:

- Loads baseline from `test/performance/baseline.json`
- Runs current benchmarks
- Calculates percentage change for each metric
- Flags regressions (> 10% slower)
- Updates baseline on improvements

**Threshold:** 10% degradation is considered a regression

```bash
./test/performance/regression_check.sh
```

## Quick Start

### Run Complete Test Suite

```bash
# Standard run (excludes stress tests)
bash test/run_performance_tests.sh

# Quick run (benchmarks and workflows only)
bash test/run_performance_tests.sh --quick

# Full run (includes stress tests)
bash test/run_performance_tests.sh --all
```

### Generate Performance Report

```bash
bash test/generate_perf_report.sh
```

This creates `test/PERFORMANCE_TEST_SUMMARY.md` with:
- Executive summary
- Detailed results from all test categories
- Performance budget compliance
- Regression analysis
- Recommendations

## Performance Budgets

Defined in `metrics/perf_budget.yml`:

| Operation | Budget | Threshold |
|-----------|--------|-----------|
| workflow_start | 100ms | 120ms |
| agent_selection | 50ms | 75ms |
| git_hooks | 30ms | 50ms |
| quality_gate | 20ms | 30ms |
| bdd_tests | 500ms | 1000ms |
| api_response_p95 | 200ms | 300ms |
| cache_hit_rate | 90% | 70% |
| memory_usage | 256MB | 512MB |
| cpu_usage | 50% | 80% |

## Test Results Structure

```
test/performance/
├── results/
│   ├── baseline.json                    # Performance baseline
│   ├── benchmark_commands_output.log    # Command benchmark logs
│   ├── workflow_benchmark_summary.json  # Workflow results
│   ├── load_test_summary.json           # Load test results
│   ├── cache_performance_summary.json   # Cache analysis
│   ├── stress_*_system.log              # System metrics during stress
│   ├── memory_*.csv                     # Memory profiling data
│   ├── regression_report.json           # Regression analysis
│   ├── test_suite_summary.json          # Overall summary
│   └── history/                         # Historical benchmarks
│       └── benchmark_YYYYMMDD_HHMMSS.json
```

## CI/CD Integration

Add to `.github/workflows/performance-tests.yml`:

```yaml
name: Performance Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  performance:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y hyperfine jq

    - name: Run performance tests
      run: bash test/run_performance_tests.sh --quick

    - name: Check regressions
      run: bash test/performance/regression_check.sh

    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: test/performance/results/
```

## Interpreting Results

### Success Criteria

✅ **Passed** if all of these are true:
- Complete cycle time < 5000ms
- Performance improvement ≥ 75%
- Cache hit rate ≥ 85%
- No regressions > 10%
- Memory usage < 256MB per process
- All operations within budget

### Performance Improvements

Track improvements over time:

```bash
# View historical trends
ls -lh test/performance/results/history/

# Compare specific benchmarks
jq '.results' test/performance/results/history/benchmark_20250101_120000.json
jq '.results' test/performance/baseline.json
```

### Debugging Performance Issues

If tests fail:

1. **Check system load**: `top`, `htop`
2. **Review logs**: `less test/performance/results/*.log`
3. **Analyze specific test**: Run individual test script
4. **Profile with valgrind**:
   ```bash
   valgrind --leak-check=full --track-origins=yes .workflow/cli/ce status
   ```

## Performance Optimization Tips

Based on test results:

1. **Cache Optimization**
   - Increase TTL for stable data
   - Implement cache warming
   - Add cache preloading

2. **Parallel Execution**
   - Use background jobs for independent operations
   - Implement async validation

3. **State Management**
   - Lazy load session files
   - Implement state pagination
   - Add state compression

4. **Memory Management**
   - Implement cache size limits
   - Add periodic cleanup
   - Use memory-mapped files for large state

## Tools and Dependencies

### Required

- **bash** 4.0+
- **jq** - JSON parsing
- **git** - Version control operations
- **python3** - YAML parsing in executor

### Recommended

- **hyperfine** - Benchmarking tool
  ```bash
  sudo apt-get install hyperfine
  ```

- **gnuplot** - Chart generation
  ```bash
  sudo apt-get install gnuplot
  ```

- **valgrind** - Memory profiling
  ```bash
  sudo apt-get install valgrind
  ```

- **sysstat** - System statistics (iostat)
  ```bash
  sudo apt-get install sysstat
  ```

## Benchmarking Best Practices

1. **Consistent Environment**
   - Run on dedicated machine
   - Disable background processes
   - Use consistent git state

2. **Warmup Runs**
   - Always include warmup runs (3-5)
   - Discard first run data
   - Clear caches between tests

3. **Sample Size**
   - Minimum 10 runs for benchmarks
   - 100 runs for micro-benchmarks
   - Statistical significance (p < 0.05)

4. **Isolation**
   - One test at a time
   - Cool-down periods between tests
   - Monitor system metrics

## Troubleshooting

### Common Issues

**Issue:** `hyperfine: command not found`
```bash
sudo apt-get install hyperfine
```

**Issue:** `jq: command not found`
```bash
sudo apt-get install jq
```

**Issue:** "Permission denied" errors
```bash
chmod +x test/performance/*.sh
chmod +x test/run_performance_tests.sh
```

**Issue:** Cache not working
```bash
# Clear and rebuild cache
rm -rf .workflow/cli/state/cache
./.workflow/cli/ce status
```

**Issue:** Test failures due to stale state
```bash
# Reset workflow state
rm -rf .workflow/cli/state/sessions/*
rm -rf .phase/*
```

## Contributing

When adding new performance tests:

1. Follow naming convention: `test_category.sh`
2. Add budget to `metrics/perf_budget.yml`
3. Update this README
4. Generate new baseline
5. Add CI/CD integration

## References

- [Claude Enhancer 5.0 Documentation](../../CLAUDE.md)
- [Performance Budgets](../../metrics/perf_budget.yml)
- [Workflow Implementation](../../.workflow/cli/)
- [hyperfine Documentation](https://github.com/sharkdp/hyperfine)

---

**Last Updated:** $(date '+%Y-%m-%d')
**Version:** 1.0
**Maintainer:** Performance Testing Team
