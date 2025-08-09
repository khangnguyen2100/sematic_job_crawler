import time
from datetime import datetime, date
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.database import CrawlLogDB, CrawlStatisticsDB


class CrawlLoggingService:
    """Service to handle comprehensive crawler logging and monitoring"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def start_crawl_session(
        self, 
        site_name: str, 
        site_url: str, 
        request_url: str,
        crawler_type: str,
        request_headers: Dict[str, str] = None
    ) -> CrawlLogDB:
        """Start a new crawl session and return log entry"""
        log_entry = CrawlLogDB(
            site_name=site_name,
            site_url=site_url,
            request_url=request_url,
            crawler_type=crawler_type,
            request_headers=request_headers or {},
            started_at=datetime.utcnow()
        )
        
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        
        return log_entry
    
    def complete_crawl_session(
        self,
        log_id: str,
        response_status: int,
        response_time_ms: int,
        response_size_bytes: int = 0,
        jobs_found: int = 0,
        jobs_processed: int = 0,
        jobs_stored: int = 0,
        jobs_duplicated: int = 0,
        error_message: str = None,
        error_details: Dict[str, Any] = None
    ):
        """Complete crawl session with results"""
        log_entry = self.db.query(CrawlLogDB).filter(CrawlLogDB.id == log_id).first()
        
        if log_entry:
            log_entry.response_status = response_status
            log_entry.response_time_ms = response_time_ms
            log_entry.response_size_bytes = response_size_bytes
            log_entry.jobs_found = jobs_found
            log_entry.jobs_processed = jobs_processed
            log_entry.jobs_stored = jobs_stored
            log_entry.jobs_duplicated = jobs_duplicated
            log_entry.error_message = error_message
            log_entry.error_details = error_details or {}
            log_entry.completed_at = datetime.utcnow()
            
            self.db.commit()
            
            # Update daily statistics
            self.update_daily_statistics(log_entry)
    
    def update_daily_statistics(self, log_entry: CrawlLogDB):
        """Update daily statistics for the crawl"""
        today = date.today()
        
        stats = self.db.query(CrawlStatisticsDB).filter(
            CrawlStatisticsDB.site_name == log_entry.site_name,
            func.date(CrawlStatisticsDB.date) == today
        ).first()
        
        if not stats:
            stats = CrawlStatisticsDB(
                site_name=log_entry.site_name,
                date=datetime.combine(today, datetime.min.time())
            )
            self.db.add(stats)
        
        # Update counters
        stats.total_requests += 1
        if log_entry.response_status and 200 <= log_entry.response_status < 300:
            stats.successful_requests += 1
        else:
            stats.failed_requests += 1
            
        stats.total_jobs_found += log_entry.jobs_found or 0
        stats.total_jobs_stored += log_entry.jobs_stored or 0
        stats.total_jobs_duplicated += log_entry.jobs_duplicated or 0
        
        # Update averages
        all_logs_today = self.db.query(CrawlLogDB).filter(
            CrawlLogDB.site_name == log_entry.site_name,
            func.date(CrawlLogDB.started_at) == today
        ).all()
        
        response_times = [log.response_time_ms for log in all_logs_today if log.response_time_ms]
        if response_times:
            stats.average_response_time_ms = sum(response_times) / len(response_times)
            
        data_sizes = [log.response_size_bytes for log in all_logs_today if log.response_size_bytes]
        if data_sizes:
            stats.total_data_size_mb = sum(data_sizes) / (1024 * 1024)  # Convert to MB
            
        stats.last_updated = datetime.utcnow()
        self.db.commit()

    def get_crawl_logs(
        self,
        site_name: str = None,
        crawler_type: str = None,
        status_filter: str = None,
        date_from: date = None,
        date_to: date = None,
        limit: int = 50,
        offset: int = 0
    ):
        """Get crawl logs with filtering"""
        query = self.db.query(CrawlLogDB)
        
        if site_name:
            query = query.filter(CrawlLogDB.site_name == site_name)
        
        if crawler_type:
            query = query.filter(CrawlLogDB.crawler_type == crawler_type)
            
        if status_filter == 'success':
            query = query.filter(CrawlLogDB.response_status.between(200, 299))
        elif status_filter == 'error':
            query = query.filter(~CrawlLogDB.response_status.between(200, 299))
            
        if date_from:
            query = query.filter(func.date(CrawlLogDB.started_at) >= date_from)
            
        if date_to:
            query = query.filter(func.date(CrawlLogDB.started_at) <= date_to)
        
        total = query.count()
        logs = query.order_by(CrawlLogDB.started_at.desc()).offset(offset).limit(limit).all()
        
        return logs, total

    def get_dashboard_summary(self):
        """Get summary statistics for dashboard"""
        today = date.today()
        
        # Today's statistics
        today_stats = self.db.query(CrawlStatisticsDB).filter(
            func.date(CrawlStatisticsDB.date) == today
        ).all()
        
        total_crawls_today = sum(stat.total_requests for stat in today_stats)
        successful_crawls_today = sum(stat.successful_requests for stat in today_stats)
        total_jobs_found_today = sum(stat.total_jobs_found for stat in today_stats)
        
        success_rate_today = (successful_crawls_today / total_crawls_today * 100) if total_crawls_today > 0 else 0
        
        # Recent errors (unique by site_name and error_message)
        recent_errors = self.db.query(CrawlLogDB).filter(
            CrawlLogDB.error_message.isnot(None),
            func.date(CrawlLogDB.started_at) == today
        ).order_by(CrawlLogDB.started_at.desc()).limit(10).all()
        
        # Remove duplicates by site_name + error_message combination
        seen_errors = set()
        unique_errors = []
        for error in recent_errors:
            error_key = (error.site_name, error.error_message)
            if error_key not in seen_errors:
                seen_errors.add(error_key)
                unique_errors.append(error)
                if len(unique_errors) >= 5:  # Limit to 5 unique errors
                    break
        
        # Active crawlers (recent activity)
        active_crawlers = self.db.query(
            CrawlLogDB.site_name,
            func.max(CrawlLogDB.started_at).label('last_activity')
        ).group_by(CrawlLogDB.site_name).all()
        
        return {
            'total_crawls_today': total_crawls_today,
            'success_rate_today': round(success_rate_today, 2),
            'total_jobs_found_today': total_jobs_found_today,
            'active_crawlers': [
                {
                    'site_name': site_name,
                    'last_activity': last_activity.isoformat() if last_activity else None
                }
                for site_name, last_activity in active_crawlers
            ],
            'recent_errors': [
                {
                    'id': str(error.id),
                    'site_name': error.site_name,
                    'error_message': error.error_message,
                    'started_at': error.started_at.isoformat() if error.started_at else None
                }
                for error in unique_errors
            ]
        }


class CrawlLogger:
    """Context manager for easier crawler logging integration"""
    
    def __init__(self, logging_service: CrawlLoggingService, site_name: str, site_url: str, request_url: str, crawler_type: str):
        self.logging_service = logging_service
        self.site_name = site_name
        self.site_url = site_url
        self.request_url = request_url
        self.crawler_type = crawler_type
        self.log_entry = None
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        self.log_entry = self.logging_service.start_crawl_session(
            self.site_name, 
            self.site_url, 
            self.request_url, 
            self.crawler_type
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        response_time_ms = int((end_time - self.start_time) * 1000)
        
        if exc_type:
            # Handle exception
            self.logging_service.complete_crawl_session(
                log_id=str(self.log_entry.id),
                response_status=500,
                response_time_ms=response_time_ms,
                error_message=str(exc_val),
                error_details={"exception_type": exc_type.__name__}
            )
        # If no exception, the crawler should call complete() manually
    
    def complete(self, **kwargs):
        """Complete the crawl session with custom parameters"""
        self.logging_service.complete_crawl_session(
            log_id=str(self.log_entry.id),
            **kwargs
        )


class AsyncCrawlLogger:
    """Async context manager for easier crawler logging integration"""
    
    def __init__(self, logging_service: CrawlLoggingService, site_name: str, site_url: str, request_url: str, crawler_type: str):
        self.logging_service = logging_service
        self.site_name = site_name
        self.site_url = site_url
        self.request_url = request_url
        self.crawler_type = crawler_type
        self.log_entry = None
        self.start_time = None
        
    async def __aenter__(self):
        self.start_time = time.time()
        self.log_entry = self.logging_service.start_crawl_session(
            self.site_name, 
            self.site_url, 
            self.request_url, 
            self.crawler_type
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        response_time_ms = int((end_time - self.start_time) * 1000)
        
        if exc_type:
            # Handle exception
            self.logging_service.complete_crawl_session(
                log_id=str(self.log_entry.id),
                response_status=500,
                response_time_ms=response_time_ms,
                error_message=str(exc_val),
                error_details={"exception_type": exc_type.__name__}
            )
        # If no exception, the crawler should call complete() manually
    
    def complete(self, **kwargs):
        """Complete the crawl session with custom parameters"""
        self.logging_service.complete_crawl_session(
            log_id=str(self.log_entry.id),
            **kwargs
        )
