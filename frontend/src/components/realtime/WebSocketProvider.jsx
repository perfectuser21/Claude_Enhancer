/**
 * WebSocket提供者组件
 * 为整个应用提供WebSocket上下文和状态管理
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';

// WebSocket上下文
const WebSocketContext = createContext(null);

// 配置
const WS_CONFIG = {
  url: process.env.REACT_APP_WS_URL || 'ws://localhost:8765',
  debug: process.env.NODE_ENV === 'development'
};

/**
 * WebSocket提供者组件
 */
export const WebSocketProvider = ({ children, userInfo }) => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [onlineUsers, setOnlineUsers] = useState([]);

  // 使用WebSocket Hook
  const ws = useWebSocket({
    url: WS_CONFIG.url,
    debug: WS_CONFIG.debug,
    onMessage: (type, data) => {
      handleGlobalMessage(type, data);
    },
    onConnectionChange: (state) => {
      console.log('WebSocket连接状态变化:', state);
    },
    onError: (error) => {
      console.error('WebSocket错误:', error);
    }
  });

  // 处理全局消息
  const handleGlobalMessage = useCallback((type, data) => {
    switch (type) {
      case 'system_notification':
      case 'project_notification':
        addNotification({
          id: data.notification_id || Date.now().toString(),
          ...data,
          timestamp: new Date(),
          read: false
        });
        break;

      case 'user_online':
        setOnlineUsers(prev => {
          const filtered = prev.filter(user => user.user_id !== data.user_id);
          return [...filtered, { ...data, status: 'online' }];
        });
        break;

      case 'user_offline':
        setOnlineUsers(prev =>
          prev.map(user =>
            user.user_id === data.user_id
              ? { ...user, status: 'offline' }
              : user
          )
        );
        break;

      default:
        // 其他消息类型可以在这里处理
        break;
    }
  }, []);

  // 添加通知
  const addNotification = useCallback((notification) => {
    setNotifications(prev => [notification, ...prev.slice(0, 49)]); // 保留最近50条

    // 自动消失的通知
    if (notification.auto_dismiss && notification.dismiss_timeout) {
      setTimeout(() => {
        removeNotification(notification.id);
      }, notification.dismiss_timeout);
    }
  }, []);

  // 移除通知
  const removeNotification = useCallback((notificationId) => {
    setNotifications(prev => prev.filter(n => n.id !== notificationId));
  }, []);

  // 标记通知为已读
  const markNotificationAsRead = useCallback((notificationId) => {
    setNotifications(prev =>
      prev.map(n =>
        n.id === notificationId ? { ...n, read: true } : n
      )
    );
  }, []);

  // 清除所有通知
  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // 初始化连接
  useEffect(() => {
    if (userInfo && !isInitialized) {
      ws.connect(userInfo)
        .then(() => {
          setIsInitialized(true);
          console.log('WebSocket连接已建立');
        })
        .catch(error => {
          console.error('WebSocket连接失败:', error);
        });
    }

    return () => {
      if (isInitialized) {
        ws.disconnect();
        setIsInitialized(false);
      }
    };
  }, [userInfo, isInitialized, ws]);

  // 提供给子组件的值
  const contextValue = {
    // WebSocket基础功能
    ...ws,
    isInitialized,

    // 通知管理
    notifications,
    unreadNotificationCount: notifications.filter(n => !n.read).length,
    addNotification,
    removeNotification,
    markNotificationAsRead,
    clearAllNotifications,

    // 在线用户
    onlineUsers,
    getOnlineUserCount: () => onlineUsers.filter(u => u.status === 'online').length,

    // 便捷方法
    sendTaskUpdate: (taskData) => {
      ws.send('task_updated', taskData);
    },

    sendUserTyping: (roomId, isTyping = true) => {
      ws.send('user_typing', {
        room_id: roomId,
        typing: isTyping,
        user_id: userInfo?.userId
      });
    },

    joinProjectRoom: (projectId, projectName) => {
      ws.joinRoom(projectId, projectName);
    },

    leaveProjectRoom: (projectId) => {
      ws.leaveRoom(projectId);
    }
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
};

/**
 * 使用WebSocket上下文的Hook
 */
export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext必须在WebSocketProvider内部使用');
  }
  return context;
};

/**
 * 高阶组件：为组件提供WebSocket功能
 */
export const withWebSocket = (Component) => {
  return function WebSocketComponent(props) {
    const webSocket = useWebSocketContext();
    return <Component {...props} webSocket={webSocket} />;
  };
};

export default WebSocketProvider;