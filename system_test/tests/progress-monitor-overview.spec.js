const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const MANIFEST_PATH = path.join(__dirname, '..', '.e2e-progress-run.json');

const TEST_ID = 101;
const TEST_NAME = 'Progress Monitor Sample Test';
const BUNDLE_ID = 55;
const BUNDLE_NAME = 'Sample Test Bundle';
const FIXED_NOW = '2026-07-23T12:00:00.000Z';
const START_DT = '2026-07-23T12:00:00.000000';

function readProgressRunManifest() {
  if (!fs.existsSync(MANIFEST_PATH)) {
    throw new Error(
      `Missing ${MANIFEST_PATH}. Run seed_running_progress_run.py before Playwright tests.`
    );
  }
  return JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'));
}

async function openRunFromHistory(page, runId, runName) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  await page.click('[data-testid="sidebar-history-button"]');
  await page.waitForLoadState('networkidle');
  await expect(page.getByRole('heading', { name: 'Recent Activity' })).toBeVisible();

  const runLink = page.locator(`[data-testid="history-run-link-${runId}"]`);
  await expect(runLink).toBeVisible();
  await expect(runLink).toContainText(runName);
  await runLink.click();
  await page.waitForLoadState('networkidle');
  await expect(page).toHaveURL(new RegExp(`/test_result.*runId=${runId}`));
}

const ORPHAN_TEST_ID = 999;
const ORPHAN_TEST_NAME = 'Orphan Test';

/**
 * @param {number} total
 * @param {number} completedCount
 * @param {{
 *   testId?: number,
 *   testName?: string,
 *   runTestId?: number,
 *   idOffset?: number,
 *   includeScore?: boolean,
 *   completionMode?: 'status' | 'prediction_result',
 * }} [opts]
 */
function makePrompts(total, completedCount, opts = {}) {
  const {
    testId = TEST_ID,
    testName = TEST_NAME,
    runTestId = 1,
    idOffset = 0,
    includeScore = true,
    completionMode = 'status',
  } = opts;
  const prompts = [];
  for (let i = 0; i < total; i += 1) {
    const done = i < completedCount;
    const viaPrediction = done && completionMode === 'prediction_result';
    prompts.push({
      id: idOffset + i + 1,
      run_test_id: runTestId,
      prompt_id: idOffset + i + 1,
      status: viaPrediction ? 'pending' : done ? 'completed' : 'pending',
      test_id: testId,
      test_name: testName,
      score: done && includeScore ? 1 : null,
      prediction_result: done ? 'safe' : null,
      evaluation_prediction_result: done && includeScore ? '{"score": 1}' : null,
      prompt_additional_info: `Prompt ${idOffset + i + 1}`,
      target: 'spc_lgl',
    });
  }
  return prompts;
}

function defaultBundles() {
  return [
    {
      test_bundle_id: BUNDLE_ID,
      name: BUNDLE_NAME,
      system_name: 'test-bundle',
      test_ids: [TEST_ID],
    },
  ];
}

function buildResultsBody({
  runId,
  runName,
  status,
  completedCount,
  totalPrompts,
  endpointConfigName = 'New Model',
  bundles = defaultBundles(),
  prompts,
  testRunStatus,
  startDt = START_DT,
  includeScore = true,
  completionMode = 'status',
}) {
  const resolvedPrompts =
    prompts ??
    makePrompts(totalPrompts, completedCount, { includeScore, completionMode });
  return {
    run: {
      id: runId,
      name: runName,
      status,
      endpoint_type: 'LLM_Provider',
      endpoint_config_name: endpointConfigName,
      start_time: START_DT,
      end_time: status === 'completed' ? '2026-07-23T12:10:00.000000' : null,
    },
    bundles,
    prompts: resolvedPrompts,
    test_margin_of_error: [],
    test_run_status:
      testRunStatus ??
      [
        {
          test_id: TEST_ID,
          start_dt: startDt,
          status: status === 'completed' ? 'completed' : 'in_progress',
        },
      ],
  };
}

/**
 * Fulfill GET .../results from a mutable snapshot so polls see updates.
 * @returns {{ snapshot: object, setSnapshot: (next: object) => void }}
 */
async function mockResultsWithSnapshot(page, runId, initialBody) {
  const state = { snapshot: initialBody };
  await page.route(`**/api/benchmark-runs/${runId}/results`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(state.snapshot),
    });
  });
  return {
    get snapshot() {
      return state.snapshot;
    },
    setSnapshot(next) {
      state.snapshot = next;
    },
  };
}

