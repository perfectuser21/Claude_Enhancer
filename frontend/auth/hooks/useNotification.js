import { useState, useCallback, useRef, useEffect } from 'react';

// Hook for managing notifications
export const useNotification = () => {
  const [notifications, setNotifications] = useState([]);
  const timeoutsRef = useRef({});

  // Generate unique ID for notifications
  const generateId = useCallback(() => {
    return `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Show notification
  const showNotification = useCallback((message, type = 'info', duration = 5000, options = {}) => {
    const id = generateId();

    const notification = {
      id,
      message,
      type, // 'success', 'error', 'warning', 'info'
      duration,
      timestamp: Date.now(),
      persistent: options.persistent || false,
      action: options.action || null,
      ...options
    };

    setNotifications(prev => [...prev, notification]);

    // Auto-remove notification after duration (unless persistent)
    if (!notification.persistent && duration > 0) {
      timeoutsRef.current[id] = setTimeout(() => {
        removeNotification(id);
      }, duration);
    }

    return id;
  }, [generateId]);

  // Remove notification
  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));

    // Clear timeout if exists
    if (timeoutsRef.current[id]) {
      clearTimeout(timeoutsRef.current[id]);
      delete timeoutsRef.current[id];
    }
  }, []);

  // Clear all notifications
  const clearAllNotifications = useCallback(() => {
    setNotifications([]);

    // Clear all timeouts
    Object.values(timeoutsRef.current).forEach(clearTimeout);
    timeoutsRef.current = {};
  }, []);

  // Shorthand methods for different types
  const showSuccess = useCallback((message, duration, options) => {
    return showNotification(message, 'success', duration, options);
  }, [showNotification]);

  const showError = useCallback((message, duration = 8000, options) => {
    return showNotification(message, 'error', duration, options);
  }, [showNotification]);

  const showWarning = useCallback((message, duration, options) => {
    return showNotification(message, 'warning', duration, options);
  }, [showNotification]);

  const showInfo = useCallback((message, duration, options) => {
    return showNotification(message, 'info', duration, options);
  }, [showNotification]);

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      Object.values(timeoutsRef.current).forEach(clearTimeout);
    };
  }, []);

  return {
    notifications,
    showNotification,
    removeNotification,
    clearAllNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo
  };
};

// Notification provider context for global notifications
import React, { createContext, useContext } from 'react';

const NotificationContext = createContext();

export const NotificationProvider = ({ children }) => {
  const notification = useNotification();

  return (
    <NotificationContext.Provider value={notification}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useGlobalNotification = () => {
  const context = useContext(NotificationContext);

  if (!context) {
    throw new Error('useGlobalNotification must be used within a NotificationProvider');
  }

  return context;
};