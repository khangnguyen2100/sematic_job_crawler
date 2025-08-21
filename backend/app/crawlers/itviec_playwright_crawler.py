"""
ITViec Crawler using Playwright with configurable parameters and pagination support
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import re
import httpx
import json
import random

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

from app.models.schemas import JobCreate, JobSource
from app.crawlers.base_crawler import BaseCrawler
from app.config.itviec_config import ITViecConfig

logger = logging.getLogger(__name__)

class ITViecPlaywrightCrawler(BaseCrawler):
    """Advanced ITViec crawler using Playwright with full configuration support"""
    
    def __init__(self, config: ITViecConfig):
        super().__init__("ITViec")
        if not config:
            raise ValueError("ITViec configuration is required")
        self.config = config
        self.playwright: Optional[Any] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.logger = logging.getLogger(__name__)
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._init_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_browser()
    
    async def _init_browser(self) -> None:
        """Initialize browser with enhanced stealth settings and anti-detection measures"""
        try:
            self.logger.info("Launching browser with advanced anti-detection measures for ITViec")
            
            # Get playwright instance
            self.playwright = await async_playwright().start()
            
            # Enhanced stealth arguments based on ZenRows recommendations
            stealth_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-extensions-file-access-check',
                '--disable-extensions',
                '--disable-plugins-discovery',
                '--disable-web-security',
                '--allow-running-insecure-content',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--no-zygote',
                '--disable-gpu',
                '--hide-scrollbars',
                '--mute-audio',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--window-size=1920,1080'
            ]
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.headless,
                args=stealth_args
            )
            
            # Create context with enhanced fingerprinting resistance
            self.context = await self.browser.new_context(
                viewport=self.config.viewport,
                user_agent=self.config.user_agent,
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0'
                }
            )
            
            self.page = await self.context.new_page()
            
            # Apply advanced stealth patches
            await self._apply_stealth_patches()
            
            self.logger.info("Browser initialized with advanced anti-detection measures for ITViec")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def _apply_stealth_patches(self) -> None:
        """Apply stealth patches to hide automation traces"""
        try:
            # Remove webdriver property (Method from ZenRows blog)
            await self.page.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Remove automation indicators
                delete window.navigator.__proto__.webdriver;
                
                // Mock chrome property
                window.chrome = {
                    runtime: {},
                };
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'vi'],
                });
                
                // Hide automation properties
                const originalQuery = window.document.querySelector;
                window.document.querySelector = function(selector) {
                    if (selector === 'img[src*="data:image/png;base64"]') {
                        return null;
                    }
                    return originalQuery.call(document, selector);
                };
            """)
            
        except Exception as e:
            self.logger.warning(f"Failed to apply stealth patches: {e}")

    async def _try_flaresolverr_bypass(self, url: str) -> Optional[str]:
        """
        Try to bypass Cloudflare using FlareSolverr as fallback
        Based on Method #1 from ZenRows blog
        """
        try:
            flaresolverr_url = "http://localhost:8191/v1"  # Default FlareSolverr endpoint
            
            payload = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60000,
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            self.logger.info(f"🔧 Attempting FlareSolverr bypass for {url}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(flaresolverr_url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "ok":
                        self.logger.info("✅ FlareSolverr bypass successful")
                        return result["solution"]["response"]
                    else:
                        self.logger.warning(f"❌ FlareSolverr failed: {result.get('message', 'Unknown error')}")
                        return None
                else:
                    self.logger.warning(f"❌ FlareSolverr request failed with status {response.status_code}")
                    return None
                    
        except Exception as e:
            self.logger.warning(f"❌ FlareSolverr bypass failed: {e}")
            return None
    
    async def _try_cloudscraper_bypass(self, url: str) -> Optional[str]:
        """
        Try to bypass Cloudflare using cloudscraper technique
        Based on Method #1 from ZenRows blog
        """
        try:
            self.logger.info(f"🔧 Attempting cloudscraper-style bypass for {url}")
            
            # Enhanced headers that mimic a real browser more closely
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Cache-Control': 'max-age=0'
            }
            
            async with httpx.AsyncClient(
                headers=headers,
                timeout=30.0,
                follow_redirects=True,
                verify=False  # Disable SSL verification
            ) as client:
                # First, visit the homepage to establish session
                homepage_response = await client.get(self.config.base_url)
                
                # Small delay to mimic human behavior
                await asyncio.sleep(random.uniform(1, 3))
                
                # Now try the target URL
                response = await client.get(url)
                
                if response.status_code == 200 and "Cloudflare" not in response.text:
                    self.logger.info("✅ Cloudscraper-style bypass successful")
                    return response.text
                else:
                    self.logger.warning(f"❌ Cloudscraper-style bypass failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            self.logger.warning(f"❌ Cloudscraper-style bypass failed: {e}")
            return None
    
    async def _solve_cloudflare_challenge(self, page: Page, max_wait_time: int = 120) -> bool:
        """
        Wait for human to solve Cloudflare challenge manually
        Returns True if challenge is solved, False if timeout
        """
        self.logger.info("🔒 Cloudflare challenge detected!")
        self.logger.info("📢 PLEASE SOLVE THE CHALLENGE MANUALLY IN THE BROWSER WINDOW")
        self.logger.info("   - Look for CAPTCHA, checkbox, or verification button")
        self.logger.info("   - Complete any required verification")
        self.logger.info(f"   - Waiting up to {max_wait_time} seconds for you to solve it...")
        
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < max_wait_time:
            try:
                # Check if we're still on a challenge page
                current_title = await page.title()
                current_url = page.url
                
                # Common Cloudflare challenge indicators
                if all([
                    "just a moment" not in current_title.lower(),
                    "checking your browser" not in current_title.lower(),
                    "verify you are human" not in current_title.lower(),
                    "cloudflare" not in current_title.lower()
                ]):
                    # Additional check: look for actual content
                    await asyncio.sleep(2)  # Let page settle
                    
                    # Check if we can find job-related content
                    content_indicators = [
                        '.job',
                        '.job-item',
                        '.job-card',
                        'input[placeholder*="search"]',
                        'h1, h2, h3'  # Any heading content
                    ]
                    
                    for selector in content_indicators:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            logger.info("✅ Challenge appears to be solved! Found page content.")
                            return True
                    
                    # If no job content but title changed, likely solved
                    if current_url != "about:blank" and len(current_title) > 10:
                        logger.info("✅ Challenge solved! Page title and URL changed.")
                        return True
                
                # Still on challenge page, wait a bit more
                await asyncio.sleep(3)
                
                # Show progress to user
                elapsed = int(asyncio.get_event_loop().time() - start_time)
                remaining = max_wait_time - elapsed
                if elapsed % 10 == 0:  # Show message every 10 seconds
                    logger.info(f"⏳ Still waiting for challenge solution... {remaining}s remaining")
                
            except Exception as e:
                logger.warning(f"Error checking challenge status: {e}")
                await asyncio.sleep(3)
        
        logger.error("❌ Timeout waiting for challenge solution")
        return False
    
    async def _close_browser(self) -> None:
        """Close browser and cleanup resources"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            self.logger.info("Browser closed successfully")
        except Exception as e:
            self.logger.warning(f"Error closing browser: {e}")
    
    async def crawl_jobs(self, max_jobs: int = 100) -> List[JobCreate]:
        """Crawl jobs from ITViec with pagination support"""
        jobs = []
        
        try:
            # Get search URLs
            search_urls = self.config.get_priority_search_urls(max_pages=3)  # Start with priority URLs
            
            self.logger.info(f"🚀 Starting ITViec crawl with {len(search_urls)} URLs, targeting max {max_jobs} jobs")
            
            for url_index, url in enumerate(search_urls):
                if len(jobs) >= max_jobs:
                    self.logger.info(f"✅ Reached target of {max_jobs} jobs")
                    break
                
                self.logger.info(f"📄 Crawling page {url_index + 1}/{len(search_urls)}: {url}")
                
                # Crawl single page
                page_jobs = await self._crawl_single_page(self.page, url, url_index)
                
                if page_jobs:
                    jobs.extend(page_jobs)
                    self.logger.info(f"✅ Extracted {len(page_jobs)} jobs from page {url_index + 1}")
                else:
                    self.logger.warning(f"❌ No jobs found on page {url_index + 1}")
                
                # Delay between pages
                delay = self.config.request_delay + random.uniform(0.5, 2.0)
                self.logger.info(f"⏱️ Waiting {delay:.1f}s before next page...")
                await asyncio.sleep(delay)
                
        except Exception as e:
            self.logger.error(f"Error in crawl_jobs: {e}")
        
        self.logger.info(f"🎯 ITViec crawl completed: {len(jobs)} total jobs extracted")
        return jobs[:max_jobs]  # Ensure we don't exceed max_jobs
    
    async def _crawl_single_page(self, page: Page, url: str, url_index: int) -> List[JobCreate]:
        """Crawl a single page and extract job listings"""
        jobs = []
        
        try:
            logger.info(f"Navigating to: {url}")
            
            # Add random mouse movements and delays before navigation
            await asyncio.sleep(0.5 + (0.5 * asyncio.get_event_loop().time() % 1))
            
            # Set referrer for more natural browsing pattern
            referrer = None
            if url_index > 0:
                referrer = f"{self.config.base_url}/"
            
            # Navigate to page with enhanced options
            response = await page.goto(
                url, 
                wait_until='domcontentloaded', 
                timeout=self.config.timeout * 1000,
                referer=referrer
            )
            
            # Check response status and handle Cloudflare challenges
            if response and response.status == 403:
                logger.error(f"403 Forbidden received for {url}")
                
                # Check if it's a Cloudflare challenge page
                await asyncio.sleep(2)  # Let page load completely
                page_content = await page.content()
                page_title = await page.title()
                
                logger.info(f"Page title: '{page_title}'")
                logger.info(f"Page URL: {page.url}")
                
                # More comprehensive challenge detection
                challenge_indicators = [
                    "just a moment",
                    "checking your browser", 
                    "verify you are human",
                    "cloudflare",
                    "challenge",
                    "security check",
                    "please wait"
                ]
                
                is_challenge_page = any(indicator in page_title.lower() for indicator in challenge_indicators)
                has_challenge_content = any(indicator in page_content.lower() for indicator in challenge_indicators)
                
                if is_challenge_page or has_challenge_content or len(page_title.strip()) < 5:
                    logger.info("🔒 Detected potential Cloudflare challenge page")
                    
                    # Multi-method bypass approach based on ZenRows recommendations
                    bypass_successful = False
                    
                    # Method 1: Try FlareSolverr bypass first (fastest if available)
                    if not bypass_successful:
                        flare_content = await self._try_flaresolverr_bypass(url)
                        if flare_content:
                            logger.info("✅ FlareSolverr bypass successful, parsing content")
                            soup = BeautifulSoup(flare_content, 'html.parser')
                            extracted_jobs = await self._extract_jobs_from_soup(soup, url)
                            if extracted_jobs:
                                jobs.extend(extracted_jobs)
                                bypass_successful = True
                    
                    # Method 2: Try cloudscraper-style bypass
                    if not bypass_successful:
                        scraper_content = await self._try_cloudscraper_bypass(url)
                        if scraper_content:
                            logger.info("✅ Cloudscraper bypass successful, parsing content")
                            soup = BeautifulSoup(scraper_content, 'html.parser')
                            extracted_jobs = await self._extract_jobs_from_soup(soup, url)
                            if extracted_jobs:
                                jobs.extend(extracted_jobs)
                                bypass_successful = True
                    
                    # Method 3: Fall back to human-in-the-loop challenge solving
                    if not bypass_successful:
                        challenge_solved = await self._solve_cloudflare_challenge(page, max_wait_time=self.config.challenge_timeout)
                        
                        if challenge_solved:
                            logger.info("✅ Challenge solved! Continuing with crawling...")
                            # Continue with normal crawling flow below
                        else:
                            logger.error("❌ Could not solve Cloudflare challenge within timeout")
                            return jobs
                    else:
                        # One of the bypass methods worked, return the jobs
                        return jobs
                else:
                    logger.error("403 error but not a Cloudflare challenge - possibly blocked")
                    logger.info("💡 Try manually navigating to the URL in the browser to see what's happening")
                    # Keep page open for manual inspection
                    logger.info("🖥️  Browser page will stay open for manual inspection...")
                    await asyncio.sleep(30)  # Keep page open for 30 seconds
                    return jobs
                
            elif response and response.status != 200:
                logger.error(f"HTTP {response.status} received for {url}")
                return jobs
            
            # Human-like behavior: random mouse movement
            await page.mouse.move(
                x=100 + (200 * (asyncio.get_event_loop().time() % 1)),
                y=100 + (200 * (asyncio.get_event_loop().time() % 1))
            )
            
            # Wait for job listings to load
            try:
                await page.wait_for_selector('.job', timeout=10000)
            except:
                # Try alternative selectors
                try:
                    await page.wait_for_selector('[data-job-id]', timeout=5000)
                except:
                    logger.warning("No job listings found with expected selectors")
            
            # Get page content and extract jobs
            page_content = await page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Extract jobs from the page
            extracted_jobs = await self._extract_jobs(soup, url)
            jobs.extend(extracted_jobs)
            
        except Exception as e:
            logger.error(f"Error crawling single page {url}: {e}")
        
        return jobs
    
    async def _solve_cloudflare_challenge(self, page: Page, max_wait_time: int = 180) -> bool:
        """
        Wait for human to solve Cloudflare challenge manually
        Returns True if challenge is solved, False if timeout
        """
        self.logger.info("🔒 Cloudflare challenge detected!")
        self.logger.info("📢 PLEASE SOLVE THE CHALLENGE MANUALLY IN THE BROWSER WINDOW")
        self.logger.info("   - Look for CAPTCHA, checkbox, or verification button")
        self.logger.info("   - Complete any required verification")
        self.logger.info(f"   - Waiting up to {max_wait_time} seconds for you to solve it...")
        
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < max_wait_time:
            try:
                # Check if we're still on a challenge page
                current_title = await page.title()
                current_url = page.url
                
                # Common Cloudflare challenge indicators
                if all([
                    "just a moment" not in current_title.lower(),
                    "checking your browser" not in current_title.lower(),
                    "verify you are human" not in current_title.lower(),
                    "cloudflare" not in current_title.lower()
                ]):
                    # Additional check: look for actual content
                    await asyncio.sleep(2)  # Let page settle
                    
                    # Check if we can find job-related content
                    content_indicators = [
                        '.job',
                        '[data-job-id]',
                        '.job-item',
                        'h1, h2, h3'  # Any heading content
                    ]
                    
                    for selector in content_indicators:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            logger.info("✅ Challenge appears to be solved! Found page content.")
                            return True
                
                # Wait a bit before checking again
                await asyncio.sleep(3)
                
                # Print progress every 30 seconds
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed % 30 < 3:  # Print roughly every 30 seconds
                    remaining = max_wait_time - elapsed
                    logger.info(f"⏳ Still waiting for challenge solution... {remaining:.0f}s remaining")
                
            except Exception as e:
                logger.warning(f"Error checking challenge status: {e}")
                await asyncio.sleep(5)
        
        logger.error(f"❌ Timeout waiting for challenge solution after {max_wait_time}s")
        return False
    
    async def _extract_jobs_from_soup(self, soup: BeautifulSoup, source_url: str) -> List[JobCreate]:
        """Alias for _extract_jobs to maintain consistency with bypass methods"""
        return await self._extract_jobs(soup, source_url)

    async def _extract_jobs(self, soup: BeautifulSoup, source_url: str) -> List[JobCreate]:
        """Extract jobs from ITViec page content"""
        jobs = []
        
        try:
            # ITViec job listing selectors (updated for current website structure)
            job_selectors = [
                '.job-card',  # Main job container (current structure)
                '[data-job-key]',  # Alternative selector with job key
                '.job-item'  # Legacy fallback selector
            ]
            
            job_elements = []
            for selector in job_selectors:
                job_elements = soup.select(selector)
                if job_elements:
                    self.logger.info(f"Found {len(job_elements)} job elements with selector '{selector}'")
                    break
            
            if not job_elements:
                self.logger.warning("No job elements found with any selector")
                return jobs
            
            for job_element in job_elements:
                try:
                    job = await self._extract_single_job(job_element, source_url)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    self.logger.warning(f"Error extracting single job: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error extracting jobs: {e}")
        
        return jobs
    
    async def _extract_single_job(self, job_element, source_url: str) -> Optional[JobCreate]:
        """Extract job data from a single job element"""
        try:
            # Extract basic information
            title = self._extract_title(job_element)
            company_name = self._extract_company_name(job_element)
            original_url = self._extract_job_url(job_element)
            
            self.logger.debug(f"Extracted: title='{title}', company='{company_name}', url='{original_url}'")
            
            if not all([title, company_name, original_url]):
                self.logger.warning(f"Missing required fields: title={title}, company={company_name}, url={original_url}")
                return None
            
            # Extract additional information
            location = self._extract_location(job_element)
            salary = self._extract_salary(job_element)
            job_type = self._extract_job_type(job_element)
            posted_date = self._extract_posted_date(job_element)
            description = self._extract_description(job_element)
            experience_level = self._extract_experience_level(job_element)
            
            # Create job object
            job = JobCreate(
                title=title.strip(),
                description=description or f"Position: {title} at {company_name}",
                company_name=company_name.strip(),
                posted_date=posted_date or datetime.utcnow(),
                source=JobSource.ITVIEC,
                original_url=self._make_absolute_url(original_url),
                location=location,
                salary=salary,
                job_type=job_type or "Full-time",
                experience_level=experience_level,
                source_id=self._extract_source_id(original_url)
            )
            
            return job
            
        except Exception as e:
            logger.error(f"Error extracting job data: {e}")
            return None
    
    def _extract_title(self, element) -> Optional[str]:
        """Extract job title using ITViec structure"""
        selectors = [
            'h3',  # Main title in h3 tag
            'h3 a',  # Title link within h3
            '[data-search--job-selection-target="jobTitle"]',  # Data attribute
            '.job-title a',  # Legacy fallback
            '.title a',  # Legacy fallback
            '[data-testid="job-title"]',  # Legacy fallback
        ]
        
        for selector in selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title:  # Make sure it's not empty
                    return title
        
        return None
    
    def _extract_company_name(self, element) -> Optional[str]:
        """Extract company name using ITViec structure"""
        selectors = [
            'a[href*="/companies/"]',  # Main company link
            '.company-name',  # Legacy fallback
            '.company a',  # Legacy fallback
            '.company',  # Legacy fallback
            '[data-testid="company-name"]',  # Legacy fallback
            '.employer-name'  # Legacy fallback
        ]
        
        for selector in selectors:
            company_elems = element.select(selector)  # Use select() to get all matches
            for company_elem in company_elems:
                company = company_elem.get_text(strip=True)
                if company:  # Return the first non-empty match
                    return company
        
        return None
    
    def _extract_job_url(self, element) -> Optional[str]:
        """Extract job URL using ITViec structure"""
        selectors = [
            'h3 a',  # Main title link
            'a[href*="/it-jobs/"]',  # ITViec job URL
            '.job-title a',  # Legacy fallback
            'a[href*="/jobs/"]'  # Legacy fallback
        ]
        
        for selector in selectors:
            url_elem = element.select_one(selector)
            if url_elem and url_elem.get('href'):
                href = url_elem.get('href')
                if href.startswith('/'):
                    return f"https://itviec.com{href}"
                return href
        
        return None
    
    def _extract_location(self, element) -> Optional[str]:
        """Extract job location using ITViec structure"""
        selectors = [
            '.text-rich-grey',  # Current ITViec location styling
            '[class*="location"]',  # Generic location classes
            '.job-location',  # Legacy fallback
            '[data-testid="location"]',  # Legacy fallback
            '.address'  # Legacy fallback
        ]
        
        locations = []
        for selector in selectors:
            location_elems = element.select(selector)
            for location_elem in location_elems:
                text = location_elem.get_text(strip=True)
                if text and any(keyword in text.lower() for keyword in 
                    ['ho chi minh', 'hanoi', 'ha noi', 'da nang', 'remote', 
                     'hybrid', 'office', 'vietnam', 'saigon', 'hcm']):
                    locations.append(text)
        
        if locations:
            return ', '.join(locations)
        
        return None
        
        return None
    
    def _extract_salary(self, element) -> Optional[str]:
        """Extract salary information"""
        selectors = [
            '.salary',
            '.job-salary',
            '[data-testid="salary"]',
            '.wage'
        ]
        
        for selector in selectors:
            salary_elem = element.select_one(selector)
            if salary_elem:
                salary = salary_elem.get_text(strip=True)
                if salary and salary != "Sign in to view salary":
                    return salary
        
        return None
    
    def _extract_job_type(self, element) -> Optional[str]:
        """Extract job type"""
        # Look for job type indicators in class names or text
        text = element.get_text().lower()
        
        if 'full-time' in text or 'full time' in text:
            return 'Full-time'
        elif 'part-time' in text or 'part time' in text:
            return 'Part-time'
        elif 'freelance' in text:
            return 'Freelance'
        elif 'internship' in text or 'intern' in text:
            return 'Internship'
        
        return 'Full-time'  # Default
    
    def _extract_posted_date(self, element) -> Optional[datetime]:
        """Extract posted date"""
        selectors = [
            '.posted-date',
            '.job-posted',
            '[data-testid="posted-date"]',
            '.date'
        ]
        
        for selector in selectors:
            date_elem = element.select_one(selector)
            if date_elem:
                date_text = date_elem.get_text(strip=True).lower()
                return self._parse_date_text(date_text)
        
        # Look for date patterns in text
        text = element.get_text().lower()
        date_patterns = [
            r'posted (\d+) hours? ago',
            r'posted (\d+) days? ago',
            r'(\d+) hours? ago',
            r'(\d+) days? ago'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                number = int(match.group(1))
                if 'hour' in pattern:
                    return datetime.utcnow() - timedelta(hours=number)
                elif 'day' in pattern:
                    return datetime.utcnow() - timedelta(days=number)
        
        return None
    
    def _parse_date_text(self, date_text: str) -> Optional[datetime]:
        """Parse date text into datetime object"""
        try:
            if 'hour' in date_text:
                hours_match = re.search(r'(\d+)', date_text)
                if hours_match:
                    hours = int(hours_match.group(1))
                    return datetime.utcnow() - timedelta(hours=hours)
            elif 'day' in date_text:
                days_match = re.search(r'(\d+)', date_text)
                if days_match:
                    days = int(days_match.group(1))
                    return datetime.utcnow() - timedelta(days=days)
        except:
            pass
        
        return None
    
    def _extract_description(self, element) -> Optional[str]:
        """Extract job description or summary"""
        selectors = [
            '.job-description',
            '.description',
            '.job-summary',
            '.summary'
        ]
        
        for selector in selectors:
            desc_elem = element.select_one(selector)
            if desc_elem:
                description = desc_elem.get_text(strip=True)
                if description and len(description) > 50:
                    return description[:self.config.max_description_length]
        
        # Fallback to element text (first 500 chars)
        text = element.get_text(strip=True)
        if text and len(text) > 50:
            return text[:500]
        
        return None
    
    def _extract_experience_level(self, element) -> Optional[str]:
        """Extract experience level"""
        text = element.get_text().lower()
        
        if 'fresher' in text:
            return 'Fresher'
        elif 'senior' in text:
            return 'Senior'
        elif 'junior' in text:
            return 'Junior'
        elif 'lead' in text or 'leader' in text:
            return 'Lead'
        elif 'middle' in text or 'mid' in text:
            return 'Mid-level'
        
        return None
    
    def _make_absolute_url(self, url: str) -> str:
        """Convert relative URL to absolute URL"""
        if not url:
            return ""
        
        if url.startswith('http'):
            return url
        
        if url.startswith('/'):
            return f"{self.config.base_url}{url}"
        
        return f"{self.config.base_url}/{url}"
    
    def _extract_source_id(self, url: str) -> Optional[str]:
        """Extract source ID from job URL"""
        if not url:
            return None
        
        # Extract job ID from ITViec URL pattern
        patterns = [
            r'/jobs/(\w+)',
            r'/it-jobs/([^/?]+)',
            r'job[_-]?id[=:](\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Fallback: use last part of URL path
        try:
            path = urlparse(url).path
            parts = [p for p in path.split('/') if p]
            if parts:
                return parts[-1]
        except:
            pass
        
        return None
    
    async def is_available(self) -> bool:
        """Check if ITViec is available with Cloudflare protection handling"""
        try:
            if not self.browser:
                await self._init_browser()
            
            page = await self.context.new_page()
            try:
                self.logger.info(f"🔍 Checking ITViec availability at {self.config.base_url}")
                
                # Navigate to homepage with timeout
                response = await page.goto(
                    self.config.base_url, 
                    wait_until='domcontentloaded', 
                    timeout=self.config.timeout * 1000
                )
                
                if response and response.status == 403:
                    self.logger.warning("🔒 Received 403 status - checking for Cloudflare challenge")
                    
                    # Check if it's a Cloudflare challenge page
                    await asyncio.sleep(2)  # Let page load completely
                    page_content = await page.content()
                    page_title = await page.title()
                    
                    self.logger.info(f"Page title: '{page_title}'")
                    
                    # Check for challenge indicators
                    challenge_indicators = [
                        "just a moment",
                        "checking your browser", 
                        "verify you are human",
                        "cloudflare",
                        "challenge",
                        "security check",
                        "please wait"
                    ]
                    
                    is_challenge_page = any(indicator in page_title.lower() for indicator in challenge_indicators)
                    has_challenge_content = any(indicator in page_content.lower() for indicator in challenge_indicators)
                    
                    if is_challenge_page or has_challenge_content:
                        self.logger.info("🔒 Detected Cloudflare challenge - attempting bypass methods")
                        
                        # Try bypass methods in order of preference
                        bypass_successful = False
                        
                        # Method 1: Try FlareSolverr bypass first
                        if not bypass_successful:
                            flare_content = await self._try_flaresolverr_bypass(self.config.base_url)
                            if flare_content and "ITViec" in flare_content:
                                self.logger.info("✅ FlareSolverr bypass successful for availability check")
                                bypass_successful = True
                        
                        # Method 2: Try cloudscraper-style bypass
                        if not bypass_successful:
                            scraper_content = await self._try_cloudscraper_bypass(self.config.base_url)
                            if scraper_content and "ITViec" in scraper_content:
                                self.logger.info("✅ Cloudscraper bypass successful for availability check")
                                bypass_successful = True
                        
                        # Method 3: Human-in-the-loop challenge solving
                        if not bypass_successful:
                            self.logger.info("🔧 Attempting human-in-the-loop challenge solving")
                            challenge_solved = await self._solve_cloudflare_challenge(page, max_wait_time=60)
                            if challenge_solved:
                                self.logger.info("✅ Challenge solved by human intervention")
                                bypass_successful = True
                        
                        return bypass_successful
                    else:
                        self.logger.error("❌ 403 error but not a Cloudflare challenge - possibly blocked")
                        return False
                
                elif response and response.status == 200:
                    self.logger.info("✅ ITViec is available and accessible")
                    return True
                else:
                    self.logger.error(f"❌ ITViec returned unexpected status: {response.status if response else 'No response'}")
                    return False
                    
            finally:
                await page.close()
                
        except Exception as e:
            self.logger.error(f"❌ Error checking ITViec availability: {e}")
            return False
