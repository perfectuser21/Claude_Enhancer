"""
Task Manager - Mock Implementation for Testing
"""
import time

class TaskManager:
    """任务管理器 - 测试用Mock实现"""

    def __init__(self):
        self.tasks = {}
        self.task_counter = 0

    def create_task(self, task_config):
        """创建任务"""
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"

        task = {
            'task_id': task_id,
            'agent': task_config.get('agent'),
            'description': task_config.get('description'),
            'priority': task_config.get('priority', 'medium'),
            'timeout': task_config.get('timeout', 300),
            'status': 'created',
            'created_at': time.time()
        }

        self.tasks[task_id] = task
        return task

    def execute_task(self, task_id):
        """执行任务"""
        if task_id not in self.tasks:
            return {'success': False, 'error': 'Task not found'}

        self.tasks[task_id]['status'] = 'running'

        # 模拟执行
        result = self.execute_agent(self.tasks[task_id]['agent'])

        self.tasks[task_id]['status'] = 'completed'
        return result

    def execute_agent(self, agent):
        """执行agent"""
        return {
            'success': True,
            'result': f'Mock result from {agent}',
            'agent': agent
        }

    def get_task_status(self, task_id):
        """获取任务状态"""
        if task_id not in self.tasks:
            return 'not_found'
        return self.tasks[task_id]['status']

    def update_task_status(self, task_id, status):
        """更新任务状态"""
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = status

    def execute_task_with_timeout(self, task_id):
        """带超时的任务执行"""
        if task_id not in self.tasks:
            return {'success': False, 'error': 'Task not found'}

        task = self.tasks[task_id]

        # 模拟超时检查
        if task.get('timeout', 300) < 2:
            return {'success': False, 'error': 'Task execution timeout'}

        return self.execute_task(task_id)
