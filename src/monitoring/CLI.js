#!/usr/bin/env node

/**
 * Claude Enhancer 5.0 - Monitoring CLI
 *
 * Command-line interface for managing the monitoring system:
 * - Start/stop dashboard components
 * - View metrics and alerts
 * - Configure monitoring settings
 * - Export and import data
 * - System health checks
 *
 * @author Claude Code
 * @version 1.0.0
 */

const { Command } = require('commander');
const MetricsCollector = require('./MetricsCollector');
const WebDashboard = require('./WebDashboard');
const AlertManager = require('./AlertManager');
const ClaudeEnhancerDashboard = require('./Dashboard');
const fs = require('fs').promises;
const path = require('path');
const pkg = require('./package.json');

class MonitoringCLI {
    constructor() {
        this.program = new Command();
        this.setupCommands();
    }

    /**
     * Setup CLI commands
     */
    setupCommands() {
        this.program
            .name('claude-monitor')
            .description('Claude Enhancer 5.0 Monitoring System')
            .version(pkg.version);

        // Dashboard commands
        this.setupDashboardCommands();

        // Metrics commands
        this.setupMetricsCommands();

        // Alert commands
        this.setupAlertCommands();

        // Configuration commands
        this.setupConfigCommands();

        // Utility commands
        this.setupUtilityCommands();
    }

    /**
     * Setup dashboard commands
     */
    setupDashboardCommands() {
        const dashboard = this.program
            .command('dashboard')
            .alias('dash')
            .description('Dashboard management commands');

        // Start CLI dashboard
        dashboard
            .command('start')
            .alias('s')
            .description('Start the CLI dashboard')
            .option('-r, --refresh <ms>', 'Refresh rate in milliseconds', '1000')
            .option('-d, --data-retention <hours>', 'Data retention in hours', '24')
            .action(async (options) => {
                try {
                    console.log('🚀 Starting Claude Enhancer 5.0 CLI Dashboard...\n');

                    const dashboardOptions = {
                        refreshRate: parseInt(options.refresh),
                        dataRetention: parseInt(options.dataRetention) * 60 * 60 * 1000
                    };

                    const dashboard = new ClaudeEnhancerDashboard(dashboardOptions);
                    dashboard.start();

                } catch (error) {
                    console.error('❌ Failed to start CLI dashboard:', error.message);
                    process.exit(1);
                }
            });

        // Start web dashboard
        dashboard
            .command('web')
            .alias('w')
            .description('Start the web dashboard')
            .option('-p, --port <port>', 'Server port', '3000')
            .option('-h, --host <host>', 'Server host', 'localhost')
            .option('-r, --refresh <ms>', 'Refresh rate in milliseconds', '1000')
            .action(async (options) => {
                try {
                    console.log('🌐 Starting Claude Enhancer 5.0 Web Dashboard...\n');

                    const webDashboard = new WebDashboard({
                        port: parseInt(options.port),
                        host: options.host,
                        updateInterval: parseInt(options.refresh)
                    });

                    await webDashboard.start();

                    console.log(`✅ Web Dashboard started successfully!`);
                    console.log(`📊 Dashboard URL: http://${options.host}:${options.port}`);
                    console.log(`📡 WebSocket URL: ws://${options.host}:${options.port}`);
                    console.log(`\nPress Ctrl+C to stop the server`);

                    // Handle graceful shutdown
                    process.on('SIGINT', async () => {
                        console.log('\n🛑 Stopping web dashboard...');
                        await webDashboard.stop();
                        process.exit(0);
                    });

                } catch (error) {
                    console.error('❌ Failed to start web dashboard:', error.message);
                    process.exit(1);
                }
            });

        // Dashboard status
        dashboard
            .command('status')
            .description('Check dashboard status')
            .action(async () => {
                try {
                    const status = await this.getDashboardStatus();
                    this.displayStatus(status);
                } catch (error) {
                    console.error('❌ Failed to get dashboard status:', error.message);
                    process.exit(1);
                }
            });
    }

