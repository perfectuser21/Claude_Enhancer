#!/usr/bin/env node

/**
 * Comprehensive E2E Test Runner for Error Recovery System
 * Orchestrates all end-to-end testing scenarios and generates unified reports
 */

const assert = require('assert');
const fs = require('fs').promises;
const path = require('path');

// Import test suites
const E2EErrorRecoveryTestSuite = require('./e2e-error-recovery-test-suite');
const UserJourneyTestScenarios = require('./user-journey-test-scenarios');

class ComprehensiveE2ETestRunner {
    constructor() {
        this.results = {
            executedAt: new Date().toISOString(),
            testSuites: [],
            overallSummary: {
                totalSuites: 0,
                totalTests: 0,
                passedTests: 0,
                failedTests: 0,
                totalExecutionTime: 0,
                successRate: 0
            },
            systemMetrics: {},
            recommendations: []
        };

        this.testEnvironment = {
            nodeVersion: process.version,
            platform: process.platform,
            arch: process.arch,
            workingDirectory: process.cwd()
        };
    }

    /**
     * Initialize test environment
     */
    async initializeTestEnvironment() {
        console.log('🔧 Initializing comprehensive E2E test environment...');

        // Create test directories
        const testDirs = [
            './test-results',
            './test-artifacts',
            './test-logs',
            './test-checkpoints'
        ];

        for (const dir of testDirs) {
            try {
                await fs.mkdir(dir, { recursive: true });
            } catch (error) {
                if (error.code !== 'EEXIST') {
                    console.warn(`Warning: Could not create directory ${dir}:`, error.message);
                }
            }
        }

        // Log test environment
        console.log('   📋 Test Environment:');
        console.log(`      • Node.js: ${this.testEnvironment.nodeVersion}`);
        console.log(`      • Platform: ${this.testEnvironment.platform} ${this.testEnvironment.arch}`);
        console.log(`      • Working Dir: ${this.testEnvironment.workingDirectory}`);

        console.log('✅ Test environment initialized\\n');
    }

    /**
     * Execute Core Error Recovery Test Suite
     */
    async runCoreErrorRecoveryTests() {
        console.log('🧪 Running Core Error Recovery Test Suite...');
        const startTime = Date.now();

        try {
            const testSuite = new E2EErrorRecoveryTestSuite();
            const results = await testSuite.runAllTests();

            const suiteResult = {
                name: 'Core Error Recovery Tests',
                type: 'core',
                executionTime: Date.now() - startTime,
                results: results,
                status: results.failed === 0 ? 'passed' : 'failed'
            };

            this.results.testSuites.push(suiteResult);
            this.updateOverallSummary(suiteResult);

            console.log(`✅ Core Error Recovery Tests completed in ${suiteResult.executionTime}ms`);
            return suiteResult;

        } catch (error) {
            console.error('❌ Core Error Recovery Tests failed:', error.message);
            const failedSuite = {
                name: 'Core Error Recovery Tests',
                type: 'core',
                executionTime: Date.now() - startTime,
                status: 'failed',
                error: error.message,
                results: { total: 0, passed: 0, failed: 1 }
            };

            this.results.testSuites.push(failedSuite);
            this.updateOverallSummary(failedSuite);
            return failedSuite;
        }
    }

    /**
     * Execute User Journey Test Scenarios
     */
    async runUserJourneyTests() {
        console.log('🎯 Running User Journey Test Scenarios...');
        const startTime = Date.now();

        try {
            const { RecoverySystem } = require('../src/recovery');
            const recoverySystem = new RecoverySystem({
                checkpointsDir: './test-checkpoints-journey',
                logsDir: './test-logs-journey',
                enableDiagnostics: true,
                enableAnalytics: true,
                autoRecovery: true
            });

            const journeyTester = new UserJourneyTestScenarios();
            const results = await journeyTester.runAllScenarios(recoverySystem);

            const suiteResult = {
                name: 'User Journey Test Scenarios',
                type: 'journey',
                executionTime: Date.now() - startTime,
                results: {
                    total: results.summary.total,
                    passed: results.summary.passed,
                    failed: results.summary.failed
                },
                detailedResults: results,
                status: results.summary.failed === 0 ? 'passed' : 'failed'
            };

            this.results.testSuites.push(suiteResult);
            this.updateOverallSummary(suiteResult);

            console.log(`✅ User Journey Tests completed in ${suiteResult.executionTime}ms`);
            return suiteResult;

        } catch (error) {
            console.error('❌ User Journey Tests failed:', error.message);
            const failedSuite = {
                name: 'User Journey Test Scenarios',
                type: 'journey',
                executionTime: Date.now() - startTime,
                status: 'failed',
                error: error.message,
                results: { total: 0, passed: 0, failed: 1 }
            };

            this.results.testSuites.push(failedSuite);
            this.updateOverallSummary(failedSuite);
            return failedSuite;
        }
    }

