import hashlib
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from difflib import SequenceMatcher
from datetime import datetime

from app.models.schemas import JobCreate
from app.models.database import JobMetadataDB, JobDuplicateDB


class JobDeduplicationService:
    """Service to handle job deduplication and prevent duplicate storage"""
    
    def __init__(self, db: Session):
        self.db = db
        
    async def check_and_store_job(self, job_data: JobCreate, marqo_id: str = None) -> Tuple[bool, Optional[str]]:
        """
        Check if job exists and store if unique
        Returns: (is_new_job, job_id_or_reason)
        """
        # 1. Check by source and source_id (exact match)
        if hasattr(job_data, 'source_id') and job_data.source_id:
            existing_job = await self.check_by_source_id(job_data)
            if existing_job:
                await self.log_duplicate(existing_job.id, job_data, "source_id_match")
                return False, f"Duplicate found by source ID: {existing_job.id}"
        
        # 2. Check by content hash (exact content match)
        content_hash = self.generate_content_hash(job_data)
        existing_job = await self.check_by_content_hash(content_hash)
        if existing_job:
            await self.log_duplicate(existing_job.id, job_data, "content_hash_match")
            return False, f"Duplicate found by content hash: {existing_job.id}"
        
        # 3. Check by fuzzy matching (title + company similarity)
        similar_job = await self.check_by_fuzzy_match(job_data)
        if similar_job:
            similarity_score = self.calculate_similarity(similar_job, job_data)
            if similarity_score > 0.85:  # 85% similarity threshold
                await self.log_duplicate(
                    similar_job.id, 
                    job_data, 
                    "fuzzy_match", 
                    similarity_score
                )
                return False, f"Similar job found (score: {similarity_score}): {similar_job.id}"
        
        # 4. Job is unique, store it
        new_job = await self.store_new_job(job_data, content_hash, marqo_id)
        return True, str(new_job.id)
    
    async def check_by_source_id(self, job_data: JobCreate) -> Optional[JobMetadataDB]:
        """Check if job exists by source and source_job_id"""
        source_id = getattr(job_data, 'source_id', None)
        if not source_id:
            return None
            
        return self.db.query(JobMetadataDB).filter(
            JobMetadataDB.source == job_data.source.value,
            JobMetadataDB.source_job_id == source_id
        ).first()
    
    async def check_by_content_hash(self, content_hash: str) -> Optional[JobMetadataDB]:
        """Check if job exists by content hash"""
        return self.db.query(JobMetadataDB).filter(
            JobMetadataDB.content_hash == content_hash
        ).first()
    
    def generate_content_hash(self, job_data: JobCreate) -> str:
        """Generate SHA-256 hash of job content"""
        content = f"{job_data.title}|{job_data.company_name}|{job_data.description}"
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
    
    async def log_duplicate(self, original_job_id: str, duplicate_job: JobCreate, detection_method: str, similarity_score: float = None):
        """Log a duplicate job for tracking"""
        source_id = getattr(duplicate_job, 'source_id', None)
        
        duplicate_fields = {
            'title': duplicate_job.title,
            'company_name': duplicate_job.company_name,
            'source': duplicate_job.source.value
        }
        
        duplicate_log = JobDuplicateDB(
            original_job_id=original_job_id,
            duplicate_source=duplicate_job.source.value,
            duplicate_source_id=source_id or '',
            duplicate_url=duplicate_job.original_url,
            similarity_score=similarity_score,
            duplicate_fields=duplicate_fields,
            detection_method=detection_method
        )
        
        self.db.add(duplicate_log)
        self.db.commit()
    
    async def store_new_job(self, job_data: JobCreate, content_hash: str, marqo_id: str = None) -> JobMetadataDB:
        """Store a new unique job"""
        source_id = getattr(job_data, 'source_id', None)
        
        job_entry = JobMetadataDB(
            job_id=marqo_id or str(datetime.now().timestamp()),
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

    async def get_duplicate_stats(self) -> dict:
        """Get statistics about duplicates"""
        total_duplicates = self.db.query(JobDuplicateDB).count()
        duplicates_by_method = self.db.query(
            JobDuplicateDB.detection_method,
            self.db.func.count(JobDuplicateDB.id)
        ).group_by(JobDuplicateDB.detection_method).all()
        
        return {
            'total_duplicates': total_duplicates,
            'by_method': {method: count for method, count in duplicates_by_method}
        }
