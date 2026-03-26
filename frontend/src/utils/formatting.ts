/**
 * Formatting utilities extracted from TenderList, NotificationCenter, DashboardPage
 * Phase 4 - Task 020-021
 */

/**
 * Format date string to Chinese locale date
 */
export function formatDate(dateString?: string | null): string {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('zh-CN');
}

/**
 * Format budget with currency symbol
 */
export function formatBudget(budget?: number | null, currency?: string): string {
  if (!budget) return '-';
  const symbol = currency === 'CNY' ? '¥' : currency === 'USD' ? '$' : currency === 'EUR' ? '€' : '€';
  return `${symbol}${budget.toLocaleString()}`;
}

/**
 * Get status color CSS classes
 */
export function getStatusColor(status: string): string {
  switch (status) {
    case 'active':
      return 'bg-green-100 text-green-800';
    case 'pending':
      return 'bg-yellow-100 text-yellow-800';
    case 'closed':
      return 'bg-gray-100 text-gray-800';
    case 'expired':
      return 'bg-red-100 text-red-800';
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'running':
      return 'bg-blue-100 text-blue-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

/**
 * Get Chinese status text
 */
export function getStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    active: '进行中',
    pending: '待处理',
    closed: '已关闭',
    expired: '已过期',
    completed: '已完成',
    running: '进行中',
    failed: '失败',
  };
  return statusMap[status] || status;
}

/**
 * Get notification icon by type
 */
export function getNotificationIcon(type: string): string {
  switch (type) {
    case 'tender_match':
      return '📋';
    case 'price_alert':
      return '💰';
    case 'crawl_complete':
      return '✅';
    case 'system':
      return '🔔';
    default:
      return '🔔';
  }
}

/**
 * Get provider icon by provider name
 */
export function getProviderIcon(provider?: string): string {
  switch (provider) {
    case 'ollama':
      return '🤖';
    case 'openai':
      return '🧠';
    case 'claude':
      return '📝';
    default:
      return '💬';
  }
}