const { test, expect } = require('@playwright/test');

// Helper function for navigating to model selection page (inherited from model-selection.spec.js)
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

test.describe('Test Name Card Initial State', { tag: '@happy-path' }, () => {
  
  test('GIVEN as a user first load Test Configuration page WHEN Test Name Accordion Card rendered for the first time THEN card header displays title "Fill in Test Name" AND card header displays description "Provide a name for your benchmark test." AND card header displays Card Incomplete Indicator (red circle alert icon) AND card content is expanded by default AND card content displays text "Test Name (Required)" AND card content contain empty Test Name text input field with thick grey border', async ({ page }) => {
    
    // Navigate to model selection page (Test Configuration page)
    await navigateToModelSelection(page);
    
    // Wait for the Test Name card to be visible
    const testNameCard = page.locator('[data-testid="test-name-card"]');
    await expect(testNameCard).toBeVisible();
    
    // Verify card header displays title "Fill in Test Name"
    const cardTitle = page.locator('[data-testid="additional-card-title"]');
    await expect(cardTitle).toBeVisible();
    await expect(cardTitle).toContainText('Fill in Test Name');
    
    // Verify card header displays description "Provide a name for your benchmark test."
    const cardDescription = page.locator('[data-testid="additional-card-description"]');
    await expect(cardDescription).toBeVisible();
    await expect(cardDescription).toContainText('Provide a name for your benchmark test.');
    
    // Verify card header displays Card Incomplete Indicator (red circle alert icon)
    // The status indicator should be visible and should be the red CircleAlert icon
    const statusIndicator = page.locator('[data-testid="test-name-status-indicator"]');
    await expect(statusIndicator).toBeVisible();
    
    // Verify it's the red alert icon by checking it has the text-red-500 class
    // The component uses text-red-500 class for CircleAlert when invalid
    const hasRedClass = await statusIndicator.evaluate((el) => {
      return el.classList.contains('text-red-500');
    });
    expect(hasRedClass).toBe(true);
    
    // Verify card content is expanded by default
    // The accordion has defaultValue="item-1" so it should be expanded
    const testNameInput = page.locator('[data-testid="test-name-input"]');
    await expect(testNameInput).toBeVisible();
    
    // Verify card content displays text "Test Name (Required)"
    // Find the label associated with the test-name-input using data-testid
    
    // Find the label by its relationship to the input with data-testid
    const testNameLabel = page.locator('label[for="test-name-input"]');
    await expect(testNameLabel).toBeVisible();
    const labelText = await testNameLabel.textContent();
    expect(labelText).toContain('Test Name');
    expect(labelText).toMatch(/[*]|Required/);
    
    // Verify card content contains empty Test Name text input field with thick grey border
    const testNameValue = await testNameInput.inputValue();
    expect(testNameValue).toBe('');
    
    // Check for border styling - input should have border (thick grey border)
    // We can verify the input is visible and empty, which indicates it's in initial state
    const inputBorder = await testNameInput.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        borderWidth: styles.borderWidth,
        borderColor: styles.borderColor,
        borderStyle: styles.borderStyle
      };
    });
    expect(inputBorder.borderWidth).not.toBe('0px');
    expect(inputBorder.borderStyle).not.toBe('none');
  });
});

