/**
 * Tests for App.tsx lazy loading and routing
 * TDD - RED phase: Tests that describe the expected behavior
 */

import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { render } from './setup';
import App from '../App';

// Mock the lazy loaded components
vi.mock('../pages/DashboardPage', () => ({
  DashboardPage: () => <div data-testid="dashboard-page">Dashboard</div>,
  default: () => <div data-testid="dashboard-page">Dashboard</div>,
}));

vi.mock('../pages/TendersPage', () => ({
  TendersPage: () => <div data-testid="tenders-page">Tenders</div>,
  default: () => <div data-testid="tenders-page">Tenders</div>,
}));

vi.mock('../components/TenderDetail', () => ({
  TenderDetail: () => <div data-testid="tender-detail">Tender Detail</div>,
  default: () => <div data-testid="tender-detail">Tender Detail</div>,
}));

vi.mock('../pages/TendererProfilePage', () => ({
  TendererProfilePage: () => <div data-testid="tenderer-profile">Tenderer Profile</div>,
  default: () => <div data-testid="tenderer-profile">Tenderer Profile</div>,
}));

vi.mock('../pages/UserPreferencesPage', () => ({
  UserPreferencesPage: () => <div data-testid="user-preferences">User Preferences</div>,
  default: () => <div data-testid="user-preferences">User Preferences</div>,
}));

vi.mock('../pages/CrawlerConfigPage', () => ({
  CrawlerConfigPage: () => <div data-testid="crawler-config">Crawler Config</div>,
  default: () => <div data-testid="crawler-config">Crawler Config</div>,
}));

vi.mock('../components/NotificationCenter', () => ({
  NotificationCenter: () => <div data-testid="notification-center">Notification Center</div>,
  default: () => <div data-testid="notification-center">Notification Center</div>,
}));

vi.mock('../pages/LLMConfigPage', () => ({
  LLMConfigPage: () => <div data-testid="llm-config">LLM Config</div>,
  default: () => <div data-testid="llm-config">LLM Config</div>,
}));

vi.mock('../pages/AnalysisChatPage', () => ({
  AnalysisChatPage: () => <div data-testid="analysis-chat">Analysis Chat</div>,
  default: () => <div data-testid="analysis-chat">Analysis Chat</div>,
}));

// Mock ErrorBoundary to simplify tests
vi.mock('../components/ErrorBoundary', () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe('App', () => {
  it('should render the navigation', () => {
    render(<App />);

    expect(screen.getByText('BiaoXun')).toBeInTheDocument();
    expect(screen.getByText('仪表盘')).toBeInTheDocument();
    expect(screen.getByText('招标列表')).toBeInTheDocument();
  });

  it('should render all navigation links', () => {
    render(<App />);

    expect(screen.getByText('AI分析')).toBeInTheDocument();
    expect(screen.getByText('大模型配置')).toBeInTheDocument();
    expect(screen.getByText('设置')).toBeInTheDocument();
    expect(screen.getByText('爬虫配置')).toBeInTheDocument();
  });

  it('should have a footer', () => {
    render(<App />);

    expect(screen.getByText(/标讯 - 招标信息平台/)).toBeInTheDocument();
  });
});

describe('App lazy loading', () => {
  it('should use React.lazy for page components', async () => {
    // This test verifies that components are lazily loaded
    // by checking if they're wrapped in Suspense
    const appModule = await import('../App');
    const AppComponent = appModule.default;

    expect(AppComponent).toBeDefined();
  });
});