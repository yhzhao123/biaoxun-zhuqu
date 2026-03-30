import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { ErrorBoundary } from './components/ErrorBoundary';
import MainLayout from './components/layout/MainLayout';

// Phase 5 - Analytics Dashboard (New)
const Dashboard = lazy(() => import('./pages/dashboard'));
const TenderList = lazy(() => import('./pages/tenders'));
const TenderDetail = lazy(() => import('./pages/tenders/detail'));
const Opportunity = lazy(() => import('./pages/opportunity'));
const Trends = lazy(() => import('./pages/trends'));
const Classification = lazy(() => import('./pages/classification'));
const Realtime = lazy(() => import('./pages/realtime'));
const Settings = lazy(() => import('./pages/settings'));

// Phase 4 - Legacy Pages (Keep for compatibility)
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const TendersPage = lazy(() => import('./pages/TendersPage'));
const TendererProfilePage = lazy(() => import('./pages/TendererProfilePage'));
const UserPreferencesPage = lazy(() => import('./pages/UserPreferencesPage'));
const CrawlerConfigPage = lazy(() => import('./pages/CrawlerConfigPage'));
const LLMConfigPage = lazy(() => import('./pages/LLMConfigPage'));
const AnalysisChatPage = lazy(() => import('./pages/AnalysisChatPage'));

const PageLoader: React.FC = () => (
  <div className="flex justify-center items-center h-64">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
  </div>
);

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: '#1890ff' } }}>
      <ErrorBoundary>
        <BrowserRouter>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              {/* Phase 5 - New UI with Layout */}
              <Route path="/" element={<MainLayout />}>
                <Route index element={<Dashboard />} />
                <Route path="tenders" element={<TenderList />} />
                <Route path="tenders/:id" element={<TenderDetail />} />
                <Route path="opportunity" element={<Opportunity />} />
                <Route path="trends" element={<Trends />} />
                <Route path="classification" element={<Classification />} />
                <Route path="realtime" element={<Realtime />} />
                <Route path="settings" element={<Settings />} />
              </Route>

              {/* Phase 4 - Legacy routes (redirect or keep) */}
              <Route path="/legacy" element={<DashboardPage />} />
              <Route path="/legacy/tenders" element={<TendersPage />} />
              <Route path="/legacy/tenderers/:id" element={<TendererProfilePage />} />
              <Route path="/legacy/preferences" element={<UserPreferencesPage />} />
              <Route path="/legacy/crawler" element={<CrawlerConfigPage />} />
              <Route path="/legacy/llm" element={<LLMConfigPage />} />
              <Route path="/legacy/chat" element={<AnalysisChatPage />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </ErrorBoundary>
    </ConfigProvider>
  );
};

export default App;
