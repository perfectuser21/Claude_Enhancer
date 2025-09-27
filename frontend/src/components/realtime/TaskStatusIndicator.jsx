/**
 * 实时任务状态指示器组件
 * 显示任务的实时状态变化和协作信息
 */

import React, { useState, useEffect, useRef } from 'react';
import { useTaskUpdates } from '../../hooks/useWebSocket';
import './TaskStatusIndicator.css';

const TaskStatusIndicator = ({
  taskId,
  projectId,
  initialStatus = 'todo',
  showCollaborators = true,
  showStatusHistory = false,
  className = ''
}) => {
  const [currentStatus, setCurrentStatus] = useState(initialStatus);
  const [statusHistory, setStatusHistory] = useState([]);
  const [collaborators, setCollaborators] = useState([]);
  const [isUpdating, setIsUpdating] = useState(false);
  const [lastUpdateBy, setLastUpdateBy] = useState(null);
  const updateTimeoutRef = useRef(null);

  const {
    taskUpdates,
    send,
    isConnected,
    joinRoom,
    leaveRoom
  } = useTaskUpdates(projectId);

  // 监听任务更新
  useEffect(() => {
    const relevantUpdates = taskUpdates.filter(update =>
      update.task?.task_id === taskId || update.task?.id === taskId
    );

    if (relevantUpdates.length > 0) {
      const latestUpdate = relevantUpdates[relevantUpdates.length - 1];

      if (latestUpdate.type === 'status_changed') {
        setCurrentStatus(latestUpdate.task.new_status || latestUpdate.task.status);
        setLastUpdateBy(latestUpdate.task.changed_by || latestUpdate.task.updated_by);

        // 添加到状态历史
        setStatusHistory(prev => [...prev, {
          status: latestUpdate.task.new_status || latestUpdate.task.status,
          timestamp: latestUpdate.timestamp,
          user: latestUpdate.task.changed_by || latestUpdate.task.updated_by
        }].slice(-10)); // 保留最近10条

        // 显示更新动画
        setIsUpdating(true);
        if (updateTimeoutRef.current) {
          clearTimeout(updateTimeoutRef.current);
        }
        updateTimeoutRef.current = setTimeout(() => {
          setIsUpdating(false);
        }, 2000);
      }
    }
  }, [taskUpdates, taskId]);

  // 监听协作者变化
  useEffect(() => {
    if (projectId && isConnected) {
      // 监听项目房间的用户变化
      const handleUserJoin = (data) => {
        if (data.room_id === projectId) {
          setCollaborators(prev => {
            const filtered = prev.filter(c => c.user_id !== data.user_id);
            return [...filtered, data];
          });
        }
      };

      const handleUserLeave = (data) => {
        if (data.room_id === projectId) {
          setCollaborators(prev => prev.filter(c => c.user_id !== data.user_id));
        }
      };

      // 这里应该注册事件监听器
      // 实际实现中需要通过WebSocket Hook注册

      return () => {
        // 清理监听器
      };
    }
  }, [projectId, isConnected]);

  // 获取状态显示信息
  const getStatusInfo = (status) => {
    const statusMap = {
      'todo': { label: '待办', color: '#6c757d', icon: '⏸️' },
      'in_progress': { label: '进行中', color: '#007bff', icon: '🔄' },
      'review': { label: '待审查', color: '#ffc107', icon: '👀' },
      'completed': { label: '已完成', color: '#28a745', icon: '✅' },
      'cancelled': { label: '已取消', color: '#dc3545', icon: '❌' }
    };
    return statusMap[status] || { label: status, color: '#6c757d', icon: '❓' };
  };

  // 格式化时间
  const formatTime = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = now - time;

    if (diff < 60000) {
      return '刚刚';
    } else if (diff < 3600000) {
      return `${Math.floor(diff / 60000)}分钟前`;
    } else {
      return time.toLocaleTimeString();
    }
  };

  const statusInfo = getStatusInfo(currentStatus);

  return (
    <div className={`task-status-indicator ${className} ${isUpdating ? 'updating' : ''}`}>
      {/* 主要状态显示 */}
      <div className="status-main">
        <div
          className="status-badge"
          style={{ backgroundColor: statusInfo.color }}
        >
          <span className="status-icon">{statusInfo.icon}</span>
          <span className="status-label">{statusInfo.label}</span>
        </div>

        {/* 连接状态指示器 */}
        <div className={`connection-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
          <span className="connection-dot" />
          <span className="connection-text">
            {isConnected ? '实时' : '离线'}
          </span>
        </div>
      </div>

      {/* 最近更新信息 */}
      {lastUpdateBy && (
        <div className="last-update">
          <span className="update-text">
            由 {lastUpdateBy} 更新
          </span>
          {statusHistory.length > 0 && (
            <span className="update-time">
              {formatTime(statusHistory[statusHistory.length - 1].timestamp)}
            </span>
          )}
        </div>
      )}

      {/* 协作者显示 */}
      {showCollaborators && collaborators.length > 0 && (
        <div className="collaborators">
          <div className="collaborators-label">协作者:</div>
          <div className="collaborators-list">
            {collaborators.slice(0, 3).map(collaborator => (
              <div
                key={collaborator.user_id}
                className="collaborator-avatar"
                title={collaborator.username}
              >
                {collaborator.username?.charAt(0)?.toUpperCase()}
              </div>
            ))}
            {collaborators.length > 3 && (
              <div className="collaborator-more">
                +{collaborators.length - 3}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 状态历史 */}
      {showStatusHistory && statusHistory.length > 0 && (
        <div className="status-history">
          <div className="history-label">状态历史:</div>
          <div className="history-list">
            {statusHistory.slice(-3).map((item, index) => (
              <div key={index} className="history-item">
                <span className="history-status">
                  {getStatusInfo(item.status).label}
                </span>
                <span className="history-time">
                  {formatTime(item.timestamp)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 更新动画 */}
      {isUpdating && (
        <div className="update-animation">
          <div className="update-pulse" />
          <div className="update-text">状态已更新</div>
        </div>
      )}
    </div>
  );
};

export default TaskStatusIndicator;