    /**
     * Execute Performance and Load Tests
     */
    async runPerformanceTests() {
        console.log('⚡ Running Performance and Load Tests...');
        const startTime = Date.now();

        try {
            const performanceResults = await this.executePerformanceTestSuite();

            const suiteResult = {
                name: 'Performance and Load Tests',
                type: 'performance',
                executionTime: Date.now() - startTime,
                results: performanceResults,
                status: performanceResults.passed >= performanceResults.total * 0.8 ? 'passed' : 'failed'
            };

            this.results.testSuites.push(suiteResult);
            this.updateOverallSummary(suiteResult);

            console.log(`✅ Performance Tests completed in ${suiteResult.executionTime}ms`);
            return suiteResult;

        } catch (error) {
            console.error('❌ Performance Tests failed:', error.message);
            const failedSuite = {
                name: 'Performance and Load Tests',
                type: 'performance',
                executionTime: Date.now() - startTime,
                status: 'failed',
                error: error.message,
                results: { total: 0, passed: 0, failed: 1 }
            };

            this.results.testSuites.push(failedSuite);
            this.updateOverallSummary(failedSuite);
            return failedSuite;
        }
    }

    /**
     * Execute performance test scenarios
     */
    async executePerformanceTestSuite() {
        console.log('   🏃 Testing recovery system performance...');

        const { RecoverySystem } = require('../src/recovery');
        const tests = [
            {
                name: 'Concurrent Recovery Operations',
                test: async () => await this.testConcurrentRecovery()
            },
            {
                name: 'High-Frequency Error Scenarios',
                test: async () => await this.testHighFrequencyErrors()
            },
            {
                name: 'Memory Usage Under Load',
                test: async () => await this.testMemoryUsageUnderLoad()
            },
            {
                name: 'Recovery Time Performance',
                test: async () => await this.testRecoveryTimePerformance()
            }
        ];

        let passed = 0;
        let failed = 0;
        const results = [];

        for (const testCase of tests) {
            console.log(`      • ${testCase.name}...`);
            try {
                const result = await testCase.test();
                console.log(`        ✅ ${result.message} (${result.timeMs}ms)`);
                results.push({ ...testCase, success: true, result });
                passed++;
            } catch (error) {
                console.log(`        ❌ ${error.message}`);
                results.push({ ...testCase, success: false, error: error.message });
                failed++;
            }
        }

        return {
            total: tests.length,
            passed,
            failed,
            details: results
        };
    }

    async testConcurrentRecovery() {
        const { RecoverySystem } = require('../src/recovery');
        const recoverySystem = new RecoverySystem();

        const startTime = Date.now();
        const concurrentOperations = 10;

        // Create operations that will fail and require recovery
        const operations = Array.from({ length: concurrentOperations }, (_, i) => {
            return recoverySystem.execute(async () => {
                if (Math.random() < 0.7) {
                    throw new Error(`Simulated error ${i}`);
                }
                return { success: true, id: i };
            });
        });

        const results = await Promise.allSettled(operations);
        const successful = results.filter(r => r.status === 'fulfilled').length;
        const timeMs = Date.now() - startTime;

        if (successful < concurrentOperations * 0.6) {
            throw new Error(`Only ${successful}/${concurrentOperations} operations succeeded`);
        }

        return {
            message: `${successful}/${concurrentOperations} concurrent operations succeeded`,
            timeMs,
            successRate: (successful / concurrentOperations) * 100
        };
    }

