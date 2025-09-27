/**
 * Vitest配置文件
 * Claude Enhancer 5.0 - 前端测试配置
 * Initial-tests阶段 - 前端测试框架配置
 */

import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],

  test: {
    // 测试环境配置
    environment: 'jsdom',

    // 全局设置
    globals: true,

    // 设置文件
    setupFiles: ['./src/test-setup.ts'],

    // 包含文件模式
    include: [
      'src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      '__tests__/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'
    ],

    // 排除文件模式
    exclude: [
      'node_modules/**',
      'dist/**',
      'build/**',
      'coverage/**',
      '.next/**',
      '.nuxt/**',
      '.vercel/**',
      'cypress/**',
      'e2e/**'
    ],

    // 监听配置
    watch: true,
    watchExclude: [
      'node_modules/**',
      'dist/**',
      'build/**'
    ],

    // 覆盖率配置
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/**',
        'src/test-setup.ts',
        'src/**/*.d.ts',
        'src/**/*.config.{js,ts}',
        'src/**/*.stories.{js,ts,jsx,tsx}',
        'src/**/*.test.{js,ts,jsx,tsx}',
        'src/**/*.spec.{js,ts,jsx,tsx}',
        'src/**/index.{js,ts}',
        'src/types/**',
        'src/utils/test-utils.tsx'
      ],
      include: [
        'src/**/*.{js,ts,jsx,tsx}'
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    },

    // 输出配置
    outputFile: {
      junit: './test-results/junit.xml',
      json: './test-results/results.json'
    },

    // 报告器配置
    reporters: ['verbose', 'junit', 'json'],

    // 超时配置
    testTimeout: 10000,
    hookTimeout: 10000,

    // 并发配置
    maxConcurrency: 5,
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
        useAtomics: true,
        minThreads: 1,
        maxThreads: 4
      }
    },

    // Mock配置
    mockReset: true,
    clearMocks: true,
    restoreMocks: true,

    // 日志配置
    logHeapUsage: true,

    // 快照配置
    updateSnapshot: 'new',

    // 禁用隔离（提高性能）
    isolate: false,

    // 缓存配置
    cache: {
      dir: './node_modules/.vitest'
    }
  },

  // 解析配置
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
      '@services': path.resolve(__dirname, './src/services'),
      '@store': path.resolve(__dirname, './src/store'),
      '@theme': path.resolve(__dirname, './src/theme'),
      '@test-utils': path.resolve(__dirname, './src/utils/test-utils.tsx')
    }
  },

  // 定义全局变量
  define: {
    'process.env.NODE_ENV': JSON.stringify('test'),
    '__DEV__': true,
    '__TEST__': true
  },

  // esbuild配置
  esbuild: {
    target: 'node14'
  },

  // 优化配置
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react/jsx-runtime',
      '@testing-library/react',
      '@testing-library/jest-dom',
      '@testing-library/user-event'
    ]
  }
});