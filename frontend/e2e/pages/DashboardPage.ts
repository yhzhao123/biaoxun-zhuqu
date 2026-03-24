import { Page, Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly totalTendersCard: Locator;
  readonly activeTendersCard: Locator;
  readonly tendersLink: Locator;

  constructor(page: Page) {
    this.page = page;
    this.totalTendersCard = page.locator('text=Total Tenders').locator('..');
    this.activeTendersCard = page.locator('text=Active Tenders').locator('..');
    this.tendersLink = page.getByRole('link', { name: 'Tenders' });
  }

  async goto() {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');
  }

  async expectDashboardLoaded() {
    await expect(this.page).toHaveTitle(/BiaoXun/);
    await expect(this.page.locator('h1')).toContainText('Dashboard');
    await expect(this.totalTendersCard).toBeVisible();
    await expect(this.activeTendersCard).toBeVisible();
  }

  async navigateToTenders() {
    await this.tendersLink.click();
    await this.page.waitForURL('**/tenders');
  }
}
