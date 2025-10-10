# Claude Enhancer Observability System

> Production-grade monitoring, logging, and observability infrastructure for Claude Enhancer 5.0

## 🎯 Overview

The Claude Enhancer Observability System provides **comprehensive monitoring** covering the three pillars of observability:

- **Metrics**: Real-time performance, usage, error, and resource metrics
- **Logs**: Structured logging with multiple severity levels and automatic rotation
- **Traces**: Performance tracking with baseline comparison and regression detection

## 📊 System Architecture

```
observability/
├── metrics/              # Metrics collection and export
│   ├── collector.sh      # Multi-format metrics collector
│   └── *.prom           # Prometheus-format metrics
├── logging/              # Structured logging system
│   ├── logger.sh         # Multi-level logging with rotation
│   └── logs/            # Log storage by category
├── probes/               # Health check system
│   └── healthcheck.sh    # Liveness, readiness, startup probes
├── alerts/               # Alert management
│   ├── alert_rules.yml   # Alert rule definitions
│   ├── notifier.sh       # Multi-channel notifications
│   └── fired/           # Active alerts
├── dashboards/           # Status visualization
│   └── status.sh         # Real-time monitoring dashboard
├── performance/          # Performance monitoring
│   ├── monitor.sh        # Regression detection, reporting
│   └── baselines/       # Performance baselines
└── analytics/            # Usage analytics
    ├── usage_tracker.sh  # User behavior tracking
    └── reports/         # Analytics reports
```

## 🚀 Quick Start

### 1. Initialize All Systems

```bash
# Initialize observability infrastructure
./observability/metrics/collector.sh collect
./observability/logging/logger.sh init
./observability/probes/healthcheck.sh all
```

### 2. View Real-Time Dashboard

```bash
# Start live monitoring dashboard
./observability/dashboards/status.sh live

# Options: full (default), compact, minimal
./observability/dashboards/status.sh live compact
```

### 3. Run Health Checks

```bash
# Comprehensive health check
./observability/probes/healthcheck.sh all

# Individual probes
./observability/probes/healthcheck.sh liveness
./observability/probes/healthcheck.sh readiness
./observability/probes/healthcheck.sh startup
```

## 📈 Service Level Objectives (SLOs)

Defined in `observability/slo/slo.yml`:

| SLO | Target | Measurement |
|-----|--------|-------------|
| **Availability** | 99.9% | Uptime percentage |
| **Error Rate** | <0.1% | Failed commands / total |
| **P95 Latency** | <500ms | Command execution time |
| **Cache Hit Rate** | >85% | Cache efficiency |
| **Memory Usage** | <80% | Resource utilization |

## 🔍 Metrics Collection

### Automatic Collection

Metrics are automatically collected for:

- **Performance**: Command execution times, cache hit/miss rates
- **Usage**: Active terminals, commands executed, features tracked
- **Errors**: Error counts by type and severity
- **Resources**: CPU, memory, disk, network usage

### Manual Collection

```bash
# Collect all metrics
./observability/metrics/collector.sh collect

# Export to Prometheus format
./observability/metrics/collector.sh export-prometheus

# Export to JSON
./observability/metrics/collector.sh export-json

# Run as background daemon
./observability/metrics/collector.sh daemon
```

### Available Metrics

```
# Performance
ce_command_duration_milliseconds{operation="..."}
ce_performance_budget_violations_total{operation="..."}
ce_cache_hits_total
ce_cache_misses_total
ce_cache_hit_rate_percent

# Usage
ce_active_terminals
ce_commands_executed_total
ce_terminals_by_phase{phase="..."}
ce_features_total
ce_pull_requests_total

# Errors
ce_errors_total{level="..."}
ce_git_errors_total
ce_validation_errors_total
ce_failed_commands_total
ce_error_rate_percent

# Resources
ce_cpu_usage_percent
ce_memory_usage_percent
ce_memory_used_megabytes
ce_disk_usage_percent
ce_state_directory_bytes
ce_cache_directory_bytes
```

