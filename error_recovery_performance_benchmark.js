#!/usr/bin/env node

/**
 * Error Recovery Performance Benchmark
 * Measures performance characteristics under various loads
 */

const ErrorRecovery = require('./src/recovery/ErrorRecovery');

class PerformanceBenchmark {
    constructor() {
        this.recovery = new ErrorRecovery({
            maxRetries: 3,
            baseRetryDelay: 100,
            enableMetrics: true
        });

        this.results = {};
    }

    async runBenchmarks() {
        console.log('⚡ Error Recovery Performance Benchmark');
        console.log('=' * 50);

        const benchmarks = [
            { name: 'Single Error Processing Speed', test: this.benchmarkSingleError.bind(this) },
            { name: 'Batch Error Processing', test: this.benchmarkBatchProcessing.bind(this) },
            { name: 'Checkpoint Performance', test: this.benchmarkCheckpoints.bind(this) },
            { name: 'Memory Usage Under Load', test: this.benchmarkMemoryUsage.bind(this) },
            { name: 'Concurrent Operations', test: this.benchmarkConcurrency.bind(this) },
            { name: 'Recovery Strategy Performance', test: this.benchmarkRecoveryStrategies.bind(this) }
        ];

        for (const benchmark of benchmarks) {
            console.log(`\n🏃 Running: ${benchmark.name}`);
            this.results[benchmark.name] = await benchmark.test();
        }

        this.generateReport();
        return this.results;
    }

    async benchmarkSingleError() {
        const iterations = 1000;
        const times = [];

        for (let i = 0; i < iterations; i++) {
            const error = new Error(`Test error ${i}`);
            error.code = 'TEST_ERROR';

            const start = process.hrtime.bigint();
            const analysis = this.recovery.analyzeError(error);
            const end = process.hrtime.bigint();

            times.push(Number(end - start) / 1000000); // Convert to milliseconds
        }

        return {
            iterations,
            avgTime: times.reduce((a, b) => a + b, 0) / times.length,
            minTime: Math.min(...times),
            maxTime: Math.max(...times),
            medianTime: times.sort((a, b) => a - b)[Math.floor(times.length / 2)]
        };
    }

    async benchmarkBatchProcessing() {
        const batchSizes = [10, 50, 100, 500, 1000];
        const results = {};

        for (const batchSize of batchSizes) {
            const errors = [];
            for (let i = 0; i < batchSize; i++) {
                const error = new Error(`Batch error ${i}`);
                error.code = `ERROR_${i % 10}`;
                errors.push(error);
            }

            const start = process.hrtime.bigint();

            for (const error of errors) {
                this.recovery.analyzeError(error);
            }

            const end = process.hrtime.bigint();
            const duration = Number(end - start) / 1000000; // milliseconds

            results[batchSize] = {
                duration,
                errorsPerSecond: Math.round(batchSize / (duration / 1000)),
                avgPerError: duration / batchSize
            };
        }

        return results;
    }

    async benchmarkCheckpoints() {
        const operations = ['create', 'restore', 'cleanup'];
        const dataSizes = [1, 10, 100, 1000]; // KB
        const results = {};

        for (const operation of operations) {
            results[operation] = {};

            for (const sizeKB of dataSizes) {
                const times = [];
                const iterations = 20;

                for (let i = 0; i < iterations; i++) {
                    const checkpointId = `perf-${operation}-${sizeKB}-${i}`;
                    const data = { content: 'X'.repeat(sizeKB * 1024) };

                    let duration;

                    if (operation === 'create') {
                        const start = process.hrtime.bigint();
                        await this.recovery.createCheckpoint(checkpointId, data);
                        const end = process.hrtime.bigint();
                        duration = Number(end - start) / 1000000;
                    } else if (operation === 'restore') {
                        // First create a checkpoint
                        await this.recovery.createCheckpoint(checkpointId, data);

                        const start = process.hrtime.bigint();
                        await this.recovery.restoreCheckpoint(checkpointId);
                        const end = process.hrtime.bigint();
                        duration = Number(end - start) / 1000000;
                    } else if (operation === 'cleanup') {
                        // First create a checkpoint
                        await this.recovery.createCheckpoint(checkpointId, data);

                        const start = process.hrtime.bigint();
                        await this.recovery.cleanupCheckpoint(checkpointId);
                        const end = process.hrtime.bigint();
                        duration = Number(end - start) / 1000000;
                    }

                    times.push(duration);
                }

                results[operation][`${sizeKB}KB`] = {
                    avgTime: times.reduce((a, b) => a + b, 0) / times.length,
                    minTime: Math.min(...times),
                    maxTime: Math.max(...times)
                };
            }
        }

        return results;
    }

