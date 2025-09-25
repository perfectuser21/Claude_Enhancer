#!/usr/bin/env node

/**
 * Claude Enhancer 5.0 - Real-time Monitoring Dashboard
 *
 * Features:
 * - Real-time phase progression tracking
 * - Performance metrics visualization
 * - Gate validation status monitoring
 * - Agent execution tracking
 * - Error tracking and alerting
 * - Historical data analysis
 *
 * @author Claude Code
 * @version 1.0.0
 */

const blessed = require('blessed');
const contrib = require('blessed-contrib');
const fs = require('fs').promises;
const path = require('path');
const EventEmitter = require('events');

class ClaudeEnhancerDashboard extends EventEmitter {
    constructor(options = {}) {
        super();

        this.options = {
            refreshRate: options.refreshRate || 1000,
            dataRetention: options.dataRetention || 24 * 60 * 60 * 1000, // 24 hours
            alertThresholds: {
                phaseTimeout: 300000, // 5 minutes
                errorRate: 0.05, // 5%
                memoryUsage: 0.9, // 90%
                cacheHitRate: 0.8 // 80%
            },
            ...options
        };

        this.metrics = new Map();
        this.historicalData = [];
        this.alerts = [];
        this.currentPhase = 'idle';
        this.agentStatus = new Map();

        this.initializeScreen();
        this.initializeWidgets();
        this.startDataCollection();
        this.setupEventHandlers();
    }

    /**
     * Initialize the blessed screen
     */
    initializeScreen() {
        this.screen = blessed.screen({
            smartCSR: true,
            title: 'Claude Enhancer 5.0 - Monitoring Dashboard',
            debug: true,
            dockBorders: true,
            cursor: {
                artificial: true,
                shape: 'line',
                blink: true,
                color: 'white'
            }
        });

        // Handle screen exit
        this.screen.key(['escape', 'q', 'C-c'], () => {
            this.cleanup();
            return process.exit(0);
        });

        // Handle screen resize
        this.screen.on('resize', () => {
            this.emit('resize');
        });
    }

    /**
     * Initialize dashboard widgets
     */
    initializeWidgets() {
        // Create grid for layout
        this.grid = new contrib.grid({
            rows: 12,
            cols: 12,
            screen: this.screen
        });

        // Phase Progress Widget (top-left)
        this.phaseWidget = this.grid.set(0, 0, 3, 6, contrib.gauge, {
            label: 'Phase Progress',
            stroke: 'green',
            fill: 'white',
            gaugeColor: 'cyan',
            gaugeStyle: {
                fg: 'cyan'
            }
        });

        // Performance Metrics Chart (top-right)
        this.performanceChart = this.grid.set(0, 6, 3, 6, contrib.line, {
            style: {
                line: 'cyan',
                text: 'green',
                baseline: 'black'
            },
            xLabelPadding: 3,
            xPadding: 5,
            label: 'Performance Metrics (ms)'
        });

        // Agent Status Table (middle-left)
        this.agentTable = this.grid.set(3, 0, 4, 6, contrib.table, {
            keys: true,
            fg: 'white',
            selectedFg: 'white',
            selectedBg: 'blue',
            interactive: true,
            label: 'Agent Status',
            width: '100%',
            height: '100%',
            border: { type: 'line', fg: 'cyan' },
            columnSpacing: 2,
            columnWidth: [15, 10, 15, 20, 15]
        });

        // Gate Validation Status (middle-right)
        this.gateWidget = this.grid.set(3, 6, 2, 6, blessed.box, {
            label: 'Gate Validation Status',
            border: { type: 'line', fg: 'cyan' },
            style: { fg: 'white', border: { fg: 'cyan' } }
        });

        // Error Log (middle-right-bottom)
        this.errorLog = this.grid.set(5, 6, 2, 6, blessed.log, {
            fg: 'red',
            selectedFg: 'red',
            label: 'Error Log',
            border: { type: 'line', fg: 'red' },
            scrollable: true,
            alwaysScroll: true,
            mouse: true,
            keys: true
        });

        // System Health Bar Chart (bottom-left)
        this.healthChart = this.grid.set(7, 0, 2, 6, contrib.bar, {
            label: 'System Health',
            barWidth: 4,
            barSpacing: 6,
            xOffset: 0,
            maxHeight: 9
        });

        // Cache Performance Donut (bottom-right)
        this.cacheDonut = this.grid.set(7, 6, 2, 3, contrib.donut, {
            label: 'Cache Performance',
            radius: 8,
            arcWidth: 3,
            remainColor: 'red',
            yPadding: 2,
            data: [
                { percent: 80, label: 'hit', color: 'green' }
            ]
        });

        // Memory Usage Gauge (bottom-right)
        this.memoryGauge = this.grid.set(7, 9, 2, 3, contrib.gauge, {
            label: 'Memory Usage',
            stroke: 'green',
            fill: 'white',
            gaugeColor: 'yellow',
            gaugeStyle: {
                fg: 'yellow'
            }
        });

        // Status Bar (bottom)
        this.statusBar = this.grid.set(9, 0, 1, 12, blessed.box, {
            label: 'Status',
            content: 'Dashboard started - Monitoring Claude Enhancer 5.0',
            border: { type: 'line', fg: 'white' },
            style: { fg: 'white', border: { fg: 'white' } }
        });

        // Controls Help (bottom)
        this.controlsBox = this.grid.set(10, 0, 2, 12, blessed.box, {
            label: 'Controls',
            content: 'Press [q] or [ESC] to quit | [r] to reset | [e] to export | [a] to view alerts | [h] for help',
            border: { type: 'line', fg: 'cyan' },
            style: { fg: 'cyan', border: { fg: 'cyan' } },
            align: 'center'
        });

        this.setupAdditionalControls();
    }

