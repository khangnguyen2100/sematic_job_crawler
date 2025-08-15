"""
Backend Configuration Constants
This file centralizes all hardcoded values to make them configurable
"""
import os
from typing import Dict, Any

# Server Configuration
class ServerConfig:
    DEFAULT_HOST = "0.0.0.0"
    DEFAULT_API_PORT = 8003  # Updated to use available port
    DEFAULT_MARQO_PORT = 8882
    
    # Development server info for documentation
    DEV_SERVER_URL = f"http://localhost:{DEFAULT_API_PORT}"
    DEV_FRONTEND_URL = "http://localhost:3030"  # Updated to match frontend port
    
    # Default CORS origins
    DEFAULT_CORS_ORIGINS = "http://localhost:3030,http://127.0.0.1:3030"

# Database Configuration
class DatabaseConfig:
    DEFAULT_DATABASE_URL = "postgresql://username:password@localhost:5432/job_crawler"
    
    # Connection settings
    POOL_SIZE = 10
    MAX_OVERFLOW = 20
    POOL_TIMEOUT = 30

# Marqo Configuration  
class MarqoConfig:
    DEFAULT_URL = f"http://localhost:8882"
    DEFAULT_MODEL = "hf/all-MiniLM-L6-v2"
    INDEX_NAME = "job-index"
    
    # Index settings
    DEFAULT_SEARCHABLE_ATTRIBUTES = ["title", "description", "company_name"]
    DEFAULT_FILTER_ATTRIBUTES = ["source", "location", "job_type"]

# Authentication Configuration
class AuthConfig:
    # JWT settings
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS = 8
    DEFAULT_JWT_SECRET = "your-super-secret-jwt-key-change-in-production"
    
    # Default admin credentials (should be changed in production)
    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_PASSWORD = "123123"

# Job Sources Configuration - DEPRECATED
# All site configurations should be loaded from database via crawler_configs table
# This hardcoded configuration has been removed to enforce 100% database-driven configuration
# JOB_SOURCES_CONFIG = {
#     ... configurations moved to database ...
# }

# Crawler Configuration
class CrawlerConfig:
    DEFAULT_PAGE_LIMIT = 5
    DEFAULT_REQUEST_DELAY = 1.0  # seconds
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_TIMEOUT = 30  # seconds
    
    # User agent for requests
    DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; JobCrawler/1.0)"

# Analytics Configuration
class AnalyticsConfig:
    DEFAULT_DAYS_RANGE = 7
    DEFAULT_LIMIT = 10
    
    # Interaction types
    INTERACTION_TYPES = ["search", "view", "click"]

# Environment variable helpers
def get_database_url() -> str:
    """Get database URL from environment or use default"""
    return os.getenv("DATABASE_URL", DatabaseConfig.DEFAULT_DATABASE_URL)

def get_marqo_url() -> str:
    """Get Marqo URL from environment or use default"""
    return os.getenv("MARQO_URL", MarqoConfig.DEFAULT_URL)

def get_jwt_secret() -> str:
    """Get JWT secret from environment or use default"""
    return os.getenv("JWT_SECRET", AuthConfig.DEFAULT_JWT_SECRET)

def get_admin_credentials() -> tuple[str, str]:
    """Get admin credentials from environment or use defaults"""
    username = os.getenv("ADMIN_USERNAME", AuthConfig.DEFAULT_ADMIN_USERNAME)
    password = os.getenv("ADMIN_PASSWORD", AuthConfig.DEFAULT_ADMIN_PASSWORD)
    return username, password

def get_cors_origins() -> list[str]:
    """Get CORS origins from environment or use default"""
    origins = os.getenv("ALLOWED_ORIGINS", ServerConfig.DEFAULT_CORS_ORIGINS)
    return origins.split(",")

def get_api_port() -> int:
    """Get API port from environment or use default"""
    return int(os.getenv("API_PORT", ServerConfig.DEFAULT_API_PORT))

def get_api_host() -> str:
    """Get API host from environment or use default"""
    return os.getenv("API_HOST", ServerConfig.DEFAULT_HOST)
