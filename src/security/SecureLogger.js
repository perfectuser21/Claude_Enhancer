/**
 * Secure Logging Utility for Production Systems
 * Filters sensitive data and sanitizes output for security compliance
 */

const crypto = require('crypto');
const fs = require('fs').promises;
const path = require('path');

class SecureLogger {
    constructor(options = {}) {
        this.config = {
            logLevel: options.logLevel || 'info',
            sanitize: options.sanitize !== false,
            hashSensitive: options.hashSensitive !== false,
            maxLogSize: options.maxLogSize || 10 * 1024 * 1024, // 10MB
            logDir: options.logDir || '/tmp/claude/logs',
            rotateOnSize: options.rotateOnSize !== false,
            ...options
        };

        // Sensitive data patterns to sanitize
        this.sensitivePatterns = [
            // Credentials and tokens
            /(?:password|pwd|pass|secret|token|key|auth)[\s]*[=:]\s*['"]?([^'"\s\n]+)/gi,
            // API keys
            /(?:api[_-]?key|access[_-]?token|bearer)\s*[=:]\s*['"]?([a-zA-Z0-9_\-]{20,})/gi,
            // File paths (partial sanitization)
            /([a-zA-Z]:\\(?:[^\\/:*?"<>|\n]+\\)*[^\\/:*?"<>|\n]*|\/(?:[^\/\n]+\/)*[^\/\n]*)/g,
            // Email addresses
            /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
            // Credit card patterns
            /\b(?:\d{4}[-\s]?){3}\d{4}\b/g,
            // SSH keys
            /-----BEGIN [A-Z\s]+-----[\s\S]*?-----END [A-Z\s]+-----/gi,
            // Git URLs with credentials
            /https?:\/\/[^@\s]+:[^@\s]+@[^\s]+/gi
        ];

        this.levels = {
            error: 0,
            warn: 1,
            info: 2,
            debug: 3,
            trace: 4
        };

        this.currentLevel = this.levels[this.config.logLevel] || 2;
        this.init();
    }

    async init() {
        try {
            await fs.mkdir(this.config.logDir, { recursive: true, mode: 0o750 });
        } catch (error) {
            // Fallback to current directory if log dir creation fails
            this.config.logDir = process.cwd();
        }
    }

    /**
     * Sanitize sensitive data from log messages
     */
    sanitizeData(data) {
        if (!this.config.sanitize) return data;

        let sanitized = typeof data === 'string' ? data : JSON.stringify(data, null, 2);

        // Remove sensitive patterns
        for (const pattern of this.sensitivePatterns) {
            sanitized = sanitized.replace(pattern, (match, ...groups) => {
                const sensitiveValue = groups.find(g => g !== undefined);
                if (sensitiveValue && this.config.hashSensitive) {
                    const hash = crypto.createHash('sha256')
                        .update(sensitiveValue)
                        .digest('hex')
                        .substring(0, 8);
                    return match.replace(sensitiveValue, `[REDACTED-${hash}]`);
                }
                return match.replace(sensitiveValue || match, '[REDACTED]');
            });
        }

        // Sanitize command arguments
        sanitized = sanitized.replace(
            /(spawn|exec|execSync)\s*\(\s*['"`]([^'"`]+)['"`]/gi,
            (match, method, command) => {
                const sanitizedCommand = this.sanitizeCommand(command);
                return match.replace(command, sanitizedCommand);
            }
        );

        return sanitized;
    }

    /**
     * Sanitize command strings to prevent injection logging
     */
    sanitizeCommand(command) {
        // Remove potentially dangerous characters and patterns
        return command
            .replace(/[;&|`$(){}[\]]/g, '[SANITIZED]')
            .replace(/--?[a-zA-Z-]+=([^\s]+)/g, (match, value) => {
                if (value.length > 20) {
                    return match.replace(value, `[TRUNCATED-${value.length}chars]`);
                }
                return match;
            });
    }

    /**
     * Create structured log entry
     */
    createLogEntry(level, message, meta = {}) {
        const timestamp = new Date().toISOString();
        const sanitizedMessage = this.sanitizeData(message);
        const sanitizedMeta = this.sanitizeData(meta);

        return {
            timestamp,
            level: level.toUpperCase(),
            message: sanitizedMessage,
            meta: sanitizedMeta,
            pid: process.pid,
            hostname: require('os').hostname(),
            version: process.version
        };
    }

    /**
     * Log error level messages
     */
    error(message, meta = {}) {
        if (this.currentLevel >= this.levels.error) {
            this.writeLog('error', message, meta);
        }
    }

    /**
     * Log warning level messages
     */
    warn(message, meta = {}) {
        if (this.currentLevel >= this.levels.warn) {
            this.writeLog('warn', message, meta);
        }
    }

    /**
     * Log info level messages
     */
    info(message, meta = {}) {
        if (this.currentLevel >= this.levels.info) {
            this.writeLog('info', message, meta);
        }
    }

    /**
     * Log debug level messages (production safe)
     */
    debug(message, meta = {}) {
        if (this.currentLevel >= this.levels.debug) {
            this.writeLog('debug', message, meta);
        }
    }

    /**
     * Security-focused logging for audit trails
     */
    security(message, meta = {}) {
        const securityEntry = this.createLogEntry('security', message, {
            ...meta,
            userAgent: process.env.USER_AGENT || 'unknown',
            remoteIP: process.env.REMOTE_ADDR || 'localhost'
        });

        this.writeToFile('security.log', JSON.stringify(securityEntry) + '\n');
    }

    /**
     * Write log entry
     */
    async writeLog(level, message, meta = {}) {
        try {
            const entry = this.createLogEntry(level, message, meta);
            const logLine = JSON.stringify(entry) + '\n';

            // Write to appropriate log file
            const filename = level === 'error' ? 'error.log' : 'application.log';
            await this.writeToFile(filename, logLine);

            // Also write to stderr for errors in development
            if (level === 'error' && process.env.NODE_ENV !== 'production') {
                process.stderr.write(`${entry.timestamp} [${entry.level}] ${entry.message}\n`);
            }
        } catch (error) {
            // Fallback to stderr if file writing fails
            process.stderr.write(`Failed to write log: ${error.message}\n`);
        }
    }

    /**
     * Safe file writing with rotation
     */
    async writeToFile(filename, data) {
        const logPath = path.join(this.config.logDir, filename);
        
        try {
            // Check file size for rotation
            if (this.config.rotateOnSize) {
                try {
                    const stats = await fs.stat(logPath);
                    if (stats.size > this.config.maxLogSize) {
                        await this.rotateLogFile(logPath);
                    }
                } catch (error) {
                    // File doesn't exist yet, continue
                }
            }

            await fs.appendFile(logPath, data, { flag: 'a', mode: 0o640 });
        } catch (error) {
            // Fallback to console in case of file write failures
            if (process.env.NODE_ENV !== 'production') {
                console.error(`Log write failed: ${error.message}`);
            }
        }
    }

    /**
     * Rotate log files when they exceed max size
     */
    async rotateLogFile(logPath) {
        try {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const rotatedPath = `${logPath}.${timestamp}`;
            await fs.rename(logPath, rotatedPath);
        } catch (error) {
            // If rotation fails, continue with current file
        }
    }

    /**
     * Replace console.log calls with secure logging
     */
    replaceConsole() {
        if (process.env.NODE_ENV === 'production') {
            console.log = this.info.bind(this);
            console.warn = this.warn.bind(this);
            console.error = this.error.bind(this);
            console.debug = this.debug.bind(this);
        }
    }

    /**
     * Get logger instance for specific module
     */
    static getLogger(moduleName, options = {}) {
        return new SecureLogger({
            ...options,
            module: moduleName
        });
    }
}

module.exports = SecureLogger;
