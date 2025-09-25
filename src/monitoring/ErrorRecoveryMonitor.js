/**
 * Claude Enhancer 5.0 - Error Recovery Monitoring System
 * Comprehensive monitoring and observability for error recovery operations
 */

const fs = require('fs').promises;
const path = require('path');
const { EventEmitter } = require('events');

class ErrorRecoveryMonitor extends EventEmitter {
    constructor(options = {}) {
        super();

        this.config = {
            metricsDir: options.metricsDir || './.claude/metrics',
            alertsDir: options.alertsDir || './.claude/alerts',
            logsDir: options.logsDir || './.claude/logs',
            dashboardPort: options.dashboardPort || 3000,
            metricsInterval: options.metricsInterval || 30000, // 30 seconds
            alertThresholds: {
                errorRate: 0.05,           // 5% error rate threshold
                recoveryTime: 5000,        // 5 second max recovery time
                circuitBreakerTrips: 3,    // Max circuit breaker trips per hour
                memoryUsage: 0.8,          // 80% memory usage threshold
                diskSpace: 0.9,            // 90% disk usage threshold
                consecutiveFailures: 5      // 5 consecutive failures
            },
            retentionPeriod: 7 * 24 * 60 * 60 * 1000, // 7 days
            enableRealTimeAlerts: true,
            enableDashboard: true,
            enableMetricsExport: true,
            ...options
        };

        // Monitoring state
        this.metrics = new Map();
        this.alerts = [];
        this.dashboardData = new Map();
        this.healthStatus = 'healthy';
        this.lastMetricsSnapshot = null;
        this.alertHistory = [];
        this.activeAlerts = new Map();

        // Performance tracking
        this.performanceMetrics = {
            recoveryTimes: [],
            errorRates: [],
            throughput: [],
            resourceUsage: [],
            circuitBreakerStatus: new Map()
        };

        // Initialize monitoring
        this.initializeMonitoring();
    }

    async initializeMonitoring() {
        try {
            // Create required directories
            await this.ensureDirectories();

            // Initialize metrics collection
            this.initializeMetricsCollection();

            // Start monitoring loops
            this.startMetricsCollection();
            this.startHealthChecks();
            this.startAlertProcessing();

            // Setup event listeners
            this.setupEventListeners();

            console.log('✅ Error Recovery Monitor initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize Error Recovery Monitor:', error);
            throw error;
        }
    }

    async ensureDirectories() {
        const dirs = [
            this.config.metricsDir,
            this.config.alertsDir,
            this.config.logsDir,
            path.join(this.config.logsDir, 'recovery'),
            path.join(this.config.metricsDir, 'snapshots'),
            path.join(this.config.metricsDir, 'exports')
        ];

        for (const dir of dirs) {
            await fs.mkdir(dir, { recursive: true });
        }
    }

    initializeMetricsCollection() {
        // Initialize core metrics
        const coreMetrics = [
            'errors_total',
            'recoveries_total',
            'recovery_success_rate',
            'average_recovery_time',
            'circuit_breaker_trips',
            'checkpoints_created',
            'checkpoints_restored',
            'pattern_detections',
            'graceful_degradations',
            'resource_usage'
        ];

        coreMetrics.forEach(metric => {
            this.metrics.set(metric, {
                value: 0,
                timestamp: Date.now(),
                history: [],
                labels: {}
            });
        });
    }

    setupEventListeners() {
        // Listen for recovery system events
        process.on('errorRecovery:start', (data) => this.handleRecoveryStart(data));
        process.on('errorRecovery:success', (data) => this.handleRecoverySuccess(data));
        process.on('errorRecovery:failure', (data) => this.handleRecoveryFailure(data));
        process.on('errorRecovery:circuitBreakerTrip', (data) => this.handleCircuitBreakerTrip(data));
        process.on('errorRecovery:checkpointCreated', (data) => this.handleCheckpointCreated(data));
        process.on('errorRecovery:patternDetected', (data) => this.handlePatternDetected(data));
    }

    // Event Handlers
    handleRecoveryStart(data) {
        this.incrementMetric('recoveries_total');
        this.recordEvent('recovery_start', data);

        this.emit('recoveryStarted', {
            timestamp: Date.now(),
            errorType: data.errorType,
            strategy: data.strategy,
            context: data.context
        });
    }

