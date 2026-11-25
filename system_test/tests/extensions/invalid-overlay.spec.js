/**
 * Claims: an invalid overlay is dropped as a whole; the built-in benchmarks, datasets and config
 * keep working; the API still starts (F1, F6). The reason is logged.
 */
const { test, expect } = require('@playwright/test');
const { withOverlayApi, INVALID_OVERLAY_KINDS, OVERLAY_BUNDLE_NAME } = require('../../utils/extensionOverlay');
const { bundleNames } = require('../../utils/extensionRuns');

test.setTimeout(360000);

const sorted = (names) => [...names].sort();

test.describe('invalid overlays are ignored as a whole', () => {
  for (const kind of Object.keys(INVALID_OVERLAY_KINDS)) {
    test(`invalid overlay (${kind}) is ignored, logged, and built-in config still works`, async ({ request }) => {
      const baseline = await withOverlayApi({ flagOn: false, overlay: null }, (api) =>
        bundleNames(request, api.baseURL)
      );

      await withOverlayApi({ flagOn: true, overlay: 'invalid', invalidKind: kind }, async (api) => {
        // The API started, so the process survived the overlay error.
        const names = await bundleNames(request, api.baseURL);
        expect(sorted(names)).toEqual(sorted(baseline));
        expect(names).not.toContain(OVERLAY_BUNDLE_NAME);

        expect(api.logText()).toContain('Ignoring benchmark extensions overlay at');

        // Built-in metric config is intact.
        const labels = await request.get(`${api.baseURL}/api/metrics/accuracy_adapter/score-result-names`);
        expect(labels.status()).toBe(200);
      });
    });
  }
});
