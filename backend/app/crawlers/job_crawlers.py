import requests
from bs4 import BeautifulSoup
from typing import List
from datetime import datetime, timedelta
import asyncio
import random

from app.models.schemas import JobCreate, JobSource
from .base_crawler import BaseCrawler

import requests
from bs4 import BeautifulSoup
from typing import List
from datetime import datetime, timedelta
import asyncio
import random

from app.models.schemas import JobCreate, JobSource
from .base_crawler import BaseCrawler
from .topcv_playwright_crawler import TopCVPlaywrightCrawler
from app.config.topcv_config import DEFAULT_TOPCV_CONFIG, QUICK_CONFIG

class TopCVCrawler(BaseCrawler):
    """TopCV Crawler using Playwright - Updated Implementation"""
    def __init__(self, use_quick_config: bool = False):
        super().__init__("TopCV")
        self.config = QUICK_CONFIG if use_quick_config else DEFAULT_TOPCV_CONFIG
        self.playwright_crawler = None
        
    async def crawl_jobs(self, max_jobs: int = 100) -> List[JobCreate]:
        """Crawl jobs from TopCV using Playwright"""
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
        for i in range(count):
            job = JobCreate(
                title=f"Software Developer {i+1}",
                description=f"We are looking for a talented Software Developer to join our team. "
                          f"The ideal candidate should have experience in Python, JavaScript, and web development. "
                          f"This is an excellent opportunity to work on exciting projects.",
                company_name=f"Tech Company {i+1}",
                posted_date=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                source=JobSource.TOPCV,
                original_url=f"https://www.topcv.vn/job/{i+1}",
                location="Ho Chi Minh City",
                salary="15-25 million VND",
                job_type="Full-time",
                experience_level="Mid-level",
                source_id=str(1000 + i)
            )
            jobs.append(job)
            await asyncio.sleep(0.1)
        return jobs
        
    async def is_available(self) -> bool:
        """Check if TopCV is available"""
        try:
            async with TopCVPlaywrightCrawler(self.config) as crawler:
                return await crawler.is_available()
        except Exception as e:
            print(f"Error checking TopCV availability: {e}")
            # Fallback check
            try:
                response = requests.get("https://www.topcv.vn", timeout=10)
                return response.status_code == 200
            except:
                return False

class ITViecCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("ITViec")
        self.base_url = "https://itviec.com"
        
    async def crawl_jobs(self, max_jobs: int = 100) -> List[JobCreate]:
        """Crawl jobs from ITViec"""
        jobs = []
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
                    original_url=f"https://itviec.com/jobs/{i+1}",
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
            response = requests.get(self.base_url, timeout=10)
            return response.status_code == 200
        except:
            return False

class VietnamWorksCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("VietnamWorks")
        self.base_url = "https://www.vietnamworks.com"
        
    async def crawl_jobs(self, max_jobs: int = 100) -> List[JobCreate]:
        """Crawl jobs from VietnamWorks"""
        jobs = []
        try:
            # Mock implementation
            for i in range(min(max_jobs, 12)):
                job = JobCreate(
                    title=f"Backend Developer {i+1}",
                    description=f"We are seeking an experienced Backend Developer to design and implement "
                              f"scalable server-side applications. Knowledge of Python, Django, and PostgreSQL required.",
                    company_name=f"Enterprise {i+1}",
                    posted_date=datetime.utcnow() - timedelta(days=random.randint(1, 25)),
                    source=JobSource.VIETNAMWORKS,
                    original_url=f"https://www.vietnamworks.com/job/{i+1}",
                    location="Da Nang",
                    salary="18-30 million VND",
                    job_type="Full-time",
                    experience_level="Mid-level"
                )
                jobs.append(job)
                await asyncio.sleep(0.1)
                
        except Exception as e:
            print(f"Error crawling VietnamWorks: {e}")
            
        return jobs
    
    async def is_available(self) -> bool:
        """Check if VietnamWorks is available"""
        try:
            response = requests.get(self.base_url, timeout=10)
            return response.status_code == 200
        except:
            return False

class LinkedInCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("LinkedIn")
        self.base_url = "https://www.linkedin.com"
        
    async def crawl_jobs(self, max_jobs: int = 100) -> List[JobCreate]:
        """Crawl jobs from LinkedIn"""
        jobs = []
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
                    original_url=f"https://www.linkedin.com/jobs/view/{i+1}",
                    location="Ho Chi Minh City",
                    salary="25-40 million VND",
                    job_type="Full-time",
                    experience_level="Senior"
                )
                jobs.append(job)
                await asyncio.sleep(0.2)
                
        except Exception as e:
            print(f"Error crawling LinkedIn: {e}")
            
        return jobs
    
    async def is_available(self) -> bool:
        """Check if LinkedIn is available"""
        try:
            response = requests.get(self.base_url, timeout=10)
            return response.status_code == 200
        except:
            return False
