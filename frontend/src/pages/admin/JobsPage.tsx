import { Button, Card, CardContent, CardHeader, CardTitle, Input } from "@/components";
import { adminApi } from "@/services/api";
import { JobSource } from "@/types";
import { Job } from "@/types/admin";
import { Briefcase, Building, Calendar, Clock, DollarSign, ExternalLink, MapPin, Search, Trash2, Users } from "lucide-react";
import { useEffect, useState } from "react";

const JobsPage: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalJobs, setTotalJobs] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);
  
  const jobsPerPage = 50;

  const loadJobs = async (page: number = 1, source?: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await adminApi.getJobs(page, jobsPerPage, source);
      
      setJobs(response.jobs);
      setCurrentPage(response.current_page);
      setTotalPages(response.total_pages);
      setTotalJobs(response.total);
      
    } catch (err: any) {
      console.error('Failed to load jobs:', err);
      setError(err.message || 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs(1, selectedSource);
  }, [selectedSource]);

  const handleSearch = () => {
    loadJobs(1, selectedSource);
  };

  const handlePageChange = (page: number) => {
    loadJobs(page, selectedSource);
  };

  const handleJobSelect = (jobId: string, selected: boolean) => {
    if (selected) {
      setSelectedJobs([...selectedJobs, jobId]);
    } else {
      setSelectedJobs(selectedJobs.filter(id => id !== jobId));
    }
  };

  const handleSelectAll = () => {
    if (selectedJobs.length === jobs.length) {
      setSelectedJobs([]);
    } else {
      setSelectedJobs(jobs.map(job => job.id).filter((id): id is string => id !== undefined));
    }
  };

  const handleBulkAction = async (action: string) => {
    if (selectedJobs.length === 0) return;
    
    try {
      await adminApi.manageJobs(action, selectedJobs);
      await loadJobs(currentPage, selectedSource);
      setSelectedJobs([]);
    } catch (err: any) {
      setError(err.message || `Failed to ${action} jobs`);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this job?')) return;
    
    try {
      await adminApi.deleteJob(jobId);
      await loadJobs(currentPage, selectedSource);
    } catch (err: any) {
      setError(err.message || 'Failed to delete job');
    }
  };

  const getSourceBadgeColor = (source: JobSource) => {
    const colors = {
      [JobSource.LINKEDIN]: 'bg-blue-100 text-blue-800',
      [JobSource.TOPCV]: 'bg-green-100 text-green-800',
      [JobSource.ITVIEC]: 'bg-purple-100 text-purple-800',
      [JobSource.VIETNAMWORKS]: 'bg-orange-100 text-orange-800',
      [JobSource.OTHER]: 'bg-gray-100 text-gray-800',
    };
    return colors[source] || 'bg-gray-100 text-gray-800';
  };

  if (loading && jobs.length === 0) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading jobs...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Job Management</h1>
          <p className="text-gray-600">Manage and monitor job listings</p>
        </div>
        <div className="flex gap-2">
          {selectedJobs.length > 0 && (
            <>
              <Button 
                variant="outline" 
                onClick={() => handleBulkAction('activate')}
              >
                Activate Selected ({selectedJobs.length})
              </Button>
              <Button 
                variant="outline" 
                onClick={() => handleBulkAction('deactivate')}
              >
                Deactivate Selected
              </Button>
              <Button 
                variant="destructive" 
                onClick={() => handleBulkAction('delete')}
              >
                Delete Selected
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Briefcase className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Jobs</p>
                <p className="text-2xl font-bold text-gray-900">{totalJobs.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Users className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Jobs</p>
                <p className="text-2xl font-bold text-gray-900">{jobs.filter(j => !j.is_deleted).length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Calendar className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">This Week</p>
                <p className="text-2xl font-bold text-gray-900">
                  {jobs.filter(j => {
                    if (!j.created_at) return false;
                    const jobDate = new Date(j.created_at);
                    const weekAgo = new Date();
                    weekAgo.setDate(weekAgo.getDate() - 7);
                    return jobDate > weekAgo;
                  }).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Clock className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Recent</p>
                <p className="text-2xl font-bold text-gray-900">
                  {jobs.filter(j => {
                    if (!j.created_at) return false;
                    const jobDate = new Date(j.created_at);
                    const dayAgo = new Date();
                    dayAgo.setDate(dayAgo.getDate() - 1);
                    return jobDate > dayAgo;
                  }).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search jobs by title, company, or description..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
              </div>
            </div>
            <select 
              value={selectedSource} 
              onChange={(e) => setSelectedSource(e.target.value)}
              className="w-48 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Sources</option>
              <option value="TopCV">TopCV</option>
              <option value="LinkedIn">LinkedIn</option>
              <option value="ITViec">ITViec</option>
              <option value="VietnamWorks">VietnamWorks</option>
            </select>
            <Button onClick={handleSearch}>
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Jobs Table */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>Jobs ({totalJobs.toLocaleString()})</CardTitle>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={selectedJobs.length === jobs.length && jobs.length > 0}
                onChange={handleSelectAll}
                className="rounded"
              />
              <span className="text-sm text-gray-600">Select All</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {jobs.filter(job => job.id).map((job) => (
              <div
                key={job.id}
                className={`p-4 border rounded-lg hover:shadow-md transition-shadow ${
                  job.id && selectedJobs.includes(job.id) ? 'bg-blue-50 border-blue-200' : 'bg-white'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <input
                      type="checkbox"
                      checked={job.id ? selectedJobs.includes(job.id) : false}
                      onChange={(e) => job.id && handleJobSelect(job.id, e.target.checked)}
                      className="mt-1 rounded"
                    />
                    <div className="flex-1">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-gray-900 hover:text-blue-600 cursor-pointer">
                            {job.title}
                          </h3>
                          <p className="text-gray-600 flex items-center gap-1 mt-1">
                            <Building className="h-4 w-4" />
                            {job.company_name}
                          </p>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getSourceBadgeColor(job.source)}`}>
                          {job.source}
                        </span>
                      </div>
                      
                      <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-600">
                        {job.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="h-4 w-4" />
                            {job.location}
                          </span>
                        )}
                        {job.salary && (
                          <span className="flex items-center gap-1">
                            <DollarSign className="h-4 w-4" />
                            {job.salary}
                          </span>
                        )}
                        {job.job_type && (
                          <span className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {job.job_type}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {job.created_at ? new Date(job.created_at).toLocaleDateString() : 'N/A'}
                        </span>
                      </div>
                      
                      {job.description && (
                        <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                          {job.description.length > 150 
                            ? job.description.substring(0, 150) + '...'
                            : job.description
                          }
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 ml-4">
                    {job.original_url && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => window.open(job.original_url, '_blank')}
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => job.id && handleDeleteJob(job.id)}
                      disabled={!job.id}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-between">
              <p className="text-sm text-gray-600">
                Showing {((currentPage - 1) * jobsPerPage) + 1} to {Math.min(currentPage * jobsPerPage, totalJobs)} of {totalJobs} jobs
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage <= 1}
                >
                  Previous
                </Button>
                <span className="flex items-center px-3 py-2 text-sm">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage >= totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default JobsPage;