    async benchmarkMemoryUsage() {
        const initialMemory = process.memoryUsage();
        const memorySnapshots = [initialMemory];

        // Process increasing amounts of errors
        const errorCounts = [100, 500, 1000, 2000, 5000];

        for (const count of errorCounts) {
            for (let i = 0; i < count; i++) {
                const error = new Error(`Memory test error ${i}`);
                error.stack = 'X'.repeat(1000); // Make errors consume more memory
                this.recovery.analyzeError(error);
            }

            memorySnapshots.push(process.memoryUsage());
        }

        return {
            snapshots: memorySnapshots.map((snapshot, index) => ({
                errorCount: index === 0 ? 0 : errorCounts[index - 1],
                heapUsed: Math.round(snapshot.heapUsed / 1024 / 1024), // MB
                heapTotal: Math.round(snapshot.heapTotal / 1024 / 1024), // MB
                external: Math.round(snapshot.external / 1024 / 1024), // MB
                rss: Math.round(snapshot.rss / 1024 / 1024) // MB
            })),
            memoryIncrease: Math.round((memorySnapshots[memorySnapshots.length - 1].heapUsed - initialMemory.heapUsed) / 1024 / 1024)
        };
    }

    async benchmarkConcurrency() {
        const concurrencyLevels = [1, 2, 4, 8, 16];
        const results = {};

        for (const concurrency of concurrencyLevels) {
            const errorsPerThread = 100;
            const promises = [];

            const start = process.hrtime.bigint();

            for (let thread = 0; thread < concurrency; thread++) {
                promises.push(this.processErrorBatch(thread, errorsPerThread));
            }

            await Promise.all(promises);

            const end = process.hrtime.bigint();
            const duration = Number(end - start) / 1000000;
            const totalErrors = concurrency * errorsPerThread;

            results[concurrency] = {
                duration,
                errorsPerSecond: Math.round(totalErrors / (duration / 1000)),
                efficiencyRatio: (totalErrors / duration) / (100 / (duration / concurrency))
            };
        }

        return results;
    }

    async processErrorBatch(threadId, count) {
        for (let i = 0; i < count; i++) {
            const error = new Error(`Thread ${threadId} error ${i}`);
            error.code = `THREAD_${threadId}`;
            this.recovery.analyzeError(error);
        }
    }

    async benchmarkRecoveryStrategies() {
        const strategies = ['network', 'file', 'validation', 'phase'];
        const results = {};

        for (const strategy of strategies) {
            let successCount = 0;
            let attempts = 0;
            const times = [];

            const testOperation = async () => {
                attempts++;
                if (attempts < 3) {
                    const error = new Error(`Strategy test error for ${strategy}`);
                    error.code = strategy === 'network' ? 'ETIMEDOUT' : 'TEST_ERROR';
                    throw error;
                }
                return 'success';
            };

            // Run multiple tests for this strategy
            for (let i = 0; i < 10; i++) {
                attempts = 0;

                const start = process.hrtime.bigint();

                try {
                    await this.recovery.executeWithRecovery(testOperation, {
                        strategy: strategy
                    });
                    successCount++;
                } catch (error) {
                    // Recovery failed
                }

                const end = process.hrtime.bigint();
                times.push(Number(end - start) / 1000000);
            }

            results[strategy] = {
                successRate: (successCount / 10) * 100,
                avgTime: times.reduce((a, b) => a + b, 0) / times.length,
                minTime: Math.min(...times),
                maxTime: Math.max(...times)
            };
        }

        return results;
    }

