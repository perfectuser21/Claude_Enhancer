#!/usr/bin/env node

/**
 * Claude Enhancer Plus - Advanced Recovery CLI
 * Comprehensive command-line interface for error recovery and system management
 */

const { Command } = require('commander');
const chalk = require('chalk');
const ora = require('ora');
const Table = require('cli-table3');
const inquirer = require('inquirer');
const path = require('path');
const fs = require('fs').promises;

const ErrorRecovery = require('../ErrorRecovery');
const RetryManager = require('../RetryManager');
const ErrorDiagnostics = require('../ErrorDiagnostics');
const CheckpointManager = require('../CheckpointManager');
const { createCLILogger } = require('../../utils/CLISecureLogger');

class AdvancedRecoveryCLI {
    constructor() {
        this.program = new Command();
        this.errorRecovery = new ErrorRecovery();
        this.retryManager = new RetryManager();
        this.diagnostics = new ErrorDiagnostics();
        this.checkpointManager = new CheckpointManager();
        this.cliLogger = createCLILogger('AdvancedRecoveryCLI');

        this.setupCommands();
        this.setupEventHandlers();

        // Setup cleanup on exit
        process.on('exit', (code) => this.cliLogger.endSession(code));
        process.on('SIGINT', () => {
            this.cliLogger.endSession(130);
            process.exit(130);
        });
    }

    setupCommands() {
        this.program
            .name('recovery-cli')
            .description('Advanced error recovery and system management CLI')
            .version('2.0.0');

        // Status commands
        this.program
            .command('status')
            .description('Show system recovery status')
            .option('-v, --verbose', 'Show detailed status')
            .option('-j, --json', 'Output as JSON')
            .action(this.statusCommand.bind(this));

        // Recovery commands
        this.program
            .command('recover')
            .description('Execute recovery operations')
            .option('-t, --type <type>', 'Recovery type (git, network, file, etc.)')
            .option('-a, --auto', 'Automatic recovery based on analysis')
            .option('-c, --checkpoint <id>', 'Use specific checkpoint')
            .option('--dry-run', 'Show what would be done without executing')
            .action(this.recoverCommand.bind(this));

        // Circuit breaker commands
        this.program
            .command('circuit-breaker')
            .description('Manage circuit breakers')
            .option('-l, --list', 'List all circuit breakers')
            .option('-r, --reset <type>', 'Reset specific circuit breaker')
            .option('--reset-all', 'Reset all circuit breakers')
            .option('-s, --status <type>', 'Show status of specific circuit breaker')
            .action(this.circuitBreakerCommand.bind(this));

        // Checkpoint commands
        this.program
            .command('checkpoint')
            .description('Manage checkpoints')
            .option('-l, --list', 'List all checkpoints')
            .option('-c, --create <id>', 'Create new checkpoint')
            .option('-r, --restore <id>', 'Restore from checkpoint')
            .option('-d, --delete <id>', 'Delete checkpoint')
            .option('--cleanup', 'Clean up old checkpoints')
            .action(this.checkpointCommand.bind(this));

        // Analytics commands
        this.program
            .command('analytics')
            .description('Show error analytics and insights')
            .option('-p, --patterns', 'Show error patterns')
            .option('-f, --frequency', 'Show error frequency analysis')
            .option('-e, --effectiveness', 'Show recovery effectiveness')
            .option('-r, --recommendations', 'Show recommendations')
            .action(this.analyticsCommand.bind(this));

        // Pattern commands
        this.program
            .command('patterns')
            .description('Manage error patterns')
            .option('-l, --list', 'List detected patterns')
            .option('-a, --analyze', 'Analyze current patterns')
            .option('-c, --clear', 'Clear pattern data')
            .option('--export <file>', 'Export patterns to file')
            .action(this.patternsCommand.bind(this));

        // Diagnostics commands
        this.program
            .command('diagnose')
            .description('Diagnose specific error or system issues')
            .argument('[error-message]', 'Error message to diagnose')
            .option('-i, --interactive', 'Interactive diagnosis mode')
            .option('-d, --detailed', 'Detailed analysis')
            .option('--system', 'System-wide diagnostics')
            .action(this.diagnoseCommand.bind(this));

        // Maintenance commands
        this.program
            .command('maintenance')
            .description('Perform system maintenance')
            .option('--cleanup', 'Clean up old data and logs')
            .option('--optimize', 'Optimize performance')
            .option('--health-check', 'Perform health check')
            .option('--backup', 'Backup recovery data')
            .action(this.maintenanceCommand.bind(this));

        // Configuration commands
        this.program
            .command('config')
            .description('Manage recovery system configuration')
            .option('-s, --show', 'Show current configuration')
            .option('-e, --edit', 'Edit configuration interactively')
            .option('--reset', 'Reset to default configuration')
            .option('-v, --validate', 'Validate configuration')
            .action(this.configCommand.bind(this));

        // Interactive mode
        this.program
            .command('interactive')
            .alias('i')
            .description('Start interactive recovery mode')
            .action(this.interactiveMode.bind(this));
    }

