/**
 * Claude Enhancer Plus - Advanced Alert Manager
 * Multi-channel alerting system for error recovery monitoring
 */

const fs = require('fs').promises;
const path = require('path');
const { EventEmitter } = require('events');

class AlertManager extends EventEmitter {
    constructor(options = {}) {
        super();

        this.config = {
            alertsDir: options.alertsDir || './.claude/alerts',
            notificationChannels: options.notificationChannels || ['console', 'file'],
            alertRules: options.alertRules || [],
            silenceRules: options.silenceRules || [],
            escalationRules: options.escalationRules || [],
            retentionPeriod: options.retentionPeriod || 30 * 24 * 60 * 60 * 1000, // 30 days
            batchingInterval: options.batchingInterval || 30000, // 30 seconds
            maxAlertsPerBatch: options.maxAlertsPerBatch || 10,
            enableSmartGrouping: options.enableSmartGrouping !== false,
            ...options
        };

        this.alerts = new Map();
        this.silencedAlerts = new Set();
        this.alertHistory = [];
        this.notificationChannels = new Map();
        this.alertRules = new Map();
        this.escalationTimers = new Map();
        this.batchedAlerts = [];
        this.statistics = {
            totalAlerts: 0,
            alertsByType: new Map(),
            alertsBySeverity: new Map(),
            resolvedAlerts: 0,
            silencedAlerts: 0
        };

        this.initializeAlertManager();
    }

    async initializeAlertManager() {
        try {
            await this.ensureDirectories();
            await this.loadAlertRules();
            await this.initializeNotificationChannels();
            this.startBatchingTimer();

            console.log('✅ Alert Manager initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize Alert Manager:', error);
            throw error;
        }
    }

    async ensureDirectories() {
        const dirs = [
            this.config.alertsDir,
            path.join(this.config.alertsDir, 'active'),
            path.join(this.config.alertsDir, 'resolved'),
            path.join(this.config.alertsDir, 'silenced'),
            path.join(this.config.alertsDir, 'history')
        ];

        for (const dir of dirs) {
            await fs.mkdir(dir, { recursive: true });
        }
    }

    async loadAlertRules() {
        // Default alert rules
        const defaultRules = [
            {
                id: 'high_error_rate',
                name: 'High Error Rate',
                condition: 'error_rate > 0.05',
                severity: 'warning',
                description: 'Error rate exceeds 5%',
                threshold: 0.05,
                evaluationInterval: 60000, // 1 minute
                forDuration: 300000, // 5 minutes
                channels: ['console', 'file', 'webhook']
            },
            {
                id: 'critical_error_rate',
                name: 'Critical Error Rate',
                condition: 'error_rate > 0.15',
                severity: 'critical',
                description: 'Error rate critically high (>15%)',
                threshold: 0.15,
                evaluationInterval: 30000, // 30 seconds
                forDuration: 120000, // 2 minutes
                channels: ['console', 'file', 'webhook', 'slack']
            },
            {
                id: 'slow_recovery',
                name: 'Slow Recovery Times',
                condition: 'avg_recovery_time > 5000',
                severity: 'warning',
                description: 'Average recovery time exceeds 5 seconds',
                threshold: 5000,
                evaluationInterval: 60000,
                forDuration: 600000, // 10 minutes
                channels: ['console', 'file']
            },
            {
                id: 'circuit_breaker_open',
                name: 'Circuit Breaker Open',
                condition: 'circuit_breaker_state == "open"',
                severity: 'critical',
                description: 'Circuit breaker is open',
                evaluationInterval: 15000, // 15 seconds
                forDuration: 0, // Immediate
                channels: ['console', 'file', 'webhook', 'slack']
            },
            {
                id: 'consecutive_failures',
                name: 'Consecutive Failures',
                condition: 'consecutive_failures >= 5',
                severity: 'critical',
                description: '5 or more consecutive recovery failures',
                threshold: 5,
                evaluationInterval: 30000,
                forDuration: 0,
                channels: ['console', 'file', 'webhook', 'slack', 'email']
            },
            {
                id: 'memory_usage_high',
                name: 'High Memory Usage',
                condition: 'memory_usage > 0.8',
                severity: 'warning',
                description: 'Memory usage exceeds 80%',
                threshold: 0.8,
                evaluationInterval: 60000,
                forDuration: 300000,
                channels: ['console', 'file']
            },
            {
                id: 'disk_space_low',
                name: 'Low Disk Space',
                condition: 'disk_usage > 0.9',
                severity: 'critical',
                description: 'Disk usage exceeds 90%',
                threshold: 0.9,
                evaluationInterval: 300000, // 5 minutes
                forDuration: 0,
                channels: ['console', 'file', 'webhook', 'slack', 'email']
            }
        ];

        // Load custom rules from config
        const customRules = this.config.alertRules || [];
        const allRules = [...defaultRules, ...customRules];

        for (const rule of allRules) {
            this.alertRules.set(rule.id, {
                ...rule,
                lastEvaluation: 0,
                triggeredAt: null,
                evaluationCount: 0
            });
        }

        console.log(`📋 Loaded ${allRules.length} alert rules`);
    }

