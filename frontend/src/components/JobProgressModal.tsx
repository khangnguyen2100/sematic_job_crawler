import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Steps } from '@/components/ui/steps';
import { adminApi } from '@/services/api';
import { CrawlStep, CrawlStepStatus } from '@/types/admin';
import {
  Activity,
  AlertCircle,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Clock,
  History,
  Loader2,
  PlayCircle,
  RefreshCw,
  XCircle
} from 'lucide-react';
import React, { useCallback, useEffect, useState } from 'react';

interface JobProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  siteName: string;
}

interface JobProgress {
  job_id: string;
  site_name: string;
  status: string;
  started_at: string;
  completed_at?: string;
  total_jobs_found: number;
  total_jobs_added: number;
  total_duplicates: number;
  summary?: string;
  errors: string[];
  steps: CrawlStep[];
}

interface SiteStatus {
  site_name: string;
  active_jobs_count: number;
  has_running_job: boolean;
  active_jobs: Array<{
    job_id: string;
    status: string;
    started_at: string;
  }>;
  last_completed?: {
    job_id: string;
    status: string;
    completed_at: string;
    jobs_added: number;
    summary?: string;
  };
  recent_history_count: number;
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'RUNNING':
      return <PlayCircle className="h-4 w-4 text-blue-500" />;
    case 'COMPLETED':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'FAILED':
      return <XCircle className="h-4 w-4 text-red-500" />;
    case 'PENDING':
      return <Clock className="h-4 w-4 text-gray-400" />;
    default:
      return <Clock className="h-4 w-4 text-gray-400" />;
  }
};

const getStatusBadge = (status: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive"> = {
    'RUNNING': 'default',
    'COMPLETED': 'secondary',
    'FAILED': 'destructive',
    'PENDING': 'secondary'
  };
  
  return (
    <Badge variant={variants[status] || 'secondary'}>
      {getStatusIcon(status)}
      <span className="ml-1">{status}</span>
    </Badge>
  );
};

