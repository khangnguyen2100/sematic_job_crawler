"""Configuration for ITViec crawler settings"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class ITViecSortBy(str, Enum):
    """Sort options for ITViec search results"""
    NEWEST = "published"
    RELEVANCE = "relevance"
    SALARY = "salary"

class ITViecExperienceLevel(str, Enum):
    """Experience level filters for ITViec"""
    FRESHER = "fresher"
    JUNIOR = "junior" 
    MIDDLE = "middle"
    SENIOR = "senior"
    LEAD = "lead"

class ITViecJobType(str, Enum):
    """Job type filters for ITViec"""
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"

class ITViecWorkMode(str, Enum):
    """Work mode filters for ITViec"""
    AT_OFFICE = "at-office"
    HYBRID = "hybrid"
    REMOTE = "remote"

class ITViecParams(BaseModel):
    """URL parameters for ITViec search"""
    query: str = ""  # Search query/keyword
    sort: str = "published"  # Sort by newest by default
    page: str = "1"  # Page number
    experience_level: Optional[str] = None  # Experience level filter
    job_type: Optional[str] = None  # Job type filter
    work_mode: Optional[str] = None  # Work mode filter
    city: Optional[str] = None  # City filter (ho-chi-minh, ha-noi, etc.)

class ITViecRoutes(BaseModel):
    """Search routes/paths for ITViec - MUST be loaded from database"""
    paths: List[str] = []  # Empty by default - must be loaded from database

class ITViecConfig(BaseModel):
    """Configuration for ITViec crawler"""
    
    # Base URLs and endpoints - should be loaded from database
    base_url: str = "https://itviec.com"
    search_endpoint: str = "/it-jobs"
    
    # Browser settings - configurable from database
    timeout: int = 45  # Increased for Cloudflare challenges
    headless: bool = False  # Visible for challenge solving
    viewport: Dict[str, int] = Field(default_factory=lambda: {"width": 1366, "height": 768})
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Crawling behavior settings
    max_pages: int = 3
    start_page: int = 1
    jobs_per_page: int = 20
    request_delay: float = 3.0  # Delay between requests
    
    # Data requirements
    required_fields: List[str] = Field(default_factory=lambda: ["title", "company_name", "original_url"])
    max_description_length: int = 5000
    
    # Cloudflare protection settings
    challenge_timeout: int = 120  # Time to wait for human challenge solving
    company_page_timeout: int = 15
    enable_human_challenge_solving: bool = True
    crawl_company_details: bool = True
    
    # Search configuration
    search_keywords: List[str] = Field(default_factory=lambda: ["nodejs", "react", "vue", "python", "java", "javascript"])
    
    # Experience levels mapping
    experience_levels: Dict[str, str] = Field(default_factory=lambda: {
        "internship": "internship",
        "fresher": "fresher", 
        "junior": "junior",
        "middle": "middle",
        "senior": "senior",
        "manager": "manager"
    })
    
    # Job types mapping
    job_types: Dict[str, str] = Field(default_factory=lambda: {
        "fulltime": "full-time",
        "parttime": "part-time", 
        "freelance": "freelance",
        "contract": "contract"
    })
    
    # Work modes mapping
    work_modes: Dict[str, str] = Field(default_factory=lambda: {
        "office": "at-office",
        "remote": "remote",
        "hybrid": "hybrid"
    })
    
    # Search parameters and routes - loaded from database
    params: ITViecParams = Field(default_factory=ITViecParams)
    routes: ITViecRoutes = Field(default_factory=ITViecRoutes)
    
    def build_search_url_from_route(self, route_path: str, params: Optional[ITViecParams] = None) -> str:
        """Build search URL from a route path and parameters"""
        if not params:
            params = self.params
            
        # Construct base URL with route
        url = f"{self.base_url}/{route_path}"
        
        # Build query parameters
        query_params = []
        if params.query:
            query_params.append(f"q={params.query}")
        if params.sort:
            query_params.append(f"sort={params.sort}")
        if params.page:
            query_params.append(f"page={params.page}")
        if params.experience_level:
            query_params.append(f"level={params.experience_level}")
        if params.job_type:
            query_params.append(f"job_type={params.job_type}")
        if params.work_mode:
            query_params.append(f"work_mode={params.work_mode}")
        if params.city:
            query_params.append(f"city={params.city}")
            
        # Combine URL with parameters
        if query_params:
            url += "?" + "&".join(query_params)
            
        return url
    
    def build_search_url(self, keyword: str = "", page: int = 1, **filters) -> str:
        """Build a complete search URL with keyword and filters"""
        params = ITViecParams(
            query=keyword,
            page=str(page),
            **filters
        )
        return self.build_search_url_from_route("it-jobs", params)
        
    def get_search_urls(self, max_pages: Optional[int] = None) -> List[str]:
        """Generate search URLs for all configured routes and keywords"""
        urls = []
        max_pages = max_pages or self.max_pages
        
        # If routes are configured, use them
        if self.routes.paths:
            for route_path in self.routes.paths:
                for page in range(self.start_page, min(max_pages + 1, self.start_page + max_pages)):
                    params = ITViecParams(page=str(page))
                    url = self.build_search_url_from_route(route_path, params)
                    urls.append(url)
        else:
            # Fallback to search keywords
            if self.search_keywords:
                for keyword in self.search_keywords:
                    for page in range(self.start_page, min(max_pages + 1, self.start_page + max_pages)):
                        url = self.build_search_url(keyword, page)
                        urls.append(url)
            else:
                # Default search without keywords
                for page in range(self.start_page, min(max_pages + 1, self.start_page + max_pages)):
                    url = self.build_search_url("", page)
                    urls.append(url)
        
        return urls

    def get_priority_search_urls(self, max_pages: int = 3) -> List[str]:
        """Get priority URLs for testing/quick crawls"""
        priority_keywords = ["python", "javascript", "java", "react", "nodejs"]
        urls = []
        
        for keyword in priority_keywords[:3]:  # Limit to first 3 keywords
            for page in range(1, min(max_pages + 1, 3)):  # Limit to 2 pages per keyword
                url = self.build_search_url(keyword, page)
                urls.append(url)
                
        return urls
        
    class Config:
        """Pydantic config"""
        use_enum_values = True
