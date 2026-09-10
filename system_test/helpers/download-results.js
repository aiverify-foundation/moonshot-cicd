const { expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const MANIFEST_PATH = path.join(__dirname, '..', '.e2e-download-run.json');

function readDownloadRunManifest() {
  if (!fs.existsSync(MANIFEST_PATH)) {
    throw new Error(
      `Missing ${MANIFEST_PATH}. Run seed_completed_download_run.py before Playwright tests.`
    );
  }
  return JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'));
}

function countPromptsInExport(exportData) {
  let count = 0;
  for (const entry of exportData.run_results || []) {
    const individual = entry.results?.individual_results || {};
    for (const bucket of Object.values(individual)) {
      if (Array.isArray(bucket)) {
        count += bucket.length;
      }
    }
  }
  return count;
}

function collectAllExportPromptIds(exportData) {
  const ids = [];
  for (const entry of exportData.run_results || []) {
    const individual = entry.results?.individual_results || {};
    for (const bucket of Object.values(individual)) {
      if (!Array.isArray(bucket)) continue;
      for (const prompt of bucket) {
        ids.push(Number(prompt.prompt_id));
      }
    }
  }
  return ids;
}

/**
 * The portal uses showSaveFilePicker when available (see lib/api.ts saveBlobAsFile).
 * That path does not emit Playwright's "download" event — only the anchor fallback does.
 * Stub the picker to auto-accept saves so we can assert filename and JSON without a dialog.
 */
async function stubNativeSaveAsPicker(page) {
  await page.addInitScript(() => {
    window.showSaveFilePicker = async (options) => {
      window.__e2eSavePickerOptions = {
        suggestedName: options?.suggestedName,
        types: options?.types,
      };
      const chunks = [];
      return {
        createWritable: async () => ({
          write: async (chunk) => {
            chunks.push(chunk);
          },
          close: async () => {
            window.__e2eSavedBlobParts = chunks;
          },
        }),
      };
    };
  });
}

async function readSavedJsonFromPage(page) {
  const jsonText = await page.evaluate(async () => {
    const parts = window.__e2eSavedBlobParts;
    if (!parts || parts.length === 0) return null;
    return new Blob(parts).text();
  });
  expect(jsonText).toBeTruthy();
  return JSON.parse(jsonText);
}

async function openRunFromHistory(page, runId, runName) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  await page.click('[data-testid="sidebar-history-button"]');
  await page.waitForLoadState('networkidle');
  await expect(page.getByRole('heading', { name: 'Recent Activity' })).toBeVisible();

  const runLink = page.locator(`[data-testid="history-run-link-${runId}"]`);
  await expect(runLink).toBeVisible();
  await expect(runLink).toContainText(runName);
  await runLink.click();
  await page.waitForLoadState('networkidle');
  await expect(page).toHaveURL(new RegExp(`/test_result.*runId=${runId}`));
}

module.exports = {
  readDownloadRunManifest,
  countPromptsInExport,
  collectAllExportPromptIds,
  stubNativeSaveAsPicker,
  readSavedJsonFromPage,
  openRunFromHistory,
};
