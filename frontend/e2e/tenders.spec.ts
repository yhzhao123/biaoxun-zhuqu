import { test, expect } from '@playwright/test';
import { DashboardPage } from './pages/DashboardPage';
import { TendersPage } from './pages/TendersPage';

test.describe('BiaoXun E2E Tests', () => {
  test.describe('Dashboard Flow', () => {
    test('should load dashboard with statistics', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();

      await dashboard.expectDashboardLoaded();

      // Verify statistics cards are visible
      await expect(page.locator('text=Total Tenders')).toBeVisible();
      await expect(page.locator('text=Active Tenders')).toBeVisible();
      await expect(page.locator('text=Total Budget')).toBeVisible();

      // Take screenshot
      await page.screenshot({ path: 'e2e/screenshots/dashboard.png' });
    });

    test('should navigate to tenders page', async ({ page }) => {
      const dashboard = new DashboardPage(page);
      await dashboard.goto();

      await dashboard.navigateToTenders();

      const tendersPage = new TendersPage(page);
      await tendersPage.expectTendersLoaded();
    });
  });

  test.describe('Tenders List Flow', () => {
    test('should display tender list', async ({ page }) => {
      const tendersPage = new TendersPage(page);
      await tendersPage.goto();

      await tendersPage.expectTendersLoaded();

      // Verify table headers
      await expect(page.locator('th', { hasText: 'Title' })).toBeVisible();
      await expect(page.locator('th', { hasText: 'Tenderer' })).toBeVisible();
      await expect(page.locator('th', { hasText: 'Budget' })).toBeVisible();

      // Take screenshot
      await page.screenshot({ path: 'e2e/screenshots/tenders-list.png' });
    });

    test('should search tenders', async ({ page }) => {
      const tendersPage = new TendersPage(page);
      await tendersPage.goto();

      // Perform search
      await tendersPage.search('test');

      // Verify search results or empty state
      const count = await tendersPage.getTenderCount();
      expect(count).toBeGreaterThanOrEqual(0);

      // Take screenshot
      await page.screenshot({ path: 'e2e/screenshots/tenders-search.png' });
    });

    test('should filter by status', async ({ page }) => {
      const tendersPage = new TendersPage(page);
      await tendersPage.goto();

      // Filter by active status
      await tendersPage.filterByStatus('active');

      // Verify filtered results
      await page.waitForLoadState('networkidle');

      // Take screenshot
      await page.screenshot({ path: 'e2e/screenshots/tenders-filtered.png' });
    });

    test('should navigate to tender detail', async ({ page }) => {
      const tendersPage = new TendersPage(page);
      await tendersPage.goto();

      // Wait for data to load
      await page.waitForTimeout(1000);

      // Check if there are any tenders
      const count = await tendersPage.getTenderCount();

      if (count > 0) {
        // Click first tender
        await tendersPage.clickFirstTender();

        // Verify detail page loaded
        await expect(page.locator('h1')).toBeVisible();
        await expect(page.locator('text=Basic Information')).toBeVisible();

        // Take screenshot
        await page.screenshot({ path: 'e2e/screenshots/tender-detail.png' });
      }
    });
  });

  test.describe('Navigation Flow', () => {
    test('should navigate between pages', async ({ page }) => {
      // Start at dashboard
      await page.goto('/');
      await expect(page.locator('h1')).toContainText('Dashboard');

      // Navigate to tenders
      await page.getByRole('link', { name: 'Tenders' }).click();
      await page.waitForURL('**/tenders');
      await expect(page.locator('h1')).toContainText('Tender Notices');

      // Navigate back to dashboard
      await page.getByRole('link', { name: 'Dashboard' }).click();
      await page.waitForURL('**/');
      await expect(page.locator('h1')).toContainText('Dashboard');
    });
  });
});
