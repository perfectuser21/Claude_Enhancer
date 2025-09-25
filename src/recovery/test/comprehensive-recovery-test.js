/**
 * Claude Enhancer 5.0 - Comprehensive Error Recovery Test Suite
 * Tests all aspects of the advanced error recovery system
 */

const assert = require('assert');
const { EventEmitter } = require('events');
const fs = require('fs').promises;
const path = require('path');

const ErrorRecovery = require('../ErrorRecovery');
const RetryManager = require('../RetryManager');
const ErrorDiagnostics = require('../ErrorDiagnostics');
const CheckpointManager = require('../CheckpointManager');
const ErrorAnalytics = require('../ErrorAnalytics');

class ComprehensiveRecoveryTest extends EventEmitter {
    constructor() {
        super();
        this.testResults = {
            passed: 0,
            failed: 0,
            skipped: 0,
            total: 0,
            details: []
        };

        this.testData = {
            sampleErrors: this.generateSampleErrors(),
            testCheckpoints: this.generateTestCheckpoints(),
            mockOperations: this.createMockOperations()
        };

        this.setupTestEnvironment();
    }

    /**
     * Setup test environment
     */
    async setupTestEnvironment() {
        this.testDir = path.join(__dirname, '../../../.test-recovery');

        try {
            await fs.mkdir(this.testDir, { recursive: true });
        } catch (error) {
            if (error.code !== 'EEXIST') throw error;
        }

        // Initialize systems with test configuration
        this.errorRecovery = new ErrorRecovery({
            checkpointsDir: path.join(this.testDir, 'checkpoints'),
            enableMetrics: true,
            gracefulDegradation: true
        });

        this.retryManager = new RetryManager({
            defaultMaxRetries: 2,
            baseDelay: 100,
            maxDelay: 1000
        });

        this.diagnostics = new ErrorDiagnostics({
            logDir: path.join(this.testDir, 'logs'),
            enableMetrics: true
        });

        this.checkpointManager = new CheckpointManager({
            checkpointsDir: path.join(this.testDir, 'checkpoints')
        });

        this.analytics = new ErrorAnalytics({
            dataDir: path.join(this.testDir, 'analytics'),
            enableMachineLearning: false, // Disable for testing
            enablePrediction: false
        });

        await this.waitForInitialization();
    }

    /**
     * Wait for all systems to initialize
     */
    async waitForInitialization() {
        return new Promise((resolve) => {
            let initialized = 0;
            const totalSystems = 1; // Only ErrorRecovery emits 'ready'

            const checkInitialization = () => {
                initialized++;
                if (initialized >= totalSystems) {
                    resolve();
                }
            };

            this.errorRecovery.on('ready', checkInitialization);

            // Fallback timeout
            setTimeout(() => resolve(), 2000);
        });
    }

    /**
     * Run all tests
     */
    async runAllTests() {
        console.log('🧪 Starting Comprehensive Error Recovery Tests...\n');

        const testSuites = [
            { name: 'Error Recovery Core', tests: this.testErrorRecoveryCore.bind(this) },
            { name: 'Retry Management', tests: this.testRetryManagement.bind(this) },
            { name: 'Circuit Breakers', tests: this.testCircuitBreakers.bind(this) },
            { name: 'Checkpoint Management', tests: this.testCheckpointManagement.bind(this) },
            { name: 'Error Diagnostics', tests: this.testErrorDiagnostics.bind(this) },
            { name: 'Error Analytics', tests: this.testErrorAnalytics.bind(this) },
            { name: 'Pattern Learning', tests: this.testPatternLearning.bind(this) },
            { name: 'Recovery Strategies', tests: this.testRecoveryStrategies.bind(this) },
            { name: 'Integration Tests', tests: this.testIntegration.bind(this) },
            { name: 'Performance Tests', tests: this.testPerformance.bind(this) }
        ];

        for (const suite of testSuites) {
            console.log(`\n🔍 Running ${suite.name} Tests:`);
            await this.runTestSuite(suite.name, suite.tests);
        }

        await this.generateTestReport();
        await this.cleanup();

        return this.testResults;
    }

