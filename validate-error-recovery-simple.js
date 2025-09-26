#!/usr/bin/env node

/**
 * Claude Enhancer 5.0 - Error Recovery System Simple Validation
 * Basic validation without external dependencies
 */

const path = require('path');
const fs = require('fs').promises;

class SimpleErrorRecoveryValidator {
    constructor() {
        this.results = {
            passed: 0,
            failed: 0,
            details: []
        };
    }

    async validate() {
        // console.log('🔍 Validating Error Recovery System...\n');

        // Test file structure
        await this.validateFileStructure();

        // Test module imports
        await this.validateModuleImports();

        // Test basic functionality
        await this.validateBasicFunctionality();

        this.displayResults();
        return this.results.failed === 0;
    }

    async validateFileStructure() {
        // console.log('📁 Validating file structure...');

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
        // console.log('\n📦 Validating module imports...');

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
        // console.log('\n⚙️ Validating basic functionality...');

        try {
            // Test ErrorRecovery instantiation
            const ErrorRecovery = require('./src/recovery/ErrorRecovery');
            const errorRecovery = new ErrorRecovery({
                checkpointsDir: '/tmp/test-checkpoints'
            });

            if (errorRecovery && typeof errorRecovery.getMetrics === 'function') {
                const metrics = errorRecovery.getMetrics();
                this.recordResult('ErrorRecovery instantiation', true, `Created with ${Object.keys(metrics).length} metrics`);
            } else {
                this.recordResult('ErrorRecovery instantiation', false, 'Missing expected methods');
            }

            // Test ErrorAnalytics instantiation
            const ErrorAnalytics = require('./src/recovery/ErrorAnalytics');
            const analytics = new ErrorAnalytics({
                dataDir: '/tmp/test-analytics',
                enableMachineLearning: false,
                enablePrediction: false
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

            // Test simple error analysis
            const ErrorDiagnostics = require('./src/recovery/ErrorDiagnostics');
            const diagnostics = new ErrorDiagnostics({
                logDir: '/tmp/test-logs'
            });

            const testError = new Error('Test error for validation');
            testError.code = 'TEST_ERROR';

            const diagnostic = await diagnostics.analyzeError(testError);

            if (diagnostic && diagnostic.id && diagnostic.analysis) {
                this.recordResult('Error analysis', true, `Analyzed with category: ${diagnostic.category}`);
            } else {
                this.recordResult('Error analysis', false, 'Analysis failed or incomplete');
            }

        } catch (error) {
            this.recordResult('Basic functionality', false, `Error: ${error.message.substring(0, 100)}`);
        }
    }

    recordResult(test, passed, message) {
        const result = { test, passed, message, timestamp: new Date().toISOString() };
        this.results.details.push(result);

        if (passed) {
            this.results.passed++;
            // console.log(`  ✅ ${test}: ${message}`);
        } else {
            this.results.failed++;
            // console.log(`  ❌ ${test}: ${message}`);
        }
    }

    displayResults() {
        const total = this.results.passed + this.results.failed;
        const successRate = total > 0 ? ((this.results.passed / total) * 100).toFixed(1) : '0.0';

        // console.log('\n📊 Validation Results:');
        // console.log(`  ✅ Passed: ${this.results.passed}`);
        // console.log(`  ❌ Failed: ${this.results.failed}`);
        // console.log(`  📈 Success Rate: ${successRate}%`);

        if (this.results.failed === 0) {
            // console.log('\n🎉 All validations passed! Error Recovery System is ready.');
        } else {
            // console.log('\n⚠️  Some validations failed. Please check the issues above.');
        }

        // console.log('\n🚀 Available Commands:');
        // console.log('  • Run test: node src/recovery/test/comprehensive-recovery-test.js');
        // console.log('  • Run demo: node src/recovery/ErrorRecoveryDemo.js');
        // console.log('  • Check status: node -e "// console.log(require(\'./src/recovery\').RecoverySystem)"');
    }
}

// Run validation if called directly
if (require.main === module) {
    (async () => {
        try {
            const validator = new SimpleErrorRecoveryValidator();
            const success = await validator.validate();
            process.exit(success ? 0 : 1);
        } catch (error) {
            console.error('Validation failed:', error.message);
            process.exit(1);
        }
    })();
} else {
    module.exports = SimpleErrorRecoveryValidator;
}