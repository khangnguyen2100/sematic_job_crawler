#!/usr/bin/env python3
"""
Test TopCV website access and analyze blocking mechanisms
"""
import asyncio
import logging
from playwright.async_api import async_playwright
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_topcv_access():
    """Test different ways to access TopCV"""
    
    # Test 1: Basic requests library
    logger.info("=== Test 1: Basic requests library ===")
    try:
        response = requests.get("https://www.topcv.vn", timeout=10)
        logger.info(f"Requests status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
    except Exception as e:
        logger.error(f"Requests failed: {e}")
    
    # Test 2: Enhanced requests with headers
    logger.info("\n=== Test 2: Enhanced requests with headers ===")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
        response = requests.get("https://www.topcv.vn", headers=headers, timeout=10)
        logger.info(f"Enhanced requests status: {response.status_code}")
    except Exception as e:
        logger.error(f"Enhanced requests failed: {e}")
    
    # Test 3: Playwright homepage access
    logger.info("\n=== Test 3: Playwright homepage access ===")
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1366, 'height': 768}
        )
        page = await context.new_page()
        
        response = await page.goto("https://www.topcv.vn", wait_until='domcontentloaded', timeout=30000)
        logger.info(f"Playwright homepage status: {response.status}")
        
        # Get page title
        title = await page.title()
        logger.info(f"Page title: {title}")
        
        # Test search URL directly
        logger.info("\n=== Test 4: Direct search URL access ===")
        search_url = "https://www.topcv.vn/tim-viec-lam-python-developer"
        response = await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
        logger.info(f"Search page status: {response.status}")
        
        title = await page.title()
        logger.info(f"Search page title: {title}")
        
        # Check if we can find job elements
        await asyncio.sleep(2)
        job_elements = await page.query_selector_all('.job-item-search-result')
        logger.info(f"Found {len(job_elements)} job elements")
        
        # Try alternative selectors
        if not job_elements:
            alternative_selectors = [
                '.job-item',
                '[data-job-id]',
                '.job-list-item',
                '.result-job-item'
            ]
            for selector in alternative_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    break
        
        await browser.close()
        await playwright.stop()
        
    except Exception as e:
        logger.error(f"Playwright test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_topcv_access())
