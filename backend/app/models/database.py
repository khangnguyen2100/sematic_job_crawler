from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Boolean, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
import uuid
from datetime import datetime
import os

from app.config.constants import get_database_url

# Database configuration
DATABASE_URL = get_database_url()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class UserInteractionDB(Base):
    __tablename__ = "user_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    job_id = Column(String(255), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    interaction_metadata = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

class CrawlLogDB(Base):
    """Track crawler requests and responses for monitoring"""
    __tablename__ = "crawl_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_name = Column(String(100), nullable=False, index=True)
    site_url = Column(Text, nullable=False)
    request_url = Column(Text, nullable=False)
    crawler_type = Column(String(50), nullable=False, index=True)
    request_method = Column(String(10), nullable=False, default='GET')
    request_headers = Column(JSONB)
    response_status = Column(Integer, index=True)
    response_time_ms = Column(Integer)
    response_size_bytes = Column(Integer)
    jobs_found = Column(Integer, default=0)
    jobs_processed = Column(Integer, default=0)
    jobs_stored = Column(Integer, default=0)
    jobs_duplicated = Column(Integer, default=0)
    error_message = Column(Text)
    error_details = Column(JSONB)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime)

class CrawlStatisticsDB(Base):
    """Daily aggregated crawler statistics"""
    __tablename__ = "crawl_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_name = Column(String(100), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    total_jobs_found = Column(Integer, default=0)
    total_jobs_stored = Column(Integer, default=0)
    total_jobs_duplicated = Column(Integer, default=0)
    average_response_time_ms = Column(DECIMAL(10,2))
    total_data_size_mb = Column(DECIMAL(10,2))
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)

class CrawlerConfigDB(Base):
    """Store crawler configurations for different job sites"""
    __tablename__ = "crawler_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_name = Column(String(100), nullable=False, unique=True)
    site_url = Column(Text, nullable=False)
    config = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CrawlHistoryDB(Base):
    """Store detailed crawl session history and progress tracking"""
    __tablename__ = "crawl_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(255), nullable=False, unique=True, index=True)
    site_name = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)  # running, completed, failed, cancelled
    
    # Crawl configuration
    crawl_config = Column(JSONB)  # Store the config used for this crawl
    
    # Detailed step tracking
    steps = Column(JSONB)  # Store all steps with their status, timing, and details
    
    # Summary statistics
    total_jobs_found = Column(Integer, default=0)
    total_jobs_added = Column(Integer, default=0)
    total_duplicates = Column(Integer, default=0)
    total_urls_processed = Column(Integer, default=0)
    
    # Timing information
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime)
    duration_seconds = Column(DECIMAL(10,2))
    
    # Error tracking
    errors = Column(JSONB)  # Store any errors that occurred
    summary = Column(JSONB)  # Store final summary information
    
    # Metadata
    triggered_by = Column(String(100))  # manual, scheduled, api
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

async def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
