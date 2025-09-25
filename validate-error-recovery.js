#!/usr/bin/env node

/**
 * Claude Enhancer 5.0 - Error Recovery System Validation
 * Quick validation script to ensure all components are working correctly
 */

const path = require('path');
const fs = require('fs').promises;
const chalk = require('chalk');

class ErrorRecoveryValidator {
    constructor() {
        this.results = {
            passed: 0,
            failed: 0,
            warnings: 0,
            details: []
        };
    }

    async validate() {
        console.log(chalk.bold.cyan('🔍 Validating Error Recovery System...\n'));

        // Test file structure
        await this.validateFileStructure();

        // Test module imports
        await this.validateModuleImports();

        // Test basic functionality
        await this.validateBasicFunctionality();

        // Test integration
        await this.validateIntegration();

        this.displayResults();
        return this.results.failed === 0;
    }

    async validateFileStructure() {
        console.log(chalk.blue('📁 Validating file structure...'));

        const expectedFiles = [
            'src/recovery/ErrorRecovery.js',
            'src/recovery/ErrorAnalytics.js',
            'src/recovery/ErrorDiagnostics.js',
            'src/recovery/RetryManager.js',
            'src/recovery/CheckpointManager.js',
            'src/recovery/cli/advanced-recovery-cli.js',
            'src/recovery/test/comprehensive-recovery-test.js',
            'src/recovery/ErrorRecoveryDemo.js',
            'src/recovery/index.js'
        ];

        for (const file of expectedFiles) {
            try {
                await fs.access(file);
                this.recordResult(file, true, 'File exists');
            } catch (error) {
                this.recordResult(file, false, 'File missing');
            }
        }
    }

    async validateModuleImports() {
        console.log(chalk.blue('\n📦 Validating module imports...'));

        const modules = [
            { name: 'ErrorRecovery', path: './src/recovery/ErrorRecovery' },
            { name: 'ErrorAnalytics', path: './src/recovery/ErrorAnalytics' },
            { name: 'ErrorDiagnostics', path: './src/recovery/ErrorDiagnostics' },
            { name: 'RetryManager', path: './src/recovery/RetryManager' },
            { name: 'CheckpointManager', path: './src/recovery/CheckpointManager' },
            { name: 'RecoverySystem', path: './src/recovery/index', prop: 'RecoverySystem' }
        ];

        for (const module of modules) {
            try {
                const imported = require(module.path);
                const target = module.prop ? imported[module.prop] : imported;

                if (typeof target === 'function' || typeof target === 'object') {
                    this.recordResult(`${module.name} import`, true, 'Module imported successfully');
                } else {
                    this.recordResult(`${module.name} import`, false, 'Module export is invalid');
                }
            } catch (error) {
                this.recordResult(`${module.name} import`, false, `Import failed: ${error.message.substring(0, 100)}`);
            }
        }
    }

    async validateBasicFunctionality() {
        console.log(chalk.blue('\n⚙️ Validating basic functionality...'));

        try {
            // Test ErrorRecovery instantiation
            const ErrorRecovery = require('./src/recovery/ErrorRecovery');
            const errorRecovery = new ErrorRecovery({
                checkpointsDir: '/tmp/test-checkpoints'
            });

            if (errorRecovery && typeof errorRecovery.getMetrics === 'function') {
                const metrics = errorRecovery.getMetrics();
                this.recordResult('ErrorRecovery instantiation', true, 'Created and has metrics');
            } else {
                this.recordResult('ErrorRecovery instantiation', false, 'Missing expected methods');
            }

            // Test ErrorAnalytics instantiation
            const ErrorAnalytics = require('./src/recovery/ErrorAnalytics');
            const analytics = new ErrorAnalytics({
                dataDir: '/tmp/test-analytics',
                enableMachineLearning: false
            });

            if (analytics && typeof analytics.getMetrics === 'function') {
                this.recordResult('ErrorAnalytics instantiation', true, 'Created successfully');
            } else {
                this.recordResult('ErrorAnalytics instantiation', false, 'Missing expected methods');
            }

            // Test RecoverySystem instantiation
            const { RecoverySystem } = require('./src/recovery/index');
            const recoverySystem = new RecoverySystem({
                checkpointsDir: '/tmp/test-recovery',
                enableAnalytics: false
            });

            if (recoverySystem && typeof recoverySystem.getStatus === 'function') {
                this.recordResult('RecoverySystem instantiation', true, 'Created successfully');
            } else {
                this.recordResult('RecoverySystem instantiation', false, 'Missing expected methods');
            }

        } catch (error) {
            this.recordResult('Basic functionality', false, `Error: ${error.message.substring(0, 100)}`);
        }
    }

