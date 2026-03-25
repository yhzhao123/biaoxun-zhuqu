/**
 * SettingsPage - Page Object for User Settings/Preferences page
 * Updated with more robust selectors
 */

import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class SettingsPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(): Promise<void> {
    await this.page.goto('/settings');
    await this.waitForLoading();
  }

  // Header
  get pageTitle() {
    return this.page.locator('h1:has-text("用户设置")');
  }

  get backLink() {
    return this.page.locator('a:has-text("返回")');
  }

  // Basic info section - use more specific selector
  get usernameDisplay() {
    return this.page.locator('.text-gray-900').first();
  }

  get emailInput() {
    return this.page.locator('input[type="email"]');
  }

  // Use all selects - the form has 5 selects: region, industry, theme, language, items_per_page
  get allSelects() {
    return this.page.locator('select');
  }

  get regionSelect() {
    return this.allSelects.nth(0);
  }

  get industrySelect() {
    return this.allSelects.nth(1);
  }

  // Notification toggles - look for buttons in the notification section
  get notificationSectionButtons() {
    return this.page.locator('.bg-white:has-text("通知偏好") button');
  }

  // Display settings section
  get themeSelect() {
    // Find select in display settings section
    return this.page.locator('.bg-white:has-text("显示设置") select').nth(0);
  }

  get languageSelect() {
    return this.page.locator('.bg-white:has-text("显示设置") select').nth(1);
  }

  get itemsPerPageSelect() {
    return this.page.locator('.bg-white:has-text("显示设置") select').nth(2);
  }

  // Buttons
  get saveButton() {
    return this.page.getByRole('button', { name: '保存设置' });
  }

  get retryButton() {
    return this.page.getByRole('button', { name: '重试' });
  }

  // Messages
  get successMessage() {
    return this.page.locator('.bg-green-100');
  }

  get errorMessage() {
    return this.page.locator('.bg-red-100');
  }

  get loadingSpinner() {
    return this.page.locator('.animate-spin');
  }

  // Methods
  async getUsername(): Promise<string> {
    await this.usernameDisplay.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
    return await this.usernameDisplay.textContent() || '';
  }

  async getEmail(): Promise<string> {
    return await this.emailInput.inputValue();
  }

  async selectRegion(region: string): Promise<void> {
    await this.regionSelect.selectOption({ label: region });
  }

  async selectIndustry(industry: string): Promise<void> {
    await this.industrySelect.selectOption({ label: industry });
  }

  async selectTheme(theme: string): Promise<void> {
    await this.themeSelect.selectOption({ label: theme });
  }

  async selectLanguage(language: string): Promise<void> {
    const langMap: Record<string, string> = { 'zh': '中文', 'en': 'English' };
    await this.languageSelect.selectOption({ label: langMap[language] || language });
  }

  async selectItemsPerPage(count: number): Promise<void> {
    await this.itemsPerPageSelect.selectOption(count.toString());
  }

  async toggleNotification(index: number): Promise<boolean> {
    const buttons = this.page.locator('.flex.items-center.justify-between button');
    await buttons.nth(index).click();
    await this.page.waitForTimeout(500);
    const classes = await buttons.nth(index).getAttribute('class');
    return classes?.includes('bg-blue-600') || false;
  }

  async toggleEmailNotification(): Promise<boolean> {
    return this.toggleNotification(0);
  }

  async toggleTenderMatchNotification(): Promise<boolean> {
    return this.toggleNotification(1);
  }

  async saveSettings(): Promise<void> {
    await this.saveButton.click();
    await this.page.waitForTimeout(1000);
  }

  async isSuccessMessageVisible(): Promise<boolean> {
    return await this.successMessage.isVisible();
  }

  async getSuccessMessageText(): Promise<string> {
    await this.successMessage.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
    return await this.successMessage.textContent() || '';
  }

  async isErrorMessageVisible(): Promise<boolean> {
    return await this.errorMessage.isVisible();
  }

  async getErrorMessageText(): Promise<string> {
    await this.errorMessage.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
    return await this.errorMessage.textContent() || '';
  }

  async isLoading(): Promise<boolean> {
    return await this.loadingSpinner.isVisible();
  }

  async hasRetryButton(): Promise<boolean> {
    return await this.retryButton.isVisible();
  }

  async clickRetry(): Promise<void> {
    await this.retryButton.click();
    await this.page.waitForTimeout(1000);
  }
}