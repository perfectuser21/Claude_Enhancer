# TaskFlow Pro - React Frontend

现代化任务管理系统的React前端，基于React 18 + TypeScript + Chakra UI构建。

## 🚀 功能特性

### 核心功能
- **用户认证** - 完整的登录/注册系统，支持JWT认证
- **任务管理** - 创建、编辑、删除和状态管理
- **看板视图** - 拖拽式Kanban面板，支持任务状态切换
- **列表视图** - 传统列表视图，支持排序和筛选
- **实时更新** - 基于Zustand的状态管理，实时同步

### UI/UX特性
- **响应式设计** - 完美适配桌面和移动设备
- **暗色模式** - 支持明暗主题切换
- **无障碍支持** - 完整的键盘导航和屏幕阅读器支持
- **流畅动画** - 基于Framer Motion的平滑过渡效果

## 🛠️ 技术栈

| 类别 | 技术选择 | 版本 | 说明 |
|------|----------|------|------|
| **框架** | React | 18.2.0 | 现代React with Hooks |
| **语言** | TypeScript | 4.9.0 | 类型安全 |
| **状态管理** | Zustand | 4.4.0 | 轻量级状态管理 |
| **UI组件** | Chakra UI | 2.8.0 | 模块化UI组件库 |
| **表单处理** | React Hook Form | 7.45.0 | 高性能表单库 |
| **表单验证** | Zod | 3.22.0 | Schema验证 |
| **路由** | React Router | 6.8.0 | 客户端路由 |
| **拖拽** | React Beautiful DnD | 13.1.1 | 拖拽功能 |
| **图标** | Lucide React | 0.279.0 | 现代图标库 |
| **日期处理** | date-fns | 2.30.0 | 日期工具库 |
| **HTTP客户端** | Axios | 1.3.0 | API请求 |

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/          # React组件
│   │   ├── atoms/          # 原子组件（Button, Input等）
│   │   ├── molecules/      # 分子组件（TaskCard等）
│   │   ├── organisms/      # 有机体组件（TaskList, KanbanBoard等）
│   │   └── templates/      # 页面模板
│   ├── pages/              # 页面组件
│   │   ├── auth/          # 认证页面
│   │   ├── dashboard/     # 仪表板
│   │   ├── tasks/         # 任务管理
│   │   └── settings/      # 设置页面
│   ├── hooks/              # 自定义Hooks
│   ├── store/              # Zustand状态管理
│   ├── types/              # TypeScript类型定义
│   ├── theme/              # Chakra UI主题配置
│   ├── utils/              # 工具函数
│   ├── App.tsx            # 主应用组件
│   └── main.tsx           # 应用入口
├── public/                 # 静态资源
├── package.json           # 项目配置
├── vite.config.ts         # Vite配置
├── tsconfig.json          # TypeScript配置
└── README.md              # 项目文档
```

## 🔧 开发设置

### 环境要求
- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装依赖
```bash
cd frontend
npm install
```

### 环境配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

### 启动开发服务器
```bash
npm run dev
```
访问 http://localhost:3000

### 其他命令
```bash
# 构建生产版本
npm run build

# 预览生产版本
npm run preview

# 类型检查
npm run type-check

# 代码检查
npm run lint

# 代码格式化
npm run format

# 运行测试
npm run test
```

## 🎨 组件架构

### 原子设计系统
采用Atomic Design原则组织组件：

1. **Atoms（原子）** - 最基础的UI元素
   - Avatar, Badge, Button, Input等

2. **Molecules（分子）** - 原子组合形成的复合组件
   - TaskCard, SearchBox, FormField等

3. **Organisms（有机体）** - 复杂的功能组件
   - TaskList, KanbanBoard, LoginForm等

4. **Templates（模板）** - 页面级布局组件

5. **Pages（页面）** - 具体的页面实现

### 状态管理

#### AuthStore
```typescript
interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials) => Promise<void>;
  logout: () => void;
}
```

#### TaskStore
```typescript
interface TaskStore {
  tasks: Task[];
  selectedTask: Task | null;
  filter: TaskFilter;
  setTasks: (tasks: Task[]) => void;
  updateTask: (id: string, updates: Partial<Task>) => void;
}
```

#### UIStore
```typescript
interface UIStore {
  theme: 'light' | 'dark';
  currentView: ViewType;
  toggleTheme: () => void;
  setCurrentView: (view: ViewType) => void;
}
```

## 🎯 核心功能使用

### 任务管理
```typescript
import { useTasks } from '@hooks/useTasks';

