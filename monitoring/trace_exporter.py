#!/usr/bin/env python3
"""
Trace Exporter - Perfect21 Distributed Tracing
基于OpenTelemetry的分布式追踪系统
"""

import time
import threading
import json
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from contextlib import contextmanager
from dataclasses import dataclass, asdict
import asyncio
from contextvars import ContextVar

# 简化的OpenTelemetry实现
trace_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('trace_context', default=None)

@dataclass
class SpanContext:
    """Span上下文"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = None

    def __post_init__(self):
        if self.baggage is None:
            self.baggage = {}

@dataclass
class Span:
    """追踪Span"""
    context: SpanContext
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    tags: Dict[str, Any] = None
    logs: List[Dict[str, Any]] = None
    status: str = 'OK'  # OK, ERROR, TIMEOUT

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.logs is None:
            self.logs = []

    @property
    def duration(self) -> Optional[float]:
        """获取持续时间"""
        if self.end_time:
            return self.end_time - self.start_time
        return None

    def finish(self, status: str = 'OK'):
        """结束Span"""
        self.end_time = time.time()
        self.status = status

    def set_tag(self, key: str, value: Any):
        """设置标签"""
        self.tags[key] = value

    def log(self, message: str, level: str = 'INFO', **kwargs):
        """添加日志"""
        self.logs.append({
            'timestamp': time.time(),
            'level': level,
            'message': message,
            **kwargs
        })

    def set_error(self, error: Exception):
        """设置错误信息"""
        self.status = 'ERROR'
        self.set_tag('error', True)
        self.set_tag('error.type', type(error).__name__)
        self.set_tag('error.message', str(error))
        self.log(f"Error: {error}", level='ERROR')

class Perfect21Tracer:
    """Perfect21分布式追踪器"""

    def __init__(self, service_name: str = "perfect21"):
        self.service_name = service_name
        self.spans: Dict[str, Span] = {}
        self.finished_spans: List[Span] = []
        self._lock = threading.Lock()
        self._exporters: List['TraceExporter'] = []

    def add_exporter(self, exporter: 'TraceExporter'):
        """添加导出器"""
        self._exporters.append(exporter)

    def start_span(self,
                   operation_name: str,
                   parent_context: Optional[SpanContext] = None,
                   tags: Dict[str, Any] = None) -> Span:
        """开始新的Span"""

        # 生成trace_id和span_id
        if parent_context:
            trace_id = parent_context.trace_id
            parent_span_id = parent_context.span_id
        else:
            trace_id = self._generate_trace_id()
            parent_span_id = None

        span_id = self._generate_span_id()

        # 创建Span上下文
        context = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id
        )

        # 创建Span
        span = Span(
            context=context,
            operation_name=operation_name,
            start_time=time.time(),
            tags=tags or {}
        )

        # 设置服务信息
        span.set_tag('service.name', self.service_name)
        span.set_tag('span.kind', 'internal')

        with self._lock:
            self.spans[span_id] = span

        # 设置当前上下文
        trace_context.set({
            'trace_id': trace_id,
            'span_id': span_id,
            'span': span
        })

        return span

    def finish_span(self, span: Span):
        """结束Span"""
        if not span.end_time:
            span.finish()

        with self._lock:
            # 移动到已完成列表
            if span.context.span_id in self.spans:
                del self.spans[span.context.span_id]
            self.finished_spans.append(span)

            # 导出Span
            for exporter in self._exporters:
                try:
                    exporter.export_span(span)
                except Exception as e:
                    print(f"Error exporting span: {e}")

    @contextmanager
    def span(self, operation_name: str, **kwargs):
        """Span上下文管理器"""
        current_context = trace_context.get()
        parent_context = None

        if current_context:
            parent_context = SpanContext(
                trace_id=current_context['trace_id'],
                span_id=current_context['span_id']
            )

        span = self.start_span(operation_name, parent_context, kwargs.get('tags'))

        try:
            yield span
        except Exception as e:
            span.set_error(e)
            raise
        finally:
            self.finish_span(span)

    def get_current_span(self) -> Optional[Span]:
        """获取当前Span"""
        current_context = trace_context.get()
        if current_context:
            return current_context.get('span')
        return None

    def inject_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """注入追踪上下文到HTTP头"""
        current_context = trace_context.get()
        if current_context:
            headers = headers.copy()
            headers['X-Trace-Id'] = current_context['trace_id']
            headers['X-Span-Id'] = current_context['span_id']
            headers['X-Perfect21-Trace'] = 'true'
        return headers

    def extract_context(self, headers: Dict[str, str]) -> Optional[SpanContext]:
        """从HTTP头提取追踪上下文"""
        trace_id = headers.get('X-Trace-Id')
        span_id = headers.get('X-Span-Id')

        if trace_id and span_id:
            return SpanContext(
                trace_id=trace_id,
                span_id=span_id
            )
        return None

    def _generate_trace_id(self) -> str:
        """生成trace ID"""
        return str(uuid.uuid4()).replace('-', '')

    def _generate_span_id(self) -> str:
        """生成span ID"""
        return str(uuid.uuid4()).replace('-', '')[:16]

    def get_finished_spans(self, limit: int = 100) -> List[Span]:
        """获取已完成的Spans"""
        with self._lock:
            return self.finished_spans[-limit:]

    def clear_finished_spans(self):
        """清理已完成的Spans"""
        with self._lock:
            self.finished_spans.clear()

class TraceExporter:
    """追踪导出器基类"""

    def export_span(self, span: Span):
        """导出单个Span"""
        raise NotImplementedError

    def export_spans(self, spans: List[Span]):
        """批量导出Spans"""
        for span in spans:
            self.export_span(span)

class JaegerExporter(TraceExporter):
    """Jaeger导出器"""

    def __init__(self, agent_host: str = "localhost", agent_port: int = 6831):
        self.agent_host = agent_host
        self.agent_port = agent_port

    def export_span(self, span: Span):
        """导出到Jaeger（模拟实现）"""
        try:
            # 在实际实现中，这里会发送UDP包到Jaeger Agent
            jaeger_span = self._convert_to_jaeger_format(span)
            print(f"Export to Jaeger: {jaeger_span['operationName']} ({span.duration:.3f}s)")
        except Exception as e:
            print(f"Error exporting to Jaeger: {e}")

    def _convert_to_jaeger_format(self, span: Span) -> Dict[str, Any]:
        """转换为Jaeger格式"""
        return {
            'traceID': span.context.trace_id,
            'spanID': span.context.span_id,
            'parentSpanID': span.context.parent_span_id,
            'operationName': span.operation_name,
            'startTime': int(span.start_time * 1000000),  # 微秒
            'duration': int((span.duration or 0) * 1000000),  # 微秒
            'tags': [{'key': k, 'value': str(v)} for k, v in span.tags.items()],
            'logs': span.logs,
            'process': {
                'serviceName': span.tags.get('service.name', 'perfect21'),
                'tags': []
            }
        }

class ConsoleExporter(TraceExporter):
    """控制台导出器"""

    def export_span(self, span: Span):
        """导出到控制台"""
        duration_str = f"{span.duration:.3f}s" if span.duration else "ongoing"
        status_icon = "✅" if span.status == 'OK' else "❌"

        print(f"{status_icon} [{span.context.trace_id[:8]}] {span.operation_name} ({duration_str})")

        if span.tags:
            for key, value in span.tags.items():
                if key not in ['service.name', 'span.kind']:
                    print(f"    {key}: {value}")

class FileExporter(TraceExporter):
    """文件导出器"""

    def __init__(self, file_path: str = "logs/traces.jsonl"):
        self.file_path = file_path
        self._ensure_directory()

    def _ensure_directory(self):
        """确保目录存在"""
        import os
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def export_span(self, span: Span):
        """导出到文件"""
        try:
            span_data = {
                'timestamp': datetime.fromtimestamp(span.start_time).isoformat(),
                'traceId': span.context.trace_id,
                'spanId': span.context.span_id,
                'parentSpanId': span.context.parent_span_id,
                'operationName': span.operation_name,
                'duration': span.duration,
                'status': span.status,
                'tags': span.tags,
                'logs': span.logs
            }

            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(span_data, ensure_ascii=False) + '\n')

        except Exception as e:
            print(f"Error writing trace to file: {e}")

class Perfect21TracingMiddleware:
    """Perfect21追踪中间件"""

    def __init__(self, tracer: Perfect21Tracer):
        self.tracer = tracer

    def __call__(self, request, call_next):
        """ASGI中间件"""
        import asyncio
        return asyncio.create_task(self._process_request(request, call_next))

    async def _process_request(self, request, call_next):
        """处理请求并创建追踪"""
        # 提取上下文
        headers = dict(request.headers)
        parent_context = self.tracer.extract_context(headers)

        # 创建Span
        operation_name = f"{request.method} {request.url.path}"

        with self.tracer.span(operation_name, tags={
            'http.method': request.method,
            'http.url': str(request.url),
            'http.scheme': request.url.scheme,
            'http.host': request.url.hostname,
            'component': 'http'
        }) as span:
            try:
                response = await call_next(request)

                # 设置响应信息
                span.set_tag('http.status_code', response.status_code)
                span.set_tag('http.response_size', len(response.body) if hasattr(response, 'body') else 0)

                if response.status_code >= 400:
                    span.set_tag('error', True)
                    span.status = 'ERROR'

                return response

            except Exception as e:
                span.set_error(e)
                raise

class Perfect21AgentTracer:
    """Perfect21 Agent执行追踪器"""

    def __init__(self, tracer: Perfect21Tracer):
        self.tracer = tracer

    @contextmanager
    def trace_agent_execution(self, agent_name: str, task: str, **kwargs):
        """追踪Agent执行"""
        with self.tracer.span(f"agent_execution:{agent_name}", tags={
            'agent.name': agent_name,
            'agent.task': task,
            'component': 'perfect21_agent',
            **kwargs
        }) as span:
            yield span

    @contextmanager
    def trace_parallel_execution(self, workflow_type: str, agent_count: int):
        """追踪并行执行"""
        with self.tracer.span(f"parallel_execution:{workflow_type}", tags={
            'workflow.type': workflow_type,
            'workflow.agent_count': agent_count,
            'component': 'perfect21_workflow'
        }) as span:
            yield span

    @contextmanager
    def trace_git_operation(self, operation: str, **kwargs):
        """追踪Git操作"""
        with self.tracer.span(f"git_operation:{operation}", tags={
            'git.operation': operation,
            'component': 'perfect21_git',
            **kwargs
        }) as span:
            yield span

    @contextmanager
    def trace_quality_check(self, check_type: str, **kwargs):
        """追踪质量检查"""
        with self.tracer.span(f"quality_check:{check_type}", tags={
            'quality.check_type': check_type,
            'component': 'perfect21_quality',
            **kwargs
        }) as span:
            yield span

# 全局追踪器实例
tracer = Perfect21Tracer()
agent_tracer = Perfect21AgentTracer(tracer)

# 默认添加控制台导出器
tracer.add_exporter(ConsoleExporter())
tracer.add_exporter(FileExporter())

# 便捷函数
def start_span(operation_name: str, **kwargs) -> Span:
    """开始新的Span"""
    return tracer.start_span(operation_name, tags=kwargs)

def get_current_span() -> Optional[Span]:
    """获取当前Span"""
    return tracer.get_current_span()

def trace_agent_execution(agent_name: str, task: str, **kwargs):
    """追踪Agent执行"""
    return agent_tracer.trace_agent_execution(agent_name, task, **kwargs)

def trace_parallel_execution(workflow_type: str, agent_count: int):
    """追踪并行执行"""
    return agent_tracer.trace_parallel_execution(workflow_type, agent_count)

def trace_git_operation(operation: str, **kwargs):
    """追踪Git操作"""
    return agent_tracer.trace_git_operation(operation, **kwargs)

def trace_quality_check(check_type: str, **kwargs):
    """追踪质量检查"""
    return agent_tracer.trace_quality_check(check_type, **kwargs)

def configure_tracing(service_name: str = "perfect21",
                     jaeger_host: str = None,
                     file_output: str = None):
    """配置追踪系统"""
    global tracer, agent_tracer

    tracer = Perfect21Tracer(service_name)
    agent_tracer = Perfect21AgentTracer(tracer)

    # 添加导出器
    tracer.add_exporter(ConsoleExporter())

    if file_output:
        tracer.add_exporter(FileExporter(file_output))

    if jaeger_host:
        try:
            host, port = jaeger_host.split(':') if ':' in jaeger_host else (jaeger_host, 6831)
            tracer.add_exporter(JaegerExporter(host, int(port)))
        except Exception as e:
            print(f"Failed to configure Jaeger exporter: {e}")

def get_trace_summary() -> Dict[str, Any]:
    """获取追踪摘要"""
    finished_spans = tracer.get_finished_spans(limit=1000)

    if not finished_spans:
        return {'message': 'No traces available'}

    # 按操作分组统计
    operations = {}
    total_spans = len(finished_spans)

    for span in finished_spans:
        op_name = span.operation_name
        if op_name not in operations:
            operations[op_name] = {
                'count': 0,
                'total_duration': 0,
                'avg_duration': 0,
                'error_count': 0,
                'error_rate': 0
            }

        operations[op_name]['count'] += 1
        if span.duration:
            operations[op_name]['total_duration'] += span.duration

        if span.status == 'ERROR':
            operations[op_name]['error_count'] += 1

    # 计算平均值和错误率
    for op_data in operations.values():
        if op_data['count'] > 0:
            op_data['avg_duration'] = op_data['total_duration'] / op_data['count']
            op_data['error_rate'] = op_data['error_count'] / op_data['count']

    return {
        'total_spans': total_spans,
        'operations': operations,
        'summary_time': datetime.now().isoformat()
    }