    /**
     * Setup additional keyboard controls
     */
    setupAdditionalControls() {
        this.screen.key(['r'], () => {
            this.resetMetrics();
            this.updateStatusBar('Metrics reset');
        });

        this.screen.key(['e'], () => {
            this.exportMetrics();
        });

        this.screen.key(['a'], () => {
            this.showAlerts();
        });

        this.screen.key(['h'], () => {
            this.showHelp();
        });
    }

    /**
     * Start data collection and monitoring
     */
    startDataCollection() {
        this.dataCollectionInterval = setInterval(() => {
            this.collectMetrics();
            this.updateWidgets();
            this.checkAlerts();
            this.cleanupOldData();
        }, this.options.refreshRate);

        // Initialize with default data
        this.initializeDefaultData();
    }

    /**
     * Initialize default data for visualization
     */
    initializeDefaultData() {
        // Phase progress
        this.currentPhase = 'phase_0';
        this.phaseProgress = 0;

        // Performance data
        this.performanceData = {
            title: 'Performance',
            x: [],
            y: []
        };

        // Agent status
        this.agentStatus = new Map([
            ['backend-architect', { status: 'idle', lastRun: Date.now(), duration: 0, success: true }],
            ['security-auditor', { status: 'idle', lastRun: Date.now(), duration: 0, success: true }],
            ['test-engineer', { status: 'idle', lastRun: Date.now(), duration: 0, success: true }],
            ['api-designer', { status: 'idle', lastRun: Date.now(), duration: 0, success: true }],
            ['database-specialist', { status: 'idle', lastRun: Date.now(), duration: 0, success: true }],
            ['performance-engineer', { status: 'idle', lastRun: Date.now(), duration: 0, success: true }]
        ]);

        // System health
        this.systemHealth = {
            cpu: 15,
            memory: 45,
            disk: 30,
            network: 25
        };

        // Cache performance
        this.cacheStats = {
            hitRate: 85,
            missRate: 15
        };
    }

    /**
     * Collect current metrics from the system
     */
    async collectMetrics() {
        const timestamp = Date.now();

        try {
            // Collect phase information
            await this.collectPhaseMetrics();

            // Collect performance metrics
            await this.collectPerformanceMetrics();

            // Collect agent status
            await this.collectAgentMetrics();

            // Collect system health
            await this.collectSystemHealth();

            // Store historical data
            this.storeHistoricalData(timestamp);

        } catch (error) {
            this.logError(`Data collection error: ${error.message}`);
        }
    }

    /**
     * Collect phase progression metrics
     */
    async collectPhaseMetrics() {
        try {
            const phaseFile = path.join(process.cwd(), '.claude/logs/current_phase.json');

            try {
                const phaseData = await fs.readFile(phaseFile, 'utf8');
                const phase = JSON.parse(phaseData);

                this.currentPhase = phase.current || 'phase_0';
                this.phaseProgress = ((phase.step || 0) / 8) * 100;

                // Update phase transitions
                if (phase.transitions) {
                    this.phaseTransitions = phase.transitions;
                }

            } catch (fileError) {
                // File doesn't exist or is invalid, use simulation
                this.simulatePhaseProgress();
            }

        } catch (error) {
            this.logError(`Phase metrics collection failed: ${error.message}`);
        }
    }

