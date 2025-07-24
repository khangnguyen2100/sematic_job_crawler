# 📋 TODO List - Job Search Platform Enhancements

## Overview
This file contains detailed implementation tasks for enhancing the job search platform with crawler configuration management, improved user tracking, job interaction history, UI improvements, and real data integration.

---

## 🛠️ Task 1: Crawler Configuration Management Page

### **Objective**
Create an admin page for managing crawler configurations for different job sites with a card-based interface and configuration dialogs.

### **Implementation Plan**

#### **1.1 Database Schema**
Create a new table to store crawler configurations:

```sql
CREATE TABLE crawler_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_name VARCHAR(100) NOT NULL UNIQUE,
    site_url TEXT NOT NULL,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Config JSON Structure:**
```json
{
    "base_url": "https://www.topcv.vn",
    "search_endpoint": "/tim-viec-lam",
    "job_list_selector": ".job-item",
    "job_title_selector": ".job-title",
    "company_selector": ".company-name",
    "location_selector": ".job-location",
    "description_selector": ".job-description",
    "pagination": {
        "type": "click", // or "url"
        "selector": ".next-page",
        "max_pages": 50
    },
    "rate_limit": {
        "requests_per_minute": 30,
        "delay_between_requests": 2
    },
    "headers": {
        "User-Agent": "Mozilla/5.0...",
        "Accept": "text/html,application/xhtml+xml"
    },
    "filters": {
        "keywords": ["python", "react", "nodejs"],
        "locations": ["ho-chi-minh", "ha-noi"],
        "experience_levels": ["junior", "senior"]
    }
}
```

#### **1.2 Backend Implementation**

**Files to create/modify:**
- `backend/app/models/database.py` - Add CrawlerConfigDB model
- `backend/app/routes/crawler_config.py` - New API routes
- `backend/app/schemas/schemas.py` - Add crawler config schemas
- `backend/app/services/crawler_config_service.py` - Business logic

**API Endpoints:**
```python
# GET /admin/crawler-configs - List all configurations
# POST /admin/crawler-configs - Create new configuration
# PUT /admin/crawler-configs/{config_id} - Update configuration
# DELETE /admin/crawler-configs/{config_id} - Delete configuration
# POST /admin/crawler-configs/{config_id}/test - Test configuration
# POST /admin/crawler-configs/{config_id}/toggle - Enable/disable
```

#### **1.3 Frontend Implementation**

**Files to create:**
- `frontend/src/pages/CrawlerConfigPage.tsx` - Main configuration page
- `frontend/src/components/CrawlerConfigCard.tsx` - Individual site card
- `frontend/src/components/CrawlerConfigDialog.tsx` - Configuration dialog
- `frontend/src/types/crawler.ts` - TypeScript types

**UI Components:**
- **Cards Grid**: Display each site as a card with status indicators
- **Configuration Dialog**: Modal with tabs for different config sections
- **Test Mode**: Button to test crawler configuration
- **Status Indicators**: Active/inactive, last crawl time, success rate

#### **1.4 Pre-configured Sites**
```javascript
const DEFAULT_SITES = [
    { name: "TopCV", url: "https://www.topcv.vn", icon: "topcv-icon.png" },
    { name: "ITViec", url: "https://itviec.com", icon: "itviec-icon.png" },
    { name: "VietnamWorks", url: "https://www.vietnamworks.com", icon: "vw-icon.png" },
    { name: "LinkedIn", url: "https://www.linkedin.com/jobs", icon: "linkedin-icon.png" },
    { name: "JobsGO", url: "https://jobsgo.vn", icon: "jobsgo-icon.png" }
];
```

---

## 👤 Task 2: Enhanced User Identity System

### **Objective**
Implement device fingerprinting and IP-based user identification for anonymous user tracking without requiring account creation.

### **Implementation Plan**

#### **2.1 Database Schema Updates**
Modify the user_interactions table and add user_sessions table:

```sql
-- Update user_interactions table
ALTER TABLE user_interactions 
DROP COLUMN user_id,
ADD COLUMN user_fingerprint VARCHAR(255) NOT NULL,
ADD COLUMN session_id VARCHAR(255) NOT NULL,
ADD COLUMN ip_address INET,
ADD COLUMN user_agent TEXT,
ADD COLUMN device_info JSONB;

-- Create user_sessions table
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL UNIQUE,
    user_fingerprint VARCHAR(255) NOT NULL,
    ip_address INET NOT NULL,
    user_agent TEXT,
    device_info JSONB,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    total_interactions INTEGER DEFAULT 0,
    INDEX idx_fingerprint (user_fingerprint),
    INDEX idx_session (session_id),
    INDEX idx_ip (ip_address)
);
```

#### **2.2 Device Fingerprinting Implementation**

**Frontend fingerprinting (client-side):**
```javascript
// Install: npm install fingerprintjs2
import FingerprintJS from 'fingerprintjs2';

