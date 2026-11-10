const { expect } = require('@playwright/test');

const MOON771_FLAG = 'AIVET_OCT2026_MOON771';

// Keep in sync with moonshot_portal_app/lib/productBranding.ts (getHeaderProductName).
const PRODUCT_NAME_AIVET_HEADER = 'Evals Toolkit';
const PRODUCT_NAME_LEGACY = 'Moonshot';

/**
 * @param {Record<string, boolean> | undefined} flags
 * @returns {string}
 */
function productNameFromFlags(flags) {
  return flags?.[MOON771_FLAG] === true ? PRODUCT_NAME_AIVET_HEADER : PRODUCT_NAME_LEGACY;
}

/**
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<{ flags: Record<string, boolean>, productName: string }>}
 */
async function goToLandingWithFlags(page) {
  const flagsResponsePromise = page.waitForResponse(
    (resp) => resp.url().includes('/api/feature-flags') && resp.ok()
  );

  await page.goto('/');

  const flagsResponse = await flagsResponsePromise;
  const body = await flagsResponse.json();
  const flags = body.flags ?? {};
  const productName = productNameFromFlags(flags);

  await page.waitForLoadState('networkidle');
  await expect(page.locator('h1')).toHaveText(productName);

  return { flags, productName };
}

/**
 * @param {import('@playwright/test').Page} page
 * @param {string} productName
 * @param {'wiki' | 'issues' | 'GitHub repository'} kind
 */
function headerLink(page, productName, kind) {
  return page.getByLabel(`Open ${productName} ${kind}`);
}

module.exports = {
  MOON771_FLAG,
  productNameFromFlags,
  goToLandingWithFlags,
  headerLink,
};
