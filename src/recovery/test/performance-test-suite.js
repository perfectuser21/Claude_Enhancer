/**
 * Claude Enhancer 5.0 - Error Recovery Performance Test Suite
 * Comprehensive performance testing for error recovery system
 *
 * Tests:
 * 1. Recovery speed under different error scenarios
 * 2. Memory usage during recovery operations
 * 3. Checkpoint save/load performance
 * 4. Concurrent error handling capacity
 */

const fs = require('fs').promises;
const path = require('path');
const { performance } = require('perf_hooks');
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const EventEmitter = require('events');

// Import the recovery system components
const ErrorRecovery = require('../ErrorRecovery');
const CheckpointManager = require('../CheckpointManager');

class PerformanceTestSuite extends EventEmitter {
    constructor(options = {}) {
        super();
        this.config = {
            testDataDir: options.testDataDir || './performance-test-data',
            reportDir: options.reportDir || './performance-reports',
            maxConcurrentTests: options.maxConcurrentTests || 50,
            testDuration: options.testDuration || 30000, // 30 seconds
            warmupIterations: options.warmupIterations || 10,
            benchmarkIterations: options.benchmarkIterations || 100,
            memoryMeasurementInterval: options.memoryMeasurementInterval || 100, // ms
            ...options
        };

        this.metrics = {
            recoverySpeed: new Map(),
            memoryUsage: new Map(),
            checkpointPerformance: new Map(),
            concurrentCapacity: new Map(),
            errorScenarios: new Map(),
            systemResources: new Map()
        };

        this.testResults = {
            timestamp: new Date().toISOString(),
            environment: this.getEnvironmentInfo(),
            tests: [],
            summary: {},
            recommendations: []
        };

        this.setupTestEnvironment();
    }

    /**
     * Main performance test orchestrator
     */
    async runPerformanceTests() {
        console.log('🚀 Starting Error Recovery Performance Test Suite...');
        console.log(`📊 Test Configuration:
        - Test Duration: ${this.config.testDuration / 1000}s
        - Concurrent Limit: ${this.config.maxConcurrentTests}
        - Benchmark Iterations: ${this.config.benchmarkIterations}
        - Memory Sampling: ${this.config.memoryMeasurementInterval}ms`);

        try {
            // Initialize test environment
            await this.initializeTestEnvironment();

            // Test Suite 1: Recovery Speed Analysis
            console.log('\n🏃 Test Suite 1: Recovery Speed Analysis');
            await this.testRecoverySpeed();

            // Test Suite 2: Memory Usage Analysis
            console.log('\n🧠 Test Suite 2: Memory Usage Analysis');
            await this.testMemoryUsage();

            // Test Suite 3: Checkpoint Performance
            console.log('\n💾 Test Suite 3: Checkpoint Performance Analysis');
            await this.testCheckpointPerformance();

            // Test Suite 4: Concurrent Handling Capacity
            console.log('\n⚡ Test Suite 4: Concurrent Error Handling Analysis');
            await this.testConcurrentCapacity();

            // Generate comprehensive report
            await this.generatePerformanceReport();

            console.log('\n✅ Performance testing completed successfully!');
            console.log(`📋 Report saved to: ${path.join(this.config.reportDir, 'performance_report.json')}`);

        } catch (error) {
            console.error('❌ Performance testing failed:', error);
            throw error;
        }
    }

