#!/usr/bin/env python3
"""
Perfect21 重构后的架构示例
展示解耦和优化后的设计模式
"""

import asyncio
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import yaml
import json

# ================ 接口抽象层 ================

class IClaudeCodeAdapter(ABC):
    """Claude Code适配器接口 - 完全解耦"""

    @abstractmethod
    async def execute_subagent(self, agent_type: str, prompt: str,
                              context: Optional[Dict] = None) -> Dict[str, Any]:
        """执行子代理"""
        pass

    @abstractmethod
    def get_available_agents(self) -> List[str]:
        """获取可用代理列表"""
        pass

    @abstractmethod
    def validate_agent_type(self, agent_type: str) -> bool:
        """验证代理类型"""
        pass

class DirectClaudeCodeAdapter(IClaudeCodeAdapter):
    """直接调用适配器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timeout = config.get('timeout', 300)
        self.max_concurrent = config.get('max_concurrent_agents', 5)
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

    async def execute_subagent(self, agent_type: str, prompt: str,
                              context: Optional[Dict] = None) -> Dict[str, Any]:
        """执行子代理"""
        async with self.semaphore:
            # 模拟调用Claude Code的Task工具
            start_time = time.time()

            # 这里在实际环境中会调用真正的Task工具
            await asyncio.sleep(0.1)  # 模拟执行时间

            return {
                'success': True,
                'agent_type': agent_type,
                'result': f'Result from {agent_type}',
                'execution_time': time.time() - start_time,
                'context': context
            }

    def get_available_agents(self) -> List[str]:
        return [
            'backend-architect', 'frontend-specialist', 'database-specialist',
            'test-engineer', 'security-auditor', 'devops-engineer'
        ]

    def validate_agent_type(self, agent_type: str) -> bool:
        return agent_type in self.get_available_agents()

class MockClaudeCodeAdapter(IClaudeCodeAdapter):
    """测试用Mock适配器"""

    async def execute_subagent(self, agent_type: str, prompt: str,
                              context: Optional[Dict] = None) -> Dict[str, Any]:
        await asyncio.sleep(0.01)  # 模拟快速执行
        return {
            'success': True,
            'agent_type': agent_type,
            'result': f'Mock result from {agent_type}',
            'execution_time': 0.01
        }

    def get_available_agents(self) -> List[str]:
        return ['mock-agent-1', 'mock-agent-2']

    def validate_agent_type(self, agent_type: str) -> bool:
        return True

# ================ 事件驱动架构 ================

class EventBus:
    """事件总线"""

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[Dict] = []

    async def publish(self, event_type: str, data: Any):
        """发布事件"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': time.time()
        }
        self.event_history.append(event)

        # 异步通知所有订阅者
        handlers = self.subscribers.get(event_type, [])
        if handlers:
            await asyncio.gather(*[handler(data) for handler in handlers])

    def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    def get_event_history(self, event_type: Optional[str] = None) -> List[Dict]:
        """获取事件历史"""
        if event_type:
            return [e for e in self.event_history if e['type'] == event_type]
        return self.event_history.copy()

# ================ 插件系统 ================

