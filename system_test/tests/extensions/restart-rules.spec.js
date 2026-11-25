/**
 * Claims: the restart rules in the verification doc (F4, invalid-overlay decision per process).
 *   - An overlay shared.yaml edit is seeded by POST /api/seed-shared-config-if-changed without a restart.
 *   - A run's worker process reads the overlay moonshot_config.yaml when it starts, so a metric entry added
 *     to the overlay config is used by the next run without a restart (F4, F13). The API process itself
 *     keeps the config it read at start-up.
 *   - An overlay marked invalid stays ignored for the life of the process, even after it is fixed.
 */
const path = require('path');
const { test, expect } = require('@playwright/test');
const { withOverlayApi, buildOverlay, writeText, configYaml, sharedYaml, OVERLAY_BUNDLE_NAME, METRIC_BUNDLE_NAME, OK_SYSTEM_NAME } = require('../../utils/extensionOverlay');
const { bundleNames, runPrompts, startRun, waitForRun, uniqueName } = require('../../utils/extensionRuns');

const MISSING_METRIC_LOG = 'Metric config not found for extension_example_metric_adapter';

test.setTimeout(480000);

async function reseedEndpoint(request, baseURL) {
  const response = await request.post(`${baseURL}/api/seed-shared-config-if-changed`);
  expect(response.status()).toBe(200);
  return response.json();
}

test.describe('restart rules for overlay edits', () => {
  test('an edited overlay shared.yaml is seeded without a restart, and a run picks up a new metric config', async ({
    request,
  }) => {
    await withOverlayApi({ flagOn: true, overlay: 'valid', overlayOptions: { withExtensionMetric: false } }, async (api) => {
      const before = await bundleNames(request, api.baseURL);
      expect(before).toContain(OVERLAY_BUNDLE_NAME);
      expect(before).not.toContain(METRIC_BUNDLE_NAME);

      // Add the metric bundle to the overlay shared.yaml, but not its metric config yet.
      writeText(
        path.join(api.overlayPath, 'test_configs', 'shared.yaml'),
        sharedYaml({ withExtensionMetric: true })
      );
      const reseed = await reseedEndpoint(request, api.baseURL);
      expect(reseed.seeded).toBe(true);
      expect(await bundleNames(request, api.baseURL)).toContain(METRIC_BUNDLE_NAME);

      // The bundle is seeded, but there is no metrics entry for it, so the run logs the error.
      // The run row still ends as "completed", because each prompt records the error.
      const firstOffset = api.logOffset();
      const firstRun = uniqueName('e2e-no-metric-config');
      await startRun(request, api.baseURL, {
        bundleName: METRIC_BUNDLE_NAME,
        providerSystemName: OK_SYSTEM_NAME,
        runName: firstRun,
      });
      await waitForRun(request, api.baseURL, firstRun);
      expect(api.logSince(firstOffset)).toContain(MISSING_METRIC_LOG);

      // Add the metrics entry to the overlay config without restarting the API.
      writeText(path.join(api.overlayPath, 'moonshot_config.yaml'), configYaml({ withExtensionMetric: true }));
      const secondOffset = api.logOffset();
      const secondRun = uniqueName('e2e-config-reread-by-worker');
      await startRun(request, api.baseURL, {
        bundleName: METRIC_BUNDLE_NAME,
        providerSystemName: OK_SYSTEM_NAME,
        runName: secondRun,
      });
      const completed = await waitForRun(request, api.baseURL, secondRun);
      expect(completed.status).toBe('completed');
      expect(api.logSince(secondOffset)).not.toContain(MISSING_METRIC_LOG);
      const prompts = await runPrompts(request, api.baseURL, completed.id);
      expect(prompts.length).toBeGreaterThan(0);
      for (const prompt of prompts) {
        expect(String(prompt.prediction_result)).toContain('OK');
      }
    });
  });

  test('an invalid overlay stays ignored after it is fixed, until the API restarts', async ({ request }) => {
    await withOverlayApi({ flagOn: true, overlay: 'invalid', invalidKind: 'malformed-config' }, async (api) => {
      expect(await bundleNames(request, api.baseURL)).not.toContain(OVERLAY_BUNDLE_NAME);

      // Fix the overlay on disk, then ask for a reseed while the process keeps running.
      buildOverlay(api.overlayPath, { withExtensionMetric: true });
      await reseedEndpoint(request, api.baseURL);
      const whileRunning = await bundleNames(request, api.baseURL);
      expect(whileRunning).not.toContain(OVERLAY_BUNDLE_NAME);
      expect(whileRunning).not.toContain(METRIC_BUNDLE_NAME);

      await api.restart();
      const afterRestart = await bundleNames(request, api.baseURL);
      expect(afterRestart).toContain(OVERLAY_BUNDLE_NAME);
      expect(afterRestart).toContain(METRIC_BUNDLE_NAME);
    });
  });
});
