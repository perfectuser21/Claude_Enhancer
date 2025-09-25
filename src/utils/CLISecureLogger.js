/**
 * CLISecureLogger.js - Secure logger wrapper for CLI tools
 *
 * Provides dual logging:
 * - Visual console output for user interaction (preserved formatting)
 * - Secure logging for audit trails and monitoring
 *
 * Perfect21 Security Standards Compliant
 */

const { logger } = require('./SecureLogger');
const chalk = require('chalk');

class CLISecureLogger {
    constructor(cliName = 'CLI') {
        this.cliName = cliName;
        this.logger = logger;
        this.sessionId = Date.now().toString(36);

        // Initialize CLI session logging
        this.logger.audit('CLI_SESSION_START', 'system', cliName, {
            sessionId: this.sessionId,
            pid: process.pid,
            args: process.argv.slice(2)
        });
    }

    /**
     * Log and display information message
     */
    info(message, consoleMessage = null, context = {}) {
        // Display to user (preserved formatting)
        console.log(consoleMessage || message);

        // Secure audit log
        this.logger.info(`[CLI:${this.cliName}] ${this._stripAnsi(message)}`, {
            ...context,
            sessionId: this.sessionId,
            cli: this.cliName
        });
    }

    /**
     * Log and display success message
     */
    success(message, consoleMessage = null, context = {}) {
        // Display to user (preserved formatting)
        console.log(consoleMessage || chalk.green(message));

        // Secure audit log
        this.logger.audit('CLI_SUCCESS', 'system', this.cliName, {
            message: this._stripAnsi(message),
            ...context,
            sessionId: this.sessionId
        });
    }

    /**
     * Log and display warning message
     */
    warn(message, consoleMessage = null, context = {}) {
        // Display to user (preserved formatting)
        console.log(consoleMessage || chalk.yellow(message));

        // Secure warning log
        this.logger.warn(`[CLI:${this.cliName}] ${this._stripAnsi(message)}`, {
            ...context,
            sessionId: this.sessionId,
            cli: this.cliName
        });
    }

    /**
     * Log and display error message
     */
    error(message, error = null, consoleMessage = null, context = {}) {
        // Display to user (preserved formatting)
        console.error(consoleMessage || chalk.red(message));

        // Secure error log with full context
        this.logger.error(`[CLI:${this.cliName}] ${this._stripAnsi(message)}`, error, {
            ...context,
            sessionId: this.sessionId,
            cli: this.cliName
        });
    }

    /**
     * Log and display command execution
     */
    command(command, args = [], context = {}) {
        const message = `Executing command: ${command}`;

        // Display to user
        console.log(chalk.blue(`🔧 ${message}`));

        // Secure audit log (args may contain sensitive data)
        this.logger.audit('CLI_COMMAND', 'user', command, {
            command,
            argCount: args.length,
            ...context,
            sessionId: this.sessionId,
            cli: this.cliName
        });
    }

    /**
     * Log operation start
     */
    operationStart(operation, context = {}) {
        const message = `Starting ${operation}...`;

        console.log(chalk.blue(`🔧 ${message}`));

        this.logger.performance(`${operation}_START`, 0, {
            operation,
            ...context,
            sessionId: this.sessionId,
            cli: this.cliName,
            timestamp: Date.now()
        });

        return Date.now();
    }

    /**
     * Log operation completion
     */
    operationComplete(operation, startTime, context = {}) {
        const duration = Date.now() - startTime;
        const message = `✅ ${operation} completed`;

        console.log(chalk.green(message));

        this.logger.performance(`${operation}_COMPLETE`, duration, {
            operation,
            ...context,
            sessionId: this.sessionId,
            cli: this.cliName
        });
    }

    /**
     * Log operation failure
     */
    operationFailed(operation, error, startTime = null, context = {}) {
        const duration = startTime ? Date.now() - startTime : null;
        const message = `❌ ${operation} failed`;

        console.error(chalk.red(message));

        this.logger.error(`[CLI:${this.cliName}] ${operation} failed`, error, {
            operation,
            duration,
            ...context,
            sessionId: this.sessionId,
            cli: this.cliName
        });
    }

    /**
     * Log user interaction
     */
    userAction(action, data = {}, context = {}) {
        this.logger.audit('CLI_USER_ACTION', 'user', action, {
            ...data,
            ...context,
            sessionId: this.sessionId,
            cli: this.cliName
        });
    }

    /**
     * Log security event
     */
    security(event, details = {}, context = {}) {
        this.logger.security(`[CLI:${this.cliName}] ${event}`, {
            ...details,
            ...context,
            sessionId: this.sessionId,
            cli: this.cliName
        });
    }

    /**
     * End CLI session
     */
    endSession(exitCode = 0, context = {}) {
        this.logger.audit('CLI_SESSION_END', 'system', this.cliName, {
            sessionId: this.sessionId,
            exitCode,
            duration: Date.now() - parseInt(this.sessionId, 36),
            ...context
        });
    }

    /**
     * Strip ANSI color codes from message for clean logging
     */
    _stripAnsi(str) {
        if (typeof str !== 'string') return str;
        return str.replace(/\u001b\[\d+m/g, '');
    }

    /**
     * Table display with logging
     */
    table(title, data, context = {}) {
        console.log(chalk.bold.blue(`\n${title}\n`));
        console.log(data.toString());

        this.logger.info(`[CLI:${this.cliName}] Table displayed: ${title}`, {
            tableRows: Array.isArray(data) ? data.length : 'unknown',
            ...context,
            sessionId: this.sessionId
        });
    }

    /**
     * Progress indicator with logging
     */
    progress(current, total, operation, context = {}) {
        const percentage = Math.round((current / total) * 100);
        const message = `Progress: ${current}/${total} (${percentage}%) - ${operation}`;

        console.log(chalk.blue(message));

        if (percentage % 25 === 0 || current === total) {
            this.logger.info(`[CLI:${this.cliName}] ${message}`, {
                current,
                total,
                percentage,
                operation,
                ...context,
                sessionId: this.sessionId
            });
        }
    }
}

/**
 * Factory function to create CLI loggers
 */
function createCLILogger(cliName) {
    return new CLISecureLogger(cliName);
}

module.exports = {
    CLISecureLogger,
    createCLILogger
};

/**
 * Usage Examples:
 *
 * const { createCLILogger } = require('../../utils/CLISecureLogger');
 * const cliLogger = createCLILogger('RecoveryCLI');
 *
 * // Replace console.log with:
 * cliLogger.info('Starting process...', chalk.blue('🔧 Starting process...'));
 *
 * // Replace console.error with:
 * cliLogger.error('Process failed', error, chalk.red('❌ Process failed'));
 *
 * // Track operations:
 * const startTime = cliLogger.operationStart('recovery');
 * // ... do work ...
 * cliLogger.operationComplete('recovery', startTime);
 *
 * // End session on exit:
 * process.on('exit', (code) => cliLogger.endSession(code));
 */