"""
TopCV Crawler using Playwright with configurable parameters and pagination support
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
from app.config.topcv_config import TopCVConfig

logger = logging.getLogger(__name__)

class TopCVPlaywrightCrawler(BaseCrawler):
    """Advanced TopCV crawler using Playwright with full configuration support"""
    
    def __init__(self, config: TopCVConfig):
        super().__init__("TopCV")
        if not config:
            raise ValueError("TopCV configuration is required")
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
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
            self.logger.info("Launching browser with advanced anti-detection measures")
            
            self.browser = await async_playwright().start()
            
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
            
            self.context = await self.browser.chromium.launch(
                headless=False,
                args=stealth_args
            )
            
            # Create context with enhanced fingerprinting resistance
            self.page_context = await self.context.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'en-US,en;q=0.9',
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
            
            self.page = await self.page_context.new_page()
            
            # Apply advanced stealth patches
            await self._apply_stealth_patches()
            
            self.logger.info("Browser initialized with advanced anti-detection measures")
            
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
                    get: () => ['en-US', 'en'],
                });
                
                // Hide automation properties
                const originalQuery = window.document.querySelector;
                window.document.querySelector = function(selector) {
                    if (selector === 'img[src*="data:image/png;base64"]') {
                        return null;
                    }
                    return originalQuery.call(document, selector);
                };
                
                // Randomize canvas fingerprint slightly
                const getContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(type) {
                    if (type === '2d') {
                        const ctx = getContext.call(this, type);
                        const originalFillText = ctx.fillText;
                        ctx.fillText = function(text, x, y) {
                            return originalFillText.call(this, text, x + Math.random() * 0.1, y + Math.random() * 0.1);
                        };
                        return ctx;
                    }
                    return getContext.call(this, type);
                };
            """)
            
            self.logger.info("Applied stealth patches to hide automation traces")
            
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
                        '.job-item-search-result',
                        '.job-item',
                        'input[placeholder*="tìm kiếm"]',
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
    
    async def _close_browser(self):
        """Close browser and cleanup"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    async def crawl_jobs(self, max_jobs: int = 100) -> List[JobCreate]:
        """Main crawling method with enhanced anti-bot measures and rate limiting"""
        if not self.browser:
            await self._init_browser()
        
        jobs = []
        urls = self.config.get_search_urls_from_routes()
        
        logger.info(f"Starting crawl with {len(urls)} URLs, max {max_jobs} jobs")
        logger.info(f"Using request delay: {self.config.request_delay}s")
        
        # Initialize session by visiting homepage first
        try:
            logger.info("Initializing session by visiting TopCV homepage...")
            init_page = await self.context.new_page()
            await init_page.goto(self.config.base_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)  # Let the page settle
            await init_page.close()
            logger.info("Session initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize session: {e}")
        
        try:
            for url_index, url in enumerate(urls):
                if len(jobs) >= max_jobs:
                    break
                    
                logger.info(f"Crawling URL {url_index + 1}/{len(urls)}: {url}")
                
                try:
                    page_jobs = await self._crawl_page(url, max_jobs - len(jobs), url_index)
                    jobs.extend(page_jobs)
                    
                    logger.info(f"Found {len(page_jobs)} jobs on this page. Total: {len(jobs)}")
                    
                    # Enhanced delay between pages with randomization
                    if url_index < len(urls) - 1:
                        delay = self.config.request_delay + (2.0 * (asyncio.get_event_loop().time() % 1))
                        logger.info(f"Waiting {delay:.1f}s before next page...")
                        await asyncio.sleep(delay)
                        
                except Exception as e:
                    logger.error(f"Error crawling URL {url}: {e}")
                    if "403" in str(e) or "forbidden" in str(e).lower():
                        logger.warning("Received 403 error, increasing delay and continuing...")
                        await asyncio.sleep(10)  # Wait longer after 403
                    continue
            
            logger.info(f"Crawling completed. Total jobs found: {len(jobs)}")
            return jobs
            
        except Exception as e:
            logger.error(f"Error during crawling: {e}")
            return jobs
        finally:
            # For human-in-the-loop mode, ask before closing browser
            logger.info("🔍 Crawling completed. Browser window will remain open for inspection.")
            logger.info("📢 You can manually inspect the results or close the browser when ready.")
            # Don't auto-close in human-in-the-loop mode - let user close manually
            # await self._close_browser()
    
    async def _crawl_page(self, url: str, max_jobs: int, url_index: int = 0) -> List[JobCreate]:
        """Crawl a single search results page with enhanced anti-bot measures"""
        page = await self.context.new_page()
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
                            extracted_jobs = await self._extract_jobs(soup, url)
                            if extracted_jobs:
                                jobs.extend(extracted_jobs)
                                bypass_successful = True
                    
                    # Method 2: Try cloudscraper-style bypass
                    if not bypass_successful:
                        scraper_content = await self._try_cloudscraper_bypass(url)
                        if scraper_content:
                            logger.info("✅ Cloudscraper bypass successful, parsing content")
                            soup = BeautifulSoup(scraper_content, 'html.parser')
                            extracted_jobs = await self._extract_jobs(soup, url)
                            if extracted_jobs:
                                jobs.extend(extracted_jobs)
                                bypass_successful = True
                    
                    # Method 3: Fall back to human-in-the-loop challenge solving
                    if not bypass_successful:
                        challenge_solved = await self._solve_cloudflare_challenge(page, max_wait_time=120)
                        
                        if challenge_solved:
                            logger.info("✅ Challenge solved! Continuing with crawling...")
                        logger.info("✅ Challenge solved! Continuing with crawling...")
                        # Continue with normal crawling flow below
                    else:
                        logger.error("❌ Could not solve Cloudflare challenge within timeout")
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
            
            # Wait for page to stabilize
            await asyncio.sleep(1)
            
            # Scroll down slowly to trigger dynamic content loading
            await page.evaluate("""
                window.scrollTo({
                    top: document.body.scrollHeight / 3,
                    behavior: 'smooth'
                });
            """)
            await asyncio.sleep(1.5)
            
            # Wait for job listings to load - use TopCV specific selector
            try:
                await page.wait_for_selector('.job-item-search-result', timeout=15000)
                logger.info("Job listings loaded successfully")
            except Exception as e:
                logger.warning(f"Could not find .job-item-search-result: {e}")
                # Check if we got blocked
                page_content = await page.content()
                if "captcha" in page_content.lower() or "blocked" in page_content.lower():
                    logger.error("Page appears to be blocked or has CAPTCHA")
                    # Save page content for debugging
                    logger.debug(f"Page content preview: {page_content[:500]}")
                    return jobs
                
                # Try alternative waiting strategy
                await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Extract job listings using TopCV specific selector
            job_elements = await page.query_selector_all('.job-item-search-result')
            
            if not job_elements:
                # Fallback selectors
                selectors_to_try = [
                    '[data-job-id]',
                    '.job-item',
                    '.job-list-item',
                    '.job-list .job-item-search-result'
                ]
                for selector in selectors_to_try:
                    job_elements = await page.query_selector_all(selector)
                    if job_elements:
                        logger.info(f"Found {len(job_elements)} jobs using fallback selector: {selector}")
                        break
            
            logger.info(f"Found {len(job_elements)} job elements on page")
            
            if not job_elements:
                # Log page title and URL for debugging
                page_title = await page.title()
                logger.warning(f"No job elements found on page: {page_title} ({url})")
                # Save a small portion of page content for debugging
                page_content = await page.content()
                logger.debug(f"Page content preview: {page_content[:1000]}")
            
            for i, job_element in enumerate(job_elements):
                if len(jobs) >= max_jobs:
                    break
                    
                try:
                    # Human-like delay between job extractions
                    if i > 0:
                        await asyncio.sleep(0.1 + (0.2 * (i % 3)))
                    
                    job_data = await self._extract_job_from_element(page, job_element)
                    if job_data and self._validate_job_data(job_data):
                        # Get additional details if enabled
                        if self.config.crawl_company_details and job_data.original_url:
                            job_data = await self._enrich_job_with_details(job_data)
                        
                        jobs.append(job_data)
                        logger.debug(f"Extracted job {i + 1}: {job_data.title}")
                    
                except Exception as e:
                        logger.warning(f"Error extracting job {i + 1}: {e}")
                        continue
            
            # Human-like behavior: scroll back up
            await page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' });")
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error crawling page {url}: {e}")
            # Check if it's a network/timeout error vs. blocking
            if "403" in str(e) or "forbidden" in str(e).lower():
                logger.error("Received 403 Forbidden - possible anti-bot detection")
            elif "timeout" in str(e).lower():
                logger.error("Page load timeout - possible slow response or blocking")
            
        finally:
            await page.close()
        
        return jobs
    
    async def _extract_job_from_element(self, page: Page, job_element) -> Optional[JobCreate]:
        """Extract job data from a job listing element"""
        try:
            # Get HTML content for BeautifulSoup parsing
            html_content = await job_element.inner_html()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract basic information
            title = await self._extract_title(job_element, soup)
            company_name = await self._extract_company_name(job_element, soup)
            original_url = await self._extract_job_url(job_element, soup)
            
            if not all([title, company_name, original_url]):
                logger.debug(f"Missing required fields: title={title}, company={company_name}, url={original_url}")
                return None
            
            # Extract additional information
            location = await self._extract_location(job_element, soup)
            salary = await self._extract_salary(job_element, soup)
            job_type = await self._extract_job_type(job_element, soup)
            posted_date = await self._extract_posted_date(job_element, soup)
            description = await self._extract_description(job_element, soup)
            
            # Create job object
            job = JobCreate(
                title=title.strip(),
                description=description or f"Position: {title} at {company_name}",
                company_name=company_name.strip(),
                posted_date=posted_date or datetime.utcnow(),
                source=JobSource.TOPCV,
                original_url=self._make_absolute_url(original_url),
                location=location,
                salary=salary,
                job_type=job_type or "Full-time",
                experience_level=await self._extract_experience_level(job_element, soup),
                source_id=self._extract_source_id(original_url)
            )
            
            return job
            
        except Exception as e:
            logger.error(f"Error extracting job data: {e}")
            return None
    
    async def _extract_title(self, element, soup: BeautifulSoup) -> Optional[str]:
        """Extract job title using TopCV structure"""
        selectors = [
            '.title a span',  # TopCV specific: h3.title > a > span
            '.title a',
            'h3.title a',
            '.job-title a',
            '.job-item-title a',
            '[data-testid="job-title"]',
        ]
        
        for selector in selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title:  # Make sure it's not empty
                    return title
        
        # Fallback: try to get from element directly
        try:
            title_elem = await element.query_selector('h3.title a, .title a')
            if title_elem:
                title = await title_elem.text_content()
                if title and title.strip():
                    return title.strip()
        except:
            pass
        
        return None
    
    async def _extract_company_name(self, element, soup: BeautifulSoup) -> Optional[str]:
        """Extract company name using TopCV structure"""
        selectors = [
            '.company-name',      # TopCV specific
            'a.company .company-name',  # More specific TopCV selector
            '.company .company-name',
            '.job-company',
            '.company',
            '[data-testid="company-name"]',
            '.employer-name'
        ]
        
        for selector in selectors:
            company_elem = soup.select_one(selector)
            if company_elem:
                company = company_elem.get_text(strip=True)
                if company:  # Make sure it's not empty
                    return company
        
        # Fallback
        try:
            company_elem = await element.query_selector('.company-name, .company')
            if company_elem:
                company = await company_elem.text_content()
                if company and company.strip():
                    return company.strip()
        except:
            pass
        
        return None
    
    async def _extract_job_url(self, element, soup: BeautifulSoup) -> Optional[str]:
        """Extract job URL using TopCV structure"""
        selectors = [
            '.title a',       # TopCV specific: h3.title > a
            'h3.title a',
            '.job-title a',
            '[data-testid="job-title"] a'
        ]
        
        for selector in selectors:
            link_elem = soup.select_one(selector)
            if link_elem and link_elem.get('href'):
                href = link_elem['href']
                if href and href.strip():  # Make sure it's not empty
                    return href.strip()
        
        # Fallback
        try:
            link_elem = await element.query_selector('h3.title a, .title a')
            if link_elem:
                href = await link_elem.get_attribute('href')
                if href and href.strip():
                    return href.strip()
        except:
            pass
        
        return None
    
    async def _extract_location(self, element, soup: BeautifulSoup) -> Optional[str]:
        """Extract job location using TopCV structure"""
        selectors = [
            '.address .city-text',  # TopCV specific
            '.address',
            '.location',
            '.job-location',
            '[data-testid="location"]'
        ]
        
        for selector in selectors:
            location_elem = soup.select_one(selector)
            if location_elem:
                location = location_elem.get_text(strip=True)
                if location:  # Make sure it's not empty
                    return location
        
        return None
    
    async def _extract_salary(self, element, soup: BeautifulSoup) -> Optional[str]:
        """Extract salary information using TopCV structure"""
        selectors = [
            '.title-salary',      # TopCV specific selector
            '.salary',
            '.job-salary',
            '.price',
            '[data-testid="salary"]'
        ]
        
        for selector in selectors:
            salary_elem = soup.select_one(selector)
            if salary_elem:
                salary_text = salary_elem.get_text(strip=True)
                # Clean up the text and return if meaningful
                if salary_text and salary_text.lower() not in ['thỏa thuận', 'cạnh tranh', 'negotiable', 'thoả thuận']:
                    return salary_text.replace('Thoả thuận', '').strip()
                elif salary_text:  # Even if it's "Thoả thuận", return it
                    return salary_text
        
        return None
    
    async def _extract_job_type(self, element, soup: BeautifulSoup) -> Optional[str]:
        """Extract job type (full-time, part-time, etc.)"""
        selectors = [
            '.job-type',
            '.employment-type',
            '.work-type'
        ]
        
        for selector in selectors:
            type_elem = soup.select_one(selector)
            if type_elem:
                return type_elem.get_text(strip=True)
        
        return "Full-time"  # Default
    
    async def _extract_posted_date(self, element, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract job posted date"""
        selectors = [
            '.posted-date',
            '.job-date',
            '.date',
            '[data-testid="posted-date"]'
        ]
        
        for selector in selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                return self._parse_date(date_text)
        
        return datetime.utcnow()  # Default to now
    
    async def _extract_description(self, element, soup: BeautifulSoup) -> Optional[str]:
        """Extract job description"""
        selectors = [
            '.job-description',
            '.description',
            '.job-summary'
        ]
        
        for selector in selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                description = desc_elem.get_text(strip=True)
                if len(description) > 50:  # Ensure it's substantial
                    return description[:self.config.max_description_length]
        
        return None
    
    async def _extract_experience_level(self, element, soup: BeautifulSoup) -> Optional[str]:
        """Extract experience level using TopCV structure"""
        selectors = [
            '.exp',              # TopCV specific: label.exp
            '.experience',
            '.exp-level',
            '.job-experience'
        ]
        
        for selector in selectors:
            exp_elem = soup.select_one(selector)
            if exp_elem:
                exp_text = exp_elem.get_text(strip=True)
                if exp_text:  # Make sure it's not empty
                    return exp_text
        
        return None
    
    def _extract_source_id(self, url: str) -> Optional[str]:
        """Extract source job ID from URL"""
        try:
            # TopCV URLs pattern: /viec-lam/job-title/1234567.html
            match = re.search(r'/viec-lam/.*?/(\d+)\.html', url)
            if match:
                return match.group(1)
            
            # Alternative pattern: job-id-123456
            match = re.search(r'/viec-lam/.*?-(\d+)', url)
            if match:
                return match.group(1)
            
            # Another pattern: /job/123456
            match = re.search(r'/job/(\d+)', url)
            if match:
                return match.group(1)
                
        except Exception as e:
            logger.warning(f"Could not extract source ID from URL {url}: {e}")
        
        return None
    
    def _make_absolute_url(self, url: str) -> str:
        """Convert relative URL to absolute URL"""
        if url.startswith('http'):
            return url
        return urljoin(self.config.base_url, url)
    
    def _parse_date(self, date_text: str) -> datetime:
        """Parse Vietnamese date text to datetime"""
        try:
            # Common Vietnamese date patterns
            if 'hôm nay' in date_text.lower():
                return datetime.utcnow()
            elif 'hôm qua' in date_text.lower():
                return datetime.utcnow() - timedelta(days=1)
            elif 'ngày trước' in date_text.lower():
                days_match = re.search(r'(\d+)\s*ngày trước', date_text)
                if days_match:
                    days = int(days_match.group(1))
                    return datetime.utcnow() - timedelta(days=days)
            elif 'tuần trước' in date_text.lower():
                weeks_match = re.search(r'(\d+)\s*tuần trước', date_text)
                if weeks_match:
                    weeks = int(weeks_match.group(1))
                    return datetime.utcnow() - timedelta(weeks=weeks)
            
            # Try to parse standard date formats
            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                try:
                    return datetime.strptime(date_text, fmt)
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not parse date '{date_text}': {e}")
        
        return datetime.utcnow()
    
    def _validate_job_data(self, job: JobCreate) -> bool:
        """Validate extracted job data"""
        # Check required fields
        for field in self.config.required_fields:
            if not getattr(job, field, None):
                return False
        
        # Validate title length
        if len(job.title) < 3:
            return False
        
        # Validate URL
        if not job.original_url.startswith('http'):
            return False
        
        return True
    
    async def _enrich_job_with_details(self, job: JobCreate) -> JobCreate:
        """Enrich job with additional details from job detail page"""
        if not job.original_url:
            return job
        
        page = await self.context.new_page()
        try:
            await page.goto(job.original_url, 
                          wait_until='domcontentloaded', 
                          timeout=self.config.company_page_timeout * 1000)
            
            # Extract detailed description
            description_elem = await page.query_selector(
                '.job-description, .job-detail-description, .description-content'
            )
            if description_elem:
                detailed_description = await description_elem.text_content()
                if detailed_description and len(detailed_description) > len(job.description or ''):
                    job.description = detailed_description[:self.config.max_description_length]
            
            # Extract additional company information
            company_elem = await page.query_selector('.company-info, .company-detail')
            if company_elem:
                company_text = await company_elem.text_content()
                if company_text and job.description:
                    job.description += f"\n\nCompany Info: {company_text[:500]}"
            
        except Exception as e:
            logger.warning(f"Could not enrich job details for {job.original_url}: {e}")
        finally:
            await page.close()
        
        return job
    
    async def is_available(self) -> bool:
        """Check if TopCV is available"""
        try:
            if not self.browser:
                await self._init_browser()
            
            page = await self.context.new_page()
            try:
                response = await page.goto(self.config.base_url, timeout=10000)
                return response.status == 200
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"Error checking TopCV availability: {e}")
            return False
