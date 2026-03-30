// 招标信息数据类型
export interface Tender {
  id: string;
  title: string;
  tenderer: string;
  region: string;
  industry: string;
  amount: number;
  publishDate: string;
  deadlineDate: string;
  status: 'pending' | 'bidding' | 'closed';
  classification?: ClassificationResult;
  opportunityScore?: OpportunityScore;
}

// 分类结果
export interface ClassificationResult {
  tendererCategory: Category;
  regionCategory: Category;
  industryCategory: Category;
  amountCategory: Category;
}

export interface Category {
  normalized: string;
  type?: string;
  zone?: string;
  code?: string;
  range?: string;
  level?: string;
  confidence?: number;
}

// 商机评分
export interface OpportunityScore {
  totalScore: number;
  level: 'high' | 'medium' | 'low';
  factors: {
    amountScore: number;
    competitionScore: number;
    timelineScore: number;
    relevanceScore: number;
    historyScore: number;
  };
  recommendations: string[];
  riskFactors: string[];
}

// 趋势分析结果
export interface TrendAnalysis {
  timeSeries: TimeSeriesData[];
  regionDistribution: RegionData[];
  industryHeat: IndustryData[];
  amountDistribution: AmountData[];
  insights: string[];
  recommendations: string[];
}

export interface TimeSeriesData {
  period: string;
  count: number;
  totalAmount: number;
}

export interface RegionData {
  region: string;
  count: number;
  percentage: number;
}

export interface IndustryData {
  industry: string;
  count: number;
  heat: number;
}

export interface AmountData {
  range: string;
  count: number;
}

// 仪表板概览数据
export interface DashboardOverview {
  totalCount: number;
  todayCount: number;
  totalAmount: number;
  avgAmount: number;
  highValueCount: number;
  pendingCount: number;
}

// 分类统计
export interface ClassificationSummary {
  byRegion: Record<string, number>;
  byIndustry: Record<string, number>;
  byAmount: Record<string, number>;
  byTendererType: Record<string, number>;
}

// 实时消息
export interface RealtimeMessage {
  id: string;
  type: 'new_tender' | 'high_value' | 'deadline_warning' | 'system';
  title: string;
  content: string;
  timestamp: string;
  read: boolean;
  data?: Tender;
}

// API 响应类型
export interface ApiResponse<T> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
  error?: string;
}

// 分页类型
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// 筛选条件
export interface TenderFilters {
  region?: string;
  industry?: string;
  status?: string;
  minAmount?: number;
  maxAmount?: number;
  startDate?: string;
  endDate?: string;
  keyword?: string;
}
