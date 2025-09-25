/**
 * Claude Enhancer Plus - Performance Test Validation
 * Quick validation script to test the performance testing framework
 */

const path = require('path');
const fs = require('fs').promises;

// Import test components
const ErrorRecovery = require('../ErrorRecovery');
const CheckpointManager = require('../CheckpointManager');
const PerformanceBenchmarks = require('./performance-benchmarks');

class PerformanceTestValidator {
    constructor() {
        this.testResults = {
            passed: 0,
            failed: 0,
            errors: []
        };
    }

    async validatePerformanceTests() {
        console.log('🔍 Validating Performance Test Framework...');
        console.log('='.repeat(50));

        try {
            // Test 1: Component Initialization
            await this.testComponentInitialization();

            // Test 2: Basic Recovery Speed Test
            await this.testBasicRecoverySpeed();

            // Test 3: Checkpoint Performance Test
            await this.testCheckpointPerformance();

            // Test 4: Memory Usage Test
            await this.testMemoryUsage();

            // Test 5: Concurrent Operations Test
            await this.testConcurrentOperations();

            // Generate validation report
            await this.generateValidationReport();

            console.log('\n✅ Performance Test Framework Validation Complete');
            console.log(`✅ Tests Passed: ${this.testResults.passed}`);
            console.log(`❌ Tests Failed: ${this.testResults.failed}`);

            if (this.testResults.failed === 0) {
                console.log('🎉 All tests passed! Performance framework is ready.');
                return true;
            } else {
                console.log('⚠️  Some tests failed. Check the validation report.');
                return false;
            }

        } catch (error) {
            console.error('❌ Validation failed:', error);
            this.testResults.errors.push(error.message);
            return false;
        }
    }

    async testComponentInitialization() {
        console.log('🧪 Test 1: Component Initialization');

        try {
            // Test ErrorRecovery initialization
            const errorRecovery = new ErrorRecovery({
                enableMetrics: true,
                checkpointsDir: './test-checkpoints'
            });

            if (!errorRecovery) {
                throw new Error('ErrorRecovery failed to initialize');
            }

            // Test CheckpointManager initialization
            const checkpointManager = new CheckpointManager({
                checkpointsDir: './test-checkpoints'
            });

            if (!checkpointManager) {
                throw new Error('CheckpointManager failed to initialize');
            }

            // Test PerformanceBenchmarks initialization
            const benchmarks = new PerformanceBenchmarks({
                benchmarkIterations: 5,
                warmupIterations: 2
            });

            if (!benchmarks) {
                throw new Error('PerformanceBenchmarks failed to initialize');
            }

            console.log('  ✅ All components initialized successfully');
            this.testResults.passed++;

        } catch (error) {
            console.log('  ❌ Component initialization failed:', error.message);
            this.testResults.failed++;
            this.testResults.errors.push(`Component initialization: ${error.message}`);
        }
    }

    async testBasicRecoverySpeed() {
        console.log('🧪 Test 2: Basic Recovery Speed Test');

        try {
            const errorRecovery = new ErrorRecovery({
                enableMetrics: true,
                maxRetries: 2
            });

            // Create a simple error scenario
            const testError = new Error('Test network error');
            testError.code = 'ECONNRESET';

            const startTime = Date.now();

            // Test recovery
            await errorRecovery.recoverFromError(testError, async () => {
                // Simulate successful operation after recovery
                await new Promise(resolve => setTimeout(resolve, 10));
            });

            const duration = Date.now() - startTime;

            if (duration < 5000) { // Should complete within 5 seconds
                console.log(`  ✅ Recovery completed in ${duration}ms`);
                this.testResults.passed++;
            } else {
                throw new Error(`Recovery took too long: ${duration}ms`);
            }

        } catch (error) {
            console.log('  ❌ Recovery speed test failed:', error.message);
            this.testResults.failed++;
            this.testResults.errors.push(`Recovery speed: ${error.message}`);
        }
    }

    async testCheckpointPerformance() {
        console.log('🧪 Test 3: Checkpoint Performance Test');

        try {
            const checkpointManager = new CheckpointManager({
                checkpointsDir: './test-checkpoints'
            });

            const testData = {
                id: 'test-checkpoint',
                timestamp: Date.now(),
                data: 'x'.repeat(1024) // 1KB of data
            };

            // Test checkpoint creation
            const startTime = Date.now();
            const checkpoint = await checkpointManager.createCheckpoint('perf-test', testData);
            const createDuration = Date.now() - startTime;

            if (!checkpoint) {
                throw new Error('Checkpoint creation failed');
            }

            // Test checkpoint restoration
            const restoreStartTime = Date.now();
            const restored = await checkpointManager.restoreCheckpoint('perf-test');
            const restoreDuration = Date.now() - restoreStartTime;

            if (!restored) {
                throw new Error('Checkpoint restoration failed');
            }

            console.log(`  ✅ Checkpoint create: ${createDuration}ms, restore: ${restoreDuration}ms`);
            this.testResults.passed++;

        } catch (error) {
            console.log('  ❌ Checkpoint performance test failed:', error.message);
            this.testResults.failed++;
            this.testResults.errors.push(`Checkpoint performance: ${error.message}`);
        }
    }

