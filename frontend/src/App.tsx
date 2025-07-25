import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import AdminLayout from './components/AdminLayout';
import './index.css';
import AdminDashboardPage from './pages/AdminDashboardPage';
import AdminLoginPage from './pages/AdminLoginPage';
import JobSearchPage from './pages/JobSearchPage';
import CrawlLogsPage from './pages/admin/CrawlLogsPage';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<JobSearchPage />} />
          <Route 
            path="/admin/*" 
            element={
              <AdminLayout>
                <Routes>
                  <Route path="login" element={<AdminLoginPage />} />
                  <Route path="dashboard" element={<AdminDashboardPage />} />
                  <Route path="crawl-logs" element={<CrawlLogsPage />} />
                </Routes>
              </AdminLayout>
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
