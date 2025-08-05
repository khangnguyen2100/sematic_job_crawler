#!/usr/bin/env python3
"""
Data Sources Seeding Script
This script initializes the database with the standard job crawler data sources.
Run this script to automatically add TopCV, LinkedIn, ITViec, and VietnamWorks configurations.
"""

import asyncio
import json
from sqlalchemy.orm import Session
from app.models.database import SessionLocal, CrawlerConfigDB
from app.config.constants import JOB_SOURCES_CONFIG

def get_data_source_configs():
    """Define the standard data source configurations"""
    return [
        {
            "site_name": "TopCV",
            "site_url": "https://www.topcv.vn",
            "config": {
                "search_keywords": [
                    "cong-nghe-thong-tin",
                    "python-developer", 
                    "java-developer",
                    "javascript-developer",
                    "full-stack-developer"
                ],
                "max_pages": 5,
                "jobs_per_page": 20,
                "start_page": 1,
                "request_delay": 2.0,
                "timeout": 30,
                "headless": True,
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "viewport": {"width": 1920, "height": 1080},
                "max_description_length": 5000,
                "required_fields": ["title", "company_name", "original_url"],
                "crawl_company_details": True,
                "company_page_timeout": 15,
                "default_params": {
                    "type_keyword": "1",
                    "sba": "1",
                    "sort_by": "1"
                },
                "category_families": {
                    "it": "r257",
                    "software": "r257", 
                    "developer": "r257",
                    "programming": "r257"
                }
            },
            "is_active": True
        },
        {
            "site_name": "LinkedIn",
            "site_url": "https://www.linkedin.com",
            "config": {
                "search_keywords": [
                    "software developer",
                    "python developer", 
                    "java developer",
                    "javascript developer",
                    "full stack developer",
                    "frontend developer",
                    "backend developer"
                ],
                "max_pages": 3,
                "jobs_per_page": 25,
                "request_delay": 3.0,
                "timeout": 30,
                "headless": True,
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "viewport": {"width": 1920, "height": 1080},
                "max_description_length": 8000,
                "required_fields": ["title", "company_name", "original_url"],
                "location_filters": ["Vietnam", "Ho Chi Minh City", "Hanoi"],
                "experience_levels": ["entry", "mid", "senior"]
            },
            "is_active": True
        },
        {
            "site_name": "ITViec",
            "site_url": "https://itviec.com",
            "config": {
                "search_keywords": ["nodejs", "react", "vue", "python", "java"],
                "max_pages": 3,
                "jobs_per_page": 20,
                "request_delay": 2.0,
                "timeout": 20,
                "headless": True,
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "viewport": {"width": 1920, "height": 1080},
                "max_description_length": 5000,
                "required_fields": ["title", "company_name", "original_url"]
            },
            "is_active": True
        },
        {
            "site_name": "VietnamWorks",
            "site_url": "https://www.vietnamworks.com",
            "config": {
                "search_keywords": ["backend", "frontend", "fullstack", "developer"],
                "max_pages": 2,
                "jobs_per_page": 20,
                "request_delay": 2.5,
                "timeout": 25,
                "headless": True,
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "viewport": {"width": 1920, "height": 1080},
                "max_description_length": 5000,
                "required_fields": ["title", "company_name", "original_url"]
            },
            "is_active": True
        }
    ]

def seed_data_sources():
    """Seed the database with standard data source configurations"""
    db = SessionLocal()
    try:
        configs = get_data_source_configs()
        
        for config_data in configs:
            # Check if already exists
            existing = db.query(CrawlerConfigDB).filter(
                CrawlerConfigDB.site_name == config_data["site_name"]
            ).first()
            
            if existing:
                print(f"✓ {config_data['site_name']} already exists, skipping...")
                continue
            
            # Create new configuration
            new_config = CrawlerConfigDB(
                site_name=config_data["site_name"],
                site_url=config_data["site_url"],
                config=config_data["config"],
                is_active=config_data["is_active"]
            )
            
            db.add(new_config)
            db.commit()
            db.refresh(new_config)
            
            print(f"✓ Added {config_data['site_name']} configuration")
        
        print(f"\n🎉 Data source seeding completed successfully!")
        
        # Show summary
        total_sources = db.query(CrawlerConfigDB).count()
        active_sources = db.query(CrawlerConfigDB).filter(CrawlerConfigDB.is_active == True).count()
        print(f"📊 Total data sources: {total_sources}")
        print(f"📊 Active data sources: {active_sources}")
        
    except Exception as e:
        print(f"❌ Error seeding data sources: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 Seeding data sources...")
    seed_data_sources()
