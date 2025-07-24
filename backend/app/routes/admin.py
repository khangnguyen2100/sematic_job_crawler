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
from app.models.database import get_db, JobMetadataDB
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
    db: Session = Depends(get_db),
    marqo_service: MarqoService = Depends(get_marqo_service)
):
    """Get admin dashboard statistics"""
    try:
        # Get total jobs from database
        total_jobs = db.query(JobMetadataDB).count()
        
        # Get jobs by source
        jobs_by_source = {}
        source_counts = db.query(
            JobMetadataDB.source,
            func.count(JobMetadataDB.id)
        ).group_by(JobMetadataDB.source).all()
        
        for source, count in source_counts:
            jobs_by_source[source] = count
        
        # Get recent jobs (last 24 hours)
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        recent_jobs = db.query(JobMetadataDB).filter(
            JobMetadataDB.created_at >= twenty_four_hours_ago
        ).count()
        
        # Get Marqo index stats
        marqo_stats = await marqo_service.get_index_stats()
        
        return AdminDashboardStats(
            total_jobs=total_jobs,
            jobs_by_source=jobs_by_source,
            recent_jobs=recent_jobs,
            pending_sync_jobs=0,  # Could be enhanced with actual sync queue
            last_sync_time=None  # Could be enhanced with last sync tracking
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

@router.get("/jobs", response_model=PaginatedJobsResponse)
async def get_admin_jobs(
    page: int = 1,
    per_page: int = 20,
    source: str = None,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get paginated list of jobs for admin"""
    try:
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Build query
        query = db.query(JobMetadataDB)
        if source:
            query = query.filter(JobMetadataDB.source == source)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        jobs_data = query.order_by(desc(JobMetadataDB.created_at)).offset(offset).limit(per_page).all()
        
        # Convert to Job objects
        jobs = []
        for job_data in jobs_data:
            job = Job(
                id=job_data.marqo_id,
                title=job_data.title,
                description=job_data.description,
                company_name=job_data.company_name,
                posted_date=job_data.posted_date,
                source=JobSource(job_data.source),
                original_url=job_data.original_url,
                location=job_data.location,
                salary=job_data.salary,
                job_type=job_data.job_type,
                experience_level=job_data.experience_level,
                created_at=job_data.created_at,
                updated_at=job_data.updated_at
            )
            jobs.append(job)
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        return PaginatedJobsResponse(
            jobs=jobs,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
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
            # Delete from both database and Marqo
            deleted_count = 0
            for job_id in job_ids:
                # Delete from database
                db_job = db.query(JobMetadataDB).filter(JobMetadataDB.marqo_id == job_id).first()
                if db_job:
                    db.delete(db_job)
                    deleted_count += 1
                
                # Delete from Marqo (implement in MarqoService if needed)
                # await marqo_service.delete_job(job_id)
            
            db.commit()
            return {"message": f"Deleted {deleted_count} jobs", "affected_jobs": deleted_count}
        
        elif action == "refresh":
            # Refresh job data from original sources
            return {"message": f"Refresh initiated for {len(job_ids)} jobs", "affected_jobs": len(job_ids)}
        
        elif action == "reindex":
            # Reindex jobs in Marqo
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
    db: Session = Depends(get_db)
):
    """Delete a specific job"""
    try:
        # Delete from database
        db_job = db.query(JobMetadataDB).filter(JobMetadataDB.marqo_id == job_id).first()
        if not db_job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        db.delete(db_job)
        db.commit()
        
        return {"message": "Job deleted successfully", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")
