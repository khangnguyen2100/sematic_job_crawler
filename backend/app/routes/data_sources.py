"""
Data Source Configuration Management API

This module provides CRUD operations for managing crawler configurations,
including site domains, parameters, and other crawler-specific settings.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.database import get_db, CrawlerConfigDB
from app.services.auth_service import get_current_admin
from app.models.schemas import JobSource
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
    max_jobs: Optional[int] = 100

class SyncJobResponse(BaseModel):
    job_id: str
    message: str
    site_name: str

@router.get("/", response_model=List[CrawlerConfigResponse])
async def get_all_data_sources(
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all crawler configurations"""
    configs = db.query(CrawlerConfigDB).all()
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
    """Get configuration for a specific site"""
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
    config_data: CrawlerConfigUpdate,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update configuration for a specific site"""
    config = db.query(CrawlerConfigDB).filter(
        CrawlerConfigDB.site_name == site_name
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration for site '{site_name}' not found"
        )
    
    # Update fields if provided
    if config_data.site_name is not None:
        config.site_name = config_data.site_name
    if config_data.site_url is not None:
        config.site_url = config_data.site_url
    if config_data.config is not None:
        config.config = config_data.config
    if config_data.is_active is not None:
        config.is_active = config_data.is_active
    
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
    """Delete configuration for a specific site"""
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

@router.get("/{site_name}/test", response_model=Dict[str, Any])
async def test_data_source(
    site_name: str,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Test connectivity to a data source"""
    config = db.query(CrawlerConfigDB).filter(
        CrawlerConfigDB.site_name == site_name
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration for site '{site_name}' not found"
        )
    
    # Enhanced connectivity test with proper headers and user agent
    import requests
    try:
        # Use realistic browser headers to avoid anti-bot detection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Get timeout from config if available, default to 10 seconds
        timeout = 10
        if hasattr(config, 'config') and config.config:
            config_dict = config.config if isinstance(config.config, dict) else {}
            timeout = config_dict.get('timeout', 10)
        
        response = requests.get(
            config.site_url, 
            headers=headers,
            timeout=timeout,
            allow_redirects=True
        )
        
        # Consider 2xx and 3xx as successful (redirects are common)
        is_available = 200 <= response.status_code < 400
        
        return {
            "site_name": config.site_name,
            "site_url": config.site_url,
            "is_available": is_available,
            "status_code": response.status_code,
            "response_time_ms": int(response.elapsed.total_seconds() * 1000),
            "tested_at": datetime.utcnow().isoformat(),
            "final_url": response.url,  # Show if there were redirects
            "note": "Using realistic browser headers to avoid anti-bot detection"
        }
    except Exception as e:
        return {
            "site_name": config.site_name,
            "site_url": config.site_url,
            "is_available": False,
            "error": str(e),
            "tested_at": datetime.utcnow().isoformat(),
            "note": "Test failed - this may be due to anti-bot protection or network issues"
        }

@router.post("/bulk-create", response_model=List[CrawlerConfigResponse])
async def bulk_create_data_sources(
    configs: List[CrawlerConfigCreate],
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create multiple crawler configurations at once"""
    created_configs = []
    errors = []
    
    for config_data in configs:
        try:
            # Check if site already exists
            existing = db.query(CrawlerConfigDB).filter(
                CrawlerConfigDB.site_name == config_data.site_name
            ).first()
            
            if existing:
                errors.append(f"Site '{config_data.site_name}' already exists")
                continue
            
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
            
            created_configs.append(CrawlerConfigResponse(
                id=str(new_config.id),
                site_name=new_config.site_name,
                site_url=new_config.site_url,
                config=new_config.config,
                is_active=new_config.is_active,
                created_at=new_config.created_at,
                updated_at=new_config.updated_at
            ))
            
        except Exception as e:
            errors.append(f"Error creating config for '{config_data.site_name}': {str(e)}")
    
    if errors and not created_configs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors, "created": []}
        )
    
    return created_configs

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
    
    # Start the background crawl task
    background_tasks.add_task(
        crawl_progress_service.run_site_crawl,
        job_id=job_id,
        site_name=site_name,
        config=crawl_config,
        marqo_service=marqo_service,
        db=db
    )
    
    return SyncJobResponse(
        job_id=job_id,
        message=f"Sync job started for {site_name}",
        site_name=site_name
    )

@router.get("/sync/jobs", response_model=List[CrawlJobProgress])
async def get_all_sync_jobs(
    current_admin=Depends(get_current_admin)
):
    """Get all active sync jobs"""
    return crawl_progress_service.get_all_active_jobs()

@router.get("/sync/jobs/{job_id}", response_model=CrawlJobProgress)
async def get_sync_job_progress(
    job_id: str,
    current_admin=Depends(get_current_admin)
):
    """Get progress for a specific sync job"""
    progress = crawl_progress_service.get_job_progress(job_id)
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sync job '{job_id}' not found"
        )
    
    return progress