class Perfect21Plugin(ABC):
    """插件基类"""

    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        pass

    @abstractmethod
    async def initialize(self, context: Dict[str, Any]) -> bool:
        """初始化插件"""
        pass

    @abstractmethod
    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """执行插件功能"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """清理插件资源"""
        pass

class WorkflowPlugin(Perfect21Plugin):
    """工作流插件"""

    def __init__(self):
        self.is_initialized = False
        self.claude_adapter: Optional[IClaudeCodeAdapter] = None

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "workflow_engine",
            "version": "2.0.0",
            "capabilities": ["workflow_execution", "task_management", "parallel_execution"],
            "dependencies": ["claude_code_adapter"]
        }

    async def initialize(self, context: Dict[str, Any]) -> bool:
        """初始化工作流插件"""
        self.claude_adapter = context.get('claude_adapter')
        if not self.claude_adapter:
            return False

        self.is_initialized = True
        return True

    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        if not self.is_initialized:
            return {'success': False, 'error': 'Plugin not initialized'}

        workflow_type = request.get('workflow_type', 'parallel')
        agents = request.get('agents', [])
        prompt = request.get('prompt', '')

        if workflow_type == 'parallel':
            return await self._execute_parallel_workflow(agents, prompt)
        elif workflow_type == 'sequential':
            return await self._execute_sequential_workflow(agents, prompt)
        else:
            return {'success': False, 'error': f'Unknown workflow type: {workflow_type}'}

    async def _execute_parallel_workflow(self, agents: List[str], prompt: str) -> Dict[str, Any]:
        """并行执行工作流"""
        tasks = []
        for agent in agents:
            if self.claude_adapter.validate_agent_type(agent):
                task = self.claude_adapter.execute_subagent(agent, prompt)
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            'success': True,
            'workflow_type': 'parallel',
            'agent_count': len(agents),
            'results': results,
            'execution_time': sum(r.get('execution_time', 0) for r in results if isinstance(r, dict))
        }

    async def _execute_sequential_workflow(self, agents: List[str], prompt: str) -> Dict[str, Any]:
        """顺序执行工作流"""
        results = []
        total_time = 0

        for agent in agents:
            if self.claude_adapter.validate_agent_type(agent):
                result = await self.claude_adapter.execute_subagent(agent, prompt)
                results.append(result)
                total_time += result.get('execution_time', 0)

        return {
            'success': True,
            'workflow_type': 'sequential',
            'agent_count': len(agents),
            'results': results,
            'execution_time': total_time
        }

    async def cleanup(self) -> None:
        """清理工作流插件"""
        self.claude_adapter = None
        self.is_initialized = False

class AuthPlugin(Perfect21Plugin):
    """认证插件"""

    def __init__(self):
        self.is_initialized = False
        self.auth_config = {}

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "auth_system",
            "version": "2.0.0",
            "capabilities": ["user_auth", "token_management", "permission_check"],
            "dependencies": []
        }

    async def initialize(self, context: Dict[str, Any]) -> bool:
        """初始化认证插件"""
        self.auth_config = context.get('auth_config', {})
        self.is_initialized = True
        return True

    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """执行认证功能"""
        if not self.is_initialized:
            return {'success': False, 'error': 'Plugin not initialized'}

        action = request.get('action')
        if action == 'authenticate':
            return await self._authenticate_user(request)
        elif action == 'validate_token':
            return await self._validate_token(request)
        elif action == 'check_permission':
            return await self._check_permission(request)
        else:
            return {'success': False, 'error': f'Unknown action: {action}'}

    async def _authenticate_user(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """用户认证"""
        username = request.get('username')
        password = request.get('password')

        # 模拟认证逻辑
        await asyncio.sleep(0.05)

        return {
            'success': True,
            'user_id': f"user_{username}",
            'token': f"token_{username}_{int(time.time())}",
            'expires_in': 3600
        }

    async def _validate_token(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """验证令牌"""
        token = request.get('token')

        # 模拟验证逻辑
        await asyncio.sleep(0.01)

        return {
            'success': True,
            'valid': 'token_' in token,
            'user_id': token.split('_')[1] if 'token_' in token else None
        }

    async def _check_permission(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """检查权限"""
        user_id = request.get('user_id')
        permission = request.get('permission')

        # 模拟权限检查
        await asyncio.sleep(0.01)

        return {
            'success': True,
            'user_id': user_id,
            'permission': permission,
            'granted': True  # 简化的权限逻辑
        }

    async def cleanup(self) -> None:
        """清理认证插件"""
        self.auth_config = {}
        self.is_initialized = False

# ================ 插件管理器 ================

class PluginManager:
    """插件管理器"""

    def __init__(self, event_bus: EventBus):
        self.plugins: Dict[str, Perfect21Plugin] = {}
        self.plugin_registry: Dict[str, Dict] = {}
        self.event_bus = event_bus

    async def load_plugin(self, plugin_name: str, plugin_class: type, context: Dict[str, Any]) -> bool:
        """加载插件"""
        try:
            plugin = plugin_class()

            # 初始化插件
            if await plugin.initialize(context):
                self.plugins[plugin_name] = plugin
                self.plugin_registry[plugin_name] = plugin.get_plugin_info()

                # 发布插件加载事件
                await self.event_bus.publish('plugin_loaded', {
                    'plugin_name': plugin_name,
                    'plugin_info': plugin.get_plugin_info()
                })

                return True
            else:
                return False

        except Exception as e:
            await self.event_bus.publish('plugin_load_failed', {
                'plugin_name': plugin_name,
                'error': str(e)
            })
            return False

    async def execute_plugin_capability(self, capability: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """执行插件能力"""
        for plugin_name, plugin in self.plugins.items():
            info = self.plugin_registry[plugin_name]
            if capability in info.get('capabilities', []):
                result = await plugin.execute(request)

                # 发布执行事件
                await self.event_bus.publish('plugin_executed', {
                    'plugin_name': plugin_name,
                    'capability': capability,
                    'success': result.get('success', False)
                })

                return result

        return {'success': False, 'error': f'No plugin found for capability: {capability}'}

    async def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            await plugin.cleanup()

            del self.plugins[plugin_name]
            del self.plugin_registry[plugin_name]

            await self.event_bus.publish('plugin_unloaded', {
                'plugin_name': plugin_name
            })

            return True
        return False

    def list_plugins(self) -> Dict[str, Dict]:
        """列出所有插件"""
        return self.plugin_registry.copy()

    def get_plugin_capabilities(self) -> Dict[str, List[str]]:
        """获取所有插件能力"""
        capabilities = {}
        for plugin_name, info in self.plugin_registry.items():
            capabilities[plugin_name] = info.get('capabilities', [])
        return capabilities

# ================ 配置管理 ================

@dataclass
class Perfect21Config:
    """Perfect21配置"""
    adapter_type: str = "direct"
    lazy_loading: bool = True
    plugin_mode: bool = True
    claude_code: Dict[str, Any] = None
    plugins: Dict[str, Any] = None
    performance: Dict[str, Any] = None

    def __post_init__(self):
        if self.claude_code is None:
            self.claude_code = {
                'timeout': 300,
                'max_concurrent_agents': 5
            }
        if self.plugins is None:
            self.plugins = {
                'enabled': ['workflow_engine', 'auth_system'],
                'disabled': []
            }
        if self.performance is None:
            self.performance = {
                'cache_enabled': True,
                'memory_limit_mb': 100
            }

class ConfigLoader:
    """配置加载器"""

    @staticmethod
    def load_from_yaml(file_path: str) -> Perfect21Config:
        """从YAML文件加载配置"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return Perfect21Config(
            adapter_type=data.get('adapter_type', 'direct'),
            lazy_loading=data.get('lazy_loading', True),
            plugin_mode=data.get('plugin_mode', True),
            claude_code=data.get('claude_code', {}),
            plugins=data.get('plugins', {}),
            performance=data.get('performance', {})
        )

    @staticmethod
    def load_default() -> Perfect21Config:
        """加载默认配置"""
        return Perfect21Config()

