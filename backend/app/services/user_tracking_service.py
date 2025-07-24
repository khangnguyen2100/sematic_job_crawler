"""
Enhanced User Tracking Service
Handles device fingerprinting and anonymous user identification
"""

from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import hashlib
import json
from fastapi import Request

Base = declarative_base()

class UserSessionDB(Base):
    """Enhanced user session tracking with device fingerprinting"""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    user_fingerprint = Column(String(255), nullable=False, index=True)
    ip_address = Column(INET, nullable=False)
    user_agent = Column(Text)
    device_info = Column(JSONB)
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_interactions = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

class JobInteractionDB(Base):
    """Track specific job interactions with enhanced user identification"""
    __tablename__ = "job_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_fingerprint = Column(String(255), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    job_id = Column(String(255), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False)  # 'view', 'click', 'apply', 'save'
    interaction_data = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

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

class UserTrackingService:
    """Service for enhanced anonymous user tracking"""
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Extract client IP handling proxies and load balancers"""
        # Check for forwarded IP headers (common with proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
            
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate unique session ID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_user_fingerprint(device_info: Dict[str, Any], ip: str, user_agent: str) -> str:
        """Generate stable user fingerprint from device characteristics"""
        # Combine stable device characteristics
        fingerprint_data = {
            "screen_resolution": device_info.get("screen", ""),
            "timezone": device_info.get("timezone", ""),
            "language": device_info.get("language", ""),
            "platform": device_info.get("platform", ""),
            "ip_subnet": ".".join(ip.split(".")[:3]) + ".0",  # Use subnet for some privacy
            "user_agent_hash": hashlib.md5(user_agent.encode()).hexdigest()[:16]
        }
        
        # Create stable hash
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]
    
    def identify_user(self, request: Request, device_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Identify user with enhanced tracking information"""
        ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Get device fingerprint from header or generate from device_info
        fingerprint = request.headers.get("x-device-fingerprint")
        if not fingerprint and device_info:
            fingerprint = self.generate_user_fingerprint(device_info, ip, user_agent)
        
        # Get or generate session ID
        session_id = request.cookies.get("session_id")
        if not session_id:
            session_id = self.generate_session_id()
        
        return {
            "user_fingerprint": fingerprint or "anonymous",
            "session_id": session_id,
            "ip_address": ip,
            "user_agent": user_agent,
            "device_info": device_info or {}
        }
    
    async def track_job_interaction(
        self, 
        db_session,
        user_info: Dict[str, Any],
        job_id: str,
        interaction_type: str,
        interaction_data: Optional[Dict[str, Any]] = None
    ):
        """Track a job interaction with full user context"""
        interaction = JobInteractionDB(
            user_fingerprint=user_info["user_fingerprint"],
            session_id=user_info["session_id"],
            job_id=job_id,
            interaction_type=interaction_type,
            interaction_data=interaction_data or {},
            ip_address=user_info["ip_address"],
            user_agent=user_info["user_agent"]
        )
        
        db_session.add(interaction)
        await db_session.commit()
        return interaction
    
    async def get_user_job_history(
        self, 
        db_session,
        user_fingerprint: str,
        limit: int = 50
    ) -> list:
        """Get user's job interaction history"""
        query = db_session.query(JobInteractionDB).filter(
            JobInteractionDB.user_fingerprint == user_fingerprint
        ).order_by(JobInteractionDB.created_at.desc()).limit(limit)
        
        return query.all()
    
    async def get_job_interaction_status(
        self,
        db_session,
        user_fingerprint: str,
        job_ids: list
    ) -> Dict[str, Dict[str, Any]]:
        """Get interaction status for multiple jobs for a user"""
        query = db_session.query(JobInteractionDB).filter(
            JobInteractionDB.user_fingerprint == user_fingerprint,
            JobInteractionDB.job_id.in_(job_ids)
        )
        
        interactions = query.all()
        
        # Group by job_id and aggregate interaction types
        job_status = {}
        for interaction in interactions:
            job_id = interaction.job_id
            if job_id not in job_status:
                job_status[job_id] = {
                    "viewed": False,
                    "clicked": False,
                    "applied": False,
                    "saved": False,
                    "view_count": 0,
                    "last_interaction": None
                }
            
            # Update status based on interaction type
            if interaction.interaction_type == "view":
                job_status[job_id]["viewed"] = True
                job_status[job_id]["view_count"] += 1
            elif interaction.interaction_type == "click":
                job_status[job_id]["clicked"] = True
            elif interaction.interaction_type == "apply":
                job_status[job_id]["applied"] = True
            elif interaction.interaction_type == "save":
                job_status[job_id]["saved"] = True
            
            # Update last interaction time
            if (not job_status[job_id]["last_interaction"] or 
                interaction.created_at > job_status[job_id]["last_interaction"]):
                job_status[job_id]["last_interaction"] = interaction.created_at
        
        return job_status

# Default crawler configurations for pre-configured sites
DEFAULT_CRAWLER_CONFIGS = [
    {
        "site_name": "TopCV",
        "site_url": "https://www.topcv.vn",
        "config": {
            "base_url": "https://www.topcv.vn",
            "search_endpoint": "/tim-viec-lam",
            "selectors": {
                "job_list": ".job-item",
                "job_title": ".job-title a",
                "company": ".company-name",
                "location": ".job-location",
                "salary": ".job-salary",
                "description": ".job-description"
            },
            "pagination": {
                "type": "click",
                "selector": ".pagination .next",
                "max_pages": 50
            },
            "rate_limit": {
                "requests_per_minute": 30,
                "delay_between_requests": 2
            },
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }
    },
    {
        "site_name": "ITViec",
        "site_url": "https://itviec.com",
        "config": {
            "base_url": "https://itviec.com",
            "search_endpoint": "/jobs",
            "selectors": {
                "job_list": ".job_content",
                "job_title": ".title a",
                "company": ".company-name",
                "location": ".location",
                "salary": ".salary",
                "description": ".job-description"
            },
            "pagination": {
                "type": "url",
                "pattern": "?page={page}",
                "max_pages": 100
            },
            "rate_limit": {
                "requests_per_minute": 20,
                "delay_between_requests": 3
            },
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }
    },
    {
        "site_name": "VietnamWorks",
        "site_url": "https://www.vietnamworks.com",
        "config": {
            "base_url": "https://www.vietnamworks.com",
            "search_endpoint": "/jobs-search",
            "selectors": {
                "job_list": ".job-item",
                "job_title": ".job-title",
                "company": ".company",
                "location": ".location",
                "salary": ".salary",
                "description": ".summary"
            },
            "pagination": {
                "type": "click",
                "selector": ".next-page",
                "max_pages": 50
            },
            "rate_limit": {
                "requests_per_minute": 25,
                "delay_between_requests": 2.5
            },
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }
    }
]
