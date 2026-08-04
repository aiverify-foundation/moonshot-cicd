const { expect } = require('@playwright/test');

/** Navigate landing → select first bundle → model selection page. */
async function navigateToModelSelection(page) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.click('[data-testid="benchmark-link"]');
  await page.waitForLoadState('networkidle');
  await page.waitForSelector('[data-testid^="toggle-"]', { timeout: 10000 });
  const toggleButtons = page.locator('[data-testid^="toggle-"]');
  await toggleButtons.first().click();
  await page.waitForTimeout(500);
  const configureButton = page.locator('[data-testid="configure-and-run-benchmark-tests"]');
  await configureButton.click();
  await page.waitForLoadState('networkidle');
  await expect(page.locator('[data-testid="select-model-header"]')).toContainText(
    'Configure And Run Tests'
  );
}

async function fillInTestName(page, testName) {
  const testNameCard = page.locator('[data-testid="additional-card-title"]');
  await expect(testNameCard).toBeVisible();
  const testNameInput = page.locator('[data-testid="test-name-input"]');
  const isInputVisible = await testNameInput.isVisible().catch(() => false);
  if (!isInputVisible) {
    await testNameCard.click();
  }
  await expect(testNameInput).toBeVisible();
  await testNameInput.fill(testName);
}

async function expandModelSelectionCard(page) {
  const cardTitle = page.locator('[data-testid="card-title"]');
  await expect(cardTitle).toBeVisible();
  await expect(cardTitle).toContainText('Select App or Model Under Test');
  const providerCombobox = page.locator('[data-testid="provider-combobox-trigger"]');
  const isComboboxVisible = await providerCombobox.isVisible().catch(() => false);
  if (!isComboboxVisible) {
    await cardTitle.click();
  }
  await expect(providerCombobox).toBeVisible();
}

async function getToModelSelectionCard(page) {
  await navigateToModelSelection(page);
  await fillInTestName(page, 'My Test Benchmark');
  await expandModelSelectionCard(page);
}

async function selectStandardProviderWithModels(page) {
  await page.click('[data-testid="provider-combobox-trigger"]');
  await page.waitForSelector('[data-testid^="provider-option-"]', { timeout: 5000 });
  await page.locator('[data-testid^="provider-option-"]').first().click();
  await page.waitForTimeout(500);
}

/**
 * Select a standard provider by visible name (e.g. /OpenAI/i or /Together/i).
 * @param {import('@playwright/test').Page} page
 * @param {RegExp|string} namePattern
 */
async function selectProviderByName(page, namePattern) {
  await page.click('[data-testid="provider-combobox-trigger"]');
  await page.waitForSelector('[data-testid^="provider-option-"]', { timeout: 5000 });
  const option = page
    .locator('[data-testid^="provider-option-"]')
    .filter({ hasText: namePattern })
    .first();
  await expect(option).toBeVisible({ timeout: 10000 });
  await option.click();
  await page.waitForTimeout(500);
}

async function openModelDropdownWithOptions(page) {
  await page.click('[data-testid="model-combobox-trigger"]');
  await page.waitForSelector('[data-testid^="model-option-"]', { timeout: 10000 });
}

function editModelSheet(page) {
  return page.getByTestId('edit-model-sheet');
}

/** Visible sheet title (avoids sr-only SheetTitle; works without title testid in stale builds). */
function editModelSheetTitle(sheet) {
  return sheet
    .locator('h2.text-lg.font-semibold')
    .filter({ hasText: 'Edit Model Configuration' });
}

async function waitForEditModelSheetReady(page) {
  const sheet = editModelSheet(page);
  await expect(sheet).toBeVisible({ timeout: 10000 });
  await expect(sheet.locator('#modelConfig')).toBeVisible({ timeout: 10000 });
  await expect(editModelSheetTitle(sheet)).toBeVisible();
  return sheet;
}

async function openAddNewModelSheet(page) {
  await page.click('[data-testid="model-combobox-trigger"]');
  const addNew = page.locator('[data-testid="add-new-model-from-dropdown"]');
  await expect(addNew).toBeVisible({ timeout: 10000 });
  await addNew.click();
  await waitForEditModelSheetReady(page);
}

async function openEditFirstModelSheet(page) {
  await openModelDropdownWithOptions(page);
  const firstEditButton = page.locator('[data-testid^="edit-model-"]').first();
  await expect(firstEditButton).toBeVisible();
  await firstEditButton.click();
  await waitForEditModelSheetReady(page);
}

/**
 * Open edit for a model option whose label contains `namePattern`.
 * @param {import('@playwright/test').Page} page
 * @param {RegExp|string} namePattern
 */
async function openEditModelSheetByName(page, namePattern) {
  await openModelDropdownWithOptions(page);
  const option = page
    .locator('[data-testid^="model-option-"]')
    .filter({ hasText: namePattern })
    .first();
  await expect(option).toBeVisible({ timeout: 10000 });
  await option.locator('[data-testid^="edit-model-"]').click();
  await waitForEditModelSheetReady(page);
}

/**
 * Mock POST /api/providers/test-connection for deterministic pass/fail.
 * @returns {Promise<{ getLastRequestBody: () => object|null }>}
 */
async function mockTestConnection(page, { success = true, error = null, delayMs = 0 } = {}) {
  let lastBody = null;
  await page.route('**/api/providers/test-connection', async (route) => {
    try {
      lastBody = route.request().postDataJSON();
    } catch {
      lastBody = null;
    }
    if (delayMs) {
      await new Promise((r) => setTimeout(r, delayMs));
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success,
        error: success ? null : error || 'Connection test failed',
        response_preview: success ? 'OK' : null,
      }),
    });
  });
  return {
    getLastRequestBody: () => lastBody,
  };
}

/**
 * Resolve OpenAI provider id from GET /api/providers.
 * @param {import('@playwright/test').APIRequestContext} request
 */
async function fetchProviderBySystemName(request, systemName) {
  const response = await request.get('/api/providers');
  expect(response.ok()).toBeTruthy();
  const providers = await response.json();
  const row = (Array.isArray(providers) ? providers : []).find(
    (p) => p.system_name === systemName
  );
  expect(row).toBeTruthy();
  return row;
}

/**
 * Store an API key for a provider so latest-details reports api_key_configured.
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {number|string} providerId
 * @param {string} apiKey
 */
async function setProviderApiKey(request, providerId, apiKey = 'sk-e2e-fake-key') {
  const response = await request.post(`/api/providers/${providerId}/api-key`, {
    data: { api_key: apiKey },
  });
  expect(response.ok()).toBeTruthy();
}

module.exports = {
  navigateToModelSelection,
  fillInTestName,
  expandModelSelectionCard,
  getToModelSelectionCard,
  selectStandardProviderWithModels,
  selectProviderByName,
  openModelDropdownWithOptions,
  openAddNewModelSheet,
  openEditFirstModelSheet,
  openEditModelSheetByName,
  editModelSheet,
  editModelSheetTitle,
  mockTestConnection,
  fetchProviderBySystemName,
  setProviderApiKey,
};
