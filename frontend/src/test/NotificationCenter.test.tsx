/**
 * NotificationCenter tests - Phase 8
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import { render } from './setup';
import userEvent from '@testing-library/user-event';
import { NotificationCenter } from '../components/NotificationCenter';
import { api } from '../services/api';

// Mock the API
vi.mock('../services/api', () => ({
  api: {
    getNotifications: vi.fn(),
    getUnreadNotificationCount: vi.fn(),
    markNotificationAsRead: vi.fn(),
    markAllNotificationsAsRead: vi.fn(),
    deleteNotification: vi.fn(),
  },
}));

const mockNotifications = [
  {
    id: '1',
    type: 'tender_match' as const,
    title: '新招标匹配',
    message: '有新的招标信息匹配您的关注',
    is_read: false,
    created_at: '2026-03-25T10:00:00Z',
  },
  {
    id: '2',
    type: 'crawl_complete' as const,
    title: '爬取完成',
    message: '已完成招标信息爬取，共 100 条',
    is_read: true,
    created_at: '2026-03-24T15:00:00Z',
  },
  {
    id: '3',
    type: 'system' as const,
    title: '系统通知',
    message: '系统维护通知',
    is_read: false,
    created_at: '2026-03-23T09:00:00Z',
  },
];

describe('NotificationCenter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render loading state initially', () => {
    vi.mocked(api.getNotifications).mockImplementation(
      () => new Promise(() => {}) // Never resolves to keep loading
    );

    render(<NotificationCenter />);
    expect(screen.getByText(/加载中/)).toBeInTheDocument();
  });

  it('should render notifications list', async () => {
    vi.mocked(api.getNotifications).mockResolvedValue({
      count: 3,
      results: mockNotifications,
    });
    vi.mocked(api.getUnreadNotificationCount).mockResolvedValue(2);

    render(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.getByText('新招标匹配')).toBeInTheDocument();
      expect(screen.getByText('爬取完成')).toBeInTheDocument();
    });
  });

  it('should display unread count in header', async () => {
    vi.mocked(api.getNotifications).mockResolvedValue({
      count: 3,
      results: mockNotifications,
    });
    vi.mocked(api.getUnreadNotificationCount).mockResolvedValue(2);

    render(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument(); // Unread count badge
    });
  });

  it('should call markAsRead when clicking unread notification', async () => {
    vi.mocked(api.getNotifications).mockResolvedValue({
      count: 3,
      results: mockNotifications,
    });
    vi.mocked(api.getUnreadNotificationCount).mockResolvedValue(2);
    vi.mocked(api.markNotificationAsRead).mockResolvedValue();

    render(<NotificationCenter />);

    await waitFor(() => {
      const unreadNotification = screen.getByText('新招标匹配').closest('div.px-6');
      if (unreadNotification) {
        fireEvent.click(unreadNotification);
      }
    });

    expect(api.markNotificationAsRead).toHaveBeenCalledWith('1');
  });

  it('should call markAllAsRead when clicking mark all button', async () => {
    vi.mocked(api.getNotifications).mockResolvedValue({
      count: 3,
      results: mockNotifications,
    });
    vi.mocked(api.getUnreadNotificationCount).mockResolvedValue(2);
    vi.mocked(api.markAllNotificationsAsRead).mockResolvedValue();

    render(<NotificationCenter />);

    await waitFor(() => {
      const markAllButton = screen.getByRole('button', { name: /全部标记已读/ });
      fireEvent.click(markAllButton);
    });

    expect(api.markAllNotificationsAsRead).toHaveBeenCalled();
  });

  it('should call deleteNotification when clicking delete button', async () => {
    vi.mocked(api.getNotifications).mockResolvedValue({
      count: 3,
      results: mockNotifications,
    });
    vi.mocked(api.getUnreadNotificationCount).mockResolvedValue(2);
    vi.mocked(api.deleteNotification).mockResolvedValue();

    render(<NotificationCenter />);

    await waitFor(() => {
      const deleteButtons = screen.getAllByRole('button', { name: /删除/ });
      fireEvent.click(deleteButtons[0]);
    });

    expect(api.deleteNotification).toHaveBeenCalledWith('1');
  });

  it('should render empty state when no notifications', async () => {
    vi.mocked(api.getNotifications).mockResolvedValue({
      count: 0,
      results: [],
    });
    vi.mocked(api.getUnreadNotificationCount).mockResolvedValue(0);

    render(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.getByText(/暂无通知/)).toBeInTheDocument();
    });
  });

  it('should render correct icon for different notification types', async () => {
    vi.mocked(api.getNotifications).mockResolvedValue({
      count: 3,
      results: mockNotifications,
    });
    vi.mocked(api.getUnreadNotificationCount).mockResolvedValue(2);

    render(<NotificationCenter />);

    await waitFor(() => {
      // tender_match should have a specific icon (check by title)
      expect(screen.getAllByTitle(/通知/).length).toBeGreaterThan(0);
    });
  });

  it('should format date correctly', async () => {
    vi.mocked(api.getNotifications).mockResolvedValue({
      count: 1,
      results: [mockNotifications[0]],
    });
    vi.mocked(api.getUnreadNotificationCount).mockResolvedValue(1);

    render(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.getByText(/2026年3月25日/)).toBeInTheDocument();
    });
  });

  it('should handle API error gracefully', async () => {
    vi.mocked(api.getNotifications).mockRejectedValue(new Error('Network error'));
    vi.mocked(api.getUnreadNotificationCount).mockResolvedValue(0);

    render(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.getByText(/加载失败/)).toBeInTheDocument();
    });
  });
});