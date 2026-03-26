/**
 * LLMConfigPage - 大模型配置页面
 * 支持Ollama、OpenAI、Claude等多种LLM提供商
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { llmService, type HealthCheckResult, type TestConfigResult } from '../services/llmApi';
import type { LLMConfig } from '../types/llm';

const PROVIDER_OPTIONS = [
  { value: 'ollama', label: 'Ollama (本地)', defaultModel: 'qwen2.5:7b', defaultUrl: 'http://localhost:11434' },
  { value: 'openai', label: 'OpenAI', defaultModel: 'gpt-3.5-turbo', defaultUrl: '' },
  { value: 'claude', label: 'Claude (Anthropic)', defaultModel: 'claude-3-haiku-20240307', defaultUrl: '' },
];

export const LLMConfigPage: React.FC = () => {
  const [configs, setConfigs] = useState<LLMConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingConfig, setEditingConfig] = useState<LLMConfig | null>(null);
  const [testingId, setTestingId] = useState<number | null>(null);
  const [testResult, setTestResult] = useState<TestConfigResult | null>(null);
  const [healthStatus, setHealthStatus] = useState<HealthCheckResult | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);

  const [formData, setFormData] = useState<Partial<LLMConfig>>({
    provider: 'ollama',
    name: '',
    api_key: '',
    api_base_url: 'http://localhost:11434',
    model_name: 'qwen2.5:7b',
    temperature: 0.7,
    max_tokens: 2000,
    is_active: true,
  });

  useEffect(() => {
    fetchConfigs();
    checkHealth();
  }, []);

  const fetchConfigs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await llmService.getConfigs();
      setConfigs(data);
    } catch (err: any) {
      const errorMsg = err.userMessage || err.response?.data?.detail || '加载配置失败';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const checkHealth = async () => {
    try {
      setLoadingHealth(true);
      const result = await llmService.healthCheck();
      setHealthStatus(result);
    } catch (err) {
      console.error('健康检查失败:', err);
    } finally {
      setLoadingHealth(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      if (editingConfig?.id) {
        await llmService.updateConfig(editingConfig.id, formData);
      } else {
        await llmService.createConfig(formData);
      }
      setShowForm(false);
      setEditingConfig(null);
      fetchConfigs();
    } catch (err: any) {
      const errorMsg = err.errorData?.detail ||
                       err.errorData?.message ||
                       err.userMessage ||
                       '保存失败';
      setError(errorMsg);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这个配置吗？')) return;
    try {
      await llmService.deleteConfig(id);
      fetchConfigs();
    } catch (err: any) {
      setError(err.userMessage || '删除失败');
    }
  };

  const handleTest = async (id: number) => {
    setTestingId(id);
    setTestResult(null);

    try {
      const result = await llmService.testConfig(id);
      setTestResult(result);
    } catch (err: any) {
      setTestResult({
        success: false,
        message: err.userMessage || '测试失败',
        provider: '',
        error_type: 'unknown'
      });
    } finally {
      setTestingId(null);
    }
  };

  const handleSetDefault = async (id: number) => {
    try {
      await llmService.setDefaultConfig(id);
      fetchConfigs();
    } catch (err: any) {
      setError(err.userMessage || '设置默认配置失败');
    }
  };

  const handleProviderChange = (provider: string) => {
    const option = PROVIDER_OPTIONS.find(o => o.value === provider);
    if (option) {
      setFormData({
        ...formData,
        provider: provider as 'ollama' | 'openai' | 'claude',
        model_name: option.defaultModel,
        api_base_url: option.defaultUrl,
      });
    }
  };

  const handleEdit = (config: LLMConfig) => {
    setEditingConfig(config);
    setFormData(config);
    setShowForm(true);
  };

  const getProviderLabel = (provider: string) => {
    return PROVIDER_OPTIONS.find(o => o.value === provider)?.label || provider;
  };

  const getStatusColor = (available: boolean, configured?: boolean) => {
    if (available) return 'bg-green-100 text-green-800';
    if (configured === false) return 'bg-gray-100 text-gray-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-gray-600 hover:text-gray-900">返回</Link>
          <h1 className="text-2xl font-bold text-gray-900">大模型配置</h1>
        </div>
        <div className="flex gap-2">
          <button
            onClick={checkHealth}
            disabled={loadingHealth}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            {loadingHealth ? '检测中...' : '检测连接'}
          </button>
          <button
            onClick={() => {
              setEditingConfig(null);
              setFormData({
                provider: 'ollama',
                name: '',
                api_key: '',
                api_base_url: 'http://localhost:11434',
                model_name: 'qwen2.5:7b',
                temperature: 0.7,
                max_tokens: 2000,
                is_active: true,
              });
              setShowForm(true);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            添加配置
          </button>
        </div>
      </div>

      {/* Provider Status Cards */}
      {healthStatus && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Ollama Status */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium">Ollama (本地)</h3>
              <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(healthStatus.providers.ollama.available)}`}>
                {healthStatus.providers.ollama.available ? '可用' : '不可用'}
              </span>
            </div>
            {healthStatus.providers.ollama.available ? (
              <div className="text-sm text-gray-600">
                <p>URL: {healthStatus.providers.ollama.url}</p>
                <p>模型: {healthStatus.providers.ollama.models?.join(', ')}</p>
              </div>
            ) : (
              <div className="text-sm">
                <p className="text-red-600">{healthStatus.providers.ollama.error}</p>
                {healthStatus.providers.ollama.solution && (
                  <p className="text-blue-600 mt-1">建议: {healthStatus.providers.ollama.solution}</p>
                )}
              </div>
            )}
          </div>

          {/* OpenAI Status */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium">OpenAI</h3>
              <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(healthStatus.providers.openai.available, healthStatus.providers.openai.configured)}`}>
                {healthStatus.providers.openai.available ? '可用' : healthStatus.providers.openai.configured ? '配置错误' : '未配置'}
              </span>
            </div>
            <div className="text-sm">
              {healthStatus.providers.openai.error && (
                <p className="text-red-600">{healthStatus.providers.openai.error}</p>
              )}
              {healthStatus.providers.openai.solution && (
                <p className="text-blue-600">建议: {healthStatus.providers.openai.solution}</p>
              )}
            </div>
          </div>

          {/* Claude Status */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium">Claude (Anthropic)</h3>
              <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(healthStatus.providers.claude.available, healthStatus.providers.claude.configured)}`}>
                {healthStatus.providers.claude.available ? '可用' : healthStatus.providers.claude.configured ? '配置错误' : '未配置'}
              </span>
            </div>
            <div className="text-sm">
              {healthStatus.providers.claude.error && (
                <p className="text-red-600">{healthStatus.providers.claude.error}</p>
              )}
              {healthStatus.providers.claude.solution && (
                <p className="text-blue-600">建议: {healthStatus.providers.claude.solution}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Test Result Modal */}
      {testResult && (
        <div className={`rounded-lg p-4 ${testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <div className="flex justify-between items-start">
            <div>
              <h4 className={`font-medium ${testResult.success ? 'text-green-800' : 'text-red-800'}`}>
                {testResult.success ? '测试成功' : '测试失败'}
              </h4>
              <p className={`mt-1 ${testResult.success ? 'text-green-700' : 'text-red-700'}`}>
                {testResult.message}
              </p>
              {testResult.solution && (
                <p className="mt-2 text-sm text-blue-700">
                  建议: {testResult.solution}
                </p>
              )}
            </div>
            <button
              onClick={() => setTestResult(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              关闭
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">关闭</button>
        </div>
      )}

      {/* Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">
            {editingConfig ? '编辑配置' : '添加配置'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">配置名称</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-md"
                  required
                  placeholder="例如：本地Ollama"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">提供商</label>
                <select
                  value={formData.provider}
                  onChange={(e) => handleProviderChange(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border rounded-md"
                >
                  {PROVIDER_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">模型名称</label>
                <input
                  type="text"
                  value={formData.model_name}
                  onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-md"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">API基础URL</label>
                <input
                  type="text"
                  value={formData.api_base_url}
                  onChange={(e) => setFormData({ ...formData, api_base_url: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-md"
                  placeholder={formData.provider === 'ollama' ? 'http://localhost:11434' : '留空使用默认'}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">API密钥</label>
                <input
                  type="password"
                  value={formData.api_key || ''}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border rounded-md"
                  placeholder={formData.provider === 'ollama' ? '本地模型不需要' : '输入API密钥'}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">温度参数</label>
                <input
                  type="number"
                  min={0}
                  max={2}
                  step={0.1}
                  value={formData.temperature}
                  onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                  className="mt-1 block w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">最大Token数</label>
                <input
                  type="number"
                  min={100}
                  max={8000}
                  step={100}
                  value={formData.max_tokens}
                  onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                  className="mt-1 block w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div className="flex items-center">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="rounded"
                  />
                  <span className="text-sm font-medium text-gray-700">启用</span>
                </label>
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
                onClick={() => setShowForm(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                取消
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Configs List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">名称</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">提供商</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">模型</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">加载中...</td>
              </tr>
            ) : configs.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                  暂无配置，请添加一个LLM配置
                </td>
              </tr>
            ) : (
              configs.map((config) => (
                <tr key={config.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="font-medium">{config.name}</div>
                    {config.is_default && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                        默认
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {getProviderLabel(config.provider)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{config.model_name}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2 py-1 text-xs rounded-full ${
                      config.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {config.is_active ? '启用' : '禁用'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm space-x-2">
                    <button
                      onClick={() => config.id && handleTest(config.id)}
                      disabled={testingId === config.id}
                      className="text-green-600 hover:text-green-900 disabled:opacity-50"
                    >
                      {testingId === config.id ? '测试中...' : '测试'}
                    </button>
                    {!config.is_default && (
                      <button
                        onClick={() => config.id && handleSetDefault(config.id)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        设为默认
                      </button>
                    )}
                    <button
                      onClick={() => handleEdit(config)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      编辑
                    </button>
                    <button
                      onClick={() => config.id && handleDelete(config.id)}
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

      {/* Usage Guide */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">使用说明</h3>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li><strong>Ollama:</strong> 本地运行的大模型，无需API密钥。运行 <code className="bg-blue-100 px-1 rounded">ollama serve</code> 启动服务</li>
          <li><strong>OpenAI:</strong> 需要OpenAI API密钥，在服务器设置环境变量 <code className="bg-blue-100 px-1 rounded">OPENAI_API_KEY</code></li>
          <li><strong>Claude:</strong> 需要Anthropic API密钥，在服务器设置环境变量 <code className="bg-blue-100 px-1 rounded">ANTHROPIC_API_KEY</code></li>
          <li>点击"测试"按钮可以验证配置是否正确</li>
          <li>设置"默认配置"后，对话将自动使用该配置</li>
        </ul>
      </div>
    </div>
  );
};

export default LLMConfigPage;