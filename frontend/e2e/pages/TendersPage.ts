import { Page, Locator, expect } from '@playwright/test';

export class TendersPage {
  readonly page: Page;
  readonly searchInput: Locator;
  readonly statusFilter: Locator;
  readonly regionFilter: Locator;
  readonly tenderRows: Locator;
  readonly pagination: Locator;
  readonly nextButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.searchInput = page.getByPlaceholder(/搜索标题|Search/i);
    this.statusFilter = page.locator('select').filter({ hasText: /全部|All/ }).first();
    this.regionFilter = page.locator('select').filter({ hasText: /全部|All/ }).nth(1);
    this.tenderRows = page.locator('table tbody tr');
    this.pagination = page.locator('text=Page');
    this.nextButton = page.getByRole('button', { name: /下一页|Next/i });
  }

  async goto() {
    await this.page.goto('/tenders');
    await this.page.waitForLoadState('networkidle');
  }

  async expectTendersLoaded() {
    await expect(this.page).toHaveURL(/.*tenders/);
    // Wait for loading to complete if loading indicator is shown
    await this.page.locator('text=页面加载中').waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
    await this.page.waitForTimeout(500);
    await expect(this.page.locator('h1')).toContainText(/招标公告|Tender/);
  }

  async search(query: string) {
    await this.searchInput.fill(query);
    await this.page.waitForTimeout(500); // Wait for debounce
    await this.page.waitForLoadState('networkidle');
  }

  async filterByStatus(status: string) {
    await this.statusFilter.selectOption(status);
    await this.page.waitForLoadState('networkidle');
  }

  async getTenderCount() {
    return await this.tenderRows.count();
  }

  async clickFirstTender() {
    const firstTender = this.tenderRows.first().locator('a').first();
    await firstTender.click();
    await this.page.waitForURL(/.*tenders\/\w+/);
  }
}