const generateFingerprint = async () => {
    return new Promise((resolve) => {
        FingerprintJS.get((components) => {
            const fingerprint = FingerprintJS.x64hash128(
                components.map(pair => pair.value).join(''), 31
            );
            resolve(fingerprint);
        });
    });
};

const getDeviceInfo = () => ({
    screen: `${screen.width}x${screen.height}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: navigator.language,
    platform: navigator.platform,
    cookieEnabled: navigator.cookieEnabled,
    onlineStatus: navigator.onLine,
    touchSupport: 'ontouchstart' in window
});
```

**Backend tracking service:**
```python
# backend/app/services/user_tracking_service.py
class UserTrackingService:
    def identify_user(self, request):
        # Extract IP (handle proxies)
        ip = self.get_client_ip(request)
        user_agent = request.headers.get('user-agent', '')
        fingerprint = request.headers.get('x-device-fingerprint', '')
        
        # Generate session ID if not exists
        session_id = request.cookies.get('session_id') or str(uuid.uuid4())
        
        return {
            'user_fingerprint': fingerprint,
            'session_id': session_id,
            'ip_address': ip,
            'user_agent': user_agent
        }
```

#### **2.3 Privacy Compliance**
- Add privacy notice for anonymous tracking
- Implement data retention policies (90 days)
- Allow users to opt-out via browser settings
- GDPR compliance for EU users

---

## 📊 Task 3: Job Interaction History

### **Objective**
Track user interactions with jobs and provide visual indicators for previously viewed jobs.

### **Implementation Plan**

#### **3.1 Database Schema**
Create job_interactions table:

```sql
CREATE TABLE job_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_fingerprint VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    job_id VARCHAR(255) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL, -- 'view', 'click', 'apply', 'save'
    interaction_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_user_job (user_fingerprint, job_id),
    INDEX idx_session (session_id),
    INDEX idx_job (job_id),
    INDEX idx_type (interaction_type)
);
```

#### **3.2 Backend Implementation**

**API Endpoints:**
```python
# POST /api/jobs/{job_id}/interactions - Record interaction
# GET /api/user/job-history - Get user's job interaction history
# GET /api/jobs/search - Enhanced with interaction indicators
```

**Enhanced search response:**
```json
{
    "jobs": [
        {
            "id": "job_123",
            "title": "Senior Python Developer",
            "company": "Tech Corp",
            "user_interactions": {
                "viewed": true,
                "clicked": true,
                "view_count": 3,
                "last_viewed": "2025-01-20T10:30:00Z",
                "saved": false
            }
        }
    ]
}
```

#### **3.3 Frontend Implementation**

**UI Indicators:**
- **Viewed Badge**: Small blue dot or "Viewed" tag
- **Click History**: Different background color for clicked jobs
- **View Count**: Number of times viewed
- **Last Seen**: Relative time ("2 hours ago")

**Components to update:**
- `JobCard.tsx` - Add interaction indicators
- `JobList.tsx` - Handle interaction tracking
- `JobDetailPage.tsx` - Track detailed views

---

## 🎨 Task 4: Two-Column Job Search Layout

### **Objective**
Redesign the job search interface with a modern two-column layout for better user experience.

### **Implementation Plan**

#### **4.1 Layout Design**

**Desktop Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Header / Search Bar                      │
├─────────────────────────┬───────────────────────────────────┤
│                         │                                   │
│     Job List Panel      │        Job Detail Panel          │
│   (Scrollable List)     │     (Selected Job Details)       │
│                         │                                   │
│  ┌─────────────────┐    │   ┌─────────────────────────────┐ │
│  │   Job Card 1    │    │   │                             │ │
│  │   [Selected]    │    │   │      Job Description       │ │
│  └─────────────────┘    │   │      Company Info           │ │
│  ┌─────────────────┐    │   │      Requirements          │ │
│  │   Job Card 2    │    │   │      Apply Button          │ │
│  └─────────────────┘    │   │                             │ │
│  ┌─────────────────┐    │   └─────────────────────────────┘ │
│  │   Job Card 3    │    │                                   │
│  └─────────────────┘    │                                   │
│                         │                                   │
└─────────────────────────┴───────────────────────────────────┘
```

**Mobile Layout:** Stack vertically, hide detail panel initially

#### **4.2 Implementation**

**Files to modify:**
- `JobSearchPage.tsx` - Restructure main layout
- `JobList.tsx` - Left panel component
- `JobDetailPanel.tsx` - New right panel component
- `JobCard.tsx` - Update for list view

**Key Features:**
- **Split View**: 40% list, 60% details
- **Responsive**: Collapsible on mobile
- **Sticky Header**: Search filters always visible
- **Infinite Scroll**: In left panel
- **Quick Preview**: Hover effects

---

## 🕷️ Task 5: Real TopCV Integration

### **Objective**
Implement actual web scraping for TopCV.vn with proper handling of anti-bot measures and data extraction.

### **Implementation Plan**

#### **5.1 Technical Requirements**

**Dependencies to install:**
```bash
# Backend
pip install selenium beautifulsoup4 requests-html playwright
pip install fake-useragent python-decouple schedule

# Browser automation
playwright install chromium
```

#### **5.2 Crawler Implementation**

**Files to create:**
- `backend/app/crawlers/topcv_crawler.py` - Specific TopCV crawler
- `backend/app/services/crawler_scheduler.py` - Background job scheduler
- `backend/app/utils/anti_bot.py` - Anti-detection utilities

**TopCV Crawler Structure:**
```python
class TopCVCrawler(BaseCrawler):
    def __init__(self):
        self.base_url = "https://www.topcv.vn"
        self.search_url = f"{self.base_url}/tim-viec-lam"
        
    async def crawl_jobs(self, keywords=None, location=None, limit=100):
        # Use Playwright for JavaScript rendering
        # Implement pagination handling
        # Extract job data with proper selectors
        # Handle rate limiting
        # Store in database and Marqo
        
    def extract_job_details(self, job_element):
        # Extract title, company, location, salary, description
        # Handle different job card formats
        # Clean and normalize data
```

#### **5.3 Anti-Bot Measures**

**Strategies:**
- **Rotating User Agents**: Use fake-useragent library
- **Proxy Rotation**: Implement proxy pool if needed
- **Rate Limiting**: 1-2 requests per second
- **Browser Automation**: Use Playwright with stealth mode
- **CAPTCHA Handling**: Manual intervention or 2captcha service
- **Session Management**: Maintain cookies and sessions

#### **5.4 Data Pipeline**

**Workflow:**
1. **Scheduled Crawling**: Every 6 hours
2. **Data Validation**: Check for required fields
3. **Deduplication**: Avoid storing duplicate jobs
4. **Vector Indexing**: Add to Marqo for search
5. **Monitoring**: Log success/failure rates

#### **5.5 Background Processing**

**Scheduler Implementation:**
```python
# Use APScheduler for background jobs
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', hours=6)
async def crawl_topcv_jobs():
    crawler = TopCVCrawler()
    await crawler.crawl_and_store()

# Start scheduler with FastAPI
@app.on_event("startup")
async def start_scheduler():
    scheduler.start()
```

---

## 🚀 Implementation Priority

### **Phase 1 (Week 1)**
1. ✅ Enhanced user identity system (Task 2)
2. ✅ Job interaction history (Task 3)
3. ✅ Database schema updates

### **Phase 2 (Week 2)**
1. ✅ Two-column layout redesign (Task 4)
2. ✅ UI/UX improvements
3. ✅ Mobile responsiveness

### **Phase 3 (Week 3)**
1. ✅ Crawler configuration page (Task 1)
2. ✅ Admin interface enhancements
3. ✅ Configuration management

### **Phase 4 (Week 4)**
1. ✅ Real TopCV integration (Task 5)
2. ✅ Background job processing
3. ✅ Production deployment

---

## 🔧 Technical Considerations

### **Performance**
- **Database Indexing**: Proper indexes for fast queries
- **Caching**: Redis for frequently accessed data
- **API Rate Limiting**: Protect against abuse
- **Background Jobs**: Celery or APScheduler for heavy tasks

### **Security**
- **Input Validation**: Sanitize all crawler inputs
- **Rate Limiting**: Prevent API abuse
- **Privacy Compliance**: GDPR/CCPA considerations
- **Error Handling**: Graceful failure recovery

### **Monitoring**
- **Logging**: Comprehensive application logs
- **Metrics**: Track crawler success rates
- **Alerts**: Notify on crawler failures
- **Performance**: Monitor response times

### **Scalability**
- **Horizontal Scaling**: Multiple crawler instances
- **Load Balancing**: Distribute crawler load
- **Database Sharding**: If data grows large
- **CDN**: For static assets

---

## 📝 Notes

### **Legal Considerations**
- **robots.txt**: Respect website crawling policies
- **Terms of Service**: Review ToS for each site
- **Rate Limiting**: Be respectful to target servers
- **Data Usage**: Ensure proper attribution

### **Data Quality**
- **Validation Rules**: Ensure data consistency
- **Cleaning Pipelines**: Remove duplicates and invalid data
- **Monitoring**: Track data quality metrics
- **Feedback Loop**: Users can report bad data

### **User Experience**
- **Loading States**: Show progress during operations
- **Error Messages**: User-friendly error handling
- **Offline Support**: Cache for offline viewing
- **Accessibility**: WCAG compliance

---

## 🎯 Success Metrics

### **Technical Metrics**
- **Crawler Success Rate**: >95%
- **Data Freshness**: <6 hours old
- **API Response Time**: <500ms
- **Database Query Performance**: <100ms

### **User Metrics**
- **Job View Rate**: Track user engagement
- **Search Success Rate**: Users find relevant jobs
- **Return Users**: Anonymous user retention
- **Interaction Patterns**: Click-through rates

### **Business Metrics**
- **Job Coverage**: Number of unique jobs
- **Source Diversity**: Multiple site coverage
- **Data Accuracy**: User feedback on job quality
- **System Uptime**: 99.9% availability

---

*This TODO list will be updated as tasks are completed and new requirements emerge.*
