#!/usr/bin/env python3
"""
Perfect21 Opus41 实时监控和可视化系统
提供实时Dashboard、性能图表、质量追踪等功能
"""

import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import os
import sys

# 添加路径以支持导入
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from modules.logger import log_info, log_error

@dataclass
class VisualizationMetrics:
    """可视化指标"""
    timestamp: datetime
    quality_score: float
    success_rate: float
    execution_time: float
    active_agents: int
    layer_progress: Dict[int, float]
    agent_status: Dict[str, str]
    refinement_progress: float = 0.0

class Opus41Visualizer:
    """Opus41实时可视化系统"""

    def __init__(self):
        self.metrics_history: List[VisualizationMetrics] = []
        self.current_metrics: Optional[VisualizationMetrics] = None
        self.dashboard_active = False
        self.update_thread: Optional[threading.Thread] = None
        self.dashboard_data = {}

    def start_real_time_monitoring(self, plan_config: Dict[str, Any]):
        """启动实时监控"""
        log_info("启动Opus41实时监控系统")

        self.dashboard_active = True
        self.dashboard_data = {
            "plan": plan_config,
            "start_time": datetime.now().isoformat(),
            "status": "active",
            "metrics": [],
            "layers": {},
            "agents": {},
            "quality_progression": []
        }

        # 启动更新线程
        self.update_thread = threading.Thread(target=self._update_dashboard_loop)
        self.update_thread.daemon = True
        self.update_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        self.dashboard_active = False
        if self.update_thread:
            self.update_thread.join(timeout=1)
        log_info("Opus41监控系统已停止")

    def update_metrics(self,
                      quality_score: float,
                      success_rate: float,
                      execution_time: float,
                      active_agents: int,
                      layer_progress: Dict[int, float],
                      agent_status: Dict[str, str],
                      refinement_progress: float = 0.0):
        """更新指标"""
        metrics = VisualizationMetrics(
            timestamp=datetime.now(),
            quality_score=quality_score,
            success_rate=success_rate,
            execution_time=execution_time,
            active_agents=active_agents,
            layer_progress=layer_progress,
            agent_status=agent_status,
            refinement_progress=refinement_progress
        )

        self.current_metrics = metrics
        self.metrics_history.append(metrics)

        # 更新dashboard数据
        self._update_dashboard_data(metrics)

    def _update_dashboard_loop(self):
        """Dashboard更新循环"""
        while self.dashboard_active:
            if self.current_metrics:
                self._generate_console_dashboard()
            time.sleep(2)  # 每2秒更新一次

    def _update_dashboard_data(self, metrics: VisualizationMetrics):
        """更新dashboard数据"""
        self.dashboard_data["metrics"].append({
            "timestamp": metrics.timestamp.isoformat(),
            "quality_score": metrics.quality_score,
            "success_rate": metrics.success_rate,
            "execution_time": metrics.execution_time,
            "active_agents": metrics.active_agents,
            "refinement_progress": metrics.refinement_progress
        })

        # 更新层进度
        for layer_id, progress in metrics.layer_progress.items():
            self.dashboard_data["layers"][f"layer_{layer_id}"] = {
                "progress": progress,
                "updated": metrics.timestamp.isoformat()
            }

        # 更新agent状态
        for agent, status in metrics.agent_status.items():
            self.dashboard_data["agents"][agent] = {
                "status": status,
                "updated": metrics.timestamp.isoformat()
            }

        # 更新质量进展
        self.dashboard_data["quality_progression"].append({
            "timestamp": metrics.timestamp.isoformat(),
            "score": metrics.quality_score
        })

    def _generate_console_dashboard(self):
        """生成控制台dashboard"""
        if not self.current_metrics:
            return

        # 清屏
        os.system('clear' if os.name == 'posix' else 'cls')

        metrics = self.current_metrics

        print("🚀 Opus41 实时监控 Dashboard")
        print("=" * 80)
        print(f"⏰ 时间: {metrics.timestamp.strftime('%H:%M:%S')}")
        print(f"🎯 质量分数: {metrics.quality_score:.1%} {'🟢' if metrics.quality_score >= 0.8 else '🟡' if metrics.quality_score >= 0.6 else '🔴'}")
        print(f"✅ 成功率: {metrics.success_rate:.1%}")
        print(f"⚡ 执行时间: {metrics.execution_time:.1f}s")
        print(f"🤖 活跃Agents: {metrics.active_agents}")

        if metrics.refinement_progress > 0:
            print(f"🔧 改进进度: {metrics.refinement_progress:.1%}")

        print("\n📊 层执行进度:")
        for layer_id, progress in metrics.layer_progress.items():
            bar = self._create_progress_bar(progress, 30)
            print(f"  第{layer_id}层: {bar} {progress:.1%}")

        print("\n👥 Agent状态:")
        status_counts = {"running": 0, "completed": 0, "failed": 0, "pending": 0}
        for agent, status in metrics.agent_status.items():
            status_counts[status] = status_counts.get(status, 0) + 1

        print(f"  🟢 运行中: {status_counts.get('running', 0)}")
        print(f"  ✅ 已完成: {status_counts.get('completed', 0)}")
        print(f"  ❌ 失败: {status_counts.get('failed', 0)}")
        print(f"  ⏳ 等待中: {status_counts.get('pending', 0)}")

        # 显示最近的质量趋势
        if len(self.metrics_history) >= 3:
            recent_scores = [m.quality_score for m in self.metrics_history[-3:]]
            trend = "📈" if recent_scores[-1] > recent_scores[0] else "📉" if recent_scores[-1] < recent_scores[0] else "➡️"
            print(f"\n📈 质量趋势: {trend} {recent_scores[0]:.1%} → {recent_scores[-1]:.1%}")

        print("=" * 80)

    def _create_progress_bar(self, progress: float, width: int = 20) -> str:
        """创建进度条"""
        filled = int(progress * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"

    def generate_html_dashboard(self, output_file: str = "opus41_dashboard.html"):
        """生成HTML Dashboard"""
        html_content = self._create_html_dashboard()

        output_path = os.path.join(os.getcwd(), output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        log_info(f"HTML Dashboard已生成: {output_path}")
        return output_path

    def _create_html_dashboard(self) -> str:
        """创建HTML Dashboard内容"""
        dashboard_json = json.dumps(self.dashboard_data, indent=2, default=str)

        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Opus41 实时监控 Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: #ffffff;
        }}

        .dashboard-header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: #2d2d2d;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}

        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}

        .metric-label {{
            color: #cccccc;
            margin-top: 5px;
        }}

        .chart-container {{
            background: #2d2d2d;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}

        .layer-progress {{
            background: #2d2d2d;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}

        .progress-bar {{
            background: #444;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }}

        .agent-status {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            background: #2d2d2d;
            padding: 20px;
            border-radius: 10px;
        }}

        .agent-item {{
            background: #3d3d3d;
            padding: 10px;
            border-radius: 5px;
            font-size: 0.9em;
        }}

        .status-running {{ border-left: 3px solid #4CAF50; }}
        .status-completed {{ border-left: 3px solid #2196F3; }}
        .status-failed {{ border-left: 3px solid #f44336; }}
        .status-pending {{ border-left: 3px solid #FF9800; }}

        .refresh-info {{
            text-align: center;
            color: #888;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <h1>🚀 Opus41 智能优化执行监控</h1>
        <p id="current-time"></p>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value" id="quality-score">--</div>
            <div class="metric-label">质量分数</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="success-rate">--</div>
            <div class="metric-label">成功率</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="execution-time">--</div>
            <div class="metric-label">执行时间 (秒)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="active-agents">--</div>
            <div class="metric-label">活跃 Agents</div>
        </div>
    </div>

    <div class="chart-container">
        <h3>质量分数趋势</h3>
        <canvas id="qualityChart" width="400" height="200"></canvas>
    </div>

    <div class="layer-progress">
        <h3>层执行进度</h3>
        <div id="layer-progress-container">
            <!-- 动态生成 -->
        </div>
    </div>

    <div class="agent-status">
        <h3 style="grid-column: 1 / -1;">Agent 状态</h3>
        <div id="agent-status-container">
            <!-- 动态生成 -->
        </div>
    </div>

    <div class="refresh-info">
        <p>Dashboard 每 5 秒自动刷新 | 最后更新: <span id="last-update"></span></p>
    </div>

    <script>
        // Dashboard 数据
        let dashboardData = {dashboard_json};

        // 初始化图表
        const ctx = document.getElementById('qualityChart').getContext('2d');
        const qualityChart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: [],
                datasets: [{{
                    label: '质量分数',
                    data: [],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        labels: {{
                            color: '#ffffff'
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{
                            color: '#cccccc'
                        }}
                    }},
                    y: {{
                        ticks: {{
                            color: '#cccccc'
                        }},
                        min: 0,
                        max: 1
                    }}
                }}
            }}
        }});

        function updateDashboard() {{
            const latest = dashboardData.metrics[dashboardData.metrics.length - 1];
            if (!latest) return;

            // 更新指标卡片
            document.getElementById('quality-score').textContent = (latest.quality_score * 100).toFixed(1) + '%';
            document.getElementById('success-rate').textContent = (latest.success_rate * 100).toFixed(1) + '%';
            document.getElementById('execution-time').textContent = latest.execution_time.toFixed(1);
            document.getElementById('active-agents').textContent = latest.active_agents;

            // 更新质量图表
            if (dashboardData.quality_progression.length > 0) {{
                const labels = dashboardData.quality_progression.map(item =>
                    new Date(item.timestamp).toLocaleTimeString()
                );
                const data = dashboardData.quality_progression.map(item => item.score);

                qualityChart.data.labels = labels.slice(-20); // 最近20个点
                qualityChart.data.datasets[0].data = data.slice(-20);
                qualityChart.update();
            }}

            // 更新层进度
            updateLayerProgress();

            // 更新Agent状态
            updateAgentStatus();

            // 更新时间
            document.getElementById('current-time').textContent = new Date().toLocaleString();
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }}

        function updateLayerProgress() {{
            const container = document.getElementById('layer-progress-container');
            container.innerHTML = '';

            Object.entries(dashboardData.layers).forEach(([layerId, data]) => {{
                const layerDiv = document.createElement('div');
                layerDiv.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                        <span>${{layerId.replace('layer_', '第')}}层</span>
                        <span>${{(data.progress * 100).toFixed(1)}}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${{data.progress * 100}}%"></div>
                    </div>
                `;
                container.appendChild(layerDiv);
            }});
        }}

        function updateAgentStatus() {{
            const container = document.getElementById('agent-status-container');
            container.innerHTML = '';

            Object.entries(dashboardData.agents).forEach(([agent, data]) => {{
                const agentDiv = document.createElement('div');
                agentDiv.className = `agent-item status-${{data.status}}`;
                agentDiv.innerHTML = `
                    <strong>${{agent}}</strong><br>
                    <small>状态: ${{data.status}}</small>
                `;
                container.appendChild(agentDiv);
            }});
        }}

        // 初始化并设置自动刷新
        updateDashboard();
        setInterval(updateDashboard, 5000); // 每5秒刷新

        // 模拟数据更新（实际应用中通过WebSocket或API更新）
        function simulateDataUpdate() {{
            // 这里可以添加从服务器获取最新数据的逻辑
        }}
    </script>
</body>
</html>
"""
        return html_content

    def generate_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        if not self.metrics_history:
            return {"error": "No metrics data available"}

        # 计算统计指标
        quality_scores = [m.quality_score for m in self.metrics_history]
        success_rates = [m.success_rate for m in self.metrics_history]
        execution_times = [m.execution_time for m in self.metrics_history]

        report = {
            "summary": {
                "total_measurements": len(self.metrics_history),
                "time_span": {
                    "start": self.metrics_history[0].timestamp.isoformat(),
                    "end": self.metrics_history[-1].timestamp.isoformat()
                }
            },
            "quality_metrics": {
                "avg_quality_score": sum(quality_scores) / len(quality_scores),
                "max_quality_score": max(quality_scores),
                "min_quality_score": min(quality_scores),
                "final_quality_score": quality_scores[-1],
                "quality_improvement": quality_scores[-1] - quality_scores[0] if len(quality_scores) > 1 else 0
            },
            "performance_metrics": {
                "avg_success_rate": sum(success_rates) / len(success_rates),
                "avg_execution_time": sum(execution_times) / len(execution_times),
                "max_execution_time": max(execution_times),
                "min_execution_time": min(execution_times)
            },
            "trends": {
                "quality_trend": "improving" if quality_scores[-1] > quality_scores[0] else "declining" if quality_scores[-1] < quality_scores[0] else "stable",
                "performance_trend": "improving" if execution_times[-1] < execution_times[0] else "declining" if execution_times[-1] > execution_times[0] else "stable"
            },
            "recommendations": self._generate_performance_recommendations(quality_scores, success_rates, execution_times)
        }

        return report

    def _generate_performance_recommendations(self, quality_scores: List[float],
                                           success_rates: List[float],
                                           execution_times: List[float]) -> List[str]:
        """生成性能建议"""
        recommendations = []

        avg_quality = sum(quality_scores) / len(quality_scores)
        avg_success = sum(success_rates) / len(success_rates)
        avg_time = sum(execution_times) / len(execution_times)

        if avg_quality < 0.8:
            recommendations.append("质量分数偏低，建议增加代码审查和测试覆盖率")

        if avg_success < 0.85:
            recommendations.append("成功率有待提高，建议优化Agent选择和任务分配")

        if avg_time > 300:  # 5分钟
            recommendations.append("执行时间较长，建议优化并行策略和资源配置")

        if len(quality_scores) > 1:
            if quality_scores[-1] < quality_scores[0]:
                recommendations.append("质量呈下降趋势，建议增加质量门控制")

        if not recommendations:
            recommendations.append("系统运行良好，继续保持当前配置")

        return recommendations

    def export_metrics_to_json(self, filename: str = None) -> str:
        """导出指标数据到JSON文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"opus41_metrics_{timestamp}.json"

        export_data = {
            "export_time": datetime.now().isoformat(),
            "metrics_count": len(self.metrics_history),
            "dashboard_data": self.dashboard_data,
            "metrics_history": [asdict(m) for m in self.metrics_history],
            "performance_report": self.generate_performance_report()
        }

        # 处理datetime序列化
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        file_path = os.path.join(os.getcwd(), filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=json_serializer, ensure_ascii=False)

        log_info(f"指标数据已导出到: {file_path}")
        return file_path

    def create_progress_visualization(self) -> str:
        """创建进度可视化字符图"""
        if not self.current_metrics:
            return "No metrics available"

        viz = []
        viz.append("🚀 Opus41 执行进度可视化")
        viz.append("=" * 50)

        # 整体质量进度
        quality_bar = self._create_progress_bar(self.current_metrics.quality_score, 40)
        viz.append(f"📊 整体质量: {quality_bar} {self.current_metrics.quality_score:.1%}")

        # 成功率
        success_bar = self._create_progress_bar(self.current_metrics.success_rate, 40)
        viz.append(f"✅ 成功率:   {success_bar} {self.current_metrics.success_rate:.1%}")

        # 层进度
        if self.current_metrics.layer_progress:
            viz.append("\n📈 层执行进度:")
            for layer_id, progress in self.current_metrics.layer_progress.items():
                layer_bar = self._create_progress_bar(progress, 30)
                viz.append(f"  第{layer_id}层: {layer_bar} {progress:.1%}")

        # Agent状态统计
        if self.current_metrics.agent_status:
            status_counts = {}
            for status in self.current_metrics.agent_status.values():
                status_counts[status] = status_counts.get(status, 0) + 1

            viz.append("\n👥 Agent状态分布:")
            total = sum(status_counts.values())
            for status, count in status_counts.items():
                percentage = count / total if total > 0 else 0
                status_bar = self._create_progress_bar(percentage, 20)
                viz.append(f"  {status:10}: {status_bar} {count:2d} ({percentage:.1%})")

        viz.append("=" * 50)
        return "\n".join(viz)

# 全局可视化实例
_opus41_visualizer = None

def get_opus41_visualizer() -> Opus41Visualizer:
    """获取Opus41可视化器实例"""
    global _opus41_visualizer
    if _opus41_visualizer is None:
        _opus41_visualizer = Opus41Visualizer()
    return _opus41_visualizer