    /**
     * Run a test suite
     */
    async runTestSuite(suiteName, testFunction) {
        try {
            await testFunction();
        } catch (error) {
            this.recordTestResult(`${suiteName} - Suite Error`, false, error.message);
        }
    }

    /**
     * Test Error Recovery Core functionality
     */
    async testErrorRecoveryCore() {
        // Test basic error recovery
        await this.runTest('Basic Error Recovery', async () => {
            let recovered = false;
            const operation = async () => {
                if (!recovered) {
                    recovered = true;
                    throw new Error('Test error for recovery');
                }
                return 'success';
            };

            const result = await this.errorRecovery.executeWithRecovery(operation, {
                strategy: 'network',
                onRecover: () => { recovered = true; }
            });

            assert.strictEqual(result, 'success');
        });

        // Test checkpoint creation and restoration
        await this.runTest('Checkpoint Recovery', async () => {
            const checkpointId = 'test-checkpoint-' + Date.now();
            const testData = { operation: 'test', value: 42 };

            await this.errorRecovery.createCheckpoint(checkpointId, testData);

            const operation = async () => {
                throw new Error('Test error requiring checkpoint restore');
            };

            try {
                await this.errorRecovery.executeWithRecovery(operation, {
                    checkpointId,
                    strategy: 'validation'
                });
            } catch (error) {
                // Expected to fail, but checkpoint should be created
            }

            const checkpoints = await this.errorRecovery.listCheckpoints();
            assert(checkpoints.some(cp => cp.id === checkpointId));
        });

        // Test graceful degradation
        await this.runTest('Graceful Degradation', async () => {
            const operation = async () => {
                const error = new Error('Critical system failure');
                error.code = 'ENOMEM';
                throw error;
            };

            try {
                await this.errorRecovery.executeWithRecovery(operation, {
                    strategy: 'phase'
                });
            } catch (error) {
                // Should attempt graceful degradation
                assert(error.recoveryContext);
                assert(error.suggestions);
            }
        });

        // Test error enhancement
        await this.runTest('Error Enhancement', async () => {
            const originalError = new Error('Original error');
            originalError.code = 'ENOENT';

            const operation = async () => {
                throw originalError;
            };

            try {
                await this.errorRecovery.executeWithRecovery(operation);
            } catch (enhancedError) {
                assert(enhancedError.recoveryContext);
                assert(enhancedError.suggestions);
                assert(enhancedError.recoveryCommands);
                assert.strictEqual(enhancedError.category, 'filesystem');
            }
        });
    }

    /**
     * Test Retry Management functionality
     */
    async testRetryManagement() {
        // Test basic retry logic
        await this.runTest('Basic Retry Logic', async () => {
            let attempts = 0;
            const operation = async () => {
                attempts++;
                if (attempts < 3) {
                    const error = new Error('Transient error');
                    error.code = 'ETIMEDOUT';
                    throw error;
                }
                return 'success';
            };

            const result = await this.retryManager.executeWithRetry(operation, 'network');
            assert.strictEqual(result, 'success');
            assert(attempts >= 3);
        });

        // Test retry strategy customization
        await this.runTest('Custom Retry Strategy', async () => {
            this.retryManager.addRetryStrategy('test-strategy', {
                maxRetries: 1,
                baseDelay: 50,
                retryCondition: (error) => error.message.includes('retry')
            });

            let attempts = 0;
            const operation = async () => {
                attempts++;
                if (attempts === 1) {
                    throw new Error('Should retry this');
                }
                return 'success';
            };

            const result = await this.retryManager.executeWithRetry(operation, 'test-strategy');
            assert.strictEqual(result, 'success');
            assert.strictEqual(attempts, 2);
        });

        // Test retry metrics
        await this.runTest('Retry Metrics', async () => {
            const initialMetrics = this.retryManager.getMetrics('network');

            try {
                await this.retryManager.executeWithRetry(async () => {
                    throw new Error('Always fail');
                }, 'network');
            } catch (error) {
                // Expected to fail
            }

            const finalMetrics = this.retryManager.getMetrics('network');
            assert(finalMetrics.totalAttempts > initialMetrics.totalAttempts);
            assert(finalMetrics.failedRetries > initialMetrics.failedRetries);
        });
    }

