"""
Test script for TopCV Playwright Crawler
Run this to test the crawler functionality and validate job extraction
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.crawlers.topcv_playwright_crawler import TopCVPlaywrightCrawler
from app.config.topcv_config import TopCVConfig, QUICK_CONFIG, DEFAULT_TOPCV_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_crawler_basic():
    """Test basic crawler functionality"""
    print("🚀 Testing TopCV Playwright Crawler - Basic Test")
    print("=" * 60)
    
    # Use quick config for testing
    config = TopCVConfig(
        search_keywords=["python-developer"],
        max_pages=1,  # Only test 1 page
        request_delay=1.0,
        headless=False,  # Set to True for headless mode
        crawl_company_details=False  # Disable for faster testing
    )
    
    try:
        async with TopCVPlaywrightCrawler(config) as crawler:
            print(f"✅ Browser initialized successfully")
            
            # Test availability
            is_available = await crawler.is_available()
            print(f"📡 TopCV availability: {'✅ Available' if is_available else '❌ Not available'}")
            
            if not is_available:
                print("❌ TopCV is not available, skipping job crawling")
                return
            
            # Test crawling
            print(f"🔍 Starting job crawl (max 5 jobs)...")
            jobs = await crawler.crawl_jobs(max_jobs=5)
            
            print(f"📊 Crawling Results:")
            print(f"   Total jobs found: {len(jobs)}")
            
            # Display job details
            for i, job in enumerate(jobs, 1):
                print(f"\n📋 Job {i}:")
                print(f"   Title: {job.title}")
                print(f"   Company: {job.company_name}")
                print(f"   Location: {job.location}")
                print(f"   Salary: {job.salary}")
                print(f"   URL: {job.original_url}")
                print(f"   Source ID: {job.source_id}")
                print(f"   Description: {job.description[:100]}..." if job.description else "   Description: None")
            
            print(f"\n✅ Basic test completed successfully!")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

async def test_crawler_configuration():
    """Test different crawler configurations"""
    print("\n🔧 Testing Different Configurations")
    print("=" * 60)
    
    configs = [
        ("Quick Config", QUICK_CONFIG),
        ("Default Config", DEFAULT_TOPCV_CONFIG),
        ("Custom Config", TopCVConfig(
            search_keywords=["cong-nghe-thong-tin"],
            max_pages=1,
            request_delay=0.5,
            headless=True
        ))
    ]
    
    for config_name, config in configs:
        print(f"\n🧪 Testing {config_name}:")
        print(f"   Keywords: {config.search_keywords}")
        print(f"   Max pages: {config.max_pages}")
        print(f"   Headless: {config.headless}")
        
        # Generate sample URLs
        urls = config.get_search_urls()
        print(f"   Generated URLs ({len(urls)}):")
        for url in urls[:2]:  # Show first 2 URLs
            print(f"     {url}")
        if len(urls) > 2:
            print(f"     ... and {len(urls) - 2} more")

async def test_url_generation():
    """Test URL generation functionality"""
    print("\n🔗 Testing URL Generation")
    print("=" * 60)
    
    config = TopCVConfig()
    
    # Test individual URL building
    test_cases = [
        ("python-developer", 1, None),
        ("cong-nghe-thong-tin", 2, "257"),
        ("java-developer", 3, None),
    ]
    
    print("Sample URLs:")
    for keyword, page, category in test_cases:
        url = config.build_search_url(keyword, page, category)
        print(f"   {keyword} (page {page}): {url}")
    
    # Test bulk URL generation
    urls = config.get_search_urls()
    print(f"\nTotal URLs generated: {len(urls)}")
    print("First 3 URLs:")
    for url in urls[:3]:
        print(f"   {url}")

def validate_playwright_installation():
    """Check if Playwright is properly installed"""
    print("🔧 Validating Playwright Installation")
    print("=" * 60)
    
    try:
        import playwright
        print(f"✅ Playwright imported successfully")
        
        # Check if browsers are installed
        from playwright.async_api import async_playwright
        print("✅ Playwright async API available")
        
        return True
    except ImportError as e:
        print(f"❌ Playwright not installed: {e}")
        print("💡 Install with: pip install playwright")
        print("💡 Then run: playwright install")
        return False
    except Exception as e:
        print(f"❌ Playwright installation issue: {e}")
        return False

async def main():
    """Main test function"""
    print("🎯 TopCV Playwright Crawler Test Suite")
    print("=" * 60)
    
    # Validate installation
    if not validate_playwright_installation():
        print("\n❌ Playwright is not properly installed. Please install it first.")
        print("Run the following commands:")
        print("1. pip install playwright")
        print("2. playwright install")
        return
    
    # Run tests
    try:
        await test_url_generation()
        await test_crawler_configuration()
        
        # Ask user if they want to run the actual crawling test
        print("\n" + "=" * 60)
        user_input = input("🤔 Do you want to run the actual crawling test? (y/N): ").strip().lower()
        
        if user_input in ['y', 'yes']:
            await test_crawler_basic()
        else:
            print("⏭️  Skipping actual crawling test")
        
        print("\n🎉 All tests completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
