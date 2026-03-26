/**
 * LLM Configuration E2E Tests
 */
import { test, expect } from '@playwright/test';

test.describe('LLM Configuration Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173/llm-config');
    await page.waitForLoadState('networkidle');
  });

  test('should navigate to LLM config page', async ({ page }) => {
    await expect(page).toHaveURL(/\/llm-config/);
    const header = page.locator('h1');
    await expect(header).toContainText('大模型配置');
  });

  test('should display add config button', async ({ page }) => {
    const addButton = page.locator('button:has-text("添加配置")');
    await expect(addButton).toBeVisible();
  });

  test('should open config form when clicking add', async ({ page }) => {
    await page.locator('button:has-text("添加配置")').click();
    await expect(page.locator('form')).toBeVisible();
    await expect(page.locator('h2:has-text("添加配置")')).toBeVisible();
    await expect(page.locator('label:has-text("配置名称")')).toBeVisible();
    await expect(page.locator('label:has-text("提供商")')).toBeVisible();
  });

  test('should show provider options in select', async ({ page }) => {
    await page.locator('button:has-text("添加配置")').click();
    const providerSelect = page.locator('select');
    await expect(providerSelect).toBeVisible();

    // Get all options text
    const options = await page.locator('select option').allTextContents();
    expect(options).toContain('Ollama (本地)');
    expect(options).toContain('OpenAI');
    expect(options).toContain('Claude (Anthropic)');
  });

  test('should show usage guide section', async ({ page }) => {
    const guide = page.locator('h3:has-text("使用说明")');
    await expect(guide).toBeVisible();
    await expect(page.locator('text=本地运行的大模型，无需API密钥')).toBeVisible();
  });

  test('should allow canceling form', async ({ page }) => {
    await page.locator('button:has-text("添加配置")').click();
    await expect(page.locator('form')).toBeVisible();

    await page.click('button:has-text("取消")');
    await expect(page.locator('form')).not.toBeVisible();
  });

  test('should show empty state when no configs', async ({ page }) => {
    const emptyText = page.locator('text=暂无配置，请添加一个LLM配置');
    await expect(emptyText).toBeVisible();
  });

  test('should have working back button', async ({ page }) => {
    const backLink = page.locator('a:has-text("返回")');
    await expect(backLink).toBeVisible();
    await backLink.click();
    await expect(page).toHaveURL('http://localhost:5173/');
  });
});
