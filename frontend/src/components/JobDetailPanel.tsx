import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Job } from '@/types';
import { Bookmark, Building, DollarSign, ExternalLink, MapPin, Share2 } from 'lucide-react';
import React from 'react';
import SimilarJobsWidget from './SimilarJobsWidget';

interface JobDetailPanelProps {
  selectedJob: Job | null;
  onJobClick: (job: Job) => void;
  onBookmarkJob?: (job: Job) => void;
  onShareJob?: (job: Job) => void;
}

const JobDetailPanel: React.FC<JobDetailPanelProps> = ({
  selectedJob,
  onJobClick,
  onBookmarkJob,
  onShareJob,
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

  if (!selectedJob) {
    return (
      <div className="bg-white rounded-lg shadow h-full flex items-center justify-center">
        <div className="text-center text-gray-500">
          <Building className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p className="text-lg mb-2">Select a job to view details</p>
          <p className="text-sm">Choose from the job list to see full information</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow h-full flex flex-col">
      {/* Job Header */}
      <div className="p-6 border-b">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              {selectedJob.title}
            </h1>
            <div className="flex items-center gap-4 text-gray-600 mb-3">
              <div className="flex items-center">
                <Building className="w-4 h-4 mr-2" />
                {selectedJob.company_name}
              </div>
              {selectedJob.location && (
                <div className="flex items-center">
                  <MapPin className="w-4 h-4 mr-2" />
                  {selectedJob.location}
                </div>
              )}
              {selectedJob.salary && (
                <div className="flex items-center">
                  <DollarSign className="w-4 h-4 mr-2" />
                  {selectedJob.salary}
                </div>
              )}
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              <Badge className={getSourceColor(selectedJob.source)}>
                {selectedJob.source}
              </Badge>
              <span className="text-sm text-gray-500">
                Posted {formatRelativeTime(selectedJob.posted_date)}
              </span>
              {selectedJob.search_score && (
                <Badge variant="secondary">
                  {Math.round(selectedJob.search_score * 100)}% match
                </Badge>
              )}
              {selectedJob.job_type && (
                <Badge variant="outline">
                  {selectedJob.job_type}
                </Badge>
              )}
              {selectedJob.experience_level && (
                <Badge variant="outline">
                  {selectedJob.experience_level}
                </Badge>
              )}
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex items-center gap-2 ml-4">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => onShareJob?.(selectedJob)}
            >
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => onBookmarkJob?.(selectedJob)}
            >
              <Bookmark className="w-4 h-4 mr-2" />
              Save
            </Button>
            <Button 
              onClick={() => onJobClick(selectedJob)}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Apply Now
            </Button>
          </div>
        </div>
      </div>

      {/* Job Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* Description */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Job Description</h3>
            <div className="prose prose-sm max-w-none text-gray-700">
              {selectedJob.description.split('\n').map((paragraph, index) => (
                paragraph.trim() && (
                  <p key={index} className="mb-3">{paragraph}</p>
                )
              ))}
            </div>
          </div>

          {/* Requirements */}
          {/* Note: The requirements field is not in the current Job type, but keeping for future enhancement */}
          {/* {selectedJob.requirements && selectedJob.requirements.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3">Requirements</h3>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                {selectedJob.requirements.map((req, index) => (
                  <li key={index}>{req}</li>
                ))}
              </ul>
            </div>
          )} */}

          {/* Benefits */}
          {/* Note: The benefits field is not in the current Job type, but keeping for future enhancement */}
          {/* {selectedJob.benefits && selectedJob.benefits.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3">Benefits</h3>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                {selectedJob.benefits.map((benefit, index) => (
                  <li key={index}>{benefit}</li>
                ))}
              </ul>
            </div>
          )} */}

          {/* Company Information */}
          <div>
            <h3 className="text-lg font-semibold mb-3">About {selectedJob.company_name}</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center">
                  <Building className="w-6 h-6 text-gray-600" />
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 mb-1">{selectedJob.company_name}</h4>
                  <p className="text-sm text-gray-600">
                    View more jobs from this company and learn about their culture, values, and work environment.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Similar Jobs Widget */}
          <SimilarJobsWidget currentJob={selectedJob} />
        </div>
      </div>
    </div>
  );
};

export default JobDetailPanel;