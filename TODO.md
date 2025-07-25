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

### **Research Results (TopCV.vn Analysis)**

#### **5.0 Site Structure Analysis**
**Base URL**: `https://www.topcv.vn`

**Key Endpoints:**
- Main search: `https://www.topcv.vn/tim-viec-lam-cong-nghe-thong-tin` (IT jobs)
- Job detail: `https://www.topcv.vn/viec-lam/{job-slug}/{job-id}.html`
- Company page: `https://www.topcv.vn/cong-ty/{company-slug}/{company-id}.html`

**URL Patterns:**
```
Job Search: /tim-viec-lam-{category}
Job Detail: /viec-lam/{job-title-slug}/{job-id}.html
Company: /cong-ty/{company-name-slug}/{company-id}.html
```

**Page Structure:**
1. **Job Listing Page** (`/tim-viec-lam-cong-nghe-thong-tin`):
   - Shows "1.485 việc làm Công Nghệ Thông Tin"
   - Job cards with: title, company, location, salary, experience, skills
   - Pagination at bottom
   - Filters sidebar

2. **Job Detail Page** (`/viec-lam/{slug}/{id}.html`):
   - Complete job description
   - Company information
   - Requirements, benefits, equipment
   - Location and working hours
   - Application deadline

**Data Extraction Points:**
```html
<!-- Job Card (List Page) -->
<h3 class="job-title">
  <a href="/viec-lam/middle-unity-developer/1810341.html">Middle Unity Developer</a>
</h3>
<div class="company-name">CÔNG TY CỔ PHẦN SABO GAME</div>
<div class="location">Hà Nội</div>
<div class="salary">15 - 30 triệu</div>
<div class="experience">2 năm</div>
<div class="skills">Game Developer, Game, Nghỉ thứ 7</div>

<!-- Job Detail Page -->
<section class="job-description">Mô tả công việc</section>
<section class="job-requirements">Yêu cầu ứng viên</section>
<section class="job-benefits">Quyền lợi</section>
<section class="working-location">Địa điểm làm việc</section>
<section class="working-time">Thời gian làm việc</section>
```

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
        self.categories = {
            'cong-nghe-thong-tin': 'Công nghệ thông tin',
            'kinh-doanh-ban-hang': 'Kinh doanh/Bán hàng',
            'marketing-pr-quang-cao': 'Marketing/PR',
            'ke-toan-kiem-toan': 'Kế toán/Kiểm toán',
            'tai-chinh-ngan-hang': 'Tài chính/Ngân hàng'
        }
        
    async def crawl_jobs(self, category='cong-nghe-thong-tin', pages=5):
        """Crawl job listings from TopCV"""
        jobs = []
        
        for page in range(1, pages + 1):
            url = f"{self.base_url}/tim-viec-lam-{category}"
            if page > 1:
                url += f"?page={page}"
                
            # Use Playwright for JavaScript rendering
            job_cards = await self.extract_job_cards(url)
            
            for card in job_cards:
                job_detail = await self.extract_job_details(card['detail_url'])
                jobs.append(job_detail)
                
        return jobs
        
    async def extract_job_cards(self, url):
        """Extract job cards from listing page"""
        # Implementation for job cards extraction
        
    async def extract_job_details(self, detail_url):
        """Extract detailed job information"""
        # Implementation for job details extraction
