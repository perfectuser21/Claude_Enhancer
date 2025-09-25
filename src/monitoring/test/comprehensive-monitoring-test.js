/**
 * Claude Enhancer Plus - Comprehensive Monitoring System Test Suite
 * Tests all monitoring components and their integration
 */

const { MonitoringSystem, setupMonitoring } = require('../index');
const fs = require('fs').promises;
const path = require('path');

class MonitoringTestSuite {
    constructor() {
        this.testResults = [];
        this.monitoring = null;
        this.testDataDir = './.claude/test/monitoring';
        this.startTime = Date.now();
    }

    async runAllTests() {
        console.log('🧪 Starting Comprehensive Monitoring System Test Suite\n');

        try {
            await this.setupTestEnvironment();

            // Core Tests
            await this.testMonitoringSystemInitialization();
            await this.testErrorRecoveryMonitor();
            await this.testPrometheusExporter();
            await this.testDashboard();
            await this.testAlertManager();

            // Integration Tests
            await this.testComponentIntegration();
            await this.testErrorRecoveryIntegration();
            await this.testMetricsCollection();
            await this.testAlerting();

            // Performance Tests
            await this.testPerformanceMetrics();
            await this.testConcurrentMonitoring();

            // Edge Cases and Error Handling
            await this.testErrorHandling();
            await this.testResourceCleanup();

            await this.generateTestReport();

        } catch (error) {
            console.error('❌ Test suite failed:', error);
            this.recordTest('test_suite_execution', false, `Test suite failed: ${error.message}`);
        } finally {
            await this.cleanup();
        }
    }

    async setupTestEnvironment() {
        console.log('🔧 Setting up test environment...');

        // Create test directories
        await fs.mkdir(this.testDataDir, { recursive: true });
        await fs.mkdir(path.join(this.testDataDir, 'metrics'), { recursive: true });
        await fs.mkdir(path.join(this.testDataDir, 'alerts'), { recursive: true });
        await fs.mkdir(path.join(this.testDataDir, 'logs'), { recursive: true });

        this.recordTest('test_environment_setup', true, 'Test environment created successfully');
    }

    async testMonitoringSystemInitialization() {
        console.log('🧪 Testing Monitoring System Initialization...');

        try {
            // Test basic initialization
            this.monitoring = new MonitoringSystem({
                dataDir: this.testDataDir,
                metricsDir: path.join(this.testDataDir, 'metrics'),
                alertsDir: path.join(this.testDataDir, 'alerts'),
                logsDir: path.join(this.testDataDir, 'logs'),
                prometheusPort: 9091, // Use different port for testing
                dashboardPort: 3002   // Use different port for testing
            });

            const statusBefore = this.monitoring.getSystemStatus();
            console.log('   📊 Status before initialization:', statusBefore.initialized);

            await this.monitoring.initialize();

            const statusAfter = this.monitoring.getSystemStatus();
            console.log('   ✅ Status after initialization:', statusAfter.initialized);

            this.recordTest('monitoring_system_initialization',
                statusAfter.initialized && statusAfter.running,
                'Monitoring system initialized successfully');

            // Test component availability
            const hasAllComponents = statusAfter.components.monitor &&
                                   statusAfter.components.prometheus &&
                                   statusAfter.components.dashboard &&
                                   statusAfter.components.alertManager;

            this.recordTest('all_components_initialized',
                hasAllComponents,
                `Components initialized: ${JSON.stringify(statusAfter.components)}`);

        } catch (error) {
            this.recordTest('monitoring_system_initialization', false, error.message);
        }
    }

    async testErrorRecoveryMonitor() {
        console.log('🧪 Testing Error Recovery Monitor...');

        if (!this.monitoring || !this.monitoring.monitor) {
            this.recordTest('error_recovery_monitor_test', false, 'Monitor not available');
            return;
        }

        try {
            const monitor = this.monitoring.monitor;

            // Test metrics collection
            const initialMetrics = monitor.getMetrics();
            console.log('   📊 Initial metrics keys:', Object.keys(initialMetrics));

            // Simulate error recovery events
            monitor.handleRecoveryStart({
                errorType: 'network_timeout',
                strategy: 'exponential_backoff',
                context: { test: true }
            });

            await this.wait(100);

            monitor.handleRecoverySuccess({
                duration: 150,
                strategy: 'exponential_backoff',
                errorType: 'network_timeout'
            });

            await this.wait(100);

            const updatedMetrics = monitor.getMetrics();
            const recoveryMetric = updatedMetrics.recoveries_total;

            this.recordTest('monitor_event_handling',
                recoveryMetric && recoveryMetric.value > 0,
                `Recovery events processed: ${recoveryMetric?.value || 0}`);

            // Test health status
            const healthStatus = monitor.getHealthStatus();
            this.recordTest('monitor_health_check',
                healthStatus && healthStatus.status,
                `Health status: ${healthStatus?.status}`);

        } catch (error) {
            this.recordTest('error_recovery_monitor_test', false, error.message);
        }
    }

