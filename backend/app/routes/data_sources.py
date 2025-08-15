"""
Data Source Configuration Management API

This module provides CRUD operations for managing crawler configurations,
including site domains, parameters, and other crawler-specific settings.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.database import get_db, CrawlerConfigDB, CrawlHistoryDB
from app.services.auth_service import get_current_admin
from app.models.schemas import JobSource, CrawlHistoryResponse, CrawlHistoryListResponse, CrawlStepStatus
from app.services.crawl_progress_service import crawl_progress_service, CrawlJobProgress
from app.services.marqo_service import MarqoService
from pydantic import BaseModel

router = APIRouter(prefix="/admin/data-sources", tags=["admin", "data-sources"])

def get_marqo_service():
    """Get MarqoService dependency"""
    from app.main import marqo_service
    return marqo_service

# Pydantic models for request/response
class CrawlerConfigBase(BaseModel):
    site_name: str
    site_url: str
    config: Dict[str, Any]
    is_active: bool = True

class CrawlerConfigCreate(CrawlerConfigBase):
    pass

class CrawlerConfigUpdate(BaseModel):
    site_name: Optional[str] = None
    site_url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class CrawlerConfigResponse(CrawlerConfigBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Additional models for sync jobs
class SyncJobRequest(BaseModel):
    max_jobs: Optional[int] = None

class SyncJobResponse(BaseModel):
    job_id: str
    task_id: Optional[str] = None  # Background task ID for enhanced tracking
    message: str
    site_name: str

class BackgroundTaskInfo(BaseModel):
    task_id: str
    name: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    has_result: bool

@router.get("/", response_model=List[CrawlerConfigResponse])
async def get_all_data_sources(
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all crawler configurations"""
    configs = db.query(CrawlerConfigDB).all()
    configs.sort(key=lambda x: x.created_at, reverse=True)
    return [CrawlerConfigResponse(
        id=str(config.id),
        site_name=config.site_name,
        site_url=config.site_url,
        config=config.config,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at
    ) for config in configs]

@router.post("/", response_model=CrawlerConfigResponse)
async def create_data_source(
    config_data: CrawlerConfigCreate,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new crawler configuration"""
    
    # Check if site already exists
    existing = db.query(CrawlerConfigDB).filter(
        CrawlerConfigDB.site_name == config_data.site_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Configuration for site '{config_data.site_name}' already exists"
        )
    
    # Create new configuration
    new_config = CrawlerConfigDB(
        site_name=config_data.site_name,
        site_url=config_data.site_url,
        config=config_data.config,
        is_active=config_data.is_active
    )
    
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    
    return CrawlerConfigResponse(
        id=str(new_config.id),
        site_name=new_config.site_name,
        site_url=new_config.site_url,
        config=new_config.config,
        is_active=new_config.is_active,
        created_at=new_config.created_at,
        updated_at=new_config.updated_at
    )

@router.get("/{site_name}", response_model=CrawlerConfigResponse)
async def get_data_source(
    site_name: str,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get a specific crawler configuration"""
    config = db.query(CrawlerConfigDB).filter(
        CrawlerConfigDB.site_name == site_name
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration for site '{site_name}' not found"
        )
    
    return CrawlerConfigResponse(
        id=str(config.id),
        site_name=config.site_name,
        site_url=config.site_url,
        config=config.config,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at
    )

@router.put("/{site_name}", response_model=CrawlerConfigResponse)
async def update_data_source(
    site_name: str,
    update_data: CrawlerConfigUpdate,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a crawler configuration"""
    config = db.query(CrawlerConfigDB).filter(
        CrawlerConfigDB.site_name == site_name
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration for site '{site_name}' not found"
        )
    
    # Update only provided fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(config, field, value)
    
    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    
    return CrawlerConfigResponse(
        id=str(config.id),
        site_name=config.site_name,
        site_url=config.site_url,
        config=config.config,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at
    )

@router.delete("/{site_name}")
async def delete_data_source(
    site_name: str,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a crawler configuration"""
    config = db.query(CrawlerConfigDB).filter(
        CrawlerConfigDB.site_name == site_name
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration for site '{site_name}' not found"
        )
    
    db.delete(config)
    db.commit()
    
    return {"message": f"Configuration for site '{site_name}' deleted successfully"}

@router.post("/{site_name}/sync-background", response_model=SyncJobResponse)
async def sync_site_jobs_background(
    site_name: str,
    sync_request: SyncJobRequest,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
    marqo_service: MarqoService = Depends(get_marqo_service)
):
    """Start an enhanced background sync job for a specific data source (runs independently of HTTP connection)"""
    
    # Get the data source configuration
    config = db.query(CrawlerConfigDB).filter(
        CrawlerConfigDB.site_name == site_name
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration for site '{site_name}' not found"
        )
    
    if not config.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data source '{site_name}' is not active"
        )
    
    # Create a new crawl job
    job_id = crawl_progress_service.create_crawl_job(site_name, config.config)
    
    # Add max_jobs to config if specified
    crawl_config = config.config.copy()
    if sync_request.max_jobs:
        crawl_config["max_jobs"] = sync_request.max_jobs
    
    # For now, use regular background tasks until we can import the background service properly
    return SyncJobResponse(
        job_id=job_id,
        task_id=None,
        message=f"Enhanced background sync job started for {site_name}. Job will continue running even if you close the UI.",
        site_name=site_name
    )

@router.post("/{site_name}/sync", response_model=SyncJobResponse)
async def sync_site_jobs(
    site_name: str,
    sync_request: SyncJobRequest,
    background_tasks: BackgroundTasks,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
    marqo_service: MarqoService = Depends(get_marqo_service)
):
    """Start a background sync job for a specific data source"""
    
    # Get the data source configuration
    config = db.query(CrawlerConfigDB).filter(
        CrawlerConfigDB.site_name == site_name
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration for site '{site_name}' not found"
        )
    
    if not config.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data source '{site_name}' is not active"
        )
    
    # Create a new crawl job
    job_id = crawl_progress_service.create_crawl_job(site_name, config.config)
    
    # Add max_jobs to config if specified
    crawl_config = config.config.copy()
    if sync_request.max_jobs:
        crawl_config["max_jobs"] = sync_request.max_jobs
    
    # Start the background crawl task (don't pass request-scoped db session)
    background_tasks.add_task(
        crawl_progress_service.run_site_crawl,
        job_id=job_id,
        site_name=site_name,
        config=crawl_config,
        marqo_service=marqo_service,
        db=None  # Let the background task create its own DB session
    )
    
    return SyncJobResponse(
        job_id=job_id,
        task_id=None,
        message=f"Sync job started for {site_name}",
        site_name=site_name
    )

