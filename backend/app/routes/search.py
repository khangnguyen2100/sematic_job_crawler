from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List

from app.models.schemas import SearchRequest, SearchResponse, Job
from app.services.marqo_service import MarqoService
from app.services.analytics_service import AnalyticsService
from app.models.database import get_db
from app.utils.user_tracking import get_user_id

router = APIRouter()

# Dependency injection
def get_marqo_service():
    from app.main import marqo_service
    return marqo_service

def get_analytics_service():
    return AnalyticsService()

@router.post(
    "/search", 
    response_model=SearchResponse,
    summary="🔍 Semantic Job Search",
    description="Search jobs using AI-powered semantic search with natural language queries",
    response_description="List of matching jobs with relevance ranking",
    tags=["search"]
)
async def search_jobs(
    search_request: SearchRequest,
    request: Request,
    marqo_service: MarqoService = Depends(get_marqo_service),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    db = Depends(get_db)
):
    """
    ## Semantic Job Search
    
    Perform AI-powered semantic search across all job postings using vector embeddings.
    
    ### How it works:
    - Uses transformer models to understand job queries semantically
    - Searches job titles, descriptions, and company names
    - Returns results ranked by semantic similarity
    
    ### Query Examples:
    ```
    "Python developer with machine learning experience"
    "Frontend React developer remote work"
    "Senior backend engineer fintech startup"
    "Data scientist AI computer vision"
    ```
    
    ### Features:
    - **Semantic matching**: Finds relevant jobs even without exact keyword matches
    - **Source filtering**: Filter by specific job platforms (LinkedIn, TopCV, etc.)
    - **Pagination**: Control result limits and offsets
    - **Analytics tracking**: All searches are automatically tracked
    """
    try:
        # Get user ID for tracking
        user_id = get_user_id(request)
        
        # Handle empty query by providing recent jobs
        if not search_request.query.strip():
            # For empty queries, return recent jobs
            search_request.query = "*"  # Wildcard search for recent jobs
        
        # Perform search
        results = await marqo_service.search_jobs(search_request)
        
        # Track search interaction
        analytics_service.track_user_interaction(
            db=db,
            user_id=user_id,
            job_id="",  # No specific job for search
            action="search",
            metadata={
                "query": search_request.query,
                "sources": [s.value for s in search_request.sources] if search_request.sources else None,
                "limit": search_request.limit,
                "offset": search_request.offset
            }
        )
        
        return SearchResponse(**results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/search/suggestions")
async def get_search_suggestions(
    query: str = "",
    limit: int = 5
):
    """Get search suggestions based on query"""
    # This is a placeholder - in a real implementation, you might:
    # - Use a suggestion service
    # - Query popular searches from analytics
    # - Use autocomplete from job titles/companies
    
    suggestions = [
        "Python developer",
        "Frontend developer",
        "Full stack engineer",
        "DevOps engineer",
        "Data scientist",
        "Backend developer",
        "React developer",
        "Node.js developer",
        "Java developer",
        "Machine learning engineer"
    ]
    
    if query:
        # Filter suggestions based on query
        filtered = [s for s in suggestions if query.lower() in s.lower()]
        return {"suggestions": filtered[:limit]}
    
    return {"suggestions": suggestions[:limit]}
