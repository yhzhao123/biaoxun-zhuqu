/**
 * NotificationCenter - Phase 8
 * Notification center component
 */

import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { Notification } from '../types';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';

dayjs.locale('zh-cn');

export const NotificationCenter: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    fetchNotifications();
    fetchUnreadCount();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const data = await api.getNotifications();
      setNotifications(data.results);
      setError(null);
    } catch (err) {
      setError('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const count = await api.getUnreadNotificationCount();
      setUnreadCount(count);
    } catch (err) {
      // Silently fail - unread count is not critical
      setUnreadCount(0);
    }
  };

  const handleMarkAsRead = async (id: string) => {
    try {
      await api.markNotificationAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      setError('标记已读失败');
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await api.markAllNotificationsAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      setError('标记全部已读失败');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteNotification(id);
      const deleted = notifications.find((n) => n.id === id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      if (deleted && !deleted.is_read) {
        setUnreadCount((prev) => Math.max(0, prev - 1));
      }
    } catch (err) {
      setError('删除通知失败');
    }
  };

  const getNotificationIcon = (type: Notification['type']) => {
    switch (type) {
      case 'tender_match':
        return '📋';
      case 'price_alert':
        return '💰';
      case 'crawl_complete':
        return '✅';
      case 'system':
        return '🔔';
      default:
        return '🔔';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-32">
          <div className="text-gray-500">加载中...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-32">
          <div className="text-red-500">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-medium text-gray-900">通知中心</h2>
          {unreadCount > 0 && (
            <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
              {unreadCount}
            </span>
          )}
        </div>
        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllAsRead}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            全部标记已读
          </button>
        )}
      </div>

      {/* Notification List */}
      <div className="divide-y divide-gray-200">
        {notifications.length === 0 ? (
          <div className="px-6 py-8 text-center text-gray-500">暂无通知</div>
        ) : (
          notifications.map((notification) => (
            <div
              key={notification.id}
              className={`px-6 py-4 hover:bg-gray-50 ${
                !notification.is_read ? 'bg-blue-50' : ''
              }`}
              onClick={() => !notification.is_read && handleMarkAsRead(notification.id)}
            >
              <div className="flex items-start gap-3">
                <span className="text-xl" title="通知">
                  {getNotificationIcon(notification.type)}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-gray-900">
                      {notification.title}
                    </p>
                    <span className="text-xs text-gray-500">
                      {dayjs(notification.created_at).format('YYYY年M月D日 HH:mm')}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(notification.id);
                  }}
                  className="text-gray-400 hover:text-red-500"
                >
                  删除
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default NotificationCenter;