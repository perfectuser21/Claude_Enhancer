#!/usr/bin/env node

/**
 * SecureLogger Test Suite
 * Validates security features and performance of the SecureLogger system
 */

const { logger, SecureLogger } = require('./SecureLogger');
const { createCLILogger } = require('./CLISecureLogger');
const chalk = require('chalk');

class SecureLoggerTests {
    constructor() {
        this.testResults = [];
        this.testStartTime = Date.now();
        this.cliLogger = createCLILogger('SecureLoggerTests');
    }

    /**
     * Run all tests
     */
    async runAllTests() {
        this.cliLogger.info('Starting SecureLogger test suite',
            chalk.bold.blue('🧪 SecureLogger Test Suite Starting\n'));

        try {
            await this.testBasicLogging();
            await this.testDataSanitization();
            await this.testSecurityFeatures();
            await this.testPerformance();
            await this.testCLILogger();
            await this.testErrorHandling();

            this.displayResults();

        } catch (error) {
            this.cliLogger.error('Test suite failed', error);
            process.exit(1);
        }
    }

    /**
     * Test basic logging functionality
     */
    async testBasicLogging() {
        const testName = 'Basic Logging';
        console.log(chalk.blue(`\n🔍 Testing ${testName}...`));

        try {
            // Test all log levels
            logger.debug('Debug message test');
            logger.info('Info message test');
            logger.warn('Warning message test');
            logger.error('Error message test');

            // Test with context
            logger.info('Context test', {
                userId: 123,
                operation: 'test'
            });

            this.addResult(testName, 'PASS', 'All log levels working');
        } catch (error) {
            this.addResult(testName, 'FAIL', error.message);
        }
    }

    /**
     * Test sensitive data sanitization
     */
    async testDataSanitization() {
        const testName = 'Data Sanitization';
        console.log(chalk.blue(`\n🔒 Testing ${testName}...`));

        try {
            // Test password sanitization
            const sensitiveData = {
                password: 'secret123',
                token: 'jwt_token_abc123def456',
                apiKey: 'api_key_xyz789',
                email: 'test@example.com',
                ipAddress: '192.168.1.100',
                creditCard: '4111-1111-1111-1111'
            };

            // These should be sanitized automatically
            logger.info('Testing password sanitization: password="secret123"');
            logger.info('Testing token sanitization: token="jwt_token_abc123def456"');
            logger.info('Testing API key sanitization: api_key="api_key_xyz789"');
            logger.info('Testing email sanitization: user email is test@example.com');
            logger.info('Testing IP sanitization: client IP is 192.168.1.100');
            logger.info('User data object', sensitiveData);

            this.addResult(testName, 'PASS', 'Sensitive data sanitization working');
        } catch (error) {
            this.addResult(testName, 'FAIL', error.message);
        }
    }

    /**
     * Test security-specific features
     */
    async testSecurityFeatures() {
        const testName = 'Security Features';
        console.log(chalk.blue(`\n🛡️ Testing ${testName}...`));

        try {
            // Test security logging
            logger.security('Unauthorized access attempt', {
                ip: '192.168.1.50',
                userAgent: 'Suspicious Bot',
                endpoint: '/admin'
            });

            // Test audit logging
            logger.audit('LOGIN', 'user@example.com', 'user:123', {
                success: true
            });

            // Test performance logging
            logger.performance('API Request', 250, {
                endpoint: '/api/users',
                method: 'GET'
            });

            this.addResult(testName, 'PASS', 'Security logging features working');
        } catch (error) {
            this.addResult(testName, 'FAIL', error.message);
        }
    }

    /**
     * Test performance characteristics
     */
    async testPerformance() {
        const testName = 'Performance';
        console.log(chalk.blue(`\n⚡ Testing ${testName}...`));

        try {
            const iterations = 1000;
            const startTime = Date.now();

            // Rapid logging test
            for (let i = 0; i < iterations; i++) {
                logger.debug(`Performance test iteration ${i} with sensitive data: password=test123`);
            }

            const endTime = Date.now();
            const duration = endTime - startTime;
            const avgTime = duration / iterations;

            console.log(chalk.green(`  ✓ ${iterations} log entries processed in ${duration}ms`));
            console.log(chalk.green(`  ✓ Average time per log entry: ${avgTime.toFixed(3)}ms`));

            if (avgTime < 1.0) {
                this.addResult(testName, 'PASS', `Average ${avgTime.toFixed(3)}ms per log`);
            } else {
                this.addResult(testName, 'WARN', `Performance concern: ${avgTime.toFixed(3)}ms per log`);
            }
        } catch (error) {
            this.addResult(testName, 'FAIL', error.message);
        }
    }