```

**Specific TopCV Selectors:**
```python
TOPCV_SELECTORS = {
    'job_cards': 'div[class*="job-item"], article[class*="job"]',
    'job_title': 'h3 a, .job-title a',
    'company_name': '.company-name, .company a',
    'location': '.job-location, .location',
    'salary': '.salary, .job-salary',
    'experience': '.experience, .job-experience',
    'skills': '.skills, .job-tags',
    'detail_link': 'h3 a[href], .job-title a[href]',
    
    # Job detail page selectors
    'description': '[class*="job-description"], section:contains("Mô tả công việc")',
    'requirements': '[class*="job-requirements"], section:contains("Yêu cầu")',
    'benefits': '[class*="job-benefits"], section:contains("Quyền lợi")',
    'working_time': '[class*="working-time"], section:contains("Thời gian")',
    'working_location': '[class*="working-location"], section:contains("Địa điểm")',
    'deadline': '[class*="deadline"], .deadline',
    'company_info': '.company-info, .company-detail'
}
```

**Data Mapping Implementation:**
```python
class TopCVDataMapper:
    @staticmethod
    def map_job_data(raw_data: dict) -> JobCreate:
        """Map TopCV data to JobCreate schema"""
        return JobCreate(
            title=TopCVDataMapper.clean_title(raw_data.get('title', '')),
            company_name=TopCVDataMapper.clean_company(raw_data.get('company', '')),
            location=TopCVDataMapper.normalize_location(raw_data.get('location', '')),
            description=TopCVDataMapper.clean_description(raw_data.get('description', '')),
            requirements=raw_data.get('requirements', ''),
            salary=TopCVDataMapper.parse_salary(raw_data.get('salary', '')),
            job_type='full-time',  # Default as most jobs are full-time
            experience_level=TopCVDataMapper.parse_experience(raw_data.get('experience', '')),
            external_url=raw_data.get('detail_url', ''),
            benefits=TopCVDataMapper.extract_benefits(raw_data.get('benefits', '')),
            skills=TopCVDataMapper.extract_skills(raw_data.get('skills', '')),
            deadline=TopCVDataMapper.parse_deadline(raw_data.get('deadline', '')),
            source='TopCV',
            source_id=TopCVDataMapper.extract_job_id(raw_data.get('detail_url', ''))
        )
    
    @staticmethod
    def clean_title(title: str) -> str:
        """Clean job title from TopCV format"""
        # Remove special prefixes like "GẤP", "HOT", etc.
        prefixes = ['GẤP', 'HOT', '🌠Tin mới', '✨Nổi bật', '💎 TOP']
        for prefix in prefixes:
            title = title.replace(prefix, '').strip()
        return title.strip()
    
    @staticmethod
    def parse_salary(salary_text: str) -> str:
        """Parse salary from TopCV format"""
        # Examples: "15 - 30 triệu", "Thoả thuận", "Từ 36 triệu"
        if not salary_text or salary_text == 'Thoả thuận':
            return 'Negotiable'
        
        # Convert Vietnamese format to standard
        salary_text = salary_text.replace('triệu', 'M VND')
        salary_text = salary_text.replace('Từ ', 'From ')
        salary_text = salary_text.replace(' - ', ' - ')
        
        return salary_text
    
    @staticmethod
    def normalize_location(location: str) -> str:
        """Normalize location format"""
        # Common Vietnamese location mappings
        location_map = {
            'Hồ Chí Minh': 'Ho Chi Minh City',
            'Hà Nội': 'Hanoi',
            'Đà Nẵng': 'Da Nang',
            'Cần Thơ': 'Can Tho'
        }
        
        for vn_name, en_name in location_map.items():
            location = location.replace(vn_name, en_name)
            
        return location.strip()
    
    @staticmethod
    def extract_job_id(detail_url: str) -> str:
        """Extract job ID from detail URL"""
        # URL format: /viec-lam/job-title/1810341.html
        import re
        match = re.search(r'/(\d+)\.html', detail_url)
        return match.group(1) if match else ''
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

## � Task 6: Job Deduplication System

### **Objective**
Implement a robust mechanism to prevent duplicate jobs from being stored in the system by checking job existence before insertion.

### **Implementation Plan**

#### **6.1 Database Schema Updates**
Add unique constraints and deduplication tracking:

```sql
-- Add unique constraint to jobs table
ALTER TABLE jobs ADD COLUMN source_job_id VARCHAR(255);
ALTER TABLE jobs ADD COLUMN content_hash VARCHAR(64);
CREATE UNIQUE INDEX idx_unique_job ON jobs (source, source_job_id);
CREATE INDEX idx_content_hash ON jobs (content_hash);

-- Job deduplication tracking table
CREATE TABLE job_duplicates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_job_id UUID NOT NULL REFERENCES jobs(id),
    duplicate_source VARCHAR(100) NOT NULL,
    duplicate_source_id VARCHAR(255) NOT NULL,
    duplicate_url TEXT,
    detected_at TIMESTAMP DEFAULT NOW(),
    similarity_score DECIMAL(3,2), -- 0.00 to 1.00
    duplicate_fields JSONB, -- Which fields were duplicated
    INDEX idx_original_job (original_job_id),
    INDEX idx_duplicate_source (duplicate_source, duplicate_source_id)
);
```

