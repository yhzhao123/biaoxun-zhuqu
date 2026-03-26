/**
 * LLM API Service - 大模型API服务
 */
import axios from 'axios';
import type { AxiosResponse } from 'axios';
import type {
  LLMConfig,
  ChatConversation,
  ChatRequest,
  ChatResponse,
  TenderAnalysisRequest,
  TenderAnalysisResponse
} from '../types/llm';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface HealthCheckResult {
  status: string;
  providers: {
    ollama: {
      available: boolean;
      models?: string[];
      url?: string;
      error?: string;
      solution?: string;
    };
    openai: {
      available: boolean;
      configured: boolean;
      error?: string;
      solution?: string;
    };
    claude: {
      available: boolean;
      configured: boolean;
      error?: string;
      solution?: string;
    };
  };
  recommendations: Array<{
    provider: string;
    action: string;
    command?: string;
    env_var?: string;
  }>;
}

export interface TestConfigResult {
  success: boolean;
  message: string;
  provider: string;
  model?: string;
  details?: Record<string, unknown>;
  error_type?: string;
  solution?: string;
  status_code?: number;
}

class LLMService {
  private client = axios.create({
    baseURL: `${API_BASE_URL}/llm`,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  constructor() {
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

    // Response interceptor for better error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // Enhance error object with useful information
        if (error.response) {
          error.userMessage = error.response.data?.message ||
                              error.response.data?.detail ||
                              `请求失败 (${error.response.status})`;
          error.errorData = error.response.data;
        } else if (error.request) {
          error.userMessage = '无法连接到服务器，请检查网络连接';
        } else {
          error.userMessage = error.message || '未知错误';
        }
        return Promise.reject(error);
      }
    );
  }

  // Health Check API (no auth required)
  async healthCheck(): Promise<HealthCheckResult> {
    const response: AxiosResponse<HealthCheckResult> = await this.client.get('/configs/health/');
    return response.data;
  }

  // LLM Config API
  async getConfigs(): Promise<LLMConfig[]> {
    const response = await this.client.get('/configs/');
    // 处理分页响应或直接数组
    if (response.data && typeof response.data === 'object' && 'results' in response.data) {
      return response.data.results;
    }
    return response.data;
  }

  async getConfig(id: number): Promise<LLMConfig> {
    const response: AxiosResponse<LLMConfig> = await this.client.get(`/configs/${id}/`);
    return response.data;
  }

  async createConfig(config: Partial<LLMConfig>): Promise<LLMConfig> {
    const response: AxiosResponse<LLMConfig> = await this.client.post('/configs/', config);
    return response.data;
  }

  async updateConfig(id: number, config: Partial<LLMConfig>): Promise<LLMConfig> {
    const response: AxiosResponse<LLMConfig> = await this.client.put(`/configs/${id}/`, config);
    return response.data;
  }

  async deleteConfig(id: number): Promise<void> {
    await this.client.delete(`/configs/${id}/`);
  }

  async testConfig(id: number): Promise<TestConfigResult> {
    const response = await this.client.post(`/configs/${id}/test/`);
    return response.data;
  }

  async setDefaultConfig(id: number): Promise<{ success: boolean }> {
    const response = await this.client.post(`/configs/${id}/activate/`);
    return response.data;
  }

  async getDefaultConfig(): Promise<LLMConfig | null> {
    try {
      const response: AxiosResponse<LLMConfig> = await this.client.get('/configs/default/');
      return response.data;
    } catch {
      return null;
    }
  }

  // Chat API
  async getConversations(): Promise<ChatConversation[]> {
    const response: AxiosResponse<ChatConversation[]> = await this.client.get('/chat/');
    return response.data;
  }

  async createConversation(title?: string, tenderId?: string): Promise<ChatConversation> {
    const response: AxiosResponse<ChatConversation> = await this.client.post('/chat/', {
      title: title || '新对话',
      tender_id: tenderId
    });
    return response.data;
  }

  async getConversation(id: number): Promise<ChatConversation> {
    const response: AxiosResponse<ChatConversation> = await this.client.get(`/chat/${id}/`);
    return response.data;
  }

  async deleteConversation(id: number): Promise<void> {
    await this.client.delete(`/chat/${id}/`);
  }

  async sendMessage(conversationId: number, message: string): Promise<ChatResponse> {
    const response: AxiosResponse<ChatResponse> = await this.client.post(
      `/chat/${conversationId}/send/`,
      { message }
    );
    return response.data;
  }

  async analyzeTender(data: TenderAnalysisRequest): Promise<TenderAnalysisResponse> {
    const response: AxiosResponse<TenderAnalysisResponse> = await this.client.post(
      '/chat/analyze-tender/',
      data
    );
    return response.data;
  }
}

export const llmService = new LLMService();
export default llmService;
