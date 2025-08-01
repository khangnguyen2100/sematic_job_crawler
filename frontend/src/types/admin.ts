import { Job, JobSource } from './index';

// Admin types for TypeScript
export interface AdminLoginRequest {
  username: string;
  password: string;
}

export interface AdminLoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface AdminDashboardStats {
  total_jobs: number;
  jobs_by_source: Record<string, number>;
  recent_jobs: number;
  pending_sync_jobs: number;
  last_sync_time?: string;
}

export interface JobSyncRequest {
  sources: JobSource[];
  limit?: number;
}

export interface PaginatedJobsResponse {
  jobs: Job[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
