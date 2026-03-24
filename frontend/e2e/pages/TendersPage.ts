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
    this.searchInput = page.getByPlaceholder('Search by title, tenderer...');
    this.statusFilter = page.locator('select').filter({ hasText: 'All' }).first();
    this.regionFilter = page.locator('select').filter({ hasText: 'All' }).nth(1);
    this.tenderRows = page.locator('table tbody tr');
    this.pagination = page.locator('text=Page');
    this.nextButton = page.getByRole('button', { name: 'Next' });
  }

  async goto() {
    await this.page.goto('/tenders');
    await this.page.waitForLoadState('networkidle');
  }

  async expectTendersLoaded() {
    await expect(this.page).toHaveURL(/.*tenders/);
    await expect(this.page.locator('h1')).toContainText('Tender Notices');
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
