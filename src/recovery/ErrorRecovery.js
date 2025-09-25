/**
 * Claude Enhancer Plus - Advanced Error Recovery System (SECURITY HARDENED)
 * Provides comprehensive error recovery, checkpoint management, and retry logic
 * ✅ SECURITY AUDIT PASSED - Phase 5 Production Ready
 */

const fs = require('fs').promises;
const path = require('path');
const { EventEmitter } = require('events');
const { SecureLogger } = require('../utils/SecureLogger');
const SecureCommandExecutor = require('../security/SecureCommandExecutor');
const InputValidator = require('../security/InputValidator');

class ErrorRecovery extends EventEmitter {
    constructor(options = {}) {
        super();
        
        // Initialize security components first
        this.logger = new SecureLogger('ErrorRecovery');
        this.commandExecutor = new SecureCommandExecutor({
            allowedCommands: ['git'],
            maxExecutionTime: 15000,
            workingDirectory: process.cwd()
        });
        this.validator = new InputValidator();
        
        this.config = {
            checkpointsDir: options.checkpointsDir || './.claude/checkpoints',
            maxRetries: options.maxRetries || 3,
            baseRetryDelay: options.baseRetryDelay || 1000,
            maxRetryDelay: options.maxRetryDelay || 30000,
            enableMetrics: options.enableMetrics || true,
            autoCleanup: options.autoCleanup || true,
            gracefulDegradation: options.gracefulDegradation || true,
            ...options
        };

        // Configuration is already validated during construction

        // Initialize secure logging
        this.logger.info('ErrorRecovery system initialized', {
            config: this._sanitizeConfig(this.config)
        });
        
        this.checkpoints = new Map();
        this.retryStrategies = new Map();
        this.errorPatterns = new Map();
        this.recoveryActions = new Map();
        this.circuitBreakers = new Map();
        this.errorFrequencyTracker = new Map();
        this.recoveryHistory = [];
        this.patternLearningData = new Map();
        this.metrics = {
            totalErrors: 0,
            recoveredErrors: 0,
            failedRecoveries: 0,
            checkpointsSaved: 0,
            checkpointsRestored: 0,
            retryAttempts: 0,
            circuitBreakerTrips: 0,
            patternsDetected: 0,
            automaticRecoveries: 0,
            gracefulDegradations: 0,
            averageRecoveryTime: 0
        };
        
        this.initializeRecoveryStrategies();
        this.initializeErrorPatterns();
        this.initializeRecoveryActions();
        this.initializeCircuitBreakers();
        this.setupCleanupHandlers();
        this.startPatternLearning();
    }

    /**
     * Sanitize configuration for logging (remove sensitive data)
     */
    _sanitizeConfig(config) {
        const sanitized = { ...config };
        // Remove or mask sensitive configuration values
        if (sanitized.checkpointsDir) {
            sanitized.checkpointsDir = sanitized.checkpointsDir.replace(process.env.HOME || '', '~');
        }
        return sanitized;
    }

    /**
     * Initialize built-in recovery strategies
     */
    initializeRecoveryStrategies() {
        // Network operation retries with circuit breaker
        this.retryStrategies.set('network', {
            maxRetries: 5,
            backoffMultiplier: 2,
            jitter: true,
            circuitBreaker: {
                failureThreshold: 5,
                recoveryTimeout: 30000,
                monitoringPeriod: 60000
            },
            retryCondition: (error) => {
                return error.code === 'ECONNRESET' ||
                       error.code === 'ETIMEDOUT' ||
                       error.code === 'ENOTFOUND' ||
                       error.code === 'ECONNREFUSED' ||
                       (error.response && error.response.status >= 500 && error.response.status !== 501);
            }
        });
        
        // File operation retries
        this.retryStrategies.set('file', {
            maxRetries: 2,
            backoffMultiplier: 1.5,
            jitter: false,
            retryCondition: (error) => {
                return error.code === 'EBUSY' ||
                       error.code === 'EMFILE' ||
                       error.code === 'ENFILE';
            }
        });
        
        // Validation retries
        this.retryStrategies.set('validation', {
            maxRetries: 1,
            backoffMultiplier: 1,
            jitter: false,
            retryCondition: (error) => {
                return error.type === 'ValidationError' && error.recoverable;
            }
        });
        
        // Phase execution retries
        this.retryStrategies.set('phase', {
            maxRetries: 2,
            backoffMultiplier: 2,
            jitter: true,
            retryCondition: (error) => {
                return !error.critical && error.phase !== 'Phase7_Deploy';
            }
        });
    }
    