    /**
     * Test Circuit Breaker functionality
     */
    async testCircuitBreakers() {
        // Test circuit breaker opening
        await this.runTest('Circuit Breaker Opening', async () => {
            // Simulate multiple failures to open circuit breaker
            for (let i = 0; i < 6; i++) {
                this.errorRecovery.updateCircuitBreaker('network', false, new Error('Test failure'));
            }

            const breakerStatus = this.errorRecovery.checkCircuitBreaker('network');
            assert.strictEqual(breakerStatus.canProceed, false);
            assert.strictEqual(breakerStatus.state, 'OPEN');
        });

        // Test circuit breaker recovery
        await this.runTest('Circuit Breaker Recovery', async () => {
            const breaker = this.errorRecovery.circuitBreakers.get('network');
            breaker.state = 'HALF_OPEN';

            // Simulate successful operation
            this.errorRecovery.updateCircuitBreaker('network', true);

            const breakerStatus = this.errorRecovery.checkCircuitBreaker('network');
            assert.strictEqual(breakerStatus.state, 'CLOSED');
        });

        // Test circuit breaker metrics
        await this.runTest('Circuit Breaker Metrics', async () => {
            const analytics = this.errorRecovery.getCircuitBreakerAnalytics();
            assert(typeof analytics === 'object');
            assert(analytics.network);
            assert(analytics.network.state);
            assert(typeof analytics.network.failureCount === 'number');
        });
    }

    /**
     * Test Checkpoint Management
     */
    async testCheckpointManagement() {
        // Test checkpoint creation
        await this.runTest('Checkpoint Creation', async () => {
            const checkpointId = 'test-checkpoint-creation';
            const testState = { data: 'test', timestamp: Date.now() };

            const checkpoint = await this.checkpointManager.createCheckpoint(
                checkpointId,
                testState,
                { description: 'Test checkpoint', tags: ['test'] }
            );

            assert.strictEqual(checkpoint.id, checkpointId);
            assert.strictEqual(checkpoint.description, 'Test checkpoint');
            assert(checkpoint.metadata);
            assert(checkpoint.metadata.hash);
        });

        // Test checkpoint statistics
        await this.runTest('Checkpoint Statistics', async () => {
            const stats = await this.checkpointManager.getStatistics();
            assert(typeof stats.totalCheckpoints === 'number');
            assert(typeof stats.totalSize === 'number');
            assert(stats.totalCheckpoints >= 1); // From previous test
        });

        // Test checkpoint validation
        await this.runTest('Checkpoint Validation', async () => {
            try {
                await this.checkpointManager.createCheckpoint('', {}); // Invalid ID
                assert.fail('Should have thrown validation error');
            } catch (error) {
                assert(error.message.includes('Checkpoint ID'));
            }
        });
    }

    /**
     * Test Error Diagnostics
     */
    async testErrorDiagnostics() {
        // Test error analysis
        await this.runTest('Error Analysis', async () => {
            const testError = new Error('Cannot read property "test" of undefined');
            testError.name = 'TypeError';

            const diagnostic = await this.diagnostics.analyzeError(testError, {
                operation: 'test',
                phase: 'Phase3_Implementation'
            });

            assert(diagnostic.id);
            assert(diagnostic.analysis);
            assert(diagnostic.analysis.patternMatches);
            assert.strictEqual(diagnostic.category, 'javascript');
            assert.strictEqual(diagnostic.severity, 'high');
        });

        // Test pattern matching
        await this.runTest('Pattern Matching', async () => {
            const networkError = new Error('ECONNREFUSED: Connection refused');
            networkError.code = 'ECONNREFUSED';

            const diagnostic = await this.diagnostics.analyzeError(networkError);

            assert.strictEqual(diagnostic.category, 'network');
            assert(diagnostic.analysis.suggestions.length > 0);
            assert(diagnostic.analysis.rootCause);
        });

        // Test diagnostic reports
        await this.runTest('Diagnostic Reports', async () => {
            const report = await this.diagnostics.generateReport({
                includeHistory: true,
                includeMetrics: true,
                includePatterns: true
            });

            assert(report.generatedAt);
            assert(report.summary);
            assert(typeof report.summary.totalErrors === 'number');
        });
    }

