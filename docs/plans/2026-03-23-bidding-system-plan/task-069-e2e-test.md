# Task 069: E2E Testing (E2E测试)

## Task Header

| Field | Value |
|-------|-------|
| Task ID | 069 |
| Name | End-to-End Testing |
| Type | test |
| Dependencies | Task 067 (Database Optimization), Task 068 (Cache Strategy) |
| Created | 2026-03-23 |
| Estimated Effort | 10-14 hours |

## Description

Implement comprehensive end-to-end tests using Playwright for the bidding system. Cover critical user journeys including auction browsing, bid placement, real-time updates, auction completion, and payment processing. Tests should validate the integration of database optimizations and caching strategies implemented in previous tasks.

## Files to Create/Modify

### Create
- `e2e/playwright.config.ts` - Playwright configuration
- `e2e/fixtures/user.ts` - Test user fixtures and auth helpers
- `e2e/fixtures/auction.ts` - Auction test data generators
- `e2e/pages/auction-list.page.ts` - Page object for auction listing
- `e2e/pages/auction-detail.page.ts` - Page object for auction detail
- `e2e/pages/bid-modal.page.ts` - Page object for bid placement
- `e2e/tests/smoke.spec.ts` - Smoke tests
- `e2e/tests/critical-path.spec.ts` - Critical user journey tests
- `e2e/tests/concurrent-bidding.spec.ts` - Concurrent bidding scenarios
- `e2e/tests/realtime-updates.spec.ts` - WebSocket real-time tests
- `e2e/utils/test-helpers.ts` - Test utilities and assertions

### Modify
- `package.json` - Add Playwright scripts and dependencies
- `docker-compose.test.yml` - Add E2E test services
- `.github/workflows/e2e.yml` - CI/CD workflow for E2E tests
- `.env.test` - Test environment configuration

## Implementation Steps

### Step 1: Playwright Configuration

```typescript
// e2e/playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'e2e-report' }],
    ['junit', { outputFile: 'e2e-results.xml' }],
  ],

  use: {
    baseURL: process.env.TEST_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],

  webServer: {
    command: 'npm run test:server',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Step 2: Page Objects

```typescript
// e2e/pages/auction-list.page.ts
export class AuctionListPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/auctions');
    await this.page.waitForSelector('[data-testid="auction-list"]');
  }

  async getAuctionCount(): Promise<number> {
    const items = await this.page.locator('[data-testid="auction-item"]').count();
    return items;
  }

  async clickAuction(index: number) {
    await this.page.locator('[data-testid="auction-item"]').nth(index).click();
    await this.page.waitForURL(/\/auctions\/\d+/);
  }

  async filterByCategory(category: string) {
    await this.page.selectOption('[data-testid="category-filter"]', category);
    await this.page.waitForLoadState('networkidle');
  }

  async sortBy(sortOption: 'ending-soon' | 'newest' | 'price-asc' | 'price-desc') {
    await this.page.selectOption('[data-testid="sort-select"]', sortOption);
    await this.page.waitForLoadState('networkidle');
  }
}

// e2e/pages/auction-detail.page.ts
export class AuctionDetailPage {
  constructor(private page: Page) {}

  async getCurrentPrice(): Promise<number> {
    const priceText = await this.page.locator('[data-testid="current-price"]').textContent();
    return parseFloat(priceText?.replace(/[^0-9.]/g, '') || '0');
  }

  async getBidCount(): Promise<number> {
    const countText = await this.page.locator('[data-testid="bid-count"]').textContent();
    return parseInt(countText?.replace(/\D/g, '') || '0');
  }

  async openBidModal() {
    await this.page.click('[data-testid="place-bid-button"]');
    await this.page.waitForSelector('[data-testid="bid-modal"]');
  }

  async getTimeRemaining(): Promise<string> {
    return await this.page.locator('[data-testid="time-remaining"]').textContent() || '';
  }

  async addToWatchlist() {
    await this.page.click('[data-testid="add-watchlist-button"]');
    await this.page.waitForSelector('[data-testid="watchlist-added"]');
  }
}

// e2e/pages/bid-modal.page.ts
export class BidModalPage {
  constructor(private page: Page) {}

  async enterBidAmount(amount: number) {
    await this.page.fill('[data-testid="bid-amount-input"]', amount.toString());
  }

  async submitBid() {
    await this.page.click('[data-testid="submit-bid-button"]');
  }

  async getErrorMessage(): Promise<string> {
    return await this.page.locator('[data-testid="bid-error"]').textContent() || '';
  }

  async getSuccessMessage(): Promise<string> {
    return await this.page.waitForSelector('[data-testid="bid-success"]');
    return await this.page.locator('[data-testid="bid-success"]').textContent() || '';
  }

