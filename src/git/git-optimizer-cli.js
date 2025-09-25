#!/usr/bin/env node

/**
 * Claude Enhancer Plus - Git Optimizer CLI
 *
 * Command-line interface for managing Git optimizations
 * Usage: node git-optimizer-cli.js [command] [options]
 */

const GitIntegration = require('./GitIntegration');
const fs = require('fs').promises;
const path = require('path');

class GitOptimizerCLI {
    constructor() {
        this.gitIntegration = null;
        this.commands = {
            'init': this.initOptimizer.bind(this),
            'status': this.showStatus.bind(this),
            'test': this.runTests.bind(this),
            'benchmark': this.runBenchmark.bind(this),
            'report': this.generateReport.bind(this),
            'cache': this.manageCache.bind(this),
            'hooks': this.manageHooks.bind(this),
            'health': this.checkHealth.bind(this),
            'cleanup': this.cleanup.bind(this),
            'help': this.showHelp.bind(this)
        };
    }

    async run() {
        const args = process.argv.slice(2);
        const command = args[0] || 'help';
        const options = this.parseOptions(args.slice(1));

        try {
            if (this.commands[command]) {
                await this.commands[command](options);
            } else {
                console.error(`❌ 未知命令: ${command}`);
                await this.showHelp();
                process.exit(1);
            }
        } catch (error) {
            console.error(`❌ 命令执行失败: ${error.message}`);
            if (options.verbose) {
                console.error(error.stack);
            }
            process.exit(1);
        }
    }

    /**
     * 初始化Git优化器
     */
    async initOptimizer(options = {}) {
        console.log('🚀 初始化Claude Enhancer Plus Git优化器...');

        const gitIntegration = new GitIntegration(process.cwd(), {
            enableCaching: !options.noCache,
            enableMonitoring: !options.noMonitoring,
            enableOptimizedHooks: !options.noHooks,
            enableBatching: !options.noBatching,
            verbose: options.verbose
        });

        await new Promise((resolve, reject) => {
            gitIntegration.on('ready', resolve);
            gitIntegration.on('error', reject);
        });

        this.gitIntegration = gitIntegration;

        // 导出配置给hook脚本
        const configPath = await gitIntegration.exportConfigForHooks();
        console.log(`✅ Git优化器初始化完成`);
        console.log(`📝 配置文件: ${configPath}`);

        // 显示组件状态
        const report = gitIntegration.getPerformanceReport();
        console.log('\n📊 组件状态:');
        Object.entries(report.system.components).forEach(([name, enabled]) => {
            console.log(`  ${enabled ? '✅' : '❌'} ${name}`);
        });
    }

    /**
     * 显示当前状态
     */
    async showStatus(options = {}) {
        await this.ensureInitialized(options);

        console.log('📊 Claude Enhancer Plus Git优化器状态\n');

        const report = this.gitIntegration.getPerformanceReport();

        // 系统状态
        console.log('🔧 系统状态:');
        console.log(`  就绪状态: ${report.system.ready ? '✅ 就绪' : '❌ 未就绪'}`);
        console.log(`  初始化状态: ${report.system.initialized ? '✅ 已初始化' : '❌ 未初始化'}`);

        // 组件状态
        console.log('\n📦 组件状态:');
        Object.entries(report.system.components).forEach(([name, enabled]) => {
            console.log(`  ${enabled ? '✅' : '❌'} ${this.formatComponentName(name)}`);
        });

        // 性能统计
        if (report.monitor?.summary) {
            const summary = report.monitor.summary;
            console.log('\n⚡ 性能统计:');
            console.log(`  总操作数: ${summary.totalOperations}`);
            console.log(`  平均执行时间: ${summary.averageTime}ms`);
            console.log(`  缓存命中率: ${summary.cacheHitRate}%`);
            console.log(`  快速操作占比: ${summary.fastOperationsPercent}%`);
            console.log(`  当前运行操作: ${summary.currentOperations}`);
        }

        // 缓存统计
        if (report.cache) {
            console.log('\n💾 缓存统计:');
            console.log(`  缓存大小: ${report.cache.cacheSize}/${report.cache.maxSize}`);
            console.log(`  文件监控器: ${report.cache.watchers}`);
            console.log(`  缓存年龄: ${Math.round(report.cache.globalCacheAge / 1000)}s`);
        }

        // 优化建议
        const suggestions = this.gitIntegration.getOptimizationSuggestions();
        if (suggestions.length > 0) {
            console.log('\n💡 优化建议:');
            suggestions.slice(0, 3).forEach((suggestion, index) => {
                console.log(`  ${index + 1}. [${suggestion.priority || 'normal'}] ${suggestion.message}`);
            });
        }
    }

