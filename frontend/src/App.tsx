import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import AdminLayout from './components/AdminLayout';
import ProtectedRoute from './components/ProtectedRoute';
import './index.css';
import AdminDashboardPage from './pages/AdminDashboardPage';
import AdminLoginPage from './pages/AdminLoginPage';
import JobSearchPage from './pages/JobSearchPage';
import CrawlLogsPage from './pages/admin/CrawlLogsPage';
import DataSourcesPage from './pages/admin/DataSourcesPage';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<JobSearchPage />} />
          
          {/* Public admin route - login */}
          <Route path="/admin/login" element={<AdminLoginPage />} />
          
          {/* Protected admin routes */}
          <Route 
            path="/admin/*" 
            element={
              <ProtectedRoute>
                <AdminLayout>
                  <Routes>
                    <Route path="dashboard" element={<AdminDashboardPage />} />
                    <Route path="data-sources" element={<DataSourcesPage />} />
                    <Route path="sources" element={<DataSourcesPage />} />
                    <Route path="crawl-logs" element={<CrawlLogsPage />} />
                    {/* Default redirect to dashboard for /admin */}
                    <Route path="" element={<AdminDashboardPage />} />
                  </Routes>
                </AdminLayout>
              </ProtectedRoute>
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