#### **6.2 Deduplication Logic Implementation**

**Files to create/modify:**
- `backend/app/services/job_deduplication_service.py` - Core deduplication logic
- `backend/app/utils/content_hasher.py` - Content hashing utilities
- `backend/app/models/database.py` - Add JobDuplicate model

**Deduplication Service:**
```python
import hashlib
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.schemas.schemas import JobCreate
from app.models.database import Job, JobDuplicate

class JobDeduplicationService:
    def __init__(self, db: Session):
        self.db = db
        
    async def check_and_store_job(self, job_data: JobCreate) -> Tuple[bool, Optional[str]]:
        """
        Check if job exists and store if unique
        Returns: (is_new_job, job_id_or_reason)
        """
        # 1. Check by source and source_id (exact match)
        existing_job = await self.check_by_source_id(job_data)
        if existing_job:
            await self.log_duplicate(existing_job.id, job_data, "source_id_match")
            return False, f"Duplicate found by source ID: {existing_job.id}"
        
        # 2. Check by content hash (exact content match)
        content_hash = self.generate_content_hash(job_data)
        existing_job = await self.check_by_content_hash(content_hash)
        if existing_job:
            await self.log_duplicate(existing_job.id, job_data, "content_hash_match")
            return False, f"Duplicate found by content hash: {existing_job.id}"
        
        # 3. Check by fuzzy matching (title + company similarity)
        similar_job = await self.check_by_fuzzy_match(job_data)
        if similar_job:
            similarity_score = self.calculate_similarity(similar_job, job_data)
            if similarity_score > 0.85:  # 85% similarity threshold
                await self.log_duplicate(
                    similar_job.id, 
                    job_data, 
                    "fuzzy_match", 
                    similarity_score
                )
                return False, f"Similar job found (score: {similarity_score}): {similar_job.id}"
        
        # 4. Job is unique, store it
        new_job = await self.store_new_job(job_data, content_hash)
        return True, new_job.id
    
    async def check_by_source_id(self, job_data: JobCreate) -> Optional[Job]:
        """Check if job exists by source and source_job_id"""
        return self.db.query(Job).filter(
            Job.source == job_data.source,
            Job.source_job_id == job_data.source_id
        ).first()
    
    async def check_by_content_hash(self, content_hash: str) -> Optional[Job]:
        """Check if job exists by content hash"""
        return self.db.query(Job).filter(
            Job.content_hash == content_hash
        ).first()
    
    def generate_content_hash(self, job_data: JobCreate) -> str:
        """Generate SHA-256 hash of job content"""
        content = f"{job_data.title}|{job_data.company_name}|{job_data.description}|{job_data.requirements}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def check_by_fuzzy_match(self, job_data: JobCreate) -> Optional[Job]:
        """Check for similar jobs using fuzzy matching"""
        # Use SQL LIKE or implement Levenshtein distance
        similar_jobs = self.db.query(Job).filter(
            Job.title.ilike(f"%{job_data.title[:20]}%"),
            Job.company_name.ilike(f"%{job_data.company_name}%")
        ).limit(5).all()
        
        for job in similar_jobs:
            if self.calculate_similarity(job, job_data) > 0.85:
                return job
        return None
    
    def calculate_similarity(self, existing_job: Job, new_job: JobCreate) -> float:
        """Calculate similarity score between jobs"""
        from difflib import SequenceMatcher
        
        title_sim = SequenceMatcher(None, existing_job.title, new_job.title).ratio()
        company_sim = SequenceMatcher(None, existing_job.company_name, new_job.company_name).ratio()
        
        # Weighted average: title 60%, company 40%
        return (title_sim * 0.6) + (company_sim * 0.4)
```

#### **6.3 Integration with Crawlers**

