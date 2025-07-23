import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import JobSearchPage from './pages/JobSearchPage';
import './index.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<JobSearchPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
