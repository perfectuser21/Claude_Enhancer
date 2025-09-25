/**
 * Claude Enhancer 5.0 - Prometheus Metrics Exporter
 * Exports error recovery metrics in Prometheus format for monitoring
 */

const http = require('http');
const { EventEmitter } = require('events');

class PrometheusExporter extends EventEmitter {
    constructor(options = {}) {
        super();

        this.config = {
            port: options.port || 9090,
            host: options.host || '0.0.0.0',
            path: options.path || '/metrics',
            updateInterval: options.updateInterval || 15000, // 15 seconds
            enableHistograms: options.enableHistograms || true,
            ...options
        };

        this.metrics = new Map();
        this.server = null;
        this.isRunning = false;

        this.initializeMetrics();
    }

    initializeMetrics() {
        // Counter metrics
        this.registerMetric('error_recovery_errors_total', 'counter', 'Total number of errors encountered', ['error_type', 'recovery_strategy']);
        this.registerMetric('error_recovery_recoveries_total', 'counter', 'Total number of successful recoveries', ['strategy', 'error_type']);
        this.registerMetric('error_recovery_failures_total', 'counter', 'Total number of failed recovery attempts', ['strategy', 'error_type']);
        this.registerMetric('error_recovery_circuit_breaker_trips_total', 'counter', 'Total circuit breaker trips', ['breaker_id', 'reason']);
        this.registerMetric('error_recovery_checkpoints_created_total', 'counter', 'Total checkpoints created', ['checkpoint_type']);
        this.registerMetric('error_recovery_checkpoints_restored_total', 'counter', 'Total checkpoints restored', ['checkpoint_type']);
        this.registerMetric('error_recovery_patterns_detected_total', 'counter', 'Total error patterns detected', ['pattern_type', 'severity']);

        // Gauge metrics
        this.registerMetric('error_recovery_active_recoveries', 'gauge', 'Number of currently active recovery operations');
        this.registerMetric('error_recovery_circuit_breaker_state', 'gauge', 'Circuit breaker state (0=closed, 1=open, 2=half-open)', ['breaker_id']);
        this.registerMetric('error_recovery_health_status', 'gauge', 'Overall health status (0=critical, 1=warning, 2=healthy)');
        this.registerMetric('error_recovery_memory_usage_bytes', 'gauge', 'Memory usage in bytes');
        this.registerMetric('error_recovery_checkpoint_count', 'gauge', 'Number of active checkpoints');

        // Histogram metrics
        if (this.config.enableHistograms) {
            this.registerMetric('error_recovery_duration_seconds', 'histogram', 'Duration of recovery operations in seconds', ['strategy', 'error_type'], {
                buckets: [0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30, 60]
            });
            this.registerMetric('error_recovery_retry_attempts', 'histogram', 'Number of retry attempts', ['strategy'], {
                buckets: [1, 2, 3, 5, 10, 20, 50]
            });
        }

        // Summary metrics
        this.registerMetric('error_recovery_success_rate', 'summary', 'Success rate of recovery operations', ['strategy'], {
            quantiles: [0.5, 0.9, 0.95, 0.99]
        });
    }

    registerMetric(name, type, help, labels = [], options = {}) {
        this.metrics.set(name, {
            name,
            type,
            help,
            labels,
            values: new Map(),
            options,
            lastUpdate: Date.now()
        });
    }

    updateMetric(name, value, labels = {}) {
        const metric = this.metrics.get(name);
        if (!metric) {
            console.warn(`Metric ${name} not found`);
            return;
        }

        const labelKey = this.generateLabelKey(labels);

        switch (metric.type) {
            case 'counter':
                const currentCounter = metric.values.get(labelKey) || 0;
                metric.values.set(labelKey, currentCounter + value);
                break;

            case 'gauge':
                metric.values.set(labelKey, value);
                break;

            case 'histogram':
                this.updateHistogram(metric, value, labelKey);
                break;

            case 'summary':
                this.updateSummary(metric, value, labelKey);
                break;
        }

        metric.lastUpdate = Date.now();
        this.emit('metricUpdated', { name, value, labels });
    }

    incrementCounter(name, labels = {}, value = 1) {
        this.updateMetric(name, value, labels);
    }

    setGauge(name, value, labels = {}) {
        this.updateMetric(name, value, labels);
    }

    observeHistogram(name, value, labels = {}) {
        this.updateMetric(name, value, labels);
    }

    observeSummary(name, value, labels = {}) {
        this.updateMetric(name, value, labels);
    }

