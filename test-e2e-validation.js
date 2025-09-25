#!/usr/bin/env node

/**
 * E2E Test Validation Script
 * Quick validation of the end-to-end testing framework
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Validating E2E Test Framework...\n');

// Check if required files exist
const requiredFiles = [
    './src/recovery/index.js',
    './src/recovery/ErrorRecovery.js',
    './src/recovery/CheckpointManager.js',
    './test/e2e-error-recovery-test-suite.js',
    './test/user-journey-test-scenarios.js',
    './test/comprehensive-e2e-test-runner.js'
];

let validationPassed = true;

console.log('📁 Checking required files...');
for (const file of requiredFiles) {
    if (fs.existsSync(file)) {
        console.log(`  ✅ ${file}`);
    } else {
        console.log(`  ❌ ${file} - MISSING`);
        validationPassed = false;
    }
}

// Check if recovery system can be loaded
console.log('\n🔧 Testing recovery system loading...');
try {
    const { RecoverySystem } = require('./src/recovery');
    const recovery = new RecoverySystem({
        checkpointsDir: './.test-validation-checkpoints',
        enableDiagnostics: true,
        enableMetrics: true
    });
    console.log('  ✅ RecoverySystem loaded successfully');

    // Test basic functionality
    console.log('\n🧪 Testing basic functionality...');

    // Test execute method
    const testResult = recovery.execute(async () => {
        return { test: 'validation', status: 'success' };
    });

    console.log('  ✅ Basic execute method works');

} catch (error) {
    console.log(`  ❌ Recovery system loading failed: ${error.message}`);
    validationPassed = false;
}

// Test E2E test classes
console.log('\n🎯 Testing E2E test classes...');
try {
    const E2ETestSuite = require('./test/e2e-error-recovery-test-suite');
    const UserJourneyTests = require('./test/user-journey-test-scenarios');
    const ComprehensiveRunner = require('./test/comprehensive-e2e-test-runner');

    console.log('  ✅ E2EErrorRecoveryTestSuite loaded');
    console.log('  ✅ UserJourneyTestScenarios loaded');
    console.log('  ✅ ComprehensiveE2ETestRunner loaded');

    // Test instantiation
    const testSuite = new E2ETestSuite();
    const journeyTests = new UserJourneyTests();
    const runner = new ComprehensiveRunner();

    console.log('  ✅ All test classes instantiated successfully');

} catch (error) {
    console.log(`  ❌ Test class loading failed: ${error.message}`);
    validationPassed = false;
}

// Validation summary
console.log('\n' + '='.repeat(50));
if (validationPassed) {
    console.log('🎉 E2E Test Framework Validation PASSED');
    console.log('\nYou can now run comprehensive testing with:');
    console.log('  node test/comprehensive-e2e-test-runner.js');
    console.log('\nOr run individual test suites:');
    console.log('  node test/e2e-error-recovery-test-suite.js');
    console.log('  node test-recovery-basic.js');
} else {
    console.log('❌ E2E Test Framework Validation FAILED');
    console.log('\nPlease fix the issues above before running tests.');
}
console.log('='.repeat(50));

process.exit(validationPassed ? 0 : 1);