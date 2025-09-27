import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UIStore, ViewType, KanbanColumn, Notification } from '../types';

const defaultKanbanColumns: KanbanColumn[] = [
  {
    id: 'todo',
    title: 'To Do',
    status: 'todo',
    taskIds: [],
    color: '#4A5568',
  },
  {
    id: 'in_progress',
    title: 'In Progress',
    status: 'in_progress',
    taskIds: [],
    limit: 3,
    color: '#3182CE',
  },
  {
    id: 'review',
    title: 'Review',
    status: 'review',
    taskIds: [],
    limit: 5,
    color: '#D69E2E',
  },
  {
    id: 'done',
    title: 'Done',
    status: 'done',
    taskIds: [],
    color: '#38A169',
  },
];

export const useUIStore = create<UIStore>()(
  persist(
    (set, get) => ({
      theme: 'light',
      sidebarCollapsed: false,
      currentView: 'kanban',
      kanbanColumns: defaultKanbanColumns,
      notifications: [],

      toggleTheme: () => {
        set(
          (state) => ({
            theme: state.theme === 'light' ? 'dark' : 'light',
          }),
          false,
          'toggleTheme'
        );
      },

      toggleSidebar: () => {
        set(
          (state) => ({
            sidebarCollapsed: !state.sidebarCollapsed,
          }),
          false,
          'toggleSidebar'
        );
      },

      setCurrentView: (view: ViewType) => {
        set({ currentView: view }, false, 'setCurrentView');
      },

      updateKanbanColumn: (columnId: string, updates: Partial<KanbanColumn>) => {
        set(
          (state) => ({
            kanbanColumns: state.kanbanColumns.map((column) =>
              column.id === columnId ? { ...column, ...updates } : column
            ),
          }),
          false,
          'updateKanbanColumn'
        );
      },

      addNotification: (notification: Omit<Notification, 'id' | 'createdAt'>) => {
        const newNotification: Notification = {
          ...notification,
          id: `notification-${Date.now()}-${Math.random()}`,
          createdAt: new Date().toISOString(),
        };

        set(
          (state) => ({
            notifications: [newNotification, ...state.notifications].slice(0, 50), // Keep only latest 50
          }),
          false,
          'addNotification'
        );

        // Auto-remove non-error notifications after 5 seconds
        if (notification.type !== 'error') {
          setTimeout(() => {
            const currentNotifications = get().notifications;
            const updatedNotifications = currentNotifications.filter(
              (n) => n.id !== newNotification.id
            );
            set({ notifications: updatedNotifications });
          }, 5000);
        }
      },

      markNotificationRead: (id: string) => {
        set(
          (state) => ({
            notifications: state.notifications.map((notification) =>
              notification.id === id ? { ...notification, isRead: true } : notification
            ),
          }),
          false,
          'markNotificationRead'
        );
      },

      clearNotifications: () => {
        set({ notifications: [] }, false, 'clearNotifications');
      },
    }),
    {
      name: 'ui-storage',
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        currentView: state.currentView,
        kanbanColumns: state.kanbanColumns,
      }),
    }
  )
);

// UI utility functions
export const uiUtils = {
  // Show success notification
  showSuccess: (title: string, message?: string) => {
    useUIStore.getState().addNotification({
      title,
      message: message || '',
      type: 'success',
      isRead: false,
      userId: '', // Will be set by the app when user is available
    });
  },

  // Show error notification
  showError: (title: string, message?: string) => {
    useUIStore.getState().addNotification({
      title,
      message: message || '',
      type: 'error',
      isRead: false,
      userId: '',
    });
  },

  // Show warning notification
  showWarning: (title: string, message?: string) => {
    useUIStore.getState().addNotification({
      title,
      message: message || '',
      type: 'warning',
      isRead: false,
      userId: '',
    });
  },

  // Show info notification
  showInfo: (title: string, message?: string) => {
    useUIStore.getState().addNotification({
      title,
      message: message || '',
      type: 'info',
      isRead: false,
      userId: '',
    });
  },

  // Get theme colors based on current theme
  getThemeColors: () => {
    const { theme } = useUIStore.getState();

    if (theme === 'dark') {
      return {
        bg: 'gray.800',
        cardBg: 'gray.700',
        border: 'gray.600',
        text: 'white',
        secondaryText: 'gray.300',
        accent: 'blue.400',
        success: 'green.400',
        warning: 'yellow.400',
        error: 'red.400',
      };
    } else {
      return {
        bg: 'gray.50',
        cardBg: 'white',
        border: 'gray.200',
        text: 'gray.800',
        secondaryText: 'gray.600',
        accent: 'blue.500',
        success: 'green.500',
        warning: 'yellow.500',
        error: 'red.500',
      };
    }
  },

  // Check if any notifications are unread
  hasUnreadNotifications: () => {
    const { notifications } = useUIStore.getState();
    return notifications.some(notification => !notification.isRead);
  },

  // Get unread notifications count
  getUnreadCount: () => {
    const { notifications } = useUIStore.getState();
    return notifications.filter(notification => !notification.isRead).length;
  },

  // Format view display name
  getViewDisplayName: (view: ViewType) => {
    const viewNames = {
      kanban: 'Kanban Board',
      list: 'List View',
      calendar: 'Calendar View',
      timeline: 'Timeline View',
    };
    return viewNames[view] || view;
  },

  // Get column by status
  getColumnByStatus: (status: string) => {
    const { kanbanColumns } = useUIStore.getState();
    return kanbanColumns.find(column => column.status === status);
  },

  // Update column task IDs
  updateColumnTaskIds: (columnId: string, taskIds: string[]) => {
    useUIStore.getState().updateKanbanColumn(columnId, { taskIds });
  },

  // Get all column task IDs
  getAllColumnTaskIds: () => {
    const { kanbanColumns } = useUIStore.getState();
    return kanbanColumns.reduce((acc, column) => {
      acc[column.status] = column.taskIds;
      return acc;
    }, {} as Record<string, string[]>);
  },
};

// Selectors for computed UI state
export const uiSelectors = {
  // Check if sidebar should be shown on mobile
  shouldShowSidebar: () => {
    const { sidebarCollapsed } = useUIStore.getState();
    return !sidebarCollapsed;
  },

  // Get active notifications (unread or recent)
  getActiveNotifications: () => {
    const { notifications } = useUIStore.getState();
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

    return notifications.filter(notification =>
      !notification.isRead || new Date(notification.createdAt) > oneHourAgo
    );
  },

  // Get priority notifications (errors and warnings)
  getPriorityNotifications: () => {
    const { notifications } = useUIStore.getState();
    return notifications.filter(notification =>
      (notification.type === 'error' || notification.type === 'warning') && !notification.isRead
    );
  },

  // Check if current view supports certain features
  getCurrentViewCapabilities: () => {
    const { currentView } = useUIStore.getState();

    return {
      supportsDragDrop: currentView === 'kanban',
      supportsFiltering: true,
      supportsSorting: currentView === 'list',
      supportsGrouping: currentView === 'kanban' || currentView === 'list',
      supportsDateNavigation: currentView === 'calendar' || currentView === 'timeline',
    };
  },
};