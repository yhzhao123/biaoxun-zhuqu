/**
 * UserPreferencesPage - Phase 9 (Fixed)
 * User preferences and settings page with error handling and form persistence
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import type { UserPreferences } from '../types';

// Default preferences for fallback
const DEFAULT_PREFERENCES: UserPreferences = {
  id: 'default',
  username: '用户',
  email: '',
  default_region: '',
  default_industry: '',
  notification_preferences: {
    email_enabled: true,
    tender_match_enabled: false,
    price_alert_enabled: false,
    system_notifications_enabled: true,
    crawl_complete_enabled: false,
  },
  display_settings: {
    theme: 'light',
    language: 'zh',
    items_per_page: 20,
  },
};

export const UserPreferencesPage: React.FC = () => {
  const [preferences, setPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [hasFetched, setHasFetched] = useState(false);

  // Form state for persistence
  const [formData, setFormData] = useState({
    default_region: '',
    default_industry: '',
    theme: 'light',
    language: 'zh',
    items_per_page: 20,
  });

  useEffect(() => {
    fetchPreferences();
  }, []);

  const fetchPreferences = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getUserPreferences();
      if (data) {
        setPreferences(data);
        // Initialize form data
        setFormData({
          default_region: data.default_region || '',
          default_industry: data.default_industry || '',
          theme: data.display_settings?.theme || 'light',
          language: data.display_settings?.language || 'zh',
          items_per_page: data.display_settings?.items_per_page || 20,
        });
      }
      setHasFetched(true);
    } catch (err) {
      setError('加载失败，请检查网络连接');
      // Keep default preferences
      setPreferences(DEFAULT_PREFERENCES);
      setHasFetched(true);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleRetry = () => {
    fetchPreferences();
  };

  const handleNotificationChange = async (
    key: keyof UserPreferences['notification_preferences'],
    value: boolean
  ) => {
    const updated = {
      ...preferences,
      notification_preferences: {
        ...preferences.notification_preferences,
        [key]: value,
      },
    };
    setPreferences(updated);

    try {
      await api.updateNotificationPreferences({
        [key]: value,
      });
    } catch (err) {
      // Silent fail - state is already updated locally
      setError('保存失败，请稍后重试');
    }
  };

  const handleFormChange = (field: string, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    const updated: UserPreferences = {
      ...preferences,
      default_region: formData.default_region,
      default_industry: formData.default_industry,
      display_settings: {
        ...preferences.display_settings,
        theme: formData.theme,
        language: formData.language,
        items_per_page: formData.items_per_page,
      },
    };

    try {
      await api.updateUserPreferences(updated);
      setPreferences(updated);
      setSuccessMessage('保存成功');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError('保存失败，请稍后重试');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-500">加载中...</span>
      </div>
    );
  }

  if (error && !hasFetched) {
    return (
      <div className="flex flex-col justify-center items-center h-64 space-y-4">
        <div className="text-red-500 text-lg">{error}</div>
        <button
          onClick={handleRetry}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/" className="text-gray-600 hover:text-gray-900">返回</Link>
        <h1 className="text-2xl font-bold text-gray-900">用户设置</h1>
      </div>

      {/* Success message */}
      {successMessage && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          {successMessage}
        </div>
      )}

      {/* Error message with retry */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded flex justify-between items-center">
          <span>{error}</span>
          <button onClick={handleRetry} className="text-red-700 hover:text-red-900 underline">
            重试
          </button>
        </div>
      )}

      {/* Basic info */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">基本信息</h2>
        </div>
        <div className="px-6 py-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">用户名</label>
            <div className="mt-1 text-gray-900">{preferences.username}</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">邮箱</label>
            <input
              type="email"
              value={preferences.email}
              readOnly
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">默认地区</label>
            <select
              value={formData.default_region}
              onChange={(e) => handleFormChange('default_region', e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">请选择</option>
              <option value="北京市">北京市</option>
              <option value="上海市">上海市</option>
              <option value="广东省">广东省</option>
              <option value="浙江省">浙江省</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">默认行业</label>
            <select
              value={formData.default_industry}
              onChange={(e) => handleFormChange('default_industry', e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">请选择</option>
              <option value="建筑工程">建筑工程</option>
              <option value="软件开发">软件开发</option>
              <option value="设备采购">设备采购</option>
              <option value="服务咨询">服务咨询</option>
            </select>
          </div>
        </div>
      </div>

      {/* Notification preferences */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">通知偏好</h2>
        </div>
        <div className="px-6 py-4 space-y-4">
          {Object.entries(preferences.notification_preferences).map(([key, value]) => {
            const labels: Record<string, string> = {
              email_enabled: '邮件通知',
              tender_match_enabled: '招标匹配',
              price_alert_enabled: '价格提醒',
              system_notifications_enabled: '系统通知',
              crawl_complete_enabled: '爬取完成',
            };
            return (
              <div key={key} className="flex items-center justify-between">
                <span className="text-gray-900">{labels[key] || key}</span>
                <button
                  onClick={() => handleNotificationChange(key as keyof UserPreferences['notification_preferences'], !value)}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                    value ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow transition duration-200 ${
                      value ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Display settings */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">显示设置</h2>
        </div>
        <div className="px-6 py-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">主题</label>
            <select
              value={formData.theme}
              onChange={(e) => handleFormChange('theme', e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="light">浅色</option>
              <option value="dark">深色</option>
              <option value="auto">自动</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">语言</label>
            <select
              value={formData.language}
              onChange={(e) => handleFormChange('language', e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="zh">中文</option>
              <option value="en">English</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">每页条数</label>
            <select
              value={formData.items_per_page}
              onChange={(e) => handleFormChange('items_per_page', parseInt(e.target.value))}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>
      </div>

      {/* Save button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          保存设置
        </button>
      </div>
    </div>
  );
};

export default UserPreferencesPage;
