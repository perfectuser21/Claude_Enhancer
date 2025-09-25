#!/usr/bin/env node

/**
 * Claude Enhancer Plus - Performance Test Orchestrator
 * Main entry point for running comprehensive performance tests
 */

const fs = require('fs').promises;
const path = require('path');
const { performance } = require('perf_hooks');

// Import test suites
const PerformanceTestSuite = require('./performance-test-suite');
const StressTestRunner = require('./stress-test-runner');
const PerformanceBenchmarks = require('./performance-benchmarks');

// Import recovery system components
const ErrorRecovery = require('../ErrorRecovery');
const CheckpointManager = require('../CheckpointManager');

class PerformanceTestOrchestrator {
    constructor(options = {}) {
        this.config = {
            // Test configuration
            runBenchmarks: options.runBenchmarks !== false,
            runStressTests: options.runStressTests !== false,
            runEndurance: options.runEndurance !== false,

            // Test parameters
            benchmarkIterations: options.benchmarkIterations || 100,
            stressDuration: options.stressDuration || 60000, // 1 minute
            enduranceDuration: options.enduranceDuration || 300000, // 5 minutes

            // Concurrency settings
            maxConcurrency: options.maxConcurrency || 50,
            stressWorkers: options.stressWorkers || 8,

            // Output settings
            outputDir: options.outputDir || './performance-test-results',
            generateCharts: options.generateCharts || false,
            verboseOutput: options.verboseOutput || true,

            ...options
        };

        this.testResults = {
            orchestrator: {
                startTime: null,
                endTime: null,
                totalDuration: 0,
                testsRun: [],
                systemInfo: this.getSystemInfo()
            },
            benchmark: null,
            stressTest: null,
            enduranceTest: null,
            summary: {},
            recommendations: []
        };

        this.setupEnvironment();
    }

    /**
     * Main orchestrator method - runs all performance tests
     */
    async runAllPerformanceTests() {
        console.log('🚀 Claude Enhancer Plus - Performance Test Suite');
        console.log('='.repeat(60));
        console.log(`📅 Started: ${new Date().toISOString()}`);
        console.log(`⚙️  Configuration: ${JSON.stringify(this.config, null, 2)}`);
        console.log('='.repeat(60));

        this.testResults.orchestrator.startTime = Date.now();

        try {
            // Phase 1: Benchmark Tests
            if (this.config.runBenchmarks) {
                console.log('\n📊 Phase 1: Performance Benchmarks');
                console.log('-'.repeat(40));
                await this.runBenchmarkTests();
                this.testResults.orchestrator.testsRun.push('benchmarks');
            }

            // Phase 2: Stress Tests
            if (this.config.runStressTests) {
                console.log('\n🚨 Phase 2: Stress Testing');
                console.log('-'.repeat(40));
                await this.runStressTests();
                this.testResults.orchestrator.testsRun.push('stress');
            }

            // Phase 3: Endurance Tests
            if (this.config.runEndurance) {
                console.log('\n⏱️  Phase 3: Endurance Testing');
                console.log('-'.repeat(40));
                await this.runEnduranceTests();
                this.testResults.orchestrator.testsRun.push('endurance');
            }

            // Generate comprehensive analysis
            console.log('\n📋 Analyzing Results...');
            await this.analyzeAllResults();

            // Generate final report
            console.log('\n📄 Generating Final Report...');
            await this.generateFinalReport();

            console.log('\n✅ All Performance Tests Completed Successfully!');
            console.log(`📊 Total Duration: ${((Date.now() - this.testResults.orchestrator.startTime) / 1000).toFixed(2)}s`);
            console.log(`📁 Results Directory: ${this.config.outputDir}`);

        } catch (error) {
            console.error('\n❌ Performance Testing Failed:', error);
            await this.generateErrorReport(error);
            throw error;

        } finally {
            this.testResults.orchestrator.endTime = Date.now();
            this.testResults.orchestrator.totalDuration =
                this.testResults.orchestrator.endTime - this.testResults.orchestrator.startTime;

            await this.cleanup();
        }
    }

