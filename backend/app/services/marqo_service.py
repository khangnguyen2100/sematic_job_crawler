import marqo
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session

from app.config.constants import MarqoConfig, get_marqo_url
from app.models.schemas import Job, JobCreate, SearchRequest
from app.services.job_metadata_service import JobMetadataService

class MarqoService:
    def __init__(self):
        self.marqo_url = get_marqo_url()
        self.client = None
        self.index_name = MarqoConfig.INDEX_NAME
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def initialize(self):
        """Initialize Marqo client and create index if it doesn't exist"""
        try:
            # Run synchronous Marqo operations in thread pool
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self._init_sync
            )
            print(f"Marqo service initialized successfully at {self.marqo_url}")
        except Exception as e:
            print(f"Error initializing Marqo service: {e}")
            raise

    def _init_sync(self):
        """Synchronous initialization"""
        self.client = marqo.Client(url=self.marqo_url)
        
        # Create index if it doesn't exist
        try:
            self.client.get_index(self.index_name)
        except Exception:
            # Index doesn't exist, create it
            try:
                # Try new API first (Marqo 2.22.0+) - create structured index
                self.client.create_index(
                    index_name=self.index_name,
                    settings={
                        "type": "structured",
                        "model": "hf/all-MiniLM-L6-v2",
                        "normalize_embeddings": True,
                        "text_preprocessing": {
                            "split_length": 2,
                            "split_overlap": 0,
                            "split_method": "sentence"
                        },
                        "treat_urls_and_pointers_as_images": False,
                        "allFields": [
                            {"name": "title", "type": "text", "features": ["lexical_search", "filter"]},
                            {"name": "description", "type": "text", "features": ["lexical_search", "filter"]},
                            {"name": "company_name", "type": "text", "features": ["lexical_search", "filter"]},
                            {"name": "posted_date", "type": "text", "features": ["filter"]},
                            {"name": "source", "type": "text", "features": ["filter"]},
                            {"name": "original_url", "type": "text", "features": ["filter"]},
                            {"name": "source_id", "type": "text", "features": ["filter"]},
                            {"name": "content_hash", "type": "text", "features": ["filter"]},
                            {"name": "location", "type": "text", "features": ["filter"]},
                            {"name": "salary", "type": "text", "features": ["filter"]},
                            {"name": "job_type", "type": "text", "features": ["filter"]},
                            {"name": "experience_level", "type": "text", "features": ["filter"]},
                            {"name": "created_at", "type": "text", "features": ["filter"]},
                            {"name": "updated_at", "type": "text", "features": ["filter"]}
                        ],
                        "tensorFields": ["title", "description", "company_name"]
                    }
                )
            except (TypeError, Exception):
                # Fall back to old API (Marqo < 2.22.0) or create unstructured index
                self.client.create_index(
                    index_name=self.index_name,
                    model="hf/all-MiniLM-L6-v2"
                )

    async def add_job(self, job: JobCreate, db: Optional[Session] = None) -> str:
        """Add a single job to Marqo (after duplicate check should be done)"""
        job_id = str(uuid.uuid4())
        job_dict = self._job_to_dict(job, job_id)
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.index(self.index_name).add_documents(
                    [job_dict],
                    tensor_fields=["title", "description", "company_name"]
                )
            )
            
            # Add URL to job metadata for future duplicate checking
            if db and job.original_url:
                JobMetadataService.add_job_url(db, job.original_url)
            
            return job_id
        except Exception as e:
            print(f"Error adding job to Marqo: {e}")
            raise

    async def add_jobs_batch(self, jobs: List[JobCreate], db: Optional[Session] = None) -> List[str]:
        """Add multiple jobs to Marqo in batch (after duplicate check should be done)"""
        job_ids = []
        job_dicts = []
        urls_to_add = []
        
        for job in jobs:
            job_id = str(uuid.uuid4())
            job_ids.append(job_id)
            job_dicts.append(self._job_to_dict(job, job_id))
            
            # Collect URLs for metadata batch insert
            if job.original_url:
                urls_to_add.append(job.original_url)
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.index(self.index_name).add_documents(
                    job_dicts,
                    tensor_fields=["title", "description", "company_name"]
                )
            )
            
            # Add URLs to job metadata for future duplicate checking
            if db and urls_to_add:
                JobMetadataService.add_job_urls_batch(db, urls_to_add)
            
            return job_ids
        except Exception as e:
            print(f"Error adding jobs batch to Marqo: {e}")
            raise
            raise

    async def search_jobs(self, search_request: SearchRequest) -> Dict[str, Any]:
        """Search jobs using semantic search"""
        try:
            # Prepare search filters
            filter_string = None
            if search_request.sources:
                source_filters = [f"source:{source.value}" for source in search_request.sources]
                filter_string = " OR ".join(source_filters)

            # Perform search using direct HTTP request to handle version compatibility
            import requests
            import json
            
            search_payload = {
                "q": search_request.query,
                "limit": search_request.limit,
                "offset": search_request.offset,
                "searchableAttributes": ["title", "description", "company_name"]
            }
            
            if filter_string:
                search_payload["filter"] = filter_string
                
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: requests.post(
                    f"{self.marqo_url}/indexes/{self.index_name}/search",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(search_payload)
                )
            )
            
            if response.status_code != 200:
                raise Exception(f"Search request failed: {response.text}")
                
            search_results = response.json()

            # Convert results to job objects
            jobs = []
            for hit in search_results.get("hits", []):
                # For direct HTTP API, job data is in the hit itself, not in _source
                job_data = {k: v for k, v in hit.items() if not k.startswith('_')}
                try:
                    job = Job(**job_data)
                    job.id = hit.get("_id")
                    # Add search score from Marqo
                    job.search_score = hit.get("_score", 0.0)
                    jobs.append(job)
                except Exception as e:
                    print(f"Error converting search result to job: {e}")
                    print(f"Hit data: {hit}")
                    continue

            return {
                "jobs": jobs,
                "total": len(jobs),
                "limit": search_request.limit,
                "offset": search_request.offset,
                "query": search_request.query
            }

        except Exception as e:
            print(f"Error searching jobs: {e}")
            raise

    async def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """Get a job by its ID"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.index(self.index_name).get_document(job_id)
            )
            
            if result:
                job = Job(**result)
                job.id = job_id
                return job
            return None
        except Exception as e:
            print(f"Error getting job by ID: {e}")
            return None

    def check_duplicate_job(self, job: JobCreate, db: Session) -> bool:
        """
        Check if a job already exists using PostgreSQL job_metadata table
        This is much faster than checking Marqo index
        
        Args:
            job: Job to check for duplicates
            db: Database session
            
        Returns:
            True if job is duplicate, False if new
        """
        try:
            # Primary duplicate check using original_url
            if job.original_url:
                return JobMetadataService.check_duplicate_by_url(db, job.original_url)
            
            # Fallback: if no original_url, create a synthetic URL from job data
            # This handles cases where crawlers don't provide original_url
            synthetic_url = self._generate_synthetic_url(job)
            return JobMetadataService.check_duplicate_by_url(db, synthetic_url)
            
        except Exception as e:
            print(f"Error checking duplicate job: {e}")
            return False  # In case of error, allow the job to be added
    
    def _generate_synthetic_url(self, job) -> str:
        """
        Generate a synthetic URL for jobs without original_url
        Uses job content to create a unique identifier
        Accepts both Job and JobCreate objects
        """
        import hashlib
        
        # Handle both Job and JobCreate objects
        source = job.source.value if hasattr(job.source, 'value') else job.source
        title = job.title
        company_name = job.company_name
        location = getattr(job, 'location', '') or ''
        
        # Create a unique identifier from job content
        content = f"{source}|{title}|{company_name}|{location}"
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Create synthetic URL
        return f"synthetic://{source}/{content_hash}"

    async def check_duplicate_job_legacy(self, job: JobCreate) -> bool:
        """
        Legacy method: Check if a job already exists based on Marqo search
        This method is slower and kept for backward compatibility
        Use check_duplicate_job() with PostgreSQL instead
        """
        try:
            import requests
            import json
            
            # 1. Check by source + original_url (primary duplicate check)
            if job.original_url:
                filter_query = f"source:{job.source.value} AND original_url:{job.original_url}"
                
                search_payload = {
                    "q": "*",  # Get all matching filter
                    "limit": 1,
                    "filter": filter_query
                }
                
                response = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: requests.post(
                        f"{self.marqo_url}/indexes/{self.index_name}/search",
                        headers={"Content-Type": "application/json"},
                        data=json.dumps(search_payload)
                    )
                )
                
                if response.status_code == 200:
                    results = response.json()
                    if results.get("hits") and len(results["hits"]) > 0:
                        return True  # Duplicate found by source + URL
            
            # 2. Check by source + source_id if available
            source_id = getattr(job, 'source_id', None)
            if source_id:
                filter_query = f"source:{job.source.value} AND source_id:{source_id}"
                
                search_payload = {
                    "q": "*",
                    "limit": 1,
                    "filter": filter_query
                }
                
                response = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: requests.post(
                        f"{self.marqo_url}/indexes/{self.index_name}/search",
                        headers={"Content-Type": "application/json"},
                        data=json.dumps(search_payload)
                    )
                )
                
                if response.status_code == 200:
                    results = response.json()
                    if results.get("hits") and len(results["hits"]) > 0:
                        return True  # Duplicate found by source + source_id
            
            # 3. Check by content hash as final fallback
            import hashlib
            content = f"{job.title}|{job.company_name}|{job.description}"
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            filter_query = f"content_hash:{content_hash}"
            
            search_payload = {
                "q": "*",
                "limit": 1,
                "filter": filter_query
            }
            
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: requests.post(
                    f"{self.marqo_url}/indexes/{self.index_name}/search",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(search_payload)
                )
            )
            
            if response.status_code == 200:
                results = response.json()
                if results.get("hits") and len(results["hits"]) > 0:
                    return True  # Duplicate found by content hash
            
            return False  # No duplicates found
            
        except Exception as e:
            print(f"Error checking duplicate job: {e}")
            return False  # In case of error, allow the job to be added

    async def recreate_index(self) -> bool:
        """Recreate the index with proper tensor fields configuration"""
        try:
            # Delete existing index if it exists
            try:
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: self.client.delete_index(self.index_name)
                )
                print(f"Deleted existing index: {self.index_name}")
            except Exception as e:
                print(f"Index {self.index_name} didn't exist or couldn't be deleted: {e}")
            
            # Recreate the index with proper configuration
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self._create_index_sync
            )
            print(f"Recreated index: {self.index_name}")
            return True
        except Exception as e:
            print(f"Error recreating index: {e}")
            return False

    def _create_index_sync(self):
        """Create index synchronously with proper tensor fields"""
        try:
            # For older Marqo versions (like 2.16.1), use unstructured index
            # The key is to provide tensor_fields when adding documents
            self.client.create_index(
                index_name=self.index_name,
                model="hf/all-MiniLM-L6-v2"
            )
        except Exception as e:
            print(f"Error creating index: {e}")
            raise

    async def delete_job(self, job_id: str, db: Optional[Session] = None) -> bool:
        """Delete a job by ID from both Marqo and PostgreSQL metadata"""
        job_url = None
        
        try:
            # First, try to get the job to retrieve its URL before deletion
            if db:
                try:
                    job = await self.get_job_by_id(job_id)
                    if job:
                        if hasattr(job, 'original_url') and job.original_url:
                            job_url = job.original_url
                        else:
                            # Generate synthetic URL if no original_url
                            job_url = self._generate_synthetic_url(job)
                except Exception as e:
                    print(f"Warning: Could not retrieve job before deletion (will try to clean up metadata): {e}")
            
            # Delete from Marqo (always attempt this)
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.index(self.index_name).delete_documents([job_id])
            )
            
            # Delete from PostgreSQL metadata if we have the URL and database session
            if db and job_url:
                deleted = JobMetadataService.delete_job_url(db, job_url)
                if deleted:
                    print(f"Successfully deleted job URL from metadata: {job_url}")
                else:
                    print(f"Job URL not found in metadata or already deleted: {job_url}")
            elif db:
                print("Warning: Could not determine job URL for metadata cleanup")
            
            return True
        except Exception as e:
            print(f"Error deleting job: {e}")
            return False

    async def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the job index"""
        try:
            stats = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.index(self.index_name).get_stats()
            )
            return stats
        except Exception as e:
            print(f"Error getting index stats: {e}")
            return {}

    async def clear_all_documents(self) -> bool:
        """Clear all documents from the Marqo index"""
        try:
            # Get all document IDs in batches due to Marqo limit
            import requests
            import json
            
            all_document_ids = []
            offset = 0
            limit = 1000  # Marqo's maximum limit
            
            while True:
                # Search for documents to get their IDs
                search_payload = {
                    "q": "*",
                    "limit": limit,
                    "offset": offset,
                    "searchableAttributes": ["title"]
                }
                
                response = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: requests.post(
                        f"{self.marqo_url}/indexes/{self.index_name}/search",
                        headers={"Content-Type": "application/json"},
                        data=json.dumps(search_payload)
                    )
                )
                
                if response.status_code != 200:
                    print(f"Failed to search for documents to delete: {response.text}")
                    return False
                
                search_results = response.json()
                hits = search_results.get("hits", [])
                
                if not hits:
                    break  # No more documents
                
                batch_ids = [hit.get("_id") for hit in hits if hit.get("_id")]
                all_document_ids.extend(batch_ids)
                
                print(f"Found {len(batch_ids)} documents (total: {len(all_document_ids)})")
                
                # If we got fewer results than the limit, we're done
                if len(hits) < limit:
                    break
                
                offset += limit
            
            if not all_document_ids:
                print("No documents found to delete")
                return True
            
            print(f"Found total of {len(all_document_ids)} documents to delete")
            
            # Delete documents in batches to avoid overwhelming the system
            batch_size = 100
            total_deleted = 0
            
            for i in range(0, len(all_document_ids), batch_size):
                batch = all_document_ids[i:i + batch_size]
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        lambda: self.client.index(self.index_name).delete_documents(batch)
                    )
                    total_deleted += len(batch)
                    print(f"Deleted batch of {len(batch)} documents ({total_deleted}/{len(all_document_ids)})")
                except Exception as e:
                    print(f"Error deleting batch: {e}")
                    continue
            
            print(f"Successfully deleted {total_deleted} documents from Marqo")
            return True
            
        except Exception as e:
            print(f"Error clearing all documents: {e}")
            return False

    def _job_to_dict(self, job: JobCreate, job_id: str) -> Dict[str, Any]:
        """Convert JobCreate to dictionary for Marqo"""
        import hashlib
        
        now = datetime.utcnow()
        
        # Generate content hash for duplicate detection
        content = f"{job.title}|{job.company_name}|{job.description}"
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        return {
            "_id": job_id,
            "title": job.title,
            "description": job.description,
            "company_name": job.company_name,
            "posted_date": job.posted_date.isoformat(),
            "source": job.source.value,
            "original_url": job.original_url,
            "source_id": getattr(job, 'source_id', None) or "",
            "content_hash": content_hash,
            "location": job.location,
            "salary": job.salary,
            "job_type": job.job_type,
            "experience_level": job.experience_level,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