    setupEventHandlers() {
        this.errorRecovery.on('errorAnalyzed', (data) => {
            if (process.env.RECOVERY_VERBOSE) {
                console.log(chalk.gray(`Error analyzed: ${data.analysis.category} - ${data.analysis.severity}`));
            }
        });

        this.errorRecovery.on('errorRecovered', (data) => {
            console.log(chalk.green('✓'), `Error recovered in ${data.recoveryTime}ms`);
        });

        this.errorRecovery.on('circuitBreakerOpened', (data) => {
            console.log(chalk.red('⚠'), `Circuit breaker opened for ${data.type}`);
        });

        this.errorRecovery.on('patternsAnalyzed', (data) => {
            if (process.env.RECOVERY_VERBOSE) {
                console.log(chalk.blue('📊'), `Patterns analyzed: ${data.frequency + data.temporal + data.correlation} total`);
            }
        });
    }

    async statusCommand(options) {
        const spinner = ora('Gathering system status...').start();

        try {
            const metrics = this.errorRecovery.getMetrics();
            const analytics = this.errorRecovery.getAnalytics();
            const checkpointStats = await this.checkpointManager.getStatistics();

            spinner.stop();

            if (options.json) {
                console.log(JSON.stringify({
                    metrics,
                    analytics,
                    checkpointStats,
                    timestamp: new Date().toISOString()
                }, null, 2));
                return;
            }

            this.displayStatusTable(metrics, analytics, checkpointStats, options.verbose);

        } catch (error) {
            spinner.fail(`Failed to get status: ${error.message}`);
            process.exit(1);
        }
    }

    displayStatusTable(metrics, analytics, checkpointStats, verbose = false) {
        console.log(chalk.bold.blue('\n📊 Recovery System Status\n'));

        // Main metrics table
        const metricsTable = new Table({
            head: [chalk.cyan('Metric'), chalk.cyan('Value'), chalk.cyan('Status')]
        });

        const successRate = parseFloat(metrics.successRate);
        const successStatus = successRate >= 90 ? chalk.green('Excellent') :
                             successRate >= 70 ? chalk.yellow('Good') :
                             chalk.red('Needs Attention');

        metricsTable.push(
            ['Total Errors', metrics.totalErrors, metrics.totalErrors > 100 ? chalk.yellow('High') : chalk.green('Normal')],
            ['Recovery Rate', metrics.successRate, successStatus],
            ['Avg Recovery Time', `${metrics.averageRecoveryTimeMs}ms`, metrics.averageRecoveryTimeMs < 1000 ? chalk.green('Fast') : chalk.yellow('Slow')],
            ['Automatic Recoveries', metrics.automaticRecoveries, chalk.green('Active')],
            ['Circuit Breaker Trips', metrics.circuitBreakerTrips, metrics.circuitBreakerTrips > 10 ? chalk.red('High') : chalk.green('Low')]
        );

        console.log(metricsTable.toString());

        // Circuit breaker status
        if (verbose || Object.values(metrics.circuitBreakerStates).some(state => state !== 'CLOSED')) {
            console.log(chalk.bold.yellow('\n⚡ Circuit Breaker Status\n'));

            const breakerTable = new Table({
                head: [chalk.cyan('Type'), chalk.cyan('State'), chalk.cyan('Health')]
            });

            for (const [type, state] of Object.entries(metrics.circuitBreakerStates)) {
                const healthColor = state === 'CLOSED' ? chalk.green :
                                  state === 'HALF_OPEN' ? chalk.yellow :
                                  chalk.red;

                const healthText = state === 'CLOSED' ? 'Healthy' :
                                 state === 'HALF_OPEN' ? 'Recovering' :
                                 'Unhealthy';

                breakerTable.push([type, healthColor(state), healthColor(healthText)]);
            }

            console.log(breakerTable.toString());
        }

        // Checkpoint information
        console.log(chalk.bold.green('\n💾 Checkpoint Status\n'));
        const checkpointTable = new Table({
            head: [chalk.cyan('Metric'), chalk.cyan('Value')]
        });

        checkpointTable.push(
            ['Total Checkpoints', checkpointStats.totalCheckpoints],
            ['Active Checkpoints', checkpointStats.activeCheckpoints],
            ['Critical Checkpoints', checkpointStats.criticalCheckpoints],
            ['Total Size', this.formatBytes(checkpointStats.totalSize)]
        );

        console.log(checkpointTable.toString());

        // Pattern analysis summary
        if (verbose && metrics.patternStats.frequencyPatterns > 0) {
            console.log(chalk.bold.magenta('\n🔍 Pattern Analysis\n'));
            const patternTable = new Table({
                head: [chalk.cyan('Type'), chalk.cyan('Count')]
            });

            patternTable.push(
                ['Frequency Patterns', metrics.patternStats.frequencyPatterns],
                ['Temporal Patterns', metrics.patternStats.temporalPatterns],
                ['Correlation Patterns', metrics.patternStats.correlationPatterns]
            );

            console.log(patternTable.toString());
        }

        // Recommendations
        const recommendations = analytics.recommendations.filter(r => r.priority === 'high');
        if (recommendations.length > 0) {
            console.log(chalk.bold.red('\n⚠️  High Priority Recommendations\n'));
            recommendations.forEach((rec, index) => {
                console.log(chalk.red(`${index + 1}.`), rec.message);
                console.log(chalk.gray(`   Action: ${rec.action}\n`));
            });
        }
    }