  async close() {
    await this.page.click('[data-testid="close-modal-button"]');
  }
}
```

### Step 3: Critical Path Tests

```typescript
// e2e/tests/critical-path.spec.ts
import { test, expect } from '@playwright/test';
import { AuctionListPage } from '../pages/auction-list.page';
import { AuctionDetailPage } from '../pages/auction-detail.page';
import { BidModalPage } from '../pages/bid-modal.page';
import { createTestUser, createActiveAuction } from '../fixtures';

test.describe('Critical User Journeys', () => {
  test.beforeEach(async ({ page }) => {
    // Setup test data
    await createTestUser('test@example.com', 'password123');
    await createActiveAuction({
      title: 'Test Auction',
      startingPrice: 100,
      endTime: new Date(Date.now() + 3600000), // 1 hour from now
    });
  });

  test('User can browse and bid on an auction', async ({ page }) => {
    const listPage = new AuctionListPage(page);
    const detailPage = new AuctionDetailPage(page);
    const bidModal = new BidModalPage(page);

    // Step 1: Browse auction list
    await listPage.goto();
    await expect(page.locator('[data-testid="auction-list"]')).toBeVisible();
    const initialCount = await listPage.getAuctionCount();
    expect(initialCount).toBeGreaterThan(0);

    // Step 2: View auction detail
    await listPage.clickAuction(0);
    await expect(page.locator('[data-testid="auction-detail"]')).toBeVisible();

    const initialPrice = await detailPage.getCurrentPrice();
    const initialBidCount = await detailPage.getBidCount();

    // Step 3: Place a bid
    await detailPage.openBidModal();
    await bidModal.enterBidAmount(initialPrice + 10);
    await bidModal.submitBid();

    // Step 4: Verify bid success
    const successMessage = await bidModal.getSuccessMessage();
    expect(successMessage).toContain('Bid placed successfully');
    await bidModal.close();

    // Step 5: Verify updated state
    await page.waitForTimeout(500); // Wait for state update
    const newPrice = await detailPage.getCurrentPrice();
    const newBidCount = await detailPage.getBidCount();

    expect(newPrice).toBe(initialPrice + 10);
    expect(newBidCount).toBe(initialBidCount + 1);
  });

  test('User cannot bid below minimum increment', async ({ page }) => {
    const listPage = new AuctionListPage(page);
    const detailPage = new AuctionDetailPage(page);
    const bidModal = new BidModalPage(page);

    await listPage.goto();
    await listPage.clickAuction(0);

    const currentPrice = await detailPage.getCurrentPrice();

    await detailPage.openBidModal();
    await bidModal.enterBidAmount(currentPrice + 1); // Too low increment
    await bidModal.submitBid();

    const errorMessage = await bidModal.getErrorMessage();
    expect(errorMessage).toContain('Minimum bid increment');
  });

  test('User can add auction to watchlist', async ({ page }) => {
    const listPage = new AuctionListPage(page);
    const detailPage = new AuctionDetailPage(page);

    await listPage.goto();
    await listPage.clickAuction(0);

    await detailPage.addToWatchlist();

    // Verify watchlist persistence
    await page.goto('/watchlist');
    await expect(page.locator('[data-testid="watchlist-item"]')).toHaveCount(1);
  });
});
```

### Step 4: Concurrent Bidding Tests

```typescript
// e2e/tests/concurrent-bidding.spec.ts
import { test, expect } from '@playwright/test';
import { createTestUser, createActiveAuction } from '../fixtures';