    /**
     * Setup metrics commands
     */
    setupMetricsCommands() {
        const metrics = this.program
            .command('metrics')
            .alias('m')
            .description('Metrics management commands');

        // Start metrics collector
        metrics
            .command('collect')
            .alias('c')
            .description('Start metrics collection')
            .option('-i, --interval <ms>', 'Collection interval in milliseconds', '1000')
            .option('-s, --storage <dir>', 'Storage directory', '.claude/logs')
            .action(async (options) => {
                try {
                    console.log('📊 Starting metrics collection...\n');

                    const collector = new MetricsCollector({
                        collectInterval: parseInt(options.interval),
                        storageDir: path.resolve(options.storage)
                    });

                    collector.on('metric', (name, data) => {
                        console.log(`[${new Date().toISOString()}] ${name}:`,
                            JSON.stringify(data, null, 2));
                    });

                    collector.on('error', (message, error) => {
                        console.error(`❌ ${message}:`, error);
                    });

                    collector.start();

                    console.log('✅ Metrics collection started');
                    console.log('Press Ctrl+C to stop collection\n');

                    // Handle graceful shutdown
                    process.on('SIGINT', () => {
                        console.log('\n🛑 Stopping metrics collection...');
                        collector.stop();
                        process.exit(0);
                    });

                } catch (error) {
                    console.error('❌ Failed to start metrics collection:', error.message);
                    process.exit(1);
                }
            });

        // View metrics
        metrics
            .command('view [metric]')
            .alias('v')
            .description('View collected metrics')
            .option('-s, --since <timestamp>', 'Show metrics since timestamp')
            .option('-l, --limit <count>', 'Limit number of results', '10')
            .option('-f, --format <format>', 'Output format (json|table)', 'table')
            .action(async (metric, options) => {
                try {
                    const since = options.since ? parseInt(options.since) : Date.now() - 3600000;
                    const limit = parseInt(options.limit);

                    const metricsData = await this.getMetrics(metric, since, limit);

                    if (options.format === 'json') {
                        console.log(JSON.stringify(metricsData, null, 2));
                    } else {
                        this.displayMetricsTable(metricsData, metric);
                    }

                } catch (error) {
                    console.error('❌ Failed to view metrics:', error.message);
                    process.exit(1);
                }
            });

        // Export metrics
        metrics
            .command('export [filename]')
            .alias('e')
            .description('Export metrics to file')
            .option('-s, --since <timestamp>', 'Export metrics since timestamp')
            .option('-u, --until <timestamp>', 'Export metrics until timestamp')
            .option('-m, --metrics <names>', 'Comma-separated list of metrics to export')
            .action(async (filename, options) => {
                try {
                    const exportOptions = {
                        since: options.since ? parseInt(options.since) : 0,
                        until: options.until ? parseInt(options.until) : Date.now(),
                        metrics: options.metrics ? options.metrics.split(',') : null
                    };

                    const exportFile = await this.exportMetrics(filename, exportOptions);
                    console.log(`✅ Metrics exported to: ${exportFile}`);

                } catch (error) {
                    console.error('❌ Failed to export metrics:', error.message);
                    process.exit(1);
                }
            });
    }

