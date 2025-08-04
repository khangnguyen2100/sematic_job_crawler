import marqo
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.config.constants import MarqoConfig, get_marqo_url
from app.models.schemas import Job, JobCreate, SearchRequest

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

    async def add_job(self, job: JobCreate) -> str:
        """Add a single job to Marqo"""
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
                lambda: self.client.index(self.index_name).add_documents(
                    job_dicts,
                    tensor_fields=["title", "description", "company_name"]
                )
            )
            return job_ids
        except Exception as e:
            print(f"Error adding jobs batch to Marqo: {e}")
            raise
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
            # Search for similar jobs using only tensor fields
            import requests
            import json
            
            search_query = f"{job.title} {job.company_name}"
            search_payload = {
                "q": search_query,
                "limit": 10,
                "searchableAttributes": ["title", "company_name"]
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
                return False
                
            results = response.json()

            # Check for exact matches
            for hit in results.get("hits", []):
                job_data = {k: v for k, v in hit.items() if not k.startswith('_')}
                if (job_data.get("original_url") == job.original_url or
                    (job_data.get("title") == job.title and 
                     job_data.get("company_name") == job.company_name)):
                    return True
            
            return False
        except Exception as e:
            print(f"Error checking duplicate job: {e}")
            return False

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
