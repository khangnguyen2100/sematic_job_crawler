from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from app.config.constants import ServerConfig, get_cors_origins
from app.routes import search, jobs, upload, analytics, admin, crawl_logs, data_sources
from app.services.marqo_service import MarqoService
from app.scheduler.job_scheduler import JobScheduler
from app.models.database import init_db

# Load environment variables
load_dotenv()

# Global services
marqo_service = None
job_scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global marqo_service, job_scheduler
    
    # Initialize database
    await init_db()
    
    # Initialize Marqo service
    marqo_service = MarqoService()
    await marqo_service.initialize()
    
    # Initialize and start scheduler
    job_scheduler = JobScheduler(marqo_service)
    job_scheduler.start()
    
    yield
    
    # Shutdown
    if job_scheduler:
        job_scheduler.shutdown()

app = FastAPI(
    title="Job Crawler & Search API",
    description="""
    ## 🔍 Semantic Job Search Platform
    
    A comprehensive job aggregation and semantic search platform that crawls job postings 
    from multiple Vietnamese job sites and provides AI-powered search capabilities.
    
    ### 🌟 Features:
    * **Semantic Search**: AI-powered job search using vector embeddings
    * **Multi-Source Crawling**: Automated crawling from LinkedIn, TopCV, ITViec, VietnamWorks
    * **Analytics Dashboard**: User behavior tracking and job performance analytics
    * **Bulk Import**: CSV/JSON bulk job upload with validation
    * **Scheduled Jobs**: Automated daily crawling at 00:00 and 12:00
    
    ### 🚀 Quick Start:
    1. **Search Jobs**: Use `POST /api/v1/search` with natural language queries
    2. **Upload Jobs**: Use `POST /api/v1/upload/csv` for bulk job imports
    3. **View Analytics**: Check `GET /api/v1/analytics/dashboard` for insights
    4. **Trigger Crawl**: Manual crawling via `POST /api/v1/analytics/crawler/trigger`
    
    ### 📚 Documentation:
    - **Swagger UI**: This interactive documentation
    - **ReDoc**: Alternative documentation at `/redoc`
    - **OpenAPI Schema**: Raw schema at `/openapi.json`
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI endpoint
    redoc_url="/redoc",  # ReDoc endpoint
    openapi_url="/openapi.json",  # OpenAPI schema endpoint
    contact={
        "name": "Job Crawler API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": ServerConfig.DEV_SERVER_URL,
            "description": "Development server"
        }
    ],
    tags_metadata=[
        {
            "name": "search",
            "description": "🔍 Semantic search operations for job discovery",
            "externalDocs": {
                "description": "Search Documentation",
                "url": "https://docs.example.com/search",
            },
        },
        {
            "name": "jobs",
            "description": "💼 Job management and retrieval operations",
        },
        {
            "name": "upload",
            "description": "📤 Bulk data import operations via CSV/JSON",
        },
        {
            "name": "analytics",
            "description": "📊 Analytics, reporting, and crawler management",
        },
        {
            "name": "admin",
            "description": "🔒 Admin dashboard and management operations (requires authentication)",
        },
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trust host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Global dependency to access services
def get_marqo_service():
    return marqo_service

def get_job_scheduler():
    return job_scheduler

# Include routers
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
app.include_router(crawl_logs.router, prefix="/api/v1/admin/crawl-logs", tags=["admin", "crawl-logs"])
app.include_router(data_sources.router, prefix="/api/v1", tags=["admin", "data-sources"])

@app.get("/")
async def root():
    return {"message": "Job Crawler & Search API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
