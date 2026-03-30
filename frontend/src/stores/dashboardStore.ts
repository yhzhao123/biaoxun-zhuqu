import { create } from 'zustand';
import { DashboardOverview, TrendAnalysis, Tender } from '@/types';

interface DashboardState {
  overview: DashboardOverview | null;
  trends: TrendAnalysis | null;
  highValueTenders: Tender[];
  isLoading: boolean;
  
  setOverview: (overview: DashboardOverview) => void;
  setTrends: (trends: TrendAnalysis) => void;
  setHighValueTenders: (tenders: Tender[]) => void;
  setLoading: (loading: boolean) => void;
  
  // 统计数据更新
  updateStats: (updates: Partial<DashboardOverview>) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  overview: null,
  trends: null,
  highValueTenders: [],
  isLoading: false,
  
  setOverview: (overview) => set({ overview }),
  setTrends: (trends) => set({ trends }),
  setHighValueTenders: (tenders) => set({ highValueTenders: tenders }),
  setLoading: (loading) => set({ isLoading: loading }),
  
  updateStats: (updates) => set((state) => ({
    overview: state.overview ? { ...state.overview, ...updates } : null,
  })),
}));