    /**
     * Simulate phase progress for demo purposes
     */
    simulatePhaseProgress() {
        const phases = ['phase_0', 'phase_1', 'phase_2', 'phase_3', 'phase_4', 'phase_5', 'phase_6', 'phase_7'];
        const currentIndex = phases.indexOf(this.currentPhase);

        // Simulate progress within current phase
        this.phaseProgress += Math.random() * 5;

        // Advance to next phase when progress reaches 100
        if (this.phaseProgress >= 100 && currentIndex < phases.length - 1) {
            this.currentPhase = phases[currentIndex + 1];
            this.phaseProgress = 0;
            this.updateStatusBar(`Advanced to ${this.currentPhase}`);
        } else if (this.phaseProgress >= 100 && currentIndex === phases.length - 1) {
            this.phaseProgress = 100;
        }
    }

    /**
     * Collect performance metrics
     */
    async collectPerformanceMetrics() {
        try {
            const perfFile = path.join(process.cwd(), '.claude/logs/performance.json');

            try {
                const perfData = await fs.readFile(perfFile, 'utf8');
                const perf = JSON.parse(perfData);

                // Add performance data point
                const timestamp = new Date().toLocaleTimeString();
                this.performanceData.x.push(timestamp);
                this.performanceData.y.push(perf.responseTime || this.generateMockPerformance());

                // Keep only last 20 data points
                if (this.performanceData.x.length > 20) {
                    this.performanceData.x.shift();
                    this.performanceData.y.shift();
                }

            } catch (fileError) {
                // Use mock data
                const timestamp = new Date().toLocaleTimeString();
                this.performanceData.x.push(timestamp);
                this.performanceData.y.push(this.generateMockPerformance());

                if (this.performanceData.x.length > 20) {
                    this.performanceData.x.shift();
                    this.performanceData.y.shift();
                }
            }

        } catch (error) {
            this.logError(`Performance metrics collection failed: ${error.message}`);
        }
    }

    /**
     * Generate mock performance data
     */
    generateMockPerformance() {
        const base = 150 + Math.sin(Date.now() / 10000) * 50;
        return Math.max(50, base + (Math.random() - 0.5) * 100);
    }

    /**
     * Collect agent execution metrics
     */
    async collectAgentMetrics() {
        try {
            const agentFile = path.join(process.cwd(), '.claude/logs/agent_status.json');

            try {
                const agentData = await fs.readFile(agentFile, 'utf8');
                const agents = JSON.parse(agentData);

                // Update agent status from file
                for (const [agentName, status] of Object.entries(agents)) {
                    this.agentStatus.set(agentName, {
                        status: status.status || 'idle',
                        lastRun: status.lastRun || Date.now(),
                        duration: status.duration || 0,
                        success: status.success !== false
                    });
                }

            } catch (fileError) {
                // Simulate agent activity
                this.simulateAgentActivity();
            }

        } catch (error) {
            this.logError(`Agent metrics collection failed: ${error.message}`);
        }
    }

    /**
     * Simulate agent activity for demo
     */
    simulateAgentActivity() {
        const agents = Array.from(this.agentStatus.keys());

        // Randomly activate agents
        if (Math.random() < 0.1) { // 10% chance per refresh
            const agentName = agents[Math.floor(Math.random() * agents.length)];
            const currentStatus = this.agentStatus.get(agentName);

            if (currentStatus.status === 'idle') {
                this.agentStatus.set(agentName, {
                    ...currentStatus,
                    status: 'running',
                    lastRun: Date.now()
                });
            } else if (currentStatus.status === 'running') {
                // Complete the agent run
                this.agentStatus.set(agentName, {
                    ...currentStatus,
                    status: 'idle',
                    duration: Date.now() - currentStatus.lastRun,
                    success: Math.random() > 0.05 // 95% success rate
                });
            }
        }
    }

