const { test, expect } = require('@playwright/test');
const {
  getToModelSelectionCard,
  selectProviderByName,
  openAddNewModelSheet,
  openEditFirstModelSheet,
  openEditModelSheetByName,
  openModelDropdownWithOptions,
  editModelSheet,
  mockTestConnection,
} = require('../utils/modelSelection');

const OPENAI_EXPLANATION = 'Enter an OpenAI model name, e.g. gpt-4o-mini';
const SAVED_TOKEN_HELPER =
  'Your token has already been saved. No further action is needed unless you would like to replace it with a new one.';

async function setupOpenAI(page) {
  await getToModelSelectionCard(page);
  await selectProviderByName(page, /OpenAI/i);
}

async function setupTogether(page) {
  await getToModelSelectionCard(page);
  await selectProviderByName(page, /TogetherAI|Together/i);
}

async function fillModelAndToken(sheet, { model = 'gpt-4o-mini', token = 'sk-e2e-test' } = {}) {
  await sheet.locator('#model').fill(model);
  await sheet.locator('#token').fill(token);
}

async function clickTestAndWaitEnabled(sheet) {
  await sheet.getByTestId('edit-model-test-connection').click();
  await expect(sheet.getByTestId('edit-model-save')).toBeEnabled({ timeout: 15000 });
}

