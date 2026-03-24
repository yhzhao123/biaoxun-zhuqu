/**
 * DashboardPage - Phase 4
 * Overview dashboard with statistics
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import type { Statistics, CrawlTask } from '../types';
import { api } from '../services/api';

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<Statistics | null>(null);
  const [tasks, setTasks] = useState<CrawlTask[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsData, tasksData] = await Promise.all([
          api.getStatistics(),
          api.getCrawlTasks(),
        ]);
        setStats(statsData);
        setTasks(tasksData.slice(0, 5)); // Last 5 tasks
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">仪表盘</h1>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500">招标总数</div>
            <div className="mt-2 text-3xl font-bold text-gray-900">
              {stats.total_tenders.toLocaleString()}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500">进行中</div>
            <div className="mt-2 text-3xl font-bold text-green-600">
              {stats.active_tenders.toLocaleString()}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500">总预算</div>
            <div className="mt-2 text-3xl font-bold text-blue-600">
              ¥{(stats.total_budget / 1000000).toFixed(1)}M
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500">地区数</div>
            <div className="mt-2 text-3xl font-bold text-purple-600">
              {new Set(stats.by_region.map((r) => r.region)).size}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent tasks */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-medium text-gray-900">最近爬取任务</h2>
            <Link to="/crawler" className="text-sm text-blue-600 hover:text-blue-800">
              查看全部
            </Link>
          </div>
          <div className="divide-y divide-gray-200">
            {tasks.map((task) => (
              <div key={task.id} className="px-6 py-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{task.name}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {task.source_site} • {new Date(task.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      getStatusColor(task.status)
                    }`}
                  >
                    {task.status === 'completed' ? '已完成' : task.status === 'running' ? '进行中' : task.status === 'failed' ? '失败' : '待处理'}
                  </span>
                </div>
                {task.items_crawled > 0 && (
                  <div className="mt-2 text-xs text-gray-500">
                    已爬取: {task.items_crawled} 条
                  </div>
                )}
              </div>
            ))}
            {tasks.length === 0 && (
              <div className="px-6 py-4 text-sm text-gray-500">暂无任务</div>
            )}
          </div>
        </div>

        {/* Quick actions */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">快捷操作</h2>
          </div>
          <div className="p-6 space-y-4">
            <Link
              to="/tenders"
              className="block w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-center"
            >
              浏览全部招标
            </Link>
            <button
              onClick={() => api.triggerCrawl('default')}
              className="block w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              立即启动爬虫
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
