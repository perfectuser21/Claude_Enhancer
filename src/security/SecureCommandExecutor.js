/**
 * Secure Command Executor - Prevents command injection vulnerabilities
 * Validates and sanitizes all command execution for production safety
 */

const { spawn } = require('child_process');
const path = require('path');
const { SecureLogger } = require('../utils/SecureLogger');

class SecureCommandExecutor {
    constructor(options = {}) {
        this.config = {
            allowedCommands: options.allowedCommands || ['git', 'npm', 'node'],
            maxExecutionTime: options.maxExecutionTime || 30000,
            workingDirectory: options.workingDirectory || process.cwd(),
            enableLogging: options.enableLogging !== false,
            ...options
        };

        this.logger = new SecureLogger('SecureCommandExecutor');
        
        // Command whitelist with allowed arguments
        this.commandWhitelist = new Map([
            ['git', {
                allowed: true,
                safeArgs: ['status', 'stash', 'reset', 'add', 'commit', 'push', 'pull', 'branch', 'checkout', 'log', 'diff', 'rev-parse'],
                dangerousArgs: ['rm', 'clean', '--force', '--hard', '--amend'],
                maxArgs: 10
            }],
            ['npm', {
                allowed: true,
                safeArgs: ['install', 'test', 'run', 'audit', 'ls', 'outdated'],
                dangerousArgs: ['uninstall', 'publish', 'unpublish'],
                maxArgs: 5
            }],
            ['node', {
                allowed: true,
                safeArgs: ['-v', '--version', '-e'],
                dangerousArgs: ['-p', '--print'],
                maxArgs: 3
            }]
        ]);
    }

    /**
     * Execute command securely with validation and sanitization
     */
    async executeCommand(command, args = [], options = {}) {
        const executionId = this.generateExecutionId();
        
        try {
            // Input validation
            const validationResult = this.validateCommand(command, args);
            if (!validationResult.valid) {
                throw new Error(`Command validation failed: ${validationResult.reason}`);
            }

            // Sanitize command and arguments
            const sanitizedCommand = this.sanitizeCommand(command);
            const sanitizedArgs = this.sanitizeArguments(args);

            // Log security event
            this.logger.security('Command execution initiated', {
                executionId,
                command: sanitizedCommand,
                argCount: sanitizedArgs.length,
                workingDir: this.sanitizeWorkingDirectory(options.cwd || this.config.workingDirectory)
            });

            // Execute with security constraints
            const result = await this.secureSpawn(sanitizedCommand, sanitizedArgs, {
                ...options,
                cwd: this.validateWorkingDirectory(options.cwd || this.config.workingDirectory),
                timeout: Math.min(options.timeout || this.config.maxExecutionTime, this.config.maxExecutionTime),
                env: this.sanitizeEnvironment(options.env)
            });

            this.logger.info('Command executed successfully', {
                executionId,
                exitCode: result.exitCode,
                executionTime: result.executionTime
            });

            return result;

        } catch (error) {
            this.logger.error('Command execution failed', {
                executionId,
                error: error.message,
                command: this.sanitizeCommand(command)
            });
            throw error;
        }
    }

    /**
     * Validate command against whitelist and security rules
     */
    validateCommand(command, args) {
        // Check if command is string
        if (typeof command !== 'string') {
            return { valid: false, reason: 'Command must be a string' };
        }

        // Remove path and get base command
        const baseCommand = path.basename(command);

        // Check against whitelist
        if (!this.commandWhitelist.has(baseCommand)) {
            return { valid: false, reason: `Command '${baseCommand}' is not whitelisted` };
        }

        const commandConfig = this.commandWhitelist.get(baseCommand);

        // Check if command is allowed
        if (!commandConfig.allowed) {
            return { valid: false, reason: `Command '${baseCommand}' is disabled` };
        }

        // Validate arguments
        if (!Array.isArray(args)) {
            return { valid: false, reason: 'Arguments must be an array' };
        }

        // Check argument count
        if (args.length > commandConfig.maxArgs) {
            return { valid: false, reason: `Too many arguments (max: ${commandConfig.maxArgs})` };
        }

        // Check for dangerous arguments
        for (const arg of args) {
            if (typeof arg !== 'string') {
                return { valid: false, reason: 'All arguments must be strings' };
            }

            // Check for dangerous patterns
            if (commandConfig.dangerousArgs.some(dangerous => arg.includes(dangerous))) {
                return { valid: false, reason: `Dangerous argument detected: ${arg}` };
            }

            // Check for command injection patterns
            if (this.hasInjectionPatterns(arg)) {
                return { valid: false, reason: `Potential injection detected in argument: ${arg}` };
            }
        }

        return { valid: true };
    }