    handleRecoverySuccess(data) {
        const recoveryTime = data.duration || 0;

        this.incrementMetric('recovery_success_rate');
        this.updateMetric('average_recovery_time', recoveryTime);
        this.performanceMetrics.recoveryTimes.push({
            timestamp: Date.now(),
            duration: recoveryTime,
            strategy: data.strategy
        });

        this.recordEvent('recovery_success', data);
        this.checkAlertConditions('recovery_success', data);

        this.emit('recoverySuccessful', {
            timestamp: Date.now(),
            duration: recoveryTime,
            strategy: data.strategy,
            errorType: data.errorType
        });
    }

    handleRecoveryFailure(data) {
        this.incrementMetric('errors_total');
        this.recordEvent('recovery_failure', data);

        // Check for consecutive failures
        this.checkConsecutiveFailures(data);
        this.checkAlertConditions('recovery_failure', data);

        this.emit('recoveryFailed', {
            timestamp: Date.now(),
            error: data.error,
            attempts: data.attempts,
            strategy: data.strategy
        });
    }

    handleCircuitBreakerTrip(data) {
        this.incrementMetric('circuit_breaker_trips');
        this.recordEvent('circuit_breaker_trip', data);

        this.performanceMetrics.circuitBreakerStatus.set(data.breakerId, {
            state: 'open',
            timestamp: Date.now(),
            reason: data.reason
        });

        this.triggerAlert('circuit_breaker_trip', {
            severity: 'warning',
            message: `Circuit breaker ${data.breakerId} tripped`,
            details: data
        });

        this.emit('circuitBreakerTripped', data);
    }

    handleCheckpointCreated(data) {
        this.incrementMetric('checkpoints_created');
        this.recordEvent('checkpoint_created', data);
    }

    handlePatternDetected(data) {
        this.incrementMetric('pattern_detections');
        this.recordEvent('pattern_detected', data);

        if (data.severity === 'high') {
            this.triggerAlert('pattern_detected', {
                severity: 'warning',
                message: `High-severity error pattern detected: ${data.pattern}`,
                details: data
            });
        }
    }

    // Metrics Management
    incrementMetric(name, value = 1, labels = {}) {
        const metric = this.metrics.get(name) || this.createMetric(name);
        metric.value += value;
        metric.timestamp = Date.now();
        metric.labels = { ...metric.labels, ...labels };

        // Keep history (last 1000 data points)
        metric.history.push({
            value: metric.value,
            timestamp: metric.timestamp
        });

        if (metric.history.length > 1000) {
            metric.history.shift();
        }

        this.metrics.set(name, metric);
    }

    updateMetric(name, value, labels = {}) {
        const metric = this.metrics.get(name) || this.createMetric(name);

        // For average calculations
        if (name === 'average_recovery_time') {
            const history = this.performanceMetrics.recoveryTimes;
            if (history.length > 0) {
                const sum = history.reduce((acc, item) => acc + item.duration, 0);
                metric.value = sum / history.length;
            }
        } else {
            metric.value = value;
        }

        metric.timestamp = Date.now();
        metric.labels = { ...metric.labels, ...labels };

        metric.history.push({
            value: metric.value,
            timestamp: metric.timestamp
        });

        if (metric.history.length > 1000) {
            metric.history.shift();
        }

        this.metrics.set(name, metric);
    }

    createMetric(name) {
        return {
            value: 0,
            timestamp: Date.now(),
            history: [],
            labels: {}
        };
    }

    // Health Monitoring
    startHealthChecks() {
        setInterval(async () => {
            await this.performHealthCheck();
        }, this.config.metricsInterval);
    }