    /**
     * 运行测试
     */
    async runTests(options = {}) {
        await this.ensureInitialized(options);

        console.log('🧪 运行Git优化器测试套件...\n');

        const tests = [
            { name: '基础Git状态查询', test: this.testBasicStatus },
            { name: '批量文件状态查询', test: this.testBatchStatus },
            { name: '文件添加操作', test: this.testFileAdd },
            { name: '分支信息查询', test: this.testBranchInfo },
            { name: '提交历史查询', test: this.testCommitHistory },
            { name: '智能差异检查', test: this.testIntelligentDiff }
        ];

        let passed = 0;
        let failed = 0;

        for (const testCase of tests) {
            try {
                const startTime = Date.now();
                await testCase.test.call(this);
                const duration = Date.now() - startTime;

                console.log(`✅ ${testCase.name} (${duration}ms)`);
                passed++;
            } catch (error) {
                console.log(`❌ ${testCase.name}: ${error.message}`);
                failed++;
            }
        }

        console.log(`\n📊 测试结果: ${passed} 通过, ${failed} 失败`);

        if (failed > 0) {
            process.exit(1);
        }
    }

    /**
     * 运行基准测试
     */
    async runBenchmark(options = {}) {
        await this.ensureInitialized(options);

        console.log('⏱️ 运行性能基准测试...\n');

        const iterations = options.iterations || 10;
        const benchmarks = [];

        // 基准测试项目
        const tests = [
            { name: 'Git状态查询', operation: () => this.gitIntegration.getStatus() },
            { name: '分支信息查询', operation: () => this.gitIntegration.getBranchInfo() },
            { name: '提交历史查询', operation: () => this.gitIntegration.getCommitHistory({ limit: 5 }) },
            { name: '差异检查', operation: () => this.gitIntegration.getDiff({ cached: true }) }
        ];

        for (const test of tests) {
            console.log(`📊 基准测试: ${test.name}`);

            const times = [];
            for (let i = 0; i < iterations; i++) {
                const startTime = Date.now();
                try {
                    await test.operation();
                    times.push(Date.now() - startTime);
                } catch (error) {
                    console.warn(`  警告: 迭代 ${i + 1} 失败: ${error.message}`);
                }
            }

            if (times.length > 0) {
                const avgTime = times.reduce((sum, time) => sum + time, 0) / times.length;
                const minTime = Math.min(...times);
                const maxTime = Math.max(...times);

                benchmarks.push({
                    name: test.name,
                    avgTime,
                    minTime,
                    maxTime,
                    iterations: times.length
                });

                console.log(`  平均: ${avgTime.toFixed(2)}ms, 最小: ${minTime}ms, 最大: ${maxTime}ms`);
            }
        }

        // 生成基准测试报告
        if (options.save) {
            const reportPath = path.join(process.cwd(), '.claude', 'benchmark-report.json');
            const report = {
                timestamp: new Date().toISOString(),
                iterations,
                benchmarks,
                system: this.gitIntegration.getPerformanceReport()
            };

            await fs.mkdir(path.dirname(reportPath), { recursive: true });
            await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
            console.log(`\n📄 基准测试报告已保存: ${reportPath}`);
        }
    }

    /**
     * 生成详细报告
     */
    async generateReport(options = {}) {
        await this.ensureInitialized(options);

        console.log('📋 生成Git优化器详细报告...\n');

        const report = this.gitIntegration.getPerformanceReport();
        const suggestions = this.gitIntegration.getOptimizationSuggestions();

        // 生成Markdown报告
        const markdown = this.generateMarkdownReport(report, suggestions);

        if (options.output) {
            await fs.writeFile(options.output, markdown);
            console.log(`✅ 报告已保存到: ${options.output}`);
        } else {
            console.log(markdown);
        }
    }

