/**
 * App component - Phase 4
 * Main application with routing and lazy loading
 */

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { ErrorBoundary } from './components/ErrorBoundary';

// Lazy load all page components for better performance
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const TendersPage = lazy(() => import('./pages/TendersPage'));
const TenderDetail = lazy(() => import('./components/TenderDetail'));
const TendererProfilePage = lazy(() => import('./pages/TendererProfilePage'));
const UserPreferencesPage = lazy(() => import('./pages/UserPreferencesPage'));
const CrawlerConfigPage = lazy(() => import('./pages/CrawlerConfigPage'));
const NotificationCenter = lazy(() => import('./components/NotificationCenter'));
const LLMConfigPage = lazy(() => import('./pages/LLMConfigPage'));
const AnalysisChatPage = lazy(() => import('./pages/AnalysisChatPage'));

// Loading fallback component
const PageLoader: React.FC = () => (
  <div className="flex justify-center items-center h-64">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
  </div>
);

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-100">
          {/* Navigation */}
          <nav className="bg-white shadow-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex">
                  <Link to="/" className="flex items-center">
                    <span className="text-xl font-bold text-blue-600">BiaoXun</span>
                  </Link>
                  <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                    <Link
                      to="/"
                      className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900"
                    >
                      仪表盘
                    </Link>
                    <Link
                      to="/tenders"
                      className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 hover:text-gray-900"
                    >
                      招标列表
                    </Link>
                    <Link
                      to="/analysis-chat"
                      className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 hover:text-gray-900"
                    >
                      AI分析
                    </Link>
                    <Link
                      to="/llm-config"
                      className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 hover:text-gray-900"
                    >
                      大模型配置
                    </Link>
                    <Link
                      to="/settings"
                      className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 hover:text-gray-900"
                    >
                      设置
                    </Link>
                    <Link
                      to="/crawler"
                      className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-500 hover:text-gray-900"
                    >
                      爬虫配置
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </nav>

          {/* Main content */}
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/tenders" element={<TendersPage />} />
                <Route path="/tenders/:id" element={<TenderDetail />} />
                <Route path="/tenderers/:id" element={<TendererProfilePage />} />
                <Route path="/settings" element={<UserPreferencesPage />} />
                <Route path="/crawler" element={<CrawlerConfigPage />} />
                <Route path="/notifications" element={<NotificationCenter />} />
                <Route path="/llm-config" element={<LLMConfigPage />} />
                <Route path="/analysis-chat" element={<AnalysisChatPage />} />
              </Routes>
            </Suspense>
          </main>

          {/* Footer */}
          <footer className="bg-white border-t border-gray-200 mt-12">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
              <p className="text-center text-sm text-gray-500">
                标讯 - 招标信息平台 © 2026
              </p>
            </div>
          </footer>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
};

export default App;
