#!/usr/bin/env node

/**
 * Claude Enhancer Plus - Error Recovery System Demo
 * Comprehensive demonstration of the advanced error recovery capabilities
 */

const chalk = require('chalk');
const ora = require('ora');
const Table = require('cli-table3');

const ErrorRecovery = require('./ErrorRecovery');
const RetryManager = require('./RetryManager');
const ErrorDiagnostics = require('./ErrorDiagnostics');
const CheckpointManager = require('./CheckpointManager');
const ErrorAnalytics = require('./ErrorAnalytics');
const { createCLILogger } = require('../utils/CLISecureLogger');

class ErrorRecoveryDemo {
    constructor() {
        this.systems = {};
        this.demoScenarios = [];
        this.results = [];
        this.cliLogger = createCLILogger('ErrorRecoveryDemo');

        this.initializeDemoScenarios();

        // Setup cleanup on exit
        process.on('exit', (code) => this.cliLogger.endSession(code));
        process.on('SIGINT', () => {
            this.cliLogger.endSession(130);
            process.exit(130);
        });
    }

    /**
     * Initialize all systems and run demo
     */
    async run() {
        this.cliLogger.info('Starting Error Recovery System Demo',
            chalk.bold.cyan('🚀 Claude Enhancer Plus - Error Recovery System Demo\n'));

        const demoStartTime = this.cliLogger.operationStart('Error Recovery Demo');

        await this.initializeSystems();
        await this.runDemoScenarios();
        await this.displayResults();
        await this.demonstrateAnalytics();
        await this.showSystemMetrics();

        this.cliLogger.operationComplete('Error Recovery Demo', demoStartTime);
        console.log(chalk.bold.green('\n✨ Demo completed successfully!\n'));
    }

    /**
     * Initialize all recovery systems
     */
    async initializeSystems() {
        const spinner = ora('Initializing error recovery systems...').start();

        try {
            // Initialize Error Recovery system
            this.systems.errorRecovery = new ErrorRecovery({
                enableMetrics: true,
                gracefulDegradation: true,
                autoCleanup: false // Keep data for demo
            });

            // Initialize Retry Manager
            this.systems.retryManager = new RetryManager({
                defaultMaxRetries: 3,
                baseDelay: 500,
                maxDelay: 5000
            });

            // Initialize Error Diagnostics
            this.systems.diagnostics = new ErrorDiagnostics({
                enableMetrics: true,
                patternThreshold: 2
            });

            // Initialize Checkpoint Manager
            this.systems.checkpointManager = new CheckpointManager({
                maxCheckpoints: 50,
                autoBackup: true
            });

            // Initialize Error Analytics
            this.systems.analytics = new ErrorAnalytics({
                enableMachineLearning: false, // Simplified for demo
                enablePrediction: true
            });

            // Wait for initialization
            await new Promise(resolve => setTimeout(resolve, 1000));

            spinner.succeed('All systems initialized successfully');

            // Display system overview
            this.displaySystemOverview();

        } catch (error) {
            spinner.fail(`System initialization failed: ${error.message}`);
            throw error;
        }
    }

    /**
     * Display overview of initialized systems
     */
    displaySystemOverview() {
        console.log(chalk.bold.blue('\n📋 System Overview:\n'));

        const systemTable = new Table({
            head: [chalk.cyan('System'), chalk.cyan('Status'), chalk.cyan('Features')]
        });

        systemTable.push(
            ['Error Recovery', chalk.green('✓ Active'), 'Circuit Breakers, Pattern Learning, Checkpoints'],
            ['Retry Manager', chalk.green('✓ Active'), 'Exponential Backoff, Strategy Customization'],
            ['Error Diagnostics', chalk.green('✓ Active'), 'Pattern Matching, Root Cause Analysis'],
            ['Checkpoint Manager', chalk.green('✓ Active'), 'State Persistence, Restoration'],
            ['Error Analytics', chalk.green('✓ Active'), 'ML Analysis, Prediction, Insights']
        );

        console.log(systemTable.toString());
    }

    /**
     * Initialize demo scenarios
     */
    initializeDemoScenarios() {
        this.demoScenarios = [
            {
                name: 'Network Timeout Recovery',
                description: 'Simulate network timeout and demonstrate automatic recovery',
                scenario: this.networkTimeoutScenario.bind(this)
            },
            {
                name: 'File System Error Recovery',
                description: 'Handle missing files and demonstrate path creation',
                scenario: this.fileSystemErrorScenario.bind(this)
            },
            {
                name: 'Memory Pressure Handling',
                description: 'Demonstrate graceful degradation under memory pressure',
                scenario: this.memoryPressureScenario.bind(this)
            },
            {
                name: 'Circuit Breaker Protection',
                description: 'Show circuit breaker opening and recovery',
                scenario: this.circuitBreakerScenario.bind(this)
            },
            {
                name: 'Pattern Learning Demo',
                description: 'Demonstrate error pattern detection and learning',
                scenario: this.patternLearningScenario.bind(this)
            },
            {
                name: 'Checkpoint Recovery',
                description: 'Show state checkpointing and restoration',
                scenario: this.checkpointRecoveryScenario.bind(this)
            },
            {
                name: 'Comprehensive Recovery',
                description: 'Full integration test with multiple error types',
                scenario: this.comprehensiveRecoveryScenario.bind(this)
            }
        ];
    }