    /**
     * 管理缓存
     */
    async manageCache(options = {}) {
        await this.ensureInitialized(options);

        const action = options.action || 'status';

        switch (action) {
            case 'clear':
                if (this.gitIntegration.statusCache) {
                    this.gitIntegration.statusCache.cache.clear();
                    this.gitIntegration.statusCache.invalidateGlobalCache();
                    console.log('✅ 缓存已清空');
                } else {
                    console.log('❌ 缓存未启用');
                }
                break;

            case 'warm':
                console.log('🔥 预热缓存...');
                await this.gitIntegration.getStatus();
                await this.gitIntegration.getBranchInfo();
                console.log('✅ 缓存预热完成');
                break;

            case 'status':
            default:
                if (this.gitIntegration.statusCache) {
                    const stats = this.gitIntegration.statusCache.getStats();
                    console.log('💾 缓存状态:');
                    console.log(`  大小: ${stats.cacheSize}/${stats.maxSize}`);
                    console.log(`  监控器: ${stats.watchers}`);
                    console.log(`  命中率: ${stats.hitRate}`);
                } else {
                    console.log('❌ 缓存未启用');
                }
                break;
        }
    }

    /**
     * 管理Hooks
     */
    async manageHooks(options = {}) {
        await this.ensureInitialized(options);

        const action = options.action || 'status';

        switch (action) {
            case 'test':
                console.log('🧪 测试pre-commit hooks...');
                try {
                    const result = await this.gitIntegration.runPreCommitChecks();
                    console.log(`✅ Hooks测试${result.success ? '通过' : '失败'}`);
                    if (result.executionTime) {
                        console.log(`⏱️ 执行时间: ${result.executionTime}ms`);
                    }
                } catch (error) {
                    console.log(`❌ Hooks测试失败: ${error.message}`);
                }
                break;

            case 'status':
            default:
                if (this.gitIntegration.optimizedHooks) {
                    const stats = this.gitIntegration.optimizedHooks.getPerformanceStats();
                    console.log('🪝 Hooks状态:');
                    console.log(`  总运行次数: ${stats.totalRuns}`);
                    console.log(`  快速退出: ${stats.fastExits}`);
                    console.log(`  缓存命中: ${stats.cacheHits}`);
                    console.log(`  平均执行时间: ${stats.avgExecutionTime.toFixed(2)}ms`);
                } else {
                    console.log('❌ 优化Hooks未启用');
                }
                break;
        }
    }

    /**
     * 健康检查
     */
    async checkHealth(options = {}) {
        await this.ensureInitialized(options);

        console.log('🏥 Git优化器健康检查...\n');

        const health = await this.gitIntegration.healthCheck();

        console.log(`整体状态: ${this.getHealthIcon(health.overall)} ${health.overall}`);

        if (Object.keys(health.components).length > 0) {
            console.log('\n组件健康状态:');
            Object.entries(health.components).forEach(([name, component]) => {
                console.log(`  ${this.getHealthIcon(component.status)} ${this.formatComponentName(name)}`);
                if (options.verbose && component.details) {
                    Object.entries(component.details).forEach(([key, value]) => {
                        console.log(`    ${key}: ${value}`);
                    });
                }
            });
        }

        if (health.issues.length > 0) {
            console.log('\n⚠️ 发现的问题:');
            health.issues.forEach((issue, index) => {
                console.log(`  ${index + 1}. ${issue}`);
            });
        }

        if (health.overall !== 'healthy') {
            process.exit(1);
        }
    }

    /**
     * 清理资源
     */
    async cleanup(options = {}) {
        console.log('🧹 清理Git优化器资源...');

        if (this.gitIntegration) {
            this.gitIntegration.cleanup();
            this.gitIntegration = null;
        }

        // 清理临时文件
        const tempFiles = [
            '.claude/cache/git-status.json',
            '.claude/logs/git-performance.log',
            '.claude/git-integration-config.json'
        ];

        for (const file of tempFiles) {
            try {
                await fs.unlink(path.join(process.cwd(), file));
                console.log(`🗑️ 已删除: ${file}`);
            } catch {
                // 文件不存在，忽略
            }
        }

        console.log('✅ 清理完成');
    }

