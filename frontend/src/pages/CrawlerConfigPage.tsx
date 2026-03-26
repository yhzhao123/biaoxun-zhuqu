/**
 * CrawlerConfigPage - 爬虫源配置页面
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';

interface CrawlSource {
  id: string;
  name: string;
  base_url: string;
  list_url_pattern: string;
  selector_title: string;
  selector_content: string;
  selector_publish_date: string;
  selector_tenderer: string;
  selector_budget: string;
  delay_seconds: number;
  status: 'active' | 'inactive' | 'maintenance';
  total_crawled: number;
  last_crawl_at: string | null;
}

export const CrawlerConfigPage: React.FC = () => {
  const [sources, setSources] = useState<CrawlSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingSource, setEditingSource] = useState<CrawlSource | null>(null);

  // Form state
  const [formData, setFormData] = useState<Partial<CrawlSource>>({
    name: '',
    base_url: '',
    list_url_pattern: '',
    selector_title: 'h1, .title',
    selector_content: '.content',
    selector_publish_date: '.date',
    selector_tenderer: '.tenderer',
    selector_budget: '.budget',
    delay_seconds: 1,
    status: 'active',
  });

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      setLoading(true);
      const data = await api.getCrawlSources();
      setSources(data);
    } catch (err) {
      setError('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingSource) {
        await api.updateCrawlSource(editingSource.id, formData);
      } else {
        await api.createCrawlSource(formData);
      }
      setShowAddForm(false);
      setEditingSource(null);
      fetchSources();
    } catch (err) {
      setError('保存失败');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这个爬虫源吗？')) return;
    try {
      await api.deleteCrawlSource(id);
      fetchSources();
    } catch (err) {
      setError('删除失败');
    }
  };

  const handleEdit = (source: CrawlSource) => {
    setEditingSource(source);
    setFormData(source);
    setShowAddForm(true);
  };

  const handleTest = async (id: string) => {
    try {
      const result = await api.testCrawlSource(id);
      alert(result.message);
    } catch (err) {
      alert('测试失败');
    }
  };

  const handleStartCrawl = async (source: CrawlSource) => {
    try {
      const result = await api.triggerCrawl(source.id!);
      alert(`爬虫任务已启动！\n任务ID: ${result.task_id}\n爬虫源: ${result.source}\n状态: ${result.status}`);
    } catch (err) {
      alert('启动失败');
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      maintenance: 'bg-yellow-100 text-yellow-800',
    };
    const labels: Record<string, string> = {
      active: '启用',
      inactive: '禁用',
      maintenance: '维护中',
    };
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${styles[status] || styles.inactive}`}>
        {labels[status] || status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-gray-600 hover:text-gray-900">返回</Link>
          <h1 className="text-2xl font-bold text-gray-900">爬虫源配置</h1>
        </div>
        <button
          onClick={() => {
            setEditingSource(null);
            setFormData({
              name: '',
              base_url: '',
              list_url_pattern: '',
              selector_title: 'h1, .title',
              selector_content: '.content',
              selector_publish_date: '.date',
              selector_tenderer: '.tenderer',
              selector_budget: '.budget',
              delay_seconds: 1,
              status: 'active',
            });
            setShowAddForm(true);
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          添加爬虫源
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
          <button onClick={fetchSources} className="ml-2 underline">重试</button>
        </div>
      )}

      {/* Add/Edit Form */}
      {showAddForm && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">
            {editingSource ? '编辑爬虫源' : '添加爬虫源'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">网站名称</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-md"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">基础URL</label>
                <input
                  type="url"
                  value={formData.base_url}
                  onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-md"
                  required
                  placeholder="https://example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">列表页URL模式</label>
                <input
                  type="text"
                  value={formData.list_url_pattern}
                  onChange={(e) => setFormData({ ...formData, list_url_pattern: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-md"
                  placeholder="/list?page={page}"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">请求间隔(秒)</label>
                <input
                  type="number"
                  min={0}
                  max={60}
                  value={formData.delay_seconds}
                  onChange={(e) => setFormData({ ...formData, delay_seconds: parseInt(e.target.value) })}
                  className="mt-1 block w-full px-3 py-2 border rounded-md"
                />
              </div>
            </div>

            <div className="border-t pt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">CSS选择器配置</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs text-gray-600">标题</label>
                  <input
                    type="text"
                    value={formData.selector_title}
                    onChange={(e) => setFormData({ ...formData, selector_title: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border rounded-md text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600">内容</label>
                  <input
                    type="text"
                    value={formData.selector_content}
                    onChange={(e) => setFormData({ ...formData, selector_content: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border rounded-md text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600">发布日期</label>
                  <input
                    type="text"
                    value={formData.selector_publish_date}
                    onChange={(e) => setFormData({ ...formData, selector_publish_date: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border rounded-md text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600">招标人</label>
                  <input
                    type="text"
                    value={formData.selector_tenderer}
                    onChange={(e) => setFormData({ ...formData, selector_tenderer: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border rounded-md text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600">预算</label>
                  <input
                    type="text"
                    value={formData.selector_budget}
                    onChange={(e) => setFormData({ ...formData, selector_budget: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border rounded-md text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600">状态</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                    className="mt-1 block w-full px-3 py-2 border rounded-md text-sm"
                  >
                    <option value="active">启用</option>
                    <option value="inactive">禁用</option>
                    <option value="maintenance">维护中</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="flex gap-2 pt-4">
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                保存
              </button>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                取消
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Sources List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">网站名称</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">URL</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">爬取数</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">加载中...</td>
              </tr>
            ) : sources.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">暂无爬虫源</td>
              </tr>
            ) : (
              sources.map((source) => (
                <tr key={source.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium">{source.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-500 truncate max-w-xs">
                    <a href={source.base_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                      {source.base_url}
                    </a>
                  </td>
                  <td className="px-6 py-4">{getStatusBadge(source.status)}</td>
                  <td className="px-6 py-4 text-sm">{source.total_crawled}</td>
                  <td className="px-6 py-4 text-sm space-x-2">
                    <button
                      onClick={() => handleStartCrawl(source)}
                      className="text-green-600 hover:text-green-900 font-medium"
                    >
                      启动
                    </button>
                    <button
                      onClick={() => handleTest(source.id)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      测试
                    </button>
                    <button
                      onClick={() => handleEdit(source)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      编辑
                    </button>
                    <button
                      onClick={() => handleDelete(source.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CrawlerConfigPage;
