/**
 * TenderList component - Phase 4 Task 020-021
 * Display paginated list of tender notices
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import type { Tender, TenderFilter } from '../types';
import { api } from '../services/api';

interface TenderListProps {
  filter?: TenderFilter;
}

export const TenderList: React.FC<TenderListProps> = ({ filter }) => {
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  const fetchTenders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getTenders(filter, page, pageSize);
      setTenders(response.results);
      setTotalCount(response.count);
    } catch (err) {
      setError('加载招标列表失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [filter, page]);

  useEffect(() => {
    fetchTenders();
  }, [fetchTenders]);

  const totalPages = Math.ceil(totalCount / pageSize);

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('zh-CN');
  };

  const formatBudget = (budget?: number, currency?: string) => {
    if (!budget) return '-';
    const symbol = currency === 'CNY' ? '¥' : currency === 'USD' ? '$' : '€';
    return `${symbol}${budget.toLocaleString()}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'closed':
        return 'bg-gray-100 text-gray-800';
      case 'expired':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      active: '进行中',
      pending: '待处理',
      closed: '已关闭',
      expired: '已过期',
    };
    return statusMap[status] || status;
  };

  if (loading && tenders.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error}
        <button
          onClick={fetchTenders}
          className="ml-4 text-sm underline hover:no-underline"
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Results count */}
      <div className="text-sm text-gray-600">
        共 {totalCount} 条招标信息
      </div>

      {/* Tender list */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                标题
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                招标人
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                预算
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                发布日期
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                状态
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                来源
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {tenders.map((tender) => (
              <tr key={tender.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <Link
                    to={`/tenders/${tender.id}`}
                    className="text-blue-600 hover:text-blue-900 font-medium"
                  >
                    {tender.title}
                  </Link>
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">
                  {tender.tenderer}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">
                  {formatBudget(tender.budget, tender.currency)}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {formatDate(tender.publish_date)}
                </td>
                <td className="px-6 py-4">
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      getStatusColor(tender.status)
                    }`}
                  >
                    {getStatusText(tender.status)}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm">
                  {tender.source_url ? (
                    <a
                      href={tender.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-900 flex items-center gap-1"
                      title={tender.source_site || '查看原文'}
                    >
                      <span className="truncate max-w-[150px]">{tender.source_site || '查看原文'}</span>
                      <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  ) : (
                    <span className="text-gray-500">{tender.source_site || '-'}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2 mt-6">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 border rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            上一页
          </button>
          <span className="text-sm text-gray-600">
            第 {page} / {totalPages} 页
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 border rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
};

export default TenderList;
