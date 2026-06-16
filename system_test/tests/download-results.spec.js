const { test, expect } = require('@playwright/test');
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const MANIFEST_PATH = path.join(__dirname, '..', '.e2e-download-run.json');
const VALIDATE_SCHEMA_SCRIPT = path.join(
  __dirname,
  '..',
  'scripts',
  'validate_schema1_json.py'
);

function readDownloadRunManifest() {
  if (!fs.existsSync(MANIFEST_PATH)) {
    throw new Error(
      `Missing ${MANIFEST_PATH}. Run seed_completed_download_run.py before Playwright tests.`
    );
  }
  return JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'));
}

/** Validate export JSON with GA Schema1 (Pydantic) and validate_json from process_check_app. */
function assertExportConformsToSchema1(exportData) {
  const python = process.env.E2E_PYTHON || 'python3';
  const result = spawnSync(python, [VALIDATE_SCHEMA_SCRIPT], {
    input: JSON.stringify(exportData),
    encoding: 'utf8',
  });
  if (result.status !== 0) {
    const detail = (result.stderr || result.stdout || '').trim();
    throw new Error(
      detail || `Schema1 validation exited with status ${result.status ?? 'unknown'}`
    );
  }
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

test.describe('Test Results download', () => {
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
    await expect(downloadButton).toHaveText('Download');

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
    assertExportConformsToSchema1(parsed);
    expect(countPromptsInExport(parsed)).toBe(manifest.expectedPromptCount);

    await expect(downloadButton).toBeEnabled();
    await expect(downloadButton).toHaveText('Download');
  });
});