export const JobProgressModal: React.FC<JobProgressModalProps> = ({ 
  isOpen, 
  onClose, 
  siteName 
}) => {
  const [siteStatus, setSiteStatus] = useState<SiteStatus | null>(null);
  const [jobsHistory, setJobsHistory] = useState<JobProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'active' | 'history'>('active');
  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());
  const [selectedStep, setSelectedStep] = useState<CrawlStep | null>(null);

  // Toggle job expansion
  const toggleJobExpansion = (jobId: string) => {
    const newExpanded = new Set(expandedJobs);
    if (newExpanded.has(jobId)) {
      newExpanded.delete(jobId);
      // Clear selected step if we're collapsing the job that has the selected step
      if (selectedStep && jobsHistory.find(job => job.job_id === jobId)?.steps.some(step => step.id === selectedStep.id)) {
        setSelectedStep(null);
      }
    } else {
      newExpanded.add(jobId);
    }
    setExpandedJobs(newExpanded);
  };

  // Handle step click
  const handleStepClick = (step: CrawlStep, _index: number) => {
    setSelectedStep(selectedStep?.id === step.id ? null : step);
  };

  // Get status icon for steps
  const getStepStatusIcon = (status: CrawlStepStatus) => {
    switch (status) {
      case CrawlStepStatus.PENDING:
        return <Clock className="h-4 w-4 text-gray-400" />;
      case CrawlStepStatus.RUNNING:
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case CrawlStepStatus.COMPLETED:
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case CrawlStepStatus.FAILED:
        return <XCircle className="h-4 w-4 text-red-500" />;
      case CrawlStepStatus.SKIPPED:
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  // Stable fetch function to prevent unnecessary re-renders
  const fetchData = useCallback(async () => {
    if (!siteName) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // Fetch site status and job history
      const [statusData, historyData] = await Promise.all([
        adminApi.getSiteStatus(siteName),
        adminApi.getSiteJobsHistory(siteName, 10)
      ]);
      
      setSiteStatus(statusData);
      setJobsHistory(historyData);
    } catch (err) {
      console.error('Failed to fetch job data:', err);
      setError('Failed to load job information');
    } finally {
      setLoading(false);
    }
  }, [siteName]);

  useEffect(() => {
    if (!isOpen || !siteName) return;

    fetchData();

    // Poll for updates every 5 seconds if there are active jobs
    const interval = setInterval(() => {
      if (siteStatus?.has_running_job) {
        fetchData();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [isOpen, siteName, siteStatus?.has_running_job, fetchData]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getDuration = (startedAt: string, completedAt?: string) => {
    const start = new Date(startedAt);
    const end = completedAt ? new Date(completedAt) : new Date();
    const diffMs = end.getTime() - start.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const mins = Math.floor(diffSecs / 60);
    const secs = diffSecs % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  // Job Card Component with Step Details
  const JobCard: React.FC<{ job: JobProgress; showSteps?: boolean }> = ({ job, showSteps = true }) => {
    const isExpanded = expandedJobs.has(job.job_id);
    const hasSteps = job.steps && job.steps.length > 0;

    return (
      <Card key={job.job_id}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CardTitle className="text-lg">Job {job.job_id.slice(0, 8)}</CardTitle>
            </div>
            {getStatusBadge(job.status)}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
            <div>
              <span className="font-medium">Started:</span> {formatDate(job.started_at)}
            </div>
            {job.completed_at && (
              <div>
                <span className="font-medium">Completed:</span> {formatDate(job.completed_at)}
              </div>
            )}
            <div>
              <span className="font-medium">Duration:</span> {getDuration(job.started_at, job.completed_at)}
            </div>
            <div>
              <span className="font-medium">Jobs Added:</span> {job.total_jobs_added}
            </div>
          </div>
          
          {job.summary && (
            <div className="mt-3 p-3 bg-gray-50 rounded">
              <p className="text-sm">{job.summary}</p>
            </div>
          )}
          
          {/* Job Statistics */}
          {(job.total_jobs_found > 0 || job.total_jobs_added > 0 || job.total_duplicates > 0) && (
            <div className="grid grid-cols-3 gap-4 mt-4 p-3 bg-blue-50 rounded">
              <div className="text-center">
                <div className="text-lg font-bold text-blue-600">{job.total_jobs_found}</div>
                <div className="text-xs text-gray-600">Found</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-green-600">{job.total_jobs_added}</div>
                <div className="text-xs text-gray-600">Added</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-yellow-600">{job.total_duplicates}</div>
                <div className="text-xs text-gray-600">Duplicates</div>
              </div>
            </div>
          )}

          {/* Steps Section - Show by default for Job History */}
          {showSteps && hasSteps && (
            <div className="mt-6 border-t pt-4">
              <h4 className="font-medium text-gray-900 mb-4 flex items-center gap-2">
                Crawl Steps
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleJobExpansion(job.job_id)}
                  className="p-1 h-6 w-6 ml-auto"
                >
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </Button>
              </h4>
              <Steps 
                steps={job.steps} 
                currentStep={job.steps.findIndex(step => step.status === "running")}
                onStepClick={handleStepClick}
              />
            </div>
          )}

          {/* Selected Step Details */}
          {selectedStep && expandedJobs.has(job.job_id) && job.steps.some(step => step.id === selectedStep.id) && (
            <div className="mt-4 border rounded-lg p-4 bg-gray-50">
              <h5 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                {getStepStatusIcon(selectedStep.status)}
                {selectedStep.name}
              </h5>
              <p className="text-sm text-gray-600 mb-3">{selectedStep.description}</p>
              
              {selectedStep.message && (
                <div className="mb-3">
                  <span className="text-sm font-medium text-gray-700">Message:</span>
                  <p className="text-sm text-gray-600 mt-1">{selectedStep.message}</p>
                </div>
              )}
              
              {selectedStep.error && (
                <div className="mb-3">
                  <span className="text-sm font-medium text-red-700">Error:</span>
                  <p className="text-sm text-red-600 mt-1 font-mono bg-red-50 p-2 rounded">{selectedStep.error}</p>
                </div>
              )}
              
              {Object.keys(selectedStep.details).length > 0 && (
                <div className="mb-3">
                  <span className="text-sm font-medium text-gray-700">Details:</span>
                  <pre className="text-sm text-gray-600 mt-1 bg-white p-2 rounded border overflow-x-auto">
                    {JSON.stringify(selectedStep.details, null, 2)}
                  </pre>
                </div>
              )}
              
              <div className="flex justify-between text-xs text-gray-500">
                {selectedStep.started_at && (
                  <span>Started: {new Date(selectedStep.started_at).toLocaleTimeString()}</span>
                )}
                {selectedStep.completed_at && (
                  <span>Completed: {new Date(selectedStep.completed_at).toLocaleTimeString()}</span>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Job Progress - {siteName}
            </DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
            <span className="ml-2">Loading job information...</span>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  if (error) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Job Progress - {siteName}
            </DialogTitle>
          </DialogHeader>
          <div className="text-center py-8">
            <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <p className="text-red-600">{error}</p>
            <Button onClick={onClose} className="mt-4">Close</Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Job Progress - {siteName}
          </DialogTitle>
        </DialogHeader>

        {/* Status Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Jobs</p>
                  <p className="text-2xl font-bold">{siteStatus?.active_jobs_count || 0}</p>
                </div>
                <PlayCircle className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Status</p>
                  <p className="text-lg font-semibold">
                    {siteStatus?.has_running_job ? (
                      <span className="text-blue-600">Running</span>
                    ) : (
                      <span className="text-gray-600">Idle</span>
                    )}
                  </p>
                </div>
                {siteStatus?.has_running_job ? (
                  <RefreshCw className="h-8 w-8 text-blue-600 animate-spin" />
                ) : (
                  <CheckCircle className="h-8 w-8 text-green-600" />
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Recent History</p>
                  <p className="text-2xl font-bold">{siteStatus?.recent_history_count || 0}</p>
                </div>
                <History className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-6">
          <Button
            variant={activeTab === 'active' ? 'default' : 'outline'}
            onClick={() => setActiveTab('active')}
            className="flex items-center gap-2"
          >
            <PlayCircle className="h-4 w-4" />
            Active Jobs ({siteStatus?.active_jobs_count || 0})
          </Button>
          <Button
            variant={activeTab === 'history' ? 'default' : 'outline'}
            onClick={() => setActiveTab('history')}
            className="flex items-center gap-2"
          >
            <History className="h-4 w-4" />
            Job History ({jobsHistory.length})
          </Button>
        </div>

        {/* Tab Content */}
        <div className="space-y-4">
          {activeTab === 'active' ? (
            // Active Jobs
            <div>
              {siteStatus?.active_jobs && siteStatus.active_jobs.length > 0 ? (
                <div className="space-y-4">
                  {siteStatus.active_jobs.map((job) => {
                    // Convert active job to JobProgress format for display
                    const jobProgress: JobProgress = {
                      job_id: job.job_id,
                      site_name: siteName,
                      status: job.status,
                      started_at: job.started_at,
                      completed_at: undefined,
                      total_jobs_found: 0,
                      total_jobs_added: 0,
                      total_duplicates: 0,
                      summary: undefined,
                      errors: [],
                      steps: []
                    };
                    
                    return <JobCard key={job.job_id} job={jobProgress} showSteps={false} />;
                  })}
                </div>
              ) : (
                <Card>
                  <CardContent className="p-8 text-center">
                    <PlayCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Jobs</h3>
                    <p className="text-gray-600">There are currently no crawl jobs running for {siteName}.</p>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            // Job History
            <div>
              {jobsHistory.length > 0 ? (
                <div className="space-y-4">
                  {jobsHistory.map((job) => (
                    <JobCard key={job.job_id} job={job} showSteps={true} />
                  ))}
                </div>
              ) : (
                <Card>
                  <CardContent className="p-8 text-center">
                    <History className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Job History</h3>
                    <p className="text-gray-600">No crawl jobs have been run for {siteName} yet.</p>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>

        {/* Last Completed Job Info */}
        {siteStatus?.last_completed && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="text-lg">Last Completed Job</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm">
                    Job {siteStatus.last_completed.job_id.slice(0, 8)} •{' '}
                    {getStatusBadge(siteStatus.last_completed.status)} •{' '}
                    {siteStatus.last_completed.jobs_added} jobs added
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Completed {formatDate(siteStatus.last_completed.completed_at)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Close Button */}
        <div className="flex justify-end mt-6">
          <Button onClick={onClose}>Close</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
