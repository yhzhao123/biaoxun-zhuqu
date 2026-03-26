/**
 * Analysis Chat E2E Tests
 */
import { test, expect } from '@playwright/test';

test.describe('Analysis Chat Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173/analysis-chat');
    await page.waitForLoadState('networkidle');
  });

  test('should navigate to analysis chat page', async ({ page }) => {
    await expect(page).toHaveURL(/\/analysis-chat/);
  });

  test('should show welcome screen for new users', async ({ page }) => {
    const welcomeTitle = page.locator('h2:has-text("招标信息分析助手")');
    await expect(welcomeTitle).toBeVisible();

    const description = page.locator('text=我可以帮你分析招标信息');
    await expect(description).toBeVisible();
  });

  test('should have new conversation button in welcome', async ({ page }) => {
    const newConvButton = page.locator('button:has-text("开始新对话")').first();
    await expect(newConvButton).toBeVisible();
  });

  test('should have sample analysis button', async ({ page }) => {
    const sampleButton = page.locator('button:has-text("分析示例招标")');
    await expect(sampleButton).toBeVisible();
  });

  test('should show LLM status in header', async ({ page }) => {
    // The LLM status shows in the header as either:
    // - "{icon} {config_name}" when configured (e.g., "🧠 openrouter")
    // - "⚠️ 未配置LLM" when not configured
    // Use getByText to find the element containing the emoji indicator
    const llmStatus = page.getByText(/🤖|🧠|📝|⚠️/).first();
    await expect(llmStatus).toBeVisible();
  });

  test('should show config link when LLM not configured', async ({ page }) => {
    // Check for warning about LLM not configured (only visible when no default config)
    const warning = page.locator('text=尚未配置LLM');
    const isVisible = await warning.isVisible().catch(() => false);

    if (isVisible) {
      const configLink = page.locator('.bg-orange-50 a:has-text("大模型配置")');
      await expect(configLink).toBeVisible();
    }
  });

  test('should toggle sidebar', async ({ page }) => {
    // First check sidebar is visible
    const sidebar = page.locator('text=对话历史');
    await expect(sidebar).toBeVisible();

    // Click toggle button
    await page.click('text=◀');

    // Sidebar should be hidden (button changes to ▶)
    await expect(page.locator('text=▶')).toBeVisible();
  });

  test('should have back button in header', async ({ page }) => {
    const backLink = page.locator('a:has-text("返回")');
    await expect(backLink).toBeVisible();
    await backLink.click();
    await expect(page).toHaveURL('http://localhost:5173/');
  });

  test('should start new conversation from welcome', async ({ page }) => {
    // Mock the config API to return a valid config
    await page.route('**/api/v1/llm/configs/default/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          name: 'Test Config',
          provider: 'ollama',
          model_name: 'qwen2.5:7b',
          is_active: true,
          is_default: true,
        }),
      });
    });

    // Mock the conversations list API
    await page.route('**/api/v1/llm/chat/', async (route, request) => {
      if (request.method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        });
      } else if (request.method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            title: '新对话',
            created_at: new Date().toISOString(),
            messages: []
          }),
        });
      }
    });

    // Mock the conversation detail API
    await page.route('**/api/v1/llm/chat/1/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          title: '新对话',
          created_at: new Date().toISOString(),
          messages: []
        }),
      });
    });

    // Reload the page to apply mocks
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Click the new conversation button
    await page.locator('button:has-text("开始新对话")').first().click();

    // After clicking, input area should appear with the correct placeholder
    const textarea = page.locator('textarea[placeholder="输入消息..."]');
    await expect(textarea).toBeVisible();
  });

  test('should show sidebar with conversation list', async ({ page }) => {
    const sidebarHeader = page.locator('.w-64 .p-4 h2');
    await expect(sidebarHeader).toContainText('对话历史');
  });

  test('should have navigation link to analysis chat', async ({ page }) => {
    // Check navigation menu has the link
    const navLink = page.locator('nav a:has-text("AI分析")');
    await expect(navLink).toBeVisible();
  });

  test('should create conversation and send message', async ({ page }) => {
    // Mock the APIs for this test
    await page.route('**/api/v1/llm/configs/default/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          name: 'Test Config',
          provider: 'openai',
          model_name: 'gpt-4',
          is_active: true,
          is_default: true,
        }),
      });
    });

    await page.route('**/api/v1/llm/chat/', async (route, request) => {
      if (request.method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        });
      } else if (request.method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 2,
            title: '新对话',
            created_at: new Date().toISOString(),
            messages: []
          }),
        });
      }
    });

    await page.route('**/api/v1/llm/chat/2/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 2,
          title: '新对话',
          created_at: new Date().toISOString(),
          messages: []
        }),
      });
    });

    await page.route('**/api/v1/llm/chat/2/send/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'This is a test AI response.',
          conversation_id: 2,
          extracted_entities: {}
        }),
      });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Click new conversation button
    await page.locator('button:has-text("开始新对话")').first().click();

    // Verify textarea is visible
    const textarea = page.locator('textarea');
    await expect(textarea).toBeVisible();

    // Type a message
    await textarea.fill('Test message');

    // Click send button
    await page.locator('button:has-text("发送")').click();

    // Wait for response (user message should appear)
    const userMessage = page.locator('.bg-blue-600.text-white:has-text("Test message")');
    await expect(userMessage).toBeVisible();
  });
});
