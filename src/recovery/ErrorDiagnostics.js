/**
 * Claude Enhancer 5.0 - Advanced Error Diagnostics System
 * Provides comprehensive error analysis, pattern detection, and root cause analysis
 */

const fs = require('fs').promises;
const path = require('path');
const { EventEmitter } = require('events');

class ErrorDiagnostics extends EventEmitter {
    constructor(options = {}) {
        super();
        this.config = {
            logDir: options.logDir || './.claude/logs',
            maxLogSize: options.maxLogSize || 10 * 1024 * 1024, // 10MB
            retentionDays: options.retentionDays || 30,
            patternThreshold: options.patternThreshold || 3,
            enableStackTrace: options.enableStackTrace !== false,
            enableMetrics: options.enableMetrics !== false,
            ...options
        };
        
        this.errorHistory = [];
        this.errorPatterns = new Map();
        this.rootCauseMap = new Map();
        this.diagnosticRules = new Map();
        this.metrics = {
            totalErrors: 0,
            categorizedErrors: new Map(),
            resolvedErrors: 0,
            pendingErrors: 0,
            criticalErrors: 0,
            patternDetections: 0
        };
        
        this.initializeDiagnosticRules();
    }
    
    /**
     * Initialize diagnostic rules for common error patterns
     */
    initializeDiagnosticRules() {
        // File system errors
        this.addDiagnosticRule('filesystem', {
            patterns: [
                /ENOENT.*no such file or directory/i,
                /EACCES.*permission denied/i,
                /EPERM.*operation not permitted/i,
                /ENOSPC.*no space left on device/i
            ],
            severity: 'high',
            category: 'filesystem',
            rootCauseAnalysis: (error) => {
                if (/ENOENT/i.test(error.message)) {
                    return {
                        cause: 'Missing file or directory',
                        likelihood: 0.9,
                        evidence: ['File path not found', 'Directory structure incomplete'],
                        solutions: [
                            'Create missing directories',
                            'Verify file paths',
                            'Check deployment process'
                        ]
                    };
                }
                if (/EACCES|EPERM/i.test(error.message)) {
                    return {
                        cause: 'Insufficient permissions',
                        likelihood: 0.95,
                        evidence: ['Permission denied error', 'Access control restriction'],
                        solutions: [
                            'Check file permissions (chmod)',
                            'Verify user privileges',
                            'Run with appropriate permissions'
                        ]
                    };
                }
                return { cause: 'Unknown filesystem issue', likelihood: 0.5 };
            }
        });
        
        // Network errors
        this.addDiagnosticRule('network', {
            patterns: [
                /ECONNREFUSED/i,
                /ETIMEDOUT/i,
                /ENOTFOUND/i,
                /ENETUNREACH/i,
                /socket hang up/i
            ],
            severity: 'medium',
            category: 'network',
            rootCauseAnalysis: (error) => {
                if (/ECONNREFUSED/i.test(error.message)) {
                    return {
                        cause: 'Service unavailable or port closed',
                        likelihood: 0.9,
                        evidence: ['Connection actively refused', 'Service not running'],
                        solutions: [
                            'Check service status',
                            'Verify port availability',
                            'Check firewall rules'
                        ]
                    };
                }
                if (/ETIMEDOUT/i.test(error.message)) {
                    return {
                        cause: 'Network timeout or slow response',
                        likelihood: 0.8,
                        evidence: ['Request timeout', 'Network latency'],
                        solutions: [
                            'Increase timeout values',
                            'Check network connectivity',
                            'Verify endpoint performance'
                        ]
                    };
                }
                return { cause: 'Network connectivity issue', likelihood: 0.7 };
            }
        });
        
        // JavaScript/Node.js errors
        this.addDiagnosticRule('javascript', {
            patterns: [
                /Cannot read property.*of undefined/i,
                /Cannot read properties of undefined/i,
                /is not a function/i,
                /Unexpected token/i,
                /SyntaxError/i,
                /ReferenceError/i
            ],
            severity: 'high',
            category: 'javascript',
            rootCauseAnalysis: (error) => {
                if (/Cannot read property.*of undefined/i.test(error.message)) {
                    return {
                        cause: 'Undefined object property access',
                        likelihood: 0.95,
                        evidence: ['Property access on undefined', 'Missing null checks'],
                        solutions: [
                            'Add null/undefined checks',
                            'Use optional chaining (?.)',
                            'Initialize variables properly'
                        ]
                    };
                }
                if (/is not a function/i.test(error.message)) {
                    return {
                        cause: 'Incorrect function call or missing method',
                        likelihood: 0.9,
                        evidence: ['Function call on non-function', 'Method not available'],
                        solutions: [
                            'Verify function existence',
                            'Check object methods',
                            'Validate function imports'
                        ]
                    };
                }
                return { cause: 'JavaScript runtime error', likelihood: 0.8 };
            }
        });
        
        // Git errors
        this.addDiagnosticRule('git', {
            patterns: [
                /fatal: not a git repository/i,
                /fatal: remote.*does not appear to be a git repository/i,
                /error: failed to push some refs/i,
                /merge conflict/i,
                /cannot lock ref/i
            ],
            severity: 'medium',
            category: 'git',
            rootCauseAnalysis: (error) => {
                if (/not a git repository/i.test(error.message)) {
                    return {
                        cause: 'Git repository not initialized',
                        likelihood: 0.95,
                        evidence: ['Missing .git directory', 'Not in git repository'],
                        solutions: [
                            'Initialize git repository (git init)',
                            'Navigate to correct directory',
                            'Clone repository if needed'
                        ]
                    };
                }
                if (/merge conflict/i.test(error.message)) {
                    return {
                        cause: 'Git merge conflicts present',
                        likelihood: 0.9,
                        evidence: ['Conflicting changes', 'Merge operation failed'],
                        solutions: [
                            'Resolve merge conflicts manually',
                            'Use git mergetool',
                            'Abort merge and try different approach'
                        ]
                    };
                }
                return { cause: 'Git operation failure', likelihood: 0.7 };
            }
        });
    }
    
