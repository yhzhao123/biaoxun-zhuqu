/**
 * BasePage - Base Page Object class with common functionality
 */

import { Page } from '@playwright/test';

export class BasePage {
  protected page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async navigate(path: string): Promise<void> {
    await this.page.goto(path);
  }

  async waitForLoading(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({ path: `e2e/test-results/screenshots/${name}.png`, fullPage: true });
  }

  async clickButton(text: string): Promise<void> {
    await this.page.getByRole('button', { name: text }).click();
  }

  async getText(selector: string): Promise<string> {
    return await this.page.locator(selector).textContent() || '';
  }

  async waitForElement(selector: string, timeout = 10000): Promise<void> {
    await this.page.locator(selector).waitFor({ state: 'visible', timeout });
  }
}