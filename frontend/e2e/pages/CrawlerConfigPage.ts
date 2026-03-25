/**
 * CrawlerConfigPage - Page Object for Crawler Configuration page
 * Updated with more robust selectors
 */

import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class CrawlerConfigPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(): Promise<void> {
    await this.page.goto('/crawler');
    await this.waitForLoading();
  }

  // Form locators
  get addSourceButton() {
    return this.page.getByRole('button', { name: '添加爬虫源' });
  }

  get formContainer() {
    return this.page.locator('.bg-white.rounded-lg.shadow:has-text("CSS选择器配置")');
  }

  get nameInput() {
    return this.formContainer.locator('input[type="text"]').first();
  }

  get baseUrlInput() {
    return this.formContainer.locator('input[type="url"]');
  }

  get listUrlPatternInput() {
    return this.formContainer.locator('input[placeholder*="page"]');
  }

  get selectorInputs() {
    return this.formContainer.locator('input.text-sm');
  }

  get saveButton() {
    return this.formContainer.getByRole('button', { name: '保存' });
  }

  get cancelButton() {
    return this.formContainer.getByRole('button', { name: '取消' });
  }

  // Table locators
  get sourcesTable() {
    return this.page.locator('table');
  }

  get sourcesRows() {
    return this.page.locator('tbody tr');
  }

  // Actions
  async clickAddSource(): Promise<void> {
    await this.addSourceButton.click();
    await this.page.waitForTimeout(500);
  }

  async fillSourceForm(data: {
    name: string;
    baseUrl: string;
    listUrlPattern?: string;
    selectorTitle?: string;
    selectorContent?: string;
  }): Promise<void> {
    await this.nameInput.fill(data.name);
    await this.baseUrlInput.fill(data.baseUrl);
    if (data.listUrlPattern) {
      await this.listUrlPatternInput.fill(data.listUrlPattern);
    }
    if (data.selectorTitle || data.selectorContent) {
      const inputs = this.selectorInputs;
      if (data.selectorTitle) {
        await inputs.nth(0).fill(data.selectorTitle);
      }
      if (data.selectorContent) {
        await inputs.nth(1).fill(data.selectorContent);
      }
    }
  }

  async saveSource(): Promise<void> {
    await this.saveButton.click();
    await this.page.waitForTimeout(1000);
  }

  async isSourceInList(name: string): Promise<boolean> {
    try {
      await this.sourcesTable.waitFor({ state: 'visible', timeout: 5000 });
      const row = this.page.locator('tbody tr').filter({ hasText: name });
      return await row.count() > 0;
    } catch {
      return false;
    }
  }

  async getSourceRow(name: string) {
    const row = this.page.locator('tbody tr').filter({ hasText: name });
    return {
      row,
      editButton: row.getByRole('button', { name: '编辑' }),
      deleteButton: row.getByRole('button', { name: '删除' }),
      testButton: row.getByRole('button', { name: '测试' }),
    };
  }

  async editSource(name: string): Promise<void> {
    const source = await this.getSourceRow(name);
    await source.editButton.click();
    await this.page.waitForTimeout(500);
  }

  async deleteSource(name: string): Promise<void> {
    const source = await this.getSourceRow(name);
    this.page.on('dialog', dialog => dialog.accept());
    await source.deleteButton.click();
    await this.page.waitForTimeout(1000);
  }

  async testSource(name: string): Promise<void> {
    const source = await this.getSourceRow(name);
    await source.testButton.click();
    await this.page.waitForTimeout(2000);
  }

  async getErrorMessage(): Promise<string | null> {
    const error = this.page.locator('.bg-red-100');
    if (await error.isVisible()) {
      return await error.textContent();
    }
    return null;
  }

  async getSuccessMessage(): Promise<string | null> {
    const success = this.page.locator('.bg-green-100');
    if (await success.isVisible()) {
      return await success.textContent();
    }
    return null;
  }
}