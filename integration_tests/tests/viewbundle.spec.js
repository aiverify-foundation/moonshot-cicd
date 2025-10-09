const { test, expect } = require('@playwright/test');

// Helper function for navigating to view bundles page
async function navigateToViewBundles(page) {
  await page.goto('/');
  
  // Wait for the page to load
  await page.waitForLoadState('networkidle');
  
  // Click on the "View Bundles" link using data-testid
  await page.click('[data-testid="view-bundles-link"]');
  
  // Wait for navigation to complete
  await page.waitForLoadState('networkidle');
  
  // Verify we're on the bundles page by checking the URL
  await expect(page).toHaveURL(/.*\/view_bundles/);
}

// Helper function to toggle all toggle buttons
async function toggleAllButtons(page) {
  // Wait for toggle buttons to load
  await page.waitForSelector('[data-testid^="toggle-"]', { timeout: 10000 });
  
  // Get all toggle buttons
  const toggleButtons = page.locator('[data-testid^="toggle-"]');
  const count = await toggleButtons.count();
  
  // Iterate through all toggle buttons and click them
  for (let i = 0; i < count; i++) {
    const toggleButton = toggleButtons.nth(i);
    await toggleButton.click();

  }
}

test.describe('Moonshot Integration Tests', () => {

  test('navigate to view bundles page', async ({ page }) => {
    await navigateToViewBundles(page);
    
    // Check that the configure button is disabled (no bundles selected)
    const configureButton = page.locator('[data-testid="configure-and-run-benchmark-tests"]');
    // We cannot click the disabled button so just checking that it is disabled
    await expect(configureButton).toBeDisabled();
    
    // Verify the page content is still there
    await expect(page.locator('[data-testid="select-bundles-header"]')).toContainText('Select bundles');
  });

  test('configure button becomes enabled after selecting a bundle', async ({ page }) => {
    await navigateToViewBundles(page);
    
    // Check that the configure button is initially disabled
    const configureButton = page.locator('[data-testid="configure-and-run-benchmark-tests"]');
    await expect(configureButton).toBeDisabled();
    
    // Wait for bundles to load and find the first toggle button
    await page.waitForSelector('[data-testid^="toggle-"]', { timeout: 10000 });
    
    // Get all toggle buttons and select the second one (index 1)
    const toggleButtons = page.locator('[data-testid^="toggle-"]');
    const secondToggleButton = toggleButtons.nth(1); // nth(0) is first, nth(1) is second, etc.
    
    // Click the second bundle toggle button to select it
    await secondToggleButton.click();
    
    // Wait a moment for the state to update
    await page.waitForTimeout(500);
    
    // Check that the configure button is now enabled
    await expect(configureButton).toBeEnabled();
    
    // Verify the button text is still correct
    await expect(configureButton).toContainText('Configure and Run Benchmark Tests');
    
    // Click the enabled configure button to verify it works
    await configureButton.click();
    
    // Verify navigation occurred (should go to select_model page)
    await expect(page).toHaveURL(/.*\/select_model/);
  });

  test('configure button becomes disabled after toggling off all bundles', async ({ page }) => {
    await navigateToViewBundles(page);
    
    // Check that the configure button is initially disabled
    const configureButton = page.locator('[data-testid="configure-and-run-benchmark-tests"]');
    await expect(configureButton).toBeDisabled();
    
    // Wait for bundles to load and find the first toggle button
    await page.waitForSelector('[data-testid^="toggle-"]', { timeout: 10000 });
    
    // Get all toggle buttons and select the second one (index 1)
    const toggleButtons = page.locator('[data-testid^="toggle-"]');
    const thirdToggleButton = toggleButtons.nth(2); // nth(0) is first, nth(1) is second, etc.
    
    // Click the second bundle toggle button to select it
    await thirdToggleButton.click();
    
    // Wait a moment for the state to update
    await page.waitForTimeout(500);
    
    // Check that the configure button is now enabled
    await expect(configureButton).toBeEnabled();
    
    // Verify the button text is still correct
    await expect(configureButton).toContainText('Configure and Run Benchmark Tests');
    
    // Click the second bundle toggle button to select it
    await thirdToggleButton.click();
    
    // Wait a moment for the state to update
    await page.waitForTimeout(500);
    
    // Check that the configure button is now disabled
    await expect(configureButton).toBeDisabled();
    
  });

  test('configure button becomes disabled after toggling off all bundles(Multiple bundles)', async ({ page }) => {
    await navigateToViewBundles(page);
    
    // Check that the configure button is initially disabled
    const configureButton = page.locator('[data-testid="configure-and-run-benchmark-tests"]');
    await expect(configureButton).toBeDisabled();
    
    // Wait for bundles to load and find the first toggle button
    await page.waitForSelector('[data-testid^="toggle-"]', { timeout: 10000 });
    
    // Toggle all the bundles
    await toggleAllButtons(page)

    // Wait a moment for the state to update
    await page.waitForTimeout(200);
    
    // Check that the configure button is now enabled
    await expect(configureButton).toBeEnabled(); //see if I can change this timeout
    
    // Verify the button text is still correct
    await expect(configureButton).toContainText('Configure and Run Benchmark Tests');

    // Wait for toggle buttons to load
    await page.waitForSelector('[data-testid^="toggle-"]', { timeout: 10000 });
  
    // Get all toggle buttons
    const toggleButtons = page.locator('[data-testid^="toggle-"]');
    const count = await toggleButtons.count();
  
    // Iterate through all toggle buttons and click them
    for (let i = 0; i < count; i++) {
      const toggleButton = toggleButtons.nth(i);
      await toggleButton.click();
      if(i == count - 1){
        // Check that the configure button is now disabled after toggling down all the bundles
        await expect(configureButton).toBeDisabled(); // check if I can timeout here
      }
      else{
        // Check that the configure button is still enabled
        await expect(configureButton).toBeEnabled(); // check if I can timeout here
      }
    }
    
  });

  test('Ensure all elements are displayed on the Select Bundles page with the correct content', async ({ page }) => {
    // Navigate to the view bundles page
    await navigateToViewBundles(page);
    
    // 1. Verify "Back to Home Page" button exists and links to landing page
    const backToHomeButton = page.locator('[data-testid="back-to-home-button"]');
    await expect(backToHomeButton).toBeVisible();
    await expect(backToHomeButton).toContainText('Back to Home Page');
    
    // Verify the button links to landing page (check href attribute or click and verify navigation)
    const backToHomeLink = page.locator('[data-testid="back-to-home-button"]');
    await expect(backToHomeLink).toHaveAttribute('href', '/');
    
    // 2. Verify "Configure and run benchmark test" button is disabled
    const configureButton = page.locator('[data-testid="configure-and-run-benchmark-tests"]');
    await expect(configureButton).toBeVisible();
    await expect(configureButton).toBeDisabled();
    await expect(configureButton).toContainText('Configure and Run Benchmark Tests');
    
    // 3. Verify page header and description text
    const pageHeader = page.locator('h1');
    await expect(pageHeader).toContainText('Select bundles');
    
    const descriptionText = page.locator('[data-testid="select-bundles-description"]');
    await expect(descriptionText).toContainText('Select suitable bundles for your benchmark test');
    
    // 4. Verify breadcrumb navigation
    const breadcrumb = page.locator('[data-testid="Breadcrumb"]');
    await expect(breadcrumb).toBeVisible();
    await expect(breadcrumb).toContainText('New Benchmark Test');
    await expect(breadcrumb).toContainText('Select Recipes Or Bundles');
    
    // 5. Wait for bundle cards to load
    await page.waitForSelector('[data-testid^="bundle-card-"]', { timeout: 10000 });
    
    // Get all bundle cards
    const bundleCards = page.locator('[data-testid^="bundle-card-"]');
    const cardCount = await bundleCards.count();
    
    // Verify at least one bundle card exists
    await expect(cardCount).toBeGreaterThan(0);
    
    // 6. Verify each bundle card contains all required elements
    for (let i = 0; i < Math.min(cardCount, 3); i++) { // Check first 3 cards to avoid long test execution
      const card = bundleCards.nth(i);
      
      // Test Bundle Group text (e.g. IMDA's Starter Kit)
      const bundleGroup = card.locator('[data-testid="bundle-group"]');
      await expect(bundleGroup).toBeVisible();
      await expect(bundleGroup).not.toBeEmpty();
      
      // Test Bundle Name text
      const bundleName = card.locator('[data-testid="bundle-name"]');
      await expect(bundleName).toBeVisible();
      await expect(bundleName).not.toBeEmpty();
      
      // Test Bundle Description text
      const bundleDescription = card.locator('[data-testid="bundle-description"]');
      await expect(bundleDescription).toBeVisible();
      await expect(bundleDescription).not.toBeEmpty();
      
      // Number of Tests
      const numberOfTests = card.locator('[data-testid="number-of-tests"]');
      await expect(numberOfTests).toBeVisible();
      await expect(numberOfTests).toContainText(/\d+/); // Should contain at least one digit
      
      // Number of Prompts
      const numberOfPrompts = card.locator('[data-testid="number-of-prompts"]');
      await expect(numberOfPrompts).toBeVisible();
      await expect(numberOfPrompts).toContainText(/\d+/); // Should contain at least one digit
      
      // List at most 2 Test names
      const testNames = card.locator('[data-testid^="test-name-"]');
      const testNameCount = await testNames.count();
      await expect(testNameCount).toBeLessThanOrEqual(2);
      
      // Verify test names are not empty
      for (let j = 0; j < testNameCount; j++) {
        const testName = testNames.nth(j);
        await expect(testName).toBeVisible();
        await expect(testName).not.toBeEmpty();
      }
      
      // "+{x} more" text if more than 2 Tests
      if (testNameCount === 2) {
        const moreTestsText = card.locator('[data-testid="more-tests-text"]');
        await expect(moreTestsText).toBeVisible();
        await expect(moreTestsText).toContainText(/\+.*more/);
      }
      
      // "Select" checkbox
      const selectCheckbox = card.locator('[data-testid^="toggle-"]');
      await expect(selectCheckbox).toBeVisible();
      await expect(selectCheckbox).toContainText('Select');
      // cannot explicitly verify if a checkbox exists
      
      // "Learn more" text (to add hyperlink in View Tests for Bundle story)
      const learnMoreText = card.locator('[data-testid="learn-more-link"]');
      await expect(learnMoreText).toBeVisible();
      await expect(learnMoreText).toContainText('Learn more');
      
      // Verify learn more is a clickable link
      await expect(learnMoreText).toHaveAttribute('href');
    }
  });

  test('hover over bundle description shows full description in tooltip', async ({ page }) => {
    // Navigate to the view bundles page
    await navigateToViewBundles(page);
    
    // Wait for bundle cards to load
    await page.waitForSelector('[data-testid^="bundle-card-"]', { timeout: 10000 });
    
    // Get the first bundle card
    const bundleCards = page.locator('[data-testid^="bundle-card-"]');
    const firstCard = bundleCards.first();
    
    // Get the bundle description element
    const bundleDescription = firstCard.locator('[data-testid="bundle-description"]');
    await expect(bundleDescription).toBeVisible();
    
    // Get the full description text for comparison
    const descriptionText = await bundleDescription.textContent();
    
    // Hover over the description element
    await bundleDescription.hover();
    
    // Wait for tooltip to appear
    await page.waitForTimeout(500);
    
    // Check that the tooltip content is visible and contains the full description
    const tooltipContent = page.locator('[role="tooltip"] p');
    await expect(tooltipContent).toBeVisible();
    
    // Verify the tooltip contains the same text as the description
    const tooltipText = await tooltipContent.textContent();
    expect(tooltipText.trim()).toBe(descriptionText.trim());

    // remove tooltip test is not done because it is not reliable
  });

});