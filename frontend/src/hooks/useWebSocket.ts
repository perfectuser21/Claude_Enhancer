/**
 * WebSocket React Hook
 * 提供React组件中使用WebSocket的便捷方法
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { createWebSocketService, getWebSocketService, WebSocketConfig, ConnectionState } from '../services/websocket';

interface UseWebSocketOptions {
  url: string;
  autoConnect?: boolean;
  onMessage?: (type: string, data: any) => void;
  onConnectionChange?: (state: ConnectionState) => void;
  onError?: (error: Error) => void;
  debug?: boolean;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  connectionState: ConnectionState;
  connect: (userInfo: { userId: string; username: string }) => Promise<void>;
  disconnect: () => void;
  send: (type: string, data: any, options?: any) => void;
  on: (event: string, callback: (data: any) => void) => () => void;
  once: (event: string, callback: (data: any) => void) => () => void;
  off: (event: string, callback?: (data: any) => void) => void;
  joinRoom: (roomId: string, roomName?: string) => void;
  leaveRoom: (roomId: string) => void;
  error: Error | null;
}

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    isConnected: false,
    isConnecting: false,
    reconnectAttempts: 0
  });
  const [error, setError] = useState<Error | null>(null);

  const wsRef = useRef(getWebSocketService());
  const unsubscribeRefs = useRef<(() => void)[]>([]);

  // 初始化WebSocket服务
  useEffect(() => {
    if (!wsRef.current) {
      const config: WebSocketConfig = {
        url: options.url,
        debug: options.debug || false
      };
      wsRef.current = createWebSocketService(config);
    }

    const ws = wsRef.current;

    // 设置连接状态监听器
    const unsubscribeConnection = ws.onConnectionChange((state) => {
      setConnectionState(state);
      options.onConnectionChange?.(state);
    });

    // 设置错误监听器
    const unsubscribeError = ws.onError((err) => {
      setError(err);
      options.onError?.(err);
    });

    // 设置通用消息监听器
    let unsubscribeMessage: (() => void) | undefined;
    if (options.onMessage) {
      unsubscribeMessage = ws.on('*', ({ type, data }) => {
        options.onMessage!(type, data);
      });
    }

    unsubscribeRefs.current = [
      unsubscribeConnection,
      unsubscribeError,
      ...(unsubscribeMessage ? [unsubscribeMessage] : [])
    ];

    return () => {
      unsubscribeRefs.current.forEach(unsub => unsub());
      unsubscribeRefs.current = [];
    };
  }, [options.url, options.debug, options.onConnectionChange, options.onError, options.onMessage]);

  // 连接方法
  const connect = useCallback(async (userInfo: { userId: string; username: string }) => {
    if (wsRef.current) {
      setError(null);
      try {
        await wsRef.current.connect(userInfo);
      } catch (err) {
        setError(err as Error);
        throw err;
      }
    }
  }, []);

  // 断开连接方法
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.disconnect();
    }
  }, []);

  // 发送消息方法
  const send = useCallback((type: string, data: any, options?: any) => {
    if (wsRef.current) {
      wsRef.current.send(type, data, options);
    }
  }, []);

  // 监听事件方法
  const on = useCallback((event: string, callback: (data: any) => void) => {
    if (wsRef.current) {
      return wsRef.current.on(event, callback);
    }
    return () => {};
  }, []);

  // 一次性监听事件方法
  const once = useCallback((event: string, callback: (data: any) => void) => {
    if (wsRef.current) {
      return wsRef.current.once(event, callback);
    }
    return () => {};
  }, []);

  // 移除事件监听器方法
  const off = useCallback((event: string, callback?: (data: any) => void) => {
    if (wsRef.current) {
      wsRef.current.off(event, callback);
    }
  }, []);

  // 加入房间方法
  const joinRoom = useCallback((roomId: string, roomName?: string) => {
    if (wsRef.current) {
      wsRef.current.joinRoom(roomId, roomName);
    }
  }, []);

  // 离开房间方法
  const leaveRoom = useCallback((roomId: string) => {
    if (wsRef.current) {
      wsRef.current.leaveRoom(roomId);
    }
  }, []);

  return {
    isConnected: connectionState.isConnected,
    isConnecting: connectionState.isConnecting,
    connectionState,
    connect,
    disconnect,
    send,
    on,
    once,
    off,
    joinRoom,
    leaveRoom,
    error
  };
}

/**
 * 任务实时更新Hook
 */
export function useTaskUpdates(projectId?: string) {
  const [tasks, setTasks] = useState<any[]>([]);
  const [taskUpdates, setTaskUpdates] = useState<any[]>([]);

  const ws = useWebSocket({
    url: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws',
    onMessage: (type, data) => {
      switch (type) {
        case 'task_created':
          setTasks(prev => [...prev, data]);
          setTaskUpdates(prev => [...prev, { type: 'created', task: data, timestamp: new Date() }]);
          break;

        case 'task_updated':
          setTasks(prev => prev.map(task =>
            task.task_id === data.task_id ? { ...task, ...data } : task
          ));
          setTaskUpdates(prev => [...prev, { type: 'updated', task: data, timestamp: new Date() }]);
          break;

        case 'task_deleted':
          setTasks(prev => prev.filter(task => task.task_id !== data.task_id));
          setTaskUpdates(prev => [...prev, { type: 'deleted', task: data, timestamp: new Date() }]);
          break;

        case 'task_status_changed':
          setTasks(prev => prev.map(task =>
            task.task_id === data.task_id
              ? { ...task, status: data.new_status }
              : task
          ));
          setTaskUpdates(prev => [...prev, { type: 'status_changed', task: data, timestamp: new Date() }]);
          break;
      }
    }
  });

  // 加入项目房间
  useEffect(() => {
    if (ws.isConnected && projectId) {
      ws.joinRoom(projectId, `Project ${projectId}`);
      return () => ws.leaveRoom(projectId);
    }
  }, [ws.isConnected, projectId, ws]);

  // 清理更新历史（保留最近50条）
  useEffect(() => {
    if (taskUpdates.length > 50) {
      setTaskUpdates(prev => prev.slice(-50));
    }
  }, [taskUpdates]);

  return {
    ...ws,
    tasks,
    taskUpdates,
    setTasks
  };
}