    /**
     * Add a custom diagnostic rule
     */
    addDiagnosticRule(name, rule) {
        const completeRule = {
            patterns: [],
            severity: 'medium',
            category: 'unknown',
            rootCauseAnalysis: () => ({ cause: 'Unknown', likelihood: 0.5 }),
            ...rule
        };
        
        this.diagnosticRules.set(name, completeRule);
        this.emit('diagnosticRuleAdded', { name, rule: completeRule });
    }
    
    /**
     * Analyze error and provide comprehensive diagnostics
     */
    async analyzeError(error, context = {}) {
        const errorInfo = this.extractErrorInfo(error);
        const timestamp = new Date().toISOString();
        
        // Create diagnostic entry
        const diagnostic = {
            id: this.generateErrorId(),
            timestamp,
            error: errorInfo,
            context,
            analysis: {},
            severity: 'medium',
            category: 'unknown',
            resolved: false
        };
        
        try {
            // Pattern matching
            diagnostic.analysis.patternMatches = this.findPatternMatches(errorInfo);
            
            // Root cause analysis
            diagnostic.analysis.rootCause = await this.performRootCauseAnalysis(errorInfo, context);
            
            // Severity assessment
            diagnostic.severity = this.assessSeverity(errorInfo, diagnostic.analysis.patternMatches);
            
            // Category classification
            diagnostic.category = this.classifyError(diagnostic.analysis.patternMatches);
            
            // Generate suggestions
            diagnostic.analysis.suggestions = this.generateSuggestions(diagnostic);
            
            // Pattern detection
            diagnostic.analysis.patterns = this.detectErrorPatterns(errorInfo);
            
            // Stack trace analysis
            if (this.config.enableStackTrace && errorInfo.stack) {
                diagnostic.analysis.stackTrace = this.analyzeStackTrace(errorInfo.stack);
            }
            
            // Update metrics
            this.updateMetrics(diagnostic);
            
            // Store in history
            this.errorHistory.push(diagnostic);
            
            // Log diagnostic
            await this.logDiagnostic(diagnostic);
            
            // Emit event
            this.emit('errorAnalyzed', diagnostic);
            
            return diagnostic;
            
        } catch (analysisError) {
            this.emit('analysisError', { error: analysisError, originalError: error });
            
            // Return basic diagnostic
            diagnostic.analysis.error = `Analysis failed: ${analysisError.message}`;
            return diagnostic;
        }
    }
    
