#!/usr/bin/env python3
"""
Test human-like navigation to TopCV job pages
"""
import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_human_navigation():
    """Test navigating like a human user through TopCV"""
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,  # Use visible browser
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-web-security'
        ]
    )
    
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1366, 'height': 768}
    )
    
    # Remove webdriver property
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
    """)
    
    page = await context.new_page()
    
    try:
        logger.info("Step 1: Visit homepage and wait")
        response = await page.goto("https://www.topcv.vn", wait_until='domcontentloaded')
        logger.info(f"Homepage status: {response.status}")
        
        # Wait and scroll like a human
        await asyncio.sleep(3)
        await page.evaluate("window.scrollTo(0, 500)")
        await asyncio.sleep(2)
        
        logger.info("Step 2: Look for job search links or forms")
        
        # Try to find job search elements on homepage
        search_selectors = [
            'input[placeholder*="tìm kiếm"]',
            'input[placeholder*="search"]', 
            'input[name="keyword"]',
            '.search-input',
            '#search-input',
            'a[href*="tim-viec-lam"]',
            'a[href*="viec-lam"]'
        ]
        
        found_element = None
        for selector in search_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                logger.info(f"Found {len(elements)} elements with selector: {selector}")
                found_element = elements[0]
                
                # If it's a link, click it
                if selector.startswith('a['):
                    logger.info("Clicking job search link...")
                    await found_element.click()
                    await asyncio.sleep(5)  # Wait for navigation
                    
                    current_url = page.url
                    title = await page.title()
                    logger.info(f"Current URL: {current_url}")
                    logger.info(f"Current title: {title}")
                    
                    if "just a moment" not in title.lower():
                        logger.info("✅ Successfully navigated to job search page!")
                        
                        # Look for job listings
                        await asyncio.sleep(3)
                        job_elements = await page.query_selector_all('.job-item-search-result, .job-item, [data-job-id]')
                        logger.info(f"Found {len(job_elements)} job elements")
                        
                        if job_elements:
                            for i, job in enumerate(job_elements[:3]):
                                try:
                                    text = await job.text_content()
                                    logger.info(f"Job {i+1}: {text[:80]}...")
                                except:
                                    pass
                    else:
                        logger.warning("❌ Still got Cloudflare challenge after navigation")
                    
                    break
                    
                # If it's an input, try searching
                elif selector.startswith('input'):
                    logger.info("Found search input, trying to search...")
                    await found_element.fill("python developer")
                    await asyncio.sleep(1)
                    
                    # Look for search button
                    search_buttons = await page.query_selector_all('button[type="submit"], .search-btn, .btn-search')
                    if search_buttons:
                        await search_buttons[0].click()
                        await asyncio.sleep(5)
                        
                        current_url = page.url
                        title = await page.title()
                        logger.info(f"Search result URL: {current_url}")
                        logger.info(f"Search result title: {title}")
                        
                        if "just a moment" not in title.lower():
                            logger.info("✅ Successfully searched for jobs!")
                            job_elements = await page.query_selector_all('.job-item-search-result, .job-item, [data-job-id]')
                            logger.info(f"Found {len(job_elements)} job elements")
                        else:
                            logger.warning("❌ Search triggered Cloudflare challenge")
                    break
        
        if not found_element:
            logger.warning("❌ Could not find any job search elements on homepage")
            
    except Exception as e:
        logger.error(f"Navigation test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Keep browser open for manual inspection
        logger.info("Keeping browser open for 30 seconds for manual inspection...")
        await asyncio.sleep(30)
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_human_navigation())
