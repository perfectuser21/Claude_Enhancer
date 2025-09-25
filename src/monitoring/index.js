/**
 * Claude Enhancer 5.0 - Complete Monitoring System Integration
 * Main entry point for all monitoring and observability components
 */

const ErrorRecoveryMonitor = require('./ErrorRecoveryMonitor');
const PrometheusExporter = require('./PrometheusExporter');
const ErrorRecoveryDashboard = require('./ErrorRecoveryDashboard');
const AlertManager = require('./AlertManager');
const { EventEmitter } = require('events');

class MonitoringSystem extends EventEmitter {
    constructor(options = {}) {
        super();

        this.config = {
            monitoringEnabled: options.monitoringEnabled !== false,
            prometheusEnabled: options.prometheusEnabled !== false,
            dashboardEnabled: options.dashboardEnabled !== false,
            alertingEnabled: options.alertingEnabled !== false,

            // Directories
            dataDir: options.dataDir || './.claude/monitoring',
            metricsDir: options.metricsDir || './.claude/metrics',
            alertsDir: options.alertsDir || './.claude/alerts',
            logsDir: options.logsDir || './.claude/logs',

            // Ports
            prometheusPort: options.prometheusPort || 9090,
            dashboardPort: options.dashboardPort || 3001,

            // Intervals
            metricsInterval: options.metricsInterval || 30000,
            healthCheckInterval: options.healthCheckInterval || 60000,

            // Notification settings
            webhookUrl: options.webhookUrl,
            slackWebhookUrl: options.slackWebhookUrl,
            slackChannel: options.slackChannel || '#alerts',

            ...options
        };

        this.monitor = null;
        this.prometheusExporter = null;
        this.dashboard = null;
        this.alertManager = null;

        this.isInitialized = false;
        this.isRunning = false;
    }

    async initialize() {
        try {
            console.log('🚀 Initializing Error Recovery Monitoring System...');

            // Initialize core monitoring
            if (this.config.monitoringEnabled) {
                this.monitor = new ErrorRecoveryMonitor({
                    metricsDir: this.config.metricsDir,
                    alertsDir: this.config.alertsDir,
                    logsDir: this.config.logsDir,
                    metricsInterval: this.config.metricsInterval,
                    enableRealTimeAlerts: this.config.alertingEnabled,
                    enableDashboard: this.config.dashboardEnabled,
                    enableMetricsExport: this.config.prometheusEnabled
                });

                await this.monitor.initializeMonitoring();
            }

            // Initialize Prometheus exporter
            if (this.config.prometheusEnabled) {
                this.prometheusExporter = new PrometheusExporter({
                    port: this.config.prometheusPort,
                    enableHistograms: true
                });

                if (this.monitor) {
                    this.prometheusExporter.integrateWithMonitor(this.monitor);
                }

                await this.prometheusExporter.startServer();
            }

            // Initialize dashboard
            if (this.config.dashboardEnabled) {
                this.dashboard = new ErrorRecoveryDashboard({
                    port: this.config.dashboardPort,
                    updateInterval: 5000
                });

                if (this.monitor) {
                    this.dashboard.integrateWithMonitor(this.monitor);
                }

                await this.dashboard.startServer();
            }

            // Initialize alert manager
            if (this.config.alertingEnabled) {
                this.alertManager = new AlertManager({
                    alertsDir: this.config.alertsDir,
                    webhookUrl: this.config.webhookUrl,
                    slackWebhookUrl: this.config.slackWebhookUrl,
                    slackChannel: this.config.slackChannel,
                    enableSmartGrouping: true,
                    batchingInterval: 30000
                });

                // Integrate with monitor
                if (this.monitor) {
                    this.integrateAlertingWithMonitoring();
                }
            }

            // Setup cross-component integration
            this.setupIntegrations();

            this.isInitialized = true;
            this.isRunning = true;

            console.log('✅ Error Recovery Monitoring System initialized successfully');
            this.emitSystemStatus();

        } catch (error) {
            console.error('❌ Failed to initialize monitoring system:', error);
            throw error;
        }
    }