test.describe('Edit Model Configuration Sheet', () => {
  // Shared E2E DB: keep this file serial so create/update/api-key tests do not race.
  test.describe.configure({ mode: 'serial' });

  // ---------------------------------------------------------------------
  // AC1: Open sheet (create / edit)
  // ---------------------------------------------------------------------
  test.describe('AC1 Open sheet', { tag: '@happy-path' }, () => {
    test('Add New Model Configuration opens sheet with new-config defaults', async ({ page }) => {
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);

      await expect(
        sheet.locator('h2.text-lg.font-semibold').filter({ hasText: 'Edit Model Configuration' })
      ).toBeVisible();
      await expect(sheet.locator('#modelConfig')).toHaveValue('New Model');
      await expect(sheet.locator('#model')).toHaveValue('');
      await expect(sheet.locator('#model')).toHaveAttribute('placeholder', 'gpt-4o-mini');
      await expect(sheet.getByTestId('edit-model-provider-display')).toHaveText(/OpenAI/i);
    });

    test('Edit button opens sheet prefilled with saved config', async ({ page }) => {
      await setupOpenAI(page);
      await openEditFirstModelSheet(page);
      const sheet = editModelSheet(page);

      await expect(
        sheet.locator('h2.text-lg.font-semibold').filter({ hasText: 'Edit Model Configuration' })
      ).toBeVisible();
      await expect(sheet.locator('#modelConfig')).not.toHaveValue('New Model');
      await expect(sheet.locator('#model')).not.toHaveValue('');
      await expect(sheet.getByTestId('edit-model-provider-display')).toHaveText(/OpenAI/i);
      await expect(sheet.getByTestId('edit-model-param-key-0')).toHaveValue('temperature');
      await expect(sheet.getByTestId('edit-model-param-value-0')).toHaveValue('1.0');
    });

    test('Closing edit then Add New shows new-config defaults', async ({ page }) => {
      await setupOpenAI(page);
      await openEditFirstModelSheet(page);
      const sheet = editModelSheet(page);
      const editedName = await sheet.locator('#modelConfig').inputValue();
      expect(editedName).not.toBe('New Model');

      await sheet.getByTestId('edit-model-back').click();
      await expect(sheet).not.toBeVisible();

      await openAddNewModelSheet(page);
      await expect(editModelSheet(page).locator('#modelConfig')).toHaveValue('New Model');
      await expect(editModelSheet(page).locator('#model')).toHaveValue('');
    });
  });

  // ---------------------------------------------------------------------
  // AC2: Form fields
  // ---------------------------------------------------------------------
  test.describe('AC2 Form fields', { tag: '@happy-path' }, () => {
    test('Required labels and action buttons are present', async ({ page }) => {
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);

      await expect(sheet.getByText('Model Configuration Name*')).toBeVisible();
      await expect(sheet.getByText('Model Provider*')).toBeVisible();
      await expect(sheet.getByText('Model*', { exact: true })).toBeVisible();
      await expect(sheet.getByRole('heading', { name: 'Advanced Parameters' })).toBeVisible();
      await expect(sheet.getByText('Parameter', { exact: true })).toBeVisible();
      await expect(sheet.getByText('Value', { exact: true })).toBeVisible();
      await expect(sheet.getByTestId('edit-model-back')).toBeVisible();
      await expect(sheet.getByTestId('edit-model-test-connection')).toBeVisible();
      await expect(sheet.getByTestId('edit-model-save')).toBeVisible();
    });

    test('Model Provider is display-only and shows OpenAI', async ({ page }) => {
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);
      const provider = sheet.getByTestId('edit-model-provider-display');
      await expect(provider).toHaveText(/OpenAI/i);
      await expect(provider.locator('input')).toHaveCount(0);
    });

    test('Provider model textbox explanation is shown', async ({ page }) => {
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      await expect(editModelSheet(page).getByText(OPENAI_EXPLANATION)).toBeVisible();
    });

    test('Model input placeholder uses provider defaultModel', async ({ page }) => {
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      await expect(editModelSheet(page).locator('#model')).toHaveAttribute(
        'placeholder',
        'gpt-4o-mini'
      );
    });
  });

  // ---------------------------------------------------------------------
  // AC3: Token / API key UX
  // ---------------------------------------------------------------------
  test.describe('AC3 Token UX', () => {
    test('Token is required when no API key is configured', async ({ page }) => {
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);

      await expect(sheet.getByText('Token*', { exact: true })).toBeVisible();
      await expect(sheet.locator('#token')).toHaveAttribute('placeholder', 'Enter token');
      await expect(sheet.getByText(SAVED_TOKEN_HELPER)).toHaveCount(0);
    });

    test('Token is optional when an API key is already configured', async ({ page }) => {
      // Route-mock latest-details so we do not permanently set a key on the shared E2E DB.
      await page.route('**/api/providers/by-system-name/**/latest-details', async (route) => {
        const response = await route.fetch();
        const json = await response.json();
        await route.fulfill({
          status: response.status(),
          contentType: 'application/json',
          body: JSON.stringify({ ...json, api_key_configured: true }),
        });
      });

      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);

      await expect(sheet.getByText('Token (optional)')).toBeVisible({ timeout: 10000 });
      await expect(sheet.locator('#token')).toHaveAttribute('placeholder', '••••••••');
      await expect(sheet.getByText(SAVED_TOKEN_HELPER)).toBeVisible();
    });

    test('Test Connection blocked without token when no key is stored', async ({ page }) => {
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);

      await sheet.locator('#model').fill('gpt-4o-mini');
      // Token left empty

      page.once('dialog', async (dialog) => {
        expect(dialog.message()).toMatch(/enter a token/i);
        await dialog.accept();
      });

      await sheet.getByTestId('edit-model-test-connection').click();
      await expect(sheet.getByTestId('edit-model-save')).toBeDisabled();
    });
  });

  // ---------------------------------------------------------------------
  // AC4: Advanced parameters
  // ---------------------------------------------------------------------
  test.describe('AC4 Advanced parameters', () => {
    test.describe.configure({ mode: 'serial' });

    test('New config preloads provider default config pairs', async ({ page }) => {
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);

      await expect(sheet.getByTestId('edit-model-param-key-0')).toHaveValue('temperature');
      await expect(sheet.getByTestId('edit-model-param-value-0')).toHaveValue('1.0');
    });

    test('Existing config loads saved config pairs (Together seed ≠ default)', async ({
      page,
    }) => {
      // Together seed uses temperature 0.7; adapter default is typically different or same —
      // assert seeded saved value 0.7 loads on edit.
      await setupTogether(page);
      await openEditFirstModelSheet(page);
      const sheet = editModelSheet(page);

      await expect(sheet.getByTestId('edit-model-param-key-0')).toHaveValue('temperature');
      await expect(sheet.getByTestId('edit-model-param-value-0')).toHaveValue('0.7');
    });

    test('User can add an advanced parameter row', async ({ page }) => {
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);

      await expect(sheet.getByTestId('edit-model-param-row-0')).toBeVisible();
      await sheet.getByTestId('edit-model-param-add').click();
      await expect(sheet.getByTestId('edit-model-param-row-1')).toBeVisible();
      await expect(sheet.getByTestId('edit-model-param-key-1')).toHaveValue('');
      await expect(sheet.getByTestId('edit-model-param-value-1')).toHaveValue('');
    });

    test('User can delete only non-default rows on a new config', async ({ page }) => {
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);

      await expect(sheet.getByTestId('edit-model-param-delete-0')).toHaveCount(0);
      await sheet.getByTestId('edit-model-param-add').click();
      await expect(sheet.getByTestId('edit-model-param-delete-1')).toBeVisible();
      await sheet.getByTestId('edit-model-param-delete-1').click();
      await expect(sheet.getByTestId('edit-model-param-row-1')).toHaveCount(0);
    });

    test('Editing existing config can delete a param row and persist after Test+Save', async ({
      page,
    }) => {
      await mockTestConnection(page, { success: true });
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);

      const uniqueName = `E2E Delete Param ${Date.now()}`;
      await sheet.locator('#modelConfig').fill(uniqueName);
      await fillModelAndToken(sheet);
      await sheet.getByTestId('edit-model-param-add').click();
      await sheet.getByTestId('edit-model-param-key-1').fill('max_tokens');
      await sheet.getByTestId('edit-model-param-value-1').fill('64');
      await clickTestAndWaitEnabled(sheet);

      const createPromise = page.waitForResponse(
        (res) =>
          res.url().includes('/api/database-model-configs') &&
          res.request().method() === 'POST' &&
          res.ok()
      );
      await sheet.getByTestId('edit-model-save').click();
      await createPromise;
      await expect(sheet).not.toBeVisible();

      await openEditModelSheetByName(page, uniqueName);
      const editSheet = editModelSheet(page);

      // Row order after reload follows Object.entries(savedConfigPairs) — do not assume index 1.
      const keyInputs = editSheet.locator('[data-testid^="edit-model-param-key-"]');
      await expect(keyInputs).toHaveCount(2);

      let maxTokensIndex = -1;
      const keyCount = await keyInputs.count();
      for (let i = 0; i < keyCount; i++) {
        if ((await keyInputs.nth(i).inputValue()) === 'max_tokens') {
          maxTokensIndex = i;
          break;
        }
      }
      expect(maxTokensIndex).toBeGreaterThanOrEqual(0);

      await editSheet.getByTestId(`edit-model-param-delete-${maxTokensIndex}`).click();

      const remainingKeys = [];
      const remaining = editSheet.locator('[data-testid^="edit-model-param-key-"]');
      await expect(remaining).toHaveCount(1);
      for (let i = 0; i < (await remaining.count()); i++) {
        remainingKeys.push(await remaining.nth(i).inputValue());
      }
      expect(remainingKeys).not.toContain('max_tokens');
      expect(remainingKeys).toContain('temperature');

      // Token optional if key was saved on create; fill token only if required
      if (await editSheet.getByText('Token*', { exact: true }).isVisible().catch(() => false)) {
        await editSheet.locator('#token').fill('sk-e2e-test');
      }

      await clickTestAndWaitEnabled(editSheet);
      const putPromise = page.waitForResponse(
        (res) =>
          res.url().includes('/api/database-model-configs/') &&
          res.request().method() === 'PUT' &&
          res.ok()
      );
      await editSheet.getByTestId('edit-model-save').click();
      const putRes = await putPromise;
      const putBody = putRes.request().postDataJSON();
      expect(putBody.savedConfigPairs).not.toHaveProperty('max_tokens');
      expect(putBody.savedConfigPairs).toHaveProperty('temperature');
    });
  });

  // ---------------------------------------------------------------------
  // AC5: Test Connection
  // ---------------------------------------------------------------------
  test.describe('AC5 Test Connection', () => {
    test('Test Connection requires a model name', async ({ page }) => {
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);
      await sheet.locator('#token').fill('sk-e2e-test');

      page.once('dialog', async (dialog) => {
        expect(dialog.message()).toMatch(/model name/i);
        await dialog.accept();
      });
      await sheet.getByTestId('edit-model-test-connection').click();
    });

    test('Successful Test Connection shows Test Passed and enables Save', async ({
      page,
    }) => {
      await mockTestConnection(page, { success: true });
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);
      await fillModelAndToken(sheet);
      await clickTestAndWaitEnabled(sheet);
      await expect(sheet.getByTestId('edit-model-test-result')).toContainText('Test Passed');
    });

    test('Failed Test Connection shows error and still unlocks Save', async ({ page }) => {
      await mockTestConnection(page, { success: false, error: 'Invalid API key' });
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);
      await fillModelAndToken(sheet);
      await clickTestAndWaitEnabled(sheet);
      await expect(sheet.getByTestId('edit-model-test-result')).toContainText(
        'Test Failed: Invalid API key'
      );
    });

    test('Test Connection sends model name, savedConfigPairs, and api_key', async ({
      page,
    }) => {
      const mock = await mockTestConnection(page, { success: true });
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);
      await fillModelAndToken(sheet, { model: 'gpt-4', token: 'sk-test' });
      await clickTestAndWaitEnabled(sheet);

      const body = mock.getLastRequestBody();
      expect(body).toBeTruthy();
      expect(body.model_name).toBe('gpt-4');
      expect(body.api_key).toBe('sk-test');
      expect(body.savedConfigPairs).toMatchObject({ temperature: '1.0' });
      expect(body.llm_provider_id).toBeTruthy();
    });
  });

  // ---------------------------------------------------------------------
  // AC6: Save fingerprint gating
  // ---------------------------------------------------------------------
  test.describe('AC6 Save gating', () => {
    test('Save is disabled until Test Connection for current form values', async ({
      page,
    }) => {
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);
      await fillModelAndToken(sheet);
      await expect(sheet.getByTestId('edit-model-save')).toBeDisabled();
    });

    test('Changing token after successful test disables Save again', async ({ page }) => {
      await mockTestConnection(page, { success: true });
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);
      await fillModelAndToken(sheet);
      await clickTestAndWaitEnabled(sheet);

      await sheet.locator('#token').fill('sk-e2e-changed');
      await expect(sheet.getByTestId('edit-model-save')).toBeDisabled();
      await expect(sheet.getByTestId('edit-model-test-result')).toHaveCount(0);

      await clickTestAndWaitEnabled(sheet);
      await expect(sheet.getByTestId('edit-model-test-result')).toContainText('Test Passed');
    });

    test('Changing Model name after successful test disables Save again', async ({
      page,
    }) => {
      await mockTestConnection(page, { success: true });
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);
      await fillModelAndToken(sheet);
      await clickTestAndWaitEnabled(sheet);

      await sheet.locator('#model').fill('gpt-4o');
      await expect(sheet.getByTestId('edit-model-save')).toBeDisabled();
    });

    test('Changing advanced parameters after successful test disables Save again', async ({
      page,
    }) => {
      await mockTestConnection(page, { success: true });
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);
      await fillModelAndToken(sheet);
      await clickTestAndWaitEnabled(sheet);

      await sheet.getByTestId('edit-model-param-value-0').fill('0.5');
      await expect(sheet.getByTestId('edit-model-save')).toBeDisabled();
    });

    test('Changing only Model Configuration Name does not invalidate fingerprint', async ({
      page,
    }) => {
      await mockTestConnection(page, { success: true });
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);
      await fillModelAndToken(sheet);
      await clickTestAndWaitEnabled(sheet);

      await sheet.locator('#modelConfig').fill('Renamed Without Retest');
      await expect(sheet.getByTestId('edit-model-save')).toBeEnabled();
      await expect(sheet.getByTestId('edit-model-test-result')).toContainText('Test Passed');
    });

    test('Save is disabled while Testing is in progress', async ({ page }) => {
      await mockTestConnection(page, { success: true, delayMs: 800 });
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);
      await fillModelAndToken(sheet);

      await sheet.getByTestId('edit-model-test-connection').click();
      await expect(sheet.getByTestId('edit-model-test-connection')).toContainText('Testing…');
      await expect(sheet.getByTestId('edit-model-save')).toBeDisabled();
      await expect(sheet.getByTestId('edit-model-save')).toBeEnabled({ timeout: 15000 });
    });
  });

  // ---------------------------------------------------------------------
  // AC7: Save create / update
  // ---------------------------------------------------------------------
  test.describe('AC7 Save create and update', () => {
    test.describe.configure({ mode: 'serial' });

    test('Saving a new model configuration creates a DB row', { tag: '@happy-path' }, async ({
      page,
    }) => {
      await mockTestConnection(page, { success: true });
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);

      const uniqueName = `E2E Create ${Date.now()}`;
      await sheet.locator('#modelConfig').fill(uniqueName);
      await fillModelAndToken(sheet);
      await clickTestAndWaitEnabled(sheet);

      const createPromise = page.waitForResponse(
        (res) =>
          res.url().includes('/api/database-model-configs') &&
          !res.url().match(/\/api\/database-model-configs\/\d+/) &&
          res.request().method() === 'POST' &&
          res.ok()
      );
      await sheet.getByTestId('edit-model-save').click();
      await createPromise;
      await expect(sheet).not.toBeVisible();

      await openModelDropdownWithOptions(page);
      await expect(
        page.locator('[data-testid^="model-option-"]').filter({ hasText: uniqueName })
      ).toBeVisible();
    });

    test('Saving an existing model configuration updates that DB row', {
      tag: '@happy-path',
    }, async ({ page }) => {
      await mockTestConnection(page, { success: true });
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);

      const uniqueName = `E2E Update Base ${Date.now()}`;
      await sheet.locator('#modelConfig').fill(uniqueName);
      await fillModelAndToken(sheet);
      await clickTestAndWaitEnabled(sheet);
      await sheet.getByTestId('edit-model-save').click();
      await expect(editModelSheet(page)).not.toBeVisible({ timeout: 15000 });

      await openEditModelSheetByName(page, uniqueName);
      const editSheet = editModelSheet(page);
      const renamed = `${uniqueName} Renamed`;
      await editSheet.locator('#modelConfig').fill(renamed);
      // Name-only change keeps fingerprint; Save should stay enabled if prior test still valid —
      // opening sheet clears test state, so re-test.
      if (await editSheet.getByText('Token*', { exact: true }).isVisible().catch(() => false)) {
        await editSheet.locator('#token').fill('sk-e2e-test');
      }
      await clickTestAndWaitEnabled(editSheet);

      let sawPost = false;
      page.on('request', (req) => {
        if (
          req.method() === 'POST' &&
          req.url().includes('/api/database-model-configs') &&
          !req.url().match(/\/api\/database-model-configs\/\d+/)
        ) {
          sawPost = true;
        }
      });

      const putPromise = page.waitForResponse(
        (res) =>
          res.url().includes('/api/database-model-configs/') &&
          res.request().method() === 'PUT' &&
          res.ok()
      );
      await editSheet.getByTestId('edit-model-save').click();
      const putRes = await putPromise;
      expect(putRes.request().postDataJSON().name).toBe(renamed);
      expect(sawPost).toBe(false);
      await expect(editSheet).not.toBeVisible();

      await openModelDropdownWithOptions(page);
      await expect(
        page.locator('[data-testid^="model-option-"]').filter({ hasText: renamed })
      ).toBeVisible();
    });

    test('Updating model name on an existing config updates in place', async ({ page }) => {
      await mockTestConnection(page, { success: true });
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);

      const uniqueName = `E2E Model Rename ${Date.now()}`;
      await sheet.locator('#modelConfig').fill(uniqueName);
      await fillModelAndToken(sheet, { model: 'gpt-4o-mini' });
      await clickTestAndWaitEnabled(sheet);
      await sheet.getByTestId('edit-model-save').click();
      await expect(editModelSheet(page)).not.toBeVisible({ timeout: 15000 });

      await openEditModelSheetByName(page, uniqueName);
      const editSheet = editModelSheet(page);
      await editSheet.locator('#model').fill('gpt-4o');
      if (await editSheet.getByText('Token*', { exact: true }).isVisible().catch(() => false)) {
        await editSheet.locator('#token').fill('sk-e2e-test');
      }
      await clickTestAndWaitEnabled(editSheet);

      const putPromise = page.waitForResponse(
        (res) =>
          res.url().includes('/api/database-model-configs/') &&
          res.request().method() === 'PUT' &&
          res.ok()
      );
      await editSheet.getByTestId('edit-model-save').click();
      const putRes = await putPromise;
      expect(putRes.request().postDataJSON().model_name).toBe('gpt-4o');
    });

    test('Entering a new token on Save stores the API key before persisting config', async ({
      page,
    }) => {
      await mockTestConnection(page, { success: true });
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);

      const uniqueName = `E2E Token Save ${Date.now()}`;
      await sheet.locator('#modelConfig').fill(uniqueName);
      await fillModelAndToken(sheet, { token: 'sk-e2e-persist' });
      await clickTestAndWaitEnabled(sheet);

      const apiKeyPromise = page.waitForRequest(
        (req) =>
          req.method() === 'POST' && /\/api\/providers\/\d+\/api-key$/.test(req.url())
      );
      const createPromise = page.waitForResponse(
        (res) =>
          res.url().includes('/api/database-model-configs') &&
          res.request().method() === 'POST' &&
          res.ok()
      );
      await sheet.getByTestId('edit-model-save').click();
      const apiKeyReq = await apiKeyPromise;
      expect(apiKeyReq.postDataJSON().api_key).toBe('sk-e2e-persist');
      await createPromise;
    });
  });

  // ---------------------------------------------------------------------
  // AC8: Back / dismiss without saving
  // ---------------------------------------------------------------------
  test.describe('AC8 Dismiss without saving', () => {
    test('Back closes sheet without create/update', async ({ page }) => {
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);
      await sheet.locator('#modelConfig').fill(`E2E Discard ${Date.now()}`);
      await sheet.locator('#model').fill('gpt-4o-mini');

      let persisted = false;
      page.on('request', (req) => {
        const url = req.url();
        if (
          (req.method() === 'POST' || req.method() === 'PUT') &&
          url.includes('/api/database-model-configs')
        ) {
          persisted = true;
        }
      });

      await sheet.getByTestId('edit-model-back').click();
      await expect(sheet).not.toBeVisible();
      expect(persisted).toBe(false);
    });

    test('Dismissing the sheet via Escape closes without saving', async ({ page }) => {
      await setupOpenAI(page);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);
      await sheet.locator('#modelConfig').fill(`E2E Escape ${Date.now()}`);

      let persisted = false;
      page.on('request', (req) => {
        const url = req.url();
        if (
          (req.method() === 'POST' || req.method() === 'PUT') &&
          url.includes('/api/database-model-configs')
        ) {
          persisted = true;
        }
      });

      await page.keyboard.press('Escape');
      await expect(sheet).not.toBeVisible();
      expect(persisted).toBe(false);
    });
  });
});