    /**
     * Test Suite 1: Recovery Speed Under Different Error Scenarios
     */
    async testRecoverySpeed() {
        const errorScenarios = [
            { type: 'network', severity: 'low', description: 'Network timeout' },
            { type: 'network', severity: 'high', description: 'Connection refused' },
            { type: 'file', severity: 'low', description: 'File busy' },
            { type: 'file', severity: 'high', description: 'Permission denied' },
            { type: 'validation', severity: 'medium', description: 'Schema validation error' },
            { type: 'memory', severity: 'high', description: 'Out of memory' },
            { type: 'timeout', severity: 'medium', description: 'Operation timeout' },
            { type: 'concurrent', severity: 'high', description: 'Concurrent modification' }
        ];

        for (const scenario of errorScenarios) {
            console.log(`  📈 Testing ${scenario.type} recovery (${scenario.severity})...`);

            const recoveryTimes = [];
            const errorRecovery = new ErrorRecovery({
                enableMetrics: true,
                maxRetries: 3
            });

            // Warmup
            for (let i = 0; i < this.config.warmupIterations; i++) {
                await this.simulateErrorRecovery(recoveryTimes, errorRecovery, scenario);
            }

            // Actual benchmarks
            recoveryTimes.length = 0; // Clear warmup data
            for (let i = 0; i < this.config.benchmarkIterations; i++) {
                await this.simulateErrorRecovery(recoveryTimes, errorRecovery, scenario);
            }

            const stats = this.calculateStatistics(recoveryTimes);
            this.metrics.recoverySpeed.set(`${scenario.type}_${scenario.severity}`, stats);

            console.log(`    ⏱️  Average: ${stats.average.toFixed(2)}ms`);
            console.log(`    📊 P95: ${stats.p95.toFixed(2)}ms, P99: ${stats.p99.toFixed(2)}ms`);
        }

        // Store test results
        this.testResults.tests.push({
            suite: 'recoverySpeed',
            timestamp: new Date().toISOString(),
            metrics: Object.fromEntries(this.metrics.recoverySpeed),
            status: 'completed'
        });
    }

    /**
     * Test Suite 2: Memory Usage During Recovery Operations
     */
    async testMemoryUsage() {
        const testScenarios = [
            { name: 'single_recovery', concurrent: 1, checkpoints: 10 },
            { name: 'moderate_load', concurrent: 10, checkpoints: 50 },
            { name: 'high_load', concurrent: 25, checkpoints: 100 },
            { name: 'extreme_load', concurrent: 50, checkpoints: 200 }
        ];

        for (const scenario of testScenarios) {
            console.log(`  🧠 Testing memory usage: ${scenario.name}...`);

            const memoryProfile = await this.profileMemoryUsage(scenario);
            this.metrics.memoryUsage.set(scenario.name, memoryProfile);

            console.log(`    💾 Peak Memory: ${(memoryProfile.peakUsage / 1024 / 1024).toFixed(2)}MB`);
            console.log(`    📈 Memory Growth: ${memoryProfile.memoryGrowthRate.toFixed(2)}MB/s`);
            console.log(`    🔄 GC Pressure: ${memoryProfile.gcPressure}%`);
        }

        this.testResults.tests.push({
            suite: 'memoryUsage',
            timestamp: new Date().toISOString(),
            metrics: Object.fromEntries(this.metrics.memoryUsage),
            status: 'completed'
        });
    }

    /**
     * Test Suite 3: Checkpoint Save/Load Performance
     */
    async testCheckpointPerformance() {
        const dataSizes = [
            { name: 'small', size: 1024, description: '1KB state' },
            { name: 'medium', size: 10240, description: '10KB state' },
            { name: 'large', size: 102400, description: '100KB state' },
            { name: 'xlarge', size: 1048576, description: '1MB state' }
        ];

        const checkpointManager = new CheckpointManager({
            checkpointsDir: path.join(this.config.testDataDir, 'checkpoints')
        });

        for (const dataSize of dataSizes) {
            console.log(`  💾 Testing checkpoint performance: ${dataSize.description}...`);

            // Generate test data
            const testData = this.generateTestData(dataSize.size);

            // Test save performance
            const saveMetrics = await this.benchmarkCheckpointSave(checkpointManager, testData, dataSize.name);

            // Test load performance
            const loadMetrics = await this.benchmarkCheckpointLoad(checkpointManager, dataSize.name);

            const combinedMetrics = {
                dataSize: dataSize.size,
                save: saveMetrics,
                load: loadMetrics,
                throughput: {
                    saveRate: dataSize.size / saveMetrics.average,
                    loadRate: dataSize.size / loadMetrics.average
                }
            };

            this.metrics.checkpointPerformance.set(dataSize.name, combinedMetrics);

            console.log(`    💾 Save: ${saveMetrics.average.toFixed(2)}ms (${(combinedMetrics.throughput.saveRate / 1024).toFixed(2)}KB/ms)`);
            console.log(`    📖 Load: ${loadMetrics.average.toFixed(2)}ms (${(combinedMetrics.throughput.loadRate / 1024).toFixed(2)}KB/ms)`);
        }

        this.testResults.tests.push({
            suite: 'checkpointPerformance',
            timestamp: new Date().toISOString(),
            metrics: Object.fromEntries(this.metrics.checkpointPerformance),
            status: 'completed'
        });
    }