    /**
     * Test Error Analytics
     */
    async testErrorAnalytics() {
        // Test error analysis
        await this.runTest('Analytics Error Analysis', async () => {
            const testError = new Error('Test analytics error');
            const context = {
                phase: 'Phase3_Implementation',
                operationType: 'file_operation'
            };

            const analysis = await this.analytics.analyzeError(testError, context);

            assert(analysis.id);
            assert(analysis.features);
            assert(analysis.classifications);
            assert(typeof analysis.confidence === 'number');
            assert(analysis.confidence >= 0 && analysis.confidence <= 1);
        });

        // Test feature extraction
        await this.runTest('Feature Extraction', async () => {
            const error = new Error('Network timeout occurred');
            error.code = 'ETIMEDOUT';

            const context = { timeSinceLastError: 5000 };

            const analysis = await this.analytics.analyzeError(error, context);

            assert(analysis.features.temporal);
            assert(analysis.features.content);
            assert(analysis.features.context);
            assert(typeof analysis.features.temporal.hour === 'number');
            assert(typeof analysis.features.content.messageLength === 'number');
        });

        // Test analytics metrics
        await this.runTest('Analytics Metrics', async () => {
            const metrics = this.analytics.getMetrics();

            assert(typeof metrics.totalAnalyzed === 'number');
            assert(typeof metrics.averageProcessingTime === 'number');
            assert(typeof metrics.averageConfidence === 'number');
        });
    }

    /**
     * Test Pattern Learning
     */
    async testPatternLearning() {
        // Test error frequency tracking
        await this.runTest('Error Frequency Tracking', async () => {
            const error = new Error('Recurring test error');

            // Track the same error multiple times
            for (let i = 0; i < 5; i++) {
                this.errorRecovery.trackErrorFrequency(error);
            }

            const signature = this.errorRecovery.generateErrorSignature(error);
            const frequencies = this.errorRecovery.errorFrequencyTracker.get(signature);

            assert(frequencies);
            assert.strictEqual(frequencies.length, 5);
        });

        // Test pattern detection
        await this.runTest('Pattern Detection', async () => {
            // Generate multiple similar errors to trigger pattern detection
            for (let i = 0; i < 4; i++) {
                const error = new Error('Pattern test error');
                error.timestamp = Date.now() - (i * 1000);

                this.errorRecovery.trackErrorFrequency(error);
                this.errorRecovery.recoveryHistory.push({
                    timestamp: new Date(error.timestamp).toISOString(),
                    error: error.message,
                    category: 'test',
                    strategy: 'network',
                    attempt: 1
                });
            }

            this.errorRecovery.analyzeErrorPatterns();

            const patterns = this.errorRecovery.patternLearningData.get('frequency') || [];
            assert(Array.isArray(patterns));
        });
    }

