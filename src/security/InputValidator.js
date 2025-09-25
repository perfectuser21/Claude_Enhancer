/**
 * Input Validation Utility for Security Compliance
 */

const path = require('path');
const crypto = require('crypto');

class InputValidator {
    constructor(options = {}) {
        this.config = {
            maxStringLength: options.maxStringLength || 1000,
            allowedFileExtensions: options.allowedFileExtensions || ['.js', '.json', '.md', '.txt', '.log'],
            maxPathDepth: options.maxPathDepth || 10,
            enableStrictMode: options.enableStrictMode !== false,
            ...options
        };

        // Common attack patterns
        this.maliciousPatterns = [
            // Path traversal
            /\.\.[\/\\]/g,
            /\.\.[\/\\].*[\/\\]/g,
            /[\/\\]\.\.$/g,
            
            // Command injection
            /[;&|`$(){}[\]]/g,
            
            // Script injection
            /<script[^>]*>.*?<\/script>/gi,
            /javascript:/gi,
            /vbscript:/gi,
            /on\w+\s*=/gi,
            
            // SQL injection
            /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)/gi,
            /(\b(OR|AND)\s+\d+\s*=\s*\d+)/gi,
            
            // File system attacks
            /\/(proc|sys|dev|etc)\//gi,
            /\\\\[^\\]+\\/gi,
            
            // URL/Protocol attacks
            /file:\/\//gi,
            /ftp:\/\//gi,
            /data:/gi,
            
            // Null bytes and control characters
            /\x00/g,
            /[\x01-\x08\x0B\x0C\x0E-\x1F\x7F]/g
        ];
    }

    /**
     * Validate and sanitize file path to prevent path traversal
     */
    validateFilePath(filePath, options = {}) {
        if (!filePath || typeof filePath !== 'string') {
            throw new Error('File path must be a non-empty string');
        }

        const result = {
            valid: true,
            sanitized: filePath,
            warnings: []
        };

        try {
            // Check for null bytes and control characters
            if (/\x00/.test(filePath)) {
                throw new Error('Null bytes detected in path');
            }

            // Check for path traversal attempts
            if (/\.\.[\/\\]/.test(filePath)) {
                throw new Error('Path traversal attempt detected');
            }

            // Normalize path
            let normalized = path.normalize(filePath);
            
            // Ensure path doesn't start with /
            if (normalized.startsWith('/') && !options.allowAbsolute) {
                throw new Error('Absolute paths not allowed');
            }

            // Check path depth
            const parts = normalized.split(path.sep).filter(part => part && part !== '.');
            if (parts.length > this.config.maxPathDepth) {
                throw new Error('Path depth exceeds maximum allowed');
            }

            // Validate file extension if provided
            const extension = path.extname(normalized);
            if (extension && !this.config.allowedFileExtensions.includes(extension)) {
                result.warnings.push('Unusual file extension detected');
            }

            // Check for suspicious patterns
            for (const pattern of this.maliciousPatterns) {
                if (pattern.test(normalized)) {
                    throw new Error('Suspicious pattern detected in path');
                }
            }

            // Resolve to absolute path for final validation
            if (options.basePath) {
                const absolutePath = path.resolve(options.basePath, normalized);
                const basePath = path.resolve(options.basePath);
                
                if (!absolutePath.startsWith(basePath + path.sep) && absolutePath !== basePath) {
                    throw new Error('Path escapes base directory');
                }
                
                result.sanitized = absolutePath;
            } else {
                result.sanitized = normalized;
            }

        } catch (error) {
            result.valid = false;
            result.error = error.message;
        }

        return result;
    }

    /**
     * Validate and sanitize string input
     */
    validateString(input, options = {}) {
        const result = {
            valid: true,
            sanitized: input,
            warnings: []
        };

        if (typeof input !== 'string') {
            result.valid = false;
            result.error = 'Input must be a string';
            return result;
        }

        const maxLength = options.maxLength || this.config.maxStringLength;
        
        // Check length
        if (input.length > maxLength) {
            result.valid = false;
            result.error = 'String exceeds maximum length';
            return result;
        }

        // Check for malicious patterns
        let sanitized = input;
        
        for (const pattern of this.maliciousPatterns) {
            if (pattern.test(sanitized)) {
                if (this.config.enableStrictMode) {
                    result.valid = false;
                    result.error = 'Malicious pattern detected in input';
                    return result;
                } else {
                    sanitized = sanitized.replace(pattern, '[FILTERED]');
                    result.warnings.push('Suspicious pattern filtered from input');
                }
            }
        }

        // Remove or encode special characters based on context
        if (options.context === 'html') {
            sanitized = this.htmlEncode(sanitized);
        } else if (options.context === 'sql') {
            sanitized = this.sqlEscape(sanitized);
        } else if (options.context === 'shell') {
            sanitized = this.shellEscape(sanitized);
        }

        result.sanitized = sanitized;
        return result;
    }

    /**
     * Validate command arguments for safe execution
     */
    validateCommandArgs(args) {
        if (!Array.isArray(args)) {
            throw new Error('Command arguments must be an array');
        }

        const sanitized = [];
        
        for (let i = 0; i < args.length; i++) {
            const arg = args[i];
            
            if (typeof arg !== 'string') {
                throw new Error('All arguments must be strings');
            }

            // Check for injection patterns
            if (/[;&|`$(){}[\]]/.test(arg)) {
                throw new Error('Dangerous characters detected in argument');
            }

            // Check for suspicious file paths
            if (arg.includes('../') || arg.includes('..\\')) {
                throw new Error('Path traversal detected in argument');
            }

            sanitized.push(arg.trim());
        }

        return sanitized;
    }

    /**
     * Validate checkpoint ID
     */
    validateCheckpointId(checkpointId) {
        if (!checkpointId || typeof checkpointId !== 'string') {
            throw new Error('Checkpoint ID must be a non-empty string');
        }

        // Only allow alphanumeric characters, hyphens, and underscores
        if (!/^[a-zA-Z0-9_-]+$/.test(checkpointId)) {
            throw new Error('Checkpoint ID contains invalid characters');
        }

        if (checkpointId.length > 100) {
            throw new Error('Checkpoint ID too long');
        }

        return checkpointId;
    }

    /**
     * HTML encode for XSS prevention
     */
    htmlEncode(input) {
        return input
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#x27;')
            .replace(/\//g, '&#x2F;');
    }

    /**
     * SQL escape for injection prevention
     */
    sqlEscape(input) {
        return input.replace(/'/g, "''").replace(/;/g, '');
    }

    /**
     * Shell escape for command injection prevention
     */
    shellEscape(input) {
        // Remove dangerous shell characters
        return input.replace(/[;&|`$(){}[\]\\<>]/g, '');
    }

    /**
     * Generate secure random identifier
     */
    generateSecureId(prefix = 'secure', length = 16) {
        const randomBytes = crypto.randomBytes(Math.ceil(length / 2));
        const randomId = randomBytes.toString('hex').substr(0, length);
        return prefix + '_' + randomId;
    }
}

module.exports = InputValidator;