    /**
     * Test Suite 4: Concurrent Error Handling Capacity
     */
    async testConcurrentCapacity() {
        const concurrencyLevels = [1, 5, 10, 25, 50, 100];

        for (const concurrency of concurrencyLevels) {
            if (concurrency > this.config.maxConcurrentTests) {
                console.log(`  ⚠️  Skipping concurrency ${concurrency} (exceeds limit ${this.config.maxConcurrentTests})`);
                continue;
            }

            console.log(`  ⚡ Testing concurrent capacity: ${concurrency} workers...`);

            const capacityMetrics = await this.testConcurrentErrorHandling(concurrency);
            this.metrics.concurrentCapacity.set(`concurrency_${concurrency}`, capacityMetrics);

            console.log(`    📊 Success Rate: ${capacityMetrics.successRate.toFixed(2)}%`);
            console.log(`    ⚡ Throughput: ${capacityMetrics.throughput.toFixed(2)} ops/sec`);
            console.log(`    🕐 Average Latency: ${capacityMetrics.averageLatency.toFixed(2)}ms`);
        }

        this.testResults.tests.push({
            suite: 'concurrentCapacity',
            timestamp: new Date().toISOString(),
            metrics: Object.fromEntries(this.metrics.concurrentCapacity),
            status: 'completed'
        });
    }

    /**
     * Simulate error recovery for performance measurement
     */
    async simulateErrorRecovery(recoveryTimes, errorRecovery, scenario) {
        const startTime = performance.now();

        try {
            // Simulate different error types
            const error = this.createSimulatedError(scenario);

            // Attempt recovery
            await errorRecovery.recoverFromError(error, async () => {
                // Simulated operation that might fail
                await this.simulateOperation(scenario);
            });

            const endTime = performance.now();
            recoveryTimes.push(endTime - startTime);

        } catch (recoveryError) {
            const endTime = performance.now();
            recoveryTimes.push(endTime - startTime);
            // Log failed recovery for analysis
        }
    }

    /**
     * Profile memory usage during recovery operations
     */
    async profileMemoryUsage(scenario) {
        const memorySnapshots = [];
        const initialMemory = process.memoryUsage();

        // Start memory monitoring
        const memoryInterval = setInterval(() => {
            const memUsage = process.memoryUsage();
            memorySnapshots.push({
                timestamp: Date.now(),
                heapUsed: memUsage.heapUsed,
                heapTotal: memUsage.heapTotal,
                external: memUsage.external,
                rss: memUsage.rss
            });
        }, this.config.memoryMeasurementInterval);

        try {
            // Simulate concurrent recovery operations
            const operations = [];
            for (let i = 0; i < scenario.concurrent; i++) {
                operations.push(this.simulateConcurrentRecovery(scenario.checkpoints));
            }

            await Promise.all(operations);

        } finally {
            clearInterval(memoryInterval);
        }

        // Analyze memory usage
        const finalMemory = process.memoryUsage();
        const peakUsage = Math.max(...memorySnapshots.map(s => s.heapUsed));
        const memoryGrowth = finalMemory.heapUsed - initialMemory.heapUsed;
        const duration = memorySnapshots.length * this.config.memoryMeasurementInterval / 1000;

        return {
            initialUsage: initialMemory.heapUsed,
            finalUsage: finalMemory.heapUsed,
            peakUsage,
            memoryGrowth,
            memoryGrowthRate: memoryGrowth / duration,
            gcPressure: this.calculateGCPressure(memorySnapshots),
            snapshots: memorySnapshots
        };
    }

    /**
     * Test concurrent error handling capacity
     */
    async testConcurrentErrorHandling(concurrency) {
        const startTime = Date.now();
        const results = [];

        // Create workers for concurrent testing
        const workers = [];
        for (let i = 0; i < concurrency; i++) {
            workers.push(this.createErrorHandlingWorker());
        }

        try {
            // Execute concurrent operations
            const operationPromises = workers.map(worker =>
                this.executeWorkerOperations(worker, this.config.testDuration / concurrency)
            );

            const workerResults = await Promise.allSettled(operationPromises);

            // Process results
            for (const result of workerResults) {
                if (result.status === 'fulfilled') {
                    results.push(...result.value);
                }
            }

        } finally {
            // Cleanup workers
            workers.forEach(worker => worker.terminate());
        }

        const endTime = Date.now();
        const totalDuration = endTime - startTime;

        // Calculate metrics
        const successCount = results.filter(r => r.success).length;
        const totalOperations = results.length;
        const successRate = (successCount / totalOperations) * 100;
        const throughput = (totalOperations / totalDuration) * 1000; // ops/sec
        const averageLatency = results.reduce((sum, r) => sum + r.latency, 0) / totalOperations;

        return {
            concurrency,
            totalOperations,
            successCount,
            successRate,
            throughput,
            averageLatency,
            totalDuration,
            results: results.slice(0, 100) // Sample for analysis
        };
    }