    /**
     * Run comprehensive benchmark tests
     */
    async runBenchmarkTests() {
        console.log('🎯 Starting Performance Benchmarks...');

        const benchmarks = new PerformanceBenchmarks({
            benchmarkIterations: this.config.benchmarkIterations,
            warmupIterations: Math.floor(this.config.benchmarkIterations / 10),
            outputDir: path.join(this.config.outputDir, 'benchmarks')
        });

        // Initialize test components
        const errorRecovery = new ErrorRecovery({
            enableMetrics: true,
            checkpointsDir: path.join(this.config.outputDir, 'benchmark-checkpoints')
        });

        const checkpointManager = new CheckpointManager({
            checkpointsDir: path.join(this.config.outputDir, 'benchmark-checkpoints')
        });

        try {
            // Run individual benchmark suites
            console.log('  🏃 Recovery Speed Benchmarks...');
            const recoveryResults = await benchmarks.benchmarkRecoverySpeed(errorRecovery);

            console.log('  💾 Checkpoint Performance Benchmarks...');
            const checkpointResults = await benchmarks.benchmarkCheckpointPerformance(checkpointManager);

            console.log('  ⚡ Concurrent Capacity Benchmarks...');
            const concurrentResults = await benchmarks.benchmarkConcurrentCapacity(errorRecovery);

            console.log('  🧠 Memory Usage Analysis...');
            const memoryOperations = await this.createMemoryTestOperations(errorRecovery, checkpointManager);
            const memoryResults = await benchmarks.benchmarkMemoryUsage(memoryOperations);

            // Generate benchmark report
            const benchmarkReport = await benchmarks.generateBenchmarkReport();
            this.testResults.benchmark = benchmarkReport;

            console.log('  ✅ Benchmarks completed');

        } catch (error) {
            console.error('  ❌ Benchmark tests failed:', error);
            throw error;
        }
    }

    /**
     * Run stress tests under high load
     */
    async runStressTests() {
        console.log('⚡ Starting Stress Tests...');

        const stressRunner = new StressTestRunner({
            duration: this.config.stressDuration,
            maxWorkers: this.config.stressWorkers,
            errorRate: 0.3, // 30% error rate for stress testing
            checkpointFrequency: 50
        });

        try {
            await stressRunner.runStressTest();
            this.testResults.stressTest = {
                completed: true,
                duration: this.config.stressDuration,
                workers: this.config.stressWorkers
            };

            console.log('  ✅ Stress tests completed');

        } catch (error) {
            console.error('  ❌ Stress tests failed:', error);
            this.testResults.stressTest = {
                completed: false,
                error: error.message,
                duration: this.config.stressDuration
            };
            throw error;
        }
    }

    /**
     * Run long-duration endurance tests
     */
    async runEnduranceTests() {
        console.log('⏱️  Starting Endurance Tests...');

        const enduranceTestSuite = new PerformanceTestSuite({
            testDuration: this.config.enduranceDuration,
            maxConcurrentTests: Math.min(this.config.maxConcurrency, 25), // Conservative for endurance
            benchmarkIterations: Math.floor(this.config.benchmarkIterations / 2),
            memoryMeasurementInterval: 1000 // Less frequent for long tests
        });

        try {
            await enduranceTestSuite.runPerformanceTests();
            this.testResults.enduranceTest = {
                completed: true,
                duration: this.config.enduranceDuration
            };

            console.log('  ✅ Endurance tests completed');

        } catch (error) {
            console.error('  ❌ Endurance tests failed:', error);
            this.testResults.enduranceTest = {
                completed: false,
                error: error.message,
                duration: this.config.enduranceDuration
            };
            throw error;
        }
    }

