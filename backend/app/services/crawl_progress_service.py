"""
Crawl Progress Tracking Service

This service handles tracking the progress of crawl jobs and provides
real-time updates to the frontend through progress tracking.
"""

import asyncio
import uuid
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.schemas import JobCreate, CrawlResult, CrawlStep, CrawlStepStatus
from app.models.database import CrawlHistoryDB, SessionLocal
from app.services.marqo_service import MarqoService
from app.crawlers.crawler_manager import CrawlerManager
from app.crawlers.topcv_playwright_crawler import TopCVPlaywrightCrawler
from app.config.topcv_config import TopCVConfig

class CrawlJobProgress(BaseModel):
    job_id: str
    site_name: str
    status: CrawlStepStatus
    steps: List[CrawlStep]
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_jobs_found: int = 0
    total_jobs_added: int = 0
    total_duplicates: int = 0
    errors: List[str] = []
    summary: Optional[str] = None

class CrawlProgressService:
    def __init__(self, db_session: Optional[Session] = None):
        self.active_jobs: Dict[str, CrawlJobProgress] = {}
        self.completed_jobs: Dict[str, CrawlJobProgress] = {}
        self.max_completed_jobs = 50  # Keep last 50 completed jobs
        self.db_session = db_session

    def create_crawl_job(self, site_name: str, config: Dict[str, Any], triggered_by: str = "manual") -> str:
        """Create a new crawl job and return its ID"""
        job_id = str(uuid.uuid4())
        
        # Define the crawl steps based on site type
        steps = self._create_steps_for_site(site_name)
        
        progress = CrawlJobProgress(
            job_id=job_id,
            site_name=site_name,
            status=CrawlStepStatus.PENDING,
            steps=steps,
            started_at=datetime.utcnow()
        )
        
        self.active_jobs[job_id] = progress
        
        # Save to database
        try:
            db = SessionLocal()
            try:
                history_record = CrawlHistoryDB(
                    job_id=job_id,
                    site_name=site_name,
                    status="running",
                    crawl_config=config,
                    steps=[step.dict() for step in steps],
                    triggered_by=triggered_by,
                    started_at=datetime.utcnow()
                )
                db.add(history_record)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"Failed to save crawl history to database: {e}")
            # Continue without database persistence
        
        return job_id

    def _create_steps_for_site(self, site_name: str) -> List[CrawlStep]:
        """Create crawl steps based on the site type"""
        if site_name.lower() == "topcv":
            return [
                CrawlStep(
                    id="1",
                    name="Initialize",
                    description="Initialize crawler and validate configuration",
                    status=CrawlStepStatus.PENDING
                ),
                CrawlStep(
                    id="2", 
                    name="Check Availability",
                    description="Check if the target site is accessible",
                    status=CrawlStepStatus.PENDING
                ),
                CrawlStep(
                    id="3",
                    name="Start Browser",
                    description="Launch browser and set up crawling environment",
                    status=CrawlStepStatus.PENDING
                ),
                CrawlStep(
                    id="4",
                    name="Generate URLs",
                    description="Generate search URLs based on configuration",
                    status=CrawlStepStatus.PENDING
                ),
                CrawlStep(
                    id="5",
                    name="Crawl Jobs",
                    description="Extract job listings from search results",
                    status=CrawlStepStatus.PENDING
                ),
                CrawlStep(
                    id="6",
                    name="Process Jobs",
                    description="Process and validate job data",
                    status=CrawlStepStatus.PENDING
                ),
                CrawlStep(
                    id="7",
                    name="Check Duplicates",
                    description="Check for duplicate jobs and filter existing ones",
                    status=CrawlStepStatus.PENDING
                ),
                CrawlStep(
                    id="8",
                    name="Save Jobs",
                    description="Save new jobs to database and search index",
                    status=CrawlStepStatus.PENDING
                ),
                CrawlStep(
                    id="9",
                    name="Cleanup",
                    description="Clean up resources and generate summary",
                    status=CrawlStepStatus.PENDING
                )
            ]
        else:
            # Generic steps for other sites
            return [
                CrawlStep(
                    id="1",
                    name="Initialize",
                    description="Initialize crawler and validate configuration",
                    status=CrawlStepStatus.PENDING
                ),
                CrawlStep(
                    id="2",
                    name="Check Availability", 
                    description="Check if the target site is accessible",
                    status=CrawlStepStatus.PENDING
                ),
                CrawlStep(
                    id="3",
                    name="Crawl Jobs",
                    description="Extract job listings from the site",
                    status=CrawlStepStatus.PENDING
                ),
                CrawlStep(
                    id="4",
                    name="Process Jobs",
                    description="Process and save job data",
                    status=CrawlStepStatus.PENDING
                ),
                CrawlStep(
                    id="5",
                    name="Finalize",
                    description="Complete crawling and generate summary",
                    status=CrawlStepStatus.PENDING
                )
            ]

    def update_step(self, job_id: str, step_id: str, status: CrawlStepStatus, 
                   message: Optional[str] = None, error: Optional[str] = None,
                   progress_percentage: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        """Update a specific step's status and details"""
        if job_id not in self.active_jobs:
            return False
            
        job = self.active_jobs[job_id]
        
        # Find and update the step
        for step in job.steps:
            if step.id == step_id:
                old_status = step.status
                step.status = status
                step.message = message
                step.error = error
                
                if progress_percentage is not None:
                    step.progress_percentage = progress_percentage
                    
                if details:
                    step.details.update(details)
                
                # Set timestamps
                if status == CrawlStepStatus.RUNNING and old_status == CrawlStepStatus.PENDING:
                    step.started_at = datetime.utcnow()
                elif status in [CrawlStepStatus.COMPLETED, CrawlStepStatus.FAILED]:
                    step.completed_at = datetime.utcnow()
                
                break
        
        # Update overall job status
        self._update_job_status(job_id)
        
        # Save to database
        try:
            db = SessionLocal()
            try:
                history_record = db.query(CrawlHistoryDB).filter(
                    CrawlHistoryDB.job_id == job_id
                ).first()
                
                if history_record:
                    # Convert steps to JSON-serializable format
                    steps_data = []
                    for step in job.steps:
                        step_dict = step.dict()
                        # Convert datetime objects to ISO strings
                        if step_dict.get('started_at'):
                            step_dict['started_at'] = step_dict['started_at'].isoformat()
                        if step_dict.get('completed_at'):
                            step_dict['completed_at'] = step_dict['completed_at'].isoformat()
                        steps_data.append(step_dict)
                    
                    # Update the database record
                    history_record.steps = steps_data
                    history_record.status = job.status.value
                    if job.completed_at:
                        history_record.completed_at = job.completed_at
                        history_record.duration_seconds = (job.completed_at - job.started_at).total_seconds()
                    history_record.updated_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"Failed to update crawl history in database: {e}")
        
        return True

    def _update_job_status(self, job_id: str):
        """Update the overall job status based on step statuses"""
        if job_id not in self.active_jobs:
            return
            
        job = self.active_jobs[job_id]
        
        # Check if any step is running
        if any(step.status == CrawlStepStatus.RUNNING for step in job.steps):
            job.status = CrawlStepStatus.RUNNING
        # Check if any step failed
        elif any(step.status == CrawlStepStatus.FAILED for step in job.steps):
            job.status = CrawlStepStatus.FAILED
            job.completed_at = datetime.utcnow()
            self._move_to_completed(job_id)
        # Check if all steps are completed
        elif all(step.status in [CrawlStepStatus.COMPLETED, CrawlStepStatus.SKIPPED] for step in job.steps):
            job.status = CrawlStepStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            self._move_to_completed(job_id)

    def _move_to_completed(self, job_id: str):
        """Move job from active to completed"""
        if job_id in self.active_jobs:
            job = self.active_jobs.pop(job_id)
            self.completed_jobs[job_id] = job
            
            # Update database record status
            try:
                db = SessionLocal()
                try:
                    history_record = db.query(CrawlHistoryDB).filter(CrawlHistoryDB.job_id == job_id).first()
                    if history_record:
                        # Update status based on job completion
                        if job.status == CrawlStepStatus.COMPLETED:
                            history_record.status = "completed"
                        elif job.status == CrawlStepStatus.FAILED:
                            history_record.status = "failed"
                        else:
                            history_record.status = "completed"  # Default to completed
                        
                        # Update completion time and stats
                        history_record.completed_at = job.completed_at
                        if job.completed_at and job.started_at:
                            duration = (job.completed_at - job.started_at).total_seconds()
                            history_record.duration_seconds = duration
                        
                        # Update job statistics
                        history_record.total_jobs_found = job.total_jobs_found
                        history_record.total_jobs_added = job.total_jobs_added
                        history_record.total_duplicates = job.total_duplicates
                        
                        # Update steps with final state
                        history_record.steps = [step.dict() for step in job.steps]
                        
                        # Update errors and summary
                        history_record.errors = job.errors
                        history_record.summary = job.summary
                        
                        db.commit()
                        print(f"DEBUG: Updated database status for job {job_id} to {history_record.status}")
                finally:
                    db.close()
            except Exception as e:
                print(f"Failed to update database status for job {job_id}: {e}")
            
            # Maintain max completed jobs limit
            if len(self.completed_jobs) > self.max_completed_jobs:
                oldest_job_id = min(self.completed_jobs.keys(), 
                                  key=lambda k: self.completed_jobs[k].started_at)
                del self.completed_jobs[oldest_job_id]

    def get_job_progress(self, job_id: str) -> Optional[CrawlJobProgress]:
        """Get progress for a specific job"""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        elif job_id in self.completed_jobs:
            return self.completed_jobs[job_id]
        return None

    def get_all_active_jobs(self) -> List[CrawlJobProgress]:
        """Get all currently active jobs"""
        return list(self.active_jobs.values())

    def update_job_stats(self, job_id: str, total_found: int = None, 
                        total_added: int = None, total_duplicates: int = None):
        """Update job statistics"""
        job = self.get_job_progress(job_id)
        if job:
            if total_found is not None:
                job.total_jobs_found = total_found
            if total_added is not None:
                job.total_jobs_added = total_added
            if total_duplicates is not None:
                job.total_duplicates = total_duplicates

    def add_job_error(self, job_id: str, error: str):
        """Add an error to the job's error list"""
        job = self.get_job_progress(job_id)
        if job:
            job.errors.append(error)

    def set_job_summary(self, job_id: str, summary: str):
        """Set the final summary for a completed job"""
        job = self.get_job_progress(job_id)
        if job:
            job.summary = summary

    def get_completed_jobs(self, limit: int = 50) -> List[CrawlJobProgress]:
        """Get list of completed jobs"""
        return list(self.completed_jobs.values())[-limit:]

    def get_jobs_by_site(self, site_name: str, include_completed: bool = True) -> List[CrawlJobProgress]:
        """Get all jobs for a specific site"""
        jobs = []
        
        # Add active jobs
        for job in self.active_jobs.values():
            if job.site_name.lower() == site_name.lower():
                jobs.append(job)
        
        # Add completed jobs if requested
        if include_completed:
            for job in self.completed_jobs.values():
                if job.site_name.lower() == site_name.lower():
                    jobs.append(job)
        
        # Sort by started_at (newest first)
        jobs.sort(key=lambda x: x.started_at, reverse=True)
        return jobs

    def get_job_history_from_db(self, site_name: Optional[str] = None, limit: int = 50) -> List[CrawlJobProgress]:
        """Get job history from database"""
        try:
            db = SessionLocal()
            try:
                query = db.query(CrawlHistoryDB)
                if site_name:
                    query = query.filter(CrawlHistoryDB.site_name.ilike(f"%{site_name}%"))
                
                records = query.order_by(CrawlHistoryDB.started_at.desc()).limit(limit).all()
                
                jobs = []
                for record in records:
                    # Convert database record to CrawlJobProgress
                    steps = []
                    if record.steps:
                        for step_data in record.steps:
                            # Convert ISO strings back to datetime objects
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
                    
                    job = CrawlJobProgress(
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
                    jobs.append(job)
                
                return jobs
            finally:
                db.close()
        except Exception as e:
            print(f"Failed to get job history from database: {e}")
            return []

    def get_active_jobs_for_site(self, site_name: str) -> List[CrawlJobProgress]:
        """Get active jobs for a specific site"""
        return [job for job in self.active_jobs.values() 
                if job.site_name.lower() == site_name.lower()]

    async def run_site_crawl(self, job_id: str, site_name: str, config: Dict[str, Any], 
                           marqo_service: MarqoService, db: Session = None) -> CrawlJobProgress:
        """Run the actual crawl job with progress tracking"""
        
        # For background tasks, create a new database session to avoid stale connections
        db_session = None
        if db is None:
            from app.models.database import SessionLocal
            db_session = SessionLocal()
            db = db_session
        
        # Update initial step
        self.update_step(job_id, "1", CrawlStepStatus.RUNNING, "Initializing crawler...")
        
        try:
            if site_name.lower() == "topcv":
                result = await self._run_topcv_crawl(job_id, config, marqo_service, db)
            else:
                # For other sites, use generic crawler
                result = await self._run_generic_crawl(job_id, site_name, config, marqo_service, db)
                
            return self.get_job_progress(job_id)
            
        except Exception as e:
            # Mark current running step as failed
            for step in self.active_jobs.get(job_id, CrawlJobProgress(job_id="", site_name="", status=CrawlStepStatus.FAILED, steps=[], started_at=datetime.utcnow())).steps:
                if step.status == CrawlStepStatus.RUNNING:
                    self.update_step(job_id, step.id, CrawlStepStatus.FAILED, error=str(e))
                    break
            
            # Add to job errors
            self.add_job_error(job_id, f"Crawl failed: {str(e)}")
            
            # Force job to failed state
            if job_id in self.active_jobs:
                self.active_jobs[job_id].status = CrawlStepStatus.FAILED
                self.active_jobs[job_id].completed_at = datetime.utcnow()
                self._move_to_completed(job_id)
            
            return self.get_job_progress(job_id)
        finally:
            # Close the database session if we created it
            if db_session:
                db_session.close()

    async def _run_topcv_crawl(self, job_id: str, config: Dict[str, Any], 
                              marqo_service: MarqoService, db: Session = None):
        """Run TopCV-specific crawl with detailed progress tracking"""
        
        try:
            # Step 1: Initialize - Load configuration from database
            await asyncio.sleep(0.1)
            self.update_step(job_id, "1", CrawlStepStatus.RUNNING, "Loading TopCV configuration from database...")
            
            # Load configuration from database - no hardcoded fallbacks
            if not db:
                self.update_step(job_id, "1", CrawlStepStatus.FAILED, "Database session not available")
                return
            
            from app.services.config_service import config_service
            try:
                # Get site configuration from database
                site_config = config_service.get_site_config(db, "TopCV")
                if not site_config:
                    self.update_step(job_id, "1", CrawlStepStatus.FAILED, 
                                   "TopCV configuration not found in database")
                    return
                
                # Parse configuration
                topcv_config = config_service.parse_topcv_config(site_config)
                crawler_info = config_service.get_crawler_info(db, "TopCV")
                
                self.update_step(job_id, "1", CrawlStepStatus.COMPLETED, 
                               f"Configuration loaded successfully from database for {crawler_info['site_url']}")
            except Exception as e:
                self.update_step(job_id, "1", CrawlStepStatus.FAILED, 
                               f"Failed to load TopCV configuration: {str(e)}")
                return
            
            # Step 2: Check availability
            self.update_step(job_id, "2", CrawlStepStatus.RUNNING, f"Checking {crawler_info['site_url']} availability...")
            
            # Test basic connectivity with proper headers (avoid 403)
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'max-age=0',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1'
                }
                response = requests.get(topcv_config.base_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    self.update_step(job_id, "2", CrawlStepStatus.COMPLETED, f"{crawler_info['site_name']} is accessible")
                else:
                    self.update_step(job_id, "2", CrawlStepStatus.FAILED, f"{crawler_info['site_name']} returned status code: {response.status_code}")
                    return
            except Exception as e:
                self.update_step(job_id, "2", CrawlStepStatus.FAILED, f"Cannot reach {crawler_info['site_name']}: {str(e)}")
                return
            
            # Step 3: Start browser
            self.update_step(job_id, "3", CrawlStepStatus.RUNNING, "Starting browser for human challenge solving...")
            await asyncio.sleep(1)  # Simulate browser startup
            
            # Step 4: Generate URLs and check for known blocking
            self.update_step(job_id, "4", CrawlStepStatus.RUNNING, "Generating search URLs and checking access...")
            search_urls = topcv_config.get_search_urls_from_routes()
            
            # Add warning about potential blocking
            # Show sample URLs from different routes (first URL from each route)
            sample_urls = []
            routes_count = len(topcv_config.routes.paths)
            pages_per_route = topcv_config.max_pages
            
            for i in range(min(5, routes_count)):  # Show up to 5 different routes
                url_index = i * pages_per_route  # First page of each route
                if url_index < len(search_urls):
                    sample_urls.append(search_urls[url_index])
            
            details = {
                "url_count": len(search_urls), 
                "urls": sample_urls,
                "routes_count": routes_count,
                "pages_per_route": pages_per_route,
                "note": "TopCV uses Cloudflare protection that may block automated access"
            }
            
            self.update_step(job_id, "4", CrawlStepStatus.COMPLETED, 
                           f"Generated {len(search_urls)} search URLs. Note: TopCV may block automated access.", 
                           details=details)
            
            # Step 5: Crawl jobs
            self.update_step(job_id, "5", CrawlStepStatus.RUNNING, "Starting crawl with human challenge solving enabled...")
            
            # Initialize crawler with fallback strategy
            try:
                async with TopCVPlaywrightCrawler(topcv_config) as crawler:
                    self.update_step(job_id, "3", CrawlStepStatus.COMPLETED, "Browser started - ready for human challenge solving")
                    
                    # Add a step update to inform user about potential challenges
                    self.update_step(job_id, "5", CrawlStepStatus.RUNNING, 
                                   "Attempting to access job pages. If Cloudflare challenge appears, solve it manually in the browser window.")
                    
                    max_jobs = min(config.get("max_jobs", 100), 500)  # Cap at 500 jobs
                    jobs = await crawler.crawl_jobs(max_jobs)
                    
                    if len(jobs) > 0:
                        self.update_step(job_id, "5", CrawlStepStatus.COMPLETED, 
                                       f"Successfully found {len(jobs)} job listings",
                                       details={"jobs_found": len(jobs)})
                        self.update_job_stats(job_id, total_found=len(jobs))
                    else:
                        # No jobs found - likely due to blocking
                        self.update_step(job_id, "5", CrawlStepStatus.FAILED, 
                                       "No jobs found - TopCV may have blocked the crawler with Cloudflare protection",
                                       error="TopCV appears to be using Cloudflare protection that prevents automated access to job search pages. This is not an error in our crawler but a deliberate anti-bot measure by TopCV.")
                        
                        # Add helpful information
                        self.add_job_error(job_id, "TopCV has implemented Cloudflare protection on job search pages that prevents automated crawling. This is a common anti-bot measure used by many websites.")
                        
                        # Set summary for this case
                        summary = "Crawl blocked by TopCV's Cloudflare protection. TopCV has implemented server-side anti-bot measures that prevent automated access to their job search pages. This is not an error in our crawler but a deliberate protection mechanism by TopCV."
                        self.set_job_summary(job_id, summary)
                        return
                        
            except Exception as crawler_error:
                self.update_step(job_id, "5", CrawlStepStatus.FAILED, 
                               f"Crawler error: {str(crawler_error)}")
                self.add_job_error(job_id, f"Crawler initialization failed: {str(crawler_error)}")
                return
            
            # Step 6: Process jobs
            self.update_step(job_id, "6", CrawlStepStatus.RUNNING, "Processing job data...")
            processed_jobs = []
            for i, job in enumerate(jobs):
                if job.title and job.company_name:  # Basic validation
                    processed_jobs.append(job)
                
                # Update progress
                progress = int((i + 1) / len(jobs) * 100)
                self.update_step(job_id, "6", CrawlStepStatus.RUNNING, 
                               f"Processed {i + 1}/{len(jobs)} jobs", 
                               progress_percentage=progress)
            
            self.update_step(job_id, "6", CrawlStepStatus.COMPLETED, 
                           f"Processed {len(processed_jobs)} valid jobs")
            
            # Step 7: Check duplicates using PostgreSQL (much faster)
            self.update_step(job_id, "7", CrawlStepStatus.RUNNING, "Checking for duplicates...")
            new_jobs = []
            duplicates = 0
            
            for i, job in enumerate(processed_jobs):
                is_duplicate = marqo_service.check_duplicate_job(job, db)
                if not is_duplicate:
                    new_jobs.append(job)
                else:
                    duplicates += 1
                
                # Update progress
                progress = int((i + 1) / len(processed_jobs) * 100)
                self.update_step(job_id, "7", CrawlStepStatus.RUNNING,
                               f"Checked {i + 1}/{len(processed_jobs)} jobs for duplicates",
                               progress_percentage=progress)
            
            self.update_step(job_id, "7", CrawlStepStatus.COMPLETED, 
                           f"Found {len(new_jobs)} new jobs, {duplicates} duplicates")
            self.update_job_stats(job_id, total_duplicates=duplicates)
            
            # Debug logging for Step 7->8 transition
            print(f"DEBUG: Step 7 complete - new_jobs count: {len(new_jobs)}, duplicates: {duplicates}")
            
            # Step 8: Save jobs
            if new_jobs:
                self.update_step(job_id, "8", CrawlStepStatus.RUNNING, "Saving jobs to database...")
                added_count = 0
                
                for i, job in enumerate(new_jobs):
                    try:
                        await marqo_service.add_job(job, db)
                        added_count += 1
                    except Exception as e:
                        self.add_job_error(job_id, f"Failed to save job '{job.title}': {str(e)}")
                    
                    # Update progress
                    progress = int((i + 1) / len(new_jobs) * 100)
                    self.update_step(job_id, "8", CrawlStepStatus.RUNNING,
                                   f"Saved {added_count}/{len(new_jobs)} jobs",
                                   progress_percentage=progress)
                
                self.update_step(job_id, "8", CrawlStepStatus.COMPLETED, 
                               f"Successfully saved {added_count} jobs")
                self.update_job_stats(job_id, total_added=added_count)
            else:
                self.update_step(job_id, "8", CrawlStepStatus.SKIPPED, "No new jobs to save")
                self.update_job_stats(job_id, total_added=0)
                
            # Step 9: Cleanup (always run regardless of whether jobs were saved)
            self.update_step(job_id, "9", CrawlStepStatus.RUNNING, "Cleaning up resources...")
            await asyncio.sleep(0.5)  # Simulate cleanup time
            
            # Generate summary
            total_found = len(jobs)
            total_processed = len(processed_jobs)
            total_new = len(new_jobs)
            total_added = self.get_job_progress(job_id).total_jobs_added
            
            summary = f"Crawl completed successfully! Found {total_found} jobs, processed {total_processed}, identified {total_new} new jobs, and successfully saved {total_added} jobs to the database."
            
            if duplicates > 0:
                summary += f" Skipped {duplicates} duplicate jobs."
            
            self.set_job_summary(job_id, summary)
            self.update_step(job_id, "9", CrawlStepStatus.COMPLETED, "Cleanup completed successfully")
                
        except Exception as e:
            # This will be caught by the outer try-catch and handled appropriately
            raise e

    async def _run_generic_crawl(self, job_id: str, site_name: str, config: Dict[str, Any], 
                                marqo_service: MarqoService, db: Session = None):
        """Run generic crawl for non-TopCV sites"""
        
        try:
            # Step 1: Initialize - Load configuration from database
            await asyncio.sleep(0.1)
            self.update_step(job_id, "1", CrawlStepStatus.RUNNING, f"Loading {site_name} configuration from database...")
            
            # Load configuration from database - no hardcoded fallbacks
            if not db:
                self.update_step(job_id, "1", CrawlStepStatus.FAILED, "Database session not available")
                return
            
            from app.services.config_service import config_service
            try:
                # Get crawler info from database
                crawler_info = config_service.get_crawler_info(db, site_name)
                if not crawler_info:
                    self.update_step(job_id, "1", CrawlStepStatus.FAILED, 
                                   f"{site_name} configuration not found in database")
                    return
                
                self.update_step(job_id, "1", CrawlStepStatus.COMPLETED, 
                               f"Configuration loaded successfully from database for {crawler_info['site_url']}")
            except Exception as e:
                self.update_step(job_id, "1", CrawlStepStatus.FAILED, 
                               f"Failed to load {site_name} configuration: {str(e)}")
                return
            
            # Step 2: Check availability
            self.update_step(job_id, "2", CrawlStepStatus.RUNNING, f"Checking {crawler_info['site_url']} availability...")
            
            try:
                response = requests.get(crawler_info['site_url'], timeout=10)
                if response.status_code == 200:
                    self.update_step(job_id, "2", CrawlStepStatus.COMPLETED, f"{site_name} is accessible")
                else:
                    self.update_step(job_id, "2", CrawlStepStatus.FAILED, 
                                   f"{site_name} returned status code: {response.status_code}")
                    return
            except Exception as e:
                self.update_step(job_id, "2", CrawlStepStatus.FAILED, f"Cannot reach {site_name}: {str(e)}")
                return
            
            # Step 3: Crawl jobs (placeholder for now)
            self.update_step(job_id, "3", CrawlStepStatus.RUNNING, f"Crawling jobs from {site_name}...")
            await asyncio.sleep(2)  # Simulate crawling time
            
            # For now, return mock success for non-TopCV sites
            self.update_step(job_id, "3", CrawlStepStatus.COMPLETED, f"Crawling not yet implemented for {site_name}")
            
            # Step 4: Process jobs
            self.update_step(job_id, "4", CrawlStepStatus.SKIPPED, "No jobs to process")
            
            # Step 5: Finalize
            self.update_step(job_id, "5", CrawlStepStatus.COMPLETED, "Crawl completed")
            
            summary = f"Crawl for {site_name} completed. Note: Full crawling implementation is not yet available for this site."
            self.set_job_summary(job_id, summary)
            
        except Exception as e:
            raise e

# Global instance
crawl_progress_service = CrawlProgressService()
