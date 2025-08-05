from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.schemas import CrawlLogListResponse, CrawlDashboardSummary, CrawlStatisticsResponse
from app.services.crawl_logging_service import CrawlLoggingService
from app.routes.admin import get_current_admin

router = APIRouter(tags=["admin", "crawl-logs"])


def get_crawl_logging_service(db: Session = Depends(get_db)):
    """Dependency to get crawl logging service"""
    return CrawlLoggingService(db)


@router.get("")
async def get_crawl_logs(
    site_name: Optional[str] = None,
    crawler_type: Optional[str] = None,
    status: Optional[str] = Query(None, description="'success', 'error', or 'all'"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    current_admin=Depends(get_current_admin),
    logging_service: CrawlLoggingService = Depends(get_crawl_logging_service)
):
    """Get crawl logs with filtering and pagination"""
    try:
        logs, total = logging_service.get_crawl_logs(
            site_name=site_name,
            crawler_type=crawler_type,
            status_filter=status,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        log_data = []
        for log in logs:
            duration_ms = None
            if log.completed_at and log.started_at:
                duration_ms = int((log.completed_at - log.started_at).total_seconds() * 1000)
            
            log_data.append({
                'id': str(log.id),
                'site_name': log.site_name,
                'site_url': log.site_url,
                'request_url': log.request_url,
                'crawler_type': log.crawler_type,
                'response_status': log.response_status,
                'response_time_ms': log.response_time_ms,
                'duration_ms': duration_ms,
                'jobs_found': log.jobs_found,
                'jobs_processed': log.jobs_processed,
                'jobs_stored': log.jobs_stored,
                'jobs_duplicated': log.jobs_duplicated,
                'error_message': log.error_message,
                'started_at': log.started_at.isoformat() if log.started_at else None,
                'completed_at': log.completed_at.isoformat() if log.completed_at else None
            })
        
        return {
            'logs': log_data,
            'total': total,
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get crawl logs: {str(e)}")


@router.get("/{log_id}")
async def get_crawl_log_details(
    log_id: str,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get specific log details"""
    try:
        log = db.query(db.CrawlLogDB).filter(db.CrawlLogDB.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")
        
        duration_ms = None
        if log.completed_at and log.started_at:
            duration_ms = int((log.completed_at - log.started_at).total_seconds() * 1000)
        
        return {
            'id': str(log.id),
            'site_name': log.site_name,
            'site_url': log.site_url,
            'request_url': log.request_url,
            'crawler_type': log.crawler_type,
            'request_method': log.request_method,
            'request_headers': log.request_headers,
            'response_status': log.response_status,
            'response_time_ms': log.response_time_ms,
            'response_size_bytes': log.response_size_bytes,
            'duration_ms': duration_ms,
            'jobs_found': log.jobs_found,
            'jobs_processed': log.jobs_processed,
            'jobs_stored': log.jobs_stored,
            'jobs_duplicated': log.jobs_duplicated,
            'error_message': log.error_message,
            'error_details': log.error_details,
            'started_at': log.started_at.isoformat() if log.started_at else None,
            'completed_at': log.completed_at.isoformat() if log.completed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get log details: {str(e)}")


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    current_admin=Depends(get_current_admin),
    logging_service: CrawlLoggingService = Depends(get_crawl_logging_service)
):
    """Get dashboard summary statistics"""
    try:
        summary = logging_service.get_dashboard_summary()
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard summary: {str(e)}")


@router.delete("/cleanup")
async def cleanup_old_logs(
    days_to_keep: int = Query(90, ge=1, le=365, description="Number of days to keep logs"),
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Clean up old logs based on retention policy"""
    try:
        cutoff_date = datetime.now() - datetime.timedelta(days=days_to_keep)
        
        # Delete old crawl logs
        deleted_logs = db.query(db.CrawlLogDB).filter(
            db.CrawlLogDB.started_at < cutoff_date
        ).delete()
        
        # Delete old statistics
        deleted_stats = db.query(db.CrawlStatisticsDB).filter(
            db.CrawlStatisticsDB.date < cutoff_date
        ).delete()
        
        db.commit()
        
        return {
            'message': f'Cleanup completed',
            'deleted_logs': deleted_logs,
            'deleted_statistics': deleted_stats,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to cleanup logs: {str(e)}")


@router.get("/statistics/sites")
async def get_site_statistics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get statistics by site for the last N days"""
    try:
        from sqlalchemy import func
        from app.models.database import CrawlStatisticsDB
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        stats = db.query(
            CrawlStatisticsDB.site_name,
            func.sum(CrawlStatisticsDB.total_requests).label('total_requests'),
            func.sum(CrawlStatisticsDB.successful_requests).label('successful_requests'),
            func.sum(CrawlStatisticsDB.failed_requests).label('failed_requests'),
            func.sum(CrawlStatisticsDB.total_jobs_found).label('total_jobs_found'),
            func.sum(CrawlStatisticsDB.total_jobs_stored).label('total_jobs_stored'),
            func.sum(CrawlStatisticsDB.total_jobs_duplicated).label('total_jobs_duplicated'),
            func.avg(CrawlStatisticsDB.average_response_time_ms).label('avg_response_time')
        ).filter(
            CrawlStatisticsDB.date >= cutoff_date
        ).group_by(CrawlStatisticsDB.site_name).all()
        
        result = []
        for stat in stats:
            success_rate = (stat.successful_requests / stat.total_requests * 100) if stat.total_requests > 0 else 0
            
            result.append({
                'site_name': stat.site_name,
                'total_requests': stat.total_requests,
                'successful_requests': stat.successful_requests,
                'failed_requests': stat.failed_requests,
                'success_rate': round(success_rate, 2),
                'total_jobs_found': stat.total_jobs_found,
                'total_jobs_stored': stat.total_jobs_stored,
                'total_jobs_duplicated': stat.total_jobs_duplicated,
                'average_response_time_ms': round(float(stat.avg_response_time), 2) if stat.avg_response_time else None
            })
        
        return {
            'statistics': result,
            'period_days': days,
            'period_start': cutoff_date.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get site statistics: {str(e)}")