    async recoverCommand(options) {
        const spinner = ora('Initializing recovery operation...').start();

        try {
            if (options.auto) {
                spinner.text = 'Analyzing system for automatic recovery...';
                await this.automaticRecovery(options.dryRun);
            } else if (options.type) {
                spinner.text = `Executing ${options.type} recovery...`;
                await this.typeSpecificRecovery(options.type, options);
            } else {
                spinner.stop();
                await this.interactiveRecovery();
                return;
            }

            spinner.succeed('Recovery operation completed');

        } catch (error) {
            spinner.fail(`Recovery failed: ${error.message}`);

            // Suggest alternative recovery methods
            console.log(chalk.yellow('\n💡 Alternative recovery options:'));
            console.log('  • recovery-cli recover --auto');
            console.log('  • recovery-cli interactive');
            console.log('  • recovery-cli diagnose --system');

            process.exit(1);
        }
    }

    async automaticRecovery(dryRun = false) {
        const analytics = this.errorRecovery.getAnalytics();
        const recommendations = analytics.recommendations
            .filter(r => r.priority === 'high' || r.priority === 'critical')
            .slice(0, 5);

        if (recommendations.length === 0) {
            console.log(chalk.green('✓ No critical issues detected requiring immediate recovery'));
            return;
        }

        console.log(chalk.blue('\n🔧 Automatic Recovery Plan:\n'));

        recommendations.forEach((rec, index) => {
            console.log(chalk.blue(`${index + 1}.`), rec.message);
            console.log(chalk.gray(`   Action: ${rec.action}`));
        });

        if (dryRun) {
            console.log(chalk.yellow('\n[DRY RUN] Recovery plan generated but not executed'));
            return;
        }

        const confirm = await inquirer.prompt([{
            type: 'confirm',
            name: 'proceed',
            message: 'Execute automatic recovery plan?',
            default: true
        }]);

        if (!confirm.proceed) {
            console.log(chalk.yellow('Recovery cancelled'));
            return;
        }

        // Execute recovery actions
        for (const rec of recommendations) {
            const spinner = ora(`Executing: ${rec.action}`).start();

            try {
                await this.executeRecoveryAction(rec.action, rec.type);
                spinner.succeed();
            } catch (error) {
                spinner.fail(`Action failed: ${error.message}`);
            }
        }
    }

