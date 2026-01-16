module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/__tests__/**/*.test.js', '**/?(*.)+(spec|test).js'],
  collectCoverageFrom: [
    'apps/**/*.js',
    '!apps/**/node_modules/**',
    '!apps/**/test/**'
  ],
  setupFilesAfterEnv: [],
  verbose: true,
  forceExit: true,
  detectOpenHandles: true,
  testTimeout: 10000
};