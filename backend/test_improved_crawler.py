#!/usr/bin/env python3
"""
Test the improved crawl progress service with better error handling
"""
import asyncio
import logging
from app.services.crawl_progress_service import crawl_progress_service
from app.config.topcv_config import TopCVConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_improved_crawler():
    """Test the improved crawler with better error handling"""
    
    # Create a test job
    config = {
        "search_keywords": ["python-developer"],
        "max_pages": 1,
        "request_delay": 3.0,
        "timeout": 45,
        "headless": True,
        "crawl_company_details": False
    }
    
    job_id = crawl_progress_service.create_crawl_job("TopCV", config)
    logger.info(f"Created test job: {job_id}")
    
    # Run the crawl (this will likely fail due to Cloudflare)
    try:
        result = await crawl_progress_service.run_site_crawl(
            job_id, "TopCV", config, None, None
        )
        
        logger.info("Crawl completed!")
        logger.info(f"Job status: {result.status}")
        logger.info(f"Summary: {result.summary}")
        
        if result.errors:
            logger.info("Errors:")
            for error in result.errors:
                logger.info(f"  - {error}")
                
        # Print step details
        logger.info("\nStep details:")
        for step in result.steps:
            logger.info(f"  {step.id}. {step.name}: {step.status}")
            if step.message:
                logger.info(f"     Message: {step.message}")
            if step.error:
                logger.info(f"     Error: {step.error}")
                
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_improved_crawler())
