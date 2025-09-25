/**
 * Claude Enhancer Plus - Git Performance Monitor
 *
 * Real-time monitoring and optimization suggestions for Git operations
 * Provides insights into Git performance bottlenecks
 */

const fs = require('fs').promises;
const path = require('path');
const { EventEmitter } = require('events');

class GitPerformanceMonitor extends EventEmitter {
    constructor(gitOptimizer, options = {}) {
        super();

        this.gitOptimizer = gitOptimizer;
        this.repositoryPath = gitOptimizer.repositoryPath;
        this.logFile = path.join(this.repositoryPath, '.claude', 'logs', 'git-performance.log');

        // 性能阈值
        this.thresholds = {
            fast: options.fastThreshold || 100,    // 100ms
            medium: options.mediumThreshold || 500, // 500ms
            slow: options.slowThreshold || 1000,   // 1s
            verySlow: options.verySlowThreshold || 3000 // 3s
        };

        // 统计数据
        this.stats = {
            totalOperations: 0,
            fastOperations: 0,
            slowOperations: 0,
            totalTime: 0,
            averageTime: 0,
            commandFrequency: new Map(),
            slowestOperations: [],
            cacheHitRate: 0,
            optimizationSuggestions: []
        };

        // 实时监控
        this.realtimeMetrics = {
            currentOperations: new Set(),
            recentOperations: [], // 最近100个操作
            bottlenecks: new Map()
        };

        this.init();
    }

    async init() {
        try {
            await fs.mkdir(path.dirname(this.logFile), { recursive: true });
            await this.loadHistoricalData();
            this.startRealTimeMonitoring();
        } catch (error) {
            console.warn('Git性能监控初始化警告:', error.message);
        }
    }

    /**
     * 开始操作监控
     */
    startOperation(operationName, details = {}) {
        const operation = {
            id: this.generateOperationId(),
            name: operationName,
            details,
            startTime: Date.now(),
            status: 'running'
        };

        this.realtimeMetrics.currentOperations.add(operation);
        this.emit('operation-start', operation);

        return operation.id;
    }

    /**
     * 结束操作监控
     */
    endOperation(operationId, result = {}) {
        const operation = Array.from(this.realtimeMetrics.currentOperations)
            .find(op => op.id === operationId);

        if (!operation) {
            console.warn('未找到操作ID:', operationId);
            return;
        }

        const endTime = Date.now();
        const duration = endTime - operation.startTime;

        // 更新操作信息
        operation.endTime = endTime;
        operation.duration = duration;
        operation.result = result;
        operation.status = result.error ? 'failed' : 'completed';

        // 从当前操作中移除
        this.realtimeMetrics.currentOperations.delete(operation);

        // 添加到最近操作
        this.addToRecentOperations(operation);

        // 更新统计数据
        this.updateStatistics(operation);

        // 检查性能并生成建议
        this.analyzePerformance(operation);

        // 记录日志
        this.logOperation(operation);

        this.emit('operation-end', operation);
        return operation;
    }

    /**
     * 批量操作监控
     */
    monitorBatchOperation(operations) {
        const batchId = this.generateOperationId();
        const batchStartTime = Date.now();

        const operationIds = operations.map(op => {
            return this.startOperation(op.name, { ...op.details, batchId });
        });

        return {
            batchId,
            operationIds,
            end: (results = []) => {
                const batchEndTime = Date.now();
                const batchDuration = batchEndTime - batchStartTime;

                // 结束各个操作
                operationIds.forEach((id, index) => {
                    this.endOperation(id, results[index] || {});
                });

                // 分析批量操作性能
                this.analyzeBatchPerformance(batchId, batchDuration, operationIds.length);

                return {
                    batchId,
                    duration: batchDuration,
                    operations: operationIds.length
                };
            }
        };
    }

    /**
     * 实时性能分析
     */
    analyzePerformance(operation) {
        const { name, duration } = operation;

        // 性能分类
        if (duration > this.thresholds.verySlow) {
            this.recordBottleneck(name, duration, 'very-slow');
            this.generateOptimizationSuggestion(operation, 'very-slow');
        } else if (duration > this.thresholds.slow) {
            this.recordBottleneck(name, duration, 'slow');
            this.generateOptimizationSuggestion(operation, 'slow');
        }

        // 检查重复慢操作
        this.checkForRepeatedSlowOperations(name, duration);
    }

    /**
     * 记录性能瓶颈
     */
    recordBottleneck(operationName, duration, severity) {
        const key = `${operationName}-${severity}`;
        const existing = this.realtimeMetrics.bottlenecks.get(key);

        this.realtimeMetrics.bottlenecks.set(key, {
            operation: operationName,
            severity,
            count: (existing?.count || 0) + 1,
            totalDuration: (existing?.totalDuration || 0) + duration,
            averageDuration: ((existing?.totalDuration || 0) + duration) / ((existing?.count || 0) + 1),
            lastOccurrence: Date.now()
        });
    }

