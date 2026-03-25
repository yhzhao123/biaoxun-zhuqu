/**
 * TendererProfilePage - Phase 5
 * Tenderer detail page with clustering information
 */

import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../services/api';
import type { Tenderer } from '../types';
import { TenderList } from '../components/TenderList';

export const TendererProfilePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [tenderer, setTenderer] = useState<Tenderer | null>(null);
  const [clusterTenderers, setClusterTenderers] = useState<Tenderer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchTenderer(id);
    }
  }, [id]);

  const fetchTenderer = async (tendererId: string) => {
    try {
      setLoading(true);
      const data = await api.getTenderer(tendererId);
      setTenderer(data);

      // Fetch cluster if available
      if (data.cluster_id) {
        const clusterData = await api.getTendererCluster(data.cluster_id);
        setClusterTenderers(clusterData.filter((t) => t.id !== tendererId));
      }

      setError(null);
    } catch (err) {
      setError('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const formatBudget = (budget: number): string => {
    if (budget >= 1000000) {
      return `¥${(budget / 1000000).toFixed(1)}M`;
    }
    if (budget >= 1000) {
      return `¥${(budget / 1000).toFixed(1)}K`;
    }
    return `¥${budget}`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (error || !tenderer) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-red-500">{error || '招标人不存在'}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/tenders"
          className="text-gray-600 hover:text-gray-900"
        >
          返回
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">{tenderer.name}</h1>
        {tenderer.cluster_id && (
          <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
            Cluster #{tenderer.cluster_id}
          </span>
        )}
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500">招标总数</div>
          <div className="mt-2 text-3xl font-bold text-gray-900">
            {tenderer.total_tenders}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500">进行中</div>
          <div className="mt-2 text-3xl font-bold text-green-600">
            {tenderer.active_tenders}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500">总预算</div>
          <div className="mt-2 text-3xl font-bold text-blue-600">
            {formatBudget(tenderer.total_budget)}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500">行业数</div>
          <div className="mt-2 text-3xl font-bold text-purple-600">
            {tenderer.industries.length}
          </div>
        </div>
      </div>

      {/* Cluster information */}
      {clusterTenderers.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">
              同Cluster ({clusterTenderers.length})
            </h2>
          </div>
          <div className="px-6 py-4">
            <div className="flex flex-wrap gap-2">
              {clusterTenderers.map((t) => (
                <Link
                  key={t.id}
                  to={`/tenderers/${t.id}`}
                  className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 text-sm"
                >
                  {t.name}
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Industries */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">行业分布</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {tenderer.industries.map((industry) => (
              <div key={industry.name} className="px-6 py-3 flex justify-between items-center">
                <span className="text-gray-900">{industry.name}</span>
                <span className="text-gray-600">{industry.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Regions */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">地区分布</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {tenderer.regions.map((region) => (
              <div key={region.name} className="px-6 py-3 flex justify-between items-center">
                <span className="text-gray-900">{region.name}</span>
                <span className="text-gray-600">{region.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent tenders */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">最近招标</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {tenderer.recent_tenders.length > 0 ? (
            tenderer.recent_tenders.map((tender) => (
              <div key={tender.id} className="px-6 py-4">
                <Link
                  to={`/tenders/${tender.id}`}
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  {tender.title}
                </Link>
                <div className="text-sm text-gray-500 mt-1">
                  {tender.notice_id} • {tender.budget ? formatBudget(tender.budget) : '金额未知'}
                </div>
              </div>
            ))
          ) : (
            <div className="px-6 py-4 text-gray-500">暂无招标</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TendererProfilePage;