"""
Simple duplicate checking service that returns counts without database logging
"""
import hashlib
import uuid
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from difflib import SequenceMatcher

from app.models.schemas import JobCreate
from app.models.database import JobMetadataDB


class SimpleDuplicateChecker:
    """Simple duplicate checker that returns boolean without logging"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def is_duplicate(self, job_data: JobCreate) -> Tuple[bool, str]:
        """
        Check if job is duplicate without storing anything
        Returns: (is_duplicate, reason)
        """
        # 1. Check by source and source_id (exact match)
        if hasattr(job_data, 'source_id') and job_data.source_id:
            existing_job = await self.check_by_source_id(job_data)
            if existing_job:
                return True, "source_id_match"
        
        # 2. Check by URL (common duplicate case)
        if job_data.original_url:
            existing_job = await self.check_by_url(job_data)
            if existing_job:
                return True, "url_match"
        
        # 3. Check by content hash (exact content match)
        content_hash = self.generate_content_hash(job_data)
        existing_job = await self.check_by_content_hash(content_hash)
        if existing_job:
            return True, "content_hash_match"
        
        # 4. Check by fuzzy matching (title + company similarity)
        similar_job = await self.check_by_fuzzy_match(job_data)
        if similar_job:
            similarity_score = self.calculate_similarity(similar_job, job_data)
            if similarity_score > 0.85:  # 85% similarity threshold
                return True, f"fuzzy_match_score_{similarity_score:.2f}"
        
        return False, "unique"
    
    async def check_by_source_id(self, job_data: JobCreate) -> Optional[JobMetadataDB]:
        """Check if job exists by source and source_job_id"""
        source_id = getattr(job_data, 'source_id', None)
        if not source_id:
            return None
            
        return self.db.query(JobMetadataDB).filter(
            JobMetadataDB.source == job_data.source.value,
            JobMetadataDB.source_job_id == source_id
        ).first()
    
    async def check_by_url(self, job_data: JobCreate) -> Optional[JobMetadataDB]:
        """Check if job exists by URL"""
        return self.db.query(JobMetadataDB).filter(
            JobMetadataDB.original_url == job_data.original_url
        ).first()
    
    async def check_by_content_hash(self, content_hash: str) -> Optional[JobMetadataDB]:
        """Check if job exists by content hash"""
        return self.db.query(JobMetadataDB).filter(
            JobMetadataDB.content_hash == content_hash
        ).first()
    
    def generate_content_hash(self, job_data: JobCreate) -> str:
        """Generate SHA-256 hash of job content"""
        # Include key fields that identify unique content
        content_parts = [
            job_data.title,
            job_data.company_name,
            job_data.description or '',
            getattr(job_data, 'requirements', '') or '',
            job_data.location or '',
            job_data.salary or ''
        ]
        content = '|'.join(content_parts)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def check_by_fuzzy_match(self, job_data: JobCreate) -> Optional[JobMetadataDB]:
        """Check for similar jobs using fuzzy matching"""
        # Get jobs with similar title and company
        title_words = job_data.title.split()[:3]  # First 3 words
        title_pattern = f"%{' '.join(title_words)}%"
        
        similar_jobs = self.db.query(JobMetadataDB).filter(
            JobMetadataDB.title.ilike(title_pattern),
            JobMetadataDB.company_name.ilike(f"%{job_data.company_name}%")
        ).limit(5).all()
        
        for job in similar_jobs:
            if self.calculate_similarity(job, job_data) > 0.85:
                return job
        return None
    
    def calculate_similarity(self, existing_job: JobMetadataDB, new_job: JobCreate) -> float:
        """Calculate similarity score between jobs"""
        title_sim = SequenceMatcher(None, existing_job.title or '', new_job.title).ratio()
        company_sim = SequenceMatcher(None, existing_job.company_name or '', new_job.company_name).ratio()
        
        # Weighted average: title 60%, company 40%
        return (title_sim * 0.6) + (company_sim * 0.4)
    
    async def store_new_job(self, job_data: JobCreate, content_hash: str, marqo_id: str = None) -> JobMetadataDB:
        """Store a new unique job in PostgreSQL"""
        source_id = getattr(job_data, 'source_id', None)
        
        job_entry = JobMetadataDB(
            job_id=marqo_id or str(uuid.uuid4()),
            source=job_data.source.value,
            original_url=job_data.original_url,
            source_job_id=source_id,
            content_hash=content_hash,
            title=job_data.title,
            company_name=job_data.company_name,
            description=job_data.description,
            marqo_id=marqo_id
        )
        
        self.db.add(job_entry)
        self.db.commit()
        self.db.refresh(job_entry)
        
        return job_entry
