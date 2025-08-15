"""Configuration for TopCV crawler settings"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class TopCVSearchType(str, Enum):
    """Search type for TopCV job search"""
    KEYWORD = "1"  # type_keyword=1
    COMPANY = "2"  # type_keyword=2

class TopCVSortBy(str, Enum):
    """Sort options for TopCV search results"""
    NEWEST = "1"
    RELEVANCE = "0"

class TopCVParams(BaseModel):
    """URL parameters for TopCV search"""
    type_keyword: str = "1"  # Search by keyword
    sba: str = "1"  # Search by all (salary, benefits, etc.)
    sort_by: str = "1"  # Sort by newest
    page: str = "1"  # Page number
    category_family: Optional[str] = None  # Category family (e.g., r257 for IT)

class TopCVRoutes(BaseModel):
    """Search routes/paths for TopCV - MUST be loaded from database"""
    paths: List[str] = []  # Empty by default - must be loaded from database

class TopCVConfig(BaseModel):
    """Configuration for TopCV crawler"""
    
    # Base URLs and endpoints - should be loaded from database
    # base_url: str = "https://www.topcv.vn"  # DEPRECATED: Use database config
    base_url: str = ""  # Must be loaded from database
    search_endpoint: str = "/tim-viec-lam"
    
    # Search routes configuration
    routes: TopCVRoutes = TopCVRoutes()
    
    # Default search parameters
    params: TopCVParams = TopCVParams()
    
    # Search configuration - DEPRECATED: Must be loaded from database
    search_keywords: List[str] = []  # Empty by default - must be loaded from database
    
    # Category family mapping for IT jobs - MUST be loaded from database
    category_families: Dict[str, str] = {}  # Empty by default - must be loaded from database
    
    # Pagination settings
    max_pages: int = Field(default=5, ge=1, le=20)
    jobs_per_page: int = Field(default=20, ge=1, le=50)
    start_page: int = Field(default=1, ge=1)
    
    # Request settings
    request_delay: float = Field(default=3.0, ge=1.0, le=10.0)  # Longer delay between requests
    timeout: int = Field(default=45, ge=15, le=90)  # Longer timeout for anti-bot measures
    
    # Browser settings
    headless: bool = False  # Default to visible for challenge solving
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    viewport: Dict[str, int] = {"width": 1366, "height": 768}  # More common resolution
    
    # Human-in-the-loop settings
    enable_human_challenge_solving: bool = True
    challenge_timeout: int = Field(default=120, ge=30, le=300)  # Time to wait for human to solve challenge
    
    # Job extraction settings
    max_description_length: int = Field(default=5000, ge=100)
    required_fields: List[str] = ["title", "company_name", "original_url"]
    
    # Company page crawling
    crawl_company_details: bool = True
    company_page_timeout: int = Field(default=15, ge=5, le=30)
    
    def build_search_url_from_route(self, route_path: str, params: Optional[TopCVParams] = None) -> str:
        """Build search URL from a route path and parameters"""
        if not params:
            params = self.params
            
        # Construct base URL with route
        url = f"{self.base_url}/{route_path}"
        
        # Build query parameters
        query_params = []
        if params.type_keyword:
            query_params.append(f"type_keyword={params.type_keyword}")
        if params.sba:
            query_params.append(f"sba={params.sba}")
        if params.sort_by:
            query_params.append(f"sort_by={params.sort_by}")
        if params.page:
            query_params.append(f"page={params.page}")
        if params.category_family:
            query_params.append(f"category_family={params.category_family}")
            
        # Combine URL with parameters
        if query_params:
            url += "?" + "&".join(query_params)
            
        return url
    
    def build_search_url(self, keyword: str, page: int = 1, category_family: Optional[str] = None) -> str:
        """Build search URL with parameters (legacy method for backward compatibility)"""
        # Construct base search URL
        if category_family:
            url = f"{self.base_url}{self.search_endpoint}-{keyword}-kcr{category_family}"
        else:
            url = f"{self.base_url}{self.search_endpoint}-{keyword}"
        
        # Add parameters
        params = {
            "type_keyword": self.params.type_keyword,
            "sba": self.params.sba,
            "sort_by": self.params.sort_by,
            "page": str(page)
        }
        
        if category_family:
            params["category_family"] = f"r{category_family}"
        
        # Build query string
        query_params = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{url}?{query_params}"
    
    def get_search_urls_from_routes(self) -> List[str]:
        """Generate search URLs from configured routes and parameters"""
        urls = []
        
        for route_path in self.routes.paths:
            # Generate URLs for all pages
            for page in range(self.start_page, self.start_page + self.max_pages):
                # Create params with current page
                page_params = TopCVParams(
                    type_keyword=self.params.type_keyword,
                    sba=self.params.sba,
                    sort_by=self.params.sort_by,
                    page=str(page),
                    category_family=self.params.category_family
                )
                
                url = self.build_search_url_from_route(route_path, page_params)
                urls.append(url)
        
        return urls
    
    def get_search_urls(self) -> List[str]:
        """Generate all search URLs for configured keywords and pages (legacy method)"""
        urls = []
        
        for keyword in self.search_keywords:
            # Check if keyword should use category family
            category_family = None
            for category, family_id in self.category_families.items():
                if category in keyword.lower():
                    category_family = family_id.replace("r", "")
                    break
            
            # Generate URLs for all pages
            for page in range(self.start_page, self.start_page + self.max_pages):
                url = self.build_search_url(keyword, page, category_family)
                urls.append(url)
        
        return urls
    
    class Config:
        use_enum_values = True

# NOTE: All configuration instances below are DEPRECATED
# Configuration MUST be loaded from database only
# These are kept for type reference only

# DEPRECATED: Use database configuration only
# DEFAULT_TOPCV_CONFIG = TopCVConfig()

# DEPRECATED: Use database configuration only
# COMPREHENSIVE_CONFIG = TopCVConfig(...)

# DEPRECATED: Use database configuration only  
# QUICK_CONFIG = TopCVConfig(...)