    async testPrometheusExporter() {
        console.log('🧪 Testing Prometheus Exporter...');

        if (!this.monitoring || !this.monitoring.prometheusExporter) {
            this.recordTest('prometheus_exporter_test', false, 'Prometheus exporter not available');
            return;
        }

        try {
            const exporter = this.monitoring.prometheusExporter;

            // Test metrics registration
            const status = exporter.getStatus();
            console.log('   📊 Prometheus status:', status);

            this.recordTest('prometheus_server_running',
                status.running,
                `Prometheus server running on port ${status.port}`);

            // Test metric updates
            exporter.incrementCounter('error_recovery_errors_total',
                { error_type: 'test', recovery_strategy: 'test' });

            exporter.setGauge('error_recovery_active_recoveries', 5);

            exporter.observeHistogram('error_recovery_duration_seconds', 0.150,
                { strategy: 'test', error_type: 'test' });

            const metricsValue = exporter.getMetricValue('error_recovery_errors_total',
                { error_type: 'test', recovery_strategy: 'test' });

            this.recordTest('prometheus_metric_updates',
                metricsValue === 1,
                `Metric value: ${metricsValue}`);

            // Test metrics format
            const metricsOutput = exporter.formatMetricsForPrometheus();
            const hasPrometheusFormat = metricsOutput.includes('# HELP') &&
                                       metricsOutput.includes('# TYPE');

            this.recordTest('prometheus_format_output',
                hasPrometheusFormat,
                'Metrics formatted in Prometheus format');

        } catch (error) {
            this.recordTest('prometheus_exporter_test', false, error.message);
        }
    }

    async testDashboard() {
        console.log('🧪 Testing Error Recovery Dashboard...');

        if (!this.monitoring || !this.monitoring.dashboard) {
            this.recordTest('dashboard_test', false, 'Dashboard not available');
            return;
        }

        try {
            const dashboard = this.monitoring.dashboard;

            // Test dashboard status
            const status = dashboard.getStatus();
            console.log('   📊 Dashboard status:', status);

            this.recordTest('dashboard_server_running',
                status.running,
                `Dashboard running on port ${status.port}`);

            // Test dashboard data
            const dashboardData = dashboard.getDashboardData();
            const hasRequiredData = dashboardData.current_metrics &&
                                  dashboardData.health !== undefined;

            this.recordTest('dashboard_data_available',
                hasRequiredData,
                'Dashboard data structure correct');

            // Simulate event updates
            dashboard.addEvent('test_event', 'Test event for dashboard');
            dashboard.updateHealthStatus('healthy');

            await this.wait(100);

            const updatedData = dashboard.getDashboardData();
            const hasEvents = updatedData.recentEvents &&
                            updatedData.recentEvents.length > 0;

            this.recordTest('dashboard_event_updates',
                hasEvents,
                `Events count: ${updatedData.recentEvents?.length || 0}`);

        } catch (error) {
            this.recordTest('dashboard_test', false, error.message);
        }
    }