    /**
     * Setup alert commands
     */
    setupAlertCommands() {
        const alerts = this.program
            .command('alerts')
            .alias('a')
            .description('Alert management commands');

        // Start alert manager
        alerts
            .command('start')
            .description('Start alert manager')
            .option('-c, --config <file>', 'Configuration file')
            .action(async (options) => {
                try {
                    console.log('🚨 Starting Alert Manager...\n');

                    let config = {};
                    if (options.config) {
                        const configData = await fs.readFile(options.config, 'utf8');
                        config = JSON.parse(configData);
                    }

                    const alertManager = new AlertManager(config);

                    alertManager.on('alert-created', (alert, group) => {
                        console.log(`🆕 Alert created: ${alert.title} (${alert.severity})`);
                    });

                    alertManager.on('alert-escalated', (alert, group) => {
                        console.log(`⬆️ Alert escalated: ${alert.title}`);
                    });

                    alertManager.on('notification-sent', (channel, alert) => {
                        console.log(`📤 Notification sent via ${channel.type}`);
                    });

                    console.log('✅ Alert Manager started');
                    console.log('Press Ctrl+C to stop\n');

                    // Handle graceful shutdown
                    process.on('SIGINT', () => {
                        console.log('\n🛑 Stopping Alert Manager...');
                        alertManager.stop();
                        process.exit(0);
                    });

                } catch (error) {
                    console.error('❌ Failed to start Alert Manager:', error.message);
                    process.exit(1);
                }
            });

        // List alerts
        alerts
            .command('list')
            .alias('ls')
            .description('List active alerts')
            .option('-s, --severity <level>', 'Filter by severity')
            .option('-c, --category <category>', 'Filter by category')
            .option('-a, --acknowledged', 'Show only acknowledged alerts')
            .option('-u, --unacknowledged', 'Show only unacknowledged alerts')
            .option('-f, --format <format>', 'Output format (json|table)', 'table')
            .action(async (options) => {
                try {
                    const filters = {
                        severity: options.severity,
                        category: options.category,
                        acknowledged: options.acknowledged ? true : options.unacknowledged ? false : undefined
                    };

                    const alerts = await this.getAlerts(filters);

                    if (options.format === 'json') {
                        console.log(JSON.stringify(alerts, null, 2));
                    } else {
                        this.displayAlertsTable(alerts);
                    }

                } catch (error) {
                    console.error('❌ Failed to list alerts:', error.message);
                    process.exit(1);
                }
            });

        // Send test alert
        alerts
            .command('test')
            .description('Send test alert')
            .option('-s, --severity <level>', 'Alert severity', 'warning')
            .option('-t, --title <title>', 'Alert title', 'Test Alert')
            .option('-m, --message <message>', 'Alert message', 'This is a test alert')
            .action(async (options) => {
                try {
                    const testAlert = {
                        title: options.title,
                        message: options.message,
                        severity: options.severity,
                        source: 'cli',
                        category: 'test'
                    };

                    const alertManager = new AlertManager();
                    const alert = await alertManager.processAlert(testAlert);

                    console.log(`✅ Test alert sent: ${alert.id}`);

                } catch (error) {
                    console.error('❌ Failed to send test alert:', error.message);
                    process.exit(1);
                }
            });

        // Acknowledge alert
        alerts
            .command('ack <alertId>')
            .description('Acknowledge an alert')
            .option('-u, --user <user>', 'User acknowledging the alert', 'cli-user')
            .action(async (alertId, options) => {
                try {
                    const alertManager = new AlertManager();
                    await alertManager.acknowledgeAlert(alertId, options.user);
                    console.log(`✅ Alert ${alertId} acknowledged`);

                } catch (error) {
                    console.error('❌ Failed to acknowledge alert:', error.message);
                    process.exit(1);
                }
            });

        // Resolve alert
        alerts
            .command('resolve <alertId>')
            .description('Resolve an alert')
            .option('-u, --user <user>', 'User resolving the alert', 'cli-user')
            .option('-r, --resolution <text>', 'Resolution description')
            .action(async (alertId, options) => {
                try {
                    const alertManager = new AlertManager();
                    await alertManager.resolveAlert(alertId, options.user, options.resolution);
                    console.log(`✅ Alert ${alertId} resolved`);

                } catch (error) {
                    console.error('❌ Failed to resolve alert:', error.message);
                    process.exit(1);
                }
            });
    }

