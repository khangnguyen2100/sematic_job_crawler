#!/usr/bin/env python3
"""
Test script to verify ITViec crawler fixes
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, '/Users/khang.nguyen/WorkSpace/personal/marqo_learning/backend')

from app.crawlers.job_crawlers import ITViecCrawler
from app.models.database import SessionLocal
from app.services.config_service import config_service

async def test_itviec_crawler():
    """Test ITViec crawler with database session"""
    print("🔧 Testing ITViec crawler fixes...")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Test 1: Create ITViec crawler
        print("\n📝 Test 1: Creating ITViec crawler...")
        crawler = ITViecCrawler(db_session=db)
        
        if crawler.config is None:
            print("❌ Config is None - ITViec not configured in database")
            return False
        
        if crawler.crawler_info is None:
            print("❌ Crawler info is None - ITViec not configured in database")
            return False
            
        print("✅ ITViec crawler created successfully")
        print(f"   Site URL: {crawler.crawler_info['site_url']}")
        
        # Test 2: Check availability
        print("\n📝 Test 2: Checking availability...")
        try:
            is_available = await crawler.is_available()
            if is_available:
                print("✅ ITViec is available")
            else:
                print("⚠️  ITViec is not available (might be Cloudflare protection)")
        except Exception as e:
            print(f"❌ Availability check failed: {e}")
            return False
        
        # Test 3: Try crawling (limited)
        print("\n📝 Test 3: Testing job crawling...")
        try:
            jobs = await crawler.crawl_jobs(max_jobs=5)
            print(f"✅ Crawl completed. Found {len(jobs)} jobs")
            
            if jobs:
                print(f"   Sample job: {jobs[0].title} at {jobs[0].company_name}")
            
        except Exception as e:
            print(f"❌ Crawl failed: {e}")
            return False
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_itviec_crawler())