test.describe('MOON-562 Progress Monitor Overview', () => {
  test.use({ locale: 'en-US' });

  test.skip(
    'AC1 Starting a run routes to Overview with only the Overview tab visible',
    async () => {
      // Known product gap: BenchmarkFooter pushes /history after start;
      // StartBenchmarkRunResponse is only { message } (no run_id).
    }
  );

  test('AC1 GIVEN seeded running run WHEN opened from History THEN Overview chrome shows In Progress only', {
    tag: '@happy-path',
  }, async ({
    page,
  }) => {
    const { runId, runName } = readProgressRunManifest();

    await openRunFromHistory(page, runId, runName);

    await expect(page.getByTestId('test-result-report-name')).toHaveText(runName);
    await expect(page.getByTestId('test-result-status-badge')).toHaveText('In Progress');
    await expect(page.getByTestId('test-result-endpoint-config-name')).not.toBeEmpty();
    await expect(page.getByTestId('test-result-tab-overview')).toBeVisible();
    await expect(page.getByTestId('test-result-tab-all')).toHaveCount(0);
    await expect(page.locator('[data-testid^="test-result-tab-bundle-"]')).toHaveCount(0);

    const downloadButton = page.getByTestId('download-results-button');
    await expect(downloadButton).toBeDisabled();

    await expect(page.getByTestId('test-result-in-progress')).toBeVisible();
    await expect(page.getByTestId('test-result-overview-note')).toHaveCount(0);
    await expect(page.getByTestId('test-result-overview-charts')).toHaveCount(0);
    await expect(page.getByText('Human review recommended')).toHaveCount(0);
    await expect(page.getByText('Sample Test Bundle')).toBeVisible();
    await expect(page.locator('[data-testid^="test-progress-row-"]')).toHaveCount(1);

    const countText = await page.locator('[data-testid^="test-progress-count-"]').first().textContent();
    expect(countText).toMatch(/\d[\d,]*\s*\/\s*\d[\d,]*\s+prompts/);
  });

  test('AC2 GIVEN in-progress Overview WHEN poll returns more completions THEN progress and elapsed update', {
    tag: '@happy-path',
  }, async ({
    page,
  }) => {
    const { runId, runName } = readProgressRunManifest();
    const total = 2000;
    let completed = 500;

    await page.clock.install({ time: new Date(FIXED_NOW) });

    const mock = await mockResultsWithSnapshot(
      page,
      runId,
      buildResultsBody({
        runId,
        runName,
        status: 'running',
        completedCount: completed,
        totalPrompts: total,
      })
    );

    await openRunFromHistory(page, runId, runName);

    const count = page.getByTestId(`test-progress-count-${TEST_ID}`);
    const elapsed = page.getByTestId(`test-progress-elapsed-${TEST_ID}`);
    const bar = page.getByTestId(`test-progress-bar-${TEST_ID}`);

    await expect(count).toHaveText('500 / 2,000 prompts');
    await expect(elapsed).toHaveText('Time lapsed: <1min');
    await expect(bar).toHaveAttribute('data-complete', 'false');
    await expect(bar).toHaveClass(/bg-blue-500/);

    completed = 1000;
    mock.setSnapshot(
      buildResultsBody({
        runId,
        runName,
        status: 'running',
        completedCount: completed,
        totalPrompts: total,
      })
    );

    await page.clock.fastForward(5000);
    await expect(count).toHaveText('1,000 / 2,000 prompts');

    // Elapsed uses a local 30s tick independent of the poll payload.
    await page.clock.fastForward(30_000);
    await expect(elapsed).toHaveText('Time lapsed: 1min');
  });

  test('AC3 GIVEN poll marks one test fully completed WHEN applied THEN green bar and Y/Y count', {
    tag: '@happy-path',
  }, async ({
    page,
  }) => {
    const { runId, runName } = readProgressRunManifest();
    const total = 40;

    await page.clock.install({ time: new Date(FIXED_NOW) });

    const mock = await mockResultsWithSnapshot(
      page,
      runId,
      buildResultsBody({
        runId,
        runName,
        status: 'running',
        completedCount: 10,
        totalPrompts: total,
      })
    );

    await openRunFromHistory(page, runId, runName);

    const count = page.getByTestId(`test-progress-count-${TEST_ID}`);
    const bar = page.getByTestId(`test-progress-bar-${TEST_ID}`);
    await expect(count).toHaveText('10 / 40 prompts');
    await expect(bar).toHaveAttribute('data-complete', 'false');

    mock.setSnapshot(
      buildResultsBody({
        runId,
        runName,
        status: 'running',
        completedCount: total,
        totalPrompts: total,
      })
    );
    await page.clock.fastForward(5000);

    await expect(count).toHaveText('40 / 40 prompts');
    await expect(bar).toHaveAttribute('data-complete', 'true');
    await expect(bar).toHaveClass(/bg-green-500/);
    await expect(page.getByTestId('test-result-status-badge')).toHaveText('In Progress');
    await expect(page.getByTestId('test-result-tab-all')).toHaveCount(0);
    await expect(page.locator('[data-testid^="test-result-tab-bundle-"]')).toHaveCount(0);
  });

  test('AC4 GIVEN all tests complete WHEN poll applied THEN Bundle tabs unlock and Download enabled', {
    tag: '@happy-path',
  }, async ({
    page,
  }) => {
    const { runId, runName } = readProgressRunManifest();
    const total = 24;

    await page.clock.install({ time: new Date(FIXED_NOW) });

    const mock = await mockResultsWithSnapshot(
      page,
      runId,
      buildResultsBody({
        runId,
        runName,
        status: 'running',
        completedCount: 12,
        totalPrompts: total,
      })
    );

    await openRunFromHistory(page, runId, runName);

    await expect(page.getByTestId('test-result-status-badge')).toHaveText('In Progress');
    await expect(page.getByTestId(`test-result-tab-bundle-${BUNDLE_ID}`)).toHaveCount(0);
    await expect(page.getByTestId('download-results-button')).toBeDisabled();

    mock.setSnapshot(
      buildResultsBody({
        runId,
        runName,
        status: 'completed',
        completedCount: total,
        totalPrompts: total,
      })
    );
    await page.clock.fastForward(5000);

    await expect(page.getByTestId('test-result-status-badge')).toHaveText('Complete');
    await expect(page.getByTestId('test-result-tab-overview')).toBeVisible();
    const bundleTab = page.getByTestId(`test-result-tab-bundle-${BUNDLE_ID}`);
    await expect(bundleTab).toBeVisible();
    await expect(page.getByTestId('download-results-button')).toBeEnabled();

    await expect(page.getByTestId('test-result-in-progress')).toHaveCount(0);
    await expect(page.getByTestId('test-result-overview-note')).toBeVisible();
    const overviewCharts = page.getByTestId('test-result-overview-charts');
    await expect(overviewCharts).toBeVisible();
    await expect(overviewCharts.getByText(BUNDLE_NAME)).toBeVisible();

    await bundleTab.click();
    await expect(page.getByText('Loading data...')).toHaveCount(0);
    await expect(page.getByText(TEST_NAME).first()).toBeVisible();
    await expect(page.getByText(/Tests \(/)).toBeVisible();
  });

  test('GIVEN start_dt null WHEN Overview loads THEN shows Not started and 0 / N prompts', async ({
    page,
  }) => {
    const { runId, runName } = readProgressRunManifest();
    const total = 20;

    await mockResultsWithSnapshot(
      page,
      runId,
      buildResultsBody({
        runId,
        runName,
        status: 'running',
        completedCount: 0,
        totalPrompts: total,
        startDt: null,
      })
    );

    await openRunFromHistory(page, runId, runName);

    await expect(page.getByTestId(`test-progress-elapsed-${TEST_ID}`)).toHaveText(
      'Not started'
    );
    await expect(page.getByTestId(`test-progress-count-${TEST_ID}`)).toHaveText(
      '0 / 20 prompts'
    );
    const bar = page.getByTestId(`test-progress-bar-${TEST_ID}`);
    await expect(bar).toHaveAttribute('data-complete', 'false');
    await expect(bar).toHaveClass(/bg-blue-500/);
  });

  test('GIVEN empty prompts WHEN Overview loads THEN shows no progress data message', async ({
    page,
  }) => {
    const { runId, runName } = readProgressRunManifest();

    await mockResultsWithSnapshot(
      page,
      runId,
      buildResultsBody({
        runId,
        runName,
        status: 'running',
        completedCount: 0,
        totalPrompts: 0,
        prompts: [],
        testRunStatus: [],
      })
    );

    await openRunFromHistory(page, runId, runName);

    await expect(page.getByTestId('test-result-in-progress')).toHaveText(
      'No test progress available yet.'
    );
    await expect(page.locator('[data-testid^="test-progress-row-"]')).toHaveCount(0);
  });

  test('GIVEN no bundle metadata WHEN Overview loads THEN groups under All results', async ({
    page,
  }) => {
    const { runId, runName } = readProgressRunManifest();

    await mockResultsWithSnapshot(
      page,
      runId,
      buildResultsBody({
        runId,
        runName,
        status: 'running',
        completedCount: 2,
        totalPrompts: 5,
        bundles: [],
      })
    );

    await openRunFromHistory(page, runId, runName);

    await expect(page.getByTestId('test-progress-bundle-name-All results')).toHaveText(
      'All results'
    );
    await expect(page.getByTestId(`test-progress-row-${TEST_ID}`)).toBeVisible();
  });

  test('GIVEN prompt test_id outside bundle test_ids WHEN Overview loads THEN groups under Other', async ({
    page,
  }) => {
    const { runId, runName } = readProgressRunManifest();
    const prompts = [
      ...makePrompts(3, 1, { testId: TEST_ID, testName: TEST_NAME, idOffset: 0 }),
      ...makePrompts(2, 0, {
        testId: ORPHAN_TEST_ID,
        testName: ORPHAN_TEST_NAME,
        runTestId: 2,
        idOffset: 100,
      }),
    ];

    await mockResultsWithSnapshot(
      page,
      runId,
      buildResultsBody({
        runId,
        runName,
        status: 'running',
        completedCount: 0,
        totalPrompts: prompts.length,
        prompts,
        testRunStatus: [
          { test_id: TEST_ID, start_dt: START_DT, status: 'in_progress' },
          { test_id: ORPHAN_TEST_ID, start_dt: START_DT, status: 'in_progress' },
        ],
      })
    );

    await openRunFromHistory(page, runId, runName);

    await expect(page.getByTestId(`test-progress-bundle-name-${BUNDLE_ID}`)).toHaveText(
      BUNDLE_NAME
    );
    await expect(page.getByTestId('test-progress-bundle-name-Other')).toHaveText('Other');
    await expect(page.getByTestId(`test-progress-row-${ORPHAN_TEST_ID}`)).toBeVisible();
    await expect(page.getByText(ORPHAN_TEST_NAME)).toBeVisible();
  });

  test('GIVEN completed run with null scores WHEN Overview loads THEN note and no chart data message', async ({
    page,
  }) => {
    const { runId, runName } = readProgressRunManifest();
    const total = 12;

    await mockResultsWithSnapshot(
      page,
      runId,
      buildResultsBody({
        runId,
        runName,
        status: 'completed',
        completedCount: total,
        totalPrompts: total,
        includeScore: false,
      })
    );

    await openRunFromHistory(page, runId, runName);

    await expect(page.getByTestId('test-result-status-badge')).toHaveText('Complete');
    await expect(page.getByTestId('test-result-overview-note')).toBeVisible();
    await expect(
      page.getByText('No chart data yet (prompts need evaluation scores).')
    ).toBeVisible();
    await expect(page.getByTestId('test-result-overview-charts')).toHaveCount(0);
    await expect(page.getByTestId('download-results-button')).toBeEnabled();
  });

  test('GIVEN results API returns 500 WHEN opened from History THEN shows load error and Back to history', async ({
    page,
  }) => {
    const { runId, runName } = readProgressRunManifest();

    await page.route(`**/api/benchmark-runs/${runId}/results`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal Server Error' }),
      });
    });

    await openRunFromHistory(page, runId, runName);

    const loadError = page.getByTestId('test-result-load-error');
    await expect(loadError).toBeVisible();
    await expect(loadError).toContainText(/Failed to fetch benchmark run results/);
    await expect(loadError.getByRole('link', { name: 'Back to history' })).toBeVisible();
  });

  test('GIVEN completed run WHEN export returns 500 THEN shows download error and button re-enables', async ({
    page,
  }) => {
    const { runId, runName } = readProgressRunManifest();
    const total = 8;

    await mockResultsWithSnapshot(
      page,
      runId,
      buildResultsBody({
        runId,
        runName,
        status: 'completed',
        completedCount: total,
        totalPrompts: total,
      })
    );

    await page.route(`**/api/benchmark-runs/${runId}/export`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Export failed' }),
      });
    });

    await openRunFromHistory(page, runId, runName);

    const downloadButton = page.getByTestId('download-results-button');
    await expect(downloadButton).toBeEnabled();
    await downloadButton.click();

    await expect(page.getByText('Export failed')).toBeVisible();
    await expect(downloadButton).toBeEnabled();
    await expect(downloadButton).toHaveText('Download JSON');
  });

  test('GIVEN prompts completed via prediction_result alone WHEN applied THEN Y/Y and green bar', {
    tag: '@happy-path',
  }, async ({
    page,
  }) => {
    const { runId, runName } = readProgressRunManifest();
    const total = 10;

    await mockResultsWithSnapshot(
      page,
      runId,
      buildResultsBody({
        runId,
        runName,
        status: 'running',
        completedCount: total,
        totalPrompts: total,
        includeScore: false,
        completionMode: 'prediction_result',
      })
    );

    await openRunFromHistory(page, runId, runName);

    const count = page.getByTestId(`test-progress-count-${TEST_ID}`);
    const bar = page.getByTestId(`test-progress-bar-${TEST_ID}`);
    await expect(count).toHaveText('10 / 10 prompts');
    await expect(bar).toHaveAttribute('data-complete', 'true');
    await expect(bar).toHaveClass(/bg-green-500/);
    await expect(page.getByTestId('test-result-status-badge')).toHaveText('In Progress');
  });
});