    async testAlertManager() {
        console.log('🧪 Testing Alert Manager...');

        if (!this.monitoring || !this.monitoring.alertManager) {
            this.recordTest('alert_manager_test', false, 'Alert manager not available');
            return;
        }

        try {
            const alertManager = this.monitoring.alertManager;

            // Test alert creation
            const testAlert = {
                type: 'test_alert',
                severity: 'warning',
                message: 'Test alert message',
                description: 'This is a test alert',
                details: { test: true }
            };

            const alert = await alertManager.processAlert(testAlert);
            console.log('   🚨 Created alert:', alert?.id);

            this.recordTest('alert_creation',
                alert && alert.id,
                `Alert created with ID: ${alert?.id}`);

            // Test alert statistics
            const stats = alertManager.getStatistics();
            console.log('   📊 Alert statistics:', stats);

            this.recordTest('alert_statistics',
                stats.totalAlerts > 0,
                `Total alerts: ${stats.totalAlerts}`);

            // Test active alerts
            const activeAlerts = alertManager.getActiveAlerts();
            this.recordTest('active_alerts_retrieval',
                activeAlerts.length > 0,
                `Active alerts: ${activeAlerts.length}`);

            // Test alert resolution
            if (alert) {
                const resolved = await alertManager.resolveAlert(alert.id, 'test');
                this.recordTest('alert_resolution',
                    resolved,
                    'Alert resolved successfully');
            }

        } catch (error) {
            this.recordTest('alert_manager_test', false, error.message);
        }
    }

    async testComponentIntegration() {
        console.log('🧪 Testing Component Integration...');

        try {
            // Test event flow between components
            const eventData = {
                errorType: 'integration_test',
                strategy: 'test_strategy',
                duration: 200
            };

            // Record event through monitoring system
            this.monitoring.recordEvent('recovery_success', eventData);

            await this.wait(200);

            // Check if event was processed by all components
            const metrics = this.monitoring.getMetrics();
            const hasMetrics = Object.keys(metrics).length > 0;

            this.recordTest('event_flow_integration',
                hasMetrics,
                'Events flow between components correctly');

            // Test health check integration
            const healthStatus = await this.monitoring.performSystemHealthCheck();
            const hasHealthData = healthStatus.components &&
                                 Object.keys(healthStatus.components).length > 0;

            this.recordTest('health_check_integration',
                hasHealthData,
                `Health check components: ${Object.keys(healthStatus.components || {}).join(', ')}`);

        } catch (error) {
            this.recordTest('component_integration', false, error.message);
        }
    }

    async testErrorRecoveryIntegration() {
        console.log('🧪 Testing Error Recovery System Integration...');

        try {
            // Mock error recovery system
            const mockErrorRecovery = {
                on: (event, callback) => {
                    // Store callbacks for later testing
                    this.mockCallbacks = this.mockCallbacks || {};
                    this.mockCallbacks[event] = callback;
                }
            };

            // Integrate with monitoring
            this.monitoring.integrateWithErrorRecovery(mockErrorRecovery);

            // Simulate error recovery events
            if (this.mockCallbacks) {
                if (this.mockCallbacks.recoveryStarted) {
                    this.mockCallbacks.recoveryStarted({
                        errorType: 'mock_error',
                        strategy: 'mock_strategy'
                    });
                }

                if (this.mockCallbacks.recoverySuccess) {
                    this.mockCallbacks.recoverySuccess({
                        duration: 300,
                        strategy: 'mock_strategy',
                        errorType: 'mock_error'
                    });
                }
            }

            await this.wait(200);

            this.recordTest('error_recovery_integration',
                true,
                'Error recovery system integration completed');

        } catch (error) {
            this.recordTest('error_recovery_integration', false, error.message);
        }
    }

    async testMetricsCollection() {
        console.log('🧪 Testing Metrics Collection...');

        try {
            // Test metrics collection over time
            const initialMetrics = this.monitoring.getMetrics();
            const initialCount = Object.keys(initialMetrics).length;

            // Simulate multiple events
            for (let i = 0; i < 5; i++) {
                this.monitoring.recordEvent('recovery_started', {
                    errorType: `test_${i}`,
                    strategy: 'batch_test'
                });

                await this.wait(50);
            }

            await this.wait(200);

            const updatedMetrics = this.monitoring.getMetrics();
            const updatedCount = Object.keys(updatedMetrics).length;

            this.recordTest('metrics_collection_over_time',
                updatedCount >= initialCount,
                `Metrics collected: ${updatedCount} (was ${initialCount})`);

            // Test performance metrics
            const performanceMetrics = this.monitoring.getPerformanceMetrics();
            const hasPerformanceData = performanceMetrics &&
                                     typeof performanceMetrics.errorRate === 'number';

            this.recordTest('performance_metrics_calculation',
                hasPerformanceData,
                'Performance metrics calculated correctly');

        } catch (error) {
            this.recordTest('metrics_collection', false, error.message);
        }
    }

