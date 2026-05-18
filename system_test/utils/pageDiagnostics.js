/**
 * Diagnostic utility function to print all page elements in a formatted manner
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} [reportTitle='PAGE DIAGNOSTIC REPORT'] - Optional title for the diagnostic report
 */
async function printPageDiagnostics(page, reportTitle = 'PAGE DIAGNOSTIC REPORT') {
  // Wait for page to be fully loaded
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);
  
  console.log('\n' + '='.repeat(80));
  console.log(reportTitle.toUpperCase());
  console.log('='.repeat(80) + '\n');
  
  // Get page URL and title
  const url = page.url();
  const title = await page.title();
  console.log('📍 PAGE INFORMATION:');
  console.log(`   URL: ${url}`);
  console.log(`   Title: ${title}\n`);
  
  // Get all elements with data-testid attributes
  console.log('🔍 ELEMENTS WITH data-testid ATTRIBUTES:');
  const testIdElements = await page.locator('[data-testid]').all();
  for (let i = 0; i < testIdElements.length; i++) {
    const element = testIdElements[i];
    const testId = await element.getAttribute('data-testid');
    const tagName = await element.evaluate(el => el.tagName.toLowerCase());
    const text = await element.textContent().catch(() => '');
    const isVisible = await element.isVisible().catch(() => false);
    const isEnabled = await element.isEnabled().catch(() => false);
    
    console.log(`   [${i + 1}] data-testid="${testId}"`);
    console.log(`       Tag: <${tagName}>`);
    console.log(`       Text: "${text.trim().substring(0, 100)}${text.length > 100 ? '...' : ''}"`);
    console.log(`       Visible: ${isVisible}, Enabled: ${isEnabled}`);
    
    // Get additional attributes
    const role = await element.getAttribute('role').catch(() => null);
    const type = await element.getAttribute('type').catch(() => null);
    const placeholder = await element.getAttribute('placeholder').catch(() => null);
    const value = await element.inputValue().catch(() => null);
    
    if (role) console.log(`       Role: ${role}`);
    if (type) console.log(`       Type: ${type}`);
    if (placeholder) console.log(`       Placeholder: ${placeholder}`);
    if (value) console.log(`       Value: ${value}`);
    console.log('');
  }
  
  // Get all buttons
  console.log('\n🔘 BUTTONS:');
  const buttons = await page.locator('button').all();
  for (let i = 0; i < buttons.length; i++) {
    const button = buttons[i];
    const text = await button.textContent().catch(() => '');
    const isVisible = await button.isVisible().catch(() => false);
    const isDisabled = await button.isDisabled().catch(() => false);
    const testId = await button.getAttribute('data-testid').catch(() => null);
    
    console.log(`   [${i + 1}] "${text.trim()}"`);
    if (testId) console.log(`       data-testid: ${testId}`);
    console.log(`       Visible: ${isVisible}, Disabled: ${isDisabled}`);
    console.log('');
  }
  
  // Get all inputs
  console.log('\n📝 INPUT FIELDS:');
  const inputs = await page.locator('input, textarea, select').all();
  for (let i = 0; i < inputs.length; i++) {
    const input = inputs[i];
    const tagName = await input.evaluate(el => el.tagName.toLowerCase());
    const type = await input.getAttribute('type').catch(() => 'text');
    const placeholder = await input.getAttribute('placeholder').catch(() => null);
    const value = await input.inputValue().catch(() => '');
    const isVisible = await input.isVisible().catch(() => false);
    const isDisabled = await input.isDisabled().catch(() => false);
    const testId = await input.getAttribute('data-testid').catch(() => null);
    
    console.log(`   [${i + 1}] <${tagName} type="${type}">`);
    if (testId) console.log(`       data-testid: ${testId}`);
    if (placeholder) console.log(`       Placeholder: ${placeholder}`);
    if (value) console.log(`       Value: ${value}`);
    console.log(`       Visible: ${isVisible}, Disabled: ${isDisabled}`);
    console.log('');
  }
  
  // Get all headings
  console.log('\n📋 HEADINGS:');
  const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
  for (let i = 0; i < headings.length; i++) {
    const heading = headings[i];
    const level = await heading.evaluate(el => el.tagName.toLowerCase());
    const text = await heading.textContent().catch(() => '');
    const isVisible = await heading.isVisible().catch(() => false);
    const testId = await heading.getAttribute('data-testid').catch(() => null);
    
    console.log(`   [${i + 1}] <${level}> "${text.trim()}"`);
    if (testId) console.log(`       data-testid: ${testId}`);
    console.log(`       Visible: ${isVisible}`);
    console.log('');
  }
  
  // Get all links
  console.log('\n🔗 LINKS:');
  const links = await page.locator('a').all();
  for (let i = 0; i < links.length; i++) {
    const link = links[i];
    const text = await link.textContent().catch(() => '');
    const href = await link.getAttribute('href').catch(() => null);
    const isVisible = await link.isVisible().catch(() => false);
    const testId = await link.getAttribute('data-testid').catch(() => null);
    
    console.log(`   [${i + 1}] "${text.trim()}"`);
    if (testId) console.log(`       data-testid: ${testId}`);
    if (href) console.log(`       href: ${href}`);
    console.log(`       Visible: ${isVisible}`);
    console.log('');
  }
  
  // Get all visible text content (main content areas)
  console.log('\n📄 MAIN CONTENT AREAS:');
  const mainContent = await page.locator('main, [role="main"], article, section').all();
  if (mainContent.length === 0) {
    // Fallback to body if no semantic main content
    const bodyText = await page.locator('body').textContent();
    const lines = bodyText.split('\n').filter(line => line.trim().length > 0).slice(0, 20);
    console.log('   Body content (first 20 non-empty lines):');
    lines.forEach((line, idx) => {
      console.log(`   [${idx + 1}] ${line.trim().substring(0, 80)}${line.length > 80 ? '...' : ''}`);
    });
  } else {
    for (let i = 0; i < mainContent.length; i++) {
      const content = mainContent[i];
      const text = await content.textContent().catch(() => '');
      const lines = text.split('\n').filter(line => line.trim().length > 0).slice(0, 10);
      console.log(`   Content Area [${i + 1}] (first 10 non-empty lines):`);
      lines.forEach((line, idx) => {
        console.log(`      [${idx + 1}] ${line.trim().substring(0, 80)}${line.length > 80 ? '...' : ''}`);
      });
      console.log('');
    }
  }
  
  // Get all dropdowns/comboboxes
  console.log('\n📦 DROPDOWNS/COMBOBOXES:');
  const comboboxes = await page.locator('[role="combobox"], [role="listbox"], select').all();
  for (let i = 0; i < comboboxes.length; i++) {
    const combobox = comboboxes[i];
    const role = await combobox.getAttribute('role').catch(() => 'select');
    const text = await combobox.textContent().catch(() => '');
    const isVisible = await combobox.isVisible().catch(() => false);
    const isExpanded = await combobox.getAttribute('aria-expanded').catch(() => null);
    const testId = await combobox.getAttribute('data-testid').catch(() => null);
    
    console.log(`   [${i + 1}] Role: ${role}`);
    if (testId) console.log(`       data-testid: ${testId}`);
    console.log(`       Text: "${text.trim().substring(0, 60)}${text.length > 60 ? '...' : ''}"`);
    console.log(`       Visible: ${isVisible}`);
    if (isExpanded !== null) console.log(`       Expanded: ${isExpanded}`);
    console.log('');
  }
  
  // Get all dialogs/sheets
  console.log('\n💬 DIALOGS/SHEETS:');
  const dialogs = await page.locator('[role="dialog"], dialog').all();
  for (let i = 0; i < dialogs.length; i++) {
    const dialog = dialogs[i];
    const isVisible = await dialog.isVisible().catch(() => false);
    const text = await dialog.textContent().catch(() => '');
    const testId = await dialog.getAttribute('data-testid').catch(() => null);
    
    console.log(`   [${i + 1}] Dialog/Sheet`);
    if (testId) console.log(`       data-testid: ${testId}`);
    console.log(`       Visible: ${isVisible}`);
    if (text) {
      const lines = text.split('\n').filter(line => line.trim().length > 0).slice(0, 5);
      console.log(`       Content (first 5 lines):`);
      lines.forEach((line, idx) => {
        console.log(`          [${idx + 1}] ${line.trim().substring(0, 60)}${line.length > 60 ? '...' : ''}`);
      });
    }
    console.log('');
  }
  
  // Summary statistics
  console.log('\n📊 SUMMARY STATISTICS:');
  console.log(`   Total elements with data-testid: ${testIdElements.length}`);
  console.log(`   Total buttons: ${buttons.length}`);
  console.log(`   Total inputs: ${inputs.length}`);
  console.log(`   Total headings: ${headings.length}`);
  console.log(`   Total links: ${links.length}`);
  console.log(`   Total comboboxes/dropdowns: ${comboboxes.length}`);
  console.log(`   Total dialogs/sheets: ${dialogs.length}`);
  
  console.log('\n' + '='.repeat(80));
  console.log('END OF DIAGNOSTIC REPORT');
  console.log('='.repeat(80) + '\n');
}

module.exports = { printPageDiagnostics };