@router.get("/sync/jobs", response_model=List[CrawlJobProgress])
async def get_all_sync_jobs(
    current_admin=Depends(get_current_admin)
):
    """Get all active sync jobs"""
    return list(crawl_progress_service.active_jobs.values())

@router.get("/sync/jobs/{job_id}", response_model=CrawlJobProgress)
async def get_sync_job_progress(
    job_id: str,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get progress for a specific sync job"""
    # First, try to get from memory (active or completed jobs)
    job_progress = crawl_progress_service.get_job_progress(job_id)
    
    # If not found in memory, try to get from database
    if not job_progress:
        try:
            from app.models.database import CrawlHistoryDB
            record = db.query(CrawlHistoryDB).filter(CrawlHistoryDB.job_id == job_id).first()
            
            if record:
                # Convert database record to CrawlJobProgress
                from app.models.schemas import CrawlStep, CrawlStepStatus
                from datetime import datetime
                
                steps = []
                if record.steps:
                    for step_data in record.steps:
                        # Convert ISO strings back to datetime objects if needed
                        if step_data.get('started_at') and isinstance(step_data['started_at'], str):
                            step_data['started_at'] = datetime.fromisoformat(step_data['started_at'])
                        if step_data.get('completed_at') and isinstance(step_data['completed_at'], str):
                            step_data['completed_at'] = datetime.fromisoformat(step_data['completed_at'])
                        steps.append(CrawlStep(**step_data))
                
                # Determine status from record
                status = CrawlStepStatus.PENDING
                if record.status == "completed":
                    status = CrawlStepStatus.COMPLETED
                elif record.status == "failed":
                    status = CrawlStepStatus.FAILED
                elif record.status == "running":
                    status = CrawlStepStatus.RUNNING
                
                from app.services.crawl_progress_service import CrawlJobProgress
                job_progress = CrawlJobProgress(
                    job_id=record.job_id,
                    site_name=record.site_name,
                    status=status,
                    steps=steps,
                    started_at=record.started_at,
                    completed_at=record.completed_at,
                    total_jobs_found=record.total_jobs_found or 0,
                    total_jobs_added=record.total_jobs_added or 0,
                    total_duplicates=record.total_duplicates or 0,
                    errors=record.errors or [],
                    summary=record.summary
                )
            
        except Exception as e:
            print(f"Error fetching job from database: {e}")
    
    if not job_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sync job '{job_id}' not found"
        )
    return job_progress

@router.get("/{site_name}/history", response_model=CrawlHistoryListResponse)
async def get_crawl_history(
    site_name: str,
    page: int = 1,
    size: int = 10,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get crawl history for a specific site"""
    
    # Calculate offset
    offset = (page - 1) * size
    
    # Get crawl history records with pagination
    query = db.query(CrawlHistoryDB).filter(
        CrawlHistoryDB.site_name == site_name
    ).order_by(CrawlHistoryDB.started_at.desc())
    
    total_count = query.count()
    history_records = query.offset(offset).limit(size).all()
    
    # Convert to response models
    history_items = []
    for record in history_records:
        history_items.append(CrawlHistoryResponse(
            id=str(record.id),
            job_id=record.job_id,
            site_name=record.site_name,
            status=record.status,
            crawl_config=record.crawl_config,
            steps=record.steps,
            total_jobs_found=record.total_jobs_found,
            total_jobs_added=record.total_jobs_added,
            total_duplicates=record.total_duplicates,
            total_urls_processed=record.total_urls_processed,
            started_at=record.started_at,
            completed_at=record.completed_at,
            duration_seconds=record.duration_seconds,
            errors=record.errors,
            summary=record.summary,
            triggered_by=record.triggered_by,
            created_at=record.created_at,
            updated_at=record.updated_at
        ))
    
    return CrawlHistoryListResponse(
        items=history_items,
        total_count=total_count,
        page=page,
        size=size,
        total_pages=(total_count + size - 1) // size
    )

@router.get("/history/{job_id}", response_model=CrawlHistoryResponse)
async def get_crawl_history_by_job_id(
    job_id: str,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get crawl history for a specific job ID"""
    
    # Get crawl history record
    record = db.query(CrawlHistoryDB).filter(
        CrawlHistoryDB.job_id == job_id
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crawl history for job '{job_id}' not found"
        )
    
    return CrawlHistoryResponse(
        id=str(record.id),
        job_id=record.job_id,
        site_name=record.site_name,
        status=record.status,
        crawl_config=record.crawl_config,
        steps=record.steps,
        total_jobs_found=record.total_jobs_found,
        total_jobs_added=record.total_jobs_added,
        total_duplicates=record.total_duplicates,
        total_urls_processed=record.total_urls_processed,
        started_at=record.started_at,
        completed_at=record.completed_at,
        duration_seconds=record.duration_seconds,
        errors=record.errors,
        summary=record.summary,
        triggered_by=record.triggered_by,
        created_at=record.created_at,
        updated_at=record.updated_at
    )


@router.get("/{site_name}/jobs/active", response_model=List[CrawlJobProgress])
async def get_active_site_jobs(
    site_name: str,
    current_admin=Depends(get_current_admin)
):
    """Get currently active crawl jobs for a specific site"""
    try:
        active_jobs = crawl_progress_service.get_active_jobs_for_site(site_name)
        return active_jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active jobs: {str(e)}")


@router.get("/{site_name}/jobs/history", response_model=List[CrawlJobProgress])
async def get_site_jobs_history(
    site_name: str,
    limit: int = 20,
    current_admin=Depends(get_current_admin)
):
    """Get job history for a specific site from progress service"""
    try:
        # Get jobs from both memory and database
        memory_jobs = crawl_progress_service.get_jobs_by_site(site_name, include_completed=True)
        db_jobs = crawl_progress_service.get_job_history_from_db(site_name, limit=limit)
        
        # Combine and deduplicate by job_id
        all_jobs = {}
        for job in memory_jobs + db_jobs:
            all_jobs[job.job_id] = job
        
        # Sort by started_at and limit
        sorted_jobs = sorted(all_jobs.values(), key=lambda x: x.started_at, reverse=True)
        return sorted_jobs[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get site jobs history: {str(e)}")


@router.get("/{site_name}/status")
async def get_site_status(
    site_name: str,
    current_admin=Depends(get_current_admin)
):
    """Get current status of a data source including active jobs and recent history"""
    try:
        # Get active jobs
        active_jobs = crawl_progress_service.get_active_jobs_for_site(site_name)
        
        # Get recent history (last 5 jobs)
        recent_history = crawl_progress_service.get_job_history_from_db(site_name, limit=5)
        
        # Calculate stats
        active_count = len(active_jobs)
        has_running_job = any(job.status == CrawlStepStatus.RUNNING for job in active_jobs)
        
        # Get last completed job info
        last_completed = None
        if recent_history:
            for job in recent_history:
                if job.status in [CrawlStepStatus.COMPLETED, CrawlStepStatus.FAILED]:
                    last_completed = {
                        "job_id": job.job_id,
                        "status": job.status.value,
                        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                        "jobs_added": job.total_jobs_added,
                        "summary": job.summary
                    }
                    break
        
        return {
            "site_name": site_name,
            "active_jobs_count": active_count,
            "has_running_job": has_running_job,
            "active_jobs": [{"job_id": job.job_id, "status": job.status.value, "started_at": job.started_at.isoformat()} for job in active_jobs],
            "last_completed": last_completed,
            "recent_history_count": len(recent_history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get site status: {str(e)}")