## 📝 Logging System

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARN**: Warning messages (potential issues)
- **ERROR**: Error messages (recoverable)
- **CRITICAL**: Critical errors (severe issues)
- **FATAL**: Fatal errors (system shutdown)

### Usage in Scripts

```bash
# Source the logger
source ./observability/logging/logger.sh

# Log messages
ce_log_debug "Detailed debug information"
ce_log_info "General information"
ce_log_warn "Warning: Something might be wrong"
ce_log_error "Error occurred: ${error_message}"
ce_log_critical "Critical system issue"

# Structured logging with context
ce_log_with_context "ERROR" "Authentication failed" \
    user="john" \
    ip="192.168.1.1" \
    reason="invalid_password"

# Performance logging
ce_log_performance "database_query" 45 "success"

# Audit logging
ce_log_audit "user_login" "john" "/api/auth" "POST" "success"
```

### Log Management

```bash
# Search logs
./observability/logging/logger.sh search "ERROR" errors 100

# Get log statistics
./observability/logging/logger.sh stats application

# Tail logs in real-time
./observability/logging/logger.sh tail errors 50

# Rotate logs
./observability/logging/logger.sh rotate all

# Cleanup old logs
./observability/logging/logger.sh cleanup
```

### Log Files

```
.workflow/observability/logs/
├── application/
│   └── YYYY-MM-DD.log    # Daily application logs
├── errors/
│   └── YYYY-MM-DD.log    # Error logs only
├── audit/
│   └── YYYY-MM-DD.log    # Security audit logs
└── performance/
    └── YYYY-MM-DD.log    # Performance logs
```

## 🏥 Health Checks

### Health Check Types

1. **Liveness Probe**: Is the system running?
   - Git repository accessible
   - Required tools available
   - State directory writable
   - No critical locks
   - System load acceptable

2. **Readiness Probe**: Ready to accept commands?
   - Core libraries loadable
   - Cache directory accessible
   - Git operations functional
   - No state conflicts
   - Sufficient disk space
   - Sufficient memory

3. **Startup Probe**: Initialization complete?
   - Workflow executor present
   - Phase gates configured
   - Git hooks installed
   - State directory initialized
   - Monitoring initialized

### Running Health Checks

```bash
# All probes with verbose output
./observability/probes/healthcheck.sh all text

# JSON output for automation
./observability/probes/healthcheck.sh all json

# Quick health check
./observability/probes/healthcheck.sh quick

# Simulate HTTP endpoints
./observability/probes/healthcheck.sh endpoint /healthz
./observability/probes/healthcheck.sh endpoint /healthz/ready
```

### Health Check Results

```json
{
  "timestamp": "2025-10-10T12:00:00Z",
  "overall_status": "healthy",
  "probes": {
    "liveness": {"status": "healthy", "result": 0},
    "readiness": {"status": "healthy", "result": 0},
    "startup": {"status": "healthy", "result": 0}
  }
}
```

## 🚨 Alert Management

### Alert Rules

Defined in `observability/alerts/alert_rules.yml`:

**Critical Alerts:**
- System down (>2 minutes)
- High error rate (>1%)
- Critical CPU/memory usage (>95%)
- Disk space critical (<5%)

**Warning Alerts:**
- High latency (p95 >500ms)
- Performance budget violations
- Cache degraded (<70% hit rate)
- Resource usage high (>80%)

**Info Alerts:**
- State directory growing rapidly
- High feature count
- Capacity planning signals

### Alert Notification

```bash
# Send an alert
./observability/alerts/notifier.sh send \
    "HighErrorRate" \
    "critical" \
    "Error rate exceeds 1%" \
    "Current rate: 2.5%" \
    "docs/runbooks/high-error-rate.md" \
    "Investigate immediately"

# List active alerts
./observability/alerts/notifier.sh list

# Resolve an alert
./observability/alerts/notifier.sh resolve <alert_id> "Issue resolved"

# Get alert statistics
./observability/alerts/notifier.sh stats
```