/**
 * 用户在线状态Hook
 */
export function useOnlineUsers(roomId?: string) {
  const [onlineUsers, setOnlineUsers] = useState<any[]>([]);
  const [userStatuses, setUserStatuses] = useState<Record<string, string>>({});

  const ws = useWebSocket({
    url: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws',
    onMessage: (type, data) => {
      switch (type) {
        case 'user_online':
          setOnlineUsers(prev => {
            const filtered = prev.filter(user => user.user_id !== data.user_id);
            return [...filtered, data];
          });
          setUserStatuses(prev => ({ ...prev, [data.user_id]: 'online' }));
          break;

        case 'user_offline':
          setOnlineUsers(prev => prev.filter(user => user.user_id !== data.user_id));
          setUserStatuses(prev => ({ ...prev, [data.user_id]: 'offline' }));
          break;

        case 'user_join_project':
          if (!roomId || data.room_id === roomId) {
            setOnlineUsers(prev => {
              const filtered = prev.filter(user => user.user_id !== data.user_id);
              return [...filtered, data];
            });
          }
          break;

        case 'user_leave_project':
          if (!roomId || data.room_id === roomId) {
            setOnlineUsers(prev => prev.filter(user => user.user_id !== data.user_id));
          }
          break;
      }
    }
  });

  // 请求在线用户列表
  useEffect(() => {
    if (ws.isConnected) {
      ws.send('get_online_users', { room_id: roomId });
    }
  }, [ws.isConnected, roomId, ws]);

  return {
    ...ws,
    onlineUsers,
    userStatuses,
    getUserStatus: (userId: string) => userStatuses[userId] || 'offline'
  };
}

/**
 * 协作编辑Hook
 */
export function useCollaborativeEditing(documentId: string) {
  const [collaborators, setCollaborators] = useState<any[]>([]);
  const [documentState, setDocumentState] = useState<any>(null);
  const [isEditing, setIsEditing] = useState(false);

  const ws = useWebSocket({
    url: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws',
    onMessage: (type, data) => {
      switch (type) {
        case 'collaboration_start':
          if (data.document_id === documentId) {
            setCollaborators(prev => {
              const filtered = prev.filter(user => user.user_id !== data.user_id);
              return [...filtered, data];
            });
          }
          break;

        case 'collaboration_end':
          if (data.document_id === documentId) {
            setCollaborators(prev => prev.filter(user => user.user_id !== data.user_id));
          }
          break;

        case 'document_edit':
          if (data.document_id === documentId) {
            setDocumentState(prev => ({ ...prev, ...data }));
          }
          break;
      }
    }
  });

  // 开始协作编辑
  const startCollaboration = useCallback(() => {
    if (ws.isConnected && !isEditing) {
      ws.send('collaboration_start', { document_id: documentId });
      ws.joinRoom(documentId, `Document ${documentId}`);
      setIsEditing(true);
    }
  }, [ws, documentId, isEditing]);

  // 结束协作编辑
  const endCollaboration = useCallback(() => {
    if (ws.isConnected && isEditing) {
      ws.send('collaboration_end', { document_id: documentId });
      ws.leaveRoom(documentId);
      setIsEditing(false);
    }
  }, [ws, documentId, isEditing]);

  // 发送编辑操作
  const sendEdit = useCallback((action: string, position: number, content: string) => {
    if (ws.isConnected && isEditing) {
      ws.send('document_edit', {
        document_id: documentId,
        action,
        position,
        content
      });
    }
  }, [ws, documentId, isEditing]);

  // 组件卸载时结束协作
  useEffect(() => {
    return () => {
      if (isEditing) {
        endCollaboration();
      }
    };
  }, [isEditing, endCollaboration]);

  return {
    ...ws,
    collaborators,
    documentState,
    isEditing,
    startCollaboration,
    endCollaboration,
    sendEdit
  };
}

/**
 * 通知Hook
 */
export function useNotifications() {
  const [notifications, setNotifications] = useState<any[]>([]);

  const ws = useWebSocket({
    url: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws',
    onMessage: (type, data) => {
      if (type === 'system_notification' || type === 'project_notification') {
        const notification = {
          id: data.notification_id || Date.now().toString(),
          ...data,
          timestamp: new Date(),
          read: false
        };
        setNotifications(prev => [notification, ...prev]);

        // 自动消失的通知
        if (data.auto_dismiss && data.dismiss_timeout) {
          setTimeout(() => {
            setNotifications(prev => prev.filter(n => n.id !== notification.id));
          }, data.dismiss_timeout);
        }
      }
    }
  });

  // 标记通知为已读
  const markAsRead = useCallback((notificationId: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
    );
  }, []);

  // 删除通知
  const removeNotification = useCallback((notificationId: string) => {
    setNotifications(prev => prev.filter(n => n.id !== notificationId));
  }, []);

  // 清除所有通知
  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  return {
    ...ws,
    notifications,
    unreadCount: notifications.filter(n => !n.read).length,
    markAsRead,
    removeNotification,
    clearAll
  };
}