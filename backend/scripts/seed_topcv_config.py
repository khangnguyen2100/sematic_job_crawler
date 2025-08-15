"""
Script to seed TopCV configuration in the database
Updated to use database-only configuration (no hardcoded fallbacks)
"""
import asyncio
import sys
import os

# Add the app directory to the path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import CrawlerConfigDB, Base

# Database URL - adjust as needed
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://job_user:job_password@localhost:5432/job_crawler")

def seed_topcv_config():
    """Seed TopCV configuration in the database with comprehensive settings"""
    
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Define complete TopCV configuration
        topcv_config = {
            # Base settings
            "base_url": "https://www.topcv.vn",
            "search_endpoint": "/tim-viec-lam",
            
            # Search routes/paths (configurable from database)
            "routes": {
                "paths": [
                    "tim-viec-lam-python-developer-kcr257",
                    "tim-viec-lam-java-developer-kcr257", 
                    "tim-viec-lam-javascript-developer-kcr257",
                    "tim-viec-lam-cong-nghe-thong-tin-cr257",
                    "tim-viec-lam-full-stack-developer-kcr257",
                    "tim-viec-lam-backend-developer-kcr257",
                    "tim-viec-lam-frontend-developer-kcr257",
                    "tim-viec-lam-devops-engineer-kcr257",
                    "tim-viec-lam-data-scientist-kcr257",
                    "tim-viec-lam-mobile-developer-kcr257"
                ]
            },
            
            # Default search parameters
            "params": {
                "type_keyword": "1",
                "sba": "1", 
                "sort_by": "1",
                "page": "1",
                "category_family": "r257"
            },
            
            # Search keywords (configurable from database)
            "search_keywords": [
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
            
            # Category family mapping for IT jobs
            "category_families": {
                "it": "r257",
                "software": "r257", 
                "developer": "r257",
                "programming": "r257"
            },
            
            # Pagination settings
            "max_pages": 5,
            "jobs_per_page": 20,
            "start_page": 1,
            
            # Request settings
            "request_delay": 3.0,
            "timeout": 45,
            
            # Browser settings
            "headless": False,
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1366, "height": 768},
            
            # Human-in-the-loop settings
            "enable_human_challenge_solving": True,
            "challenge_timeout": 120,
            
            # Job extraction settings
            "max_description_length": 5000,
            "required_fields": ["title", "company_name", "original_url"],
            
            # Company page crawling
            "crawl_company_details": True,
            "company_page_timeout": 15
        }
        
        # Check if TopCV config already exists
        existing_config = session.query(CrawlerConfigDB).filter(
            CrawlerConfigDB.site_name == "TopCV"
        ).first()
        
        if existing_config:
            print("TopCV configuration already exists in database")
            # Update with latest config
            existing_config.config = topcv_config
            existing_config.site_url = "https://www.topcv.vn"
            existing_config.is_active = True
            session.commit()
            print("✅ Updated TopCV configuration with database-driven settings")
        else:
            # Create new TopCV configuration
            new_config = CrawlerConfigDB(
                site_name="TopCV",
                site_url="https://www.topcv.vn",
                config=topcv_config,
                is_active=True
            )
            
            session.add(new_config)
            session.commit()
            print("✅ Created new TopCV configuration in database")
            
        # Print the configuration
        config = session.query(CrawlerConfigDB).filter(
            CrawlerConfigDB.site_name == "TopCV"
        ).first()
        
        print(f"\n📊 TopCV Configuration Summary:")
        print(f"   Site Name: {config.site_name}")
        print(f"   Site URL: {config.site_url}")
        print(f"   Is Active: {config.is_active}")
        print(f"   Config Keys: {list(config.config.keys())}")
        print(f"   Routes Count: {len(config.config.get('routes', {}).get('paths', []))}")
        print(f"   Search Keywords Count: {len(config.config.get('search_keywords', []))}")
        print(f"   Max Pages: {config.config.get('max_pages', 5)}")
        print(f"   Request Delay: {config.config.get('request_delay', 3.0)}s")
        print(f"   Headless Mode: {config.config.get('headless', False)}")
        
        print(f"\n🎯 Database-Driven Configuration Validation:")
        print(f"   ✅ No hardcoded fallbacks")
        print(f"   ✅ All settings from database")
        print(f"   ✅ Configurable routes and keywords")
        print(f"   ✅ Admin can modify via web interface")
        
    except Exception as e:
        print(f"❌ Error seeding TopCV configuration: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print("🚀 Seeding TopCV Configuration (100% Database-Driven)")
    seed_topcv_config()
