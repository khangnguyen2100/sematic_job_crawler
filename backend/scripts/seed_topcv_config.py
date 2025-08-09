"""
Script to seed TopCV configuration in the database
"""
import asyncio
import sys
import os

# Add the app directory to the path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import CrawlerConfigDB, Base
from app.config.topcv_config import DEFAULT_TOPCV_CONFIG

# Database URL - adjust as needed
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://job_user:job_password@localhost:5432/job_crawler")

def seed_topcv_config():
    """Seed TopCV configuration in the database"""
    
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Check if TopCV config already exists
        existing_config = session.query(CrawlerConfigDB).filter(
            CrawlerConfigDB.site_name == "TopCV"
        ).first()
        
        if existing_config:
            print("TopCV configuration already exists in database")
            # Update with latest default config
            existing_config.config = DEFAULT_TOPCV_CONFIG.model_dump()
            session.commit()
            print("Updated TopCV configuration with latest defaults")
        else:
            # Create new TopCV configuration
            new_config = CrawlerConfigDB(
                site_name="TopCV",
                site_url="https://www.topcv.vn",
                config=DEFAULT_TOPCV_CONFIG.model_dump(),
                is_active=True
            )
            
            session.add(new_config)
            session.commit()
            print("Created new TopCV configuration in database")
            
        # Print the configuration
        config = session.query(CrawlerConfigDB).filter(
            CrawlerConfigDB.site_name == "TopCV"
        ).first()
        
        print(f"\nTopCV Configuration:")
        print(f"Site Name: {config.site_name}")
        print(f"Site URL: {config.site_url}")
        print(f"Is Active: {config.is_active}")
        print(f"Config Keys: {list(config.config.keys())}")
        print(f"Search Keywords: {config.config.get('search_keywords', [])}")
        print(f"Max Pages: {config.config.get('max_pages', 5)}")
        
    except Exception as e:
        print(f"Error seeding TopCV configuration: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_topcv_config()
