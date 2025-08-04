"""
TopCV Crawler using Playwright with configurable parameters and pagination support
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import re

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

from app.models.schemas import JobCreate, JobSource
from app.crawlers.base_crawler import BaseCrawler
from app.config.topcv_config import TopCVConfig, DEFAULT_TOPCV_CONFIG

logger = logging.getLogger(__name__)

class TopCVPlaywrightCrawler(BaseCrawler):
    """Advanced TopCV crawler using Playwright with full configuration support"""
    
    def __init__(self, config: Optional[TopCVConfig] = None):
        super().__init__("TopCV")
        self.config = config or DEFAULT_TOPCV_CONFIG
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._init_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_browser()
    
    async def _init_browser(self):
        """Initialize Playwright browser and context"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with configuration
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage'
                ]
            )
            
            # Create context with configuration
            self.context = await self.browser.new_context(
                user_agent=self.config.user_agent,
                viewport=self.config.viewport,
                java_script_enabled=True,
                ignore_https_errors=True
            )
            
            # Add stealth settings
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            logger.info("Browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
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
        """Main crawling method with pagination support"""
        if not self.browser:
            await self._init_browser()
        
        jobs = []
        urls = self.config.get_search_urls()
        
        logger.info(f"Starting crawl with {len(urls)} URLs, max {max_jobs} jobs")
        
        try:
            for url_index, url in enumerate(urls):
                if len(jobs) >= max_jobs:
                    break
                    
                logger.info(f"Crawling URL {url_index + 1}/{len(urls)}: {url}")
                
                page_jobs = await self._crawl_page(url, max_jobs - len(jobs))
                jobs.extend(page_jobs)
                
                logger.info(f"Found {len(page_jobs)} jobs on this page. Total: {len(jobs)}")
                
                # Delay between pages
                if url_index < len(urls) - 1:
                    await asyncio.sleep(self.config.request_delay)
            
            logger.info(f"Crawling completed. Total jobs found: {len(jobs)}")
            return jobs
            
        except Exception as e:
            logger.error(f"Error during crawling: {e}")
            return jobs
        finally:
            if self.config.headless:  # Only auto-close in headless mode
                await self._close_browser()
    
    async def _crawl_page(self, url: str, max_jobs: int) -> List[JobCreate]:
        """Crawl a single search results page"""
        page = await self.context.new_page()
        jobs = []
        
        try:
            # Navigate to page
            await page.goto(url, wait_until='domcontentloaded', timeout=self.config.timeout * 1000)
            
            # Wait for job listings to load - use TopCV specific selector
            try:
                await page.wait_for_selector('.job-item-search-result', timeout=10000)
                logger.info("Job listings loaded successfully")
            except Exception as e:
                logger.warning(f"Could not find .job-item-search-result: {e}")
                # Try alternative waiting strategy
                await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Extract job listings using TopCV specific selector
            job_elements = await page.query_selector_all('.job-item-search-result')
            
            if not job_elements:
                # Fallback selectors
                selectors_to_try = [
                    '[data-job-id]',
                    '.job-item',
                    '.job-list-item'
                ]
                for selector in selectors_to_try:
                    job_elements = await page.query_selector_all(selector)
                    if job_elements:
                        logger.info(f"Found {len(job_elements)} jobs using fallback selector: {selector}")
                        break
            
            logger.info(f"Found {len(job_elements)} job elements on page")
            
            for i, job_element in enumerate(job_elements):
                if len(jobs) >= max_jobs:
                    break
                    
                try:
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
            
        except Exception as e:
            logger.error(f"Error crawling page {url}: {e}")
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