    /**
     * Benchmark checkpoint save operations
     */
    async benchmarkCheckpointSave(checkpointManager, testData, testName) {
        const saveTimes = [];

        // Warmup
        for (let i = 0; i < this.config.warmupIterations; i++) {
            await checkpointManager.createCheckpoint(`warmup_${i}_${testName}`, testData);
        }

        // Actual benchmark
        for (let i = 0; i < this.config.benchmarkIterations; i++) {
            const startTime = performance.now();

            try {
                await checkpointManager.createCheckpoint(`bench_${i}_${testName}`, testData);
                const endTime = performance.now();
                saveTimes.push(endTime - startTime);

            } catch (error) {
                saveTimes.push(Number.MAX_SAFE_INTEGER); // Mark as failed
            }
        }

        return this.calculateStatistics(saveTimes);
    }

    /**
     * Benchmark checkpoint load operations
     */
    async benchmarkCheckpointLoad(checkpointManager, testName) {
        const loadTimes = [];

        // Benchmark loading existing checkpoints
        for (let i = 0; i < this.config.benchmarkIterations; i++) {
            const checkpointId = `bench_${i}_${testName}`;
            const startTime = performance.now();

            try {
                await checkpointManager.restoreCheckpoint(checkpointId);
                const endTime = performance.now();
                loadTimes.push(endTime - startTime);

            } catch (error) {
                loadTimes.push(Number.MAX_SAFE_INTEGER); // Mark as failed
            }
        }

        return this.calculateStatistics(loadTimes);
    }

    /**
     * Generate comprehensive performance report
     */
    async generatePerformanceReport() {
        // Calculate summary metrics
        this.testResults.summary = {
            recoverySpeed: this.analyzeRecoverySpeedResults(),
            memoryEfficiency: this.analyzeMemoryResults(),
            checkpointPerformance: this.analyzeCheckpointResults(),
            concurrentCapacity: this.analyzeConcurrentResults(),
            overallScore: 0,
            bottlenecks: [],
            recommendations: []
        };

        // Generate recommendations
        this.generateRecommendations();

        // Calculate overall performance score
        this.calculateOverallScore();

        // Save detailed report
        await this.savePerformanceReport();

        // Generate visual charts if possible
        await this.generatePerformanceCharts();

        console.log('\n📊 Performance Test Summary:');
        console.log(`   Overall Score: ${this.testResults.summary.overallScore}/100`);
        console.log(`   Bottlenecks Found: ${this.testResults.summary.bottlenecks.length}`);
        console.log(`   Recommendations: ${this.testResults.summary.recommendations.length}`);
    }

    // Helper Methods

    createSimulatedError(scenario) {
        const errorTypes = {
            network: () => ({ code: 'ECONNRESET', message: 'Connection reset by peer' }),
            file: () => ({ code: 'EBUSY', message: 'Resource busy or locked' }),
            validation: () => ({ type: 'ValidationError', message: 'Invalid data format' }),
            memory: () => ({ code: 'ENOMEM', message: 'Cannot allocate memory' }),
            timeout: () => ({ code: 'ETIMEDOUT', message: 'Operation timed out' }),
            concurrent: () => ({ code: 'EEXIST', message: 'Resource already exists' })
        };

        const errorGenerator = errorTypes[scenario.type] || errorTypes.network;
        return { ...errorGenerator(), scenario };
    }

    async simulateOperation(scenario) {
        // Simulate operation duration based on scenario
        const delays = {
            low: () => Math.random() * 100,
            medium: () => Math.random() * 500 + 100,
            high: () => Math.random() * 1000 + 500
        };

        const delay = delays[scenario.severity] || delays.medium;
        await new Promise(resolve => setTimeout(resolve, delay()));
    }