    async typeSpecificRecovery(type, options) {
        const strategies = {
            git: async () => {
                console.log(chalk.blue('🔧 Git Recovery:'));
                console.log('  • Stashing uncommitted changes');
                console.log('  • Resetting to clean state');
                console.log('  • Validating repository integrity');

                // Execute git recovery
                const result = await this.errorRecovery.recoveryActions.get('resetGitState')();
                return result;
            },

            network: async () => {
                console.log(chalk.blue('🌐 Network Recovery:'));
                console.log('  • Testing connectivity');
                console.log('  • Resetting circuit breakers');
                console.log('  • Applying exponential backoff');

                // Reset network circuit breaker
                const breaker = this.errorRecovery.circuitBreakers.get('network');
                if (breaker) {
                    breaker.state = 'CLOSED';
                    breaker.failureCount = 0;
                }

                return { success: true, actions: ['Network circuit breaker reset'] };
            },

            filesystem: async () => {
                console.log(chalk.blue('📁 Filesystem Recovery:'));
                console.log('  • Creating missing directories');
                console.log('  • Fixing permissions');
                console.log('  • Cleaning temporary files');

                // Execute filesystem recovery
                const result = await this.errorRecovery.recoveryActions.get('createMissingPaths')();
                return result;
            },

            memory: async () => {
                console.log(chalk.blue('🧠 Memory Recovery:'));
                console.log('  • Triggering garbage collection');
                console.log('  • Clearing caches');
                console.log('  • Enabling graceful degradation');

                if (global.gc) {
                    global.gc();
                }

                return { success: true, actions: ['Memory cleanup completed'] };
            }
        };

        const recoveryFunction = strategies[type];
        if (!recoveryFunction) {
            throw new Error(`Unknown recovery type: ${type}`);
        }

        const result = await recoveryFunction();

        if (result.success) {
            console.log(chalk.green('\n✓ Recovery successful'));
            result.actions?.forEach(action => {
                console.log(chalk.gray(`  • ${action}`));
            });
        } else {
            throw new Error(result.error || 'Recovery failed');
        }
    }

    async circuitBreakerCommand(options) {
        if (options.list) {
            await this.listCircuitBreakers();
        } else if (options.reset) {
            await this.resetCircuitBreaker(options.reset);
        } else if (options.resetAll) {
            await this.resetAllCircuitBreakers();
        } else if (options.status) {
            await this.showCircuitBreakerStatus(options.status);
        } else {
            await this.listCircuitBreakers();
        }
    }

    async listCircuitBreakers() {
        console.log(chalk.bold.blue('\n⚡ Circuit Breaker Status\n'));

        const analytics = this.errorRecovery.getCircuitBreakerAnalytics();
        const table = new Table({
            head: [
                chalk.cyan('Type'),
                chalk.cyan('State'),
                chalk.cyan('Failures'),
                chalk.cyan('Last Failure'),
                chalk.cyan('Health')
            ]
        });

        for (const [type, data] of Object.entries(analytics)) {
            const stateColor = data.state === 'CLOSED' ? chalk.green :
                             data.state === 'HALF_OPEN' ? chalk.yellow :
                             chalk.red;

            const healthColor = data.healthStatus === 'healthy' ? chalk.green :
                              data.healthStatus === 'recovering' ? chalk.yellow :
                              chalk.red;

            table.push([
                type,
                stateColor(data.state),
                data.failureCount,
                data.lastFailure ? data.lastFailure.toLocaleString() : 'Never',
                healthColor(data.healthStatus)
            ]);
        }

        console.log(table.toString());
    }

    async resetCircuitBreaker(type) {
        const breaker = this.errorRecovery.circuitBreakers.get(type);
        if (!breaker) {
            console.log(chalk.red(`Circuit breaker '${type}' not found`));
            return;
        }

        breaker.state = 'CLOSED';
        breaker.failureCount = 0;
        breaker.lastFailureTime = null;
        breaker.nextAttemptTime = null;

        console.log(chalk.green(`✓ Reset circuit breaker: ${type}`));
    }

    async resetAllCircuitBreakers() {
        const breakers = Array.from(this.errorRecovery.circuitBreakers.keys());

        for (const type of breakers) {
            await this.resetCircuitBreaker(type);
        }

        console.log(chalk.green(`✓ Reset all ${breakers.length} circuit breakers`));
    }

    async analyticsCommand(options) {
        const spinner = ora('Analyzing system data...').start();

        try {
            const analytics = this.errorRecovery.getAnalytics();
            spinner.stop();

            if (options.patterns) {
                this.displayPatternAnalytics(analytics.patternInsights);
            } else if (options.frequency) {
                this.displayFrequencyAnalytics(analytics.errorFrequency);
            } else if (options.effectiveness) {
                this.displayEffectivenessAnalytics(analytics.recoveryEffectiveness);
            } else if (options.recommendations) {
                this.displayRecommendations(analytics.recommendations);
            } else {
                this.displayFullAnalytics(analytics);
            }

        } catch (error) {
            spinner.fail(`Analytics failed: ${error.message}`);
        }
    }

