# Observability Quick Reference Card

> **Fast access to common monitoring commands**

## 🚀 Common Commands

### Health & Status

```bash
# Quick health check
./observability/probes/healthcheck.sh quick

# Full health check
./observability/probes/healthcheck.sh all

# Live dashboard
./observability/dashboards/status.sh live

# One-time status view
./observability/dashboards/status.sh once
```

### Metrics

```bash
# Collect all metrics
./observability/metrics/collector.sh collect

# Export to Prometheus
./observability/metrics/collector.sh export-prometheus

# Export to JSON
./observability/metrics/collector.sh export-json

# View metrics
cat .workflow/observability/metrics/metrics.prom
```

### Logging

```bash
# Tail error logs
./observability/logging/logger.sh tail errors 50

# Search logs
./observability/logging/logger.sh search "ERROR" errors 100

# Log statistics
./observability/logging/logger.sh stats application

# Cleanup old logs
./observability/logging/logger.sh cleanup
```

### Alerts

```bash
# List active alerts
./observability/alerts/notifier.sh list

# Get alert statistics
./observability/alerts/notifier.sh stats

# Resolve an alert
./observability/alerts/notifier.sh resolve <alert_id>

# Send test alert
./observability/alerts/notifier.sh send "Test" "info" "Test alert"
```

### Performance

```bash
# Watch performance in real-time
./observability/performance/monitor.sh live

# Create baseline
./observability/performance/monitor.sh baseline production

# Generate report
./observability/performance/monitor.sh report weekly

# Analyze trends
./observability/performance/monitor.sh trends all 7
```

### Analytics

```bash
# Most used commands
./observability/analytics/usage_tracker.sh commands 20

# Session statistics
./observability/analytics/usage_tracker.sh sessions 30

# Usage heatmap
./observability/analytics/usage_tracker.sh heatmap

# Generate report
./observability/analytics/usage_tracker.sh report monthly
```

## 📝 Log Usage in Scripts

```bash
# Source the logger
source ./observability/logging/logger.sh

# Log at different levels
ce_log_debug "Detailed debug info"
ce_log_info "General information"
ce_log_warn "Warning message"
ce_log_error "Error occurred: ${error}"
ce_log_critical "Critical issue"

# Structured logging with context
ce_log_with_context "ERROR" "Authentication failed" \
    user="john" \
    ip="192.168.1.1"

# Performance logging
ce_log_performance "database_query" 45 "success"

# Audit logging
ce_log_audit "user_login" "john" "/api/auth" "POST" "success"
```

## 📊 Custom Metrics in Scripts

```bash
# Source metrics collector
source ./observability/metrics/collector.sh

# Record counter
ce_metrics_counter "my_counter" 1 "{label=\"value\"}" "My counter"

# Record gauge
ce_metrics_gauge "my_gauge" 42 "{label=\"value\"}" "My gauge"

# Record histogram
ce_metrics_histogram "my_histogram" 123 "{label=\"value\"}" "My histogram"
```

## 🔍 Troubleshooting Quick Fixes

### High Resource Usage
```bash
# Check resources
./observability/dashboards/status.sh once | grep -A 5 "Resource Usage"

# Cleanup
./observability/logging/logger.sh cleanup
./observability/metrics/collector.sh cleanup
```

### Performance Issues
```bash
# Check for regressions
./observability/performance/monitor.sh trends all 7

# Review baselines
ls -lh .workflow/observability/performance/baselines/
```

### Too Many Alerts
```bash
# Review active alerts
./observability/alerts/notifier.sh list

# Check statistics
./observability/alerts/notifier.sh stats

# Cleanup old alerts
./observability/alerts/notifier.sh cleanup 7
```

## 📈 Key Metrics to Watch

| Metric | Target | Command |
|--------|--------|---------|
| Availability | >99.9% | Check dashboard SLO section |
| Error Rate | <0.1% | `ce_error_rate_percent` |
| P95 Latency | <500ms | Check performance log |
| Cache Hit Rate | >85% | `ce_cache_hit_rate_percent` |
| CPU Usage | <80% | `ce_cpu_usage_percent` |
| Memory Usage | <80% | `ce_memory_usage_percent` |
| Disk Usage | <85% | `ce_disk_usage_percent` |

## 🚨 Critical Alerts Response

### System Down
1. Check health: `./observability/probes/healthcheck.sh all`
2. Review logs: `./observability/logging/logger.sh tail errors 100`
3. Check resources: `./observability/dashboards/status.sh once`

### High Error Rate
1. Check error logs: `./observability/logging/logger.sh search "ERROR" errors`
2. Review metrics: `cat .workflow/observability/metrics/metrics.prom | grep error`
3. Analyze patterns: `./observability/analytics/usage_tracker.sh report`

### Performance Degradation
1. Check regressions: `./observability/performance/monitor.sh trends all 1`
2. Review baseline: `cat .workflow/observability/performance/baselines/*.json`
3. Generate report: `./observability/performance/monitor.sh report investigation`

## 🔧 Configuration

### Environment Variables

```bash
# Metrics
export CE_METRICS_INTERVAL=60
export CE_METRICS_FORMAT="prometheus"

# Logging
export CE_LOG_LEVEL="INFO"
export CE_LOG_FORMAT="json"

# Alerts
export CE_ALERT_CHANNELS="console,file"
export CE_ALERT_EMAIL="ops@example.com"

# Performance
export CE_PERF_REGRESSION_THRESHOLD=0.2
```

## 📍 Important File Locations

```
Configuration:
  observability/slo/slo.yml
  observability/alerts/alert_rules.yml
  metrics/perf_budget.yml

Logs:
  .workflow/observability/logs/application/
  .workflow/observability/logs/errors/
  .workflow/observability/logs/audit/
  .workflow/observability/logs/performance/

Metrics:
  .workflow/observability/metrics/metrics.prom
  .workflow/observability/metrics/metrics.json

Performance:
  .workflow/observability/performance/baselines/
  .workflow/observability/performance/reports/
  .workflow/observability/performance/regressions.jsonl

Analytics:
  .workflow/observability/analytics/usage/
  .workflow/observability/analytics/reports/

Alerts:
  .workflow/observability/alerts/fired/
  .workflow/observability/alerts/resolved/
```

## ⚡ Quick Start Checklist

- [ ] Run health check: `./observability/probes/healthcheck.sh all`
- [ ] Initialize logging: `./observability/logging/logger.sh init`
- [ ] Collect metrics: `./observability/metrics/collector.sh collect`
- [ ] View dashboard: `./observability/dashboards/status.sh once`
- [ ] Create baseline: `./observability/performance/monitor.sh baseline`
- [ ] Review alerts: `./observability/alerts/notifier.sh list`

---

**For full documentation**: See `observability/README.md`
**For implementation details**: See `P7_MONITORING_IMPLEMENTATION_COMPLETE.md`
