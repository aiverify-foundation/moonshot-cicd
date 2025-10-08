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
    // Wait a moment for the state to update
    await page.waitForTimeout(200);
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
    await expect(page.locator('h1')).toContainText('View Bundles');
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
    
    // Check that the configure button is now enabled
    await expect(configureButton).toBeEnabled();
    
    // Verify the button text is still correct
    await expect(configureButton).toContainText('Configure and Run Benchmark Tests');
    
    //toggle down all the bundles

      // Wait for toggle buttons to load
    await page.waitForSelector('[data-testid^="toggle-"]', { timeout: 10000 });
  
    // Get all toggle buttons
    const toggleButtons = page.locator('[data-testid^="toggle-"]');
    const count = await toggleButtons.count();
  
    // Iterate through all toggle buttons and click them
    for (let i = 0; i < count; i++) {
      const toggleButton = toggleButtons.nth(i);
      await toggleButton.click();
      // Wait a moment for the state to update
      await page.waitForTimeout(200);
      if(i == count - 1){
        // Check that the configure button is now disabled after toggling down all the bundles
        await expect(configureButton).toBeDisabled();
      }
      else{
        // Check that the configure button is still enabled
        await expect(configureButton).toBeEnabled();
      }
    }
    
  });

});