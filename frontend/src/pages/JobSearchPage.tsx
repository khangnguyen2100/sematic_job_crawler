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

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const searchRequest: SearchRequest = {
        query: searchQuery,
        sources: selectedSources.length > 0 ? selectedSources : undefined,
        limit: 20,
        offset: 0,
      };

      const results = await jobsApi.searchJobs(searchRequest);
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadInitialJobs = async () => {
    setLoading(true);
    try {
      const results = await jobsApi.listJobs({ limit: 20 });
      setSearchResults(results);
    } catch (error) {
      console.error('Failed to load initial jobs:', error);
    } finally {
      setLoading(false);
    }
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
              <div className="flex-1">
                <Input
                  type="text"
                  placeholder="Search for jobs (e.g., 'Python developer', 'Frontend React')"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="h-12 text-lg"
                />
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
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {searchResults?.jobs.map((job, index) => (
              <JobCard key={job.id || index} job={job} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default JobSearchPage;
