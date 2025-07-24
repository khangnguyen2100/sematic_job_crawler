import { Badge } from '@/components/ui/badge';
import { Job } from '@/types';
import { Building, MapPin, TrendingUp } from 'lucide-react';
import React, { useEffect, useState } from 'react';

interface SimilarJobsWidgetProps {
  currentJob: Job;
  onJobSelect?: (job: Job) => void;
}

const SimilarJobsWidget: React.FC<SimilarJobsWidgetProps> = ({
  currentJob,
  onJobSelect,
}) => {
  const [similarJobs, setSimilarJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSimilarJobs();
  }, [currentJob.id]);

  const loadSimilarJobs = async () => {
    setLoading(true);
    try {
      // Mock similar jobs for demonstration
      // In a real implementation, this would call an API endpoint
      const mockSimilarJobs: Job[] = [
        {
          id: 'similar-1',
          title: 'Frontend Developer',
          description: 'Looking for a skilled frontend developer...',
          company_name: 'TechCorp',
          posted_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          source: 'ITViec' as any,
          original_url: 'https://example.com/job1',
          location: 'Ho Chi Minh City',
          salary: '$800 - $1,200',
          job_type: 'Full-time',
          experience_level: 'Mid-level',
          search_score: 0.85,
        },
        {
          id: 'similar-2',
          title: 'Senior React Developer',
          description: 'We are seeking a senior React developer...',
          company_name: 'StartupXYZ',
          posted_date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
          source: 'TopCV' as any,
          original_url: 'https://example.com/job2',
          location: 'Hanoi',
          salary: '$1,000 - $1,500',
          job_type: 'Full-time',
          experience_level: 'Senior',
          search_score: 0.82,
        },
        {
          id: 'similar-3',
          title: 'Full Stack Developer',
          description: 'Join our team as a full stack developer...',
          company_name: 'InnovateLab',
          posted_date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
          source: 'VietnamWorks' as any,
          original_url: 'https://example.com/job3',
          location: 'Da Nang',
          salary: '$900 - $1,400',
          job_type: 'Full-time',
          experience_level: 'Mid-level',
          search_score: 0.78,
        },
      ];

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 800));
      setSimilarJobs(mockSimilarJobs);
    } catch (error) {
      console.error('Error loading similar jobs:', error);
    } finally {
      setLoading(false);
    }
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

  const getMatchColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50';
    return 'text-orange-600 bg-orange-50';
  };

  if (loading) {
    return (
      <div>
        <h3 className="text-lg font-semibold mb-3 flex items-center">
          <TrendingUp className="w-5 h-5 mr-2" />
          Similar Jobs
        </h3>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-gray-50 rounded-lg p-4">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-lg font-semibold mb-3 flex items-center">
        <TrendingUp className="w-5 h-5 mr-2" />
        Similar Jobs
      </h3>
      
      {similarJobs.length === 0 ? (
        <div className="bg-gray-50 rounded-lg p-6 text-center">
          <TrendingUp className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          <p className="text-gray-600">No similar jobs found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {similarJobs.map((job) => (
            <div
              key={job.id}
              className="bg-gray-50 hover:bg-gray-100 rounded-lg p-4 transition-colors cursor-pointer"
              onClick={() => onJobSelect?.(job)}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 text-sm truncate">
                    {job.title}
                  </h4>
                  <div className="flex items-center gap-1 text-xs text-gray-600 mt-1">
                    <Building className="w-3 h-3" />
                    <span className="truncate">{job.company_name}</span>
                  </div>
                </div>
                {job.search_score && (
                  <Badge 
                    variant="outline" 
                    className={`text-xs ${getMatchColor(job.search_score)}`}
                  >
                    {Math.round(job.search_score * 100)}%
                  </Badge>
                )}
              </div>
              
              <div className="flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center gap-2">
                  {job.location && (
                    <div className="flex items-center">
                      <MapPin className="w-3 h-3 mr-1" />
                      {job.location}
                    </div>
                  )}
                  {job.salary && (
                    <span>{job.salary}</span>
                  )}
                </div>
                <span>{formatRelativeTime(job.posted_date)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
      
      <div className="mt-4 text-center">
        <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
          View more similar jobs →
        </button>
      </div>
    </div>
  );
};

export default SimilarJobsWidget;