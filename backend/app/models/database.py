from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Boolean, DECIMAL, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
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

class JobMetadataDB(Base):
    __tablename__ = "job_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(255), nullable=False, unique=True, index=True)
    source = Column(String(50), nullable=False, index=True)
    original_url = Column(Text, nullable=False)
    crawl_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # New columns for deduplication
    source_job_id = Column(String(255), index=True)
    content_hash = Column(String(64), index=True)
    title = Column(String(500))
    company_name = Column(String(200))
    description = Column(Text)
    marqo_id = Column(String(255), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class JobDuplicateDB(Base):
    """Track duplicate jobs that were detected and skipped"""
    __tablename__ = "job_duplicates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_job_id = Column(UUID(as_uuid=True), ForeignKey('job_metadata.id'), nullable=False, index=True)
    duplicate_source = Column(String(100), nullable=False)
    duplicate_source_id = Column(String(255), nullable=False)
    duplicate_url = Column(Text)
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    similarity_score = Column(DECIMAL(3,2))  # 0.00 to 1.00
    duplicate_fields = Column(JSONB)  # Which fields were duplicated
    detection_method = Column(String(50))  # 'source_id_match', 'content_hash_match', 'fuzzy_match'
    
    # Relationship
    original_job = relationship("JobMetadataDB", backref="duplicates")

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
