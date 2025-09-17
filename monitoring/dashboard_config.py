#!/usr/bin/env python3
"""
Dashboard Configuration - Perfect21 Performance Dashboards
生成Grafana仪表板配置和自定义监控面板
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class GrafanaDashboardGenerator:
    """Grafana仪表板生成器"""

    def __init__(self):
        self.dashboard_template = {
            "annotations": {
                "list": [
                    {
                        "builtIn": 1,
                        "datasource": "-- Grafana --",
                        "enable": True,
                        "hide": True,
                        "iconColor": "rgba(0, 211, 255, 1)",
                        "name": "Annotations & Alerts",
                        "type": "dashboard"
                    }
                ]
            },
            "editable": True,
            "gnetId": None,
            "graphTooltip": 0,
            "id": None,
            "links": [],
            "panels": [],
            "schemaVersion": 27,
            "style": "dark",
            "tags": ["perfect21", "monitoring"],
            "templating": {
                "list": []
            },
            "time": {
                "from": "now-1h",
                "to": "now"
            },
            "timepicker": {},
            "timezone": "",
            "version": 1
        }

    def create_overview_dashboard(self) -> Dict[str, Any]:
        """创建Perfect21概览仪表板"""
        dashboard = self.dashboard_template.copy()
        dashboard.update({
            "title": "Perfect21 Overview",
            "description": "Perfect21 System Overview Dashboard",
            "uid": "perfect21-overview",
            "panels": [
                self._create_system_metrics_panel(0, 0, 12, 8),
                self._create_api_metrics_panel(12, 0, 12, 8),
                self._create_agent_execution_panel(0, 8, 12, 8),
                self._create_git_workflow_panel(12, 8, 12, 8),
                self._create_error_rate_panel(0, 16, 24, 6),
                self._create_performance_heatmap(0, 22, 24, 8)
            ]
        })
        return dashboard

    def create_agent_performance_dashboard(self) -> Dict[str, Any]:
        """创建Agent性能仪表板"""
        dashboard = self.dashboard_template.copy()
        dashboard.update({
            "title": "Perfect21 Agent Performance",
            "description": "Detailed Agent Execution Metrics",
            "uid": "perfect21-agents",
            "panels": [
                self._create_agent_throughput_panel(0, 0, 12, 8),
                self._create_agent_latency_panel(12, 0, 12, 8),
                self._create_parallel_execution_panel(0, 8, 12, 8),
                self._create_agent_success_rate_panel(12, 8, 12, 8),
                self._create_workflow_comparison_panel(0, 16, 24, 10)
            ]
        })
        return dashboard

    def create_quality_dashboard(self) -> Dict[str, Any]:
        """创建质量监控仪表板"""
        dashboard = self.dashboard_template.copy()
        dashboard.update({
            "title": "Perfect21 Quality Metrics",
            "description": "Code Quality and Testing Metrics",
            "uid": "perfect21-quality",
            "panels": [
                self._create_code_coverage_panel(0, 0, 12, 8),
                self._create_quality_checks_panel(12, 0, 12, 8),
                self._create_sync_point_panel(0, 8, 12, 8),
                self._create_error_trends_panel(12, 8, 12, 8),
                self._create_test_results_panel(0, 16, 24, 8)
            ]
        })
        return dashboard

    def create_infrastructure_dashboard(self) -> Dict[str, Any]:
        """创建基础设施监控仪表板"""
        dashboard = self.dashboard_template.copy()
        dashboard.update({
            "title": "Perfect21 Infrastructure",
            "description": "System Resources and Infrastructure Metrics",
            "uid": "perfect21-infrastructure",
            "panels": [
                self._create_cpu_memory_panel(0, 0, 12, 8),
                self._create_disk_network_panel(12, 0, 12, 8),
                self._create_service_status_panel(0, 8, 12, 8),
                self._create_cache_metrics_panel(12, 8, 12, 8),
                self._create_database_panel(0, 16, 24, 8)
            ]
        })
        return dashboard

    def _create_system_metrics_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """系统指标面板"""
        return {
            "id": 1,
            "title": "System Metrics",
            "type": "stat",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "perfect21_system_cpu_usage_percent",
                    "legendFormat": "CPU Usage %",
                    "refId": "A"
                },
                {
                    "expr": "perfect21_system_memory_usage_bytes{type='used'} / perfect21_system_memory_usage_bytes{type='total'} * 100",
                    "legendFormat": "Memory Usage %",
                    "refId": "B"
                },
                {
                    "expr": "perfect21_application_uptime_seconds / 3600",
                    "legendFormat": "Uptime Hours",
                    "refId": "C"
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "steps": [
                            {"color": "green", "value": 0},
                            {"color": "yellow", "value": 70},
                            {"color": "red", "value": 90}
                        ]
                    },
                    "unit": "percent"
                }
            }
        }

    def _create_api_metrics_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """API指标面板"""
        return {
            "id": 2,
            "title": "API Performance",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "rate(perfect21_api_requests_total[5m])",
                    "legendFormat": "Requests/sec - {{method}} {{endpoint}}",
                    "refId": "A"
                },
                {
                    "expr": "histogram_quantile(0.95, rate(perfect21_api_request_duration_seconds_bucket[5m]))",
                    "legendFormat": "95th Percentile Latency",
                    "refId": "B"
                }
            ],
            "yAxes": [
                {"label": "Requests/sec", "unit": "reqps"},
                {"label": "Latency", "unit": "s"}
            ]
        }

    def _create_agent_execution_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """Agent执行面板"""
        return {
            "id": 3,
            "title": "Agent Executions",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "rate(perfect21_agent_executions_total{status='success'}[5m])",
                    "legendFormat": "Successful - {{agent_name}}",
                    "refId": "A"
                },
                {
                    "expr": "rate(perfect21_agent_executions_total{status='error'}[5m])",
                    "legendFormat": "Failed - {{agent_name}}",
                    "refId": "B"
                },
                {
                    "expr": "histogram_quantile(0.95, rate(perfect21_agent_execution_duration_seconds_bucket[5m]))",
                    "legendFormat": "95th Percentile Duration",
                    "refId": "C"
                }
            ]
        }

    def _create_git_workflow_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """Git工作流面板"""
        return {
            "id": 4,
            "title": "Git Workflow",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "rate(perfect21_git_operations_total[5m])",
                    "legendFormat": "{{operation}} - {{status}}",
                    "refId": "A"
                },
                {
                    "expr": "rate(perfect21_git_hooks_executions_total[5m])",
                    "legendFormat": "Hook: {{hook_type}}",
                    "refId": "B"
                }
            ]
        }

    def _create_error_rate_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """错误率面板"""
        return {
            "id": 5,
            "title": "Error Rates",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "rate(perfect21_errors_total[5m])",
                    "legendFormat": "{{error_type}} - {{component}}",
                    "refId": "A"
                },
                {
                    "expr": "rate(perfect21_error_recovery_attempts_total{status='success'}[5m])",
                    "legendFormat": "Recovery Success",
                    "refId": "B"
                }
            ],
            "yAxes": [{"label": "Errors/sec", "min": 0}],
            "alert": {
                "conditions": [
                    {
                        "evaluator": {"params": [0.1], "type": "gt"},
                        "operator": {"type": "and"},
                        "query": {"params": ["A", "5m", "now"]},
                        "reducer": {"params": [], "type": "avg"},
                        "type": "query"
                    }
                ],
                "executionErrorState": "alerting",
                "for": "5m",
                "frequency": "10s",
                "handler": 1,
                "name": "High Error Rate",
                "noDataState": "no_data",
                "notifications": []
            }
        }

    def _create_performance_heatmap(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """性能热力图"""
        return {
            "id": 6,
            "title": "Performance Heatmap",
            "type": "heatmap",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "increase(perfect21_agent_execution_duration_seconds_bucket[5m])",
                    "format": "heatmap",
                    "legendFormat": "{{le}}",
                    "refId": "A"
                }
            ],
            "heatmap": {
                "hideZeroBuckets": True,
                "highlightCards": True,
                "highlightInSeries": True
            },
            "xAxis": {"show": True},
            "yAxis": {
                "decimals": 0,
                "format": "s",
                "logBase": 1,
                "max": None,
                "min": None,
                "show": True
            }
        }

    def _create_agent_throughput_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """Agent吞吐量面板"""
        return {
            "id": 7,
            "title": "Agent Throughput",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "sum(rate(perfect21_agent_executions_total[5m])) by (agent_name)",
                    "legendFormat": "{{agent_name}}",
                    "refId": "A"
                }
            ]
        }

    def _create_agent_latency_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """Agent延迟面板"""
        return {
            "id": 8,
            "title": "Agent Latency Distribution",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "histogram_quantile(0.50, rate(perfect21_agent_execution_duration_seconds_bucket[5m]))",
                    "legendFormat": "50th percentile",
                    "refId": "A"
                },
                {
                    "expr": "histogram_quantile(0.95, rate(perfect21_agent_execution_duration_seconds_bucket[5m]))",
                    "legendFormat": "95th percentile",
                    "refId": "B"
                },
                {
                    "expr": "histogram_quantile(0.99, rate(perfect21_agent_execution_duration_seconds_bucket[5m]))",
                    "legendFormat": "99th percentile",
                    "refId": "C"
                }
            ]
        }

    def _create_parallel_execution_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """并行执行面板"""
        return {
            "id": 9,
            "title": "Parallel Execution Performance",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "rate(perfect21_parallel_executions_total[5m])",
                    "legendFormat": "{{workflow_type}} - {{status}}",
                    "refId": "A"
                },
                {
                    "expr": "avg(perfect21_parallel_execution_duration_seconds) by (workflow_type)",
                    "legendFormat": "Avg Duration - {{workflow_type}}",
                    "refId": "B"
                }
            ]
        }

    def _create_agent_success_rate_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """Agent成功率面板"""
        return {
            "id": 10,
            "title": "Agent Success Rate",
            "type": "stat",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "rate(perfect21_agent_executions_total{status='success'}[5m]) / rate(perfect21_agent_executions_total[5m]) * 100",
                    "legendFormat": "{{agent_name}}",
                    "refId": "A"
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "steps": [
                            {"color": "red", "value": 0},
                            {"color": "yellow", "value": 95},
                            {"color": "green", "value": 99}
                        ]
                    },
                    "unit": "percent"
                }
            }
        }

    def _create_workflow_comparison_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """工作流对比面板"""
        return {
            "id": 11,
            "title": "Workflow Performance Comparison",
            "type": "table",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "sum(rate(perfect21_parallel_executions_total[1h])) by (workflow_type)",
                    "format": "table",
                    "instant": True,
                    "refId": "A"
                },
                {
                    "expr": "avg(perfect21_parallel_execution_duration_seconds) by (workflow_type)",
                    "format": "table",
                    "instant": True,
                    "refId": "B"
                }
            ]
        }

    def _create_code_coverage_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """代码覆盖率面板"""
        return {
            "id": 12,
            "title": "Code Coverage",
            "type": "gauge",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "perfect21_code_coverage_percentage",
                    "legendFormat": "{{project}}",
                    "refId": "A"
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "steps": [
                            {"color": "red", "value": 0},
                            {"color": "yellow", "value": 80},
                            {"color": "green", "value": 90}
                        ]
                    },
                    "unit": "percent",
                    "min": 0,
                    "max": 100
                }
            }
        }

    def _create_quality_checks_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """质量检查面板"""
        return {
            "id": 13,
            "title": "Quality Checks",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "rate(perfect21_quality_checks_total[5m])",
                    "legendFormat": "{{check_type}} - {{status}}",
                    "refId": "A"
                }
            ]
        }

    def _create_sync_point_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """同步点面板"""
        return {
            "id": 14,
            "title": "Sync Point Validations",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "rate(perfect21_sync_point_validations_total[5m])",
                    "legendFormat": "{{sync_point_type}} - {{status}}",
                    "refId": "A"
                }
            ]
        }

    def _create_error_trends_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """错误趋势面板"""
        return {
            "id": 15,
            "title": "Error Trends",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "increase(perfect21_errors_total[1h])",
                    "legendFormat": "{{error_type}}",
                    "refId": "A"
                }
            ]
        }

    def _create_test_results_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """测试结果面板"""
        return {
            "id": 16,
            "title": "Test Results Summary",
            "type": "stat",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "perfect21_quality_checks_total{check_type='test', status='passed'}",
                    "legendFormat": "Tests Passed",
                    "refId": "A"
                },
                {
                    "expr": "perfect21_quality_checks_total{check_type='test', status='failed'}",
                    "legendFormat": "Tests Failed",
                    "refId": "B"
                }
            ]
        }

    def _create_cpu_memory_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """CPU内存面板"""
        return {
            "id": 17,
            "title": "CPU & Memory",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "perfect21_system_cpu_usage_percent",
                    "legendFormat": "CPU Usage %",
                    "refId": "A"
                },
                {
                    "expr": "perfect21_system_memory_usage_bytes{type='used'} / perfect21_system_memory_usage_bytes{type='total'} * 100",
                    "legendFormat": "Memory Usage %",
                    "refId": "B"
                }
            ]
        }

    def _create_disk_network_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """磁盘网络面板"""
        return {
            "id": 18,
            "title": "Disk & Network",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "perfect21_system_disk_usage_bytes{type='used'} / perfect21_system_disk_usage_bytes{type='total'} * 100",
                    "legendFormat": "Disk Usage %",
                    "refId": "A"
                }
            ]
        }

    def _create_service_status_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """服务状态面板"""
        return {
            "id": 19,
            "title": "Service Status",
            "type": "stat",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "up",
                    "legendFormat": "{{job}}",
                    "refId": "A"
                }
            ]
        }

    def _create_cache_metrics_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """缓存指标面板"""
        return {
            "id": 20,
            "title": "Cache Metrics",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "rate(perfect21_cache_operations_total{status='hit'}[5m]) / rate(perfect21_cache_operations_total[5m]) * 100",
                    "legendFormat": "Cache Hit Rate %",
                    "refId": "A"
                },
                {
                    "expr": "perfect21_cache_size_bytes",
                    "legendFormat": "Cache Size - {{cache_type}}",
                    "refId": "B"
                }
            ]
        }

    def _create_database_panel(self, x: int, y: int, w: int, h: int) -> Dict[str, Any]:
        """数据库面板"""
        return {
            "id": 21,
            "title": "Database Metrics",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [
                {
                    "expr": "rate(perfect21_database_operations_total[5m])",
                    "legendFormat": "{{operation}}",
                    "refId": "A"
                }
            ]
        }

class CustomDashboardConfig:
    """自定义仪表板配置"""

    @staticmethod
    def create_sla_dashboard() -> Dict[str, Any]:
        """创建SLA监控仪表板"""
        return {
            "title": "Perfect21 SLA Dashboard",
            "description": "Service Level Agreement Monitoring",
            "uid": "perfect21-sla",
            "panels": [
                {
                    "title": "SLA Compliance",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "(1 - rate(perfect21_api_requests_total{status_code=~'5..'}[30d])) * 100",
                            "legendFormat": "Availability %"
                        }
                    ],
                    "thresholds": [
                        {"color": "red", "value": 0},
                        {"color": "yellow", "value": 99},
                        {"color": "green", "value": 99.9}
                    ]
                }
            ]
        }

    @staticmethod
    def create_business_metrics_dashboard() -> Dict[str, Any]:
        """创建业务指标仪表板"""
        return {
            "title": "Perfect21 Business Metrics",
            "description": "Business KPIs and Metrics",
            "uid": "perfect21-business",
            "panels": [
                {
                    "title": "Active Users",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "perfect21_active_users",
                            "legendFormat": "Active Users"
                        }
                    ]
                },
                {
                    "title": "Workspace Utilization",
                    "type": "pie",
                    "targets": [
                        {
                            "expr": "perfect21_workspace_count",
                            "legendFormat": "Workspaces"
                        }
                    ]
                }
            ]
        }

def generate_all_dashboards() -> Dict[str, Dict[str, Any]]:
    """生成所有仪表板配置"""
    generator = GrafanaDashboardGenerator()

    dashboards = {
        "overview": generator.create_overview_dashboard(),
        "agents": generator.create_agent_performance_dashboard(),
        "quality": generator.create_quality_dashboard(),
        "infrastructure": generator.create_infrastructure_dashboard(),
        "sla": CustomDashboardConfig.create_sla_dashboard(),
        "business": CustomDashboardConfig.create_business_metrics_dashboard()
    }

    return dashboards

def save_dashboard_configs(output_dir: str = "monitoring/dashboards"):
    """保存仪表板配置到文件"""
    import os
    os.makedirs(output_dir, exist_ok=True)

    dashboards = generate_all_dashboards()

    for name, config in dashboards.items():
        file_path = os.path.join(output_dir, f"{name}-dashboard.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"Saved dashboard: {file_path}")

def create_monitoring_config() -> Dict[str, Any]:
    """创建完整的监控配置"""
    return {
        "grafana": {
            "version": "8.0.0",
            "dashboards": generate_all_dashboards(),
            "datasources": [
                {
                    "name": "Prometheus",
                    "type": "prometheus",
                    "url": "http://prometheus:9090",
                    "access": "proxy",
                    "isDefault": True
                }
            ]
        },
        "alerting": {
            "notification_channels": [
                {
                    "name": "slack-alerts",
                    "type": "slack",
                    "settings": {
                        "url": "${SLACK_WEBHOOK_URL}",
                        "channel": "#perfect21-alerts",
                        "username": "Perfect21 Monitor"
                    }
                }
            ]
        },
        "recording_rules": [
            {
                "name": "perfect21:api_success_rate",
                "expr": "rate(perfect21_api_requests_total{status_code!~'5..'}[5m]) / rate(perfect21_api_requests_total[5m])"
            },
            {
                "name": "perfect21:agent_success_rate",
                "expr": "rate(perfect21_agent_executions_total{status='success'}[5m]) / rate(perfect21_agent_executions_total[5m])"
            }
        ]
    }

if __name__ == "__main__":
    # 生成并保存仪表板配置
    save_dashboard_configs()
    print("All dashboard configurations generated successfully!")