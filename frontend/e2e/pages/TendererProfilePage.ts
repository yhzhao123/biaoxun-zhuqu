/**
 * TendererProfilePage - Page Object for Tenderer Profile page
 */

import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class TendererProfilePage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(tendererId: string): Promise<void> {
    await this.page.goto(`/tenderers/${tendererId}`);
    await this.waitForLoading();
  }

  // Header elements
  get pageTitle() {
    return this.page.locator('h1.text-2xl');
  }

  get backLink() {
    return this.page.getByRole('link', { name: '返回' });
  }

  // Stats cards
  get totalTendersCard() {
    return this.page.locator('.grid-cols-1 >> text=招标总数').locator('..').locator('.text-3xl');
  }

  get activeTendersCard() {
    return this.page.locator('.grid-cols-1 >> text=进行中').locator('..').locator('.text-3xl');
  }

  get totalBudgetCard() {
    return this.page.locator('.grid-cols-1 >> text=总预算').locator('..').locator('.text-3xl');
  }

  get industryCountCard() {
    return this.page.locator('.grid-cols-1 >> text=行业数').locator('..').locator('.text-3xl');
  }

  // Sections
  get industriesSection() {
    return this.page.locator('text=行业分布');
  }

  get regionsSection() {
    return this.page.locator('text=地区分布');
  }

  get recentTendersSection() {
    return this.page.locator('text=最近招标');
  }

  get clusterSection() {
    return this.page.locator('text=同Cluster');
  }

  // Methods
  async getTotalTenders(): Promise<string> {
    await this.totalTendersCard.waitFor({ state: 'visible' });
    return await this.totalTendersCard.textContent() || '';
  }

  async getActiveTenders(): Promise<string> {
    await this.activeTendersCard.waitFor({ state: 'visible' });
    return await this.activeTendersCard.textContent() || '';
  }

  async getTotalBudget(): Promise<string> {
    await this.totalBudgetCard.waitFor({ state: 'visible' });
    return await this.totalBudgetCard.textContent() || '';
  }

  async getIndustryCount(): Promise<string> {
    await this.industryCountCard.waitFor({ state: 'visible' });
    return await this.industryCountCard.textContent() || '';
  }

  async getIndustries(): Promise<string[]> {
    const section = this.page.locator('.grid-cols-1 >> text=行业分布').locator('..').locator('.divide-y');
    const items = section.locator('.flex.justify-between');
    const count = await items.count();
    const industries: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await items.nth(i).textContent();
      if (text) {
        industries.push(text.trim());
      }
    }
    return industries;
  }

  async getRegions(): Promise<string[]> {
    const section = this.page.locator('.grid-cols-1 >> text=地区分布').locator('..').locator('.divide-y');
    const items = section.locator('.flex.justify-between');
    const count = await items.count();
    const regions: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await items.nth(i).textContent();
      if (text) {
        regions.push(text.trim());
      }
    }
    return regions;
  }

  async getRecentTenders(): Promise<string[]> {
    const section = this.page.locator('text=最近招标').locator('..').locator('..').locator('.divide-y');
    const items = section.locator('.text-blue-600');
    const count = await items.count();
    const tenders: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await items.nth(i).textContent();
      if (text) {
        tenders.push(text.trim());
      }
    }
    return tenders;
  }

  async hasClusterInfo(): Promise<boolean> {
    return await this.clusterSection.isVisible();
  }

  async getClusterTenderers(): Promise<string[]> {
    if (!(await this.hasClusterInfo())) {
      return [];
    }
    const links = this.clusterSection.locator('..').locator('..').locator('a');
    const count = await links.count();
    const tenderers: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await links.nth(i).textContent();
      if (text) {
        tenderers.push(text.trim());
      }
    }
    return tenderers;
  }

  async isLoading(): Promise<boolean> {
    const spinner = this.page.locator('.animate-spin');
    return await spinner.isVisible();
  }

  async hasError(): Promise<boolean> {
    const error = this.page.locator('.text-red-500');
    return await error.isVisible();
  }

  async getErrorMessage(): Promise<string | null> {
    const error = this.page.locator('.text-red-500');
    if (await error.isVisible()) {
      return await error.textContent();
    }
    return null;
  }
}