# WebSocket实时通信系统使用指南

Claude Enhancer 5.0 的WebSocket实时通信系统提供了完整的实时功能，包括任务状态更新、用户在线状态、协作编辑、系统通知等功能。

## 🚀 快速开始

### 后端启动

#### 1. 安装依赖
```bash
pip install websockets
```

#### 2. 启动WebSocket服务器
```python
# 方法1: 独立启动
python src/websocket/server.py --host 0.0.0.0 --port 8765

# 方法2: 集成到现有应用
from src.websocket import initialize_websocket_system
await initialize_websocket_system("0.0.0.0", 8765)
```

### 前端集成

#### 1. 基础设置
```jsx
// App.jsx
import { WebSocketProvider } from './components/realtime/WebSocketProvider';

function App() {
  const userInfo = {
    userId: 'user_123',
    username: 'John Doe'
  };

  return (
    <WebSocketProvider userInfo={userInfo}>
      <YourAppComponents />
    </WebSocketProvider>
  );
}
```

#### 2. 使用实时功能
```jsx
// 在组件中使用
import { useWebSocketContext } from './components/realtime/WebSocketProvider';

function TaskList() {
  const {
    isConnected,
    sendTaskUpdate,
    joinProjectRoom,
    notifications
  } = useWebSocketContext();

  useEffect(() => {
    if (isConnected) {
      joinProjectRoom('project_123', 'My Project');
    }
  }, [isConnected]);

  return (
    <div>
      <div>连接状态: {isConnected ? '已连接' : '未连接'}</div>
      {/* 其他组件 */}
    </div>
  );
}
```

## 📡 核心功能

### 1. 任务实时更新

#### 后端广播任务更新
```python
from src.websocket import broadcast_task_update

# 任务创建
await broadcast_task_update({
    'task_id': 'task_123',
    'title': '新任务',
    'status': 'todo',
    'assignee_id': 'user_456',
    'project_id': 'project_123'
}, 'task_created')

# 任务状态变更
await broadcast_task_update({
    'task_id': 'task_123',
    'old_status': 'todo',
    'new_status': 'in_progress',
    'changed_by': 'user_789'
}, 'task_status_changed')
```

#### 前端监听任务更新
```jsx
import { useTaskUpdates } from './hooks/useWebSocket';

function TaskComponent({ projectId }) {
  const { tasks, taskUpdates, isConnected } = useTaskUpdates(projectId);

  return (
    <div>
      {tasks.map(task => (
        <TaskItem key={task.task_id} task={task} />
      ))}
    </div>
  );
}
```

### 2. 用户在线状态

#### 显示在线用户
```jsx
import OnlineUsers from './components/realtime/OnlineUsers';

function ProjectSidebar({ projectId }) {
  return (
    <div>
      <OnlineUsers
        roomId={projectId}
        projectName="我的项目"
        showCollaborators={true}
      />
    </div>
  );
}
```

#### 监听用户状态变化
```jsx
import { useOnlineUsers } from './hooks/useWebSocket';

function UserStatus({ roomId }) {
  const { onlineUsers, userStatuses, getUserStatus } = useOnlineUsers(roomId);

  return (
    <div>
      在线用户: {onlineUsers.length}
      {onlineUsers.map(user => (
        <div key={user.user_id}>
          {user.username} - {getUserStatus(user.user_id)}
        </div>
      ))}
    </div>
  );
}
```

### 3. 实时通知系统

#### 发送系统通知
```python
from src.websocket import send_notification_to_user

# 发送给特定用户
await send_notification_to_user(
    'user_123',
    '任务提醒',
    '您有新的任务分配',
    'info'
)
```

#### 显示通知中心
```jsx
import NotificationCenter from './components/realtime/NotificationCenter';

function Header() {
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <div>
      <button onClick={() => setShowNotifications(true)}>
        通知 🔔
      </button>

      <NotificationCenter
        isOpen={showNotifications}
        onClose={() => setShowNotifications(false)}
      />
    </div>
  );
}
```

### 4. 协作编辑

#### 开始协作编辑
```jsx
import { useCollaborativeEditing } from './hooks/useWebSocket';

function DocumentEditor({ documentId }) {
  const {
    collaborators,
    isEditing,
    startCollaboration,
    endCollaboration,
    sendEdit
  } = useCollaborativeEditing(documentId);

  const handleTextChange = (position, content) => {
    sendEdit('insert', position, content);
  };

  return (
    <div>
      <button onClick={startCollaboration}>开始协作</button>
      <div>协作者: {collaborators.length}</div>
      {/* 文档编辑器 */}
    </div>
  );
}
```

