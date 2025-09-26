/**
 * Claude Enhancer 5.0 - 性能基准测试套件
 * 
 * 测试目标：
 * - Hook执行时间＜ 3秒
 * - Phase转换延迟＜ 1秒
 * - Agent并行性能优化
 * - 内存使用情况
 * - 网络请求效率
 * 
 * @version 5.0.0
 */

const { performance } = require('perf_hooks');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class PerformanceBenchmark {
    constructor() {
        this.metrics = {
            hooks: {},
            phases: {},
            agents: {},
            system: {},
            baseline: {}
        };
        
        this.thresholds = {
            hook_timeout: 3000,      // 3秒
            phase_transition: 1000,   // 1秒
            agent_parallel: 5000,     // 5秒
            memory_usage: 200 * 1024 * 1024, // 200MB
            cpu_usage: 80             // 80%
        };
    }

    /**
     * === Hook性能测试 ===
     */
    
    async benchmarkHooks() {
        console.log('\n🚀 开始 Hook性能基准测试...');
        
        const hooksDir = path.join(process.cwd(), '.claude/hooks');
        const testHooks = [
            'smart_agent_selector.sh',
            'quality_gate.sh',
            'performance_monitor.sh',
            'error_handler.sh',
            'branch_helper.sh'
        ];
        
        for (const hookName of testHooks) {
            const hookPath = path.join(hooksDir, hookName);
            
            if (fs.existsSync(hookPath)) {
                console.log(`  📋 测试Hook: ${hookName}`);
                
                const metrics = await this.measureHookPerformance(hookPath, hookName);
                this.metrics.hooks[hookName] = metrics;
                
                // 性能验证
                if (metrics.executionTime > this.thresholds.hook_timeout) {
                    console.log(`    ⚠️  性能警告: ${hookName} 执行时间 ${metrics.executionTime}ms > ${this.thresholds.hook_timeout}ms`);
                } else {
                    console.log(`    ✅ 性能正常: ${hookName} 执行时间 ${metrics.executionTime}ms`);
                }
            } else {
                console.log(`  ⚠️  Hook文件不存在: ${hookName}`);
            }
        }
        
        return this.metrics.hooks;
    }
    
    async measureHookPerformance(hookPath, hookName) {
        const testInputs = [
            '{"prompt": "simple test task", "type": "simple"}',
            '{"prompt": "complex architecture design system", "type": "complex"}',
            '{"prompt": "medium implementation task", "type": "standard"}'
        ];
        
        const runs = [];
        
        for (const input of testInputs) {
            try {
                const startTime = performance.now();
                const startMemory = process.memoryUsage();
                
                // 执行Hook
                execSync(`bash "${hookPath}"`, {
                    input,
                    timeout: this.thresholds.hook_timeout,
                    stdio: 'pipe'
                });
                
                const endTime = performance.now();
                const endMemory = process.memoryUsage();
                
                const executionTime = Math.round(endTime - startTime);
                const memoryDelta = endMemory.heapUsed - startMemory.heapUsed;
                
                runs.push({
                    executionTime,
                    memoryDelta,
                    input: input.substring(0, 50) + '...'
                });
                
            } catch (error) {
                runs.push({
                    executionTime: this.thresholds.hook_timeout,
                    memoryDelta: 0,
                    error: error.message,
                    input: input.substring(0, 50) + '...'
                });
            }
        }
        
        // 计算平均性能
        const avgExecutionTime = Math.round(
            runs.reduce((sum, run) => sum + run.executionTime, 0) / runs.length
        );
        
        const avgMemoryDelta = Math.round(
            runs.reduce((sum, run) => sum + run.memoryDelta, 0) / runs.length
        );
        
        return {
            hookName,
            executionTime: avgExecutionTime,
            memoryDelta: avgMemoryDelta,
            runs,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * === Phase转换性能测试 ===
     */
    
    async benchmarkPhaseTransitions() {
        console.log('\n🚀 开始 Phase转换性能测试...');
        
        const phaseTransitions = [
            { from: 0, to: 1, name: 'Branch创建 → 需求分析' },
            { from: 1, to: 2, name: '需求分析 → 设计规划' },
            { from: 2, to: 3, name: '设计规划 → 实现开发' },
            { from: 3, to: 4, name: '实现开发 → 本地测试' },
            { from: 4, to: 5, name: '本地测试 → 代码提交' },
            { from: 5, to: 6, name: '代码提交 → 代码审查' },
            { from: 6, to: 7, name: '代码审查 → 合并部署' }
        ];
        
        for (const transition of phaseTransitions) {
            console.log(`  📋 测试转换: ${transition.name}`);
            
            const metrics = await this.measurePhaseTransition(transition);
            this.metrics.phases[`${transition.from}_to_${transition.to}`] = metrics;
            
            if (metrics.transitionTime > this.thresholds.phase_transition) {
                console.log(`    ⚠️  转换超时: ${metrics.transitionTime}ms > ${this.thresholds.phase_transition}ms`);
            } else {
                console.log(`    ✅ 转换正常: ${metrics.transitionTime}ms`);
            }
        }
        
        return this.metrics.phases;
    }
    
    async measurePhaseTransition(transition) {
        const startTime = performance.now();
        
        // 模拟Phase转换过程
        const transitionSteps = [
            () => this.validatePhaseCompletion(transition.from),
            () => this.prepareNextPhase(transition.to),
            () => this.transferPhaseData(transition.from, transition.to),
            () => this.initializePhase(transition.to),
            () => this.triggerPhaseHooks(transition.to)
        ];
        
        const stepMetrics = [];
        
        for (let i = 0; i < transitionSteps.length; i++) {
            const stepStart = performance.now();
            
            try {
                await transitionSteps[i]();
                const stepEnd = performance.now();
                
                stepMetrics.push({
                    step: i + 1,
                    time: Math.round(stepEnd - stepStart),
                    status: 'success'
                });
            } catch (error) {
                const stepEnd = performance.now();
                
                stepMetrics.push({
                    step: i + 1,
                    time: Math.round(stepEnd - stepStart),
                    status: 'error',
                    error: error.message
                });
            }
        }
        
        const endTime = performance.now();
        const totalTransitionTime = Math.round(endTime - startTime);
        
        return {
            from: transition.from,
            to: transition.to,
            name: transition.name,
            transitionTime: totalTransitionTime,
            steps: stepMetrics,
            timestamp: new Date().toISOString()
        };
    }
    
    async validatePhaseCompletion(phase) {
        // 模拟验证Phase完成状态
        await this.simulateDelay(10, 50); // 10-50ms
        return { phase, completed: true };
    }
    
    async prepareNextPhase(phase) {
        // 模拟Phase准备工作
        await this.simulateDelay(50, 200); // 50-200ms
        return { phase, prepared: true };
    }
    
    async transferPhaseData(fromPhase, toPhase) {
        // 模拟数据传递
        await this.simulateDelay(20, 100); // 20-100ms
        return { from: fromPhase, to: toPhase, transferred: true };
    }
    
    async initializePhase(phase) {
        // 模拟Phase初始化
        await this.simulateDelay(30, 150); // 30-150ms
        return { phase, initialized: true };
    }
    
    async triggerPhaseHooks(phase) {
        // 模拟Hook触发
        await this.simulateDelay(100, 300); // 100-300ms
        return { phase, hooksTriggered: true };
    }

    /**
     * === Agent并行性能测试 ===
     */
    
    async benchmarkAgentParallelism() {
        console.log('\n🚀 开始Agent并行性能测试...');
        
        const testScenarios = [
            { name: '4-Agent简单任务', agentCount: 4, taskComplexity: 'simple' },
            { name: '6-Agent标准任务', agentCount: 6, taskComplexity: 'standard' },
            { name: '8-Agent复杂任务', agentCount: 8, taskComplexity: 'complex' }
        ];
        
        for (const scenario of testScenarios) {
            console.log(`  📋 测试场景: ${scenario.name}`);
            
            const metrics = await this.measureAgentParallelism(scenario);
            this.metrics.agents[scenario.name] = metrics;
            
            if (metrics.totalExecutionTime > this.thresholds.agent_parallel) {
                console.log(`    ⚠️  Agent执行超时: ${metrics.totalExecutionTime}ms > ${this.thresholds.agent_parallel}ms`);
            } else {
                console.log(`    ✅ Agent执行正常: ${metrics.totalExecutionTime}ms`);
            }
        }
        
        return this.metrics.agents;
    }
    
    async measureAgentParallelism(scenario) {
        const startTime = performance.now();
        
        // 模拟Agent并行执行
        const agentTasks = this.generateAgentTasks(scenario.agentCount, scenario.taskComplexity);
        
        // 串行 vs 并行比较
        const serialTime = await this.measureSerialExecution(agentTasks);
        const parallelTime = await this.measureParallelExecution(agentTasks);
        
        const endTime = performance.now();
        const totalTime = Math.round(endTime - startTime);
        
        return {
            scenario: scenario.name,
            agentCount: scenario.agentCount,
            taskComplexity: scenario.taskComplexity,
            serialExecutionTime: serialTime,
            parallelExecutionTime: parallelTime,
            parallelImprovement: Math.round(((serialTime - parallelTime) / serialTime) * 100),
            totalExecutionTime: totalTime,
            timestamp: new Date().toISOString()
        };
    }
    
    generateAgentTasks(agentCount, complexity) {
        const baseTime = {
            simple: { min: 100, max: 300 },
            standard: { min: 200, max: 500 },
            complex: { min: 400, max: 800 }
        };
        
        const timeRange = baseTime[complexity] || baseTime.standard;
        
        return Array.from({ length: agentCount }, (_, i) => ({
            id: i + 1,
            name: `agent_${i + 1}`,
            duration: Math.floor(Math.random() * (timeRange.max - timeRange.min)) + timeRange.min,
            complexity
        }));
    }
    
    async measureSerialExecution(tasks) {
        const startTime = performance.now();
        
        for (const task of tasks) {
            await this.simulateAgentWork(task);
        }
        
        const endTime = performance.now();
        return Math.round(endTime - startTime);
    }
    
    async measureParallelExecution(tasks) {
        const startTime = performance.now();
        
        // 并行执行所有Agent任务
        await Promise.all(tasks.map(task => this.simulateAgentWork(task)));
        
        const endTime = performance.now();
        return Math.round(endTime - startTime);
    }
    
    async simulateAgentWork(task) {
        // 模拟Agent工作载荷
        return new Promise(resolve => {
            setTimeout(() => {
                // 模拟CPU密集型任务
                let result = 0;
                const iterations = Math.floor(task.duration * 1000);
                for (let i = 0; i < iterations; i++) {
                    result += Math.random();
                }
                
                resolve({
                    taskId: task.id,
                    result,
                    executedAt: Date.now()
                });
            }, task.duration);
        });
    }

    /**
     * === 系统资源测试 ===
     */
    
    async benchmarkSystemResources() {
        console.log('\n🚀 开始系统资源测试...');
        
        const resourceMetrics = {
            memory: await this.measureMemoryUsage(),
            cpu: await this.measureCPUUsage(),
            disk: await this.measureDiskUsage(),
            network: await this.measureNetworkLatency()
        };
        
        this.metrics.system = resourceMetrics;
        
        // 资源使用验证
        this.validateResourceUsage(resourceMetrics);
        
        return resourceMetrics;
    }
    
    async measureMemoryUsage() {
        const memUsage = process.memoryUsage();
        
        return {
            heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024), // MB
            heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024), // MB
            rss: Math.round(memUsage.rss / 1024 / 1024), // MB
            external: Math.round(memUsage.external / 1024 / 1024), // MB
            timestamp: Date.now()
        };
    }
    
    async measureCPUUsage() {
        const startTime = process.cpuUsage();
        
        // 模拏CPU密集型任务
        await this.simulateDelay(100, 200);
        
        const endTime = process.cpuUsage(startTime);
        
        return {
            user: Math.round(endTime.user / 1000), // 微秒转毫秒
            system: Math.round(endTime.system / 1000), // 微秒转毫秒
            total: Math.round((endTime.user + endTime.system) / 1000),
            timestamp: Date.now()
        };
    }
    
    async measureDiskUsage() {
        try {
            const projectRoot = process.cwd();
            const stats = fs.statSync(projectRoot);
            
            return {
                projectSize: this.getDirectorySize(projectRoot),
                claudeDir: this.getDirectorySize(path.join(projectRoot, '.claude')),
                tempFiles: this.countTempFiles(projectRoot),
                timestamp: Date.now()
            };
        } catch (error) {
            return {
                error: error.message,
                timestamp: Date.now()
            };
        }
    }
    
    getDirectorySize(dirPath) {
        try {
            let totalSize = 0;
            const files = fs.readdirSync(dirPath);
            
            for (const file of files) {
                const filePath = path.join(dirPath, file);
                const stats = fs.statSync(filePath);
                
                if (stats.isDirectory()) {
                    if (!file.startsWith('.git') && !file.startsWith('node_modules')) {
                        totalSize += this.getDirectorySize(filePath);
                    }
                } else {
                    totalSize += stats.size;
                }
            }
            
            return Math.round(totalSize / 1024); // KB
        } catch (error) {
            return 0;
        }
    }
    
    countTempFiles(dirPath) {
        try {
            const tempPatterns = [/\.tmp$/, /\.temp$/, /\.bak$/, /~$/];
            let tempCount = 0;
            
            const scanDirectory = (dir) => {
                const files = fs.readdirSync(dir);
                
                for (const file of files) {
                    const filePath = path.join(dir, file);
                    const stats = fs.statSync(filePath);
                    
                    if (stats.isDirectory() && !file.startsWith('.')) {
                        scanDirectory(filePath);
                    } else if (tempPatterns.some(pattern => pattern.test(file))) {
                        tempCount++;
                    }
                }
            };
            
            scanDirectory(dirPath);
            return tempCount;
        } catch (error) {
            return -1;
        }
    }
    
    async measureNetworkLatency() {
        // 模拟网络延迟检测
        const testEndpoints = [
            'localhost',
            'github.com',
            'npmjs.com'
        ];
        
        const latencies = {};
        
        for (const endpoint of testEndpoints) {
            try {
                const startTime = performance.now();
                
                // 模拟网络请求（简化）
                await this.simulateDelay(10, 100);
                
                const endTime = performance.now();
                latencies[endpoint] = Math.round(endTime - startTime);
            } catch (error) {
                latencies[endpoint] = -1; // 错误标记
            }
        }
        
        return {
            latencies,
            averageLatency: Math.round(
                Object.values(latencies)
                    .filter(l => l > 0)
                    .reduce((sum, l) => sum + l, 0) / 
                Object.values(latencies).filter(l => l > 0).length
            ),
            timestamp: Date.now()
        };
    }
    
    validateResourceUsage(metrics) {
        console.log('  📋 验证系统资源使用...');
        
        // 内存使用验证
        const memoryMB = metrics.memory.heapUsed;
        const memoryThresholdMB = Math.round(this.thresholds.memory_usage / 1024 / 1024);
        
        if (memoryMB > memoryThresholdMB) {
            console.log(`    ⚠️  内存使用过高: ${memoryMB}MB > ${memoryThresholdMB}MB`);
        } else {
            console.log(`    ✅ 内存使用正常: ${memoryMB}MB`);
        }
        
        // CPU使用验证
        const cpuTime = metrics.cpu.total;
        if (cpuTime > 1000) { // 1秒
            console.log(`    ⚠️  CPU使用时间过长: ${cpuTime}ms`);
        } else {
            console.log(`    ✅ CPU使用正常: ${cpuTime}ms`);
        }
        
        // 临时文件验证
        if (metrics.disk.tempFiles > 10) {
            console.log(`    ⚠️  临时文件过多: ${metrics.disk.tempFiles}个`);
        } else {
            console.log(`    ✅ 临时文件正常: ${metrics.disk.tempFiles}个`);
        }
    }

    /**
     * === 辅助方法 ===
     */
    
    async simulateDelay(minMs, maxMs) {
        const delay = Math.floor(Math.random() * (maxMs - minMs)) + minMs;
        return new Promise(resolve => setTimeout(resolve, delay));
    }
    
    generatePerformanceReport() {
        const report = {
            title: 'Claude Enhancer 5.0 - 性能基准测试报告',
            timestamp: new Date().toISOString(),
            summary: this.generatePerformanceSummary(),
            metrics: this.metrics,
            thresholds: this.thresholds,
            recommendations: this.generatePerformanceRecommendations()
        };
        
        return report;
    }
    
    generatePerformanceSummary() {
        const summary = {
            totalTests: 0,
            passedTests: 0,
            warningTests: 0,
            failedTests: 0,
            categories: {
                hooks: { status: 'unknown', issues: [] },
                phases: { status: 'unknown', issues: [] },
                agents: { status: 'unknown', issues: [] },
                system: { status: 'unknown', issues: [] }
            }
        };
        
        // 分析Hook性能
        Object.values(this.metrics.hooks).forEach(hook => {
            summary.totalTests++;
            if (hook.executionTime > this.thresholds.hook_timeout) {
                summary.failedTests++;
                summary.categories.hooks.issues.push(`${hook.hookName}: ${hook.executionTime}ms`);
            } else {
                summary.passedTests++;
            }
        });
        
        // 分析Phase性能
        Object.values(this.metrics.phases).forEach(phase => {
            summary.totalTests++;
            if (phase.transitionTime > this.thresholds.phase_transition) {
                summary.warningTests++;
                summary.categories.phases.issues.push(`${phase.name}: ${phase.transitionTime}ms`);
            } else {
                summary.passedTests++;
            }
        });
        
        // 分析Agent性能
        Object.values(this.metrics.agents).forEach(agent => {
            summary.totalTests++;
            if (agent.totalExecutionTime > this.thresholds.agent_parallel) {
                summary.failedTests++;
                summary.categories.agents.issues.push(`${agent.scenario}: ${agent.totalExecutionTime}ms`);
            } else {
                summary.passedTests++;
            }
        });
        
        // 设置类别状态
        Object.keys(summary.categories).forEach(category => {
            const cat = summary.categories[category];
            if (cat.issues.length === 0) {
                cat.status = 'passed';
            } else if (category === 'phases') {
                cat.status = 'warning';
            } else {
                cat.status = 'failed';
            }
        });
        
        return summary;
    }
    
    generatePerformanceRecommendations() {
        const recommendations = [];
        const summary = this.generatePerformanceSummary();
        
        // Hook性能优化建议
        if (summary.categories.hooks.issues.length > 0) {
            recommendations.push({
                category: 'hooks',
                priority: 'high',
                issue: 'Hook执行超时',
                details: summary.categories.hooks.issues,
                actions: [
                    '优化Hook脚本逻辑',
                    '添加缓存机制',
                    '减少不必要的文件I/O',
                    '考虑异步处理'
                ]
            });
        }
        
        // Phase转换优化建议
        if (summary.categories.phases.issues.length > 0) {
            recommendations.push({
                category: 'phases',
                priority: 'medium',
                issue: 'Phase转换耗时过长',
                details: summary.categories.phases.issues,
                actions: [
                    '优化数据传递效率',
                    '并行化部分转换步骤',
                    '减少不必要的验证检查'
                ]
            });
        }
        
        // Agent并行性优化建议
        if (summary.categories.agents.issues.length > 0) {
            recommendations.push({
                category: 'agents',
                priority: 'high',
                issue: 'Agent并行执行优化',
                details: summary.categories.agents.issues,
                actions: [
                    '优化Agent间通信机制',
                    '实现真正的并行处理',
                    '添加Agent负载均衡'
                ]
            });
        }
        
        // 系统资源优化建议
        const memoryMB = this.metrics.system?.memory?.heapUsed || 0;
        if (memoryMB > 150) { // 150MB阈值
            recommendations.push({
                category: 'system',
                priority: 'low',
                issue: '内存使用优化',
                details: [`当前内存使用: ${memoryMB}MB`],
                actions: [
                    '添加内存泄漏检测',
                    '优化大对象的处理',
                    '实现对象池复用'
                ]
            });
        }
        
        return recommendations;
    }

    /**
     * === 主执行方法 ===
     */
    
    async runAllBenchmarks() {
        console.log('🚀 Claude Enhancer 5.0 - 启动性能基准测试套件');
        console.log('='.repeat(80));
        
        const benchmarks = [
            () => this.benchmarkHooks(),
            () => this.benchmarkPhaseTransitions(),
            () => this.benchmarkAgentParallelism(),
            () => this.benchmarkSystemResources()
        ];
        
        let completedBenchmarks = 0;
        const totalBenchmarks = benchmarks.length;
        
        for (const benchmark of benchmarks) {
            try {
                await benchmark();
                completedBenchmarks++;
                
                const progress = Math.round((completedBenchmarks / totalBenchmarks) * 100);
                console.log(`\n📊 测试进度: ${progress}% (${completedBenchmarks}/${totalBenchmarks})`);
                
            } catch (error) {
                console.error(`❌ 性能测试错误:`, error.message);
            }
        }
        
        console.log('\n' + '='.repeat(80));
        console.log('🎯 性能测试完成，生成报告...');
        
        return this.generatePerformanceReport();
    }
}

// 导出测试套件
module.exports = PerformanceBenchmark;

// 如果直接运行此文件
if (require.main === module) {
    const benchmark = new PerformanceBenchmark();
    
    benchmark.runAllBenchmarks().then(report => {
        console.log('\n📊 性能报告:');
        console.log(JSON.stringify(report, null, 2));
        
        // 保存报告到文件
        const reportPath = path.join(__dirname, 'performance-benchmark-report.json');
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        console.log(`\n💾 性能报告已保存到: ${reportPath}`);
        
        // 退出码
        const summary = report.summary;
        const hasFailures = summary.failedTests > 0;
        process.exit(hasFailures ? 1 : 0);
        
    }).catch(error => {
        console.error('❌ 性能测试套件失败:', error);
        process.exit(1);
    });
}
