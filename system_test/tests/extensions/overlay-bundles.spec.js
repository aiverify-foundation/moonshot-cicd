/**
 * Claims: with no usable overlay the custom route matches the built-in route (S1-S3, S12, F8).
 * Each test starts its own API instances, so the shared :8000 stack is not used.
 */
const { test, expect } = require('@playwright/test');
const { withOverlayApi } = require('../../utils/extensionOverlay');
const { bundleNames } = require('../../utils/extensionRuns');
const { openPortal } = require('../../utils/extensionPortal');
const {
  OVERLAY_BUNDLE_NAME,
  OVERLAY_BUNDLE_ID,
  METRIC_BUNDLE_NAME,
} = require('../../utils/extensionOverlay');

const RESEED_MARKER = 'Test config file changed or first run';
const sorted = (names) => [...names].sort();

test.setTimeout(360000);

test.describe('overlay bundles follow the MOON807 gate and overlay presence', () => {
  test('overlay on adds the overlay bundles and the portal lists them', async ({ page, request }) => {
    const baseline = await withOverlayApi({ flagOn: true, overlay: null }, (api) =>
      bundleNames(request, api.baseURL)
    );

    await withOverlayApi({ flagOn: true, overlay: 'valid' }, async (api) => {
      const names = await bundleNames(request, api.baseURL);
      expect(sorted(names)).toEqual(sorted([...baseline, OVERLAY_BUNDLE_NAME, METRIC_BUNDLE_NAME]));

      await openPortal(page, api.baseURL);
      await page.click('[data-testid="benchmark-link"]');
      await page.waitForLoadState('networkidle');
      await expect(page.locator(`[data-testid="bundle-card-${OVERLAY_BUNDLE_ID}"]`)).toBeVisible({
        timeout: 15000,
      });
    });
  });

  test('flag off ignores an overlay that is present on disk', async ({ request }) => {
    const baseline = await withOverlayApi({ flagOn: false, overlay: null }, (api) =>
      bundleNames(request, api.baseURL)
    );

    await withOverlayApi({ flagOn: false, overlay: 'valid' }, async (api) => {
      const names = await bundleNames(request, api.baseURL);
      expect(sorted(names)).toEqual(sorted(baseline));
      expect(names).not.toContain(OVERLAY_BUNDLE_NAME);
    });
  });

  test('an overlay directory env var that points at a missing path behaves like no overlay', async ({
    request,
  }) => {
    const baseline = await withOverlayApi({ flagOn: true, overlay: null }, (api) =>
      bundleNames(request, api.baseURL)
    );

    await withOverlayApi({ flagOn: true, overlay: 'valid' }, async (api) => {
      expect(await bundleNames(request, api.baseURL)).toContain(OVERLAY_BUNDLE_NAME);

      api.overlayDir = `${api.root}/does-not-exist`;
      await api.restart();

      expect(sorted(await bundleNames(request, api.baseURL))).toEqual(sorted(baseline));
    });
  });

  test('removing the overlay and restarting restores the baseline, then does not reseed again', async ({
    request,
  }) => {
    const baseline = await withOverlayApi({ flagOn: true, overlay: null }, (api) =>
      bundleNames(request, api.baseURL)
    );

    await withOverlayApi({ flagOn: true, overlay: 'valid' }, async (api) => {
      expect(await bundleNames(request, api.baseURL)).toContain(OVERLAY_BUNDLE_NAME);

      api.removeOverlayDir();
      const beforeRemovalRestart = api.logOffset();
      await api.restart();

      expect(sorted(await bundleNames(request, api.baseURL))).toEqual(sorted(baseline));
      // The first start without the overlay reseeds once (S1e, S1g).
      expect(api.logSince(beforeRemovalRestart)).toContain(RESEED_MARKER);

      const beforeSecondRestart = api.logOffset();
      await api.restart();
      expect(api.logSince(beforeSecondRestart)).not.toContain(RESEED_MARKER);
      expect(sorted(await bundleNames(request, api.baseURL))).toEqual(sorted(baseline));
    });
  });
});
