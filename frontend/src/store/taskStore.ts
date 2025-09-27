import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import axios from 'axios';
import { TaskStore, Task, TaskFilter, TaskSort, TaskFormData, ApiResponse, PaginatedResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const initialFilter: TaskFilter = {
  status: [],
  priority: [],
  assigneeId: [],
  tags: [],
  search: '',
};

const initialSort: TaskSort = {
  field: 'createdAt',
  direction: 'desc',
};

export const useTaskStore = create<TaskStore>()(
  devtools(
    (set, get) => ({
      tasks: [],
      selectedTask: null,
      filter: initialFilter,
      sort: initialSort,
      isLoading: false,
      error: null,

      setTasks: (tasks: Task[]) => {
        set({ tasks }, false, 'setTasks');
      },

      addTask: (task: Task) => {
        set(
          (state) => ({
            tasks: [task, ...state.tasks],
          }),
          false,
          'addTask'
        );
      },

      updateTask: (id: string, updates: Partial<Task>) => {
        set(
          (state) => ({
            tasks: state.tasks.map((task) =>
              task.id === id ? { ...task, ...updates, updatedAt: new Date().toISOString() } : task
            ),
            selectedTask: state.selectedTask?.id === id
              ? { ...state.selectedTask, ...updates, updatedAt: new Date().toISOString() }
              : state.selectedTask,
          }),
          false,
          'updateTask'
        );
      },

      deleteTask: (id: string) => {
        set(
          (state) => ({
            tasks: state.tasks.filter((task) => task.id !== id),
            selectedTask: state.selectedTask?.id === id ? null : state.selectedTask,
          }),
          false,
          'deleteTask'
        );
      },

      setSelectedTask: (task: Task | null) => {
        set({ selectedTask: task }, false, 'setSelectedTask');
      },

      setFilter: (filter: Partial<TaskFilter>) => {
        set(
          (state) => ({
            filter: { ...state.filter, ...filter },
          }),
          false,
          'setFilter'
        );
      },

      setSort: (sort: TaskSort) => {
        set({ sort }, false, 'setSort');
      },

      clearFilter: () => {
        set({ filter: initialFilter }, false, 'clearFilter');
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading }, false, 'setLoading');
      },

      setError: (error: string | null) => {
        set({ error }, false, 'setError');
      },
    }),
    {
      name: 'task-store',
    }
  )
);

// Task API actions
export const taskActions = {
  // Fetch tasks with filtering and sorting
  fetchTasks: async (filter?: TaskFilter, sort?: TaskSort, page = 1, pageSize = 50) => {
    const { setLoading, setError, setTasks } = useTaskStore.getState();

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();

      if (filter) {
        if (filter.status?.length) params.append('status', filter.status.join(','));
        if (filter.priority?.length) params.append('priority', filter.priority.join(','));
        if (filter.assigneeId?.length) params.append('assigneeId', filter.assigneeId.join(','));
        if (filter.projectId) params.append('projectId', filter.projectId);
        if (filter.tags?.length) params.append('tags', filter.tags.join(','));
        if (filter.search) params.append('search', filter.search);
        if (filter.dueDateFrom) params.append('dueDateFrom', filter.dueDateFrom);
        if (filter.dueDateTo) params.append('dueDateTo', filter.dueDateTo);
      }

      if (sort) {
        params.append('sortBy', sort.field);
        params.append('sortOrder', sort.direction);
      }

      params.append('page', page.toString());
      params.append('pageSize', pageSize.toString());

      const response = await axios.get<PaginatedResponse<Task>>(
        `${API_BASE_URL}/tasks?${params.toString()}`
      );

      setTasks(response.data.data);
      setLoading(false);
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Failed to fetch tasks';
      setError(errorMessage);
      setLoading(false);
      throw new Error(errorMessage);
    }
  },

  // Create new task
  createTask: async (taskData: TaskFormData) => {
    const { setLoading, setError, addTask } = useTaskStore.getState();

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post<ApiResponse<Task>>(
        `${API_BASE_URL}/tasks`,
        taskData
      );

      const newTask = response.data.data;
      addTask(newTask);
      setLoading(false);

      return newTask;
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Failed to create task';
      setError(errorMessage);
      setLoading(false);
      throw new Error(errorMessage);
    }
  },

  // Update existing task
  updateTask: async (id: string, updates: Partial<TaskFormData>) => {
    const { setLoading, setError, updateTask } = useTaskStore.getState();

    setLoading(true);
    setError(null);

    try {
      const response = await axios.patch<ApiResponse<Task>>(
        `${API_BASE_URL}/tasks/${id}`,
        updates
      );

      const updatedTask = response.data.data;
      updateTask(id, updatedTask);
      setLoading(false);

      return updatedTask;
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Failed to update task';
      setError(errorMessage);
      setLoading(false);
      throw new Error(errorMessage);
    }
  },

  // Delete task
  deleteTask: async (id: string) => {
    const { setLoading, setError, deleteTask } = useTaskStore.getState();

    setLoading(true);
    setError(null);

    try {
      await axios.delete(`${API_BASE_URL}/tasks/${id}`);

      deleteTask(id);
      setLoading(false);
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Failed to delete task';
      setError(errorMessage);
      setLoading(false);
      throw new Error(errorMessage);
    }
  },

  // Get task by ID
  getTask: async (id: string) => {
    const { setLoading, setError, setSelectedTask } = useTaskStore.getState();

    setLoading(true);
    setError(null);

    try {
      const response = await axios.get<ApiResponse<Task>>(
        `${API_BASE_URL}/tasks/${id}`
      );

      const task = response.data.data;
      setSelectedTask(task);
      setLoading(false);

      return task;
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Failed to fetch task';
      setError(errorMessage);
      setLoading(false);
      throw new Error(errorMessage);
    }
  },

  // Update task status (for drag & drop)
  updateTaskStatus: async (id: string, status: string) => {
    const { updateTask } = useTaskStore.getState();

    try {
      const response = await axios.patch<ApiResponse<Task>>(
        `${API_BASE_URL}/tasks/${id}/status`,
        { status }
      );

      const updatedTask = response.data.data;
      updateTask(id, updatedTask);

      return updatedTask;
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Failed to update task status';
      throw new Error(errorMessage);
    }
  },
};

