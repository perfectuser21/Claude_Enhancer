/**
 * Claude Enhancer Plus - Git Integration Layer
 *
 * Unified interface for all Git optimizations
 * Integrates GitOptimizer, GitStatusCache, OptimizedHooks, and GitPerformanceMonitor
 */

const GitOptimizer = require('./GitOptimizer');
const GitStatusCache = require('./GitStatusCache');
const OptimizedHooks = require('./OptimizedHooks');
const GitPerformanceMonitor = require('./GitPerformanceMonitor');
const { EventEmitter } = require('events');
const fs = require('fs').promises;
const path = require('path');

class GitIntegration extends EventEmitter {
    constructor(repositoryPath = process.cwd(), options = {}) {
        super();

        this.repositoryPath = repositoryPath;
        this.options = {
            enableCaching: options.enableCaching !== false,
            enableMonitoring: options.enableMonitoring !== false,
            enableOptimizedHooks: options.enableOptimizedHooks !== false,
            enableBatching: options.enableBatching !== false,
            ...options
        };

        // 初始化组件
        this.gitOptimizer = null;
        this.statusCache = null;
        this.optimizedHooks = null;
        this.performanceMonitor = null;

        // 状态
        this.initialized = false;
        this.ready = false;

        this.init();
    }

    async init() {
        try {
            console.log('🚀 初始化Claude Enhancer Plus Git优化系统...');

            // 1. 初始化Git优化器
            this.gitOptimizer = new GitOptimizer({
                repositoryPath: this.repositoryPath,
                ...this.options
            });

            // 2. 初始化状态缓存
            if (this.options.enableCaching) {
                this.statusCache = new GitStatusCache(this.gitOptimizer, {
                    maxCacheAge: this.options.cacheMaxAge || 30000,
                    watchFiles: this.options.watchFiles !== false
                });
            }

            // 3. 初始化性能监控
            if (this.options.enableMonitoring) {
                this.performanceMonitor = new GitPerformanceMonitor(this.gitOptimizer);

                // 监听性能事件
                this.performanceMonitor.on('operation-end', (operation) => {
                    this.emit('performance-data', operation);
                });
            }

            // 4. 初始化优化的Hooks
            if (this.options.enableOptimizedHooks) {
                this.optimizedHooks = new OptimizedHooks(this.repositoryPath);
            }

            // 5. 设置组件间的集成
            this.setupIntegration();

            this.initialized = true;
            this.ready = true;

            console.log('✅ Git优化系统初始化完成');
            this.emit('ready');

        } catch (error) {
            console.error('❌ Git优化系统初始化失败:', error.message);
            this.emit('error', error);
            throw error;
        }
    }

    /**
     * 设置组件间的集成
     */
    setupIntegration() {
        // 集成性能监控到Git优化器
        if (this.performanceMonitor && this.gitOptimizer) {
            const originalExecuteGitCommand = this.gitOptimizer.executeGitCommand.bind(this.gitOptimizer);

            this.gitOptimizer.executeGitCommand = async (command, options = {}) => {
                const operationId = this.performanceMonitor.startOperation('git-command', {
                    command: command.split(' ')[0] // 只记录命令名
                });

                try {
                    const result = await originalExecuteGitCommand(command, options);
                    this.performanceMonitor.endOperation(operationId, { success: true });
                    return result;
                } catch (error) {
                    this.performanceMonitor.endOperation(operationId, { error: error.message });
                    throw error;
                }
            };
        }

        // 集成缓存事件到性能监控
        if (this.statusCache && this.performanceMonitor) {
            this.statusCache.on('cache-hit', (event) => {
                this.emit('cache-performance', { type: 'hit', ...event });
            });

            this.statusCache.on('cache-miss', (event) => {
                this.emit('cache-performance', { type: 'miss', ...event });
            });
        }
    }

