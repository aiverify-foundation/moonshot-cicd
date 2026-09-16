const { test, expect } = require('@playwright/test');
const {
  readDownloadRunManifest,
  collectAllExportPromptIds,
  stubNativeSaveAsPicker,
  readSavedJsonFromPage,
  openRunFromHistory,
} = require('../helpers/download-results');

function countById(ids) {
  const counts = {};
  for (const id of ids) {
    counts[id] = (counts[id] || 0) + 1;
  }
  return counts;
}

test.describe('Test Results download — API validation', { tag: '@happy-path' }, () => {
  test('GIVEN completed run WHEN user downloads JSON THEN saved file matches export API and results prompt coverage', async ({
    page,
    request,
  }) => {
    const manifest = readDownloadRunManifest();
    const { runId, runName } = manifest;
    const expectedFilename = `${runName}.json`;

    await stubNativeSaveAsPicker(page);
    await openRunFromHistory(page, runId, runName);

    const downloadButton = page.locator('[data-testid="download-results-button"]');
    await expect(downloadButton).toBeEnabled();

    const exportResponsePromise = page.waitForResponse(
      (response) =>
        response.url().includes(`/api/benchmark-runs/${runId}/export`) &&
        response.status() === 200
    );

    await downloadButton.click();
    const uiExportResponse = await exportResponsePromise;
    expect(uiExportResponse.headers()['content-disposition']).toContain(expectedFilename);

    const saved = await readSavedJsonFromPage(page);

    const exportApiResponse = await request.get(`/api/benchmark-runs/${runId}/export`);
    expect(exportApiResponse.ok()).toBeTruthy();
    const exportBody = await exportApiResponse.json();
    expect(saved).toEqual(exportBody);

    const resultsApiResponse = await request.get(`/api/benchmark-runs/${runId}/results`);
    expect(resultsApiResponse.ok()).toBeTruthy();
    const resultsBody = await resultsApiResponse.json();
    const resultsPromptIds = (resultsBody.prompts || []).map((p) => Number(p.prompt_id));
    const exportPromptIds = collectAllExportPromptIds(saved);

    expect(exportPromptIds.length).toBe(resultsPromptIds.length);
    expect(countById(exportPromptIds)).toEqual(countById(resultsPromptIds));
  });
});
