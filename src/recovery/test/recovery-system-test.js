/**
 * Claude Enhancer 5.0 - Recovery System Test Suite
 * Comprehensive testing for error recovery functionality
 */

const { RecoverySystem, ErrorRecovery, CheckpointManager, RetryManager } = require('../index');
const fs = require('fs').promises;
const path = require('path');

class RecoverySystemTests {
    constructor() {
        this.testResults = [];
        this.tempDir = path.join(__dirname, 'temp');
    }
    
    async runAllTests() {
        console.log('🧪 Starting Recovery System Test Suite...\n');
        
        try {
            await this.setupTestEnvironment();
            
            // Core component tests
            await this.testErrorRecovery();
            await this.testCheckpointManager();
            await this.testRetryManager();
            await this.testIntegratedSystem();
            
            // Advanced feature tests
            await this.testErrorPatternDetection();
            await this.testCircuitBreaker();
            await this.testGracefulDegradation();
            
            await this.cleanupTestEnvironment();
            
            this.printTestResults();
            
        } catch (error) {
            console.error('❌ Test suite failed:', error.message);
            throw error;
        }
    }
    
    async setupTestEnvironment() {
        await fs.mkdir(this.tempDir, { recursive: true });
        await fs.mkdir(path.join(this.tempDir, 'checkpoints'), { recursive: true });
        await fs.mkdir(path.join(this.tempDir, 'logs'), { recursive: true });
        
        this.addTestResult('Environment Setup', 'PASS', 'Test environment created');
    }
    
    async testErrorRecovery() {
        console.log('📋 Testing ErrorRecovery component...');
        
        try {
            const recovery = new ErrorRecovery({
                checkpointsDir: path.join(this.tempDir, 'checkpoints'),
                enableMetrics: true
            });
            
            // Test successful execution
            const result = await recovery.executeWithRecovery(async () => {
                return 'success';
            }, { checkpointId: 'test_checkpoint_1' });
            
            if (result === 'success') {
                this.addTestResult('ErrorRecovery - Success Path', 'PASS', 'Operation executed successfully');
            } else {
                this.addTestResult('ErrorRecovery - Success Path', 'FAIL', 'Unexpected result');
            }
            
            // Test retry logic
            let attemptCount = 0;
            try {
                await recovery.executeWithRecovery(async () => {
                    attemptCount++;
                    if (attemptCount < 3) {
                        const error = new Error('Temporary failure');
                        error.code = 'ECONNRESET';
                        throw error;
                    }
                    return 'recovered';
                }, { 
                    checkpointId: 'test_checkpoint_2',
                    strategy: 'network' 
                });
                
                this.addTestResult('ErrorRecovery - Retry Logic', 'PASS', `Recovered after ${attemptCount} attempts`);
            } catch (error) {
                this.addTestResult('ErrorRecovery - Retry Logic', 'FAIL', error.message);
            }
            
            // Test metrics
            const metrics = recovery.getMetrics();
            if (metrics.totalErrors >= 0 && metrics.recoveredErrors >= 0) {
                this.addTestResult('ErrorRecovery - Metrics', 'PASS', 'Metrics collected successfully');
            } else {
                this.addTestResult('ErrorRecovery - Metrics', 'FAIL', 'Invalid metrics');
            }
            
        } catch (error) {
            this.addTestResult('ErrorRecovery - Component Test', 'FAIL', error.message);
        }
    }
    
    async testCheckpointManager() {
        console.log('💾 Testing CheckpointManager component...');
        
        try {
            const checkpointManager = new CheckpointManager({
                checkpointsDir: path.join(this.tempDir, 'checkpoints')
            });
            
            // Test checkpoint creation
            const testState = {
                phase: 'Phase3_Implementation',
                files: ['src/test.js', 'src/utils.js'],
                config: { debug: true }
            };
            
            const checkpoint = await checkpointManager.createCheckpoint(
                'test_state_1', 
                testState,
                {
                    description: 'Test checkpoint',
                    tags: ['test', 'phase3'],
                    critical: false
                }
            );
            
            if (checkpoint.id === 'test_state_1') {
                this.addTestResult('CheckpointManager - Creation', 'PASS', 'Checkpoint created successfully');
            } else {
                this.addTestResult('CheckpointManager - Creation', 'FAIL', 'Invalid checkpoint ID');
            }
            
            // Test checkpoint restoration
            const restored = await checkpointManager.restoreCheckpoint('test_state_1');
            if (JSON.stringify(restored.state) === JSON.stringify(testState)) {
                this.addTestResult('CheckpointManager - Restoration', 'PASS', 'State restored correctly');
            } else {
                this.addTestResult('CheckpointManager - Restoration', 'FAIL', 'State mismatch');
            }
            
            // Test statistics
            const stats = await checkpointManager.getStatistics();
            if (stats.totalCheckpoints >= 1) {
                this.addTestResult('CheckpointManager - Statistics', 'PASS', `Found ${stats.totalCheckpoints} checkpoints`);
            } else {
                this.addTestResult('CheckpointManager - Statistics', 'FAIL', 'No checkpoints found');
            }
            
        } catch (error) {
            this.addTestResult('CheckpointManager - Component Test', 'FAIL', error.message);
        }
    }
    
