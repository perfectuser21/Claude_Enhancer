import { useCallback } from 'react';
import { useTaskStore, taskActions } from '../store';
import { useUIStore, uiUtils } from '../store/uiStore';
import { TaskStatus } from '../types';

export const useKanban = () => {
  const { tasks, isLoading, error } = useTaskStore();
  const { kanbanColumns } = useUIStore();

  const moveTask = useCallback(async (taskId: string, newStatus: TaskStatus) => {
    try {
      // Optimistic update
      const task = tasks.find(t => t.id === taskId);
      if (!task) {
        throw new Error('Task not found');
      }

      const oldStatus = task.status;

      // Update task status locally first for immediate feedback
      useTaskStore.getState().updateTask(taskId, { status: newStatus });

      try {
        // Update on server
        await taskActions.updateTaskStatus(taskId, newStatus);

        uiUtils.showSuccess(
          'Task moved',
          `"${task.title}" moved from ${oldStatus} to ${newStatus}`
        );
      } catch (error) {
        // Revert on failure
        useTaskStore.getState().updateTask(taskId, { status: oldStatus });
        throw error;
      }
    } catch (error: any) {
      uiUtils.showError('Failed to move task', error.message);
      throw error;
    }
  }, [tasks]);

  const getTasksByStatus = useCallback(() => {
    const tasksByStatus: Record<TaskStatus, typeof tasks> = {
      todo: [],
      in_progress: [],
      review: [],
      done: [],
    };

    tasks.forEach(task => {
      if (tasksByStatus[task.status]) {
        tasksByStatus[task.status].push(task);
      }
    });

    return tasksByStatus;
  }, [tasks]);

  const getColumnStats = useCallback(() => {
    const tasksByStatus = getTasksByStatus();

    return kanbanColumns.map(column => {
      const columnTasks = tasksByStatus[column.status] || [];
      const isOverLimit = column.limit && columnTasks.length > column.limit;

      return {
        ...column,
        taskCount: columnTasks.length,
        isOverLimit,
        tasks: columnTasks,
      };
    });
  }, [kanbanColumns, getTasksByStatus]);

  return {
    tasks,
    columns: kanbanColumns,
    columnStats: getColumnStats(),
    loading: isLoading,
    error,
    moveTask,
    getTasksByStatus,
  };
};