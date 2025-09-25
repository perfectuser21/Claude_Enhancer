/**
 * Claude Enhancer 5.0 - Error Recovery Stress Test Runner
 * Specialized stress testing for error recovery system under extreme conditions
 */

const cluster = require('cluster');
const os = require('os');
const { performance } = require('perf_hooks');
const EventEmitter = require('events');
const fs = require('fs').promises;
const path = require('path');

const ErrorRecovery = require('../ErrorRecovery');
const CheckpointManager = require('../CheckpointManager');

class StressTestRunner extends EventEmitter {
    constructor(options = {}) {
        super();
        this.config = {
            duration: options.duration || 60000, // 1 minute
            rampUpTime: options.rampUpTime || 10000, // 10 seconds
            rampDownTime: options.rampDownTime || 10000, // 10 seconds
            maxWorkers: options.maxWorkers || os.cpus().length * 2,
            errorRate: options.errorRate || 0.3, // 30% error rate
            checkpointFrequency: options.checkpointFrequency || 100, // Every 100 operations
            memoryPressureEnabled: options.memoryPressureEnabled || true,
            cpuIntensiveEnabled: options.cpuIntensiveEnabled || true,
            networkLatencySimulation: options.networkLatencySimulation || true,
            ...options
        };

        this.workers = [];
        this.testResults = {
            startTime: null,
            endTime: null,
            totalOperations: 0,
            successfulOperations: 0,
            failedOperations: 0,
            recoveredErrors: 0,
            unrecoveredErrors: 0,
            checkpointsCreated: 0,
            checkpointsRestored: 0,
            memoryStats: [],
            performanceStats: [],
            bottlenecks: [],
            workerStats: new Map()
        };

        this.systemMonitor = new SystemResourceMonitor();
    }

    /**
     * Run comprehensive stress test
     */
    async runStressTest() {
        console.log('🚨 Starting Error Recovery Stress Test');
        console.log(`⚙️  Configuration:
        - Duration: ${this.config.duration / 1000}s
        - Workers: ${this.config.maxWorkers}
        - Error Rate: ${this.config.errorRate * 100}%
        - Checkpoint Frequency: ${this.config.checkpointFrequency}`);

        try {
            this.testResults.startTime = Date.now();

            // Start system monitoring
            await this.systemMonitor.startMonitoring(100); // Monitor every 100ms

            // Phase 1: Ramp up load gradually
            console.log('\n📈 Phase 1: Ramping up load...');
            await this.rampUpPhase();

            // Phase 2: Sustained high load
            console.log('\n⚡ Phase 2: Sustained high load...');
            await this.sustainedLoadPhase();

            // Phase 3: Ramp down gracefully
            console.log('\n📉 Phase 3: Ramping down...');
            await this.rampDownPhase();

            // Stop monitoring and collect results
            await this.systemMonitor.stopMonitoring();
            this.testResults.endTime = Date.now();

            // Analyze results and generate report
            await this.analyzeResults();
            await this.generateStressTestReport();

            console.log('\n✅ Stress test completed successfully!');

        } catch (error) {
            console.error('❌ Stress test failed:', error);
            throw error;
        } finally {
            await this.cleanup();
        }
    }

    /**
     * Phase 1: Gradually increase load to test system responsiveness
     */
    async rampUpPhase() {
        const workers = Math.ceil(this.config.maxWorkers / 3); // Start with 1/3 workers
        const duration = this.config.rampUpTime;

        await this.runLoadPhase('rampUp', workers, duration, {
            errorRate: this.config.errorRate * 0.5, // Lower error rate initially
            operationComplexity: 'low'
        });
    }

    /**
     * Phase 2: Full load with maximum stress conditions
     */
    async sustainedLoadPhase() {
        const workers = this.config.maxWorkers;
        const duration = this.config.duration - this.config.rampUpTime - this.config.rampDownTime;

        await this.runLoadPhase('sustained', workers, duration, {
            errorRate: this.config.errorRate,
            operationComplexity: 'high',
            enableChaosEngineering: true
        });
    }

    /**
     * Phase 3: Gracefully reduce load and test cleanup
     */
    async rampDownPhase() {
        const workers = Math.ceil(this.config.maxWorkers / 2); // Reduce to half workers
        const duration = this.config.rampDownTime;

        await this.runLoadPhase('rampDown', workers, duration, {
            errorRate: this.config.errorRate * 0.7, // Slightly lower error rate
            operationComplexity: 'medium',
            enableGracefulShutdown: true
        });
    }

