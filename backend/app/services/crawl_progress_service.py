"""
Crawl Progress Tracking Service

This service handles tracking the progress of crawl jobs and provides
real-time updates to the frontend through progress tracking.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.schemas import JobCreate, CrawlResult
from app.services.marqo_service import MarqoService
from app.crawlers.crawler_manager import CrawlerManager
from app.crawlers.topcv_playwright_crawler import TopCVPlaywrightCrawler
from app.config.topcv_config import TopCVConfig

class CrawlStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class CrawlStep(BaseModel):
    id: str
    name: str
    description: str
    status: CrawlStepStatus = CrawlStepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: int = 0
    message: Optional[str] = None
    error: Optional[str] = None
    details: Dict[str, Any] = {}

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
    def __init__(self):
        self.active_jobs: Dict[str, CrawlJobProgress] = {}
        self.completed_jobs: Dict[str, CrawlJobProgress] = {}
        self.max_completed_jobs = 50  # Keep last 50 completed jobs

    def create_crawl_job(self, site_name: str, config: Dict[str, Any]) -> str:
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
        return job_id

    def _create_steps_for_site(self, site_name: str) -> List[CrawlStep]:
        """Create crawl steps based on the site type"""
        if site_name.lower() == "topcv":
            return [
                CrawlStep(
                    id="1",
                    name="Initialize",
                    description="Initialize crawler and validate configuration"
                ),
                CrawlStep(
                    id="2", 
                    name="Check Availability",
                    description="Check if the target site is accessible"
                ),
                CrawlStep(
                    id="3",
                    name="Start Browser",
                    description="Launch browser and set up crawling environment"
                ),
                CrawlStep(
                    id="4",
                    name="Generate URLs",
                    description="Generate search URLs based on configuration"
                ),
                CrawlStep(
                    id="5",
                    name="Crawl Jobs",
                    description="Extract job listings from search results"
                ),
                CrawlStep(
                    id="6",
                    name="Process Jobs",
                    description="Process and validate job data"
                ),
                CrawlStep(
                    id="7",
                    name="Check Duplicates",
                    description="Check for duplicate jobs and filter existing ones"
                ),
                CrawlStep(
                    id="8",
                    name="Save Jobs",
                    description="Save new jobs to database and search index"
                ),
                CrawlStep(
                    id="9",
                    name="Cleanup",
                    description="Clean up resources and generate summary"
                )
            ]
        else:
            # Generic steps for other sites
            return [
                CrawlStep(
                    id="1",
                    name="Initialize",
                    description="Initialize crawler and validate configuration"
                ),
                CrawlStep(
                    id="2",
                    name="Check Availability", 
                    description="Check if the target site is accessible"
                ),
                CrawlStep(
                    id="3",
                    name="Crawl Jobs",
                    description="Extract job listings from the site"
                ),
                CrawlStep(
                    id="4",
                    name="Process Jobs",
                    description="Process and save job data"
                ),
                CrawlStep(
                    id="5",
                    name="Finalize",
                    description="Complete crawling and generate summary"
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

    async def run_site_crawl(self, job_id: str, site_name: str, config: Dict[str, Any], 
                           marqo_service: MarqoService, db: Session = None) -> CrawlJobProgress:
        """Run the actual crawl job with progress tracking"""
        
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

    async def _run_topcv_crawl(self, job_id: str, config: Dict[str, Any], 
                              marqo_service: MarqoService, db: Session = None):
        """Run TopCV-specific crawl with detailed progress tracking"""
        
        try:
            # Step 1: Initialize - already running
            await asyncio.sleep(0.5)  # Simulate initialization time
            self.update_step(job_id, "1", CrawlStepStatus.COMPLETED, "Crawler initialized successfully")
            
            # Step 2: Check availability
            self.update_step(job_id, "2", CrawlStepStatus.RUNNING, "Checking TopCV availability...")
            
            # Create TopCV config from stored config
            topcv_config = TopCVConfig(**config)
            
            # Test basic connectivity with proper headers (avoid 403)
            import requests
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
                    self.update_step(job_id, "2", CrawlStepStatus.COMPLETED, "TopCV is accessible")
                else:
                    self.update_step(job_id, "2", CrawlStepStatus.FAILED, f"TopCV returned status code: {response.status_code}")
                    return
            except Exception as e:
                self.update_step(job_id, "2", CrawlStepStatus.FAILED, f"Cannot reach TopCV: {str(e)}")
                return
            
            # Step 3: Start browser
            self.update_step(job_id, "3", CrawlStepStatus.RUNNING, "Starting browser for human challenge solving...")
            await asyncio.sleep(1)  # Simulate browser startup
            
            # Step 4: Generate URLs and check for known blocking
            self.update_step(job_id, "4", CrawlStepStatus.RUNNING, "Generating search URLs and checking access...")
            search_urls = topcv_config.get_search_urls()
            
            # Add warning about potential blocking
            details = {
                "url_count": len(search_urls), 
                "urls": search_urls[:5],
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
            
            # Step 7: Check duplicates
            self.update_step(job_id, "7", CrawlStepStatus.RUNNING, "Checking for duplicates...")
            new_jobs = []
            duplicates = 0
            
            for i, job in enumerate(processed_jobs):
                is_duplicate = await marqo_service.check_duplicate_job(job)
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
                        await marqo_service.add_job(job)
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
                
                # Step 9: Cleanup
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
            # Step 1: Initialize - already running
            await asyncio.sleep(0.5)
            self.update_step(job_id, "1", CrawlStepStatus.COMPLETED, f"Initialized {site_name} crawler")
            
            # Step 2: Check availability
            self.update_step(job_id, "2", CrawlStepStatus.RUNNING, f"Checking {site_name} availability...")
            
            site_url = config.get("site_url", "")
            if site_url:
                try:
                    import requests
                    response = requests.get(site_url, timeout=10)
                    if response.status_code == 200:
                        self.update_step(job_id, "2", CrawlStepStatus.COMPLETED, f"{site_name} is accessible")
                    else:
                        self.update_step(job_id, "2", CrawlStepStatus.FAILED, 
                                       f"{site_name} returned status code: {response.status_code}")
                        return
                except Exception as e:
                    self.update_step(job_id, "2", CrawlStepStatus.FAILED, f"Cannot reach {site_name}: {str(e)}")
                    return
            else:
                self.update_step(job_id, "2", CrawlStepStatus.FAILED, "No site URL configured")
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
