import FilterSidebar, { FilterState } from '@/components/FilterSidebar';
import JobDetailPanel from '@/components/JobDetailPanel';
import SearchPanel from '@/components/SearchPanel';
import { Button } from '@/components/ui/button';
import useJobSearch from '@/hooks/useJobSearch';
import { Job } from '@/types';
import { Filter, X } from 'lucide-react';
import React, { useState } from 'react';

const TwoColumnJobSearchPage: React.FC = () => {
  const {
    jobs,
    selectedJob,
    searchQuery,
    filters,
    isLoading,
    jobInteractions,
    setSearchQuery,
    setFilters,
    setSelectedJob,
    searchJobs,
    trackJobInteraction,
  } = useJobSearch();

  const [showFilters, setShowFilters] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 1024);

  // Handle responsive behavior
  React.useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 1024);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleJobSelect = async (job: Job) => {
    setSelectedJob(job);
    
    // Track job view
    await trackJobInteraction(job.id!, 'view', {
      search_query: searchQuery,
      position_in_results: jobs.findIndex(j => j.id === job.id) + 1
    });
  };

  const handleJobClick = async (job: Job) => {
    // Track job click
    await trackJobInteraction(job.id!, 'click', {
      search_query: searchQuery,
      action: 'external_link'
    });

    // Open job in new tab
    window.open(job.original_url, '_blank');
  };

  const handleBookmarkJob = async (job: Job) => {
    await trackJobInteraction(job.id!, 'save', {
      search_query: searchQuery,
    });
  };

  const handleShareJob = async (job: Job) => {
    // Copy job URL to clipboard
    const jobUrl = `${window.location.origin}${window.location.pathname}?job=${job.id}`;
    await navigator.clipboard.writeText(jobUrl);
    
    // Track share action
    await trackJobInteraction(job.id!, 'share', {
      search_query: searchQuery,
    });
    
    // Could show a toast notification here
    alert('Job link copied to clipboard!');
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    searchJobs(searchQuery, filters);
  };

  const handleFiltersChange = (newFilters: FilterState) => {
    setFilters(newFilters);
    searchJobs(searchQuery, newFilters);
  };

  const clearFilters = () => {
    const emptyFilters: FilterState = {
      location: '',
      salary: { min: '', max: '' },
      jobType: [],
      experienceLevel: [],
      company: '',
      sources: [],
      remote: false,
    };
    handleFiltersChange(emptyFilters);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Job Search</h1>
            
            {/* Mobile Filter Toggle */}
            {isMobile && (
              <Button
                variant="outline"
                onClick={() => setShowFilters(!showFilters)}
                className="lg:hidden"
              >
                {showFilters ? (
                  <X className="w-4 h-4 mr-2" />
                ) : (
                  <Filter className="w-4 h-4 mr-2" />
                )}
                Filters
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Mobile Filters Overlay */}
        {isMobile && showFilters && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowFilters(false)} />
            <div className="fixed inset-y-0 left-0 w-80 bg-white shadow-xl overflow-y-auto">
              <div className="p-4">
                <FilterSidebar
                  filters={filters}
                  onFiltersChange={handleFiltersChange}
                  onClearFilters={clearFilters}
                />
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-140px)]">
          
          {/* Desktop Filters Sidebar */}
          <div className="hidden lg:block lg:col-span-3">
            <FilterSidebar
              filters={filters}
              onFiltersChange={handleFiltersChange}
              onClearFilters={clearFilters}
            />
          </div>
          
          {/* Search Panel - Left Column */}
          <div className="lg:col-span-4">
            <SearchPanel
              jobs={jobs}
              selectedJob={selectedJob}
              searchQuery={searchQuery}
              isLoading={isLoading}
              jobInteractions={jobInteractions}
              onJobSelect={handleJobSelect}
              onSearchQueryChange={setSearchQuery}
              onSearch={handleSearch}
            />
          </div>

          {/* Job Detail Panel - Right Column */}
          <div className="lg:col-span-5">
            <JobDetailPanel
              selectedJob={selectedJob}
              onJobClick={handleJobClick}
              onBookmarkJob={handleBookmarkJob}
              onShareJob={handleShareJob}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default TwoColumnJobSearchPage;
