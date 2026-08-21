const { test, expect } = require('@playwright/test');

const UNDESIRABLE_BUNDLE = 'Undesirable Content';
const VIOLENT_CRIMES_TEST = 'MLCommons AILuminate - Violent Crimes';
const VIOLENT_CRIMES_LEARN_MORE =
  'test-learn-more-mlcommons-ailuminate-violent-crimes';

const ADVERSARIAL_BUNDLE = 'Adversarial Prompts';
const CYBERSECEVAL_TEST = 'CyberSecEval - Prompt Injections 3';
const CYBERSECEVAL_LEARN_MORE =
  'test-learn-more-cyberseceval-prompt-injections-3';

const LLAMA_GUARD_MODEL = 'meta-llama/Llama-Guard-4-12B';
const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';

async function navigateToBenchmark(page) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.click('[data-testid="benchmark-link"]');
  await page.waitForLoadState('networkidle');
  await expect(
    page.locator('[data-testid="select-bundles-header"]')
  ).toContainText('Select Test Bundles');
}

async function openBundleSheet(page, bundleName) {
  await page.waitForSelector('[data-testid^="bundle-card-"]', {
    timeout: 15000,
  });
  const card = page
    .locator('[data-testid^="bundle-card-"]')
    .filter({
      has: page.locator('[data-testid="bundle-name"]', { hasText: bundleName }),
    });
  await expect(card.first()).toBeVisible();
  await card.first().locator('[data-testid="learn-more-link"]').click();
  await expect(page.locator('[data-testid="bundle-details-sheet"]')).toBeVisible();
  await expect(page.locator('[data-testid="bundle-details-name"]')).toContainText(
    bundleName
  );
}

/**
 * @param {import('@playwright/test').Page} page
 * @param {import('@playwright/test').BrowserContext} context
 * @param {string} learnMoreTestId
 */
async function openTestDetailsInNewTab(page, context, learnMoreTestId) {
  const popupPromise = context.waitForEvent('page');
  await page.locator(`[data-testid="${learnMoreTestId}"]`).click();
  const popup = await popupPromise;
  await popup.waitForLoadState('networkidle');
  return popup;
}

/**
 * Resolve a test from GET /api/bundles by display name.
 * DB-backed bundles use numeric dataset.id (not the YAML system name).
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {string} testName
 */
async function findBundleTest(request, testName) {
  const response = await request.get('/api/bundles');
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  for (const bundle of data.bundles || []) {
    for (const bundleTest of bundle.tests || []) {
      if (bundleTest.name === testName) {
        return {
          bundle,
          test: bundleTest,
          datasetId: String(bundleTest.dataset?.id ?? ''),
          datasetName: String(bundleTest.dataset?.name ?? ''),
        };
      }
    }
  }
  throw new Error(`Test not found in /api/bundles: ${testName}`);
}

function viewTestUrl({ testName, dataset } = {}) {
  const params = new URLSearchParams();
  if (testName != null) params.set('test', testName);
  if (dataset != null) params.set('dataset', String(dataset));
  const qs = params.toString();
  return qs ? `/view_test/?${qs}` : '/view_test/';
}

/**
 * FastAPI blocks static routes without a same-origin Referer.
 * Always send referer from the app root (same pattern as in-app navigation).
 */
async function gotoViewTest(page, { testName, dataset } = {}) {
  await page.goto(viewTestUrl({ testName, dataset }), {
    referer: `${BASE_URL}/`,
    waitUntil: 'networkidle',
  });
}

/**
 * Mock GET /api/bundles (portal fetches absolute http://localhost:8000/api/bundles).
 * @param {import('@playwright/test').Page} page
 * @param {{ status?: number, body?: object } | (() => { status?: number, body?: object })} responseOrFactory
 */
async function mockBundles(page, responseOrFactory) {
  await page.route('**/api/bundles**', async (route) => {
    if (route.request().method() !== 'GET') {
      await route.continue();
      return;
    }
    const resolved =
      typeof responseOrFactory === 'function'
        ? responseOrFactory()
        : responseOrFactory;
    const status = resolved.status ?? 200;
    if (status >= 400) {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'mocked bundles failure' }),
      });
      return;
    }
    await route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(resolved.body ?? { bundles: [] }),
    });
  });
}

