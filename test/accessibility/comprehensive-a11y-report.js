#!/usr/bin/env node

/**
 * Comprehensive Accessibility Testing Report Generator
 * Phase 4: Local Testing - Final Accessibility Validation Report
 *
 * Consolidates results from:
 * 1. Error accessibility tests
 * 2. Playwright browser tests
 * 3. Screen reader simulations
 * 4. WCAG compliance checks
 * 5. Manual accessibility validation
 */

const fs = require('fs').promises;
const path = require('path');

class ComprehensiveAccessibilityReporter {
    constructor(options = {}) {
        this.options = {
            outputDir: options.outputDir || '/tmp/claude',
            includeRecommendations: options.includeRecommendations !== false,
            generateHTML: options.generateHTML !== false,
            verbose: options.verbose || false,
            ...options
        };

        this.testResults = new Map();
        this.consolidatedResults = {
            timestamp: new Date().toISOString(),
            summary: {
                totalTests: 0,
                passedTests: 0,
                failedTests: 0,
                warningTests: 0,
                wcagViolations: 0,
                successRate: 0
            },
            testSuites: [],
            wcagCompliance: new Map(),
            recommendations: [],
            actionItems: []
        };

        this.wcagGuidelines = {
            '1.1.1': 'Non-text Content',
            '1.2.1': 'Audio-only and Video-only (Prerecorded)',
            '1.2.2': 'Captions (Prerecorded)',
            '1.2.3': 'Audio Description or Media Alternative (Prerecorded)',
            '1.3.1': 'Info and Relationships',
            '1.3.2': 'Meaningful Sequence',
            '1.3.3': 'Sensory Characteristics',
            '1.4.1': 'Use of Color',
            '1.4.2': 'Audio Control',
            '1.4.3': 'Contrast (Minimum)',
            '1.4.4': 'Resize Text',
            '1.4.5': 'Images of Text',
            '2.1.1': 'Keyboard',
            '2.1.2': 'No Keyboard Trap',
            '2.1.4': 'Character Key Shortcuts',
            '2.2.1': 'Timing Adjustable',
            '2.2.2': 'Pause, Stop, Hide',
            '2.3.1': 'Three Flashes or Below Threshold',
            '2.4.1': 'Bypass Blocks',
            '2.4.2': 'Page Titled',
            '2.4.3': 'Focus Order',
            '2.4.4': 'Link Purpose (In Context)',
            '2.4.5': 'Multiple Ways',
            '2.4.6': 'Headings and Labels',
            '2.4.7': 'Focus Visible',
            '2.5.1': 'Pointer Gestures',
            '2.5.2': 'Pointer Cancellation',
            '2.5.3': 'Label in Name',
            '2.5.4': 'Motion Actuation',
            '3.1.1': 'Language of Page',
            '3.1.2': 'Language of Parts',
            '3.2.1': 'On Focus',
            '3.2.2': 'On Input',
            '3.2.3': 'Consistent Navigation',
            '3.2.4': 'Consistent Identification',
            '3.3.1': 'Error Identification',
            '3.3.2': 'Labels or Instructions',
            '3.3.3': 'Error Suggestion',
            '3.3.4': 'Error Prevention (Legal, Financial, Data)',
            '4.1.1': 'Parsing',
            '4.1.2': 'Name, Role, Value',
            '4.1.3': 'Status Messages'
        };
    }

    async generateComprehensiveReport() {
        console.log('📊 Generating Comprehensive Accessibility Report...\n');

        try {
            // Collect results from all test suites
            await this.collectTestResults();

            // Analyze WCAG compliance
            this.analyzeWCAGCompliance();

            // Generate recommendations
            this.generateRecommendations();

            // Generate action items
            this.generateActionItems();

            // Calculate summary statistics
            this.calculateSummaryStatistics();

            // Save reports
            await this.saveReports();

            // Display results
            this.displayResults();

            return this.consolidatedResults;

        } catch (error) {
            console.error('❌ Report generation failed:', error);
            throw error;
        }
    }

