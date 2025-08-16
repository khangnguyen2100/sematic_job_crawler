from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.models.schemas import (
    AdminLoginRequest, AdminLoginResponse, AdminDashboardStats,
    JobSyncRequest, JobSyncResponse, PaginatedJobsResponse,
    JobManagementAction, Job, JobSource
)
from app.services.auth_service import AuthService, get_current_admin
from app.services.marqo_service import MarqoService
from app.services.analytics_service import AnalyticsService
from app.models.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

router = APIRouter(prefix="/admin", tags=["admin"])

# Dependency injection
def get_marqo_service():
    from app.main import marqo_service
    return marqo_service

def get_analytics_service():
    return AnalyticsService()

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(login_request: AdminLoginRequest):
    """Admin login endpoint"""
    if not AuthService.authenticate_admin(login_request.username, login_request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = AuthService.create_access_token(
        data={"sub": login_request.username, "role": "admin"}
    )
    
    return AdminLoginResponse(
        access_token=access_token,
        expires_in=480 * 60  # 8 hours in seconds
    )

@router.get("/dashboard/stats", response_model=AdminDashboardStats)
async def get_dashboard_stats(
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    marqo_service: MarqoService = Depends(get_marqo_service)
):
    """Get admin dashboard statistics"""
    try:
        # Get Marqo index stats
        marqo_stats = await marqo_service.get_index_stats()
        
        # Extract relevant data from Marqo stats
        total_jobs = marqo_stats.get('numberOfDocuments', 0)
        
        # Note: We can't get jobs by source from index stats, so we provide a placeholder
        jobs_by_source = {
            "TopCV": 0,
            "ITViec": 0, 
            "VietnamWorks": 0,
            "LinkedIn": 0
        }
        
        return AdminDashboardStats(
            total_jobs=total_jobs,
            jobs_by_source=jobs_by_source,
            recent_jobs=0,  # Could be enhanced with time-based filtering in Marqo
            pending_sync_jobs=0,
            last_sync_time=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

@router.get("/jobs", response_model=PaginatedJobsResponse)
async def get_admin_jobs(
    page: int = 1,
    per_page: int = 20,
    source: str = None,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    marqo_service: MarqoService = Depends(get_marqo_service)
):
    """Get paginated list of jobs for admin"""
    try:
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Create a search request to get jobs from Marqo
        from app.models.schemas import SearchRequest, JobSource as JobSourceEnum
        
        search_request = SearchRequest(
            query="*",  # Get all jobs
            sources=[JobSourceEnum(source)] if source else None,
            location="",
            limit=per_page,
            offset=offset
        )
        
        # Get jobs from Marqo
        search_result = await marqo_service.search_jobs(search_request)
        jobs = search_result.get("jobs", [])
        
        # Get the actual total count from Marqo index stats
        marqo_stats = await marqo_service.get_index_stats()
        total = marqo_stats.get('numberOfDocuments', 0)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return PaginatedJobsResponse(
            jobs=jobs,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            current_page=page
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get jobs: {str(e)}")

@router.post("/jobs/sync", response_model=JobSyncResponse)
async def sync_jobs(
    sync_request: JobSyncRequest,
    background_tasks: BackgroundTasks,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    marqo_service: MarqoService = Depends(get_marqo_service)
):
    """Trigger job synchronization from specified sources"""
    try:
        # This would typically trigger your crawler services
        # For now, we'll return a mock response
        # In a real implementation, you'd:
        # 1. Queue crawling tasks for each source
        # 2. Track progress in a job queue/database
        # 3. Return immediate response with job ID for tracking
        
        total_synced = 0
        failed_sources = []
        
        for source in sync_request.sources:
            try:
                # Mock sync logic - replace with actual crawler calls
                print(f"Syncing jobs from {source.value}...")
                # Simulate some synced jobs
                total_synced += 10  # Mock number
            except Exception as e:
                print(f"Failed to sync from {source.value}: {e}")
                failed_sources.append(source.value)
        
        return JobSyncResponse(
            message=f"Sync initiated for {len(sync_request.sources)} sources",
            synced_jobs=total_synced,
            failed_sources=failed_sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync jobs: {str(e)}")

@router.post("/jobs/manage")
async def manage_jobs(
    action_request: JobManagementAction,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db),
    marqo_service: MarqoService = Depends(get_marqo_service)
):
    """Perform bulk actions on jobs"""
    try:
        action = action_request.action.lower()
        job_ids = action_request.job_ids
        
        if action == "delete":
            # Delete from both Marqo and PostgreSQL metadata
            deleted_count = 0
            for job_id in job_ids:
                success = await marqo_service.delete_job(job_id, db)
                if success:
                    deleted_count += 1
            
            return {"message": f"Deleted {deleted_count} jobs", "affected_jobs": deleted_count}
        
        elif action == "refresh":
            # Refresh job data from original sources
            return {"message": f"Refresh initiated for {len(job_ids)} jobs", "affected_jobs": len(job_ids)}
        
        elif action == "reindex":
            # Reindex jobs in Marqo - for now just return success
            return {"message": f"Reindexing initiated for {len(job_ids)} jobs", "affected_jobs": len(job_ids)}
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to manage jobs: {str(e)}")

@router.get("/analytics/summary")
async def get_analytics_summary(
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    db: Session = Depends(get_db)
):
    """Get analytics summary for admin dashboard"""
    try:
        # Get search analytics
        total_searches = db.execute("SELECT COUNT(*) FROM user_interactions WHERE action = 'search'").scalar()
        total_views = db.execute("SELECT COUNT(*) FROM user_interactions WHERE action = 'view'").scalar()
        total_clicks = db.execute("SELECT COUNT(*) FROM user_interactions WHERE action = 'click'").scalar()
        
        # Get popular searches (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        popular_queries = db.execute("""
            SELECT metadata->>'query' as query, COUNT(*) as count
            FROM user_interactions 
            WHERE action = 'search' 
            AND created_at >= %s
            AND metadata->>'query' IS NOT NULL
            GROUP BY metadata->>'query'
            ORDER BY count DESC
            LIMIT 10
        """, (seven_days_ago,)).fetchall()
        
        return {
            "total_searches": total_searches or 0,
            "total_views": total_views or 0,
            "total_clicks": total_clicks or 0,
            "popular_queries": [{"query": row[0], "count": row[1]} for row in popular_queries] if popular_queries else []
        }
    except Exception as e:
        print(f"Analytics error: {e}")
        return {
            "total_searches": 0,
            "total_views": 0,
            "total_clicks": 0,
            "popular_queries": []
        }

@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    marqo_service: MarqoService = Depends(get_marqo_service),
    db: Session = Depends(get_db)
):
    """Delete a specific job"""
    try:
        # Delete from both Marqo and PostgreSQL metadata
        success = await marqo_service.delete_job(job_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"message": "Job deleted successfully", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")