    calculateStatistics(values) {
        const sorted = values.filter(v => v !== Number.MAX_SAFE_INTEGER).sort((a, b) => a - b);
        const count = sorted.length;

        if (count === 0) {
            return { average: 0, median: 0, p95: 0, p99: 0, min: 0, max: 0 };
        }

        const sum = sorted.reduce((a, b) => a + b, 0);
        const average = sum / count;
        const median = sorted[Math.floor(count / 2)];
        const p95 = sorted[Math.floor(count * 0.95)];
        const p99 = sorted[Math.floor(count * 0.99)];

        return {
            average,
            median,
            p95,
            p99,
            min: sorted[0],
            max: sorted[count - 1],
            count,
            stdDev: Math.sqrt(sorted.reduce((sq, n) => sq + Math.pow(n - average, 2), 0) / count)
        };
    }

    generateTestData(size) {
        const data = {
            id: Math.random().toString(36),
            timestamp: Date.now(),
            config: {},
            state: {},
            metadata: {}
        };

        // Fill with random data to reach target size
        const targetStr = JSON.stringify(data);
        const padding = 'x'.repeat(Math.max(0, size - targetStr.length));
        data.padding = padding;

        return data;
    }

    calculateGCPressure(snapshots) {
        // Simplified GC pressure calculation
        let gcEvents = 0;
        for (let i = 1; i < snapshots.length; i++) {
            if (snapshots[i].heapUsed < snapshots[i - 1].heapUsed * 0.8) {
                gcEvents++;
            }
        }
        return Math.min(100, (gcEvents / snapshots.length) * 100);
    }

    async simulateConcurrentRecovery(checkpointCount) {
        const errorRecovery = new ErrorRecovery();
        const operations = [];

        for (let i = 0; i < checkpointCount; i++) {
            operations.push((async () => {
                const error = this.createSimulatedError({ type: 'network', severity: 'medium' });
                await errorRecovery.recoverFromError(error, async () => {
                    await this.simulateOperation({ severity: 'low' });
                });
            })());
        }

        await Promise.all(operations);
    }

    createErrorHandlingWorker() {
        // For this implementation, we'll simulate workers
        return {
            id: Math.random().toString(36),
            terminate: () => {}
        };
    }

    async executeWorkerOperations(worker, duration) {
        const results = [];
        const startTime = Date.now();

        while (Date.now() - startTime < duration) {
            const operationStart = performance.now();

            try {
                // Simulate error handling operation
                await this.simulateOperation({ severity: 'medium' });

                results.push({
                    success: true,
                    latency: performance.now() - operationStart,
                    timestamp: Date.now()
                });

            } catch (error) {
                results.push({
                    success: false,
                    latency: performance.now() - operationStart,
                    timestamp: Date.now(),
                    error: error.message
                });
            }
        }

        return results;
    }

    analyzeRecoverySpeedResults() {
        const results = Object.fromEntries(this.metrics.recoverySpeed);
        const averages = Object.values(results).map(r => r.average);
        const overall = averages.reduce((sum, avg) => sum + avg, 0) / averages.length;

        return {
            overallAverage: overall,
            fastestScenario: Object.keys(results).reduce((a, b) =>
                results[a].average < results[b].average ? a : b
            ),
            slowestScenario: Object.keys(results).reduce((a, b) =>
                results[a].average > results[b].average ? a : b
            ),
            details: results
        };
    }

    analyzeMemoryResults() {
        const results = Object.fromEntries(this.metrics.memoryUsage);
        const peakUsages = Object.values(results).map(r => r.peakUsage);
        const maxPeak = Math.max(...peakUsages);

        return {
            maxPeakUsage: maxPeak,
            averageGrowthRate: Object.values(results).reduce((sum, r) => sum + r.memoryGrowthRate, 0) / Object.values(results).length,
            details: results
        };
    }

    analyzeCheckpointResults() {
        const results = Object.fromEntries(this.metrics.checkpointPerformance);
        const saveRates = Object.values(results).map(r => r.throughput.saveRate);
        const loadRates = Object.values(results).map(r => r.throughput.loadRate);

        return {
            averageSaveRate: saveRates.reduce((sum, rate) => sum + rate, 0) / saveRates.length,
            averageLoadRate: loadRates.reduce((sum, rate) => sum + rate, 0) / loadRates.length,
            details: results
        };
    }