    generateReport() {
        console.log('\n' + '='.repeat(60));
        console.log('📊 PERFORMANCE BENCHMARK RESULTS');
        console.log('='.repeat(60));

        // Single Error Processing
        const singleError = this.results['Single Error Processing Speed'];
        console.log('\n🔍 Single Error Processing:');
        console.log(`  Average Time: ${singleError.avgTime.toFixed(3)}ms`);
        console.log(`  Min Time: ${singleError.minTime.toFixed(3)}ms`);
        console.log(`  Max Time: ${singleError.maxTime.toFixed(3)}ms`);
        console.log(`  Median Time: ${singleError.medianTime.toFixed(3)}ms`);

        // Batch Processing
        const batch = this.results['Batch Error Processing'];
        console.log('\n📦 Batch Processing Performance:');
        for (const [batchSize, data] of Object.entries(batch)) {
            console.log(`  ${batchSize} errors: ${data.errorsPerSecond} errors/sec (${data.avgPerError.toFixed(3)}ms/error)`);
        }

        // Checkpoint Performance
        const checkpoints = this.results['Checkpoint Performance'];
        console.log('\n💾 Checkpoint Performance:');
        for (const [operation, sizes] of Object.entries(checkpoints)) {
            console.log(`  ${operation.charAt(0).toUpperCase() + operation.slice(1)}:`);
            for (const [size, times] of Object.entries(sizes)) {
                console.log(`    ${size}: ${times.avgTime.toFixed(2)}ms avg (${times.minTime.toFixed(2)}-${times.maxTime.toFixed(2)}ms)`);
            }
        }

        // Memory Usage
        const memory = this.results['Memory Usage Under Load'];
        console.log('\n🧠 Memory Usage:');
        memory.snapshots.forEach(snapshot => {
            console.log(`  ${snapshot.errorCount} errors: ${snapshot.heapUsed}MB heap, ${snapshot.rss}MB RSS`);
        });
        console.log(`  Total Memory Increase: ${memory.memoryIncrease}MB`);

        // Concurrency
        const concurrency = this.results['Concurrent Operations'];
        console.log('\n🔄 Concurrency Performance:');
        for (const [level, data] of Object.entries(concurrency)) {
            console.log(`  ${level} threads: ${data.errorsPerSecond} errors/sec (efficiency: ${data.efficiencyRatio.toFixed(2)})`);
        }

        // Recovery Strategies
        const strategies = this.results['Recovery Strategy Performance'];
        console.log('\n🛠️ Recovery Strategy Performance:');
        for (const [strategy, data] of Object.entries(strategies)) {
            console.log(`  ${strategy}: ${data.successRate}% success, ${data.avgTime.toFixed(2)}ms avg`);
        }

        // Overall Metrics
        const metrics = this.recovery.getMetrics();
        console.log('\n📈 System Metrics:');
        console.log(`  Total Errors Processed: ${metrics.totalErrors}`);
        console.log(`  Recovery Success Rate: ${metrics.successRate}`);
        console.log(`  Checkpoints Created: ${metrics.checkpointsSaved}`);
    }
}

// Run benchmark if called directly
if (require.main === module) {
    (async () => {
        try {
            const benchmark = new PerformanceBenchmark();
            await benchmark.runBenchmarks();
        } catch (error) {
            console.error('Benchmark failed:', error);
            process.exit(1);
        }
    })();
} else {
    module.exports = PerformanceBenchmark;
}