    async performHealthCheck() {
        try {
            const health = {
                timestamp: Date.now(),
                status: 'healthy',
                components: {},
                metrics: {}
            };

            // Check system resources
            const resourceUsage = await this.getResourceUsage();
            health.components.resources = {
                status: resourceUsage.memory < this.config.alertThresholds.memoryUsage ? 'healthy' : 'warning',
                memory: resourceUsage.memory,
                disk: resourceUsage.disk
            };

            // Check error recovery system
            const errorRate = this.calculateErrorRate();
            health.components.errorRecovery = {
                status: errorRate < this.config.alertThresholds.errorRate ? 'healthy' : 'warning',
                errorRate,
                averageRecoveryTime: this.getAverageRecoveryTime()
            };

            // Check circuit breakers
            const circuitBreakerStatus = this.getCircuitBreakerHealth();
            health.components.circuitBreakers = circuitBreakerStatus;

            // Calculate overall health
            const componentStatuses = Object.values(health.components).map(c => c.status);
            if (componentStatuses.includes('critical')) {
                health.status = 'critical';
            } else if (componentStatuses.includes('warning')) {
                health.status = 'warning';
            }

            this.healthStatus = health.status;
            this.emit('healthCheck', health);

            // Save health snapshot
            await this.saveHealthSnapshot(health);

        } catch (error) {
            console.error('Health check failed:', error);
            this.healthStatus = 'critical';
        }
    }

    // Alert System
    startAlertProcessing() {
        setInterval(async () => {
            await this.processAlerts();
        }, 5000); // Check alerts every 5 seconds
    }

    async checkAlertConditions(event, data) {
        const now = Date.now();

        // Check error rate
        const errorRate = this.calculateErrorRate();
        if (errorRate > this.config.alertThresholds.errorRate) {
            await this.triggerAlert('high_error_rate', {
                severity: 'warning',
                message: `High error rate detected: ${(errorRate * 100).toFixed(2)}%`,
                details: { errorRate, threshold: this.config.alertThresholds.errorRate }
            });
        }

        // Check recovery time
        if (data.duration && data.duration > this.config.alertThresholds.recoveryTime) {
            await this.triggerAlert('slow_recovery', {
                severity: 'warning',
                message: `Slow recovery detected: ${data.duration}ms`,
                details: { duration: data.duration, threshold: this.config.alertThresholds.recoveryTime }
            });
        }

        // Check resource usage
        const resourceUsage = await this.getResourceUsage();
        if (resourceUsage.memory > this.config.alertThresholds.memoryUsage) {
            await this.triggerAlert('high_memory_usage', {
                severity: 'warning',
                message: `High memory usage: ${(resourceUsage.memory * 100).toFixed(2)}%`,
                details: { usage: resourceUsage.memory, threshold: this.config.alertThresholds.memoryUsage }
            });
        }
    }

    async triggerAlert(type, alert) {
        const alertId = `${type}_${Date.now()}`;
        const fullAlert = {
            id: alertId,
            type,
            timestamp: Date.now(),
            status: 'active',
            ...alert
        };

        this.alerts.push(fullAlert);
        this.activeAlerts.set(alertId, fullAlert);
        this.alertHistory.push(fullAlert);

        // Emit alert event
        this.emit('alert', fullAlert);

        // Save alert
        await this.saveAlert(fullAlert);

        // Send real-time notification if enabled
        if (this.config.enableRealTimeAlerts) {
            await this.sendRealTimeAlert(fullAlert);
        }

        console.warn(`🚨 Alert triggered: ${alert.message}`);
    }

    async sendRealTimeAlert(alert) {
        // Implementation for real-time alerts (Slack, email, etc.)
        // This would integrate with notification services
        console.log(`📢 Real-time alert: ${alert.message}`);
    }

    async processAlerts() {
        const now = Date.now();
        const activeAlerts = Array.from(this.activeAlerts.values());

        for (const alert of activeAlerts) {
            // Auto-resolve alerts after 1 hour if conditions are met
            if (now - alert.timestamp > 60 * 60 * 1000) {
                if (await this.shouldResolveAlert(alert)) {
                    await this.resolveAlert(alert.id);
                }
            }
        }
    }

    async shouldResolveAlert(alert) {
        // Logic to determine if alert should be auto-resolved
        switch (alert.type) {
            case 'high_error_rate':
                return this.calculateErrorRate() <= this.config.alertThresholds.errorRate;
            case 'slow_recovery':
                return this.getAverageRecoveryTime() <= this.config.alertThresholds.recoveryTime;
            case 'high_memory_usage':
                const usage = await this.getResourceUsage();
                return usage.memory <= this.config.alertThresholds.memoryUsage;
            default:
                return false;
        }
    }

