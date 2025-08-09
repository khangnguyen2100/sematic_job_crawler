import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Steps } from '@/components/ui/steps';
import { adminApi } from '@/services/api';
import { CrawlJobProgress, CrawlStep, CrawlStepStatus } from '@/types/admin';
import { AlertCircle, CheckCircle, Clock, Loader2, XCircle } from 'lucide-react';
import React, { useEffect, useState } from 'react';

interface SyncJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  jobId: string;
  siteName: string;
}

const getStatusIcon = (status: CrawlStepStatus) => {
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

export const SyncJobModal: React.FC<SyncJobModalProps> = ({ isOpen, onClose, jobId, siteName }) => {
  const [progress, setProgress] = useState<CrawlJobProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStep, setSelectedStep] = useState<CrawlStep | null>(null);

  useEffect(() => {
    if (!isOpen || !jobId) return;

    const fetchProgress = async () => {
      try {
        const data = await adminApi.getSyncJobProgress(jobId);
        setProgress(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch sync job progress:', err);
        setError('Failed to load sync job progress');
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchProgress();

    // Poll for updates every 2 seconds while job is running
    const interval = setInterval(() => {
      if (progress?.status === CrawlStepStatus.RUNNING) {
        fetchProgress();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isOpen, jobId, progress?.status]);

  const getOverallProgress = () => {
    if (!progress) return 0;
    
    const totalSteps = progress.steps.length;
    const completedSteps = progress.steps.filter(step => 
      step.status === CrawlStepStatus.COMPLETED || step.status === CrawlStepStatus.SKIPPED
    ).length;
    
    return Math.round((completedSteps / totalSteps) * 100);
  };

  const getCurrentStepIndex = () => {
    if (!progress) return -1;
    
    // Find the first step that's running, or the last completed/failed step
    const runningIndex = progress.steps.findIndex(step => step.status === CrawlStepStatus.RUNNING);
    if (runningIndex !== -1) return runningIndex;
    
    // Find the last completed or failed step
    for (let i = progress.steps.length - 1; i >= 0; i--) {
      if (progress.steps[i].status === CrawlStepStatus.COMPLETED || 
          progress.steps[i].status === CrawlStepStatus.FAILED ||
          progress.steps[i].status === CrawlStepStatus.SKIPPED) {
        return i;
      }
    }
    
    return 0;
  };

  const handleStepClick = (step: CrawlStep, _index: number) => {
    setSelectedStep(selectedStep?.id === step.id ? null : step);
  };

  const isJobComplete = progress?.status === CrawlStepStatus.COMPLETED || progress?.status === CrawlStepStatus.FAILED;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {getStatusIcon(progress?.status || CrawlStepStatus.PENDING)}
            Sync Job Progress - {siteName}
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            <span className="ml-2">Loading sync job progress...</span>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <p className="text-red-600">{error}</p>
            <Button onClick={onClose} className="mt-4">Close</Button>
          </div>
        ) : progress ? (
          <div className="space-y-6">
            {/* Overall Progress */}
            <div className="space-y-2">
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

            {/* Error Summary for Failed Jobs */}
            {progress.status === CrawlStepStatus.FAILED && (
              <div className="border-l-4 border-red-500 bg-red-50 p-4">
                <div className="flex">
                  <XCircle className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Sync Job Failed</h3>
                    <div className="mt-2 text-sm text-red-700">
                      {/* Check if it's a TopCV blocking issue */}
                      {progress.errors.some(error => 
                        error.toLowerCase().includes('cloudflare') || 
                        error.toLowerCase().includes('blocked') ||
                        error.toLowerCase().includes('403') ||
                        error.toLowerCase().includes('anti-bot')
                      ) ? (
                        <div>
                          <p className="font-medium">Website Protection Detected</p>
                          <p className="mt-1">TopCV has implemented anti-bot protection (Cloudflare) that prevents automated crawling. This is a common security measure used by many job sites to prevent automated access.</p>
                          <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded">
                            <p className="text-yellow-800 text-xs">
                              <strong>Note:</strong> This is not an error in our crawler, but a deliberate protection mechanism by TopCV. 
                              Manual browsing to TopCV will work normally, but automated crawling is currently blocked.
                            </p>
                          </div>
                        </div>
                      ) : (
                        <p>The sync job encountered an error and could not complete successfully.</p>
                      )}
                      
                      {progress.errors.length > 0 && (
                        <details className="mt-3">
                          <summary className="cursor-pointer text-red-600 hover:text-red-800">
                            Show technical details
                          </summary>
                          <ul className="mt-2 list-disc list-inside text-xs">
                            {progress.errors.map((error, index) => (
                              <li key={index}>{error}</li>
                            ))}
                          </ul>
                        </details>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Summary */}
            {progress.summary && (
              <div className="space-y-2">
                <h3 className="font-medium text-gray-900">Summary</h3>
                <div className={`border-l-4 p-3 rounded ${
                  progress.status === CrawlStepStatus.COMPLETED 
                    ? 'border-green-500 bg-green-50' 
                    : progress.status === CrawlStepStatus.FAILED
                    ? 'border-red-500 bg-red-50'
                    : 'border-blue-500 bg-blue-50'
                }`}>
                  <p className={`text-sm ${
                    progress.status === CrawlStepStatus.COMPLETED 
                      ? 'text-green-800' 
                      : progress.status === CrawlStepStatus.FAILED
                      ? 'text-red-800'
                      : 'text-blue-800'
                  }`}>{progress.summary}</p>
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
                onClick={onClose} 
                variant={isJobComplete ? "default" : "outline"}
              >
                {isJobComplete ? "Close" : "Close (Running in Background)"}
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <AlertCircle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <p className="text-gray-600">No progress data available</p>
            <Button onClick={onClose} className="mt-4">Close</Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
