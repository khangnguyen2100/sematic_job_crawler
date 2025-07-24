#!/bin/bash

echo "🚀 Starting Job Crawler Development Environment"

# Start databases with Docker
echo "📊 Starting PostgreSQL and Marqo..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

echo "✅ Development databases are ready!"
echo ""
echo "🔗 Services:"
echo "   PostgreSQL: localhost:5432"
echo "   Marqo:      localhost:8882"
echo ""
echo "💡 Next steps:"
echo "   1. Install backend dependencies: cd backend && poetry install"
echo "   2. Run backend: cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8002"
echo "   3. Run frontend: cd frontend && npm run dev"
echo "   4. Or use VS Code debugger (F5) to debug backend"
echo ""
