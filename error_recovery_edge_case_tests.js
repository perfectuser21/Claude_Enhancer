#!/usr/bin/env node

/**
 * Error Recovery Edge Case Tests
 * Tests extreme conditions and edge cases for the error recovery system
 */

const ErrorRecovery = require('./src/recovery/ErrorRecovery');
const fs = require('fs').promises;
const path = require('path');

class EdgeCaseTestSuite {
    constructor() {
        this.testResults = [];
        this.recovery = new ErrorRecovery({
            maxRetries: 5,
            baseRetryDelay: 50,
            enableMetrics: true,
            gracefulDegradation: true
        });
    }

    async runAllTests() {
        console.log('🧪 Error Recovery Edge Case Test Suite');
        console.log('=' * 50);

        const tests = [
            { name: 'Extremely Long Error Messages', test: this.testLongErrorMessages.bind(this) },
            { name: 'Malformed Error Objects', test: this.testMalformedErrors.bind(this) },
            { name: 'Circular Reference Errors', test: this.testCircularReferences.bind(this) },
            { name: 'High Frequency Error Bursts', test: this.testHighFrequencyErrors.bind(this) },
            { name: 'Memory Pressure Recovery', test: this.testMemoryPressure.bind(this) },
            { name: 'Concurrent Checkpoint Operations', test: this.testConcurrentCheckpoints.bind(this) },
            { name: 'Network Instability Simulation', test: this.testNetworkInstability.bind(this) },
            { name: 'File System Edge Cases', test: this.testFileSystemEdgeCases.bind(this) },
            { name: 'Recursive Error Scenarios', test: this.testRecursiveErrors.bind(this) },
            { name: 'Race Condition Handling', test: this.testRaceConditions.bind(this) }
        ];

        for (const test of tests) {
            await this.runTest(test.name, test.test);
        }

        this.printSummary();
        return this.testResults;
    }

    async runTest(testName, testFunction) {
        const startTime = Date.now();
        console.log(`\n🔬 Running: ${testName}`);

        try {
            const result = await testFunction();
            const duration = Date.now() - startTime;

            this.testResults.push({
                name: testName,
                status: 'PASSED',
                duration,
                details: result
            });

            console.log(`   ✅ PASSED (${duration}ms)`);
            if (result.message) {
                console.log(`   📝 ${result.message}`);
            }

        } catch (error) {
            const duration = Date.now() - startTime;

            this.testResults.push({
                name: testName,
                status: 'FAILED',
                duration,
                error: error.message,
                stack: error.stack
            });

            console.log(`   ❌ FAILED (${duration}ms): ${error.message}`);
        }
    }

    async testLongErrorMessages() {
        // Test with extremely long error messages (>100KB)
        const longMessage = 'X'.repeat(100000);
        const error = new Error(longMessage);

        const analysis = this.recovery.analyzeError(error);

        return {
            message: `Analyzed error with ${longMessage.length} character message`,
            messageLength: analysis.message.length,
            category: analysis.category
        };
    }

    async testMalformedErrors() {
        // Test with various malformed error objects
        const malformedErrors = [
            null,
            undefined,
            { message: 'Not an Error object' },
            'String error',
            42,
            [],
            { toString: () => { throw new Error('toString failed'); } }
        ];

        const results = [];

        for (const errorObj of malformedErrors) {
            try {
                const analysis = this.recovery.analyzeError(errorObj);
                results.push({ type: typeof errorObj, status: 'handled', category: analysis.category });
            } catch (e) {
                results.push({ type: typeof errorObj, status: 'error', message: e.message });
            }
        }

        return {
            message: `Tested ${malformedErrors.length} malformed error types`,
            results
        };
    }

    async testCircularReferences() {
        // Create error with circular references
        const obj1 = { name: 'obj1' };
        const obj2 = { name: 'obj2', ref: obj1 };
        obj1.ref = obj2;

        const error = new Error('Circular reference error');
        error.data = obj1;

        const analysis = this.recovery.analyzeError(error);

        return {
            message: 'Handled error with circular references',
            category: analysis.category,
            hasCircularRef: true
        };
    }

