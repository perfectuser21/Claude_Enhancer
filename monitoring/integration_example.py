#!/usr/bin/env python3
"""
Monitoring Integration Example - Perfect21
展示如何集成完整的监控系统到Perfect21应用中
"""

import asyncio
import time
from typing import Dict, Any
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

# 导入Perfect21监控系统
from monitoring import (
    start_monitoring_system,
    stop_monitoring_system,
    get_monitoring_status,
    monitor_function,
    MetricsMiddleware,
    Perfect21TracingMiddleware,
    record_api_request,
    record_agent_execution,
    trace_agent_execution,
    log_api_request,
    log_agent_execution,
    fire_custom_alert,
    run_health_checks,
    metrics_collector,
    tracer
)

class Perfect21MonitoringApp:
    """Perfect21监控集成应用示例"""

    def __init__(self):
        self.app = FastAPI(
            title="Perfect21 Monitoring Demo",
            description="Perfect21监控系统集成示例",
            version="1.0.0"
        )
        self._setup_middleware()
        self._setup_routes()
        self._monitoring_config = self._create_monitoring_config()

    def _create_monitoring_config(self) -> Dict[str, Any]:
        """创建监控配置"""
        return {
            'metrics': {
                'port': 8080,
                'update_interval': 30
            },
            'tracing': {
                'service_name': 'perfect21-demo',
                'jaeger_host': 'localhost:6831',
                'file_output': 'logs/traces.jsonl'
            },
            'health': {
                'interval': 60
            },
            'alerting': {
                'slack_webhook': None,  # 设置你的Slack webhook URL
                'email': {
                    'smtp': {
                        'host': 'smtp.gmail.com',
                        'port': 587,
                        'username': 'your-email@gmail.com',
                        'password': 'your-password',
                        'use_tls': True
                    },
                    'to_emails': ['admin@perfect21.com']
                }
            },
            'dashboards': {
                'generate': True,
                'output_dir': 'monitoring/dashboards'
            }
        }

    def _setup_middleware(self):
        """设置中间件"""
        # CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 监控中间件
        metrics_middleware = MetricsMiddleware(metrics_collector)
        tracing_middleware = Perfect21TracingMiddleware(tracer)

        # 自定义监控中间件
        @self.app.middleware("http")
        async def monitoring_middleware(request: Request, call_next):
            start_time = time.time()

            # 提取请求信息
            method = request.method
            url = str(request.url)
            user_agent = request.headers.get("user-agent", "")
            user_id = request.headers.get("x-user-id")  # 假设从头部获取用户ID
            source_ip = request.client.host

            try:
                # 处理请求
                response = await call_next(request)
                duration = time.time() - start_time

                # 记录API指标
                record_api_request(
                    method=method,
                    endpoint=request.url.path,
                    status_code=response.status_code,
                    duration=duration
                )

                # 记录审计日志
                log_api_request(
                    method=method,
                    endpoint=request.url.path,
                    status_code=response.status_code,
                    user_id=user_id,
                    source_ip=source_ip,
                    user_agent=user_agent,
                    duration=duration
                )

                return response

            except Exception as e:
                duration = time.time() - start_time

                # 记录错误
                record_api_request(
                    method=method,
                    endpoint=request.url.path,
                    status_code=500,
                    duration=duration
                )

                # 记录审计日志
                log_api_request(
                    method=method,
                    endpoint=request.url.path,
                    status_code=500,
                    user_id=user_id,
                    source_ip=source_ip,
                    user_agent=user_agent,
                    duration=duration
                )

                raise

    def _setup_routes(self):
        """设置路由"""

        @self.app.get("/")
        async def root():
            return {"message": "Perfect21 Monitoring Demo", "status": "running"}

        @self.app.get("/health")
        async def health_check():
            """健康检查端点"""
            health_results = await run_health_checks()
            return health_results

        @self.app.get("/metrics")
        async def get_metrics():
            """获取Prometheus指标"""
            from monitoring import get_metrics
            metrics_data = get_metrics()
            return Response(content=metrics_data, media_type="text/plain")

        @self.app.get("/monitoring/status")
        async def monitoring_status():
            """获取监控系统状态"""
            return get_monitoring_status()

        @self.app.post("/demo/agent-execution")
        async def demo_agent_execution(request: Dict[str, Any]):
            """演示Agent执行监控"""
            agent_name = request.get("agent_name", "demo-agent")
            task = request.get("task", "demo task")
            simulate_error = request.get("simulate_error", False)

            # 使用追踪装饰器
            with trace_agent_execution(agent_name, task) as span:
                start_time = time.time()

                try:
                    # 模拟Agent执行
                    await self._simulate_agent_work(agent_name, task, simulate_error)

                    duration = time.time() - start_time

                    # 记录成功执行
                    record_agent_execution(agent_name, "success", duration)
                    log_agent_execution(agent_name, task, True, duration)

                    span.set_tag("success", True)
                    span.set_tag("duration", duration)

                    return {
                        "status": "success",
                        "agent_name": agent_name,
                        "task": task,
                        "duration": duration
                    }

                except Exception as e:
                    duration = time.time() - start_time

                    # 记录失败执行
                    record_agent_execution(agent_name, "error", duration)
                    log_agent_execution(agent_name, task, False, duration)

                    span.set_error(e)

                    # 触发告警
                    fire_custom_alert(
                        name="AgentExecutionFailure",
                        message=f"Agent {agent_name} failed: {str(e)}",
                        severity="warning",
                        labels={"agent_name": agent_name, "task": task}
                    )

                    return {
                        "status": "error",
                        "agent_name": agent_name,
                        "task": task,
                        "error": str(e),
                        "duration": duration
                    }

        @self.app.post("/demo/parallel-workflow")
        async def demo_parallel_workflow(request: Dict[str, Any]):
            """演示并行工作流监控"""
            workflow_type = request.get("workflow_type", "premium_quality")
            agent_count = request.get("agent_count", 3)

            from monitoring import trace_parallel_execution

            with trace_parallel_execution(workflow_type, agent_count) as span:
                start_time = time.time()

                try:
                    # 模拟并行执行
                    tasks = []
                    for i in range(agent_count):
                        agent_name = f"parallel-agent-{i}"
                        task = asyncio.create_task(
                            self._simulate_agent_work(agent_name, f"parallel task {i}")
                        )
                        tasks.append(task)

                    # 等待所有任务完成
                    await asyncio.gather(*tasks)

                    duration = time.time() - start_time
                    metrics_collector.record_parallel_execution(workflow_type, "success", duration)

                    span.set_tag("success", True)
                    span.set_tag("total_duration", duration)

                    return {
                        "status": "success",
                        "workflow_type": workflow_type,
                        "agent_count": agent_count,
                        "duration": duration
                    }

                except Exception as e:
                    duration = time.time() - start_time
                    metrics_collector.record_parallel_execution(workflow_type, "error", duration)

                    span.set_error(e)

                    return {
                        "status": "error",
                        "workflow_type": workflow_type,
                        "error": str(e),
                        "duration": duration
                    }

        @self.app.post("/demo/fire-alert")
        async def demo_fire_alert(request: Dict[str, Any]):
            """演示告警系统"""
            alert_name = request.get("name", "TestAlert")
            message = request.get("message", "This is a test alert")
            severity = request.get("severity", "warning")

            fire_custom_alert(
                name=alert_name,
                message=message,
                severity=severity,
                labels={"source": "demo", "component": "test"}
            )

            return {
                "status": "alert_fired",
                "name": alert_name,
                "message": message,
                "severity": severity
            }

        @self.app.get("/monitoring/dashboard-config")
        async def get_dashboard_config():
            """获取仪表板配置"""
            from monitoring import generate_all_dashboards
            return generate_all_dashboards()

    @monitor_function("simulate_agent_work")
    async def _simulate_agent_work(self, agent_name: str, task: str, simulate_error: bool = False):
        """模拟Agent工作"""
        # 模拟工作时间
        work_time = 0.5 + (hash(agent_name) % 100) / 200  # 0.5-1.0秒
        await asyncio.sleep(work_time)

        if simulate_error:
            raise Exception(f"Simulated error in {agent_name}")

        return {"agent": agent_name, "task": task, "result": "completed"}

    def start(self, host: str = "0.0.0.0", port: int = 8000):
        """启动应用"""
        # 启动监控系统
        start_monitoring_system(self._monitoring_config)

        # 启动FastAPI应用
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)

    def stop(self):
        """停止应用"""
        stop_monitoring_system()