    /**
     * 统一的Git状态查询接口
     */
    async getStatus(options = {}) {
        this.ensureReady();

        const startTime = Date.now();
        let operationId = null;

        try {
            if (this.performanceMonitor) {
                operationId = this.performanceMonitor.startOperation('unified-status', options);
            }

            let result;

            if (options.files && options.files.length > 0) {
                // 文件特定状态查询
                if (this.statusCache) {
                    result = await this.statusCache.getBatchFileStatus(options.files, options.forceRefresh);
                } else {
                    result = await this.gitOptimizer.getBatchedStatus(options.files);
                }
            } else {
                // 全局状态查询
                if (this.statusCache) {
                    result = await this.statusCache.getGlobalStatus(options.forceRefresh);
                } else {
                    result = await this.gitOptimizer.getBatchedStatus();
                }
            }

            const duration = Date.now() - startTime;

            if (operationId) {
                this.performanceMonitor.endOperation(operationId, {
                    success: true,
                    filesProcessed: options.files?.length || 'all'
                });
            }

            this.emit('status-query', { duration, result, options });
            return result;

        } catch (error) {
            if (operationId) {
                this.performanceMonitor.endOperation(operationId, { error: error.message });
            }

            this.emit('status-error', { error, options });
            throw error;
        }
    }

    /**
     * 统一的文件添加接口
     */
    async addFiles(files, options = {}) {
        this.ensureReady();

        const startTime = Date.now();
        let operationId = null;

        try {
            if (this.performanceMonitor) {
                operationId = this.performanceMonitor.startOperation('unified-add', {
                    fileCount: files.length,
                    ...options
                });
            }

            const result = await this.gitOptimizer.batchAdd(files);
            const duration = Date.now() - startTime;

            if (operationId) {
                this.performanceMonitor.endOperation(operationId, {
                    success: result.success,
                    filesAdded: result.addedFiles?.length || 0
                });
            }

            // 清除状态缓存
            if (this.statusCache) {
                this.statusCache.invalidateGlobalCache();
                files.forEach(file => this.statusCache.invalidateFileCache(file));
            }

            this.emit('files-added', { result, duration, files });
            return result;

        } catch (error) {
            if (operationId) {
                this.performanceMonitor.endOperation(operationId, { error: error.message });
            }

            this.emit('add-error', { error, files });
            throw error;
        }
    }

    /**
     * 执行优化的pre-commit检查
     */
    async runPreCommitChecks(options = {}) {
        this.ensureReady();

        if (!this.optimizedHooks) {
            throw new Error('优化Hooks未启用');
        }

        const startTime = Date.now();
        let operationId = null;

        try {
            if (this.performanceMonitor) {
                operationId = this.performanceMonitor.startOperation('pre-commit-checks', options);
            }

            const result = await this.optimizedHooks.executePreCommit();
            const duration = Date.now() - startTime;

            if (operationId) {
                this.performanceMonitor.endOperation(operationId, {
                    success: result.success,
                    checksRun: 'all'
                });
            }

            this.emit('pre-commit-result', { result, duration });
            return result;

        } catch (error) {
            if (operationId) {
                this.performanceMonitor.endOperation(operationId, { error: error.message });
            }

            this.emit('pre-commit-error', { error });
            throw error;
        }
    }

    /**
     * 获取分支信息
     */
    async getBranchInfo(options = {}) {
        this.ensureReady();

        const operationId = this.performanceMonitor?.startOperation('branch-info', options);

        try {
            const result = await this.gitOptimizer.getBranchInfo();

            if (operationId) {
                this.performanceMonitor.endOperation(operationId, { success: true });
            }

            return result;

        } catch (error) {
            if (operationId) {
                this.performanceMonitor.endOperation(operationId, { error: error.message });
            }

            throw error;
        }
    }

    /**
     * 获取提交历史
     */
    async getCommitHistory(options = {}) {
        this.ensureReady();

        const operationId = this.performanceMonitor?.startOperation('commit-history', options);

        try {
            const result = await this.gitOptimizer.getCommitHistory(options);

            if (operationId) {
                this.performanceMonitor.endOperation(operationId, {
                    success: true,
                    commitsRetrieved: result.length
                });
            }

            return result;

        } catch (error) {
            if (operationId) {
                this.performanceMonitor.endOperation(operationId, { error: error.message });
            }

            throw error;
        }
    }

    /**
     * 智能差异检查
     */
    async getDiff(options = {}) {
        this.ensureReady();

        const operationId = this.performanceMonitor?.startOperation('intelligent-diff', options);

        try {
            const result = await this.gitOptimizer.getIntelligentDiff(options);

            if (operationId) {
                this.performanceMonitor.endOperation(operationId, { success: true });
            }

            return result;

        } catch (error) {
            if (operationId) {
                this.performanceMonitor.endOperation(operationId, { error: error.message });
            }

            throw error;
        }
    }

