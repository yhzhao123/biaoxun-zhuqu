/**
 * TendererProfile component - Phase 10 Task 054-055
 * Display tenderer profile with statistics and history
 */

import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { Tender } from '../types';

interface TendererStats {
  name: string;
  total_tenders: number;
  total_budget: number;
  active_tenders: number;
  industries: { name: string; count: number }[];
  recent_tenders: Tender[];
}

interface TendererProfileProps {
  tendererName?: string;
}

export const TendererProfile: React.FC<TendererProfileProps> = ({ tendererName }) => {
  const [stats, setStats] = useState<TendererStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tendererName) return;

    const fetchTendererStats = async () => {
      setLoading(true);
      setError(null);
      try {
        // 这里应该调用API获取招标人统计数据
        // 目前使用模拟数据
        const mockStats: TendererStats = {
          name: tendererName,
          total_tenders: 15,
          total_budget: 25000000,
          active_tenders: 3,
          industries: [
            { name: 'IT', count: 8 },
            { name: '建筑', count: 4 },
            { name: '医疗', count: 3 },
          ],
          recent_tenders: [],
        };
        setStats(mockStats);
      } catch (err) {
        setError('加载招标人数据失败');
      } finally {
        setLoading(false);
      }
    };

    fetchTendererStats();
  }, [tendererName]);

  const formatBudget = (budget: number) => {
    if (budget >= 100000000) {
      return `¥${(budget / 100000000).toFixed(1)}亿`;
    } else if (budget >= 10000) {
      return `¥${(budget / 10000).toFixed(0)}万`;
    }
    return `¥${budget}`;
  };

  if (!tendererName) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-gray-500 py-8">
          请选择招标人查看画像
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-red-500 py-8">
          {error || '暂无数据'}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4 mb-4">
        <h2 className="text-xl font-bold text-gray-900">{stats.name}</h2>
        <p className="text-sm text-gray-500 mt-1">招标人画像</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">招标总数</div>
          <div className="text-2xl font-bold text-blue-600">
            {stats.total_tenders}
          </div>
        </div>
        <div className="bg-green-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">总预算</div>
          <div className="text-2xl font-bold text-green-600">
            {formatBudget(stats.total_budget)}
          </div>
        </div>
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">进行中</div>
          <div className="text-2xl font-bold text-purple-600">
            {stats.active_tenders}
          </div>
        </div>
        <div className="bg-orange-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">主要行业</div>
          <div className="text-2xl font-bold text-orange-600">
            {stats.industries[0]?.name || '-'}
          </div>
        </div>
      </div>

      {/* Industry Distribution */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-3">行业分布</h3>
        <div className="space-y-2">
          {stats.industries.map((industry) => (
            <div key={industry.name} className="flex items-center">
              <div className="w-24 text-sm text-gray-600">{industry.name}</div>
              <div className="flex-1 mx-3">
                <div className="h-2 bg-gray-200 rounded-full">
                  <div
                    className="h-2 bg-blue-600 rounded-full"
                    style={{
                      width: `${(industry.count / stats.total_tenders) * 100}%`,
                    }}
                  />
                </div>
              </div>
              <div className="w-12 text-sm text-gray-900 text-right">
                {industry.count}个
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">最近活动</h3>
        {stats.recent_tenders.length > 0 ? (
          <div className="space-y-3">
            {stats.recent_tenders.slice(0, 5).map((tender) => (
              <div
                key={tender.id}
                className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0"
              >
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {tender.title}
                  </div>
                  <div className="text-xs text-gray-500">
                    {tender.publish_date}
                  </div>
                </div>
                <div className="text-sm text-blue-600">
                  {formatBudget(tender.budget || 0)}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-500 text-sm">暂无近期招标记录</div>
        )}
      </div>
    </div>
  );
};

export default TendererProfile;
