/**
 * Claims: a deleted extension metric adapter file fails export, score labels and rerun with a
 * structured adapter_not_found detail and no file paths; the portal shows a notice (F3).
 */
const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');
const { ExtensionApi, routePortalApiTo } = require('../../utils/extensionServer');
const {
  buildOverlay,
  EXTENSION_METRIC_NAME,
  METRIC_BUNDLE_NAME,
  OK_SYSTEM_NAME,
} = require('../../utils/extensionOverlay');
const { startRun, waitForRun, runPrompts, uniqueName } = require('../../utils/extensionRuns');

test.setTimeout(360000);

test.describe('a missing extension metric adapter file', () => {
  test('fails export, score labels and rerun with adapter_not_found, and the portal shows a notice', async ({
    page,
    request,
  }) => {
    const api = new ExtensionApi({ flagOn: true });
    try {
      buildOverlay(api.overlayPath);
      api.overlayDir = api.overlayPath;
      await api.start();

      const runName = uniqueName('e2e-missing-adapter');
      await startRun(request, api.baseURL, {
        bundleName: METRIC_BUNDLE_NAME,
        providerSystemName: OK_SYSTEM_NAME,
        runName,
      });
      const run = await waitForRun(request, api.baseURL, runName);
      expect(run.status).toBe('completed');

      // Delete the metric adapter file while the run still refers to it.
      await api.stop();
      fs.rmSync(path.join(api.overlayPath, 'adapters', 'metric', `${EXTENSION_METRIC_NAME}.py`));
      await api.start();

      const exportResponse = await request.get(`${api.baseURL}/api/benchmark-runs/${run.id}/export`);
      expect(exportResponse.status()).toBe(409);
      const exportBody = await exportResponse.json();
      expect(exportBody.detail.code).toBe('adapter_not_found');
      expect(exportBody.detail.adapter_name).toBe(EXTENSION_METRIC_NAME);
      const exportText = JSON.stringify(exportBody);
      expect(exportText).not.toContain(api.root);
      expect(exportText).not.toContain('.py');

      const labels = await request.get(
        `${api.baseURL}/api/metrics/${EXTENSION_METRIC_NAME}/score-result-names`
      );
      expect(labels.status()).toBe(404);
      const labelsBody = await labels.json();
      expect(labelsBody.detail.code).toBe('adapter_not_found');

      const prompts = await runPrompts(request, api.baseURL, run.id);
      expect(prompts.length).toBeGreaterThan(0);
      const rerun = await request.post(
        `${api.baseURL}/api/benchmark-run-test-prompts/${prompts[0].id}/regenerate`
      );
      expect(rerun.status()).toBe(409);
      const rerunBody = await rerun.json();
      expect(rerunBody.detail.code).toBe('adapter_not_found');

      await routePortalApiTo(page, api.baseURL);
      // The API refuses static pages without a same-origin Referer, so pass one as a real page would send.
      await page.goto(`${api.baseURL}/test_result/?runId=${run.id}`, { referer: `${api.baseURL}/` });
      await page.waitForLoadState('networkidle');
      // The page opens on "Overview". Each bundle's section, which holds the notice, is hidden until its tab is picked.
      await page.getByRole('button', { name: /Custom Extension Metric/ }).click();
      await expect(page.getByTestId('metric-adapter-missing-notice')).toBeVisible({ timeout: 30000 });
    } finally {
      await api.dispose();
    }
  });
});