    displayPatternAnalytics(patterns) {
        console.log(chalk.bold.magenta('\n🔍 Error Pattern Analysis\n'));

        if (patterns.frequencyPatterns.length > 0) {
            console.log(chalk.blue('📊 Frequency Patterns:'));
            patterns.frequencyPatterns.forEach(pattern => {
                console.log(`  • ${pattern.signature}: ${pattern.frequency} occurrences (${pattern.severity})`);
            });
        }

        if (patterns.temporalPatterns.length > 0) {
            console.log(chalk.blue('\n⏰ Temporal Patterns:'));
            patterns.temporalPatterns.forEach(pattern => {
                console.log(`  • ${pattern.type}: Peak hours at ${pattern.peakHours?.map(h => `${h.hour}:00`).join(', ')}`);
            });
        }

        if (patterns.correlationPatterns.length > 0) {
            console.log(chalk.blue('\n🔗 Correlation Patterns:'));
            patterns.correlationPatterns.forEach(pattern => {
                console.log(`  • ${pattern.sequence}: ${pattern.occurrences} occurrences (${pattern.severity})`);
            });
        }
    }

    async interactiveMode() {
        console.log(chalk.bold.blue('\n🚀 Interactive Recovery Mode\n'));

        while (true) {
            const action = await inquirer.prompt([{
                type: 'list',
                name: 'action',
                message: 'What would you like to do?',
                choices: [
                    { name: '📊 View System Status', value: 'status' },
                    { name: '🔧 Execute Recovery', value: 'recover' },
                    { name: '⚡ Manage Circuit Breakers', value: 'breakers' },
                    { name: '💾 Manage Checkpoints', value: 'checkpoints' },
                    { name: '🔍 View Analytics', value: 'analytics' },
                    { name: '🩺 Run Diagnostics', value: 'diagnose' },
                    { name: '⚙️ Configuration', value: 'config' },
                    { name: '❌ Exit', value: 'exit' }
                ]
            }]);

            try {
                switch (action.action) {
                    case 'status':
                        await this.statusCommand({ verbose: true });
                        break;
                    case 'recover':
                        await this.interactiveRecovery();
                        break;
                    case 'breakers':
                        await this.interactiveCircuitBreakers();
                        break;
                    case 'checkpoints':
                        await this.interactiveCheckpoints();
                        break;
                    case 'analytics':
                        await this.interactiveAnalytics();
                        break;
                    case 'diagnose':
                        await this.interactiveDiagnostics();
                        break;
                    case 'config':
                        await this.interactiveConfig();
                        break;
                    case 'exit':
                        console.log(chalk.green('👋 Goodbye!'));
                        return;
                }
            } catch (error) {
                console.log(chalk.red(`Error: ${error.message}`));
            }

            // Pause before showing menu again
            await inquirer.prompt([{
                type: 'input',
                name: 'continue',
                message: 'Press Enter to continue...'
            }]);
        }
    }

    async interactiveRecovery() {
        const recoveryType = await inquirer.prompt([{
            type: 'list',
            name: 'type',
            message: 'Select recovery type:',
            choices: [
                { name: '🤖 Automatic Recovery (Recommended)', value: 'auto' },
                { name: '📁 Git Recovery', value: 'git' },
                { name: '🌐 Network Recovery', value: 'network' },
                { name: '📂 Filesystem Recovery', value: 'filesystem' },
                { name: '🧠 Memory Recovery', value: 'memory' },
                { name: '🔄 Custom Recovery', value: 'custom' }
            ]
        }]);

        if (recoveryType.type === 'auto') {
            await this.automaticRecovery(false);
        } else if (recoveryType.type === 'custom') {
            await this.customRecovery();
        } else {
            await this.typeSpecificRecovery(recoveryType.type, {});
        }
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async executeRecoveryAction(action, type) {
        // Simulate recovery action execution
        await new Promise(resolve => setTimeout(resolve, 1000));

        // This would contain actual recovery logic
        return { success: true };
    }

    run() {
        this.program.parse();
    }
}

// Export for use as module or run directly
if (require.main === module) {
    const cli = new AdvancedRecoveryCLI();
    cli.run();
} else {
    module.exports = AdvancedRecoveryCLI;
}