from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.services.analytics_service import AnalyticsService
from app.models.database import get_db

router = APIRouter()

def get_analytics_service():
    return AnalyticsService()

@router.get("/analytics/popular-jobs")
async def get_popular_jobs(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    db = Depends(get_db)
):
    """Get most popular jobs based on user interactions"""
    try:
        popular_jobs = analytics_service.get_popular_jobs(db, days=days, limit=limit)
        return {
            "popular_jobs": popular_jobs,
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get popular jobs: {str(e)}")

@router.get("/analytics/search-stats")
async def get_search_analytics(
    days: int = Query(7, ge=1, le=30),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    db = Depends(get_db)
):
    """Get search analytics and statistics"""
    try:
        stats = analytics_service.get_search_analytics(db, days=days)
        stats["period_days"] = days
        stats["generated_at"] = datetime.utcnow().isoformat()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search analytics: {str(e)}")

@router.get("/analytics/user/{user_id}/interactions")
async def get_user_interactions(
    user_id: str,
    limit: int = Query(50, ge=1, le=100),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    db = Depends(get_db)
):
    """Get interactions for a specific user"""
    try:
        interactions = analytics_service.get_user_interactions(db, user_id=user_id, limit=limit)
        return {
            "user_id": user_id,
            "interactions": interactions,
            "total": len(interactions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user interactions: {str(e)}")

@router.get("/analytics/crawler/status")
async def get_crawler_status():
    """Get crawler and scheduler status"""
    try:
        from app.main import job_scheduler
        
        if job_scheduler:
            status = job_scheduler.get_scheduler_status()
            return status
        else:
            return {"status": "not_initialized"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get crawler status: {str(e)}")

@router.post("/analytics/crawler/trigger", response_model=dict)
async def trigger_manual_crawl():
    """Manually trigger a crawl job"""
    try:
        from app.main import job_scheduler
        
        if not job_scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not available")
        
        results = await job_scheduler.trigger_manual_crawl()
        
        # Convert CrawlResult to dict if needed
        if hasattr(results, 'dict'):
            results_dict = results.dict()
        else:
            results_dict = results
            
        return {
            "message": "Manual crawl triggered",
            "results": results_dict,
            "triggered_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger crawl: {str(e)}")

@router.get("/analytics/dashboard")
async def get_dashboard_data(
    days: int = Query(7, ge=1, le=30),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    db = Depends(get_db)
):
    """Get comprehensive dashboard data"""
    try:
        # Get various analytics data
        search_stats = analytics_service.get_search_analytics(db, days=days)
        popular_jobs = analytics_service.get_popular_jobs(db, days=days, limit=5)
        
        # Get job index stats
        from app.main import marqo_service
        index_stats = {}
        if marqo_service:
            try:
                index_stats = await marqo_service.get_index_stats()
            except:
                pass
        
        # Get crawler status
        crawler_status = {"status": "unknown"}
        try:
            from app.main import job_scheduler
            if job_scheduler:
                crawler_status = job_scheduler.get_scheduler_status()
        except:
            pass
        
        return {
            "search_analytics": search_stats,
            "popular_jobs": popular_jobs,
            "index_stats": index_stats,
            "crawler_status": crawler_status,
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")
