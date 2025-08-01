from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import os
from datetime import datetime

from app.services.marqo_service import MarqoService
from app.crawlers.crawler_manager import CrawlerManager

class JobScheduler:
    def __init__(self, marqo_service: MarqoService):
        self.scheduler = AsyncIOScheduler()
        self.marqo_service = marqo_service
        self.crawler_manager = CrawlerManager(marqo_service)
        self.is_running = False
        
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            return
            
        # Schedule crawling jobs
        # Default: every day at 00:00 and 12:00
        cron_schedule = os.getenv("CRAWL_SCHEDULE_CRON", "0 0,12 * * *")
        
        self.scheduler.add_job(
            func=self._crawl_all_jobs,
            trigger=CronTrigger.from_crontab(cron_schedule),
            id='crawl_all_jobs',
            name='Crawl all job sources',
            replace_existing=True
        )
        
        # Add a manual trigger for testing (every 5 minutes in development)
        if os.getenv("DEBUG", "False").lower() == "true":
            self.scheduler.add_job(
                func=self._crawl_sample_jobs,
                trigger=CronTrigger(minute="*/30"),  # Every 30 minutes for testing
                id='crawl_sample_jobs',
                name='Crawl sample jobs (development)',
                replace_existing=True
            )
        
        self.scheduler.start()
        self.is_running = True
        print("Job scheduler started successfully")
        
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            print("Job scheduler shut down")
    
    async def _crawl_all_jobs(self):
        """Scheduled task to crawl all job sources"""
        try:
            print(f"Starting scheduled crawl at {datetime.now()}")
            max_jobs_per_source = int(os.getenv("MAX_JOBS_PER_SOURCE", "100"))
            
            results = await self.crawler_manager.crawl_all_sources(max_jobs_per_source)
            
            print(f"Scheduled crawl completed:")
            print(f"  Total crawled: {results['total_crawled']}")
            print(f"  Total added: {results['total_added']}")
            print(f"  Duplicates skipped: {results['duplicates_skipped']}")
            
            if results['errors']:
                print(f"  Errors: {len(results['errors'])}")
                for error in results['errors'][:5]:  # Show first 5 errors
                    print(f"    - {error}")
                    
        except Exception as e:
            print(f"Error in scheduled crawl: {e}")
    
    async def _crawl_sample_jobs(self):
        """Scheduled task to crawl a few sample jobs (for development)"""
        try:
            print(f"Starting sample crawl at {datetime.now()}")
            
            # Crawl just a few jobs from each source for testing
            results = await self.crawler_manager.crawl_all_sources(max_jobs_per_source=5)
            
            print(f"Sample crawl completed: {results['total_added']} jobs added")
                    
        except Exception as e:
            print(f"Error in sample crawl: {e}")
    
    async def trigger_manual_crawl(self):
        """Manually trigger a crawl job"""
        try:
            print("Manual crawl triggered")
            max_jobs_per_source = int(os.getenv("MAX_JOBS_PER_SOURCE", "50"))
            
            results = await self.crawler_manager.crawl_all_sources(max_jobs_per_source)
            return results
            
        except Exception as e:
            print(f"Error in manual crawl: {e}")
            return {"error": str(e)}
    
    def get_scheduler_status(self):
        """Get scheduler status and job information"""
        if not self.is_running:
            return {"status": "stopped"}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "status": "running",
            "jobs": jobs
        }
