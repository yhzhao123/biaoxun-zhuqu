import apiClient from './client';
import {
  Tender,
  ClassificationResult,
  OpportunityScore,
  TrendAnalysis,
  DashboardOverview,
  ClassificationSummary,
  PaginatedResponse,
  TenderFilters,
  ApiResponse,
} from '@/types';

// 招标分类 API
export const classifyTender = async (tender: Partial<Tender>): Promise<ApiResponse<ClassificationResult>> => {
  return apiClient.post('/analytics/classify', tender);
};

// 商机评分 API
export const scoreOpportunity = async (tenderId: string): Promise<ApiResponse<OpportunityScore>> => {
  return apiClient.post('/analytics/score', { tender_id: tenderId });
};

// 趋势分析 API
export const analyzeTrends = async (params: {
  analysis_type?: 'all' | 'time_series' | 'region' | 'industry' | 'amount' | 'tenderer';
  start_date?: string;
  end_date?: string;
}): Promise<ApiResponse<TrendAnalysis>> => {
  return apiClient.post('/analytics/trends', params);
};

// 数据聚合 API
export const aggregateData = async (params: {
  query_type: 'overview' | 'classification' | 'opportunities' | 'trends' | 'dashboard';
  filters?: TenderFilters;
}): Promise<ApiResponse<unknown>> => {
  return apiClient.post('/analytics/aggregate', params);
};

// 获取仪表板概览
export const getDashboardOverview = async (): Promise<ApiResponse<DashboardOverview>> => {
  return aggregateData({ query_type: 'overview' }) as Promise<ApiResponse<DashboardOverview>>;
};

// 获取分类统计
export const getClassificationSummary = async (): Promise<ApiResponse<ClassificationSummary>> => {
  return aggregateData({ query_type: 'classification' }) as Promise<ApiResponse<ClassificationSummary>>;
};

// 获取招标列表
export const getTenderList = async (
  filters?: TenderFilters,
  page = 1,
  pageSize = 20
): Promise<ApiResponse<PaginatedResponse<Tender>>> => {
  return apiClient.post('/analytics/aggregate', {
    query_type: 'opportunities',
    filters,
    page,
    page_size: pageSize,
  });
};

// 获取招标详情
export const getTenderDetail = async (tenderId: string): Promise<ApiResponse<Tender>> => {
  return apiClient.get(`/tenders/${tenderId}`);
};

// 批量分类
export const classifyBatch = async (tenders: Partial<Tender>[]): Promise<ApiResponse<{
  total: number;
  classified: number;
  results: Array<{ tender_id: string; status: string } & ClassificationResult>;
  summary: ClassificationSummary;
}>> => {
  return apiClient.post('/analytics/classify-batch', { tenders });
};

// 获取高价值商机
export const getHighValueOpportunities = async (
  threshold = 80,
  limit = 10
): Promise<ApiResponse<Tender[]>> => {
  return apiClient.post('/analytics/aggregate', {
    query_type: 'opportunities',
    filters: { minScore: threshold },
    limit,
  });
};