    async resolveAlert(alertId) {
        const alert = this.activeAlerts.get(alertId);
        if (alert) {
            alert.status = 'resolved';
            alert.resolvedAt = Date.now();
            this.activeAlerts.delete(alertId);

            await this.saveAlert(alert);
            this.emit('alertResolved', alert);

            console.log(`✅ Alert resolved: ${alert.message}`);
        }
    }

    // Metrics Collection
    startMetricsCollection() {
        setInterval(async () => {
            await this.collectMetrics();
        }, this.config.metricsInterval);
    }

    async collectMetrics() {
        try {
            const snapshot = {
                timestamp: Date.now(),
                metrics: {},
                performance: {},
                health: this.healthStatus
            };

            // Collect current metrics
            for (const [name, metric] of this.metrics.entries()) {
                snapshot.metrics[name] = {
                    value: metric.value,
                    timestamp: metric.timestamp,
                    labels: metric.labels
                };
            }

            // Collect performance metrics
            snapshot.performance = {
                errorRate: this.calculateErrorRate(),
                averageRecoveryTime: this.getAverageRecoveryTime(),
                throughput: this.calculateThroughput(),
                circuitBreakerStatus: Object.fromEntries(this.performanceMetrics.circuitBreakerStatus)
            };

            this.lastMetricsSnapshot = snapshot;

            // Save snapshot
            await this.saveMetricsSnapshot(snapshot);

            // Update dashboard data
            this.updateDashboardData(snapshot);

            this.emit('metricsCollected', snapshot);

        } catch (error) {
            console.error('Metrics collection failed:', error);
        }
    }

    // Calculations
    calculateErrorRate() {
        const totalErrors = this.metrics.get('errors_total')?.value || 0;
        const totalRecoveries = this.metrics.get('recoveries_total')?.value || 0;
        const total = totalErrors + totalRecoveries;

        return total > 0 ? totalErrors / total : 0;
    }

    getAverageRecoveryTime() {
        return this.metrics.get('average_recovery_time')?.value || 0;
    }

    calculateThroughput() {
        const now = Date.now();
        const oneHourAgo = now - 60 * 60 * 1000;

        const recentRecoveries = this.performanceMetrics.recoveryTimes.filter(
            item => item.timestamp > oneHourAgo
        );

        return recentRecoveries.length;
    }

    getCircuitBreakerHealth() {
        const status = { status: 'healthy', breakers: {} };

        for (const [id, breaker] of this.performanceMetrics.circuitBreakerStatus) {
            status.breakers[id] = breaker;
            if (breaker.state === 'open') {
                status.status = 'warning';
            }
        }

        return status;
    }

    checkConsecutiveFailures(data) {
        // Implementation to track consecutive failures
        const key = `${data.strategy}_${data.errorType}`;
        const failures = this.consecutiveFailures || new Map();

        const current = failures.get(key) || 0;
        failures.set(key, current + 1);

        if (current + 1 >= this.config.alertThresholds.consecutiveFailures) {
            this.triggerAlert('consecutive_failures', {
                severity: 'critical',
                message: `${current + 1} consecutive failures for ${key}`,
                details: { key, count: current + 1 }
            });
        }

        this.consecutiveFailures = failures;
    }

    // Resource Monitoring
    async getResourceUsage() {
        const usage = process.memoryUsage();
        const totalMemory = require('os').totalmem();

        return {
            memory: usage.heapUsed / totalMemory,
            disk: 0.5, // Placeholder - would implement actual disk usage check
            cpu: process.cpuUsage()
        };
    }

    // Data Persistence
    async saveMetricsSnapshot(snapshot) {
        const filename = `metrics_${Date.now()}.json`;
        const filepath = path.join(this.config.metricsDir, 'snapshots', filename);

        await fs.writeFile(filepath, JSON.stringify(snapshot, null, 2));

        // Cleanup old snapshots
        await this.cleanupOldFiles(path.join(this.config.metricsDir, 'snapshots'));
    }

    async saveAlert(alert) {
        const filename = `alert_${alert.id}.json`;
        const filepath = path.join(this.config.alertsDir, filename);

        await fs.writeFile(filepath, JSON.stringify(alert, null, 2));
    }