    /**
     * Create memory test operations for benchmarking
     */
    async createMemoryTestOperations(errorRecovery, checkpointManager) {
        const operations = [];

        // Operation 1: Multiple error recoveries
        for (let i = 0; i < 50; i++) {
            operations.push(async () => {
                const error = new Error('Memory test error');
                error.code = 'TEST_ERROR';
                await errorRecovery.recoverFromError(error, async () => {
                    await new Promise(resolve => setTimeout(resolve, 10));
                });
            });
        }

        // Operation 2: Checkpoint creation and restoration
        for (let i = 0; i < 20; i++) {
            operations.push(async () => {
                const testData = this.generateTestData(1024 * (i + 1)); // Increasing size
                const checkpointId = `memory_test_${i}_${Date.now()}`;
                await checkpointManager.createCheckpoint(checkpointId, testData);
                await checkpointManager.restoreCheckpoint(checkpointId);
            });
        }

        // Operation 3: Concurrent operations
        for (let i = 0; i < 30; i++) {
            operations.push(async () => {
                const promises = [];
                for (let j = 0; j < 5; j++) {
                    promises.push((async () => {
                        const error = new Error('Concurrent test error');
                        error.code = 'CONCURRENT_ERROR';
                        await errorRecovery.recoverFromError(error, async () => {
                            await new Promise(resolve => setTimeout(resolve, Math.random() * 50));
                        });
                    })());
                }
                await Promise.all(promises);
            });
        }

        return operations;
    }

    /**
     * Analyze all test results and generate insights
     */
    async analyzeAllResults() {
        const analysis = {
            overallScore: 0,
            keyFindings: [],
            performanceBottlenecks: [],
            scalabilityIssues: [],
            memoryIssues: [],
            reliabilityIssues: [],
            recommendations: []
        };

        // Analyze benchmark results
        if (this.testResults.benchmark) {
            this.analyzeBenchmarkResults(this.testResults.benchmark, analysis);
        }

        // Analyze stress test results
        if (this.testResults.stressTest && this.testResults.stressTest.completed) {
            this.analyzeStressTestResults(this.testResults.stressTest, analysis);
        }

        // Analyze endurance test results
        if (this.testResults.enduranceTest && this.testResults.enduranceTest.completed) {
            this.analyzeEnduranceResults(this.testResults.enduranceTest, analysis);
        }

        // Calculate overall performance score
        analysis.overallScore = this.calculateOverallScore(analysis);

        // Generate actionable recommendations
        this.generateActionableRecommendations(analysis);

        this.testResults.summary = analysis;
    }

    /**
     * Analyze benchmark results
     */
    analyzeBenchmarkResults(benchmarkResults, analysis) {
        // Recovery speed analysis
        if (benchmarkResults.benchmarks.recoverySpeed) {
            const recoveryResults = benchmarkResults.benchmarks.recoverySpeed;
            const avgTimes = Object.values(recoveryResults).map(r => r.stats.average);
            const overallAvg = avgTimes.reduce((a, b) => a + b, 0) / avgTimes.length;

            analysis.keyFindings.push({
                category: 'Recovery Speed',
                metric: 'Average Recovery Time',
                value: `${overallAvg.toFixed(2)}ms`,
                assessment: overallAvg < 500 ? 'excellent' : overallAvg < 1000 ? 'good' : 'needs improvement'
            });

            if (overallAvg > 1000) {
                analysis.performanceBottlenecks.push({
                    category: 'Recovery Speed',
                    issue: `Slow average recovery time: ${overallAvg.toFixed(2)}ms`,
                    impact: 'high',
                    priority: 'high'
                });
            }
        }

        // Checkpoint performance analysis
        if (benchmarkResults.benchmarks.checkpointPerformance) {
            const checkpointResults = benchmarkResults.benchmarks.checkpointPerformance;
            const throughputs = Object.values(checkpointResults).map(r => r.throughput.save);
            const avgThroughput = throughputs.reduce((a, b) => a + b, 0) / throughputs.length;

            analysis.keyFindings.push({
                category: 'Checkpoint Performance',
                metric: 'Average Save Throughput',
                value: `${(avgThroughput / 1024).toFixed(2)} KB/ms`,
                assessment: avgThroughput > 100000 ? 'excellent' : avgThroughput > 10000 ? 'good' : 'needs improvement'
            });
        }

        // Concurrent capacity analysis
        if (benchmarkResults.benchmarks.concurrentCapacity) {
            const concurrentResults = benchmarkResults.benchmarks.concurrentCapacity;
            const maxThroughput = Math.max(...Object.values(concurrentResults).map(r => r.throughput));
            const degradationPoint = this.findThroughputDegradationPoint(concurrentResults);

            analysis.keyFindings.push({
                category: 'Concurrent Capacity',
                metric: 'Maximum Throughput',
                value: `${maxThroughput.toFixed(2)} ops/sec`,
                assessment: maxThroughput > 1000 ? 'excellent' : maxThroughput > 500 ? 'good' : 'needs improvement'
            });

            if (degradationPoint) {
                analysis.scalabilityIssues.push({
                    category: 'Concurrent Capacity',
                    issue: `Throughput degradation detected at concurrency level: ${degradationPoint}`,
                    impact: 'medium',
                    priority: 'medium'
                });
            }
        }
    }