    /**
     * 生成优化建议
     */
    generateOptimizationSuggestion(operation, severity) {
        const suggestions = [];

        switch (operation.name) {
            case 'git-status':
                if (severity === 'very-slow') {
                    suggestions.push({
                        type: 'caching',
                        message: 'git status查询过慢，建议启用状态缓存',
                        solution: '使用GitStatusCache进行状态缓存'
                    });
                }
                break;

            case 'git-diff':
                if (severity === 'slow') {
                    suggestions.push({
                        type: 'batching',
                        message: 'git diff操作较慢，建议批量处理',
                        solution: '使用getBatchedStatus合并多个diff查询'
                    });
                }
                break;

            case 'git-add':
                if (severity === 'slow') {
                    suggestions.push({
                        type: 'batching',
                        message: 'git add操作较慢，建议批量添加文件',
                        solution: '使用batchAdd一次添加多个文件'
                    });
                }
                break;
        }

        // 添加到建议列表
        suggestions.forEach(suggestion => {
            this.stats.optimizationSuggestions.push({
                ...suggestion,
                timestamp: Date.now(),
                operation: operation.name,
                duration: operation.duration
            });
        });

        // 限制建议数量
        if (this.stats.optimizationSuggestions.length > 50) {
            this.stats.optimizationSuggestions = this.stats.optimizationSuggestions.slice(-50);
        }
    }

    /**
     * 检查重复的慢操作
     */
    checkForRepeatedSlowOperations(operationName, duration) {
        const recentSameOps = this.realtimeMetrics.recentOperations
            .filter(op => op.name === operationName && op.duration > this.thresholds.medium)
            .slice(-5); // 最近5次相同操作

        if (recentSameOps.length >= 3) {
            const avgDuration = recentSameOps.reduce((sum, op) => sum + op.duration, 0) / recentSameOps.length;

            this.generateOptimizationSuggestion({
                name: operationName,
                duration: avgDuration
            }, 'repeated-slow');
        }
    }

    /**
     * 批量操作性能分析
     */
    analyzeBatchPerformance(batchId, totalDuration, operationCount) {
        const avgOperationTime = totalDuration / operationCount;

        if (avgOperationTime > this.thresholds.medium) {
            this.stats.optimizationSuggestions.push({
                type: 'batch-optimization',
                message: `批量操作 ${batchId} 平均执行时间较长 (${avgOperationTime}ms)`,
                solution: '考虑增加并行度或使用更高效的批量API',
                timestamp: Date.now()
            });
        }
    }

    /**
     * 更新统计数据
     */
    updateStatistics(operation) {
        this.stats.totalOperations++;
        this.stats.totalTime += operation.duration;
        this.stats.averageTime = this.stats.totalTime / this.stats.totalOperations;

        // 分类统计
        if (operation.duration <= this.thresholds.fast) {
            this.stats.fastOperations++;
        } else if (operation.duration >= this.thresholds.slow) {
            this.stats.slowOperations++;
        }

        // 命令频率统计
        const count = this.stats.commandFrequency.get(operation.name) || 0;
        this.stats.commandFrequency.set(operation.name, count + 1);

        // 记录最慢操作
        this.updateSlowestOperations(operation);
    }

    /**
     * 更新最慢操作记录
     */
    updateSlowestOperations(operation) {
        this.stats.slowestOperations.push({
            name: operation.name,
            duration: operation.duration,
            timestamp: operation.startTime,
            details: operation.details
        });

        // 按持续时间排序并保留前10个
        this.stats.slowestOperations.sort((a, b) => b.duration - a.duration);
        if (this.stats.slowestOperations.length > 10) {
            this.stats.slowestOperations = this.stats.slowestOperations.slice(0, 10);
        }
    }

    /**
     * 添加到最近操作
     */
    addToRecentOperations(operation) {
        this.realtimeMetrics.recentOperations.push(operation);

        // 保持最近100个操作
        if (this.realtimeMetrics.recentOperations.length > 100) {
            this.realtimeMetrics.recentOperations = this.realtimeMetrics.recentOperations.slice(-100);
        }
    }

    /**
     * 获取性能报告
     */
    getPerformanceReport() {
        const now = Date.now();

        // 计算缓存命中率
        const gitStats = this.gitOptimizer.getPerformanceStats();
        this.stats.cacheHitRate = parseFloat(gitStats.cacheHitRate) || 0;

        // 最近性能趋势
        const recentOps = this.realtimeMetrics.recentOperations.slice(-20);
        const recentAvgTime = recentOps.length > 0 ?
            recentOps.reduce((sum, op) => sum + op.duration, 0) / recentOps.length : 0;

        return {
            summary: {
                totalOperations: this.stats.totalOperations,
                averageTime: Math.round(this.stats.averageTime),
                recentAverageTime: Math.round(recentAvgTime),
                cacheHitRate: this.stats.cacheHitRate,
                fastOperationsPercent: Math.round((this.stats.fastOperations / this.stats.totalOperations) * 100),
                currentOperations: this.realtimeMetrics.currentOperations.size
            },
            performance: {
                slowestOperations: this.stats.slowestOperations,
                bottlenecks: Array.from(this.realtimeMetrics.bottlenecks.values()),
                commandFrequency: Object.fromEntries(this.stats.commandFrequency)
            },
            optimization: {
                suggestions: this.stats.optimizationSuggestions.slice(-10),
                potentialImprovements: this.calculatePotentialImprovements()
            },
            realtime: {
                recentOperations: this.realtimeMetrics.recentOperations.slice(-5),
                activeOperations: Array.from(this.realtimeMetrics.currentOperations)
            }
        };
    }