    async initializeNotificationChannels() {
        // Console notification channel
        this.notificationChannels.set('console', {
            type: 'console',
            enabled: true,
            send: this.sendConsoleNotification.bind(this)
        });

        // File notification channel
        this.notificationChannels.set('file', {
            type: 'file',
            enabled: true,
            path: path.join(this.config.alertsDir, 'notifications.log'),
            send: this.sendFileNotification.bind(this)
        });

        // Webhook notification channel
        this.notificationChannels.set('webhook', {
            type: 'webhook',
            enabled: this.config.webhookUrl ? true : false,
            url: this.config.webhookUrl,
            send: this.sendWebhookNotification.bind(this)
        });

        // Slack notification channel
        this.notificationChannels.set('slack', {
            type: 'slack',
            enabled: this.config.slackWebhookUrl ? true : false,
            webhookUrl: this.config.slackWebhookUrl,
            channel: this.config.slackChannel || '#alerts',
            send: this.sendSlackNotification.bind(this)
        });

        // Email notification channel (placeholder)
        this.notificationChannels.set('email', {
            type: 'email',
            enabled: false, // Implement email service integration
            send: this.sendEmailNotification.bind(this)
        });

        const enabledChannels = Array.from(this.notificationChannels.values())
            .filter(channel => channel.enabled)
            .map(channel => channel.type);

        console.log(`📡 Initialized notification channels: ${enabledChannels.join(', ')}`);
    }

    // Alert Processing
    async processAlert(alertData) {
        try {
            const alert = this.createAlert(alertData);

            // Check if alert should be silenced
            if (this.isAlertSilenced(alert)) {
                this.silencedAlerts.add(alert.id);
                this.statistics.silencedAlerts++;
                return null;
            }

            // Check for duplicate alerts
            const existingAlert = this.findSimilarAlert(alert);
            if (existingAlert) {
                return this.updateExistingAlert(existingAlert, alert);
            }

            // Store new alert
            this.alerts.set(alert.id, alert);
            this.alertHistory.push(alert);

            // Update statistics
            this.updateStatistics(alert);

            // Add to batch for notification
            if (this.config.enableSmartGrouping) {
                this.batchedAlerts.push(alert);
            } else {
                await this.sendNotifications(alert);
            }

            // Setup escalation if needed
            this.setupEscalation(alert);

            this.emit('alertCreated', alert);

            console.log(`🚨 Alert created: ${alert.type} - ${alert.message}`);
            return alert;

        } catch (error) {
            console.error('Failed to process alert:', error);
            return null;
        }
    }

