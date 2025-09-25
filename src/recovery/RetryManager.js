/**
 * Claude Enhancer 5.0 - Intelligent Retry Management System
 * Provides exponential backoff, jitter, and context-aware retry logic
 */

const { EventEmitter } = require('events');

class RetryManager extends EventEmitter {
    constructor(options = {}) {
        super();
        this.config = {
            defaultMaxRetries: options.defaultMaxRetries || 3,
            baseDelay: options.baseDelay || 1000,
            maxDelay: options.maxDelay || 30000,
            backoffFactor: options.backoffFactor || 2,
            jitterEnabled: options.jitterEnabled !== false,
            jitterFactor: options.jitterFactor || 0.1,
            circuitBreakerEnabled: options.circuitBreakerEnabled || true,
            circuitBreakerThreshold: options.circuitBreakerThreshold || 5,
            circuitBreakerTimeout: options.circuitBreakerTimeout || 60000,
            ...options
        };
        
        this.retryStrategies = new Map();
        this.circuitBreakers = new Map();
        this.retryMetrics = new Map();
        
        this.initializeDefaultStrategies();
    }
    
    /**
     * Initialize default retry strategies for common scenarios
     */
    initializeDefaultStrategies() {
        // Network operations
        this.addRetryStrategy('network', {
            maxRetries: 3,
            baseDelay: 1000,
            backoffFactor: 2,
            jitterEnabled: true,
            retryCondition: (error, attempt) => {
                const networkErrors = ['ECONNRESET', 'ETIMEDOUT', 'ENOTFOUND', 'ECONNREFUSED'];
                return networkErrors.includes(error.code) || 
                       (error.response && error.response.status >= 500);
            }
        });
        
        // File operations
        this.addRetryStrategy('file', {
            maxRetries: 2,
            baseDelay: 500,
            backoffFactor: 1.5,
            jitterEnabled: false,
            retryCondition: (error, attempt) => {
                const fileErrors = ['EBUSY', 'EMFILE', 'ENFILE', 'EAGAIN'];
                return fileErrors.includes(error.code);
            }
        });
        
        // Validation operations
        this.addRetryStrategy('validation', {
            maxRetries: 1,
            baseDelay: 100,
            backoffFactor: 1,
            jitterEnabled: false,
            retryCondition: (error, attempt) => {
                return error.type === 'ValidationError' && error.recoverable === true;
            }
        });
    }
    
    /**
     * Add a custom retry strategy
     */
    addRetryStrategy(name, strategy) {
        const fullStrategy = {
            maxRetries: this.config.defaultMaxRetries,
            baseDelay: this.config.baseDelay,
            backoffFactor: this.config.backoffFactor,
            jitterEnabled: this.config.jitterEnabled,
            retryCondition: () => true,
            beforeRetry: async () => {},
            ...strategy
        };
        
        this.retryStrategies.set(name, fullStrategy);
        this.retryMetrics.set(name, {
            totalAttempts: 0,
            successfulRetries: 0,
            failedRetries: 0,
            circuitBreakerTrips: 0
        });
        
        this.emit('strategyAdded', { name, strategy: fullStrategy });
    }
    
    /**
     * Execute operation with retry logic
     */
    async executeWithRetry(operation, strategyName = 'default', options = {}) {
        const strategy = this.retryStrategies.get(strategyName) || this.getDefaultStrategy();
        const operationId = options.operationId || `op_${Date.now()}`;
        const context = options.context || {};
        
        let lastError;
        let attempt = 0;
        const maxAttempts = strategy.maxRetries + 1;
        
        while (attempt < maxAttempts) {
            try {
                this.updateMetrics(strategyName, 'totalAttempts');
                
                // Execute the operation
                const result = await operation(attempt, context);
                
                // Success - update metrics and return
                if (attempt > 0) {
                    this.updateMetrics(strategyName, 'successfulRetries');
                }
                
                this.emit('operationSucceeded', {
                    operationId,
                    strategyName,
                    attempt,
                    totalAttempts: attempt + 1
                });
                
                return result;
                
            } catch (error) {
                lastError = error;
                attempt++;
                
                this.emit('operationAttemptFailed', {
                    operationId,
                    strategyName,
                    attempt,
                    error: error.message,
                    willRetry: attempt < maxAttempts
                });
                
                // Check if we should retry
                if (attempt >= maxAttempts) {
                    break;
                }
                
                // Check retry condition
                if (!strategy.retryCondition(error, attempt)) {
                    break;
                }
                
                // Calculate delay and wait
                const delay = this.calculateDelay(attempt - 1, strategy);
                await this.sleep(delay);
            }
        }
        
        // All attempts failed
        this.updateMetrics(strategyName, 'failedRetries');
        
        this.emit('operationFailed', {
            operationId,
            strategyName,
            totalAttempts: attempt,
            finalError: lastError.message
        });
        
        throw lastError;
    }
    
    /**
     * Helper methods
     */
    getDefaultStrategy() {
        return {
            maxRetries: this.config.defaultMaxRetries,
            baseDelay: this.config.baseDelay,
            backoffFactor: this.config.backoffFactor,
            jitterEnabled: this.config.jitterEnabled,
            retryCondition: () => true,
            beforeRetry: async () => {}
        };
    }
    
    calculateDelay(attempt, strategy) {
        let delay = strategy.baseDelay * Math.pow(strategy.backoffFactor, attempt);
        
        // Add jitter if enabled
        if (strategy.jitterEnabled) {
            const jitter = delay * this.config.jitterFactor * Math.random();
            delay += jitter;
        }
        
        return Math.min(delay, this.config.maxDelay);
    }
    
    updateMetrics(strategyName, metricType) {
        const metrics = this.retryMetrics.get(strategyName);
        if (metrics) {
            metrics[metricType]++;
        }
    }
    
    getMetrics(strategyName = null) {
        if (strategyName) {
            return this.retryMetrics.get(strategyName) || null;
        }
        
        const allMetrics = {};
        for (const [name, metrics] of this.retryMetrics.entries()) {
            allMetrics[name] = metrics;
        }
        
        return allMetrics;
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

module.exports = RetryManager;