    async testMemoryUsage() {
        console.log('🧪 Test 4: Memory Usage Test');

        try {
            const initialMemory = process.memoryUsage();
            const errorRecovery = new ErrorRecovery({
                enableMetrics: true
            });

            // Perform multiple recovery operations to test memory usage
            const operations = [];
            for (let i = 0; i < 10; i++) {
                operations.push((async () => {
                    const error = new Error(`Test error ${i}`);
                    error.code = 'TEST_ERROR';
                    await errorRecovery.recoverFromError(error, async () => {
                        await new Promise(resolve => setTimeout(resolve, 5));
                    });
                })());
            }

            await Promise.all(operations);

            const finalMemory = process.memoryUsage();
            const memoryGrowth = finalMemory.heapUsed - initialMemory.heapUsed;

            // Memory growth should be reasonable (less than 50MB for this test)
            if (memoryGrowth < 50 * 1024 * 1024) {
                console.log(`  ✅ Memory growth: ${(memoryGrowth / 1024 / 1024).toFixed(2)}MB`);
                this.testResults.passed++;
            } else {
                throw new Error(`Excessive memory growth: ${(memoryGrowth / 1024 / 1024).toFixed(2)}MB`);
            }

        } catch (error) {
            console.log('  ❌ Memory usage test failed:', error.message);
            this.testResults.failed++;
            this.testResults.errors.push(`Memory usage: ${error.message}`);
        }
    }

    async testConcurrentOperations() {
        console.log('🧪 Test 5: Concurrent Operations Test');

        try {
            const errorRecovery = new ErrorRecovery({
                enableMetrics: true
            });

            const concurrency = 5;
            const startTime = Date.now();

            // Run concurrent recovery operations
            const promises = [];
            for (let i = 0; i < concurrency; i++) {
                promises.push((async () => {
                    const error = new Error(`Concurrent error ${i}`);
                    error.code = 'CONCURRENT_ERROR';
                    await errorRecovery.recoverFromError(error, async () => {
                        await new Promise(resolve => setTimeout(resolve, Math.random() * 50));
                    });
                })());
            }

            const results = await Promise.allSettled(promises);
            const duration = Date.now() - startTime;

            const successful = results.filter(r => r.status === 'fulfilled').length;
            const failed = results.filter(r => r.status === 'rejected').length;

            if (successful === concurrency && duration < 3000) {
                console.log(`  ✅ Concurrent operations: ${successful}/${concurrency} successful in ${duration}ms`);
                this.testResults.passed++;
            } else {
                throw new Error(`Concurrent test failed: ${successful}/${concurrency} successful, ${duration}ms`);
            }

        } catch (error) {
            console.log('  ❌ Concurrent operations test failed:', error.message);
            this.testResults.failed++;
            this.testResults.errors.push(`Concurrent operations: ${error.message}`);
        }
    }

    async generateValidationReport() {
        const report = {
            timestamp: new Date().toISOString(),
            testSuite: 'Performance Test Framework Validation',
            results: {
                passed: this.testResults.passed,
                failed: this.testResults.failed,
                total: this.testResults.passed + this.testResults.failed,
                successRate: (this.testResults.passed / (this.testResults.passed + this.testResults.failed)) * 100
            },
            errors: this.testResults.errors,
            environment: {
                nodeVersion: process.version,
                platform: process.platform,
                memory: process.memoryUsage()
            },
            recommendations: this.generateRecommendations()
        };

        try {
            await fs.mkdir('./validation-results', { recursive: true });
            const reportPath = path.join('./validation-results', 'validation-report.json');
            await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
            console.log(`📄 Validation report saved: ${reportPath}`);
        } catch (error) {
            console.log('⚠️  Could not save validation report:', error.message);
        }

        return report;
    }

    generateRecommendations() {
        const recommendations = [];

        if (this.testResults.failed > 0) {
            recommendations.push('Review and fix failed test cases before running full performance tests');
        }

        if (this.testResults.errors.some(e => e.includes('memory'))) {
            recommendations.push('Monitor memory usage carefully during performance tests');
        }

        if (this.testResults.errors.some(e => e.includes('timeout'))) {
            recommendations.push('Consider increasing timeout values for slower systems');
        }

        recommendations.push('Run performance tests in a controlled environment for consistent results');
        recommendations.push('Monitor system resources during performance testing');

        return recommendations;
    }
}

// Run validation if called directly
if (require.main === module) {
    (async () => {
        const validator = new PerformanceTestValidator();
        const success = await validator.validatePerformanceTests();
        process.exit(success ? 0 : 1);
    })();
}

module.exports = PerformanceTestValidator;