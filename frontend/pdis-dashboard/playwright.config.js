// @ts-check
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/e2e',
  // Maximum time one test can run before it is considered failed
  timeout: 30_000,
  // Expect timeout for individual assertions
  expect: { timeout: 5_000 },
  // Run tests in parallel (CI-safe — no shared state between tests)
  fullyParallel: false,
  // Fail the build on CI if you accidentally left test.only in the code
  forbidOnly: !!process.env.CI,
  // Retry failed tests once on CI (network/timing flakes)
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['list'], ['html', { open: 'never' }]],

  use: {
    // Base URL so tests can use `await page.goto('/')` directly
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    // Collect trace on failure only — keeps artifacts small
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
