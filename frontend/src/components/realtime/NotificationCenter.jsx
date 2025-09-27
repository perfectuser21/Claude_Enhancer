/**
 * 实时通知中心组件
 * 显示系统通知、任务更新、协作提醒等
 */

import React, { useState, useEffect } from 'react';
import { useNotifications } from '../../hooks/useWebSocket';
import './NotificationCenter.css';

const NotificationCenter = ({ isOpen, onToggle, onClose }) => {
  const {
    notifications,
    unreadCount,
    markAsRead,
    removeNotification,
    clearAll,
    isConnected
  } = useNotifications();

  const [filter, setFilter] = useState('all'); // all, unread, system, task

  // 过滤通知
  const filteredNotifications = notifications.filter(notification => {
    switch (filter) {
      case 'unread':
        return !notification.read;
      case 'system':
        return notification.type === 'system';
      case 'task':
        return notification.type === 'task' || notification.type === 'project';
      default:
        return true;
    }
  });

  // 获取通知图标
  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success':
        return '✅';
      case 'warning':
        return '⚠️';
      case 'error':
        return '❌';
      case 'info':
      default:
        return 'ℹ️';
    }
  };

  // 获取通知样式类
  const getNotificationClass = (notification) => {
    const classes = ['notification-item'];

    if (!notification.read) {
      classes.push('unread');
    }

    classes.push(`notification-${notification.type}`);

    return classes.join(' ');
  };

  // 处理通知点击
  const handleNotificationClick = (notification) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }

    // 如果有操作URL，跳转到对应页面
    if (notification.action_url) {
      window.location.href = notification.action_url;
    }
  };

  // 格式化时间
  const formatTime = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = now - time;

    if (diff < 60000) { // 1分钟内
      return '刚刚';
    } else if (diff < 3600000) { // 1小时内
      return `${Math.floor(diff / 60000)}分钟前`;
    } else if (diff < 86400000) { // 24小时内
      return `${Math.floor(diff / 3600000)}小时前`;
    } else {
      return time.toLocaleDateString();
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="notification-center">
      <div className="notification-overlay" onClick={onClose} />

      <div className="notification-panel">
        {/* 头部 */}
        <div className="notification-header">
          <h3>通知中心</h3>
          <div className="notification-header-actions">
            <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
              {isConnected ? '🟢 已连接' : '🔴 未连接'}
            </span>
            <button
              className="close-button"
              onClick={onClose}
              aria-label="关闭通知中心"
            >
              ✕
            </button>
          </div>
        </div>

        {/* 过滤器 */}
        <div className="notification-filters">
          <button
            className={filter === 'all' ? 'active' : ''}
            onClick={() => setFilter('all')}
          >
            全部 ({notifications.length})
          </button>
          <button
            className={filter === 'unread' ? 'active' : ''}
            onClick={() => setFilter('unread')}
          >
            未读 ({unreadCount})
          </button>
          <button
            className={filter === 'system' ? 'active' : ''}
            onClick={() => setFilter('system')}
          >
            系统
          </button>
          <button
            className={filter === 'task' ? 'active' : ''}
            onClick={() => setFilter('task')}
          >
            任务
          </button>
        </div>

        {/* 操作按钮 */}
        {notifications.length > 0 && (
          <div className="notification-actions">
            <button
              className="clear-all-button"
              onClick={clearAll}
            >
              清空所有
            </button>
          </div>
        )}

        {/* 通知列表 */}
        <div className="notification-list">
          {filteredNotifications.length === 0 ? (
            <div className="no-notifications">
              <div className="no-notifications-icon">🔔</div>
              <p>
                {filter === 'unread' ? '没有未读通知' : '暂无通知'}
              </p>
            </div>
          ) : (
            filteredNotifications.map(notification => (
              <div
                key={notification.id}
                className={getNotificationClass(notification)}
                onClick={() => handleNotificationClick(notification)}
              >
                <div className="notification-icon">
                  {getNotificationIcon(notification.type)}
                </div>

                <div className="notification-content">
                  <div className="notification-title">
                    {notification.title}
                  </div>
                  <div className="notification-message">
                    {notification.message}
                  </div>
                  <div className="notification-time">
                    {formatTime(notification.timestamp)}
                  </div>
                </div>

                <div className="notification-actions">
                  {!notification.read && (
                    <button
                      className="mark-read-button"
                      onClick={(e) => {
                        e.stopPropagation();
                        markAsRead(notification.id);
                      }}
                      title="标记为已读"
                    >
                      ✓
                    </button>
                  )}
                  <button
                    className="remove-button"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeNotification(notification.id);
                    }}
                    title="删除通知"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default NotificationCenter;