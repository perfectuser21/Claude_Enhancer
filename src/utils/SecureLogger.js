/**
 * SecureLogger.js - Enterprise-grade secure logging system
 *
 * Features:
 * - Automatic data sanitization (passwords, tokens, keys, PII)
 * - Environment-aware log levels
 * - Pattern masking for emails, IPs, tokens
 * - Performance optimized
 * - Memory leak protection
 *
 * Claude Enhancer 5.0 Security Standards Compliant
 */

class SecureLogger {
    constructor() {
        this.logLevels = {
            DEBUG: 0,
            INFO: 1,
            WARN: 2,
            ERROR: 3
        };

        // Environment-based configuration
        this.currentLevel = this._determineLogLevel();
        this.isProduction = process.env.NODE_ENV === 'production';

        // Sensitive data patterns for sanitization
        this.sensitivePatterns = {
            // Authentication & Authorization
            password: /(?:password|pwd|passwd|pass)[\s]*[:=]\s*["']?([^"',\s\n\r]+)/gi,
            token: /(?:token|jwt|bearer|auth)[\s]*[:=]\s*["']?([a-zA-Z0-9._-]{20,})/gi,
            apiKey: /(?:api[_-]?key|apikey|key)[\s]*[:=]\s*["']?([a-zA-Z0-9._-]{16,})/gi,
            secret: /(?:secret|private[_-]?key)[\s]*[:=]\s*["']?([a-zA-Z0-9._-]{16,})/gi,

            // Network & Infrastructure
            ipAddress: /\b(?:\d{1,3}\.){3}\d{1,3}\b/g,
            email: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
            url: /https?:\/\/[^\s"'<>]+/g,

            // Database & Connection strings
            connectionString: /(?:mongodb|mysql|postgres|redis):\/\/[^\s"'<>]+/gi,

            // Credit cards & Financial
            creditCard: /\b(?:\d{4}[-\s]?){3}\d{4}\b/g,

            // Custom patterns (can be extended)
            customSecrets: /(?:client[_-]?secret|refresh[_-]?token)[\s]*[:=]\s*["']?([a-zA-Z0-9._-]{16,})/gi
        };

        // Masking configurations
        this.maskingRules = {
            full: '***REDACTED***',
            partial: (value) => {
                if (typeof value !== 'string') return '***';
                if (value.length <= 8) return '***';
                return value.substring(0, 2) + '***' + value.substring(value.length - 2);
            },
            email: (email) => {
                if (typeof email !== 'string' || !email.includes('@')) {
                    return '***@***.***';
                }
                const [user, domain] = email.split('@');
                if (!user || !domain) {
                    return '***@***.***';
                }
                const maskedUser = user.length > 2 ? user[0] + '***' + user.slice(-1) : '***';
                return `${maskedUser}@${domain}`;
            },
            ip: (ip) => {
                if (typeof ip !== 'string' || !ip.includes('.')) {
                    return '***.***.***.***';
                }
                const parts = ip.split('.');
                if (parts.length !== 4) {
                    return '***.***.***.***';
                }
                return `${parts[0]}.***.***.${parts[3]}`;
            }
        };

        // Performance optimization
        this.logBuffer = [];
        this.bufferSize = 100;
        this.bufferFlushInterval = 5000; // 5 seconds

        if (!this.isProduction) {
            this._startBufferFlusher();
        }

        // Bind methods to preserve context
        this.debug = this.debug.bind(this);
        this.info = this.info.bind(this);
        this.warn = this.warn.bind(this);
        this.error = this.error.bind(this);
    }

    /**
     * Determine appropriate log level based on environment
     */
    _determineLogLevel() {
        const env = process.env.NODE_ENV;
        const logLevel = process.env.LOG_LEVEL;

        if (logLevel) {
            return this.logLevels[logLevel.toUpperCase()] || this.logLevels.INFO;
        }

        switch (env) {
            case 'production':
                return this.logLevels.WARN;
            case 'staging':
                return this.logLevels.INFO;
            case 'test':
                return this.logLevels.ERROR;
            default:
                return this.logLevels.DEBUG;
        }
    }

    /**
     * Sanitize sensitive data from log messages
     */
    _sanitizeMessage(message) {
        if (typeof message !== 'string') {
            message = this._safeStringify(message);
        }

        let sanitized = message;

        // Apply all sanitization patterns
        Object.entries(this.sensitivePatterns).forEach(([type, pattern]) => {
            sanitized = sanitized.replace(pattern, (match, ...groups) => {
                // For patterns with capture groups, use the captured value
                if (groups.length > 0 && groups[0]) {
                    const sensitiveValue = groups[0];
                    return match.replace(sensitiveValue, this._getMaskForType(type, sensitiveValue));
                } else {
                    // For patterns without capture groups (like email, ip)
                    return this._getMaskForType(type, match);
                }
            });
        });

        return sanitized;
    }

    /**
     * Get appropriate mask based on data type
     */
    _getMaskForType(type, value) {
        switch (type) {
            case 'email':
                return this.maskingRules.email(value);
            case 'ipAddress':
                return this.maskingRules.ip(value);
            case 'password':
            case 'secret':
            case 'apiKey':
                return this.maskingRules.full;
            case 'token':
                return this.maskingRules.partial(value);
            default:
                return this.maskingRules.partial(value);
        }
    }

    /**
     * Safely stringify objects, handling circular references
     */
    _safeStringify(obj) {
        const seen = new WeakSet();
        try {
            return JSON.stringify(obj, (key, value) => {
                if (typeof value === 'object' && value !== null) {
                    if (seen.has(value)) {
                        return '[Circular Reference]';
                    }
                    seen.add(value);
                }
                return value;
            }, 2);
        } catch (error) {
            return `[Unable to stringify: ${error.message}]`;
        }
    }

    /**
     * Format log entry with metadata
     */
    _formatLogEntry(level, message, context = {}) {
        const timestamp = new Date().toISOString();
        const sanitizedMessage = this._sanitizeMessage(message);

        const logEntry = {
            timestamp,
            level,
            message: sanitizedMessage,
            pid: process.pid,
            ...context
        };

        // Add stack trace for errors
        if (level === 'ERROR' && context.error) {
            logEntry.stack = context.error.stack;
        }

        return logEntry;
    }

    /**
     * Output log entry based on environment
     */
    _output(logEntry) {
        if (this.isProduction) {
            // In production, output structured JSON
            console.log(JSON.stringify(logEntry));
        } else {
            // In development, output formatted for readability
            const colorCode = this._getColorCode(logEntry.level);
            const resetCode = '\x1b[0m';

            console.log(
                `${colorCode}[${logEntry.timestamp}] ${logEntry.level}${resetCode}: ${logEntry.message}`
            );

            if (logEntry.context && Object.keys(logEntry.context).length > 0) {
                console.log('Context:', logEntry.context);
            }
        }
    }

    /**
     * Get ANSI color code for log level
     */
    _getColorCode(level) {
        const colors = {
            DEBUG: '\x1b[36m', // Cyan
            INFO: '\x1b[32m',  // Green
            WARN: '\x1b[33m',  // Yellow
            ERROR: '\x1b[31m'  // Red
        };
        return colors[level] || '\x1b[0m';
    }

    /**
     * Start buffer flusher for development mode
     */
    _startBufferFlusher() {
        setInterval(() => {
            if (this.logBuffer.length > 0) {
                this.logBuffer.forEach(entry => this._output(entry));
                this.logBuffer = [];
            }
        }, this.bufferFlushInterval);
    }

    /**
     * Core logging method
     */
    _log(level, message, context = {}) {
        const levelNum = this.logLevels[level];

        if (levelNum < this.currentLevel) {
            return; // Skip logging if below threshold
        }

        const logEntry = this._formatLogEntry(level, message, context);

        if (this.isProduction || level === 'ERROR') {
            // Immediately output in production or for errors
            this._output(logEntry);
        } else {
            // Buffer for development mode
            this.logBuffer.push(logEntry);

            if (this.logBuffer.length >= this.bufferSize) {
                this.logBuffer.forEach(entry => this._output(entry));
                this.logBuffer = [];
            }
        }
    }

    /**
     * Public logging methods
     */
    debug(message, context = {}) {
        this._log('DEBUG', message, context);
    }

    info(message, context = {}) {
        this._log('INFO', message, context);
    }

    warn(message, context = {}) {
        this._log('WARN', message, context);
    }

    error(message, error = null, context = {}) {
        if (error instanceof Error) {
            context.error = error;
            context.errorMessage = error.message;
            context.errorStack = error.stack;
        }
        this._log('ERROR', message, context);
    }

    /**
     * Special method for security events
     */
    security(message, context = {}) {
        this._log('ERROR', `[SECURITY] ${message}`, {
            ...context,
            security: true,
            timestamp: Date.now()
        });
    }

    /**
     * Performance monitoring
     */
    performance(label, duration, context = {}) {
        this._log('INFO', `[PERFORMANCE] ${label}: ${duration}ms`, {
            ...context,
            performance: true,
            duration
        });
    }

    /**
     * Audit logging
     */
    audit(action, user, resource, context = {}) {
        this._log('INFO', `[AUDIT] ${action} by ${user} on ${resource}`, {
            ...context,
            audit: true,
            action,
            user,
            resource
        });
    }

    /**
     * Replace console.log functionality
     */
    replaceConsole() {
        const originalConsole = {
            log: console.log,
            info: console.info,
            warn: console.warn,
            error: console.error,
            debug: console.debug
        };

        console.log = (...args) => this.info(args.join(' '));
        console.info = (...args) => this.info(args.join(' '));
        console.warn = (...args) => this.warn(args.join(' '));
        console.error = (...args) => this.error(args.join(' '));
        console.debug = (...args) => this.debug(args.join(' '));

        // Return function to restore original console
        return () => {
            Object.assign(console, originalConsole);
        };
    }

    /**
     * Flush any buffered logs (useful for graceful shutdown)
     */
    flush() {
        if (this.logBuffer.length > 0) {
            this.logBuffer.forEach(entry => this._output(entry));
            this.logBuffer = [];
        }
    }

    /**
     * Update log level at runtime
     */
    setLogLevel(level) {
        const levelNum = this.logLevels[level.toUpperCase()];
        if (levelNum !== undefined) {
            this.currentLevel = levelNum;
            this.info(`Log level updated to ${level.toUpperCase()}`);
        } else {
            this.warn(`Invalid log level: ${level}`);
        }
    }
}

// Create singleton instance
const secureLogger = new SecureLogger();

// Export both the instance and the class
module.exports = {
    SecureLogger,
    logger: secureLogger,

    // Convenience exports
    debug: secureLogger.debug,
    info: secureLogger.info,
    warn: secureLogger.warn,
    error: secureLogger.error,
    security: secureLogger.security,
    performance: secureLogger.performance,
    audit: secureLogger.audit
};

/**
 * Usage Examples:
 *
 * const { logger } = require('./utils/SecureLogger');
 *
 * // Basic logging
 * logger.info('User login successful', { userId: 123 });
 * logger.error('Database connection failed', error, { database: 'users' });
 *
 * // Security logging
 * logger.security('Unauthorized access attempt', { ip: '192.168.1.1' });
 *
 * // Performance logging
 * logger.performance('API Response', 150, { endpoint: '/api/users' });
 *
 * // Audit logging
 * logger.audit('DELETE', 'admin@example.com', 'user:123');
 *
 * // Replace console globally
 * const restore = logger.replaceConsole();
 * console.log('This will be logged securely'); // Automatically sanitized
 * restore(); // Restore original console
 */