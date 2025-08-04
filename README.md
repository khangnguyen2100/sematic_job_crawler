# Gemini Project Overview: Job Search Platform

This document provides a summary of the project structure, key technologies, and guidance on how to run, configure, and customize the application.

## 1. Project Summary

This is a full-stack job search application designed to crawl job postings from various sources, index them for powerful semantic search using Marqo, and provide a dual-interface for job seekers and administrators.

- **Core Functionality:** Crawling, data indexing, semantic search, and system administration.
- **User Interfaces:** 
  1. A public-facing job search page.
  2. A comprehensive admin dashboard to manage crawlers, view logs, and oversee job data.

## 2. Key Technologies

- **Backend:** Python, FastAPI
- **Frontend:** TypeScript, React, Vite
- **Search:** Marqo (Vector Search)
- **Crawling:** Playwright
- **Containerization:** Docker & Docker Compose
- **Database:** SQL (likely PostgreSQL)

## 3. How to Run the Project

The application is containerized for easy setup.

1.  **Prerequisites:** Docker and Docker Compose must be installed.
2.  **Environment Variables:** Copy the backend environment template:
    ```bash
    cp backend/.env.example backend/.env
    ```
3.  **Fill in `.env`:** Populate `backend/.env` with your database credentials, Marqo URL, and any other required settings.
4.  **Start Services:** Use the provided script to build and start all services (backend, frontend, database, Marqo):
    ```bash
    ./start-dev.sh
    ```

## 4. How to Customize and Configure

Customization is primarily done by modifying configuration files or extending the existing codebase in specific directories.

### Key Configuration Files:

- **`docker-compose.yml`:** Defines all running services, their ports, and environment variables. Modify this to change service definitions or add new ones.
- **`backend/.env`:** (You create this from `.env.example`) The central place for all backend secrets and environment-specific settings like database connection strings and API keys.
- **`backend/app/config/`:** Contains application-level constants and crawler-specific configurations (`topcv_config.py`).

### Extending the Application:

- **To Add a New Crawler:**
  1. Create a new crawler class in `backend/app/crawlers/` inheriting from `BaseCrawler`.
  2. Implement the required methods for navigation and data extraction.
  3. Add configuration for your new crawler in `backend/app/config/`.
  4. Register the new crawler in `backend/app/crawlers/crawler_manager.py`.

- **To Add a New API Endpoint:**
  1. Add a new router file in `backend/app/routes/`.
  2. Define your new endpoints using FastAPI's decorators.
  3. Include the new router in `backend/app/main.py`.

- **To Add a New Frontend Page/Component:**
  1. Create new `.tsx` files in `frontend/src/pages/` or `frontend/src/components/`.
  2. Use the existing components in `frontend/src/components/ui/` for a consistent look and feel.
  3. Add routing for new pages in `frontend/src/App.tsx`.