### 5. 任务状态指示器

```jsx
import TaskStatusIndicator from './components/realtime/TaskStatusIndicator';

function TaskCard({ task, projectId }) {
  return (
    <div className="task-card">
      <h3>{task.title}</h3>
      <TaskStatusIndicator
        taskId={task.id}
        projectId={projectId}
        initialStatus={task.status}
        showCollaborators={true}
        showStatusHistory={true}
      />
    </div>
  );
}
```

## 🔧 配置选项

### 环境变量
```bash
# .env
REACT_APP_WS_URL=ws://localhost:8765
NODE_ENV=development
```

### WebSocket配置
```javascript
// websocket配置
const wsConfig = {
  url: 'ws://localhost:8765',
  heartbeatInterval: 30000,      // 30秒心跳
  reconnectInterval: 5000,       // 5秒重连间隔
  maxReconnectAttempts: 10,      // 最大重连次数
  debug: true                    // 调试模式
};
```

## 📊 监控和调试

### 获取连接统计
```python
from src.websocket import get_websocket_stats

stats = get_websocket_stats()
print(f"活跃连接: {stats['active_connections']}")
print(f"总消息数: {stats['messages_sent']}")
```

### 前端调试
```javascript
// 在浏览器控制台中
console.log('WebSocket状态:', window.wsInstance?.getState());
```

## 🛡️ 安全考虑

### 1. 认证验证
```python
# 在server.py中自定义认证逻辑
async def authenticate_user(self, user_id: str, username: str) -> bool:
    # 检查JWT token
    # 验证用户权限
    # 检查IP白名单
    return True  # 替换为实际验证逻辑
```

### 2. 消息过滤
```python
# 只允许用户接收相关项目的消息
def can_user_access_room(user_id: str, room_id: str) -> bool:
    # 检查用户是否为项目成员
    return True
```

## 📈 性能优化

### 1. 消息队列
- 支持离线消息队列
- 自动重连时重发未确认消息
- 消息优先级处理

### 2. 连接管理
- 自动清理非活跃连接
- 心跳保活机制
- 智能重连策略

### 3. 内存优化
- 限制通知历史数量
- 定期清理过期数据
- 懒加载大数据集

## 🔍 故障排除

### 常见问题

#### 1. 连接失败
```bash
# 检查WebSocket服务器状态
telnet localhost 8765

# 检查防火墙设置
sudo ufw status
```

#### 2. 消息丢失
- 检查网络连接
- 确认服务器日志
- 验证消息格式

#### 3. 性能问题
- 监控连接数量
- 检查消息频率
- 优化事件处理器

### 调试技巧

#### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 前端调试
```javascript
// 启用WebSocket调试
const ws = createWebSocketService({
  url: 'ws://localhost:8765',
  debug: true
});
```

## 🚀 部署指南

### 生产环境配置
```python
# 生产环境启动
await start_websocket_server("0.0.0.0", 8765)
```

### Docker部署
```dockerfile
# Dockerfile
EXPOSE 8765
CMD ["python", "src/websocket/server.py", "--host", "0.0.0.0", "--port", "8765"]
```

### Nginx代理
```nginx
# nginx.conf
location /ws {
    proxy_pass http://localhost:8765;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

## 📚 API参考

### 事件类型
- `connect` - 用户连接
- `disconnect` - 用户断开
- `task_created` - 任务创建
- `task_updated` - 任务更新
- `task_status_changed` - 任务状态变更
- `user_online` - 用户上线
- `user_offline` - 用户下线
- `system_notification` - 系统通知
- `document_edit` - 文档编辑

### 消息格式
```json
{
  "type": "task_updated",
  "data": {
    "task_id": "task_123",
    "title": "任务标题",
    "status": "in_progress"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "message_id": "msg_123",
  "user_id": "user_456",
  "room_id": "project_789"
}
```

## 🤝 贡献指南

欢迎贡献代码！请确保：

1. 遵循现有代码风格
2. 添加必要的测试
3. 更新相关文档
4. 提交前进行充分测试

---

💡 **提示**: 这个WebSocket系统设计为高性能、可扩展的实时通信解决方案。如果遇到问题，请查看日志或提交Issue。