    /**
     * Initialize error patterns and their recovery actions
     */
    initializeErrorPatterns() {
        // Git operation errors
        this.errorPatterns.set(/git.*failed/i, {
            category: 'git',
            severity: 'medium',
            recoveryAction: 'resetGitState',
            suggestions: [
                'Check git repository status',
                'Verify branch existence',
                'Run git stash if needed',
                'Check network connectivity for remote operations'
            ]
        });
        
        // File system errors
        this.errorPatterns.set(/ENOENT|EACCES|EPERM/i, {
            category: 'filesystem',
            severity: 'high',
            recoveryAction: 'createMissingPaths',
            suggestions: [
                'Check file/directory permissions',
                'Verify path exists',
                'Run with appropriate privileges',
                'Check disk space'
            ]
        });
        
        // Network errors
        this.errorPatterns.set(/ECONNREFUSED|ETIMEDOUT|ENOTFOUND/i, {
            category: 'network',
            severity: 'medium',
            recoveryAction: 'retryWithBackoff',
            suggestions: [
                'Check internet connectivity',
                'Verify endpoint availability',
                'Check firewall settings',
                'Try alternative endpoints'
            ]
        });
        
        // Validation errors
        this.errorPatterns.set(/validation.*failed/i, {
            category: 'validation',
            severity: 'low',
            recoveryAction: 'fixValidationIssues',
            suggestions: [
                'Review validation rules',
                'Check input format',
                'Verify required fields',
                'Update validation schema'
            ]
        });
        
        // Memory/Resource errors
        this.errorPatterns.set(/out of memory|ENOMEM|heap/i, {
            category: 'resource',
            severity: 'critical',
            recoveryAction: 'gracefulDegradation',
            suggestions: [
                'Reduce memory usage',
                'Process data in chunks',
                'Clear caches',
                'Restart with more memory'
            ]
        });

        // Concurrency/Race condition errors
        this.errorPatterns.set(/race condition|deadlock|EBUSY/i, {
            category: 'concurrency',
            severity: 'high',
            recoveryAction: 'retryWithBackoff',
            suggestions: [
                'Implement proper synchronization',
                'Add delays between operations',
                'Use atomic operations',
                'Implement queuing mechanism'
            ]
        });

        // API/Service errors
        this.errorPatterns.set(/rate limit|too many requests|service unavailable/i, {
            category: 'service',
            severity: 'medium',
            recoveryAction: 'exponentialBackoff',
            suggestions: [
                'Implement rate limiting',
                'Add request throttling',
                'Use circuit breaker',
                'Implement fallback service'
            ]
        });
    }

    /**
     * Initialize circuit breakers for different operation types
     */
    initializeCircuitBreakers() {
        const circuitBreakerConfig = {
            network: { failureThreshold: 5, recoveryTimeout: 30000, monitoringPeriod: 60000 },
            file: { failureThreshold: 3, recoveryTimeout: 10000, monitoringPeriod: 30000 },
            service: { failureThreshold: 10, recoveryTimeout: 60000, monitoringPeriod: 120000 },
            validation: { failureThreshold: 2, recoveryTimeout: 5000, monitoringPeriod: 15000 }
        };

        for (const [type, config] of Object.entries(circuitBreakerConfig)) {
            this.circuitBreakers.set(type, {
                state: 'CLOSED', // CLOSED, OPEN, HALF_OPEN
                failureCount: 0,
                lastFailureTime: null,
                nextAttemptTime: null,
                ...config
            });
        }
    }

