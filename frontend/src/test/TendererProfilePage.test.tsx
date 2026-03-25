/**
 * TendererProfilePage tests - Phase 5
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { TendererProfilePage } from '../pages/TendererProfilePage';
import type { Tenderer } from '../types';

// Create mock functions at module level
const mockGetTenderer = vi.fn();
const mockGetTendererCluster = vi.fn();

// Mock api module
vi.mock('../services/api', () => ({
  api: {
    getTenderer: (...args: unknown[]) => mockGetTenderer(...args),
    getTendererCluster: (...args: unknown[]) => mockGetTendererCluster(...args),
  },
}));

const mockTenderer: Tenderer = {
  id: '1',
  name: '测试招标人',
  normalized_name: '测试招标人',
  cluster_id: 1,
  total_tenders: 50,
  total_budget: 10000000,
  active_tenders: 10,
  industries: [
    { name: '建筑工程', count: 30 },
    { name: '软件开发', count: 20 },
  ],
  regions: [
    { name: '北京市', count: 25 },
    { name: '上海市', count: 25 },
  ],
  recent_tenders: [
    {
      id: 't1',
      notice_id: 'NC001',
      title: '测试招标1',
      tenderer: '测试招标人',
      budget: 100000,
      currency: 'CNY',
      status: 'active' as const,
      created_at: '2026-03-25T10:00:00Z',
      updated_at: '2026-03-25T10:00:00Z',
    },
  ],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-03-25T00:00:00Z',
};

const mockClusterTenderers: Tenderer[] = [
  { id: '1', name: '测试招标人', normalized_name: '测试招标人', cluster_id: 1, total_tenders: 10, total_budget: 1000000, active_tenders: 5, industries: [], regions: [], recent_tenders: [], created_at: '', updated_at: '' },
  { id: '2', name: '测试招标人分公司', normalized_name: '测试招标人分公司', cluster_id: 1, total_tenders: 5, total_budget: 500000, active_tenders: 2, industries: [], regions: [], recent_tenders: [], created_at: '', updated_at: '' },
];

describe('TendererProfilePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderWithRouter = (ui: React.ReactElement) => {
    return render(
      <MemoryRouter initialEntries={['/tenderers/1']}>
        <Routes>
          <Route path="/tenderers/:id" element={ui} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('should render loading state initially', () => {
    mockGetTenderer.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderWithRouter(<TendererProfilePage />);
    expect(screen.getByText(/加载中/)).toBeInTheDocument();
  });

  it('should render tenderer profile data', async () => {
    mockGetTenderer.mockResolvedValue(mockTenderer);
    mockGetTendererCluster.mockResolvedValue([]);

    renderWithRouter(<TendererProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('测试招标人')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument(); // total_tenders
      expect(screen.getByText('¥10.0M')).toBeInTheDocument(); // total_budget
    });
  });

  it('should display industries breakdown', async () => {
    mockGetTenderer.mockResolvedValue(mockTenderer);
    mockGetTendererCluster.mockResolvedValue([]);

    renderWithRouter(<TendererProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('建筑工程')).toBeInTheDocument();
      expect(screen.getByText('30')).toBeInTheDocument();
    });
  });

  it('should display regions breakdown', async () => {
    mockGetTenderer.mockResolvedValue(mockTenderer);
    mockGetTendererCluster.mockResolvedValue([]);

    renderWithRouter(<TendererProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('北京市')).toBeInTheDocument();
      expect(screen.getByText('上海市')).toBeInTheDocument();
    });
  });

  it('should render recent tenders list', async () => {
    mockGetTenderer.mockResolvedValue(mockTenderer);
    mockGetTendererCluster.mockResolvedValue([]);

    renderWithRouter(<TendererProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('测试招标1')).toBeInTheDocument();
    });
  });

  it('should display cluster information', async () => {
    mockGetTenderer.mockResolvedValue(mockTenderer);
    mockGetTendererCluster.mockResolvedValue(mockClusterTenderers);

    renderWithRouter(<TendererProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/同Cluster/)).toBeInTheDocument();
    });
  });

  it('should handle API error gracefully', async () => {
    mockGetTenderer.mockRejectedValue(new Error('Network error'));

    renderWithRouter(<TendererProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/加载失败/)).toBeInTheDocument();
    });
  });

  it('should format budget correctly', async () => {
    mockGetTenderer.mockResolvedValue(mockTenderer);
    mockGetTendererCluster.mockResolvedValue([]);

    renderWithRouter(<TendererProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('¥10.0M')).toBeInTheDocument();
    });
  });

  it('should display active tenders count', async () => {
    mockGetTenderer.mockResolvedValue(mockTenderer);
    mockGetTendererCluster.mockResolvedValue([]);

    renderWithRouter(<TendererProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument(); // active_tenders
    });
  });

  it('should show back button', async () => {
    mockGetTenderer.mockResolvedValue(mockTenderer);
    mockGetTendererCluster.mockResolvedValue([]);

    renderWithRouter(<TendererProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/返回/)).toBeInTheDocument();
    });
  });
});