# ================ 核心架构 ================

class Perfect21Core:
    """重构后的Perfect21核心类"""

    def __init__(self, claude_adapter: IClaudeCodeAdapter, event_bus: EventBus, config: Perfect21Config):
        self.claude_adapter = claude_adapter
        self.event_bus = event_bus
        self.config = config
        self.plugin_manager = PluginManager(event_bus)
        self.is_initialized = False

        # 性能监控
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'total_execution_time': 0.0
        }

    async def initialize(self) -> bool:
        """初始化Perfect21核心"""
        try:
            # 订阅事件
            self.event_bus.subscribe('agent_execution_requested', self._handle_agent_execution)
            self.event_bus.subscribe('plugin_executed', self._update_execution_stats)

            # 加载插件
            await self._load_configured_plugins()

            self.is_initialized = True

            await self.event_bus.publish('perfect21_initialized', {
                'timestamp': time.time(),
                'config': asdict(self.config)
            })

            return True

        except Exception as e:
            await self.event_bus.publish('perfect21_initialization_failed', {
                'error': str(e)
            })
            return False

    async def _load_configured_plugins(self):
        """加载配置的插件"""
        enabled_plugins = self.config.plugins.get('enabled', [])
        context = {
            'claude_adapter': self.claude_adapter,
            'event_bus': self.event_bus,
            'config': self.config
        }

        plugin_classes = {
            'workflow_engine': WorkflowPlugin,
            'auth_system': AuthPlugin
        }

        for plugin_name in enabled_plugins:
            if plugin_name in plugin_classes:
                success = await self.plugin_manager.load_plugin(
                    plugin_name, plugin_classes[plugin_name], context
                )
                if success:
                    print(f"✅ 插件 {plugin_name} 加载成功")
                else:
                    print(f"❌ 插件 {plugin_name} 加载失败")

    async def execute_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        if not self.is_initialized:
            return {'success': False, 'error': 'Perfect21 not initialized'}

        start_time = time.time()

        try:
            # 通过插件系统执行工作流
            result = await self.plugin_manager.execute_plugin_capability('workflow_execution', workflow_config)

            # 更新统计
            self.execution_stats['total_executions'] += 1
            if result.get('success'):
                self.execution_stats['successful_executions'] += 1
            self.execution_stats['total_execution_time'] += time.time() - start_time

            return result

        except Exception as e:
            await self.event_bus.publish('workflow_execution_failed', {
                'error': str(e),
                'workflow_config': workflow_config
            })
            return {'success': False, 'error': str(e)}

    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """用户认证"""
        return await self.plugin_manager.execute_plugin_capability('user_auth', {
            'action': 'authenticate',
            'username': username,
            'password': password
        })

    async def _handle_agent_execution(self, data: Dict[str, Any]):
        """处理代理执行请求"""
        agent_type = data.get('agent_type')
        prompt = data.get('prompt')

        if self.claude_adapter.validate_agent_type(agent_type):
            result = await self.claude_adapter.execute_subagent(agent_type, prompt)
            await self.event_bus.publish('agent_execution_completed', {
                'agent_type': agent_type,
                'success': result.get('success', False),
                'execution_time': result.get('execution_time', 0)
            })

    async def _update_execution_stats(self, data: Dict[str, Any]):
        """更新执行统计"""
        # 可以在这里实现更详细的统计逻辑
        pass

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'initialized': self.is_initialized,
            'adapter_type': type(self.claude_adapter).__name__,
            'loaded_plugins': list(self.plugin_manager.list_plugins().keys()),
            'execution_stats': self.execution_stats.copy(),
            'config': asdict(self.config)
        }

    async def shutdown(self):
        """关闭系统"""
        # 卸载所有插件
        for plugin_name in list(self.plugin_manager.plugins.keys()):
            await self.plugin_manager.unload_plugin(plugin_name)

        await self.event_bus.publish('perfect21_shutdown', {
            'timestamp': time.time()
        })

