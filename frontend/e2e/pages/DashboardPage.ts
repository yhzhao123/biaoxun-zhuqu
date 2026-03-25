import { Page, Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly totalTendersCard: Locator;
  readonly activeTendersCard: Locator;
  readonly tendersLink: Locator;
  readonly dashboardTitle: Locator;

  constructor(page: Page) {
    this.page = page;
    this.totalTendersCard = page.locator('text=招标总数').locator('..');
    this.activeTendersCard = page.locator('text=进行中').locator('..');
    // Use specific navigation link for tenders
    this.tendersLink = page.locator('nav').getByRole('link', { name: '招标列表' });
    this.dashboardTitle = page.locator('h1');
  }

  async goto() {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');
  }

  async expectDashboardLoaded() {
    await expect(this.page).toHaveTitle(/BiaoXun/);
    await expect(this.dashboardTitle).toContainText('仪表盘');
    // Wait for loading to complete if loading indicator is shown
    await this.page.locator('text=页面加载中').waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
    await this.page.waitForTimeout(1000);
    // Page is loaded - either shows statistics or shows empty state
  }

  async navigateToTenders() {
    await this.tendersLink.click();
    await this.page.waitForURL('**/tenders');
  }
}
