# Copilot Instructions - Job Search Platform

## Architecture Overview

This is a **semantic job search platform** with three core layers:
- **Frontend**: React/TypeScript with dual interfaces (public search + admin dashboard)
- **Backend**: FastAPI with crawler orchestration, semantic search, and analytics  
- **Data Layer**: PostgreSQL + Marqo vector database for semantic search

Key architectural pattern: **Service-oriented with async background processing**
- Global services (`marqo_service`, `job_scheduler`) initialized in `app/main.py` lifespan
- Crawlers inherit from `BaseCrawler` and are orchestrated by `CrawlerManager`
- All search operations go through `MarqoService` for vector embeddings

## Critical Development Patterns

### Service Initialization & Dependencies
Services are globally initialized in `main.py` lifespan and accessed via dependency functions:
```python
# In main.py
marqo_service = MarqoService()
job_scheduler = JobScheduler(marqo_service)

# In routes
def get_marqo_service():
    return marqo_service
```

### Adding New Job Crawlers
1. Inherit from `BaseCrawler` in `app/crawlers/`
2. Implement `crawl_jobs()` and `is_available()` methods
3. Add to `CrawlerManager.crawlers` list 
4. Configuration goes in `app/config/` following `topcv_config.py` pattern

### Database + Vector Search Integration
- PostgreSQL stores job metadata and relationships
- Marqo handles semantic search with embeddings
- Jobs are added to both via `MarqoService.add_jobs_batch()`
- Deduplication happens at both DB and vector level

## Development Workflow

### Running the Stack
Use VS Code tasks for development:
- **🐍 Run Backend**: Starts Docker services + Poetry backend with hot reload
- **⚛️ Run Frontend**: Yarn dev server with Vite

Backend runs on `:8002`, Frontend on `:3030`, Marqo on `:8882`, PostgreSQL on `:5432`

### Configuration Management
- Environment: `backend/.env` (copy from `.env.example`)
- Constants: `backend/app/config/constants.py` for hardcoded values
- Crawler configs: `backend/app/config/*_config.py` files

### Key Testing/Debug Commands
```bash
# Backend in Poetry environment
cd backend && poetry run python -m pytest
cd backend && poetry run uvicorn app.main:app --reload

# Test specific crawler
cd backend && poetry run python test_topcv_integration.py

# Check services health
curl http://localhost:8002/health
curl http://localhost:8882/health

# Frontend linting (REQUIRED after any frontend changes)
cd frontend && yarn lint

# TypeScript compilation check (REQUIRED after any frontend changes)
cd frontend && yarn tsc
```

**⚠️ IMPORTANT**: Always run both `yarn lint` AND `yarn tsc` after making frontend changes. ESLint must pass with zero warnings AND TypeScript must compile without errors before considering any frontend task complete.

## Frontend Architecture

React Router structure:
- `/` → Job search (public)
- `/admin/*` → Admin dashboard with nested routes in `AdminLayout`

Key patterns:
- API calls via `services/api.ts` using Axios
- UI components from `components/ui/` (shadcn/ui pattern)
- Type definitions in `types/` directory

### Frontend Code Quality Requirements

**CRITICAL**: When making ANY changes to frontend code, you MUST run both ESLint and TypeScript compilation checks and fix all errors before completing the task:

```bash
# Run from frontend directory
cd frontend && yarn lint
cd frontend && yarn tsc
# OR alternatively
cd frontend && npx eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0
cd frontend && npx tsc --noEmit
```

**Required workflow for frontend changes**:
1. Make your code changes
2. Run `yarn tsc` to check for TypeScript compilation errors
3. Fix any TypeScript errors found
4. Run `yarn lint` to check for ESLint errors
5. Fix any ESLint errors found
6. Verify both `yarn tsc` and `yarn lint` pass with no errors/warnings
7. Only then consider the task complete

**Common fixes needed**:
- **TypeScript errors**: Undefined properties, type mismatches, missing type annotations
- **Unused variables**: prefix with `_` (e.g., `_unusedVar`)
- **Missing dependencies** in useEffect: add to dependency array or use ESLint disable comment
- **TypeScript `any` types**: replace with proper types when possible
- **Import/export issues**: ensure all imports are used
- **Null/undefined safety**: add proper type guards and optional chaining

**ESLint Configuration**: The project uses `@typescript-eslint/parser` with React hooks and TypeScript rules enabled.
**TypeScript Configuration**: Strict mode enabled with comprehensive type checking.

## Backend Route Organization

Routes are modular in `app/routes/`:
- `search.py` → Semantic search endpoints
- `jobs.py` → CRUD operations
- `analytics.py` → Dashboard data + manual crawler triggers
- `admin.py` → Authentication and admin functions  
- `upload.py` → Bulk CSV/JSON imports

Each route file follows FastAPI router pattern and is included in `main.py`.

## Scheduler & Background Jobs

`JobScheduler` (APScheduler) runs:
- Daily crawls at 00:00 and 12:00 UTC
- Manual triggers via `POST /api/v1/analytics/crawler/trigger`
- Graceful shutdown in app lifespan

## Common Integration Points

- **Marqo Index**: `job-index` with structured schema in `MarqoService._init_sync()`
- **Database Models**: SQLAlchemy models in `models/database.py`, Pydantic schemas in `models/schemas.py`
- **CORS**: Configured for `localhost:3030` in development
- **Error Handling**: Consistent patterns across routes with proper HTTP status codes