**Update crawler implementations:**
```python
# In TopCVCrawler and other crawlers
class TopCVCrawler(BaseCrawler):
    def __init__(self, db: Session):
        super().__init__()
        self.dedup_service = JobDeduplicationService(db)
    
    async def process_job(self, job_data: JobCreate):
        """Process job with deduplication check"""
        is_new, result = await self.dedup_service.check_and_store_job(job_data)
        
        if is_new:
            logger.info(f"New job stored: {result}")
            # Add to Marqo index
            await self.marqo_service.add_job(job_data)
        else:
            logger.info(f"Duplicate job skipped: {result}")
            
        return is_new, result
```

---

## 📊 Task 7: Crawl Request Logging System

### **Objective**
Create a comprehensive logging system to track all crawler requests, responses, and performance metrics for monitoring and debugging.

### **Implementation Plan**

#### **7.1 Database Schema**
Create crawl logs table:

```sql
CREATE TABLE crawl_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_name VARCHAR(100) NOT NULL,
    site_url TEXT NOT NULL,
    request_url TEXT NOT NULL,
    crawler_type VARCHAR(50) NOT NULL, -- 'topcv', 'itviec', etc.
    request_method VARCHAR(10) NOT NULL DEFAULT 'GET',
    request_headers JSONB,
    response_status INTEGER,
    response_time_ms INTEGER,
    response_size_bytes INTEGER,
    jobs_found INTEGER DEFAULT 0,
    jobs_processed INTEGER DEFAULT 0,
    jobs_stored INTEGER DEFAULT 0,
    jobs_duplicated INTEGER DEFAULT 0,
    error_message TEXT,
    error_details JSONB,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_ms INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000
    ) STORED,
    
    -- Indexes for performance
    INDEX idx_site_name (site_name),
    INDEX idx_started_at (started_at),
    INDEX idx_status (response_status),
    INDEX idx_crawler_type (crawler_type)
);

-- Summary table for quick statistics
CREATE TABLE crawl_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    total_jobs_found INTEGER DEFAULT 0,
    total_jobs_stored INTEGER DEFAULT 0,
    total_jobs_duplicated INTEGER DEFAULT 0,
    average_response_time_ms DECIMAL(10,2),
    total_data_size_mb DECIMAL(10,2),
    last_updated TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(site_name, date)
);
```

#### **7.2 Logging Service Implementation**

**Files to create:**
- `backend/app/services/crawl_logging_service.py` - Logging service
- `backend/app/models/database.py` - Add CrawlLog and CrawlStatistics models

