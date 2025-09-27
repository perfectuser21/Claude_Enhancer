import { useCallback, useEffect } from 'react';
import { useTaskStore, taskActions, taskSelectors } from '../store';
import { TaskFormData, UseTasksReturn } from '../types';
import { uiUtils } from '../store/uiStore';

export const useTasks = (): UseTasksReturn => {
  const {
    tasks,
    isLoading,
    error,
    filter,
    sort,
  } = useTaskStore();

  // Load tasks on mount
  useEffect(() => {
    taskActions.fetchTasks(filter, sort).catch((error) => {
      uiUtils.showError('Failed to load tasks', error.message);
    });
  }, [filter, sort]);

  const createTask = useCallback(async (data: TaskFormData) => {
    try {
      const newTask = await taskActions.createTask(data);
      uiUtils.showSuccess('Task created successfully', `"${newTask.title}" has been created.`);
    } catch (error: any) {
      uiUtils.showError('Failed to create task', error.message);
      throw error;
    }
  }, []);

  const updateTask = useCallback(async (id: string, data: Partial<TaskFormData>) => {
    try {
      const updatedTask = await taskActions.updateTask(id, data);
      uiUtils.showSuccess('Task updated successfully', `"${updatedTask.title}" has been updated.`);
    } catch (error: any) {
      uiUtils.showError('Failed to update task', error.message);
      throw error;
    }
  }, []);

  const deleteTask = useCallback(async (id: string) => {
    try {
      const taskToDelete = tasks.find(task => task.id === id);
      await taskActions.deleteTask(id);
      uiUtils.showSuccess(
        'Task deleted successfully',
        taskToDelete ? `"${taskToDelete.title}" has been deleted.` : 'Task has been deleted.'
      );
    } catch (error: any) {
      uiUtils.showError('Failed to delete task', error.message);
      throw error;
    }
  }, [tasks]);

  const refreshTasks = useCallback(async () => {
    try {
      await taskActions.fetchTasks(filter, sort);
    } catch (error: any) {
      uiUtils.showError('Failed to refresh tasks', error.message);
      throw error;
    }
  }, [filter, sort]);

  return {
    tasks: taskSelectors.getFilteredTasks(),
    loading: isLoading,
    error,
    createTask,
    updateTask,
    deleteTask,
    refreshTasks,
  };
};