/**
 * 测试环境设置文件
 * Claude Enhancer 5.0 - 前端测试环境配置
 * Initial-tests阶段 - 测试环境初始化
 */

import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeAll, afterAll } from 'vitest';

// 清理测试环境
afterEach(() => {
  cleanup();
});

// 全局测试配置
beforeAll(() => {
  // 配置全局测试环境
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => {},
    }),
  });

  // 模拟 ResizeObserver
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };

  // 模拟 IntersectionObserver
  global.IntersectionObserver = class IntersectionObserver {
    constructor() {}
    observe() {}
    unobserve() {}
    disconnect() {}
  };

  // 配置环境变量
  process.env.NODE_ENV = 'test';

  // 禁用 console 警告（可选）
  const originalWarn = console.warn;
  console.warn = (...args: any[]) => {
    // 过滤掉一些不重要的警告
    const message = args[0];
    if (
      typeof message === 'string' &&
      (message.includes('Warning: ReactDOM.render') ||
       message.includes('Warning: validateDOMNesting'))
    ) {
      return;
    }
    originalWarn(...args);
  };
});

afterAll(() => {
  // 测试完成后的清理工作
});

// 扩展 expect 匹配器
expect.extend({
  toBeInTheDocument: expect.any(Function),
  toHaveClass: expect.any(Function),
  toHaveStyle: expect.any(Function),
  toHaveAttribute: expect.any(Function),
  toBeVisible: expect.any(Function),
  toBeDisabled: expect.any(Function),
  toHaveValue: expect.any(Function),
  toHaveTextContent: expect.any(Function),
});

// Mock 全局 fetch
global.fetch = vi.fn();

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
};
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
  writable: true,
});

// Mock window.location
delete (window as any).location;
window.location = {
  href: 'http://localhost:3000',
  origin: 'http://localhost:3000',
  protocol: 'http:',
  host: 'localhost:3000',
  hostname: 'localhost',
  port: '3000',
  pathname: '/',
  search: '',
  hash: '',
  assign: vi.fn(),
  replace: vi.fn(),
  reload: vi.fn(),
} as any;

// Mock window.history
Object.defineProperty(window, 'history', {
  value: {
    back: vi.fn(),
    forward: vi.fn(),
    go: vi.fn(),
    pushState: vi.fn(),
    replaceState: vi.fn(),
    length: 1,
    state: null,
  },
  writable: true,
});

// Mock URL.createObjectURL
Object.defineProperty(URL, 'createObjectURL', {
  value: vi.fn(() => 'mock-url'),
  writable: true,
});

Object.defineProperty(URL, 'revokeObjectURL', {
  value: vi.fn(),
  writable: true,
});

// Mock FileReader
global.FileReader = class FileReader {
  result: string | ArrayBuffer | null = null;
  error: DOMException | null = null;
  readyState: number = 0;
  onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onabort: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onloadstart: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onloadend: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onprogress: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;

  readAsArrayBuffer(file: Blob): void {}
  readAsBinaryString(file: Blob): void {}
  readAsDataURL(file: Blob): void {}
  readAsText(file: Blob, encoding?: string): void {}
  abort(): void {}
  addEventListener(type: string, listener: EventListener): void {}
  removeEventListener(type: string, listener: EventListener): void {}
  dispatchEvent(event: Event): boolean { return true; }

  static readonly EMPTY = 0;
  static readonly LOADING = 1;
  static readonly DONE = 2;
};

// Mock scrollTo
Object.defineProperty(window, 'scrollTo', {
  value: vi.fn(),
  writable: true,
});

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

// Mock getBoundingClientRect
Element.prototype.getBoundingClientRect = vi.fn(() => ({
  bottom: 0,
  height: 0,
  left: 0,
  right: 0,
  top: 0,
  width: 0,
  x: 0,
  y: 0,
  toJSON: () => {},
}));

// Mock getComputedStyle
Object.defineProperty(window, 'getComputedStyle', {
  value: vi.fn(() => ({
    getPropertyValue: vi.fn(() => ''),
  })),
  writable: true,
});

// 设置默认超时时间
vi.setConfig({
  testTimeout: 10000,
});

// 全局测试工具函数
declare global {
  var createMockUser: () => {
    id: string;
    username: string;
    email: string;
    firstName: string;
    lastName: string;
  };

  var createMockTask: () => {
    id: string;
    title: string;
    description: string;
    status: string;
    priority: string;
    createdAt: string;
    updatedAt: string;
  };

  var createMockProject: () => {
    id: string;
    name: string;
    description: string;
    status: string;
    createdAt: string;
    updatedAt: string;
  };
}

// 实现全局测试工具函数
global.createMockUser = () => ({
  id: 'user-123',
  username: 'testuser',
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
});

global.createMockTask = () => ({
  id: 'task-123',
  title: '测试任务',
  description: '这是一个测试任务',
  status: 'todo',
  priority: 'medium',
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
});

global.createMockProject = () => ({
  id: 'project-123',
  name: '测试项目',
  description: '这是一个测试项目',
  status: 'active',
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
});