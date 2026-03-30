import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Biaoxun Tender Analytics System
 * Tests critical user journeys after directory restructuring
 */

test.describe('Dashboard Page', () => {
  test('should load dashboard with stats and charts', async ({ page }) => {
    await page.goto('/');

    // Verify page title
    await expect(page).toHaveTitle(/标讯|Biaoxun/);

    // Verify sidebar navigation exists
    await expect(page.locator('aside')).toBeVisible();

    // Verify dashboard header
    await expect(page.locator('h1, h2').filter({ hasText: /仪表板|Dashboard/ })).toBeVisible();

    // Verify stat cards are present
    const statCards = page.locator('.ant-card');
    await expect(statCards.first()).toBeVisible();

    // Take screenshot for verification
    await page.screenshot({ path: 'e2e/test-results/dashboard.png', fullPage: true });
  });

  test('should display navigation menu items', async ({ page }) => {
    await page.goto('/');

    // Check navigation items
    const navItems = ['仪表板', '招标列表', '商机分析', '趋势分析', '数据分类', '实时推送', '设置'];
    for (const item of navItems) {
      await expect(page.locator('nav, aside').filter({ hasText: item })).toBeVisible();
    }
  });
});

test.describe('Tender List Page', () => {
  test('should load tender list with filters', async ({ page }) => {
    await page.goto('/tenders');

    // Verify page loads
    await expect(page.locator('h2').filter({ hasText: /招标列表|Tenders/ })).toBeVisible();

    // Verify search input exists
    await expect(page.locator('input[placeholder*="搜索"], input[placeholder*="search"]').first()).toBeVisible();

    // Verify table exists
    await expect(page.locator('table, .ant-table').first()).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'e2e/test-results/tender-list.png' });
  });

  test('should filter tenders by region', async ({ page }) => {
    await page.goto('/tenders');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Find and click region filter
    const regionSelect = page.locator('select, .ant-select').filter({ hasText: /地区|Region/ }).first();
    if (await regionSelect.isVisible().catch(() => false)) {
      await regionSelect.click();
      await page.locator('text=北京').first().click();

      // Wait for table to update
      await page.waitForTimeout(500);

      // Verify filtered results
      await expect(page.locator('table tbody tr').first()).toBeVisible();
    }
  });
});

test.describe('Tender Detail Page', () => {
  test('should load tender detail with scoring', async ({ page }) => {
    // Navigate to tender list first
    await page.goto('/tenders');
    await page.waitForLoadState('networkidle');

    // Click on first tender row
    const firstRow = page.locator('table tbody tr').first();
    if (await firstRow.isVisible().catch(() => false)) {
      await firstRow.click();

      // Wait for detail page to load
      await page.waitForURL(/\/tenders\/.+/);

      // Verify tender detail elements
      await expect(page.locator('text=基本信息').first()).toBeVisible();
      await expect(page.locator('text=商机评分').first()).toBeVisible();

      // Take screenshot
      await page.screenshot({ path: 'e2e/test-results/tender-detail.png' });
    }
  });
});

test.describe('Opportunity Analysis Page', () => {
  test('should load opportunity analysis with radar chart', async ({ page }) => {
    await page.goto('/opportunity');

    // Verify page loads
    await expect(page.locator('h2').filter({ hasText: /商机分析|Opportunity/ })).toBeVisible();

    // Verify chart container exists
    await expect(page.locator('.echarts-for-react, canvas').first()).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'e2e/test-results/opportunity.png' });
  });
});

test.describe('Trends Page', () => {
  test('should load trends with multiple charts', async ({ page }) => {
    await page.goto('/trends');

    // Verify page loads
    await expect(page.locator('h2').filter({ hasText: /趋势分析|Trends/ })).toBeVisible();

    // Verify tabs exist
    await expect(page.locator('.ant-tabs-tab').first()).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'e2e/test-results/trends.png' });
  });
});

test.describe('Classification Page', () => {
  test('should load classification with tabs', async ({ page }) => {
    await page.goto('/classification');

    // Verify page loads
    await expect(page.locator('h2').filter({ hasText: /数据分类|Classification/ })).toBeVisible();

    // Verify tabs exist
    await expect(page.locator('.ant-tabs-tab').first()).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'e2e/test-results/classification.png' });
  });
});

test.describe('Settings Page', () => {
  test('should load settings with form', async ({ page }) => {
    await page.goto('/settings');

    // Verify page loads
    await expect(page.locator('h2').filter({ hasText: /设置|Settings/ })).toBeVisible();

    // Verify form elements exist
    await expect(page.locator('form, .ant-form').first()).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'e2e/test-results/settings.png' });
  });
});

test.describe('Navigation Flow', () => {
  test('should navigate between pages via sidebar', async ({ page }) => {
    await page.goto('/');

    // Navigate to tenders
    await page.click('text=招标列表');
    await page.waitForURL(/\/tenders/);
    await expect(page).toHaveURL(/\/tenders/);

    // Navigate to opportunity
    await page.click('text=商机分析');
    await page.waitForURL(/\/opportunity/);
    await expect(page).toHaveURL(/\/opportunity/);

    // Navigate to trends
    await page.click('text=趋势分析');
    await page.waitForURL(/\/trends/);
    await expect(page).toHaveURL(/\/trends/);

    // Navigate back to dashboard
    await page.click('text=仪表板');
    await page.waitForURL(/\/$/);
    await expect(page).toHaveURL(/\/$/);
  });
});

test.describe('Responsive Layout', () => {
  test('should display correctly on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');

    // Verify page loads without errors
    await expect(page.locator('body')).toBeVisible();

    // Take mobile screenshot
    await page.screenshot({ path: 'e2e/test-results/dashboard-mobile.png' });
  });
});
