#!/usr/bin/env python3
"""
Perfect21 测试仪表板生成器
生成HTML仪表板展示测试结果和覆盖率
"""

import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

class TestDashboardGenerator:
    """测试仪表板生成器"""
    
    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.project_root = test_dir.parent
        self.dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'project': 'Perfect21 Login API Testing',
            'test_suites': [],
            'coverage': {},
            'security': {},
            'performance': {},
            'summary': {}
        }
    
    def collect_test_data(self):
        """收集测试数据"""
        print("📈 正在收集测试数据...")
        
        # 收集JUnit XML文件
        self._collect_junit_results()
        
        # 收集覆盖率数据
        self._collect_coverage_data()
        
        # 收集安全扫描结果
        self._collect_security_data()
        
        # 收集性能测试结果
        self._collect_performance_data()
        
        # 计算综合统计
        self._calculate_summary()
    
    def _collect_junit_results(self):
        """收集JUnit测试结果"""
        junit_files = [
            ('unit', 'junit-unit.xml'),
            ('integration', 'junit-integration.xml'),
            ('security', 'junit-security.xml'),
            ('performance', 'junit-performance.xml'),
            ('e2e', 'junit-e2e.xml')
        ]
        
        for test_type, filename in junit_files:
            filepath = self.project_root / filename
            if filepath.exists():
                try:
                    tree = ET.parse(filepath)
                    root = tree.getroot()
                    
                    test_suite = {
                        'name': test_type,
                        'tests': int(root.get('tests', 0)),
                        'failures': int(root.get('failures', 0)),
                        'errors': int(root.get('errors', 0)),
                        'skipped': int(root.get('skipped', 0)),
                        'time': float(root.get('time', 0.0)),
                        'test_cases': []
                    }
                    
                    # 收集测试用例详情
                    for testcase in root.findall('.//testcase'):
                        case_info = {
                            'name': testcase.get('name', ''),
                            'classname': testcase.get('classname', ''),
                            'time': float(testcase.get('time', 0.0)),
                            'status': 'passed'
                        }
                        
                        # 检查失败或错误
                        if testcase.find('failure') is not None:
                            case_info['status'] = 'failed'
                            case_info['message'] = testcase.find('failure').get('message', '')
                        elif testcase.find('error') is not None:
                            case_info['status'] = 'error'
                            case_info['message'] = testcase.find('error').get('message', '')
                        elif testcase.find('skipped') is not None:
                            case_info['status'] = 'skipped'
                        
                        test_suite['test_cases'].append(case_info)
                    
                    # 计算成功率
                    total_tests = test_suite['tests']
                    if total_tests > 0:
                        passed = total_tests - test_suite['failures'] - test_suite['errors'] - test_suite['skipped']
                        test_suite['success_rate'] = (passed / total_tests) * 100
                    else:
                        test_suite['success_rate'] = 0
                    
                    self.dashboard_data['test_suites'].append(test_suite)
                    
                except ET.ParseError as e:
                    print(f"⚠️ 解析JUnit文件失败 {filename}: {e}")
    
    def _collect_coverage_data(self):
        """收集覆盖率数据"""
        coverage_file = self.project_root / 'coverage-unit.xml'
        
        if coverage_file.exists():
            try:
                tree = ET.parse(coverage_file)
                root = tree.getroot()
                
                # 获取总体覆盖率
                coverage_elem = root.find('.//coverage')
                if coverage_elem is not None:
                    line_rate = float(coverage_elem.get('line-rate', 0))
                    branch_rate = float(coverage_elem.get('branch-rate', 0))
                    
                    self.dashboard_data['coverage'] = {
                        'line_coverage': line_rate * 100,
                        'branch_coverage': branch_rate * 100,
                        'packages': []
                    }
                    
                    # 获取模块级别覆盖率
                    for package in root.findall('.//package'):
                        package_name = package.get('name', '')
                        package_line_rate = float(package.get('line-rate', 0))
                        package_branch_rate = float(package.get('branch-rate', 0))
                        
                        self.dashboard_data['coverage']['packages'].append({
                            'name': package_name,
                            'line_coverage': package_line_rate * 100,
                            'branch_coverage': package_branch_rate * 100
                        })
            
            except ET.ParseError as e:
                print(f"⚠️ 解析覆盖率文件失败: {e}")
    
    def _collect_security_data(self):
        """收集安全扫描数据"""
        bandit_file = self.project_root / 'bandit-report.json'
        
        if bandit_file.exists():
            try:
                with open(bandit_file, 'r') as f:
                    bandit_data = json.load(f)
                
                self.dashboard_data['security'] = {
                    'bandit': {
                        'high_issues': len([r for r in bandit_data.get('results', []) if r.get('issue_severity') == 'HIGH']),
                        'medium_issues': len([r for r in bandit_data.get('results', []) if r.get('issue_severity') == 'MEDIUM']),
                        'low_issues': len([r for r in bandit_data.get('results', []) if r.get('issue_severity') == 'LOW']),
                        'total_issues': len(bandit_data.get('results', [])),
                        'files_scanned': len(bandit_data.get('metrics', {}).get('_totals', {}).get('CONFIDENCE.HIGH', 0))
                    }
                }
            
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"⚠️ 读取Bandit报告失败: {e}")
    
    def _collect_performance_data(self):
        """收集性能测试数据"""
        # 收集benchmark结果
        benchmark_file = self.project_root / 'benchmark-results.json'
        if benchmark_file.exists():
            try:
                with open(benchmark_file, 'r') as f:
                    benchmark_data = json.load(f)
                
                self.dashboard_data['performance']['benchmarks'] = benchmark_data
            
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"⚠️ 读取性能测试结果失败: {e}")
        
        # 收集负载测试结果
        import glob
        load_test_files = glob.glob(str(self.project_root / 'load_test_report_*.md'))
        if load_test_files:
            # 取最新的报告
            latest_report = max(load_test_files, key=os.path.getctime)
            self.dashboard_data['performance']['load_test_report'] = latest_report
    
    def _calculate_summary(self):
        """计算综合统计"""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_time = 0
        
        for suite in self.dashboard_data['test_suites']:
            total_tests += suite['tests']
            total_failed += suite['failures'] + suite['errors']
            total_skipped += suite['skipped']
            total_time += suite['time']
        
        total_passed = total_tests - total_failed - total_skipped
        
        self.dashboard_data['summary'] = {
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'total_time': total_time,
            'test_suites_count': len(self.dashboard_data['test_suites'])
        }
    
    def generate_html_dashboard(self, output_file: str = 'test_dashboard.html'):
        """生成HTML仪表板"""
        html_template = self._get_html_template()
        
        # 替换模板中的数据
        html_content = html_template.replace('{{DASHBOARD_DATA}}', json.dumps(self.dashboard_data, indent=2))
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📈 测试仪表板已生成: {output_file}")
        return output_file
    
    def _get_html_template(self) -> str:
        """获取HTML模板"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perfect21 Login API 测试仪表板</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .dashboard {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.8;
            font-size: 1.1em;
        }
        
        .content {
            padding: 30px;
        }
        
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 4px solid;
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card.success { border-left-color: #27ae60; }
        .card.warning { border-left-color: #f39c12; }
        .card.danger { border-left-color: #e74c3c; }
        .card.info { border-left-color: #3498db; }
        
        .card-title {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        
        .card-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .card-subtitle {
            font-size: 0.8em;
            color: #999;
            margin-top: 5px;
        }
        
        .charts-section {
            margin-top: 30px;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .chart-container {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .chart-title {
            font-size: 1.3em;
            color: #2c3e50;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .test-suites {
            margin-top: 30px;
        }
        
        .suite-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .suite-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .suite-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
            text-transform: capitalize;
        }
        
        .suite-status {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-success {
            background: #d4edda;
            color: #155724;
        }
        
        .status-warning {
            background: #fff3cd;
            color: #856404;
        }
        
        .status-danger {
            background: #f8d7da;
            color: #721c24;
        }
        
        .suite-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .stat {
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        
        .stat-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .stat-label {
            font-size: 0.8em;
            color: #666;
            text-transform: uppercase;
        }
        
        .progress-bar {
            width: 100%;
            height: 10px;
            background: #e9ecef;
            border-radius: 5px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #27ae60, #2ecc71);
            transition: width 0.3s ease;
        }
        
        .test-cases {
            margin-top: 15px;
        }
        
        .test-case {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        
        .test-case:last-child {
            border-bottom: none;
        }
        
        .test-case-name {
            font-family: monospace;
            font-size: 0.9em;
        }
        
        .test-case-status {
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.7em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .test-passed { background: #d4edda; color: #155724; }
        .test-failed { background: #f8d7da; color: #721c24; }
        .test-skipped { background: #fff3cd; color: #856404; }
        .test-error { background: #f8d7da; color: #721c24; }
        
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            margin-top: 30px;
        }
        
        .btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
            margin: 5px;
            transition: background 0.3s ease;
        }
        
        .btn:hover {
            background: #2980b9;
        }
        
        @media (max-width: 768px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
            
            .summary-cards {
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            }
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🔒 Perfect21 Login API</h1>
            <p>测试综合仪表板</p>
            <p id="timestamp"></p>
        </div>
        
        <div class="content">
            <!-- 概览卡片 -->
            <div class="summary-cards" id="summaryCards"></div>
            
            <!-- 图表区域 -->
            <div class="charts-section">
                <div class="charts-grid">
                    <div class="chart-container">
                        <div class="chart-title">测试结果分布</div>
                        <canvas id="testResultsChart"></canvas>
                    </div>
                    
                    <div class="chart-container">
                        <div class="chart-title">测试套件成功率</div>
                        <canvas id="suiteSuccessChart"></canvas>
                    </div>
                    
                    <div class="chart-container" id="coverageChartContainer" style="display: none;">
                        <div class="chart-title">代码覆盖率</div>
                        <canvas id="coverageChart"></canvas>
                    </div>
                    
                    <div class="chart-container" id="securityChartContainer" style="display: none;">
                        <div class="chart-title">安全问题分布</div>
                        <canvas id="securityChart"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- 测试套件详情 -->
            <div class="test-suites">
                <h2>📋 测试套件详情</h2>
                <div id="testSuitesContainer"></div>
            </div>
        </div>
        
        <div class="footer">
            <p>生成时间: <span id="generatedTime"></span></p>
            <button class="btn" onclick="location.reload()">刷新数据</button>
            <button class="btn" onclick="exportData()">导出数据</button>
        </div>
    </div>
    
    <script>
        // 测试数据
        const dashboardData = {{DASHBOARD_DATA}};
        
        // 初始化仪表板
        function initDashboard() {
            updateTimestamp();
            createSummaryCards();
            createCharts();
            createTestSuiteDetails();
        }
        
        function updateTimestamp() {
            const timestamp = new Date(dashboardData.timestamp);
            document.getElementById('timestamp').textContent = timestamp.toLocaleString('zh-CN');
            document.getElementById('generatedTime').textContent = timestamp.toLocaleString('zh-CN');
        }
        
        function createSummaryCards() {
            const summary = dashboardData.summary;
            const container = document.getElementById('summaryCards');
            
            const cards = [
                {
                    title: '总测试数',
                    value: summary.total_tests,
                    subtitle: `${summary.test_suites_count} 个测试套件`,
                    type: 'info'
                },
                {
                    title: '通过测试',
                    value: summary.total_passed,
                    subtitle: `成功率 ${summary.success_rate.toFixed(1)}%`,
                    type: 'success'
                },
                {
                    title: '失败测试',
                    value: summary.total_failed,
                    subtitle: '需要修复',
                    type: summary.total_failed > 0 ? 'danger' : 'success'
                },
                {
                    title: '执行时间',
                    value: `${summary.total_time.toFixed(1)}s`,
                    subtitle: '总耗时',
                    type: 'info'
                }
            ];
            
            // 添加覆盖率卡片
            if (dashboardData.coverage && dashboardData.coverage.line_coverage) {
                cards.push({
                    title: '代码覆盖率',
                    value: `${dashboardData.coverage.line_coverage.toFixed(1)}%`,
                    subtitle: '行覆盖率',
                    type: dashboardData.coverage.line_coverage >= 80 ? 'success' : 'warning'
                });
            }
            
            // 添加安全问题卡片
            if (dashboardData.security && dashboardData.security.bandit) {
                const securityIssues = dashboardData.security.bandit.total_issues;
                cards.push({
                    title: '安全问题',
                    value: securityIssues,
                    subtitle: `${dashboardData.security.bandit.high_issues} 高危问题`,
                    type: securityIssues === 0 ? 'success' : securityIssues > 5 ? 'danger' : 'warning'
                });
            }
            
            container.innerHTML = cards.map(card => `
                <div class="card ${card.type}">
                    <div class="card-title">${card.title}</div>
                    <div class="card-value">${card.value}</div>
                    <div class="card-subtitle">${card.subtitle}</div>
                </div>
            `).join('');
        }
        
        function createCharts() {
            createTestResultsChart();
            createSuiteSuccessChart();
            
            if (dashboardData.coverage && dashboardData.coverage.line_coverage) {
                createCoverageChart();
            }
            
            if (dashboardData.security && dashboardData.security.bandit) {
                createSecurityChart();
            }
        }
        
        function createTestResultsChart() {
            const ctx = document.getElementById('testResultsChart').getContext('2d');
            const summary = dashboardData.summary;
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['通过', '失败', '跳过'],
                    datasets: [{
                        data: [summary.total_passed, summary.total_failed, summary.total_skipped],
                        backgroundColor: ['#27ae60', '#e74c3c', '#f39c12'],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
        
        function createSuiteSuccessChart() {
            const ctx = document.getElementById('suiteSuccessChart').getContext('2d');
            const suites = dashboardData.test_suites;
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: suites.map(s => s.name),
                    datasets: [{
                        label: '成功率 (%)',
                        data: suites.map(s => s.success_rate),
                        backgroundColor: suites.map(s => s.success_rate >= 90 ? '#27ae60' : s.success_rate >= 70 ? '#f39c12' : '#e74c3c'),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
        
        function createCoverageChart() {
            const container = document.getElementById('coverageChartContainer');
            container.style.display = 'block';
            
            const ctx = document.getElementById('coverageChart').getContext('2d');
            const coverage = dashboardData.coverage;
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['行覆盖率', '分支覆盖率'],
                    datasets: [{
                        label: '覆盖率 (%)',
                        data: [coverage.line_coverage, coverage.branch_coverage],
                        backgroundColor: ['#3498db', '#9b59b6'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
        
        function createSecurityChart() {
            const container = document.getElementById('securityChartContainer');
            container.style.display = 'block';
            
            const ctx = document.getElementById('securityChart').getContext('2d');
            const security = dashboardData.security.bandit;
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['高危', '中危', '低危'],
                    datasets: [{
                        data: [security.high_issues, security.medium_issues, security.low_issues],
                        backgroundColor: ['#e74c3c', '#f39c12', '#f1c40f'],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
        
        function createTestSuiteDetails() {
            const container = document.getElementById('testSuitesContainer');
            const suites = dashboardData.test_suites;
            
            container.innerHTML = suites.map(suite => {
                const statusClass = suite.success_rate >= 90 ? 'status-success' : 
                                  suite.success_rate >= 70 ? 'status-warning' : 'status-danger';
                
                const passed = suite.tests - suite.failures - suite.errors - suite.skipped;
                
                return `
                    <div class="suite-card">
                        <div class="suite-header">
                            <div class="suite-name">${suite.name} 测试</div>
                            <div class="suite-status ${statusClass}">
                                ${suite.success_rate.toFixed(1)}% 成功率
                            </div>
                        </div>
                        
                        <div class="suite-stats">
                            <div class="stat">
                                <div class="stat-value">${suite.tests}</div>
                                <div class="stat-label">总数</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">${passed}</div>
                                <div class="stat-label">通过</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">${suite.failures}</div>
                                <div class="stat-label">失败</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">${suite.errors}</div>
                                <div class="stat-label">错误</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">${suite.skipped}</div>
                                <div class="stat-label">跳过</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">${suite.time.toFixed(2)}s</div>
                                <div class="stat-label">时间</div>
                            </div>
                        </div>
                        
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${suite.success_rate}%"></div>
                        </div>
                        
                        ${suite.test_cases.length > 0 ? createTestCasesHTML(suite.test_cases) : ''}
                    </div>
                `;
            }).join('');
        }
        
        function createTestCasesHTML(testCases) {
            const maxCases = 10; // 最多显示10个测试用例
            const displayCases = testCases.slice(0, maxCases);
            
            return `
                <div class="test-cases">
                    <h4>测试用例 (${displayCases.length}/${testCases.length})</h4>
                    ${displayCases.map(testCase => `
                        <div class="test-case">
                            <div class="test-case-name">${testCase.name}</div>
                            <div class="test-case-status test-${testCase.status}">${testCase.status}</div>
                        </div>
                    `).join('')}
                    ${testCases.length > maxCases ? `<p>… 及其他 ${testCases.length - maxCases} 个测试用例</p>` : ''}
                </div>
            `;
        }
        
        function exportData() {
            const dataStr = JSON.stringify(dashboardData, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'test_results.json';
            link.click();
            URL.revokeObjectURL(url);
        }
        
        // 初始化仪表板
        document.addEventListener('DOMContentLoaded', initDashboard);
    </script>
</body>
</html>
        """


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Perfect21 测试仪表板生成器')
    parser.add_argument('--test-dir', type=Path, default=Path(__file__).parent, help='测试目录路径')
    parser.add_argument('--output', default='test_dashboard.html', help='输出文件名')
    
    args = parser.parse_args()
    
    # 初始化生成器
    generator = TestDashboardGenerator(args.test_dir)
    
    # 收集数据
    generator.collect_test_data()
    
    # 生成HTML仪表板
    output_file = generator.generate_html_dashboard(args.output)
    
    print(f"✅ 仪表板生成完成: {output_file}")
    print(f"🌍 可以在浏览器中打开: file://{os.path.abspath(output_file)}")


if __name__ == '__main__':
    main()
