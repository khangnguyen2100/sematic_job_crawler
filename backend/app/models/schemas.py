from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class JobSource(str, Enum):
    LINKEDIN = "LinkedIn"
    TOPCV = "TopCV"
    ITVIEC = "ITViec"
    VIETNAMWORKS = "VietnamWorks"
    OTHER = "Other"

class Job(BaseModel):
    id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1, max_length=200)
    posted_date: datetime
    source: JobSource
    original_url: str = Field(..., min_length=1)
    location: Optional[str] = None
    salary: Optional[str] = None
    job_type: Optional[str] = None  # Full-time, Part-time, Contract, etc.
    experience_level: Optional[str] = None  # Junior, Senior, etc.
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class JobCreate(BaseModel):
    title: str
    description: str
    company_name: str
    posted_date: datetime
    source: JobSource
    original_url: str
    location: Optional[str] = None
    salary: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    company_name: Optional[str] = None
    posted_date: Optional[datetime] = None
    source: Optional[JobSource] = None
    original_url: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    sources: Optional[List[JobSource]] = None
    limit: Optional[int] = Field(default=10, ge=1, le=100)
    offset: Optional[int] = Field(default=0, ge=0)

class SearchResponse(BaseModel):
    jobs: List[Job]
    total: int
    limit: int
    offset: int
    query: str

class UserInteraction(BaseModel):
    id: Optional[str] = None
    user_id: str  # IP address or device ID
    job_id: str
    action: str  # "view", "click", "search"
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime

class UploadResponse(BaseModel):
    message: str
    processed_jobs: int
    errors: List[str] = []