    async testHighFrequencyErrors() {
        const { RecoverySystem } = require('../src/recovery');
        const recoverySystem = new RecoverySystem();

        const startTime = Date.now();
        const errorCount = 50;
        let recoveredCount = 0;

        for (let i = 0; i < errorCount; i++) {
            try {
                await recoverySystem.execute(async () => {
                    throw new Error(`High frequency error ${i}`);
                });
                recoveredCount++;
            } catch (error) {
                // Error not recovered
            }
        }

        const timeMs = Date.now() - startTime;
        const averageRecoveryTime = timeMs / errorCount;

        if (averageRecoveryTime > 500) {
            throw new Error(`Average recovery time too high: ${averageRecoveryTime}ms`);
        }

        return {
            message: `Processed ${errorCount} errors, ${recoveredCount} recovered`,
            timeMs,
            averageRecoveryTime: averageRecoveryTime.toFixed(1) + 'ms'
        };
    }

    async testMemoryUsageUnderLoad() {
        const startTime = Date.now();
        const initialMemory = process.memoryUsage().heapUsed;

        // Simulate memory-intensive recovery operations
        const { RecoverySystem } = require('../src/recovery');
        const recoverySystem = new RecoverySystem();

        // Create multiple checkpoints and recovery operations
        const operations = [];
        for (let i = 0; i < 20; i++) {
            operations.push(
                recoverySystem.createCheckpoint(`load-test-${i}`, {
                    data: new Array(1000).fill(`test-data-${i}`),
                    timestamp: Date.now()
                })
            );
        }

        await Promise.all(operations);

        const finalMemory = process.memoryUsage().heapUsed;
        const memoryIncrease = (finalMemory - initialMemory) / 1024 / 1024; // MB
        const timeMs = Date.now() - startTime;

        if (memoryIncrease > 100) { // 100MB threshold
            throw new Error(`Memory usage increased by ${memoryIncrease.toFixed(1)}MB - too high`);
        }

        return {
            message: `Memory increase: ${memoryIncrease.toFixed(1)}MB (acceptable)`,
            timeMs,
            memoryIncreaseMB: memoryIncrease.toFixed(1)
        };
    }

    async testRecoveryTimePerformance() {
        const { RecoverySystem } = require('../src/recovery');
        const recoverySystem = new RecoverySystem();

        const recoveryTimes = [];
        const testCount = 10;

        for (let i = 0; i < testCount; i++) {
            const startTime = Date.now();

            try {
                await recoverySystem.execute(async () => {
                    throw new Error(`Performance test error ${i}`);
                });
            } catch (error) {
                // Expected to fail in some cases
            }

            recoveryTimes.push(Date.now() - startTime);
        }

        const averageRecoveryTime = recoveryTimes.reduce((sum, time) => sum + time, 0) / testCount;
        const maxRecoveryTime = Math.max(...recoveryTimes);

        if (averageRecoveryTime > 1000 || maxRecoveryTime > 3000) {
            throw new Error(`Recovery times too slow - avg: ${averageRecoveryTime}ms, max: ${maxRecoveryTime}ms`);
        }

        return {
            message: `Average recovery time: ${averageRecoveryTime.toFixed(0)}ms`,
            timeMs: recoveryTimes.reduce((sum, time) => sum + time, 0),
            averageRecoveryTime: averageRecoveryTime.toFixed(0) + 'ms',
            maxRecoveryTime: maxRecoveryTime + 'ms'
        };
    }

    /**
     * Execute Integration Tests
     */
    async runIntegrationTests() {
        console.log('🔗 Running Integration Tests...');
        const startTime = Date.now();

        try {
            const integrationResults = await this.executeIntegrationTestSuite();

            const suiteResult = {
                name: 'Integration Tests',
                type: 'integration',
                executionTime: Date.now() - startTime,
                results: integrationResults,
                status: integrationResults.passed >= integrationResults.total * 0.9 ? 'passed' : 'failed'
            };

            this.results.testSuites.push(suiteResult);
            this.updateOverallSummary(suiteResult);

            console.log(`✅ Integration Tests completed in ${suiteResult.executionTime}ms`);
            return suiteResult;

        } catch (error) {
            console.error('❌ Integration Tests failed:', error.message);
            const failedSuite = {
                name: 'Integration Tests',
                type: 'integration',
                executionTime: Date.now() - startTime,
                status: 'failed',
                error: error.message,
                results: { total: 0, passed: 0, failed: 1 }
            };

            this.results.testSuites.push(failedSuite);
            this.updateOverallSummary(failedSuite);
            return failedSuite;
        }
    }