    /**
     * Calculate overall performance score
     */
    calculateOverallScore(analysis) {
        let score = 100;

        // Deduct for bottlenecks
        score -= analysis.performanceBottlenecks.length * 15;
        score -= analysis.scalabilityIssues.length * 10;
        score -= analysis.memoryIssues.length * 10;
        score -= analysis.reliabilityIssues.length * 20;

        return Math.max(0, Math.min(100, score));
    }

    /**
     * Generate actionable recommendations
     */
    generateActionableRecommendations(analysis) {
        const recommendations = [];

        // Performance recommendations
        if (analysis.performanceBottlenecks.length > 0) {
            recommendations.push({
                category: 'Performance Optimization',
                priority: 'high',
                action: 'Optimize error recovery algorithms and reduce retry delays',
                expectedImpact: '20-30% improvement in recovery speed'
            });
        }

        // Scalability recommendations
        if (analysis.scalabilityIssues.length > 0) {
            recommendations.push({
                category: 'Scalability',
                priority: 'medium',
                action: 'Implement adaptive concurrency controls and backpressure mechanisms',
                expectedImpact: '15-25% improvement in high-load scenarios'
            });
        }

        // Memory recommendations
        if (analysis.memoryIssues.length > 0) {
            recommendations.push({
                category: 'Memory Management',
                priority: 'medium',
                action: 'Implement memory pooling and optimize checkpoint storage',
                expectedImpact: '10-20% reduction in memory usage'
            });
        }

        // General recommendations
        recommendations.push({
            category: 'General Optimization',
            priority: 'low',
            action: 'Enable checkpoint compression and implement async I/O where possible',
            expectedImpact: '5-15% overall performance improvement'
        });

        analysis.recommendations = recommendations;
    }

    /**
     * Generate comprehensive final report
     */
    async generateFinalReport() {
        const report = {
            metadata: {
                testSuite: 'Claude Enhancer Plus - Error Recovery Performance Tests',
                version: '2.0',
                timestamp: new Date().toISOString(),
                duration: this.testResults.orchestrator.totalDuration,
                systemInfo: this.testResults.orchestrator.systemInfo,
                configuration: this.config
            },
            executiveSummary: {
                overallScore: this.testResults.summary.overallScore,
                testsRun: this.testResults.orchestrator.testsRun,
                keyFindings: this.testResults.summary.keyFindings.slice(0, 5), // Top 5
                criticalIssues: this.testResults.summary.performanceBottlenecks.filter(b => b.priority === 'high').length,
                recommendations: this.testResults.summary.recommendations.length
            },
            detailedResults: {
                benchmark: this.testResults.benchmark,
                stressTest: this.testResults.stressTest,
                enduranceTest: this.testResults.enduranceTest
            },
            analysis: this.testResults.summary,
            actionPlan: this.createActionPlan()
        };

        // Save comprehensive report
        await fs.mkdir(this.config.outputDir, { recursive: true });
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const reportPath = path.join(this.config.outputDir, `performance_test_final_report_${timestamp}.json`);

        await fs.writeFile(reportPath, JSON.stringify(report, null, 2));

        // Generate executive summary
        await this.generateExecutiveSummary(report, reportPath);

        console.log(`📄 Final Report: ${reportPath}`);
        return report;
    }