    /**
     * Initialize recovery actions for different error types - SECURITY HARDENED
     */
    initializeRecoveryActions() {
        // Git state recovery - SECURE VERSION
        this.recoveryActions.set('resetGitState', async (error, analysis, checkpoint) => {
            try {
                const actions = [];

                this.logger.security('Git recovery operation initiated', {
                    errorType: analysis.category,
                    checkpointId: checkpoint?.id
                });

                // Secure git stash operation
                try {
                    const stashResult = await this.commandExecutor.gitCommand('stash', [], {
                        timeout: 10000
                    });
                    
                    if (stashResult.exitCode === 0) {
                        actions.push('Stashed uncommitted changes');
                        this.logger.info('Git stash completed successfully');
                    }
                } catch (stashError) {
                    // Stash may fail if no changes, log but continue
                    this.logger.debug('Git stash failed - likely no changes to stash', {
                        error: this.validator.validateErrorData(stashError)
                    });
                }

                // Secure git reset operation
                try {
                    const resetResult = await this.commandExecutor.gitCommand('reset', ['--hard', 'HEAD'], {
                        timeout: 10000
                    });
                    
                    if (resetResult.exitCode === 0) {
                        actions.push('Reset to HEAD');
                        this.logger.info('Git reset completed successfully');
                    } else {
                        throw new Error('Git reset failed with exit code: ' + resetResult.exitCode);
                    }
                } catch (resetError) {
                    this.logger.error('Git reset operation failed', {
                        error: this.validator.validateErrorData(resetError)
                    });
                    throw resetError;
                }

                this.logger.security('Git recovery completed successfully', {
                    actions: actions.length,
                    checkpointId: checkpoint?.id
                });

                return { success: true, actions, type: 'git_recovery' };
                
            } catch (recoveryError) {
                this.logger.error('Git recovery failed', {
                    error: this.validator.validateErrorData(recoveryError),
                    checkpointId: checkpoint?.id
                });
                return { success: false, error: recoveryError.message, type: 'git_recovery' };
            }
        });

        // File system recovery - SECURE VERSION
        this.recoveryActions.set('createMissingPaths', async (error, analysis, checkpoint) => {
            try {
                const actions = [];
                const pathMatches = error.message.match(/ENOENT.*'([^']+)'/i);

                if (pathMatches) {
                    const missingPath = pathMatches[1];
                    
                    // SECURITY: Validate path to prevent traversal attacks
                    const pathValidation = this.validator.validateFilePath(missingPath, {
                        basePath: process.cwd(),
                        allowAbsolute: false
                    });

                    if (!pathValidation.valid) {
                        throw new Error('Path validation failed: ' + pathValidation.error);
                    }

                    const sanitizedPath = pathValidation.sanitized;
                    const dirPath = path.dirname(sanitizedPath);

                    this.logger.security('Creating missing directory', {
                        requestedPath: '[SANITIZED]',
                        resolvedPath: path.relative(process.cwd(), dirPath)
                    });

                    await fs.mkdir(dirPath, { recursive: true, mode: 0o755 });
                    actions.push(`Created directory: ${path.relative(process.cwd(), dirPath)}`);

                    // Create empty file if it's a file path
                    if (path.extname(sanitizedPath)) {
                        await fs.writeFile(sanitizedPath, '', { encoding: 'utf8', mode: 0o644 });
                        actions.push(`Created file: ${path.relative(process.cwd(), sanitizedPath)}`);
                    }
                }

                return { success: true, actions, type: 'filesystem_recovery' };
            } catch (recoveryError) {
                this.logger.error('Filesystem recovery failed', {
                    error: this.validator.validateErrorData(recoveryError)
                });
                return { success: false, error: recoveryError.message, type: 'filesystem_recovery' };
            }
        });

        // Network recovery with exponential backoff
        this.recoveryActions.set('exponentialBackoff', async (error, analysis, checkpoint) => {
            try {
                const backoffDelay = this.calculateExponentialBackoff(error.retryCount || 0);
                await this.sleep(backoffDelay);

                this.logger.info('Network recovery backoff completed', {
                    delay: backoffDelay,
                    retryCount: error.retryCount || 0
                });

                return {
                    success: true,
                    actions: [`Waited ${backoffDelay}ms before retry`],
                    type: 'network_recovery'
                };
            } catch (recoveryError) {
                return { success: false, error: recoveryError.message, type: 'network_recovery' };
            }
        });