    /**
     * Run all demo scenarios
     */
    async runDemoScenarios() {
        console.log(chalk.bold.yellow('\n🎭 Running Demo Scenarios:\n'));

        for (let i = 0; i < this.demoScenarios.length; i++) {
            const scenario = this.demoScenarios[i];
            console.log(chalk.blue(`\n${i + 1}. ${scenario.name}`));
            console.log(chalk.gray(`   ${scenario.description}`));

            const result = await this.runScenario(scenario);
            this.results.push(result);

            // Brief pause between scenarios
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }

    /**
     * Run a single scenario
     */
    async runScenario(scenario) {
        const startTime = Date.now();
        let spinner = ora(`Running ${scenario.name}...`).start();

        try {
            const result = await scenario.scenario();
            const duration = Date.now() - startTime;

            spinner.succeed(`${scenario.name} completed in ${duration}ms`);

            return {
                name: scenario.name,
                success: true,
                duration,
                details: result
            };

        } catch (error) {
            spinner.fail(`${scenario.name} failed: ${error.message}`);

            return {
                name: scenario.name,
                success: false,
                duration: Date.now() - startTime,
                error: error.message
            };
        }
    }

    /**
     * Network timeout recovery scenario
     */
    async networkTimeoutScenario() {
        let attempts = 0;

        const operation = async () => {
            attempts++;
            if (attempts < 3) {
                const error = new Error('ETIMEDOUT: Network request timed out');
                error.code = 'ETIMEDOUT';
                throw error;
            }
            return { success: true, data: 'Network operation completed', attempts };
        };

        const result = await this.systems.errorRecovery.executeWithRecovery(operation, {
            strategy: 'network',
            context: { operationType: 'api_call', timeout: 5000 }
        });

        console.log(chalk.green(`     ✓ Recovered after ${attempts} attempts`));
        return result;
    }

    /**
     * File system error recovery scenario
     */
    async fileSystemErrorScenario() {
        const operation = async () => {
            const error = new Error("ENOENT: no such file or directory, open '/demo/missing/file.txt'");
            error.code = 'ENOENT';
            throw error;
        };

        try {
            await this.systems.errorRecovery.executeWithRecovery(operation, {
                strategy: 'file',
                context: { operationType: 'file_read' }
            });
        } catch (recoveredError) {
            // Analyze the enhanced error
            const diagnostic = await this.systems.diagnostics.analyzeError(recoveredError);
            console.log(chalk.green(`     ✓ Error categorized as: ${diagnostic.category}`));
            console.log(chalk.gray(`     ℹ Recovery suggestions: ${diagnostic.analysis.suggestions.slice(0, 2).join(', ')}`));
            return { diagnostic, recovered: true };
        }
    }

    /**
     * Memory pressure scenario
     */
    async memoryPressureScenario() {
        const operation = async () => {
            const error = new Error('JavaScript heap out of memory');
            error.code = 'ENOMEM';
            throw error;
        };

        try {
            await this.systems.errorRecovery.executeWithRecovery(operation, {
                strategy: 'phase',
                context: { memoryUsage: 0.95, operationType: 'data_processing' }
            });
        } catch (error) {
            // Should have attempted graceful degradation
            if (error.recoveryContext) {
                console.log(chalk.green(`     ✓ Graceful degradation attempted`));
                console.log(chalk.gray(`     ℹ Suggestions: ${error.suggestions.slice(0, 2).join(', ')}`));
                return { gracefulDegradation: true, suggestions: error.suggestions };
            }
            throw error;
        }
    }

    /**
     * Circuit breaker scenario
     */
    async circuitBreakerScenario() {
        // Simulate multiple failures to open circuit breaker
        console.log(chalk.gray('     → Simulating repeated failures...'));

        for (let i = 0; i < 6; i++) {
            this.systems.errorRecovery.updateCircuitBreaker('network', false, new Error('Service unavailable'));
        }

        const breakerStatus = this.systems.errorRecovery.checkCircuitBreaker('network');
        console.log(chalk.yellow(`     ⚡ Circuit breaker state: ${breakerStatus.state}`));

        // Reset and demonstrate recovery
        await new Promise(resolve => setTimeout(resolve, 100));
        this.systems.errorRecovery.updateCircuitBreaker('network', true);

        const recoveredStatus = this.systems.errorRecovery.checkCircuitBreaker('network');
        console.log(chalk.green(`     ✓ Circuit breaker recovered: ${recoveredStatus.state}`));

        return {
            openedState: breakerStatus.state,
            recoveredState: recoveredStatus.state
        };
    }

    /**
     * Pattern learning scenario
     */
    async patternLearningScenario() {
        // Generate recurring error pattern
        console.log(chalk.gray('     → Generating recurring error patterns...'));

        const recurringError = new Error('Database connection pool exhausted');

        for (let i = 0; i < 4; i++) {
            this.systems.errorRecovery.trackErrorFrequency(recurringError);

            // Add to recovery history
            this.systems.errorRecovery.recoveryHistory.push({
                timestamp: new Date(Date.now() - (i * 60000)).toISOString(), // Spread over time
                error: recurringError.message,
                category: 'database',
                strategy: 'network',
                attempt: 1
            });
        }

        // Trigger pattern analysis
        this.systems.errorRecovery.analyzeErrorPatterns();

        const frequencyPatterns = this.systems.errorRecovery.patternLearningData.get('frequency') || [];
        console.log(chalk.green(`     ✓ Detected ${frequencyPatterns.length} frequency patterns`));

        return { patternsDetected: frequencyPatterns.length };
    }

    /**
     * Checkpoint recovery scenario
     */
    async checkpointRecoveryScenario() {
        const checkpointId = `demo-checkpoint-${Date.now()}`;
        const importantState = {
            processedData: { count: 1000, status: 'partial' },
            userSession: { id: 'user123', authenticated: true },
            operationProgress: { phase: 'Phase3', step: 15 }
        };

        // Create checkpoint
        console.log(chalk.gray('     → Creating checkpoint...'));
        await this.systems.errorRecovery.createCheckpoint(checkpointId, importantState, {
            description: 'Demo checkpoint before risky operation',
            tags: ['demo', 'important']
        });

        // Simulate operation that needs checkpoint restore
        const operation = async () => {
            throw new Error('Critical operation failed, need to restore state');
        };

        try {
            await this.systems.errorRecovery.executeWithRecovery(operation, {
                checkpointId,
                strategy: 'validation'
            });
        } catch (error) {
            // Checkpoint should have been created and available for restore
            const checkpoints = await this.systems.errorRecovery.listCheckpoints();
            const ourCheckpoint = checkpoints.find(cp => cp.id === checkpointId);

            if (ourCheckpoint) {
                console.log(chalk.green(`     ✓ Checkpoint created and available for recovery`));
                console.log(chalk.gray(`     ℹ Checkpoint contains: ${Object.keys(importantState).join(', ')}`));
                return { checkpointCreated: true, checkpointData: importantState };
            }
        }
    }

    /**
     * Comprehensive recovery scenario
     */
    async comprehensiveRecoveryScenario() {
        console.log(chalk.gray('     → Testing multiple integrated systems...'));

        const errors = [
            { error: new Error('ECONNREFUSED: Connection refused'), expected: 'network' },
            { error: new Error('Cannot read property "data" of undefined'), expected: 'javascript' },
            { error: new Error('EACCES: permission denied'), expected: 'filesystem' }
        ];

        const results = [];

        for (const testCase of errors) {
            testCase.error.code = testCase.error.message.match(/^[A-Z]+/)?.[0];

            // Analyze with diagnostics
            const diagnostic = await this.systems.diagnostics.analyzeError(testCase.error);

            // Analyze with analytics
            const analysis = await this.systems.analytics.analyzeError(testCase.error, {
                phase: 'Phase3_Implementation',
                operationType: 'demo'
            });

            results.push({
                error: testCase.error.message,
                expectedCategory: testCase.expected,
                diagnosticCategory: diagnostic.category,
                analyticsConfidence: analysis.confidence,
                matched: diagnostic.category === testCase.expected
            });
        }

        const accuracy = results.filter(r => r.matched).length / results.length;
        console.log(chalk.green(`     ✓ Classification accuracy: ${(accuracy * 100).toFixed(1)}%`));

        return { testCases: results.length, accuracy };
    }

    /**
     * Display demo results
     */
    async displayResults() {
        console.log(chalk.bold.green('\n📊 Demo Results Summary:\n'));

        const resultsTable = new Table({
            head: [
                chalk.cyan('Scenario'),
                chalk.cyan('Status'),
                chalk.cyan('Duration'),
                chalk.cyan('Details')
            ]
        });

        for (const result of this.results) {
            const statusIcon = result.success ? chalk.green('✅') : chalk.red('❌');
            const statusText = result.success ? chalk.green('Success') : chalk.red('Failed');
            const duration = `${result.duration}ms`;
            const details = result.success ?
                chalk.gray('Completed successfully') :
                chalk.red(result.error);

            resultsTable.push([
                result.name,
                `${statusIcon} ${statusText}`,
                duration,
                details
            ]);
        }

        console.log(resultsTable.toString());

        // Summary stats
        const successful = this.results.filter(r => r.success).length;
        const total = this.results.length;
        const successRate = ((successful / total) * 100).toFixed(1);

        console.log(chalk.bold.cyan(`\nOverall Success Rate: ${successRate}% (${successful}/${total})`));
    }

    /**
     * Demonstrate analytics capabilities
     */
    async demonstrateAnalytics() {
        console.log(chalk.bold.magenta('\n🧠 Analytics & Insights:\n'));

        // Get system analytics
        const analytics = this.systems.errorRecovery.getAnalytics();
        const metrics = this.systems.errorRecovery.getMetrics();

        // Display error frequency analysis
        if (analytics.errorFrequency.topErrors.length > 0) {
            console.log(chalk.blue('📊 Top Error Patterns:'));
            analytics.errorFrequency.topErrors.slice(0, 3).forEach((error, index) => {
                console.log(chalk.gray(`  ${index + 1}. ${error.signature} (${error.count} occurrences)`));
            });
        }

        // Display circuit breaker status
        console.log(chalk.blue('\n⚡ Circuit Breaker Health:'));
        const cbAnalytics = analytics.circuitBreakerStatus;
        for (const [type, status] of Object.entries(cbAnalytics)) {
            const healthColor = status.healthStatus === 'healthy' ? chalk.green :
                              status.healthStatus === 'recovering' ? chalk.yellow :
                              chalk.red;
            console.log(`  ${type}: ${healthColor(status.healthStatus)} (${status.state})`);
        }

        // Display recommendations
        if (analytics.recommendations.length > 0) {
            console.log(chalk.blue('\n💡 System Recommendations:'));
            analytics.recommendations.slice(0, 3).forEach((rec, index) => {
                const priorityColor = rec.priority === 'high' ? chalk.red :
                                    rec.priority === 'medium' ? chalk.yellow :
                                    chalk.gray;
                console.log(`  ${index + 1}. ${priorityColor(rec.priority.toUpperCase())}: ${rec.message}`);
            });
        }
    }

    /**
     * Show comprehensive system metrics
     */
    async showSystemMetrics() {
        console.log(chalk.bold.cyan('\n📈 System Performance Metrics:\n'));

        const metricsTable = new Table({
            head: [chalk.cyan('System'), chalk.cyan('Key Metrics'), chalk.cyan('Performance')]
        });

        // Error Recovery metrics
        const errorRecoveryMetrics = this.systems.errorRecovery.getMetrics();
        metricsTable.push([
            'Error Recovery',
            `Errors: ${errorRecoveryMetrics.totalErrors}\nRecovered: ${errorRecoveryMetrics.recoveredErrors}\nSuccess Rate: ${errorRecoveryMetrics.successRate}`,
            `Avg Recovery: ${errorRecoveryMetrics.averageRecoveryTimeMs}ms\nCircuit Trips: ${errorRecoveryMetrics.circuitBreakerTrips}`
        ]);

        // Retry Manager metrics
        const retryMetrics = this.systems.retryManager.getMetrics();
        const networkMetrics = retryMetrics.network || {};
        metricsTable.push([
            'Retry Manager',
            `Total Attempts: ${networkMetrics.totalAttempts || 0}\nSuccessful Retries: ${networkMetrics.successfulRetries || 0}`,
            `Failed Retries: ${networkMetrics.failedRetries || 0}`
        ]);

        // Analytics metrics
        const analyticsMetrics = this.systems.analytics.getMetrics();
        metricsTable.push([
            'Analytics',
            `Analyzed: ${analyticsMetrics.totalAnalyzed}\nPatterns: ${analyticsMetrics.patternsDetected}`,
            `Avg Processing: ${analyticsMetrics.averageProcessingTime.toFixed(2)}ms\nConfidence: ${(analyticsMetrics.averageConfidence * 100).toFixed(1)}%`
        ]);

        console.log(metricsTable.toString());

        // Display pattern learning data
        const patternData = this.systems.errorRecovery.patternLearningData;
        if (patternData.size > 0) {
            console.log(chalk.blue('\n🔍 Pattern Learning Status:'));
            for (const [type, patterns] of patternData.entries()) {
                console.log(`  ${type}: ${Array.isArray(patterns) ? patterns.length : 0} patterns detected`);
            }
        }
    }
}

// Run demo if called directly
if (require.main === module) {
    const demo = new ErrorRecoveryDemo();
    demo.run().catch(error => {
        console.error(chalk.red('Demo failed:'), error);
        process.exit(1);
    });
} else {
    module.exports = ErrorRecoveryDemo;
}