**Crawl Logging Service:**
```python
import time
from datetime import datetime, date
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.database import CrawlLog, CrawlStatistics

class CrawlLoggingService:
    def __init__(self, db: Session):
        self.db = db
        
    def start_crawl_session(
        self, 
        site_name: str, 
        site_url: str, 
        request_url: str,
        crawler_type: str,
        request_headers: Dict[str, str] = None
    ) -> CrawlLog:
        """Start a new crawl session and return log entry"""
        log_entry = CrawlLog(
            site_name=site_name,
            site_url=site_url,
            request_url=request_url,
            crawler_type=crawler_type,
            request_headers=request_headers or {},
            started_at=datetime.utcnow()
        )
        
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        
        return log_entry
    
    def complete_crawl_session(
        self,
        log_id: str,
        response_status: int,
        response_time_ms: int,
        response_size_bytes: int = 0,
        jobs_found: int = 0,
        jobs_processed: int = 0,
        jobs_stored: int = 0,
        jobs_duplicated: int = 0,
        error_message: str = None,
        error_details: Dict[str, Any] = None
    ):
        """Complete crawl session with results"""
        log_entry = self.db.query(CrawlLog).filter(CrawlLog.id == log_id).first()
        
        if log_entry:
            log_entry.response_status = response_status
            log_entry.response_time_ms = response_time_ms
            log_entry.response_size_bytes = response_size_bytes
            log_entry.jobs_found = jobs_found
            log_entry.jobs_processed = jobs_processed
            log_entry.jobs_stored = jobs_stored
            log_entry.jobs_duplicated = jobs_duplicated
            log_entry.error_message = error_message
            log_entry.error_details = error_details or {}
            log_entry.completed_at = datetime.utcnow()
            
            self.db.commit()
            
            # Update daily statistics
            self.update_daily_statistics(log_entry)
    
    def update_daily_statistics(self, log_entry: CrawlLog):
        """Update daily statistics for the crawl"""
        today = date.today()
        
        stats = self.db.query(CrawlStatistics).filter(
            CrawlStatistics.site_name == log_entry.site_name,
            CrawlStatistics.date == today
        ).first()
        
        if not stats:
            stats = CrawlStatistics(
                site_name=log_entry.site_name,
                date=today
            )
            self.db.add(stats)
        
        # Update counters
        stats.total_requests += 1
        if log_entry.response_status and 200 <= log_entry.response_status < 300:
            stats.successful_requests += 1
        else:
            stats.failed_requests += 1
            
        stats.total_jobs_found += log_entry.jobs_found or 0
        stats.total_jobs_stored += log_entry.jobs_stored or 0
        stats.total_jobs_duplicated += log_entry.jobs_duplicated or 0
        
        # Update averages
        all_logs_today = self.db.query(CrawlLog).filter(
            CrawlLog.site_name == log_entry.site_name,
            CrawlLog.started_at >= today
        ).all()
        
        response_times = [log.response_time_ms for log in all_logs_today if log.response_time_ms]
        if response_times:
            stats.average_response_time_ms = sum(response_times) / len(response_times)
            
        data_sizes = [log.response_size_bytes for log in all_logs_today if log.response_size_bytes]
        if data_sizes:
            stats.total_data_size_mb = sum(data_sizes) / (1024 * 1024)  # Convert to MB
            
        stats.last_updated = datetime.utcnow()
        self.db.commit()

# Context manager for easier usage
class CrawlLogger:
    def __init__(self, logging_service: CrawlLoggingService, site_name: str, site_url: str, request_url: str, crawler_type: str):
        self.logging_service = logging_service
        self.site_name = site_name
        self.site_url = site_url
        self.request_url = request_url
        self.crawler_type = crawler_type
        self.log_entry = None
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        self.log_entry = self.logging_service.start_crawl_session(
            self.site_name, 
            self.site_url, 
            self.request_url, 
            self.crawler_type
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        response_time_ms = int((end_time - self.start_time) * 1000)
        
        if exc_type:
            # Handle exception
            self.logging_service.complete_crawl_session(
                log_id=str(self.log_entry.id),
                response_status=500,
                response_time_ms=response_time_ms,
                error_message=str(exc_val),
                error_details={"exception_type": exc_type.__name__}
            )
        else:
            # Normal completion (to be updated by crawler)
            pass
    
    def complete(self, **kwargs):
        """Complete the crawl session with custom parameters"""
        self.logging_service.complete_crawl_session(
            log_id=str(self.log_entry.id),
            **kwargs
        )
```

---

## 📋 Task 8: Admin Crawl Logs Dashboard

### **Objective**
Create an admin dashboard page to view, filter, and analyze crawler logs and statistics for monitoring system health and performance.

### **Implementation Plan**

#### **8.1 Backend API Endpoints**

**Files to create/modify:**
- `backend/app/routes/admin/crawl_logs.py` - New admin routes
- `backend/app/schemas/admin.py` - Add crawl log schemas

**API Endpoints:**
```python
# GET /admin/crawl-logs - List crawl logs with filters
# GET /admin/crawl-logs/{log_id} - Get specific log details
# GET /admin/crawl-logs/statistics - Get aggregated statistics
# GET /admin/crawl-logs/summary - Get dashboard summary
# DELETE /admin/crawl-logs - Clean old logs (retention policy)

from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from datetime import datetime, date

@app.get("/admin/crawl-logs")
async def get_crawl_logs(
    site_name: Optional[str] = None,
    crawler_type: Optional[str] = None,
    status: Optional[str] = None,  # 'success', 'error', 'all'
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get crawl logs with filtering and pagination"""
    pass

@app.get("/admin/crawl-logs/dashboard")
async def get_dashboard_summary():
    """Get dashboard summary statistics"""
    return {
        "total_crawls_today": 0,
        "success_rate_today": 0.0,
        "total_jobs_found_today": 0,
        "active_crawlers": [],
        "recent_errors": [],
        "performance_metrics": {}
    }
```

