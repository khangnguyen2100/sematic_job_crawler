#!/bin/bash

echo "🗄️  Database Migration Utility"

# Set script to exit on any error
set -e

# Change to the backend directory if not already there
cd "$(dirname "$0")"

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -c, --create   Create database tables (initial setup)"
    echo "  -m, --migrate  Run migration script (add missing columns)"
    echo "  -s, --seed     Seed database with initial data"
    echo "  -a, --all      Run all operations (create, migrate, seed)"
    echo ""
    echo "Examples:"
    echo "  $0 --migrate          # Run migration script only"
    echo "  $0 --all              # Run all database operations"
    echo "  $0 --create --seed    # Create tables and seed data"
}

# Function to load environment variables
load_env() {
    if [ -f ".env.local" ]; then
        echo "📝 Loading environment variables from .env.local"
        export $(grep -v '^#' .env.local | xargs)
    elif [ -f ".env" ]; then
        echo "📝 Loading environment variables from .env"
        export $(grep -v '^#' .env | xargs)
    else
        echo "⚠️  No .env.local or .env file found. Using default environment variables."
    fi

    # Set default DATABASE_URL if not provided
    if [ -z "$DATABASE_URL" ]; then
        export DATABASE_URL="postgresql://job_user:job_password@localhost:5432/job_crawler"
        echo "📊 Using default DATABASE_URL: $DATABASE_URL"
    fi
}

# Function to check if poetry is available
check_poetry() {
    if ! command -v poetry &> /dev/null; then
        echo "❌ Poetry not found. Please install Poetry first."
        exit 1
    fi
}

# Function to create database tables
create_tables() {
    echo "🏗️  Creating database tables..."
    if [ -f "init-db.sql" ]; then
        poetry run python -c "
from sqlalchemy import create_engine, text
from app.config.constants import get_database_url
import os

engine = create_engine(get_database_url())
with open('init-db.sql', 'r') as f:
    sql_content = f.read()

with engine.connect() as conn:
    for statement in sql_content.split(';'):
        if statement.strip():
            conn.execute(text(statement))
    conn.commit()
print('✅ Database tables created successfully')
"
    else
        echo "⚠️  init-db.sql not found. Skipping table creation."
    fi
}

# Function to run migrations
run_migrations() {
    echo "🔧 Running migration script..."
    if [ -f "scripts/migrate_db.py" ]; then
        poetry run python scripts/migrate_db.py
    else
        echo "⚠️  scripts/migrate_db.py not found. Skipping migrations."
    fi
}

# Function to seed database
seed_database() {
    echo "🌱 Seeding database with initial data..."
    if [ -f "scripts/seed_data_sources.py" ]; then
        poetry run python scripts/seed_data_sources.py
    else
        echo "⚠️  scripts/seed_data_sources.py not found. Skipping seeding."
    fi
}

# Parse command line arguments
CREATE_TABLES=false
RUN_MIGRATIONS=false
SEED_DATABASE=false

if [ $# -eq 0 ]; then
    echo "❌ No options provided."
    show_usage
    exit 1
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -c|--create)
            CREATE_TABLES=true
            shift
            ;;
        -m|--migrate)
            RUN_MIGRATIONS=true
            shift
            ;;
        -s|--seed)
            SEED_DATABASE=true
            shift
            ;;
        -a|--all)
            CREATE_TABLES=true
            RUN_MIGRATIONS=true
            SEED_DATABASE=true
            shift
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
echo "🚀 Starting database operations..."

load_env
check_poetry

if [ "$CREATE_TABLES" = true ]; then
    create_tables
fi

if [ "$RUN_MIGRATIONS" = true ]; then
    run_migrations
fi

if [ "$SEED_DATABASE" = true ]; then
    seed_database
fi

echo "✅ All database operations completed successfully!"
