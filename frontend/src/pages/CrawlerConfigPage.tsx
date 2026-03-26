/**
 * CrawlerConfigPage - 爬虫源配置页面
 * 支持多种数据提取模式：HTML解析、API调用、智能提取、LLM提取
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';

interface CrawlSource {
  id: string;
  name: string;
  base_url: string;
  list_url_pattern: string;
  // 数据提取模式
  extraction_mode: 'html' | 'api' | 'intelligent' | 'llm' | 'auto';
  // CSS选择器配置
  selector_title: string;
  selector_content: string;
  selector_publish_date: string;
  selector_tenderer: string;
  selector_budget: string;
  // API配置
  api_url: string;
  api_method: 'GET' | 'POST';
  api_params: Record<string, any>;
  api_headers: Record<string, string>;
  api_response_path: string;
  // API字段映射
  api_field_title: string;
  api_field_url: string;
  api_field_date: string;
  api_field_budget: string;
  api_field_tenderer: string;
  // 分页配置
  page_param_name: string;
  page_start: number;
  max_pages: number;
  // 列表页配置
  list_container_selector: string;
  list_item_selector: string;
  list_link_selector: string;
  // 其他配置
  delay_seconds: number;
  status: 'active' | 'inactive' | 'maintenance';
  total_crawled: number;
  last_crawl_at: string | null;
}

const EXTRACTION_MODE_OPTIONS = [
  { value: 'auto', label: '自动选择（推荐）', description: '依次尝试智能提取、LLM、HTML解析' },
  { value: 'html', label: 'HTML解析', description: '使用CSS选择器解析HTML页面' },
  { value: 'api', label: 'API调用', description: '直接调用外部API获取JSON数据' },
  { value: 'intelligent', label: '智能提取', description: '自动分析页面结构提取数据' },
  { value: 'llm', label: 'LLM提取', description: '使用大模型解析内容' },
];

const getDefaultFormData = (): Partial<CrawlSource> => ({
  name: '',
  base_url: '',
  list_url_pattern: '',
  extraction_mode: 'auto',
  selector_title: 'h1, .title',
  selector_content: '.content',
  selector_publish_date: '.date',
  selector_tenderer: '.tenderer',
  selector_budget: '.budget',
  api_url: '',
  api_method: 'POST',
  api_params: {},
  api_headers: { 'Content-Type': 'application/json' },
  api_response_path: '',
  api_field_title: 'title',
  api_field_url: 'url',
  api_field_date: 'time',
  api_field_budget: 'budget',
  api_field_tenderer: 'tenderer',
  page_param_name: 'page',
  page_start: 1,
  max_pages: 10,
  list_container_selector: '',
  list_item_selector: '',
  list_link_selector: '',
  delay_seconds: 1,
  status: 'active',
});

export const CrawlerConfigPage: React.FC = () => {
  const [sources, setSources] = useState<CrawlSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingSource, setEditingSource] = useState<CrawlSource | null>(null);

  // Form state
  const [formData, setFormData] = useState<Partial<CrawlSource>>(getDefaultFormData());

  // Active tab in form
  const [activeTab, setActiveTab] = useState<'basic' | 'html' | 'api'>('basic');

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
            setFormData(getDefaultFormData());
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
            {/* Tabs */}
            <div className="border-b border-gray-200">
              <nav className="flex space-x-4">
                {['basic', 'html', 'api'].map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setActiveTab(tab as any)}
                    className={`px-4 py-2 text-sm font-medium border-b-2 ${
                      activeTab === tab
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {tab === 'basic' ? '基础配置' : tab === 'html' ? 'HTML解析' : 'API配置'}
                  </button>
                ))}
              </nav>
            </div>

            {/* Basic Tab */}
            {activeTab === 'basic' && (
              <div className="space-y-4">
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
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">数据提取模式</label>
                  <select
                    value={formData.extraction_mode}
                    onChange={(e) => setFormData({ ...formData, extraction_mode: e.target.value as any })}
                    className="mt-1 block w-full px-3 py-2 border rounded-md"
                  >
                    {EXTRACTION_MODE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-gray-500">
                    {EXTRACTION_MODE_OPTIONS.find(o => o.value === formData.extraction_mode)?.description}
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-4">
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
                  <div>
                    <label className="block text-sm font-medium text-gray-700">最大爬取页数</label>
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={formData.max_pages}
                      onChange={(e) => setFormData({ ...formData, max_pages: parseInt(e.target.value) })}
                      className="mt-1 block w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">状态</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                    className="mt-1 block w-full px-3 py-2 border rounded-md"
                  >
                    <option value="active">启用</option>
                    <option value="inactive">禁用</option>
                    <option value="maintenance">维护中</option>
                  </select>
                </div>
              </div>
            )}

            {/* HTML Tab */}
            {activeTab === 'html' && (
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-gray-700">列表页选择器</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs text-gray-600">列表容器</label>
                    <input
                      type="text"
                      value={formData.list_container_selector}
                      onChange={(e) => setFormData({ ...formData, list_container_selector: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border rounded-md text-sm"
                      placeholder=".list-container"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600">列表项</label>
                    <input
                      type="text"
                      value={formData.list_item_selector}
                      onChange={(e) => setFormData({ ...formData, list_item_selector: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border rounded-md text-sm"
                      placeholder=".list-item"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600">详情链接</label>
                    <input
                      type="text"
                      value={formData.list_link_selector}
                      onChange={(e) => setFormData({ ...formData, list_link_selector: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border rounded-md text-sm"
                      placeholder="a.title"
                    />
                  </div>
                </div>

                <h3 className="text-sm font-medium text-gray-700 pt-4">详情页选择器</h3>
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
                </div>
              </div>
            )}

            {/* API Tab */}
            {activeTab === 'api' && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">API端点URL</label>
                    <input
                      type="text"
                      value={formData.api_url}
                      onChange={(e) => setFormData({ ...formData, api_url: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border rounded-md"
                      placeholder="https://api.example.com/search"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">请求方法</label>
                    <select
                      value={formData.api_method}
                      onChange={(e) => setFormData({ ...formData, api_method: e.target.value as any })}
                      className="mt-1 block w-full px-3 py-2 border rounded-md"
                    >
                      <option value="POST">POST</option>
                      <option value="GET">GET</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">响应数据路径</label>
                  <input
                    type="text"
                    value={formData.api_response_path}
                    onChange={(e) => setFormData({ ...formData, api_response_path: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border rounded-md"
                    placeholder="data.list 或 data.middle.listAndBox"
                  />
                  <p className="mt-1 text-xs text-gray-500">使用点号分隔的JSON路径</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">分页参数名</label>
                    <input
                      type="text"
                      value={formData.page_param_name}
                      onChange={(e) => setFormData({ ...formData, page_param_name: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">起始页码</label>
                    <input
                      type="number"
                      min={0}
                      value={formData.page_start}
                      onChange={(e) => setFormData({ ...formData, page_start: parseInt(e.target.value) })}
                      className="mt-1 block w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                </div>

                <h3 className="text-sm font-medium text-gray-700 pt-4">字段映射（JSON路径）</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs text-gray-600">标题字段</label>
                    <input
                      type="text"
                      value={formData.api_field_title}
                      onChange={(e) => setFormData({ ...formData, api_field_title: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border rounded-md text-sm"
                      placeholder="title"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600">URL字段</label>
                    <input
                      type="text"
                      value={formData.api_field_url}
                      onChange={(e) => setFormData({ ...formData, api_field_url: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border rounded-md text-sm"
                      placeholder="url"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600">日期字段</label>
                    <input
                      type="text"
                      value={formData.api_field_date}
                      onChange={(e) => setFormData({ ...formData, api_field_date: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border rounded-md text-sm"
                      placeholder="time"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600">预算字段</label>
                    <input
                      type="text"
                      value={formData.api_field_budget}
                      onChange={(e) => setFormData({ ...formData, api_field_budget: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border rounded-md text-sm"
                      placeholder="budget"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600">招标人字段</label>
                    <input
                      type="text"
                      value={formData.api_field_tenderer}
                      onChange={(e) => setFormData({ ...formData, api_field_tenderer: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border rounded-md text-sm"
                      placeholder="tenderer"
                    />
                  </div>
                </div>
              </div>
            )}

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
