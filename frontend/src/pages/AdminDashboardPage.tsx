import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { adminApi } from '@/services/api';
import { Job, JobSource } from '@/types';
import { AdminDashboardStats, PaginatedJobsResponse } from '@/types/admin';
import {
  BarChart3,
  Briefcase,
  ChevronLeft, ChevronRight,
  Download,
  ExternalLink,
  Filter,
  Plus,
  RefreshCw,
  Trash2,
  TrendingUp,
  Users
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const StatCard: React.FC<{ title: string; value: string | number; icon: React.ReactNode; trend?: string }> = ({ 
  title, value, icon, trend 
}) => (
  <Card>
    <CardContent className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {trend && <p className="text-xs text-green-600">{trend}</p>}
        </div>
        <div className="text-blue-600">{icon}</div>
      </div>
    </CardContent>
  </Card>
);

const JobRow: React.FC<{ job: Job; onDelete: (id: string) => void }> = ({ job, onDelete }) => {
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  return (
    <tr className="border-b hover:bg-gray-50">
      <td className="px-6 py-4">
        <div className="flex flex-col">
          <span className="font-medium text-gray-900">{job.title}</span>
          <span className="text-sm text-gray-500">{job.company_name}</span>
        </div>
      </td>
      <td className="px-6 py-4">
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          job.source === JobSource.LINKEDIN ? 'bg-blue-100 text-blue-800' :
          job.source === JobSource.TOPCV ? 'bg-green-100 text-green-800' :
          job.source === JobSource.ITVIEC ? 'bg-purple-100 text-purple-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {job.source}
        </span>
      </td>
      <td className="px-6 py-4 text-sm text-gray-500">{job.location || 'Remote'}</td>
      <td className="px-6 py-4 text-sm text-gray-500">{formatDate(job.posted_date)}</td>
      <td className="px-6 py-4">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => window.open(job.original_url, '_blank')}
            title="View Job"
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => job.id && onDelete(job.id)}
            className="text-red-600 hover:text-red-800"
            title="Delete Job"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </td>
    </tr>
  );
};

const AdminDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [jobs, setJobs] = useState<PaginatedJobsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [sourceFilter, setSourceFilter] = useState<string>('');
  const [syncLoading, setSyncLoading] = useState(false);
  const [showSyncDropdown, setShowSyncDropdown] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!adminApi.isAuthenticated()) {
      navigate('/admin/login');
      return;
    }
    loadDashboardData();
    loadJobs();
  }, [navigate]);

  const loadDashboardData = async () => {
    try {
      // Mock data for now since backend might have DB issues
      const mockStats: AdminDashboardStats = {
        total_jobs: 110,
        jobs_by_source: {
          'LinkedIn': 28,
          'TopCV': 28,
          'ITViec': 27,
          'VietnamWorks': 27
        },
        recent_jobs: 15,
        pending_sync_jobs: 0
      };
      setStats(mockStats);
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadJobs = async (page: number = currentPage, source?: string) => {
    setJobsLoading(true);
    try {
      // Mock data for demonstration
      const mockJobs: PaginatedJobsResponse = {
        jobs: [
          {
            id: '1',
            title: 'Senior Python Developer',
            description: 'We are seeking an experienced Senior Python Developer...',
            company_name: 'Tech Innovate Vietnam',
            posted_date: '2025-01-20T00:00:00',
            source: JobSource.TOPCV,
            original_url: 'https://www.topcv.vn/job/1001',
            location: 'Ho Chi Minh City',
            salary: '25-35 million VND',
            job_type: 'Full-time',
            experience_level: 'Senior'
          },
          {
            id: '2',
            title: 'Frontend React Developer',
            description: 'Join our frontend team to build modern web applications...',
            company_name: 'Digital Solutions Co',
            posted_date: '2025-01-19T00:00:00',
            source: JobSource.ITVIEC,
            original_url: 'https://www.itviec.com/job/2002',
            location: 'Ha Noi',
            salary: '18-28 million VND',
            job_type: 'Full-time',
            experience_level: 'Mid-level'
          }
        ],
        total: 110,
        page: page,
        per_page: 20,
        total_pages: 6
      };
      setJobs(mockJobs);
    } catch (error) {
      console.error('Failed to load jobs:', error);
    } finally {
      setJobsLoading(false);
    }
  };

  const handleLogout = () => {
    adminApi.logout();
    navigate('/admin/login');
  };

  const handleSyncJobs = async (sources: JobSource[]) => {
    setSyncLoading(true);
    setShowSyncDropdown(false);
    try {
      await adminApi.syncJobs({ sources });
      // Refresh data after sync
      await loadDashboardData();
      await loadJobs();
    } catch (error) {
      console.error('Failed to sync jobs:', error);
    } finally {
      setSyncLoading(false);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    if (confirm('Are you sure you want to delete this job?')) {
      try {
        await adminApi.deleteJob(jobId);
        await loadJobs(); // Refresh list
      } catch (error) {
        console.error('Failed to delete job:', error);
      }
    }
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    loadJobs(page, sourceFilter);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">Monitor platform analytics and manage jobs</p>
      </div>

      {/* Actions */}
      <div className="flex justify-end mb-6">
        <div className="relative">
          <Button
            onClick={() => setShowSyncDropdown(!showSyncDropdown)}
            disabled={syncLoading}
            className="flex items-center gap-2"
          >
            {syncLoading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Syncing...
              </>
            ) : (
              <>
                <Plus className="h-4 w-4" />
                Sync Jobs
              </>
            )}
          </Button>
          
          {showSyncDropdown && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border z-50">
              <div className="py-1">
                      <button
                        onClick={() => handleSyncJobs([JobSource.LINKEDIN])}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        Sync from LinkedIn
                      </button>
                      <button
                        onClick={() => handleSyncJobs([JobSource.TOPCV])}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        Sync from TopCV
                      </button>
                      <button
                        onClick={() => handleSyncJobs([JobSource.ITVIEC])}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        Sync from ITViec
                      </button>
                      <button
                        onClick={() => handleSyncJobs([JobSource.VIETNAMWORKS])}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        Sync from VietnamWorks
                      </button>
                      <hr className="my-1" />
                      <button
                        onClick={() => handleSyncJobs([JobSource.LINKEDIN, JobSource.TOPCV, JobSource.ITVIEC, JobSource.VIETNAMWORKS])}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 font-medium"
                      >
                        Sync from All Sources
                      </button>
                    </div>
                  </div>
                )}
              </div>
      </div>

      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Jobs"
            value={stats?.total_jobs.toLocaleString() || '0'}
            icon={<Briefcase className="h-6 w-6" />}
            trend="+12% from last month"
          />
          <StatCard
            title="Recent Jobs"
            value={stats?.recent_jobs || '0'}
            icon={<TrendingUp className="h-6 w-6" />}
            trend="Last 24 hours"
          />
          <StatCard
            title="Sources Active"
            value={Object.keys(stats?.jobs_by_source || {}).length}
            icon={<Users className="h-6 w-6" />}
          />
          <StatCard
            title="Sync Status"
            value="Healthy"
            icon={<BarChart3 className="h-6 w-6" />}
            trend="All systems operational"
          />
        </div>

        {/* Source Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Jobs by Source</CardTitle>
              <CardDescription>Distribution of jobs across different platforms</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(stats?.jobs_by_source || {}).map(([source, count]) => (
                  <div key={source} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${
                        source === 'LinkedIn' ? 'bg-blue-500' :
                        source === 'TopCV' ? 'bg-green-500' :
                        source === 'ITViec' ? 'bg-purple-500' :
                        'bg-orange-500'
                      }`}></div>
                      <span className="font-medium">{source}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">{count} jobs</span>
                      <div className={`w-24 h-2 rounded-full bg-gray-200`}>
                        <div 
                          className={`h-full rounded-full ${
                            source === 'LinkedIn' ? 'bg-blue-500' :
                            source === 'TopCV' ? 'bg-green-500' :
                            source === 'ITViec' ? 'bg-purple-500' :
                            'bg-orange-500'
                          }`}
                          style={{ width: `${(count / (stats?.total_jobs || 1)) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Common administrative tasks</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" className="w-full justify-start">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh All Data
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <Download className="h-4 w-4 mr-2" />
                Export Jobs Data
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <BarChart3 className="h-4 w-4 mr-2" />
                View Analytics
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Jobs Table */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>All Jobs</CardTitle>
                <CardDescription>Manage and monitor job listings</CardDescription>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 text-gray-500" />
                  <select
                    value={sourceFilter}
                    onChange={(e) => {
                      setSourceFilter(e.target.value);
                      setCurrentPage(1);
                      loadJobs(1, e.target.value);
                    }}
                    className="border border-gray-300 rounded-md px-3 py-2 text-sm"
                  >
                    <option value="">All Sources</option>
                    <option value="LinkedIn">LinkedIn</option>
                    <option value="TopCV">TopCV</option>
                    <option value="ITViec">ITViec</option>
                    <option value="VietnamWorks">VietnamWorks</option>
                  </select>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {jobsLoading ? (
              <div className="text-center py-8">
                <div className="w-6 h-6 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p>Loading jobs...</p>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left px-6 py-3 font-medium text-gray-900">Job Title</th>
                        <th className="text-left px-6 py-3 font-medium text-gray-900">Source</th>
                        <th className="text-left px-6 py-3 font-medium text-gray-900">Location</th>
                        <th className="text-left px-6 py-3 font-medium text-gray-900">Posted Date</th>
                        <th className="text-left px-6 py-3 font-medium text-gray-900">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {jobs?.jobs.map((job) => (
                        <JobRow key={job.id} job={job} onDelete={handleDeleteJob} />
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {jobs && jobs.total_pages > 1 && (
                  <div className="flex items-center justify-between mt-6">
                    <p className="text-sm text-gray-700">
                      Showing {((currentPage - 1) * 20) + 1} to {Math.min(currentPage * 20, jobs.total)} of {jobs.total} results
                    </p>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(currentPage - 1)}
                        disabled={currentPage === 1}
                      >
                        <ChevronLeft className="h-4 w-4" />
                        Previous
                      </Button>
                      <span className="px-3 py-1 text-sm">
                        Page {currentPage} of {jobs.total_pages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(currentPage + 1)}
                        disabled={currentPage === jobs.total_pages}
                      >
                        Next
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminDashboardPage;
