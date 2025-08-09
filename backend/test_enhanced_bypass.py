#!/usr/bin/env python3
"""
Enhanced Top    # Import here to avoid issues if dependencies missing
    try:
        from app.crawlers.topcv_playwright_crawler import TopCVPlaywrightCrawler
        from app.config.topcv_config import TopCVConfig
    except ImportError as e:
        print(f"❌ Failed to import crawler: {e}")
        return
    
    # Configuration using TopCVConfig class
    config = TopCVConfig(
        keywords=['python-developer'],
        max_pages=1,
        max_jobs=10,
        headless=False,
        enable_human_challenge_solving=True,
        challenge_timeout=120
    )with Multiple Cloudflare Bypass Methods
Based on ZenRows blog recommendations: https://www.zenrows.com/blog/bypass-cloudflare

This script demonstrates:
1. Enhanced stealth mode with anti-detection patches
2. FlareSolverr integration (if available)
3. Cloudscraper-style bypass
4. Human-in-the-loop challenge solving (fallback)
"""

import asyncio
import logging
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def test_enhanced_bypass():
    """Test the enhanced TopCV crawler with multiple bypass methods"""
    
    print("🚀 Starting Enhanced TopCV Crawler Test")
    print("=" * 60)
    print("📋 New Features from ZenRows Blog Integration:")
    print("   1. ✨ Enhanced Stealth Mode (removes webdriver properties)")
    print("   2. 🔧 FlareSolverr Integration (automated solver)")
    print("   3. 🌐 Cloudscraper-style Bypass (enhanced headers)")
    print("   4. 👤 Human-in-the-Loop Solving (manual fallback)")
    print("=" * 60)
    print()
    
    # Import here to avoid issues if dependencies missing
    try:
        from app.crawlers.topcv_playwright_crawler import TopCVPlaywrightCrawler
        from app.config.topcv_config import TopCVConfig
    except ImportError as e:
        print(f"❌ Failed to import crawler: {e}")
        return
    
    # Configuration using TopCVConfig class
    config = TopCVConfig(
        search_keywords=['python-developer'],
        max_pages=1,
        headless=False,
        enable_human_challenge_solving=True,
        challenge_timeout=120
    )
    
    print("📋 Test Configuration:")
    print(f"   - search_keywords: {config.search_keywords}")
    print(f"   - max_pages: {config.max_pages}")
    print(f"   - headless: {config.headless}")
    print(f"   - enable_human_challenge_solving: {config.enable_human_challenge_solving}")
    print(f"   - challenge_timeout: {config.challenge_timeout}")
    print()
    
    print("🔄 Bypass Method Priority:")
    print("   1. FlareSolverr (fastest, requires separate service)")
    print("   2. Cloudscraper-style (request-based, fast)")
    print("   3. Human-in-the-loop (manual, most reliable)")
    print()
    
    print("📢 INSTRUCTIONS:")
    print("   1. A browser window will open with enhanced stealth mode")
    print("   2. The crawler will first try automated bypass methods")
    print("   3. If Cloudflare challenge appears, it may solve automatically")
    print("   4. If manual intervention needed, follow the prompts")
    print("   5. Watch the logs to see which bypass method succeeds")
    print("=" * 60)
    
    # Initialize crawler
    try:
        crawler = TopCVPlaywrightCrawler(config)
        print("✅ Enhanced crawler initialized successfully")
        
        # Start crawling
        start_time = datetime.now()
        jobs = await crawler.crawl_jobs()
        end_time = datetime.now()
        
        # Results
        print("=" * 60)
        print("🎉 Enhanced Crawl Test Completed!")
        print(f"⏱️  Duration: {(end_time - start_time).total_seconds():.1f} seconds")
        print(f"📊 Jobs found: {len(jobs)}")
        
        if jobs:
            print("✅ Success! Sample job:")
            sample_job = jobs[0]
            print(f"   - Title: {sample_job.title}")
            print(f"   - Company: {sample_job.company}")
            print(f"   - Location: {sample_job.location}")
            print(f"   - URL: {sample_job.url}")
        else:
            print("⚠️  No jobs found - this could indicate:")
            print("   - All bypass methods were blocked")
            print("   - Challenge solving was incomplete")
            print("   - Page structure has changed")
            print("   - Search returned no results")
            
        print("=" * 60)
        print("💡 Next Steps:")
        print("   1. If FlareSolverr failed, consider installing it:")
        print("      docker run -d -p 8191:8191 flaresolverr/flaresolverr")
        print("   2. The browser window remains open for inspection")
        print("   3. Check logs above to see which bypass method worked")
        print("   4. Enhanced stealth patches are now active by default")
        print("=" * 60)
        print("🖥️  Browser window is still open for your inspection")
        print("   You can manually verify the results or close the browser")
        print("⏳ Press Ctrl+C to exit and close the browser")
        
        # Keep the script running so browser stays open
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Exiting and closing browser...")
            await crawler.close()
            
    except Exception as e:
        print(f"❌ Error during crawling: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_bypass())
