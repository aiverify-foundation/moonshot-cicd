const { test, expect } = require('@playwright/test');
const {
  readDownloadRunManifest,
  countPromptsInExport,
  stubNativeSaveAsPicker,
  readSavedJsonFromPage,
  openRunFromHistory,
} = require('../../helpers/download-results');

test.describe('Test Results download — Integration Tests', { tag: '@integration' }, () => {
  test('GIVEN completed run with prompts WHEN user opens run from History and clicks Download THEN JSON is saved via Save As flow', async ({
    page,
  }) => {
    const manifest = readDownloadRunManifest();
    const { runId, runName } = manifest;
    const expectedFilename = `${runName}.json`;

    await stubNativeSaveAsPicker(page);
    await openRunFromHistory(page, runId, runName);

    const downloadButton = page.locator('[data-testid="download-results-button"]');
    await expect(downloadButton).toBeEnabled();
    await expect(downloadButton).toHaveText('Download JSON');

    const exportResponsePromise = page.waitForResponse(
      (response) =>
        response.url().includes(`/api/benchmark-runs/${runId}/export`) &&
        response.status() === 200
    );

    await downloadButton.click();
    await expect(downloadButton).toHaveText('Downloading…');
    await expect(downloadButton).toBeDisabled();

    const exportResponse = await exportResponsePromise;
    expect(exportResponse.headers()['content-disposition']).toContain(expectedFilename);

    const pickerOptions = await page.evaluate(() => window.__e2eSavePickerOptions);
    expect(pickerOptions).toBeTruthy();
    expect(pickerOptions.suggestedName).toBe(expectedFilename);
    expect(pickerOptions.types?.[0]?.accept?.['application/json']).toContain('.json');

    const parsed = await readSavedJsonFromPage(page);
    expect(parsed).toHaveProperty('run_metadata');
    expect(parsed).toHaveProperty('run_results');
    expect(countPromptsInExport(parsed)).toBe(manifest.expectedPromptCount);

    await expect(downloadButton).toBeEnabled();
    await expect(downloadButton).toHaveText('Download JSON');
  });
});