# ================ 工厂类 ================

class Perfect21Factory:
    """Perfect21工厂类"""

    @staticmethod
    async def create_from_config(config: Perfect21Config) -> Perfect21Core:
        """从配置创建Perfect21实例"""
        # 创建适配器
        adapter = Perfect21Factory._create_adapter(config)

        # 创建事件总线
        event_bus = EventBus()

        # 创建核心实例
        core = Perfect21Core(adapter, event_bus, config)

        # 初始化
        await core.initialize()

        return core

    @staticmethod
    def _create_adapter(config: Perfect21Config) -> IClaudeCodeAdapter:
        """创建适配器"""
        adapter_type = config.adapter_type

        if adapter_type == "direct":
            return DirectClaudeCodeAdapter(config.claude_code)
        elif adapter_type == "mock":
            return MockClaudeCodeAdapter()
        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")

    @staticmethod
    async def create_for_testing() -> Perfect21Core:
        """创建测试实例"""
        config = Perfect21Config(adapter_type="mock")
        return await Perfect21Factory.create_from_config(config)

# ================ 示例使用 ================

async def demo_refactored_architecture():
    """演示重构后的架构"""
    print("🚀 Perfect21 重构架构演示")
    print("=" * 60)

    # 1. 创建Perfect21实例
    print("1. 创建Perfect21实例...")
    config = Perfect21Config(adapter_type="direct")
    perfect21 = await Perfect21Factory.create_from_config(config)

    # 2. 查看系统状态
    print("\n2. 系统状态:")
    status = perfect21.get_system_status()
    print(f"   初始化状态: {status['initialized']}")
    print(f"   适配器类型: {status['adapter_type']}")
    print(f"   加载的插件: {status['loaded_plugins']}")

    # 3. 执行并行工作流
    print("\n3. 执行并行工作流...")
    workflow_result = await perfect21.execute_workflow({
        'workflow_type': 'parallel',
        'agents': ['backend-architect', 'frontend-specialist', 'database-specialist'],
        'prompt': '设计一个用户认证系统'
    })
    print(f"   工作流执行成功: {workflow_result['success']}")
    print(f"   代理数量: {workflow_result.get('agent_count', 0)}")
    print(f"   执行时间: {workflow_result.get('execution_time', 0):.2f}秒")

    # 4. 用户认证
    print("\n4. 用户认证...")
    auth_result = await perfect21.authenticate_user("testuser", "password123")
    print(f"   认证成功: {auth_result['success']}")
    if auth_result['success']:
        print(f"   用户ID: {auth_result.get('user_id')}")
        print(f"   令牌: {auth_result.get('token', '')[:20]}...")

    # 5. 查看事件历史
    print("\n5. 事件历史:")
    events = perfect21.event_bus.get_event_history()
    print(f"   总事件数: {len(events)}")
    for event in events[-3:]:  # 显示最后3个事件
        print(f"   • {event['type']} (时间: {event['timestamp']:.2f})")

    # 6. 关闭系统
    print("\n6. 关闭系统...")
    await perfect21.shutdown()
    print("   系统已关闭")

if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_refactored_architecture())