    /**
     * Test Recovery Strategies
     */
    async testRecoveryStrategies() {
        // Test git recovery strategy
        await this.runTest('Git Recovery Strategy', async () => {
            const gitError = new Error('Git operation failed');
            gitError.category = 'git';

            const analysis = { category: 'git', severity: 'medium' };
            const recoveryAction = this.errorRecovery.recoveryActions.get('resetGitState');

            // Mock git commands to avoid actual git operations in tests
            const originalSpawn = require('child_process').spawn;
            require('child_process').spawn = (command, args) => {
                const mockProcess = new EventEmitter();
                setTimeout(() => mockProcess.emit('close', 0), 10);
                return mockProcess;
            };

            const result = await recoveryAction(gitError, analysis, null);

            // Restore original spawn
            require('child_process').spawn = originalSpawn;

            assert(result.success);
            assert(Array.isArray(result.actions));
        });

        // Test filesystem recovery strategy
        await this.runTest('Filesystem Recovery Strategy', async () => {
            const fsError = new Error("ENOENT: no such file or directory, open '/test/path/file.txt'");
            fsError.code = 'ENOENT';

            const analysis = { category: 'filesystem', severity: 'high' };
            const recoveryAction = this.errorRecovery.recoveryActions.get('createMissingPaths');

            const result = await recoveryAction(fsError, analysis, null);

            assert(result.success);
            assert(result.actions.length > 0);
        });

        // Test network recovery strategy
        await this.runTest('Network Recovery Strategy', async () => {
            const networkError = new Error('ETIMEDOUT: Network timeout');
            networkError.code = 'ETIMEDOUT';
            networkError.retryCount = 1;

            const analysis = { category: 'network', severity: 'medium' };
            const recoveryAction = this.errorRecovery.recoveryActions.get('exponentialBackoff');

            const startTime = Date.now();
            const result = await recoveryAction(networkError, analysis, null);
            const elapsed = Date.now() - startTime;

            assert(result.success);
            assert(elapsed >= 100); // Should have waited for backoff delay
        });
    }

    /**
     * Test Integration between components
     */
    async testIntegration() {
        // Test full error recovery flow
        await this.runTest('Full Recovery Flow', async () => {
            let attempts = 0;
            const operation = async () => {
                attempts++;
                if (attempts < 3) {
                    const error = new Error('Integration test error');
                    error.code = 'ETIMEDOUT';
                    throw error;
                }
                return 'integration success';
            };

            const result = await this.errorRecovery.executeWithRecovery(operation, {
                strategy: 'network',
                context: { phase: 'Phase3_Implementation' }
            });

            assert.strictEqual(result, 'integration success');
            assert(attempts >= 3);

            // Check that all systems recorded the interactions
            const metrics = this.errorRecovery.getMetrics();
            assert(metrics.totalErrors > 0);
        });

        // Test analytics integration
        await this.runTest('Analytics Integration', async () => {
            const error = new Error('Analytics integration test');
            const context = { phase: 'Phase3_Implementation', operationType: 'test' };

            // Analyze error with both diagnostics and analytics
            const diagnostic = await this.diagnostics.analyzeError(error, context);
            const analysis = await this.analytics.analyzeError(error, context);

            assert(diagnostic.id);
            assert(analysis.id);
            assert.strictEqual(diagnostic.error.message, analysis.error.message);
        });
    }

    /**
     * Test Performance characteristics
     */
    async testPerformance() {
        // Test processing speed
        await this.runTest('Processing Speed', async () => {
            const errors = this.testData.sampleErrors.slice(0, 10);
            const startTime = Date.now();

            for (const error of errors) {
                await this.diagnostics.analyzeError(error);
            }

            const elapsed = Date.now() - startTime;
            const avgTime = elapsed / errors.length;

            // Should process errors reasonably quickly (under 100ms each on average)
            assert(avgTime < 100, `Average processing time ${avgTime}ms is too slow`);
        });

        // Test memory usage
        await this.runTest('Memory Usage', async () => {
            const initialMemory = process.memoryUsage();

            // Process many errors
            for (let i = 0; i < 100; i++) {
                const error = new Error(`Test error ${i}`);
                await this.diagnostics.analyzeError(error);
            }

            const finalMemory = process.memoryUsage();
            const memoryIncrease = finalMemory.heapUsed - initialMemory.heapUsed;

            // Memory increase should be reasonable (under 50MB for 100 errors)
            assert(memoryIncrease < 50 * 1024 * 1024,
                   `Memory increase ${memoryIncrease} bytes is too high`);
        });

        // Test concurrent processing
        await this.runTest('Concurrent Processing', async () => {
            const promises = [];
            const startTime = Date.now();

            // Process multiple errors concurrently
            for (let i = 0; i < 10; i++) {
                const error = new Error(`Concurrent test error ${i}`);
                promises.push(this.diagnostics.analyzeError(error));
            }

            await Promise.all(promises);
            const elapsed = Date.now() - startTime;

            // Concurrent processing should be faster than sequential
            assert(elapsed < 1000, `Concurrent processing took ${elapsed}ms, too slow`);
        });
    }

