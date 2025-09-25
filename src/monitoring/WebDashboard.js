#!/usr/bin/env node

/**
 * Claude Enhancer 5.0 - Web Dashboard Server
 *
 * Provides a web-based monitoring interface with:
 * - Real-time updates via WebSocket
 * - REST API for metrics access
 * - Interactive charts and visualizations
 * - Mobile-responsive design
 *
 * @author Claude Code
 * @version 1.0.0
 */

const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const fs = require('fs').promises;
const MetricsCollector = require('./MetricsCollector');

class WebDashboard {
    constructor(options = {}) {
        this.options = {
            port: options.port || 3000,
            host: options.host || 'localhost',
            updateInterval: options.updateInterval || 1000,
            cors: options.cors !== false,
            auth: options.auth || null,
            staticPath: options.staticPath || path.join(__dirname, 'web'),
            ...options
        };

        this.app = express();
        this.server = http.createServer(this.app);
        this.wss = new WebSocket.Server({ server: this.server });

        this.metricsCollector = new MetricsCollector({
            collectInterval: this.options.updateInterval
        });

        this.clients = new Set();
        this.isStarted = false;

        this.setupExpress();
        this.setupWebSocket();
        this.setupMetricsCollector();
    }

    /**
     * Setup Express middleware and routes
     */
    setupExpress() {
        // CORS middleware
        if (this.options.cors) {
            this.app.use((req, res, next) => {
                res.header('Access-Control-Allow-Origin', '*');
                res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
                res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
                next();
            });
        }

        // Body parser
        this.app.use(express.json());
        this.app.use(express.urlencoded({ extended: true }));

        // Authentication middleware
        if (this.options.auth) {
            this.app.use('/api', this.authenticateRequest.bind(this));
        }

        // Serve static files
        this.app.use(express.static(this.options.staticPath));

        // API routes
        this.setupAPIRoutes();

        // Serve dashboard HTML
        this.app.get('/', (req, res) => {
            res.sendFile(path.join(this.options.staticPath, 'index.html'));
        });

        // Health check endpoint
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                timestamp: new Date().toISOString(),
                uptime: process.uptime(),
                version: require('../../../package.json').version || '1.0.0'
            });
        });
    }

    /**
     * Setup API routes
     */
    setupAPIRoutes() {
        // Get all metrics
        this.app.get('/api/metrics', async (req, res) => {
            try {
                const since = parseInt(req.query.since) || 0;
                const metrics = this.metricsCollector.getAllMetrics(since);

                res.json({
                    success: true,
                    data: metrics,
                    timestamp: Date.now()
                });
            } catch (error) {
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });

        // Get specific metric
        this.app.get('/api/metrics/:name', async (req, res) => {
            try {
                const { name } = req.params;
                const since = parseInt(req.query.since) || 0;
                const metric = this.metricsCollector.getMetric(name, since);

                res.json({
                    success: true,
                    data: metric,
                    timestamp: Date.now()
                });
            } catch (error) {
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });

        // Get current system status
        this.app.get('/api/status', async (req, res) => {
            try {
                const status = await this.getSystemStatus();

                res.json({
                    success: true,
                    data: status,
                    timestamp: Date.now()
                });
            } catch (error) {
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });

        // Export metrics
        this.app.post('/api/export', async (req, res) => {
            try {
                const filename = await this.metricsCollector.exportMetrics();

                res.json({
                    success: true,
                    data: {
                        filename,
                        message: 'Metrics exported successfully'
                    }
                });
            } catch (error) {
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });

        // Reset metrics
        this.app.post('/api/reset', async (req, res) => {
            try {
                // Clear metrics collector data
                this.metricsCollector.metrics.clear();

                res.json({
                    success: true,
                    data: {
                        message: 'Metrics reset successfully'
                    }
                });
            } catch (error) {
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });

        // Get alerts
        this.app.get('/api/alerts', async (req, res) => {
            try {
                const alerts = await this.getAlerts();

                res.json({
                    success: true,
                    data: alerts,
                    timestamp: Date.now()
                });
            } catch (error) {
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });

        // Configuration endpoints
        this.app.get('/api/config', (req, res) => {
            res.json({
                success: true,
                data: {
                    updateInterval: this.options.updateInterval,
                    metricsRetention: this.metricsCollector.options.maxDataPoints,
                    collectors: Array.from(this.metricsCollector.collectors.keys())
                }
            });
        });

        // Update configuration
        this.app.put('/api/config', (req, res) => {
            try {
                const { updateInterval, metricsRetention } = req.body;

                if (updateInterval && updateInterval >= 100) {
                    this.options.updateInterval = updateInterval;
                    this.updateClientBroadcastInterval();
                }

                if (metricsRetention && metricsRetention > 0) {
                    this.metricsCollector.options.maxDataPoints = metricsRetention;
                }

                res.json({
                    success: true,
                    data: {
                        message: 'Configuration updated successfully',
                        newConfig: {
                            updateInterval: this.options.updateInterval,
                            metricsRetention: this.metricsCollector.options.maxDataPoints
                        }
                    }
                });
            } catch (error) {
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });
    }

    /**
     * Setup WebSocket connections
     */
    setupWebSocket() {
        this.wss.on('connection', (ws, req) => {
            console.log(`New WebSocket client connected from ${req.socket.remoteAddress}`);

            this.clients.add(ws);

            // Send initial data
            this.sendInitialData(ws);

            // Handle messages from client
            ws.on('message', (message) => {
                try {
                    const data = JSON.parse(message);
                    this.handleWebSocketMessage(ws, data);
                } catch (error) {
                    console.error('WebSocket message parse error:', error);
                }
            });

            // Handle client disconnect
            ws.on('close', () => {
                this.clients.delete(ws);
                console.log('WebSocket client disconnected');
            });

            // Handle errors
            ws.on('error', (error) => {
                console.error('WebSocket error:', error);
                this.clients.delete(ws);
            });
        });

        // Start broadcasting updates
        this.startBroadcast();
    }

    /**
     * Setup metrics collector event handlers
     */
    setupMetricsCollector() {
        this.metricsCollector.on('metric', (name, data) => {
            this.broadcastToClients({
                type: 'metric',
                name,
                data,
                timestamp: Date.now()
            });
        });

        this.metricsCollector.on('error', (message, error) => {
            this.broadcastToClients({
                type: 'error',
                message,
                error: error?.message || error,
                timestamp: Date.now()
            });
        });

        this.metricsCollector.on('collection-complete', (timestamp) => {
            this.broadcastToClients({
                type: 'collection-complete',
                timestamp
            });
        });
    }

    /**
     * Send initial data to new WebSocket client
     */
    async sendInitialData(ws) {
        try {
            const status = await this.getSystemStatus();
            const recentMetrics = this.metricsCollector.getAllMetrics(Date.now() - 300000); // Last 5 minutes

            ws.send(JSON.stringify({
                type: 'initial',
                data: {
                    status,
                    metrics: recentMetrics,
                    config: {
                        updateInterval: this.options.updateInterval,
                        collectors: Array.from(this.metricsCollector.collectors.keys())
                    }
                },
                timestamp: Date.now()
            }));
        } catch (error) {
            console.error('Error sending initial data:', error);
        }
    }

    /**
     * Handle WebSocket messages from clients
     */
    handleWebSocketMessage(ws, data) {
        switch (data.type) {
            case 'subscribe':
                // Client wants to subscribe to specific metrics
                ws.subscriptions = new Set(data.metrics || []);
                break;

            case 'unsubscribe':
                // Client wants to unsubscribe from metrics
                if (data.metrics) {
                    data.metrics.forEach(metric => {
                        ws.subscriptions?.delete(metric);
                    });
                }
                break;

            case 'get-metrics':
                // Client requesting specific metrics
                this.handleMetricsRequest(ws, data);
                break;

            case 'ping':
                // Keepalive ping
                ws.send(JSON.stringify({
                    type: 'pong',
                    timestamp: Date.now()
                }));
                break;

            default:
                console.warn('Unknown WebSocket message type:', data.type);
        }
    }

    /**
     * Handle metrics request from WebSocket client
     */
    async handleMetricsRequest(ws, data) {
        try {
            const { metrics, since } = data;
            const result = {};

            if (metrics && Array.isArray(metrics)) {
                for (const metric of metrics) {
                    result[metric] = this.metricsCollector.getMetric(metric, since || 0);
                }
            } else {
                Object.assign(result, this.metricsCollector.getAllMetrics(since || 0));
            }

            ws.send(JSON.stringify({
                type: 'metrics-response',
                data: result,
                requestId: data.requestId,
                timestamp: Date.now()
            }));
        } catch (error) {
            ws.send(JSON.stringify({
                type: 'error',
                message: 'Failed to get metrics',
                error: error.message,
                requestId: data.requestId,
                timestamp: Date.now()
            }));
        }
    }

    /**
     * Start broadcasting updates to all clients
     */
    startBroadcast() {
        this.broadcastInterval = setInterval(() => {
            if (this.clients.size > 0) {
                this.broadcastSystemUpdate();
            }
        }, this.options.updateInterval);
    }

    /**
     * Broadcast system update to all clients
     */
    async broadcastSystemUpdate() {
        try {
            const status = await this.getSystemStatus();

            this.broadcastToClients({
                type: 'status-update',
                data: status,
                timestamp: Date.now()
            });
        } catch (error) {
            console.error('Error broadcasting system update:', error);
        }
    }

    /**
     * Broadcast message to all connected clients
     */
    broadcastToClients(message) {
        const messageStr = JSON.stringify(message);

        for (const client of this.clients) {
            if (client.readyState === WebSocket.OPEN) {
                try {
                    // Check if client has subscriptions
                    if (client.subscriptions && message.type === 'metric') {
                        if (!client.subscriptions.has(message.name)) {
                            continue; // Skip if client not subscribed to this metric
                        }
                    }

                    client.send(messageStr);
                } catch (error) {
                    console.error('Error sending to client:', error);
                    this.clients.delete(client);
                }
            } else {
                // Remove dead connections
                this.clients.delete(client);
            }
        }
    }

    /**
     * Update client broadcast interval
     */
    updateClientBroadcastInterval() {
        if (this.broadcastInterval) {
            clearInterval(this.broadcastInterval);
            this.startBroadcast();
        }
    }

    /**
     * Get current system status
     */
    async getSystemStatus() {
        const latestMetrics = {};

        for (const [name, metricArray] of this.metricsCollector.metrics) {
            if (metricArray.length > 0) {
                latestMetrics[name] = metricArray[metricArray.length - 1].data;
            }
        }

        return {
            isCollecting: this.metricsCollector.isCollecting,
            connectedClients: this.clients.size,
            metricsCount: this.metricsCollector.metrics.size,
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            latest: latestMetrics
        };
    }

    /**
     * Get alerts from metrics
     */
    async getAlerts() {
        const alerts = [];
        const now = Date.now();

        // Check for system alerts based on latest metrics
        const systemMetric = this.metricsCollector.getMetric('system');
        if (systemMetric.length > 0) {
            const latest = systemMetric[systemMetric.length - 1].data;

            if (latest.memory > 90) {
                alerts.push({
                    type: 'critical',
                    category: 'system',
                    message: `High memory usage: ${latest.memory.toFixed(1)}%`,
                    timestamp: now,
                    value: latest.memory
                });
            }

            if (latest.cpu > 80) {
                alerts.push({
                    type: 'warning',
                    category: 'system',
                    message: `High CPU usage: ${latest.cpu.toFixed(1)}%`,
                    timestamp: now,
                    value: latest.cpu
                });
            }
        }

        // Check for performance alerts
        const performanceMetric = this.metricsCollector.getMetric('performance');
        if (performanceMetric.length > 0) {
            const latest = performanceMetric[performanceMetric.length - 1].data;

            if (latest.responseTime > 1000) {
                alerts.push({
                    type: 'warning',
                    category: 'performance',
                    message: `Slow response time: ${latest.responseTime.toFixed(0)}ms`,
                    timestamp: now,
                    value: latest.responseTime
                });
            }

            if (latest.errorRate > 0.05) {
                alerts.push({
                    type: 'error',
                    category: 'performance',
                    message: `High error rate: ${(latest.errorRate * 100).toFixed(1)}%`,
                    timestamp: now,
                    value: latest.errorRate
                });
            }
        }

        // Check for agent alerts
        const agentMetric = this.metricsCollector.getMetric('agents');
        if (agentMetric.length > 0) {
            const latest = agentMetric[agentMetric.length - 1].data;

            if (latest.summary.successRate < 0.8) {
                alerts.push({
                    type: 'error',
                    category: 'agents',
                    message: `Low agent success rate: ${(latest.summary.successRate * 100).toFixed(1)}%`,
                    timestamp: now,
                    value: latest.summary.successRate
                });
            }
        }

        return alerts;
    }

    /**
     * Authenticate request (if auth is enabled)
     */
    authenticateRequest(req, res, next) {
        const authHeader = req.headers.authorization;

        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({
                success: false,
                error: 'Missing or invalid authorization header'
            });
        }

        const token = authHeader.substring(7);

        if (token !== this.options.auth.token) {
            return res.status(401).json({
                success: false,
                error: 'Invalid token'
            });
        }

        next();
    }

    /**
     * Create the web dashboard HTML
     */
    async createWebDashboardHTML() {
        const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Enhancer 5.0 - Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff;
            min-height: 100vh;
        }

        .header {
            background: rgba(0, 0, 0, 0.2);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(10px);
        }

        .header h1 {
            font-size: 1.8rem;
            font-weight: 300;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4CAF50;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }

        .card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.2s ease;
        }

        .card:hover {
            transform: translateY(-2px);
        }

        .card h3 {
            margin-bottom: 1rem;
            font-weight: 400;
            color: #e0e0e0;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .metric {
            text-align: center;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
        }

        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 0.25rem;
        }

        .metric-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }

        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 1rem;
        }

        .agent-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }

        .agent-table th,
        .agent-table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .agent-table th {
            background: rgba(255, 255, 255, 0.1);
            font-weight: 500;
        }

        .status-running {
            color: #4CAF50;
        }

        .status-idle {
            color: #FFC107;
        }

        .status-error {
            color: #F44336;
        }

        .alert {
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .alert-critical {
            background: rgba(244, 67, 54, 0.2);
            border-left: 4px solid #F44336;
        }

        .alert-warning {
            background: rgba(255, 193, 7, 0.2);
            border-left: 4px solid #FFC107;
        }

        .alert-info {
            background: rgba(33, 150, 243, 0.2);
            border-left: 4px solid #2196F3;
        }

        .controls {
            position: fixed;
            top: 20px;
            right: 20px;
            display: flex;
            gap: 1rem;
            z-index: 1000;
        }

        .btn {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            cursor: pointer;
            transition: background 0.2s ease;
        }

        .btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
                gap: 1rem;
                padding: 1rem;
            }

            .header {
                padding: 1rem;
                flex-direction: column;
                gap: 1rem;
            }

            .controls {
                position: static;
                justify-content: center;
                margin-top: 1rem;
            }
        }

        .phase-progress {
            width: 100%;
            height: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            overflow: hidden;
            margin: 1rem 0;
        }

        .phase-progress-bar {
            height: 100%;
            background: linear-gradient(45deg, #4CAF50, #8BC34A);
            transition: width 0.3s ease;
            border-radius: 10px;
        }

        .connection-status {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            background: rgba(76, 175, 80, 0.9);
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .connection-status.disconnected {
            background: rgba(244, 67, 54, 0.9);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Claude Enhancer 5.0 - Monitoring Dashboard</h1>
        <div class="status-indicator">
            <div class="status-dot"></div>
            <span id="statusText">System Active</span>
        </div>
    </div>

    <div class="controls">
        <button class="btn" onclick="exportMetrics()">Export Data</button>
        <button class="btn" onclick="resetMetrics()">Reset</button>
        <button class="btn" onclick="toggleAutoRefresh()">Auto Refresh: ON</button>
    </div>

    <div class="dashboard">
        <!-- Phase Progress Card -->
        <div class="card">
            <h3>Phase Progress</h3>
            <div class="metric-grid">
                <div class="metric">
                    <div class="metric-value" id="currentPhase">Phase 0</div>
                    <div class="metric-label">Current Phase</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="phaseProgress">0%</div>
                    <div class="metric-label">Progress</div>
                </div>
            </div>
            <div class="phase-progress">
                <div class="phase-progress-bar" id="phaseProgressBar" style="width: 0%"></div>
            </div>
            <div id="phaseDetails" style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.8;"></div>
        </div>

        <!-- Performance Metrics Card -->
        <div class="card">
            <h3>Performance Metrics</h3>
            <div class="metric-grid">
                <div class="metric">
                    <div class="metric-value" id="responseTime">0ms</div>
                    <div class="metric-label">Response Time</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="throughput">0/s</div>
                    <div class="metric-label">Throughput</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="errorRate">0%</div>
                    <div class="metric-label">Error Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="activeConnections">0</div>
                    <div class="metric-label">Active Connections</div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="performanceChart"></canvas>
            </div>
        </div>

        <!-- System Health Card -->
        <div class="card">
            <h3>System Health</h3>
            <div class="metric-grid">
                <div class="metric">
                    <div class="metric-value" id="cpuUsage">0%</div>
                    <div class="metric-label">CPU Usage</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="memoryUsage">0%</div>
                    <div class="metric-label">Memory Usage</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="diskUsage">0%</div>
                    <div class="metric-label">Disk Usage</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="networkUsage">0%</div>
                    <div class="metric-label">Network Usage</div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="systemChart"></canvas>
            </div>
        </div>

        <!-- Agent Status Card -->
        <div class="card">
            <h3>Agent Status</h3>
            <div class="metric-grid">
                <div class="metric">
                    <div class="metric-value" id="totalAgents">0</div>
                    <div class="metric-label">Total Agents</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="runningAgents">0</div>
                    <div class="metric-label">Running</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="idleAgents">0</div>
                    <div class="metric-label">Idle</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="successRate">0%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
            </div>
            <table class="agent-table" id="agentTable">
                <thead>
                    <tr>
                        <th>Agent</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Success</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>

        <!-- Cache Performance Card -->
        <div class="card">
            <h3>Cache Performance</h3>
            <div class="metric-grid">
                <div class="metric">
                    <div class="metric-value" id="cacheHitRate">0%</div>
                    <div class="metric-label">Hit Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="cacheMissRate">0%</div>
                    <div class="metric-label">Miss Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="totalCacheRequests">0</div>
                    <div class="metric-label">Total Requests</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="cacheEvictions">0</div>
                    <div class="metric-label">Evictions</div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="cacheChart"></canvas>
            </div>
        </div>

        <!-- Alerts Card -->
        <div class="card">
            <h3>Active Alerts</h3>
            <div id="alertsContainer">
                <div style="text-align: center; opacity: 0.6; margin: 2rem 0;">
                    No active alerts
                </div>
            </div>
        </div>
    </div>

    <div class="connection-status" id="connectionStatus">
        <div class="status-dot"></div>
        <span>Connected</span>
    </div>

    <script>
        let ws;
        let charts = {};
        let autoRefresh = true;
        let metricsData = {};

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
            initializeCharts();
            updateConnectionStatus(false);
        });

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            ws = new WebSocket(\`\${protocol}//\${host}\`);

            ws.onopen = function() {
                console.log('WebSocket connected');
                updateConnectionStatus(true);

                // Subscribe to all metrics
                ws.send(JSON.stringify({
                    type: 'subscribe',
                    metrics: ['phase', 'performance', 'system', 'agents', 'cache', 'gates', 'errors']
                }));
            };

            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            ws.onclose = function() {
                console.log('WebSocket disconnected');
                updateConnectionStatus(false);

                // Attempt to reconnect after 5 seconds
                setTimeout(connectWebSocket, 5000);
            };

            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
                updateConnectionStatus(false);
            };
        }

        function handleWebSocketMessage(data) {
            switch (data.type) {
                case 'initial':
                    handleInitialData(data.data);
                    break;
                case 'metric':
                    handleMetricUpdate(data);
                    break;
                case 'status-update':
                    handleStatusUpdate(data.data);
                    break;
                case 'error':
                    console.error('Server error:', data.message);
                    break;
                case 'pong':
                    // Handle keepalive response
                    break;
            }
        }

        function handleInitialData(data) {
            metricsData = data.metrics || {};
            updateAllWidgets();
        }

        function handleMetricUpdate(data) {
            const { name, data: metricData } = data;

            if (!metricsData[name]) {
                metricsData[name] = [];
            }

            metricsData[name].push({
                timestamp: Date.now(),
                data: metricData
            });

            // Keep only last 100 data points per metric
            if (metricsData[name].length > 100) {
                metricsData[name] = metricsData[name].slice(-100);
            }

            updateSpecificWidget(name, metricData);
        }

        function handleStatusUpdate(status) {
            document.getElementById('statusText').textContent =
                \`System Active - \${status.connectedClients} clients\`;
        }

        function updateAllWidgets() {
            for (const [metricName, metricArray] of Object.entries(metricsData)) {
                if (metricArray.length > 0) {
                    const latest = metricArray[metricArray.length - 1].data;
                    updateSpecificWidget(metricName, latest);
                }
            }
        }

        function updateSpecificWidget(metricName, data) {
            switch (metricName) {
                case 'phase':
                    updatePhaseWidget(data);
                    break;
                case 'performance':
                    updatePerformanceWidget(data);
                    break;
                case 'system':
                    updateSystemWidget(data);
                    break;
                case 'agents':
                    updateAgentsWidget(data);
                    break;
                case 'cache':
                    updateCacheWidget(data);
                    break;
                case 'gates':
                    updateGatesWidget(data);
                    break;
                case 'errors':
                    updateErrorsWidget(data);
                    break;
            }
        }

        function updatePhaseWidget(data) {
            const phaseNames = {
                'phase_0': 'Git Branch Creation',
                'phase_1': 'Requirements Analysis',
                'phase_2': 'Design Planning',
                'phase_3': 'Implementation',
                'phase_4': 'Local Testing',
                'phase_5': 'Code Commit',
                'phase_6': 'Code Review',
                'phase_7': 'Merge & Deploy'
            };

            document.getElementById('currentPhase').textContent = phaseNames[data.phase] || data.phase;
            document.getElementById('phaseProgress').textContent = \`\${Math.round(data.progress || 0)}%\`;
            document.getElementById('phaseProgressBar').style.width = \`\${data.progress || 0}%\`;

            const duration = data.duration ? \`Duration: \${Math.round(data.duration / 1000)}s\` : '';
            document.getElementById('phaseDetails').textContent = duration;
        }

        function updatePerformanceWidget(data) {
            document.getElementById('responseTime').textContent = \`\${Math.round(data.responseTime || 0)}ms\`;
            document.getElementById('throughput').textContent = \`\${Math.round(data.throughput || 0)}/s\`;
            document.getElementById('errorRate').textContent = \`\${((data.errorRate || 0) * 100).toFixed(1)}%\`;
            document.getElementById('activeConnections').textContent = data.activeConnections || 0;

            updatePerformanceChart();
        }

        function updateSystemWidget(data) {
            document.getElementById('cpuUsage').textContent = \`\${Math.round(data.cpu || 0)}%\`;
            document.getElementById('memoryUsage').textContent = \`\${Math.round(data.memory || 0)}%\`;
            document.getElementById('diskUsage').textContent = \`\${Math.round(data.disk || 0)}%\`;
            document.getElementById('networkUsage').textContent = \`\${Math.round(data.network || 0)}%\`;

            updateSystemChart();
        }

        function updateAgentsWidget(data) {
            const summary = data.summary || {};

            document.getElementById('totalAgents').textContent = summary.total || 0;
            document.getElementById('runningAgents').textContent = summary.running || 0;
            document.getElementById('idleAgents').textContent = summary.idle || 0;
            document.getElementById('successRate').textContent = \`\${(summary.successRate * 100 || 0).toFixed(1)}%\`;

            updateAgentTable(data.agents || {});
        }

        function updateAgentTable(agents) {
            const tbody = document.querySelector('#agentTable tbody');
            tbody.innerHTML = '';

            for (const [name, status] of Object.entries(agents)) {
                const row = tbody.insertRow();

                const nameCell = row.insertCell();
                nameCell.textContent = name.replace(/-/g, ' ');

                const statusCell = row.insertCell();
                statusCell.textContent = status.status;
                statusCell.className = \`status-\${status.status}\`;

                const durationCell = row.insertCell();
                durationCell.textContent = status.duration > 0 ? \`\${status.duration}ms\` : '-';

                const successCell = row.insertCell();
                successCell.textContent = status.success ? '✓' : '✗';
                successCell.style.color = status.success ? '#4CAF50' : '#F44336';
            }
        }

        function updateCacheWidget(data) {
            document.getElementById('cacheHitRate').textContent = \`\${data.hitRate?.toFixed(1) || 0}%\`;
            document.getElementById('cacheMissRate').textContent = \`\${data.missRate?.toFixed(1) || 0}%\`;
            document.getElementById('totalCacheRequests').textContent = data.totalRequests || 0;
            document.getElementById('cacheEvictions').textContent = data.evictions || 0;

            updateCacheChart();
        }

        function updateGatesWidget(data) {
            // Gates are handled as part of alerts for now
        }

        function updateErrorsWidget(data) {
            // Update alerts with error information
            updateAlerts();
        }

        function initializeCharts() {
            // Performance Chart
            const performanceCtx = document.getElementById('performanceChart').getContext('2d');
            charts.performance = new Chart(performanceCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Response Time (ms)',
                        data: [],
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { color: 'rgba(255, 255, 255, 0.7)' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        },
                        x: {
                            ticks: { color: 'rgba(255, 255, 255, 0.7)' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: { color: 'rgba(255, 255, 255, 0.9)' }
                        }
                    }
                }
            });

            // System Chart
            const systemCtx = document.getElementById('systemChart').getContext('2d');
            charts.system = new Chart(systemCtx, {
                type: 'bar',
                data: {
                    labels: ['CPU', 'Memory', 'Disk', 'Network'],
                    datasets: [{
                        label: 'Usage %',
                        data: [0, 0, 0, 0],
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.8)',
                            'rgba(54, 162, 235, 0.8)',
                            'rgba(255, 205, 86, 0.8)',
                            'rgba(75, 192, 192, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: { color: 'rgba(255, 255, 255, 0.7)' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        },
                        x: {
                            ticks: { color: 'rgba(255, 255, 255, 0.7)' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: { color: 'rgba(255, 255, 255, 0.9)' }
                        }
                    }
                }
            });

            // Cache Chart
            const cacheCtx = document.getElementById('cacheChart').getContext('2d');
            charts.cache = new Chart(cacheCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Hits', 'Misses'],
                    datasets: [{
                        data: [80, 20],
                        backgroundColor: ['#4CAF50', '#F44336']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: 'rgba(255, 255, 255, 0.9)' }
                        }
                    }
                }
            });
        }

        function updatePerformanceChart() {
            if (!metricsData.performance || !charts.performance) return;

            const data = metricsData.performance.slice(-20); // Last 20 data points
            const labels = data.map(d => new Date(d.timestamp).toLocaleTimeString());
            const values = data.map(d => d.data.responseTime || 0);

            charts.performance.data.labels = labels;
            charts.performance.data.datasets[0].data = values;
            charts.performance.update('none');
        }

        function updateSystemChart() {
            if (!metricsData.system || !charts.system) return;

            const latest = metricsData.system[metricsData.system.length - 1].data;
            charts.system.data.datasets[0].data = [
                latest.cpu || 0,
                latest.memory || 0,
                latest.disk || 0,
                latest.network || 0
            ];
            charts.system.update('none');
        }

        function updateCacheChart() {
            if (!metricsData.cache || !charts.cache) return;

            const latest = metricsData.cache[metricsData.cache.length - 1].data;
            charts.cache.data.datasets[0].data = [
                latest.hitRate || 0,
                latest.missRate || 0
            ];
            charts.cache.update('none');
        }

        function updateAlerts() {
            // This would fetch and display alerts from the server
            fetch('/api/alerts')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayAlerts(data.data);
                    }
                })
                .catch(error => console.error('Error fetching alerts:', error));
        }

        function displayAlerts(alerts) {
            const container = document.getElementById('alertsContainer');

            if (!alerts || alerts.length === 0) {
                container.innerHTML = \`
                    <div style="text-align: center; opacity: 0.6; margin: 2rem 0;">
                        No active alerts
                    </div>
                \`;
                return;
            }

            container.innerHTML = alerts.map(alert => \`
                <div class="alert alert-\${alert.type}">
                    <strong>\${alert.category.toUpperCase()}:</strong>
                    \${alert.message}
                    <small style="margin-left: auto; opacity: 0.8;">
                        \${new Date(alert.timestamp).toLocaleTimeString()}
                    </small>
                </div>
            \`).join('');
        }

        function updateConnectionStatus(connected) {
            const status = document.getElementById('connectionStatus');
            const statusText = status.querySelector('span');

            if (connected) {
                status.classList.remove('disconnected');
                statusText.textContent = 'Connected';
            } else {
                status.classList.add('disconnected');
                statusText.textContent = 'Disconnected';
            }
        }

        // Control functions
        function exportMetrics() {
            fetch('/api/export', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(\`Metrics exported successfully: \${data.data.filename}\`);
                    } else {
                        alert(\`Export failed: \${data.error}\`);
                    }
                })
                .catch(error => {
                    console.error('Export error:', error);
                    alert('Export failed');
                });
        }

        function resetMetrics() {
            if (confirm('Are you sure you want to reset all metrics?')) {
                fetch('/api/reset', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            metricsData = {};
                            updateAllWidgets();
                            alert('Metrics reset successfully');
                        } else {
                            alert(\`Reset failed: \${data.error}\`);
                        }
                    })
                    .catch(error => {
                        console.error('Reset error:', error);
                        alert('Reset failed');
                    });
            }
        }

        function toggleAutoRefresh() {
            autoRefresh = !autoRefresh;
            const btn = event.target;
            btn.textContent = \`Auto Refresh: \${autoRefresh ? 'ON' : 'OFF'}\`;

            if (!autoRefresh && ws) {
                // Unsubscribe from updates
                ws.send(JSON.stringify({ type: 'unsubscribe' }));
            } else if (autoRefresh && ws) {
                // Re-subscribe to updates
                ws.send(JSON.stringify({
                    type: 'subscribe',
                    metrics: ['phase', 'performance', 'system', 'agents', 'cache', 'gates', 'errors']
                }));
            }
        }

        // Periodically update alerts
        setInterval(updateAlerts, 5000);

        // Send keepalive pings
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    </script>
</body>
</html>`;

        const webDir = path.join(this.options.staticPath);
        await fs.mkdir(webDir, { recursive: true });
        await fs.writeFile(path.join(webDir, 'index.html'), htmlContent);
    }

    /**
     * Start the web dashboard server
     */
    async start() {
        if (this.isStarted) {
            return this;
        }

        try {
            // Create web dashboard HTML
            await this.createWebDashboardHTML();

            // Start metrics collector
            this.metricsCollector.start();

            // Start server
            await new Promise((resolve, reject) => {
                this.server.listen(this.options.port, this.options.host, (error) => {
                    if (error) {
                        reject(error);
                    } else {
                        resolve();
                    }
                });
            });

            this.isStarted = true;

            console.log(`Web Dashboard started at http://${this.options.host}:${this.options.port}`);
            console.log(`WebSocket endpoint: ws://${this.options.host}:${this.options.port}`);

            return this;

        } catch (error) {
            throw new Error(`Failed to start web dashboard: ${error.message}`);
        }
    }

    /**
     * Stop the web dashboard server
     */
    async stop() {
        if (!this.isStarted) {
            return this;
        }

        try {
            // Stop metrics collector
            this.metricsCollector.stop();

            // Stop broadcast interval
            if (this.broadcastInterval) {
                clearInterval(this.broadcastInterval);
            }

            // Close all WebSocket connections
            for (const client of this.clients) {
                client.close();
            }
            this.clients.clear();

            // Close WebSocket server
            this.wss.close();

            // Stop HTTP server
            await new Promise((resolve) => {
                this.server.close(resolve);
            });

            this.isStarted = false;

            console.log('Web Dashboard stopped');

            return this;

        } catch (error) {
            throw new Error(`Failed to stop web dashboard: ${error.message}`);
        }
    }
}

module.exports = WebDashboard;

// CLI usage
if (require.main === module) {
    const dashboard = new WebDashboard({
        port: process.env.PORT || 3000,
        host: process.env.HOST || 'localhost',
        updateInterval: 1000
    });

    dashboard.start().catch(error => {
        console.error('Failed to start dashboard:', error);
        process.exit(1);
    });

    // Handle graceful shutdown
    process.on('SIGINT', () => {
        console.log('\nStopping web dashboard...');
        dashboard.stop().then(() => {
            process.exit(0);
        });
    });

    process.on('SIGTERM', () => {
        dashboard.stop().then(() => {
            process.exit(0);
        });
    });
}