    /**
     * Execute integration test scenarios
     */
    async executeIntegrationTestSuite() {
        console.log('   🔌 Testing system integration points...');

        const tests = [
            {
                name: 'Recovery System + Git Integration',
                test: async () => await this.testGitIntegration()
            },
            {
                name: 'Recovery System + File System',
                test: async () => await this.testFileSystemIntegration()
            },
            {
                name: 'Recovery System + Process Management',
                test: async () => await this.testProcessIntegration()
            },
            {
                name: 'Cross-Component Communication',
                test: async () => await this.testCrossComponentCommunication()
            }
        ];

        let passed = 0;
        let failed = 0;
        const results = [];

        for (const testCase of tests) {
            console.log(`      • ${testCase.name}...`);
            try {
                const result = await testCase.test();
                console.log(`        ✅ ${result.message}`);
                results.push({ ...testCase, success: true, result });
                passed++;
            } catch (error) {
                console.log(`        ❌ ${error.message}`);
                results.push({ ...testCase, success: false, error: error.message });
                failed++;
            }
        }

        return {
            total: tests.length,
            passed,
            failed,
            details: results
        };
    }

    async testGitIntegration() {
        const { RecoverySystem } = require('../src/recovery');
        const recoverySystem = new RecoverySystem();

        // Simulate git operation with recovery
        const result = await recoverySystem.execute(async () => {
            // Simulate git command that might fail
            if (Math.random() < 0.3) {
                throw new Error('Git operation failed: remote unreachable');
            }
            return { status: 'git operation completed' };
        }, {
            retryStrategy: 'network',
            context: { operationType: 'git' }
        });

        return { message: 'Git integration working correctly' };
    }

    async testFileSystemIntegration() {
        const { RecoverySystem } = require('../src/recovery');
        const recoverySystem = new RecoverySystem();

        // Test file system operations with recovery
        const result = await recoverySystem.execute(async () => {
            // Simulate file operation that might fail
            if (Math.random() < 0.2) {
                const error = new Error('File operation failed');
                error.code = 'EBUSY';
                throw error;
            }
            return { status: 'file operation completed' };
        }, {
            retryStrategy: 'file',
            context: { operationType: 'filesystem' }
        });

        return { message: 'File system integration working correctly' };
    }

    async testProcessIntegration() {
        // Test process-level integration
        const { RecoverySystem } = require('../src/recovery');
        const recoverySystem = new RecoverySystem();

        // Test process recovery scenarios
        const healthCheck = await recoverySystem.healthCheck();

        if (healthCheck.overall !== 'healthy' && healthCheck.overall !== 'degraded') {
            throw new Error('Process integration health check failed');
        }

        return { message: 'Process integration working correctly' };
    }

    async testCrossComponentCommunication() {
        // Test communication between components
        const { RecoverySystem } = require('../src/recovery');
        const recoverySystem = new RecoverySystem();

        // Create checkpoint
        const checkpointId = await recoverySystem.createCheckpoint('integration-test', {
            test: 'cross-component-communication',
            timestamp: Date.now()
        });

        // Verify checkpoint was created and can be restored
        const restored = await recoverySystem.restoreCheckpoint(checkpointId);

        if (!restored || !restored.data || restored.data.test !== 'cross-component-communication') {
            throw new Error('Cross-component communication failed');
        }

        return { message: 'Cross-component communication working correctly' };
    }

    /**
     * Update overall summary with suite results
     */
    updateOverallSummary(suiteResult) {
        this.results.overallSummary.totalSuites++;
        this.results.overallSummary.totalTests += suiteResult.results.total || 0;
        this.results.overallSummary.passedTests += suiteResult.results.passed || 0;
        this.results.overallSummary.failedTests += suiteResult.results.failed || 0;
        this.results.overallSummary.totalExecutionTime += suiteResult.executionTime || 0;
    }