    /**
     * Generate executive summary document
     */
    async generateExecutiveSummary(report, reportPath) {
        const summary = `
Claude Enhancer Plus - Error Recovery Performance Test Report
============================================================

Executive Summary
-----------------
Overall Performance Score: ${report.executiveSummary.overallScore}/100
Test Duration: ${(report.metadata.duration / 1000).toFixed(2)} seconds
Tests Run: ${report.executiveSummary.testsRun.join(', ')}

Key Findings
------------
${report.executiveSummary.keyFindings.map((finding, i) =>
    `${i + 1}. ${finding.category}: ${finding.metric} = ${finding.value} (${finding.assessment})`
).join('\n')}

Critical Issues Found
--------------------
${report.executiveSummary.criticalIssues} high-priority issues identified

Top Recommendations
------------------
${report.analysis.recommendations.slice(0, 3).map((rec, i) =>
    `${i + 1}. ${rec.action} (Expected Impact: ${rec.expectedImpact})`
).join('\n')}

System Information
------------------
Node.js Version: ${report.metadata.systemInfo.nodeVersion}
Platform: ${report.metadata.systemInfo.platform}
CPU Cores: ${report.metadata.systemInfo.cpuCores}
Memory: ${(report.metadata.systemInfo.totalMemory / 1024 / 1024 / 1024).toFixed(2)}GB

Next Steps
----------
${report.actionPlan.immediateActions.map((action, i) => `${i + 1}. ${action}`).join('\n')}

Full detailed report: ${reportPath}
Generated: ${report.metadata.timestamp}
`;

        const summaryPath = path.join(this.config.outputDir, 'PERFORMANCE_TEST_SUMMARY.txt');
        await fs.writeFile(summaryPath, summary);

        console.log(`📋 Executive Summary: ${summaryPath}`);
    }

    /**
     * Create action plan based on test results
     */
    createActionPlan() {
        const plan = {
            immediateActions: [],
            shortTermActions: [],
            longTermActions: []
        };

        // Immediate actions (critical issues)
        const criticalIssues = this.testResults.summary.performanceBottlenecks?.filter(b => b.priority === 'high') || [];
        if (criticalIssues.length > 0) {
            plan.immediateActions.push('Address critical performance bottlenecks identified in recovery speed');
            plan.immediateActions.push('Implement emergency performance patches for high-priority issues');
        }

        // Short-term actions (optimization)
        plan.shortTermActions.push('Optimize error recovery algorithms based on benchmark results');
        plan.shortTermActions.push('Implement adaptive concurrency controls');
        plan.shortTermActions.push('Enable checkpoint compression and async I/O');

        // Long-term actions (architectural)
        plan.longTermActions.push('Redesign error recovery architecture for better scalability');
        plan.longTermActions.push('Implement advanced memory management strategies');
        plan.longTermActions.push('Develop predictive error recovery mechanisms');

        return plan;
    }

    // Utility methods

    setupEnvironment() {
        // Ensure output directory exists
        process.nextTick(async () => {
            try {
                await fs.mkdir(this.config.outputDir, { recursive: true });
            } catch (error) {
                console.warn('Warning: Could not create output directory:', error.message);
            }
        });
    }

    getSystemInfo() {
        const os = require('os');
        return {
            nodeVersion: process.version,
            platform: process.platform,
            architecture: process.arch,
            cpuCores: os.cpus().length,
            totalMemory: os.totalmem(),
            freeMemory: os.freemem(),
            uptime: os.uptime()
        };
    }

