/**
 * Jest setup file for Claude Enhancer 5.3
 * Runs before all tests
 */

// Set test environment variables
process.env.NODE_ENV = 'test';
process.env.LOG_LEVEL = 'error'; // Reduce noise during tests

// Global test timeout
jest.setTimeout(10000);

// Mock console methods to reduce noise (optional)
global.console = {
  ...console,
  // Uncomment to suppress console logs during tests
  // log: jest.fn(),
  // debug: jest.fn(),
  // info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};

// Setup global test utilities
global.testUtils = {
  // Helper to wait for async operations
  waitFor: (ms) => new Promise(resolve => setTimeout(resolve, ms)),

  // Helper to generate test data
  generateTestData: (count = 10) => {
    return Array.from({ length: count }, (_, i) => ({
      id: i + 1,
      name: `Test Item ${i + 1}`,
      timestamp: new Date().toISOString()
    }));
  }
};

// Setup mocks for common modules
jest.mock('winston', () => ({
  createLogger: jest.fn(() => ({
    info: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    debug: jest.fn(),
  })),
  format: {
    combine: jest.fn(),
    timestamp: jest.fn(),
    printf: jest.fn(),
    colorize: jest.fn(),
    simple: jest.fn(),
  },
  transports: {
    Console: jest.fn(),
    File: jest.fn(),
  },
}));

// Cleanup after all tests
afterAll(() => {
  // Clean up any resources
  jest.clearAllTimers();
  jest.clearAllMocks();
});