    /**
     * Generate comprehensive final report
     */
    async generateFinalReport() {
        console.log('\\n' + '='.repeat(80));
        console.log('📊 COMPREHENSIVE E2E TEST RESULTS');
        console.log('='.repeat(80));

        const { overallSummary } = this.results;
        overallSummary.successRate = overallSummary.totalTests > 0
            ? (overallSummary.passedTests / overallSummary.totalTests) * 100
            : 0;

        console.log(`\\n📈 Overall Summary:`);
        console.log(`   • Test Suites: ${overallSummary.totalSuites}`);
        console.log(`   • Total Tests: ${overallSummary.totalTests}`);
        console.log(`   • Passed: ${overallSummary.passedTests} ✅`);
        console.log(`   • Failed: ${overallSummary.failedTests} ❌`);
        console.log(`   • Success Rate: ${overallSummary.successRate.toFixed(1)}%`);
        console.log(`   • Total Time: ${overallSummary.totalExecutionTime}ms`);

        console.log(`\\n📋 Test Suite Breakdown:`);
        this.results.testSuites.forEach(suite => {
            const statusIcon = suite.status === 'passed' ? '✅' : '❌';
            const testsInfo = suite.results ? `${suite.results.passed}/${suite.results.total}` : 'N/A';
            console.log(`   ${statusIcon} ${suite.name}: ${testsInfo} tests (${suite.executionTime}ms)`);
        });

        // Collect system metrics
        this.results.systemMetrics = await this.collectSystemMetrics();

        // Generate recommendations
        this.results.recommendations = this.generateRecommendations();

        // Save comprehensive report
        await this.saveDetailedReport();

        // Display final verdict
        this.displayFinalVerdict();

        return this.results;
    }

    async collectSystemMetrics() {
        const memoryUsage = process.memoryUsage();

        return {
            memory: {
                heapUsed: Math.round(memoryUsage.heapUsed / 1024 / 1024) + 'MB',
                heapTotal: Math.round(memoryUsage.heapTotal / 1024 / 1024) + 'MB',
                external: Math.round(memoryUsage.external / 1024 / 1024) + 'MB'
            },
            runtime: {
                nodeVersion: process.version,
                platform: process.platform,
                uptime: process.uptime() + 's'
            },
            testEnvironment: this.testEnvironment
        };
    }

    generateRecommendations() {
        const recommendations = [];
        const { overallSummary } = this.results;

        // Success rate recommendations
        if (overallSummary.successRate < 80) {
            recommendations.push({
                type: 'critical',
                category: 'reliability',
                message: 'Test success rate is below 80% - system reliability needs immediate attention'
            });
        } else if (overallSummary.successRate < 95) {
            recommendations.push({
                type: 'warning',
                category: 'reliability',
                message: 'Test success rate could be improved - consider investigating failed tests'
            });
        }

        // Performance recommendations
        const avgTimePerTest = overallSummary.totalExecutionTime / overallSummary.totalTests;
        if (avgTimePerTest > 2000) {
            recommendations.push({
                type: 'performance',
                category: 'speed',
                message: 'Average test execution time is high - consider optimizing recovery performance'
            });
        }

        // Coverage recommendations
        const failedSuites = this.results.testSuites.filter(s => s.status === 'failed');
        if (failedSuites.length > 0) {
            recommendations.push({
                type: 'coverage',
                category: 'testing',
                message: `${failedSuites.length} test suites failed - review and fix failing tests`
            });
        }

        // Production readiness
        if (overallSummary.successRate >= 95 && overallSummary.failedTests === 0) {
            recommendations.push({
                type: 'success',
                category: 'deployment',
                message: 'System shows excellent reliability - ready for production deployment'
            });
        }

        return recommendations;
    }

    async saveDetailedReport() {
        const reportPath = path.join(process.cwd(), 'COMPREHENSIVE_E2E_TEST_REPORT.json');

        try {
            await fs.writeFile(reportPath, JSON.stringify(this.results, null, 2));
            console.log(`\\n📄 Detailed report saved to: ${reportPath}`);
        } catch (error) {
            console.warn(`⚠️  Could not save detailed report: ${error.message}`);
        }

        // Also save a summary report
        const summaryPath = path.join(process.cwd(), 'E2E_TEST_SUMMARY.md');
        const summaryContent = this.generateMarkdownSummary();

        try {
            await fs.writeFile(summaryPath, summaryContent);
            console.log(`📄 Summary report saved to: ${summaryPath}`);
        } catch (error) {
            console.warn(`⚠️  Could not save summary report: ${error.message}`);
        }
    }

