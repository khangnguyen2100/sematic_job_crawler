#!/usr/bin/env python3
"""
Direct test of TopCV crawler to isolate the 403 error issue
"""
import asyncio
import logging
from app.crawlers.topcv_playwright_crawler import TopCVPlaywrightCrawler
from app.config.topcv_config import TopCVConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_topcv_crawler():
    """Test the TopCV crawler directly"""
    
    # Create configuration with anti-bot settings
    config = TopCVConfig(
        search_keywords=["python-developer"],
        max_pages=1,  # Test with just 1 page
        request_delay=3.0,
        timeout=45,
        headless=False,  # Use visible browser for debugging
        crawl_company_details=False
    )
    
    logger.info("Starting TopCV crawler test...")
    logger.info(f"Config: {config.dict()}")
    
    try:
        async with TopCVPlaywrightCrawler(config) as crawler:
            logger.info("Crawler initialized successfully")
            
            # Test with a small number of jobs
            jobs = await crawler.crawl_jobs(max_jobs=5)
            
            logger.info(f"Crawl completed! Found {len(jobs)} jobs")
            
            if jobs:
                logger.info("Sample jobs:")
                for i, job in enumerate(jobs[:3]):  # Show first 3 jobs
                    logger.info(f"  {i+1}. {job.title} at {job.company_name}")
                    logger.info(f"     URL: {job.original_url}")
            else:
                logger.warning("No jobs found - possible blocking or page structure change")
                
    except Exception as e:
        logger.error(f"Crawler test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_topcv_crawler())
