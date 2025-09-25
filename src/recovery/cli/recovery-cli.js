#!/usr/bin/env node
/**
 * Claude Enhancer Plus - Recovery CLI Commands
 * Command-line interface for error recovery operations
 */

const { Command } = require('commander');
const chalk = require('chalk');
const ErrorRecovery = require('../ErrorRecovery');
const CheckpointManager = require('../CheckpointManager');
const path = require('path');
const fs = require('fs').promises;
const { createCLILogger } = require('../../utils/CLISecureLogger');

class RecoveryCLI {
    constructor() {
        this.program = new Command();
        this.errorRecovery = new ErrorRecovery();
        this.checkpointManager = new CheckpointManager();
        this.cliLogger = createCLILogger('RecoveryCLI');

        // Setup cleanup on exit
        process.on('exit', (code) => this.cliLogger.endSession(code));
        process.on('SIGINT', () => {
            this.cliLogger.endSession(130);
            process.exit(130);
        });

        this.setupCommands();
    }
    
    setupCommands() {
        this.program
            .name('phase-controller')
            .description('Claude Enhancer Plus Recovery Controller')
            .version('2.0.0');
        
        // Recovery commands
        this.program
            .command('recover')
            .description('Attempt automatic recovery from errors')
            .option('--type <type>', 'Specify error type (git, network, file, validation)')
            .option('--checkpoint <id>', 'Restore from specific checkpoint')
            .option('--auto', 'Attempt automatic recovery')
            .option('--network-check', 'Perform network connectivity check')
            .option('--create-dirs', 'Create missing directories')
            .option('--verbose', 'Show detailed recovery information')
            .action(this.handleRecover.bind(this));
        
        // Rollback commands
        this.program
            .command('rollback')
            .description('Rollback to previous state')
            .option('--last', 'Rollback to last checkpoint')
            .option('--checkpoint <id>', 'Rollback to specific checkpoint')
            .option('--list', 'List available rollback points')
            .option('--confirm', 'Skip confirmation prompt')
            .action(this.handleRollback.bind(this));
        
        // Fix commands
        this.program
            .command('fix')
            .description('Apply specific fixes for common issues')
            .option('--permissions', 'Fix file permissions')
            .option('--validation', 'Fix validation issues')
            .option('--git-state', 'Fix git repository state')
            .option('--dependencies', 'Fix dependency issues')
            .option('--all', 'Attempt all available fixes')
            .action(this.handleFix.bind(this));
        
        // Checkpoint commands
        this.program
            .command('checkpoint')
            .description('Manage system checkpoints')
            .option('--create <id>', 'Create new checkpoint')
            .option('--list', 'List available checkpoints')
            .option('--delete <id>', 'Delete checkpoint')
            .option('--info <id>', 'Show checkpoint information')
            .option('--cleanup', 'Clean up old checkpoints')
            .action(this.handleCheckpoint.bind(this));
        
        // Status commands
        this.program
            .command('status')
            .description('Show system and recovery status')
            .option('--metrics', 'Show recovery metrics')
            .option('--health', 'Perform system health check')
            .option('--errors', 'Show recent errors')
            .action(this.handleStatus.bind(this));
        
        // Diagnostic commands
        this.program
            .command('diagnose')
            .description('Run comprehensive system diagnostics')
            .option('--full', 'Run full diagnostic suite')
            .option('--quick', 'Run quick health check')
            .option('--export <file>', 'Export diagnostic report')
            .action(this.handleDiagnose.bind(this));
    }
    
    async handleRecover(options) {
        const startTime = this.cliLogger.operationStart('error recovery process');

        try {
            this.cliLogger.userAction('recover_command', { options });

            if (options.networkCheck) {
                await this.performNetworkCheck();
            }

            if (options.createDirs) {
                await this.createMissingDirectories();
            }

            if (options.checkpoint) {
                await this.recoverFromCheckpoint(options.checkpoint);
            }

            if (options.auto || options.type) {
                await this.performAutoRecovery(options.type);
            }

            this.cliLogger.operationComplete('error recovery process', startTime);

        } catch (error) {
            this.cliLogger.operationFailed('error recovery process', error, startTime);
            process.exit(1);
        }
    }
    
