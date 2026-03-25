import { test, expect } from '@playwright/test';

test.describe('BiaoXun Basic E2E Tests', () => {
  test('should load the homepage', async ({ page }) => {
    await page.goto('/');

    // Wait for the page to load
    await page.waitForLoadState('domcontentloaded');

    // Verify the app title is visible
    await expect(page.locator('text=BiaoXun')).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'e2e/screenshots/homepage.png', fullPage: true });
  });

  test('should navigate to tenders page', async ({ page }) => {
    await page.goto('/');

    // Click on Tenders link
    const tendersLink = page.getByRole('link', { name: /Tenders|招标/i });
    if (await tendersLink.isVisible().catch(() => false)) {
      await tendersLink.click();
      await page.waitForURL('**/tenders');

      // Verify we're on tenders page
      await expect(page).toHaveURL(/.*tenders/);
    }

    // Take screenshot
    await page.screenshot({ path: 'e2e/screenshots/tenders-page.png', fullPage: true });
  });

  test('should display navigation', async ({ page }) => {
    await page.goto('/');

    // Check if navigation is visible
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();

    // Check for navigation links
    const linkCount = await page.getByRole('link').count();
    expect(linkCount).toBeGreaterThan(0);
  });

  test('should be responsive', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Wait for load
    await page.waitForLoadState('domcontentloaded');

    // Take mobile screenshot
    await page.screenshot({ path: 'e2e/screenshots/mobile-view.png', fullPage: true });

    // Test desktop viewport
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.reload();

    // Take desktop screenshot
    await page.screenshot({ path: 'e2e/screenshots/desktop-view.png', fullPage: true });
  });
});
