/**
 * API service - Phase 4 Task 019
 * Backend communication layer
 */

import axios from 'axios';
import type { AxiosInstance, AxiosResponse } from 'axios';
import type { Tender, TenderListResponse, TenderFilter, CrawlTask, Statistics, Tenderer, Notification, UserPreferences } from '../types';

export interface TrendData {
  date: string;
  count: number;
  budget?: number;
}

export interface DistributionData {
  name: string;
  value: number;
}

export interface TendererStats {
  name: string;
  total_tenders: number;
  total_budget: number;
  active_tenders: number;
  industries: { name: string; count: number }[];
  recent_tenders: Tender[];
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          // Django REST Framework TokenAuthentication expects "Token <token>" format
          config.headers.Authorization = `Token ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  // Tenders API
  async getTenders(filter?: TenderFilter, page = 1, pageSize = 20): Promise<TenderListResponse> {
    const params = { ...filter, page, page_size: pageSize };
    const response: AxiosResponse<TenderListResponse> = await this.client.get('/tenders/', { params });
    return response.data;
  }

  async getTender(id: string): Promise<Tender> {
    const response: AxiosResponse<Tender> = await this.client.get(`/tenders/${id}/`);
    return response.data;
  }

  async searchTenders(query: string, filter?: TenderFilter): Promise<TenderListResponse> {
    const params = { search: query, ...filter };
    const response: AxiosResponse<TenderListResponse> = await this.client.get('/tenders/search/', { params });
    return response.data;
  }

  // Crawler API
  async getCrawlTasks(): Promise<CrawlTask[]> {
    const response: AxiosResponse<CrawlTask[]> = await this.client.get('/crawler/tasks/');
    return response.data;
  }

  async triggerCrawl(sourceId: number): Promise<{ task_id: number; status: string; source: string }> {
    const response = await this.client.post('/crawler/trigger/', { source_id: sourceId });
    return response.data;
  }

  // Statistics API
  async getStatistics(): Promise<Statistics> {
    const response: AxiosResponse<Statistics> = await this.client.get('/statistics/');
    return response.data;
  }

  async getTrendData(days = 30): Promise<TrendData[]> {
    const response = await this.client.get('/statistics/trend/', { params: { days } });
    return response.data;
  }

  async getRegionDistribution(): Promise<DistributionData[]> {
    const response = await this.client.get('/statistics/regions/');
    return response.data;
  }

  async getIndustryDistribution(): Promise<DistributionData[]> {
    const response = await this.client.get('/statistics/industries/');
    return response.data;
  }

  // Export API (Task 056-057)
  async exportTenders(format: 'excel' | 'csv' | 'pdf', filter?: TenderFilter): Promise<Blob> {
    const params = { format, ...filter };
    const response = await this.client.get('/tenders/export/', {
      params,
      responseType: 'blob',
    });
    return response.data;
  }

  async downloadExport(blob: Blob, filename: string): Promise<void> {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  // Tenderer API (Phase 5)
  async getTenderer(id: string): Promise<Tenderer> {
    const response: AxiosResponse<Tenderer> = await this.client.get(`/tenderers/${id}/`);
    return response.data;
  }

  async searchTenderers(query: string): Promise<Tenderer[]> {
    const response: AxiosResponse<Tenderer[]> = await this.client.get('/tenderers/search/', {
      params: { search: query },
    });
    return response.data;
  }

  async getTendererCluster(id: number): Promise<Tenderer[]> {
    const response: AxiosResponse<Tenderer[]> = await this.client.get(`/tenderers/clusters/${id}/`);
    return response.data;
  }

  // Notification API (Phase 8)
  async getNotifications(page = 1, pageSize = 20): Promise<{ count: number; results: Notification[] }> {
    const response = await this.client.get('/notifications/', { params: { page, page_size: pageSize } });
    return response.data;
  }

  async getUnreadNotificationCount(): Promise<number> {
    const response = await this.client.get('/notifications/unread-count/');
    return response.data.count;
  }

  async markNotificationAsRead(id: string): Promise<void> {
    await this.client.patch(`/notifications/${id}/read/`);
  }

  async markAllNotificationsAsRead(): Promise<void> {
    await this.client.post('/notifications/mark-all-read/');
  }

  async deleteNotification(id: string): Promise<void> {
    await this.client.delete(`/notifications/${id}/`);
  }

  // User Preferences API (Phase 9)
  async getUserPreferences(): Promise<UserPreferences> {
    const response: AxiosResponse<UserPreferences> = await this.client.get('/users/preferences/');
    return response.data;
  }

  async updateUserPreferences(preferences: Partial<UserPreferences>): Promise<UserPreferences> {
    const response: AxiosResponse<UserPreferences> = await this.client.patch('/users/preferences/', preferences);
    return response.data;
  }

  async updateNotificationPreferences(preferences: Partial<UserPreferences['notification_preferences']>): Promise<UserPreferences> {
    const response: AxiosResponse<UserPreferences> = await this.client.patch(
      '/users/preferences/notifications/',
      preferences
    );
    return response.data;
  }

  // Crawler Sources API
  async getCrawlSources(): Promise<any[]> {
    const response = await this.client.get('/crawler/sources/');
    return response.data.results || response.data;
  }

  async createCrawlSource(data: Partial<any>): Promise<any> {
    const response = await this.client.post('/crawler/sources/', data);
    return response.data;
  }

  async updateCrawlSource(id: string, data: Partial<any>): Promise<any> {
    const response = await this.client.patch(`/crawler/sources/${id}/`, data);
    return response.data;
  }

  async deleteCrawlSource(id: string): Promise<void> {
    await this.client.delete(`/crawler/sources/${id}/`);
  }

  async testCrawlSource(id: string): Promise<any> {
    const response = await this.client.post(`/crawler/sources/${id}/test/`);
    return response.data;
  }

  // Tenderer Analysis API
  async analyzeTenderer(tenderer: string, days = 365): Promise<any> {
    const response = await this.client.get('/analysis/tenderers/analyze/', {
      params: { tenderer, days }
    });
    return response.data;
  }

  async getTendererList(): Promise<any[]> {
    const response = await this.client.get('/analysis/tenderers/list_tenderers/');
    return response.data;
  }
}

export const api = new ApiService();
export default api;