    /**
     * 显示帮助信息
     */
    async showHelp() {
        console.log(`
🚀 Claude Enhancer Plus Git优化器CLI

用法: node git-optimizer-cli.js [命令] [选项]

命令:
  init        初始化Git优化器
  status      显示当前状态
  test        运行测试套件
  benchmark   运行性能基准测试
  report      生成详细报告
  cache       管理缓存 (status|clear|warm)
  hooks       管理Hooks (status|test)
  health      健康检查
  cleanup     清理资源
  help        显示此帮助信息

选项:
  --no-cache        禁用缓存
  --no-monitoring   禁用监控
  --no-hooks        禁用优化Hooks
  --no-batching     禁用批量操作
  --verbose         详细输出
  --save            保存报告
  --output FILE     输出文件路径
  --iterations N    基准测试迭代次数 (默认: 10)
  --action ACTION   子命令操作

示例:
  node git-optimizer-cli.js init --verbose
  node git-optimizer-cli.js status
  node git-optimizer-cli.js benchmark --iterations 20 --save
  node git-optimizer-cli.js cache --action clear
  node git-optimizer-cli.js report --output report.md
        `);
    }

    // 测试方法
    async testBasicStatus() {
        const status = await this.gitIntegration.getStatus();
        if (typeof status !== 'object') {
            throw new Error('状态查询返回结果格式错误');
        }
    }

    async testBatchStatus() {
        const files = ['package.json', 'README.md'];
        const status = await this.gitIntegration.getStatus({ files });
        if (typeof status !== 'object') {
            throw new Error('批量状态查询返回结果格式错误');
        }
    }

    async testFileAdd() {
        // 这只是测试接口，不会实际添加文件
        try {
            await this.gitIntegration.addFiles([]);
        } catch (error) {
            if (!error.message.includes('没有文件需要添加')) {
                throw error;
            }
        }
    }

    async testBranchInfo() {
        const info = await this.gitIntegration.getBranchInfo();
        if (!info.current) {
            throw new Error('无法获取当前分支信息');
        }
    }

    async testCommitHistory() {
        const history = await this.gitIntegration.getCommitHistory({ limit: 1 });
        if (!Array.isArray(history)) {
            throw new Error('提交历史格式错误');
        }
    }

    async testIntelligentDiff() {
        const diff = await this.gitIntegration.getDiff({ nameOnly: true });
        if (typeof diff !== 'string') {
            throw new Error('差异检查返回格式错误');
        }
    }

    // 工具方法
    async ensureInitialized(options = {}) {
        if (!this.gitIntegration) {
            await this.initOptimizer(options);
        }
    }

    parseOptions(args) {
        const options = {};
        for (let i = 0; i < args.length; i++) {
            const arg = args[i];
            if (arg.startsWith('--')) {
                const key = arg.substring(2);
                const nextArg = args[i + 1];

                if (nextArg && !nextArg.startsWith('--')) {
                    options[key] = nextArg;
                    i++;
                } else {
                    options[key] = true;
                }
            }
        }
        return options;
    }

    formatComponentName(name) {
        return name
            .replace(/([A-Z])/g, ' $1')
            .replace(/^./, str => str.toUpperCase());
    }

    getHealthIcon(status) {
        switch (status) {
            case 'healthy': return '✅';
            case 'degraded': return '⚠️';
            case 'unhealthy': return '❌';
            default: return '❓';
        }
    }

    generateMarkdownReport(report, suggestions) {
        return `# Git优化器性能报告

生成时间: ${new Date().toISOString()}

## 系统状态

- 就绪状态: ${report.system.ready ? '✅ 就绪' : '❌ 未就绪'}
- 组件状态: ${Object.values(report.system.components).filter(Boolean).length}/${Object.keys(report.system.components).length} 启用

## 性能统计

${report.monitor?.summary ? `
- 总操作数: ${report.monitor.summary.totalOperations}
- 平均执行时间: ${report.monitor.summary.averageTime}ms
- 缓存命中率: ${report.monitor.summary.cacheHitRate}%
- 快速操作占比: ${report.monitor.summary.fastOperationsPercent}%
` : '无监控数据'}

## 优化建议

${suggestions.length > 0 ? suggestions.map((s, i) => `${i + 1}. **[${s.priority || 'normal'}]** ${s.message}`).join('\n') : '暂无优化建议'}

---
*报告由Claude Enhancer Plus Git优化器生成*
`;
    }
}

// 运行CLI
if (require.main === module) {
    const cli = new GitOptimizerCLI();
    cli.run().catch(error => {
        console.error('CLI执行失败:', error.message);
        process.exit(1);
    });
}

module.exports = GitOptimizerCLI;