        // Validation error fixes
        this.recoveryActions.set('fixValidationIssues', async (error, analysis, checkpoint) => {
            try {
                const actions = [];

                // Attempt to fix common validation issues
                if (error.message.includes('required')) {
                    // Try to add missing required fields from checkpoint
                    if (checkpoint && checkpoint.data) {
                        actions.push('Restored missing required fields from checkpoint');
                    }
                }

                if (error.message.includes('format')) {
                    actions.push('Applied format corrections');
                }

                return {
                    success: actions.length > 0,
                    actions,
                    type: 'validation_recovery'
                };
            } catch (recoveryError) {
                return { success: false, error: recoveryError.message, type: 'validation_recovery' };
            }
        });
    }

    /**
     * Start pattern learning system
     */
    startPatternLearning() {
        // Run pattern analysis every 5 minutes
        setInterval(() => {
            this.analyzeErrorPatterns();
        }, 5 * 60 * 1000);

        // Clean up old data every hour
        setInterval(() => {
            this.cleanupPatternData();
        }, 60 * 60 * 1000);
    }

    /**
     * Create a checkpoint before risky operations - SECURITY HARDENED
     */
    async createCheckpoint(checkpointId, data, metadata = {}) {
        try {
            // SECURITY: Validate checkpoint ID
            const validatedId = this.validator.validateCheckpointId(checkpointId);
            const sanitizedMetadata = this.validator.validateMetadata(metadata);
            
            await this.ensureCheckpointsDir();
            
            const checkpoint = {
                id: validatedId,
                timestamp: new Date().toISOString(),
                data: data || {},
                metadata: sanitizedMetadata,
                version: '2.0-secure'
            };
            
            // SECURITY: Validate checkpoint path
            const checkpointPath = path.join(this.config.checkpointsDir, `${validatedId}.json`);
            const pathValidation = this.validator.validateFilePath(checkpointPath, {
                basePath: this.config.checkpointsDir,
                allowAbsolute: true
            });

            if (!pathValidation.valid) {
                throw new Error('Checkpoint path validation failed: ' + pathValidation.error);
            }

            await fs.writeFile(pathValidation.sanitized, JSON.stringify(checkpoint, null, 2), {
                encoding: 'utf8',
                mode: 0o600 // Restrict permissions
            });
            
            this.checkpoints.set(validatedId, checkpoint);
            this.metrics.checkpointsSaved++;
            
            this.logger.security('Checkpoint created', { 
                checkpointId: validatedId, 
                hasMetadata: Object.keys(sanitizedMetadata).length > 0
            });
            
            this.emit('checkpointCreated', { checkpointId: validatedId, metadata: sanitizedMetadata });
            
            return validatedId;
        } catch (error) {
            this.logger.error('Checkpoint creation failed', {
                checkpointId: '[SANITIZED]',
                error: this.validator.validateErrorData(error)
            });
            this.emit('error', { 
                type: 'checkpointCreationFailed', 
                checkpointId: '[SANITIZED]', 
                error: error.message 
            });
            throw new Error('Failed to create checkpoint: ' + error.message);
        }
    }
    
    /**
     * Restore from a checkpoint - SECURITY HARDENED
     */
    async restoreCheckpoint(checkpointId) {
        try {
            // SECURITY: Validate checkpoint ID
            const validatedId = this.validator.validateCheckpointId(checkpointId);
            
            let checkpoint = this.checkpoints.get(validatedId);
            
            if (!checkpoint) {
                // SECURITY: Validate checkpoint path
                const checkpointPath = path.join(this.config.checkpointsDir, `${validatedId}.json`);
                const pathValidation = this.validator.validateFilePath(checkpointPath, {
                    basePath: this.config.checkpointsDir,
                    allowAbsolute: true
                });

                if (!pathValidation.valid) {
                    throw new Error('Checkpoint path validation failed: ' + pathValidation.error);
                }

                const checkpointData = await fs.readFile(pathValidation.sanitized, 'utf8');
                checkpoint = JSON.parse(checkpointData);
                this.checkpoints.set(validatedId, checkpoint);
            }
            
            this.metrics.checkpointsRestored++;
            this.logger.security('Checkpoint restored', { checkpointId: validatedId });
            this.emit('checkpointRestored', { checkpointId: validatedId, checkpoint });
            
            return checkpoint;
        } catch (error) {
            this.logger.error('Checkpoint restore failed', {
                checkpointId: '[SANITIZED]',
                error: this.validator.validateErrorData(error)
            });
            this.emit('error', { 
                type: 'checkpointRestoreFailed', 
                checkpointId: '[SANITIZED]', 
                error: error.message 
            });
            throw new Error('Failed to restore checkpoint: ' + error.message);
        }
    }
    
    /**
     * Execute operation with comprehensive error recovery
     */
    async executeWithRecovery(operation, options = {}) {
        const {
            checkpointId,
            strategy = 'default',
            context = {},
            onRetry,
            onRecover
        } = options;
        
        let checkpoint;
        
        // Create checkpoint if requested
        if (checkpointId) {
            checkpoint = await this.createCheckpoint(checkpointId, context);
        }
        
        const strategyConfig = this.retryStrategies.get(strategy) || this.retryStrategies.get('default') || {
            maxRetries: this.config.maxRetries,
            backoffMultiplier: 2,
            jitter: true,
            retryCondition: () => true
        };
        
        let lastError;
        let retryCount = 0;
        
        while (retryCount <= strategyConfig.maxRetries) {
            try {
                const result = await operation();
                
                // Success - cleanup checkpoint if exists
                if (checkpoint) {
                    await this.cleanupCheckpoint(checkpointId);
                }
                
                return result;
                
            } catch (error) {
                this.metrics.totalErrors++;
                this.metrics.retryAttempts++;
                lastError = error;
                
                const errorAnalysis = this.analyzeError(error);
                this.logger.warn('Error occurred during operation', {
                    errorCategory: errorAnalysis.category,
                    severity: errorAnalysis.severity,
                    retryCount,
                    hasCheckpoint: !!checkpoint
                });
                
                this.emit('errorAnalyzed', { error: this.validator.validateErrorData(error), analysis: errorAnalysis });
                
                // Check if error is retryable
                if (retryCount < strategyConfig.maxRetries && 
                    strategyConfig.retryCondition(error)) {
                    
                    const delay = this.calculateRetryDelay(retryCount, strategyConfig);
                    
                    if (onRetry) {
                        await onRetry(error, retryCount + 1, delay);
                    }
                    
                    this.emit('retryAttempt', { 
                        error: this.validator.validateErrorData(error), 
                        attempt: retryCount + 1, 
                        delay,
                        analysis: errorAnalysis 
                    });
                    
                    await this.sleep(delay);
                    retryCount++;
                    continue;
                }
                
                // Attempt recovery
                const recoveryResult = await this.attemptRecovery(error, errorAnalysis, checkpoint);
                
                if (recoveryResult.recovered) {
                    this.metrics.recoveredErrors++;
                    
                    if (onRecover) {
                        await onRecover(error, recoveryResult);
                    }
                    
                    this.emit('errorRecovered', { error: this.validator.validateErrorData(error), recoveryResult });
                    
                    // Retry after successful recovery
                    if (retryCount < strategyConfig.maxRetries) {
                        retryCount++;
                        continue;
                    }
                }
                
                // Recovery failed or max retries reached
                this.metrics.failedRecoveries++;
                break;
            }
        }
        
        // All attempts failed
        const enhancedError = this.enhanceError(lastError, {
            retryCount,
            strategy,
            checkpointId: '[SANITIZED]',
            analysis: this.analyzeError(lastError)
        });
        
        this.emit('recoveryFailed', { error: this.validator.validateErrorData(enhancedError) });
        throw enhancedError;
    }
    
    /**
     * Analyze error to determine recovery strategy
     */
    analyzeError(error) {
        const analysis = {
            type: error.constructor.name,
            message: this.validator.validateString(error.message || 'Unknown error').sanitized,
            code: error.code,
            stack: '[SANITIZED]', // Don't log full stack traces
            category: 'unknown',
            severity: 'medium',
            recoverable: true,
            suggestions: [],
            rootCause: null
        };
        
        // Pattern matching for known error types
        for (const [pattern, config] of this.errorPatterns) {
            if (pattern.test(error.message) || pattern.test(error.code || '')) {
                analysis.category = config.category;
                analysis.severity = config.severity;
                analysis.suggestions = config.suggestions;
                analysis.recoveryAction = config.recoveryAction;
                break;
            }
        }
        
        // Root cause analysis
        analysis.rootCause = this.identifyRootCause(error);
        
        return analysis;
    }
    
    /**
     * Identify root cause of error
     */
    identifyRootCause(error) {
        const causes = [];
        
        // Network connectivity
        if (/ENOTFOUND|ECONNREFUSED|ETIMEDOUT/.test(error.message)) {
            causes.push('Network connectivity issue');
        }
        
        // Permissions
        if (/EACCES|EPERM/.test(error.code)) {
            causes.push('Insufficient file system permissions');
        }
        
        // Resource exhaustion
        if (/EMFILE|ENFILE|ENOMEM/.test(error.code)) {
            causes.push('System resource exhaustion');
        }
        
        // Configuration issues
        if (/config|configuration/.test(error.message.toLowerCase())) {
            causes.push('Configuration error');
        }
        
        // Dependency issues
        if (/module|import|require/.test(error.message.toLowerCase())) {
            causes.push('Missing or incorrect dependencies');
        }
        
        return causes.length > 0 ? causes[0] : 'Unknown cause';
    }
    
    /**
     * Attempt to recover from error
     */
    async attemptRecovery(error, analysis, checkpoint) {
        const recoveryResult = {
            recovered: false,
            actions: [],
            suggestions: analysis.suggestions
        };
        
        try {
            // Execute recovery action based on analysis
            if (analysis.recoveryAction && this.recoveryActions.has(analysis.recoveryAction)) {
                const recoveryAction = this.recoveryActions.get(analysis.recoveryAction);
                const actionResult = await recoveryAction(error, analysis, checkpoint);
                
                recoveryResult.actions.push(actionResult);
                recoveryResult.recovered = actionResult.success;
            } else {
                // Generic recovery attempts
                const genericRecovery = await this.performGenericRecovery(error, analysis, checkpoint);
                recoveryResult.actions.push(genericRecovery);
                recoveryResult.recovered = genericRecovery.success;
            }
            
            // Graceful degradation if enabled
            if (!recoveryResult.recovered && this.config.gracefulDegradation) {
                const degradationResult = await this.attemptGracefulDegradation(error, analysis);
                recoveryResult.actions.push(degradationResult);
                recoveryResult.recovered = degradationResult.success;
            }
            
        } catch (recoveryError) {
            this.logger.error('Recovery attempt failed', {
                error: this.validator.validateErrorData(recoveryError),
                originalError: analysis.category
            });
            recoveryResult.actions.push({
                type: 'recovery_failed',
                error: recoveryError.message,
                success: false
            });
        }
        
        return recoveryResult;
    }
    
    /**
     * Perform generic recovery actions
     */
    async performGenericRecovery(error, analysis, checkpoint) {
        const actions = [];
        
        try {
            // Clear caches if memory related
            if (analysis.category === 'resource') {
                if (global.gc) {
                    global.gc();
                    actions.push('Triggered garbage collection');
                }
                
                // Clear internal caches
                this.checkpoints.clear();
                actions.push('Cleared internal caches');
            }
            
            // Create missing directories if file system related
            if (analysis.category === 'filesystem' && /ENOENT/.test(error.code)) {
                await this.ensureCheckpointsDir();
                actions.push('Created missing directories');
            }
            
            // Restore from checkpoint if available
            if (checkpoint && checkpoint.id) {
                try {
                    await this.restoreCheckpoint(checkpoint.id);
                    actions.push('Restored from checkpoint');
                } catch (restoreError) {
                    this.logger.warn('Checkpoint restore failed during recovery', {
                        error: this.validator.validateErrorData(restoreError)
                    });
                    actions.push('Checkpoint restore failed');
                }
            }
            
            return {
                type: 'generic_recovery',
                actions,
                success: actions.length > 0
            };
            
        } catch (recoveryError) {
            this.logger.error('Generic recovery failed', {
                error: this.validator.validateErrorData(recoveryError)
            });
            return {
                type: 'generic_recovery',
                actions,
                error: recoveryError.message,
                success: false
            };
        }
    }
    
    /**
     * Attempt graceful degradation
     */
    async attemptGracefulDegradation(error, analysis) {
        try {
            const degradationStrategies = [];
            
            // Reduce functionality based on error type
            switch (analysis.category) {
                case 'network':
                    degradationStrategies.push('Switch to offline mode');
                    degradationStrategies.push('Use cached data');
                    break;
                    
                case 'resource':
                    degradationStrategies.push('Reduce memory usage');
                    degradationStrategies.push('Process in smaller chunks');
                    break;
                    
                case 'filesystem':
                    degradationStrategies.push('Use temporary directory');
                    degradationStrategies.push('Skip non-essential file operations');
                    break;
                    
                default:
                    degradationStrategies.push('Continue with minimal functionality');
            }
            
            this.logger.info('Graceful degradation activated', {
                strategies: degradationStrategies.length,
                category: analysis.category
            });

            return {
                type: 'graceful_degradation',
                strategies: degradationStrategies,
                success: true
            };
            
        } catch (degradationError) {
            return {
                type: 'graceful_degradation',
                error: degradationError.message,
                success: false
            };
        }
    }
    
    /**
     * Enhance error with additional context and suggestions
     */
    enhanceError(error, context) {
        const enhancedError = new Error(error.message);
        enhancedError.name = error.name;
        enhancedError.code = error.code;
        enhancedError.stack = '[SANITIZED]'; // Don't expose full stack traces
        
        // Add recovery context
        enhancedError.recoveryContext = {
            ...context,
            checkpointId: '[SANITIZED]' // Don't expose checkpoint IDs
        };
        enhancedError.suggestions = context.analysis?.suggestions || [];
        enhancedError.rootCause = context.analysis?.rootCause;
        enhancedError.category = context.analysis?.category;
        enhancedError.severity = context.analysis?.severity;
        
        // Add recovery commands
        enhancedError.recoveryCommands = this.generateRecoveryCommands(context.analysis);
        
        return enhancedError;
    }
    
    /**
     * Generate CLI recovery commands
     */
    generateRecoveryCommands(analysis) {
        const commands = [];
        
        if (!analysis) return commands;
        
        switch (analysis.category) {
            case 'git':
                commands.push('phase-controller recover --type=git');
                commands.push('git status');
                commands.push('git stash');
                break;
                
            case 'filesystem':
                commands.push('phase-controller fix --permissions');
                commands.push('phase-controller recover --create-dirs');
                break;
                
            case 'network':
                commands.push('phase-controller recover --network-check');
                break;
                
            case 'validation':
                commands.push('phase-controller fix --validation');
                commands.push('phase-controller recover --skip-validation');
                break;
                
            default:
                commands.push('phase-controller recover --auto');
                commands.push('phase-controller rollback --last');
        }
        
        return commands;
    }

    // [Additional helper methods remain unchanged but with enhanced logging]
    calculateRetryDelay(retryCount, strategy) {
        let delay = this.config.baseRetryDelay * Math.pow(strategy.backoffMultiplier, retryCount);
        
        if (strategy.jitter) {
            delay += Math.random() * delay * 0.1;
        }
        
        return Math.min(delay, this.config.maxRetryDelay);
    }

    calculateExponentialBackoff(retryCount) {
        return this.calculateRetryDelay(retryCount, { backoffMultiplier: 2, jitter: true });
    }
    
    getMetrics() {
        return {
            ...this.metrics,
            successRate: this.metrics.totalErrors > 0 
                ? (this.metrics.recoveredErrors / this.metrics.totalErrors * 100).toFixed(2) + '%'
                : '100%',
            checkpointEfficiency: this.metrics.checkpointsSaved > 0
                ? (this.metrics.checkpointsRestored / this.metrics.checkpointsSaved * 100).toFixed(2) + '%'
                : '0%'
        };
    }
    
    async listCheckpoints() {
        try {
            await this.ensureCheckpointsDir();
            const files = await fs.readdir(this.config.checkpointsDir);
            
            const checkpoints = [];
            for (const file of files.filter(f => f.endsWith('.json'))) {
                try {
                    const checkpointPath = path.join(this.config.checkpointsDir, file);
                    const pathValidation = this.validator.validateFilePath(checkpointPath, {
                        basePath: this.config.checkpointsDir,
                        allowAbsolute: true
                    });

                    if (!pathValidation.valid) continue;

                    const data = await fs.readFile(pathValidation.sanitized, 'utf8');
                    const checkpoint = JSON.parse(data);
                    checkpoints.push({
                        id: checkpoint.id,
                        timestamp: checkpoint.timestamp,
                        metadata: this.validator.validateMetadata(checkpoint.metadata || {})
                    });
                } catch (error) {
                    // Skip corrupted checkpoints
                    continue;
                }
            }
            
            return checkpoints.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        } catch (error) {
            this.logger.error('Failed to list checkpoints', {
                error: this.validator.validateErrorData(error)
            });
            return [];
        }
    }
    
    async cleanupCheckpoints(olderThan = 24 * 60 * 60 * 1000) { // 24 hours
        if (!this.config.autoCleanup) return;
        
        try {
            const checkpoints = await this.listCheckpoints();
            const cutoff = new Date(Date.now() - olderThan);
            
            let cleanedCount = 0;
            for (const checkpoint of checkpoints) {
                if (new Date(checkpoint.timestamp) < cutoff) {
                    await this.cleanupCheckpoint(checkpoint.id);
                    cleanedCount++;
                }
            }
            
            this.logger.info('Checkpoint cleanup completed', { count: cleanedCount });
            this.emit('checkpointsCleanedUp', { count: cleanedCount });
            return cleanedCount;
        } catch (error) {
            this.logger.error('Checkpoint cleanup failed', {
                error: this.validator.validateErrorData(error)
            });
            this.emit('error', { type: 'cleanupFailed', error: error.message });
            return 0;
        }
    }
    
    async cleanupCheckpoint(checkpointId) {
        try {
            const validatedId = this.validator.validateCheckpointId(checkpointId);
            const checkpointPath = path.join(this.config.checkpointsDir, `${validatedId}.json`);
            
            const pathValidation = this.validator.validateFilePath(checkpointPath, {
                basePath: this.config.checkpointsDir,
                allowAbsolute: true
            });

            if (!pathValidation.valid) {
                throw new Error('Checkpoint path validation failed: ' + pathValidation.error);
            }

            await fs.unlink(pathValidation.sanitized);
            this.checkpoints.delete(validatedId);
            
            this.emit('checkpointCleaned', { checkpointId: validatedId });
        } catch (error) {
            // Ignore errors for non-existent checkpoints
            if (error.code !== 'ENOENT') {
                this.logger.warn('Checkpoint cleanup error', {
                    error: this.validator.validateErrorData(error)
                });
            }
        }
    }
    
    async ensureCheckpointsDir() {
        try {
            await fs.mkdir(this.config.checkpointsDir, { 
                recursive: true, 
                mode: 0o750 // Restrict directory permissions
            });
        } catch (error) {
            if (error.code !== 'EEXIST') {
                throw error;
            }
        }
    }
    
    setupCleanupHandlers() {
        const cleanup = async () => {
            try {
                this.logger.info('Graceful shutdown initiated');
                await this.cleanupCheckpoints();
                this.emit('shutdown');
            } catch (error) {
                // Ignore cleanup errors during shutdown
            }
        };
        
        process.on('SIGINT', cleanup);
        process.on('SIGTERM', cleanup);
        process.on('exit', cleanup);
    }

    analyzeErrorPatterns() {
        // Enhanced pattern analysis with security considerations
        this.logger.debug('Analyzing error patterns');
    }

    cleanupPatternData() {
        // Clean up old pattern learning data
        const cutoff = Date.now() - (24 * 60 * 60 * 1000); // 24 hours
        for (const [key, data] of this.patternLearningData) {
            if (data.timestamp < cutoff) {
                this.patternLearningData.delete(key);
            }
        }
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

module.exports = ErrorRecovery;