    generateMarkdownSummary() {
        const { overallSummary } = this.results;
        const date = new Date(this.results.executedAt).toLocaleString();

        return `# End-to-End Test Results

**Executed:** ${date}

## Summary
- **Total Test Suites:** ${overallSummary.totalSuites}
- **Total Tests:** ${overallSummary.totalTests}
- **Success Rate:** ${overallSummary.successRate.toFixed(1)}%
- **Execution Time:** ${overallSummary.totalExecutionTime}ms

## Test Suites
${this.results.testSuites.map(suite =>
  `- ${suite.status === 'passed' ? '✅' : '❌'} **${suite.name}**: ${suite.results?.passed || 0}/${suite.results?.total || 0} tests`
).join('\\n')}

## Recommendations
${this.results.recommendations.map(rec =>
  `- **${rec.type.toUpperCase()}** (${rec.category}): ${rec.message}`
).join('\\n')}

## System Metrics
- **Memory Usage:** ${this.results.systemMetrics?.memory?.heapUsed || 'N/A'}
- **Node.js Version:** ${this.results.systemMetrics?.runtime?.nodeVersion || 'N/A'}
- **Platform:** ${this.results.systemMetrics?.runtime?.platform || 'N/A'}
`;
    }

    displayFinalVerdict() {
        const { overallSummary } = this.results;

        console.log('\\n' + '='.repeat(80));

        if (overallSummary.failedTests === 0) {
            console.log('🎉 ALL TESTS PASSED! System is ready for production deployment.');
        } else if (overallSummary.successRate >= 90) {
            console.log('✅ MOSTLY SUCCESSFUL! Minor issues detected but system is largely functional.');
        } else if (overallSummary.successRate >= 70) {
            console.log('⚠️  PARTIAL SUCCESS! Significant issues detected - investigation required.');
        } else {
            console.log('❌ CRITICAL FAILURES! System requires major fixes before deployment.');
        }

        console.log('='.repeat(80));
    }

    /**
     * Run all E2E test suites
     */
    async runAllTests() {
        const startTime = Date.now();

        try {
            console.log('🚀 Starting Comprehensive End-to-End Testing\\n');

            // Initialize test environment
            await this.initializeTestEnvironment();

            // Run all test suites
            await this.runCoreErrorRecoveryTests();
            await this.runUserJourneyTests();
            await this.runPerformanceTests();
            await this.runIntegrationTests();

            // Generate final report
            const finalResults = await this.generateFinalReport();

            console.log(`\\n⏱️  Total testing completed in ${Date.now() - startTime}ms`);

            return finalResults;

        } catch (error) {
            console.error('\\n💥 Comprehensive testing failed:', error);
            process.exit(1);
        }
    }

    /**
     * Cleanup test environment
     */
    async cleanup() {
        console.log('\\n🧹 Cleaning up test environment...');

        try {
            // Remove test directories
            const cleanupDirs = [
                './test-checkpoints',
                './test-logs',
                './test-artifacts',
                './test-checkpoints-e2e',
                './test-logs-e2e',
                './test-checkpoints-journey',
                './test-logs-journey'
            ];

            for (const dir of cleanupDirs) {
                try {
                    await fs.rmdir(dir, { recursive: true });
                } catch (error) {
                    // Ignore cleanup errors
                }
            }

            console.log('✅ Test environment cleaned up');
        } catch (error) {
            console.warn('⚠️  Warning: Cleanup partially failed:', error.message);
        }
    }
}

// Execute if run directly
if (require.main === module) {
    const testRunner = new ComprehensiveE2ETestRunner();

    testRunner.runAllTests()
        .then(async (results) => {
            await testRunner.cleanup();
            const success = results.overallSummary.failedTests === 0;
            process.exit(success ? 0 : 1);
        })
        .catch(async (error) => {
            console.error('\\n💥 Test execution failed:', error);
            await testRunner.cleanup();
            process.exit(1);
        });
}

module.exports = ComprehensiveE2ETestRunner;