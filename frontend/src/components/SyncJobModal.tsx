import {
  Activity,
  AlertCircle,
  CheckCircle,
  Clock,
  History,
  Loader2,
  Maximize,
  Minimize,
  PlayCircle,
  XCircle
} from 'lucide-react';
import React, { useCallback, useEffect, useState } from 'react';
import { adminApi } from '../services/api';
import { CrawlJobProgress, CrawlStep, CrawlStepStatus } from '../types/admin';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Progress } from './ui/progress';
import { Steps } from './ui/steps';

interface SyncJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  siteName: string;
  jobId?: string;
  mode?: 'single' | 'browse';
}

const SyncJobModal: React.FC<SyncJobModalProps> = ({ 
  isOpen, 
  onClose, 
  siteName, 
  jobId,
  mode = 'single'
}) => {
  const [progress, setProgress] = useState<CrawlJobProgress | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedStep, setSelectedStep] = useState<CrawlStep | null>(null);
  
  // Browse mode state
  const [activeJobs, setActiveJobs] = useState<any[]>([]);
  const [jobHistory, setJobHistory] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'active' | 'history'>('active');
  const [selectedJob, setSelectedJob] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Job counts from status API
  const [activeJobsCount, setActiveJobsCount] = useState(0);
  const [historyJobsCount, setHistoryJobsCount] = useState(0);

  // Fetch data based on mode
  useEffect(() => {
    if (!isOpen) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        if (mode === 'single' && jobId) {
          // Single job mode - fetch specific job progress
          const progressData = await adminApi.getSyncJobProgress(jobId);
          setProgress(progressData);
        } else if (mode === 'browse') {
          // Browse mode - fetch data based on active tab
          if (activeTab === 'active') {
            // Only fetch status for active tab
            const statusData = await adminApi.getSiteStatus(siteName);
            setActiveJobs(statusData.active_jobs || []);
            setActiveJobsCount(statusData.active_jobs_count || 0);
            setHistoryJobsCount(statusData.recent_history_count || 0);
          } else {
            // Only fetch history if we don't have it yet or if explicitly requested
            if (jobHistory.length === 0) {
              const historyData = await adminApi.getSiteJobsHistory(siteName, 10);
              setJobHistory(historyData || []);
            }
          }
        }
      } catch (err) {
        console.error('Failed to fetch data:', err);
        setError(mode === 'single' ? 'Failed to load job progress' : 'Failed to load job data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Set up polling only when needed:
    // 1. Single mode (always poll for job progress)
    // 2. Browse mode with active tab AND there are active jobs to monitor
    let interval: number | null = null;
    
    if (mode === 'single') {
      // Poll in single mode to track job progress
      interval = setInterval(fetchData, 2000);
    } else if (mode === 'browse' && activeTab === 'active' && activeJobs.length > 0) {
      // Only poll when viewing active tab and there are active jobs
      interval = setInterval(fetchData, 3000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isOpen, jobId, siteName, mode, activeTab, activeJobs.length]);

  const handleClose = () => {
    setProgress(null);
    setError(null);
    setSelectedStep(null);
    setActiveJobs([]);
    setJobHistory([]);
    setSelectedJob(null);
    onClose();
  };

  const handleJobSelect = async (job: any) => {
    try {
      setLoading(true);
      const progressData = await adminApi.getSyncJobProgress(job.job_id);
      setProgress(progressData);
      setSelectedJob(job.job_id);
    } catch (err) {
      console.error('Failed to fetch job progress:', err);
      setError('Failed to load job progress');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const diffMs = end.getTime() - start.getTime();
    const diffMinutes = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffSeconds = Math.floor((diffMs % 60000) / 1000);

    if (diffHours > 0) {
      return `${diffHours}h ${diffMinutes % 60}m`;
    } else if (diffMinutes > 0) {
      return `${diffMinutes}m ${diffSeconds}s`;
    } else {
      return `${diffSeconds}s`;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive"> = {
      'RUNNING': 'default',
      'running': 'default',
      'COMPLETED': 'secondary',
      'completed': 'secondary',
      'FAILED': 'destructive',
      'failed': 'destructive',
      'PENDING': 'secondary',
      'pending': 'secondary'
    };

    return (
      <Badge variant={variants[status] || 'secondary'}>
        {status.toUpperCase()}
      </Badge>
    );
  };

  const getOverallProgress = useCallback(() => {
    if (!progress?.steps) return 0;
    
    const completedSteps = progress.steps.filter(step => 
      step.status === CrawlStepStatus.COMPLETED
    ).length;
    
    return Math.round((completedSteps / progress.steps.length) * 100);
  }, [progress]);

  const getCurrentStepIndex = useCallback(() => {
    if (!progress?.steps) return 0;
    
    const runningIndex = progress.steps.findIndex(step => 
      step.status === CrawlStepStatus.RUNNING
    );
    
    if (runningIndex !== -1) return runningIndex;
    
    const completedCount = progress.steps.filter(step => 
      step.status === CrawlStepStatus.COMPLETED
    ).length;
    
    return Math.min(completedCount, progress.steps.length - 1);
  }, [progress]);

  const getStatusIcon = (status: CrawlStepStatus) => {
    switch (status) {
      case CrawlStepStatus.COMPLETED:
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case CrawlStepStatus.FAILED:
        return <XCircle className="h-5 w-5 text-red-500" />;
      case CrawlStepStatus.RUNNING:
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const handleTabChange = async (tab: 'active' | 'history') => {
    setActiveTab(tab);
    
    // Fetch history data when switching to history tab if we don't have it yet
    if (tab === 'history' && jobHistory.length === 0) {
      try {
        setLoading(true);
        const historyData = await adminApi.getSiteJobsHistory(siteName, 10);
        setJobHistory(historyData || []);
      } catch (err) {
        console.error('Failed to fetch job history:', err);
        setError('Failed to load job history');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleStepClick = (step: CrawlStep, _index: number) => {
    setSelectedStep(selectedStep?.id === step.id ? null : step);
  };

  const isJobComplete = progress?.status === CrawlStepStatus.COMPLETED || progress?.status === CrawlStepStatus.FAILED;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className={`overflow-y-auto ${isFullscreen ? 'max-w-[95vw] max-h-[95vh] w-[95vw] h-[95vh]' : 'max-w-6xl max-h-[90vh] w-[95vw]'}`}>
        <DialogHeader className='h-10'>
          <DialogTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {mode === 'browse' ? (
                <>
                  <Activity className="h-5 w-5" />
                  Job Progress - {siteName}
                </>
              ) : (
                <>
                  {getStatusIcon(progress?.status || CrawlStepStatus.PENDING)}
                  Sync Job Progress - {siteName}
                </>
              )}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="flex items-center gap-1"
            >
              {isFullscreen ? (
                <>
                  <Minimize className="h-4 w-4" />
                  Exit Fullscreen
                </>
              ) : (
                <>
                  <Maximize className="h-4 w-4" />
                  Fullscreen
                </>
              )}
            </Button>
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            <span className="ml-2">Loading job information...</span>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <p className="text-red-600">{error}</p>
            <Button onClick={handleClose} className="mt-4">Close</Button>
          </div>
        ) : mode === 'browse' ? (
          // Browse Mode - Show tabs with active jobs and history
          <div className="space-y-6 items-start">
            {/* Tabs */}
            <div className="flex space-x-1 mb-6">
              <Button
                variant={activeTab === 'active' ? 'default' : 'outline'}
                onClick={() => handleTabChange('active')}
                className="flex items-center gap-2"
              >
                <PlayCircle className="h-4 w-4" />
                Active Process ({activeJobsCount})
              </Button>
              <Button
                variant={activeTab === 'history' ? 'default' : 'outline'}
                onClick={() => handleTabChange('history')}
                className="flex items-center gap-2"
              >
                <History className="h-4 w-4" />
                History Process ({historyJobsCount})
              </Button>
            </div>

            {/* Tab Content */}
            <div className="space-y-4 items-start">
              {activeTab === 'active' ? (
                // Active Jobs
                <div className="items-start">
                  {activeJobs.length > 0 ? (
                    <div className="space-y-4">
                      {activeJobs.map((job) => (
                        <Card 
                          key={job.job_id}
                          className={`cursor-pointer transition-colors ${
                            selectedJob === job.job_id ? 'ring-2 ring-blue-500' : 'hover:bg-gray-50'
                          }`}
                          onClick={() => handleJobSelect(job)}
                        >
                          <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                              <CardTitle className="text-lg">Job {job.job_id.slice(0, 8)}</CardTitle>
                              {getStatusBadge(job.status)}
                            </div>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div>
                                <span className="font-medium">Started:</span> {formatDate(job.started_at)}
                              </div>
                              <div>
                                <span className="font-medium">Duration:</span> {getDuration(job.started_at)}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
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
                <div className="items-start">
                  {jobHistory.length > 0 ? (
                    <div className="space-y-4 items-start">
                      {jobHistory.map((job) => (
                        <Card 
                          key={job.job_id}
                          className={`cursor-pointer transition-colors ${
                            selectedJob === job.job_id ? 'ring-2 ring-blue-500' : 'hover:bg-gray-50'
                          }`}
                          onClick={() => handleJobSelect(job)}
                        >
                          <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                              <CardTitle className="text-lg">Job {job.job_id.slice(0, 8)}</CardTitle>
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
                                <span className="font-medium">Jobs Added:</span> {job.total_jobs_added || 0}
                              </div>
                            </div>

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

                            {job.summary && (
                              <div className="mt-3 p-3 bg-gray-50 rounded">
                                <p className="text-sm">{job.summary}</p>
                              </div>
                            )}
                          </CardContent>
                        </Card>
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

            {/* Selected Job Progress Details */}
            {progress && selectedJob && (
              <div className="border-t pt-6">
                <h3 className="font-medium text-gray-900 mb-4">Job Details - {selectedJob.slice(0, 8)}</h3>
                
                {/* Overall Progress */}
                <div className="space-y-2 mb-6">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">Overall Progress</span>
                    <span className="text-sm text-gray-500">{getOverallProgress()}%</span>
                  </div>
                  <Progress value={getOverallProgress()} className="h-3" />
                </div>

                {/* Job Statistics */}
                {(progress.total_jobs_found > 0 || progress.total_jobs_added > 0 || progress.total_duplicates > 0) && (
                  <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg mb-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{progress.total_jobs_found}</div>
                      <div className="text-xs text-gray-600">Jobs Found</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{progress.total_jobs_added}</div>
                      <div className="text-xs text-gray-600">Jobs Added</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-yellow-600">{progress.total_duplicates}</div>
                      <div className="text-xs text-gray-600">Duplicates</div>
                    </div>
                  </div>
                )}

                {/* Steps */}
                <div className="space-y-4">
                  <h4 className="font-medium text-gray-900">Crawl Steps</h4>
                  <Steps 
                    steps={progress.steps} 
                    currentStep={getCurrentStepIndex()}
                    onStepClick={handleStepClick}
                  />
                </div>

                {/* Selected Step Details */}
                {selectedStep && (
                  <div className="border rounded-lg p-4 bg-gray-50 mt-4">
                    <h5 className="font-medium text-gray-900 mb-2">{selectedStep.name}</h5>
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

                    {/* Step timing */}
                    <div className="text-xs text-gray-500 space-y-1">
                      {selectedStep.started_at && (
                        <div>Started: {new Date(selectedStep.started_at).toLocaleString()}</div>
                      )}
                      {selectedStep.completed_at && (
                        <div>Completed: {new Date(selectedStep.completed_at).toLocaleString()}</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Close Button */}
            <div className="flex justify-end pt-4 border-t">
              <Button onClick={handleClose}>Close</Button>
            </div>
          </div>
        ) : progress ? (
          // Single Job Mode - Original behavior
          <div className="space-y-6 items-start">
            {/* Overall Progress */}
            <div className="space-y-2 items-start">
              <div className="flex justify-between items-center">
                <span className="font-medium">Overall Progress</span>
                <span className="text-sm text-gray-500">{getOverallProgress()}%</span>
              </div>
              <Progress value={getOverallProgress()} className="h-3" />
            </div>

            {/* Job Statistics */}
            {(progress.total_jobs_found > 0 || progress.total_jobs_added > 0 || progress.total_duplicates > 0) && (
              <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{progress.total_jobs_found}</div>
                  <div className="text-xs text-gray-600">Jobs Found</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{progress.total_jobs_added}</div>
                  <div className="text-xs text-gray-600">Jobs Added</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">{progress.total_duplicates}</div>
                  <div className="text-xs text-gray-600">Duplicates</div>
                </div>
              </div>
            )}

            {/* Horizontal Steps */}
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">Crawl Steps</h3>
              <Steps 
                steps={progress.steps} 
                currentStep={getCurrentStepIndex()}
                onStepClick={handleStepClick}
              />
            </div>

            {/* Selected Step Details */}
            {selectedStep && (
              <div className="border rounded-lg p-4 bg-gray-50">
                <h4 className="font-medium text-gray-900 mb-2">{selectedStep.name}</h4>
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

                {/* Step timing */}
                <div className="text-xs text-gray-500 space-y-1">
                  {selectedStep.started_at && (
                    <div>Started: {new Date(selectedStep.started_at).toLocaleString()}</div>
                  )}
                  {selectedStep.completed_at && (
                    <div>Completed: {new Date(selectedStep.completed_at).toLocaleString()}</div>
                  )}
                </div>
              </div>
            )}

            {/* Job Summary */}
            {progress.summary && (
              <div className="border rounded-lg p-4">
                <div className="flex items-start gap-3">
                  {getStatusIcon(progress.status)}
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900 mb-1">Summary</h4>
                    <p className={`text-sm ${
                      progress.status === CrawlStepStatus.COMPLETED 
                        ? 'text-green-800' 
                        : progress.status === CrawlStepStatus.FAILED
                        ? 'text-red-800'
                        : 'text-blue-800'
                    }`}>{progress.summary}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Time Information */}
            <div className="text-xs text-gray-500 space-y-1">
              <div>Started: {new Date(progress.started_at).toLocaleString()}</div>
              {progress.completed_at && (
                <div>Completed: {new Date(progress.completed_at).toLocaleString()}</div>
              )}
            </div>

            {/* Close Button */}
            <div className="flex justify-end">
              <Button 
                onClick={handleClose} 
                variant={isJobComplete ? "default" : "outline"}
              >
                {isJobComplete ? "Close" : "Continue in Background"}
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <AlertCircle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <p className="text-gray-600">No progress data available</p>
            <Button onClick={handleClose} className="mt-4">Close</Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default SyncJobModal;
