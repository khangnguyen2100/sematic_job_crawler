# Semantic Job Crawler & Search Platform

A full-stack job aggregation and semantic search platform that crawls job postings from multiple Vietnamese job sites and provides AI-powered search capabilities using vector embeddings.

## 🌟 Features

### 🕸️ Multi-Source Job Crawling
- **Automated crawling** from LinkedIn, TopCV, ITViec, and VietnamWorks
- **Scheduled execution** at 00:00 and 12:00 daily
- **Duplicate detection** to avoid redundant entries
- **Rate limiting** and respectful crawling practices

### 🔍 Semantic Search
- **Vector-based search** using Marqo and transformer models
- **Natural language queries** (e.g., "Python developer with machine learning experience")
- **Source filtering** by job site
- **Relevance-based ranking**

### 📊 Analytics & Tracking
- **User behavior tracking** (searches, clicks, views)
- **Popular jobs analytics**
- **Search pattern insights**
- **Crawler performance monitoring**

### 📥 Data Management
- **CSV import/export** functionality
- **Bulk job upload** with validation
- **Duplicate prevention**
- **Data integrity checks**

### 🎨 Modern Frontend
- **Responsive design** with TailwindCSS
- **Real-time search** with debouncing
- **Job cards** with rich metadata
- **Filter and sort** capabilities

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Databases     │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   PostgreSQL    │
│                 │    │                 │    │   Marqo         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └─────────────►│   Job Crawlers  │◄─────────────┘
                        │   (Scheduled)   │
                        └─────────────────┘
```

### Tech Stack

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS + Shadcn UI
- React Router
- Axios for API calls

**Backend:**
- Python 3.10+ with FastAPI
- Marqo for vector search
- PostgreSQL for metadata
- APScheduler for job scheduling
- SQLAlchemy ORM

**Infrastructure:**
- Docker & Docker Compose
- Poetry for Python dependencies
- nginx (production reverse proxy)

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd marqo_learning
```

### 2. Environment Setup
```bash
# Backend environment
cp backend/.env.example backend/.env

# Edit backend/.env with your settings
DATABASE_URL=postgresql://job_user:job_password@postgres:5432/job_crawler
MARQO_URL=http://marqo:8882
ALLOWED_ORIGINS=http://localhost:3000
```

### 3. Start Services
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Marqo**: http://localhost:8882

### 5. Initial Data Load
```bash
# Trigger manual crawl to populate initial data
curl -X POST http://localhost:8000/api/v1/analytics/crawler/trigger
```

## 📋 Development

### Backend Development
```bash
cd backend

# Install dependencies
poetry install

# Run development server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
poetry run pytest

# Code formatting
poetry run black .
poetry run isort .
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run linting
npm run lint
```

## 🔧 Configuration

### Backend Configuration (`backend/.env`)
```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/job_crawler

# Marqo
MARQO_URL=http://localhost:8882

# CORS
ALLOWED_ORIGINS=http://localhost:3000

# Crawler Settings
CRAWL_SCHEDULE_CRON=0 0,12 * * *
MAX_JOBS_PER_SOURCE=100

# Security
SECRET_KEY=your-secret-key-here

# Development
DEBUG=True
```

### Crawler Configuration
The crawler runs on a configurable schedule (default: daily at 00:00 and 12:00).

**Available Sources:**
- LinkedIn (limited due to anti-scraping measures)
- TopCV
- ITViec  
- VietnamWorks

**Note**: Current implementation includes mock crawlers for demonstration. Production deployment requires implementing actual web scraping with proper error handling, rate limiting, and compliance with each site's robots.txt and terms of service.

## 📊 API Endpoints

### Search & Jobs
- `POST /api/v1/search` - Semantic job search
- `GET /api/v1/jobs` - List jobs with filters
- `GET /api/v1/jobs/{id}` - Get specific job
- `POST /api/v1/jobs/{id}/click` - Track job click

### Data Upload
- `POST /api/v1/upload/csv` - Upload jobs via CSV
- `POST /api/v1/upload/json` - Upload jobs via JSON
- `GET /api/v1/upload/template` - Download CSV template

### Analytics
- `GET /api/v1/analytics/popular-jobs` - Most clicked jobs
- `GET /api/v1/analytics/search-stats` - Search analytics
- `GET /api/v1/analytics/dashboard` - Comprehensive dashboard data
- `POST /api/v1/analytics/crawler/trigger` - Manual crawl trigger

## 🎯 Usage Examples

### Search Jobs
```bash
# Semantic search
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python developer with machine learning experience",
    "sources": ["ITViec", "TopCV"],
    "limit": 10
  }'
```

### Upload Jobs via CSV
```bash
curl -X POST "http://localhost:8000/api/v1/upload/csv" \
  -F "file=@jobs.csv" \
  -F "source=TopCV"
```

### Get Analytics
```bash
# Popular jobs in last 7 days
curl "http://localhost:8000/api/v1/analytics/popular-jobs?days=7&limit=5"

# Search statistics
curl "http://localhost:8000/api/v1/analytics/search-stats?days=30"
```

## 🔒 Production Deployment

### Security Considerations
1. **Environment Variables**: Use secure secrets management
2. **Database**: Enable SSL and use strong passwords
3. **CORS**: Configure strict origins for production
4. **Rate Limiting**: Implement API rate limiting
5. **Authentication**: Add user authentication if needed

### Performance Optimization
1. **Database Indexing**: Add indexes for frequently queried fields
2. **Caching**: Implement Redis for search result caching
3. **CDN**: Use CDN for static assets
4. **Load Balancing**: Scale backend horizontally

### Example Production Docker Compose
```yaml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - backend
      - frontend

  backend:
    build: ./backend
    environment:
      - DEBUG=False
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
    deploy:
      replicas: 3

  # ... other services
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
poetry run pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm run test
```

### Integration Tests
```bash
# Test full workflow
docker-compose exec backend python -m pytest tests/integration/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for all frontend code
- Write tests for new features
- Update documentation for API changes
- Use semantic commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**1. Marqo Connection Error**
```bash
# Check Marqo health
curl http://localhost:8882/health

# Restart Marqo service
docker-compose restart marqo
```

**2. Database Connection Error**
```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready -U job_user

# View database logs
docker-compose logs postgres
```

**3. Frontend Build Issues**
```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**4. Crawler Not Running**
```bash
# Check scheduler status
curl http://localhost:8000/api/v1/analytics/crawler/status

# Trigger manual crawl
curl -X POST http://localhost:8000/api/v1/analytics/crawler/trigger
```

### Performance Issues
- Monitor Marqo memory usage (requires substantial RAM for large datasets)
- Check PostgreSQL connection pool settings
- Review crawler rate limiting settings

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Marqo Documentation](https://docs.marqo.ai/)
- [React Documentation](https://react.dev/)
- [TailwindCSS Documentation](https://tailwindcss.com/)

## ✨ Future Enhancements

- [ ] Real-time job notifications
- [ ] Advanced filtering (salary range, location radius)
- [ ] Job recommendation engine
- [ ] Email alerts for new matching jobs
- [ ] Mobile app development
- [ ] Machine learning for job categorization
- [ ] Integration with more job sites
- [ ] User accounts and saved searches