    /**
     * 获取综合性能报告
     */
    getPerformanceReport() {
        this.ensureReady();

        const report = {
            timestamp: Date.now(),
            system: {
                initialized: this.initialized,
                ready: this.ready,
                components: {
                    gitOptimizer: !!this.gitOptimizer,
                    statusCache: !!this.statusCache,
                    optimizedHooks: !!this.optimizedHooks,
                    performanceMonitor: !!this.performanceMonitor
                }
            },
            optimizer: this.gitOptimizer?.getPerformanceStats() || null,
            cache: this.statusCache?.getStats() || null,
            hooks: this.optimizedHooks?.getPerformanceStats() || null,
            monitor: this.performanceMonitor?.getPerformanceReport() || null
        };

        return report;
    }

    /**
     * 优化建议
     */
    getOptimizationSuggestions() {
        const suggestions = [];

        // 缓存建议
        if (this.statusCache) {
            const cacheStats = this.statusCache.getStats();
            if (cacheStats.hitRate && parseFloat(cacheStats.hitRate) < 60) {
                suggestions.push({
                    type: 'caching',
                    priority: 'high',
                    message: '状态缓存命中率较低，建议增加缓存时间或优化查询模式',
                    action: '调整maxCacheAge参数或减少forceRefresh调用'
                });
            }
        }

        // 性能监控建议
        if (this.performanceMonitor) {
            const monitorReport = this.performanceMonitor.getPerformanceReport();
            if (monitorReport.optimization.suggestions) {
                suggestions.push(...monitorReport.optimization.suggestions.map(s => ({
                    ...s,
                    source: 'performance-monitor'
                })));
            }
        }

        return suggestions;
    }

    /**
     * 导出配置用于hook脚本
     */
    async exportConfigForHooks() {
        const config = {
            optimizerAvailable: !!this.gitOptimizer,
            cacheAvailable: !!this.statusCache,
            hooksAvailable: !!this.optimizedHooks,
            monitoringEnabled: !!this.performanceMonitor,
            repositoryPath: this.repositoryPath,
            options: this.options
        };

        const configPath = path.join(this.repositoryPath, '.claude', 'git-integration-config.json');
        await fs.writeFile(configPath, JSON.stringify(config, null, 2));

        return configPath;
    }

    /**
     * 确保系统已就绪
     */
    ensureReady() {
        if (!this.ready) {
            throw new Error('Git优化系统尚未就绪，请等待初始化完成');
        }
    }

    /**
     * 健康检查
     */
    async healthCheck() {
        const health = {
            overall: 'healthy',
            components: {},
            issues: []
        };

        try {
            // 检查Git优化器
            if (this.gitOptimizer) {
                const gitStats = await this.gitOptimizer.getPerformanceStats();
                health.components.gitOptimizer = {
                    status: 'healthy',
                    cacheSize: gitStats.cacheSize,
                    uptime: gitStats.uptime
                };
            }

            // 检查状态缓存
            if (this.statusCache) {
                const cacheStats = this.statusCache.getStats();
                health.components.statusCache = {
                    status: 'healthy',
                    cacheSize: cacheStats.cacheSize,
                    watchers: cacheStats.watchers
                };
            }

            // 检查性能监控
            if (this.performanceMonitor) {
                const monitorStats = this.performanceMonitor.getPerformanceReport();
                health.components.performanceMonitor = {
                    status: 'healthy',
                    totalOperations: monitorStats.summary.totalOperations,
                    activeOperations: monitorStats.summary.currentOperations
                };
            }

            // 检查优化Hooks
            if (this.optimizedHooks) {
                const hooksStats = this.optimizedHooks.getPerformanceStats();
                health.components.optimizedHooks = {
                    status: 'healthy',
                    totalRuns: hooksStats.totalRuns,
                    fastExits: hooksStats.fastExits
                };
            }

        } catch (error) {
            health.overall = 'degraded';
            health.issues.push(`健康检查失败: ${error.message}`);
        }

        return health;
    }

    /**
     * 清理所有资源
     */
    cleanup() {
        console.log('🧹 清理Git优化系统资源...');

        if (this.gitOptimizer) {
            this.gitOptimizer.cleanup();
        }

        if (this.statusCache) {
            this.statusCache.cleanup();
        }

        if (this.optimizedHooks) {
            this.optimizedHooks.cleanup();
        }

        if (this.performanceMonitor) {
            this.performanceMonitor.cleanup();
        }

        this.removeAllListeners();
        this.ready = false;

        console.log('✅ 资源清理完成');
    }
}

module.exports = GitIntegration;