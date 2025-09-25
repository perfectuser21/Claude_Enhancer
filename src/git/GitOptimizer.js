/**
 * Claude Enhancer Plus - Git Operations Optimizer
 *
 * High-performance Git operations with intelligent caching and batching
 * Target: 60% performance improvement through optimized Git operations
 */

const { spawn, exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

class GitOptimizer {
    constructor(options = {}) {
        this.repositoryPath = options.repositoryPath || process.cwd();
        this.cacheDir = path.join(this.repositoryPath, '.claude', 'cache', 'git');
        this.cacheTTL = options.cacheTTL || 30000; // 30秒缓存
        this.batchInterval = options.batchInterval || 100; // 100ms批处理间隔
        this.maxConcurrentOps = options.maxConcurrentOps || 5;

        // 内存缓存
        this.cache = new Map();
        this.pendingBatches = new Map();
        this.runningOperations = new Set();

        this.init();
    }

    async init() {
        try {
            await fs.mkdir(this.cacheDir, { recursive: true });
            await this.warmupCache();
        } catch (error) {
            console.warn('Git cache初始化警告:', error.message);
        }
    }

    /**
     * 预热缓存 - 缓存常用Git信息
     */
    async warmupCache() {
        const warmupOps = [
            { key: 'status', cmd: 'git status --porcelain' },
            { key: 'branch', cmd: 'git rev-parse --abbrev-ref HEAD' },
            { key: 'remote', cmd: 'git remote -v' },
            { key: 'config', cmd: 'git config --list --local' }
        ];

        const promises = warmupOps.map(op =>
            this.executeGitCommand(op.cmd)
                .then(result => this.setCacheEntry(op.key, result))
                .catch(() => {}) // 忽略预热失败
        );

        await Promise.allSettled(promises);
    }

    /**
     * 批量Git状态检查 - 核心优化功能
     */
    async getBatchedStatus(files = []) {
        const cacheKey = `status-batch-${this.hashFiles(files)}`;

        // 检查缓存
        const cached = this.getCacheEntry(cacheKey);
        if (cached) {
            return cached;
        }

        // 构建优化的状态检查命令
        let cmd = 'git status --porcelain';
        if (files.length > 0) {
            const fileArgs = files.map(f => `"${f}"`).join(' ');
            cmd += ` -- ${fileArgs}`;
        }

        const result = await this.executeGitCommand(cmd);
        const statusData = this.parseGitStatus(result);

        // 缓存结果
        this.setCacheEntry(cacheKey, statusData);
        return statusData;
    }

    /**
     * 智能差异检查 - 只检查真正改变的文件
     */
    async getIntelligentDiff(options = {}) {
        const cacheKey = `diff-${JSON.stringify(options)}`;
        const cached = this.getCacheEntry(cacheKey);
        if (cached) return cached;

        let cmd = 'git diff';

        if (options.cached) cmd += ' --cached';
        if (options.nameOnly) cmd += ' --name-only';
        if (options.files && options.files.length > 0) {
            cmd += ' -- ' + options.files.map(f => `"${f}"`).join(' ');
        }

        const result = await this.executeGitCommand(cmd);
        this.setCacheEntry(cacheKey, result);
        return result;
    }

    /**
     * 批量添加操作 - 优化多文件添加
     */
    async batchAdd(files) {
        if (!Array.isArray(files) || files.length === 0) {
            return { success: true, message: '没有文件需要添加' };
        }

        // 验证文件存在性
        const existingFiles = [];
        for (const file of files) {
            try {
                await fs.access(path.resolve(this.repositoryPath, file));
                existingFiles.push(file);
            } catch {
                console.warn(`文件不存在，跳过: ${file}`);
            }
        }

        if (existingFiles.length === 0) {
            return { success: false, message: '没有有效文件可添加' };
        }

        // 批量添加 - 单个命令处理多个文件
        const fileArgs = existingFiles.map(f => `"${f}"`).join(' ');
        const cmd = `git add ${fileArgs}`;

        try {
            await this.executeGitCommand(cmd);
            this.invalidateCache(['status']); // 状态缓存失效
            return { success: true, addedFiles: existingFiles };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * 高性能文件状态检查
     */
    async getFileStatus(filePath) {
        const cacheKey = `file-status-${filePath}`;
        const cached = this.getCacheEntry(cacheKey);
        if (cached) return cached;

        try {
            const statusOutput = await this.executeGitCommand(
                `git status --porcelain -- "${filePath}"`
            );

            const status = {
                tracked: false,
                modified: false,
                staged: false,
                untracked: false
            };

            if (statusOutput.trim()) {
                const line = statusOutput.trim();
                const indexStatus = line.charAt(0);
                const workTreeStatus = line.charAt(1);

                status.tracked = indexStatus !== '?' && workTreeStatus !== '?';
                status.untracked = indexStatus === '?' && workTreeStatus === '?';
                status.staged = indexStatus !== ' ' && indexStatus !== '?';
                status.modified = workTreeStatus !== ' ' && workTreeStatus !== '?';
            } else {
                status.tracked = true; // 文件被跟踪且无变化
            }

            this.setCacheEntry(cacheKey, status, 5000); // 5秒短期缓存
            return status;
        } catch (error) {
            return { error: error.message };
        }
    }

    /**
     * 分支信息缓存优化
     */
    async getBranchInfo() {
        const cacheKey = 'branch-info';
        const cached = this.getCacheEntry(cacheKey);
        if (cached) return cached;

        try {
            const [currentBranch, remoteBranches, trackingInfo] = await Promise.all([
                this.executeGitCommand('git rev-parse --abbrev-ref HEAD'),
                this.executeGitCommand('git branch -r'),
                this.executeGitCommand('git status --porcelain=v1 --branch').catch(() => '')
            ]);

            const info = {
                current: currentBranch.trim(),
                remotes: remoteBranches.split('\n').map(b => b.trim()).filter(Boolean),
                ahead: 0,
                behind: 0
            };

            // 解析ahead/behind信息
            const trackingMatch = trackingInfo.match(/\[ahead (\d+), behind (\d+)\]/);
            if (trackingMatch) {
                info.ahead = parseInt(trackingMatch[1]);
                info.behind = parseInt(trackingMatch[2]);
            }

            this.setCacheEntry(cacheKey, info, 10000); // 10秒缓存
            return info;
        } catch (error) {
            return { error: error.message };
        }
    }

    /**
     * 提交历史优化查询
     */
    async getCommitHistory(options = {}) {
        const limit = options.limit || 20;
        const format = options.format || 'oneline';
        const cacheKey = `commits-${limit}-${format}`;

        const cached = this.getCacheEntry(cacheKey);
        if (cached) return cached;

        try {
            let cmd = `git log --max-count=${limit}`;

            switch (format) {
                case 'oneline':
                    cmd += ' --oneline';
                    break;
                case 'detailed':
                    cmd += ' --pretty=format:"%H|%an|%ad|%s" --date=short';
                    break;
            }

            const result = await this.executeGitCommand(cmd);
            const commits = result.split('\n').filter(Boolean);

            this.setCacheEntry(cacheKey, commits, 15000); // 15秒缓存
            return commits;
        } catch (error) {
            return { error: error.message };
        }
    }

    /**
     * 执行Git命令 - 带超时和错误处理
     */
    executeGitCommand(command, options = {}) {
        return new Promise((resolve, reject) => {
            const timeout = options.timeout || 10000; // 10秒超时

            const child = exec(command, {
                cwd: this.repositoryPath,
                maxBuffer: 1024 * 1024, // 1MB buffer
                timeout: timeout
            });

            let stdout = '';
            let stderr = '';

            child.stdout?.on('data', (data) => {
                stdout += data;
            });

            child.stderr?.on('data', (data) => {
                stderr += data;
            });

            child.on('close', (code) => {
                if (code === 0) {
                    resolve(stdout);
                } else {
                    reject(new Error(`Git命令失败 (${code}): ${stderr || stdout}`));
                }
            });

            child.on('error', (error) => {
                reject(error);
            });
        });
    }

    /**
     * 解析Git状态输出
     */
    parseGitStatus(statusOutput) {
        const lines = statusOutput.split('\n').filter(Boolean);
        const result = {
            modified: [],
            added: [],
            deleted: [],
            untracked: [],
            staged: []
        };

        for (const line of lines) {
            if (line.length < 3) continue;

            const indexStatus = line.charAt(0);
            const workTreeStatus = line.charAt(1);
            const fileName = line.substring(3);

            if (indexStatus !== ' ' && indexStatus !== '?') {
                result.staged.push(fileName);
            }

            switch (workTreeStatus) {
                case 'M':
                    result.modified.push(fileName);
                    break;
                case 'A':
                    result.added.push(fileName);
                    break;
                case 'D':
                    result.deleted.push(fileName);
                    break;
                case '?':
                    result.untracked.push(fileName);
                    break;
            }
        }

        return result;
    }

    /**
     * 缓存管理
     */
    getCacheEntry(key) {
        const entry = this.cache.get(key);
        if (!entry) return null;

        if (Date.now() - entry.timestamp > this.cacheTTL) {
            this.cache.delete(key);
            return null;
        }

        return entry.data;
    }

    setCacheEntry(key, data, customTTL = null) {
        this.cache.set(key, {
            data,
            timestamp: Date.now(),
            ttl: customTTL || this.cacheTTL
        });
    }

    invalidateCache(patterns = []) {
        if (patterns.length === 0) {
            this.cache.clear();
            return;
        }

        for (const [key] of this.cache) {
            if (patterns.some(pattern => key.includes(pattern))) {
                this.cache.delete(key);
            }
        }
    }

    /**
     * 工具函数
     */
    hashFiles(files) {
        return crypto.createHash('md5')
            .update(JSON.stringify(files.sort()))
            .digest('hex')
            .substring(0, 8);
    }

    /**
     * 性能监控
     */
    async getPerformanceStats() {
        return {
            cacheSize: this.cache.size,
            runningOps: this.runningOperations.size,
            cacheHitRate: this.calculateCacheHitRate(),
            uptime: process.uptime()
        };
    }

    calculateCacheHitRate() {
        // 简化的缓存命中率计算
        const totalOps = this.cache.size + this.runningOperations.size;
        return totalOps > 0 ? (this.cache.size / totalOps * 100).toFixed(2) + '%' : '0%';
    }

    /**
     * 清理资源
     */
    cleanup() {
        this.cache.clear();
        this.pendingBatches.clear();
        this.runningOperations.clear();
    }
}

module.exports = GitOptimizer;