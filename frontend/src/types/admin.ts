import { Job as BaseJob, JobSource } from './index';

// Extended Job interface for admin with additional fields
export interface Job extends BaseJob {
  is_deleted?: boolean;
  is_active?: boolean;
  admin_notes?: string;
}

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
  current_page: number;
}

// Sync Job types
export interface SyncJobRequest {
  max_jobs?: number;
}

export interface SyncJobResponse {
  job_id: string;
  message: string;
  site_name: string;
}

export enum CrawlStepStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  SKIPPED = "skipped"
}

export interface CrawlStep {
  id: string;
  name: string;
  description: string;
  status: CrawlStepStatus;
  started_at?: string;
  completed_at?: string;
  progress_percentage: number;
  message?: string;
  error?: string;
  details: Record<string, any>;
}

export interface CrawlJobProgress {
  job_id: string;
  site_name: string;
  status: CrawlStepStatus;
  steps: CrawlStep[];
  started_at: string;
  completed_at?: string;
  total_jobs_found: number;
  total_jobs_added: number;
  total_duplicates: number;
  errors: string[];
  summary?: string;
}

// Data Source types
export interface DataSource {
  id: string;
  site_name: string;
  site_url: string;
  config: any;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