    async testHighFrequencyErrors() {
        // Generate high frequency errors (1000 errors in 1 second)
        const errorCount = 1000;
        const startTime = Date.now();
        const errors = [];

        for (let i = 0; i < errorCount; i++) {
            const error = new Error(`High frequency error ${i}`);
            const analysis = this.recovery.analyzeError(error);
            errors.push(analysis);
        }

        const duration = Date.now() - startTime;
        const errorsPerSecond = errorCount / (duration / 1000);

        return {
            message: `Processed ${errorCount} errors in ${duration}ms`,
            errorsPerSecond: Math.round(errorsPerSecond),
            avgProcessingTime: duration / errorCount
        };
    }

    async testMemoryPressure() {
        // Simulate memory pressure with large checkpoints
        const largeData = [];
        for (let i = 0; i < 1000; i++) {
            largeData.push({
                id: i,
                data: 'X'.repeat(1000),
                timestamp: new Date().toISOString(),
                metadata: { index: i, processed: false }
            });
        }

        const checkpointId = `memory-pressure-${Date.now()}`;
        await this.recovery.createCheckpoint(checkpointId, largeData);

        const restored = await this.recovery.restoreCheckpoint(checkpointId);

        // Cleanup
        await this.recovery.cleanupCheckpoint(checkpointId);

        return {
            message: `Created and restored checkpoint with ${largeData.length} items`,
            dataSize: JSON.stringify(largeData).length,
            restoredSize: JSON.stringify(restored.data).length
        };
    }

    async testConcurrentCheckpoints() {
        // Test concurrent checkpoint operations
        const promises = [];
        const checkpointCount = 10;

        for (let i = 0; i < checkpointCount; i++) {
            const checkpointId = `concurrent-${i}-${Date.now()}`;
            const data = { operation: i, timestamp: Date.now() };

            promises.push(
                this.recovery.createCheckpoint(checkpointId, data)
                    .then(() => this.recovery.restoreCheckpoint(checkpointId))
                    .then(() => this.recovery.cleanupCheckpoint(checkpointId))
                    .then(() => ({ id: checkpointId, success: true }))
                    .catch(error => ({ id: checkpointId, success: false, error: error.message }))
            );
        }

        const results = await Promise.all(promises);
        const successCount = results.filter(r => r.success).length;

        return {
            message: `${successCount}/${checkpointCount} concurrent checkpoint operations succeeded`,
            successRate: (successCount / checkpointCount) * 100,
            results
        };
    }

    async testNetworkInstability() {
        // Simulate network instability with intermittent failures
        let attempts = 0;

        const unstableOperation = async () => {
            attempts++;

            // Simulate various network errors randomly
            const errorTypes = ['ECONNRESET', 'ETIMEDOUT', 'ENOTFOUND', 'ECONNREFUSED'];
            const randomError = errorTypes[Math.floor(Math.random() * errorTypes.length)];

            if (attempts < 5) {
                const error = new Error(`Network error: ${randomError}`);
                error.code = randomError;
                throw error;
            }

            return `Success after ${attempts} attempts`;
        };

        const result = await this.recovery.executeWithRecovery(unstableOperation, {
            strategy: 'network'
        });

        return {
            message: `Recovered from network instability after ${attempts} attempts`,
            result,
            totalAttempts: attempts
        };
    }

    async testFileSystemEdgeCases() {
        // Test various file system edge cases
        const edgeCases = [
            { path: '', description: 'Empty path' },
            { path: '/root/nonexistent/very/deep/path/file.txt', description: 'Deep nonexistent path' },
            { path: '/dev/null/../../../etc/passwd', description: 'Path traversal attempt' },
            { path: 'a'.repeat(1000), description: 'Extremely long filename' },
            { path: '\\0\\0\\0', description: 'Null bytes in path' },
            { path: '../../../../../../etc/passwd', description: 'Directory traversal' }
        ];

        const results = [];

        for (const testCase of edgeCases) {
            try {
                const error = new Error(`ENOENT: no such file or directory, open '${testCase.path}'`);
                error.code = 'ENOENT';

                const analysis = this.recovery.analyzeError(error);
                const recoveryAction = this.recovery.recoveryActions.get('createMissingPaths');

                if (recoveryAction) {
                    const recoveryResult = await recoveryAction(error, analysis, null);
                    results.push({
                        path: testCase.path,
                        description: testCase.description,
                        handled: true,
                        recovery: recoveryResult.success
                    });
                } else {
                    results.push({
                        path: testCase.path,
                        description: testCase.description,
                        handled: false
                    });
                }
            } catch (e) {
                results.push({
                    path: testCase.path,
                    description: testCase.description,
                    handled: false,
                    error: e.message
                });
            }
        }

        return {
            message: `Tested ${edgeCases.length} file system edge cases`,
            results,
            handledCount: results.filter(r => r.handled).length
        };
    }