    async collectTestResults() {
        console.log('🔍 Collecting test results from all suites...');

        const testFiles = [
            'accessibility-report.json',
            'accessibility-audit-report.json',
            'screen-reader-test.json'
        ];

        for (const filename of testFiles) {
            const filepath = path.join(this.options.outputDir, filename);

            try {
                const data = await fs.readFile(filepath, 'utf8');
                const results = JSON.parse(data);

                this.testResults.set(filename, results);

                // Add to consolidated results
                this.consolidatedResults.testSuites.push({
                    name: this.getTestSuiteName(filename),
                    filename: filename,
                    results: results,
                    summary: this.extractSummary(results)
                });

                console.log(`   ✅ Loaded: ${filename}`);

            } catch (error) {
                console.log(`   ⚠️  Could not load: ${filename} (${error.code})`);

                // Add placeholder for missing results
                this.consolidatedResults.testSuites.push({
                    name: this.getTestSuiteName(filename),
                    filename: filename,
                    results: null,
                    summary: { error: 'File not found', message: error.message }
                });
            }
        }
    }

    getTestSuiteName(filename) {
        const nameMap = {
            'accessibility-report.json': 'Basic Accessibility Tests',
            'accessibility-audit-report.json': 'Playwright Browser Tests',
            'screen-reader-test.json': 'Screen Reader Simulation'
        };
        return nameMap[filename] || filename;
    }

    extractSummary(results) {
        // Handle different result structures
        if (results.summary) {
            return {
                total: results.summary.total || results.summary.totalTests || 0,
                passed: results.summary.passed || results.summary.passedTests || 0,
                failed: results.summary.failed || results.summary.failedTests || 0,
                warnings: results.summary.warnings || results.summary.warningTests || 0,
                violations: results.violations?.length || 0
            };
        }

        // For screen reader test results
        if (results.announcements) {
            return {
                total: 1,
                passed: 1,
                failed: 0,
                warnings: 0,
                announcements: results.announcements?.length || 0,
                liveUpdates: results.liveRegionUpdates?.length || 0
            };
        }

        return { total: 0, passed: 0, failed: 0, warnings: 0 };
    }

    analyzeWCAGCompliance() {
        console.log('📋 Analyzing WCAG compliance...');

        const wcagViolations = new Map();

        // Collect violations from all test suites
        for (const suite of this.consolidatedResults.testSuites) {
            if (!suite.results) continue;

            // Process violations
            const violations = suite.results.violations || [];
            violations.forEach(violation => {
                const wcagCriteria = this.extractWCAGCriteria(violation);

                wcagCriteria.forEach(criteria => {
                    if (!wcagViolations.has(criteria)) {
                        wcagViolations.set(criteria, []);
                    }
                    wcagViolations.get(criteria).push({
                        source: suite.name,
                        violation: violation
                    });
                });
            });

            // Process tests that might indicate WCAG violations
            if (suite.results.tests) {
                suite.results.tests.forEach(test => {
                    if (test.status === 'failed' && test.violation) {
                        const criteria = test.violation.wcag || this.mapToCriteria(test.test);
                        if (criteria) {
                            if (!wcagViolations.has(criteria)) {
                                wcagViolations.set(criteria, []);
                            }
                            wcagViolations.get(criteria).push({
                                source: suite.name,
                                test: test.test,
                                violation: test.violation
                            });
                        }
                    }
                });
            }
        }

        this.consolidatedResults.wcagCompliance = wcagViolations;
        this.consolidatedResults.summary.wcagViolations = wcagViolations.size;
    }

    extractWCAGCriteria(violation) {
        const criteria = [];

        // Check violation tags for WCAG references
        if (violation.tags) {
            violation.tags.forEach(tag => {
                const match = tag.match(/wcag(\d{3})/);
                if (match) {
                    const number = match[1];
                    const formatted = `${number.charAt(0)}.${number.charAt(1)}.${number.charAt(2)}`;
                    criteria.push(formatted);
                }
            });
        }

        // Check for explicit WCAG reference
        if (violation.wcag) {
            criteria.push(violation.wcag);
        }

        return criteria;
    }

    mapToCriteria(testName) {
        const testToCriteriaMap = {
            'testScreenReaderCompatibility': '4.1.2',
            'testKeyboardNavigation': '2.1.1',
            'testColorContrast': '1.4.3',
            'testFocusManagement': '2.4.7',
            'testAriaUsage': '4.1.2',
            'testErrorAnnouncements': '4.1.3',
            'testErrorMessageClarity': '3.3.1',
            'testRecoveryOptionsAccessibility': '2.1.1',
            'testStatusIndicators': '4.1.3'
        };

        return testToCriteriaMap[testName];
    }