#### **8.2 Frontend Implementation**

**Files to create:**
- `frontend/src/pages/admin/CrawlLogsPage.tsx` - Main logs dashboard
- `frontend/src/components/admin/CrawlLogTable.tsx` - Logs table component
- `frontend/src/components/admin/CrawlStatistics.tsx` - Statistics widgets
- `frontend/src/components/admin/CrawlLogFilters.tsx` - Filter controls
- `frontend/src/types/crawlLogs.ts` - TypeScript types

**Dashboard Features:**
```typescript
// CrawlLogsPage.tsx
import React, { useState, useEffect } from 'react';
import { CrawlLogTable } from '@/components/admin/CrawlLogTable';
import { CrawlStatistics } from '@/components/admin/CrawlStatistics';
import { CrawlLogFilters } from '@/components/admin/CrawlLogFilters';

interface CrawlLogsDashboardProps {}

export const CrawlLogsPage: React.FC<CrawlLogsDashboardProps> = () => {
  const [logs, setLogs] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [filters, setFilters] = useState({
    site_name: '',
    crawler_type: '',
    status: 'all',
    date_from: '',
    date_to: ''
  });

  return (
    <div className="crawl-logs-dashboard">
      <div className="dashboard-header">
        <h1>Crawler Logs & Monitoring</h1>
        <div className="dashboard-actions">
          <button onClick={handleRefresh}>Refresh</button>
          <button onClick={handleExport}>Export Logs</button>
          <button onClick={handleCleanup}>Cleanup Old Logs</button>
        </div>
      </div>
      
      <CrawlStatistics data={statistics} />
      <CrawlLogFilters filters={filters} onChange={setFilters} />
      <CrawlLogTable logs={logs} />
    </div>
  );
};
```

**Statistics Widgets:**
- **Success Rate Chart**: Daily success/failure rates
- **Performance Metrics**: Average response times, data throughput
- **Job Statistics**: Jobs found, stored, duplicated
- **Site Health Status**: Current status of each crawler
- **Error Trends**: Common errors and frequency

#### **8.3 Real-time Monitoring**

**WebSocket Integration:**
```typescript
// Real-time updates for active crawls
const useRealTimeCrawlUpdates = () => {
  const [activeCrawls, setActiveCrawls] = useState([]);
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8002/ws/crawl-updates');
    
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      if (update.type === 'crawl_started') {
        setActiveCrawls(prev => [...prev, update.data]);
      } else if (update.type === 'crawl_completed') {
        setActiveCrawls(prev => prev.filter(c => c.id !== update.data.id));
      }
    };
    
    return () => ws.close();
  }, []);
  
  return activeCrawls;
};
```

---

## �🚀 Implementation Priority

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

### **Phase 5 (Week 5) - Data Quality & Monitoring**
1. 🔄 Job deduplication system (Task 6)
   - Database schema updates for unique constraints
   - Deduplication service implementation
   - Integration with existing crawlers

2. 🔄 Crawl request logging system (Task 7)
   - Comprehensive logging database schema
   - Logging service with performance metrics
   - Integration with crawler context managers

3. 🔄 Admin crawl logs dashboard (Task 8)
   - Real-time monitoring interface
   - Statistics and performance widgets
   - Log filtering and export capabilities

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
- **Job Deduplication Accuracy**: >99%
- **Duplicate Detection Rate**: <1% false positives
- **Crawl Log Coverage**: 100% of requests logged
- **System Monitoring Uptime**: 99.9%

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
- **Data Quality Score**: Based on deduplication and validation
- **Crawler Efficiency**: Jobs processed per hour per site

### **Monitoring & Quality Metrics**
- **Duplicate Job Rate**: <5% of total crawled jobs
- **Crawl Failure Rate**: <2% of total requests
- **Average Response Time**: <2 seconds per page
- **Data Processing Speed**: >1000 jobs per hour
- **Log Retention Compliance**: 90-day retention policy
- **Alert Response Time**: <5 minutes for critical issues

---

*This TODO list will be updated as tasks are completed and new requirements emerge.*