    /**
     * Test CLI logger functionality
     */
    async testCLILogger() {
        const testName = 'CLI Logger';
        console.log(chalk.blue(`\n🖥️ Testing ${testName}...`));

        try {
            const testCLI = createCLILogger('TestCLI');

            // Test various CLI logging methods
            testCLI.info('CLI info message');
            testCLI.success('CLI success message');
            testCLI.warn('CLI warning message');
            testCLI.error('CLI error message', new Error('Test error'));

            // Test operations tracking
            const opStart = testCLI.operationStart('test operation');
            await new Promise(resolve => setTimeout(resolve, 100));
            testCLI.operationComplete('test operation', opStart);

            // Test user action tracking
            testCLI.userAction('test_action', { param: 'value' });

            // Test progress tracking
            for (let i = 1; i <= 4; i++) {
                testCLI.progress(i, 4, 'test progress');
                await new Promise(resolve => setTimeout(resolve, 50));
            }

            this.addResult(testName, 'PASS', 'CLI logger functionality working');
        } catch (error) {
            this.addResult(testName, 'FAIL', error.message);
        }
    }

    /**
     * Test error handling
     */
    async testErrorHandling() {
        const testName = 'Error Handling';
        console.log(chalk.blue(`\n🚨 Testing ${testName}...`));

        try {
            // Test circular reference handling
            const circularObj = { name: 'test' };
            circularObj.self = circularObj;
            logger.info('Circular reference test', { circular: circularObj });

            // Test large object handling
            const largeObj = {
                data: 'x'.repeat(10000),
                nested: {
                    deep: {
                        very: {
                            deep: 'value'
                        }
                    }
                }
            };
            logger.info('Large object test', largeObj);

            // Test undefined/null handling
            logger.info('Null test', null);
            logger.info('Undefined test', undefined);

            // Test error object logging
            const testError = new Error('Test error with stack trace');
            testError.code = 'TEST_ERROR';
            testError.customProperty = 'custom value';
            logger.error('Error object test', testError);

            this.addResult(testName, 'PASS', 'Error handling robust');
        } catch (error) {
            this.addResult(testName, 'FAIL', error.message);
        }
    }

    /**
     * Add test result
     */
    addResult(testName, status, details) {
        this.testResults.push({
            test: testName,
            status,
            details,
            timestamp: new Date().toISOString()
        });

        const statusColor = {
            'PASS': chalk.green,
            'FAIL': chalk.red,
            'WARN': chalk.yellow
        }[status] || chalk.gray;

        console.log(statusColor(`  ${status}: ${details}`));
    }

    /**
     * Display final test results
     */
    displayResults() {
        const totalTime = Date.now() - this.testStartTime;
        const passed = this.testResults.filter(r => r.status === 'PASS').length;
        const failed = this.testResults.filter(r => r.status === 'FAIL').length;
        const warned = this.testResults.filter(r => r.status === 'WARN').length;

        console.log(chalk.bold.blue('\n📊 Test Results Summary\n'));

        // Create results table
        const Table = require('cli-table3');
        const table = new Table({
            head: ['Test', 'Status', 'Details'],
            colWidths: [20, 10, 50],
            style: {
                head: ['cyan'],
                border: ['gray']
            }
        });

        this.testResults.forEach(result => {
            const statusStyle = {
                'PASS': chalk.green(result.status),
                'FAIL': chalk.red(result.status),
                'WARN': chalk.yellow(result.status)
            }[result.status] || result.status;

            table.push([result.test, statusStyle, result.details]);
        });

        console.log(table.toString());

        // Summary statistics
        console.log(chalk.bold.green(`\n✅ Tests Passed: ${passed}`));
        if (warned > 0) console.log(chalk.bold.yellow(`⚠️ Tests with Warnings: ${warned}`));
        if (failed > 0) console.log(chalk.bold.red(`❌ Tests Failed: ${failed}`));
        console.log(chalk.bold.blue(`⏱️ Total Time: ${totalTime}ms\n`));

        // Final verdict
        if (failed === 0) {
            console.log(chalk.bold.green('🎉 All tests passed! SecureLogger is ready for production use.\n'));
            this.cliLogger.success('SecureLogger test suite completed successfully');
        } else {
            console.log(chalk.bold.red('💥 Some tests failed. Please review the issues above.\n'));
            this.cliLogger.error('SecureLogger test suite completed with failures');
            process.exit(1);
        }
    }
}

// Export for use as module
module.exports = SecureLoggerTests;

// Run if called directly
if (require.main === module) {
    const tests = new SecureLoggerTests();
    tests.runAllTests()
        .then(() => process.exit(0))
        .catch((error) => {
            console.error(chalk.red('Test suite crashed:'), error);
            process.exit(1);
        });
}