    setupIntegrations() {
        // Monitoring events to alert manager
        if (this.monitor && this.alertManager) {
            this.monitor.on('alert', (alert) => {
                this.alertManager.processAlert(alert);
            });

            this.monitor.on('metricsCollected', (snapshot) => {
                this.alertManager.evaluateAlertRules(snapshot.performance);
                this.alertManager.autoResolveAlerts(snapshot.performance);
            });
        }

        // Forward events to main system
        const components = [this.monitor, this.prometheusExporter, this.dashboard, this.alertManager].filter(Boolean);

        for (const component of components) {
            component.on('error', (error) => {
                this.emit('componentError', { component: component.constructor.name, error });
            });
        }

        // Health check integration
        setInterval(() => {
            this.performSystemHealthCheck();
        }, this.config.healthCheckInterval);
    }

    integrateAlertingWithMonitoring() {
        // Set up specific integrations between monitoring and alerting
        this.monitor.on('recoveryFailed', (data) => {
            this.alertManager.processAlert({
                type: 'recovery_failure',
                severity: 'warning',
                message: `Recovery failed for ${data.errorType}`,
                description: `Recovery attempt failed after ${data.attempts} attempts using ${data.strategy} strategy`,
                details: data
            });
        });

        this.monitor.on('circuitBreakerTripped', (data) => {
            this.alertManager.processAlert({
                type: 'circuit_breaker_open',
                severity: 'critical',
                message: `Circuit breaker ${data.breakerId} tripped`,
                description: `Circuit breaker opened due to: ${data.reason}`,
                details: data
            });
        });

        this.monitor.on('healthCheck', (health) => {
            if (health.status === 'critical') {
                this.alertManager.processAlert({
                    type: 'system_health_critical',
                    severity: 'critical',
                    message: 'System health is critical',
                    description: 'Multiple system components are showing critical status',
                    details: health
                });
            }
        });
    }

    // Integration with Error Recovery System
    integrateWithErrorRecovery(errorRecoverySystem) {
        if (!this.isInitialized) {
            console.warn('Monitoring system not initialized');
            return;
        }

        // Hook into error recovery events
        errorRecoverySystem.on('recoveryStarted', (data) => {
            this.recordEvent('recovery_started', data);
        });

        errorRecoverySystem.on('recoverySuccess', (data) => {
            this.recordEvent('recovery_success', data);
        });

        errorRecoverySystem.on('recoveryFailure', (data) => {
            this.recordEvent('recovery_failure', data);
        });

        errorRecoverySystem.on('circuitBreakerTrip', (data) => {
            this.recordEvent('circuit_breaker_trip', data);
        });

        errorRecoverySystem.on('checkpointCreated', (data) => {
            this.recordEvent('checkpoint_created', data);
        });

        errorRecoverySystem.on('patternDetected', (data) => {
            this.recordEvent('pattern_detected', data);
        });

        console.log('✅ Integrated monitoring with error recovery system');
    }

    recordEvent(eventType, data) {
        const event = {
            timestamp: Date.now(),
            type: eventType,
            data: data
        };

        // Forward to all monitoring components
        if (this.monitor) {
            process.emit(`errorRecovery:${eventType}`, data);
        }

        this.emit('eventRecorded', event);
    }

    // System Health and Status
    async performSystemHealthCheck() {
        const healthStatus = {
            timestamp: Date.now(),
            overall: 'healthy',
            components: {},
            metrics: {}
        };

        // Check each component
        if (this.monitor) {
            const monitorHealth = this.monitor.getHealthStatus();
            healthStatus.components.monitor = monitorHealth;
        }

        if (this.prometheusExporter) {
            const prometheusStatus = this.prometheusExporter.getStatus();
            healthStatus.components.prometheus = {
                status: prometheusStatus.running ? 'healthy' : 'critical',
                running: prometheusStatus.running,
                port: prometheusStatus.port
            };
        }

        if (this.dashboard) {
            const dashboardStatus = this.dashboard.getStatus();
            healthStatus.components.dashboard = {
                status: dashboardStatus.running ? 'healthy' : 'critical',
                running: dashboardStatus.running,
                port: dashboardStatus.port,
                clients: dashboardStatus.clients
            };
        }

        if (this.alertManager) {
            const alertStats = this.alertManager.getStatistics();
            healthStatus.components.alerting = {
                status: 'healthy',
                activeAlerts: alertStats.activeAlerts,
                totalAlerts: alertStats.totalAlerts
            };
        }

        // Calculate overall health
        const componentStatuses = Object.values(healthStatus.components).map(c => c.status);
        if (componentStatuses.includes('critical')) {
            healthStatus.overall = 'critical';
        } else if (componentStatuses.includes('warning')) {
            healthStatus.overall = 'warning';
        }

        this.emit('healthCheck', healthStatus);
        return healthStatus;
    }