    async saveHealthSnapshot(health) {
        const filename = `health_${Date.now()}.json`;
        const filepath = path.join(this.config.logsDir, filename);

        await fs.writeFile(filepath, JSON.stringify(health, null, 2));

        // Keep only recent health snapshots
        await this.cleanupOldFiles(this.config.logsDir, 'health_*.json');
    }

    recordEvent(eventType, data) {
        const logEntry = {
            timestamp: Date.now(),
            eventType,
            data,
            level: this.getLogLevel(eventType)
        };

        // Write to structured log
        this.writeToLog('recovery.jsonl', logEntry);
    }

    async writeToLog(filename, entry) {
        const filepath = path.join(this.config.logsDir, 'recovery', filename);
        const logLine = JSON.stringify(entry) + '\n';

        await fs.appendFile(filepath, logLine);
    }

    getLogLevel(eventType) {
        switch (eventType) {
            case 'recovery_failure':
            case 'circuit_breaker_trip':
                return 'error';
            case 'pattern_detected':
                return 'warning';
            default:
                return 'info';
        }
    }

    // Dashboard Data
    updateDashboardData(snapshot) {
        this.dashboardData.set('current_metrics', snapshot.metrics);
        this.dashboardData.set('performance', snapshot.performance);
        this.dashboardData.set('alerts', Array.from(this.activeAlerts.values()));
        this.dashboardData.set('health', this.healthStatus);
        this.dashboardData.set('last_updated', snapshot.timestamp);
    }

    // Public API Methods
    getMetrics() {
        return Object.fromEntries(this.metrics);
    }

    getPerformanceMetrics() {
        return {
            ...this.performanceMetrics,
            errorRate: this.calculateErrorRate(),
            averageRecoveryTime: this.getAverageRecoveryTime(),
            throughput: this.calculateThroughput()
        };
    }

    getActiveAlerts() {
        return Array.from(this.activeAlerts.values());
    }

    getHealthStatus() {
        return {
            status: this.healthStatus,
            timestamp: Date.now(),
            metrics: this.lastMetricsSnapshot
        };
    }

    getDashboardData() {
        return Object.fromEntries(this.dashboardData);
    }

    // Cleanup
    async cleanupOldFiles(directory, pattern = '*', maxAge = this.config.retentionPeriod) {
        try {
            const files = await fs.readdir(directory);
            const now = Date.now();

            for (const file of files) {
                const filepath = path.join(directory, file);
                const stats = await fs.stat(filepath);

                if (now - stats.mtime.getTime() > maxAge) {
                    await fs.unlink(filepath);
                }
            }
        } catch (error) {
            console.error('Cleanup failed:', error);
        }
    }

    // Export methods
    async exportMetrics(format = 'json') {
        const metrics = this.getMetrics();
        const performance = this.getPerformanceMetrics();
        const alerts = this.getActiveAlerts();

        const exportData = {
            timestamp: Date.now(),
            metrics,
            performance,
            alerts,
            health: this.healthStatus
        };

        const filename = `metrics_export_${Date.now()}.${format}`;
        const filepath = path.join(this.config.metricsDir, 'exports', filename);

        if (format === 'json') {
            await fs.writeFile(filepath, JSON.stringify(exportData, null, 2));
        } else if (format === 'csv') {
            // Implement CSV export
            const csv = this.convertToCSV(exportData);
            await fs.writeFile(filepath, csv);
        }

        return filepath;
    }

    convertToCSV(data) {
        // Simple CSV conversion implementation
        const lines = ['timestamp,metric,value'];

        for (const [name, metric] of Object.entries(data.metrics)) {
            lines.push(`${data.timestamp},${name},${metric.value}`);
        }

        return lines.join('\n');
    }

    async shutdown() {
        console.log('🔄 Shutting down Error Recovery Monitor...');

        // Save final metrics snapshot
        if (this.lastMetricsSnapshot) {
            await this.saveMetricsSnapshot(this.lastMetricsSnapshot);
        }

        // Cleanup
        await this.cleanupOldFiles(path.join(this.config.metricsDir, 'snapshots'));
        await this.cleanupOldFiles(this.config.alertsDir);
        await this.cleanupOldFiles(this.config.logsDir);

        console.log('✅ Error Recovery Monitor shutdown complete');
    }
}

module.exports = ErrorRecoveryMonitor;