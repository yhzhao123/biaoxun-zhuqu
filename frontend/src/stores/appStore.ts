import { create } from 'zustand';
import { Tender, TenderFilters, RealtimeMessage } from '@/types';

interface AppState {
  // 全局状态
  isLoading: boolean;
  error: string | null;
  
  // 当前招标
  selectedTender: Tender | null;
  setSelectedTender: (tender: Tender | null) => void;
  
  // 筛选条件
  filters: TenderFilters;
  setFilters: (filters: Partial<TenderFilters>) => void;
  resetFilters: () => void;
  
  // 实时消息
  messages: RealtimeMessage[];
  addMessage: (message: RealtimeMessage) => void;
  markMessageAsRead: (id: string) => void;
  clearMessages: () => void;
  unreadCount: () => number;
  
  // 加载状态
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

const initialFilters: TenderFilters = {
  region: undefined,
  industry: undefined,
  status: undefined,
  minAmount: undefined,
  maxAmount: undefined,
  startDate: undefined,
  endDate: undefined,
  keyword: undefined,
};

export const useAppStore = create<AppState>((set, get) => ({
  isLoading: false,
  error: null,
  selectedTender: null,
  filters: initialFilters,
  messages: [],
  
  setSelectedTender: (tender) => set({ selectedTender: tender }),
  
  setFilters: (newFilters) => set((state) => ({
    filters: { ...state.filters, ...newFilters },
  })),
  
  resetFilters: () => set({ filters: initialFilters }),
  
  addMessage: (message) => set((state) => ({
    messages: [message, ...state.messages],
  })),
  
  markMessageAsRead: (id) => set((state) => ({
    messages: state.messages.map((msg) =>
      msg.id === id ? { ...msg, read: true } : msg
    ),
  })),
  
  clearMessages: () => set({ messages: [] }),
  
  unreadCount: () => {
    return get().messages.filter((msg) => !msg.read).length;
  },
  
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));
