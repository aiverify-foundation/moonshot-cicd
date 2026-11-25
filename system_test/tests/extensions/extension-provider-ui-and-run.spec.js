/**
 * Claims: an extension connector from providers.json can be chosen in the portal, connection-tested,
 * and used for a real benchmark run (F9, and the "real run" gap in the verification doc).
 * The stub connectors answer "OK" or always fail, so no external service or API key is needed.
 */
const { test, expect } = require('@playwright/test');
const { ExtensionApi } = require('../../utils/extensionServer');
const {
  buildOverlay,
  withOverlayApi,
  OK_PROVIDER,
  ERROR_PROVIDER,
  OK_SYSTEM_NAME,
  ERROR_SYSTEM_NAME,
  OVERLAY_BUNDLE_NAME,
  OVERLAY_BUNDLE_ID,
} = require('../../utils/extensionOverlay');
const {
  createModelConfig,
  findProvider,
  getJson,
  runPrompts,
  startRun,
  uniqueName,
  waitForRun,
} = require('../../utils/extensionRuns');
const { pressTestConnectionForProvider } = require('../../utils/extensionPortal');

test.setTimeout(480000);

/** Each provider needs one model config before the portal's model dropdown has an entry. */
async function seedModelConfigs(request, baseURL) {
  for (const systemName of [OK_SYSTEM_NAME, ERROR_SYSTEM_NAME]) {
    const provider = await findProvider(request, baseURL, systemName);
    expect(provider, `${systemName} is listed`).toBeTruthy();
    await createModelConfig(request, baseURL, Number(provider.id), provider.defaultModel);
  }
}

test.describe('extension provider in the portal and in runs', () => {
  test('the OK stub connection test passes in the portal', async ({ page, request }) => {
    await withOverlayApi({ flagOn: true, overlay: 'valid' }, async (api) => {
      await seedModelConfigs(request, api.baseURL);
      await pressTestConnectionForProvider(page, api.baseURL, OVERLAY_BUNDLE_ID, OK_PROVIDER.name);
      await expect(page.getByTestId('edit-model-test-result')).toContainText('Test Passed');
    });
  });

  test('the error stub connection test fails in the portal', async ({ page, request }) => {
    await withOverlayApi({ flagOn: true, overlay: 'valid' }, async (api) => {
      await seedModelConfigs(request, api.baseURL);
      await pressTestConnectionForProvider(page, api.baseURL, OVERLAY_BUNDLE_ID, ERROR_PROVIDER.name);
      await expect(page.getByTestId('edit-model-test-result')).toContainText('Test Failed');
    });
  });

  test('a run with the OK stub completes and every prompt is answered OK', async ({ request }) => {
    await withOverlayApi({ flagOn: true, overlay: 'valid' }, async (api) => {
      const runName = uniqueName('e2e-ok-run');
      await startRun(request, api.baseURL, {
        bundleName: OVERLAY_BUNDLE_NAME,
        providerSystemName: OK_SYSTEM_NAME,
        runName,
      });
      const run = await waitForRun(request, api.baseURL, runName);
      expect(run.status).toBe('completed');

      const prompts = await runPrompts(request, api.baseURL, run.id);
      expect(prompts.length).toBeGreaterThan(0);
      for (const prompt of prompts) {
        expect(String(prompt.prediction_result)).toContain('OK');
      }

      const results = await getJson(request, `${api.baseURL}/api/benchmark-runs/${run.id}/results`);
      expect(results.status).toBe(200);
    });
  });

  test('a run with the error stub never produces an OK answer', async ({ request }) => {
    await withOverlayApi({ flagOn: true, overlay: 'valid' }, async (api) => {
      const runName = uniqueName('e2e-error-run');
      await startRun(request, api.baseURL, {
        bundleName: OVERLAY_BUNDLE_NAME,
        providerSystemName: ERROR_SYSTEM_NAME,
        runName,
      });
      const run = await waitForRun(request, api.baseURL, runName);
      const prompts = await runPrompts(request, api.baseURL, run.id);
      for (const prompt of prompts) {
        expect(String(prompt.prediction_result ?? '')).not.toContain('OK');
      }
    });
  });

  test('after the overlay is removed, a past run of the extension provider cannot be rerun (F14, current behaviour)', async ({
    request,
  }) => {
    const api = new ExtensionApi({ flagOn: true });
    try {
      buildOverlay(api.overlayPath);
      api.overlayDir = api.overlayPath;
      await api.start();

      const runName = uniqueName('e2e-f14-run');
      await startRun(request, api.baseURL, {
        bundleName: OVERLAY_BUNDLE_NAME,
        providerSystemName: OK_SYSTEM_NAME,
        runName,
      });
      const run = await waitForRun(request, api.baseURL, runName);
      expect(run.status).toBe('completed');
      const [firstPrompt] = await runPrompts(request, api.baseURL, run.id);

      // Remove the overlay and restart: the provider is hidden, but the run row stays.
      await api.stop();
      api.removeOverlayDir();
      await api.start();

      const history = await getJson(request, `${api.baseURL}/api/benchmark-runs/${run.id}`);
      expect(history.status).toBe(200);

      // Rerun rebuilds the connector from the provider row, which needs the overlay mapping.
      // This pins today's behaviour (F14). If it is fixed, update this expectation.
      const rerun = await request.post(
        `${api.baseURL}/api/benchmark-run-test-prompts/${firstPrompt.id}/regenerate`
      );
      expect(rerun.status()).toBe(400);
      expect(JSON.stringify(await rerun.json())).toContain('No connector adapter mapping');
    } finally {
      await api.dispose();
    }
  });
});
