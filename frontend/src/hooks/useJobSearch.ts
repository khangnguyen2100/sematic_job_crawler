import { Job, JobInteractionStatus } from '@/types';
import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { FilterState } from '../components/FilterSidebar';

interface UseJobSearchReturn {
  // State
  jobs: Job[];
  selectedJob: Job | null;
  searchQuery: string;
  filters: FilterState;
  isLoading: boolean;
  jobInteractions: Record<string, JobInteractionStatus>;
  page: number;
  hasMore: boolean;
  
  // Actions
  setSearchQuery: (query: string) => void;
  setFilters: (filters: FilterState) => void;
  setSelectedJob: (job: Job | null) => void;
  searchJobs: (query?: string, newFilters?: FilterState) => Promise<void>;
  loadMoreJobs: () => Promise<void>;
  refreshJobs: () => Promise<void>;
  trackJobInteraction: (jobId: string, action: string, metadata?: any) => Promise<void>;
}

const useJobSearch = (): UseJobSearchReturn => {
  const [searchParams, setSearchParams] = useSearchParams();
  // const navigate = useNavigate(); // Keep for future navigation needs
  
  // Parse URL state
  const [searchQuery, setSearchQueryState] = useState(searchParams.get('q') || '');
  const [selectedJobId, setSelectedJobId] = useState(searchParams.get('job') || null);
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '1'));
  
  // Component state
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJobState] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [jobInteractions, setJobInteractions] = useState<Record<string, JobInteractionStatus>>({});
  
  // Filter state from URL
  const [filters, setFiltersState] = useState<FilterState>(() => {
    const urlFilters: FilterState = {
      location: searchParams.get('location') || '',
      salary: {
        min: searchParams.get('salary_min') || '',
        max: searchParams.get('salary_max') || '',
      },
      jobType: searchParams.getAll('job_type'),
      experienceLevel: searchParams.getAll('experience'),
      company: searchParams.get('company') || '',
      sources: searchParams.getAll('source') as any,
      remote: searchParams.get('remote') === 'true',
    };
    return urlFilters;
  });

  // Update URL when state changes
  const updateURL = useCallback((newParams: Record<string, any>) => {
    const params = new URLSearchParams(searchParams);
    
    Object.entries(newParams).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        params.delete(key);
        value.forEach(v => params.append(key, v));
      } else if (value !== null && value !== undefined && value !== '') {
        params.set(key, value.toString());
      } else {
        params.delete(key);
      }
    });
    
    setSearchParams(params);
  }, [searchParams, setSearchParams]);

  // Set search query with URL sync
  const setSearchQuery = useCallback((query: string) => {
    setSearchQueryState(query);
    updateURL({ q: query, page: 1 });
    setPage(1);
  }, [updateURL]);

  // Set filters with URL sync
  const setFilters = useCallback((newFilters: FilterState) => {
    setFiltersState(newFilters);
    updateURL({
      location: newFilters.location,
      salary_min: newFilters.salary.min,
      salary_max: newFilters.salary.max,
      job_type: newFilters.jobType,
      experience: newFilters.experienceLevel,
      company: newFilters.company,
      source: newFilters.sources,
      remote: newFilters.remote,
      page: 1,
    });
    setPage(1);
  }, [updateURL]);

  // Set selected job with URL sync
  const setSelectedJob = useCallback((job: Job | null) => {
    setSelectedJobState(job);
    setSelectedJobId(job?.id || null);
    updateURL({ job: job?.id || null });
  }, [updateURL]);

  // Mock API calls
  const searchJobs = useCallback(async (query?: string, newFilters?: FilterState) => {
    setIsLoading(true);
    try {
      // Mock search API call - parameters used for demonstration
      console.log('Search parameters:', {
        query: query || searchQuery,
        filters: newFilters || filters,
        limit: 20,
        offset: 0,
      });
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Mock response with realistic data
      const mockJobs: Job[] = [
        {
          id: '1',
          title: 'Senior Frontend Developer',
          description: 'We are looking for a Senior Frontend Developer to join our dynamic team...',
          company_name: 'TechCorp Vietnam',
          posted_date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
          source: 'ITViec' as any,
          original_url: 'https://itviec.com/job1',
          location: 'Ho Chi Minh City',
          salary: '$1,200 - $1,800',
          job_type: 'Full-time',
          experience_level: 'Senior',
          search_score: 0.92,
        },
        {
          id: '2',
          title: 'React Developer',
          description: 'Join our startup as a React Developer and help build innovative solutions...',
          company_name: 'StartupXYZ',
          posted_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          source: 'TopCV' as any,
          original_url: 'https://topcv.vn/job2',
          location: 'Hanoi',
          salary: '$800 - $1,200',
          job_type: 'Full-time',
          experience_level: 'Mid Level',
          search_score: 0.87,
        },
        {
          id: '3',
          title: 'Full Stack Developer',
          description: 'Looking for a talented Full Stack Developer to work on exciting projects...',
          company_name: 'InnovateLab',
          posted_date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
          source: 'VietnamWorks' as any,
          original_url: 'https://vietnamworks.com/job3',
          location: 'Da Nang',
          salary: '$1,000 - $1,500',
          job_type: 'Full-time',
          experience_level: 'Mid Level',
          search_score: 0.83,
        },
        {
          id: '4',
          title: 'UI/UX Designer',
          description: 'We need a creative UI/UX Designer to enhance our user experience...',
          company_name: 'DesignStudio',
          posted_date: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
          source: 'LinkedIn' as any,
          original_url: 'https://linkedin.com/job4',
          location: 'Remote',
          salary: '$900 - $1,300',
          job_type: 'Full-time',
          experience_level: 'Mid Level',
          search_score: 0.78,
        },
        {
          id: '5',
          title: 'Backend Developer',
          description: 'Seeking a skilled Backend Developer proficient in Node.js and Python...',
          company_name: 'ServerTech',
          posted_date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
          source: 'ITViec' as any,
          original_url: 'https://itviec.com/job5',
          location: 'Ho Chi Minh City',
          salary: '$1,100 - $1,600',
          job_type: 'Full-time',
          experience_level: 'Senior',
          search_score: 0.85,
        },
      ];
      
      setJobs(mockJobs);
      setHasMore(false); // Mock no more pages
      
      // Auto-select first job if none selected
      if (!selectedJob && mockJobs.length > 0) {
        setSelectedJob(mockJobs[0]);
      }
      
    } catch (error) {
      console.error('Error searching jobs:', error);
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, filters, selectedJob, setSelectedJob]);

  const loadMoreJobs = useCallback(async () => {
    if (!hasMore || isLoading) return;
    
    setIsLoading(true);
    try {
      // Mock load more API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // For demo, just set hasMore to false
      setHasMore(false);
    } catch (error) {
      console.error('Error loading more jobs:', error);
    } finally {
      setIsLoading(false);
    }
  }, [hasMore, isLoading]);

  const refreshJobs = useCallback(async () => {
    setPage(1);
    await searchJobs();
  }, [searchJobs]);

  const trackJobInteraction = useCallback(async (jobId: string, action: string, metadata?: any) => {
    try {
      // Mock tracking API call
      console.log('Tracking job interaction:', { jobId, action, metadata });
      
      // Update local interaction state
      setJobInteractions(prev => ({
        ...prev,
        [jobId]: {
          ...prev[jobId],
          viewed: action === 'view' ? true : prev[jobId]?.viewed || false,
          clicked: action === 'click' ? true : prev[jobId]?.clicked || false,
          applied: action === 'apply' ? true : prev[jobId]?.applied || false,
          saved: action === 'save' ? true : prev[jobId]?.saved || false,
          view_count: action === 'view' ? (prev[jobId]?.view_count || 0) + 1 : prev[jobId]?.view_count || 0,
          last_interaction: new Date().toISOString(),
        }
      }));
    } catch (error) {
      console.error('Error tracking job interaction:', error);
    }
  }, []);

  // Load jobs on mount
  useEffect(() => {
    searchJobs();
  }, []);

  // Update selected job when jobs load and selectedJobId exists
  useEffect(() => {
    if (selectedJobId && jobs.length > 0) {
      const job = jobs.find(j => j.id === selectedJobId);
      if (job) {
        setSelectedJobState(job);
      }
    }
  }, [selectedJobId, jobs]);

  return {
    // State
    jobs,
    selectedJob,
    searchQuery,
    filters,
    isLoading,
    jobInteractions,
    page,
    hasMore,
    
    // Actions
    setSearchQuery,
    setFilters,
    setSelectedJob,
    searchJobs,
    loadMoreJobs,
    refreshJobs,
    trackJobInteraction,
  };
};

export default useJobSearch;