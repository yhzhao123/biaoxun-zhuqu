/**
 * TenderDetail component - Phase 4 Task 022-023
 * Display detailed information of a tender
 */

import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { Tender } from '../types';
import { api } from '../services/api';

export const TenderDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [tender, setTender] = useState<Tender | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    const fetchTender = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getTender(id);
        setTender(data);
      } catch (err) {
        setError('加载招标详情失败');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchTender();
  }, [id]);

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

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !tender) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error || '招标不存在'}
        <Link to="/tenders" className="ml-4 text-sm underline">
          返回列表
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/tenders"
          className="text-blue-600 hover:text-blue-800 text-sm mb-2 inline-block"
        >
          ← 返回列表
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">{tender.title}</h1>
        <div className="mt-2">
          <span
            className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${
              getStatusColor(tender.status)
            }`}
          >
            {getStatusText(tender.status)}
          </span>
        </div>
      </div>

      {/* Detail grid */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">基本信息</h2>
        </div>
        <div className="px-6 py-4">
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <dt className="text-sm font-medium text-gray-500">公告编号</dt>
              <dd className="mt-1 text-sm text-gray-900">{tender.notice_id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">招标人</dt>
              <dd className="mt-1 text-sm text-gray-900">{tender.tenderer}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">预算</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {formatBudget(tender.budget, tender.currency)}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">地区</dt>
              <dd className="mt-1 text-sm text-gray-900">{tender.region || '-'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">行业</dt>
              <dd className="mt-1 text-sm text-gray-900">{tender.industry || '-'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">来源</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {tender.source_site || '-'}
                {tender.source_url && (
                  <a
                    href={tender.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-2 text-blue-600 hover:text-blue-800 text-xs"
                  >
                    查看来源 →
                  </a>
                )}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">发布日期</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {formatDate(tender.publish_date)}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">截止日期</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {formatDate(tender.deadline_date)}
              </dd>
            </div>
          </dl>
        </div>

        {/* Description */}
        {tender.description && (
          <>
            <div className="px-6 py-4 border-t border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">描述</h2>
            </div>
            <div className="px-6 py-4">
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {tender.description}
              </p>
            </div>
          </>
        )}

        {/* Metadata */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="text-xs text-gray-500">
            创建时间: {formatDate(tender.created_at)} | 更新时间: {formatDate(tender.updated_at)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TenderDetail;