function mockBundleWithTest(overrides = {}) {
  const testRow = {
    name: 'Mock Sample Test',
    description: 'Mock description for E2E',
    requires_llm_aaj: true,
    metric_provider_system_name: 'together_adapter',
    metric_grader_model_name: LLAMA_GUARD_MODEL,
    dataset: {
      id: 'mock-dataset',
      name: 'mock-dataset',
      description: '',
      num_of_dataset_prompts: 10,
    },
    metric: { name: 'ailuminate_safety_classifier_adapter' },
    details: [
      {
        category_name: 'Cat',
        dataset: 'mock-dataset',
        hazard: 'h1',
        input: 'mock input',
        target: '',
        response: 'mock response',
        evaluator_verdict: 'Safe',
      },
    ],
    ...overrides,
  };
  return {
    bundles: [
      {
        id: 'mock-bundle',
        name: 'Mock Bundle',
        description: 'Mock',
        category: 'Safety',
        prompt_count: 10,
        tests: [testRow],
      },
    ],
  };
}

test.describe('MOON-543 View Test Details', () => {
  test('bundle Learn more opens the bundle details sheet', { tag: '@happy-path' }, async ({ page }) => {
    await navigateToBenchmark(page);
    await openBundleSheet(page, UNDESIRABLE_BUNDLE);

    await expect(
      page.locator('[data-testid="bundle-details-prompt-count"]')
    ).toBeVisible();
    await expect(
      page.locator('[data-testid="bundle-details-test-count"]')
    ).toBeVisible();
    const promptCount = await page
      .locator('[data-testid="bundle-details-prompt-count"]')
      .textContent();
    const testCount = await page
      .locator('[data-testid="bundle-details-test-count"]')
      .textContent();
    expect(Number(promptCount)).toBeGreaterThan(0);
    expect(Number(testCount)).toBeGreaterThan(0);
    await expect(
      page.locator('[data-testid^="test-detail-card-"]').first()
    ).toBeVisible();
  });

  test('test Learn More opens Test Details in a new tab', { tag: '@happy-path' }, async ({
    page,
    context,
    request,
  }) => {
    const { datasetId } = await findBundleTest(request, VIOLENT_CRIMES_TEST);

    await navigateToBenchmark(page);
    await openBundleSheet(page, UNDESIRABLE_BUNDLE);

    const popup = await openTestDetailsInNewTab(
      page,
      context,
      VIOLENT_CRIMES_LEARN_MORE
    );

    expect(popup.url()).toMatch(/\/view_test/);
    expect(decodeURIComponent(popup.url())).toContain(VIOLENT_CRIMES_TEST);
    expect(popup.url()).toContain(`dataset=${encodeURIComponent(datasetId)}`);

    await expect(popup.locator('[data-testid="view-test-details"]')).toBeVisible({
      timeout: 15000,
    });
    await expect(popup.locator('[data-testid="view-test-name"]')).toHaveText(
      VIOLENT_CRIMES_TEST
    );
  });

  test('Violent Crimes page shows layout, Safe/Unsafe verdicts, and no download', { tag: '@happy-path' }, async ({
    page,
    request,
  }) => {
    const { datasetId, test: bundleTest } = await findBundleTest(
      request,
      VIOLENT_CRIMES_TEST
    );

    await gotoViewTest(page, {
      testName: VIOLENT_CRIMES_TEST,
      dataset: datasetId,
    });

    await expect(page.locator('[data-testid="view-test-details"]')).toBeVisible({
      timeout: 15000,
    });
    await expect(page.locator('[data-testid="view-test-name"]')).toHaveText(
      VIOLENT_CRIMES_TEST
    );
    await expect(page.locator('[data-testid="view-test-description"]')).toBeVisible();
    await expect(
      page.locator('[data-testid="view-test-description"]')
    ).not.toBeEmpty();

    await expect(
      page.locator('[data-testid="view-test-dataset-info"]')
    ).toContainText('Dataset Information');
    await expect(
      page.locator('[data-testid="view-test-dataset-info"]')
    ).toContainText('Prompts');
    const promptCount = await page
      .locator('[data-testid="view-test-prompt-count"]')
      .textContent();
    expect(Number(promptCount)).toBeGreaterThan(0);

    await expect(page.getByText('False-positive rate')).toHaveCount(0);
    await expect(page.getByText('Number of Tokens')).toHaveCount(0);
    await expect(page.getByText('Contamination Risk')).toHaveCount(0);
    await expect(
      page.locator('[data-testid="view-test-dataset-info"]')
    ).not.toContainText('Language');

    await expect(
      page.locator('[data-testid="view-test-evaluator-info"]')
    ).toContainText('Evaluator Information');
    await expect(
      page.locator('[data-testid="view-test-evaluator-info"]')
    ).toContainText('LLM-as-judge Model');
    await expect(page.locator('[data-testid="view-test-grader-model"]')).toHaveText(
      bundleTest.metric_grader_model_name
    );

    await expect(page.locator('[data-testid="how-it-works-heading"]')).toHaveText(
      'How It Works'
    );
    const table = page.locator('[data-testid="how-it-works-table"]');
    await expect(table).toBeVisible();
    const headers = table.locator('thead th');
    await expect(headers).toHaveCount(4);
    await expect(headers.nth(0)).toHaveText('Input');
    await expect(headers.nth(1)).toHaveText('Target');
    await expect(headers.nth(2)).toHaveText('Response');
    await expect(headers.nth(3)).toHaveText('Evaluator Verdict');

    const rows = page.locator('[data-testid^="how-it-works-row-"]');
    await expect(rows).toHaveCount(2);

    for (let i = 0; i < 2; i++) {
      await expect(
        page.locator(`[data-testid="how-it-works-target-${i}"]`)
      ).toHaveText('—');
    }

    const verdictTexts = [];
    for (let i = 0; i < 2; i++) {
      const text = (
        await page.locator(`[data-testid="how-it-works-verdict-${i}"]`).textContent()
      ).trim();
      verdictTexts.push(text);
      expect(text === '1' || text === '0').toBeFalsy();
    }
    expect(
      verdictTexts.some((v) => v === 'Safe' || v === 'Unsafe')
    ).toBeTruthy();

    await expect(
      page.getByRole('button', { name: 'Download all prompts' })
    ).toHaveCount(0);
  });

  test('CyberSecEval sample shows real Target text and Safe/Unsafe verdicts', { tag: '@happy-path' }, async ({
    page,
    request,
  }) => {
    const { datasetId } = await findBundleTest(request, CYBERSECEVAL_TEST);

    await gotoViewTest(page, {
      testName: CYBERSECEVAL_TEST,
      dataset: datasetId,
    });

    await expect(page.locator('[data-testid="view-test-details"]')).toBeVisible({
      timeout: 15000,
    });
    await expect(page.locator('[data-testid="view-test-name"]')).toHaveText(
      CYBERSECEVAL_TEST
    );

    const rows = page.locator('[data-testid^="how-it-works-row-"]');
    await expect(rows).toHaveCount(2);

    for (let i = 0; i < 2; i++) {
      const target = (
        await page.locator(`[data-testid="how-it-works-target-${i}"]`).textContent()
      ).trim();
      expect(target).not.toBe('—');
      expect(target.length).toBeGreaterThan(0);
    }

    const verdictTexts = [];
    for (let i = 0; i < 2; i++) {
      verdictTexts.push(
        (
          await page
            .locator(`[data-testid="how-it-works-verdict-${i}"]`)
            .textContent()
        ).trim()
      );
    }
    expect(
      verdictTexts.some((v) => v === 'Safe' || v === 'Unsafe')
    ).toBeTruthy();
  });

  test('Evaluator Information shows em dash when no grader model', async ({
    page,
  }) => {
    await mockBundles(page, {
      body: mockBundleWithTest({
        metric_grader_model_name: null,
        requires_llm_aaj: false,
        metric_provider_system_name: null,
        metric: { name: 'accuracy_adapter' },
      }),
    });

    await gotoViewTest(page, {
      testName: 'Mock Sample Test',
      dataset: 'mock-dataset',
    });

    await expect(page.locator('[data-testid="view-test-details"]')).toBeVisible();
    await expect(page.locator('[data-testid="view-test-grader-model"]')).toHaveText(
      '—'
    );
    await expect(page.locator('[data-testid="view-test-details"]')).not.toContainText(
      'accuracy_adapter'
    );
  });

  test('How It Works empty state when dataset has no details', async ({
    page,
  }) => {
    await mockBundles(page, {
      body: mockBundleWithTest({ details: null }),
    });

    await gotoViewTest(page, {
      testName: 'Mock Sample Test',
      dataset: 'mock-dataset',
    });

    await expect(page.locator('[data-testid="how-it-works-empty"]')).toBeVisible();
    await expect(
      page.locator('[data-testid="how-it-works-empty"]')
    ).toContainText('No sample prompts available for this dataset.');
    await expect(page.locator('[data-testid="how-it-works-table"]')).toHaveCount(0);
  });

  test('missing query params shows not-found guidance', async ({ page }) => {
    await gotoViewTest(page);

    await expect(
      page.locator('[data-testid="view-test-missing-params"]')
    ).toBeVisible();
    await expect(page.locator('[data-testid="view-test-heading"]')).toHaveText(
      'Test not found'
    );
    await expect(page.locator('[data-testid="view-test-message"]')).toContainText(
      'Learn More'
    );
    await expect(
      page.locator('[data-testid="view-test-back-to-benchmark"]')
    ).toBeVisible();
  });

  test('unknown test/dataset shows not-found message', async ({ page }) => {
    await gotoViewTest(page, {
      testName: 'No Such Test',
      dataset: 'no-such-dataset',
    });

    await expect(page.locator('[data-testid="view-test-not-found"]')).toBeVisible({
      timeout: 15000,
    });
    await expect(page.locator('[data-testid="view-test-heading"]')).toHaveText(
      'Test not found'
    );
    await expect(page.locator('[data-testid="view-test-message"]')).toContainText(
      'No Such Test'
    );
    await expect(page.locator('[data-testid="view-test-message"]')).toContainText(
      'no-such-dataset'
    );
    await expect(
      page.locator('[data-testid="view-test-back-to-benchmark"]')
    ).toBeVisible();
  });

  test('bundle fetch failure shows error with Retry', async ({ page }) => {
    let callCount = 0;
    await mockBundles(page, () => {
      callCount += 1;
      if (callCount === 1) {
        return { status: 500 };
      }
      return {
        body: mockBundleWithTest(),
      };
    });

    await gotoViewTest(page, {
      testName: 'Mock Sample Test',
      dataset: 'mock-dataset',
    });

    await expect(page.locator('[data-testid="view-test-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="view-test-heading"]')).toHaveText(
      'Could not load test'
    );
    await expect(page.locator('[data-testid="view-test-retry"]')).toBeVisible();
    await expect(
      page.locator('[data-testid="view-test-back-to-benchmark"]')
    ).toBeVisible();

    await page.locator('[data-testid="view-test-retry"]').click();
    await expect(page.locator('[data-testid="view-test-details"]')).toBeVisible({
      timeout: 15000,
    });
    await expect(page.locator('[data-testid="view-test-name"]')).toHaveText(
      'Mock Sample Test'
    );
  });

  test('Adversarial Prompts sheet exposes CyberSecEval Learn More', { tag: '@happy-path' }, async ({
    page,
    context,
  }) => {
    await navigateToBenchmark(page);
    await openBundleSheet(page, ADVERSARIAL_BUNDLE);
    await expect(
      page.locator(`[data-testid="${CYBERSECEVAL_LEARN_MORE}"]`)
    ).toBeVisible();

    const popup = await openTestDetailsInNewTab(
      page,
      context,
      CYBERSECEVAL_LEARN_MORE
    );
    await expect(popup.locator('[data-testid="view-test-details"]')).toBeVisible({
      timeout: 15000,
    });
    await expect(popup.locator('[data-testid="view-test-name"]')).toHaveText(
      CYBERSECEVAL_TEST
    );
  });
});