    generateRecommendations() {
        console.log('💡 Generating accessibility recommendations...');

        const recommendations = [];

        // High Priority Recommendations
        if (this.consolidatedResults.wcagCompliance.has('4.1.2')) {
            recommendations.push({
                priority: 'high',
                category: 'ARIA Implementation',
                issue: 'Name, Role, Value violations detected',
                wcag: '4.1.2',
                solution: 'Ensure all UI components have accessible names, roles, and values defined through ARIA attributes or semantic HTML',
                impact: 'Screen readers cannot properly identify or interact with elements'
            });
        }

        if (this.consolidatedResults.wcagCompliance.has('2.1.1')) {
            recommendations.push({
                priority: 'high',
                category: 'Keyboard Accessibility',
                issue: 'Keyboard navigation issues found',
                wcag: '2.1.1',
                solution: 'Ensure all interactive elements are keyboard accessible with proper tab order and focus management',
                impact: 'Users who rely on keyboards cannot access error recovery features'
            });
        }

        if (this.consolidatedResults.wcagCompliance.has('1.4.3')) {
            recommendations.push({
                priority: 'medium',
                category: 'Color Contrast',
                issue: 'Color contrast below WCAG AA standards',
                wcag: '1.4.3',
                solution: 'Increase color contrast to at least 4.5:1 for normal text and 3:1 for large text',
                impact: 'Users with visual impairments may not be able to read error messages'
            });
        }

        if (this.consolidatedResults.wcagCompliance.has('4.1.3')) {
            recommendations.push({
                priority: 'high',
                category: 'Status Messages',
                issue: 'Status message announcements not properly implemented',
                wcag: '4.1.3',
                solution: 'Use aria-live regions and role="alert" for dynamic status updates and error messages',
                impact: 'Screen reader users miss important error and recovery status updates'
            });
        }

        if (this.consolidatedResults.wcagCompliance.has('3.3.1')) {
            recommendations.push({
                priority: 'high',
                category: 'Error Identification',
                issue: 'Error identification and description issues',
                wcag: '3.3.1',
                solution: 'Clearly identify errors and provide specific, actionable error descriptions',
                impact: 'Users cannot understand what went wrong or how to fix it'
            });
        }

        // Medium Priority Recommendations
        if (this.consolidatedResults.wcagCompliance.has('2.4.7')) {
            recommendations.push({
                priority: 'medium',
                category: 'Focus Indicators',
                issue: 'Visible focus indicators missing or insufficient',
                wcag: '2.4.7',
                solution: 'Add clear, high-contrast focus indicators to all interactive elements',
                impact: 'Keyboard users cannot see where focus is located'
            });
        }

        if (this.consolidatedResults.wcagCompliance.has('1.3.1')) {
            recommendations.push({
                priority: 'medium',
                category: 'Info and Relationships',
                issue: 'Information relationships not properly conveyed',
                wcag: '1.3.1',
                solution: 'Use proper heading hierarchy, form labels, and semantic markup',
                impact: 'Screen readers cannot understand page structure and relationships'
            });
        }

        // Low Priority Recommendations
        if (this.consolidatedResults.wcagCompliance.has('2.4.1')) {
            recommendations.push({
                priority: 'low',
                category: 'Skip Links',
                issue: 'Skip navigation mechanisms missing',
                wcag: '2.4.1',
                solution: 'Add skip links for complex interfaces to bypass repetitive navigation',
                impact: 'Keyboard users must navigate through many elements to reach main content'
            });
        }

        // Add general recommendations based on test suite results
        const hasScreenReaderTest = this.consolidatedResults.testSuites.some(s =>
            s.name === 'Screen Reader Simulation' && s.results);

        if (!hasScreenReaderTest) {
            recommendations.push({
                priority: 'medium',
                category: 'Testing Coverage',
                issue: 'Screen reader testing not conducted',
                wcag: 'General',
                solution: 'Implement regular screen reader testing with NVDA, JAWS, or VoiceOver',
                impact: 'May miss critical accessibility issues that affect screen reader users'
            });
        }

        // Sort by priority
        const priorityOrder = { 'high': 3, 'medium': 2, 'low': 1 };
        recommendations.sort((a, b) => priorityOrder[b.priority] - priorityOrder[a.priority]);

        this.consolidatedResults.recommendations = recommendations;
    }

