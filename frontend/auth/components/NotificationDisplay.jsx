import React from 'react';
import { useGlobalNotification } from '../hooks/useNotification';

const NotificationDisplay = () => {
  const { notifications, removeNotification } = useGlobalNotification();

  if (notifications.length === 0) {
    return null;
  }

  const getIconForType = (type) => {
    switch (type) {
      case 'success':
        return '✅';
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'info':
      default:
        return 'ℹ️';
    }
  };

  const getTypeClass = (type) => {
    return `notification-${type}`;
  };

  return (
    <div className="notification-container">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`notification ${getTypeClass(notification.type)}`}
        >
          <div className="notification-content">
            <div className="notification-icon">
              {getIconForType(notification.type)}
            </div>

            <div className="notification-message">
              {notification.message}
            </div>

            {notification.action && (
              <div className="notification-action">
                <button
                  type="button"
                  className="notification-action-button"
                  onClick={notification.action.handler}
                >
                  {notification.action.label}
                </button>
              </div>
            )}
          </div>

          <button
            type="button"
            className="notification-close"
            onClick={() => removeNotification(notification.id)}
            aria-label="Close notification"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
};

export default NotificationDisplay;