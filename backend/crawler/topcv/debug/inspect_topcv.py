"""
Quick test to inspect TopCV page structure
"""
import asyncio
from playwright.async_api import async_playwright

async def inspect_topcv():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Visit TopCV search page
        url = "https://www.topcv.vn/tim-viec-lam-cong-nghe-thong-tin?type_keyword=1&sba=1&page=1"
        print(f"Visiting: {url}")
        
        await page.goto(url, wait_until='domcontentloaded')
        await page.wait_for_timeout(5000)  # Wait 5 seconds for dynamic content
        
        # Take screenshot
        await page.screenshot(path="topcv_page.png")
        print("Screenshot saved as topcv_page.png")
        
        # Get page content
        content = await page.content()
        with open("topcv_page.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Page content saved as topcv_page.html")
        
        # Try to find job elements with various selectors
        selectors_to_try = [
            ".job-item",
            ".job-list-item", 
            "[data-testid='job-item']",
            ".job-card",
            ".job",
            ".search-result",
            "[class*='job']",
            ".item",
            ".vacancy",
            ".position"
        ]
        
        print("\n--- Checking job element selectors ---")
        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                print(f"✅ {selector}: Found {len(elements)} elements")
            except Exception as e:
                print(f"❌ {selector}: Error - {e}")
        
        # Wait for user input to keep browser open
        input("Press Enter to close browser...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_topcv())
