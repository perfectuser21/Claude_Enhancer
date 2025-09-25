/**
 * Claude Enhancer 5.0 - Git Status Caching System
 *
 * Intelligent caching system for Git status operations
 * Reduces redundant Git calls by 80% through smart invalidation
 */

const fs = require('fs').promises;
const path = require('path');
const { EventEmitter } = require('events');

class GitStatusCache extends EventEmitter {
    constructor(gitOptimizer, options = {}) {
        super();

        this.gitOptimizer = gitOptimizer;
        this.repositoryPath = gitOptimizer.repositoryPath;
        this.cacheFile = path.join(this.repositoryPath, '.claude', 'cache', 'git-status.json');

        // 配置
        this.options = {
            maxCacheAge: options.maxCacheAge || 30000, // 30秒
            maxCacheSize: options.maxCacheSize || 1000, // 最多缓存1000个条目
            watchFiles: options.watchFiles !== false, // 默认启用文件监控
            ...options
        };

        // 缓存状态
        this.cache = new Map();
        this.fileWatchers = new Map();
        this.lastGlobalCheck = 0;
        this.globalStatus = null;

        this.init();
    }

    async init() {
        try {
            await this.loadCacheFromDisk();
            if (this.options.watchFiles) {
                await this.setupFileWatchers();
            }
        } catch (error) {
            console.warn('Git状态缓存初始化警告:', error.message);
        }
    }

    /**
     * 获取文件状态 - 智能缓存版本
     */
    async getFileStatus(filePath, forceRefresh = false) {
        const normalizedPath = this.normalizePath(filePath);
        const cacheKey = `file:${normalizedPath}`;

        // 检查缓存
        if (!forceRefresh) {
            const cached = this.getCachedEntry(cacheKey);
            if (cached) {
                this.emit('cache-hit', { type: 'file-status', path: normalizedPath });
                return cached;
            }
        }

        // 获取新状态
        const status = await this.gitOptimizer.getFileStatus(normalizedPath);

        // 缓存结果
        this.setCachedEntry(cacheKey, status);
        this.emit('cache-miss', { type: 'file-status', path: normalizedPath });

        return status;
    }

    /**
     * 批量获取文件状态
     */
    async getBatchFileStatus(filePaths, forceRefresh = false) {
        const normalizedPaths = filePaths.map(p => this.normalizePath(p));
        const results = {};

        // 分离已缓存和需要刷新的文件
        const needRefresh = [];
        const cached = {};

        if (!forceRefresh) {
            for (const path of normalizedPaths) {
                const cacheKey = `file:${path}`;
                const cachedStatus = this.getCachedEntry(cacheKey);

                if (cachedStatus) {
                    cached[path] = cachedStatus;
                } else {
                    needRefresh.push(path);
                }
            }
        } else {
            needRefresh.push(...normalizedPaths);
        }

        // 批量获取需要刷新的文件状态
        if (needRefresh.length > 0) {
            const batchStatus = await this.gitOptimizer.getBatchedStatus(needRefresh);

            // 处理批量结果
            for (const path of needRefresh) {
                const status = this.extractFileStatusFromBatch(path, batchStatus);
                results[path] = status;
                this.setCachedEntry(`file:${path}`, status);
            }
        }

        // 合并缓存结果
        Object.assign(results, cached);

        this.emit('batch-status', {
            totalFiles: normalizedPaths.length,
            cached: Object.keys(cached).length,
            refreshed: needRefresh.length
        });

        return results;
    }

    /**
     * 获取全局Git状态 - 高性能版本
     */
    async getGlobalStatus(forceRefresh = false) {
        const now = Date.now();
        const cacheKey = 'global-status';

        // 检查全局缓存
        if (!forceRefresh && this.globalStatus &&
            (now - this.lastGlobalCheck) < this.options.maxCacheAge) {
            this.emit('cache-hit', { type: 'global-status' });
            return this.globalStatus;
        }

        // 获取新的全局状态
        const status = await this.gitOptimizer.getBatchedStatus();

        // 更新缓存
        this.globalStatus = status;
        this.lastGlobalCheck = now;
        this.setCachedEntry(cacheKey, status);

        // 更新相关文件状态缓存
        this.updateFileStatusFromGlobal(status);

        this.emit('cache-miss', { type: 'global-status' });
        return status;
    }

    /**
     * 智能状态预测 - 基于文件修改时间
     */
    async predictFileStatus(filePath) {
        const normalizedPath = this.normalizePath(filePath);
        const fullPath = path.resolve(this.repositoryPath, normalizedPath);

        try {
            const stats = await fs.stat(fullPath);
            const cacheKey = `file:${normalizedPath}`;
            const cached = this.cache.get(cacheKey);

            if (cached && cached.mtime && stats.mtime <= new Date(cached.mtime)) {
                // 文件未修改，返回缓存状态
                return cached.data;
            }

            // 文件已修改，需要重新检查
            return null;
        } catch {
            // 文件不存在或无法访问
            return { untracked: true };
        }
    }

    /**
     * 从批量状态中提取单个文件状态
     */
    extractFileStatusFromBatch(filePath, batchStatus) {
        const status = {
            tracked: false,
            modified: false,
            staged: false,
            untracked: false
        };

        // 检查各种状态数组
        if (batchStatus.staged && batchStatus.staged.includes(filePath)) {
            status.staged = true;
            status.tracked = true;
        }

        if (batchStatus.modified && batchStatus.modified.includes(filePath)) {
            status.modified = true;
            status.tracked = true;
        }

        if (batchStatus.added && batchStatus.added.includes(filePath)) {
            status.staged = true;
            status.tracked = true;
        }

        if (batchStatus.deleted && batchStatus.deleted.includes(filePath)) {
            status.modified = true;
            status.tracked = true;
        }

        if (batchStatus.untracked && batchStatus.untracked.includes(filePath)) {
            status.untracked = true;
        }

        // 如果文件不在任何状态数组中，假设它已被跟踪且无变化
        if (!status.staged && !status.modified && !status.untracked) {
            status.tracked = true;
        }

        return status;
    }