    /**
     * Run a specific load phase with given parameters
     */
    async runLoadPhase(phaseName, workerCount, duration, options) {
        console.log(`  🔄 ${phaseName}: ${workerCount} workers for ${duration / 1000}s`);

        if (cluster.isMaster) {
            // Master process: spawn workers
            const workers = [];
            const workerResults = [];

            // Spawn workers
            for (let i = 0; i < workerCount; i++) {
                const worker = cluster.fork({
                    WORKER_ID: i,
                    PHASE_NAME: phaseName,
                    DURATION: duration,
                    OPTIONS: JSON.stringify(options)
                });

                workers.push(worker);

                worker.on('message', (message) => {
                    if (message.type === 'result') {
                        workerResults.push(message.data);
                    } else if (message.type === 'stats') {
                        this.updateWorkerStats(i, message.data);
                    }
                });
            }

            // Wait for all workers to complete
            await new Promise((resolve) => {
                let completedWorkers = 0;
                workers.forEach(worker => {
                    worker.on('exit', () => {
                        completedWorkers++;
                        if (completedWorkers === workers.length) {
                            resolve();
                        }
                    });
                });

                // Timeout fallback
                setTimeout(() => {
                    workers.forEach(worker => worker.kill());
                    resolve();
                }, duration + 5000);
            });

            // Aggregate worker results
            this.aggregateWorkerResults(phaseName, workerResults);

        } else {
            // Worker process: execute load test
            await this.runWorkerLoadTest(options);
        }
    }

    /**
     * Worker process load test execution
     */
    async runWorkerLoadTest(options) {
        const workerId = process.env.WORKER_ID;
        const phaseName = process.env.PHASE_NAME;
        const duration = parseInt(process.env.DURATION);

        const errorRecovery = new ErrorRecovery({
            checkpointsDir: `./.claude/stress-test-checkpoints-${workerId}`,
            enableMetrics: true,
            maxRetries: 5
        });

        const checkpointManager = new CheckpointManager({
            checkpointsDir: `./.claude/stress-test-checkpoints-${workerId}`
        });

        const results = {
            workerId,
            phaseName,
            operations: 0,
            successes: 0,
            failures: 0,
            recoveries: 0,
            checkpoints: 0,
            startTime: Date.now(),
            endTime: null,
            errors: []
        };

        const startTime = Date.now();
        let operationCount = 0;

        try {
            while (Date.now() - startTime < duration) {
                operationCount++;
                const operationStart = performance.now();

                try {
                    // Simulate operation with potential errors
                    if (Math.random() < options.errorRate) {
                        throw this.createStressTestError(options);
                    }

                    // Simulate work based on complexity
                    await this.simulateWork(options.operationComplexity);

                    // Periodic checkpoint creation
                    if (operationCount % this.config.checkpointFrequency === 0) {
                        await checkpointManager.createCheckpoint(
                            `stress_${workerId}_${operationCount}`,
                            { operationCount, phase: phaseName, timestamp: Date.now() }
                        );
                        results.checkpoints++;
                    }

                    results.successes++;

                } catch (error) {
                    // Attempt error recovery
                    try {
                        await errorRecovery.recoverFromError(error, async () => {
                            await this.simulateWork('low');
                        });
                        results.recoveries++;
                    } catch (recoveryError) {
                        results.errors.push({
                            originalError: error.message,
                            recoveryError: recoveryError.message,
                            timestamp: Date.now()
                        });
                        results.failures++;
                    }
                }

                results.operations++;

                // Send periodic stats to master
                if (operationCount % 100 === 0) {
                    process.send({
                        type: 'stats',
                        data: {
                            operations: results.operations,
                            successes: results.successes,
                            failures: results.failures,
                            recoveries: results.recoveries
                        }
                    });
                }

                // Optional: simulate memory pressure
                if (options.enableChaosEngineering && Math.random() < 0.01) {
                    await this.simulateMemoryPressure();
                }
            }

        } catch (error) {
            results.errors.push({
                error: error.message,
                timestamp: Date.now(),
                type: 'worker_error'
            });
        } finally {
            results.endTime = Date.now();

            // Send final results to master
            process.send({
                type: 'result',
                data: results
            });

            process.exit(0);
        }
    }