### Notification Channels

- **Console**: Immediate visual feedback
- **File**: Persistent alert logs
- **Email**: Optional email notifications (requires configuration)
- **Webhook**: Optional webhook integration

### Configuration

```bash
# Set notification channels
export CE_ALERT_CHANNELS="console,file,email"

# Configure email
export CE_ALERT_EMAIL="ops@example.com"

# Configure webhook
export CE_ALERT_WEBHOOK="https://hooks.example.com/alerts"
```

## 📊 Monitoring Dashboard

### Live Dashboard

```bash
# Full dashboard with all sections
./observability/dashboards/status.sh live full

# Compact dashboard (key metrics only)
./observability/dashboards/status.sh live compact

# Minimal dashboard (SLO compliance + resources)
./observability/dashboards/status.sh live minimal
```

### Dashboard Sections

1. **SLO Compliance**: Real-time SLO status
2. **Performance Metrics**: Cache stats, command performance
3. **Resource Usage**: CPU, memory, disk with visual bars
4. **Active Terminals**: Terminal count and phase distribution
5. **Active Alerts**: Current alert status

### Export Dashboard

```bash
# Export to file for reports
./observability/dashboards/status.sh export status.txt
```

## 📉 Performance Monitoring

### Create Baseline

```bash
# Create performance baseline from recent data
./observability/performance/monitor.sh baseline production

# Baseline is used for regression detection
```

### Real-Time Monitoring

```bash
# Watch performance in real-time
./observability/performance/monitor.sh live

# Output shows:
# ✓ operation_name     45ms (budget: 100ms)
# ⚠ slow_operation    150ms (budget: 100ms)
# ✗ failed_operation  520ms (budget: 200ms)
```

### Performance Reports

```bash
# Generate comprehensive performance report
./observability/performance/monitor.sh report weekly

# Analyze trends
./observability/performance/monitor.sh trends git_status 7
```

### Regression Detection

Automatic detection when:
- Performance degrades >20% from baseline (configurable)
- Alert triggered automatically
- Regression logged for analysis

## 📊 Usage Analytics

### Track Usage Patterns

```bash
# Most used commands
./observability/analytics/usage_tracker.sh commands 20

# Session statistics
./observability/analytics/usage_tracker.sh sessions 30

# Phase progression patterns
./observability/analytics/usage_tracker.sh phases

# Feature adoption metrics
./observability/analytics/usage_tracker.sh features 30
```

### Usage Heatmap

```bash
# See usage distribution by hour
./observability/analytics/usage_tracker.sh heatmap

# Shows peak usage times for optimization
```

### Analytics Reports

```bash
# Generate comprehensive analytics report
./observability/analytics/usage_tracker.sh report monthly

# Export data for external analysis
./observability/analytics/usage_tracker.sh export json
./observability/analytics/usage_tracker.sh export csv
```

## 🔧 Configuration

### Environment Variables

```bash
# Metrics
CE_METRICS_DIR=".workflow/observability/metrics"
CE_METRICS_INTERVAL=60              # Collection interval (seconds)
CE_METRICS_RETENTION=7              # Retention (days)
CE_METRICS_FORMAT="prometheus"     # prometheus, json, statsd

# Logging
CE_LOG_DIR=".workflow/observability/logs"
CE_LOG_LEVEL="INFO"                 # DEBUG, INFO, WARN, ERROR, CRITICAL
CE_LOG_FORMAT="json"                # json, text
CE_LOG_ROTATION="daily"             # daily, size
CE_LOG_RETENTION=7                  # Retention (days)

# Health Checks
CE_HEALTH_CHECK_TIMEOUT=5           # Timeout (seconds)

# Alerts
CE_ALERT_CHANNELS="console,file"
CE_ALERT_EMAIL=""                   # Optional
CE_ALERT_WEBHOOK=""                 # Optional

# Performance
CE_PERF_REGRESSION_THRESHOLD=0.2    # 20% degradation threshold

# Analytics
CE_ANALYTICS_RETENTION=30           # Retention (days)
```

