const { test, expect } = require('@playwright/test');

test.describe('Moonshot Integration Tests', () => {

  test('navigate to view bundles page', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Click on the "View Bundles" link using data-testid
    await page.click('[data-testid="view-bundles-link"]');
    
    // Wait for navigation to complete
    await page.waitForLoadState('networkidle');
    
    // Verify we're on the bundles page by checking the URL
    await expect(page).toHaveURL(/.*\/view_bundles/);
    
    // Check that the configure button is disabled (no bundles selected)
    const configureButton = page.locator('[data-testid="configure-and-run-benchmark-tests"]');
    await expect(configureButton).toBeDisabled();
    
    // Click the disabled button
    await configureButton.click();
    
    // Verify we're still on the same page (no navigation occurred)
    await expect(page).toHaveURL(/.*\/view_bundles/);
    
    // Verify the page content is still there
    await expect(page.locator('h1')).toContainText('View Bundles');
  });

});