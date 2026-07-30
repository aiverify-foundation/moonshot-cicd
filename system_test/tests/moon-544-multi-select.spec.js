const { test, expect } = require('@playwright/test');

function escapeRegex(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

async function navigateToBenchmark(page) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.click('[data-testid="benchmark-link"]');
  await page.waitForLoadState('networkidle');
  await expect(page.locator('[data-testid="select-bundles-header"]')).toContainText('Select Test Bundles');
}

async function fetchBundles(request) {
  const response = await request.get('/api/bundles');
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  return data.bundles || [];
}

function pickTwoBundlesWithTests(bundles) {
  const eligible = bundles.filter((bundle) => Array.isArray(bundle.tests) && bundle.tests.length > 0);
  expect(eligible.length).toBeGreaterThan(1);
  return [eligible[0], eligible[1]];
}

function pickBundleWithAtLeastTwoTests(bundles) {
  const bundle = bundles.find((item) => Array.isArray(item.tests) && item.tests.length > 1);
  expect(bundle).toBeTruthy();
  return bundle;
}

function pickAnotherBundleWithTests(bundles, excludedId) {
  const bundle = bundles.find(
    (item) => item.id !== excludedId && Array.isArray(item.tests) && item.tests.length > 0
  );
  expect(bundle).toBeTruthy();
  return bundle;
}

async function selectBundleById(page, bundleId) {
  const toggle = page.locator(`[data-testid="toggle-${bundleId}"]`);
  await expect(toggle).toBeVisible();
  await toggle.click();
}

async function openBundleSheet(page, bundleName) {
  const card = page
    .locator('[data-testid^="bundle-card-"]')
    .filter({
      has: page.locator('[data-testid="bundle-name"]', { hasText: bundleName }),
    })
    .first();
  await expect(card).toBeVisible();
  await card.locator('[data-testid="learn-more-link"]').click();
  await expect(page.locator('[data-testid="bundle-details-sheet"]')).toBeVisible();
}

async function closeBundleSheet(page) {
  const sheet = page.locator('[data-testid="bundle-details-sheet"]');
  await sheet.getByRole('button', { name: 'Close' }).click();
  await expect(sheet).not.toBeVisible();
}

async function deselectFirstTestInBundleSheet(page) {
  const sheet = page.locator('[data-testid="bundle-details-sheet"]');
  const selectedButtons = sheet.locator('button[aria-label="Toggle test"]').filter({ hasText: 'Selected' });
  const count = await selectedButtons.count();
  expect(count).toBeGreaterThan(0);
  await selectedButtons.first().click();
}

async function clearAllTestsInBundleSheet(page) {
  const sheet = page.locator('[data-testid="bundle-details-sheet"]');
  const selectedButtons = sheet.locator('button[aria-label="Toggle test"]').filter({ hasText: 'Selected' });
  let remaining = await selectedButtons.count();
  while (remaining > 0) {
    await selectedButtons.first().click();
    remaining = await selectedButtons.count();
  }
}

async function selectOneTestInBundleSheet(page) {
  const sheet = page.locator('[data-testid="bundle-details-sheet"]');
  const unselectedButtons = sheet.locator('button[aria-label="Toggle test"]').filter({ hasText: 'Select' });
  expect(await unselectedButtons.count()).toBeGreaterThan(0);
  await unselectedButtons.first().click();
}

async function parseSidebarCount(page, bundleName) {
  const regex = new RegExp(`${escapeRegex(bundleName)}\\s*\\[(\\d+)\\/(\\d+)\\]`);
  const countLabel = page.locator('span.font-medium.text-sm').filter({ hasText: new RegExp(escapeRegex(bundleName)) }).first();
  await expect(countLabel).toBeVisible();
  const text = (await countLabel.textContent()) || '';
  const match = regex.exec(text);
  expect(match).toBeTruthy();
  return { selected: Number(match[1]), total: Number(match[2]) };
}

async function goToModelSelection(page) {
  await page.click('[data-testid="configure-and-run-benchmark-tests"]');
  await page.waitForLoadState('networkidle');
  await expect(page.locator('[data-testid="select-model-header"]')).toContainText('Configure And Run Tests');
}

