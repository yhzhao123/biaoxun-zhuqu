/**
 * Tender types - Phase 4 Task 018
 */

export interface Tender {
  id: string;
  notice_id: string;
  title: string;
  description?: string;
  tenderer: string;
  budget?: number;
  currency: string;
  publish_date?: string;
  deadline_date?: string;
  region?: string;
  industry?: string;
  source_url?: string;
  source_site?: string;
  status: 'pending' | 'active' | 'closed' | 'expired';
  created_at: string;
  updated_at: string;
}

export interface TenderListResponse {
  count: number;
  results: Tender[];
  page: number;
  page_size: number;
}

export interface TenderFilter {
  status?: string;
  region?: string;
  industry?: string;
  source_site?: string;
  min_budget?: number;
  max_budget?: number;
  start_date?: string;
  end_date?: string;
  search?: string;
}

export interface CrawlTask {
  id: number;
  name: string;
  source_url: string;
  source_site: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  items_crawled: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface Statistics {
  total_tenders: number;
  active_tenders: number;
  total_budget: number;
  by_region: { region: string; count: number }[];
  by_industry: { industry: string; count: number }[];
  by_status: { status: string; count: number }[];
  daily_trend: { date: string; count: number }[];
}

// Phase 5: Tenderer clustering
export interface Tenderer {
  id: string;
  name: string;
  normalized_name: string;
  cluster_id?: number;
  total_tenders: number;
  total_budget: number;
  active_tenders: number;
  industries: { name: string; count: number }[];
  regions: { name: string; count: number }[];
  recent_tenders: Tender[];
  created_at: string;
  updated_at: string;
}

// Phase 8: Notification Service
export interface Notification {
  id: string;
  type: 'tender_match' | 'price_alert' | 'system' | 'crawl_complete';
  title: string;
  message: string;
  is_read: boolean;
  data?: Record<string, unknown>;
  created_at: string;
}

export interface NotificationPreferences {
  email_enabled: boolean;
  tender_match_enabled: boolean;
  price_alert_enabled: boolean;
  system_notifications_enabled: boolean;
  crawl_complete_enabled: boolean;
}

// Phase 9: User preferences
export interface UserPreferences {
  id: string;
  username: string;
  email: string;
  notification_preferences: NotificationPreferences;
  default_region?: string;
  default_industry?: string;
  display_settings: {
    theme: 'light' | 'dark' | 'auto';
    language: 'zh' | 'en';
    items_per_page: number;
  };
  created_at: string;
  updated_at: string;
}