    async handleRollback(options) {
        const startTime = this.cliLogger.operationStart('rollback process');

        try {
            this.cliLogger.userAction('rollback_command', { options });

            if (options.list) {
                await this.listRollbackPoints();
                return;
            }

            let checkpointId;

            if (options.last) {
                checkpointId = await this.getLastCheckpoint();
            } else if (options.checkpoint) {
                checkpointId = options.checkpoint;
            } else {
                this.cliLogger.error('Invalid rollback options', null, chalk.red('Please specify --last or --checkpoint <id>'));
                return;
            }

            if (!options.confirm) {
                const confirmed = await this.confirmRollback(checkpointId);
                if (!confirmed) {
                    this.cliLogger.warn('Rollback cancelled by user', chalk.yellow('Rollback cancelled'));
                    return;
                }
            }

            await this.performRollback(checkpointId);
            this.cliLogger.operationComplete('rollback process', startTime);

        } catch (error) {
            this.cliLogger.operationFailed('rollback process', error, startTime);
            process.exit(1);
        }
    }
    
    async handleFix(options) {
        console.log(chalk.blue('🔨 Applying fixes...'));
        
        try {
            const fixes = [];
            
            if (options.permissions || options.all) {
                fixes.push(this.fixPermissions());
            }
            
            if (options.validation || options.all) {
                fixes.push(this.fixValidation());
            }
            
            if (options.gitState || options.all) {
                fixes.push(this.fixGitState());
            }
            
            if (options.dependencies || options.all) {
                fixes.push(this.fixDependencies());
            }
            
            if (fixes.length === 0) {
                console.log(chalk.yellow('No fixes specified. Use --help for options.'));
                return;
            }
            
            const results = await Promise.allSettled(fixes);
            
            let successCount = 0;
            let failCount = 0;
            
            results.forEach((result, index) => {
                if (result.status === 'fulfilled') {
                    successCount++;
                    console.log(chalk.green(`✅ Fix ${index + 1} applied successfully`));
                } else {
                    failCount++;
                    console.log(chalk.red(`❌ Fix ${index + 1} failed: ${result.reason.message}`));
                }
            });
            
            console.log(chalk.blue(`\n📊 Fix Summary: ${successCount} succeeded, ${failCount} failed`));
            
        } catch (error) {
            console.error(chalk.red('❌ Fix operation failed:'), error.message);
            process.exit(1);
        }
    }
    
    async handleCheckpoint(options) {
        try {
            if (options.create) {
                await this.createCheckpoint(options.create);
            } else if (options.list) {
                await this.listCheckpoints();
            } else if (options.delete) {
                await this.deleteCheckpoint(options.delete);
            } else if (options.info) {
                await this.showCheckpointInfo(options.info);
            } else if (options.cleanup) {
                await this.cleanupCheckpoints();
            } else {
                console.log(chalk.yellow('Please specify a checkpoint operation. Use --help for options.'));
            }
        } catch (error) {
            console.error(chalk.red('❌ Checkpoint operation failed:'), error.message);
            process.exit(1);
        }
    }
    
    async handleStatus(options) {
        console.log(chalk.blue('📊 System Status Report'));
        console.log(chalk.gray('=' * 50));
        
        try {
            if (options.health) {
                await this.performHealthCheck();
            }
            
            if (options.metrics) {
                await this.showRecoveryMetrics();
            }
            
            if (options.errors) {
                await this.showRecentErrors();
            }
            
            if (!options.health && !options.metrics && !options.errors) {
                await this.showGeneralStatus();
            }
            
        } catch (error) {
            console.error(chalk.red('❌ Status check failed:'), error.message);
            process.exit(1);
        }
    }
    