async function configureRunPrerequisites(page) {
  const runName = `moon-544-${Date.now()}`;
  const testNameInput = page.locator('[data-testid="test-name-input"]');
  const testNameCard = page.locator('[data-testid="additional-card-title"]');
  if (!(await testNameInput.isVisible())) {
    await testNameCard.click();
  }
  await expect(testNameInput).toBeVisible();
  await testNameInput.fill(runName);

  const providerCombobox = page.locator('[data-testid="provider-combobox-trigger"]');
  await expect(providerCombobox).toBeVisible();
  await providerCombobox.click();
  const providerOptions = page.locator('[data-testid^="provider-option-"]');
  const customOptions = page.locator('[data-testid^="custom-connector-option-"]');

  if (await providerOptions.count()) {
    await providerOptions.first().click();
  } else {
    expect(await customOptions.count()).toBeGreaterThan(0);
    await customOptions.first().click();
  }

  await page.waitForTimeout(300);
  const modelCombobox = page.locator('[data-testid="model-combobox-trigger"]');
  await expect(modelCombobox).toBeVisible();
  await modelCombobox.click();

  const modelOptions = page.locator('[data-testid^="model-option-"]');
  const configOptions = page.locator('[data-testid^="config-option-"]');
  if (await modelOptions.count()) {
    await modelOptions.first().click();
  } else {
    expect(await configOptions.count()).toBeGreaterThan(0);
    await configOptions.first().click();
  }

  await expect(page.locator('[data-testid="run-benchmark-tests"]')).toBeEnabled();
}