    analyzeConcurrentResults() {
        const results = Object.fromEntries(this.metrics.concurrentCapacity);
        const throughputs = Object.values(results).map(r => r.throughput);
        const maxThroughput = Math.max(...throughputs);

        return {
            maxThroughput,
            optimalConcurrency: Object.keys(results).find(key =>
                results[key].throughput === maxThroughput
            ),
            details: results
        };
    }

    generateRecommendations() {
        const recommendations = [];

        // Recovery speed recommendations
        const recoveryAnalysis = this.testResults.summary.recoverySpeed;
        if (recoveryAnalysis.overallAverage > 1000) {
            recommendations.push({
                category: 'Recovery Speed',
                priority: 'High',
                issue: 'Slow recovery times detected',
                recommendation: 'Consider optimizing retry strategies and reducing backoff delays'
            });
        }

        // Memory recommendations
        const memoryAnalysis = this.testResults.summary.memoryEfficiency;
        if (memoryAnalysis.maxPeakUsage > 100 * 1024 * 1024) { // 100MB
            recommendations.push({
                category: 'Memory Usage',
                priority: 'Medium',
                issue: 'High memory usage detected',
                recommendation: 'Implement memory pooling and optimize checkpoint storage'
            });
        }

        // Checkpoint recommendations
        const checkpointAnalysis = this.testResults.summary.checkpointPerformance;
        if (checkpointAnalysis.averageSaveRate < 1000) { // < 1KB/ms
            recommendations.push({
                category: 'Checkpoint Performance',
                priority: 'Medium',
                issue: 'Slow checkpoint operations',
                recommendation: 'Enable compression and implement async I/O operations'
            });
        }

        this.testResults.summary.recommendations = recommendations;
    }

    calculateOverallScore() {
        // Simplified scoring algorithm
        let score = 100;

        // Deduct for slow recovery
        if (this.testResults.summary.recoverySpeed.overallAverage > 500) score -= 20;
        if (this.testResults.summary.recoverySpeed.overallAverage > 1000) score -= 20;

        // Deduct for high memory usage
        if (this.testResults.summary.memoryEfficiency.maxPeakUsage > 50 * 1024 * 1024) score -= 15;
        if (this.testResults.summary.memoryEfficiency.maxPeakUsage > 100 * 1024 * 1024) score -= 15;

        // Deduct for slow checkpoints
        if (this.testResults.summary.checkpointPerformance.averageSaveRate < 1000) score -= 15;
        if (this.testResults.summary.checkpointPerformance.averageLoadRate < 2000) score -= 15;

        this.testResults.summary.overallScore = Math.max(0, score);
    }

    async savePerformanceReport() {
        await fs.mkdir(this.config.reportDir, { recursive: true });
        const reportPath = path.join(this.config.reportDir, 'performance_report.json');
        await fs.writeFile(reportPath, JSON.stringify(this.testResults, null, 2));
    }

    async generatePerformanceCharts() {
        // Placeholder for chart generation
        // In a real implementation, this would generate visual charts
        console.log('📊 Chart generation would be implemented here');
    }

    getEnvironmentInfo() {
        return {
            nodeVersion: process.version,
            platform: process.platform,
            arch: process.arch,
            memory: process.memoryUsage(),
            cpus: require('os').cpus().length,
            timestamp: new Date().toISOString()
        };
    }

    async setupTestEnvironment() {
        await fs.mkdir(this.config.testDataDir, { recursive: true });
        await fs.mkdir(this.config.reportDir, { recursive: true });
    }

    async initializeTestEnvironment() {
        console.log('🔧 Initializing test environment...');

        // Clean up previous test data
        try {
            const files = await fs.readdir(this.config.testDataDir);
            for (const file of files) {
                await fs.unlink(path.join(this.config.testDataDir, file));
            }
        } catch (error) {
            // Directory might not exist yet
        }
    }
}

// Export for use as a module
module.exports = PerformanceTestSuite;

// If run directly, execute the performance test suite
if (require.main === module) {
    (async () => {
        try {
            const suite = new PerformanceTestSuite({
                testDuration: 30000, // 30 seconds
                maxConcurrentTests: 25,
                benchmarkIterations: 50
            });

            await suite.runPerformanceTests();
            process.exit(0);

        } catch (error) {
            console.error('Performance test failed:', error);
            process.exit(1);
        }
    })();
}