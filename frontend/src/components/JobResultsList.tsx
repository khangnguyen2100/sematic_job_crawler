import { Badge } from '@/components/ui/badge';
import { Job, JobInteractionStatus } from '@/types';
import { Clock, DollarSign, Eye, MapPin, Search, Star } from 'lucide-react';
import React from 'react';

interface JobResultsListProps {
  jobs: Job[];
  selectedJob: Job | null;
  jobInteractions: Record<string, JobInteractionStatus>;
  isLoading: boolean;
  onJobSelect: (job: Job) => void;
}

const JobResultsList: React.FC<JobResultsListProps> = ({
  jobs,
  selectedJob,
  jobInteractions,
  isLoading,
  onJobSelect,
}) => {
  const getSourceColor = (source: string) => {
    const colors: Record<string, string> = {
      'topcv': 'bg-green-100 text-green-800',
      'itviec': 'bg-purple-100 text-purple-800',
      'vietnamworks': 'bg-orange-100 text-orange-800',
      'linkedin': 'bg-blue-100 text-blue-800'
    };
    return colors[source.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
    return date.toLocaleDateString();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-3"></div>
          <p className="text-gray-600">Loading jobs...</p>
        </div>
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-gray-500 p-8">
          <Search className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p className="text-lg mb-2">No jobs found</p>
          <p className="text-sm">Try adjusting your search criteria</p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-y-auto h-full">
      {jobs.map((job) => {
        const interaction = jobInteractions[job.id!];
        const isSelected = selectedJob?.id === job.id;
        
        return (
          <div
            key={job.id}
            className={`
              p-4 border-b cursor-pointer transition-all duration-200 hover:bg-gray-50
              ${isSelected ? 'bg-blue-50 border-blue-200 border-l-4 border-l-blue-500' : ''}
              ${interaction?.viewed ? 'opacity-90' : ''}
            `}
            onClick={() => onJobSelect(job)}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1 min-w-0">
                <h3 className={`font-medium truncate text-sm leading-5 ${
                  isSelected ? 'text-blue-900' : 'text-gray-900'
                }`}>
                  {job.title}
                </h3>
                <p className="text-sm text-gray-600 truncate mt-1">
                  {job.company_name}
                </p>
              </div>
              
              {/* Interaction Indicators */}
              <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                {interaction?.viewed && (
                  <Badge variant="secondary" className="text-xs px-1.5 py-0.5">
                    <Eye className="w-3 h-3 mr-1" />
                    {interaction.view_count}
                  </Badge>
                )}
                {interaction?.clicked && (
                  <div className="w-2 h-2 bg-blue-500 rounded-full" title="Clicked" />
                )}
                {interaction?.saved && (
                  <div title="Saved">
                    <Star className="w-3 h-3 text-yellow-500 fill-current" />
                  </div>
                )}
              </div>
            </div>
            
            {/* Job Details */}
            <div className="flex items-center gap-3 text-xs text-gray-500 mb-2 flex-wrap">
              {job.location && (
                <div className="flex items-center">
                  <MapPin className="w-3 h-3 mr-1 flex-shrink-0" />
                  <span className="truncate">{job.location}</span>
                </div>
              )}
              {job.salary && (
                <div className="flex items-center">
                  <DollarSign className="w-3 h-3 mr-1 flex-shrink-0" />
                  <span className="truncate">{job.salary}</span>
                </div>
              )}
            </div>
            
            {/* Footer */}
            <div className="flex items-center justify-between">
              <Badge className={getSourceColor(job.source)}>
                {job.source}
              </Badge>
              <div className="flex items-center text-xs text-gray-500">
                <Clock className="w-3 h-3 mr-1" />
                {formatRelativeTime(job.posted_date)}
              </div>
            </div>

            {/* Search Score */}
            {job.search_score && (
              <div className="mt-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">Match</span>
                  <span className="font-medium text-blue-600">
                    {Math.round(job.search_score * 100)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
                  <div 
                    className="bg-blue-600 h-1 rounded-full transition-all" 
                    style={{ width: `${job.search_score * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default JobResultsList;