# 🔐 Admin Dashboard System

A complete administrative interface for managing the job search platform with authentication, job management, and analytics.

## 📋 Features

### 🔑 Authentication
- **JWT-based authentication** with 8-hour token expiration
- **Secure password hashing** using passlib and bcrypt
- **Protected routes** requiring admin authentication
- **Credentials**: `username: admin, password: 123123`

### 📊 Dashboard Analytics
- **Real-time statistics** for total jobs, recent activity, and system health
- **Source distribution charts** showing job breakdown by platform
- **Visual indicators** for system status and performance metrics

### 📋 Job Management
- **Comprehensive job listing** with pagination support
- **Source filtering** to view jobs from specific platforms
- **Job actions** including view, edit, and delete operations
- **Bulk operations** for efficient job management

### 🔄 Data Synchronization
- **Multi-source sync** supporting LinkedIn, TopCV, ITViec, and VietnamWorks
- **Batch sync operations** with progress tracking
- **Individual source sync** for targeted updates
- **Sync status monitoring** with real-time feedback

### 🎨 User Interface
- **Modern design** using Tailwind CSS
- **Responsive layout** optimized for desktop and mobile
- **Interactive components** with smooth animations
- **Professional styling** with consistent branding

## 🏗️ Technical Architecture

### Backend Components
```
backend/app/
├── services/
│   └── auth_service.py      # JWT authentication service
├── routes/
│   └── admin.py            # Admin API endpoints
├── schemas/
│   └── schemas.py          # Admin data models (enhanced)
└── main.py                 # FastAPI app with admin routes
```

### Frontend Components
```
frontend/src/
├── pages/
│   ├── AdminLoginPage.tsx   # Authentication interface
│   └── AdminDashboardPage.tsx # Main admin dashboard
├── types/
│   └── admin.ts            # TypeScript admin types
├── services/
│   └── api.ts              # API integration (enhanced)
└── App.tsx                 # Router configuration
```

## 🚀 Getting Started

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Set environment variables
echo "ADMIN_USERNAME=admin" >> .env
echo "ADMIN_PASSWORD=123123" >> .env
echo "JWT_SECRET_KEY=your-secret-key-here" >> .env

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install

# Set environment variables
echo "VITE_API_URL=http://localhost:8000" >> .env.local
echo "VITE_ADMIN_USERNAME=admin" >> .env.local
echo "VITE_ADMIN_PASSWORD=123123" >> .env.local

# Start the frontend server
npm run dev
```

### 3. Access Admin Dashboard
1. Navigate to `http://localhost:3000/admin/login`
2. Use credentials: `admin` / `123123`
3. Access the full dashboard functionality

## 📡 API Endpoints

### Authentication
- `POST /admin/login` - Admin login with JWT token generation
- Protected routes require `Authorization: Bearer <token>` header

### Dashboard Data
- `GET /admin/dashboard` - Dashboard statistics and overview data
- `GET /admin/analytics` - Detailed analytics and metrics

### Job Management
- `GET /admin/jobs` - List all jobs with pagination and filtering
- `DELETE /admin/jobs/{job_id}` - Delete a specific job
- `POST /admin/jobs/bulk-delete` - Delete multiple jobs

### Data Synchronization
- `POST /admin/sync/{source}` - Sync jobs from a specific source
- `POST /admin/sync/all` - Sync jobs from all available sources
- `GET /admin/sync/status` - Get current synchronization status

## 🔒 Security Features

### Authentication Security
- **Password hashing** using bcrypt with salt rounds
- **JWT tokens** with configurable expiration times
- **Secure token storage** in HTTP-only cookies (recommended)
- **CORS protection** for cross-origin requests

### Authorization
- **Route protection** using FastAPI dependencies
- **Token validation** on every protected request
- **Automatic logout** on token expiration
- **Admin-only access** to sensitive operations

## 📊 Data Models

### Admin Types (TypeScript)
```typescript
interface AdminLoginRequest {
  username: string;
  password: string;
}

interface AdminDashboardData {
  totalJobs: number;
  recentJobs: number;
  sourcesActive: number;
  syncStatus: string;
  jobsBySource: SourceDistribution[];
}

interface JobListResponse {
  jobs: Job[];
  total: number;
  page: number;
  totalPages: number;
}
```

### Backend Schemas (Pydantic)
```python
class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminDashboardResponse(BaseModel):
    total_jobs: int
    recent_jobs: int
    sources_active: int
    sync_status: str
    jobs_by_source: List[SourceDistribution]

class AdminJobResponse(BaseModel):
    jobs: List[Job]
    total: int
    page: int
    total_pages: int
```

## 🎯 Usage Examples

### Login Flow
```typescript
// Frontend login handling
const login = async (username: string, password: string) => {
  const response = await adminApi.login({ username, password });
  localStorage.setItem('adminToken', response.access_token);
  navigate('/admin/dashboard');
};
```

### Job Management
```typescript
// Fetch jobs with pagination
const fetchJobs = async (page: number, source?: string) => {
  const response = await adminApi.getJobs(page, 20, source);
  setJobs(response.jobs);
  setTotalPages(response.total_pages);
};

// Sync jobs from a source
const syncJobs = async (source: string) => {
  await adminApi.syncJobs(source);
  await fetchDashboardData(); // Refresh stats
};
```

## 🔧 Configuration

### Environment Variables
```bash
# Backend (.env)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=123123
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=8

# Frontend (.env.local)
VITE_API_URL=http://localhost:8000
VITE_ADMIN_USERNAME=admin
VITE_ADMIN_PASSWORD=123123
```

### Customization Options
- **Token expiration time** - Adjust `JWT_EXPIRE_HOURS`
- **Admin credentials** - Update `ADMIN_USERNAME` and `ADMIN_PASSWORD`
- **Pagination size** - Modify default page size in admin routes
- **UI themes** - Customize Tailwind CSS colors and styling

## 🚀 Demo

A complete HTML demo is available at `frontend/admin-demo.html` that showcases:
- Full authentication flow
- Interactive dashboard with statistics
- Job management table with actions
- Source filtering and sync operations
- Responsive design and animations

Open the demo file in your browser to see the admin system in action!

## 🛠️ Future Enhancements

### Planned Features
- **User management** for multiple admin accounts
- **Role-based permissions** with different access levels
- **Advanced analytics** with charts and graphs
- **Bulk job operations** for efficient management
- **Export functionality** for data backup and analysis
- **Real-time notifications** for sync status updates
- **Audit logging** for security and compliance

### Technical Improvements
- **Database optimization** for better performance
- **Caching layer** for faster data retrieval
- **Background job processing** for sync operations
- **WebSocket integration** for real-time updates
- **Mobile app** for admin access on the go

## 📞 Support

For questions or issues with the admin system:
1. Check the browser console for error messages
2. Verify environment variables are set correctly
3. Ensure both backend and frontend servers are running
4. Review the API documentation for endpoint requirements

The admin system is designed to be intuitive and reliable, providing comprehensive tools for managing your job search platform efficiently.
