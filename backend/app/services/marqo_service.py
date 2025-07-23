import marqo
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.models.schemas import Job, JobCreate, SearchRequest

class MarqoService:
    def __init__(self):
        self.marqo_url = os.getenv("MARQO_URL", "http://localhost:8882")
        self.client = None
        self.index_name = "jobs"
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
                # Try new API first (Marqo 2.22.0+)
                self.client.create_index(
                    index_name=self.index_name,
                    settings={
                        "model": "hf/all-MiniLM-L6-v2",
                        "normalize_embeddings": True,
                        "text_preprocessing": {
                            "split_length": 2,
                            "split_overlap": 0,
                            "split_method": "sentence"
                        },
                        "treat_urls_and_pointers_as_images": False
                    }
                )
            except TypeError:
                # Fall back to old API (Marqo < 2.22.0)
                self.client.create_index(
                    index_name=self.index_name,
                    model="hf/all-MiniLM-L6-v2"
                )

    async def add_job(self, job: JobCreate) -> str:
        """Add a single job to Marqo"""
        job_id = str(uuid.uuid4())
        job_dict = self._job_to_dict(job, job_id)
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.index(self.index_name).add_documents([job_dict])
            )
            return job_id
        except Exception as e:
            print(f"Error adding job to Marqo: {e}")
            raise

    async def add_jobs_batch(self, jobs: List[JobCreate]) -> List[str]:
        """Add multiple jobs to Marqo in batch"""
        job_ids = []
        job_dicts = []
        
        for job in jobs:
            job_id = str(uuid.uuid4())
            job_ids.append(job_id)
            job_dicts.append(self._job_to_dict(job, job_id))
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.index(self.index_name).add_documents(job_dicts)
            )
            return job_ids
        except Exception as e:
            print(f"Error adding jobs batch to Marqo: {e}")
            raise

    async def search_jobs(self, search_request: SearchRequest) -> Dict[str, Any]:
        """Search jobs using semantic search"""
        try:
            # Prepare search filters
            filter_string = None
            if search_request.sources:
                source_filters = [f"source:{source.value}" for source in search_request.sources]
                filter_string = " OR ".join(source_filters)

            # Perform search
            search_results = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.index(self.index_name).search(
                    q=search_request.query,
                    limit=search_request.limit,
                    offset=search_request.offset,
                    filter_string=filter_string,
                    searchable_attributes=["title", "description", "company_name"]
                )
            )

            # Convert results to job objects
            jobs = []
            for hit in search_results.get("hits", []):
                job_data = hit.get("_source", {})
                try:
                    job = Job(**job_data)
                    job.id = hit.get("_id")
                    jobs.append(job)
                except Exception as e:
                    print(f"Error converting search result to job: {e}")
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
                job_data = result.get("_source", {})
                job = Job(**job_data)
                job.id = job_id
                return job
            return None
        except Exception as e:
            print(f"Error getting job by ID: {e}")
            return None

    async def check_duplicate_job(self, job: JobCreate) -> bool:
        """Check if a job already exists based on title, company, and URL"""
        try:
            # Search for similar jobs
            search_query = f"{job.title} {job.company_name}"
            results = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.index(self.index_name).search(
                    q=search_query,
                    limit=10,
                    searchable_attributes=["title", "company_name", "original_url"]
                )
            )

            # Check for exact matches
            for hit in results.get("hits", []):
                job_data = hit.get("_source", {})
                if (job_data.get("original_url") == job.original_url or
                    (job_data.get("title") == job.title and 
                     job_data.get("company_name") == job.company_name)):
                    return True
            
            return False
        except Exception as e:
            print(f"Error checking duplicate job: {e}")
            return False

    async def delete_job(self, job_id: str) -> bool:
        """Delete a job by ID"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.index(self.index_name).delete_documents([job_id])
            )
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

    def _job_to_dict(self, job: JobCreate, job_id: str) -> Dict[str, Any]:
        """Convert JobCreate to dictionary for Marqo"""
        now = datetime.utcnow()
        return {
            "_id": job_id,
            "title": job.title,
            "description": job.description,
            "company_name": job.company_name,
            "posted_date": job.posted_date.isoformat(),
            "source": job.source.value,
            "original_url": job.original_url,
            "location": job.location,
            "salary": job.salary,
            "job_type": job.job_type,
            "experience_level": job.experience_level,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
