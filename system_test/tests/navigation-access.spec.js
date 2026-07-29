const { test, expect } = require('@playwright/test');

const WIKI_URL = 'https://github.com/aiverify-foundation/moonshot-cicd/wiki';
const ISSUES_URL = 'https://github.com/aiverify-foundation/moonshot-cicd/issues';
const REPO_URL = 'https://github.com/aiverify-foundation/moonshot-cicd';
const STARTER_KIT_PDF_URL =
  'https://www.imda.gov.sg/-/media/imda/files/about/emerging-tech-and-research/artificial-intelligence/large-language-model-starter-kit.pdf';

const CTA_LABELS = {
  run: 'Run a benchmark test',
  howTo: 'How-to guide',
  starterKit: "IMDA's Starter Kit",
};

const CTA_SUBTEXTS = {
  run: 'Test LLM apps for safety and reliability',
  howTo: 'Understand how the product works step-by-step',
  starterKit: "Follow IMDA's guidance for safety testing",
};

async function goToLanding(page) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
}

async function assertExternalLinkOpens(page, link, expectedUrl) {
  await expect(link).toHaveAttribute('href', expectedUrl);
  await expect(link).toHaveAttribute('target', '_blank');

  // Destination is asserted via href. Popup proves new-tab behavior.
  // Do not assert popup.url() — PDF / cross-origin destinations often stay
  // on about:blank or never finish document navigation in Chromium.
  const [popup] = await Promise.all([
    page.waitForEvent('popup'),
    link.click(),
  ]);
  expect(popup).toBeTruthy();
  await popup.close();
}

test.describe('MOON-548 Navigation and Access', { tag: '@happy-path' }, () => {
  test('Header renders logo, product name, and version', async ({ page }) => {
    await goToLanding(page);

    const productName = page.locator('h1', { hasText: 'Moonshot' });
    await expect(productName).toBeVisible();

    const logoSection = page.locator('div.flex.items-center.gap-2').filter({ has: productName });
    await expect(logoSection.locator('svg').first()).toBeVisible();

    const version = productName.locator('xpath=following-sibling::p[1]');
    await expect(version).toBeVisible();
    const versionText = (await version.textContent())?.trim() ?? '';
    expect(versionText).toMatch(/^\d+\.\d+\.\d+$/);
    expect(versionText).not.toContain('Beta');
  });

  test('Primary CTA buttons render with correct subtext', async ({ page }) => {
    await goToLanding(page);

    const runCta = page.getByRole('link', { name: new RegExp(CTA_LABELS.run) });
    await expect(runCta).toBeVisible();
    await expect(runCta).toContainText(CTA_SUBTEXTS.run);

    const howToCta = page.getByRole('link', { name: new RegExp(CTA_LABELS.howTo) });
    await expect(howToCta).toBeVisible();
    await expect(howToCta).toContainText(CTA_SUBTEXTS.howTo);

    const starterKitCta = page.getByRole('link', { name: new RegExp(CTA_LABELS.starterKit) });
    await expect(starterKitCta).toBeVisible();
    await expect(starterKitCta).toContainText(CTA_SUBTEXTS.starterKit);
  });

  test('Landing shows exactly three primary CTA buttons', async ({ page }) => {
    await goToLanding(page);

    const runCta = page.getByRole('link', { name: new RegExp(CTA_LABELS.run) });
    const howToCta = page.getByRole('link', { name: new RegExp(CTA_LABELS.howTo) });
    const starterKitCta = page.getByRole('link', { name: new RegExp(CTA_LABELS.starterKit) });

    await expect(runCta).toBeVisible();
    await expect(howToCta).toBeVisible();
    await expect(starterKitCta).toBeVisible();
    await expect(runCta).toHaveCount(1);
    await expect(howToCta).toHaveCount(1);
    await expect(starterKitCta).toHaveCount(1);
  });

  test('How-to guide button links to the user guide wiki', async ({ page }) => {
    await goToLanding(page);

    const howToCta = page.getByRole('link', { name: new RegExp(CTA_LABELS.howTo) });
    await assertExternalLinkOpens(page, howToCta, WIKI_URL);
  });

  test('IMDA Starter Kit button links to the PDF', async ({ page }) => {
    await goToLanding(page);

    const starterKitCta = page.getByRole('link', { name: new RegExp(CTA_LABELS.starterKit) });
    await assertExternalLinkOpens(page, starterKitCta, STARTER_KIT_PDF_URL);
  });

  test('Connector control is absent from the DOM', async ({ page }) => {
    await goToLanding(page);

    await expect(page.getByText(/Connector/i)).toHaveCount(0);
    await expect(page.locator('[data-testid="sidebar-connectors-button"]')).toHaveCount(0);
  });

  test('Header help icon opens the Moonshot wiki', async ({ page }) => {
    await goToLanding(page);

    const help = page.getByLabel('Open Moonshot wiki');
    await expect(help).toBeVisible();
    await assertExternalLinkOpens(page, help, WIKI_URL);
  });

  test('Header issues icon opens the GitHub issues page', async ({ page }) => {
    await goToLanding(page);

    const issues = page.getByLabel('Open Moonshot issues');
    await expect(issues).toBeVisible();
    await assertExternalLinkOpens(page, issues, ISSUES_URL);
  });

  test('Header GitHub icon opens the repository', async ({ page }) => {
    await goToLanding(page);

    const github = page.getByLabel('Open Moonshot GitHub repository');
    await expect(github).toBeVisible();
    await assertExternalLinkOpens(page, github, REPO_URL);
  });

  test('Sidebar shows Home and History, not Connectors', async ({ page }) => {
    await goToLanding(page);

    await expect(page.locator('[data-testid="sidebar-back-to-home-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="sidebar-history-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="sidebar-connectors-button"]')).toHaveCount(0);
  });

  test('Clicking "Run a benchmark test" navigates to the benchmark entry route', async ({ page }) => {
    await goToLanding(page);

    await page.click('[data-testid="benchmark-link"]');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(/\/benchmark\/?$/);
    await expect(page.locator('[data-testid="select-bundles-header"]')).toContainText(
      'Select Test Bundles'
    );
  });

  test('"Run a benchmark test" CTA is an in-app link to /benchmark', async ({ page }) => {
    await goToLanding(page);

    const runLink = page.locator('[data-testid="benchmark-link"]');
    await expect(runLink).toHaveAttribute('href', /\/benchmark\/?$/);
    await expect(runLink).not.toHaveAttribute('target', '_blank');
  });

  test('Back to Home Page from benchmark returns to landing', async ({ page }) => {
    await goToLanding(page);

    await page.click('[data-testid="benchmark-link"]');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/benchmark\/?$/);

    await page.click('[data-testid="back-to-home-button"]');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole('link', { name: new RegExp(CTA_LABELS.run) })).toBeVisible();
  });

  test('Sidebar Home from benchmark returns to landing', async ({ page }) => {
    await goToLanding(page);

    await page.click('[data-testid="benchmark-link"]');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/benchmark\/?$/);

    await page.click('[data-testid="sidebar-back-to-home-button"]');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole('link', { name: new RegExp(CTA_LABELS.run) })).toBeVisible();
  });

  test('Sidebar History from landing navigates to history', async ({ page }) => {
    await goToLanding(page);

    await page.click('[data-testid="sidebar-history-button"]');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(/\/history\/?$/);
  });
});
