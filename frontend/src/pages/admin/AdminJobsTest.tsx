import { adminApi } from '@/services/api';
import React, { useEffect, useState } from 'react';

const AdminJobsTest: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const testAuth = () => {
      const authStatus = adminApi.isAuthenticated();
      setIsAuthenticated(authStatus);
      console.log('Authentication status:', authStatus);
      console.log('Token from localStorage:', localStorage.getItem('admin_token'));
    };

    const loadJobs = async () => {
      try {
        setLoading(true);
        console.log('Attempting to load jobs...');
        
        const response = await adminApi.getJobs(1, 5);
        console.log('Jobs response:', response);
        
        setJobs(response.jobs);
        setError(null);
      } catch (err: any) {
        console.error('Error loading jobs:', err);
        setError(err.message || 'Failed to load jobs');
      } finally {
        setLoading(false);
      }
    };

    testAuth();
    if (adminApi.isAuthenticated()) {
      loadJobs();
    } else {
      setLoading(false);
      setError('Not authenticated');
    }
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Admin Jobs Test Page</h1>
      
      <div className="mb-4 p-4 bg-gray-100 rounded">
        <h2 className="font-semibold">Debug Info:</h2>
        <p>Authenticated: {isAuthenticated ? 'Yes' : 'No'}</p>
        <p>Loading: {loading ? 'Yes' : 'No'}</p>
        <p>Error: {error || 'None'}</p>
        <p>Jobs Count: {jobs.length}</p>
      </div>

      {loading && <p>Loading jobs...</p>}
      
      {error && (
        <div className="p-4 bg-red-100 text-red-800 rounded">
          Error: {error}
        </div>
      )}
      
      {jobs.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-2">Jobs ({jobs.length}):</h2>
          {jobs.map((job) => (
            <div key={job.id} className="p-3 border rounded mb-2">
              <h3 className="font-medium">{job.title}</h3>
              <p className="text-gray-600">{job.company_name}</p>
              <p className="text-sm text-gray-500">Source: {job.source}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminJobsTest;
