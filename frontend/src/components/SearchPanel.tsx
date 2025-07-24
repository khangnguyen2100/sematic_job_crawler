import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Job, JobInteractionStatus } from '@/types';
import { Eye, Filter, Search, Star } from 'lucide-react';
import React from 'react';
import JobResultsList from './JobResultsList';

interface SearchPanelProps {
  jobs: Job[];
  selectedJob: Job | null;
  searchQuery: string;
  isLoading: boolean;
  jobInteractions: Record<string, JobInteractionStatus>;
  onJobSelect: (job: Job) => void;
  onSearchQueryChange: (query: string) => void;
  onSearch: (e: React.FormEvent) => void;
}

const SearchPanel: React.FC<SearchPanelProps> = ({
  jobs,
  selectedJob,
  searchQuery,
  isLoading,
  jobInteractions,
  onJobSelect,
  onSearchQueryChange,
  onSearch,
}) => {
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden h-full flex flex-col">
      {/* Search Header */}
      <div className="p-4 border-b bg-gray-50">
        <form onSubmit={onSearch} className="space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search jobs, companies, skills..."
              value={searchQuery}
              onChange={(e) => onSearchQueryChange(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Jobs ({jobs.length})</h2>
            <Button variant="outline" size="sm" type="button">
              <Filter className="w-4 h-4 mr-2" />
              Filters
            </Button>
          </div>
        </form>
      </div>
      
      {/* Quick Filters */}
      <div className="px-4 py-2 border-b bg-gray-50">
        <div className="flex gap-2 flex-wrap">
          <Badge variant="outline" className="cursor-pointer hover:bg-gray-100">
            Recent
          </Badge>
          <Badge variant="outline" className="cursor-pointer hover:bg-gray-100">
            <Star className="w-3 h-3 mr-1" />
            Bookmarked
          </Badge>
          <Badge variant="outline" className="cursor-pointer hover:bg-gray-100">
            <Eye className="w-3 h-3 mr-1" />
            Viewed
          </Badge>
          <Badge variant="outline" className="cursor-pointer hover:bg-gray-100">
            Remote
          </Badge>
        </div>
      </div>

      {/* Job Results List */}
      <div className="flex-1 overflow-hidden">
        <JobResultsList
          jobs={jobs}
          selectedJob={selectedJob}
          jobInteractions={jobInteractions}
          isLoading={isLoading}
          onJobSelect={onJobSelect}
        />
      </div>
    </div>
  );
};

export default SearchPanel;