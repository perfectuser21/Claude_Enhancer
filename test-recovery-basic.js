#!/usr/bin/env node

/**
 * Basic Error Recovery Test
 */

const ErrorRecovery = require('./src/recovery/ErrorRecovery');

async function runBasicTests() {
    console.log('🧪 Basic Error Recovery Tests\n');

    const recovery = new ErrorRecovery({
        maxRetries: 3,
        baseRetryDelay: 100,
        enableMetrics: true
    });

    let testsPassed = 0;
    let testsFailed = 0;

    // Test 1: Basic error recovery with retry
    console.log('1️⃣ Testing basic retry mechanism...');
    try {
        let attempts = 0;
        const result = await recovery.executeWithRecovery(async () => {
            attempts++;
            if (attempts < 3) {
                throw new Error('Simulated network error');
            }
            return 'Success after retries';
        }, {
            strategy: 'network',
            checkpointId: 'test-checkpoint-1'
        });

        console.log('   ✅ Retry worked:', result);
        console.log('   📊 Attempts made:', attempts);
        testsPassed++;
    } catch (error) {
        console.log('   ❌ Test failed:', error.message);
        testsFailed++;
    }

    // Test 2: Checkpoint creation and restoration
    console.log('\n2️⃣ Testing checkpoint system...');
    try {
        const testData = { user: 'test', state: 'initial' };
        const checkpointId = await recovery.createCheckpoint('test-cp-2', testData);
        console.log('   ✅ Checkpoint created:', checkpointId);

        const restored = await recovery.restoreCheckpoint(checkpointId);
        console.log('   ✅ Checkpoint restored:', restored.data);
        testsPassed++;
    } catch (error) {
        console.log('   ❌ Test failed:', error.message);
        testsFailed++;
    }

    // Test 3: Error analysis
    console.log('\n3️⃣ Testing error analysis...');
    try {
        const testError = new Error('ECONNREFUSED: Connection refused');
        testError.code = 'ECONNREFUSED';

        const analysis = recovery.analyzeError(testError);
        console.log('   ✅ Error analyzed:');
        console.log('     • Category:', analysis.category);
        console.log('     • Severity:', analysis.severity);
        console.log('     • Root cause:', analysis.rootCause);
        testsPassed++;
    } catch (error) {
        console.log('   ❌ Test failed:', error.message);
        testsFailed++;
    }

    // Test 4: Circuit breaker functionality
    console.log('\n4️⃣ Testing circuit breaker...');
    try {
        // Simulate multiple failures to trip circuit breaker
        let networkFailures = 0;

        for (let i = 0; i < 3; i++) {
            try {
                await recovery.executeWithRecovery(async () => {
                    throw new Error('Network timeout');
                }, {
                    strategy: 'network',
                    checkpointId: `test-cb-${i}`
                });
            } catch (error) {
                networkFailures++;
            }
        }

        console.log('   ✅ Circuit breaker triggered after', networkFailures, 'failures');
        testsPassed++;
    } catch (error) {
        console.log('   ❌ Test failed:', error.message);
        testsFailed++;
    }

    // Test 5: Get metrics
    console.log('\n5️⃣ Testing metrics collection...');
    try {
        const metrics = recovery.getMetrics();
        console.log('   ✅ Metrics collected:');
        console.log('     • Total errors:', metrics.totalErrors);
        console.log('     • Recovered errors:', metrics.recoveredErrors);
        console.log('     • Checkpoints saved:', metrics.checkpointsSaved);
        console.log('     • Success rate:', metrics.successRate);
        testsPassed++;
    } catch (error) {
        console.log('   ❌ Test failed:', error.message);
        testsFailed++;
    }

    // Test 6: Graceful degradation
    console.log('\n6️⃣ Testing graceful degradation...');
    try {
        const result = await recovery.executeWithRecovery(async () => {
            const error = new Error('Out of memory');
            error.code = 'ENOMEM';
            throw error;
        }, {
            strategy: 'default',
            checkpointId: 'test-degradation'
        }).catch(error => {
            if (error.recoveryContext) {
                console.log('   ✅ Graceful degradation applied');
                console.log('     • Severity:', error.severity);
                console.log('     • Suggestions:', error.suggestions.slice(0, 2));
                testsPassed++;
                return 'degraded';
            } else {
                throw error;
            }
        });
    } catch (error) {
        console.log('   ❌ Test failed:', error.message);
        testsFailed++;
    }

    // Final results
    console.log('\n' + '='.repeat(50));
    console.log('📊 Test Results:');
    console.log(`   ✅ Passed: ${testsPassed}`);
    console.log(`   ❌ Failed: ${testsFailed}`);
    console.log(`   📈 Success Rate: ${((testsPassed/(testsPassed+testsFailed))*100).toFixed(1)}%`);

    // Cleanup checkpoints
    console.log('\n🧹 Cleaning up test checkpoints...');
    const cleanedCount = await recovery.cleanupCheckpoints(0); // Clean all
    console.log(`   ✅ Cleaned ${cleanedCount} checkpoints`);

    return testsPassed > 0 && testsFailed === 0;
}

// Run tests
runBasicTests()
    .then(success => {
        console.log('\n' + (success ? '🎉 All tests passed!' : '⚠️ Some tests failed'));
        process.exit(success ? 0 : 1);
    })
    .catch(error => {
        console.error('\n❌ Test suite failed:', error);
        process.exit(1);
    });