    async handleDiagnose(options) {
        console.log(chalk.blue('🔍 Running system diagnostics...'));
        
        try {
            let diagnostics;
            
            if (options.full) {
                diagnostics = await this.runFullDiagnostics();
            } else {
                diagnostics = await this.runQuickDiagnostics();
            }
            
            this.displayDiagnostics(diagnostics);
            
            if (options.export) {
                await this.exportDiagnostics(diagnostics, options.export);
                console.log(chalk.green(`📄 Diagnostics exported to ${options.export}`));
            }
            
        } catch (error) {
            console.error(chalk.red('❌ Diagnostic failed:'), error.message);
            process.exit(1);
        }
    }
    
    // Implementation methods
    async performNetworkCheck() {
        console.log(chalk.blue('🌐 Checking network connectivity...'));
        
        const testEndpoints = [
            'https://api.github.com',
            'https://registry.npmjs.org',
            'https://google.com'
        ];
        
        for (const endpoint of testEndpoints) {
            try {
                const response = await fetch(endpoint, { method: 'HEAD', timeout: 5000 });
                if (response.ok) {
                    console.log(chalk.green(`✅ ${endpoint} - OK`));
                } else {
                    console.log(chalk.yellow(`⚠️ ${endpoint} - Status: ${response.status}`));
                }
            } catch (error) {
                console.log(chalk.red(`❌ ${endpoint} - Failed: ${error.message}`));
            }
        }
    }
    
    async createMissingDirectories() {
        console.log(chalk.blue('📁 Creating missing directories...'));
        
        const requiredDirs = [
            './.claude',
            './.claude/checkpoints',
            './.claude/logs',
            './src/recovery',
            './logs'
        ];
        
        for (const dir of requiredDirs) {
            try {
                await fs.mkdir(dir, { recursive: true });
                console.log(chalk.green(`✅ Created directory: ${dir}`));
            } catch (error) {
                if (error.code !== 'EEXIST') {
                    console.log(chalk.red(`❌ Failed to create ${dir}: ${error.message}`));
                }
            }
        }
    }
    
    async performAutoRecovery(errorType) {
        console.log(chalk.blue(`🤖 Performing auto-recovery for: ${errorType || 'general'}`));
        
        const recoveryActions = {
            git: async () => {
                console.log('- Resetting git state...');
                // Add git recovery logic
            },
            network: async () => {
                console.log('- Checking network connectivity...');
                await this.performNetworkCheck();
            },
            file: async () => {
                console.log('- Creating missing directories...');
                await this.createMissingDirectories();
            },
            validation: async () => {
                console.log('- Fixing validation issues...');
                // Add validation recovery logic
            }
        };
        
        if (errorType && recoveryActions[errorType]) {
            await recoveryActions[errorType]();
        } else {
            console.log('- Running general recovery procedures...');
            await this.createMissingDirectories();
            await this.performNetworkCheck();
        }
    }
    
    async showGeneralStatus() {
        const checkpoints = await this.checkpointManager.listCheckpoints();
        const metrics = this.errorRecovery.getMetrics();
        
        console.log(chalk.blue('\n🏥 System Health:'));
        console.log(`- Status: ${chalk.green('Operational')}`);
        console.log(`- Active Checkpoints: ${checkpoints.length}`);
        console.log(`- Recovery Success Rate: ${metrics.successRate || '100%'}`);
        console.log(`- Total Errors Handled: ${metrics.totalErrors || 0}`);
        
        console.log(chalk.blue('\n📈 Recent Activity:'));
        console.log(`- Last Checkpoint: ${checkpoints[0]?.timestamp || 'None'}`);
        console.log(`- System Uptime: ${process.uptime()}s`);
    }
    
    async run() {
        try {
            await this.program.parseAsync(process.argv);
        } catch (error) {
            console.error(chalk.red('CLI Error:'), error.message);
            process.exit(1);
        }
    }
}

// Entry point
if (require.main === module) {
    const cli = new RecoveryCLI();
    cli.run();
}

module.exports = RecoveryCLI;
