/**
 * Claude Enhancer 5.0 - Error Recovery Dashboard
 * Real-time dashboard for monitoring error recovery system
 */

const http = require('http');
const path = require('path');
const fs = require('fs').promises;
const { EventEmitter } = require('events');

class ErrorRecoveryDashboard extends EventEmitter {
    constructor(options = {}) {
        super();

        this.config = {
            port: options.port || 3001,
            host: options.host || '0.0.0.0',
            updateInterval: options.updateInterval || 5000, // 5 seconds
            dataRetention: options.dataRetention || 24 * 60 * 60 * 1000, // 24 hours
            enableWebSocket: options.enableWebSocket || true,
            maxDataPoints: options.maxDataPoints || 1000,
            ...options
        };

        this.server = null;
        this.isRunning = false;
        this.clients = new Set();
        this.dashboardData = new Map();
        this.historicalData = new Map();

        this.initializeDashboardData();
    }

    initializeDashboardData() {
        this.dashboardData.set('overview', {
            totalErrors: 0,
            totalRecoveries: 0,
            successRate: 0,
            averageRecoveryTime: 0,
            activeAlerts: 0,
            systemHealth: 'unknown'
        });

        this.dashboardData.set('charts', {
            errorRate: [],
            recoveryTime: [],
            throughput: [],
            alertTrends: [],
            circuitBreakerStatus: new Map()
        });

        this.dashboardData.set('recentEvents', []);
        this.dashboardData.set('topErrors', []);
        this.dashboardData.set('recoveryStrategies', new Map());
    }

    async startServer() {
        if (this.isRunning) {
            console.warn('Dashboard server already running');
            return;
        }

        this.server = http.createServer(async (req, res) => {
            await this.handleRequest(req, res);
        });

        return new Promise((resolve, reject) => {
            this.server.listen(this.config.port, this.config.host, (error) => {
                if (error) {
                    reject(error);
                } else {
                    this.isRunning = true;
                    console.log(`✅ Error Recovery Dashboard started on http://${this.config.host}:${this.config.port}`);
                    this.emit('dashboardStarted', { port: this.config.port, host: this.config.host });
                    resolve();
                }
            });
        });
    }