    /**
     * Create different types of stress test errors
     */
    createStressTestError(options) {
        const errorTypes = [
            { type: 'network', code: 'ECONNRESET', message: 'Connection reset during high load' },
            { type: 'timeout', code: 'ETIMEDOUT', message: 'Operation timeout under stress' },
            { type: 'resource', code: 'EMFILE', message: 'Too many open files' },
            { type: 'memory', code: 'ENOMEM', message: 'Out of memory' },
            { type: 'concurrency', code: 'EEXIST', message: 'Concurrent access conflict' },
            { type: 'validation', message: 'Data corruption detected' }
        ];

        const errorType = errorTypes[Math.floor(Math.random() * errorTypes.length)];
        const error = new Error(errorType.message);
        error.code = errorType.code;
        error.type = errorType.type;
        error.stressTest = true;

        return error;
    }

    /**
     * Simulate work of varying complexity
     */
    async simulateWork(complexity) {
        const workloads = {
            low: () => new Promise(resolve => setTimeout(resolve, Math.random() * 10)),
            medium: () => new Promise(resolve => {
                // Simulate some CPU work
                let sum = 0;
                for (let i = 0; i < 1000; i++) {
                    sum += Math.random();
                }
                setTimeout(resolve, Math.random() * 50);
            }),
            high: () => new Promise(resolve => {
                // Simulate intensive CPU work
                let sum = 0;
                for (let i = 0; i < 10000; i++) {
                    sum += Math.random() * Math.sin(i);
                }
                setTimeout(resolve, Math.random() * 100);
            })
        };

        const workload = workloads[complexity] || workloads.medium;
        await workload();
    }

    /**
     * Simulate memory pressure for chaos engineering
     */
    async simulateMemoryPressure() {
        const largeBuffer = Buffer.alloc(10 * 1024 * 1024); // 10MB
        setTimeout(() => {
            // Let GC clean it up
        }, 1000);
    }

    /**
     * Update worker statistics
     */
    updateWorkerStats(workerId, stats) {
        this.testResults.workerStats.set(workerId, stats);
    }

    /**
     * Aggregate results from all workers
     */
    aggregateWorkerResults(phaseName, workerResults) {
        for (const result of workerResults) {
            this.testResults.totalOperations += result.operations;
            this.testResults.successfulOperations += result.successes;
            this.testResults.failedOperations += result.failures;
            this.testResults.recoveredErrors += result.recoveries;
            this.testResults.checkpointsCreated += result.checkpoints;

            // Store phase-specific results
            if (!this.testResults[phaseName]) {
                this.testResults[phaseName] = {
                    operations: 0,
                    successes: 0,
                    failures: 0,
                    recoveries: 0
                };
            }

            this.testResults[phaseName].operations += result.operations;
            this.testResults[phaseName].successes += result.successes;
            this.testResults[phaseName].failures += result.failures;
            this.testResults[phaseName].recoveries += result.recoveries;
        }
    }

    /**
     * Analyze stress test results
     */
    async analyzeResults() {
        const totalDuration = this.testResults.endTime - this.testResults.startTime;
        const throughput = this.testResults.totalOperations / (totalDuration / 1000);
        const errorRate = this.testResults.failedOperations / this.testResults.totalOperations;
        const recoveryRate = this.testResults.recoveredErrors / (this.testResults.failedOperations + this.testResults.recoveredErrors);

        this.testResults.analysis = {
            duration: totalDuration,
            throughput: throughput,
            errorRate: errorRate,
            recoveryRate: recoveryRate,
            operationsPerSecond: throughput,
            successRate: this.testResults.successfulOperations / this.testResults.totalOperations,
            systemResourceUsage: await this.systemMonitor.getResourceSummary()
        };

        // Identify bottlenecks
        this.identifyBottlenecks();
    }

    /**
     * Identify performance bottlenecks
     */
    identifyBottlenecks() {
        const bottlenecks = [];

        // Check throughput bottleneck
        if (this.testResults.analysis.throughput < 100) {
            bottlenecks.push({
                type: 'throughput',
                severity: 'high',
                description: 'Low throughput detected',
                recommendation: 'Optimize critical path operations'
            });
        }

        // Check error recovery bottleneck
        if (this.testResults.analysis.recoveryRate < 0.8) {
            bottlenecks.push({
                type: 'recovery',
                severity: 'high',
                description: 'Poor error recovery rate',
                recommendation: 'Improve error handling strategies'
            });
        }

        // Check memory bottleneck
        const memoryStats = this.testResults.analysis.systemResourceUsage.memory;
        if (memoryStats.peakUsage > 0.9) {
            bottlenecks.push({
                type: 'memory',
                severity: 'medium',
                description: 'High memory usage detected',
                recommendation: 'Implement memory optimization'
            });
        }

        this.testResults.bottlenecks = bottlenecks;
    }

