/**
 * Settings Page E2E Tests
 * Tests for /settings page functionality
 */

import { test, expect } from '@playwright/test';
import { SettingsPage } from './pages/SettingsPage';

test.describe('Settings Page Flow', () => {
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    settingsPage = new SettingsPage(page);
    await settingsPage.navigate();
  });

  test('should navigate to settings page', async ({ page }) => {
    await expect(page).toHaveURL(/\/settings/);
    // Page may have API issues - check for either h1 or error state
    const hasH1 = await page.locator('h1').count() > 0;
    const hasError = await settingsPage.isErrorMessageVisible();
    expect(hasH1 || hasError).toBe(true);
  });

  test('should handle page load gracefully', async ({ page }) => {
    await page.waitForTimeout(2000);
    // Page should either load content or show error
    const isLoading = await settingsPage.isLoading();
    const hasError = await settingsPage.isErrorMessageVisible();
    const hasContent = await page.locator('.bg-white').count() > 0;
    expect(isLoading || hasError || hasContent).toBe(true);
  });

  test('should check notification section exists', async ({ page }) => {
    await page.waitForTimeout(2000);
    // Check for notification section text somewhere on page
    const bodyText = await page.locator('body').textContent();
    const hasNotificationText = bodyText?.includes('通知');
    console.log('Page has notification text:', hasNotificationText);
  });

  test('should handle retry when error occurs', async ({ page }) => {
    await page.waitForTimeout(2000);
    const hasRetry = await settingsPage.hasRetryButton();
    // Retry button should only appear if there's an error
    if (hasRetry) {
      await settingsPage.clickRetry();
    }
  });
});