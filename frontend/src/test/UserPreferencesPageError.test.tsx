/**
 * UserPreferencesPage.test.tsx - Phase 9
 * Tests for user preferences page with error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from './setup';
import { UserPreferencesPage } from '../pages/UserPreferencesPage';
import * as api from '../services/api';

// Mock the API module
vi.mock('../services/api', () => ({
  api: {
    getUserPreferences: vi.fn(),
    updateUserPreferences: vi.fn(),
    updateNotificationPreferences: vi.fn(),
  },
}));

describe('UserPreferencesPage Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should show error state when API fails', async () => {
    // Arrange: Mock API failure
    vi.mocked(api.api.getUserPreferences).mockRejectedValue(new Error('Network error'));

    // Act: Render component
    render(<UserPreferencesPage />);

    // Assert: Should show error message
    await waitFor(() => {
      expect(screen.getByText(/加载失败/i)).toBeInTheDocument();
    });
  });

  it('should show retry button when API fails', async () => {
    // Arrange: Mock API failure
    vi.mocked(api.api.getUserPreferences).mockRejectedValue(new Error('Network error'));

    // Act: Render component
    render(<UserPreferencesPage />);

    // Assert: Should show retry button
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /重试/i })).toBeInTheDocument();
    });
  });

  it('should retry loading when retry button is clicked', async () => {
    // Arrange: Mock API failure then success
    const mockData = {
      username: 'testuser',
      email: 'test@example.com',
      notification_preferences: {
        email_enabled: true,
        tender_match_enabled: false,
        price_alert_enabled: false,
        system_notifications_enabled: true,
        crawl_complete_enabled: false,
      },
      display_settings: {
        theme: 'light',
        language: 'zh',
        items_per_page: 20,
      },
    };
    vi.mocked(api.api.getUserPreferences)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce(mockData);

    // Act: Render and click retry
    render(<UserPreferencesPage />);
    await waitFor(() => screen.getByRole('button', { name: /重试/i }));
    await userEvent.click(screen.getByRole('button', { name: /重试/i }));

    // Assert: Should call API twice
    await waitFor(() => {
      expect(api.api.getUserPreferences).toHaveBeenCalledTimes(2);
    });
  });

  it('should use default data when API returns empty', async () => {
    // Arrange: Mock API returning null
    vi.mocked(api.api.getUserPreferences).mockResolvedValue(null as any);

    // Act: Render component
    render(<UserPreferencesPage />);

    // Assert: Should show default username
    await waitFor(() => {
      expect(screen.getByText(/用户/i)).toBeInTheDocument();
    });
  });

  it('should not use console.error for error handling', async () => {
    // Arrange: Spy on console.error
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(api.api.getUserPreferences).mockRejectedValue(new Error('Network error'));

    // Act: Render component
    render(<UserPreferencesPage />);
    await waitFor(() => screen.getByText(/加载失败/i));

    // Assert: Should not call console.error
    expect(consoleSpy).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });
});

describe('UserPreferencesPage Form Persistence', () => {
  const mockPreferences = {
    username: 'testuser',
    email: 'test@example.com',
    default_region: '',
    default_industry: '',
    notification_preferences: {
      email_enabled: true,
      tender_match_enabled: false,
      price_alert_enabled: false,
      system_notifications_enabled: true,
      crawl_complete_enabled: false,
    },
    display_settings: {
      theme: 'light',
      language: 'zh',
      items_per_page: 20,
    },
  };

  beforeEach(() => {
    vi.mocked(api.api.getUserPreferences).mockResolvedValue(mockPreferences);
    vi.mocked(api.api.updateUserPreferences).mockResolvedValue(mockPreferences);
  });

  it('should update region when dropdown changes', async () => {
    // Act: Render and change region
    render(<UserPreferencesPage />);
    await waitFor(() => screen.getByLabelText(/默认地区/i));

    const regionSelect = screen.getByLabelText(/默认地区/i);
    await userEvent.selectOptions(regionSelect, '北京市');

    // Assert: Region should be updated
    expect(regionSelect).toHaveValue('北京市');
  });

  it('should update industry when dropdown changes', async () => {
    // Act: Render and change industry
    render(<UserPreferencesPage />);
    await waitFor(() => screen.getByLabelText(/默认行业/i));

    const industrySelect = screen.getByLabelText(/默认行业/i);
    await userEvent.selectOptions(industrySelect, '建筑工程');

    // Assert: Industry should be updated
    expect(industrySelect).toHaveValue('建筑工程');
  });

  it('should save form data when save button is clicked', async () => {
    // Act: Render, change value, and save
    render(<UserPreferencesPage />);
    await waitFor(() => screen.getByLabelText(/默认地区/i));

    const regionSelect = screen.getByLabelText(/默认地区/i);
    await userEvent.selectOptions(regionSelect, '上海市');
    await userEvent.click(screen.getByRole('button', { name: /保存设置/i }));

    // Assert: Should call update API
    await waitFor(() => {
      expect(api.api.updateUserPreferences).toHaveBeenCalled();
    });
  });
});
