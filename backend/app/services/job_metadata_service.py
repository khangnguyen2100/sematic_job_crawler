"""
Service for managing job metadata and duplicate checking using PostgreSQL
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.database import JobMetadataDB
from app.models.schemas import JobCreate
from app.utils.url_utils import clean_job_url


class JobMetadataService:
    """Service for fast duplicate checking using PostgreSQL job_metadata table"""
    
    @staticmethod
    def check_duplicate_by_url(db: Session, url: str) -> bool:
        """
        Check if a job URL already exists in the database.
        URLs are cleaned (parameters removed) before checking to avoid duplicates with different tracking parameters.
        
        Args:
            db: Database session
            url: Job URL to check (will be cleaned automatically)
            
        Returns:
            True if URL already exists (duplicate), False if new
        """
        try:
            if not url:
                return False
            
            # Clean the URL by removing query parameters and fragments    
            clean_url = clean_job_url(url)
            if not clean_url:
                print(f"Warning: Could not clean URL: {url}")
                return False
                
            return JobMetadataService._check_duplicate_by_clean_url(db, clean_url)
            
        except Exception as e:
            print(f"Error checking duplicate by URL: {e}")
            return False  # In case of error, allow the job to be added
    
    @staticmethod
    def _check_duplicate_by_clean_url(db: Session, clean_url: str) -> bool:
        """
        Check if a clean job URL already exists in the database.
        Internal method that expects the URL to already be cleaned.
        
        Args:
            db: Database session
            clean_url: Already cleaned job URL to check
            
        Returns:
            True if URL already exists (duplicate), False if new
        """
        try:
            if not clean_url:
                return False
                
            # Fast lookup using indexed URL column
            existing = db.query(JobMetadataDB).filter(JobMetadataDB.url == clean_url).first()
            return existing is not None
            
        except Exception as e:
            print(f"Error checking duplicate by clean URL: {e}")
            return False  # In case of error, allow the job to be added
    
    @staticmethod
    def add_job_url(db: Session, url: str) -> bool:
        """
        Add a job URL to the metadata table.
        URLs are cleaned (parameters removed) before storing to ensure consistent duplicate checking.
        
        Args:
            db: Database session
            url: Job URL to add (will be cleaned automatically)
            
        Returns:
            True if added successfully, False if already exists or error
        """
        try:
            if not url:
                return False
            
            # Clean the URL by removing query parameters and fragments
            clean_url = clean_job_url(url)
            if not clean_url:
                print(f"Warning: Could not clean URL: {url}")
                return False
                
            job_metadata = JobMetadataDB(url=clean_url)
            db.add(job_metadata)
            db.commit()
            return True
            
        except IntegrityError:
            # URL already exists (unique constraint violation)
            db.rollback()
            return False
        except Exception as e:
            print(f"Error adding job URL: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def add_job_urls_batch(db: Session, urls: List[str]) -> tuple[int, int]:
        """
        Add multiple job URLs in batch, handling duplicates gracefully.
        URLs are cleaned (parameters removed) before storing to ensure consistent duplicate checking.
        
        Args:
            db: Database session
            urls: List of job URLs to add (will be cleaned automatically)
            
        Returns:
            Tuple of (added_count, duplicate_count)
        """
        added_count = 0
        duplicate_count = 0
        
        try:
            for url in urls:
                if not url:
                    continue
                
                # Clean the URL by removing query parameters and fragments
                clean_url = clean_job_url(url)
                if not clean_url:
                    print(f"Warning: Could not clean URL, skipping: {url}")
                    continue
                    
                # Check if URL already exists
                if JobMetadataService._check_duplicate_by_clean_url(db, clean_url):
                    duplicate_count += 1
                    continue
                
                # Try to add the URL
                try:
                    job_metadata = JobMetadataDB(url=clean_url)
                    db.add(job_metadata)
                    db.flush()  # Flush but don't commit yet
                    added_count += 1
                except IntegrityError:
                    # Race condition - URL was added by another process
                    db.rollback()
                    duplicate_count += 1
                    continue
            
            # Commit all successful additions
            db.commit()
            return added_count, duplicate_count
            
        except Exception as e:
            print(f"Error in batch add job URLs: {e}")
            db.rollback()
            return added_count, duplicate_count
    
    @staticmethod
    def get_total_unique_jobs(db: Session) -> int:
        """
        Get total count of unique job URLs in the database
        
        Args:
            db: Database session
            
        Returns:
            Total count of unique job URLs
        """
        try:
            return db.query(JobMetadataDB).count()
        except Exception as e:
            print(f"Error getting total unique jobs count: {e}")
            return 0
    
    @staticmethod
    def delete_job_url(db: Session, url: str) -> bool:
        """
        Delete a job URL from the metadata table.
        URLs are cleaned (parameters removed) before deletion to match the stored format.
        
        Args:
            db: Database session
            url: Job URL to delete (will be cleaned automatically)
            
        Returns:
            True if deleted successfully, False if not found or error
        """
        try:
            if not url:
                return False
            
            # Clean the URL by removing query parameters and fragments
            clean_url = clean_job_url(url)
            if not clean_url:
                print(f"Warning: Could not clean URL: {url}")
                return False
                
            # Delete the URL record
            deleted_count = db.query(JobMetadataDB).filter(JobMetadataDB.url == clean_url).delete()
            db.commit()
            
            return deleted_count > 0
            
        except Exception as e:
            print(f"Error deleting job URL: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def delete_job_url_by_pattern(db: Session, url_pattern: str) -> int:
        """
        Delete job URLs matching a pattern (useful for cleanup)
        
        Args:
            db: Database session
            url_pattern: URL pattern to match (SQL LIKE pattern)
            
        Returns:
            Number of URLs deleted
        """
        try:
            if not url_pattern:
                return 0
                
            # Delete URLs matching the pattern
            deleted_count = db.query(JobMetadataDB).filter(
                JobMetadataDB.url.like(url_pattern)
            ).delete(synchronize_session=False)
            
            db.commit()
            return deleted_count
            
        except Exception as e:
            print(f"Error deleting job URLs by pattern: {e}")
            db.rollback()
            return 0
    
    @staticmethod
    def clear_all_job_urls(db: Session) -> int:
        """
        Clear all job URLs from the metadata table
        WARNING: This removes all job metadata!
        
        Args:
            db: Database session
            
        Returns:
            Number of URLs deleted
        """
        try:
            # Delete all records
            deleted_count = db.query(JobMetadataDB).delete()
            db.commit()
            return deleted_count
            
        except Exception as e:
            print(f"Error clearing all job URLs: {e}")
            db.rollback()
            return 0

    @staticmethod
    def cleanup_old_urls(db: Session, days_old: int = 90) -> int:
        """
        Clean up job URLs older than specified days
        
        Args:
            db: Database session
            days_old: Remove URLs older than this many days
            
        Returns:
            Number of URLs removed
        """
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Delete old records
            deleted_count = db.query(JobMetadataDB).filter(
                JobMetadataDB.created_at < cutoff_date
            ).delete()
            
            db.commit()
            return deleted_count
            
        except Exception as e:
            print(f"Error cleaning up old URLs: {e}")
            db.rollback()
            return 0