    generateTestData(size) {
        const baseData = {
            id: Math.random().toString(36).substr(2, 9),
            timestamp: Date.now(),
            type: 'test_data'
        };

        const serialized = JSON.stringify(baseData);
        const padding = 'x'.repeat(Math.max(0, size - serialized.length));
        baseData.padding = padding;

        return baseData;
    }

    findThroughputDegradationPoint(concurrentResults) {
        const entries = Object.entries(concurrentResults).sort((a, b) => {
            const aConcurrency = parseInt(a[0].split('_')[1]);
            const bConcurrency = parseInt(b[0].split('_')[1]);
            return aConcurrency - bConcurrency;
        });

        let maxThroughput = 0;
        for (const [level, result] of entries) {
            if (result.throughput > maxThroughput) {
                maxThroughput = result.throughput;
            } else if (result.throughput < maxThroughput * 0.8) { // 20% degradation
                return level;
            }
        }
        return null;
    }

    async generateErrorReport(error) {
        const errorReport = {
            timestamp: new Date().toISOString(),
            error: {
                message: error.message,
                stack: error.stack,
                name: error.name
            },
            context: {
                orchestratorState: this.testResults,
                systemInfo: this.getSystemInfo(),
                configuration: this.config
            }
        };

        try {
            await fs.mkdir(this.config.outputDir, { recursive: true });
            const errorPath = path.join(this.config.outputDir, 'error_report.json');
            await fs.writeFile(errorPath, JSON.stringify(errorReport, null, 2));
            console.log(`❌ Error Report: ${errorPath}`);
        } catch (reportError) {
            console.error('Failed to generate error report:', reportError);
        }
    }

    async cleanup() {
        console.log('🧹 Performing cleanup...');
        // Add any necessary cleanup operations here
    }
}

// Command-line interface
if (require.main === module) {
    const args = process.argv.slice(2);
    const config = {};

    // Parse command-line arguments
    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        switch (arg) {
            case '--benchmark-iterations':
                config.benchmarkIterations = parseInt(args[++i]);
                break;
            case '--stress-duration':
                config.stressDuration = parseInt(args[++i]) * 1000; // Convert to ms
                break;
            case '--endurance-duration':
                config.enduranceDuration = parseInt(args[++i]) * 1000; // Convert to ms
                break;
            case '--max-concurrency':
                config.maxConcurrency = parseInt(args[++i]);
                break;
            case '--output-dir':
                config.outputDir = args[++i];
                break;
            case '--skip-benchmarks':
                config.runBenchmarks = false;
                break;
            case '--skip-stress':
                config.runStressTests = false;
                break;
            case '--skip-endurance':
                config.runEndurance = false;
                break;
            case '--verbose':
                config.verboseOutput = true;
                break;
            case '--help':
                console.log(`
Usage: node run-performance-tests.js [options]

Options:
  --benchmark-iterations <n>    Number of iterations for benchmarks (default: 100)
  --stress-duration <seconds>   Stress test duration in seconds (default: 60)
  --endurance-duration <sec>    Endurance test duration in seconds (default: 300)
  --max-concurrency <n>         Maximum concurrent operations (default: 50)
  --output-dir <path>           Output directory for results (default: ./performance-test-results)
  --skip-benchmarks             Skip benchmark tests
  --skip-stress                 Skip stress tests
  --skip-endurance              Skip endurance tests
  --verbose                     Enable verbose output
  --help                        Show this help message
`);
                process.exit(0);
        }
    }

    // Run the orchestrator
    (async () => {
        try {
            const orchestrator = new PerformanceTestOrchestrator(config);
            await orchestrator.runAllPerformanceTests();
            process.exit(0);
        } catch (error) {
            console.error('Performance tests failed:', error);
            process.exit(1);
        }
    })();
}

module.exports = PerformanceTestOrchestrator;