const TaskComponent = () => {
  const { tasks, createTask, updateTask, deleteTask } = useTasks();

  const handleCreateTask = async (data: TaskFormData) => {
    await createTask(data);
  };
};
```

### 看板功能
```typescript
import { useKanban } from '@hooks/useKanban';

const KanbanComponent = () => {
  const { columns, moveTask, getTasksByStatus } = useKanban();

  const handleTaskMove = async (taskId: string, newStatus: TaskStatus) => {
    await moveTask(taskId, newStatus);
  };
};
```

### 认证
```typescript
import { useAuth } from '@hooks/useAuth';

const AuthComponent = () => {
  const { user, login, logout, isAuthenticated } = useAuth();

  const handleLogin = async (credentials) => {
    await login(credentials);
  };
};
```

## 🔍 API集成

### 接口配置
```typescript
// 环境变量配置
VITE_API_BASE_URL=http://localhost:8000/api

// 自动添加认证头
axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
```

### 请求拦截器
```typescript
// 自动token刷新
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await refreshToken();
      return axios(originalRequest);
    }
    return Promise.reject(error);
  }
);
```

## 🎨 主题自定义

### 颜色系统
```typescript
const colors = {
  brand: {
    50: '#E3F2FD',
    500: '#2196F3',
    900: '#0D47A1',
  },
  task: {
    todo: '#4A5568',
    in_progress: '#3182CE',
    review: '#D69E2E',
    done: '#38A169',
  }
};
```

### 组件样式
```typescript
const components = {
  Button: {
    baseStyle: {
      fontWeight: '600',
      borderRadius: 'md',
    },
    variants: {
      solid: {
        bg: 'brand.500',
        _hover: { bg: 'brand.600' }
      }
    }
  }
};
```

## 📱 响应式设计

### 断点系统
```typescript
const breakpoints = {
  base: '0em',    // 0px
  sm: '30em',     // 480px
  md: '48em',     // 768px
  lg: '62em',     // 992px
  xl: '80em',     // 1280px
  '2xl': '96em',  // 1536px
};
```

### 响应式使用
```jsx
<Box
  display={{ base: 'block', md: 'flex' }}
  width={{ base: '100%', lg: '50%' }}
  fontSize={{ base: 'sm', md: 'md', lg: 'lg' }}
>
  响应式内容
</Box>
```

## 🔧 性能优化

### 代码分割
```typescript
// 路由级代码分割
const DashboardPage = lazy(() => import('@pages/dashboard/DashboardPage'));

// 组件级懒加载
const HeavyComponent = lazy(() => import('./HeavyComponent'));
```

### Bundle分析
```bash
npm run build
npx vite-bundle-analyzer dist
```

### 优化策略
- 懒加载路由和组件
- 图片懒加载和压缩
- Zustand状态持久化
- 合理的重新渲染控制

## 🧪 测试

### 单元测试
```bash
npm run test
```

### 组件测试
```typescript
import { render, screen } from '@testing-library/react';
import { TaskCard } from '@components/molecules/TaskCard';

test('renders task card', () => {
  render(<TaskCard task={mockTask} />);
  expect(screen.getByText(mockTask.title)).toBeInTheDocument();
});
```

## 🚀 部署

### 构建
```bash
npm run build
```

### 环境变量
```bash
# 生产环境
VITE_API_BASE_URL=https://api.taskflow.com
VITE_NODE_ENV=production
```

### Docker部署
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## 📚 开发指南

### 组件开发规范
1. 使用TypeScript和严格类型
2. 遵循Atomic Design原则
3. 组件props支持Chakra UI的style props
4. 导出组件类型定义

### 状态管理规范
1. 使用Zustand创建store
2. 异步操作使用actions模式
3. 合理划分store边界
4. 支持状态持久化

### 代码风格
1. 使用ESLint和Prettier
2. 遵循React Hooks规范
3. 优先使用函数组件
4. 合理使用自定义Hooks

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件了解详情。

## 👥 维护者

- Claude Enhancer Team

## 🔗 相关链接

- [Chakra UI文档](https://chakra-ui.com/)
- [React文档](https://react.dev/)
- [Zustand文档](https://zustand-demo.pmnd.rs/)
- [Vite文档](https://vitejs.dev/)

---

*TaskFlow Pro Frontend - 让任务管理变得简单高效* ✨