    generateActionItems() {
        console.log('📋 Generating action items...');

        const actionItems = [];

        // Immediate Actions (Critical Issues)
        const criticalViolations = Array.from(this.consolidatedResults.wcagCompliance.entries())
            .filter(([criteria, violations]) => {
                return ['4.1.2', '2.1.1', '4.1.3', '3.3.1'].includes(criteria);
            });

        if (criticalViolations.length > 0) {
            actionItems.push({
                priority: 'immediate',
                title: 'Fix Critical Accessibility Violations',
                description: 'Address WCAG violations that prevent users from accessing error recovery features',
                tasks: criticalViolations.map(([criteria, violations]) =>
                    `Fix ${this.wcagGuidelines[criteria]} (${criteria}) - ${violations.length} violations`
                ),
                timeframe: '1-2 days',
                effort: 'high'
            });
        }

        // Short-term Actions
        actionItems.push({
            priority: 'short-term',
            title: 'Implement Comprehensive Error Recovery Accessibility',
            description: 'Ensure all error recovery flows are fully accessible',
            tasks: [
                'Add role="alert" to all error messages',
                'Implement aria-live regions for status updates',
                'Ensure keyboard navigation works in all recovery flows',
                'Add focus management for modal error dialogs',
                'Test with actual screen readers (NVDA, JAWS, VoiceOver)'
            ],
            timeframe: '1 week',
            effort: 'medium'
        });

        actionItems.push({
            priority: 'short-term',
            title: 'Enhance Visual Accessibility',
            description: 'Improve visual accessibility for users with visual impairments',
            tasks: [
                'Audit and fix color contrast ratios',
                'Add visible focus indicators',
                'Ensure error messages don\'t rely solely on color',
                'Test with high contrast mode',
                'Verify text scaling to 200%'
            ],
            timeframe: '3-5 days',
            effort: 'medium'
        });

        // Medium-term Actions
        actionItems.push({
            priority: 'medium-term',
            title: 'Establish Accessibility Testing Process',
            description: 'Create systematic accessibility testing procedures',
            tasks: [
                'Integrate automated accessibility testing in CI/CD',
                'Set up regular manual testing schedule',
                'Create accessibility testing checklist',
                'Train team on accessibility testing tools',
                'Establish accessibility review process'
            ],
            timeframe: '2 weeks',
            effort: 'low'
        });

        // Long-term Actions
        actionItems.push({
            priority: 'long-term',
            title: 'Accessibility Excellence Program',
            description: 'Build comprehensive accessibility program',
            tasks: [
                'Conduct user testing with people with disabilities',
                'Create accessibility design system',
                'Implement accessibility monitoring dashboard',
                'Establish accessibility metrics and KPIs',
                'Regular accessibility audits by external experts'
            ],
            timeframe: '1-3 months',
            effort: 'high'
        });

        this.consolidatedResults.actionItems = actionItems;
    }

    calculateSummaryStatistics() {
        let totalTests = 0;
        let passedTests = 0;
        let failedTests = 0;
        let warningTests = 0;

        for (const suite of this.consolidatedResults.testSuites) {
            if (suite.summary && !suite.summary.error) {
                totalTests += suite.summary.total || 0;
                passedTests += suite.summary.passed || 0;
                failedTests += suite.summary.failed || 0;
                warningTests += suite.summary.warnings || 0;
            }
        }

        this.consolidatedResults.summary = {
            totalTests,
            passedTests,
            failedTests,
            warningTests,
            wcagViolations: this.consolidatedResults.wcagCompliance.size,
            successRate: totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0
        };
    }