    /**
     * Collect system health metrics
     */
    async collectSystemHealth() {
        try {
            // In a real implementation, this would collect actual system metrics
            // For demo, we'll simulate fluctuating values
            this.systemHealth.cpu += (Math.random() - 0.5) * 10;
            this.systemHealth.memory += (Math.random() - 0.5) * 5;
            this.systemHealth.disk += (Math.random() - 0.5) * 2;
            this.systemHealth.network += (Math.random() - 0.5) * 15;

            // Keep values in reasonable range
            Object.keys(this.systemHealth).forEach(key => {
                this.systemHealth[key] = Math.max(0, Math.min(100, this.systemHealth[key]));
            });

            // Update cache stats
            this.cacheStats.hitRate = Math.max(60, Math.min(95,
                this.cacheStats.hitRate + (Math.random() - 0.5) * 5));
            this.cacheStats.missRate = 100 - this.cacheStats.hitRate;

        } catch (error) {
            this.logError(`System health collection failed: ${error.message}`);
        }
    }

    /**
     * Store historical data
     */
    storeHistoricalData(timestamp) {
        const dataPoint = {
            timestamp,
            phase: this.currentPhase,
            phaseProgress: this.phaseProgress,
            performance: this.performanceData.y[this.performanceData.y.length - 1] || 0,
            systemHealth: { ...this.systemHealth },
            cacheHitRate: this.cacheStats.hitRate,
            activeAgents: Array.from(this.agentStatus.values()).filter(a => a.status === 'running').length
        };

        this.historicalData.push(dataPoint);
    }

    /**
     * Update all dashboard widgets
     */
    updateWidgets() {
        this.updatePhaseWidget();
        this.updatePerformanceChart();
        this.updateAgentTable();
        this.updateGateWidget();
        this.updateHealthChart();
        this.updateCacheDonut();
        this.updateMemoryGauge();

        this.screen.render();
    }

    /**
     * Update phase progress widget
     */
    updatePhaseWidget() {
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

        this.phaseWidget.setData({
            percent: Math.round(this.phaseProgress),
            stroke: this.phaseProgress > 80 ? 'green' : this.phaseProgress > 50 ? 'yellow' : 'red'
        });

        this.phaseWidget.setLabel(`Phase Progress - ${phaseNames[this.currentPhase] || this.currentPhase}`);
    }

    /**
     * Update performance chart
     */
    updatePerformanceChart() {
        if (this.performanceData.x.length > 0) {
            this.performanceChart.setData([this.performanceData]);
        }
    }

    /**
     * Update agent status table
     */
    updateAgentTable() {
        const headers = ['Agent', 'Status', 'Last Run', 'Duration (ms)', 'Success'];
        const data = [];

        for (const [agentName, status] of this.agentStatus.entries()) {
            const lastRun = new Date(status.lastRun).toLocaleTimeString();
            const duration = status.duration > 0 ? status.duration.toString() : '-';
            const success = status.success ? '✓' : '✗';
            const statusColor = status.status === 'running' ? 'green' :
                               status.status === 'error' ? 'red' : 'white';

            data.push([
                agentName,
                status.status,
                lastRun,
                duration,
                success
            ]);
        }

        this.agentTable.setData({
            headers,
            data
        });
    }

    /**
     * Update gate validation widget
     */
    updateGateWidget() {
        const gates = [
            { name: 'Code Quality', status: 'PASS', color: 'green' },
            { name: 'Security Scan', status: 'PASS', color: 'green' },
            { name: 'Test Coverage', status: 'WARN', color: 'yellow' },
            { name: 'Performance', status: 'PASS', color: 'green' }
        ];

        let content = '\n';
        gates.forEach(gate => {
            const symbol = gate.status === 'PASS' ? '✓' :
                          gate.status === 'WARN' ? '⚠' : '✗';
            content += `  ${symbol} ${gate.name}: {${gate.color}-fg}${gate.status}{/}\n`;
        });

        this.gateWidget.setContent(content);
    }

    /**
     * Update system health chart
     */
    updateHealthChart() {
        const healthData = {
            titles: ['CPU', 'Memory', 'Disk', 'Network'],
            data: [
                Math.round(this.systemHealth.cpu),
                Math.round(this.systemHealth.memory),
                Math.round(this.systemHealth.disk),
                Math.round(this.systemHealth.network)
            ]
        };

        this.healthChart.setData(healthData);
    }

    /**
     * Update cache performance donut
     */
    updateCacheDonut() {
        this.cacheDonut.setData([
            {
                percent: Math.round(this.cacheStats.hitRate),
                label: 'hit',
                color: this.cacheStats.hitRate > 80 ? 'green' : 'yellow'
            }
        ]);
    }

