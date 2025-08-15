"""
Configuration Service

This service provides configuration data from the database for crawlers,
replacing hardcoded values with dynamic configuration from data sources.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.database import CrawlerConfigDB
from app.config.topcv_config import TopCVConfig, TopCVParams, TopCVRoutes
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
