import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { userTracker } from '@/services/userTracking';
import {
  Bookmark,
  Building,
  Clock,
  DollarSign,
  ExternalLink,
  Eye,
  Filter,
  MapPin,
  Search,
  Star
} from 'lucide-react';
import React, { useEffect, useState } from 'react';

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  salary?: string;
  description: string;
  requirements: string[];
  benefits: string[];
  posted_date: string;
  source: string;
  original_url: string;
  search_score?: number;
}

interface JobInteractionStatus {
  viewed: boolean;
  clicked: boolean;
  applied: boolean;
  saved: boolean;
  view_count: number;
  last_interaction?: string;
}

const TwoColumnJobSearchPage: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [jobInteractions, setJobInteractions] = useState<Record<string, JobInteractionStatus>>({});

  // Load initial jobs and interaction status
  useEffect(() => {
    loadJobs();
  }, []);

  // Load interaction status when jobs change
  useEffect(() => {
    if (jobs.length > 0) {
      loadJobInteractionStatus();
    }
  }, [jobs]);

  const loadJobs = async (query?: string) => {
    setIsLoading(true);
    try {
      const searchParams = query ? `?query=${encodeURIComponent(query)}` : '';
      const response = await fetch(`/api/jobs/search${searchParams}`);
      if (response.ok) {
        const data = await response.json();
        setJobs(data.jobs || []);
        if (data.jobs && data.jobs.length > 0 && !selectedJob) {
          setSelectedJob(data.jobs[0]);
        }
      }
    } catch (error) {
      console.error('Error loading jobs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadJobInteractionStatus = async () => {
    try {
      const jobIds = jobs.map(job => job.id);
      const interactions = await userTracker.getJobInteractionStatus(jobIds);
      setJobInteractions(interactions);
    } catch (error) {
      console.error('Error loading job interactions:', error);
    }
  };

  const handleJobSelect = async (job: Job) => {
    setSelectedJob(job);
    
    // Track job view
    await userTracker.trackJobInteraction(job.id, 'view', {
      search_query: searchQuery,
      position_in_results: jobs.findIndex(j => j.id === job.id) + 1
    });

    // Update interaction status
    setJobInteractions(prev => ({
      ...prev,
      [job.id]: {
        ...prev[job.id],
        viewed: true,
        view_count: (prev[job.id]?.view_count || 0) + 1,
        last_interaction: new Date().toISOString()
      }
    }));
  };

  const handleJobClick = async (job: Job) => {
    // Track job click
    await userTracker.trackJobInteraction(job.id, 'click', {
      search_query: searchQuery,
      action: 'external_link'
    });

    // Update interaction status
    setJobInteractions(prev => ({
      ...prev,
      [job.id]: {
        ...prev[job.id],
        clicked: true,
        last_interaction: new Date().toISOString()
      }
    }));

    // Open job in new tab
    window.open(job.original_url, '_blank');
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadJobs(searchQuery);
  };

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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Job Search</h1>
            
            {/* Search Form */}
            <form onSubmit={handleSearch} className="flex items-center gap-2 max-w-md">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  type="text"
                  placeholder="Search jobs, companies, skills..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Searching...' : 'Search'}
              </Button>
            </form>
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-140px)]">
          
          {/* Left Panel - Job List */}
          <div className="lg:col-span-1 bg-white rounded-lg shadow overflow-hidden">
            <div className="p-4 border-b bg-gray-50">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Jobs ({jobs.length})</h2>
                <Button variant="outline" size="sm">
                  <Filter className="w-4 h-4 mr-2" />
                  Filters
                </Button>
              </div>
            </div>
            
            <div className="overflow-y-auto h-full">
              {jobs.map((job) => {
                const interaction = jobInteractions[job.id];
                const isSelected = selectedJob?.id === job.id;
                
                return (
                  <div
                    key={job.id}
                    className={`
                      p-4 border-b cursor-pointer transition-colors
                      ${isSelected ? 'bg-blue-50 border-blue-200' : 'hover:bg-gray-50'}
                      ${interaction?.viewed ? 'opacity-90' : ''}
                    `}
                    onClick={() => handleJobSelect(job)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-gray-900 truncate">
                          {job.title}
                        </h3>
                        <p className="text-sm text-gray-600 truncate">
                          {job.company}
                        </p>
                      </div>
                      
                      {/* Interaction Indicators */}
                      <div className="flex items-center gap-1 ml-2">
                        {interaction?.viewed && (
                          <Badge variant="secondary" className="text-xs">
                            <Eye className="w-3 h-3 mr-1" />
                            {interaction.view_count}
                          </Badge>
                        )}
                        {interaction?.clicked && (
                          <div className="w-2 h-2 bg-blue-500 rounded-full" title="Clicked" />
                        )}
                        {interaction?.saved && (
                          <div title="Saved">
                            <Star className="w-3 h-3 text-yellow-500" />
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 text-xs text-gray-500 mb-2">
                      <div className="flex items-center">
                        <MapPin className="w-3 h-3 mr-1" />
                        {job.location}
                      </div>
                      {job.salary && (
                        <div className="flex items-center">
                          <DollarSign className="w-3 h-3 mr-1" />
                          {job.salary}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <Badge className={getSourceColor(job.source)}>
                        {job.source}
                      </Badge>
                      <div className="flex items-center text-xs text-gray-500">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatRelativeTime(job.posted_date)}
                      </div>
                    </div>

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
              
              {jobs.length === 0 && !isLoading && (
                <div className="p-8 text-center text-gray-500">
                  <Search className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>No jobs found. Try adjusting your search.</p>
                </div>
              )}
            </div>
          </div>

          {/* Right Panel - Job Details */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow">
            {selectedJob ? (
              <div className="h-full flex flex-col">
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
                          {selectedJob.company}
                        </div>
                        <div className="flex items-center">
                          <MapPin className="w-4 h-4 mr-2" />
                          {selectedJob.location}
                        </div>
                        {selectedJob.salary && (
                          <div className="flex items-center">
                            <DollarSign className="w-4 h-4 mr-2" />
                            {selectedJob.salary}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-3">
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
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <Bookmark className="w-4 h-4 mr-2" />
                        Save
                      </Button>
                      <Button 
                        onClick={() => handleJobClick(selectedJob)}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        Apply Now
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Job Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  {/* Description */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Job Description</h3>
                    <div className="prose prose-sm max-w-none text-gray-700">
                      {selectedJob.description.split('\n').map((paragraph, index) => (
                        <p key={index} className="mb-3">{paragraph}</p>
                      ))}
                    </div>
                  </div>

                  {/* Requirements */}
                  {selectedJob.requirements && selectedJob.requirements.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3">Requirements</h3>
                      <ul className="list-disc list-inside space-y-2 text-gray-700">
                        {selectedJob.requirements.map((req, index) => (
                          <li key={index}>{req}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Benefits */}
                  {selectedJob.benefits && selectedJob.benefits.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3">Benefits</h3>
                      <ul className="list-disc list-inside space-y-2 text-gray-700">
                        {selectedJob.benefits.map((benefit, index) => (
                          <li key={index}>{benefit}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <Building className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p className="text-lg mb-2">Select a job to view details</p>
                  <p className="text-sm">Choose from the job list to see full information</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TwoColumnJobSearchPage;
