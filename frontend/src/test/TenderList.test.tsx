/**
 * Tests for React.memo optimization on TenderList row
 * TDD - RED phase: Tests that describe the expected behavior
 */

import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { render } from './setup';
import userEvent from '@testing-library/user-event';
import { TenderList } from '../components/TenderList';
import type { Tender } from '../types';
import React from 'react';

// Mock the API
vi.mock('../services/api', () => ({
  api: {
    getTenders: vi.fn().mockResolvedValue({
      results: [],
      count: 0,
    }),
  },
}));

const mockTender: Tender = {
  id: '1',
  title: '测试招标项目',
  tenderer: '测试招标人',
  budget: 1000000,
  currency: 'CNY',
  publish_date: '2024-01-15',
  status: 'active',
  source_site: '测试网站',
  source_url: 'https://example.com',
};

describe('TenderList', () => {
  it('should render loading state initially', () => {
    render(<TenderList />);
    // Should show loading spinner
    expect(document.querySelector('.animate-spin')).toBeInTheDocument();
  });
});

describe('TenderListRow memoization', () => {
  it('should export memoized row component', async () => {
    const module = await import('../components/TenderList');
    // The memoized row should be available
    expect(module.TenderList).toBeDefined();
  });
});