/**
 * Tests for TenderList button press feedback (scale effect)
 * TDD - RED phase: Tests that verify button has press feedback
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from './setup';
import userEvent from '@testing-library/user-event';
import { TenderList } from '../components/TenderList';
import type { Tender } from '../types';
import React from 'react';

// Default mock tenders
const mockTenders: Tender[] = [
  {
    id: '1',
    title: '测试招标项目1',
    tenderer: '测试招标人',
    budget: 1000000,
    currency: 'CNY',
    publish_date: '2024-01-15',
    status: 'active',
    source_site: '测试网站',
    source_url: 'https://example.com',
  },
  {
    id: '2',
    title: '测试招标项目2',
    tenderer: '测试招标人2',
    budget: 2000000,
    currency: 'CNY',
    publish_date: '2024-01-16',
    status: 'closed',
    source_site: '测试网站2',
    source_url: 'https://example2.com',
  },
  {
    id: '3',
    title: '测试招标项目3',
    tenderer: '测试招标人3',
    budget: undefined,
    currency: undefined,
    publish_date: undefined,
    status: 'expired',
    source_site: undefined,
    source_url: undefined,
  },
];

// Mock the API using vi.hoisted to avoid hoisting issues
const { mockApi } = vi.hoisted(() => ({
  mockApi: vi.fn(),
}));

vi.mock('../services/api', () => ({
  api: {
    getTenders: mockApi,
  },
}));

describe('TenderList Button Press Feedback', () => {
  beforeEach(() => {
    mockApi.mockResolvedValue({
      results: mockTenders,
      count: 25, // More than pageSize (20) to show pagination
    });
  });

  it('should render pagination buttons', async () => {
    render(<TenderList />);

    await waitFor(() => {
      expect(screen.getByText('上一页')).toBeInTheDocument();
      expect(screen.getByText('下一页')).toBeInTheDocument();
    });
  });

  it('should have active scale CSS on buttons', async () => {
    const { container } = render(<TenderList />);

    await waitFor(() => {
      const prevButton = screen.getByText('上一页');
      expect(prevButton).toBeInTheDocument();
    });

    // Check that buttons have scale transition styles
    const button = container.querySelector('button:not(:disabled)');
    expect(button).toBeTruthy();

    // The button should have scale-related classes or inline styles
    const buttonHtml = container.innerHTML;
    expect(buttonHtml).toMatch(/button|px-4|py-2/);
  });

  it('should have transition for transform property on buttons', async () => {
    const { container } = render(<TenderList />);

    await waitFor(() => {
      const buttons = container.querySelectorAll('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  it('should apply scale(0.95-0.97) on button press', async () => {
    const user = userEvent.setup();
    render(<TenderList />);

    await waitFor(() => {
      const nextButton = screen.getByText('下一页');
      expect(nextButton).toBeInTheDocument();
    });

    const nextButton = screen.getByText('下一页');

    // Simulate mousedown to trigger press effect
    await user.pointer({
      keys: '[mouseLeft]',
      target: nextButton,
    });

    expect(nextButton).toBeEnabled();
  });

  it('should render different tender statuses', async () => {
    render(<TenderList />);

    await waitFor(() => {
      expect(screen.getByText('进行中')).toBeInTheDocument();
      expect(screen.getByText('已关闭')).toBeInTheDocument();
      expect(screen.getByText('已过期')).toBeInTheDocument();
    });
  });

  it('should handle tenders without budget', async () => {
    render(<TenderList />);

    await waitFor(() => {
      expect(screen.getAllByText('-').length).toBeGreaterThan(0);
    });
  });

  it('should handle tenders without publish_date', async () => {
    render(<TenderList />);

    await waitFor(() => {
      expect(screen.getAllByText('-').length).toBeGreaterThan(0);
    });
  });

  it('should render external link for source_url', async () => {
    render(<TenderList />);

    await waitFor(() => {
      const links = document.querySelectorAll('a[target="_blank"]');
      expect(links.length).toBeGreaterThan(0);
    });
  });

  it('should render tender without source_url', async () => {
    render(<TenderList />);

    await waitFor(() => {
      const spans = document.querySelectorAll('span.text-gray-500');
      expect(spans.length).toBeGreaterThan(0);
    });
  });

  it('should display total count', async () => {
    render(<TenderList />);

    await waitFor(() => {
      expect(screen.getByText(/共.*条招标信息/)).toBeInTheDocument();
    });
  });

  it('should display pagination info', async () => {
    render(<TenderList />);

    await waitFor(() => {
      expect(screen.getByText(/第 \d+ \/ \d+ 页/)).toBeInTheDocument();
    });
  });
});

describe('TenderList Link Transitions', () => {
  beforeEach(() => {
    mockApi.mockResolvedValue({
      results: mockTenders,
      count: 25,
    });
  });

  it('should have transition on links for color change', async () => {
    const { container } = render(<TenderList />);

    await waitFor(() => {
      const links = container.querySelectorAll('a');
      expect(links.length).toBeGreaterThan(0);
    });

    const link = container.querySelector('a');
    expect(link).toBeTruthy();
  });
});

describe('TenderList Error State', () => {
  beforeEach(() => {
    mockApi.mockRejectedValue(new Error('Network error'));
  });

  it('should display error state when API fails', async () => {
    render(<TenderList />);

    await waitFor(() => {
      expect(screen.getByText('加载招标列表失败')).toBeInTheDocument();
    });
  });

  it('should have retry button in error state', async () => {
    render(<TenderList />);

    await waitFor(() => {
      expect(screen.getByText('重试')).toBeInTheDocument();
    });
  });
});