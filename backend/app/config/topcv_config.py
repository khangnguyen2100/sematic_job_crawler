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

class TopCVConfig(BaseModel):
    """Configuration for TopCV crawler"""
    
    # Base URLs and endpoints
    base_url: str = "https://www.topcv.vn"
    search_endpoint: str = "/tim-viec-lam"
    
    # Search configuration
    search_keywords: List[str] = [
        "cong-nghe-thong-tin",
        "python-developer", 
        "java-developer",
        "javascript-developer",
        "full-stack-developer"
    ]
    
    # URL Parameters
    default_params: Dict[str, str] = {
        "type_keyword": "1",  # TopCVSearchType.KEYWORD value
        "sba": "1",  # Search by all (salary, benefits, etc.)
        "sort_by": "1"  # TopCVSortBy.NEWEST value
    }
    
    # Category family mapping for IT jobs
    category_families: Dict[str, str] = {
        "it": "r257",  # Information Technology
        "software": "r257", 
        "developer": "r257",
        "programming": "r257"
    }
    
    # Pagination settings
    max_pages: int = Field(default=5, ge=1, le=20)
    jobs_per_page: int = Field(default=20, ge=1, le=50)
    start_page: int = Field(default=1, ge=1)
    
    # Request settings
    request_delay: float = Field(default=2.0, ge=0.5, le=10.0)  # Delay between requests in seconds
    timeout: int = Field(default=30, ge=10, le=60)  # Page timeout in seconds
    
    # Browser settings
    headless: bool = True
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    viewport: Dict[str, int] = {"width": 1920, "height": 1080}
    
    # Job extraction settings
    max_description_length: int = Field(default=5000, ge=100)
    required_fields: List[str] = ["title", "company_name", "original_url"]
    
    # Company page crawling
    crawl_company_details: bool = True
    company_page_timeout: int = Field(default=15, ge=5, le=30)
    
    def build_search_url(self, keyword: str, page: int = 1, category_family: Optional[str] = None) -> str:
        """Build search URL with parameters"""
        # Construct base search URL
        if category_family:
            url = f"{self.base_url}{self.search_endpoint}-{keyword}-kcr{category_family}"
        else:
            url = f"{self.base_url}{self.search_endpoint}-{keyword}"
        
        # Add parameters
        params = self.default_params.copy()
        params["page"] = str(page)
        
        if category_family:
            params["category_family"] = f"r{category_family}"
        
        # Build query string
        query_params = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{url}?{query_params}"
    
    def get_search_urls(self) -> List[str]:
        """Generate all search URLs for configured keywords and pages"""
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

# Default configuration instance
DEFAULT_TOPCV_CONFIG = TopCVConfig()

# Example configurations for different use cases
COMPREHENSIVE_CONFIG = TopCVConfig(
    search_keywords=[
        "cong-nghe-thong-tin",
        "python-developer",
        "java-developer", 
        "javascript-developer",
        "full-stack-developer",
        "backend-developer",
        "frontend-developer",
        "devops-engineer",
        "data-scientist",
        "mobile-developer"
    ],
    max_pages=10,
    request_delay=1.5
)

QUICK_CONFIG = TopCVConfig(
    search_keywords=["cong-nghe-thong-tin"],
    max_pages=2,
    request_delay=1.0,
    crawl_company_details=False
)
