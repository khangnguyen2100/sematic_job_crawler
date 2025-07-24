export enum JobSource {
  LINKEDIN = "LinkedIn",
  TOPCV = "TopCV",
  ITVIEC = "ITViec",
  VIETNAMWORKS = "VietnamWorks",
  OTHER = "Other"
}

export interface Job {
  id?: string;
  title: string;
  description: string;
  company_name: string;
  posted_date: string;
  source: JobSource;
  original_url: string;
  location?: string;
  salary?: string;
  job_type?: string;
  experience_level?: string;
  created_at?: string;
  updated_at?: string;
  search_score?: number;
}

export interface SearchRequest {
  query: string;
  sources?: JobSource[];
  limit?: number;
  offset?: number;
}

export interface SearchResponse {
  jobs: Job[];
  total: number;
  limit: number;
  offset: number;
  query: string;
}

export interface UploadResponse {
  message: string;
  processed_jobs: number;
  errors: string[];
}

export interface PopularJob {
  job_id: string;
  interaction_count: number;
}

export interface SearchAnalytics {
  total_searches: number;
  unique_users: number;
  active_users: Array<{
    user_id: string;
    activity_count: number;
  }>;
  period_days?: number;
  generated_at?: string;
}

export interface DashboardData {
  search_analytics: SearchAnalytics;
  popular_jobs: PopularJob[];
  index_stats: Record<string, any>;
  crawler_status: {
    status: string;
    jobs?: Array<{
      id: string;
      name: string;
      next_run: string | null;
      trigger: string;
    }>;
  };
  period_days: number;
  generated_at: string;
}
