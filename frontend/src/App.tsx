import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import './index.css';
import AdminDashboardPage from './pages/AdminDashboardPage';
import AdminLoginPage from './pages/AdminLoginPage';
import JobSearchPage from './pages/JobSearchPage';
import TwoColumnJobSearchPage from './pages/TwoColumnJobSearchPage';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<TwoColumnJobSearchPage />} />
          <Route path="/search" element={<TwoColumnJobSearchPage />} />
          <Route path="/simple" element={<JobSearchPage />} />
          <Route path="/admin/login" element={<AdminLoginPage />} />
          <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