## 🔗 Integration

### Integration with Existing Systems

The observability system integrates with:

1. **Performance Monitor** (`.workflow/cli/lib/performance_monitor.sh`)
   - Automatically tracks all command executions
   - Enforces performance budgets
   - Records violations

2. **Cache Manager** (`.workflow/cli/lib/cache_manager.sh`)
   - Tracks cache hit/miss rates
   - Monitors cache size
   - Reports cache statistics

3. **Git Hooks** (`.git/hooks/`)
   - Can trigger alerts on violations
   - Log audit events
   - Track performance

4. **CI/CD Pipelines** (`.github/workflows/`)
   - Health checks in CI
   - SLO validation
   - Performance regression detection

### Programmatic Usage

```bash
# In your scripts
source ./observability/logging/logger.sh
source ./observability/metrics/collector.sh

# Track performance
ce_perf_start "my_operation"
# ... your code ...
ce_perf_stop "my_operation"

# Log events
ce_log_info "Operation completed successfully"

# Collect metrics
ce_metrics_gauge "custom_metric" 42 "{label=\"value\"}" "My custom metric"
```

## 📚 Best Practices

### 1. Regular Monitoring

- Check dashboard daily
- Review alerts promptly
- Analyze trends weekly
- Generate reports monthly

### 2. Performance

- Set realistic performance budgets
- Create baselines after optimizations
- Monitor for regressions continuously
- Investigate violations immediately

### 3. Logging

- Use appropriate log levels
- Include context in logs
- Rotate logs regularly
- Archive important logs

### 4. Alerting

- Keep alert rules up to date
- Tune thresholds to reduce noise
- Document runbooks for each alert
- Test alert channels regularly

### 5. Health Checks

- Run health checks before deployments
- Monitor startup probe during rollouts
- Use readiness probe for load balancing
- Check liveness for auto-recovery

## 🆘 Troubleshooting

### High Resource Usage

```bash
# Check resource metrics
./observability/metrics/collector.sh collect
./observability/dashboards/status.sh once

# Cleanup if needed
./observability/logging/logger.sh cleanup
./observability/metrics/collector.sh cleanup
```

### Performance Degradation

```bash
# Check for regressions
./observability/performance/monitor.sh trends all 7

# Generate performance report
./observability/performance/monitor.sh report investigation

# Review baselines
ls -la .workflow/observability/performance/baselines/
```

### Alert Fatigue

```bash
# Review active alerts
./observability/alerts/notifier.sh list

# Check alert statistics
./observability/alerts/notifier.sh stats

# Adjust thresholds in alert_rules.yml
```

### Missing Data

```bash
# Verify systems are running
./observability/probes/healthcheck.sh all

# Check initialization
ls -la .workflow/observability/*/. metadata

# Re-initialize if needed
./observability/metrics/collector.sh collect
./observability/logging/logger.sh init
```

## 📖 Additional Resources

- [SLO Definitions](slo/slo.yml)
- [Alert Rules](alerts/alert_rules.yml)
- [Performance Budgets](../metrics/perf_budget.yml)
- [Monitoring Reports](performance/reports/)
- [Analytics Reports](analytics/reports/)

## 🎯 Goals and Metrics

| Goal | Metric | Target |
|------|--------|--------|
| High Availability | Uptime | >99.9% |
| Low Error Rate | Errors/Commands | <0.1% |
| Fast Performance | P95 Latency | <500ms |
| Efficient Caching | Cache Hit Rate | >85% |
| Resource Efficient | Memory Usage | <80% |

---

**Claude Enhancer 5.0** - Production-Grade Observability
*Real-time monitoring for real-time development*