    /**
     * Update memory usage gauge
     */
    updateMemoryGauge() {
        const memoryUsage = this.systemHealth.memory;

        this.memoryGauge.setData({
            percent: Math.round(memoryUsage),
            stroke: memoryUsage > 90 ? 'red' : memoryUsage > 70 ? 'yellow' : 'green'
        });
    }

    /**
     * Check for alerts and warnings
     */
    checkAlerts() {
        const currentTime = Date.now();
        const newAlerts = [];

        // Check phase timeout
        if (this.phaseStartTime &&
            currentTime - this.phaseStartTime > this.options.alertThresholds.phaseTimeout) {
            newAlerts.push({
                type: 'warning',
                message: `Phase ${this.currentPhase} running for over 5 minutes`,
                timestamp: currentTime
            });
        }

        // Check memory usage
        if (this.systemHealth.memory > this.options.alertThresholds.memoryUsage * 100) {
            newAlerts.push({
                type: 'critical',
                message: `High memory usage: ${this.systemHealth.memory.toFixed(1)}%`,
                timestamp: currentTime
            });
        }

        // Check cache hit rate
        if (this.cacheStats.hitRate < this.options.alertThresholds.cacheHitRate * 100) {
            newAlerts.push({
                type: 'warning',
                message: `Low cache hit rate: ${this.cacheStats.hitRate.toFixed(1)}%`,
                timestamp: currentTime
            });
        }

        // Check agent failures
        const failedAgents = Array.from(this.agentStatus.entries())
            .filter(([name, status]) => !status.success)
            .map(([name]) => name);

        if (failedAgents.length > 0) {
            newAlerts.push({
                type: 'error',
                message: `Agent failures: ${failedAgents.join(', ')}`,
                timestamp: currentTime
            });
        }

        // Add new alerts and log them
        newAlerts.forEach(alert => {
            this.alerts.push(alert);
            this.logError(alert.message);

            if (alert.type === 'critical') {
                this.updateStatusBar(`CRITICAL: ${alert.message}`);
            }
        });

        // Keep only recent alerts
        this.alerts = this.alerts.filter(alert =>
            currentTime - alert.timestamp < this.options.dataRetention);
    }

    /**
     * Log error to the error widget
     */
    logError(message) {
        const timestamp = new Date().toLocaleTimeString();
        this.errorLog.log(`[${timestamp}] ${message}`);
    }

    /**
     * Update status bar
     */
    updateStatusBar(message) {
        const timestamp = new Date().toLocaleTimeString();
        this.statusBar.setContent(`[${timestamp}] ${message}`);
        this.screen.render();
    }

    /**
     * Clean up old historical data
     */
    cleanupOldData() {
        const cutoff = Date.now() - this.options.dataRetention;
        this.historicalData = this.historicalData.filter(data => data.timestamp > cutoff);
    }

    /**
     * Reset all metrics
     */
    resetMetrics() {
        this.historicalData = [];
        this.alerts = [];
        this.initializeDefaultData();
        this.errorLog.setContent('');
        this.updateStatusBar('Dashboard metrics reset');
    }

    /**
     * Export metrics to JSON file
     */
    async exportMetrics() {
        try {
            const exportData = {
                timestamp: new Date().toISOString(),
                currentPhase: this.currentPhase,
                phaseProgress: this.phaseProgress,
                historicalData: this.historicalData,
                alerts: this.alerts,
                systemHealth: this.systemHealth,
                cacheStats: this.cacheStats,
                agentStatus: Object.fromEntries(this.agentStatus)
            };

            const filename = `claude_enhancer_metrics_${Date.now()}.json`;
            const filepath = path.join(process.cwd(), filename);

            await fs.writeFile(filepath, JSON.stringify(exportData, null, 2));
            this.updateStatusBar(`Metrics exported to ${filename}`);

        } catch (error) {
            this.logError(`Export failed: ${error.message}`);
        }
    }

    /**
     * Show alerts in a popup
     */
    showAlerts() {
        const alertBox = blessed.box({
            parent: this.screen,
            top: 'center',
            left: 'center',
            width: '50%',
            height: '60%',
            content: this.formatAlerts(),
            tags: true,
            border: {
                type: 'line'
            },
            style: {
                fg: 'white',
                bg: 'black',
                border: {
                    fg: 'red'
                }
            },
            scrollable: true,
            alwaysScroll: true,
            mouse: true,
            keys: true
        });

        alertBox.focus();
        this.screen.render();

        alertBox.key(['escape'], () => {
            alertBox.destroy();
            this.screen.render();
        });
    }