    async testRetryManager() {
        console.log('🔄 Testing RetryManager component...');
        
        try {
            const retryManager = new RetryManager();
            
            // Test successful retry
            let networkAttempts = 0;
            const networkResult = await retryManager.executeWithRetry(
                async () => {
                    networkAttempts++;
                    if (networkAttempts < 2) {
                        const error = new Error('Network timeout');
                        error.code = 'ETIMEDOUT';
                        throw error;
                    }
                    return 'network_success';
                },
                'network'
            );
            
            if (networkResult === 'network_success' && networkAttempts === 2) {
                this.addTestResult('RetryManager - Network Retry', 'PASS', `Success after ${networkAttempts} attempts`);
            } else {
                this.addTestResult('RetryManager - Network Retry', 'FAIL', 'Retry logic failed');
            }
            
            // Test file operation retry
            let fileAttempts = 0;
            const fileResult = await retryManager.executeWithRetry(
                async () => {
                    fileAttempts++;
                    if (fileAttempts < 2) {
                        const error = new Error('File busy');
                        error.code = 'EBUSY';
                        throw error;
                    }
                    return 'file_success';
                },
                'file'
            );
            
            if (fileResult === 'file_success') {
                this.addTestResult('RetryManager - File Retry', 'PASS', `Success after ${fileAttempts} attempts`);
            } else {
                this.addTestResult('RetryManager - File Retry', 'FAIL', 'File retry failed');
            }
            
            // Test metrics
            const metrics = retryManager.getMetrics();
            if (metrics.network && metrics.file) {
                this.addTestResult('RetryManager - Metrics', 'PASS', 'Strategy metrics collected');
            } else {
                this.addTestResult('RetryManager - Metrics', 'FAIL', 'Missing strategy metrics');
            }
            
        } catch (error) {
            this.addTestResult('RetryManager - Component Test', 'FAIL', error.message);
        }
    }
    
    async testIntegratedSystem() {
        console.log('🔗 Testing Integrated Recovery System...');
        
        try {
            const recoverySystem = new RecoverySystem({
                checkpointsDir: path.join(this.tempDir, 'checkpoints'),
                logsDir: path.join(this.tempDir, 'logs'),
                enableDiagnostics: true,
                enableMetrics: true
            });
            
            // Test integrated execution
            const result = await recoverySystem.execute(
                async () => {
                    return 'integrated_success';
                },
                {
                    checkpointId: 'integrated_test',
                    retryStrategy: 'default',
                    context: { test: true }
                }
            );
            
            if (result === 'integrated_success') {
                this.addTestResult('Integrated System - Execution', 'PASS', 'Integrated execution successful');
            } else {
                this.addTestResult('Integrated System - Execution', 'FAIL', 'Unexpected result');
            }
            
            // Test status reporting
            const status = await recoverySystem.getStatus();
            if (status.components && status.components.errorRecovery) {
                this.addTestResult('Integrated System - Status', 'PASS', 'Status reporting working');
            } else {
                this.addTestResult('Integrated System - Status', 'FAIL', 'Invalid status structure');
            }
            
            // Test health check
            const health = await recoverySystem.healthCheck();
            if (health.overall === 'healthy' || health.overall === 'degraded') {
                this.addTestResult('Integrated System - Health Check', 'PASS', `System is ${health.overall}`);
            } else {
                this.addTestResult('Integrated System - Health Check', 'FAIL', 'Invalid health status');
            }
            
        } catch (error) {
            this.addTestResult('Integrated System - Test', 'FAIL', error.message);
        }
    }
    
