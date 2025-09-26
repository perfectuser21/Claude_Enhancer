#!/usr/bin/env node

/**
 * Claude Enhancer 5.1 - 性能基准测试
 * 测试系统各组件的性能表现
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync, spawn } = require('child_process');
const { performance } = require('perf_hooks');

class PerformanceBenchmark {
    constructor() {
        this.results = {
            version: '5.1.0',
            timestamp: new Date().toISOString(),
            system: {
                node: process.version,
                platform: process.platform,
                arch: process.arch,
                memory: Math.round(process.memoryUsage().heapTotal / 1024 / 1024) + 'MB'
            },
            benchmarks: {},
            summary: {}
        };
        this.projectRoot = process.cwd();
    }

    async runAllBenchmarks() {
        console.log('🚀 Claude Enhancer 5.1 性能基准测试');
        console.log('=====================================');

        await this.benchmarkSystemHealth();
        await this.benchmarkHookExecution();
        await this.benchmarkAgentSelection();
        await this.benchmarkFileOperations();
        await this.benchmarkMemoryUsage();
        await this.benchmarkConcurrency();
        await this.benchmarkStartupTime();

        await this.generateSummary();
        await this.saveResults();

        console.log('\n📊 性能基准测试完成！');
        return this.results;
    }

    async benchmarkSystemHealth() {
        const testName = '系统健康检查';
        console.log(`\n🏥 ${testName}性能测试...`);

        const iterations = 100;
        const times = [];

        for (let i = 0; i < iterations; i++) {
            const start = performance.now();

            try {
                execSync('bash .claude/hooks/system_health_check.sh', {
                    stdio: 'pipe',
                    timeout: 5000
                });
                const end = performance.now();
                times.push(end - start);
            } catch (error) {
                times.push(5000); // 超时时间
            }

            if (i % 20 === 0) {
                process.stdout.write('.');
            }
        }

        const stats = this.calculateStats(times);
        this.results.benchmarks.systemHealth = {
            name: testName,
            iterations,
            ...stats,
            target: 500, // 目标时间(ms)
            status: stats.avg < 500 ? 'PASS' : 'FAIL'
        };

        console.log(`\n  平均执行时间: ${stats.avg.toFixed(2)}ms`);
        console.log(`  P95执行时间: ${stats.p95.toFixed(2)}ms`);
        console.log(`  最快执行: ${stats.min.toFixed(2)}ms`);
        console.log(`  最慢执行: ${stats.max.toFixed(2)}ms`);
        console.log(`  状态: ${this.results.benchmarks.systemHealth.status}`);
    }

    async benchmarkHookExecution() {
        const testName = 'Hook执行性能';
        console.log(`\n🪝 ${testName}测试...`);

        const hooks = [
            {
                name: 'system_health_check',
                command: 'bash .claude/hooks/system_health_check.sh',
                target: 500
            },
            {
                name: 'smart_agent_selector',
                command: 'bash .claude/hooks/smart_agent_selector_v2.sh "创建用户认证系统"',
                target: 2000
            }
        ];

        const results = {};

        for (const hook of hooks) {
            console.log(`  测试 ${hook.name}...`);
            const iterations = 50;
            const times = [];

            for (let i = 0; i < iterations; i++) {
                const start = performance.now();

                try {
                    execSync(hook.command, {
                        stdio: 'pipe',
                        timeout: 10000
                    });
                    const end = performance.now();
                    times.push(end - start);
                } catch (error) {
                    times.push(10000);
                }
            }

            const stats = this.calculateStats(times);
            results[hook.name] = {
                ...stats,
                target: hook.target,
                status: stats.avg < hook.target ? 'PASS' : 'FAIL'
            };

            console.log(`    平均: ${stats.avg.toFixed(2)}ms (目标: ${hook.target}ms) - ${results[hook.name].status}`);
        }

        this.results.benchmarks.hookExecution = {
            name: testName,
            hooks: results
        };
    }

    async benchmarkAgentSelection() {
        const testName = 'Agent选择算法';
        console.log(`\n🤖 ${testName}性能测试...`);

        const testCases = [
            '简单Bug修复',
            '创建用户认证系统，包含JWT和权限控制',
            '构建完整的电商平台，包括用户管理、商品管理、订单处理、支付系统和后台管理',
            'API接口开发',
            '数据库优化'
        ];

        const iterations = 20;
        const allTimes = [];

        for (const testCase of testCases) {
            const times = [];

            for (let i = 0; i < iterations; i++) {
                const start = performance.now();

                try {
                    execSync(`bash .claude/hooks/smart_agent_selector_v2.sh "${testCase}"`, {
                        stdio: 'pipe',
                        timeout: 10000
                    });
                    const end = performance.now();
                    times.push(end - start);
                } catch (error) {
                    times.push(10000);
                }
            }

            allTimes.push(...times);
        }

        const stats = this.calculateStats(allTimes);
        this.results.benchmarks.agentSelection = {
            name: testName,
            testCases: testCases.length,
            iterations: iterations * testCases.length,
            ...stats,
            target: 2000,
            status: stats.avg < 2000 ? 'PASS' : 'FAIL'
        };

        console.log(`  平均选择时间: ${stats.avg.toFixed(2)}ms`);
        console.log(`  P95选择时间: ${stats.p95.toFixed(2)}ms`);
        console.log(`  状态: ${this.results.benchmarks.agentSelection.status}`);
    }

    async benchmarkFileOperations() {
        const testName = '文件操作性能';
        console.log(`\n📁 ${testName}测试...`);

        const testFile = path.join(this.projectRoot, 'test-file.tmp');
        const testContent = 'A'.repeat(1024 * 10); // 10KB
        const iterations = 1000;

        // 写入测试
        console.log('  测试文件写入...');
        const writeTimes = [];
        for (let i = 0; i < iterations; i++) {
            const start = performance.now();
            await fs.writeFile(`${testFile}-${i}`, testContent);
            const end = performance.now();
            writeTimes.push(end - start);
        }

        // 读取测试
        console.log('  测试文件读取...');
        const readTimes = [];
        for (let i = 0; i < iterations; i++) {
            const start = performance.now();
            await fs.readFile(`${testFile}-${i}`, 'utf8');
            const end = performance.now();
            readTimes.push(end - start);
        }

        // 清理测试文件
        console.log('  清理测试文件...');
        for (let i = 0; i < iterations; i++) {
            try {
                await fs.unlink(`${testFile}-${i}`);
            } catch (error) {
                // 忽略清理错误
            }
        }

        const writeStats = this.calculateStats(writeTimes);
        const readStats = this.calculateStats(readTimes);

        this.results.benchmarks.fileOperations = {
            name: testName,
            write: {
                ...writeStats,
                target: 10,
                status: writeStats.avg < 10 ? 'PASS' : 'FAIL'
            },
            read: {
                ...readStats,
                target: 5,
                status: readStats.avg < 5 ? 'PASS' : 'FAIL'
            }
        };

        console.log(`  写入平均: ${writeStats.avg.toFixed(2)}ms - ${this.results.benchmarks.fileOperations.write.status}`);
        console.log(`  读取平均: ${readStats.avg.toFixed(2)}ms - ${this.results.benchmarks.fileOperations.read.status}`);
    }

    async benchmarkMemoryUsage() {
        const testName = '内存使用测试';
        console.log(`\n💾 ${testName}...`);

        const initialMemory = process.memoryUsage();
        console.log(`  初始内存使用: ${Math.round(initialMemory.heapUsed / 1024 / 1024)}MB`);

        // 模拟内存密集操作
        const bigData = [];
        for (let i = 0; i < 1000; i++) {
            bigData.push(new Array(1000).fill(Math.random()));
        }

        const peakMemory = process.memoryUsage();
        console.log(`  峰值内存使用: ${Math.round(peakMemory.heapUsed / 1024 / 1024)}MB`);

        // 触发垃圾回收
        if (global.gc) {
            global.gc();
        }

        const afterGcMemory = process.memoryUsage();
        console.log(`  垃圾回收后: ${Math.round(afterGcMemory.heapUsed / 1024 / 1024)}MB`);

        const memoryIncrease = afterGcMemory.heapUsed - initialMemory.heapUsed;
        const memoryIncreasePercentage = (memoryIncrease / initialMemory.heapUsed) * 100;

        this.results.benchmarks.memoryUsage = {
            name: testName,
            initial: Math.round(initialMemory.heapUsed / 1024 / 1024),
            peak: Math.round(peakMemory.heapUsed / 1024 / 1024),
            afterGc: Math.round(afterGcMemory.heapUsed / 1024 / 1024),
            increase: Math.round(memoryIncrease / 1024 / 1024),
            increasePercentage: memoryIncreasePercentage.toFixed(2),
            status: memoryIncreasePercentage < 10 ? 'PASS' : 'FAIL'
        };

        console.log(`  内存增长: ${this.results.benchmarks.memoryUsage.increase}MB (${this.results.benchmarks.memoryUsage.increasePercentage}%)`);
        console.log(`  状态: ${this.results.benchmarks.memoryUsage.status}`);
    }

    async benchmarkConcurrency() {
        const testName = '并发执行测试';
        console.log(`\n🔄 ${testName}...`);

        const concurrencyLevels = [1, 2, 4, 8, 12];
        const results = {};

        for (const concurrency of concurrencyLevels) {
            console.log(`  测试并发级别: ${concurrency}`);

            const promises = [];
            const start = performance.now();

            for (let i = 0; i < concurrency; i++) {
                promises.push(
                    new Promise((resolve) => {
                        const hookStart = performance.now();
                        try {
                            execSync('bash .claude/hooks/system_health_check.sh', {
                                stdio: 'pipe',
                                timeout: 5000
                            });
                        } catch (error) {
                            // 忽略Hook执行错误
                        }
                        resolve(performance.now() - hookStart);
                    })
                );
            }

            const times = await Promise.all(promises);
            const end = performance.now();
            const totalTime = end - start;

            const stats = this.calculateStats(times);
            results[`concurrency_${concurrency}`] = {
                concurrency,
                totalTime,
                avgHookTime: stats.avg,
                throughput: concurrency / (totalTime / 1000)
            };

            console.log(`    总时间: ${totalTime.toFixed(2)}ms, 吞吐量: ${results[`concurrency_${concurrency}`].throughput.toFixed(2)} ops/s`);
        }

        this.results.benchmarks.concurrency = {
            name: testName,
            levels: results,
            bestThroughput: Math.max(...Object.values(results).map(r => r.throughput))
        };
    }

    async benchmarkStartupTime() {
        const testName = '系统启动时间';
        console.log(`\n🚀 ${testName}测试...`);

        const iterations = 10;
        const times = [];

        for (let i = 0; i < iterations; i++) {
            console.log(`  启动测试 ${i + 1}/${iterations}...`);

            const start = performance.now();

            // 模拟系统启动过程
            try {
                // 加载配置
                const settingsPath = path.join(this.projectRoot, '.claude/settings.json');
                await fs.readFile(settingsPath, 'utf8');

                // 验证Hook
                execSync('bash .claude/hooks/system_health_check.sh', { stdio: 'pipe' });

                // 检查依赖
                execSync('node -e "console.log(\\"System ready\\")"', { stdio: 'pipe' });

            } catch (error) {
                // 记录错误但继续测试
            }

            const end = performance.now();
            times.push(end - start);
        }

        const stats = this.calculateStats(times);
        this.results.benchmarks.startupTime = {
            name: testName,
            iterations,
            ...stats,
            target: 2000,
            status: stats.avg < 2000 ? 'PASS' : 'FAIL'
        };

        console.log(`  平均启动时间: ${stats.avg.toFixed(2)}ms`);
        console.log(`  P95启动时间: ${stats.p95.toFixed(2)}ms`);
        console.log(`  状态: ${this.results.benchmarks.startupTime.status}`);
    }

    calculateStats(times) {
        const sorted = times.sort((a, b) => a - b);
        const sum = times.reduce((a, b) => a + b, 0);

        return {
            avg: sum / times.length,
            min: sorted[0],
            max: sorted[sorted.length - 1],
            p50: sorted[Math.floor(sorted.length * 0.5)],
            p95: sorted[Math.floor(sorted.length * 0.95)],
            p99: sorted[Math.floor(sorted.length * 0.99)],
            stddev: Math.sqrt(times.map(t => Math.pow(t - (sum / times.length), 2)).reduce((a, b) => a + b, 0) / times.length)
        };
    }

    async generateSummary() {
        console.log('\n📊 性能测试汇总');
        console.log('=====================================');

        const benchmarks = this.results.benchmarks;
        let passCount = 0;
        let totalCount = 0;

        // 统计各项测试结果
        Object.entries(benchmarks).forEach(([key, benchmark]) => {
            if (benchmark.status) {
                totalCount++;
                if (benchmark.status === 'PASS') {
                    passCount++;
                }
            } else if (benchmark.hooks) {
                // Hook测试
                Object.values(benchmark.hooks).forEach(hook => {
                    totalCount++;
                    if (hook.status === 'PASS') {
                        passCount++;
                    }
                });
            } else if (benchmark.write && benchmark.read) {
                // 文件操作测试
                totalCount += 2;
                if (benchmark.write.status === 'PASS') passCount++;
                if (benchmark.read.status === 'PASS') passCount++;
            }
        });

        this.results.summary = {
            totalTests: totalCount,
            passed: passCount,
            failed: totalCount - passCount,
            passRate: ((passCount / totalCount) * 100).toFixed(2),
            overallStatus: passCount === totalCount ? 'EXCELLENT' :
                          passRate > 80 ? 'GOOD' :
                          passRate > 60 ? 'ACCEPTABLE' : 'POOR'
        };

        console.log(`通过率: ${this.results.summary.passRate}% (${passCount}/${totalCount})`);
        console.log(`整体评级: ${this.results.summary.overallStatus}`);

        // 性能亮点
        if (benchmarks.systemHealth && benchmarks.systemHealth.avg < 300) {
            console.log('✨ 系统健康检查性能优异');
        }
        if (benchmarks.startupTime && benchmarks.startupTime.avg < 1500) {
            console.log('✨ 系统启动时间优异');
        }
        if (benchmarks.concurrency && benchmarks.concurrency.bestThroughput > 10) {
            console.log('✨ 并发处理能力优异');
        }

        // 改进建议
        console.log('\n💡 优化建议:');
        if (benchmarks.systemHealth && benchmarks.systemHealth.avg > 500) {
            console.log('  • 系统健康检查较慢，建议优化检查脚本');
        }
        if (benchmarks.memoryUsage && benchmarks.memoryUsage.status === 'FAIL') {
            console.log('  • 内存使用偏高，建议启用激进垃圾回收');
        }
        if (benchmarks.startupTime && benchmarks.startupTime.avg > 2000) {
            console.log('  • 启动时间较长，建议启用懒加载');
        }
    }

    async saveResults() {
        const reportPath = path.join(this.projectRoot, 'performance-benchmark-report.json');
        await fs.writeFile(reportPath, JSON.stringify(this.results, null, 2));

        console.log(`\n📄 详细报告已保存到: ${reportPath}`);

        // 生成简化版报告
        const summaryReport = {
            version: this.results.version,
            timestamp: this.results.timestamp,
            system: this.results.system,
            summary: this.results.summary,
            keyMetrics: {
                systemHealthAvg: this.results.benchmarks.systemHealth?.avg,
                startupTimeAvg: this.results.benchmarks.startupTime?.avg,
                bestThroughput: this.results.benchmarks.concurrency?.bestThroughput,
                memoryIncrease: this.results.benchmarks.memoryUsage?.increase
            }
        };

        const summaryPath = path.join(this.projectRoot, 'performance-summary.json');
        await fs.writeFile(summaryPath, JSON.stringify(summaryReport, null, 2));
        console.log(`📄 摘要报告已保存到: ${summaryPath}`);
    }
}

// 如果直接运行此脚本
if (require.main === module) {
    const benchmark = new PerformanceBenchmark();

    benchmark.runAllBenchmarks()
        .then(() => {
            console.log('\n🎉 性能基准测试完成！');
            console.log('查看详细报告: performance-benchmark-report.json');
        })
        .catch(error => {
            console.error('❌ 性能测试过程中发生错误:', error);
            process.exit(1);
        });
}

module.exports = PerformanceBenchmark;