// Selectors for computed values
export const taskSelectors = {
  // Get filtered and sorted tasks
  getFilteredTasks: () => {
    const { tasks, filter, sort } = useTaskStore.getState();

    let filteredTasks = [...tasks];

    // Apply filters
    if (filter.status?.length) {
      filteredTasks = filteredTasks.filter(task => filter.status!.includes(task.status));
    }

    if (filter.priority?.length) {
      filteredTasks = filteredTasks.filter(task => filter.priority!.includes(task.priority));
    }

    if (filter.assigneeId?.length) {
      filteredTasks = filteredTasks.filter(task =>
        task.assigneeId && filter.assigneeId!.includes(task.assigneeId)
      );
    }

    if (filter.projectId) {
      filteredTasks = filteredTasks.filter(task => task.projectId === filter.projectId);
    }

    if (filter.tags?.length) {
      filteredTasks = filteredTasks.filter(task =>
        filter.tags!.some(tag => task.tags.includes(tag))
      );
    }

    if (filter.search) {
      const searchLower = filter.search.toLowerCase();
      filteredTasks = filteredTasks.filter(task =>
        task.title.toLowerCase().includes(searchLower) ||
        task.description?.toLowerCase().includes(searchLower)
      );
    }

    // Apply sorting
    filteredTasks.sort((a, b) => {
      const aValue = a[sort.field];
      const bValue = b[sort.field];

      if (aValue < bValue) return sort.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sort.direction === 'asc' ? 1 : -1;
      return 0;
    });

    return filteredTasks;
  },

  // Get tasks by status for Kanban board
  getTasksByStatus: () => {
    const { tasks } = useTaskStore.getState();
    const filteredTasks = taskSelectors.getFilteredTasks();

    return {
      todo: filteredTasks.filter(task => task.status === 'todo'),
      in_progress: filteredTasks.filter(task => task.status === 'in_progress'),
      review: filteredTasks.filter(task => task.status === 'review'),
      done: filteredTasks.filter(task => task.status === 'done'),
    };
  },

  // Get task statistics
  getTaskStats: () => {
    const { tasks } = useTaskStore.getState();

    return {
      total: tasks.length,
      todo: tasks.filter(task => task.status === 'todo').length,
      in_progress: tasks.filter(task => task.status === 'in_progress').length,
      review: tasks.filter(task => task.status === 'review').length,
      done: tasks.filter(task => task.status === 'done').length,
      overdue: tasks.filter(task =>
        task.dueDate && new Date(task.dueDate) < new Date() && task.status !== 'done'
      ).length,
    };
  },
};