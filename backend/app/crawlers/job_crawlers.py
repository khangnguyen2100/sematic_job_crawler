import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
import random
from sqlalchemy.orm import Session

from app.models.schemas import JobCreate, JobSource
from .base_crawler import BaseCrawler
from .topcv_playwright_crawler import TopCVPlaywrightCrawler
from app.services.config_service import config_service

class TopCVCrawler(BaseCrawler):
    """TopCV Crawler using Playwright - Updated Implementation with Dynamic Configuration"""
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__("TopCV")
        self.db_session = db_session
        self.config = None
        self.crawler_info = None
        self._load_config()
        
    def _load_config(self):
        """Load configuration from database - no fallback to hardcoded values"""
        if not self.db_session:
            print("Warning: No database session provided. TopCV crawler will not be available.")
            return
        
        try:
            # Get site configuration from database
            site_config = config_service.get_site_config(self.db_session, "TopCV")
            if site_config:
                self.config = config_service.parse_topcv_config(site_config)
                self.crawler_info = config_service.get_crawler_info(self.db_session, "TopCV")
                return
        except Exception as e:
            print(f"Error loading TopCV config from database: {e}")
        
        # Set to None if no database configuration is available 
        print("Warning: TopCV configuration not found in database. Crawler will not be available.")
        self.config = None
        self.crawler_info = None
        
    async def crawl_jobs(self, max_jobs: int = 100) -> List[JobCreate]:
        """Crawl jobs from TopCV using Playwright"""
        if not self.config or not self.crawler_info:
            print("TopCV configuration not available. Skipping crawl.")
            return []
            
        try:
            # Use async context manager for proper resource cleanup
            async with TopCVPlaywrightCrawler(self.config) as crawler:
                jobs = await crawler.crawl_jobs(max_jobs)
                return jobs
        except Exception as e:
            print(f"Error crawling TopCV with Playwright: {e}")
            # Fallback to mock data for now
            return await self._generate_mock_jobs(min(max_jobs, 5))
    
    async def _generate_mock_jobs(self, count: int) -> List[JobCreate]:
        """Generate mock jobs as fallback"""
        jobs = []
        base_url = self.crawler_info['site_url'] if self.crawler_info else "https://www.topcv.vn"
        
        for i in range(count):
            job = JobCreate(
                title=f"Software Developer {i+1}",
                description=f"We are looking for a talented Software Developer to join our team. "
                          f"The ideal candidate should have experience in Python, JavaScript, and web development. "
                          f"This is an excellent opportunity to work on exciting projects.",
                company_name=f"Tech Company {i+1}",
                posted_date=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                source=JobSource.TOPCV,
                original_url=f"{base_url}/job/{i+1}",
                location="Ho Chi Minh City",
                salary="15-25 million VND",
                job_type="Full-time",
                experience_level="Mid-level",
                source_id=str(2000 + i)
            )
            jobs.append(job)
            await asyncio.sleep(0.1)
        return jobs
        
    async def is_available(self) -> bool:
        """Check if TopCV is available"""
        try:
            if not self.crawler_info:
                return False
            base_url = self.crawler_info['site_url']
            response = requests.get(base_url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

class VietnamWorksCrawler(BaseCrawler):
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__("VietnamWorks")
        self.db_session = db_session
        self.config = None
        self.crawler_info = None
        self._load_config()
        
    def _load_config(self):
        """Load configuration from database - no fallback to hardcoded values"""
        if not self.db_session:
            raise ValueError("Database session is required. VietnamWorks configuration must be loaded from database.")
        
        try:
            # Get site configuration from database
            site_config = config_service.get_site_config(self.db_session, "VietnamWorks")
            self.crawler_info = config_service.get_crawler_info(self.db_session, "VietnamWorks")
            self.config = site_config  # Store the config for consistency
            return
        except Exception as e:
            print(f"Error loading VietnamWorks config from database: {e}")
        
        # Fail if no database configuration is available
        raise ValueError("VietnamWorks configuration not found in database. Please ensure VietnamWorks is configured in the data sources.")
        
    async def crawl_jobs(self, max_jobs: int = 100) -> List[JobCreate]:
        """Crawl jobs from VietnamWorks"""
        jobs = []
        base_url = self.crawler_info['site_url']
        
        try:
            # Mock implementation
            for i in range(min(max_jobs, 10)):
                job = JobCreate(
                    title=f"Senior Developer {i+1}",
                    description=f"We are looking for a Senior Developer with 5+ years experience. "
                              f"Strong background in Python, Django, and cloud technologies required. "
                              f"Remote work available.",
                    company_name=f"Corporation {i+1}",
                    posted_date=datetime.utcnow() - timedelta(days=random.randint(1, 15)),
                    source=JobSource.VIETNAMWORKS,
                    original_url=f"{base_url}/job/{i+1}",
                    location="Da Nang",
                    salary="25-40 million VND",
                    job_type="Full-time",
                    experience_level="Senior",
                    source_id=str(3000 + i)
                )
                jobs.append(job)
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error crawling VietnamWorks: {e}")
        return jobs
        
    async def is_available(self) -> bool:
        """Check if VietnamWorks is available"""
        try:
            base_url = self.crawler_info['site_url']
            response = requests.get(base_url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

class ITViecCrawler(BaseCrawler):
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__("ITViec")
        self.db_session = db_session
        self.config = None
        self.crawler_info = None
        self._load_config()
        
    def _load_config(self):
        """Load configuration from database - no fallback to hardcoded values"""
        if not self.db_session:
            raise ValueError("Database session is required. ITViec configuration must be loaded from database.")
        
        try:
            # Get site configuration from database
            site_config = config_service.get_site_config(self.db_session, "ITViec")
            self.crawler_info = config_service.get_crawler_info(self.db_session, "ITViec")
            self.config = site_config  # Store the config for consistency
            return
        except Exception as e:
            print(f"Error loading ITViec config from database: {e}")
        
        # Fail if no database configuration is available  
        raise ValueError("ITViec configuration not found in database. Please ensure ITViec is configured in the data sources.")
        
    async def crawl_jobs(self, max_jobs: int = 100) -> List[JobCreate]:
        """Crawl jobs from ITViec"""
        jobs = []
        base_url = self.crawler_info['site_url']
        
        try:
            # Mock implementation
            for i in range(min(max_jobs, 8)):
                job = JobCreate(
                    title=f"Full Stack Developer {i+1}",
                    description=f"Join our dynamic team as a Full Stack Developer. "
                              f"You will work with React, Node.js, and modern web technologies. "
                              f"We offer competitive salary and great benefits.",
                    company_name=f"Startup {i+1}",
                    posted_date=datetime.utcnow() - timedelta(days=random.randint(1, 20)),
                    source=JobSource.ITVIEC,
                    original_url=f"{base_url}/jobs/{i+1}",
                    location="Ha Noi",
                    salary="20-35 million VND",
                    job_type="Full-time",
                    experience_level="Senior"
                )
                jobs.append(job)
                await asyncio.sleep(0.1)
                
        except Exception as e:
            print(f"Error crawling ITViec: {e}")
            
        return jobs
    
    async def is_available(self) -> bool:
        """Check if ITViec is available"""
        try:
            base_url = self.crawler_info['site_url']
            response = requests.get(base_url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

class LinkedInCrawler(BaseCrawler):
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__("LinkedIn")
        self.db_session = db_session
        self.config = None
        self.crawler_info = None
        self._load_config()
        
    def _load_config(self):
        """Load configuration from database - no fallback to hardcoded values"""
        if not self.db_session:
            raise ValueError("Database session is required. LinkedIn configuration must be loaded from database.")
        
        try:
            # Get site configuration from database
            site_config = config_service.get_site_config(self.db_session, "LinkedIn")
            self.crawler_info = config_service.get_crawler_info(self.db_session, "LinkedIn")
            self.config = site_config  # Store the config for consistency
            return
        except Exception as e:
            print(f"Error loading LinkedIn config from database: {e}")
        
        # Fail if no database configuration is available
        raise ValueError("LinkedIn configuration not found in database. Please ensure LinkedIn is configured in the data sources.")
        
    async def crawl_jobs(self, max_jobs: int = 100) -> List[JobCreate]:
        """Crawl jobs from LinkedIn"""
        jobs = []
        base_url = self.crawler_info['site_url']
        
        try:
            # Note: LinkedIn has strict anti-scraping measures
            # This is a mock implementation for demo purposes
            # In production, you would need proper API access or selenium with proper handling
            
            for i in range(min(max_jobs, 5)):
                job = JobCreate(
                    title=f"Software Engineer {i+1}",
                    description=f"Exciting opportunity to work as a Software Engineer at a leading technology company. "
                              f"We are looking for someone with strong problem-solving skills and experience in "
                              f"modern software development practices.",
                    company_name=f"Tech Giant {i+1}",
                    posted_date=datetime.utcnow() - timedelta(days=random.randint(1, 15)),
                    source=JobSource.LINKEDIN,
                    original_url=f"{base_url}/jobs/view/{i+1}",
                    location="Ho Chi Minh City",
                    salary="25-40 million VND",
                    job_type="Full-time",
                    experience_level="Senior",
                    source_id=str(4000 + i)
                )
                jobs.append(job)
                await asyncio.sleep(0.2)
                
        except Exception as e:
            print(f"Error crawling LinkedIn: {e}")
            
        return jobs
    
    async def is_available(self) -> bool:
        """Check if LinkedIn is available"""
        try:
            base_url = self.crawler_info['site_url']
            response = requests.get(base_url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
