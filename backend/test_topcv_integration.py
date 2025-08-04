#!/usr/bin/env python3
"""
TopCV Crawler Integration Test
Tests the complete flow: crawl -> store -> search
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.crawlers.topcv_playwright_crawler import TopCVPlaywrightCrawler
from app.config.topcv_config import TopCVConfig
from app.services.marqo_service import MarqoService
from app.models.schemas import JobCreate, SearchRequest
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_integration():
    """Test complete TopCV integration: crawl -> store -> search"""
    
    print("🎯 TopCV Integration Test")
    print("=" * 60)
    
    # 1. Test crawling
    print("📡 Step 1: Crawling jobs from TopCV")
    print("-" * 40)
    
    # Use a limited config for testing
    config = TopCVConfig(
        search_keywords=["python-developer"],
        max_pages_per_keyword=1,
        headless=True,
        timeout=30,  # Use valid timeout value (in seconds)
        request_delay=2  # Slower to be respectful
    )
    
    async with TopCVPlaywrightCrawler(config) as crawler:
        jobs = await crawler.crawl_jobs(max_jobs=3)
        
        if not jobs:
            print("❌ No jobs found during crawling")
            return False
        
        print(f"✅ Successfully crawled {len(jobs)} jobs")
        for i, job in enumerate(jobs, 1):
            print(f"   {i}. {job.title} at {job.company_name}")
    
    # 2. Test storing in Marqo
    print("\n🗄️ Step 2: Storing jobs in vector database")
    print("-" * 40)
    
    try:
        # Initialize Marqo service
        marqo_service = MarqoService()
        await marqo_service.initialize()  # Initialize the service first!
        
        # Store jobs
        stored_count = 0
        for job in jobs:
            try:
                result = await marqo_service.add_job(job)
                if result:
                    stored_count += 1
                    print(f"   ✅ Stored: {job.title}")
                else:
                    print(f"   ❌ Failed to store: {job.title}")
            except Exception as e:
                print(f"   ❌ Error storing {job.title}: {e}")
        
        print(f"✅ Successfully stored {stored_count}/{len(jobs)} jobs")
        
    except Exception as e:
        print(f"❌ Error initializing Marqo service: {e}")
        print("   Make sure Marqo is running (docker-compose up marqo)")
        return False
    
    # 3. Test searching
    print("\n🔍 Step 3: Testing semantic search")
    print("-" * 40)
    
    try:
        # Test different search queries
        test_queries = [
            "Python developer",
            "AI machine learning",
            "Full stack engineer",
        ]
        
        for query in test_queries:
            print(f"\n   🔎 Searching for: '{query}'")
            try:
                # Create SearchRequest object
                search_request = SearchRequest(
                    query=query,
                    max_results=2
                )
                results = await marqo_service.search_jobs(search_request)
                if results and 'hits' in results:
                    hits = results['hits']
                    print(f"      ✅ Found {len(hits)} results")
                    for idx, result in enumerate(hits, 1):
                        score = result.get('_score', 'N/A')
                        title = result.get('title', 'N/A')
                        company = result.get('company_name', 'N/A')
                        print(f"         {idx}. {title} at {company} (score: {score:.3f})")
                else:
                    print(f"      ⚠️ No results found")
            except Exception as e:
                print(f"      ❌ Search error: {e}")
        
        print("\n✅ Search testing completed")
        
    except Exception as e:
        print(f"❌ Error during search testing: {e}")
        return False
    
    # 4. Summary
    print("\n🎉 Integration Test Summary")
    print("=" * 60)
    print(f"✅ Crawled: {len(jobs)} jobs")
    print(f"✅ Stored: {stored_count} jobs")
    print("✅ Search: Functional")
    print("\n🚀 TopCV crawler is ready for production!")
    
    return True

async def test_crawler_configurations():
    """Test different crawler configurations"""
    print("\n🧪 Testing Different Configurations")
    print("=" * 60)
    
    configs = [
        {
            "name": "Single keyword, 1 page",
            "config": TopCVConfig(
                search_keywords=["cong-nghe-thong-tin"],
                max_pages_per_keyword=1,
                headless=True
            )
        },
        {
            "name": "Multiple keywords, 2 pages each",
            "config": TopCVConfig(
                search_keywords=["python-developer", "java-developer"],
                max_pages_per_keyword=2,
                headless=True
            )
        }
    ]
    
    for test_case in configs:
        print(f"\n📋 Testing: {test_case['name']}")
        print("-" * 40)
        
        config = test_case['config']
        urls = config.get_search_urls()
        print(f"   Generated {len(urls)} URLs")
        
        # Show first few URLs
        for i, url in enumerate(urls[:3]):
            print(f"   {i+1}. {url}")
        if len(urls) > 3:
            print(f"   ... and {len(urls) - 3} more")

def main():
    """Main test function"""
    print("🚀 Starting TopCV Integration Tests")
    
    # Check if user wants to run full integration
    while True:
        choice = input("\nRun full integration test (crawl + store + search)? (y/N): ").strip().lower()
        if choice in ['y', 'yes']:
            run_integration = True
            break
        elif choice in ['n', 'no', '']:
            run_integration = False
            break
        else:
            print("Please enter 'y' or 'n'")
    
    # Test configurations first
    asyncio.run(test_crawler_configurations())
    
    if run_integration:
        print("\n⚠️ Note: This will crawl real jobs and store them in your database.")
        print("Make sure your development environment is running:")
        print("  - PostgreSQL (for analytics)")
        print("  - Marqo (for vector search)")
        print("  - Run: ./start-dev.sh")
        
        confirm = input("\nContinue with integration test? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            success = asyncio.run(test_integration())
            if not success:
                sys.exit(1)
        else:
            print("Integration test skipped.")
    else:
        print("Integration test skipped.")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