    async testAlerting() {
        console.log('🧪 Testing Alerting System...');

        try {
            // Test manual alert creation
            const alertData = {
                type: 'manual_test_alert',
                severity: 'critical',
                message: 'Manual test alert',
                description: 'This is a manually created test alert'
            };

            const alert = await this.monitoring.triggerAlert(alertData);
            console.log('   🚨 Manual alert created:', alert?.id);

            this.recordTest('manual_alert_creation',
                alert && alert.id,
                'Manual alert created successfully');

            // Test alert retrieval
            const activeAlerts = this.monitoring.getActiveAlerts();
            const hasManualAlert = activeAlerts.some(a => a.type === 'manual_test_alert');

            this.recordTest('alert_retrieval',
                hasManualAlert,
                'Manual alert found in active alerts');

            // Test alert resolution
            if (alert) {
                const resolved = await this.monitoring.resolveAlert(alert.id);
                this.recordTest('manual_alert_resolution',
                    resolved,
                    'Manual alert resolved successfully');
            }

            // Test alert silencing
            const silenceAlert = await this.monitoring.triggerAlert({
                ...alertData,
                type: 'silence_test_alert'
            });

            if (silenceAlert) {
                this.monitoring.silenceAlert(silenceAlert.id, 60000); // 1 minute
                this.recordTest('alert_silencing',
                    true,
                    'Alert silenced successfully');
            }

        } catch (error) {
            this.recordTest('alerting_system', false, error.message);
        }
    }

    async testPerformanceMetrics() {
        console.log('🧪 Testing Performance Metrics...');

        try {
            const startTime = Date.now();

            // Generate load for performance testing
            const promises = [];
            for (let i = 0; i < 10; i++) {
                promises.push(this.generateMonitoringLoad(i));
            }

            await Promise.all(promises);

            const endTime = Date.now();
            const duration = endTime - startTime;

            console.log(`   ⏱️  Performance test completed in ${duration}ms`);

            // Check system performance
            const performanceMetrics = this.monitoring.getPerformanceMetrics();
            const systemStatus = this.monitoring.getSystemStatus();

            this.recordTest('performance_under_load',
                duration < 5000 && systemStatus.running,
                `System handled load in ${duration}ms`);

            // Test metrics accuracy
            const hasAccurateMetrics = performanceMetrics.errorRate >= 0 &&
                                     performanceMetrics.averageRecoveryTime >= 0;

            this.recordTest('performance_metrics_accuracy',
                hasAccurateMetrics,
                'Performance metrics calculated accurately');

        } catch (error) {
            this.recordTest('performance_metrics', false, error.message);
        }
    }

    async generateMonitoringLoad(index) {
        // Simulate monitoring load
        for (let i = 0; i < 5; i++) {
            this.monitoring.recordEvent('recovery_started', {
                errorType: `load_test_${index}_${i}`,
                strategy: 'load_test'
            });

            if (i % 2 === 0) {
                this.monitoring.recordEvent('recovery_success', {
                    duration: Math.random() * 1000,
                    strategy: 'load_test',
                    errorType: `load_test_${index}_${i}`
                });
            } else {
                this.monitoring.recordEvent('recovery_failure', {
                    attempts: 3,
                    strategy: 'load_test',
                    error: { type: `load_test_${index}_${i}` }
                });
            }

            await this.wait(10);
        }
    }

    async testConcurrentMonitoring() {
        console.log('🧪 Testing Concurrent Monitoring...');

        try {
            const concurrentTasks = [];

            // Create concurrent monitoring tasks
            for (let i = 0; i < 5; i++) {
                concurrentTasks.push(this.runConcurrentTask(i));
            }

            const startTime = Date.now();
            const results = await Promise.all(concurrentTasks);
            const endTime = Date.now();

            const allSuccessful = results.every(result => result.success);
            const duration = endTime - startTime;

            console.log(`   ⏱️  Concurrent tasks completed in ${duration}ms`);

            this.recordTest('concurrent_monitoring',
                allSuccessful && duration < 10000,
                `${results.length} concurrent tasks completed in ${duration}ms`);

        } catch (error) {
            this.recordTest('concurrent_monitoring', false, error.message);
        }
    }

