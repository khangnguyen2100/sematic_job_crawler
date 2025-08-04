# New schema additions for crawler response without duplicate logging

from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

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

class SimpleDuplicateCheck(BaseModel):
    """Simple duplicate check without database logging"""
    is_duplicate: bool
    reason: str  # "url_match", "title_company_match", "content_similar", "unique"
    similarity_score: Optional[float] = None
