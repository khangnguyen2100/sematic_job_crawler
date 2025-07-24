#!/bin/bash

echo "🐍 Starting FastAPI Backend in Development Mode"

# Load environment variables (filter out comments)
export $(grep -v '^#' .env.local | xargs)

# Run with uvicorn
poetry run uvicorn app.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8002 \
    --log-level debug