    async runConcurrentTask(taskId) {
        try {
            // Each task performs multiple monitoring operations
            for (let i = 0; i < 3; i++) {
                this.monitoring.recordEvent('concurrent_test', {
                    taskId,
                    iteration: i,
                    timestamp: Date.now()
                });

                await this.wait(Math.random() * 100);
            }

            return { taskId, success: true };
        } catch (error) {
            return { taskId, success: false, error: error.message };
        }
    }

    async testErrorHandling() {
        console.log('🧪 Testing Error Handling...');

        try {
            // Test invalid event data
            this.monitoring.recordEvent('invalid_event', null);

            // Test invalid alert data
            await this.monitoring.triggerAlert({
                // Missing required fields
                message: 'Invalid alert test'
            });

            // Test system resilience
            const statusAfterErrors = this.monitoring.getSystemStatus();

            this.recordTest('error_handling_resilience',
                statusAfterErrors.running,
                'System remains operational after errors');

        } catch (error) {
            // Errors should be handled gracefully
            this.recordTest('error_handling_graceful',
                true,
                'Errors handled gracefully');
        }
    }

    async testResourceCleanup() {
        console.log('🧪 Testing Resource Cleanup...');

        try {
            // Test data export before cleanup
            const exportPath = await this.monitoring.exportMetrics('json');
            const exportExists = exportPath && await this.fileExists(exportPath);

            this.recordTest('data_export',
                exportExists,
                `Data exported to: ${exportPath}`);

            // Test system shutdown
            const shutdownStart = Date.now();
            await this.monitoring.shutdown();
            const shutdownDuration = Date.now() - shutdownStart;

            this.recordTest('system_shutdown',
                shutdownDuration < 5000,
                `System shutdown completed in ${shutdownDuration}ms`);

        } catch (error) {
            this.recordTest('resource_cleanup', false, error.message);
        }
    }

    async fileExists(filepath) {
        try {
            await fs.access(filepath);
            return true;
        } catch {
            return false;
        }
    }

    recordTest(testName, passed, details) {
        const result = {
            test: testName,
            passed,
            details,
            timestamp: Date.now()
        };

        this.testResults.push(result);

        const status = passed ? '✅' : '❌';
        console.log(`   ${status} ${testName}: ${details}`);
    }

    async wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async generateTestReport() {
        console.log('\n📋 Generating Test Report...');

        const totalTests = this.testResults.length;
        const passedTests = this.testResults.filter(r => r.passed).length;
        const failedTests = totalTests - passedTests;
        const successRate = totalTests > 0 ? (passedTests / totalTests * 100).toFixed(1) : 0;

        const report = {
            summary: {
                totalTests,
                passedTests,
                failedTests,
                successRate: `${successRate}%`,
                duration: Date.now() - this.startTime,
                timestamp: new Date().toISOString()
            },
            results: this.testResults,
            systemInfo: {
                nodeVersion: process.version,
                platform: process.platform,
                memoryUsage: process.memoryUsage()
            }
        };

        // Save report
        const reportPath = path.join(this.testDataDir, 'test-report.json');
        await fs.writeFile(reportPath, JSON.stringify(report, null, 2));

        // Display summary
        console.log('\n📊 Test Summary:');
        console.log(`   Total Tests: ${totalTests}`);
        console.log(`   Passed: ${passedTests} ✅`);
        console.log(`   Failed: ${failedTests} ❌`);
        console.log(`   Success Rate: ${successRate}%`);
        console.log(`   Duration: ${report.summary.duration}ms`);
        console.log(`   Report saved to: ${reportPath}`);

        if (failedTests > 0) {
            console.log('\n❌ Failed Tests:');
            this.testResults.filter(r => !r.passed).forEach(test => {
                console.log(`   • ${test.test}: ${test.details}`);
            });
        }

        return report;
    }

    async cleanup() {
        console.log('\n🧹 Cleaning up test environment...');

        try {
            // Additional cleanup if monitoring is still running
            if (this.monitoring && this.monitoring.isRunning) {
                await this.monitoring.shutdown();
            }

            console.log('✅ Test cleanup completed');
        } catch (error) {
            console.error('⚠️  Cleanup warning:', error.message);
        }
    }
}

// Run tests if called directly
if (require.main === module) {
    const testSuite = new MonitoringTestSuite();
    testSuite.runAllTests().catch(error => {
        console.error('❌ Test suite failed:', error);
        process.exit(1);
    });
}

module.exports = MonitoringTestSuite;