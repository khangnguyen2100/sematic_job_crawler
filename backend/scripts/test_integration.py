"""
Integration test for the sync job feature
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.crawl_progress_service import crawl_progress_service
from app.services.marqo_service import MarqoService
from app.config.topcv_config import TopCVConfig

async def test_full_sync_job():
    """Test the full sync job flow"""
    print("Testing full sync job flow...")
    
    # Create TopCV config
    config = {
        "search_keywords": ["python-developer"],
        "max_pages": 1,
        "request_delay": 1.0,
        "max_jobs": 5,
        "headless": True
    }
    
    # Create a test job
    job_id = crawl_progress_service.create_crawl_job("TopCV", config)
    print(f"Created job ID: {job_id}")
    
    # Note: We're not actually running the full crawl here as it requires browser setup
    # Instead, we'll test the step progression manually
    
    print("Simulating step progression...")
    
    # Step 1: Initialize
    crawl_progress_service.update_step(job_id, "1", "running", "Initializing crawler...")
    await asyncio.sleep(0.5)
    crawl_progress_service.update_step(job_id, "1", "completed", "Crawler initialized successfully")
    
    # Step 2: Check availability
    crawl_progress_service.update_step(job_id, "2", "running", "Checking TopCV availability...")
    await asyncio.sleep(0.5)
    crawl_progress_service.update_step(job_id, "2", "completed", "TopCV is accessible")
    
    # Step 3: Start browser
    crawl_progress_service.update_step(job_id, "3", "running", "Starting browser...")
    await asyncio.sleep(0.5)
    crawl_progress_service.update_step(job_id, "3", "completed", "Browser started successfully")
    
    # Step 4: Generate URLs
    crawl_progress_service.update_step(job_id, "4", "running", "Generating search URLs...")
    await asyncio.sleep(0.5)
    crawl_progress_service.update_step(job_id, "4", "completed", "Generated 5 search URLs", 
                                       details={"url_count": 5})
    
    # Step 5: Crawl jobs (simulate)
    crawl_progress_service.update_step(job_id, "5", "running", "Crawling job listings...")
    await asyncio.sleep(1.0)
    crawl_progress_service.update_step(job_id, "5", "completed", "Found 10 job listings", 
                                       details={"jobs_found": 10})
    crawl_progress_service.update_job_stats(job_id, total_found=10)
    
    # Step 6: Process jobs
    crawl_progress_service.update_step(job_id, "6", "running", "Processing job data...")
    await asyncio.sleep(0.5)
    crawl_progress_service.update_step(job_id, "6", "completed", "Processed 8 valid jobs")
    
    # Step 7: Check duplicates
    crawl_progress_service.update_step(job_id, "7", "running", "Checking for duplicates...")
    await asyncio.sleep(0.5)
    crawl_progress_service.update_step(job_id, "7", "completed", "Found 5 new jobs, 3 duplicates")
    crawl_progress_service.update_job_stats(job_id, total_duplicates=3)
    
    # Step 8: Save jobs (simulate)
    crawl_progress_service.update_step(job_id, "8", "running", "Saving jobs to database...")
    await asyncio.sleep(0.5)
    crawl_progress_service.update_step(job_id, "8", "completed", "Successfully saved 5 jobs")
    crawl_progress_service.update_job_stats(job_id, total_added=5)
    
    # Step 9: Cleanup
    crawl_progress_service.update_step(job_id, "9", "running", "Cleaning up resources...")
    await asyncio.sleep(0.3)
    
    # Set summary
    summary = "Crawl completed successfully! Found 10 jobs, processed 8, identified 5 new jobs, and successfully saved 5 jobs to the database. Skipped 3 duplicate jobs."
    crawl_progress_service.set_job_summary(job_id, summary)
    crawl_progress_service.update_step(job_id, "9", "completed", "Cleanup completed successfully")
    
    # Get final progress
    final_progress = crawl_progress_service.get_job_progress(job_id)
    if final_progress:
        print(f"\nFinal job status: {final_progress.status}")
        print(f"Total jobs found: {final_progress.total_jobs_found}")
        print(f"Total jobs added: {final_progress.total_jobs_added}")
        print(f"Total duplicates: {final_progress.total_duplicates}")
        print(f"Summary: {final_progress.summary}")
        print(f"Completed steps: {sum(1 for step in final_progress.steps if step.status in ['completed', 'skipped'])}/{len(final_progress.steps)}")
    
    print("\nIntegration test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_full_sync_job())
