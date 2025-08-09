#!/usr/bin/env python3
"""
Test simpler TopCV URLs to bypass Cloudflare protection
"""
import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simple_urls():
    """Test different TopCV URL patterns"""
    
    test_urls = [
        "https://www.topcv.vn/",
        "https://www.topcv.vn/tim-viec-lam",
        "https://www.topcv.vn/tim-viec-lam?keyword=python",
        "https://www.topcv.vn/tim-viec-lam-python",
        "https://www.topcv.vn/viec-lam-it",
        "https://www.topcv.vn/viec-lam-cong-nghe-thong-tin"
    ]
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1366, 'height': 768},
        extra_http_headers={
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
    )
    
    page = await context.new_page()
    
    for url in test_urls:
        logger.info(f"\n=== Testing URL: {url} ===")
        try:
            response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            status = response.status
            title = await page.title()
            
            logger.info(f"Status: {status}")
            logger.info(f"Title: {title}")
            
            if status == 200 and "just a moment" not in title.lower():
                # Look for job elements
                await asyncio.sleep(2)
                
                # Try different selectors for job listings
                selectors = [
                    '.job-item-search-result',
                    '.job-item',
                    '.job-list-item', 
                    '[data-job-id]',
                    '.result-job-item',
                    'a[href*="/viec-lam/"]',
                    'a[href*="/tuyen-dung/"]'
                ]
                
                for selector in selectors:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        logger.info(f"✅ Found {len(elements)} elements with selector: {selector}")
                        
                        # Get sample job titles
                        for i, element in enumerate(elements[:3]):
                            try:
                                text = await element.text_content()
                                href = await element.get_attribute('href')
                                logger.info(f"  {i+1}. {text[:50]}... | {href}")
                            except:
                                pass
                        break
                else:
                    logger.info("❌ No job elements found with any selector")
            else:
                logger.warning(f"⚠️  Potential blocking: status={status}, title contains challenge")
                
        except Exception as e:
            logger.error(f"❌ Failed to access {url}: {e}")
    
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_simple_urls())
