#!/usr/bin/env python3
"""
Perfect21 执行可视化系统
提供多Agent工作流执行的实时可视化界面
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import threading
from collections import defaultdict

logger = logging.getLogger("ExecutionVisualizer")

class ConsoleVisualizer:
    """控制台可视化器"""

    def __init__(self, monitor, refresh_interval: float = 1.0):
        """
        初始化控制台可视化器

        Args:
            monitor: ExecutionMonitor实例
            refresh_interval: 刷新间隔（秒）
        """
        self.monitor = monitor
        self.refresh_interval = refresh_interval
        self.is_displaying = False
        self.display_thread = None

        # 订阅监控事件
        self.monitor.subscribe(self._on_monitor_event)

        logger.info("控制台可视化器初始化完成")

    def start_display(self):
        """开始显示实时监控界面"""
        if not self.is_displaying:
            self.is_displaying = True
            self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
            self.display_thread.start()
            logger.info("控制台可视化已启动")

    def stop_display(self):
        """停止显示"""
        self.is_displaying = False
        if self.display_thread:
            self.display_thread.join(timeout=2.0)
        logger.info("控制台可视化已停止")

    def _display_loop(self):
        """显示循环"""
        while self.is_displaying:
            try:
                self._clear_screen()
                self._display_dashboard()
                time.sleep(self.refresh_interval)
            except Exception as e:
                logger.error(f"显示界面时发生错误: {e}")
                time.sleep(1.0)

    def _clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _display_dashboard(self):
        """显示仪表板"""
        print("=" * 80)
        print("🚀 Perfect21 多Agent工作流监控仪表板")
        print("=" * 80)

        # 显示系统状态
        self._display_system_status()

        # 显示活跃工作流
        self._display_active_workflows()

        # 显示Agent状态
        self._display_agent_status()

        # 显示最近事件
        self._display_recent_events()

        # 显示资源使用
        self._display_resource_usage()

        print("=" * 80)
        print("🔄 实时更新中... (按Ctrl+C停止监控)")

    def _display_system_status(self):
        """显示系统状态"""
        stats = self.monitor.get_statistics()

        print(f"\n📊 系统状态")
        print(f"├─ 监控状态: {'🟢 运行中' if stats['monitoring_status'] == 'active' else '🔴 已停止'}")
        print(f"├─ 活跃工作流: {stats['active_workflows']}个")
        print(f"├─ 已完成工作流: {stats['completed_workflows']}个")
        print(f"├─ 已执行任务: {stats['total_tasks_executed']}个")
        print(f"├─ 总执行时间: {stats['total_execution_time']:.1f}秒")
        print(f"└─ 平均工作流时长: {stats['average_workflow_duration']:.1f}秒")

    def _display_active_workflows(self):
        """显示活跃工作流"""
        active_workflows = self.monitor.get_active_workflows()

        print(f"\n🔄 活跃工作流 ({len(active_workflows)}个)")

        if not active_workflows:
            print("└─ 暂无活跃工作流")
            return

        for i, workflow in enumerate(active_workflows):
            is_last = i == len(active_workflows) - 1
            prefix = "└─" if is_last else "├─"

            progress = workflow['progress']
            progress_bar = self._create_progress_bar(progress['percentage'], 20)
            status_icon = self._get_workflow_status_icon(workflow['status'])

            print(f"{prefix} {status_icon} {workflow['workflow_id']}")
            print(f"{'   ' if is_last else '│  '} ├─ 进度: {progress_bar} {progress['percentage']:.1f}%")
            print(f"{'   ' if is_last else '│  '} ├─ 任务: {progress['completed']}/{progress['total']} "
                  f"(运行:{progress['running']}, 失败:{progress['failed']})")

            if workflow['duration'] > 0:
                print(f"{'   ' if is_last else '│  '} └─ 用时: {workflow['duration']:.1f}秒")
            else:
                elapsed = (datetime.now() - datetime.fromisoformat(workflow['start_time'])).total_seconds()
                print(f"{'   ' if is_last else '│  '} └─ 已运行: {elapsed:.1f}秒")

    def _display_agent_status(self):
        """显示Agent状态"""
        agent_status = self.monitor.get_agent_status()

        print(f"\n🤖 Agent状态 ({len(agent_status)}个)")

        if not agent_status:
            print("└─ 暂无Agent活动")
            return

        # 按状态分组
        status_groups = defaultdict(list)
        for agent, status in agent_status.items():
            status_groups[status].append(agent)

        for i, (status, agents) in enumerate(status_groups.items()):
            is_last = i == len(status_groups) - 1
            prefix = "└─" if is_last else "├─"

            status_icon = self._get_agent_status_icon(status)
            print(f"{prefix} {status_icon} {status}: {len(agents)}个")

            for j, agent in enumerate(agents[:5]):  # 最多显示5个
                agent_prefix = "   └─" if is_last else "│  └─"
                if j == 4 and len(agents) > 5:
                    print(f"{agent_prefix} ... 还有{len(agents) - 5}个")
                    break
                print(f"{agent_prefix} {agent}")

    def _display_recent_events(self):
        """显示最近事件"""
        events = self.monitor.get_recent_events(limit=10)

        print(f"\n📝 最近事件 (最新{len(events)}条)")

        if not events:
            print("└─ 暂无事件")
            return

        for i, event in enumerate(events):
            is_last = i == len(events) - 1
            prefix = "└─" if is_last else "├─"

            event_icon = self._get_event_icon(event['event_type'])
            timestamp = datetime.fromisoformat(event['timestamp']).strftime("%H:%M:%S")

            message = event['message'] or event['event_type']
            if len(message) > 50:
                message = message[:47] + "..."

            print(f"{prefix} {event_icon} [{timestamp}] {message}")

            # 显示任务和Agent信息
            if event['task_id'] or event['agent_name']:
                detail_prefix = "   " if is_last else "│  "
                details = []
                if event['task_id']:
                    details.append(f"任务:{event['task_id']}")
                if event['agent_name']:
                    details.append(f"Agent:{event['agent_name']}")
                if event['duration'] > 0:
                    details.append(f"耗时:{event['duration']:.1f}s")

                if details:
                    print(f"{detail_prefix}└─ {' | '.join(details)}")

    def _display_resource_usage(self):
        """显示资源使用"""
        resources = self.monitor.get_resource_usage()

        print(f"\n💻 资源使用")

        for i, (resource, usage) in enumerate(resources.items()):
            is_last = i == len(resources) - 1
            prefix = "└─" if is_last else "├─"

            usage_bar = self._create_usage_bar(usage, 15)
            usage_color = self._get_usage_color(usage)

            print(f"{prefix} {resource.upper()}: {usage_bar} {usage:.1f}%")

    def _create_progress_bar(self, percentage: float, length: int = 20) -> str:
        """创建进度条"""
        filled = int(percentage / 100 * length)
        empty = length - filled

        bar = "█" * filled + "░" * empty

        if percentage == 100:
            return f"🟢 {bar}"
        elif percentage >= 70:
            return f"🟡 {bar}"
        else:
            return f"🔵 {bar}"

    def _create_usage_bar(self, usage: float, length: int = 15) -> str:
        """创建使用率条形图"""
        filled = int(usage / 100 * length)
        empty = length - filled

        if usage >= 90:
            return f"🔴 {'█' * filled}{'░' * empty}"
        elif usage >= 70:
            return f"🟡 {'█' * filled}{'░' * empty}"
        else:
            return f"🟢 {'█' * filled}{'░' * empty}"

    def _get_workflow_status_icon(self, status: str) -> str:
        """获取工作流状态图标"""
        icons = {
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "⏹️"
        }
        return icons.get(status, "❓")

    def _get_agent_status_icon(self, status: str) -> str:
        """获取Agent状态图标"""
        icons = {
            "busy": "🔄",
            "idle": "💤",
            "error": "❌",
            "running": "⚡",
            "stopped": "⏹️"
        }
        return icons.get(status, "❓")

    def _get_event_icon(self, event_type: str) -> str:
        """获取事件图标"""
        icons = {
            "workflow_started": "🚀",
            "workflow_completed": "✅",
            "workflow_failed": "❌",
            "task_started": "▶️",
            "task_completed": "✅",
            "task_failed": "❌",
            "agent_status_change": "🔄",
            "resource_update": "📊",
            "error_occurred": "⚠️"
        }
        return icons.get(event_type, "📝")

    def _get_usage_color(self, usage: float) -> str:
        """获取使用率颜色"""
        if usage >= 90:
            return "red"
        elif usage >= 70:
            return "yellow"
        else:
            return "green"

    def _on_monitor_event(self, event):
        """处理监控事件"""
        # 这里可以添加特殊事件的处理逻辑
        # 例如高优先级事件的特殊显示
        pass

    def display_workflow_summary(self, workflow_id: str):
        """显示工作流摘要"""
        status = self.monitor.get_workflow_status(workflow_id)
        if not status:
            print(f"❌ 未找到工作流: {workflow_id}")
            return

        print(f"\n📊 工作流摘要: {workflow_id}")
        print("=" * 60)

        # 基本信息
        print(f"状态: {self._get_workflow_status_icon(status['status'])} {status['status']}")
        print(f"开始时间: {status['start_time']}")
        if status['end_time']:
            print(f"结束时间: {status['end_time']}")
        print(f"总耗时: {status['duration']:.1f}秒")

        # 进度信息
        progress = status['progress']
        progress_bar = self._create_progress_bar(progress['percentage'], 30)
        print(f"进度: {progress_bar} {progress['percentage']:.1f}%")
        print(f"任务统计: 总计{progress['total']} | 完成{progress['completed']} | "
              f"失败{progress['failed']} | 运行中{progress['running']}")

        # 性能指标
        metrics = status['metrics']
        print(f"\n性能指标:")
        print(f"├─ 成功率: {metrics['success_rate']:.1%}")
        print(f"├─ 平均任务时长: {metrics['average_task_duration']:.1f}秒")
        print(f"└─ 并行效率: {metrics['parallel_efficiency']:.1%}")

        # 任务详情
        if status['tasks']:
            print(f"\n任务详情:")
            for i, task in enumerate(status['tasks']):
                is_last = i == len(status['tasks']) - 1
                prefix = "└─" if is_last else "├─"

                status_icon = "✅" if task['status'] == 'completed' else \
                             "❌" if task['status'] == 'failed' else "🔄"

                print(f"{prefix} {status_icon} {task['task_id']}")
                detail_prefix = "   " if is_last else "│  "
                print(f"{detail_prefix}├─ Agent: {task['agent']}")
                print(f"{detail_prefix}├─ 状态: {task['status']}")
                if task['duration'] > 0:
                    print(f"{detail_prefix}├─ 耗时: {task['duration']:.1f}秒")
                if task['error']:
                    print(f"{detail_prefix}└─ 错误: {task['error']}")
                else:
                    print(f"{detail_prefix}└─ 进度: {task['progress']}%")

class WebVisualizer:
    """Web可视化器（简化版）"""

    def __init__(self, monitor, port: int = 8080):
        """
        初始化Web可视化器

        Args:
            monitor: ExecutionMonitor实例
            port: Web服务端口
        """
        self.monitor = monitor
        self.port = port
        self.is_serving = False

        logger.info(f"Web可视化器初始化完成，端口: {port}")

    def generate_html_dashboard(self) -> str:
        """生成HTML仪表板"""
        stats = self.monitor.get_statistics()
        active_workflows = self.monitor.get_active_workflows()
        agent_status = self.monitor.get_agent_status()
        recent_events = self.monitor.get_recent_events(limit=20)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Perfect21 执行监控仪表板</title>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="5">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .dashboard {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .stat-title {{
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .section {{
            background: white;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .section-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-radius: 10px 10px 0 0;
            border-bottom: 1px solid #eee;
            font-weight: bold;
        }}
        .section-content {{
            padding: 20px;
        }}
        .workflow-item {{
            border-left: 4px solid #007bff;
            padding: 15px;
            margin-bottom: 15px;
            background: #f8f9fa;
            border-radius: 0 5px 5px 0;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }}
        .agent-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
        }}
        .agent-item {{
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-size: 12px;
        }}
        .agent-busy {{ background: #fff3cd; border: 1px solid #ffeaa7; }}
        .agent-idle {{ background: #d4edda; border: 1px solid #c3e6cb; }}
        .agent-error {{ background: #f8d7da; border: 1px solid #f1aeb5; }}
        .event-item {{
            padding: 10px 15px;
            border-bottom: 1px solid #eee;
            display: flex;
            align-items: center;
        }}
        .event-time {{
            color: #666;
            font-size: 12px;
            margin-right: 15px;
            min-width: 60px;
        }}
        .status-running {{ color: #007bff; }}
        .status-completed {{ color: #28a745; }}
        .status-failed {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🚀 Perfect21 多Agent工作流监控仪表板</h1>
            <p>实时监控 • 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">监控状态</div>
                <div class="stat-value">{'🟢 运行中' if stats['monitoring_status'] == 'active' else '🔴 已停止'}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">活跃工作流</div>
                <div class="stat-value">{stats['active_workflows']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">已完成工作流</div>
                <div class="stat-value">{stats['completed_workflows']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">总执行任务</div>
                <div class="stat-value">{stats['total_tasks_executed']}</div>
            </div>
        </div>
"""

        # 活跃工作流
        if active_workflows:
            html += """
        <div class="section">
            <div class="section-header">🔄 活跃工作流</div>
            <div class="section-content">
"""
            for workflow in active_workflows:
                progress = workflow['progress']
                html += f"""
                <div class="workflow-item">
                    <h4>{workflow['workflow_id']}</h4>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {progress['percentage']}%"></div>
                    </div>
                    <p>进度: {progress['completed']}/{progress['total']} 任务 ({progress['percentage']:.1f}%)</p>
                    <small>运行中: {progress['running']} | 失败: {progress['failed']}</small>
                </div>
"""
            html += """
            </div>
        </div>
"""

        # Agent状态
        if agent_status:
            html += """
        <div class="section">
            <div class="section-header">🤖 Agent状态</div>
            <div class="section-content">
                <div class="agent-grid">
"""
            for agent, status in agent_status.items():
                status_class = f"agent-{status}" if status in ['busy', 'idle', 'error'] else 'agent-idle'
                html += f"""
                    <div class="agent-item {status_class}">
                        <strong>{agent}</strong><br>
                        {status}
                    </div>
"""
            html += """
                </div>
            </div>
        </div>
"""

        # 最近事件
        if recent_events:
            html += """
        <div class="section">
            <div class="section-header">📝 最近事件</div>
            <div class="section-content">
"""
            for event in recent_events[:10]:
                timestamp = datetime.fromisoformat(event['timestamp']).strftime('%H:%M:%S')
                html += f"""
                <div class="event-item">
                    <div class="event-time">{timestamp}</div>
                    <div>
                        <strong>{event['event_type']}</strong>
                        {f" | {event['message']}" if event['message'] else ""}
                        {f" | Agent: {event['agent_name']}" if event['agent_name'] else ""}
                        {f" | 耗时: {event['duration']:.1f}s" if event['duration'] > 0 else ""}
                    </div>
                </div>
"""
            html += """
            </div>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""
        return html

    def save_dashboard_html(self, filename: str = "dashboard.html") -> str:
        """保存仪表板HTML文件"""
        html_content = self.generate_html_dashboard()

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"仪表板已保存到: {filename}")
            return filename
        except Exception as e:
            logger.error(f"保存HTML文件失败: {e}")
            return ""

# 可视化管理器
class VisualizationManager:
    """可视化管理器"""

    def __init__(self, monitor):
        self.monitor = monitor
        self.console_visualizer = ConsoleVisualizer(monitor)
        self.web_visualizer = WebVisualizer(monitor)

        logger.info("可视化管理器初始化完成")

    def start_console_display(self):
        """启动控制台显示"""
        self.console_visualizer.start_display()

    def stop_console_display(self):
        """停止控制台显示"""
        self.console_visualizer.stop_display()

    def display_workflow_summary(self, workflow_id: str):
        """显示工作流摘要"""
        self.console_visualizer.display_workflow_summary(workflow_id)

    def generate_html_report(self, filename: str = None) -> str:
        """生成HTML报告"""
        if not filename:
            filename = f"perfect21_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        return self.web_visualizer.save_dashboard_html(filename)

# 全局可视化管理器
_visualization_manager = None

def get_visualization_manager(monitor=None) -> VisualizationManager:
    """获取可视化管理器"""
    global _visualization_manager
    if _visualization_manager is None:
        if monitor is None:
            from .monitor import get_execution_monitor
            monitor = get_execution_monitor()
        _visualization_manager = VisualizationManager(monitor)
    return _visualization_manager