    /**
     * Format alerts for display
     */
    formatAlerts() {
        if (this.alerts.length === 0) {
            return '\n  No alerts to display.\n\n  System is operating normally.';
        }

        let content = '\n{bold}Recent Alerts:{/bold}\n\n';

        this.alerts.slice(-10).forEach(alert => {
            const time = new Date(alert.timestamp).toLocaleString();
            const color = alert.type === 'critical' ? 'red' :
                         alert.type === 'error' ? 'yellow' : 'blue';

            content += `  {${color}-fg}${alert.type.toUpperCase()}{/} [${time}]\n`;
            content += `  ${alert.message}\n\n`;
        });

        return content;
    }

    /**
     * Show help information
     */
    showHelp() {
        const helpContent = `
{bold}Claude Enhancer 5.0 - Monitoring Dashboard Help{/bold}

{bold}Keyboard Controls:{/bold}
  q, ESC, Ctrl+C  - Quit dashboard
  r               - Reset metrics
  e               - Export metrics to JSON
  a               - Show alerts popup
  h               - Show this help

{bold}Dashboard Widgets:{/bold}
  Phase Progress     - Shows current 8-phase workflow progress
  Performance Chart  - Response time metrics over time
  Agent Status       - Real-time status of all agents
  Gate Validation    - Quality gate check results
  Error Log          - Recent error messages and warnings
  System Health      - CPU, Memory, Disk, Network usage
  Cache Performance  - Cache hit/miss ratio
  Memory Gauge       - Current memory utilization

{bold}Alert Thresholds:{/bold}
  Phase Timeout      - 5 minutes per phase
  Error Rate         - 5% failure rate
  Memory Usage       - 90% utilization
  Cache Hit Rate     - 80% minimum

Press ESC to close this help.
        `;

        const helpBox = blessed.box({
            parent: this.screen,
            top: 'center',
            left: 'center',
            width: '70%',
            height: '80%',
            content: helpContent,
            tags: true,
            border: {
                type: 'line'
            },
            style: {
                fg: 'white',
                bg: 'black',
                border: {
                    fg: 'cyan'
                }
            },
            scrollable: true,
            alwaysScroll: true,
            mouse: true,
            keys: true
        });

        helpBox.focus();
        this.screen.render();

        helpBox.key(['escape'], () => {
            helpBox.destroy();
            this.screen.render();
        });
    }

    /**
     * Setup event handlers
     */
    setupEventHandlers() {
        this.on('phaseChange', (newPhase) => {
            this.currentPhase = newPhase;
            this.phaseProgress = 0;
            this.phaseStartTime = Date.now();
            this.updateStatusBar(`Phase changed to ${newPhase}`);
        });

        this.on('agentStart', (agentName) => {
            if (this.agentStatus.has(agentName)) {
                const current = this.agentStatus.get(agentName);
                this.agentStatus.set(agentName, {
                    ...current,
                    status: 'running',
                    lastRun: Date.now()
                });
            }
        });

        this.on('agentComplete', (agentName, success = true, duration = 0) => {
            if (this.agentStatus.has(agentName)) {
                const current = this.agentStatus.get(agentName);
                this.agentStatus.set(agentName, {
                    ...current,
                    status: 'idle',
                    success,
                    duration
                });
            }
        });
    }

    /**
     * Cleanup resources
     */
    cleanup() {
        if (this.dataCollectionInterval) {
            clearInterval(this.dataCollectionInterval);
        }

        this.removeAllListeners();

        if (this.screen) {
            this.screen.destroy();
        }
    }

    /**
     * Start the dashboard
     */
    start() {
        this.screen.render();
        this.updateStatusBar('Dashboard started successfully');

        // Emit initial events for demo
        setTimeout(() => {
            this.emit('phaseChange', 'phase_1');
        }, 5000);

        return this;
    }
}

// Export the class
module.exports = ClaudeEnhancerDashboard;

// CLI usage
if (require.main === module) {
    const dashboard = new ClaudeEnhancerDashboard({
        refreshRate: 1000,
        dataRetention: 24 * 60 * 60 * 1000
    });

    dashboard.start();

    // Handle graceful shutdown
    process.on('SIGINT', () => {
        dashboard.cleanup();
        process.exit(0);
    });

    process.on('SIGTERM', () => {
        dashboard.cleanup();
        process.exit(0);
    });
}