    updateHistogram(metric, value, labelKey) {
        let histogramData = metric.values.get(labelKey);
        if (!histogramData) {
            histogramData = {
                buckets: new Map(),
                sum: 0,
                count: 0
            };
            metric.values.set(labelKey, histogramData);
        }

        histogramData.sum += value;
        histogramData.count++;

        // Update buckets
        const buckets = metric.options.buckets || [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10];
        for (const bucket of buckets) {
            if (value <= bucket) {
                const currentCount = histogramData.buckets.get(bucket) || 0;
                histogramData.buckets.set(bucket, currentCount + 1);
            }
        }

        // +Inf bucket
        const infCount = histogramData.buckets.get('+Inf') || 0;
        histogramData.buckets.set('+Inf', infCount + 1);
    }

    updateSummary(metric, value, labelKey) {
        let summaryData = metric.values.get(labelKey);
        if (!summaryData) {
            summaryData = {
                values: [],
                sum: 0,
                count: 0,
                quantiles: new Map()
            };
            metric.values.set(labelKey, summaryData);
        }

        summaryData.values.push(value);
        summaryData.sum += value;
        summaryData.count++;

        // Keep only recent values (last 1000)
        if (summaryData.values.length > 1000) {
            summaryData.values.shift();
        }

        // Calculate quantiles
        this.calculateQuantiles(summaryData, metric.options.quantiles || [0.5, 0.9, 0.95, 0.99]);
    }

    calculateQuantiles(summaryData, quantiles) {
        const sorted = [...summaryData.values].sort((a, b) => a - b);

        for (const quantile of quantiles) {
            const index = Math.floor((sorted.length - 1) * quantile);
            summaryData.quantiles.set(quantile, sorted[index] || 0);
        }
    }

