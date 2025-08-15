from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class JobSource(str, Enum):
    LINKEDIN = "LinkedIn"
    TOPCV = "TopCV"
    ITVIEC = "ITViec"
    VIETNAMWORKS = "VietnamWorks"
    OTHER = "Other"

class Job(BaseModel):
    id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1, max_length=200)
    posted_date: datetime
    source: JobSource
    original_url: str = Field(..., min_length=1)
    location: Optional[str] = None
    salary: Optional[str] = None
    job_type: Optional[str] = None  # Full-time, Part-time, Contract, etc.
    experience_level: Optional[str] = None  # Junior, Senior, etc.
    source_id: Optional[str] = None  # Source-specific job ID for deduplication
    content_hash: Optional[str] = None  # Content hash for deduplication
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    search_score: Optional[float] = None  # Relevance score from search

class JobCreate(BaseModel):
    title: str
    description: str
    company_name: str
    posted_date: datetime
    source: JobSource
    original_url: str
    location: Optional[str] = None
    salary: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    source_id: Optional[str] = None  # For deduplication

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    company_name: Optional[str] = None
    posted_date: Optional[datetime] = None
    source: Optional[JobSource] = None
    original_url: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None

class SearchRequest(BaseModel):
    query: str = Field(..., max_length=1000)
    sources: Optional[List[JobSource]] = None
    limit: Optional[int] = Field(default=10, ge=1, le=100)
    offset: Optional[int] = Field(default=0, ge=0)

class SearchResponse(BaseModel):
    jobs: List[Job]
    total: int
    limit: int
    offset: int
    query: str

class UserInteraction(BaseModel):
    id: Optional[str] = None
    user_id: str  # IP address or device ID
    job_id: str
    action: str  # "view", "click", "search"
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime

class UploadResponse(BaseModel):
    message: str
    processed_jobs: int
    errors: List[str] = []

class JobBulkUpload(BaseModel):
    jobs: List[JobCreate]

# Admin Authentication Schemas
class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# Admin Dashboard Schemas
class AdminDashboardStats(BaseModel):
    total_jobs: int
    jobs_by_source: Dict[str, int]
    recent_jobs: int  # Last 24 hours
    pending_sync_jobs: int
    last_sync_time: Optional[datetime] = None

class JobSyncRequest(BaseModel):
    sources: List[JobSource]
    limit: Optional[int] = 100

class JobSyncResponse(BaseModel):
    message: str
    synced_jobs: int
    failed_sources: List[str] = []
    
class PaginatedJobsResponse(BaseModel):
    jobs: List[Job]
    total: int
    page: int
    per_page: int
    total_pages: int
    current_page: int

class JobManagementAction(BaseModel):
    action: str  # 'delete', 'refresh', 'reindex'
    job_ids: List[str]

# Crawl Log Schemas
class CrawlLogResponse(BaseModel):
    id: str
    site_name: str
    site_url: str
    request_url: str
    crawler_type: str
    response_status: Optional[int] = None
    response_time_ms: Optional[int] = None
    jobs_found: int = 0
    jobs_processed: int = 0
    jobs_stored: int = 0
    jobs_duplicated: int = 0
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

class CrawlLogListResponse(BaseModel):
    logs: List[CrawlLogResponse]
    total: int
    limit: int
    offset: int

class CrawlDashboardSummary(BaseModel):
    total_crawls_today: int
    successful_crawls_today: int
    failed_crawls_today: int
    success_rate_today: float
    total_jobs_found_today: int
    total_jobs_stored_today: int
    total_jobs_duplicated_today: int
    active_crawlers: List[str]
    recent_errors: List[Dict[str, Any]]

class CrawlStatisticsResponse(BaseModel):
    site_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    total_jobs_found: int
    total_jobs_stored: int
    average_response_time_ms: float

# Job Deduplication Schemas
# Crawler Response Schemas
class CrawlSourceResult(BaseModel):
    """Result for a single crawler source"""
    source: str
    total_crawled: int
    jobs_added: int
    jobs_already_exist: int
    errors: List[str] = []
    success_rate: float
    duration_seconds: Optional[float] = None

class CrawlResult(BaseModel):
    """Complete crawl operation result"""
    total_crawled: int
    total_added: int
    total_already_exist: int
    sources_processed: int
    errors: List[str] = []
    source_results: Dict[str, CrawlSourceResult]
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    success_rate: float

# Job Deduplication Schemas (kept for backward compatibility)
class JobDuplicateResponse(BaseModel):
    id: str
    original_job_id: str
    duplicate_source: str
    duplicate_source_id: Optional[str] = None
    duplicate_url: Optional[str] = None
    detected_at: datetime
    similarity_score: Optional[float] = None
    duplicate_fields: Dict[str, Any]

# Crawl History Schemas
class CrawlStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class CrawlStep(BaseModel):
    id: str
    name: str
    description: str
    status: CrawlStepStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: int = 0
    message: Optional[str] = None
    error: Optional[str] = None
    details: Dict[str, Any] = {}

class CrawlHistoryCreate(BaseModel):
    job_id: str
    site_name: str
    status: str
    crawl_config: Dict[str, Any] = {}
    triggered_by: str = "manual"

class CrawlHistoryUpdate(BaseModel):
    status: Optional[str] = None
    steps: Optional[List[CrawlStep]] = None
    total_jobs_found: Optional[int] = None
    total_jobs_added: Optional[int] = None
    total_duplicates: Optional[int] = None
    total_urls_processed: Optional[int] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    errors: Optional[List[str]] = None
    summary: Optional[Dict[str, Any]] = None

class CrawlHistoryResponse(BaseModel):
    id: str
    job_id: str
    site_name: str
    status: str
    crawl_config: Dict[str, Any] = {}
    steps: List[CrawlStep] = []
    total_jobs_found: int = 0
    total_jobs_added: int = 0
    total_duplicates: int = 0
    total_urls_processed: int = 0
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    errors: List[str] = []
    summary: Optional[Dict[str, Any]] = None
    triggered_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class CrawlHistoryListResponse(BaseModel):
    items: List[CrawlHistoryResponse]
    total: int
    page: int
    size: int
    pages: int
