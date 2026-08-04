const { test, expect } = require('@playwright/test');
const {
  getToAajProviderSheet,
  openAajProviderSheet,
  editAajProviderSheet,
  mockTestConnection,
} = require('../utils/modelSelection');

const SAVED_TOKEN_HELPER =
  'Your token has already been saved. No further action is needed unless you would like to replace it with a new one.';

/** Together adapter DEFAULT_MODEL used by AAJ Test Connection. */
const TOGETHER_DEFAULT_MODEL = 'meta-llama/Llama-3.3-70B-Instruct-Turbo';

async function setupAajSheet(page) {
  await getToAajProviderSheet(page);
}

async function mockApiKeyConfigured(page, configured = true) {
  await page.route('**/api/providers/by-system-name/**/latest-details', async (route) => {
    const response = await route.fetch();
    const json = await response.json();
    await route.fulfill({
      status: response.status(),
      contentType: 'application/json',
      body: JSON.stringify({ ...json, api_key_configured: configured }),
    });
  });
}

async function clickAajTestAndWaitEnabled(sheet) {
  await sheet.getByTestId('edit-aaj-test-connection').click();
  await expect(sheet.getByTestId('edit-aaj-save')).toBeEnabled({ timeout: 15000 });
}

test.describe('Add Provider Token Sheet (EditLlmAajProviderSheet)', () => {
  // Shared E2E DB: serial so api-key Save tests do not race with optional-token mocks.
  test.describe.configure({ mode: 'serial' });

  // ---------------------------------------------------------------------
  // AC1: Open sheet
  // ---------------------------------------------------------------------
  test.describe('AC1 Open sheet', { tag: '@happy-path' }, () => {
    test('Connect opens Add Provider Token sheet for the row provider', async ({ page }) => {
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);

      await expect(sheet.getByTestId('edit-aaj-provider-sheet-title')).toHaveText(
        'Add Provider Token'
      );
      await expect(sheet.getByTestId('edit-aaj-provider-display')).toHaveText(/Together/i);
      await expect(sheet.locator('#aaj-provider-token')).toHaveValue('');
    });

    test('Closing then reopening clears prior token and test state', async ({ page }) => {
      await mockTestConnection(page, { success: true });
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);

      await sheet.locator('#aaj-provider-token').fill('sk-aaj-temp');
      await clickAajTestAndWaitEnabled(sheet);
      await expect(sheet.getByTestId('edit-aaj-test-result')).toContainText('Test Passed');

      await sheet.getByTestId('edit-aaj-back').click();
      await expect(sheet).not.toBeVisible();

      await openAajProviderSheet(page, 'together_adapter');
      const reopened = editAajProviderSheet(page);
      await expect(reopened.locator('#aaj-provider-token')).toHaveValue('');
      await expect(reopened.getByTestId('edit-aaj-test-result')).toHaveCount(0);
      await expect(reopened.getByTestId('edit-aaj-save')).toBeDisabled();
    });
  });

  // ---------------------------------------------------------------------
  // AC2: Form fields
  // ---------------------------------------------------------------------
  test.describe('AC2 Form fields', { tag: '@happy-path' }, () => {
    test('Required labels and action buttons are present', async ({ page }) => {
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);

      await expect(sheet.getByText('Model Provider*')).toBeVisible();
      await expect(
        sheet.getByText(/Token\*|Token \(optional\)/)
      ).toBeVisible();
      await expect(sheet.getByTestId('edit-aaj-back')).toBeVisible();
      await expect(sheet.getByTestId('edit-aaj-test-connection')).toBeVisible();
      await expect(sheet.getByTestId('edit-aaj-save')).toBeVisible();
    });

    test('Model Provider is display-only', async ({ page }) => {
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);
      const provider = sheet.getByTestId('edit-aaj-provider-display');
      await expect(provider).toHaveText(/Together/i);
      await expect(provider.locator('input')).toHaveCount(0);
    });

    test('Sheet has no model-config / advanced-param fields', async ({ page }) => {
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);

      await expect(sheet.getByText('Model Configuration Name*')).toHaveCount(0);
      await expect(sheet.getByText('Model*', { exact: true })).toHaveCount(0);
      await expect(sheet.getByRole('heading', { name: 'Advanced Parameters' })).toHaveCount(0);
    });
  });

  // ---------------------------------------------------------------------
  // AC3: Token UX
  // ---------------------------------------------------------------------
  test.describe('AC3 Token UX', () => {
    test('Token is required when no API key is configured', async ({ page }) => {
      await mockApiKeyConfigured(page, false);
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);

      await expect(sheet.getByText('Token*', { exact: true })).toBeVisible();
      await expect(sheet.locator('#aaj-provider-token')).toHaveAttribute(
        'placeholder',
        'Enter token'
      );
      await expect(sheet.getByText(SAVED_TOKEN_HELPER)).toHaveCount(0);
    });

    test('Token is optional when an API key is already configured', async ({ page }) => {
      await mockApiKeyConfigured(page, true);
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);

      await expect(sheet.getByText('Token (optional)')).toBeVisible({ timeout: 10000 });
      await expect(sheet.locator('#aaj-provider-token')).toHaveAttribute(
        'placeholder',
        '••••••••'
      );
      await expect(sheet.getByText(SAVED_TOKEN_HELPER)).toBeVisible();
    });

    test('Test Connection blocked without token when no key is stored', async ({ page }) => {
      await mockApiKeyConfigured(page, false);
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);

      page.once('dialog', async (dialog) => {
        expect(dialog.message()).toMatch(/enter a token/i);
        await dialog.accept();
      });

      await sheet.getByTestId('edit-aaj-test-connection').click();
      await expect(sheet.getByTestId('edit-aaj-save')).toBeDisabled();
    });
  });

  // ---------------------------------------------------------------------
  // AC4: Test Connection
  // ---------------------------------------------------------------------
  test.describe('AC4 Test Connection', () => {
    test('Successful Test Connection shows Test Passed and enables Save', async ({
      page,
    }) => {
      await mockTestConnection(page, { success: true });
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);
      await sheet.locator('#aaj-provider-token').fill('sk-aaj-test');
      await clickAajTestAndWaitEnabled(sheet);
      await expect(sheet.getByTestId('edit-aaj-test-result')).toContainText('Test Passed');
    });

    test('Failed Test Connection shows error and still unlocks Save', async ({ page }) => {
      await mockTestConnection(page, { success: false, error: 'Invalid API key' });
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);
      await sheet.locator('#aaj-provider-token').fill('sk-aaj-test');
      await clickAajTestAndWaitEnabled(sheet);
      await expect(sheet.getByTestId('edit-aaj-test-result')).toContainText(
        'Test Failed: Invalid API key'
      );
    });

    test('Test Connection sends defaultModel, empty pairs, and api_key', async ({ page }) => {
      const mock = await mockTestConnection(page, { success: true });
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);
      await sheet.locator('#aaj-provider-token').fill('sk-aaj-test');
      await clickAajTestAndWaitEnabled(sheet);

      const body = mock.getLastRequestBody();
      expect(body).toBeTruthy();
      expect(body.model_name).toBe(TOGETHER_DEFAULT_MODEL);
      expect(body.api_key).toBe('sk-aaj-test');
      expect(body.savedConfigPairs).toEqual({});
      expect(body.llm_provider_id).toBeTruthy();
    });

    test('Test Connection with empty token when key is stored omits api_key', async ({
      page,
    }) => {
      await mockApiKeyConfigured(page, true);
      const mock = await mockTestConnection(page, { success: true });
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);

      await expect(sheet.getByText('Token (optional)')).toBeVisible({ timeout: 10000 });
      await clickAajTestAndWaitEnabled(sheet);

      const body = mock.getLastRequestBody();
      expect(body).toBeTruthy();
      expect(body.model_name).toBe(TOGETHER_DEFAULT_MODEL);
      expect(body.api_key == null || body.api_key === '').toBe(true);
    });
  });

  // ---------------------------------------------------------------------
  // AC5: Save gating
  // ---------------------------------------------------------------------
  test.describe('AC5 Save gating', () => {
    test('Save is disabled until Test Connection for current token fingerprint', async ({
      page,
    }) => {
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);
      await sheet.locator('#aaj-provider-token').fill('sk-aaj-test');
      await expect(sheet.getByTestId('edit-aaj-save')).toBeDisabled();
    });

    test('Changing token after successful test disables Save again', async ({ page }) => {
      await mockTestConnection(page, { success: true });
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);
      await sheet.locator('#aaj-provider-token').fill('sk-aaj-first');
      await clickAajTestAndWaitEnabled(sheet);
      await expect(sheet.getByTestId('edit-aaj-test-result')).toContainText('Test Passed');

      await sheet.locator('#aaj-provider-token').fill('sk-aaj-second');
      await expect(sheet.getByTestId('edit-aaj-save')).toBeDisabled();
      await expect(sheet.getByTestId('edit-aaj-test-result')).toHaveCount(0);

      await clickAajTestAndWaitEnabled(sheet);
      await expect(sheet.getByTestId('edit-aaj-test-result')).toContainText('Test Passed');
      await expect(sheet.getByTestId('edit-aaj-save')).toBeEnabled();
    });

    test('Save is disabled while Testing is in progress', async ({ page }) => {
      await mockTestConnection(page, { success: true, delayMs: 800 });
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);
      await sheet.locator('#aaj-provider-token').fill('sk-aaj-test');

      await sheet.getByTestId('edit-aaj-test-connection').click();
      await expect(sheet.getByTestId('edit-aaj-test-connection')).toContainText('Testing…');
      await expect(sheet.getByTestId('edit-aaj-save')).toBeDisabled();
      await expect(sheet.getByTestId('edit-aaj-save')).toBeEnabled({ timeout: 15000 });
    });
  });

  // ---------------------------------------------------------------------
  // AC6: Save stores API key
  // ---------------------------------------------------------------------
  test.describe('AC6 Save stores API key', () => {
    test.describe.configure({ mode: 'serial' });

    test('Saving with a new token stores the API key then closes', async ({ page }) => {
      await mockTestConnection(page, { success: true });
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);
      await sheet.locator('#aaj-provider-token').fill('sk-aaj-persist');
      await clickAajTestAndWaitEnabled(sheet);

      let modelConfigPersisted = false;
      page.on('request', (req) => {
        const url = req.url();
        if (
          (req.method() === 'POST' || req.method() === 'PUT') &&
          url.includes('/api/database-model-configs')
        ) {
          modelConfigPersisted = true;
        }
      });

      const apiKeyPromise = page.waitForRequest(
        (req) =>
          req.method() === 'POST' && /\/api\/providers\/\d+\/api-key$/.test(req.url())
      );
      await sheet.getByTestId('edit-aaj-save').click();
      const apiKeyReq = await apiKeyPromise;
      expect(apiKeyReq.postDataJSON().api_key).toBe('sk-aaj-persist');
      await expect(sheet).not.toBeVisible({ timeout: 15000 });
      expect(modelConfigPersisted).toBe(false);
    });

    test('Saving with existing key and empty token skips setApiKey', async ({ page }) => {
      await mockApiKeyConfigured(page, true);
      await mockTestConnection(page, { success: true });
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);

      await expect(sheet.getByText('Token (optional)')).toBeVisible({ timeout: 10000 });
      await clickAajTestAndWaitEnabled(sheet);

      let apiKeyPosted = false;
      page.on('request', (req) => {
        if (req.method() === 'POST' && /\/api\/providers\/\d+\/api-key$/.test(req.url())) {
          apiKeyPosted = true;
        }
      });

      await sheet.getByTestId('edit-aaj-save').click();
      await expect(sheet).not.toBeVisible({ timeout: 15000 });
      expect(apiKeyPosted).toBe(false);
    });
  });

  // ---------------------------------------------------------------------
  // AC7: Dismiss without saving
  // ---------------------------------------------------------------------
  test.describe('AC7 Dismiss without saving', () => {
    test('Back closes sheet without storing API key', async ({ page }) => {
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);
      await sheet.locator('#aaj-provider-token').fill('sk-aaj-discard');

      let apiKeyPosted = false;
      page.on('request', (req) => {
        if (req.method() === 'POST' && /\/api\/providers\/\d+\/api-key$/.test(req.url())) {
          apiKeyPosted = true;
        }
      });

      await sheet.getByTestId('edit-aaj-back').click();
      await expect(sheet).not.toBeVisible();
      expect(apiKeyPosted).toBe(false);
    });

    test('Dismissing the sheet via Escape closes without saving', async ({ page }) => {
      await setupAajSheet(page);
      const sheet = editAajProviderSheet(page);
      await sheet.locator('#aaj-provider-token').fill('sk-aaj-escape');

      let apiKeyPosted = false;
      page.on('request', (req) => {
        if (req.method() === 'POST' && /\/api\/providers\/\d+\/api-key$/.test(req.url())) {
          apiKeyPosted = true;
        }
      });

      await page.keyboard.press('Escape');
      await expect(sheet).not.toBeVisible();
      expect(apiKeyPosted).toBe(false);
    });
  });
});