# 使用示例
async def monitoring_demo():
    """监控系统演示"""
    print("🚀 Starting Perfect21 Monitoring Demo...")

    # 启动监控系统
    config = {
        'metrics': {'port': 8080, 'update_interval': 10},
        'tracing': {'service_name': 'perfect21-demo'},
        'health': {'interval': 30},
        'alerting': {},
        'dashboards': {'generate': True}
    }

    start_monitoring_system(config)

    try:
        # 模拟一些监控事件
        print("📊 Generating sample metrics...")

        # 模拟Agent执行
        for i in range(5):
            agent_name = f"demo-agent-{i}"
            start_time = time.time()

            # 模拟工作
            await asyncio.sleep(0.1)

            duration = time.time() - start_time
            success = i < 4  # 最后一个失败

            if success:
                record_agent_execution(agent_name, "success", duration)
                log_agent_execution(agent_name, f"task-{i}", True, duration)
            else:
                record_agent_execution(agent_name, "error", duration)
                log_agent_execution(agent_name, f"task-{i}", False, duration)

                # 触发告警
                fire_custom_alert(
                    name="DemoAgentFailure",
                    message=f"Demo agent {agent_name} failed",
                    severity="warning"
                )

        # 检查健康状态
        print("🏥 Running health checks...")
        health_results = await run_health_checks()
        print(f"Health status: {health_results['status']}")

        # 获取监控状态
        print("📈 Getting monitoring status...")
        status = get_monitoring_status()
        print(f"Monitoring active: {status['started']}")

        print("✅ Demo completed successfully!")

    finally:
        # 清理
        stop_monitoring_system()

if __name__ == "__main__":
    # 运行演示
    app = Perfect21MonitoringApp()

    # 或者运行简单演示
    # asyncio.run(monitoring_demo())

    # 启动Web应用
    app.start()