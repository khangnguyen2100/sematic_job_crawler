#!/usr/bin/env python3
"""
Database migration script to add missing columns to job_metadata table
"""

import os
from sqlalchemy import create_engine, text
from app.config.constants import get_database_url

def migrate_database():
    """Add missing columns to job_metadata table"""
    DATABASE_URL = get_database_url()
    engine = create_engine(DATABASE_URL)
    
    # Add missing columns if they don't exist
    migration_queries = [
        "ALTER TABLE job_metadata ADD COLUMN IF NOT EXISTS posted_date TIMESTAMP;",
        "ALTER TABLE job_metadata ADD COLUMN IF NOT EXISTS location VARCHAR(200);",
        "ALTER TABLE job_metadata ADD COLUMN IF NOT EXISTS salary VARCHAR(100);", 
        "ALTER TABLE job_metadata ADD COLUMN IF NOT EXISTS job_type VARCHAR(50);",
        "ALTER TABLE job_metadata ADD COLUMN IF NOT EXISTS experience_level VARCHAR(50);",
        "ALTER TABLE job_metadata ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
    ]
    
    try:
        with engine.connect() as connection:
            for query in migration_queries:
                print(f"Executing: {query}")
                connection.execute(text(query))
                connection.commit()
        
        print("✅ Database migration completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    migrate_database()