    getSystemStatus() {
        return {
            initialized: this.isInitialized,
            running: this.isRunning,
            components: {
                monitor: !!this.monitor,
                prometheus: !!this.prometheusExporter,
                dashboard: !!this.dashboard,
                alertManager: !!this.alertManager
            },
            config: {
                monitoringEnabled: this.config.monitoringEnabled,
                prometheusEnabled: this.config.prometheusEnabled,
                dashboardEnabled: this.config.dashboardEnabled,
                alertingEnabled: this.config.alertingEnabled,
                prometheusPort: this.config.prometheusPort,
                dashboardPort: this.config.dashboardPort
            }
        };
    }

    // Metrics API
    getMetrics() {
        if (!this.monitor) return {};
        return this.monitor.getMetrics();
    }

    getPerformanceMetrics() {
        if (!this.monitor) return {};
        return this.monitor.getPerformanceMetrics();
    }

    getActiveAlerts() {
        if (!this.alertManager) return [];
        return this.alertManager.getActiveAlerts();
    }

    // Dashboard and Prometheus URLs
    getUrls() {
        const urls = {};

        if (this.dashboard && this.config.dashboardEnabled) {
            urls.dashboard = `http://localhost:${this.config.dashboardPort}`;
        }

        if (this.prometheusExporter && this.config.prometheusEnabled) {
            urls.metrics = `http://localhost:${this.config.prometheusPort}/metrics`;
        }

        return urls;
    }

    emitSystemStatus() {
        const status = this.getSystemStatus();
        const urls = this.getUrls();

        console.log('\n📊 Error Recovery Monitoring System Status:');
        console.log(`   Status: ${status.running ? '🟢 Running' : '🔴 Stopped'}`);

        if (urls.dashboard) {
            console.log(`   📈 Dashboard: ${urls.dashboard}`);
        }

        if (urls.metrics) {
            console.log(`   📊 Metrics: ${urls.metrics}`);
        }

        console.log(`   📁 Data Directory: ${this.config.dataDir}`);
        console.log(`   ⏱️  Metrics Interval: ${this.config.metricsInterval}ms`);
        console.log('');
    }

    // Manual alert creation
    async triggerAlert(alertData) {
        if (!this.alertManager) {
            console.warn('Alert manager not available');
            return;
        }

        return await this.alertManager.processAlert(alertData);
    }

    // Alert management
    async resolveAlert(alertId, resolvedBy = 'user') {
        if (!this.alertManager) return false;
        return await this.alertManager.resolveAlert(alertId, resolvedBy);
    }

    silenceAlert(alertId, duration) {
        if (!this.alertManager) return;
        this.alertManager.silenceAlert(alertId, duration);
    }

    // Data export
    async exportMetrics(format = 'json') {
        if (!this.monitor) return null;
        return await this.monitor.exportMetrics(format);
    }

    // Cleanup and shutdown
    async shutdown() {
        console.log('🔄 Shutting down Error Recovery Monitoring System...');

        this.isRunning = false;

        const shutdownPromises = [];

        if (this.alertManager) {
            shutdownPromises.push(this.alertManager.shutdown());
        }

        if (this.dashboard) {
            shutdownPromises.push(this.dashboard.stopServer());
        }

        if (this.prometheusExporter) {
            shutdownPromises.push(this.prometheusExporter.stopServer());
        }

        if (this.monitor) {
            shutdownPromises.push(this.monitor.shutdown());
        }

        await Promise.all(shutdownPromises);

        console.log('✅ Error Recovery Monitoring System shutdown complete');
    }
}

// Factory functions for individual components
function createMonitor(options = {}) {
    return new ErrorRecoveryMonitor(options);
}

function createPrometheusExporter(options = {}) {
    return new PrometheusExporter(options);
}

function createDashboard(options = {}) {
    return new ErrorRecoveryDashboard(options);
}

function createAlertManager(options = {}) {
    return new AlertManager(options);
}

// Quick setup function for common configurations
async function setupMonitoring(options = {}) {
    const monitoring = new MonitoringSystem(options);
    await monitoring.initialize();
    return monitoring;
}

module.exports = {
    MonitoringSystem,
    ErrorRecoveryMonitor,
    PrometheusExporter,
    ErrorRecoveryDashboard,
    AlertManager,

    // Factory functions
    createMonitor,
    createPrometheusExporter,
    createDashboard,
    createAlertManager,

    // Quick setup
    setupMonitoring
};