    generateLabelKey(labels) {
        if (Object.keys(labels).length === 0) return '';

        return Object.entries(labels)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([k, v]) => `${k}="${v}"`)
            .join(',');
    }

    formatMetricsForPrometheus() {
        const lines = [];

        for (const [name, metric] of this.metrics.entries()) {
            // Add help and type
            lines.push(`# HELP ${name} ${metric.help}`);
            lines.push(`# TYPE ${name} ${metric.type}`);

            switch (metric.type) {
                case 'counter':
                case 'gauge':
                    for (const [labelKey, value] of metric.values.entries()) {
                        const labels = labelKey ? `{${labelKey}}` : '';
                        lines.push(`${name}${labels} ${value}`);
                    }
                    break;

                case 'histogram':
                    for (const [labelKey, histogramData] of metric.values.entries()) {
                        const baseLabels = labelKey ? `{${labelKey}` : '{';

                        // Bucket metrics
                        for (const [bucket, count] of histogramData.buckets.entries()) {
                            const bucketLabels = labelKey
                                ? `{${labelKey},le="${bucket}"}`
                                : `{le="${bucket}"}`;
                            lines.push(`${name}_bucket${bucketLabels} ${count}`);
                        }

                        // Sum and count
                        const labels = labelKey ? `{${labelKey}}` : '';
                        lines.push(`${name}_sum${labels} ${histogramData.sum}`);
                        lines.push(`${name}_count${labels} ${histogramData.count}`);
                    }
                    break;

                case 'summary':
                    for (const [labelKey, summaryData] of metric.values.entries()) {
                        // Quantile metrics
                        for (const [quantile, value] of summaryData.quantiles.entries()) {
                            const quantileLabels = labelKey
                                ? `{${labelKey},quantile="${quantile}"}`
                                : `{quantile="${quantile}"}`;
                            lines.push(`${name}${quantileLabels} ${value}`);
                        }

                        // Sum and count
                        const labels = labelKey ? `{${labelKey}}` : '';
                        lines.push(`${name}_sum${labels} ${summaryData.sum}`);
                        lines.push(`${name}_count${labels} ${summaryData.count}`);
                    }
                    break;
            }

            lines.push(''); // Empty line between metrics
        }

        return lines.join('\n');
    }

    async startServer() {
        if (this.isRunning) {
            console.warn('Prometheus exporter already running');
            return;
        }

        this.server = http.createServer((req, res) => {
            if (req.url === this.config.path && req.method === 'GET') {
                const metrics = this.formatMetricsForPrometheus();

                res.writeHead(200, {
                    'Content-Type': 'text/plain; version=0.0.4; charset=utf-8'
                });
                res.end(metrics);

                this.emit('metricsRequested', { timestamp: Date.now() });
            } else {
                res.writeHead(404);
                res.end('Not found');
            }
        });

        return new Promise((resolve, reject) => {
            this.server.listen(this.config.port, this.config.host, (error) => {
                if (error) {
                    reject(error);
                } else {
                    this.isRunning = true;
                    console.log(`✅ Prometheus exporter started on http://${this.config.host}:${this.config.port}${this.config.path}`);
                    this.emit('serverStarted', { port: this.config.port, host: this.config.host });
                    resolve();
                }
            });
        });
    }

    async stopServer() {
        if (!this.isRunning || !this.server) {
            return;
        }

        return new Promise((resolve) => {
            this.server.close(() => {
                this.isRunning = false;
                this.server = null;
                console.log('✅ Prometheus exporter stopped');
                this.emit('serverStopped');
                resolve();
            });
        });
    }

    // Integration with Error Recovery Monitor
    integrateWithMonitor(monitor) {
        // Listen to monitor events and update Prometheus metrics
        monitor.on('recoveryStarted', (data) => {
            this.incrementCounter('error_recovery_errors_total', {
                error_type: data.errorType,
                recovery_strategy: data.strategy
            });
        });

        monitor.on('recoverySuccessful', (data) => {
            this.incrementCounter('error_recovery_recoveries_total', {
                strategy: data.strategy,
                error_type: data.errorType
            });

            if (this.config.enableHistograms) {
                this.observeHistogram('error_recovery_duration_seconds', data.duration / 1000, {
                    strategy: data.strategy,
                    error_type: data.errorType
                });
            }
        });

        monitor.on('recoveryFailed', (data) => {
            this.incrementCounter('error_recovery_failures_total', {
                strategy: data.strategy,
                error_type: data.error?.type || 'unknown'
            });

            if (this.config.enableHistograms && data.attempts) {
                this.observeHistogram('error_recovery_retry_attempts', data.attempts, {
                    strategy: data.strategy
                });
            }
        });

        monitor.on('circuitBreakerTripped', (data) => {
            this.incrementCounter('error_recovery_circuit_breaker_trips_total', {
                breaker_id: data.breakerId,
                reason: data.reason
            });

            this.setGauge('error_recovery_circuit_breaker_state', 1, {
                breaker_id: data.breakerId
            });
        });

        monitor.on('healthCheck', (health) => {
            const statusValue = health.status === 'healthy' ? 2 :
                               health.status === 'warning' ? 1 : 0;
            this.setGauge('error_recovery_health_status', statusValue);

            if (health.components.resources) {
                this.setGauge('error_recovery_memory_usage_bytes',
                    health.components.resources.memory * 1024 * 1024);
            }
        });

        monitor.on('metricsCollected', (snapshot) => {
            // Update gauge metrics from monitor
            if (snapshot.metrics.checkpoints_created) {
                this.setGauge('error_recovery_checkpoint_count',
                    snapshot.metrics.checkpoints_created.value);
            }

            // Update summary metrics
            if (snapshot.performance.errorRate !== undefined) {
                this.observeSummary('error_recovery_success_rate',
                    1 - snapshot.performance.errorRate, { strategy: 'overall' });
            }
        });

        console.log('✅ Prometheus exporter integrated with Error Recovery Monitor');
    }

    // Utility methods
    getMetricValue(name, labels = {}) {
        const metric = this.metrics.get(name);
        if (!metric) return null;

        const labelKey = this.generateLabelKey(labels);
        return metric.values.get(labelKey) || 0;
    }

    resetMetric(name, labels = {}) {
        const metric = this.metrics.get(name);
        if (!metric) return;

        const labelKey = this.generateLabelKey(labels);

        if (metric.type === 'histogram') {
            metric.values.set(labelKey, {
                buckets: new Map(),
                sum: 0,
                count: 0
            });
        } else if (metric.type === 'summary') {
            metric.values.set(labelKey, {
                values: [],
                sum: 0,
                count: 0,
                quantiles: new Map()
            });
        } else {
            metric.values.set(labelKey, 0);
        }
    }

    clearAllMetrics() {
        for (const metric of this.metrics.values()) {
            metric.values.clear();
        }
        console.log('✅ All Prometheus metrics cleared');
    }

    getStatus() {
        return {
            running: this.isRunning,
            port: this.config.port,
            host: this.config.host,
            path: this.config.path,
            metricsCount: this.metrics.size,
            lastUpdate: Math.max(...Array.from(this.metrics.values()).map(m => m.lastUpdate))
        };
    }
}

module.exports = PrometheusExporter;