    /**
     * Extract comprehensive error information
     */
    extractErrorInfo(error) {
        const errorInfo = {
            message: error.message || 'Unknown error',
            name: error.name || error.constructor.name || 'Error',
            code: error.code,
            stack: error.stack,
            timestamp: new Date().toISOString()
        };
        
        // Extract additional properties
        const additionalProps = ['errno', 'syscall', 'path', 'address', 'port', 'response'];
        for (const prop of additionalProps) {
            if (error[prop] !== undefined) {
                errorInfo[prop] = error[prop];
            }
        }
        
        // HTTP response details
        if (error.response) {
            errorInfo.httpStatus = error.response.status;
            errorInfo.httpStatusText = error.response.statusText;
            errorInfo.httpHeaders = error.response.headers;
        }
        
        return errorInfo;
    }
    
    /**
     * Find matching diagnostic patterns
     */
    findPatternMatches(errorInfo) {
        const matches = [];
        
        for (const [ruleName, rule] of this.diagnosticRules.entries()) {
            for (const pattern of rule.patterns) {
                if (pattern.test(errorInfo.message) || 
                    (errorInfo.code && pattern.test(errorInfo.code))) {
                    
                    matches.push({
                        ruleName,
                        pattern: pattern.source,
                        severity: rule.severity,
                        category: rule.category,
                        confidence: 0.9 // Base confidence for pattern matches
                    });
                }
            }
        }
        
        return matches;
    }
    
    /**
     * Perform comprehensive root cause analysis
     */
    async performRootCauseAnalysis(errorInfo, context) {
        const rootCauses = [];
        
        // Rule-based analysis
        for (const [ruleName, rule] of this.diagnosticRules.entries()) {
            for (const pattern of rule.patterns) {
                if (pattern.test(errorInfo.message)) {
                    const analysis = rule.rootCauseAnalysis(errorInfo, context);
                    rootCauses.push({
                        ruleName,
                        ...analysis,
                        method: 'rule-based'
                    });
                }
            }
        }
        
        // Context-based analysis
        if (context.operation) {
            const contextAnalysis = this.analyzeContext(context);
            if (contextAnalysis) {
                rootCauses.push({
                    ...contextAnalysis,
                    method: 'context-based'
                });
            }
        }
        
        // Historical pattern analysis
        const historicalAnalysis = this.analyzeHistoricalPatterns(errorInfo);
        if (historicalAnalysis) {
            rootCauses.push({
                ...historicalAnalysis,
                method: 'historical'
            });
        }
        
        // Sort by likelihood
        rootCauses.sort((a, b) => (b.likelihood || 0) - (a.likelihood || 0));
        
        return {
            primaryCause: rootCauses[0] || { cause: 'Unknown', likelihood: 0 },
            alternativeCauses: rootCauses.slice(1, 3),
            totalCandidates: rootCauses.length
        };
    }
    
    /**
     * Assess error severity
     */
    assessSeverity(errorInfo, patternMatches) {
        let maxSeverity = 'low';
        
        // Critical keywords
        const criticalKeywords = ['fatal', 'critical', 'security', 'corruption', 'loss'];
        if (criticalKeywords.some(keyword => 
            errorInfo.message.toLowerCase().includes(keyword))) {
            return 'critical';
        }
        
        // High severity patterns
        const highSeverityPatterns = [
            /out of memory/i,
            /segmentation fault/i,
            /access violation/i,
            /database.*corrupt/i
        ];
        
        if (highSeverityPatterns.some(pattern => pattern.test(errorInfo.message))) {
            return 'high';
        }
        
        // Pattern-based severity
        for (const match of patternMatches) {
            if (match.severity === 'critical') return 'critical';
            if (match.severity === 'high' && maxSeverity !== 'critical') maxSeverity = 'high';
            if (match.severity === 'medium' && ['low'].includes(maxSeverity)) maxSeverity = 'medium';
        }
        
        return maxSeverity;
    }
    