    /**
     * Setup configuration commands
     */
    setupConfigCommands() {
        const config = this.program
            .command('config')
            .alias('cfg')
            .description('Configuration management commands');

        // Show configuration
        config
            .command('show')
            .description('Show current configuration')
            .option('-f, --format <format>', 'Output format (json|yaml)', 'json')
            .action(async (options) => {
                try {
                    const configuration = await this.getConfiguration();

                    if (options.format === 'yaml') {
                        // Simple YAML-like output
                        console.log(this.formatAsYAML(configuration));
                    } else {
                        console.log(JSON.stringify(configuration, null, 2));
                    }

                } catch (error) {
                    console.error('❌ Failed to show configuration:', error.message);
                    process.exit(1);
                }
            });

        // Set configuration value
        config
            .command('set <key> <value>')
            .description('Set configuration value')
            .action(async (key, value) => {
                try {
                    await this.setConfiguration(key, value);
                    console.log(`✅ Configuration updated: ${key} = ${value}`);

                } catch (error) {
                    console.error('❌ Failed to set configuration:', error.message);
                    process.exit(1);
                }
            });

        // Validate configuration
        config
            .command('validate')
            .description('Validate configuration')
            .action(async () => {
                try {
                    const validation = await this.validateConfiguration();

                    if (validation.valid) {
                        console.log('✅ Configuration is valid');
                    } else {
                        console.log('❌ Configuration validation failed:');
                        validation.errors.forEach(error => {
                            console.log(`   • ${error}`);
                        });
                        process.exit(1);
                    }

                } catch (error) {
                    console.error('❌ Failed to validate configuration:', error.message);
                    process.exit(1);
                }
            });
    }

    /**
     * Setup utility commands
     */
    setupUtilityCommands() {
        // Health check
        this.program
            .command('health')
            .alias('h')
            .description('Perform system health check')
            .option('-d, --detailed', 'Show detailed health information')
            .action(async (options) => {
                try {
                    const health = await this.performHealthCheck(options.detailed);
                    this.displayHealthStatus(health);

                    if (!health.overall.healthy) {
                        process.exit(1);
                    }

                } catch (error) {
                    console.error('❌ Health check failed:', error.message);
                    process.exit(1);
                }
            });

        // System information
        this.program
            .command('info')
            .alias('i')
            .description('Show system information')
            .action(async () => {
                try {
                    const info = await this.getSystemInfo();
                    this.displaySystemInfo(info);

                } catch (error) {
                    console.error('❌ Failed to get system info:', error.message);
                    process.exit(1);
                }
            });

        // Cleanup command
        this.program
            .command('cleanup')
            .description('Cleanup old data and logs')
            .option('-d, --days <days>', 'Keep data newer than N days', '7')
            .option('--dry-run', 'Show what would be cleaned without actually deleting')
            .action(async (options) => {
                try {
                    const result = await this.performCleanup(
                        parseInt(options.days),
                        options.dryRun
                    );

                    this.displayCleanupResult(result);

                } catch (error) {
                    console.error('❌ Cleanup failed:', error.message);
                    process.exit(1);
                }
            });
    }

    /**
     * Get dashboard status
     */
    async getDashboardStatus() {
        try {
            // Check if web dashboard is running
            const response = await fetch('http://localhost:3000/health');
            const webStatus = response.ok ? 'running' : 'stopped';

            return {
                web: webStatus,
                cli: 'available',
                lastCheck: new Date().toISOString()
            };

        } catch (error) {
            return {
                web: 'stopped',
                cli: 'available',
                lastCheck: new Date().toISOString()
            };
        }
    }

    /**
     * Get metrics data
     */
    async getMetrics(metricName, since, limit) {
        try {
            const collector = new MetricsCollector();

            if (metricName) {
                return collector.getMetric(metricName, since).slice(-limit);
            } else {
                const allMetrics = collector.getAllMetrics(since);
                const result = {};

                for (const [name, data] of Object.entries(allMetrics)) {
                    result[name] = data.slice(-limit);
                }

                return result;
            }

        } catch (error) {
            throw new Error(`Failed to get metrics: ${error.message}`);
        }
    }