    /**
     * 计算潜在改进
     */
    calculatePotentialImprovements() {
        const improvements = [];

        // 缓存改进潜力
        if (this.stats.cacheHitRate < 50) {
            improvements.push({
                type: 'caching',
                impact: 'high',
                description: '提高缓存命中率可减少40-60%的Git操作时间',
                currentValue: `${this.stats.cacheHitRate}%`,
                targetValue: '70%+'
            });
        }

        // 批量操作改进
        const singleOpsCount = this.stats.commandFrequency.get('git-status') || 0;
        if (singleOpsCount > this.stats.totalOperations * 0.6) {
            improvements.push({
                type: 'batching',
                impact: 'medium',
                description: '使用批量操作可减少20-40%的执行时间',
                currentValue: `${Math.round(singleOpsCount / this.stats.totalOperations * 100)}% 单次操作`,
                targetValue: '<40% 单次操作'
            });
        }

        return improvements;
    }

    /**
     * 开始实时监控
     */
    startRealTimeMonitoring() {
        // 每分钟清理过期数据
        setInterval(() => {
            this.cleanupExpiredData();
        }, 60000);

        // 每5分钟保存统计数据
        setInterval(() => {
            this.saveStatistics();
        }, 300000);
    }

    /**
     * 清理过期数据
     */
    cleanupExpiredData() {
        const oneHourAgo = Date.now() - 3600000; // 1小时前

        // 清理过期的瓶颈记录
        for (const [key, bottleneck] of this.realtimeMetrics.bottlenecks) {
            if (bottleneck.lastOccurrence < oneHourAgo) {
                this.realtimeMetrics.bottlenecks.delete(key);
            }
        }

        // 清理过期的优化建议
        this.stats.optimizationSuggestions = this.stats.optimizationSuggestions
            .filter(suggestion => suggestion.timestamp > oneHourAgo);
    }

    /**
     * 记录操作日志
     */
    async logOperation(operation) {
        try {
            const logEntry = {
                timestamp: new Date(operation.startTime).toISOString(),
                operation: operation.name,
                duration: operation.duration,
                status: operation.status,
                details: operation.details
            };

            const logLine = JSON.stringify(logEntry) + '\n';
            await fs.appendFile(this.logFile, logLine);
        } catch (error) {
            // 日志写入失败不影响主流程
            console.warn('性能日志写入失败:', error.message);
        }
    }

    /**
     * 加载历史数据
     */
    async loadHistoricalData() {
        try {
            const data = await fs.readFile(this.logFile, 'utf-8');
            const lines = data.split('\n').filter(Boolean);

            // 分析最近1000条记录
            const recentLines = lines.slice(-1000);
            for (const line of recentLines) {
                try {
                    const entry = JSON.parse(line);
                    this.updateHistoricalStats(entry);
                } catch {
                    // 跳过无效的日志行
                }
            }
        } catch {
            // 历史数据不存在，使用默认值
        }
    }

    /**
     * 更新历史统计
     */
    updateHistoricalStats(entry) {
        // 基于历史数据更新统计信息
        const duration = entry.duration;
        this.stats.totalTime += duration;

        if (duration <= this.thresholds.fast) {
            this.stats.fastOperations++;
        } else if (duration >= this.thresholds.slow) {
            this.stats.slowOperations++;
        }

        const count = this.stats.commandFrequency.get(entry.operation) || 0;
        this.stats.commandFrequency.set(entry.operation, count + 1);
    }

    /**
     * 保存统计数据
     */
    async saveStatistics() {
        try {
            const statsFile = path.join(path.dirname(this.logFile), 'git-stats.json');
            const statsData = {
                timestamp: Date.now(),
                stats: this.stats,
                metrics: this.realtimeMetrics
            };

            await fs.writeFile(statsFile, JSON.stringify(statsData, null, 2));
        } catch (error) {
            console.warn('统计数据保存失败:', error.message);
        }
    }

    /**
     * 工具函数
     */
    generateOperationId() {
        return `op_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * 清理资源
     */
    cleanup() {
        this.saveStatistics();
        this.removeAllListeners();
    }
}

module.exports = GitPerformanceMonitor;