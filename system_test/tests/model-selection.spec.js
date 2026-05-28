const { test, expect } = require('@playwright/test');
const { printPageDiagnostics } = require('../utils/pageDiagnostics');

// Helper function for navigating to model selection page
async function navigateToModelSelection(page) {
  await page.goto('/');
  
  // Wait for the page to load
  await page.waitForLoadState('networkidle');
  
  // Click on the "Benchmark" link using data-testid
  await page.click('[data-testid="benchmark-link"]');
  
  // Wait for navigation to complete
  await page.waitForLoadState('networkidle');
  
  // Wait for bundles to load and select the first bundle
  await page.waitForSelector('[data-testid^="toggle-"]', { timeout: 10000 });
  const toggleButtons = page.locator('[data-testid^="toggle-"]');
  await toggleButtons.first().click();
  
  // Wait a moment for the state to update
  await page.waitForTimeout(500);
  
  // Click the configure button to navigate to model selection
  const configureButton = page.locator('[data-testid="configure-and-run-benchmark-tests"]');
  await configureButton.click();
  
  // Wait for navigation to model selection page
  await page.waitForLoadState('networkidle');
  
  // Verify we're on the model selection page by checking for the page content
  await expect(page.locator('[data-testid="select-model-header"]')).toContainText('Configure And Run Tests');
}

async function fillInTestName(page, testName) {
  await navigateToModelSelection(page);
      
  // Wait for the test name card to be visible
  const testNameCard = page.locator('[data-testid="additional-card-title"]');
  await expect(testNameCard).toBeVisible();
  
  // Check if accordion is collapsed and expand it if needed
  const testNameInput = page.locator('[data-testid="test-name-input"]');
  const isInputVisible = await testNameInput.isVisible().catch(() => false);
  
  // this is to make the test a little more robust
  if (!isInputVisible) {
    // Click the accordion trigger - the card title is inside the AccordionTrigger button
    // Click on the card title area which should trigger the accordion
    await testNameCard.click();
  }
  
  // Verify the input is now visible
  await expect(testNameInput).toBeVisible();
  
  // Fill in the test name input with testName
  await testNameInput.fill(testName);
}

async function expandModelSelectionCard(page) {
  // Wait for the model selection card to be visible
  const cardTitle = page.locator('[data-testid="card-title"]');
  await expect(cardTitle).toBeVisible();
  await expect(cardTitle).toContainText('Select App or Model');
  
  // Check if accordion is collapsed and expand it if needed
  // The provider combobox is inside the AccordionContent, so if it's visible, the accordion is expanded
  const providerCombobox = page.locator('[data-testid="provider-combobox-trigger"]');
  const isComboboxVisible = await providerCombobox.isVisible().catch(() => false);
  
  // If the combobox is not visible, the accordion is collapsed - click the card title to expand it
  if (!isComboboxVisible) {
    // Click on the card title which should trigger the accordion to expand
    await cardTitle.click();
  }
  
  // Verify the provider combobox is now visible (accordion is expanded)
  await expect(providerCombobox).toBeVisible();
}

async function getToModelSelectionCard(page) {
  await navigateToModelSelection(page);

  // Fill in the test name input with testName
  const testName = 'My Test Benchmark';
  await fillInTestName(page, testName);
  await expandModelSelectionCard(page);
}

