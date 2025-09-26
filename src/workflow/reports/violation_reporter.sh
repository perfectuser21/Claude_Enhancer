#!/bin/bash

# ================================================================
# Violation Reporter Module
# Claude Enhancer 5.0 - Permission violation reporting and analysis
# ================================================================

set -euo pipefail

# Generate HTML violation report
generate_html_report() {
    local json_report="$1"
    local html_output="$2"

    cat > "$html_output" <<'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Enhancer 5.0 - Permission Violation Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e1e8ed;
        }
        .header h1 {
            color: #1a1a1a;
            margin: 0;
            font-size: 2.5em;
        }
        .header p {
            color: #666;
            font-size: 1.1em;
            margin: 10px 0;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
            border-left: 4px solid #007bff;
        }
        .metric-card.danger {
            border-left-color: #dc3545;
            background: #fff5f5;
        }
        .metric-card.warning {
            border-left-color: #ffc107;
            background: #fffbf0;
        }
        .metric-card.success {
            border-left-color: #28a745;
            background: #f0fff4;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 0;
        }
        .metric-label {
            color: #666;
            margin: 5px 0 0 0;
            font-size: 0.9em;
        }
        .violations-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
        }
        .violations-table th,
        .violations-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .violations-table th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        .violations-table tr:hover {
            background-color: #f5f5f5;
        }
        .severity-high {
            color: #dc3545;
            font-weight: bold;
        }
        .severity-medium {
            color: #ffc107;
            font-weight: bold;
        }
        .severity-low {
            color: #28a745;
            font-weight: bold;
        }
        .chart-container {
            margin: 30px 0;
            text-align: center;
        }
        .phase-bar {
            display: inline-block;
            vertical-align: bottom;
            margin: 0 5px;
            background: #007bff;
            color: white;
            padding: 5px;
            border-radius: 3px 3px 0 0;
            min-width: 40px;
            text-align: center;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e1e8ed;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Permission Violation Report</h1>
            <p>Claude Enhancer 5.0 Security Audit</p>
            <p id="report-date"></p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card danger">
                <h2 class="metric-value" id="total-violations">0</h2>
                <p class="metric-label">Total Violations</p>
            </div>
            <div class="metric-card warning">
                <h2 class="metric-value" id="phases-affected">0</h2>
                <p class="metric-label">Phases Affected</p>
            </div>
            <div class="metric-card warning">
                <h2 class="metric-value" id="tools-involved">0</h2>
                <p class="metric-label">Tools Involved</p>
            </div>
            <div class="metric-card success">
                <h2 class="metric-value" id="compliance-score">0%</h2>
                <p class="metric-label">Compliance Score</p>
            </div>
        </div>

        <div class="chart-container">
            <h3>Violations by Phase</h3>
            <div id="phase-chart"></div>
        </div>

        <div class="chart-container">
            <h3>Violations by Tool</h3>
            <div id="tool-chart"></div>
        </div>

        <h3>Detailed Violations</h3>
        <table class="violations-table">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Phase</th>
                    <th>Tool</th>
                    <th>Violation Type</th>
                    <th>Details</th>
                    <th>Severity</th>
                </tr>
            </thead>
            <tbody id="violations-tbody">
                <!-- Violations will be populated by JavaScript -->
            </tbody>
        </table>

        <div class="footer">
            <p>Generated by Claude Enhancer 5.0 Permission Controller</p>
            <p>Report Version: 5.0.0</p>
        </div>
    </div>

    <script>
        // Load and display report data
        function loadReportData() {
EOF

    # Embed JSON data into HTML
    echo "            const reportData = " >> "$html_output"
    cat "$json_report" >> "$html_output"
    echo ";" >> "$html_output"

    cat >> "$html_output" <<'EOF'

            // Update metrics
            document.getElementById('total-violations').textContent = reportData.summary.total_violations || 0;
            document.getElementById('report-date').textContent = 'Generated: ' + new Date(reportData.report_metadata.generated_at).toLocaleString();

            // Calculate derived metrics
            const phasesAffected = Object.keys(reportData.violations_by_phase || {}).length;
            const toolsInvolved = Object.keys(reportData.violations_by_tool || {}).length;
            const totalViolations = reportData.summary.total_violations || 0;
            const complianceScore = Math.max(0, 100 - (totalViolations * 5));

            document.getElementById('phases-affected').textContent = phasesAffected;
            document.getElementById('tools-involved').textContent = toolsInvolved;
            document.getElementById('compliance-score').textContent = complianceScore + '%';

            // Update compliance score color
            const complianceCard = document.querySelector('#compliance-score').closest('.metric-card');
            if (complianceScore >= 80) {
                complianceCard.className = 'metric-card success';
            } else if (complianceScore >= 60) {
                complianceCard.className = 'metric-card warning';
            } else {
                complianceCard.className = 'metric-card danger';
            }

            // Generate phase chart
            const phaseChart = document.getElementById('phase-chart');
            const phaseData = reportData.violations_by_phase || {};
            const maxPhaseViolations = Math.max(...Object.values(phaseData), 1);

            Object.entries(phaseData).forEach(([phase, count]) => {
                const height = Math.max(20, (count / maxPhaseViolations) * 100);
                const bar = document.createElement('div');
                bar.className = 'phase-bar';
                bar.style.height = height + 'px';
                bar.innerHTML = `<div>${phase}</div><div>${count}</div>`;
                phaseChart.appendChild(bar);
            });

            // Generate tool chart
            const toolChart = document.getElementById('tool-chart');
            const toolData = reportData.violations_by_tool || {};
            const maxToolViolations = Math.max(...Object.values(toolData), 1);

            Object.entries(toolData).forEach(([tool, count]) => {
                const height = Math.max(20, (count / maxToolViolations) * 100);
                const bar = document.createElement('div');
                bar.className = 'phase-bar';
                bar.style.height = height + 'px';
                bar.innerHTML = `<div>${tool}</div><div>${count}</div>`;
                toolChart.appendChild(bar);
            });

            // Populate violations table
            const tbody = document.getElementById('violations-tbody');
            const violations = reportData.detailed_violations || [];

            violations.forEach(violation => {
                const row = document.createElement('tr');
                const timestamp = new Date(violation.timestamp).toLocaleString();
                const severityClass = `severity-${violation.severity.toLowerCase()}`;

                row.innerHTML = `
                    <td>${timestamp}</td>
                    <td>${violation.phase}</td>
                    <td>${violation.tool}</td>
                    <td>${violation.violation_type}</td>
                    <td>${violation.details}</td>
                    <td class="${severityClass}">${violation.severity}</td>
                `;
                tbody.appendChild(row);
            });
        }

        // Load data when page loads
        document.addEventListener('DOMContentLoaded', loadReportData);
    </script>
</body>
</html>
EOF

    echo "HTML report generated: $html_output"
}

# Generate CSV report for data analysis
generate_csv_report() {
    local json_report="$1"
    local csv_output="$2"

    echo "timestamp,phase,tool,violation_type,details,severity" > "$csv_output"

    jq -r '.detailed_violations[] | [.timestamp, .phase, .tool, .violation_type, .details, .severity] | @csv' "$json_report" >> "$csv_output"

    echo "CSV report generated: $csv_output"
}

# Export functions for use in main controller
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    export -f generate_html_report generate_csv_report
fi