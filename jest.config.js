/**
 * Jest Configuration for Claude Enhancer 5.3
 * Includes comprehensive coverage reporting
 */

module.exports = {
  // Test environment
  testEnvironment: 'node',

  // Test patterns
  testMatch: [
    '**/test/**/*.test.js',
    '**/test/**/*.spec.js',
    '**/__tests__/**/*.js'
  ],

  // Coverage collection
  collectCoverage: false, // Enable only when running test:coverage
  collectCoverageFrom: [
    'src/**/*.{js,ts}',
    'frontend/src/**/*.{js,ts,tsx}',
    '.claude/core/**/*.{js,ts}',
    'scripts/**/*.{js,ts}',
    '!**/node_modules/**',
    '!**/test/**',
    '!**/tests/**',
    '!**/__tests__/**',
    '!**/coverage/**',
    '!**/dist/**',
    '!**/build/**',
    '!**/*.config.js',
    '!**/*.spec.js',
    '!**/*.test.js'
  ],

  // Coverage thresholds (ENFORCED)
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    // Critical modules require higher coverage
    './src/api/**/*.js': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    },
    './src/core/**/*.js': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    }
  },

  // Coverage reporters
  coverageReporters: [
    'text',           // Console output
    'text-summary',   // Brief summary
    'lcov',           // For CI/CD and coverage services
    'html',           // HTML report for local viewing
    'json',           // Machine-readable format
    'cobertura'       // For CI systems like Jenkins
  ],

  // Coverage output directory
  coverageDirectory: 'coverage',

  // Transform files
  transform: {
    '^.+\\.tsx?$': 'ts-jest',
    '^.+\\.jsx?$': 'babel-jest'
  },

  // Module paths
  moduleDirectories: ['node_modules', 'src'],

  // Module file extensions
  moduleFileExtensions: ['js', 'ts', 'tsx', 'json', 'node'],

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/test/setup.js'],

  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/coverage/',
    '/dist/',
    '/build/',
    '/.git/'
  ],

  // Coverage path ignore patterns
  coveragePathIgnorePatterns: [
    '/node_modules/',
    '/test/',
    '/tests/',
    '/__tests__/',
    '/coverage/',
    '/dist/',
    '/build/',
    '/.performance_backup/',
    '/deprecated/'
  ],

  // Verbose output
  verbose: true,

  // Test timeout
  testTimeout: 10000,

  // Clear mocks between tests
  clearMocks: true,

  // Restore mocks between tests
  restoreMocks: true,

  // Reset mocks between tests
  resetMocks: true,

  // Fail on console errors (optional)
  // errorOnDeprecated: true,

  // Detect open handles
  detectOpenHandles: false,

  // Force exit after tests complete
  forceExit: false,

  // Max workers
  maxWorkers: '50%',

  // Reporters (commented out jest-junit as it's optional)
  reporters: [
    'default'
    // Uncomment if jest-junit is installed:
    // [
    //   'jest-junit',
    //   {
    //     outputDirectory: './test-results',
    //     outputName: 'junit.xml',
    //     classNameTemplate: '{classname}',
    //     titleTemplate: '{title}',
    //     ancestorSeparator: ' > ',
    //     usePathForSuiteName: true
    //   }
    // ]
  ],

  // Global setup/teardown
  // globalSetup: '<rootDir>/test/global-setup.js',
  // globalTeardown: '<rootDir>/test/global-teardown.js',

  // Notify on completion
  notify: false,

  // Watch mode plugins (optional, install if needed)
  // watchPlugins: [
  //   'jest-watch-typeahead/filename',
  //   'jest-watch-typeahead/testname'
  // ]
};