    async handleRequest(req, res) {
        const url = req.url;
        const method = req.method;

        // Enable CORS
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

        if (method === 'OPTIONS') {
            res.writeHead(200);
            res.end();
            return;
        }

        try {
            if (url === '/' || url === '/dashboard') {
                await this.serveDashboardHTML(res);
            } else if (url === '/api/overview') {
                await this.serveOverviewData(res);
            } else if (url === '/api/charts') {
                await this.serveChartsData(res);
            } else if (url === '/api/alerts') {
                await this.serveAlertsData(res);
            } else if (url === '/api/events') {
                await this.serveEventsData(res);
            } else if (url === '/api/health') {
                await this.serveHealthData(res);
            } else if (url.startsWith('/api/metrics/')) {
                await this.serveMetricsData(req, res);
            } else if (url === '/ws') {
                await this.handleWebSocketUpgrade(req, res);
            } else {
                res.writeHead(404, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Not found' }));
            }
        } catch (error) {
            console.error('Dashboard request error:', error);
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Internal server error' }));
        }
    }

    async serveDashboardHTML(res) {
        const html = await this.generateDashboardHTML();
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(html);
    }

    async generateDashboardHTML() {
        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error Recovery Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #2d3748;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 1.8rem;
            font-weight: 600;
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-healthy { background: #48bb78; }
        .status-warning { background: #ed8936; }
        .status-critical { background: #f56565; }

        .dashboard-container {
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }

        .metric-card:hover {
            transform: translateY(-2px);
        }

        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #2d3748;
        }

        .metric-label {
            color: #718096;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }

        .metric-trend {
            font-size: 0.8rem;
            margin-top: 0.5rem;
        }

        .trend-up { color: #48bb78; }
        .trend-down { color: #f56565; }

        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .chart-container {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .chart-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #2d3748;
        }

        .alerts-section {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }

        .alert-item {
            display: flex;
            align-items: center;
            padding: 0.75rem;
            border-left: 4px solid #e2e8f0;
            margin-bottom: 0.5rem;
            background: #f7fafc;
        }

        .alert-critical { border-left-color: #f56565; }
        .alert-warning { border-left-color: #ed8936; }
        .alert-info { border-left-color: #4299e1; }

        .alert-message {
            flex: 1;
        }

        .alert-time {
            color: #718096;
            font-size: 0.8rem;
        }

        .events-section {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .event-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid #e2e8f0;
        }

        .event-item:last-child {
            border-bottom: none;
        }

        .loading {
            text-align: center;
            color: #718096;
            padding: 2rem;
        }

        @media (max-width: 768px) {
            .dashboard-container {
                padding: 1rem;
            }

            .metrics-grid {
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
            }

            .charts-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>
            <span id="status-indicator" class="status-indicator status-healthy"></span>
            Error Recovery Dashboard
        </h1>
    </div>

    <div class="dashboard-container">
        <!-- Metrics Overview -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" id="total-errors">0</div>
                <div class="metric-label">Total Errors</div>
                <div class="metric-trend" id="errors-trend"></div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="success-rate">0%</div>
                <div class="metric-label">Success Rate</div>
                <div class="metric-trend" id="success-trend"></div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="avg-recovery-time">0ms</div>
                <div class="metric-label">Avg Recovery Time</div>
                <div class="metric-trend" id="recovery-trend"></div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="active-alerts">0</div>
                <div class="metric-label">Active Alerts</div>
                <div class="metric-trend" id="alerts-trend"></div>
            </div>
        </div>

        <!-- Charts -->
        <div class="charts-grid">
            <div class="chart-container">
                <div class="chart-title">Error Rate Over Time</div>
                <canvas id="error-rate-chart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">Recovery Time Trend</div>
                <canvas id="recovery-time-chart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">Recovery Throughput</div>
                <canvas id="throughput-chart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">Circuit Breaker Status</div>
                <canvas id="circuit-breaker-chart"></canvas>
            </div>
        </div>

        <!-- Active Alerts -->
        <div class="alerts-section">
            <h2>Active Alerts</h2>
            <div id="alerts-container">
                <div class="loading">Loading alerts...</div>
            </div>
        </div>

        <!-- Recent Events -->
        <div class="events-section">
            <h2>Recent Events</h2>
            <div id="events-container">
                <div class="loading">Loading events...</div>
            </div>
        </div>
    </div>

    <script>
        class ErrorRecoveryDashboard {
            constructor() {
                this.charts = {};
                this.lastUpdate = 0;
                this.init();
            }

            async init() {
                this.initializeCharts();
                this.startDataPolling();

                if (window.WebSocket) {
                    this.setupWebSocket();
                }
            }

            initializeCharts() {
                const chartOptions = {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { display: true },
                        y: { display: true, beginAtZero: true }
                    },
                    plugins: {
                        legend: { display: true, position: 'top' }
                    }
                };

                // Error Rate Chart
                const errorRateCtx = document.getElementById('error-rate-chart').getContext('2d');
                this.charts.errorRate = new Chart(errorRateCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Error Rate (%)',
                            data: [],
                            borderColor: 'rgb(245, 101, 101)',
                            backgroundColor: 'rgba(245, 101, 101, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: chartOptions
                });

                // Recovery Time Chart
                const recoveryTimeCtx = document.getElementById('recovery-time-chart').getContext('2d');
                this.charts.recoveryTime = new Chart(recoveryTimeCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Avg Recovery Time (ms)',
                            data: [],
                            borderColor: 'rgb(72, 187, 120)',
                            backgroundColor: 'rgba(72, 187, 120, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: chartOptions
                });

                // Throughput Chart
                const throughputCtx = document.getElementById('throughput-chart').getContext('2d');
                this.charts.throughput = new Chart(throughputCtx, {
                    type: 'bar',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Operations/min',
                            data: [],
                            backgroundColor: 'rgba(66, 153, 225, 0.8)',
                            borderColor: 'rgb(66, 153, 225)',
                            borderWidth: 1
                        }]
                    },
                    options: chartOptions
                });

                // Circuit Breaker Chart
                const circuitBreakerCtx = document.getElementById('circuit-breaker-chart').getContext('2d');
                this.charts.circuitBreaker = new Chart(circuitBreakerCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Closed', 'Open', 'Half-Open'],
                        datasets: [{
                            data: [0, 0, 0],
                            backgroundColor: ['#48bb78', '#f56565', '#ed8936']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom' }
                        }
                    }
                });
            }

            async startDataPolling() {
                await this.updateDashboard();
                setInterval(() => this.updateDashboard(), 5000);
            }

            async updateDashboard() {
                try {
                    const [overview, charts, alerts, events, health] = await Promise.all([
                        this.fetchData('/api/overview'),
                        this.fetchData('/api/charts'),
                        this.fetchData('/api/alerts'),
                        this.fetchData('/api/events'),
                        this.fetchData('/api/health')
                    ]);

                    this.updateOverview(overview);
                    this.updateCharts(charts);
                    this.updateAlerts(alerts);
                    this.updateEvents(events);
                    this.updateHealthStatus(health);

                } catch (error) {
                    console.error('Failed to update dashboard:', error);
                }
            }

            async fetchData(endpoint) {
                const response = await fetch(endpoint);
                return response.json();
            }

            updateOverview(data) {
                document.getElementById('total-errors').textContent = data.totalErrors || 0;
                document.getElementById('success-rate').textContent =
                    ((data.successRate || 0) * 100).toFixed(1) + '%';
                document.getElementById('avg-recovery-time').textContent =
                    (data.averageRecoveryTime || 0).toFixed(0) + 'ms';
                document.getElementById('active-alerts').textContent = data.activeAlerts || 0;
            }

            updateCharts(data) {
                if (data.errorRate && this.charts.errorRate) {
                    this.updateLineChart(this.charts.errorRate, data.errorRate);
                }

                if (data.recoveryTime && this.charts.recoveryTime) {
                    this.updateLineChart(this.charts.recoveryTime, data.recoveryTime);
                }

                if (data.throughput && this.charts.throughput) {
                    this.updateBarChart(this.charts.throughput, data.throughput);
                }

                if (data.circuitBreakerStatus && this.charts.circuitBreaker) {
                    this.updateDoughnutChart(this.charts.circuitBreaker, data.circuitBreakerStatus);
                }
            }

            updateLineChart(chart, data) {
                const maxPoints = 50;
                chart.data.labels = data.slice(-maxPoints).map(point =>
                    new Date(point.timestamp).toLocaleTimeString());
                chart.data.datasets[0].data = data.slice(-maxPoints).map(point => point.value);
                chart.update('none');
            }

            updateBarChart(chart, data) {
                const maxPoints = 20;
                chart.data.labels = data.slice(-maxPoints).map(point =>
                    new Date(point.timestamp).toLocaleTimeString());
                chart.data.datasets[0].data = data.slice(-maxPoints).map(point => point.value);
                chart.update('none');
            }

            updateDoughnutChart(chart, data) {
                chart.data.datasets[0].data = [
                    data.closed || 0,
                    data.open || 0,
                    data.halfOpen || 0
                ];
                chart.update('none');
            }

            updateAlerts(alerts) {
                const container = document.getElementById('alerts-container');

                if (!alerts || alerts.length === 0) {
                    container.innerHTML = '<div class="loading">No active alerts</div>';
                    return;
                }

                container.innerHTML = alerts.map(alert =>
                    '<div class="alert-item alert-' + alert.severity + '">' +
                        '<div class="alert-message">' +
                            '<strong>' + alert.type + '</strong>: ' + alert.message +
                        '</div>' +
                        '<div class="alert-time">' +
                            new Date(alert.timestamp).toLocaleString() +
                        '</div>' +
                    '</div>'
                ).join('');
            }

            updateEvents(events) {
                const container = document.getElementById('events-container');

                if (!events || events.length === 0) {
                    container.innerHTML = '<div class="loading">No recent events</div>';
                    return;
                }

                container.innerHTML = events.slice(0, 10).map(event =>
                    '<div class="event-item">' +
                        '<div>' +
                            '<strong>' + event.type + '</strong>: ' + event.message +
                        '</div>' +
                        '<div class="alert-time">' +
                            new Date(event.timestamp).toLocaleString() +
                        '</div>' +
                    '</div>'
                ).join('');
            }

            updateHealthStatus(health) {
                const indicator = document.getElementById('status-indicator');
                indicator.className = 'status-indicator status-' + (health.status || 'unknown');
            }

            setupWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const ws = new WebSocket(protocol + '//' + window.location.host + '/ws');

                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    this.handleRealtimeUpdate(data);
                };

                ws.onerror = (error) => {
                    console.warn('WebSocket error:', error);
                };
            }

            handleRealtimeUpdate(data) {
                // Handle real-time updates from WebSocket
                if (data.type === 'metric_update') {
                    this.updateDashboard();
                } else if (data.type === 'alert') {
                    this.showRealtimeAlert(data.alert);
                }
            }

            showRealtimeAlert(alert) {
                // Show real-time alert notification
                const notification = document.createElement('div');
                notification.className = 'realtime-alert';
                notification.innerHTML =
                    '<div class="alert-notification">' +
                        '🚨 ' + alert.message +
                    '</div>';
                document.body.appendChild(notification);

                setTimeout(() => {
                    notification.remove();
                }, 5000);
            }
        }

        // Initialize dashboard when page loads
        document.addEventListener('DOMContentLoaded', () => {
            new ErrorRecoveryDashboard();
        });
    </script>
</body>
</html>
        `;
    }

    async serveOverviewData(res) {
        const overview = this.dashboardData.get('overview') || {};
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(overview));
    }

    async serveChartsData(res) {
        const charts = this.dashboardData.get('charts') || {};

        // Convert Map to Object for JSON serialization
        const chartsData = {
            errorRate: charts.errorRate || [],
            recoveryTime: charts.recoveryTime || [],
            throughput: charts.throughput || [],
            alertTrends: charts.alertTrends || [],
            circuitBreakerStatus: Object.fromEntries(charts.circuitBreakerStatus || new Map())
        };

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(chartsData));
    }

    async serveAlertsData(res) {
        // This would typically fetch from the monitoring system
        const alerts = [
            {
                id: 'alert1',
                type: 'high_error_rate',
                severity: 'warning',
                message: 'Error rate above threshold (5.2%)',
                timestamp: Date.now() - 300000
            }
        ];

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(alerts));
    }

    async serveEventsData(res) {
        const events = this.dashboardData.get('recentEvents') || [];
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(events));
    }

    async serveHealthData(res) {
        const health = {
            status: this.dashboardData.get('overview')?.systemHealth || 'healthy',
            timestamp: Date.now(),
            uptime: process.uptime(),
            version: '1.0.0'
        };

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(health));
    }

    // Integration with Error Recovery Monitor
    integrateWithMonitor(monitor) {
        monitor.on('recoveryStarted', (data) => {
            this.addEvent('recovery_started', `Recovery started for ${data.errorType} using ${data.strategy}`);
            this.updateThroughputMetric();
        });

        monitor.on('recoverySuccessful', (data) => {
            this.addEvent('recovery_successful', `Recovery successful in ${data.duration}ms using ${data.strategy}`);
            this.updateOverviewMetrics(monitor);
            this.updateRecoveryTimeChart(data.duration);
        });

        monitor.on('recoveryFailed', (data) => {
            this.addEvent('recovery_failed', `Recovery failed after ${data.attempts} attempts`);
            this.updateOverviewMetrics(monitor);
        });

        monitor.on('alert', (alert) => {
            this.addEvent('alert_triggered', alert.message);
            this.broadcastToClients({
                type: 'alert',
                alert: alert
            });
        });

        monitor.on('healthCheck', (health) => {
            this.updateHealthStatus(health.status);
        });

        monitor.on('metricsCollected', (snapshot) => {
            this.updateChartsFromSnapshot(snapshot);
            this.broadcastToClients({
                type: 'metric_update',
                timestamp: Date.now()
            });
        });

        console.log('✅ Dashboard integrated with Error Recovery Monitor');
    }

    updateOverviewMetrics(monitor) {
        const metrics = monitor.getMetrics();
        const overview = this.dashboardData.get('overview');

        overview.totalErrors = metrics.errors_total?.value || 0;
        overview.totalRecoveries = metrics.recoveries_total?.value || 0;
        overview.averageRecoveryTime = metrics.average_recovery_time?.value || 0;

        const total = overview.totalErrors + overview.totalRecoveries;
        overview.successRate = total > 0 ? overview.totalRecoveries / total : 0;

        this.dashboardData.set('overview', overview);
    }

    updateRecoveryTimeChart(duration) {
        const charts = this.dashboardData.get('charts');
        charts.recoveryTime.push({
            timestamp: Date.now(),
            value: duration
        });

        // Keep only recent data points
        if (charts.recoveryTime.length > this.config.maxDataPoints) {
            charts.recoveryTime.shift();
        }

        this.dashboardData.set('charts', charts);
    }

    updateThroughputMetric() {
        const now = Date.now();
        const charts = this.dashboardData.get('charts');

        const lastEntry = charts.throughput[charts.throughput.length - 1];
        const currentMinute = Math.floor(now / 60000) * 60000;

        if (lastEntry && lastEntry.timestamp === currentMinute) {
            lastEntry.value++;
        } else {
            charts.throughput.push({
                timestamp: currentMinute,
                value: 1
            });
        }

        // Keep only recent data points
        if (charts.throughput.length > this.config.maxDataPoints) {
            charts.throughput.shift();
        }

        this.dashboardData.set('charts', charts);
    }

    updateChartsFromSnapshot(snapshot) {
        const charts = this.dashboardData.get('charts');

        // Update error rate
        if (snapshot.performance.errorRate !== undefined) {
            charts.errorRate.push({
                timestamp: snapshot.timestamp,
                value: snapshot.performance.errorRate * 100
            });
        }

        // Keep data within retention period and max points
        const cutoffTime = Date.now() - this.config.dataRetention;
        Object.keys(charts).forEach(chartName => {
            if (Array.isArray(charts[chartName])) {
                charts[chartName] = charts[chartName]
                    .filter(point => point.timestamp > cutoffTime)
                    .slice(-this.config.maxDataPoints);
            }
        });

        this.dashboardData.set('charts', charts);
    }

    updateHealthStatus(status) {
        const overview = this.dashboardData.get('overview');
        overview.systemHealth = status;
        this.dashboardData.set('overview', overview);
    }

    addEvent(type, message) {
        const events = this.dashboardData.get('recentEvents');
        events.unshift({
            type,
            message,
            timestamp: Date.now()
        });

        // Keep only recent events
        if (events.length > 100) {
            events.splice(100);
        }

        this.dashboardData.set('recentEvents', events);
    }

    broadcastToClients(message) {
        const data = JSON.stringify(message);
        for (const client of this.clients) {
            try {
                client.send(data);
            } catch (error) {
                // Remove disconnected clients
                this.clients.delete(client);
            }
        }
    }

    async stopServer() {
        if (!this.isRunning || !this.server) {
            return;
        }

        return new Promise((resolve) => {
            this.server.close(() => {
                this.isRunning = false;
                this.server = null;
                console.log('✅ Error Recovery Dashboard stopped');
                this.emit('dashboardStopped');
                resolve();
            });
        });
    }

    getStatus() {
        return {
            running: this.isRunning,
            port: this.config.port,
            host: this.config.host,
            clients: this.clients.size,
            lastUpdate: Date.now()
        };
    }

    getDashboardData() {
        return Object.fromEntries(this.dashboardData);
    }
}

module.exports = ErrorRecoveryDashboard;