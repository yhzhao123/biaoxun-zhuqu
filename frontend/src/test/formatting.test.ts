/**
 * Tests for formatting utilities (formatDate, formatBudget, getStatusColor, getStatusText)
 * TDD - RED phase: Tests that describe the expected behavior
 */

import {
  formatDate,
  formatBudget,
  getStatusColor,
  getStatusText,
  getNotificationIcon,
  getProviderIcon,
} from '../utils/formatting';

describe('formatDate', () => {
  it('should return "-" for undefined date string', () => {
    expect(formatDate(undefined)).toBe('-');
  });

  it('should return "-" for null date string', () => {
    expect(formatDate(null)).toBe('-');
  });

  it('should return "-" for empty string', () => {
    expect(formatDate('')).toBe('-');
  });

  it('should format valid date string to Chinese locale', () => {
    const result = formatDate('2024-01-15');
    expect(result).toBe('2024/1/15');
  });

  it('should format ISO date string correctly', () => {
    const result = formatDate('2024-12-25T10:30:00Z');
    expect(result).toMatch(/\d{4}\/\d{1,2}\/\d{1,2}/);
  });
});

describe('formatBudget', () => {
  it('should return "-" for undefined budget', () => {
    expect(formatBudget(undefined)).toBe('-');
  });

  it('should return "-" for null budget', () => {
    expect(formatBudget(null)).toBe('-');
  });

  it('should return "-" for zero budget', () => {
    expect(formatBudget(0)).toBe('-');
  });

  it('should format CNY budget with ¥ symbol', () => {
    expect(formatBudget(100000, 'CNY')).toBe('¥100,000');
  });

  it('should format USD budget with $ symbol', () => {
    expect(formatBudget(50000, 'USD')).toBe('$50,000');
  });

  it('should format EUR budget with € symbol', () => {
    expect(formatBudget(75000, 'EUR')).toBe('€75,000');
  });

  it('should default to € for unknown currency', () => {
    expect(formatBudget(10000, 'GBP')).toBe('€10,000');
  });

  it('should format large numbers with comma separators', () => {
    expect(formatBudget(1234567, 'CNY')).toBe('¥1,234,567');
  });
});

describe('getStatusColor', () => {
  it('should return green for active status', () => {
    expect(getStatusColor('active')).toBe('bg-green-100 text-green-800');
  });

  it('should return yellow for pending status', () => {
    expect(getStatusColor('pending')).toBe('bg-yellow-100 text-yellow-800');
  });

  it('should return gray for closed status', () => {
    expect(getStatusColor('closed')).toBe('bg-gray-100 text-gray-800');
  });

  it('should return red for expired status', () => {
    expect(getStatusColor('expired')).toBe('bg-red-100 text-red-800');
  });

  it('should return gray for unknown status', () => {
    expect(getStatusColor('unknown')).toBe('bg-gray-100 text-gray-800');
  });
});

describe('getStatusText', () => {
  it('should return Chinese text for active status', () => {
    expect(getStatusText('active')).toBe('进行中');
  });

  it('should return Chinese text for pending status', () => {
    expect(getStatusText('pending')).toBe('待处理');
  });

  it('should return Chinese text for closed status', () => {
    expect(getStatusText('closed')).toBe('已关闭');
  });

  it('should return Chinese text for expired status', () => {
    expect(getStatusText('expired')).toBe('已过期');
  });

  it('should return original status for unknown status', () => {
    expect(getStatusText('unknown')).toBe('unknown');
  });
});

describe('getNotificationIcon', () => {
  it('should return correct icon for tender_match type', () => {
    expect(getNotificationIcon('tender_match')).toBe('📋');
  });

  it('should return correct icon for price_alert type', () => {
    expect(getNotificationIcon('price_alert')).toBe('💰');
  });

  it('should return correct icon for crawl_complete type', () => {
    expect(getNotificationIcon('crawl_complete')).toBe('✅');
  });

  it('should return correct icon for system type', () => {
    expect(getNotificationIcon('system')).toBe('🔔');
  });

  it('should return default icon for unknown type', () => {
    expect(getNotificationIcon('unknown')).toBe('🔔');
  });
});

describe('getProviderIcon', () => {
  it('should return correct icon for ollama provider', () => {
    expect(getProviderIcon('ollama')).toBe('🤖');
  });

  it('should return correct icon for openai provider', () => {
    expect(getProviderIcon('openai')).toBe('🧠');
  });

  it('should return correct icon for claude provider', () => {
    expect(getProviderIcon('claude')).toBe('📝');
  });

  it('should return default icon for unknown provider', () => {
    expect(getProviderIcon('unknown')).toBe('💬');
  });

  it('should return default icon for undefined provider', () => {
    expect(getProviderIcon(undefined)).toBe('💬');
  });
});