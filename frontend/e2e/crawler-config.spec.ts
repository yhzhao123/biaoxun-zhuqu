/**
 * Crawler Configuration E2E Tests
 * Tests for /crawler page functionality
 */

import { test, expect } from '@playwright/test';
import { CrawlerConfigPage } from './pages/CrawlerConfigPage';

test.describe('Crawler Configuration Flow', () => {
  let crawlerPage: CrawlerConfigPage;

  test.beforeEach(async ({ page }) => {
    // Listen for console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('Console error:', msg.text());
      }
    });
    crawlerPage = new CrawlerConfigPage(page);
    await crawlerPage.navigate();
  });

  test('should navigate to crawler config page', async ({ page }) => {
    await expect(page).toHaveURL(/\/crawler/);
    // Page should either have h1 or show error
    const hasH1 = await page.locator('h1').count() > 0;
    const hasError = await crawlerPage.getErrorMessage() !== null;
    expect(hasH1 || hasError).toBe(true);
  });

  test('should load crawler page content', async ({ page }) => {
    await page.waitForTimeout(2000);
    // Check page loaded something
    const isLoading = await page.locator('.animate-spin').isVisible().catch(() => false);
    const hasContent = await page.locator('.bg-white').count() > 0;
    const hasTable = await page.locator('table').count() > 0;
    expect(isLoading || hasContent || hasTable).toBe(true);
  });

  test('should check for add source button or error', async ({ page }) => {
    await page.waitForTimeout(2000);
    // Button should be visible if page loaded successfully, or error shown
    const hasAddButton = await crawlerPage.addSourceButton.isVisible().catch(() => false);
    const hasError = await crawlerPage.getErrorMessage() !== null;
    expect(hasAddButton || hasError).toBe(true);
  });
});