    displayResults() {
        console.log('\n' + '='.repeat(60));
        console.log('📊 COMPREHENSIVE ACCESSIBILITY AUDIT RESULTS');
        console.log('='.repeat(60));

        const { summary } = this.consolidatedResults;

        console.log(`\n🎯 Overall Performance:`);
        console.log(`   Success Rate: ${summary.successRate}%`);
        console.log(`   Total Tests: ${summary.totalTests}`);
        console.log(`   ✅ Passed: ${summary.passedTests}`);
        console.log(`   ❌ Failed: ${summary.failedTests}`);
        console.log(`   ⚠️  Warnings: ${summary.warningTests}`);
        console.log(`   🔍 WCAG Violations: ${summary.wcagViolations}`);

        console.log(`\n📋 Test Suite Results:`);
        for (const suite of this.consolidatedResults.testSuites) {
            const icon = suite.summary.error ? '❌' : '✅';
            const status = suite.summary.error ?
                'ERROR' :
                `${suite.summary.passed}/${suite.summary.total} passed`;
            console.log(`   ${icon} ${suite.name}: ${status}`);
        }

        if (this.consolidatedResults.wcagCompliance.size > 0) {
            console.log(`\n⚠️  WCAG Compliance Issues:`);
            for (const [criteria, violations] of this.consolidatedResults.wcagCompliance) {
                console.log(`   • ${criteria} - ${this.wcagGuidelines[criteria]}: ${violations.length} issues`);
            }
        }

        console.log(`\n💡 Priority Recommendations:`);
        const highPriority = this.consolidatedResults.recommendations.filter(r => r.priority === 'high');
        if (highPriority.length > 0) {
            highPriority.slice(0, 3).forEach(rec => {
                console.log(`   🔴 HIGH: ${rec.issue} (${rec.wcag})`);
            });
        } else {
            console.log(`   ✅ No high-priority issues found!`);
        }

        console.log(`\n📋 Immediate Action Items:`);
        const immediate = this.consolidatedResults.actionItems.filter(a => a.priority === 'immediate');
        if (immediate.length > 0) {
            immediate.forEach(action => {
                console.log(`   • ${action.title} (${action.timeframe})`);
            });
        } else {
            console.log(`   ✅ No immediate actions required!`);
        }

        // Overall assessment
        console.log(`\n🎯 Overall Assessment:`);
        if (summary.successRate >= 95) {
            console.log(`   🎉 EXCELLENT! Error recovery system is highly accessible.`);
        } else if (summary.successRate >= 85) {
            console.log(`   ✨ GOOD! Minor accessibility improvements needed.`);
        } else if (summary.successRate >= 70) {
            console.log(`   ⚠️  FAIR: Several accessibility issues need attention.`);
        } else {
            console.log(`   🔴 NEEDS WORK: Significant accessibility issues found.`);
        }

        console.log('='.repeat(60));
    }

    async saveReports() {
        console.log('\n💾 Saving comprehensive accessibility reports...');

        await fs.mkdir(this.options.outputDir, { recursive: true });

        // Save JSON report
        const jsonPath = path.join(this.options.outputDir, 'comprehensive-accessibility-report.json');
        await fs.writeFile(jsonPath, JSON.stringify(this.consolidatedResults, null, 2));
        console.log(`   ✅ JSON Report: ${jsonPath}`);

        // Generate and save HTML report
        if (this.options.generateHTML) {
            const htmlPath = path.join(this.options.outputDir, 'comprehensive-accessibility-report.html');
            const htmlReport = this.generateHTMLReport();
            await fs.writeFile(htmlPath, htmlReport);
            console.log(`   ✅ HTML Report: ${htmlPath}`);
        }

        // Generate executive summary
        const summaryPath = path.join(this.options.outputDir, 'accessibility-executive-summary.md');
        const executiveSummary = this.generateExecutiveSummary();
        await fs.writeFile(summaryPath, executiveSummary);
        console.log(`   ✅ Executive Summary: ${summaryPath}`);
    }

