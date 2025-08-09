#!/usr/bin/env python3
"""
Test TopCV crawler with human-in-the-loop challenge solving
"""
import asyncio
import logging
from app.crawlers.topcv_playwright_crawler import TopCVPlaywrightCrawler
from app.config.topcv_config import TopCVConfig

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_human_challenge_solving():
    """Test the TopCV crawler with human challenge solving"""
    
    # Create configuration for human-in-the-loop mode
    config = TopCVConfig(
        search_keywords=["python-developer"],
        max_pages=1,  # Start with just 1 page
        request_delay=2.0,
        timeout=60,
        headless=False,  # Visible browser for human interaction
        enable_human_challenge_solving=True,
        challenge_timeout=120,  # 2 minutes to solve challenge
        crawl_company_details=False
    )
    
    logger.info("🚀 Starting TopCV crawler with human-in-the-loop challenge solving")
    logger.info("📋 Configuration:")
    logger.info(f"   - Keywords: {config.search_keywords}")
    logger.info(f"   - Max pages: {config.max_pages}")
    logger.info(f"   - Headless: {config.headless}")
    logger.info(f"   - Challenge timeout: {config.challenge_timeout}s")
    logger.info("")
    logger.info("📢 INSTRUCTIONS:")
    logger.info("   1. A browser window will open")
    logger.info("   2. If you see a Cloudflare challenge, solve it manually")
    logger.info("   3. The crawler will detect when you've solved it and continue")
    logger.info("   4. You can watch the automated crawling process")
    logger.info("=" * 60)
    
    try:
        async with TopCVPlaywrightCrawler(config) as crawler:
            logger.info("✅ Crawler initialized successfully")
            
            # Test with a small number of jobs
            jobs = await crawler.crawl_jobs(max_jobs=10)
            
            logger.info("=" * 60)
            logger.info(f"🎉 Crawl completed! Found {len(jobs)} jobs")
            
            if jobs:
                logger.info("📄 Sample jobs found:")
                for i, job in enumerate(jobs[:5]):  # Show first 5 jobs
                    logger.info(f"   {i+1}. {job.title}")
                    logger.info(f"      Company: {job.company_name}")
                    logger.info(f"      Location: {job.location or 'Not specified'}")
                    logger.info(f"      URL: {job.original_url}")
                    logger.info("")
                    
                if len(jobs) > 5:
                    logger.info(f"   ... and {len(jobs) - 5} more jobs")
            else:
                logger.warning("❌ No jobs found")
                logger.info("💡 This could mean:")
                logger.info("   - Cloudflare challenge was not solved")
                logger.info("   - Page structure has changed")
                logger.info("   - Search returned no results")
                
            logger.info("=" * 60)
            logger.info("🖥️  Browser window is still open for your inspection")
            logger.info("   You can manually verify the results or close the browser")
            
            # Keep the script running so browser stays open
            logger.info("⏳ Press Ctrl+C to exit and close the browser")
            try:
                while True:
                    await asyncio.sleep(10)
            except KeyboardInterrupt:
                logger.info("👋 Exiting...")
                
    except Exception as e:
        logger.error(f"❌ Crawler test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test_human_challenge_solving())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
