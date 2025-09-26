#!/usr/bin/env node

/**
 * Claude Enhancer 5.1 - 安装验证测试
 * 验证系统是否正确安装和配置
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

class InstallationVerifier {
    constructor() {
        this.results = {
            passed: 0,
            failed: 0,
            warnings: 0,
            tests: []
        };
        this.projectRoot = process.cwd();
    }

    async runAllTests() {
        console.log('🔍 Claude Enhancer 5.1 安装验证测试');
        console.log('=====================================');

        await this.testNodeVersion();
        await this.testRequiredFiles();
        await this.testConfigurationFiles();
        await this.testHookScripts();
        await this.testDependencies();
        await this.testMonitoringSystem();
        await this.testOptimizationFeatures();
        await this.testPermissions();

        this.printSummary();

        // 如果有失败的测试，退出码为1
        if (this.results.failed > 0) {
            process.exit(1);
        }
    }

    async testNodeVersion() {
        const testName = 'Node.js版本检查';
        try {
            const nodeVersion = process.version;
            const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);

            if (majorVersion >= 18) {
                this.pass(testName, `Node.js ${nodeVersion} (符合要求 >=18.0.0)`);
            } else {
                this.fail(testName, `Node.js ${nodeVersion} 版本过低，需要 >=18.0.0`);
            }
        } catch (error) {
            this.fail(testName, `无法检查Node.js版本: ${error.message}`);
        }
    }

    async testRequiredFiles() {
        const testName = '必需文件检查';
        const requiredFiles = [
            'package.json',
            '.claude/settings.json',
            '.claude/hooks/system_health_check.sh',
            '.claude/hooks/smart_agent_selector_v2.sh',
            '.claude/install.sh',
            'README.md',
            'CHANGELOG.md'
        ];

        let missingFiles = [];

        for (const file of requiredFiles) {
            try {
                await fs.access(path.join(this.projectRoot, file));
            } catch {
                missingFiles.push(file);
            }
        }

        if (missingFiles.length === 0) {
            this.pass(testName, '所有必需文件都存在');
        } else {
            this.fail(testName, `缺少文件: ${missingFiles.join(', ')}`);
        }
    }

    async testConfigurationFiles() {
        const testName = '配置文件验证';
        try {
            // 检查主配置文件
            const settingsPath = path.join(this.projectRoot, '.claude/settings.json');
            const settingsContent = await fs.readFile(settingsPath, 'utf8');
            const settings = JSON.parse(settingsContent);

            // 验证版本
            if (settings.version === '5.1.0') {
                this.pass(testName, '配置版本正确 (5.1.0)');
            } else {
                this.fail(testName, `配置版本错误: ${settings.version}, 期望: 5.1.0`);
                return;
            }

            // 验证5.1新特性配置
            const requiredFeatures = ['lazy_loading', 'self_optimization', 'real_time_monitoring'];
            const missingFeatures = requiredFeatures.filter(feature => !settings.architecture[feature]);

            if (missingFeatures.length === 0) {
                this.pass('5.1新特性配置', '所有新特性已启用');
            } else {
                this.warning('5.1新特性配置', `未启用的特性: ${missingFeatures.join(', ')}`);
            }

            // 验证监控配置
            if (settings.monitoring && settings.monitoring.enabled) {
                this.pass('监控系统配置', '监控系统已启用');
            } else {
                this.warning('监控系统配置', '监控系统未启用');
            }

        } catch (error) {
            this.fail(testName, `配置文件解析错误: ${error.message}`);
        }
    }

    async testHookScripts() {
        const testName = 'Hook脚本验证';
        const hookScripts = [
            '.claude/hooks/system_health_check.sh',
            '.claude/hooks/smart_agent_selector_v2.sh'
        ];

        let invalidScripts = [];

        for (const script of hookScripts) {
            try {
                const scriptPath = path.join(this.projectRoot, script);
                const stats = await fs.stat(scriptPath);

                // 检查是否可执行
                if (!(stats.mode & parseInt('111', 8))) {
                    invalidScripts.push(`${script} (不可执行)`);
                    continue;
                }

                // 检查脚本内容
                const content = await fs.readFile(scriptPath, 'utf8');
                if (!content.includes('Claude Enhancer 5.1')) {
                    invalidScripts.push(`${script} (版本标识缺失)`);
                }

            } catch (error) {
                invalidScripts.push(`${script} (${error.message})`);
            }
        }

        if (invalidScripts.length === 0) {
            this.pass(testName, 'Hook脚本验证通过');
        } else {
            this.fail(testName, `问题脚本: ${invalidScripts.join(', ')}`);
        }
    }

    async testDependencies() {
        const testName = '依赖包验证';
        try {
            const packagePath = path.join(this.projectRoot, 'package.json');
            const packageContent = await fs.readFile(packagePath, 'utf8');
            const packageJson = JSON.parse(packageContent);

            // 检查版本
            if (packageJson.version === '5.1.0') {
                this.pass('Package版本', 'package.json版本正确');
            } else {
                this.fail('Package版本', `版本错误: ${packageJson.version}`);
            }

            // 检查新增依赖
            const newDependencies = ['ws', 'express', 'node-cron'];
            const missingDeps = newDependencies.filter(dep => !packageJson.dependencies[dep]);

            if (missingDeps.length === 0) {
                this.pass('新增依赖', '5.1新增依赖包完整');
            } else {
                this.warning('新增依赖', `缺少依赖: ${missingDeps.join(', ')}`);
            }

            // 检查node_modules
            try {
                await fs.access(path.join(this.projectRoot, 'node_modules'));
                this.pass(testName, 'node_modules目录存在');
            } catch {
                this.warning(testName, 'node_modules不存在，请运行 npm install');
            }

        } catch (error) {
            this.fail(testName, `依赖验证失败: ${error.message}`);
        }
    }

    async testMonitoringSystem() {
        const testName = '监控系统测试';
        try {
            // 检查监控相关文件
            const monitoringFiles = [
                'src/monitoring',
                'src/recovery'
            ];

            let missingFiles = [];
            for (const dir of monitoringFiles) {
                try {
                    await fs.access(path.join(this.projectRoot, dir));
                } catch {
                    missingFiles.push(dir);
                }
            }

            if (missingFiles.length === 0) {
                this.pass(testName, '监控系统文件结构完整');
            } else {
                this.warning(testName, `监控文件缺失: ${missingFiles.join(', ')}`);
            }

            // 测试监控脚本
            try {
                const hookPath = path.join(this.projectRoot, '.claude/hooks/performance_monitor.py');
                await fs.access(hookPath);
                this.pass('性能监控Hook', '性能监控Hook存在');
            } catch {
                this.warning('性能监控Hook', '性能监控Hook不存在');
            }

        } catch (error) {
            this.fail(testName, `监控系统测试失败: ${error.message}`);
        }
    }

    async testOptimizationFeatures() {
        const testName = '优化特性测试';
        try {
            const settingsPath = path.join(this.projectRoot, '.claude/settings.json');
            const settingsContent = await fs.readFile(settingsPath, 'utf8');
            const settings = JSON.parse(settingsContent);

            const optimizationFeatures = [
                'lazy_loading',
                'auto_scaling',
                'memory_optimization'
            ];

            const enabledFeatures = optimizationFeatures.filter(feature =>
                settings.performance && settings.performance[feature]
            );

            if (enabledFeatures.length === optimizationFeatures.length) {
                this.pass(testName, '所有优化特性已启用');
            } else {
                const missing = optimizationFeatures.filter(f => !enabledFeatures.includes(f));
                this.warning(testName, `未启用的优化特性: ${missing.join(', ')}`);
            }

        } catch (error) {
            this.fail(testName, `优化特性测试失败: ${error.message}`);
        }
    }

    async testPermissions() {
        const testName = '文件权限检查';
        try {
            const criticalFiles = [
                '.claude/install.sh',
                '.claude/hooks/system_health_check.sh',
                '.claude/hooks/smart_agent_selector_v2.sh'
            ];

            let permissionIssues = [];

            for (const file of criticalFiles) {
                try {
                    const filePath = path.join(this.projectRoot, file);
                    const stats = await fs.stat(filePath);

                    if (!(stats.mode & parseInt('111', 8))) {
                        permissionIssues.push(`${file} (不可执行)`);
                    }
                } catch (error) {
                    permissionIssues.push(`${file} (${error.message})`);
                }
            }

            if (permissionIssues.length === 0) {
                this.pass(testName, '关键文件权限正确');
            } else {
                this.fail(testName, `权限问题: ${permissionIssues.join(', ')}`);
                console.log('💡 修复建议: chmod +x .claude/hooks/*.sh .claude/install.sh');
            }

        } catch (error) {
            this.fail(testName, `权限检查失败: ${error.message}`);
        }
    }

    pass(testName, message) {
        this.results.passed++;
        this.results.tests.push({ name: testName, status: 'PASS', message });
        console.log(`✅ ${testName}: ${message}`);
    }

    fail(testName, message) {
        this.results.failed++;
        this.results.tests.push({ name: testName, status: 'FAIL', message });
        console.log(`❌ ${testName}: ${message}`);
    }

    warning(testName, message) {
        this.results.warnings++;
        this.results.tests.push({ name: testName, status: 'WARN', message });
        console.log(`⚠️ ${testName}: ${message}`);
    }

    printSummary() {
        console.log('\n📊 验证结果汇总');
        console.log('=====================================');
        console.log(`✅ 通过: ${this.results.passed}`);
        console.log(`❌ 失败: ${this.results.failed}`);
        console.log(`⚠️ 警告: ${this.results.warnings}`);

        if (this.results.failed === 0) {
            console.log('\n🎉 恭喜！Claude Enhancer 5.1 安装验证通过！');
            console.log('🚀 系统已准备就绪，可以开始使用所有新特性。');

            console.log('\n🆕 5.1版本新特性:');
            console.log('  • 自检优化系统 - 智能错误检测和恢复');
            console.log('  • 懒加载架构 - 减少内存使用，提升性能');
            console.log('  • 实时监控 - 系统健康状态追踪');
            console.log('  • 性能提升 - 整体性能提升30-60%');

            console.log('\n📚 后续步骤:');
            console.log('  1. 运行 npm run monitor 启动监控系统');
            console.log('  2. 查看 docs/UPGRADE_GUIDE.md 了解新特性');
            console.log('  3. 运行 npm run test:performance 进行性能测试');
        } else {
            console.log('\n❌ 安装验证失败，请解决上述问题后重试。');
            console.log('\n🔧 常见解决方案:');
            console.log('  • Node.js版本: 使用 nvm install 18 升级');
            console.log('  • 文件权限: 运行 chmod +x .claude/hooks/*.sh');
            console.log('  • 依赖缺失: 运行 npm install');
            console.log('  • 配置错误: 参考 docs/CONFIGURATION_GUIDE.md');
        }

        console.log(`\n⏱️ 验证完成时间: ${new Date().toISOString()}`);
    }

    async createInstallationReport() {
        const report = {
            timestamp: new Date().toISOString(),
            version: '5.1.0',
            nodeVersion: process.version,
            platform: process.platform,
            results: this.results,
            systemInfo: {
                cwd: process.cwd(),
                memory: process.memoryUsage(),
                uptime: process.uptime()
            }
        };

        const reportPath = path.join(this.projectRoot, 'installation-verification-report.json');
        await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
        console.log(`📄 验证报告已保存到: ${reportPath}`);
    }
}

// 如果直接运行此脚本
if (require.main === module) {
    const verifier = new InstallationVerifier();

    verifier.runAllTests()
        .then(async () => {
            await verifier.createInstallationReport();
        })
        .catch(error => {
            console.error('❌ 验证过程中发生错误:', error);
            process.exit(1);
        });
}

module.exports = InstallationVerifier;