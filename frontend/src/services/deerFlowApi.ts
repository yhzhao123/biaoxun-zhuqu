/**
 * deer-flow Gateway API client
 * TDD Cycle 18 - Phase 2: GREEN - Minimum implementation
 */

import axios, { type AxiosInstance, type AxiosResponse } from 'axios';

// Gateway base URL
const GATEWAY_BASE_URL = import.meta.env.VITE_DEER_FLOW_GATEWAY_URL || 'http://localhost:8001';

// Type definitions

export interface GatewayHealthResponse {
  status: string;
  service: string;
}

export interface ModelInfo {
  name: string;
  model: string;
  display_name?: string;
  description?: string;
  supports_thinking: boolean;
  supports_reasoning_effort: boolean;
}

export interface ModelsListResponse {
  models: ModelInfo[];
}

export interface SkillInfo {
  name: string;
  description: string;
  license?: string;
  category: string;
  enabled: boolean;
}

export interface SkillsListResponse {
  skills: SkillInfo[];
}

export interface SkillUpdateRequest {
  enabled: boolean;
}

export interface SkillInstallRequest {
  thread_id: string;
  path: string;
}

export interface SkillInstallResponse {
  success: boolean;
  skill_name: string;
  message: string;
}

export interface McpOAuthConfig {
  enabled: boolean;
  token_url?: string;
  grant_type?: 'client_credentials' | 'refresh_token';
  client_id?: string;
  client_secret?: string;
  refresh_token?: string;
  scope?: string;
  audience?: string;
  token_field?: string;
  token_type_field?: string;
  expires_in_field?: string;
  default_token_type?: string;
  refresh_skew_seconds?: number;
  extra_token_params?: Record<string, string>;
}

export interface McpServerConfig {
  enabled: boolean;
  type: 'stdio' | 'sse' | 'http';
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  url?: string | null;
  headers?: Record<string, string>;
  oauth?: McpOAuthConfig | null;
  description?: string;
}

export interface McpConfigResponse {
  mcp_servers: Record<string, McpServerConfig>;
}

export interface ThreadRunConfig {
  configurable?: {
    model_name?: string;
    thinking_enabled?: boolean;
    is_plan_mode?: boolean;
    subagent_enabled?: boolean;
  };
}

export interface ThreadRunRequest {
  message: string;
  config?: ThreadRunConfig;
}

export interface ThreadRunResponse {
  thread_id: string;
  run_id: string;
}

// API Client class

class DeerFlowApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: GATEWAY_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('deer-flow Gateway API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<GatewayHealthResponse> {
    const response: AxiosResponse<GatewayHealthResponse> = await this.client.get('/health');
    return response.data;
  }

  /**
   * Get list of all available models
   */
  async getModels(): Promise<ModelInfo[]> {
    const response: AxiosResponse<ModelsListResponse> = await this.client.get('/api/models');
    return response.data.models;
  }

  /**
   * Get model details by name
   */
  async getModel(modelName: string): Promise<ModelInfo> {
    const response: AxiosResponse<ModelInfo> = await this.client.get(`/api/models/${modelName}`);
    return response.data;
  }

  /**
   * Get MCP configuration
   */
  async getMcpConfig(): Promise<Record<string, McpServerConfig>> {
    const response: AxiosResponse<McpConfigResponse> = await this.client.get('/api/mcp/config');
    return response.data.mcp_servers;
  }

  /**
   * Update MCP configuration
   */
  async updateMcpConfig(mcpServers: Record<string, McpServerConfig>): Promise<Record<string, McpServerConfig>> {
    const response: AxiosResponse<McpConfigResponse> = await this.client.put('/api/mcp/config', { mcp_servers: mcpServers });
    return response.data.mcp_servers;
  }

  /**
   * Get list of all skills
   */
  async getSkills(): Promise<SkillInfo[]> {
    const response: AxiosResponse<SkillsListResponse> = await this.client.get('/api/skills');
    return response.data.skills;
  }

  /**
   * Get skill details by name
   */
  async getSkill(skillName: string): Promise<SkillInfo> {
    const response: AxiosResponse<SkillInfo> = await this.client.get(`/api/skills/${skillName}`);
    return response.data;
  }

  /**
   * Update skill enabled status
   */
  async updateSkill(skillName: string, enabled: boolean): Promise<SkillInfo> {
    const response: AxiosResponse<SkillInfo> = await this.client.put(`/api/skills/${skillName}`, { enabled });
    return response.data;
  }

  /**
   * Install skill from .skill archive
   */
  async installSkill(threadId: string, path: string): Promise<SkillInstallResponse> {
    const response: AxiosResponse<SkillInstallResponse> = await this.client.post('/api/skills/install', {
      thread_id: threadId,
      path: path,
    });
    return response.data;
  }

  /**
   * Run agent in a thread
   * Note: This is a placeholder - actual LangGraph run goes through the LangGraph SDK
   */
  async runThread(threadId: string, request: ThreadRunRequest): Promise<ThreadRunResponse> {
    const response: AxiosResponse<ThreadRunResponse> = await this.client.post(`/api/threads/${threadId}/runs`, request);
    return response.data;
  }
}

// Export singleton instance
export const deerFlowApi = new DeerFlowApiService();

export default deerFlowApi;