    async testRecursiveErrors() {
        // Test recursive error scenarios
        let recursionDepth = 0;
        const maxDepth = 100;

        const recursiveOperation = async () => {
            recursionDepth++;

            if (recursionDepth < maxDepth) {
                // Create nested error
                try {
                    await recursiveOperation();
                } catch (nestedError) {
                    const wrapperError = new Error(`Recursive error at depth ${recursionDepth}`);
                    wrapperError.cause = nestedError;
                    throw wrapperError;
                }
            } else {
                throw new Error(`Maximum recursion depth ${maxDepth} reached`);
            }
        };

        try {
            await this.recovery.executeWithRecovery(recursiveOperation, {
                strategy: 'validation'
            });
        } catch (error) {
            const analysis = this.recovery.analyzeError(error);

            return {
                message: `Handled recursive error at depth ${recursionDepth}`,
                maxDepth: recursionDepth,
                errorCategory: analysis.category,
                stackDepth: (error.stack.match(/at /g) || []).length
            };
        }
    }

    async testRaceConditions() {
        // Test race condition scenarios
        const sharedResource = { counter: 0, operations: [] };

        const racingOperation = async (operationId) => {
            // Simulate race condition
            const currentValue = sharedResource.counter;

            // Introduce random delay to increase chance of race condition
            await new Promise(resolve => setTimeout(resolve, Math.random() * 10));

            sharedResource.counter = currentValue + 1;
            sharedResource.operations.push(operationId);

            if (Math.random() < 0.3) { // 30% chance of error
                throw new Error(`Race condition error in operation ${operationId}`);
            }

            return operationId;
        };

        const promises = [];
        const operationCount = 20;

        for (let i = 0; i < operationCount; i++) {
            promises.push(
                this.recovery.executeWithRecovery(() => racingOperation(i), {
                    strategy: 'phase'
                }).catch(error => ({ error: error.message, operationId: i }))
            );
        }

        const results = await Promise.all(promises);
        const errors = results.filter(r => r.error);
        const successes = results.filter(r => !r.error);

        return {
            message: `Handled ${operationCount} racing operations`,
            successes: successes.length,
            errors: errors.length,
            finalCounter: sharedResource.counter,
            operationsLog: sharedResource.operations.length
        };
    }

    printSummary() {
        const total = this.testResults.length;
        const passed = this.testResults.filter(r => r.status === 'PASSED').length;
        const failed = this.testResults.filter(r => r.status === 'FAILED').length;
        const totalDuration = this.testResults.reduce((sum, r) => sum + r.duration, 0);
        const avgDuration = totalDuration / total;

        console.log('\n' + '='.repeat(60));
        console.log('📊 EDGE CASE TEST SUMMARY');
        console.log('='.repeat(60));
        console.log(`Total Tests: ${total}`);
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`📈 Success Rate: ${((passed / total) * 100).toFixed(1)}%`);
        console.log(`⏱️  Total Duration: ${totalDuration}ms`);
        console.log(`📊 Average Duration: ${avgDuration.toFixed(1)}ms`);

        if (failed > 0) {
            console.log('\n❌ Failed Tests:');
            this.testResults.filter(r => r.status === 'FAILED').forEach(r => {
                console.log(`  • ${r.name}: ${r.error}`);
            });
        }

        // Get final metrics
        const metrics = this.recovery.getMetrics();
        console.log('\n📈 Recovery System Metrics:');
        console.log(`  Total Errors Processed: ${metrics.totalErrors}`);
        console.log(`  Recovered Errors: ${metrics.recoveredErrors}`);
        console.log(`  Success Rate: ${metrics.successRate}`);
        console.log(`  Checkpoints Created: ${metrics.checkpointsSaved}`);
    }
}

// Run edge case tests if called directly
if (require.main === module) {
    (async () => {
        try {
            const testSuite = new EdgeCaseTestSuite();
            const results = await testSuite.runAllTests();

            const failed = results.filter(r => r.status === 'FAILED').length;
            process.exit(failed > 0 ? 1 : 0);

        } catch (error) {
            console.error('\n💥 Edge case test suite crashed:', error);
            process.exit(2);
        }
    })();
} else {
    module.exports = EdgeCaseTestSuite;
}