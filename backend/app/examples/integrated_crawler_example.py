"""
Example integration of all three implemented features:
- Issue #6: Job Deduplication System
- Issue #7: Crawl Request Logging System
- Issue #8: Admin Crawl Logs Dashboard (API endpoints)

This example demonstrates how to use all three systems together in a crawler.
"""

import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.schemas import JobCreate, JobSource
from app.services.job_deduplication_service import JobDeduplicationService
from app.services.crawl_logging_service import CrawlLoggingService, CrawlLogger


async def example_crawler_with_integrated_features():
    """
    Example crawler that demonstrates integration of:
    1. Crawl logging (Issue #7)
    2. Job deduplication (Issue #6)
    3. Results viewable in Admin Dashboard (Issue #8)
    """
    
    # Get database session
    db = next(get_db())
    
    # Initialize services
    crawl_logging_service = CrawlLoggingService(db)
    dedup_service = JobDeduplicationService(db)
    
    # Example job data from a crawl
    sample_jobs = [
        JobCreate(
            title="Senior Python Developer",
            description="We are looking for a Senior Python Developer to join our team...",
            company_name="Tech Corp Vietnam",
            posted_date=datetime.now(),
            source=JobSource.TOPCV,
            original_url="https://www.topcv.vn/viec-lam/senior-python-developer/123456.html",
            location="Ho Chi Minh City",
            salary="25-35 million VND",
            job_type="Full-time",
            experience_level="Senior",
            source_id="topcv_123456"  # Important for deduplication
        ),
        JobCreate(
            title="React Frontend Developer",
            description="Join our frontend team to build amazing user interfaces...",
            company_name="StartupXYZ",
            posted_date=datetime.now(),
            source=JobSource.TOPCV,
            original_url="https://www.topcv.vn/viec-lam/react-frontend-developer/789012.html",
            location="Hanoi",
            salary="20-30 million VND",
            job_type="Full-time",
            experience_level="Junior",
            source_id="topcv_789012"
        ),
        # Duplicate job (same content, different source_id)
        JobCreate(
            title="Senior Python Developer",
            description="We are looking for a Senior Python Developer to join our team...",
            company_name="Tech Corp Vietnam",
            posted_date=datetime.now(),
            source=JobSource.TOPCV,
            original_url="https://www.topcv.vn/viec-lam/senior-python-developer-duplicate/999999.html",
            location="Ho Chi Minh City",
            salary="25-35 million VND",
            job_type="Full-time",
            experience_level="Senior",
            source_id="topcv_999999"  # Different source_id but same content
        )
    ]
    
    # Use CrawlLogger context manager for comprehensive logging
    with CrawlLogger(
        crawl_logging_service,
        site_name="TopCV",
        site_url="https://www.topcv.vn",
        request_url="https://www.topcv.vn/tim-viec-lam-cong-nghe-thong-tin",
        crawler_type="topcv_crawler"
    ) as logger:
        
        jobs_found = len(sample_jobs)
        jobs_processed = 0
        jobs_stored = 0
        jobs_duplicated = 0
        
        print(f"🔍 Starting crawl of {jobs_found} jobs from TopCV...")
        
        for job in sample_jobs:
            jobs_processed += 1
            
            # Check for duplicates using deduplication service
            is_new_job, result = await dedup_service.check_and_store_job(job)
            
            if is_new_job:
                jobs_stored += 1
                print(f"✅ New job stored: {job.title} at {job.company_name}")
                print(f"   Job ID: {result}")
            else:
                jobs_duplicated += 1
                print(f"🔄 Duplicate job skipped: {job.title} at {job.company_name}")
                print(f"   Reason: {result}")
        
        # Complete the crawl session with results
        logger.complete(
            response_status=200,
            response_time_ms=2500,  # Simulated response time
            response_size_bytes=1024 * 50,  # Simulated response size (50KB)
            jobs_found=jobs_found,
            jobs_processed=jobs_processed,
            jobs_stored=jobs_stored,
            jobs_duplicated=jobs_duplicated
        )
        
        print(f"\n📊 Crawl completed successfully!")
        print(f"   Jobs found: {jobs_found}")
        print(f"   Jobs processed: {jobs_processed}")
        print(f"   Jobs stored: {jobs_stored}")
        print(f"   Jobs duplicated: {jobs_duplicated}")
    
    # Demonstrate how to view results through the admin dashboard endpoints
    print(f"\n🎛️  Admin Dashboard Integration:")
    print(f"   - View this crawl log: GET /api/v1/admin/crawl-logs")
    print(f"   - Dashboard summary: GET /api/v1/admin/crawl-logs/dashboard/summary")
    print(f"   - Site statistics: GET /api/v1/admin/crawl-logs/statistics/sites")
    
    db.close()


async def example_error_handling():
    """
    Example of how the logging system handles errors
    """
    db = next(get_db())
    crawl_logging_service = CrawlLoggingService(db)
    
    # Simulate a crawler with an error
    with CrawlLogger(
        crawl_logging_service,
        site_name="ITViec",
        site_url="https://itviec.com",
        request_url="https://itviec.com/it-jobs",
        crawler_type="itviec_crawler"
    ) as logger:
        
        # Simulate an error during crawling
        raise Exception("Network timeout while crawling ITViec")
    
    # The error will be automatically logged by the context manager
    print("❌ Error logged automatically by CrawlLogger context manager")
    
    db.close()


if __name__ == "__main__":
    print("🚀 Testing integrated crawler features...")
    print("=" * 60)
    
    # Run successful crawl example
    asyncio.run(example_crawler_with_integrated_features())
    
    print("\n" + "=" * 60)
    print("🔥 Testing error handling...")
    
    # Run error handling example
    try:
        asyncio.run(example_error_handling())
    except Exception as e:
        print(f"Exception handled: {e}")
    
    print("\n✅ All examples completed!")
    print("\n📝 Next steps:")
    print("   1. Start the backend server: uvicorn app.main:app --reload --port 8002")
    print("   2. Access admin dashboard at: http://localhost:3000/admin/crawl-logs")
    print("   3. View API docs at: http://localhost:8002/docs")