    /**
     * Export metrics
     */
    async exportMetrics(filename, options) {
        try {
            const collector = new MetricsCollector();
            const exportFile = await collector.exportMetrics(filename);
            return exportFile;

        } catch (error) {
            throw new Error(`Failed to export metrics: ${error.message}`);
        }
    }

    /**
     * Get alerts
     */
    async getAlerts(filters) {
        try {
            const alertManager = new AlertManager();
            return alertManager.getActiveAlerts(filters);

        } catch (error) {
            throw new Error(`Failed to get alerts: ${error.message}`);
        }
    }

    /**
     * Get configuration
     */
    async getConfiguration() {
        try {
            const configFile = path.join(process.cwd(), '.claude/logs/monitoring_config.json');

            try {
                const configData = await fs.readFile(configFile, 'utf8');
                return JSON.parse(configData);
            } catch (fileError) {
                return {
                    dashboard: {
                        refreshRate: 1000,
                        dataRetention: 86400000
                    },
                    metrics: {
                        collectInterval: 1000,
                        storageDir: '.claude/logs'
                    },
                    alerts: {
                        channels: {},
                        rules: {}
                    }
                };
            }

        } catch (error) {
            throw new Error(`Failed to get configuration: ${error.message}`);
        }
    }

    /**
     * Set configuration value
     */
    async setConfiguration(key, value) {
        try {
            const config = await this.getConfiguration();

            // Parse key path (e.g., "dashboard.refreshRate")
            const keyParts = key.split('.');
            let current = config;

            for (let i = 0; i < keyParts.length - 1; i++) {
                if (!current[keyParts[i]]) {
                    current[keyParts[i]] = {};
                }
                current = current[keyParts[i]];
            }

            // Try to parse value as number or boolean
            let parsedValue = value;
            if (!isNaN(value)) {
                parsedValue = Number(value);
            } else if (value === 'true' || value === 'false') {
                parsedValue = value === 'true';
            }

            current[keyParts[keyParts.length - 1]] = parsedValue;

            // Save configuration
            const configFile = path.join(process.cwd(), '.claude/logs/monitoring_config.json');
            await fs.writeFile(configFile, JSON.stringify(config, null, 2));

        } catch (error) {
            throw new Error(`Failed to set configuration: ${error.message}`);
        }
    }

    /**
     * Validate configuration
     */
    async validateConfiguration() {
        try {
            const config = await this.getConfiguration();
            const errors = [];

            // Validate dashboard config
            if (config.dashboard) {
                if (config.dashboard.refreshRate < 100) {
                    errors.push('dashboard.refreshRate must be at least 100ms');
                }
                if (config.dashboard.dataRetention < 60000) {
                    errors.push('dashboard.dataRetention must be at least 1 minute');
                }
            }

            // Validate metrics config
            if (config.metrics) {
                if (config.metrics.collectInterval < 100) {
                    errors.push('metrics.collectInterval must be at least 100ms');
                }
            }

            return {
                valid: errors.length === 0,
                errors
            };

        } catch (error) {
            throw new Error(`Failed to validate configuration: ${error.message}`);
        }
    }

