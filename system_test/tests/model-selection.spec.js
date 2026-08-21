const { test, expect } = require('@playwright/test');
const {
  navigateToModelSelection,
  fillInTestName,
  getToModelSelectionCard,
  selectStandardProviderWithModels,
  selectProviderByName,
  selectFirstCustomConnector,
  openModelDropdownWithOptions,
  openConfigDropdownWithOptions,
  openAddNewModelSheet,
  editModelSheet,
  editModelSheetTitle,
  customAppSheetTitle,
  waitForCustomAppSheetReady,
  mockCustomAppsForViewAll,
  mockProvidersForViewAll,
} = require('../utils/modelSelection');

test.describe('Model Selection Page Integration Tests', () => {

  test.describe('Standard Provider Selection', { tag: '@happy-path' }, () => {
    
    test('GIVEN as a user WHEN a standard provider is selected THEN display "Model Configuration" AND display a combobox', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      // Verify initial state - no provider selected
      await expect(page.locator('[data-testid="select-model-header"]')).toContainText('Configure And Run Tests');
      
      // Click on provider combobox to open it
      await page.click('[data-testid="provider-combobox-trigger"]');
      
      // Wait for dropdown to open
      await page.waitForSelector('[data-testid^="provider-option-"]', { timeout: 5000 });
      
      // Select the first standard provider
      const firstProvider = page.locator('[data-testid^="provider-option-"]').first();
      await firstProvider.click();
      
      // Wait for dropdown to close
      await page.waitForTimeout(500);
      
      // Verify that "Model Configuration" label is displayed
      const modelLabel = page.locator('[data-testid="model-label"]');
      await expect(modelLabel).toBeVisible();
      await expect(modelLabel).toContainText('Model Configuration');
      
      // Verify that model combobox is displayed
      const modelCombobox = page.locator('[data-testid="model-combobox-trigger"]');
      await expect(modelCombobox).toBeVisible();
      await expect(modelCombobox).toContainText('Select model configuration');
    });

    test('GIVEN as a user WHEN a standard provider is selected THEN display models with edit buttons', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      await selectStandardProviderWithModels(page);
      
      await openModelDropdownWithOptions(page);
      
      // Get all model options
      const modelOptions = page.locator('[data-testid^="model-option-"]');
      const modelCount = await modelOptions.count();
      
      // Verify at least one model is displayed
      await expect(modelCount).toBeGreaterThan(0);
      
      // Check each model has an edit button
      for (let i = 0; i < modelCount; i++) { 
        const modelOption = modelOptions.nth(i);
        
        // Verify model option is visible
        await expect(modelOption).toBeVisible();
        
        // Verify edit button exists for this model
        const editButton = modelOption.locator('[data-testid^="edit-model-"]');
        await expect(editButton).toBeVisible();
        
        // Verify edit button has edit icon
        const editIcon = editButton.locator('svg');
        await expect(editIcon).toBeVisible();
      }
    });

    test('GIVEN as a user WHEN a standard provider is selected THEN display "Add New Model Configuration" command', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      // Select a standard provider
      await page.click('[data-testid="provider-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="provider-option-"]', { timeout: 5000 });
      const firstProvider = page.locator('[data-testid^="provider-option-"]').first();
      await firstProvider.click();
      await page.waitForTimeout(500);
      
      // Open model dropdown
      await page.click('[data-testid="model-combobox-trigger"]');
      
      // Wait for dropdown content to load
      await page.waitForTimeout(1000);
      
      // Verify "Add New Model Configuration" command is displayed
      const addNewModelCommand = page.locator('[data-testid="add-new-model-from-dropdown"]');
      await expect(addNewModelCommand).toBeVisible();
      await expect(addNewModelCommand).toContainText('Add New Model Configuration');
      
    });

    test('GIVEN as a user WHEN edit button is clicked THEN edit model sheet opens', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      await selectStandardProviderWithModels(page);
      
      await openModelDropdownWithOptions(page);
      
      // Click on the first edit button
      const firstEditButton = page.locator('[data-testid^="edit-model-"]').first();
      await firstEditButton.click();
      
      // Wait for edit sheet to open
      await page.waitForTimeout(1000);
      
      // Verify edit sheet is visible (check for sheet content)
      const editSheet = page.locator('[role="dialog"]');
      await expect(editSheet).toBeVisible();
    });
  });

  test.describe('Custom Application Selection', { tag: '@happy-path' }, () => {
    
    test('GIVEN as a user WHEN a Custom Application is selected THEN display "Application Configuration" AND display a combobox', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      await selectFirstCustomConnector(page);
      
      // Verify that "Application Configuration" label is displayed
      const configLabel = page.locator('[data-testid="configuration-label"]');
      await expect(configLabel).toBeVisible();
      await expect(configLabel).toContainText('Application Configuration');
      
      // Verify that configuration combobox is displayed
      const configCombobox = page.locator('[data-testid="model-combobox-trigger"]');
      await expect(configCombobox).toBeVisible();
      await expect(configCombobox).toContainText('Select application configuration');
    });

    test('GIVEN as a user WHEN a Custom Application is selected THEN display configurations with edit buttons', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      await selectFirstCustomConnector(page);
      await openConfigDropdownWithOptions(page);
      
      const configOptions = page.locator('[data-testid^="config-option-"]');
      const configCount = await configOptions.count();
      await expect(configCount).toBeGreaterThan(0);
      
      for (let i = 0; i < Math.min(configCount, 3); i++) {
        const configOption = configOptions.nth(i);
        await expect(configOption).toBeVisible();
        await expect(configOption).not.toBeEmpty();
        const editButton = configOption.locator('[data-testid^="edit-config-"]');
        await expect(editButton).toBeVisible();
        await expect(editButton.locator('svg')).toBeVisible();
      }
    });

    test('GIVEN as a user WHEN a Custom Application is selected THEN display specific configuration labels', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      await selectFirstCustomConnector(page);
      await openConfigDropdownWithOptions(page);
      
      const basicConfig = page.locator('[data-testid^="config-option-"]').first();
      await expect(basicConfig).toBeVisible();
    });

    test('GIVEN as a user WHEN a Custom Application is selected THEN display "Add New App Configuration" command', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      await selectFirstCustomConnector(page);
      
      // Open configuration dropdown
      await page.click('[data-testid="model-combobox-trigger"]');
      
      // Wait for dropdown content to load
      await page.waitForTimeout(1000);
      
      // Verify "Add New App Configuration" command is displayed
      const addNewConfigCommand = page.locator('[data-testid="add-new-config-from-dropdown"]');
      await expect(addNewConfigCommand).toBeVisible();
      await expect(addNewConfigCommand).toContainText('Add New App Configuration');
      
      // Verify it has a plus icon
      const plusIcon = addNewConfigCommand.locator('svg');
      await expect(plusIcon).toBeVisible();
    });
  });

  test.describe('Status Indicators', () => {
    
    test('GIVEN as a user WHEN a Custom Application or standard provider is selected But NOT the Model or Config THEN display a red exclamation mark Icon', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      // Status indicator should be displayed
      const statusIndicators = page.locator('[data-testid="status-indicator"]');
      await expect(statusIndicators).toHaveCount(1);
      
      // Select a standard provider
      await page.click('[data-testid="provider-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="provider-option-"]', { timeout: 5000 });
      const firstProvider = page.locator('[data-testid^="provider-option-"]').first();
      await firstProvider.click();
      await page.waitForTimeout(500);
      
      // Verify red exclamation mark is displayed
      const redExclamation = page.locator('[data-testid="status-indicator"]');
      await expect(redExclamation).toBeVisible();
    });

    test('GIVEN as a user WHEN a Model or Config is Selected THEN display a green check button', { tag: '@happy-path' }, async ({ page }) => {
      await getToModelSelectionCard(page);
      
      await selectStandardProviderWithModels(page);
      
      await openModelDropdownWithOptions(page);
      const firstModel = page.locator('[data-testid^="model-option-"]').first();
      await firstModel.click();
      await page.waitForTimeout(500);
      
      // Verify green check mark is displayed
      const greenCheck = page.locator('[data-testid="status-indicator"]');
      await expect(greenCheck).toBeVisible();
    });

    test('GIVEN as a user WHEN a Custom Application Configuration is Selected THEN display a green check button', { tag: '@happy-path' }, async ({ page }) => {
      await getToModelSelectionCard(page);
      
      await selectFirstCustomConnector(page);
      await openConfigDropdownWithOptions(page);
      const firstConfig = page.locator('[data-testid^="config-option-"]').first();
      await firstConfig.click();
      await page.waitForTimeout(500);
      
      // Verify green check mark is displayed
      const greenCheck = page.locator('[data-testid="status-indicator"]');
      await expect(greenCheck).toBeVisible();
    });
  });

  test.describe('Navigation and Page Elements', { tag: '@happy-path' }, () => {
    
    test('GIVEN as a user WHEN on model selection page THEN verify all page elements are displayed correctly', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      // Verify breadcrumb navigation
      const breadcrumb = page.locator('[data-testid="Breadcrumb"]');
      await expect(breadcrumb).toBeVisible();
      await expect(breadcrumb).toContainText('New Benchmark Test');
      await expect(breadcrumb).toContainText('Select Model Or Application');
      
      // Verify page header and description
      await expect(page.locator('[data-testid="select-model-header"]')).toContainText('Configure And Run Tests');
      
      // Verify card title and description
      const cardTitle = page.locator('[data-testid="card-title"]');
      await expect(cardTitle).toBeVisible();
      
      const cardDescription = page.locator('[data-testid="card-description"]');
      await expect(cardDescription).toBeVisible();
      
      // Verify provider combobox is visible
      const providerCombobox = page.locator('[data-testid="provider-combobox-trigger"]');
      await expect(providerCombobox).toBeVisible();
      await expect(providerCombobox).toContainText('Select provider...');
      
      // Verify navigation buttons
      const backButton = page.locator('[data-testid="back-to-bundles-button"]');
      await expect(backButton).toBeVisible();
      await expect(backButton).toContainText('Back to Bundle Selection');
      
      const nextButton = page.locator('[data-testid="run-benchmark-tests"]');
      await expect(nextButton).toBeVisible();
      await expect(nextButton).toContainText('Run Benchmark Tests');
    });

    test('GIVEN as a user WHEN clicking back button THEN navigate to bundle selection page', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      // Click back button
      const backButton = page.locator('[data-testid="back-to-bundles-button"]');
      await backButton.click();
      
      // Wait for navigation
      await page.waitForLoadState('networkidle');
      
      // Verify we're back on the bundle selection page by checking for the page content
      await expect(page.locator('[data-testid="select-bundles-header"]')).toContainText('Select Test Bundles');
    });
  });

  test.describe('Provider Dropdown Functionality', { tag: '@happy-path' }, () => {
    
    test('GIVEN as a user WHEN opening provider dropdown THEN display both standard providers and custom applications', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      // Open provider dropdown
      await page.click('[data-testid="provider-combobox-trigger"]');
      
      // Wait for dropdown content
      await page.waitForTimeout(1000);
      
      // Verify standard providers section
      const standardProvidersHeading = page.locator('[data-testid="model-providers-group"]');
      await expect(standardProvidersHeading).toBeVisible();
      
      // Verify custom applications section
      const customApplicationsHeading = page.locator('[data-testid="custom-applications-group"]');
      await expect(customApplicationsHeading).toBeVisible();
      
      // Verify at least some providers are visible
      const providerOptions = page.locator('[data-testid^="provider-option-"], [data-testid^="custom-connector-option-"]');
      const providerCount = await providerOptions.count();
      await expect(providerCount).toBeGreaterThan(0);
    });

    test('GIVEN as a user WHEN provider selection changes THEN reset model/config selection', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      await selectStandardProviderWithModels(page);
      
      await openModelDropdownWithOptions(page);
      const firstModel = page.locator('[data-testid^="model-option-"]').first();
      await firstModel.click();
      await page.waitForTimeout(500);
      
      // Verify model is selected
      const modelCombobox = page.locator('[data-testid="model-combobox-trigger"]');
      const selectedModelText = await modelCombobox.textContent();
      await expect(selectedModelText).not.toContain('Select model configuration');
      
      // Change provider
      await page.click('[data-testid="provider-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="provider-option-"]', { timeout: 5000 });
      const secondProvider = page.locator('[data-testid^="provider-option-"]').nth(1);
      await secondProvider.click();
      await page.waitForTimeout(500);
      
      // Verify model selection is reset
      await expect(modelCombobox).toContainText('Select model configuration');
    });
  });

  // ---------------------------------------------------------------------
  // SelectAppOrModelCard gaps (see temp/select-app-or-model-card-implemented)
  // ---------------------------------------------------------------------
  test.describe('SelectAppOrModelCard gaps', { tag: '@happy-path' }, () => {
    test('View All / Show Less for standard providers (mocked list)', async ({ page }) => {
      await mockProvidersForViewAll(page, 4);
      try {
        await getToModelSelectionCard(page);
        await page.click('[data-testid="provider-combobox-trigger"]');
        await page.waitForSelector('[data-testid^="provider-option-"]', { timeout: 5000 });

        const viewAll = page.locator('[data-testid="view-all-standard-providers"]');
        await expect(viewAll).toBeVisible({ timeout: 10000 });

        const providerOptions = page.locator('[data-testid^="provider-option-"]');
        await expect(providerOptions).toHaveCount(3);

        await viewAll.click();
        await expect(page.locator('[data-testid="show-less-standard-providers"]')).toBeVisible();
        await expect(providerOptions).toHaveCount(4);

        await page.locator('[data-testid="show-less-standard-providers"]').click();
        await expect(page.locator('[data-testid="view-all-standard-providers"]')).toBeVisible();
        await expect(providerOptions).toHaveCount(3);
      } finally {
        await page.unroute('**/api/providers**');
      }
    });

    test('View All / Show Less for custom connectors (mocked list)', async ({ page }) => {
      await mockCustomAppsForViewAll(page, 4);
      try {
        await getToModelSelectionCard(page);
        await page.click('[data-testid="provider-combobox-trigger"]');
        await page.waitForSelector('[data-testid^="custom-connector-option-"]', { timeout: 5000 });

        const viewAll = page.locator('[data-testid="view-all-custom-connectors"]');
        await expect(viewAll).toBeVisible({ timeout: 10000 });

        const customOptions = page.locator('[data-testid^="custom-connector-option-"]');
        await expect(customOptions).toHaveCount(3);

        await viewAll.click();
        await expect(page.locator('[data-testid="show-less-custom-connectors"]')).toBeVisible();
        await expect(customOptions).toHaveCount(4);

        await page.locator('[data-testid="show-less-custom-connectors"]').click();
        await expect(page.locator('[data-testid="view-all-custom-connectors"]')).toBeVisible();
        await expect(customOptions).toHaveCount(3);
      } finally {
        await page.unroute('**/api/custom-apps**');
      }
    });

    test('edit-config opens Edit Custom Application sheet', async ({ page }) => {
      await getToModelSelectionCard(page);
      await selectFirstCustomConnector(page);
      await openConfigDropdownWithOptions(page);

      const firstEdit = page.locator('[data-testid^="edit-config-"]').first();
      await expect(firstEdit).toBeVisible();
      await firstEdit.click();
      await waitForCustomAppSheetReady(page);
    });

    test('Add New App Configuration opens Edit Custom Application sheet', async ({ page }) => {
      await getToModelSelectionCard(page);
      await selectFirstCustomConnector(page);
      await page.click('[data-testid="model-combobox-trigger"]');
      const addNew = page.locator('[data-testid="add-new-config-from-dropdown"]');
      await expect(addNew).toBeVisible({ timeout: 10000 });
      await addNew.click();
      await waitForCustomAppSheetReady(page);
      await expect(customAppSheetTitle(page)).toBeVisible();
    });

    test('Add New Model Configuration opens Edit Model sheet', async ({ page }) => {
      await getToModelSelectionCard(page);
      await selectProviderByName(page, /OpenAI/i);
      await openAddNewModelSheet(page);
      const sheet = editModelSheet(page);
      await expect(sheet).toBeVisible();
      await expect(editModelSheetTitle(sheet)).toBeVisible();
    });

    test('Selecting the same provider again clears selection', async ({ page }) => {
      await getToModelSelectionCard(page);
      await selectProviderByName(page, /OpenAI/i);

      const providerTrigger = page.locator('[data-testid="provider-combobox-trigger"]');
      await expect(providerTrigger).toContainText(/OpenAI/i);
      await expect(page.locator('[data-testid="model-combobox-trigger"]')).toBeVisible();

      await page.click('[data-testid="provider-combobox-trigger"]');
      const openaiOption = page
        .locator('[data-testid^="provider-option-"]')
        .filter({ hasText: /OpenAI/i })
        .first();
      await expect(openaiOption).toBeVisible();
      await openaiOption.click();
      await page.waitForTimeout(500);

      await expect(providerTrigger).toContainText('Select provider...');
      await expect(page.locator('[data-testid="model-combobox-trigger"]')).not.toBeVisible();
      await expect(page.locator('[data-testid="status-indicator"]')).toBeVisible();
    });

    test('Selecting the same model again clears model selection', async ({ page }) => {
      await getToModelSelectionCard(page);
      await selectProviderByName(page, /OpenAI/i);
      await openModelDropdownWithOptions(page);

      const firstModel = page.locator('[data-testid^="model-option-"]').first();
      const modelLabel = (await firstModel.textContent()) || '';
      await firstModel.click();
      await page.waitForTimeout(500);

      const modelCombobox = page.locator('[data-testid="model-combobox-trigger"]');
      await expect(modelCombobox).not.toContainText('Select model configuration');

      await page.click('[data-testid="model-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="model-option-"]', { timeout: 10000 });
      const sameModel = page
        .locator('[data-testid^="model-option-"]')
        .filter({ hasText: modelLabel.trim().slice(0, 20) })
        .first();
      await sameModel.click();
      await page.waitForTimeout(500);

      await expect(modelCombobox).toContainText('Select model configuration');
      await expect(page.locator('[data-testid="status-indicator"]')).toBeVisible();
    });

    test('Selecting the same custom config again clears config selection', async ({ page }) => {
      await getToModelSelectionCard(page);
      await selectFirstCustomConnector(page);
      await openConfigDropdownWithOptions(page);

      const firstConfig = page.locator('[data-testid^="config-option-"]').first();
      const configLabel = (await firstConfig.textContent()) || '';
      await firstConfig.click();
      await page.waitForTimeout(500);

      const configCombobox = page.locator('[data-testid="model-combobox-trigger"]');
      await expect(configCombobox).not.toContainText('Select application configuration');

      await page.click('[data-testid="model-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="config-option-"]', { timeout: 10000 });
      const sameConfig = page
        .locator('[data-testid^="config-option-"]')
        .filter({ hasText: configLabel.trim().slice(0, 20) })
        .first();
      await sameConfig.click();
      await page.waitForTimeout(500);

      await expect(configCombobox).toContainText('Select application configuration');
      await expect(page.locator('[data-testid="status-indicator"]')).toBeVisible();
    });

    test('Accordion collapse and expand hides and shows provider combobox', async ({ page }) => {
      await getToModelSelectionCard(page);
      const cardTitle = page.locator('[data-testid="card-title"]');
      const providerCombobox = page.locator('[data-testid="provider-combobox-trigger"]');
      await expect(providerCombobox).toBeVisible();

      await cardTitle.click();
      await expect(providerCombobox).not.toBeVisible();

      await cardTitle.click();
      await expect(providerCombobox).toBeVisible();
    });
  });

  test.describe('Test Name and Description Card', { tag: '@happy-path' }, () => {
    
    test('GIVEN as a user WHEN filling in test name input THEN input accepts and stores the value', async ({ page }) => {

      await navigateToModelSelection(page);

      // Fill in the test name input with testName
      const testName = 'My Test Benchmark';
      await fillInTestName(page, testName);
      
      // Verify the input contains the value we entered
      const testNameInput = page.locator('[data-testid="test-name-input"]');
      const inputValue = await testNameInput.inputValue();
      await expect(inputValue).toBe(testName);
      
      // Verify the status indicator changes to green check (test name is valid)
      const greenCheck = page.locator('[data-testid="test-name-status-indicator"]');
      await expect(greenCheck).toBeVisible();
    });
  });
});
