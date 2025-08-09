import { cn } from '@/lib/utils';
import { CrawlStep, CrawlStepStatus } from '@/types/admin';
import { AlertCircle, CheckCircle, Clock, Loader2, XCircle } from 'lucide-react';
import React from 'react';

interface StepsProps {
  steps: CrawlStep[];
  currentStep?: number;
  onStepClick?: (step: CrawlStep, index: number) => void;
  className?: string;
}

const getStatusIcon = (status: CrawlStepStatus, isActive: boolean = false) => {
  const iconClass = cn("h-4 w-4", {
    "animate-spin": status === CrawlStepStatus.RUNNING && isActive
  });

  switch (status) {
    case CrawlStepStatus.PENDING:
      return <Clock className={cn(iconClass, "text-gray-400")} />;
    case CrawlStepStatus.RUNNING:
      return <Loader2 className={cn(iconClass, "text-blue-500")} />;
    case CrawlStepStatus.COMPLETED:
      return <CheckCircle className={cn(iconClass, "text-green-500")} />;
    case CrawlStepStatus.FAILED:
      return <XCircle className={cn(iconClass, "text-red-500")} />;
    case CrawlStepStatus.SKIPPED:
      return <AlertCircle className={cn(iconClass, "text-yellow-500")} />;
    default:
      return <Clock className={cn(iconClass, "text-gray-400")} />;
  }
};

const getStatusColor = (status: CrawlStepStatus) => {
  switch (status) {
    case CrawlStepStatus.PENDING:
      return 'text-gray-600 border-gray-200';
    case CrawlStepStatus.RUNNING:
      return 'text-blue-600 border-blue-300 bg-blue-50';
    case CrawlStepStatus.COMPLETED:
      return 'text-green-600 border-green-300 bg-green-50';
    case CrawlStepStatus.FAILED:
      return 'text-red-600 border-red-300 bg-red-50';
    case CrawlStepStatus.SKIPPED:
      return 'text-yellow-600 border-yellow-300 bg-yellow-50';
    default:
      return 'text-gray-600 border-gray-200';
  }
};

const getConnectorColor = (currentStatus: CrawlStepStatus, _nextStatus: CrawlStepStatus) => {
  if (currentStatus === CrawlStepStatus.COMPLETED) {
    return 'bg-green-500';
  } else if (currentStatus === CrawlStepStatus.FAILED) {
    return 'bg-red-500';
  } else if (currentStatus === CrawlStepStatus.RUNNING) {
    return 'bg-blue-500';
  } else if (currentStatus === CrawlStepStatus.SKIPPED) {
    return 'bg-yellow-500';
  }
  return 'bg-gray-200';
};

export const Steps: React.FC<StepsProps> = ({ 
  steps, 
  currentStep, 
  onStepClick, 
  className 
}) => {
  return (
    <div className={cn("w-full", className)}>
      {/* Horizontal Steps */}
      <div className="flex items-center justify-between mb-6">
        {steps.map((step, index) => (
          <React.Fragment key={step.id}>
            {/* Step Circle */}
            <div className="flex flex-col items-center">
              <button
                onClick={() => onStepClick?.(step, index)}
                className={cn(
                  "flex items-center justify-center w-8 h-8 rounded-full border-2 transition-all duration-200",
                  getStatusColor(step.status),
                  onStepClick ? "cursor-pointer hover:scale-110" : "cursor-default",
                  currentStep === index ? "ring-2 ring-blue-300 ring-offset-2" : ""
                )}
              >
                {getStatusIcon(step.status, currentStep === index)}
              </button>
              
              {/* Step Label */}
              <div className="mt-2 text-center max-w-20">
                <div className={cn(
                  "text-xs font-medium truncate",
                  step.status === CrawlStepStatus.RUNNING ? "text-blue-600" :
                  step.status === CrawlStepStatus.COMPLETED ? "text-green-600" :
                  step.status === CrawlStepStatus.FAILED ? "text-red-600" :
                  step.status === CrawlStepStatus.SKIPPED ? "text-yellow-600" :
                  "text-gray-500"
                )}>
                  {step.name}
                </div>
              </div>
            </div>
            
            {/* Connector Line */}
            {index < steps.length - 1 && (
              <div className="flex-1 px-2">
                <div className={cn(
                  "h-0.5 w-full transition-all duration-300",
                  getConnectorColor(step.status, steps[index + 1]?.status)
                )} />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};
