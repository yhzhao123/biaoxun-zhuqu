/**
 * API service - Phase 4 Task 019
 * Backend communication layer
 */

import axios from 'axios';
import type { AxiosInstance, AxiosResponse } from 'axios';
import type { Tender, TenderListResponse, TenderFilter, CrawlTask, Statistics } from '../types';

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
          config.headers.Authorization = `Bearer ${token}`;
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

  async triggerCrawl(source: string): Promise<{ task_id: number; status: string }> {
    const response = await this.client.post('/crawler/trigger/', { source });
    return response.data;
  }

  // Statistics API
  async getStatistics(): Promise<Statistics> {
    const response: AxiosResponse<Statistics> = await this.client.get('/statistics/');
    return response.data;
  }

  async getTrendData(days = 30): Promise<{ date: string; count: number }[]> {
    const response = await this.client.get('/statistics/trend/', { params: { days } });
    return response.data;
  }
}

export const api = new ApiService();
export default api;
