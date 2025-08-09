import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { adminApi } from '@/services/api';
import { AlertCircle, CheckCircle, Clock, RefreshCw, Trash2 } from 'lucide-react';
import React, { useEffect, useState } from 'react';

interface CrawlLog {
  id: number;
  site: string;
  crawl_type: string;
  status: string;
  start_time: string;
  end_time?: string;
  jobs_processed: number;
  jobs_added: number;
  jobs_failed: number;
  errors?: any;
}

interface DashboardSummary {
  total_crawls_today: number;
  success_rate_today: number;
  total_jobs_found_today: number;
  active_crawlers: Array<{
    name?: string;
    status?: string;
  }>;
  recent_errors: Array<{
    site?: string;
    error_message?: string;
    start_time?: string;
  }>;
}

interface CrawlLogFilters {
  site: string;
  type: string;
  status: string;
  startDate: string;
  endDate: string;
}

interface Pagination {
  offset: number;
  limit: number;
  total: number;
}

const CrawlLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<CrawlLog[]>([]);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableSites, setAvailableSites] = useState<string[]>([]);
  
  const [filters, setFilters] = useState<CrawlLogFilters>({
    site: '',
    type: '',
    status: 'all',
    startDate: '',
    endDate: ''
  });
  
  const [pagination, setPagination] = useState<Pagination>({
    offset: 0,
    limit: 20,
    total: 0
  });

  // Fetch crawl logs
  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        offset: pagination.offset,
        limit: pagination.limit,
        ...(filters.site && { site_name: filters.site }),
        ...(filters.type && { crawler_type: filters.type }),
        ...(filters.status !== 'all' && { status: filters.status }),
        ...(filters.startDate && { date_from: filters.startDate }),
        ...(filters.endDate && { date_to: filters.endDate })
      };

      const data = await adminApi.getCrawlLogs(params);
      setLogs(data.logs || []);
      setPagination(prev => ({ ...prev, total: data.total || 0 }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs');
    } finally {
      setLoading(false);
    }
  };

  // Fetch dashboard summary
  const fetchSummary = async () => {
    try {
      const data = await adminApi.getCrawlLogsSummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to fetch summary:', err);
    }
  };

  // Fetch available sites
  const fetchSites = async () => {
    try {
      const data = await adminApi.getCrawlSites();
      setAvailableSites(data.sites || []);
    } catch (err) {
      console.error('Failed to fetch sites:', err);
    }
  };

  // Handle cleanup
  const cleanupLogs = async (daysToKeep: number = 30) => {
    try {
      setLoading(true);
      
      const result = await adminApi.cleanupCrawlLogs(daysToKeep);
      alert(`Cleanup completed: ${result.deleted_count || 0} logs deleted`);
      
      // Refresh logs
      fetchLogs();
      fetchSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cleanup logs');
    } finally {
      setLoading(false);
    }
  };

  // Handle refresh
  const handleRefresh = () => {
    fetchLogs();
    fetchSummary();
  };

  // Handle cleanup with confirmation
  const handleCleanup = () => {
    if (confirm('Are you sure you want to cleanup old logs (keep last 30 days)?')) {
      cleanupLogs(30);
    }
  };

  // Effects
  useEffect(() => {
    fetchLogs();
  }, [pagination.offset, pagination.limit, filters]);

  useEffect(() => {
    fetchSummary();
    fetchSites();
    
    // Refresh summary every 30 seconds
    const interval = setInterval(fetchSummary, 30000);
    return () => clearInterval(interval);
  }, []);

  // Render status badge
  const renderStatusBadge = (status: string) => {
    const statusClasses = {
      failed: 'bg-red-100 text-red-800',
      success: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800'
    };
    
    const statusIcons = {
      failed: AlertCircle,
      success: CheckCircle,
      pending: Clock
    };
    
    const IconComponent = statusIcons[status as keyof typeof statusIcons];
    const className = statusClasses[status as keyof typeof statusClasses] || 'bg-gray-100 text-gray-800';
    
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${className}`}>
        {IconComponent && <IconComponent className="w-3 h-3 mr-1" />}
        {status}
      </span>
    );
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Crawl Logs Dashboard</h1>
        <p className="text-gray-600">Monitor and manage crawler activity logs</p>
      </div>

      {/* Action Buttons */}
      <div className="mb-6 flex space-x-2">
        <Button onClick={handleRefresh} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
        <Button onClick={handleCleanup} variant="destructive">
          <Trash2 className="w-4 h-4 mr-2" />
          Cleanup Old Logs
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex">
            <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Dashboard Summary */}
      {summary && (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Active Crawlers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{summary.active_crawlers?.length || 0}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Today's Crawls</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{summary.total_crawls_today || 0}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Jobs Found Today</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-600">{summary.total_jobs_found_today || 0}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Success Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {summary.success_rate_today !== undefined && summary.success_rate_today !== null ? 
                  summary.success_rate_today.toFixed(1) : '0.0'}%
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Recent Errors */}
      {summary?.recent_errors && summary.recent_errors.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg text-red-600">Recent Errors</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {summary.recent_errors.map((errorItem, index) => (
                <div key={index} className="flex justify-between items-center p-2 bg-red-50 rounded">
                  <div>
                    <span className="font-medium">{errorItem.site}</span>
                    <span className="text-gray-500 ml-2">{errorItem.error_message}</span>
                  </div>
                  <span className="text-sm text-gray-400">
                    {errorItem.start_time ? new Date(errorItem.start_time).toLocaleString() : 'Unknown time'}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={filters.site}
              onChange={(e) => setFilters(prev => ({ ...prev, site: e.target.value }))}
            >
              <option value="">All Sites</option>
              {availableSites.map(site => (
                <option key={site} value={site}>{site}</option>
              ))}
            </select>
            
            <Input
              placeholder="Type"
              value={filters.type}
              onChange={(e) => setFilters(prev => ({ ...prev, type: e.target.value }))}
            />
            
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="success">Success</option>
              <option value="failed">Failed</option>
            </select>
            
            <Input
              type="date"
              placeholder="Start Date"
              value={filters.startDate}
              onChange={(e) => setFilters(prev => ({ ...prev, startDate: e.target.value }))}
            />
            
            <Input
              type="date"
              placeholder="End Date"
              value={filters.endDate}
              onChange={(e) => setFilters(prev => ({ ...prev, endDate: e.target.value }))}
            />
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Crawl Logs</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <RefreshCw className="w-6 h-6 animate-spin" />
              <span className="ml-2">Loading logs...</span>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Site</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Jobs</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Success Rate</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {logs.map((log) => {
                      const duration = log.end_time 
                        ? Math.round((new Date(log.end_time).getTime() - new Date(log.start_time).getTime()) / 1000)
                        : null;
                      
                      const successRate = log.jobs_processed > 0 
                        ? ((log.jobs_added / log.jobs_processed) * 100).toFixed(1)
                        : '0';

                      return (
                        <tr key={log.id} className="border-b hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {log.site}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {log.crawl_type}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {renderStatusBadge(log.status)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(log.start_time).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {duration ? `${duration}s` : '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <div className="text-xs">
                              <div>Processed: {log.jobs_processed}</div>
                              <div>Added: {log.jobs_added}</div>
                              {log.jobs_failed > 0 && (
                                <div className="text-red-600">Failed: {log.jobs_failed}</div>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <span className={`font-medium ${parseFloat(successRate) > 80 ? 'text-green-600' : parseFloat(successRate) > 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                              {successRate}%
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="mt-6 flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Showing {pagination.offset + 1} - {Math.min(pagination.offset + pagination.limit, pagination.total)} of {pagination.total}
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    onClick={() => setPagination(prev => ({ ...prev, offset: Math.max(0, prev.offset - prev.limit) }))}
                    disabled={pagination.offset === 0}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setPagination(prev => ({ ...prev, offset: prev.offset + prev.limit }))}
                    disabled={pagination.offset + pagination.limit >= pagination.total}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default CrawlLogsPage;
