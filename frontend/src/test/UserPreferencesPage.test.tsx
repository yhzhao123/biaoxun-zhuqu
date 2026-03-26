/**
 * UserPreferencesPage tests - Phase 9
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import { render } from './setup';
import { BrowserRouter } from 'react-router-dom';
import { UserPreferencesPage } from '../pages/UserPreferencesPage';
import type { UserPreferences } from '../types';

// Create mock functions at module level
const mockGetUserPreferences = vi.fn();
const mockUpdateUserPreferences = vi.fn();
const mockUpdateNotificationPreferences = vi.fn();

// Mock api module
vi.mock('../services/api', () => ({
  api: {
    getUserPreferences: (...args: unknown[]) => mockGetUserPreferences(...args),
    updateUserPreferences: (...args: unknown[]) => mockUpdateUserPreferences(...args),
    updateNotificationPreferences: (...args: unknown[]) => mockUpdateNotificationPreferences(...args),
  },
}));

const mockPreferences: UserPreferences = {
  id: '1',
  username: '测试用户',
  email: 'test@example.com',
  notification_preferences: {
    email_enabled: true,
    tender_match_enabled: true,
    price_alert_enabled: false,
    system_notifications_enabled: true,
    crawl_complete_enabled: true,
  },
  default_region: '北京市',
  default_industry: '建筑工程',
  display_settings: {
    theme: 'light',
    language: 'zh',
    items_per_page: 20,
  },
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-03-25T00:00:00Z',
};

describe('UserPreferencesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderWithRouter = (ui: React.ReactElement) => {
    return render(<BrowserRouter>{ui}</BrowserRouter>);
  };

  it('should render loading state initially', () => {
    mockGetUserPreferences.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderWithRouter(<UserPreferencesPage />);
    expect(screen.getByText(/加载中/)).toBeInTheDocument();
  });

  it('should render user preferences form', async () => {
    mockGetUserPreferences.mockResolvedValue(mockPreferences);

    renderWithRouter(<UserPreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText('测试用户')).toBeInTheDocument();
      expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
    });
  });

  it('should display notification preferences', async () => {
    mockGetUserPreferences.mockResolvedValue(mockPreferences);

    renderWithRouter(<UserPreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/邮件通知/)).toBeInTheDocument();
      expect(screen.getByText(/招标匹配/)).toBeInTheDocument();
      expect(screen.getByText(/价格提醒/)).toBeInTheDocument();
    });
  });

  it('should display display settings', async () => {
    mockGetUserPreferences.mockResolvedValue(mockPreferences);

    renderWithRouter(<UserPreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/主题/)).toBeInTheDocument();
      expect(screen.getByText(/语言/)).toBeInTheDocument();
      expect(screen.getByText(/每页条数/)).toBeInTheDocument();
    });
  });

  it('should update notification preference', async () => {
    mockGetUserPreferences.mockResolvedValue(mockPreferences);
    mockUpdateNotificationPreferences.mockResolvedValue({
      ...mockPreferences,
      notification_preferences: {
        ...mockPreferences.notification_preferences,
        email_enabled: false,
      },
    });

    renderWithRouter(<UserPreferencesPage />);

    await waitFor(() => {
      // Find and click the email toggle button (first toggle)
      const buttons = screen.getAllByRole('button');
      // Toggle buttons are the ones with class containing 'bg-blue-600' or 'bg-gray-200'
      fireEvent.click(buttons[0]);
    });

    expect(mockUpdateNotificationPreferences).toHaveBeenCalled();
  });

  it('should handle API error gracefully', async () => {
    mockGetUserPreferences.mockRejectedValue(new Error('Network error'));

    renderWithRouter(<UserPreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/加载失败/)).toBeInTheDocument();
    });
  });

  it('should show save button', async () => {
    mockGetUserPreferences.mockResolvedValue(mockPreferences);

    renderWithRouter(<UserPreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/保存设置/)).toBeInTheDocument();
    });
  });

  it('should display default region and industry', async () => {
    mockGetUserPreferences.mockResolvedValue(mockPreferences);

    renderWithRouter(<UserPreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText('北京市')).toBeInTheDocument();
      expect(screen.getByText('建筑工程')).toBeInTheDocument();
    });
  });

  it('should show success message after saving', async () => {
    mockGetUserPreferences.mockResolvedValue(mockPreferences);
    mockUpdateUserPreferences.mockResolvedValue(mockPreferences);

    renderWithRouter(<UserPreferencesPage />);

    await waitFor(() => {
      const saveButton = screen.getByText(/保存设置/);
      fireEvent.click(saveButton);
    });

    await waitFor(() => {
      expect(screen.getByText(/保存成功/)).toBeInTheDocument();
    });
  });
});