test.describe('MOON-544 Multi-Bundle and Multi-Test Selection', () => {
  test('configure button is disabled when no bundles are selected', { tag: '@happy-path' }, async ({ page }) => {
    await navigateToBenchmark(page);

    await expect(page.locator('[data-testid="configure-and-run-benchmark-tests"]')).toBeDisabled();
    await expect(
      page.getByText('No bundles selected. Please select Test Bundles to view their tests.')
    ).toBeVisible();
  });

  test('selecting multiple bundles enables bulk progression', { tag: '@happy-path' }, async ({ page, request }) => {
    const bundles = await fetchBundles(request);
    const [bundleA, bundleB] = pickTwoBundlesWithTests(bundles);
    await navigateToBenchmark(page);

    await selectBundleById(page, bundleA.id);
    await selectBundleById(page, bundleB.id);

    await expect(page.locator(`[data-testid="toggle-${bundleA.id}"]`)).toContainText('Selected');
    await expect(page.locator(`[data-testid="toggle-${bundleB.id}"]`)).toContainText('Selected');
    await expect(page.locator('[data-testid="configure-and-run-benchmark-tests"]')).toBeEnabled();
    await expect(page.getByText(new RegExp(`${escapeRegex(bundleA.name)}\\s*\\[`))).toBeVisible();
    await expect(page.getByText(new RegExp(`${escapeRegex(bundleB.name)}\\s*\\[`))).toBeVisible();
  });

  test('deselecting one bundle keeps other selected bundles intact', { tag: '@happy-path' }, async ({ page, request }) => {
    const bundles = await fetchBundles(request);
    const [bundleA, bundleB] = pickTwoBundlesWithTests(bundles);
    await navigateToBenchmark(page);

    await selectBundleById(page, bundleA.id);
    await selectBundleById(page, bundleB.id);
    await selectBundleById(page, bundleA.id);

    await expect(page.locator(`[data-testid="toggle-${bundleA.id}"]`)).toContainText('Select');
    await expect(page.locator(`[data-testid="toggle-${bundleB.id}"]`)).toContainText('Selected');
    await expect(page.locator('[data-testid="configure-and-run-benchmark-tests"]')).toBeEnabled();
    await expect(page.getByText(new RegExp(`${escapeRegex(bundleA.name)}\\s*\\[`))).toHaveCount(0);
    await expect(page.getByText(new RegExp(`${escapeRegex(bundleB.name)}\\s*\\[`))).toBeVisible();
  });

  test('deselecting all selected bundles disables bulk progression', { tag: '@happy-path' }, async ({ page, request }) => {
    const bundles = await fetchBundles(request);
    const [bundleA, bundleB] = pickTwoBundlesWithTests(bundles);
    await navigateToBenchmark(page);

    await selectBundleById(page, bundleA.id);
    await selectBundleById(page, bundleB.id);
    await selectBundleById(page, bundleA.id);
    await selectBundleById(page, bundleB.id);

    await expect(page.locator('[data-testid="configure-and-run-benchmark-tests"]')).toBeDisabled();
    await expect(
      page.getByText('No bundles selected. Please select Test Bundles to view their tests.')
    ).toBeVisible();
  });

  test('selecting a bundle auto-selects all tests in that bundle', { tag: '@happy-path' }, async ({ page, request }) => {
    const bundles = await fetchBundles(request);
    const bundle = bundles.find((item) => Array.isArray(item.tests) && item.tests.length > 0);
    expect(bundle).toBeTruthy();
    await navigateToBenchmark(page);

    await selectBundleById(page, bundle.id);
    const counts = await parseSidebarCount(page, bundle.name);
    expect(counts.selected).toBe(bundle.tests.length);
    expect(counts.total).toBe(bundle.tests.length);
  });

  test('user can partially deselect tests in a selected bundle', { tag: '@happy-path' }, async ({ page, request }) => {
    const bundles = await fetchBundles(request);
    const bundle = pickBundleWithAtLeastTwoTests(bundles);
    await navigateToBenchmark(page);

    await selectBundleById(page, bundle.id);
    const before = await parseSidebarCount(page, bundle.name);
    await openBundleSheet(page, bundle.name);
    await deselectFirstTestInBundleSheet(page);
    await closeBundleSheet(page);

    const after = await parseSidebarCount(page, bundle.name);
    expect(before.selected).toBe(bundle.tests.length);
    expect(after.selected).toBe(bundle.tests.length - 1);
    expect(after.total).toBe(bundle.tests.length);
    await expect(page.locator('[data-testid="configure-and-run-benchmark-tests"]')).toBeEnabled();
  });

  test('user can manage tests independently across multiple bundles', { tag: '@happy-path' }, async ({ page, request }) => {
    const bundles = await fetchBundles(request);
    const bundleA = pickBundleWithAtLeastTwoTests(bundles);
    const bundleB = pickAnotherBundleWithTests(bundles, bundleA.id);
    await navigateToBenchmark(page);

    await selectBundleById(page, bundleA.id);
    await selectBundleById(page, bundleB.id);

    await openBundleSheet(page, bundleA.name);
    await deselectFirstTestInBundleSheet(page);
    await closeBundleSheet(page);

    const countA = await parseSidebarCount(page, bundleA.name);
    const countB = await parseSidebarCount(page, bundleB.name);
    expect(countA.selected).toBe(bundleA.tests.length - 1);
    expect(countA.total).toBe(bundleA.tests.length);
    expect(countB.selected).toBe(bundleB.tests.length);
    expect(countB.total).toBe(bundleB.tests.length);
  });

  test('bundle details sheet supports per-test bulk curation before adding', { tag: '@happy-path' }, async ({ page, request }) => {
    const bundles = await fetchBundles(request);
    const bundle = pickBundleWithAtLeastTwoTests(bundles);
    await navigateToBenchmark(page);
    await openBundleSheet(page, bundle.name);

    const sheet = page.locator('[data-testid="bundle-details-sheet"]');
    const addButton = sheet.getByRole('button', { name: /^Add/ });
    await expect(addButton).toContainText(`Add ${bundle.tests.length} tests`);
    await expect(addButton).toBeEnabled();

    await clearAllTestsInBundleSheet(page);
    await expect(addButton).toContainText('Add tests');
    await expect(addButton).toBeDisabled();

    await selectOneTestInBundleSheet(page);
    await expect(addButton).toContainText('Add 1 test');
    await expect(addButton).toBeEnabled();
  });

  test('run request with full selections across multiple bundles omits tests_by_bundle', { tag: '@happy-path' }, async ({ page, request }) => {
    const bundles = await fetchBundles(request);
    const [bundleA, bundleB] = pickTwoBundlesWithTests(bundles);
    await navigateToBenchmark(page);

    await selectBundleById(page, bundleA.id);
    await selectBundleById(page, bundleB.id);
    await goToModelSelection(page);
    await configureRunPrerequisites(page);

    let capturedPayload;
    await page.route('**/api/start-benchmark-run', async (route) => {
      capturedPayload = JSON.parse(route.request().postData() || '{}');
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'ok' }),
      });
    });

    await page.click('[data-testid="run-benchmark-tests"]');
    await expect.poll(() => capturedPayload, { timeout: 15000 }).toBeTruthy();
    expect(capturedPayload.bundle_names).toEqual(
      expect.arrayContaining([bundleA.id, bundleB.id])
    );
    expect(capturedPayload.tests_by_bundle).toBeUndefined();
  });

  test('run request with partial selection includes tests_by_bundle only for partial bundle', { tag: '@happy-path' }, async ({ page, request }) => {
    const bundles = await fetchBundles(request);
    const bundleA = pickBundleWithAtLeastTwoTests(bundles);
    const bundleB = pickAnotherBundleWithTests(bundles, bundleA.id);
    const expectedSelectedIds = bundleA.tests
      .slice(1)
      .map((bundleTest) => bundleTest.benchmark_test_id)
      .filter((value) => value != null);
    expect(expectedSelectedIds.length).toBeGreaterThan(0);

    await navigateToBenchmark(page);
    await selectBundleById(page, bundleA.id);
    await selectBundleById(page, bundleB.id);
    await openBundleSheet(page, bundleA.name);
    await deselectFirstTestInBundleSheet(page);
    await closeBundleSheet(page);
    await goToModelSelection(page);
    await configureRunPrerequisites(page);

    let capturedPayload;
    await page.route('**/api/start-benchmark-run', async (route) => {
      capturedPayload = JSON.parse(route.request().postData() || '{}');
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'ok' }),
      });
    });

    await page.click('[data-testid="run-benchmark-tests"]');
    await expect.poll(() => capturedPayload, { timeout: 15000 }).toBeTruthy();
    expect(capturedPayload.bundle_names).toEqual(
      expect.arrayContaining([bundleA.id, bundleB.id])
    );
    expect(capturedPayload.tests_by_bundle).toBeTruthy();
    expect(Object.keys(capturedPayload.tests_by_bundle)).toEqual([bundleA.id]);
    expect(capturedPayload.tests_by_bundle[bundleA.id]).toEqual(
      expect.arrayContaining(expectedSelectedIds)
    );
    expect(capturedPayload.tests_by_bundle[bundleA.id]).toHaveLength(expectedSelectedIds.length);
    expect(capturedPayload.tests_by_bundle[bundleB.id]).toBeUndefined();
  });

  test('returning from model selection preserves selected bundles and tests', { tag: '@happy-path' }, async ({ page, request }) => {
    const bundles = await fetchBundles(request);
    const bundleA = pickBundleWithAtLeastTwoTests(bundles);
    const bundleB = pickAnotherBundleWithTests(bundles, bundleA.id);
    await navigateToBenchmark(page);

    await selectBundleById(page, bundleA.id);
    await selectBundleById(page, bundleB.id);
    await openBundleSheet(page, bundleA.name);
    await deselectFirstTestInBundleSheet(page);
    await closeBundleSheet(page);

    const beforeA = await parseSidebarCount(page, bundleA.name);
    const beforeB = await parseSidebarCount(page, bundleB.name);

    await goToModelSelection(page);
    await page.click('[data-testid="back-to-bundles-button"]');
    await expect(page.locator('[data-testid="select-bundles-header"]')).toContainText('Select Test Bundles');

    const afterA = await parseSidebarCount(page, bundleA.name);
    const afterB = await parseSidebarCount(page, bundleB.name);
    expect(afterA).toEqual(beforeA);
    expect(afterB).toEqual(beforeB);
    await expect(page.locator('[data-testid="configure-and-run-benchmark-tests"]')).toBeEnabled();
  });
});
