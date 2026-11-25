/**
 * Portal navigation for extension tests running against an isolated API instance.
 *
 * The shared helpers in modelSelection.js / bundleSelection.js call page.goto('/'), which
 * uses the Playwright config baseURL (:8000). These helpers take the instance baseURL
 * explicitly and route the portal's hardcoded localhost:8000 calls to it.
 */
const { expect } = require('@playwright/test');
const { routePortalApiTo } = require('./extensionServer');
const {
  fillInTestName,
  expandModelSelectionCard,
  selectProviderByName,
  openEditFirstModelSheet,
} = require('./modelSelection');

async function openPortal(page, baseURL) {
  await routePortalApiTo(page, baseURL);
  await page.goto(`${baseURL}/`);
  await page.waitForLoadState('networkidle');
}

/** Landing → Benchmark → select one bundle → "Configure And Run Tests". */
async function openConfigureForBundle(page, baseURL, bundleId) {
  await openPortal(page, baseURL);
  await page.click('[data-testid="benchmark-link"]');
  await page.waitForLoadState('networkidle');
  const toggle = page.locator(`[data-testid="toggle-${bundleId}"]`);
  await expect(toggle).toBeVisible({ timeout: 15000 });
  await toggle.click();
  await page.waitForTimeout(500);
  await page.locator('[data-testid="configure-and-run-benchmark-tests"]').click();
  await page.waitForLoadState('networkidle');
  await expect(page.locator('[data-testid="select-model-header"]')).toContainText(
    'Configure And Run Tests'
  );
}

/**
 * Open the first model config of a provider and press "Test Connection" in the edit sheet.
 * Assertions on the result are left to the caller.
 */
async function pressTestConnectionForProvider(page, baseURL, bundleId, providerName) {
  await openConfigureForBundle(page, baseURL, bundleId);
  await fillInTestName(page, 'E2E extension connection test');
  await expandModelSelectionCard(page);
  await selectProviderByName(page, providerName);
  await openEditFirstModelSheet(page);
  // The sheet alerts instead of testing when no token is typed. The stub ignores the value.
  await page.locator('#token').fill('e2e-stub-token');
  await page.getByTestId('edit-model-test-connection').click();
  await expect(page.getByTestId('edit-model-test-result')).toBeVisible({ timeout: 30000 });
}

module.exports = {
  openPortal,
  openConfigureForBundle,
  pressTestConnectionForProvider,
};
