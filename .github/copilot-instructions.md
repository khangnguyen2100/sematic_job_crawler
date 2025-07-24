# AI Copilot Instructions for Semantic Job Search Platform

## 🎯 Project Overview
This is a **semantic job search platform** with FastAPI backend, React frontend, and vector search capabilities using Marqo. The platform crawls Vietnamese job sites and provides AI-powered search through natural language queries.

## 🏗️ Architecture & Key Components

### Hybrid Development Setup
- **Databases**: Run PostgreSQL & Marqo in Docker (`docker-compose.dev.yml`)
- **Backend**: Local development with Poetry, hot reload, VS Code debugging
- **Frontend**: Local Vite development server with proxy to backend

### Core Services Architecture
```
MarqoService (vector search) ↔ CrawlerManager → BaseCrawler implementations
     ↕                                    ↕
AnalyticsService ↔ PostgreSQL DB ← SQLAlchemy models
```

## 🔧 Development Workflows

### Essential Commands
```bash
# Start databases only
./start-dev.sh

# Backend development
cd backend && ./run-dev.sh
# OR use VS Code: F5 for debugging, Ctrl+Shift+P → "🐍 Run Backend (Local)"

# Frontend development  
cd frontend && yarn dev

# Stop services
./stop-dev.sh
```

### VS Code Integration
- **Launch configs**: `🐍 Debug FastAPI Backend` & `🚀 Run FastAPI with Uvicorn`
- **Tasks**: Start/stop services, run backend/frontend locally
- **Environment**: Auto-loaded from `backend/.env.local` (filters comments with `grep -v '^#'`)

## 🎯 Critical Patterns & Conventions

### Port Configuration
- **Backend**: Always use port **8002** (not 8000)
- **Frontend**: Always use port **3030** (not 3000)
- **CORS**: Configure for `http://localhost:3030` and `http://127.0.0.1:3030`

### SQLAlchemy Model Requirements
- **NEVER use `metadata` as column name** - reserved by SQLAlchemy. Use `interaction_metadata` instead
- Models in `backend/app/models/database.py` use `interaction_metadata = Column(Text)`

### Marqo Version Compatibility
```python
# Always handle both old/new Marqo API versions:
try:
    # Try new API (2.22.0+)
    self.client.create_index(index_name=name, settings={...})
except TypeError:
    # Fall back to old API
    self.client.create_index(index_name=name, model="hf/all-MiniLM-L6-v2")
```

### FastAPI Dependency Injection Pattern
```python
# All route files use this pattern:
def get_marqo_service():
    from app.main import marqo_service
    return marqo_service

def get_analytics_service():
    return AnalyticsService()
```

### Frontend Module System
- **Package.json**: `"type": "module"` - use ES modules everywhere
- **Config files**: Use `export default` not `module.exports`
- **Path aliases**: `@/*` maps to `./src/*` via Vite config

## 📁 Key File Locations

### Backend Structure
- **Routes**: `backend/app/routes/{search,jobs,upload,analytics}.py`
- **Services**: `backend/app/services/{marqo_service,analytics_service}.py`
- **Models**: `backend/app/models/{schemas,database}.py`
- **Crawlers**: `backend/app/crawlers/{base_crawler,job_crawlers,crawler_manager}.py`

### Configuration & Environment
- **Dev environment**: `backend/.env.local` (comments filtered out)
- **VS Code debug**: `.vscode/launch.json` (uses `debugpy`, not `python` type)
- **Database**: PostgreSQL connection via SQLAlchemy, tables auto-created on startup

## 🔍 Search & Vector Operations

### Marqo Integration Pattern
```python
# Always use executor for sync Marqo operations:
result = await asyncio.get_event_loop().run_in_executor(
    self.executor,
    lambda: self.client.index(self.index_name).search(...)
)
```

### Job Data Flow
1. **Crawlers** → Mock implementations with realistic data structure
2. **MarqoService.add_job()** → Converts `JobCreate` to dict, stores in vector DB
3. **Search** → Semantic search via `searchable_attributes=["title", "description", "company_name"]`
4. **Analytics** → All interactions tracked in PostgreSQL

## 🐛 Common Issues & Solutions

### Poetry Package Mode Error
```toml
# In pyproject.toml, always include:
[tool.poetry]
package-mode = false

# In Dockerfile:
RUN poetry install --only=main --no-root
```

### Port Conflicts
```bash
# Kill existing processes:
pkill -f uvicorn
lsof -ti:8000 | xargs kill -9
```

### Import Errors
- Missing `BackgroundTasks` from `fastapi`
- Missing `get_db` from `app.models.database`
- Use `Job` not `JobResponse` for response models

## 📊 Analytics & Tracking
- **User tracking**: IP-based via `get_user_id(request)`
- **Interactions**: `{"search", "view", "click"}` with metadata JSON
- **Background tasks**: CSV processing, bulk operations

## 🎨 Frontend Specifics
- **Proxy setup**: `/api` → `http://localhost:8002` via Vite config
- **UI framework**: Shadcn components with Tailwind CSS
- **State management**: React hooks, no external state library
