const { expect } = require('@playwright/test');

function escapeRegex(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function exactTextRegex(value) {
  return new RegExp(`^${escapeRegex(value)}$`);
}

/**
 * Locate a single bundle card by id (preferred) or exact display name.
 * @param {import('@playwright/test').Page} page
 * @param {{ id?: string, name?: string|RegExp }} [opts]
 */
async function bundleCard(page, { id, name } = {}) {
  await page.waitForSelector('[data-testid^="bundle-card-"]', {
    timeout: 15000,
  });

  if (id != null && id !== '') {
    const card = page.locator(`[data-testid="bundle-card-${id}"]`);
    await expect(card).toHaveCount(1);
    return card;
  }

  if (name == null) {
    throw new Error('bundleCard requires id or name');
  }

  const namePattern = name instanceof RegExp ? name : exactTextRegex(name);
  const card = page.locator('[data-testid^="bundle-card-"]').filter({
    has: page.locator('[data-testid="bundle-name"]', { hasText: namePattern }),
  });
  await expect(card).toHaveCount(1);
  return card;
}

/**
 * Open the bundle details sheet via Learn more.
 * Prefer `{ id, name }` when both are known so the card is unambiguous and the title is asserted.
 * @param {import('@playwright/test').Page} page
 * @param {{ id?: string, name?: string|RegExp }} [opts]
 */
async function openBundleSheet(page, { id, name } = {}) {
  const card = await bundleCard(page, { id, name });
  await card.locator('[data-testid="learn-more-link"]').click();
  await expect(page.locator('[data-testid="bundle-details-sheet"]')).toBeVisible();
  if (typeof name === 'string') {
    await expect(page.locator('[data-testid="bundle-details-name"]')).toHaveText(
      name
    );
  }
  return card;
}

/**
 * Sidebar badge text is "{name} [{selected}/{total}]".
 * @param {import('@playwright/test').Page} page
 * @param {string} bundleName
 */
function sidebarBundleLabel(page, bundleName) {
  const pattern = new RegExp(
    `^${escapeRegex(bundleName)}\\s*\\[\\d+\\/\\d+\\]$`
  );
  return page.locator('span.font-medium.text-sm').filter({ hasText: pattern });
}

/**
 * @param {import('@playwright/test').Page} page
 * @param {string} bundleName
 * @returns {Promise<{ selected: number, total: number }>}
 */
async function parseSidebarCount(page, bundleName) {
  const countLabel = sidebarBundleLabel(page, bundleName);
  await expect(countLabel).toHaveCount(1);
  await expect(countLabel).toBeVisible();
  const text = ((await countLabel.textContent()) || '').trim();
  const match = new RegExp(
    `^${escapeRegex(bundleName)}\\s*\\[(\\d+)\\/(\\d+)\\]$`
  ).exec(text);
  expect(match).toBeTruthy();
  return { selected: Number(match[1]), total: Number(match[2]) };
}

/**
 * @param {import('@playwright/test').Page} page
 * @param {string} bundleId
 */
async function selectBundleById(page, bundleId) {
  const toggle = page.locator(`[data-testid="toggle-${bundleId}"]`);
  await expect(toggle).toBeVisible();
  await toggle.click();
}

/**
 * Resolve a bundle from GET /api/bundles by exact display name.
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {string} bundleName
 */
async function findBundleByName(request, bundleName) {
  const response = await request.get('/api/bundles');
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  const bundle = (data.bundles || []).find((row) => row.name === bundleName);
  if (!bundle) {
    throw new Error(`Bundle not found in /api/bundles: ${bundleName}`);
  }
  return bundle;
}

module.exports = {
  escapeRegex,
  exactTextRegex,
  bundleCard,
  openBundleSheet,
  sidebarBundleLabel,
  parseSidebarCount,
  selectBundleById,
  findBundleByName,
};
