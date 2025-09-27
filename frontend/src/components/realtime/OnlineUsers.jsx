/**
 * 在线用户组件
 * 显示当前在线用户列表和状态
 */

import React, { useState, useEffect } from 'react';
import { useOnlineUsers } from '../../hooks/useWebSocket';
import './OnlineUsers.css';

const OnlineUsers = ({ roomId, projectName, className = '' }) => {
  const {
    onlineUsers,
    userStatuses,
    getUserStatus,
    isConnected
  } = useOnlineUsers(roomId);

  const [isExpanded, setIsExpanded] = useState(false);
  const [hoveredUser, setHoveredUser] = useState(null);

  // 用户头像获取
  const getUserAvatar = (user) => {
    if (user.avatar_url) {
      return user.avatar_url;
    }
    // 生成默认头像（使用用户名首字母）
    const initial = user.username?.charAt(0)?.toUpperCase() || '?';
    return `data:image/svg+xml;base64,${btoa(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
        <circle cx="20" cy="20" r="20" fill="#007bff"/>
        <text x="20" y="26" font-family="Arial" font-size="16" fill="white" text-anchor="middle">${initial}</text>
      </svg>
    `)}`;
  };

  // 获取用户状态点的颜色
  const getStatusColor = (userId) => {
    const status = getUserStatus(userId);
    switch (status) {
      case 'online':
        return '#4caf50';
      case 'away':
        return '#ff9800';
      case 'busy':
        return '#f44336';
      default:
        return '#9e9e9e';
    }
  };

  // 格式化最后在线时间
  const formatLastSeen = (lastSeen) => {
    if (!lastSeen) return '未知';

    const now = new Date();
    const time = new Date(lastSeen);
    const diff = now - time;

    if (diff < 60000) {
      return '刚刚在线';
    } else if (diff < 3600000) {
      return `${Math.floor(diff / 60000)}分钟前在线`;
    } else if (diff < 86400000) {
      return `${Math.floor(diff / 3600000)}小时前在线`;
    } else {
      return time.toLocaleDateString();
    }
  };

  const totalUsers = onlineUsers.length;
  const displayUsers = isExpanded ? onlineUsers : onlineUsers.slice(0, 5);

  return (
    <div className={`online-users ${className}`}>
      {/* 头部 */}
      <div className="online-users-header">
        <div className="header-info">
          <h4>
            {projectName ? `${projectName} - 在线成员` : '在线用户'}
          </h4>
          <span className="user-count">
            {totalUsers} 人在线
          </span>
        </div>

        <div className="connection-indicator">
          <span
            className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}
            title={isConnected ? '实时连接正常' : '连接已断开'}
          />
        </div>
      </div>

      {/* 用户列表 */}
      <div className="users-list">
        {totalUsers === 0 ? (
          <div className="no-users">
            <div className="no-users-icon">👥</div>
            <p>暂无在线用户</p>
          </div>
        ) : (
          <>
            {displayUsers.map(user => (
              <div
                key={user.user_id}
                className="user-item"
                onMouseEnter={() => setHoveredUser(user.user_id)}
                onMouseLeave={() => setHoveredUser(null)}
              >
                <div className="user-avatar-container">
                  <img
                    src={getUserAvatar(user)}
                    alt={user.username}
                    className="user-avatar"
                    onError={(e) => {
                      e.target.src = getUserAvatar({ username: user.username });
                    }}
                  />
                  <div
                    className="status-indicator"
                    style={{ backgroundColor: getStatusColor(user.user_id) }}
                  />
                </div>

                <div className="user-info">
                  <div className="user-name">
                    {user.username}
                  </div>
                  <div className="user-status">
                    {getUserStatus(user.user_id) === 'online' ? '在线' : formatLastSeen(user.last_seen)}
                  </div>
                </div>

                {/* 悬停时显示的详细信息 */}
                {hoveredUser === user.user_id && (
                  <div className="user-tooltip">
                    <div className="tooltip-content">
                      <h5>{user.username}</h5>
                      <p>状态: {getUserStatus(user.user_id)}</p>
                      {user.current_project && (
                        <p>当前项目: {user.current_project}</p>
                      )}
                      <p>加入时间: {formatLastSeen(user.connected_at)}</p>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* 展开/收起按钮 */}
            {totalUsers > 5 && (
              <button
                className="expand-button"
                onClick={() => setIsExpanded(!isExpanded)}
              >
                {isExpanded
                  ? `收起 (${totalUsers - 5} 更多)`
                  : `展开 (${totalUsers - 5} 更多)`
                }
              </button>
            )}
          </>
        )}
      </div>

      {/* 底部统计 */}
      {totalUsers > 0 && (
        <div className="users-stats">
          <div className="stat-item">
            <span className="stat-label">总计:</span>
            <span className="stat-value">{totalUsers}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">在线:</span>
            <span className="stat-value">
              {Object.values(userStatuses).filter(status => status === 'online').length}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default OnlineUsers;