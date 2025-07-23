from fastapi import APIRouter, Depends, HTTPException, Request, Query
from typing import List, Optional

from app.models.schemas import Job, JobSource
from app.services.marqo_service import MarqoService
from app.services.analytics_service import AnalyticsService  
from app.models.database import get_db
from app.utils.user_tracking import get_user_id

router = APIRouter()

def get_marqo_service():
    from app.main import marqo_service
    return marqo_service

def get_analytics_service():
    return AnalyticsService()

@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    request: Request,
    marqo_service: MarqoService = Depends(get_marqo_service),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    db = Depends(get_db)
):
    """Get a specific job by ID"""
    try:
        job = await marqo_service.get_job_by_id(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Track job view
        user_id = get_user_id(request)
        analytics_service.track_user_interaction(
            db=db,
            user_id=user_id,
            job_id=job_id,
            action="view",
            metadata={"source": job.source.value}
        )
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")

@router.post("/jobs/{job_id}/click")
async def track_job_click(
    job_id: str,
    request: Request,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    db = Depends(get_db)
):
    """Track when a user clicks on a job to go to external site"""
    try:
        user_id = get_user_id(request)
        
        # Track click interaction
        success = analytics_service.track_user_interaction(
            db=db,
            user_id=user_id,
            job_id=job_id,
            action="click",
            metadata={"timestamp": request.headers.get("timestamp")}
        )
        
        if success:
            return {"message": "Click tracked successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to track click")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track click: {str(e)}")

@router.get(
    "/",
    response_model=list[Job],
    summary="📋 Get All Jobs",
    description="Retrieve all jobs from the database with optional filtering",
    response_description="List of all available job postings",
    tags=["jobs"]
)
async def get_jobs(
    skip: int = Query(0, ge=0, description="Number of jobs to skip for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of jobs to return"),
    source: Optional[str] = Query(None, description="Filter by job source (e.g., 'linkedin', 'topcv')"),
    db = Depends(get_db)
):
    """
    ## Get All Jobs
    
    Retrieve all job postings with optional pagination and filtering.
    
    ### Parameters:
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of jobs to return (1-500)
    - **source**: Filter by specific job platform
    
    ### Available Sources:
    - `linkedin` - LinkedIn job postings
    - `topcv` - TopCV Vietnam jobs
    - `itviec` - ITViec tech jobs
    - `vietnamworks` - VietnamWorks general jobs
    """

@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    marqo_service: MarqoService = Depends(get_marqo_service)
):
    """Delete a job (admin endpoint)"""
    try:
        success = await marqo_service.delete_job(job_id)
        
        if success:
            return {"message": "Job deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Job not found or could not be deleted")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")

@router.get("/jobs/stats")
async def get_jobs_stats(
    marqo_service: MarqoService = Depends(get_marqo_service)
):
    """Get statistics about the job database"""
    try:
        stats = await marqo_service.get_index_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