    /**
     * Run a single test
     */
    async runTest(testName, testFunction) {
        this.testResults.total++;

        try {
            await testFunction();
            this.testResults.passed++;
            this.recordTestResult(testName, true);
            console.log(`  ✅ ${testName}`);
        } catch (error) {
            this.testResults.failed++;
            this.recordTestResult(testName, false, error.message);
            console.log(`  ❌ ${testName}: ${error.message}`);
        }
    }

    /**
     * Record test result
     */
    recordTestResult(testName, passed, error = null) {
        this.testResults.details.push({
            name: testName,
            passed,
            error,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Generate test report
     */
    async generateTestReport() {
        const report = {
            summary: {
                total: this.testResults.total,
                passed: this.testResults.passed,
                failed: this.testResults.failed,
                successRate: ((this.testResults.passed / this.testResults.total) * 100).toFixed(2) + '%'
            },
            systems: {
                errorRecovery: this.errorRecovery.getMetrics(),
                retryManager: this.retryManager.getMetrics(),
                analytics: this.analytics.getMetrics()
            },
            details: this.testResults.details,
            generatedAt: new Date().toISOString()
        };

        const reportPath = path.join(this.testDir, 'test-report.json');
        await fs.writeFile(reportPath, JSON.stringify(report, null, 2));

        console.log(`\n📊 Test Report Summary:`);
        console.log(`   Total Tests: ${report.summary.total}`);
        console.log(`   Passed: ${report.summary.passed}`);
        console.log(`   Failed: ${report.summary.failed}`);
        console.log(`   Success Rate: ${report.summary.successRate}`);
        console.log(`\n   Report saved to: ${reportPath}`);

        return report;
    }

    /**
     * Generate sample test data
     */
    generateSampleErrors() {
        return [
            new Error('ENOENT: no such file or directory'),
            Object.assign(new Error('ETIMEDOUT: Network timeout'), { code: 'ETIMEDOUT' }),
            Object.assign(new Error('EACCES: permission denied'), { code: 'EACCES' }),
            new Error('Cannot read property "test" of undefined'),
            Object.assign(new Error('ECONNREFUSED: Connection refused'), { code: 'ECONNREFUSED' }),
            new Error('ValidationError: Missing required field'),
            Object.assign(new Error('ENOMEM: Cannot allocate memory'), { code: 'ENOMEM' }),
            new Error('SyntaxError: Unexpected token'),
            new Error('Git operation failed: fatal: not a git repository'),
            Object.assign(new Error('EBUSY: resource busy or locked'), { code: 'EBUSY' })
        ];
    }

    generateTestCheckpoints() {
        return [
            { id: 'test-checkpoint-1', data: { phase: 'Phase1', step: 1 } },
            { id: 'test-checkpoint-2', data: { phase: 'Phase2', step: 5 } },
            { id: 'test-checkpoint-3', data: { phase: 'Phase3', step: 10 } }
        ];
    }

    createMockOperations() {
        return {
            successfulOperation: async () => 'success',
            failingOperation: async () => { throw new Error('Mock failure'); },
            intermittentOperation: (() => {
                let callCount = 0;
                return async () => {
                    callCount++;
                    if (callCount <= 2) throw new Error('Intermittent failure');
                    return 'eventual success';
                };
            })()
        };
    }

    /**
     * Cleanup test environment
     */
    async cleanup() {
        try {
            // Clean up test directory
            await fs.rm(this.testDir, { recursive: true, force: true });
        } catch (error) {
            console.warn(`Warning: Could not clean up test directory: ${error.message}`);
        }
    }
}

// Export for use as module or run directly
if (require.main === module) {
    (async () => {
        try {
            const testSuite = new ComprehensiveRecoveryTest();
            const results = await testSuite.runAllTests();

            process.exit(results.failed > 0 ? 1 : 0);
        } catch (error) {
            console.error('Test suite failed:', error);
            process.exit(1);
        }
    })();
} else {
    module.exports = ComprehensiveRecoveryTest;
}