    /**
     * Generate comprehensive stress test report
     */
    async generateStressTestReport() {
        const report = {
            metadata: {
                testType: 'stress',
                timestamp: new Date().toISOString(),
                duration: this.testResults.endTime - this.testResults.startTime,
                configuration: this.config
            },
            summary: {
                totalOperations: this.testResults.totalOperations,
                successRate: this.testResults.analysis.successRate,
                errorRate: this.testResults.analysis.errorRate,
                recoveryRate: this.testResults.analysis.recoveryRate,
                throughput: this.testResults.analysis.throughput,
                bottlenecks: this.testResults.bottlenecks.length
            },
            detailed: this.testResults,
            recommendations: this.generateRecommendations()
        };

        // Save report
        const reportDir = './stress-test-reports';
        await fs.mkdir(reportDir, { recursive: true });

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const reportPath = path.join(reportDir, `stress_test_report_${timestamp}.json`);

        await fs.writeFile(reportPath, JSON.stringify(report, null, 2));

        console.log(`\n📊 Stress Test Summary:`);
        console.log(`   Total Operations: ${report.summary.totalOperations.toLocaleString()}`);
        console.log(`   Success Rate: ${(report.summary.successRate * 100).toFixed(2)}%`);
        console.log(`   Error Recovery Rate: ${(report.summary.recoveryRate * 100).toFixed(2)}%`);
        console.log(`   Throughput: ${report.summary.throughput.toFixed(2)} ops/sec`);
        console.log(`   Bottlenecks: ${report.summary.bottlenecks}`);
        console.log(`   Report: ${reportPath}`);
    }

    /**
     * Generate performance recommendations
     */
    generateRecommendations() {
        const recommendations = [];

        this.testResults.bottlenecks.forEach(bottleneck => {
            recommendations.push(bottleneck.recommendation);
        });

        // Add general recommendations
        if (this.testResults.analysis.throughput < 500) {
            recommendations.push('Consider implementing operation batching to improve throughput');
        }

        if (this.testResults.analysis.errorRate > 0.2) {
            recommendations.push('High error rate detected - review error simulation scenarios');
        }

        return recommendations;
    }

    /**
     * Cleanup resources
     */
    async cleanup() {
        try {
            // Kill any remaining workers
            if (cluster.isMaster) {
                Object.values(cluster.workers).forEach(worker => {
                    worker.kill();
                });
            }

            console.log('🧹 Cleanup completed');
        } catch (error) {
            console.error('Cleanup error:', error.message);
        }
    }
}

/**
 * System Resource Monitor
 */
class SystemResourceMonitor {
    constructor() {
        this.monitoring = false;
        this.snapshots = [];
        this.interval = null;
    }

    async startMonitoring(intervalMs = 1000) {
        this.monitoring = true;
        this.snapshots = [];

        this.interval = setInterval(() => {
            if (!this.monitoring) return;

            const snapshot = {
                timestamp: Date.now(),
                memory: process.memoryUsage(),
                cpu: process.cpuUsage(),
                uptime: process.uptime()
            };

            this.snapshots.push(snapshot);
        }, intervalMs);
    }

    async stopMonitoring() {
        this.monitoring = false;
        if (this.interval) {
            clearInterval(this.interval);
        }
    }

    async getResourceSummary() {
        const memoryUsages = this.snapshots.map(s => s.memory.heapUsed);
        const maxMemory = Math.max(...memoryUsages);
        const avgMemory = memoryUsages.reduce((a, b) => a + b, 0) / memoryUsages.length;

        return {
            memory: {
                peakUsage: maxMemory / (1024 * 1024 * 1024), // GB
                averageUsage: avgMemory / (1024 * 1024 * 1024), // GB
                snapshots: this.snapshots.length
            },
            duration: this.snapshots.length > 0 ?
                this.snapshots[this.snapshots.length - 1].timestamp - this.snapshots[0].timestamp : 0
        };
    }
}

module.exports = StressTestRunner;

// If run directly, execute the stress test
if (require.main === module) {
    const runner = new StressTestRunner({
        duration: 60000, // 1 minute
        maxWorkers: 8,
        errorRate: 0.25,
        checkpointFrequency: 50
    });

    runner.runStressTest().catch(console.error);
}