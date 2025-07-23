from abc import ABC, abstractmethod
from typing import List
from app.models.schemas import JobCreate

class BaseCrawler(ABC):
    """Base class for all job crawlers"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
    
    @abstractmethod
    async def crawl_jobs(self, max_jobs: int = 100) -> List[JobCreate]:
        """Crawl jobs from the source"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the crawler source is available"""
        pass