    createAlert(data) {
        const alertId = `${data.type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        return {
            id: alertId,
            type: data.type,
            severity: data.severity || 'info',
            message: data.message,
            description: data.description || data.message,
            source: data.source || 'error_recovery',
            timestamp: Date.now(),
            status: 'active',
            labels: data.labels || {},
            details: data.details || {},
            fingerprint: this.generateFingerprint(data),
            channels: this.getChannelsForAlert(data),
            escalationLevel: 0,
            notificationCount: 0,
            lastNotification: null,
            resolvedAt: null,
            resolvedBy: null,
            silencedUntil: null
        };
    }

    generateFingerprint(data) {
        // Create a unique fingerprint for similar alerts
        const key = `${data.type}_${data.severity}_${JSON.stringify(data.labels || {})}`;
        return require('crypto').createHash('md5').update(key).digest('hex');
    }

    getChannelsForAlert(data) {
        const rule = this.alertRules.get(data.type);
        if (rule && rule.channels) {
            return rule.channels;
        }

        // Default channels based on severity
        switch (data.severity) {
            case 'critical':
                return ['console', 'file', 'webhook', 'slack'];
            case 'warning':
                return ['console', 'file', 'webhook'];
            default:
                return ['console', 'file'];
        }
    }

    findSimilarAlert(newAlert) {
        for (const [id, existingAlert] of this.alerts.entries()) {
            if (existingAlert.fingerprint === newAlert.fingerprint &&
                existingAlert.status === 'active' &&
                Date.now() - existingAlert.timestamp < 300000) { // 5 minutes
                return existingAlert;
            }
        }
        return null;
    }

    updateExistingAlert(existingAlert, newAlert) {
        existingAlert.notificationCount++;
        existingAlert.lastNotification = Date.now();
        existingAlert.details = { ...existingAlert.details, ...newAlert.details };

        this.emit('alertUpdated', existingAlert);
        return existingAlert;
    }

    // Alert Rules Evaluation
    async evaluateAlertRules(metrics) {
        const now = Date.now();

        for (const [ruleId, rule] of this.alertRules.entries()) {
            if (now - rule.lastEvaluation < rule.evaluationInterval) {
                continue;
            }

            rule.lastEvaluation = now;
            rule.evaluationCount++;

            try {
                const conditionMet = this.evaluateCondition(rule.condition, metrics);

                if (conditionMet && !rule.triggeredAt) {
                    rule.triggeredAt = now;
                } else if (!conditionMet && rule.triggeredAt) {
                    rule.triggeredAt = null;
                }

                // Check if alert should be triggered
                if (rule.triggeredAt && (now - rule.triggeredAt >= rule.forDuration)) {
                    await this.triggerRuleAlert(rule, metrics);
                    rule.triggeredAt = null; // Reset to avoid duplicate alerts
                }

            } catch (error) {
                console.error(`Failed to evaluate rule ${ruleId}:`, error);
            }
        }
    }

    evaluateCondition(condition, metrics) {
        try {
            // Simple condition evaluation
            // In a production system, you'd use a proper expression evaluator
            const context = {
                error_rate: metrics.errorRate || 0,
                avg_recovery_time: metrics.averageRecoveryTime || 0,
                consecutive_failures: metrics.consecutiveFailures || 0,
                memory_usage: metrics.memoryUsage || 0,
                disk_usage: metrics.diskUsage || 0,
                circuit_breaker_state: metrics.circuitBreakerState || 'closed'
            };

            // Replace variables in condition
            let evaluableCondition = condition;
            for (const [key, value] of Object.entries(context)) {
                evaluableCondition = evaluableCondition.replace(
                    new RegExp(`\\b${key}\\b`, 'g'),
                    typeof value === 'string' ? `"${value}"` : value
                );
            }

            // Use Function constructor for safe evaluation (basic implementation)
            return new Function(`return ${evaluableCondition}`)();

        } catch (error) {
            console.error('Failed to evaluate condition:', condition, error);
            return false;
        }
    }

    async triggerRuleAlert(rule, metrics) {
        const alertData = {
            type: rule.id,
            severity: rule.severity,
            message: rule.name,
            description: rule.description,
            source: 'alert_rule',
            labels: { rule_id: rule.id },
            details: { metrics, rule: rule.name }
        };

        await this.processAlert(alertData);
    }

    // Alert Resolution
    async resolveAlert(alertId, resolvedBy = 'system') {
        const alert = this.alerts.get(alertId);
        if (!alert || alert.status !== 'active') {
            return false;
        }

        alert.status = 'resolved';
        alert.resolvedAt = Date.now();
        alert.resolvedBy = resolvedBy;

        // Cancel escalation
        if (this.escalationTimers.has(alertId)) {
            clearTimeout(this.escalationTimers.get(alertId));
            this.escalationTimers.delete(alertId);
        }

        // Move to resolved alerts
        this.alerts.delete(alertId);
        this.statistics.resolvedAlerts++;

        // Save resolved alert
        await this.saveResolvedAlert(alert);

        this.emit('alertResolved', alert);

        console.log(`✅ Alert resolved: ${alert.type} by ${resolvedBy}`);
        return true;
    }

    async autoResolveAlerts(metrics) {
        const activeAlerts = Array.from(this.alerts.values());

        for (const alert of activeAlerts) {
            if (await this.shouldAutoResolve(alert, metrics)) {
                await this.resolveAlert(alert.id, 'auto_resolve');
            }
        }
    }

    async shouldAutoResolve(alert, metrics) {
        const rule = this.alertRules.get(alert.type);
        if (!rule) return false;

        // Check if the condition is no longer met
        try {
            const conditionMet = this.evaluateCondition(rule.condition, metrics);

            // Auto-resolve if condition not met for 5 minutes
            if (!conditionMet && Date.now() - alert.timestamp > 300000) {
                return true;
            }
        } catch (error) {
            console.error('Error in auto-resolve check:', error);
        }

        return false;
    }

    // Alert Silencing
    silenceAlert(alertId, duration = 3600000) { // 1 hour default
        const alert = this.alerts.get(alertId);
        if (alert) {
            alert.silencedUntil = Date.now() + duration;
            this.silencedAlerts.add(alertId);
            this.emit('alertSilenced', { alert, duration });
            console.log(`🔇 Alert silenced: ${alert.type} for ${duration}ms`);
        }
    }

    unsilenceAlert(alertId) {
        const alert = this.alerts.get(alertId);
        if (alert) {
            alert.silencedUntil = null;
            this.silencedAlerts.delete(alertId);
            this.emit('alertUnsilenced', alert);
            console.log(`🔊 Alert unsilenced: ${alert.type}`);
        }
    }

    isAlertSilenced(alert) {
        // Check if alert type is globally silenced
        for (const rule of this.config.silenceRules) {
            if (this.matchesSilenceRule(alert, rule)) {
                return true;
            }
        }

        // Check if specific alert is silenced
        if (alert.silencedUntil && Date.now() < alert.silencedUntil) {
            return true;
        }

        return false;
    }

    matchesSilenceRule(alert, rule) {
        if (rule.type && rule.type !== alert.type) return false;
        if (rule.severity && rule.severity !== alert.severity) return false;

        if (rule.labels) {
            for (const [key, value] of Object.entries(rule.labels)) {
                if (alert.labels[key] !== value) return false;
            }
        }

        return true;
    }

    // Notification System
    startBatchingTimer() {
        setInterval(() => {
            if (this.batchedAlerts.length > 0) {
                this.processBatchedAlerts();
            }
        }, this.config.batchingInterval);
    }

    async processBatchedAlerts() {
        if (this.batchedAlerts.length === 0) return;

        const alertsToProcess = [...this.batchedAlerts];
        this.batchedAlerts = [];

        // Group similar alerts
        const groupedAlerts = this.groupSimilarAlerts(alertsToProcess);

        for (const group of groupedAlerts) {
            await this.sendGroupedNotifications(group);
        }
    }

    groupSimilarAlerts(alerts) {
        const groups = new Map();

        for (const alert of alerts) {
            const groupKey = `${alert.type}_${alert.severity}`;

            if (!groups.has(groupKey)) {
                groups.set(groupKey, []);
            }

            groups.get(groupKey).push(alert);
        }

        return Array.from(groups.values());
    }

    async sendGroupedNotifications(alertGroup) {
        if (alertGroup.length === 1) {
            await this.sendNotifications(alertGroup[0]);
        } else {
            const groupAlert = this.createGroupAlert(alertGroup);
            await this.sendNotifications(groupAlert);
        }
    }

    createGroupAlert(alerts) {
        const firstAlert = alerts[0];

        return {
            ...firstAlert,
            id: `group_${Date.now()}`,
            message: `${alerts.length} ${firstAlert.type} alerts`,
            description: `Multiple ${firstAlert.type} alerts occurred`,
            details: {
                count: alerts.length,
                alerts: alerts.map(a => ({ id: a.id, message: a.message, timestamp: a.timestamp }))
            }
        };
    }

    async sendNotifications(alert) {
        const channelPromises = alert.channels.map(async channelName => {
            const channel = this.notificationChannels.get(channelName);
            if (channel && channel.enabled) {
                try {
                    await channel.send(alert, channel);
                    return { channel: channelName, success: true };
                } catch (error) {
                    console.error(`Failed to send notification to ${channelName}:`, error);
                    return { channel: channelName, success: false, error };
                }
            }
            return { channel: channelName, success: false, error: 'Channel disabled' };
        });

        const results = await Promise.all(channelPromises);

        alert.lastNotification = Date.now();
        alert.notificationCount++;

        this.emit('notificationsSent', { alert, results });
    }

    // Notification Channels
    async sendConsoleNotification(alert) {
        const severity = alert.severity.toUpperCase().padEnd(8);
        const timestamp = new Date(alert.timestamp).toISOString();

        let emoji = '🔔';
        if (alert.severity === 'critical') emoji = '🚨';
        else if (alert.severity === 'warning') emoji = '⚠️';
        else if (alert.severity === 'info') emoji = 'ℹ️';

        console.log(`${emoji} [${severity}] ${timestamp} - ${alert.message}`);
        if (alert.description && alert.description !== alert.message) {
            console.log(`    ${alert.description}`);
        }
    }

    async sendFileNotification(alert, channel) {
        const logEntry = {
            timestamp: new Date(alert.timestamp).toISOString(),
            severity: alert.severity,
            type: alert.type,
            message: alert.message,
            description: alert.description,
            labels: alert.labels,
            details: alert.details
        };

        const logLine = JSON.stringify(logEntry) + '\n';
        await fs.appendFile(channel.path, logLine);
    }

    async sendWebhookNotification(alert, channel) {
        if (!channel.url) return;

        const payload = {
            alert_id: alert.id,
            type: alert.type,
            severity: alert.severity,
            message: alert.message,
            description: alert.description,
            timestamp: alert.timestamp,
            source: alert.source,
            labels: alert.labels,
            details: alert.details
        };

        // Implement HTTP POST to webhook URL
        // This is a placeholder - implement with your preferred HTTP client
        console.log(`📡 Webhook notification: ${JSON.stringify(payload)}`);
    }

    async sendSlackNotification(alert, channel) {
        if (!channel.webhookUrl) return;

        const color = alert.severity === 'critical' ? 'danger' :
                      alert.severity === 'warning' ? 'warning' : 'good';

        const payload = {
            channel: channel.channel,
            username: 'Error Recovery Alert',
            icon_emoji: ':warning:',
            attachments: [{
                color,
                title: alert.message,
                text: alert.description,
                fields: [
                    { title: 'Severity', value: alert.severity, short: true },
                    { title: 'Type', value: alert.type, short: true },
                    { title: 'Source', value: alert.source, short: true },
                    { title: 'Time', value: new Date(alert.timestamp).toISOString(), short: true }
                ],
                footer: 'Error Recovery System',
                ts: Math.floor(alert.timestamp / 1000)
            }]
        };

        // Implement Slack webhook POST
        console.log(`📱 Slack notification: ${JSON.stringify(payload)}`);
    }

    async sendEmailNotification(alert, channel) {
        // Placeholder for email notification implementation
        console.log(`📧 Email notification: ${alert.message}`);
    }

    // Escalation System
    setupEscalation(alert) {
        const escalationRules = this.config.escalationRules;
        if (!escalationRules || escalationRules.length === 0) return;

        const rule = escalationRules.find(r =>
            r.severity === alert.severity || r.type === alert.type
        );

        if (rule) {
            const timer = setTimeout(() => {
                this.escalateAlert(alert, rule);
            }, rule.delay || 300000); // 5 minutes default

            this.escalationTimers.set(alert.id, timer);
        }
    }

    async escalateAlert(alert, rule) {
        alert.escalationLevel++;

        // Increase severity if specified
        if (rule.escalateSeverity) {
            const severities = ['info', 'warning', 'critical'];
            const currentIndex = severities.indexOf(alert.severity);
            if (currentIndex < severities.length - 1) {
                alert.severity = severities[currentIndex + 1];
            }
        }

        // Add escalation channels
        if (rule.escalationChannels) {
            alert.channels = [...new Set([...alert.channels, ...rule.escalationChannels])];
        }

        await this.sendNotifications(alert);

        this.emit('alertEscalated', { alert, rule });

        console.log(`📈 Alert escalated: ${alert.type} to level ${alert.escalationLevel}`);
    }

    // Statistics and Reporting
    updateStatistics(alert) {
        this.statistics.totalAlerts++;

        const typeCount = this.statistics.alertsByType.get(alert.type) || 0;
        this.statistics.alertsByType.set(alert.type, typeCount + 1);

        const severityCount = this.statistics.alertsBySeverity.get(alert.severity) || 0;
        this.statistics.alertsBySeverity.set(alert.severity, severityCount + 1);
    }

    getStatistics() {
        return {
            ...this.statistics,
            activeAlerts: this.alerts.size,
            silencedAlertsCount: this.silencedAlerts.size,
            alertsByType: Object.fromEntries(this.statistics.alertsByType),
            alertsBySeverity: Object.fromEntries(this.statistics.alertsBySeverity),
            escalationsActive: this.escalationTimers.size
        };
    }

    // Data Persistence
    async saveResolvedAlert(alert) {
        const filename = `resolved_${alert.id}.json`;
        const filepath = path.join(this.config.alertsDir, 'resolved', filename);
        await fs.writeFile(filepath, JSON.stringify(alert, null, 2));
    }

    // Public API Methods
    getActiveAlerts() {
        return Array.from(this.alerts.values());
    }

    getAlertById(alertId) {
        return this.alerts.get(alertId);
    }

    getAlertHistory(limit = 100) {
        return this.alertHistory.slice(-limit);
    }

    getSilencedAlerts() {
        return Array.from(this.silencedAlerts);
    }

    // Cleanup
    async cleanup() {
        const cutoffTime = Date.now() - this.config.retentionPeriod;

        // Clean alert history
        this.alertHistory = this.alertHistory.filter(alert =>
            alert.timestamp > cutoffTime
        );

        // Clean resolved alerts files
        try {
            const resolvedDir = path.join(this.config.alertsDir, 'resolved');
            const files = await fs.readdir(resolvedDir);

            for (const file of files) {
                const filepath = path.join(resolvedDir, file);
                const stats = await fs.stat(filepath);

                if (stats.mtime.getTime() < cutoffTime) {
                    await fs.unlink(filepath);
                }
            }
        } catch (error) {
            console.error('Cleanup failed:', error);
        }
    }

    async shutdown() {
        console.log('🔄 Shutting down Alert Manager...');

        // Clear all escalation timers
        for (const timer of this.escalationTimers.values()) {
            clearTimeout(timer);
        }
        this.escalationTimers.clear();

        // Final cleanup
        await this.cleanup();

        console.log('✅ Alert Manager shutdown complete');
    }
}

module.exports = AlertManager;