    generateHTMLReport() {
        const { summary } = this.consolidatedResults;

        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Accessibility Report - Error Recovery System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, sans-serif; line-height: 1.6; color: #333; background: #f5f7fa; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                 color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; text-align: center; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                       gap: 1rem; margin-bottom: 2rem; }
        .metric-card { background: white; padding: 1.5rem; border-radius: 8px;
                      box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
        .metric-value { font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem; }
        .success { color: #10b981; }
        .warning { color: #f59e0b; }
        .error { color: #ef4444; }
        .section { background: white; padding: 2rem; border-radius: 8px;
                   box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem; }
        .section h2 { color: #1f2937; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #e5e7eb; }
        .test-suite { border: 1px solid #e5e7eb; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; }
        .test-suite.error { border-left: 4px solid #ef4444; background: #fef2f2; }
        .test-suite.success { border-left: 4px solid #10b981; background: #f0fdf4; }
        .recommendation { background: #f8fafc; border-left: 4px solid #3b82f6; padding: 1rem; margin: 1rem 0; border-radius: 0 6px 6px 0; }
        .recommendation.high { border-left-color: #ef4444; background: #fef2f2; }
        .recommendation.medium { border-left-color: #f59e0b; background: #fffbeb; }
        .action-item { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 1rem; margin: 1rem 0; border-radius: 6px; }
        .action-item.immediate { background: #fef2f2; border-color: #fecaca; }
        .wcag-violation { padding: 0.5rem; margin: 0.5rem 0; border-radius: 4px; background: #fef2f2; border-left: 3px solid #ef4444; }
        .footer { text-align: center; padding: 2rem; color: #6b7280; }
        .progress-bar { background: #e5e7eb; height: 8px; border-radius: 4px; overflow: hidden; margin: 0.5rem 0; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #10b981 0%, #059669 100%); transition: width 0.3s ease; }
        @media (max-width: 768px) {
            .container { padding: 1rem; }
            .metrics-grid { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }
            .metric-value { font-size: 2rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Comprehensive Accessibility Report</h1>
            <h2>Error Recovery System - Phase 4 Testing</h2>
            <p>Generated on ${new Date().toLocaleString()}</p>
            <p>WCAG 2.1 AA Compliance Assessment</p>
        </div>

        <!-- Summary Metrics -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value ${summary.successRate >= 90 ? 'success' : summary.successRate >= 70 ? 'warning' : 'error'}">
                    ${summary.successRate}%
                </div>
                <div>Success Rate</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${summary.successRate}%"></div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-value success">${summary.passedTests}</div>
                <div>Tests Passed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value ${summary.failedTests > 0 ? 'error' : 'success'}">${summary.failedTests}</div>
                <div>Tests Failed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value ${summary.wcagViolations > 0 ? 'error' : 'success'}">${summary.wcagViolations}</div>
                <div>WCAG Violations</div>
            </div>
            <div class="metric-card">
                <div class="metric-value ${summary.warningTests > 0 ? 'warning' : 'success'}">${summary.warningTests}</div>
                <div>Warnings</div>
            </div>
            <div class="metric-card">
                <div class="metric-value success">${summary.totalTests}</div>
                <div>Total Tests</div>
            </div>
        </div>

        ${this.generateTestSuitesHTML()}
        ${this.generateWCAGComplianceHTML()}
        ${this.generateRecommendationsHTML()}
        ${this.generateActionItemsHTML()}
        ${this.generateSummaryHTML()}

        <div class="footer">
            <p>Generated by Claude Enhancer 5.0 Accessibility Testing Framework</p>
            <p>For questions or support, contact the development team</p>
        </div>
    </div>
</body>
</html>
        `;
    }

    generateTestSuitesHTML() {
        let html = '<div class="section"><h2>📋 Test Suite Results</h2>';

        for (const suite of this.consolidatedResults.testSuites) {
            const hasError = suite.summary.error;
            const className = hasError ? 'error' : 'success';

            html += `
            <div class="test-suite ${className}">
                <h3>${suite.name}</h3>
                ${hasError ?
                    `<p><strong>Status:</strong> ❌ ${suite.summary.message}</p>` :
                    `<div class="metrics-grid" style="grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 0.5rem; margin-top: 1rem;">
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem; font-weight: bold; color: #10b981;">${suite.summary.passed}</div>
                            <div style="font-size: 0.8rem; color: #6b7280;">Passed</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem; font-weight: bold; color: ${suite.summary.failed > 0 ? '#ef4444' : '#10b981'};">${suite.summary.failed}</div>
                            <div style="font-size: 0.8rem; color: #6b7280;">Failed</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem; font-weight: bold; color: ${suite.summary.warnings > 0 ? '#f59e0b' : '#10b981'};">${suite.summary.warnings || 0}</div>
                            <div style="font-size: 0.8rem; color: #6b7280;">Warnings</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem; font-weight: bold; color: #6b7280;">${suite.summary.total}</div>
                            <div style="font-size: 0.8rem; color: #6b7280;">Total</div>
                        </div>
                    </div>`
                }
            </div>
            `;
        }

        html += '</div>';
        return html;
    }

    generateWCAGComplianceHTML() {
        if (this.consolidatedResults.wcagCompliance.size === 0) {
            return `
            <div class="section">
                <h2>✅ WCAG Compliance</h2>
                <p style="color: #10b981; font-weight: 500;">🎉 No WCAG compliance violations detected! Your error recovery system meets accessibility standards.</p>
            </div>
            `;
        }

        let html = '<div class="section"><h2>⚠️ WCAG Compliance Issues</h2>';

        for (const [criteria, violations] of this.consolidatedResults.wcagCompliance) {
            html += `
            <div class="wcag-violation">
                <h4>${criteria} - ${this.wcagGuidelines[criteria] || 'Unknown Guideline'}</h4>
                <p><strong>${violations.length}</strong> violation${violations.length > 1 ? 's' : ''} found</p>
                <ul style="margin-left: 1rem; margin-top: 0.5rem;">
                    ${violations.slice(0, 3).map(v => `<li>${v.source}: ${v.violation?.description || v.test || 'Violation detected'}</li>`).join('')}
                    ${violations.length > 3 ? `<li><em>...and ${violations.length - 3} more</em></li>` : ''}
                </ul>
            </div>
            `;
        }

        html += '</div>';
        return html;
    }

    generateRecommendationsHTML() {
        let html = '<div class="section"><h2>💡 Accessibility Recommendations</h2>';

        if (this.consolidatedResults.recommendations.length === 0) {
            html += '<p style="color: #10b981;">🎉 No specific recommendations - your accessibility implementation looks great!</p>';
        } else {
            for (const rec of this.consolidatedResults.recommendations) {
                html += `
                <div class="recommendation ${rec.priority}">
                    <h4>${rec.priority.toUpperCase()} PRIORITY: ${rec.issue}</h4>
                    <p><strong>Category:</strong> ${rec.category} ${rec.wcag !== 'General' ? `| <strong>WCAG:</strong> ${rec.wcag}` : ''}</p>
                    <p><strong>Solution:</strong> ${rec.solution}</p>
                    <p><strong>Impact:</strong> ${rec.impact}</p>
                </div>
                `;
            }
        }

        html += '</div>';
        return html;
    }

    generateActionItemsHTML() {
        let html = '<div class="section"><h2>📋 Action Items</h2>';

        for (const action of this.consolidatedResults.actionItems) {
            html += `
            <div class="action-item ${action.priority}">
                <h4>${action.priority.toUpperCase()}: ${action.title}</h4>
                <p>${action.description}</p>
                <p><strong>Timeframe:</strong> ${action.timeframe} | <strong>Effort:</strong> ${action.effort}</p>
                <ul style="margin-left: 1rem; margin-top: 0.5rem;">
                    ${action.tasks.map(task => `<li>${task}</li>`).join('')}
                </ul>
            </div>
            `;
        }

        html += '</div>';
        return html;
    }

    generateSummaryHTML() {
        const { summary } = this.consolidatedResults;

        let assessment = '';
        let color = '';

        if (summary.successRate >= 95) {
            assessment = '🎉 EXCELLENT! Error recovery system is highly accessible.';
            color = '#10b981';
        } else if (summary.successRate >= 85) {
            assessment = '✨ GOOD! Minor accessibility improvements needed.';
            color = '#f59e0b';
        } else if (summary.successRate >= 70) {
            assessment = '⚠️ FAIR: Several accessibility issues need attention.';
            color = '#f59e0b';
        } else {
            assessment = '🔴 NEEDS WORK: Significant accessibility issues found.';
            color = '#ef4444';
        }

        return `
        <div class="section">
            <h2>🎯 Executive Summary</h2>
            <div style="background: #f8fafc; padding: 1.5rem; border-radius: 8px; border-left: 4px solid ${color};">
                <h3 style="color: ${color}; margin-bottom: 1rem;">${assessment}</h3>
                <p style="margin-bottom: 1rem;">
                    The error recovery system has been comprehensively tested for accessibility compliance.
                    Out of ${summary.totalTests} tests conducted across multiple test suites,
                    ${summary.passedTests} passed with ${summary.failedTests} failures and ${summary.warningTests} warnings.
                </p>
                <p>
                    ${summary.wcagViolations > 0 ?
                        `<strong>Key Finding:</strong> ${summary.wcagViolations} WCAG compliance issues were identified that should be addressed to ensure full accessibility.` :
                        '<strong>Key Finding:</strong> No critical WCAG compliance violations were detected.'
                    }
                </p>
            </div>
        </div>
        `;
    }

    generateExecutiveSummary() {
        const { summary } = this.consolidatedResults;

        return `# Error Recovery System - Accessibility Audit Executive Summary

**Date:** ${new Date().toDateString()}
**Audit Type:** Comprehensive WCAG 2.1 AA Compliance Assessment
**Scope:** Error recovery interfaces, messages, and user flows

## Executive Overview

The error recovery system underwent comprehensive accessibility testing to ensure compliance with WCAG 2.1 AA standards and usability for users with disabilities.

### Key Metrics

- **Overall Success Rate:** ${summary.successRate}%
- **Tests Conducted:** ${summary.totalTests}
- **Tests Passed:** ${summary.passedTests}
- **Tests Failed:** ${summary.failedTests}
- **WCAG Violations:** ${summary.wcagViolations}

### Test Coverage

${this.consolidatedResults.testSuites.map(suite =>
    `- **${suite.name}:** ${suite.summary.error ? 'ERROR - ' + suite.summary.message : `${suite.summary.passed}/${suite.summary.total} passed`}`
).join('\n')}

### Critical Findings

${this.consolidatedResults.wcagCompliance.size > 0 ?
    Array.from(this.consolidatedResults.wcagCompliance.entries())
        .slice(0, 5)
        .map(([criteria, violations]) =>
            `- **WCAG ${criteria}** (${this.wcagGuidelines[criteria]}): ${violations.length} violations`
        ).join('\n') :
    '✅ No critical WCAG compliance violations identified.'
}

### Priority Recommendations

${this.consolidatedResults.recommendations
    .filter(r => r.priority === 'high')
    .slice(0, 3)
    .map(rec => `- **${rec.category}:** ${rec.issue}`)
    .join('\n') || '✅ No high-priority issues identified.'}

### Immediate Actions Required

${this.consolidatedResults.actionItems
    .filter(a => a.priority === 'immediate')
    .map(action => `- ${action.title} (${action.timeframe})`)
    .join('\n') || '✅ No immediate actions required.'}

## Conclusion

${summary.successRate >= 95 ?
    'The error recovery system demonstrates excellent accessibility compliance with minimal issues requiring attention.' :
    summary.successRate >= 85 ?
    'The error recovery system shows good accessibility implementation with some areas for improvement.' :
    summary.successRate >= 70 ?
    'The error recovery system has moderate accessibility compliance but requires focused improvements.' :
    'The error recovery system requires significant accessibility improvements before production deployment.'
}

### Next Steps

1. **Immediate:** Address critical WCAG violations identified in the audit
2. **Short-term:** Implement recommendations for error message accessibility
3. **Medium-term:** Establish ongoing accessibility testing procedures
4. **Long-term:** Conduct user testing with people with disabilities

---

*This report was generated by the Claude Enhancer 5.0 Accessibility Testing Framework. For detailed technical findings, refer to the comprehensive HTML report.*
`;
    }
}

// CLI interface
if (require.main === module) {
    (async () => {
        try {
            const reporter = new ComprehensiveAccessibilityReporter({
                verbose: process.argv.includes('--verbose'),
                generateHTML: !process.argv.includes('--no-html')
            });

            const results = await reporter.generateComprehensiveReport();

            // Exit with appropriate code based on results
            const successRate = results.summary.successRate;
            if (successRate >= 95) {
                process.exit(0); // Excellent
            } else if (successRate >= 85) {
                process.exit(0); // Good, but with warnings
            } else {
                process.exit(1); // Needs improvement
            }

        } catch (error) {
            console.error('❌ Accessibility report generation failed:', error);
            process.exit(1);
        }
    })();
}

module.exports = ComprehensiveAccessibilityReporter;