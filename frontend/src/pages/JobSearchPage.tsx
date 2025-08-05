import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { jobsApi } from '@/services/api';
import { Job, JobSource, SearchRequest, SearchResponse } from '@/types';
import { Briefcase, Building2, Calendar, ExternalLink, MapPin, Search } from 'lucide-react';
import React, { useEffect, useState } from 'react';

const JobCard: React.FC<{ job: Job }> = ({ job }) => {
  const handleJobClick = async () => {
    try {
      await jobsApi.trackJobClick(job.id!);
      window.open(job.original_url, '_blank');
    } catch (error) {
      console.error('Error tracking job click:', error);
      window.open(job.original_url, '_blank');
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  const getScoreColor = (score?: number) => {
    if (!score) return 'bg-gray-100 text-gray-800';
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-orange-100 text-orange-800';
  };

  const getScoreLabel = (score?: number) => {
    if (!score) return 'No score';
    if (score >= 0.8) return 'Excellent match';
    if (score >= 0.6) return 'Good match';
    return 'Fair match';
  };

  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={handleJobClick}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg font-semibold text-blue-600 hover:text-blue-800">
              {job.title}
            </CardTitle>
            <CardDescription className="flex items-center gap-2 mt-1">
              <Building2 className="h-4 w-4" />
              {job.company_name}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
              {job.source}
            </span>
            {job.search_score && (
              <div className="flex flex-col items-end gap-1">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(job.search_score)}`}>
                  {(job.search_score * 100).toFixed(1)}%
                </span>
                <span className="text-xs text-gray-500">
                  {getScoreLabel(job.search_score)}
                </span>
              </div>
            )}
            <ExternalLink className="h-4 w-4" />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-gray-700 mb-4 line-clamp-3">
          {job.description.substring(0, 200)}...
        </p>
        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          {job.location && (
            <div className="flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              {job.location}
            </div>
          )}
          {job.salary && (
            <div className="flex items-center gap-1">
              <Briefcase className="h-4 w-4" />
              {job.salary}
            </div>
          )}
          <div className="flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            {formatDate(job.posted_date)}
          </div>
        </div>
        {(job.job_type || job.experience_level) && (
          <div className="flex gap-2 mt-3">
            {job.job_type && (
              <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs">
                {job.job_type}
              </span>
            )}
            {job.experience_level && (
              <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                {job.experience_level}
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const JobSearchPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedSources, setSelectedSources] = useState<JobSource[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const jobsPerPage = 20;

  const handleSearch = async (e: React.FormEvent, page: number = 1) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    setCurrentPage(page);
    try {
      const searchRequest: SearchRequest = {
        query: searchQuery,
        sources: selectedSources.length > 0 ? selectedSources : undefined,
        limit: jobsPerPage,
        offset: (page - 1) * jobsPerPage,
      };

      const results = await jobsApi.searchJobs(searchRequest);
      setSearchResults(results);
      setShowSuggestions(false);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (page: number) => {
    const fakeEvent = { preventDefault: () => {} } as React.FormEvent;
    handleSearch(fakeEvent, page);
  };

  const loadInitialJobs = async () => {
    setLoading(true);
    try {
      const results = await jobsApi.listJobs({ limit: jobsPerPage });
      setSearchResults(results);
    } catch (error) {
      console.error('Failed to load initial jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  // Load search suggestions
  const loadSuggestions = async (query: string) => {
    if (query.length > 2) {
      try {
        const suggestions = await jobsApi.getSearchSuggestions(query, 5);
        setSuggestions(suggestions);
        setShowSuggestions(true);
      } catch (error) {
        console.error('Failed to load suggestions:', error);
      }
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    loadSuggestions(value);
  };

  const selectSuggestion = (suggestion: string) => {
    setSearchQuery(suggestion);
    setShowSuggestions(false);
    // Trigger search immediately
    const fakeEvent = { preventDefault: () => {} } as React.FormEvent;
    handleSearch(fakeEvent, 1);
  };

  useEffect(() => {
    loadInitialJobs();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Job Search Platform</h1>
            <div className="text-sm text-gray-500">
              Semantic search powered by AI
            </div>
          </div>
        </div>
      </header>

      {/* Search Section */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <Input
                  type="text"
                  placeholder="Search for jobs (e.g., 'Python developer', 'Frontend React')"
                  value={searchQuery}
                  onChange={handleSearchInputChange}
                  onFocus={() => setShowSuggestions(suggestions.length > 0)}
                  onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                  className="h-12 text-lg"
                />
                {/* Search Suggestions Dropdown */}
                {showSuggestions && suggestions.length > 0 && (
                  <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-md shadow-lg z-10 mt-1">
                    {suggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        type="button"
                        onClick={() => selectSuggestion(suggestion)}
                        className="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm border-b last:border-b-0"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <Button type="submit" disabled={loading} className="h-12 px-8">
                <Search className="h-5 w-5 mr-2" />
                {loading ? 'Searching...' : 'Search'}
              </Button>
            </div>

            {/* Source Filters */}
            <div className="flex flex-wrap gap-2">
              <span className="text-sm text-gray-600 self-center">Filter by source:</span>
              {Object.values(JobSource).map((source) => (
                <label key={source} className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedSources.includes(source)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedSources([...selectedSources, source]);
                      } else {
                        setSelectedSources(selectedSources.filter(s => s !== source));
                      }
                    }}
                    className="rounded"
                  />
                  <span className="text-sm">{source}</span>
                </label>
              ))}
            </div>
          </form>
        </div>
      </div>

      {/* Results Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {searchResults && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-900">
              {searchResults.total} jobs found
              {searchResults.query && ` for "${searchResults.query}"`}
            </h2>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Searching for jobs...</p>
          </div>
        ) : searchResults?.jobs.length === 0 ? (
          <div className="text-center py-12">
            <Briefcase className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs found</h3>
            <p className="text-gray-600">Try adjusting your search terms or filters.</p>
          </div>
        ) : (
          <div>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {searchResults?.jobs.map((job, index) => (
                <JobCard key={job.id || index} job={job} />
              ))}
            </div>
            
            {/* Pagination */}
            {searchResults && searchResults.total > jobsPerPage && (
              <div className="mt-8 flex justify-center items-center gap-2">
                <Button
                  variant="outline"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage <= 1}
                  className="px-3 py-2"
                >
                  Previous
                </Button>
                
                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, Math.ceil(searchResults.total / jobsPerPage)) }, (_, i) => {
                    const pageNum = Math.max(1, currentPage - 2) + i;
                    const totalPages = Math.ceil(searchResults.total / jobsPerPage);
                    if (pageNum > totalPages) return null;
                    
                    return (
                      <Button
                        key={pageNum}
                        variant={pageNum === currentPage ? "default" : "outline"}
                        onClick={() => handlePageChange(pageNum)}
                        className="px-3 py-2 min-w-[40px]"
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </div>
                
                <Button
                  variant="outline"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage >= Math.ceil(searchResults.total / jobsPerPage)}
                  className="px-3 py-2"
                >
                  Next
                </Button>
                
                <span className="ml-4 text-sm text-gray-600">
                  Page {currentPage} of {Math.ceil(searchResults.total / jobsPerPage)} 
                  ({searchResults.total} total jobs)
                </span>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default JobSearchPage;