    /**
     * Classify error into category
     */
    classifyError(patternMatches) {
        if (patternMatches.length === 0) return 'unknown';
        
        // Use the category from the highest confidence match
        const bestMatch = patternMatches.reduce((best, current) => 
            current.confidence > best.confidence ? current : best
        );
        
        return bestMatch.category;
    }
    
    /**
     * Generate actionable suggestions
     */
    generateSuggestions(diagnostic) {
        const suggestions = [];
        
        // Rule-based suggestions
        const rootCause = diagnostic.analysis.rootCause?.primaryCause;
        if (rootCause?.solutions) {
            suggestions.push(...rootCause.solutions.map(solution => ({
                type: 'solution',
                action: solution,
                priority: 'high',
                source: 'rule-based'
            })));
        }
        
        // Category-based suggestions
        const categoryMap = {
            filesystem: [
                'Check file and directory permissions',
                'Verify disk space availability',
                'Ensure proper file paths'
            ],
            network: [
                'Test network connectivity',
                'Verify endpoint availability',
                'Check firewall and proxy settings'
            ],
            javascript: [
                'Review code for null/undefined checks',
                'Validate function calls and imports',
                'Check variable initialization'
            ],
            git: [
                'Verify git repository state',
                'Check remote repository connectivity',
                'Resolve any merge conflicts'
            ]
        };
        
        const categorySuggestions = categoryMap[diagnostic.category] || [];
        suggestions.push(...categorySuggestions.map(suggestion => ({
            type: 'general',
            action: suggestion,
            priority: 'medium',
            source: 'category-based'
        })));
        
        // Recovery commands
        suggestions.push({
            type: 'command',
            action: `phase-controller recover --type=${diagnostic.category}`,
            priority: 'high',
            source: 'recovery'
        });
        
        return suggestions;
    }
    
    /**
     * Detect recurring error patterns
     */
    detectErrorPatterns(errorInfo) {
        const patterns = [];
        
        // Check for similar errors in history
        const similarErrors = this.errorHistory.filter(entry => 
            this.calculateSimilarity(entry.error, errorInfo) > 0.8
        );
        
        if (similarErrors.length >= this.config.patternThreshold) {
            patterns.push({
                type: 'recurring',
                frequency: similarErrors.length,
                timeSpan: this.calculateTimeSpan(similarErrors),
                confidence: Math.min(similarErrors.length / 10, 1)
            });
            
            this.metrics.patternDetections++;
        }
        
        // Check for error cascades
        const recentErrors = this.getRecentErrors(5 * 60 * 1000); // Last 5 minutes
        if (recentErrors.length > 5) {
            patterns.push({
                type: 'cascade',
                count: recentErrors.length,
                timeWindow: '5 minutes',
                confidence: 0.8
            });
        }
        
        return patterns;
    }
    