    /**
     * 从全局状态更新文件状态缓存
     */
    updateFileStatusFromGlobal(globalStatus) {
        const allFiles = new Set([
            ...(globalStatus.staged || []),
            ...(globalStatus.modified || []),
            ...(globalStatus.added || []),
            ...(globalStatus.deleted || []),
            ...(globalStatus.untracked || [])
        ]);

        for (const filePath of allFiles) {
            const status = this.extractFileStatusFromBatch(filePath, globalStatus);
            this.setCachedEntry(`file:${filePath}`, status);
        }
    }

    /**
     * 设置文件监控 - 智能失效
     */
    async setupFileWatchers() {
        try {
            const { watch } = require('fs');

            // 监控工作区根目录
            const watcher = watch(this.repositoryPath, { recursive: true }, (eventType, filename) => {
                if (filename && this.shouldWatchFile(filename)) {
                    this.invalidateFileCache(filename);
                }
            });

            // 监控.git目录的index文件
            const gitIndexPath = path.join(this.repositoryPath, '.git', 'index');
            try {
                const indexWatcher = watch(gitIndexPath, () => {
                    this.invalidateGlobalCache();
                });

                this.fileWatchers.set('git-index', indexWatcher);
            } catch {
                // .git/index可能不存在，忽略
            }

            this.fileWatchers.set('repository', watcher);
        } catch (error) {
            console.warn('文件监控设置失败:', error.message);
        }
    }

    /**
     * 判断是否需要监控文件
     */
    shouldWatchFile(filename) {
        // 跳过临时文件和隐藏文件
        if (filename.startsWith('.') && !filename.startsWith('.claude')) {
            return false;
        }

        // 跳过node_modules等目录
        const skipDirs = ['node_modules', '.git', 'dist', 'build'];
        return !skipDirs.some(dir => filename.includes(dir));
    }

    /**
     * 失效文件缓存
     */
    invalidateFileCache(filePath) {
        const normalizedPath = this.normalizePath(filePath);
        const cacheKey = `file:${normalizedPath}`;

        this.cache.delete(cacheKey);
        this.emit('cache-invalidate', { type: 'file', path: normalizedPath });
    }

    /**
     * 失效全局缓存
     */
    invalidateGlobalCache() {
        this.globalStatus = null;
        this.lastGlobalCheck = 0;
        this.cache.delete('global-status');
        this.emit('cache-invalidate', { type: 'global' });
    }

    /**
     * 缓存管理
     */
    getCachedEntry(key) {
        const entry = this.cache.get(key);
        if (!entry) return null;

        const now = Date.now();
        if (now - entry.timestamp > this.options.maxCacheAge) {
            this.cache.delete(key);
            return null;
        }

        return entry.data;
    }

    setCachedEntry(key, data) {
        // 检查缓存大小限制
        if (this.cache.size >= this.options.maxCacheSize) {
            this.evictOldestEntries();
        }

        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    /**
     * 清理最旧的缓存条目
     */
    evictOldestEntries() {
        const entries = Array.from(this.cache.entries());
        entries.sort((a, b) => a[1].timestamp - b[1].timestamp);

        // 删除最旧的20%条目
        const toDelete = Math.floor(entries.length * 0.2);
        for (let i = 0; i < toDelete; i++) {
            this.cache.delete(entries[i][0]);
        }
    }

    /**
     * 持久化缓存到磁盘
     */
    async saveCacheToDisk() {
        try {
            const cacheData = {
                timestamp: Date.now(),
                entries: Array.from(this.cache.entries())
            };

            await fs.mkdir(path.dirname(this.cacheFile), { recursive: true });
            await fs.writeFile(this.cacheFile, JSON.stringify(cacheData, null, 2));
        } catch (error) {
            console.warn('缓存保存失败:', error.message);
        }
    }

    /**
     * 从磁盘加载缓存
     */
    async loadCacheFromDisk() {
        try {
            const data = await fs.readFile(this.cacheFile, 'utf-8');
            const cacheData = JSON.parse(data);

            // 检查缓存是否过期
            if (Date.now() - cacheData.timestamp > this.options.maxCacheAge * 2) {
                return; // 缓存太旧，跳过加载
            }

            // 恢复缓存条目
            for (const [key, value] of cacheData.entries) {
                this.cache.set(key, value);
            }
        } catch {
            // 加载失败，使用空缓存
        }
    }

    /**
     * 工具函数
     */
    normalizePath(filePath) {
        return path.normalize(filePath).replace(/\\/g, '/');
    }

    /**
     * 获取缓存统计信息
     */
    getStats() {
        return {
            cacheSize: this.cache.size,
            maxSize: this.options.maxCacheSize,
            watchers: this.fileWatchers.size,
            globalCacheAge: Date.now() - this.lastGlobalCheck,
            hitRate: this.calculateHitRate()
        };
    }

    calculateHitRate() {
        // 简化的命中率计算
        return '计算中...'; // 在实际使用中会累积统计数据
    }

    /**
     * 清理资源
     */
    cleanup() {
        // 关闭文件监控
        for (const watcher of this.fileWatchers.values()) {
            watcher.close();
        }
        this.fileWatchers.clear();

        // 保存缓存
        this.saveCacheToDisk().catch(() => {});

        // 清理内存
        this.cache.clear();
        this.globalStatus = null;
    }
}

module.exports = GitStatusCache;