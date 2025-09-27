// Task Management System Types

// User and Authentication Types
export interface User {
  id: string;
  email: string;
  username: string;
  firstName: string;
  lastName: string;
  avatar?: string;
  role: UserRole;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export type UserRole = 'admin' | 'manager' | 'user';

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
}

// Task Types
export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  assigneeId?: string;
  assignee?: User;
  projectId: string;
  project?: Project;
  tags: string[];
  dueDate?: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  estimatedHours?: number;
  actualHours?: number;
  attachments?: Attachment[];
  comments?: Comment[];
}

export type TaskStatus = 'todo' | 'in_progress' | 'review' | 'done';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface TaskFilter {
  status?: TaskStatus[];
  priority?: TaskPriority[];
  assigneeId?: string[];
  projectId?: string;
  tags?: string[];
  dueDateFrom?: string;
  dueDateTo?: string;
  search?: string;
}

export interface TaskSort {
  field: 'title' | 'status' | 'priority' | 'dueDate' | 'createdAt' | 'updatedAt';
  direction: 'asc' | 'desc';
}

// Project Types
export interface Project {
  id: string;
  name: string;
  description?: string;
  color: string;
  status: ProjectStatus;
  ownerId: string;
  owner?: User;
  memberIds: string[];
  members?: User[];
  createdAt: string;
  updatedAt: string;
  deadline?: string;
  progress: number;
}

export type ProjectStatus = 'active' | 'completed' | 'archived' | 'on_hold';

// Comment Types
export interface Comment {
  id: string;
  content: string;
  taskId: string;
  authorId: string;
  author?: User;
  createdAt: string;
  updatedAt: string;
}

// Attachment Types
export interface Attachment {
  id: string;
  filename: string;
  originalName: string;
  mimeType: string;
  size: number;
  taskId: string;
  uploadedBy: string;
  uploadedAt: string;
  url: string;
}

// Notification Types
export interface Notification {
  id: string;
  title: string;
  message: string;
  type: NotificationType;
  isRead: boolean;
  userId: string;
  relatedEntityId?: string;
  relatedEntityType?: string;
  createdAt: string;
}

export type NotificationType = 'info' | 'success' | 'warning' | 'error' | 'task_assigned' | 'task_completed' | 'project_update';

// UI State Types
export interface UIState {
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
  currentView: ViewType;
  kanbanColumns: KanbanColumn[];
  isLoading: boolean;
  error: string | null;
}

export type ViewType = 'kanban' | 'list' | 'calendar' | 'timeline';

export interface KanbanColumn {
  id: string;
  title: string;
  status: TaskStatus;
  taskIds: string[];
  limit?: number;
  color: string;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  totalCount: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

// Form Types
export interface TaskFormData {
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  assigneeId?: string;
  projectId: string;
  tags: string[];
  dueDate?: string;
  estimatedHours?: number;
}

export interface ProjectFormData {
  name: string;
  description?: string;
  color: string;
  memberIds: string[];
  deadline?: string;
}

// Store State Types
export interface TaskStore {
  tasks: Task[];
  selectedTask: Task | null;
  filter: TaskFilter;
  sort: TaskSort;
  isLoading: boolean;
  error: string | null;

  // Actions
  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (id: string, updates: Partial<Task>) => void;
  deleteTask: (id: string) => void;
  setSelectedTask: (task: Task | null) => void;
  setFilter: (filter: Partial<TaskFilter>) => void;
  setSort: (sort: TaskSort) => void;
  clearFilter: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export interface UIStore {
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
  currentView: ViewType;
  kanbanColumns: KanbanColumn[];
  notifications: Notification[];

  // Actions
  toggleTheme: () => void;
  toggleSidebar: () => void;
  setCurrentView: (view: ViewType) => void;
  updateKanbanColumn: (columnId: string, updates: Partial<KanbanColumn>) => void;
  addNotification: (notification: Omit<Notification, 'id' | 'createdAt'>) => void;
  markNotificationRead: (id: string) => void;
  clearNotifications: () => void;
}

// Event Types
export interface DragDropResult {
  draggableId: string;
  type: string;
  source: {
    droppableId: string;
    index: number;
  };
  destination?: {
    droppableId: string;
    index: number;
  };
}

// Hook Return Types
export interface UseTasksReturn {
  tasks: Task[];
  loading: boolean;
  error: string | null;
  createTask: (data: TaskFormData) => Promise<void>;
  updateTask: (id: string, data: Partial<TaskFormData>) => Promise<void>;
  deleteTask: (id: string) => Promise<void>;
  refreshTasks: () => Promise<void>;
}

export interface UseProjectsReturn {
  projects: Project[];
  loading: boolean;
  error: string | null;
  createProject: (data: ProjectFormData) => Promise<void>;
  updateProject: (id: string, data: Partial<ProjectFormData>) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  refreshProjects: () => Promise<void>;
}

// Component Props Types
export interface TaskCardProps {
  task: Task;
  onEdit?: (task: Task) => void;
  onDelete?: (id: string) => void;
  onStatusChange?: (id: string, status: TaskStatus) => void;
  isDragging?: boolean;
}

export interface KanbanColumnProps {
  column: KanbanColumn;
  tasks: Task[];
  onTaskMove?: (taskId: string, newStatus: TaskStatus) => void;
}

export interface TaskListProps {
  tasks: Task[];
  loading?: boolean;
  onTaskSelect?: (task: Task) => void;
  onTaskUpdate?: (id: string, updates: Partial<Task>) => void;
  onTaskDelete?: (id: string) => void;
}