    /**
     * Analyze stack trace for insights
     */
    analyzeStackTrace(stack) {
        const lines = stack.split('\n');
        const analysis = {
            depth: lines.length,
            files: [],
            functions: [],
            externalLibraries: [],
            applicationCode: []
        };
        
        for (const line of lines) {
            // Extract file paths
            const fileMatch = line.match(/\((.+):(\d+):(\d+)\)/);
            if (fileMatch) {
                const [, filePath, lineNum, colNum] = fileMatch;
                analysis.files.push({
                    path: filePath,
                    line: parseInt(lineNum),
                    column: parseInt(colNum),
                    isExternal: filePath.includes('node_modules')
                });
                
                if (filePath.includes('node_modules')) {
                    const libMatch = filePath.match(/node_modules\/([^\/]+)/);
                    if (libMatch) {
                        analysis.externalLibraries.push(libMatch[1]);
                    }
                } else {
                    analysis.applicationCode.push(filePath);
                }
            }
            
            // Extract function names
            const funcMatch = line.match(/at\s+([^(]+)/);
            if (funcMatch) {
                analysis.functions.push(funcMatch[1].trim());
            }
        }
        
        // Remove duplicates
        analysis.externalLibraries = [...new Set(analysis.externalLibraries)];
        analysis.applicationCode = [...new Set(analysis.applicationCode)];
        
        return analysis;
    }
    
    /**
     * Update diagnostic metrics
     */
    updateMetrics(diagnostic) {
        this.metrics.totalErrors++;
        
        const category = diagnostic.category;
        if (!this.metrics.categorizedErrors.has(category)) {
            this.metrics.categorizedErrors.set(category, 0);
        }
        this.metrics.categorizedErrors.set(category, 
            this.metrics.categorizedErrors.get(category) + 1
        );
        
        if (diagnostic.severity === 'critical') {
            this.metrics.criticalErrors++;
        }
        
        this.metrics.pendingErrors++;
    }
    
    /**
     * Generate diagnostic report
     */
    async generateReport(options = {}) {
        const {
            includeHistory = true,
            includeMetrics = true,
            includePatterns = true,
            timeRange = null
        } = options;
        
        const report = {
            generatedAt: new Date().toISOString(),
            summary: {
                totalErrors: this.metrics.totalErrors,
                criticalErrors: this.metrics.criticalErrors,
                resolvedErrors: this.metrics.resolvedErrors,
                pendingErrors: this.metrics.pendingErrors
            }
        };
        
        if (includeMetrics) {
            report.metrics = {
                ...this.metrics,
                categoryBreakdown: Object.fromEntries(this.metrics.categorizedErrors)
            };
        }
        
        if (includeHistory) {
            let history = this.errorHistory;
            
            if (timeRange) {
                const cutoff = new Date(Date.now() - timeRange);
                history = history.filter(entry => 
                    new Date(entry.timestamp) >= cutoff
                );
            }
            
            report.recentErrors = history.slice(-50); // Last 50 errors
        }
        
        if (includePatterns) {
            report.patterns = this.analyzePatternTrends();
        }
        
        return report;
    }
    
    /**
     * Helper methods
     */
    generateErrorId() {
        return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    calculateSimilarity(error1, error2) {
        // Simple similarity based on message and error type
        if (error1.name !== error2.name) return 0;
        
        const message1 = error1.message.toLowerCase();
        const message2 = error2.message.toLowerCase();
        
        // Jaccard similarity for messages
        const words1 = new Set(message1.split(' '));
        const words2 = new Set(message2.split(' '));
        
        const intersection = new Set([...words1].filter(x => words2.has(x)));
        const union = new Set([...words1, ...words2]);
        
        return intersection.size / union.size;
    }
    
    calculateTimeSpan(errors) {
        if (errors.length < 2) return 0;
        
        const times = errors.map(e => new Date(e.timestamp).getTime());
        return Math.max(...times) - Math.min(...times);
    }
    
    getRecentErrors(timeWindow) {
        const cutoff = Date.now() - timeWindow;
        return this.errorHistory.filter(entry => 
            new Date(entry.timestamp).getTime() >= cutoff
        );
    }
    
    analyzeContext(context) {
        // Placeholder for context analysis logic
        return null;
    }
    
    analyzeHistoricalPatterns(errorInfo) {
        // Placeholder for historical analysis logic
        return null;
    }
    
    analyzePatternTrends() {
        // Placeholder for pattern trend analysis
        return {};
    }
    
    async logDiagnostic(diagnostic) {
        if (!this.config.enableMetrics) return;
        
        try {
            await fs.mkdir(this.config.logDir, { recursive: true });
            
            const logFile = path.join(this.config.logDir, 'diagnostics.jsonl');
            const logEntry = JSON.stringify(diagnostic) + '\n';
            
            await fs.appendFile(logFile, logEntry);
        } catch (error) {
            // Ignore logging errors
        }
    }
}

module.exports = ErrorDiagnostics;