    /**
     * Perform health check
     */
    async performHealthCheck(detailed = false) {
        const health = {
            overall: { healthy: true, issues: [] },
            components: {}
        };

        try {
            // Check storage directory
            const storageDir = path.join(process.cwd(), '.claude/logs');
            try {
                await fs.access(storageDir);
                health.components.storage = { status: 'healthy' };
            } catch (error) {
                health.components.storage = { status: 'error', message: 'Storage directory not accessible' };
                health.overall.healthy = false;
                health.overall.issues.push('Storage directory issues');
            }

            // Check configuration
            try {
                const validation = await this.validateConfiguration();
                health.components.config = {
                    status: validation.valid ? 'healthy' : 'warning',
                    errors: validation.errors
                };
                if (!validation.valid) {
                    health.overall.issues.push('Configuration validation issues');
                }
            } catch (error) {
                health.components.config = { status: 'error', message: error.message };
                health.overall.healthy = false;
                health.overall.issues.push('Configuration errors');
            }

            // Check system resources
            if (detailed) {
                const memUsage = process.memoryUsage();
                health.components.resources = {
                    status: 'healthy',
                    memory: {
                        rss: Math.round(memUsage.rss / 1024 / 1024) + ' MB',
                        heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024) + ' MB',
                        heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024) + ' MB'
                    },
                    uptime: Math.round(process.uptime()) + ' seconds'
                };
            }

        } catch (error) {
            health.overall.healthy = false;
            health.overall.issues.push(`Health check error: ${error.message}`);
        }

        return health;
    }

    /**
     * Get system information
     */
    async getSystemInfo() {
        const os = require('os');

        return {
            system: {
                platform: os.platform(),
                arch: os.arch(),
                version: os.version(),
                hostname: os.hostname(),
                uptime: Math.round(os.uptime()) + ' seconds'
            },
            process: {
                nodeVersion: process.version,
                pid: process.pid,
                uptime: Math.round(process.uptime()) + ' seconds',
                memory: process.memoryUsage(),
                cwd: process.cwd()
            },
            monitoring: {
                version: pkg.version,
                storageDir: path.join(process.cwd(), '.claude/logs')
            }
        };
    }

    /**
     * Perform cleanup
     */
    async performCleanup(days, dryRun = false) {
        const cutoff = Date.now() - (days * 24 * 60 * 60 * 1000);
        const storageDir = path.join(process.cwd(), '.claude/logs');
        const result = {
            scanned: 0,
            cleaned: 0,
            freed: 0,
            errors: []
        };

        try {
            const files = await fs.readdir(storageDir);

            for (const file of files) {
                const filePath = path.join(storageDir, file);

                try {
                    const stats = await fs.stat(filePath);
                    result.scanned++;

                    if (stats.mtime.getTime() < cutoff) {
                        if (!dryRun) {
                            await fs.unlink(filePath);
                        }
                        result.cleaned++;
                        result.freed += stats.size;
                    }

                } catch (fileError) {
                    result.errors.push(`Error processing ${file}: ${fileError.message}`);
                }
            }

        } catch (error) {
            result.errors.push(`Cleanup error: ${error.message}`);
        }

        return result;
    }

    /**
     * Display methods for CLI output
     */

    displayStatus(status) {
        console.log('📊 Dashboard Status');
        console.log('─'.repeat(30));
        console.log(`Web Dashboard:  ${status.web === 'running' ? '✅ Running' : '❌ Stopped'}`);
        console.log(`CLI Dashboard:  ${status.cli === 'available' ? '✅ Available' : '❌ Unavailable'}`);
        console.log(`Last Check:     ${new Date(status.lastCheck).toLocaleString()}`);
    }

    displayMetricsTable(metricsData, metricName) {
        if (metricName) {
            console.log(`📈 Metric: ${metricName}`);
            console.log('─'.repeat(80));

            if (!metricsData || metricsData.length === 0) {
                console.log('No data available');
                return;
            }

            metricsData.forEach(entry => {
                const timestamp = new Date(entry.timestamp).toLocaleString();
                console.log(`${timestamp}: ${JSON.stringify(entry.data, null, 2)}`);
            });

        } else {
            console.log('📈 All Metrics');
            console.log('─'.repeat(80));

            for (const [name, data] of Object.entries(metricsData)) {
                console.log(`\n${name}: ${data.length} entries`);
                if (data.length > 0) {
                    const latest = data[data.length - 1];
                    const timestamp = new Date(latest.timestamp).toLocaleString();
                    console.log(`  Latest (${timestamp}): ${JSON.stringify(latest.data, null, 2)}`);
                }
            }
        }
    }

    displayAlertsTable(alerts) {
        console.log('🚨 Active Alerts');
        console.log('─'.repeat(100));

        if (alerts.length === 0) {
            console.log('No active alerts');
            return;
        }

        console.log(sprintf('%-12s %-8s %-15s %-30s %-25s',
            'ID', 'Severity', 'Source', 'Title', 'Timestamp'));
        console.log('─'.repeat(100));

        alerts.forEach(alert => {
            const timestamp = new Date(alert.timestamp).toLocaleString();
            console.log(sprintf('%-12s %-8s %-15s %-30s %-25s',
                alert.id.substring(0, 12),
                alert.severity,
                alert.source,
                alert.title.substring(0, 30),
                timestamp
            ));
        });
    }

    displayHealthStatus(health) {
        console.log('🏥 System Health Check');
        console.log('─'.repeat(50));

        const overallStatus = health.overall.healthy ? '✅ Healthy' : '❌ Issues Detected';
        console.log(`Overall Status: ${overallStatus}`);

        if (health.overall.issues.length > 0) {
            console.log('\nIssues:');
            health.overall.issues.forEach(issue => {
                console.log(`  • ${issue}`);
            });
        }

        console.log('\nComponents:');
        for (const [component, status] of Object.entries(health.components)) {
            const statusIcon = status.status === 'healthy' ? '✅' :
                             status.status === 'warning' ? '⚠️' : '❌';
            console.log(`  ${statusIcon} ${component}: ${status.status}`);

            if (status.message) {
                console.log(`     ${status.message}`);
            }

            if (status.errors && status.errors.length > 0) {
                status.errors.forEach(error => {
                    console.log(`     • ${error}`);
                });
            }
        }
    }

    displaySystemInfo(info) {
        console.log('ℹ️  System Information');
        console.log('─'.repeat(50));

        console.log('\nSystem:');
        for (const [key, value] of Object.entries(info.system)) {
            console.log(`  ${key}: ${value}`);
        }

        console.log('\nProcess:');
        for (const [key, value] of Object.entries(info.process)) {
            if (typeof value === 'object') {
                console.log(`  ${key}:`);
                for (const [subKey, subValue] of Object.entries(value)) {
                    console.log(`    ${subKey}: ${subValue}`);
                }
            } else {
                console.log(`  ${key}: ${value}`);
            }
        }

        console.log('\nMonitoring:');
        for (const [key, value] of Object.entries(info.monitoring)) {
            console.log(`  ${key}: ${value}`);
        }
    }

    displayCleanupResult(result) {
        console.log('🧹 Cleanup Results');
        console.log('─'.repeat(30));
        console.log(`Files Scanned: ${result.scanned}`);
        console.log(`Files Cleaned: ${result.cleaned}`);
        console.log(`Space Freed: ${Math.round(result.freed / 1024 / 1024 * 100) / 100} MB`);

        if (result.errors.length > 0) {
            console.log('\nErrors:');
            result.errors.forEach(error => {
                console.log(`  • ${error}`);
            });
        }
    }

    formatAsYAML(obj, indent = 0) {
        const spaces = ' '.repeat(indent);
        let yaml = '';

        for (const [key, value] of Object.entries(obj)) {
            if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                yaml += `${spaces}${key}:\n${this.formatAsYAML(value, indent + 2)}`;
            } else {
                yaml += `${spaces}${key}: ${value}\n`;
            }
        }

        return yaml;
    }

    /**
     * Run the CLI
     */
    run() {
        this.program.parse();
    }
}

// Simple sprintf implementation for table formatting
function sprintf(format, ...args) {
    let i = 0;
    return format.replace(/%[-+#0 ]*\*?(\*|\d+)?(\.\*|\.\d+)?[hlL]?[diouxXeEfFgGaAcs%]/g, (match, width) => {
        const arg = args[i++];
        if (match.includes('s')) {
            const str = String(arg || '');
            const w = parseInt(width) || 0;
            return w > 0 ? str.padEnd(w).substring(0, w) : str;
        }
        return arg;
    });
}

// Export for testing
module.exports = MonitoringCLI;

// CLI execution
if (require.main === module) {
    const cli = new MonitoringCLI();
    cli.run();
}