    async validateIntegration() {
        console.log(chalk.blue('\n🔗 Validating integration...'));

        try {
            const { RecoverySystem } = require('./src/recovery/index');

            const recovery = new RecoverySystem({
                checkpointsDir: '/tmp/test-integration',
                enableDiagnostics: true,
                enableAnalytics: false // Disable to avoid ML complexity
            });

            // Test basic operation
            let testPassed = false;
            const testOperation = async () => {
                testPassed = true;
                return 'success';
            };

            const result = await recovery.execute(testOperation, {
                context: { test: true }
            });

            if (result === 'success' && testPassed) {
                this.recordResult('Integration test', true, 'Basic operation executed successfully');
            } else {
                this.recordResult('Integration test', false, 'Basic operation failed');
            }

            // Test error handling
            let errorCaught = false;
            const failingOperation = async () => {
                throw new Error('Test error for validation');
            };

            try {
                await recovery.execute(failingOperation, {
                    context: { test: true }
                });
            } catch (error) {
                errorCaught = true;
                // This is expected
            }

            if (errorCaught) {
                this.recordResult('Error handling', true, 'Errors are properly handled');
            } else {
                this.recordResult('Error handling', false, 'Error handling not working');
            }

        } catch (error) {
            this.recordResult('Integration validation', false, `Error: ${error.message.substring(0, 100)}`);
        }
    }

    recordResult(test, passed, message) {
        const result = { test, passed, message, timestamp: new Date().toISOString() };
        this.results.details.push(result);

        if (passed) {
            this.results.passed++;
            console.log(`  ${chalk.green('✅')} ${test}: ${chalk.gray(message)}`);
        } else {
            this.results.failed++;
            console.log(`  ${chalk.red('❌')} ${test}: ${chalk.red(message)}`);
        }
    }

    displayResults() {
        const total = this.results.passed + this.results.failed;
        const successRate = total > 0 ? ((this.results.passed / total) * 100).toFixed(1) : '0.0';

        console.log(chalk.bold.yellow('\n📊 Validation Results:'));
        console.log(chalk.green(`  ✅ Passed: ${this.results.passed}`));
        console.log(chalk.red(`  ❌ Failed: ${this.results.failed}`));
        console.log(chalk.blue(`  📈 Success Rate: ${successRate}%`));

        if (this.results.failed === 0) {
            console.log(chalk.bold.green('\n🎉 All validations passed! Error Recovery System is ready.'));
        } else {
            console.log(chalk.bold.red('\n⚠️  Some validations failed. Please check the issues above.'));
        }

        // Show next steps
        console.log(chalk.bold.cyan('\n🚀 Next Steps:'));
        console.log('  • Run full test suite: node src/recovery/test/comprehensive-recovery-test.js');
        console.log('  • Try the demo: node src/recovery/ErrorRecoveryDemo.js');
        console.log('  • Use the CLI: node src/recovery/cli/advanced-recovery-cli.js status');
    }
}

// Run validation if called directly
if (require.main === module) {
    (async () => {
        try {
            const validator = new ErrorRecoveryValidator();
            const success = await validator.validate();
            process.exit(success ? 0 : 1);
        } catch (error) {
            console.error(chalk.red('Validation failed:'), error);
            process.exit(1);
        }
    })();
} else {
    module.exports = ErrorRecoveryValidator;
}