import { DashboardData, Job, JobSource, SearchRequest, SearchResponse, UploadResponse } from '@/types';
import { AdminDashboardStats, AdminLoginRequest, AdminLoginResponse, JobSyncRequest, PaginatedJobsResponse } from '@/types/admin';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    
    // Handle authentication errors
    if (error.response?.status === 401 && error.config?.url?.includes('/admin/')) {
      // Token is invalid or expired, clear it and redirect to login
      authToken = null;
      localStorage.removeItem('admin_token');
      
      // Only redirect if we're not already on the login page
      if (window.location.pathname !== '/admin/login') {
        window.location.href = '/admin/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export const jobsApi = {
  // Search jobs
  searchJobs: async (searchRequest: SearchRequest): Promise<SearchResponse> => {
    const response = await api.post('/search', searchRequest);
    return response.data;
  },

  // Get job by ID
  getJob: async (jobId: string): Promise<Job> => {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
  },

  // List jobs
  listJobs: async (params: {
    sources?: JobSource[];
    limit?: number;
    offset?: number;
  } = {}): Promise<SearchResponse> => {
    const response = await api.get('/jobs', { params });
    return response.data;
  },

  // Track job click
  trackJobClick: async (jobId: string): Promise<void> => {
    await api.post(`/jobs/${jobId}/click`);
  },

  // Get job stats
  getJobStats: async (): Promise<any> => {
    const response = await api.get('/jobs/stats');
    return response.data;
  },

  // Upload CSV
  uploadCSV: async (file: File, source: JobSource): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source', source);

    const response = await api.post('/upload/csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Download CSV template
  downloadCSVTemplate: async (): Promise<Blob> => {
    const response = await api.get('/upload/template', {
      responseType: 'blob',
    });
    return response.data;
  },

  // Get search suggestions
  getSearchSuggestions: async (query: string = '', limit: number = 5): Promise<string[]> => {
    const response = await api.get('/search/suggestions', {
      params: { query, limit }
    });
    return response.data.suggestions;
  },

  // Analytics endpoints
  getPopularJobs: async (days: number = 7, limit: number = 10): Promise<any> => {
    const response = await api.get('/analytics/popular-jobs', {
      params: { days, limit }
    });
    return response.data;
  },

  getSearchAnalytics: async (days: number = 7): Promise<any> => {
    const response = await api.get('/analytics/search-stats', {
      params: { days }
    });
    return response.data;
  },

  getDashboardData: async (days: number = 7): Promise<DashboardData> => {
    const response = await api.get('/analytics/dashboard', {
      params: { days }
    });
    return response.data;
  },

  getCrawlerStatus: async (): Promise<any> => {
    const response = await api.get('/analytics/crawler/status');
    return response.data;
  },

  triggerManualCrawl: async (): Promise<any> => {
    const response = await api.post('/analytics/crawler/trigger');
    return response.data;
  },
};

// Token storage
let authToken: string | null = localStorage.getItem('admin_token');

// Add token to requests
api.interceptors.request.use(
  (config) => {
    // Get token from memory or localStorage
    const token = authToken || localStorage.getItem('admin_token');
    if (token && config.url?.includes('/admin/')) {
      config.headers.Authorization = `Bearer ${token}`;
      // Update in-memory token if it was retrieved from localStorage
      if (!authToken) {
        authToken = token;
      }
    }
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => Promise.reject(error)
);

export const adminApi = {
  // Authentication
  login: async (credentials: AdminLoginRequest): Promise<AdminLoginResponse> => {
    const response = await api.post('/admin/login', credentials);
    const data = response.data;
    authToken = data.access_token;
    localStorage.setItem('admin_token', data.access_token);
    return data;
  },

  logout: () => {
    authToken = null;
    localStorage.removeItem('admin_token');
  },

  isAuthenticated: (): boolean => {
    // Check both the in-memory token and localStorage
    const token = authToken || localStorage.getItem('admin_token');
    if (token && !authToken) {
      // Update the in-memory token if it exists in localStorage but not in memory
      authToken = token;
    }
    return !!token;
  },

  // Dashboard
  getDashboardStats: async (): Promise<AdminDashboardStats> => {
    const response = await api.get('/admin/dashboard/stats');
    return response.data;
  },

  // Jobs Management
  getJobs: async (page: number = 1, perPage: number = 20, source?: string): Promise<PaginatedJobsResponse> => {
    const params: any = { page, per_page: perPage };
    if (source) params.source = source;
    
    const response = await api.get('/admin/jobs', { params });
    return response.data;
  },

  syncJobs: async (syncRequest: JobSyncRequest): Promise<any> => {
    const response = await api.post('/admin/jobs/sync', syncRequest);
    return response.data;
  },

  deleteJob: async (jobId: string): Promise<any> => {
    const response = await api.delete(`/admin/jobs/${jobId}`);
    return response.data;
  },

  manageJobs: async (action: string, jobIds: string[]): Promise<any> => {
    const response = await api.post('/admin/jobs/manage', {
      action,
      job_ids: jobIds
    });
    return response.data;
  },

  // Analytics
  getAnalyticsSummary: async (): Promise<any> => {
    const response = await api.get('/admin/analytics/summary');
    return response.data;
  },

  // Crawl Logs
  getCrawlLogs: async (params: {
    site_name?: string;
    crawler_type?: string;
    status?: string;
    date_from?: string;
    date_to?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<any> => {
    const response = await api.get('/admin/crawl-logs', { params });
    return response.data;
  },

  getCrawlLogsSummary: async (): Promise<any> => {
    const response = await api.get('/admin/crawl-logs/dashboard/summary');
    return response.data;
  },

  cleanupCrawlLogs: async (days?: number): Promise<any> => {
    const params = days ? { days } : {};
    const response = await api.delete('/admin/crawl-logs/cleanup', { params });
    return response.data;
  },

  getCrawlLogById: async (logId: string): Promise<any> => {
    const response = await api.get(`/admin/crawl-logs/${logId}`);
    return response.data;
  },

  getCrawlStatistics: async (): Promise<any> => {
    const response = await api.get('/admin/crawl-logs/statistics/sites');
    return response.data;
  },
};

export default api;