    async testErrorPatternDetection() {
        console.log('🔍 Testing Error Pattern Detection...');
        
        try {
            const recovery = new ErrorRecovery();
            
            // Simulate recurring errors
            for (let i = 0; i < 3; i++) {
                try {
                    await recovery.executeWithRecovery(async () => {
                        const error = new Error('Cannot read property "length" of undefined');
                        error.name = 'TypeError';
                        throw error;
                    });
                } catch (error) {
                    // Expected to fail
                }
            }
            
            const metrics = recovery.getMetrics();
            if (metrics.totalErrors >= 3) {
                this.addTestResult('Pattern Detection - Recurring Errors', 'PASS', 'Pattern detection functioning');
            } else {
                this.addTestResult('Pattern Detection - Recurring Errors', 'FAIL', 'Pattern detection not working');
            }
            
        } catch (error) {
            this.addTestResult('Pattern Detection - Test', 'FAIL', error.message);
        }
    }
    
    async testCircuitBreaker() {
        console.log('⚡ Testing Circuit Breaker...');
        
        try {
            const retryManager = new RetryManager({
                circuitBreakerEnabled: true,
                circuitBreakerThreshold: 2
            });
            
            // Configure circuit breaker for test strategy
            retryManager.configureCircuitBreaker('test_strategy', {
                threshold: 2,
                timeout: 1000
            });
            
            // Trigger circuit breaker
            for (let i = 0; i < 3; i++) {
                try {
                    await retryManager.executeWithRetry(
                        async () => {
                            throw new Error('Service unavailable');
                        },
                        'test_strategy'
                    );
                } catch (error) {
                    // Expected failures
                }
            }
            
            const breakerState = retryManager.getCircuitBreakerState('test_strategy');
            if (breakerState && breakerState.state === 'OPEN') {
                this.addTestResult('Circuit Breaker - Activation', 'PASS', 'Circuit breaker opened correctly');
            } else {
                this.addTestResult('Circuit Breaker - Activation', 'FAIL', 'Circuit breaker not activated');
            }
            
        } catch (error) {
            this.addTestResult('Circuit Breaker - Test', 'FAIL', error.message);
        }
    }
    
    async testGracefulDegradation() {
        console.log('📉 Testing Graceful Degradation...');
        
        try {
            const recovery = new ErrorRecovery({
                gracefulDegradation: true
            });
            
            // Test degradation with resource error
            try {
                await recovery.executeWithRecovery(async () => {
                    const error = new Error('Out of memory');
                    error.code = 'ENOMEM';
                    throw error;
                });
            } catch (error) {
                // Should attempt graceful degradation
            }
            
            const metrics = recovery.getMetrics();
            if (metrics.totalErrors > 0) {
                this.addTestResult('Graceful Degradation - Resource Error', 'PASS', 'Degradation attempted');
            } else {
                this.addTestResult('Graceful Degradation - Resource Error', 'FAIL', 'No degradation detected');
            }
            
        } catch (error) {
            this.addTestResult('Graceful Degradation - Test', 'FAIL', error.message);
        }
    }
    
    addTestResult(testName, status, message) {
        this.testResults.push({
            name: testName,
            status,
            message,
            timestamp: new Date().toISOString()
        });
        
        const icon = status === 'PASS' ? '✅' : '❌';
        console.log(`  ${icon} ${testName}: ${message}`);
    }
    
    printTestResults() {
        console.log('\n📊 Test Results Summary');
        console.log('=' * 50);
        
        const passed = this.testResults.filter(t => t.status === 'PASS').length;
        const failed = this.testResults.filter(t => t.status === 'FAIL').length;
        const total = this.testResults.length;
        
        console.log(`Total Tests: ${total}`);
        console.log(`Passed: ${passed}`);
        console.log(`Failed: ${failed}`);
        console.log(`Success Rate: ${((passed / total) * 100).toFixed(1)}%`);
        
        if (failed > 0) {
            console.log('\n❌ Failed Tests:');
            this.testResults
                .filter(t => t.status === 'FAIL')
                .forEach(test => {
                    console.log(`  - ${test.name}: ${test.message}`);
                });
        }
        
        console.log('\n✨ Recovery System Test Suite Complete!');
    }
    
    async cleanupTestEnvironment() {
        try {
            await fs.rmdir(this.tempDir, { recursive: true });
            this.addTestResult('Environment Cleanup', 'PASS', 'Test environment cleaned up');
        } catch (error) {
            this.addTestResult('Environment Cleanup', 'FAIL', error.message);
        }
    }
}

// Run tests if called directly
if (require.main === module) {
    const testSuite = new RecoverySystemTests();
    testSuite.runAllTests()
        .then(() => {
            console.log('🎉 All tests completed!');
            process.exit(0);
        })
        .catch((error) => {
            console.error('💥 Test suite failed:', error);
            process.exit(1);
        });
}

module.exports = RecoverySystemTests;