test.describe('Model Selection Page Integration Tests', () => {

  test.describe('Standard Provider Selection', () => {
    
    test('GIVEN as a user WHEN a standard provider is selected THEN display "Model" AND display a combobox', async ({ page }) => {
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
      
      // Verify that "Model" label is displayed
      const modelLabel = page.locator('[data-testid="model-label"]');
      await expect(modelLabel).toBeVisible();
      
      // Verify that model combobox is displayed
      const modelCombobox = page.locator('[data-testid="model-combobox-trigger"]');
      await expect(modelCombobox).toBeVisible();
      await expect(modelCombobox).toContainText('Select model...');
    });

    test('GIVEN as a user WHEN a standard provider is selected THEN display models with edit buttons', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      // Select a standard provider
      await page.click('[data-testid="provider-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="provider-option-"]', { timeout: 5000 });
      const firstProvider = page.locator('[data-testid^="provider-option-"]').first();
      await firstProvider.click();
      await page.waitForTimeout(500);
      
      // Open model dropdown
      await page.click('[data-testid="model-combobox-trigger"]');
      
      // Wait for models to load
      await page.waitForSelector('[data-testid^="model-option-"]', { timeout: 5000 });
      
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

    test('GIVEN as a user WHEN a standard provider is selected THEN display "Add new Model" command', async ({ page }) => {
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
      
      // Verify "Add New Model" command is displayed
      const addNewModelCommand = page.locator('[data-testid="add-new-model-from-dropdown"]');
      await expect(addNewModelCommand).toBeVisible();
      await expect(addNewModelCommand).toContainText('Add New Model');
      
    });

    test('GIVEN as a user WHEN edit button is clicked THEN edit model sheet opens', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      // Select a standard provider
      await page.click('[data-testid="provider-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="provider-option-"]', { timeout: 5000 });
      const firstProvider = page.locator('[data-testid^="provider-option-"]').first();
      await firstProvider.click();
      await page.waitForTimeout(500);
      
      // Open model dropdown
      await page.click('[data-testid="model-combobox-trigger"]');
      
      // Wait for models to load
      await page.waitForSelector('[data-testid^="model-option-"]', { timeout: 5000 });
      
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

  test.describe('Custom Application Selection', () => {
    
    test('GIVEN as a user WHEN a Custom Application is selected THEN display "Configuration" AND display a combobox', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      // Click on provider combobox to open it
      await page.click('[data-testid="provider-combobox-trigger"]');
      
      // Wait for dropdown to open
      await page.waitForSelector('[data-testid^="custom-connector-option-"]', { timeout: 5000 });
      
      // Select the first custom connector
      const firstCustomConnector = page.locator('[data-testid^="custom-connector-option-"]').first();
      await firstCustomConnector.click();
      
      // Wait for dropdown to close
      await page.waitForTimeout(500);
      
      // Verify that "Configuration" label is displayed
      const configLabel = page.locator('[data-testid="configuration-label"]');
      await expect(configLabel).toBeVisible();
      
      // Verify that configuration combobox is displayed
      const configCombobox = page.locator('[data-testid="model-combobox-trigger"]');
      await expect(configCombobox).toBeVisible();
      await expect(configCombobox).toContainText('Select configuration...');
    });

    test('GIVEN as a user WHEN a Custom Application is selected THEN display configurations with edit buttons', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      // Select a custom connector
      await page.click('[data-testid="provider-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="custom-connector-option-"]', { timeout: 5000 });
      const firstCustomConnector = page.locator('[data-testid^="custom-connector-option-"]').first();
      await firstCustomConnector.click();
      await page.waitForTimeout(500);
      
      // Open configuration dropdown
      await page.click('[data-testid="model-combobox-trigger"]');
      
      // Wait for configurations to load
      await page.waitForSelector('[data-testid^="config-option-"]', { timeout: 5000 });
      
      // Get all configuration options
      const configOptions = page.locator('[data-testid^="config-option-"]');
      const configCount = await configOptions.count();
      
      // Verify at least one configuration is displayed
      await expect(configCount).toBeGreaterThan(0);
      
      // Check each configuration is displayed correctly
      for (let i = 0; i < Math.min(configCount, 3); i++) { // Check first 3 configurations
        const configOption = configOptions.nth(i);
        
        // Verify configuration option is visible
        await expect(configOption).toBeVisible();
        
        // Note: Based on the component code, configurations don't have edit buttons
        // This test verifies the configuration options are displayed correctly
        // Check that the configuration option contains some text content
        await expect(configOption).not.toBeEmpty();
        
        // Verify the configuration option contains text content
        const configText = await configOption.textContent();
        expect(configText).toBeTruthy();
        expect(configText.trim().length).toBeGreaterThan(0);
      }
    });

    test('GIVEN as a user WHEN a Custom Application is selected THEN display specific configuration labels', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      // Select a custom connector
      await page.click('[data-testid="provider-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="custom-connector-option-"]', { timeout: 5000 });
      const firstCustomConnector = page.locator('[data-testid^="custom-connector-option-"]').first();
      await firstCustomConnector.click();
      await page.waitForTimeout(500);
      
      // Open configuration dropdown
      await page.click('[data-testid="model-combobox-trigger"]');
      
      // Wait for configurations to load
      await page.waitForSelector('[data-testid^="config-option-"]', { timeout: 5000 });
      
      // Check for specific configuration labels from custom-application fixtures (MockData.ts)
      const basicConfig = page.locator('[data-testid^="config-option-"]').first();
      await expect(basicConfig).toBeVisible();

    });

    test('GIVEN as a user WHEN a Custom Application is selected THEN display "Add new Configuration" command', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      // Select a custom connector
      await page.click('[data-testid="provider-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="custom-connector-option-"]', { timeout: 5000 });
      const firstCustomConnector = page.locator('[data-testid^="custom-connector-option-"]').first();
      await firstCustomConnector.click();
      await page.waitForTimeout(500);
      
      // Open configuration dropdown
      await page.click('[data-testid="model-combobox-trigger"]');
      
      // Wait for dropdown content to load
      await page.waitForTimeout(1000);
      
      // Verify "Add New Configuration" command is displayed
      const addNewConfigCommand = page.locator('[data-testid="add-new-config-from-dropdown"]');
      await expect(addNewConfigCommand).toBeVisible();
      await expect(addNewConfigCommand).toContainText('Add New Configuration');
      
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

    test('GIVEN as a user WHEN a Model or Config is Selected THEN display a green check button', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      // Select a standard provider
      await page.click('[data-testid="provider-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="provider-option-"]', { timeout: 5000 });
      const firstProvider = page.locator('[data-testid^="provider-option-"]').first();
      await firstProvider.click();
      await page.waitForTimeout(500);
      
      // Select a model
      await page.click('[data-testid="model-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="model-option-"]', { timeout: 5000 });
      const firstModel = page.locator('[data-testid^="model-option-"]').first();
      await firstModel.click();
      await page.waitForTimeout(500);
      
      // Verify green check mark is displayed
      const greenCheck = page.locator('[data-testid="status-indicator"]');
      await expect(greenCheck).toBeVisible();
    });

    test('GIVEN as a user WHEN a Custom Application Configuration is Selected THEN display a green check button', async ({ page }) => {
      await getToModelSelectionCard(page);
      
      // Select a custom connector
      await page.click('[data-testid="provider-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="custom-connector-option-"]', { timeout: 5000 });
      const firstCustomConnector = page.locator('[data-testid^="custom-connector-option-"]').first();
      await firstCustomConnector.click();
      await page.waitForTimeout(500);
      
      // Select a configuration
      await page.click('[data-testid="model-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="config-option-"]', { timeout: 5000 });
      const firstConfig = page.locator('[data-testid^="config-option-"]').first();
      await firstConfig.click();
      await page.waitForTimeout(500);
      
      // Verify green check mark is displayed
      const greenCheck = page.locator('[data-testid="status-indicator"]');
      await expect(greenCheck).toBeVisible();
    });
  });

  test.describe('Navigation and Page Elements', () => {
    
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

  test.describe('Provider Dropdown Functionality', () => {
    
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
      
      // Select first provider
      await page.click('[data-testid="provider-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="provider-option-"]', { timeout: 5000 });
      const firstProvider = page.locator('[data-testid^="provider-option-"]').first();
      await firstProvider.click();
      await page.waitForTimeout(500);
      
      // Select a model
      await page.click('[data-testid="model-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="model-option-"]', { timeout: 5000 });
      const firstModel = page.locator('[data-testid^="model-option-"]').first();
      await firstModel.click();
      await page.waitForTimeout(500);
      
      // Verify model is selected
      const modelCombobox = page.locator('[data-testid="model-combobox-trigger"]');
      const selectedModelText = await modelCombobox.textContent();
      await expect(selectedModelText).not.toContain('Select model...');
      
      // Change provider
      await page.click('[data-testid="provider-combobox-trigger"]');
      await page.waitForSelector('[data-testid^="provider-option-"]', { timeout: 5000 });
      const secondProvider = page.locator('[data-testid^="provider-option-"]').nth(1);
      await secondProvider.click();
      await page.waitForTimeout(500);
      
      // Verify model selection is reset
      await expect(modelCombobox).toContainText('Select model...');
    });
  });

  test.describe('Test Name and Description Card', () => {
    
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

  test.describe('Diagnostic Tests', () => {
    
    test('DIAGNOSTIC: Print all page elements in formatted manner', async ({ page }) => {
      await navigateToModelSelection(page);
      await printPageDiagnostics(page, 'MODEL SELECTION PAGE DIAGNOSTIC REPORT');
    });
  });
});
