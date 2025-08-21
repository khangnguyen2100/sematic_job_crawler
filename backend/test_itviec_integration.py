#!/usr/bin/env python3
"""
Integration test for ITViec crawler implementation
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.config.itviec_config import ITViecConfig, ITViecParams
from app.crawlers.itviec_playwright_crawler import ITViecPlaywrightCrawler

async def test_itviec_integration():
    """Test ITViec crawler with real website"""
    
    print("🚀 Starting ITViec Integration Test")
    print("=" * 50)
    
    # Create test configuration
    config = ITViecConfig(
        base_url="https://itviec.com",
        max_pages=2,  # Limit to 2 pages for testing
        request_delay=3.0,
        timeout=60,
        headless=False,  # Keep visible for manual challenge solving
        enable_human_challenge_solving=True,
        challenge_timeout=180
    )
    
    print(f"📋 Configuration:")
    print(f"   Base URL: {config.base_url}")
    print(f"   Max Pages: {config.max_pages}")
    print(f"   Request Delay: {config.request_delay}s")
    print(f"   Timeout: {config.timeout}s")
    print(f"   Headless: {config.headless}")
    print()
    
    try:
        # Test the crawler
        async with ITViecPlaywrightCrawler(config) as crawler:
            print("✅ Crawler initialized successfully")
            
            # Test availability check
            is_available = await crawler.is_available()
            print(f"🌐 ITViec availability: {'✅ Available' if is_available else '❌ Not available'}")
            
            if not is_available:
                print("⚠️ ITViec appears to be unavailable. Continuing with crawler test anyway...")
            
            print()
            print("🔍 Starting job crawling...")
            print("   (This may take a few minutes, especially if Cloudflare challenges appear)")
            print("   Please solve any challenges that appear in the browser window")
            print()
            
            # Crawl jobs
            jobs = await crawler.crawl_jobs(max_jobs=20)  # Limit to 20 jobs for testing
            
            print("=" * 50)
            print(f"📊 CRAWLING RESULTS")
            print("=" * 50)
            print(f"Total jobs extracted: {len(jobs)}")
            print()
            
            if jobs:
                print("🎯 Sample Jobs:")
                print("-" * 40)
                
                for i, job in enumerate(jobs[:5], 1):  # Show first 5 jobs
                    print(f"{i}. {job.title}")
                    print(f"   Company: {job.company_name}")
                    print(f"   Location: {job.location}")
                    print(f"   Salary: {job.salary}")
                    print(f"   Experience: {job.experience_level}")
                    print(f"   URL: {job.original_url}")
                    print(f"   Source ID: {job.source_id}")
                    print()
                
                if len(jobs) > 5:
                    print(f"... and {len(jobs) - 5} more jobs")
                
                print()
                print("✅ ITViec crawler test completed successfully!")
                
                # Verify job data quality
                quality_check = {
                    "has_title": sum(1 for job in jobs if job.title and job.title.strip()),
                    "has_company": sum(1 for job in jobs if job.company_name and job.company_name.strip()),
                    "has_url": sum(1 for job in jobs if job.original_url and job.original_url.strip()),
                    "has_location": sum(1 for job in jobs if job.location),
                    "has_salary": sum(1 for job in jobs if job.salary),
                    "has_source_id": sum(1 for job in jobs if job.source_id)
                }
                
                print("📈 Data Quality Check:")
                print(f"   Jobs with title: {quality_check['has_title']}/{len(jobs)} ({quality_check['has_title']/len(jobs)*100:.1f}%)")
                print(f"   Jobs with company: {quality_check['has_company']}/{len(jobs)} ({quality_check['has_company']/len(jobs)*100:.1f}%)")
                print(f"   Jobs with URL: {quality_check['has_url']}/{len(jobs)} ({quality_check['has_url']/len(jobs)*100:.1f}%)")
                print(f"   Jobs with location: {quality_check['has_location']}/{len(jobs)} ({quality_check['has_location']/len(jobs)*100:.1f}%)")
                print(f"   Jobs with salary: {quality_check['has_salary']}/{len(jobs)} ({quality_check['has_salary']/len(jobs)*100:.1f}%)")
                print(f"   Jobs with source ID: {quality_check['has_source_id']}/{len(jobs)} ({quality_check['has_source_id']/len(jobs)*100:.1f}%)")
                
            else:
                print("❌ No jobs were extracted. This could be due to:")
                print("   - Cloudflare protection blocking access")
                print("   - Changes in ITViec website structure")
                print("   - Network issues")
                print("   - Rate limiting")
                print()
                print("💡 Try running the test again or check the crawler selectors")
                
    except Exception as e:
        print(f"❌ Error during crawler test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("ITViec Crawler Integration Test")
    print("===============================")
    print()
    
    # Run the test
    result = asyncio.run(test_itviec_integration())
    
    if result:
        print()
        print("🎉 Test completed!")
        print("Next steps:")
        print("1. Update database configuration for ITViec")
        print("2. Test the crawler with the full system")
        print("3. Monitor crawler performance in production")
    else:
        print()
        print("💥 Test failed!")
        print("Please check the errors above and fix any issues")
        sys.exit(1)
