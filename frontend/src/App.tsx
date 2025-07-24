import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import './index.css';
import AdminDashboardPage from './pages/AdminDashboardPage';
import AdminLoginPage from './pages/AdminLoginPage';
import JobSearchPage from './pages/JobSearchPage';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<JobSearchPage />} />
          <Route path="/admin/login" element={<AdminLoginPage />} />
          <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