test.describe('Concurrent Bidding Scenarios', () => {
  test('Multiple users bidding simultaneously', async ({ browser }) => {
    // Setup auction
    const auction = await createActiveAuction({
      title: 'Concurrent Test Auction',
      startingPrice: 100,
    });

    // Create multiple user contexts
    const contexts = await Promise.all([
      browser.newContext(),
      browser.newContext(),
      browser.newContext(),
    ]);

    const users = ['user1@test.com', 'user2@test.com', 'user3@test.com'];

    // Login each user
    for (let i = 0; i < contexts.length; i++) {
      const page = await contexts[i].newPage();
      await createTestUser(users[i], 'password123');
      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', users[i]);
      await page.fill('[data-testid="password-input"]', 'password123');
      await page.click('[data-testid="login-button"]');
      await page.waitForURL('/');
    }

    // Navigate all users to the same auction
    const pages = await Promise.all(
      contexts.map(ctx => {
        const page = ctx.pages()[0];
        return page.goto(`/auctions/${auction.id}`);
      })
    );

    // Place bids simultaneously
    const bidPromises = pages.map(async (page, index) => {
      await page.click('[data-testid="place-bid-button"]');
      await page.fill('[data-testid="bid-amount-input"]', (150 + index * 10).toString());
      await page.click('[data-testid="submit-bid-button"]');
      return page.waitForSelector('[data-testid="bid-success"], [data-testid="bid-error"]');
    });

    const results = await Promise.all(bidPromises);

    // Verify only the highest bid wins
    const mainPage = contexts[0].pages()[0];
    await mainPage.reload();
    const finalPrice = await mainPage.locator('[data-testid="current-price"]').textContent();
    expect(parseFloat(finalPrice?.replace(/[^0-9.]/g, '') || '0')).toBe(180); // Highest bid

    // Cleanup
    await Promise.all(contexts.map(ctx => ctx.close()));
  });

  test('Bid button disabled when auction ends', async ({ page }) => {
    // Create auction ending in 3 seconds
    const auction = await createActiveAuction({
      title: 'Ending Soon Auction',
      startingPrice: 100,
      endTime: new Date(Date.now() + 3000),
    });

    await page.goto(`/auctions/${auction.id}`);
    await expect(page.locator('[data-testid="place-bid-button"]')).toBeEnabled();

    // Wait for auction to end
    await page.waitForTimeout(3500);
    await page.reload();

    await expect(page.locator('[data-testid="place-bid-button"]')).toBeDisabled();
    await expect(page.locator('[data-testid="auction-ended-badge"]')).toBeVisible();
  });
});
```

### Step 5: Real-time Update Tests

```typescript
// e2e/tests/realtime-updates.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Real-time Bid Updates', () => {
  test('Price updates in real-time via WebSocket', async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    // Both users view same auction
    await page1.goto('/auctions/123');
    await page2.goto('/auctions/123');

    const initialPrice1 = await page1.locator('[data-testid="current-price"]').textContent();

    // User 2 places bid
    await page2.click('[data-testid="place-bid-button"]');
    await page2.fill('[data-testid="bid-amount-input"]', '200');
    await page2.click('[data-testid="submit-bid-button"]');
    await page2.waitForSelector('[data-testid="bid-success"]');

    // Verify User 1 sees update without refresh
    await expect(page1.locator('[data-testid="current-price"]')).toHaveText('$200.00', {
      timeout: 3000,
    });

    // Verify bid history updates
    await expect(page1.locator('[data-testid="bid-history-item"]')).toHaveCount(1);

    await context1.close();
    await context2.close();
  });

  test('Connection recovery after network interruption', async ({ page }) => {
    await page.goto('/auctions/123');

    // Simulate network offline
    await page.context().setOffline(true);
    await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Offline');

    // Simulate network back online
    await page.context().setOffline(false);
    await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Online', {
      timeout: 5000,
    });

    // Verify reconnect and data sync
    await expect(page.locator('[data-testid="current-price"]')).toBeVisible();
  });
});
```

### Step 6: Package.json Scripts

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:smoke": "playwright test --grep @smoke",
    "test:server": "npm run build && npm run start:test"
  },
  "devDependencies": {
    "@playwright/test": "^1.40.0"
  }
}
```

## Verification Steps

### Pre-merge Checklist
- [ ] All critical path tests pass
- [ ] Concurrent bidding tests pass
- [ ] Real-time update tests pass
- [ ] Cross-browser tests pass (Chrome, Firefox, Safari)
- [ ] Mobile responsive tests pass
- [ ] Smoke tests complete in < 5 minutes

### CI Integration
```yaml
# .github/workflows/e2e.yml
name: E2E Tests
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - name: Install dependencies
        run: npm ci
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Run E2E tests
        run: npm run test:e2e
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: e2e-report
          path: e2e-report/
```

### Test Data Verification
- [ ] Test fixtures create consistent data state
- [ ] Database cleanup runs after each test
- [ ] Parallel test execution works correctly
- [ ] No test interdependencies

## Rollback Plan

1. Disable E2E workflow in GitHub Actions
2. Revert Playwright configuration changes
3. Remove E2E test directory from test suite
4. Update CI to skip E2E stage

## Git Commit Message

```
test(e2e): implement Playwright end-to-end tests for bidding system

- Add Playwright configuration with multi-browser support
- Create page objects for auction list, detail, and bid modal
- Implement critical path tests for complete user journeys
- Add concurrent bidding scenario tests
- Create real-time WebSocket update tests
- Configure test fixtures for users and auctions
- Add mobile responsive test coverage
- Integrate E2E tests into CI/CD pipeline
- Generate HTML and JUnit test reports

Task: 069
```

## Notes

- Tests depend on Task 067 (DB optimization) and Task 068 (Cache) being stable
- Use data-testid attributes for reliable element selection
- Test database should be isolated and reset for each test run
- Consider visual regression testing for critical UI components
- Performance budgets: E2E tests should complete in < 10 minutes
