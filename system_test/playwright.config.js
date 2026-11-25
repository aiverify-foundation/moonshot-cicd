// @ts-check
const fs = require('fs');
const path = require('path');
const { defineConfig, devices } = require('@playwright/test');

// Set PLAYWRIGHT_INCLUDE_INTEGRATION=1 to include tests/integration (see npm run test:all).
const includeIntegration = process.env.PLAYWRIGHT_INCLUDE_INTEGRATION === '1';

// tests/extensions start their own API instances (utils/extensionServer.js). They are part of a
// plain `npm run test` whenever the MOON-807 flag (AIVET_OCT2026_MOON807) is true in
// feature_flags.txt, the same file the API reads. Like the runtime, this fails closed: a missing
// file, a missing line or any value other than lowercase `true` means off.
// Overrides: E2E_EXTENSIONS=1 forces them on, E2E_EXTENSIONS=0 forces them off, and naming
// --project=extensions or a path under tests/extensions on the CLI selects them even with the flag off.
const MOON807_FLAG = 'AIVET_OCT2026_MOON807';

function isMoon807FlagOn() {
  const flagsPath =
    process.env.AIVET_FEATURE_FLAGS_PATH ||
    path.join(__dirname, '..', 'moonshot_core', 'data', 'feature_flags.txt');
  try {
    return fs
      .readFileSync(flagsPath, 'utf8')
      .split('\n')
      .some((line) => line.trim() === `${MOON807_FLAG}=true`);
  } catch {
    return false;
  }
}

// The decision is stored in env vars so worker processes (which load this file without the
// CLI arguments) make the same choice as the main process.
if (!process.env.E2E_EXTENSIONS_RUN) {
  const requestedOnCli = process.argv.join(' ').includes('extensions');
  const forcedOn = process.env.E2E_EXTENSIONS === '1';
  const forcedOff = process.env.E2E_EXTENSIONS === '0';
  process.env.E2E_EXTENSIONS_RUN = !forcedOff && (forcedOn || requestedOnCli || isMoon807FlagOn()) ? '1' : '0';
  // Only an explicit extensions-only selection skips the shared :8000 seed (below).
  process.env.E2E_EXTENSIONS_ONLY = requestedOnCli && !forcedOn && !forcedOff ? '1' : '0';
}
const extensionsRequested = process.env.E2E_EXTENSIONS_RUN === '1';
// Extension-only runs are self-contained: they do not use the shared :8000 API, so the
// global seed (which writes to :8000) is skipped for them. A plain run still seeds, because
// it also runs the chromium project.
const extensionsOnly = extensionsRequested && process.env.E2E_EXTENSIONS_ONLY === '1';

const baseIgnore = includeIntegration ? [] : ['**/integration/**'];

/**
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: './tests',
  globalSetup: extensionsOnly ? undefined : require.resolve('./global-setup'),
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }]
  ],
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: process.env.BASE_URL || 'http://localhost:8000',

    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',

    /* Take screenshot on failure */
    screenshot: 'only-on-failure',

    /* Record video on failure */
    video: 'retain-on-failure',
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      testIgnore: [...baseIgnore, '**/extensions/**'],
      use: { ...devices['Desktop Chrome'] },
    },
    ...(extensionsRequested
      ? [
          {
            name: 'extensions',
            testMatch: ['**/extensions/**/*.spec.js'],
            // Each spec starts API processes and runs benchmarks, so keep one worker.
            workers: 1,
            timeout: 360000,
            use: { ...devices['Desktop Chrome'] },
          },
        ]
      : []),
  ],
});
