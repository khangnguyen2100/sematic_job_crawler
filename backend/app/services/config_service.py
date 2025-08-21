"""
Configuration Service

This service provides configuration data from the database for crawlers,
replacing hardcoded values with dynamic configuration from data sources.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.database import CrawlerConfigDB
from app.config.topcv_config import TopCVConfig, TopCVParams, TopCVRoutes
from app.config.itviec_config import ITViecConfig, ITViecParams, ITViecRoutes
import logging

logger = logging.getLogger(__name__)

class ConfigService:
    """Service to manage crawler configurations from database"""
    
    @staticmethod
    def get_site_config(db: Session, site_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific site from database"""
        try:
            config_db = db.query(CrawlerConfigDB).filter(
                CrawlerConfigDB.site_name == site_name,
                CrawlerConfigDB.is_active == True
            ).first()
            
            if not config_db:
                logger.warning(f"No active configuration found for site: {site_name}")
                return None
                
            return {
                "site_name": config_db.site_name,
                "site_url": config_db.site_url,
                "config": config_db.config,
                "is_active": config_db.is_active
            }
            
        except Exception as e:
            logger.error(f"Error getting config for site {site_name}: {e}")
            return None
    
    @staticmethod
    def parse_topcv_config(site_config: Dict[str, Any]) -> TopCVConfig:
        """Parse database configuration into TopCVConfig object"""
        try:
            config_data = site_config.get("config", {})
            
            # Extract params if available
            params_data = config_data.get("params", {})
            params = TopCVParams(
                type_keyword=params_data.get("type_keyword", "1"),
                sba=params_data.get("sba", "1"),
                sort_by=params_data.get("sort_by", "1"),
                page=params_data.get("page", "1"),
                category_family=params_data.get("category_family")
            )
            
            # Extract routes if available
            routes_data = config_data.get("routes", {})
            routes = TopCVRoutes(
                paths=routes_data.get("paths", [
                    "tim-viec-lam-python-developer-kcr257",
                    "tim-viec-lam-cong-nghe-thong-tin-cr257"
                ])
            )
            
            # Create TopCVConfig with database values
            topcv_config = TopCVConfig(
                base_url=site_config.get("site_url", site_config.get("base_url")),
                params=params,
                routes=routes,
                max_pages=config_data.get("max_pages", 5),
                request_delay=config_data.get("request_delay", 3.0),
                timeout=config_data.get("timeout", 45),
                headless=config_data.get("headless", False),
                enable_human_challenge_solving=config_data.get("enable_human_challenge_solving", True),
                challenge_timeout=config_data.get("challenge_timeout", 120),
                max_description_length=config_data.get("max_description_length", 5000),
                crawl_company_details=config_data.get("crawl_company_details", True),
                company_page_timeout=config_data.get("company_page_timeout", 15)
            )
            
            return topcv_config
            
        except Exception as e:
            logger.error(f"Error parsing TopCV config: {e}")
            # No fallback configuration - must be from database only
            raise ValueError(f"Failed to parse TopCV configuration from database: {e}")
    
    @staticmethod
    def parse_itviec_config(site_config: Dict[str, Any]) -> ITViecConfig:
        """Parse database configuration into ITViecConfig object"""
        try:
            config_data = site_config.get("config", {})
            
            # Extract params if available
            params_data = config_data.get("params", {})
            params = ITViecParams(
                query=params_data.get("search", ""),
                sort=params_data.get("sort_by", "newest"),
                page=params_data.get("page", "1"),
                experience_level=params_data.get("job_level"),
                job_type=params_data.get("job_type"),
                work_mode=params_data.get("work_mode"),
                city=params_data.get("city")
            )
            
            # Extract routes if available
            routes_data = config_data.get("routes", {})
            routes = ITViecRoutes(
                paths=routes_data.get("paths", [
                    "it-jobs",
                    "jobs"
                ])
            )
            
            # Extract viewport settings
            viewport_data = config_data.get("viewport", {})
            viewport = {
                "width": viewport_data.get("width", 1366),
                "height": viewport_data.get("height", 768)
            }
            
            # Create ITViecConfig with database values
            itviec_config = ITViecConfig(
                base_url=config_data.get("base_url", site_config.get("site_url", "https://itviec.com")),
                search_endpoint=config_data.get("search_endpoint", "/it-jobs"),
                params=params,
                routes=routes,
                
                # Browser settings
                timeout=config_data.get("timeout", 45),
                headless=config_data.get("headless", False),
                viewport=viewport,
                user_agent=config_data.get("user_agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
                
                # Crawling behavior
                max_pages=config_data.get("max_pages", 3),
                start_page=config_data.get("start_page", 1),
                jobs_per_page=config_data.get("jobs_per_page", 20),
                request_delay=config_data.get("request_delay", 3.0),
                
                # Data requirements
                required_fields=config_data.get("required_fields", ["title", "company_name", "original_url"]),
                max_description_length=config_data.get("max_description_length", 5000),
                
                # Cloudflare protection settings
                challenge_timeout=config_data.get("challenge_timeout", 120),
                company_page_timeout=config_data.get("company_page_timeout", 15),
                enable_human_challenge_solving=config_data.get("enable_human_challenge_solving", True),
                crawl_company_details=config_data.get("crawl_company_details", True),
                
                # Search configuration
                search_keywords=config_data.get("search_keywords", ["nodejs", "react", "vue", "python", "java", "javascript"]),
                
                # Mappings
                experience_levels=config_data.get("experience_levels", {
                    "internship": "internship",
                    "fresher": "fresher",
                    "junior": "junior",
                    "middle": "middle",
                    "senior": "senior",
                    "manager": "manager"
                }),
                job_types=config_data.get("job_types", {
                    "fulltime": "full-time",
                    "parttime": "part-time",
                    "freelance": "freelance",
                    "contract": "contract"
                }),
                work_modes=config_data.get("work_modes", {
                    "office": "at-office",
                    "remote": "remote",
                    "hybrid": "hybrid"
                })
            )
            
            logger.info(f"✅ Parsed ITViec config: base_url={itviec_config.base_url}, headless={itviec_config.headless}, challenge_solving={itviec_config.enable_human_challenge_solving}")
            
            return itviec_config
            
        except Exception as e:
            logger.error(f"Error parsing ITViec config: {e}")
            # No fallback configuration - must be from database only
            raise ValueError(f"Failed to parse ITViec configuration from database: {e}")
    
    @staticmethod
    def get_crawler_info(db: Session, site_name: str) -> Dict[str, Any]:
        """Get crawler information (site_name, site_url, crawler_type) from database"""
        try:
            config_db = db.query(CrawlerConfigDB).filter(
                CrawlerConfigDB.site_name == site_name,
                CrawlerConfigDB.is_active == True
            ).first()
            
            if not config_db:
                logger.warning(f"No active configuration found for site: {site_name}")
                raise ValueError(f"No configuration found for site: {site_name}. Please ensure {site_name} is configured in the data sources.")
                
            return {
                "site_name": config_db.site_name,
                "site_url": config_db.site_url,
                "crawler_type": config_db.config.get("crawler_type", f"{site_name.lower()}_crawler")
            }
            
        except ValueError:
            # Re-raise configuration not found errors
            raise
        except Exception as e:
            logger.error(f"Error getting crawler info for site {site_name}: {e}")
            raise ValueError(f"Failed to load configuration for site {site_name}: {str(e)}")

# Service instance
config_service = ConfigService()
