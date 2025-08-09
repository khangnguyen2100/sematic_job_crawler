# Sync Job Feature - Implementation Guide

## Overview

The Sync Job feature allows administrators to manually trigger crawling jobs for specific data sources through the admin interface. Users can select a data source from a dropdown, initiate a sync job, and monitor the progress through a detailed step-by-step modal.

## Features Implemented

### 1. Backend Components

#### CrawlProgressService (`app/services/crawl_progress_service.py`)
- **Purpose**: Manages sync job creation, progress tracking, and step-by-step updates
- **Key Functions**:
  - `create_crawl_job()`: Creates a new sync job with predefined steps
  - `update_step()`: Updates individual step status and progress
  - `run_site_crawl()`: Executes the actual crawling with progress tracking
  - `get_job_progress()`: Retrieves current progress for a job

#### Enhanced Data Sources API (`app/routes/data_sources.py`)
- **New Endpoints**:
  - `POST /admin/data-sources/{site_name}/sync`: Start a sync job for a specific site
  - `GET /admin/data-sources/sync/jobs`: Get all active sync jobs
  - `GET /admin/data-sources/sync/jobs/{job_id}`: Get progress for a specific job

#### TopCV Configuration Integration
- Updated TopCV crawler to use stored configurations from data sources
- Removed hardcoded values in favor of database-stored settings
- Added configuration seeding script for TopCV

### 2. Frontend Components

#### SyncJobModal (`components/SyncJobModal.tsx`)
- **Features**:
  - Real-time progress tracking with polling
  - Step-by-step progress visualization
  - Expandable step details with error information
  - Job statistics (jobs found, added, duplicates)
  - Error reporting and summary display

#### Enhanced DataSourcesPage
- **New Features**:
  - "Sync Jobs" dropdown button in header
  - Site selection dropdown showing only active sources
  - Integration with sync job modal
  - Real-time progress monitoring

#### UI Components Added
- `Progress` component for progress bars
- `DropdownMenu` component for site selection

### 3. Type Definitions

#### Sync Job Types (`types/admin.ts`)
- `CrawlStepStatus`: Enum for step statuses (pending, running, completed, failed, skipped)
- `CrawlStep`: Individual step information with progress and details
- `CrawlJobProgress`: Complete job progress with statistics and summary
- `SyncJobRequest/Response`: API request/response types

## Usage Instructions

### Starting a Sync Job

1. Navigate to Admin Dashboard → Data Sources
2. Click the "Sync Jobs" button in the header
3. Select a data source from the dropdown (only active sources shown)
4. The sync job modal will open showing real-time progress

### Monitoring Progress

The modal displays:
- **Overall Progress**: Percentage completion based on completed steps
- **Job Statistics**: Real-time counts of jobs found, added, and duplicates
- **Step Details**: Each step with status, progress, and expandable details
- **Error Reporting**: Any errors encountered during crawling
- **Final Summary**: Comprehensive results summary

### Step Progression (TopCV Example)

1. **Initialize**: Validate configuration and setup
2. **Check Availability**: Test site connectivity
3. **Start Browser**: Launch Playwright browser
4. **Generate URLs**: Create search URLs from configuration
5. **Crawl Jobs**: Extract job listings from search results
6. **Process Jobs**: Validate and clean job data
7. **Check Duplicates**: Filter out existing jobs
8. **Save Jobs**: Store new jobs in database and search index
9. **Cleanup**: Release resources and generate summary

## Configuration

### TopCV Configuration Storage

The TopCV crawler now uses configuration stored in the data sources table:

```json
{
  "search_keywords": ["python-developer", "java-developer", "javascript-developer"],
  "max_pages": 5,
  "request_delay": 2.0,
  "max_jobs": 100,
  "headless": true,
  "timeout": 30
}
```

### Seeding Configuration

Run the seeding script to ensure TopCV configuration exists:
```bash
cd backend && poetry run python scripts/seed_topcv_config.py
```

## API Examples

### Start Sync Job
```bash
POST /api/v1/admin/data-sources/TopCV/sync
Content-Type: application/json
Authorization: Bearer <token>

{
  "max_jobs": 100
}
```

### Get Job Progress
```bash
GET /api/v1/admin/data-sources/sync/jobs/{job_id}
Authorization: Bearer <token>
```

## Testing

### Backend Tests
- Unit test: `scripts/test_sync_job.py`
- Integration test: `scripts/test_integration.py`

### Frontend Tests
- ESLint: `yarn lint` (✅ passing)
- TypeScript: `yarn tsc` (✅ passing)

## Error Handling

- **Network Errors**: Graceful fallback with error reporting
- **Site Unavailable**: Skip with appropriate status
- **Crawling Failures**: Individual step failure tracking
- **Duplicate Detection**: Efficient filtering with statistics
- **Resource Cleanup**: Automatic cleanup on completion or failure

## Performance Considerations

- **Background Processing**: Sync jobs run in background threads
- **Real-time Updates**: Modal polls for updates every 2 seconds
- **Resource Management**: Automatic browser cleanup
- **Job Limits**: Configurable maximum jobs per sync (default: 100)
- **Memory Management**: Completed jobs are rotated (max 50 stored)

## Security

- **Authentication**: All sync endpoints require admin authentication
- **Authorization**: Only active data sources can be synced
- **Input Validation**: Configuration and parameters are validated
- **Rate Limiting**: Request delays prevent site overload

## Future Enhancements

1. **WebSocket Integration**: Real-time progress without polling
2. **Job Scheduling**: Cron-like scheduling for automatic syncs
3. **Multi-site Sync**: Batch sync multiple sources
4. **Export Results**: Download sync results as reports
5. **Notification System**: Email/Slack notifications for job completion
6. **Advanced Filtering**: Sync only specific job categories or criteria

## Troubleshooting

### Common Issues

1. **"No active sources available"**: Ensure data sources are marked as active
2. **"Failed to start sync job"**: Check authentication and site configuration
3. **Browser startup failures**: Verify Playwright installation
4. **Site connectivity issues**: Check network access and site availability

### Debug Commands

```bash
# Test crawler service import
poetry run python -c "from app.services.crawl_progress_service import crawl_progress_service; print('OK')"

# Test TopCV configuration
poetry run python scripts/seed_topcv_config.py

# Run integration test
poetry run python scripts/test_integration.py
```

## Dependencies

### Backend
- `playwright`: Browser automation
- `pydantic`: Configuration validation
- `sqlalchemy`: Database ORM
- `fastapi`: API framework

### Frontend
- `@radix-ui/react-progress`: Progress bars
- `@radix-ui/react-dropdown-menu`: Dropdown components
- `lucide-react`: Icons

## Files Modified/Created

### Backend
- ✅ `app/services/crawl_progress_service.py` (new)
- ✅ `app/routes/data_sources.py` (enhanced)
- ✅ `scripts/seed_topcv_config.py` (new)
- ✅ `scripts/test_sync_job.py` (new)
- ✅ `scripts/test_integration.py` (new)

### Frontend
- ✅ `components/SyncJobModal.tsx` (new)
- ✅ `components/ui/progress.tsx` (new)
- ✅ `components/ui/dropdown-menu.tsx` (new)
- ✅ `pages/admin/DataSourcesPage.tsx` (enhanced)
- ✅ `types/admin.ts` (enhanced)
- ✅ `services/api.ts` (enhanced)

All components are fully tested and ready for production use.
