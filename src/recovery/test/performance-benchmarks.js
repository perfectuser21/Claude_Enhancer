/**
 * Claude Enhancer 5.0 - Performance Benchmarking Utilities
 * Specialized benchmarking tools for error recovery system components
 */

const { performance, PerformanceObserver } = require('perf_hooks');
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

class PerformanceBenchmarks {
    constructor(options = {}) {
        this.config = {
            warmupIterations: options.warmupIterations || 10,
            benchmarkIterations: options.benchmarkIterations || 100,
            samplesRetained: options.samplesRetained || 1000,
            outputDir: options.outputDir || './benchmark-results',
            enableProfiling: options.enableProfiling || true,
            ...options
        };

        this.benchmarkResults = new Map();
        this.performanceObserver = null;
        this.activeMetrics = new Set();

        this.setupPerformanceObserver();
    }

    /**
     * Setup performance observer for detailed metrics
     */
    setupPerformanceObserver() {
        if (!this.config.enableProfiling) return;

        this.performanceObserver = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            entries.forEach(entry => {
                if (this.activeMetrics.has(entry.name)) {
                    this.recordPerformanceEntry(entry);
                }
            });
        });

        this.performanceObserver.observe({ entryTypes: ['measure', 'mark'] });
    }

    /**
     * Benchmark error recovery speed across different scenarios
     */
    async benchmarkRecoverySpeed(errorRecovery) {
        console.log('🏃 Benchmarking Error Recovery Speed...');

        const scenarios = [
            { name: 'simple_network_error', type: 'network', complexity: 'low' },
            { name: 'complex_network_error', type: 'network', complexity: 'high' },
            { name: 'file_system_error', type: 'file', complexity: 'medium' },
            { name: 'validation_error', type: 'validation', complexity: 'low' },
            { name: 'concurrent_error', type: 'concurrent', complexity: 'high' },
            { name: 'memory_error', type: 'memory', complexity: 'high' }
        ];

        const results = new Map();

        for (const scenario of scenarios) {
            console.log(`  📊 Testing ${scenario.name}...`);

            const measurements = await this.runBenchmarkSuite(
                `recovery_${scenario.name}`,
                async () => {
                    const error = this.createBenchmarkError(scenario);
                    const startTime = performance.now();

                    try {
                        await errorRecovery.recoverFromError(error, async () => {
                            await this.simulateAsyncOperation(scenario.complexity);
                        });
                        return { success: true, duration: performance.now() - startTime };
                    } catch (recoveryError) {
                        return { success: false, duration: performance.now() - startTime };
                    }
                }
            );

            results.set(scenario.name, measurements);

            console.log(`    ⚡ Average: ${measurements.stats.average.toFixed(2)}ms`);
            console.log(`    📈 P95: ${measurements.stats.p95.toFixed(2)}ms`);
        }

        this.benchmarkResults.set('recoverySpeed', results);
        return results;
    }

    /**
     * Benchmark checkpoint operations performance
     */
    async benchmarkCheckpointPerformance(checkpointManager) {
        console.log('💾 Benchmarking Checkpoint Performance...');

        const dataSizes = [
            { name: 'small', size: 1024, description: '1KB' },
            { name: 'medium', size: 10240, description: '10KB' },
            { name: 'large', size: 102400, description: '100KB' },
            { name: 'xlarge', size: 1048576, description: '1MB' },
            { name: 'xxlarge', size: 10485760, description: '10MB' }
        ];

        const results = new Map();

        for (const dataSize of dataSizes) {
            console.log(`  📦 Testing ${dataSize.description} checkpoints...`);

            // Generate test data
            const testData = this.generateTestData(dataSize.size);

            // Benchmark save operations
            const saveMeasurements = await this.runBenchmarkSuite(
                `checkpoint_save_${dataSize.name}`,
                async () => {
                    const checkpointId = `bench_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                    const startTime = performance.now();

                    try {
                        await checkpointManager.createCheckpoint(checkpointId, testData);
                        return {
                            success: true,
                            duration: performance.now() - startTime,
                            checkpointId
                        };
                    } catch (error) {
                        return { success: false, duration: performance.now() - startTime };
                    }
                }
            );

            // Benchmark load operations (using previously created checkpoints)
            const loadMeasurements = await this.runBenchmarkSuite(
                `checkpoint_load_${dataSize.name}`,
                async () => {
                    const successfulSaves = saveMeasurements.rawResults.filter(r => r.success);
                    if (successfulSaves.length === 0) return { success: false, duration: 0 };

                    const randomSave = successfulSaves[Math.floor(Math.random() * successfulSaves.length)];
                    const startTime = performance.now();

                    try {
                        await checkpointManager.restoreCheckpoint(randomSave.checkpointId);
                        return { success: true, duration: performance.now() - startTime };
                    } catch (error) {
                        return { success: false, duration: performance.now() - startTime };
                    }
                }
            );

            results.set(dataSize.name, {
                size: dataSize.size,
                save: saveMeasurements,
                load: loadMeasurements,
                throughput: {
                    save: dataSize.size / saveMeasurements.stats.average, // bytes/ms
                    load: dataSize.size / loadMeasurements.stats.average
                }
            });

            console.log(`    💾 Save: ${saveMeasurements.stats.average.toFixed(2)}ms`);
            console.log(`    📖 Load: ${loadMeasurements.stats.average.toFixed(2)}ms`);
            console.log(`    🚀 Save Throughput: ${(results.get(dataSize.name).throughput.save / 1024).toFixed(2)}KB/ms`);
        }

        this.benchmarkResults.set('checkpointPerformance', results);
        return results;
    }

    /**
     * Benchmark concurrent error handling capacity
     */
    async benchmarkConcurrentCapacity(errorRecovery) {
        console.log('⚡ Benchmarking Concurrent Error Handling...');

        const concurrencyLevels = [1, 2, 5, 10, 20, 50, 100];
        const results = new Map();

        for (const concurrency of concurrencyLevels) {
            console.log(`  🔄 Testing ${concurrency} concurrent operations...`);

            const measurements = await this.runConcurrentBenchmark(
                `concurrent_${concurrency}`,
                concurrency,
                async (workerId) => {
                    const error = this.createBenchmarkError({ type: 'network', complexity: 'medium' });
                    const startTime = performance.now();

                    try {
                        await errorRecovery.recoverFromError(error, async () => {
                            await this.simulateAsyncOperation('medium');
                        });
                        return {
                            success: true,
                            duration: performance.now() - startTime,
                            workerId
                        };
                    } catch (recoveryError) {
                        return {
                            success: false,
                            duration: performance.now() - startTime,
                            workerId,
                            error: recoveryError.message
                        };
                    }
                }
            );

            results.set(`concurrency_${concurrency}`, measurements);

            console.log(`    ✅ Success Rate: ${measurements.successRate.toFixed(2)}%`);
            console.log(`    ⚡ Throughput: ${measurements.throughput.toFixed(2)} ops/sec`);
            console.log(`    🕐 Avg Latency: ${measurements.stats.average.toFixed(2)}ms`);
        }

        this.benchmarkResults.set('concurrentCapacity', results);
        return results;
    }

    /**
     * Benchmark memory usage patterns
     */
    async benchmarkMemoryUsage(testOperations) {
        console.log('🧠 Benchmarking Memory Usage Patterns...');

        const memorySnapshots = [];
        const startMemory = process.memoryUsage();

        // Start memory monitoring
        const memoryMonitor = setInterval(() => {
            const memUsage = process.memoryUsage();
            memorySnapshots.push({
                timestamp: Date.now(),
                heapUsed: memUsage.heapUsed,
                heapTotal: memUsage.heapTotal,
                external: memUsage.external,
                rss: memUsage.rss
            });
        }, 100); // Sample every 100ms

        try {
            // Run test operations
            const operationResults = [];

            for (let i = 0; i < testOperations.length; i++) {
                const operation = testOperations[i];
                const startTime = performance.now();

                try {
                    await operation();
                    operationResults.push({
                        success: true,
                        duration: performance.now() - startTime,
                        memoryAtCompletion: process.memoryUsage()
                    });
                } catch (error) {
                    operationResults.push({
                        success: false,
                        duration: performance.now() - startTime,
                        error: error.message,
                        memoryAtCompletion: process.memoryUsage()
                    });
                }

                // Force garbage collection periodically (if --expose-gc flag is used)
                if (global.gc && i % 10 === 0) {
                    global.gc();
                }
            }

            clearInterval(memoryMonitor);

            const endMemory = process.memoryUsage();
            const memoryAnalysis = this.analyzeMemoryUsage(memorySnapshots, startMemory, endMemory);

            console.log(`    💾 Peak Memory: ${(memoryAnalysis.peakHeapUsed / 1024 / 1024).toFixed(2)}MB`);
            console.log(`    📈 Memory Growth: ${(memoryAnalysis.totalGrowth / 1024 / 1024).toFixed(2)}MB`);
            console.log(`    🔄 GC Events: ${memoryAnalysis.estimatedGCEvents}`);

            this.benchmarkResults.set('memoryUsage', {
                snapshots: memorySnapshots,
                analysis: memoryAnalysis,
                operations: operationResults
            });

            return memoryAnalysis;

        } catch (error) {
            clearInterval(memoryMonitor);
            throw error;
        }
    }

    /**
     * Run a benchmark suite with warmup and measurement phases
     */
    async runBenchmarkSuite(benchmarkName, testFunction) {
        this.activeMetrics.add(benchmarkName);

        try {
            // Warmup phase
            performance.mark(`${benchmarkName}_warmup_start`);
            for (let i = 0; i < this.config.warmupIterations; i++) {
                await testFunction();
            }
            performance.mark(`${benchmarkName}_warmup_end`);
            performance.measure(`${benchmarkName}_warmup`, `${benchmarkName}_warmup_start`, `${benchmarkName}_warmup_end`);

            // Measurement phase
            const results = [];
            performance.mark(`${benchmarkName}_benchmark_start`);

            for (let i = 0; i < this.config.benchmarkIterations; i++) {
                const result = await testFunction();
                results.push(result);
            }

            performance.mark(`${benchmarkName}_benchmark_end`);
            performance.measure(`${benchmarkName}_benchmark`, `${benchmarkName}_benchmark_start`, `${benchmarkName}_benchmark_end`);

            const durations = results
                .filter(r => r.success !== false)
                .map(r => r.duration)
                .filter(d => d !== undefined && !isNaN(d));

            return {
                benchmarkName,
                rawResults: results,
                durations,
                stats: this.calculateStatistics(durations),
                successRate: (results.filter(r => r.success).length / results.length) * 100
            };

        } finally {
            this.activeMetrics.delete(benchmarkName);
        }
    }

    /**
     * Run concurrent benchmark
     */
    async runConcurrentBenchmark(benchmarkName, concurrency, testFunction) {
        const startTime = Date.now();
        const promises = [];

        // Create concurrent operations
        for (let i = 0; i < concurrency; i++) {
            promises.push(testFunction(i));
        }

        const results = await Promise.allSettled(promises);
        const endTime = Date.now();
        const totalDuration = endTime - startTime;

        // Process results
        const successfulResults = results
            .filter(r => r.status === 'fulfilled' && r.value.success)
            .map(r => r.value);

        const failedResults = results
            .filter(r => r.status === 'rejected' || (r.status === 'fulfilled' && !r.value.success));

        const durations = successfulResults.map(r => r.duration);
        const throughput = results.length / (totalDuration / 1000); // ops/sec

        return {
            benchmarkName,
            concurrency,
            totalResults: results.length,
            successfulResults: successfulResults.length,
            failedResults: failedResults.length,
            successRate: (successfulResults.length / results.length) * 100,
            throughput,
            totalDuration,
            stats: this.calculateStatistics(durations),
            rawResults: results.map(r => r.status === 'fulfilled' ? r.value : { error: r.reason })
        };
    }

    /**
     * Calculate comprehensive statistics
     */
    calculateStatistics(values) {
        if (!values || values.length === 0) {
            return {
                count: 0,
                average: 0,
                median: 0,
                min: 0,
                max: 0,
                p95: 0,
                p99: 0,
                stdDev: 0
            };
        }

        const sorted = [...values].sort((a, b) => a - b);
        const count = sorted.length;
        const sum = sorted.reduce((a, b) => a + b, 0);
        const average = sum / count;

        const median = count % 2 === 0
            ? (sorted[count / 2 - 1] + sorted[count / 2]) / 2
            : sorted[Math.floor(count / 2)];

        const p95Index = Math.floor(count * 0.95);
        const p99Index = Math.floor(count * 0.99);

        const variance = sorted.reduce((sum, value) => sum + Math.pow(value - average, 2), 0) / count;
        const stdDev = Math.sqrt(variance);

        return {
            count,
            average,
            median,
            min: sorted[0],
            max: sorted[count - 1],
            p95: sorted[Math.min(p95Index, count - 1)],
            p99: sorted[Math.min(p99Index, count - 1)],
            stdDev,
            variance
        };
    }

    /**
     * Analyze memory usage patterns
     */
    analyzeMemoryUsage(snapshots, startMemory, endMemory) {
        if (snapshots.length === 0) {
            return {
                totalGrowth: 0,
                peakHeapUsed: startMemory.heapUsed,
                estimatedGCEvents: 0,
                memoryEfficiency: 100
            };
        }

        const heapUsages = snapshots.map(s => s.heapUsed);
        const peakHeapUsed = Math.max(...heapUsages);
        const totalGrowth = endMemory.heapUsed - startMemory.heapUsed;

        // Estimate GC events (simple heuristic: significant drops in heap usage)
        let gcEvents = 0;
        for (let i = 1; i < snapshots.length; i++) {
            const current = snapshots[i].heapUsed;
            const previous = snapshots[i - 1].heapUsed;
            const dropPercentage = (previous - current) / previous;

            if (dropPercentage > 0.1) { // 10% drop indicates potential GC
                gcEvents++;
            }
        }

        const memoryEfficiency = Math.max(0, 100 - (totalGrowth / peakHeapUsed) * 100);

        return {
            initialHeapUsed: startMemory.heapUsed,
            finalHeapUsed: endMemory.heapUsed,
            peakHeapUsed,
            totalGrowth,
            estimatedGCEvents: gcEvents,
            memoryEfficiency,
            snapshots: snapshots.length,
            avgHeapUsed: heapUsages.reduce((a, b) => a + b, 0) / heapUsages.length
        };
    }

    /**
     * Generate comprehensive performance report
     */
    async generateBenchmarkReport() {
        const report = {
            metadata: {
                timestamp: new Date().toISOString(),
                nodeVersion: process.version,
                platform: process.platform,
                architecture: process.arch,
                configuration: this.config
            },
            summary: this.generateSummary(),
            benchmarks: Object.fromEntries(this.benchmarkResults),
            analysis: this.performAnalysis(),
            recommendations: this.generateRecommendations()
        };

        // Save detailed report
        await fs.mkdir(this.config.outputDir, { recursive: true });
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const reportPath = path.join(this.config.outputDir, `benchmark_report_${timestamp}.json`);

        await fs.writeFile(reportPath, JSON.stringify(report, null, 2));

        // Generate summary report
        await this.generateSummaryReport(report, reportPath);

        console.log(`\n📊 Benchmark Report Generated: ${reportPath}`);
        return report;
    }

    /**
     * Generate performance summary
     */
    generateSummary() {
        const summary = {
            totalBenchmarks: this.benchmarkResults.size,
            overallPerformanceScore: 0,
            criticalIssues: 0,
            recommendations: 0
        };

        // Calculate overall performance score (simplified)
        let totalScore = 0;
        let scoredBenchmarks = 0;

        for (const [category, results] of this.benchmarkResults.entries()) {
            if (category === 'recoverySpeed') {
                const avgRecoveryTime = this.calculateAverageFromResults(results, 'average');
                const score = Math.max(0, 100 - (avgRecoveryTime / 10)); // 10ms = 100 points
                totalScore += score;
                scoredBenchmarks++;
            }

            if (category === 'concurrentCapacity') {
                const avgSuccessRate = this.calculateAverageFromResults(results, 'successRate');
                totalScore += avgSuccessRate;
                scoredBenchmarks++;
            }
        }

        summary.overallPerformanceScore = scoredBenchmarks > 0 ? totalScore / scoredBenchmarks : 0;
        return summary;
    }

    /**
     * Perform detailed analysis
     */
    performAnalysis() {
        const analysis = {
            performanceBottlenecks: [],
            scalabilityIssues: [],
            memoryIssues: [],
            recommendations: []
        };

        // Analyze each benchmark category
        for (const [category, results] of this.benchmarkResults.entries()) {
            switch (category) {
                case 'recoverySpeed':
                    this.analyzeRecoverySpeed(results, analysis);
                    break;
                case 'checkpointPerformance':
                    this.analyzeCheckpointPerformance(results, analysis);
                    break;
                case 'concurrentCapacity':
                    this.analyzeConcurrentCapacity(results, analysis);
                    break;
                case 'memoryUsage':
                    this.analyzeMemoryPerformance(results, analysis);
                    break;
            }
        }

        return analysis;
    }

    /**
     * Analyze recovery speed results
     */
    analyzeRecoverySpeed(results, analysis) {
        for (const [scenario, measurements] of results.entries()) {
            if (measurements.stats.average > 1000) { // > 1 second
                analysis.performanceBottlenecks.push({
                    category: 'Recovery Speed',
                    scenario,
                    issue: `Slow recovery time: ${measurements.stats.average.toFixed(2)}ms`,
                    severity: measurements.stats.average > 5000 ? 'high' : 'medium'
                });
            }

            if (measurements.stats.p99 > 5000) { // P99 > 5 seconds
                analysis.performanceBottlenecks.push({
                    category: 'Recovery Speed',
                    scenario,
                    issue: `High P99 latency: ${measurements.stats.p99.toFixed(2)}ms`,
                    severity: 'high'
                });
            }
        }
    }

    /**
     * Analyze checkpoint performance results
     */
    analyzeCheckpointPerformance(results, analysis) {
        for (const [size, measurements] of results.entries()) {
            const saveRate = measurements.throughput.save / 1024; // KB/ms
            const loadRate = measurements.throughput.load / 1024; // KB/ms

            if (saveRate < 100) { // < 100 KB/ms
                analysis.performanceBottlenecks.push({
                    category: 'Checkpoint Performance',
                    scenario: `${size} save`,
                    issue: `Low save throughput: ${saveRate.toFixed(2)} KB/ms`,
                    severity: saveRate < 10 ? 'high' : 'medium'
                });
            }

            if (loadRate < 500) { // < 500 KB/ms
                analysis.performanceBottlenecks.push({
                    category: 'Checkpoint Performance',
                    scenario: `${size} load`,
                    issue: `Low load throughput: ${loadRate.toFixed(2)} KB/ms`,
                    severity: loadRate < 50 ? 'high' : 'medium'
                });
            }
        }
    }

    /**
     * Analyze concurrent capacity results
     */
    analyzeConcurrentCapacity(results, analysis) {
        let maxThroughput = 0;
        let throughputDegradation = false;

        for (const [level, measurements] of results.entries()) {
            if (measurements.successRate < 95) {
                analysis.scalabilityIssues.push({
                    category: 'Concurrent Capacity',
                    level,
                    issue: `Low success rate at concurrency: ${measurements.successRate.toFixed(2)}%`,
                    severity: measurements.successRate < 90 ? 'high' : 'medium'
                });
            }

            if (measurements.throughput > maxThroughput) {
                maxThroughput = measurements.throughput;
            } else if (measurements.throughput < maxThroughput * 0.8) {
                throughputDegradation = true;
            }
        }

        if (throughputDegradation) {
            analysis.scalabilityIssues.push({
                category: 'Concurrent Capacity',
                issue: 'Throughput degradation detected at high concurrency',
                severity: 'medium'
            });
        }
    }

    /**
     * Generate performance recommendations
     */
    generateRecommendations() {
        const recommendations = [];

        // Generic recommendations based on results
        if (this.benchmarkResults.has('recoverySpeed')) {
            recommendations.push({
                category: 'Recovery Speed',
                recommendation: 'Consider implementing adaptive retry strategies based on error type',
                priority: 'medium'
            });
        }

        if (this.benchmarkResults.has('checkpointPerformance')) {
            recommendations.push({
                category: 'Checkpoint Performance',
                recommendation: 'Implement checkpoint compression and async I/O for better performance',
                priority: 'high'
            });
        }

        if (this.benchmarkResults.has('concurrentCapacity')) {
            recommendations.push({
                category: 'Concurrent Capacity',
                recommendation: 'Implement proper backpressure mechanisms for high load scenarios',
                priority: 'high'
            });
        }

        return recommendations;
    }

    // Helper methods

    createBenchmarkError(scenario) {
        const errorTypes = {
            network: { code: 'ECONNRESET', message: 'Connection reset by peer' },
            file: { code: 'EBUSY', message: 'Resource busy or locked' },
            validation: { type: 'ValidationError', message: 'Invalid input data' },
            concurrent: { code: 'EEXIST', message: 'Resource already exists' },
            memory: { code: 'ENOMEM', message: 'Out of memory' }
        };

        const errorDef = errorTypes[scenario.type] || errorTypes.network;
        const error = new Error(errorDef.message);

        if (errorDef.code) error.code = errorDef.code;
        if (errorDef.type) error.type = errorDef.type;

        error.scenario = scenario;
        return error;
    }

    async simulateAsyncOperation(complexity) {
        const delays = {
            low: () => new Promise(resolve => setTimeout(resolve, Math.random() * 10)),
            medium: () => new Promise(resolve => setTimeout(resolve, Math.random() * 50)),
            high: () => new Promise(resolve => setTimeout(resolve, Math.random() * 100))
        };

        const delay = delays[complexity] || delays.medium;
        await delay();
    }

    generateTestData(size) {
        const baseData = {
            id: crypto.randomUUID(),
            timestamp: Date.now(),
            type: 'test_data',
            metadata: {
                generated: true,
                size: size
            }
        };

        const serialized = JSON.stringify(baseData);
        const padding = 'x'.repeat(Math.max(0, size - serialized.length));
        baseData.padding = padding;

        return baseData;
    }

    recordPerformanceEntry(entry) {
        // Store performance entries for detailed analysis
        if (!this.performanceEntries) {
            this.performanceEntries = [];
        }
        this.performanceEntries.push(entry);
    }

    calculateAverageFromResults(results, property) {
        const values = Array.from(results.values())
            .map(r => r[property] || r.stats?.[property])
            .filter(v => v !== undefined && !isNaN(v));

        return values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;
    }

    async generateSummaryReport(fullReport, reportPath) {
        const summaryText = `
Performance Benchmark Summary
============================
Generated: ${fullReport.metadata.timestamp}
Node.js: ${fullReport.metadata.nodeVersion}
Platform: ${fullReport.metadata.platform}

Overall Performance Score: ${fullReport.summary.overallPerformanceScore.toFixed(2)}/100

Key Metrics:
-----------
${this.formatSummaryMetrics(fullReport)}

Performance Issues Found: ${fullReport.analysis.performanceBottlenecks.length}
Scalability Issues Found: ${fullReport.analysis.scalabilityIssues.length}
Memory Issues Found: ${fullReport.analysis.memoryIssues.length}

Top Recommendations:
-------------------
${fullReport.recommendations.slice(0, 5).map((rec, i) => `${i + 1}. ${rec.recommendation}`).join('\n')}

Full detailed report: ${reportPath}
`;

        const summaryPath = path.join(this.config.outputDir, 'benchmark_summary.txt');
        await fs.writeFile(summaryPath, summaryText);

        console.log(`📋 Summary Report: ${summaryPath}`);
    }

    formatSummaryMetrics(report) {
        const lines = [];

        if (report.benchmarks.recoverySpeed) {
            const avgRecovery = this.calculateAverageFromResults(report.benchmarks.recoverySpeed, 'average');
            lines.push(`Recovery Speed: ${avgRecovery.toFixed(2)}ms avg`);
        }

        if (report.benchmarks.concurrentCapacity) {
            const avgSuccessRate = this.calculateAverageFromResults(report.benchmarks.concurrentCapacity, 'successRate');
            lines.push(`Concurrent Success Rate: ${avgSuccessRate.toFixed(2)}%`);
        }

        if (report.benchmarks.checkpointPerformance) {
            lines.push(`Checkpoint Performance: See detailed report`);
        }

        return lines.join('\n');
    }
}

module.exports = PerformanceBenchmarks;

// If run directly, execute benchmarks
if (require.main === module) {
    (async () => {
        try {
            console.log('🚀 Starting Performance Benchmarks...');

            const ErrorRecovery = require('../ErrorRecovery');
            const CheckpointManager = require('../CheckpointManager');

            const benchmarks = new PerformanceBenchmarks({
                benchmarkIterations: 50,
                warmupIterations: 10
            });

            const errorRecovery = new ErrorRecovery({
                enableMetrics: true
            });

            const checkpointManager = new CheckpointManager({
                checkpointsDir: './benchmark-checkpoints'
            });

            // Run all benchmarks
            await benchmarks.benchmarkRecoverySpeed(errorRecovery);
            await benchmarks.benchmarkCheckpointPerformance(checkpointManager);
            await benchmarks.benchmarkConcurrentCapacity(errorRecovery);

            // Generate comprehensive report
            await benchmarks.generateBenchmarkReport();

            console.log('✅ Performance benchmarking completed!');

        } catch (error) {
            console.error('❌ Benchmark failed:', error);
            process.exit(1);
        }
    })();
}