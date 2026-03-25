/**
 * UserPreferencesPage - Phase 9
 * User preferences and settings page
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import type { UserPreferences } from '../types';

export const UserPreferencesPage: React.FC = () => {
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchPreferences();
  }, []);

  const fetchPreferences = async () => {
    try {
      setLoading(true);
      const data = await api.getUserPreferences();
      setPreferences(data);
      setError(null);
    } catch (err) {
      setError('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const handleNotificationChange = async (
    key: keyof UserPreferences['notification_preferences'],
    value: boolean
  ) => {
    if (!preferences) return;

    try {
      const updated = await api.updateNotificationPreferences({
        [key]: value,
      });
      setPreferences(updated);
    } catch (err) {
      console.error('Failed to update notification preference:', err);
    }
  };

  const handleSave = async () => {
    if (!preferences) return;

    try {
      await api.updateUserPreferences(preferences);
      setSuccessMessage('保存成功');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Failed to save preferences:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (error || !preferences) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-red-500">{error || '加载失败'}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/"
          className="text-gray-600 hover:text-gray-900"
        >
          返回
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">用户设置</h1>
      </div>

      {/* Success message */}
      {successMessage && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          {successMessage}
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
              defaultValue={preferences.email}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              readOnly
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">默认地区</label>
            <select
              defaultValue={preferences.default_region || ''}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
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
              defaultValue={preferences.default_industry || ''}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
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
          <div className="flex items-center justify-between">
            <span className="text-gray-900">邮件通知</span>
            <button
              onClick={() => handleNotificationChange('email_enabled', !preferences.notification_preferences.email_enabled)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                preferences.notification_preferences.email_enabled ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  preferences.notification_preferences.email_enabled ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-900">招标匹配</span>
            <button
              onClick={() => handleNotificationChange('tender_match_enabled', !preferences.notification_preferences.tender_match_enabled)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                preferences.notification_preferences.tender_match_enabled ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  preferences.notification_preferences.tender_match_enabled ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-900">价格提醒</span>
            <button
              onClick={() => handleNotificationChange('price_alert_enabled', !preferences.notification_preferences.price_alert_enabled)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                preferences.notification_preferences.price_alert_enabled ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  preferences.notification_preferences.price_alert_enabled ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-900">系统通知</span>
            <button
              onClick={() => handleNotificationChange('system_notifications_enabled', !preferences.notification_preferences.system_notifications_enabled)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                preferences.notification_preferences.system_notifications_enabled ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  preferences.notification_preferences.system_notifications_enabled ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-900">爬取完成</span>
            <button
              onClick={() => handleNotificationChange('crawl_complete_enabled', !preferences.notification_preferences.crawl_complete_enabled)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                preferences.notification_preferences.crawl_complete_enabled ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  preferences.notification_preferences.crawl_complete_enabled ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
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
              defaultValue={preferences.display_settings.theme}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="light">浅色</option>
              <option value="dark">深色</option>
              <option value="auto">自动</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">语言</label>
            <select
              defaultValue={preferences.display_settings.language}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="zh">中文</option>
              <option value="en">English</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">每页条数</label>
            <select
              defaultValue={preferences.display_settings.items_per_page}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
              <option value="100">100</option>
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