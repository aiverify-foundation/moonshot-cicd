/**
 * Claims: a built-in adapter wins over an overlay adapter with the same name; the collision is
 * logged; the rest of the overlay stays active (F2).
 */
const path = require('path');
const { test, expect } = require('@playwright/test');
const { withOverlayApi, writeText, OVERLAY_BUNDLE_NAME } = require('../../utils/extensionOverlay');
const { bundleNames } = require('../../utils/extensionRuns');

test.setTimeout(360000);

// If this file were ever imported, the import itself would fail, so a passing score label
// request proves the built-in accuracy adapter was used.
const COLLIDING_ADAPTER = `raise RuntimeError("overlay accuracy_adapter must not be loaded")\n`;

async function scoreLabels(request, baseURL) {
  const response = await request.get(`${baseURL}/api/metrics/accuracy_adapter/score-result-names`);
  expect(response.status()).toBe(200);
  return response.json();
}

test.describe('adapter name collisions', () => {
  test('an overlay adapter named like a built-in adapter is ignored and logged', async ({ request }) => {
    const baseline = await withOverlayApi({ flagOn: true, overlay: null }, (api) =>
      scoreLabels(request, api.baseURL)
    );

    await withOverlayApi(
      {
        flagOn: true,
        overlay: 'valid',
        prepare: (api) => {
          writeText(path.join(api.overlayPath, 'adapters', 'metric', 'accuracy_adapter.py'), COLLIDING_ADAPTER);
        },
      },
      async (api) => {
        expect(await scoreLabels(request, api.baseURL)).toEqual(baseline);
        expect(api.logText()).toContain('has the same name as built-in adapter');
        // The collision affects only the colliding adapter; the overlay bundle stays active.
        expect(await bundleNames(request, api.baseURL)).toContain(OVERLAY_BUNDLE_NAME);
      }
    );
  });
});