    /**
     * Check for command injection patterns
     */
    hasInjectionPatterns(input) {
        const injectionPatterns = [
            /[;&|`$(){}[\]]/,
            /\$\([^)]*\)/,
            /`[^`]*`/,
            /\|\s*\w+/,
            /&&\s*\w+/,
            /\|\|\s*\w+/,
            />\s*\/\w+/,
            /<\s*\/\w+/
        ];

        return injectionPatterns.some(pattern => pattern.test(input));
    }

    /**
     * Sanitize command name
     */
    sanitizeCommand(command) {
        if (typeof command !== 'string') {
            throw new Error('Command must be a string');
        }

        // Remove path traversal attempts
        const sanitized = path.basename(command);
        
        // Remove dangerous characters
        return sanitized.replace(/[^a-zA-Z0-9\-_\.]/g, '');
    }

    /**
     * Sanitize command arguments
     */
    sanitizeArguments(args) {
        if (!Array.isArray(args)) {
            throw new Error('Arguments must be an array');
        }

        return args.map(arg => {
            if (typeof arg !== 'string') {
                throw new Error('All arguments must be strings');
            }

            // Basic sanitization - remove null bytes and control characters
            return arg.replace(/[\x00-\x1F\x7F]/g, '');
        });
    }

    /**
     * Validate working directory to prevent path traversal
     */
    validateWorkingDirectory(cwd) {
        if (!cwd) return this.config.workingDirectory;

        const resolved = path.resolve(cwd);
        const allowed = path.resolve(this.config.workingDirectory);

        // Ensure directory is within allowed workspace
        if (!resolved.startsWith(allowed)) {
            throw new Error(`Working directory outside allowed workspace: ${resolved}`);
        }

        return resolved;
    }

    /**
     * Sanitize working directory for logging
     */
    sanitizeWorkingDirectory(cwd) {
        const resolved = path.resolve(cwd || this.config.workingDirectory);
        const relative = path.relative(process.cwd(), resolved);
        return relative || '.';
    }

    /**
     * Sanitize environment variables
     */
    sanitizeEnvironment(env) {
        if (!env) return { ...process.env };

        const sanitized = { ...process.env };
        
        // Remove potentially dangerous environment variables
        const dangerousEnvVars = [
            'LD_PRELOAD', 'DYLD_INSERT_LIBRARIES', 'PATH'
        ];

        for (const dangerous of dangerousEnvVars) {
            if (env[dangerous]) {
                this.logger.warn(`Blocked dangerous environment variable: ${dangerous}`);
                delete env[dangerous];
            }
        }

        return { ...sanitized, ...env };
    }

    /**
     * Secure spawn wrapper with timeout and validation
     */
    async secureSpawn(command, args, options = {}) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            
            const child = spawn(command, args, {
                cwd: options.cwd,
                env: options.env,
                stdio: ['ignore', 'pipe', 'pipe'],
                timeout: options.timeout,
                killSignal: 'SIGKILL'
            });

            let stdout = '';
            let stderr = '';

            // Capture output with size limits
            const maxOutputSize = 1024 * 1024;

            child.stdout?.on('data', (data) => {
                stdout += data.toString();
                if (stdout.length > maxOutputSize) {
                    child.kill('SIGKILL');
                    reject(new Error('Command output exceeded size limit'));
                }
            });

            child.stderr?.on('data', (data) => {
                stderr += data.toString();
                if (stderr.length > maxOutputSize) {
                    child.kill('SIGKILL');
                    reject(new Error('Command error output exceeded size limit'));
                }
            });

            child.on('close', (code, signal) => {
                const executionTime = Date.now() - startTime;
                
                if (signal) {
                    reject(new Error(`Command terminated by signal: ${signal}`));
                } else {
                    resolve({
                        exitCode: code,
                        stdout: stdout.trim(),
                        stderr: stderr.trim(),
                        executionTime,
                        signal
                    });
                }
            });

            child.on('error', (error) => {
                const executionTime = Date.now() - startTime;
                error.executionTime = executionTime;
                reject(error);
            });

            // Set timeout
            if (options.timeout) {
                setTimeout(() => {
                    if (!child.killed) {
                        child.kill('SIGKILL');
                        reject(new Error(`Command timeout after ${options.timeout}ms`));
                    }
                }, options.timeout);
            }
        });
    }

    /**
     * Generate unique execution ID for audit trail
     */
    generateExecutionId() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substr(2, 9);
        return `exec_${timestamp}_${random}`;
    }

    /**
     * Create safe git command wrapper
     */
    async gitCommand(action, args = [], options = {}) {
        const safeGitActions = ['status', 'stash', 'reset', 'add', 'commit', 'branch', 'log'];
        
        if (!safeGitActions.includes(action)) {
            throw new Error(`Git action '${action}' is not allowed`);
        }

        return this.executeCommand('git', [action, ...args], {
            ...options,
            timeout: 15000
        });
    }
}

module.exports = SecureCommandExecutor;
