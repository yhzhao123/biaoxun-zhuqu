/**
 * LLM Types - 大模型相关类型定义
 */

export interface LLMConfig {
  id?: number;
  provider: 'ollama' | 'openai' | 'claude';
  name: string;
  api_key?: string;
  api_base_url?: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
  is_default: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  metadata?: {
    extracted_entities?: Record<string, unknown>;
    provider?: string;
    model?: string;
  };
}

export interface ChatConversation {
  id?: number;
  title: string;
  messages: ChatMessage[];
  tender_id?: string;
  llm_config?: number;
  created_at?: string;
  updated_at?: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: number;
  tender_id?: string;
  llm_config_id?: number;
}

export interface ChatResponse {
  message: string;
  conversation_id: number;
  extracted_entities?: Record<string, unknown>;
}

export interface TenderAnalysisRequest {
  content: string;
  question?: string;
  tender_id?: string;
}

export interface TenderAnalysisResponse {
  analysis: string;
  entities: {
    tenderer?: string;
    budget?: string;
    region?: string;
    industry?: string;
    deadline?: string;
  };
  suggestions: string[];
}
