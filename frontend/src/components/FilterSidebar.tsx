import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { JobSource } from '@/types';
import { 
  Building, 
  ChevronDown, 
  ChevronUp, 
  DollarSign, 
  MapPin, 
  X 
} from 'lucide-react';
import React, { useState } from 'react';

interface FilterState {
  location: string;
  salary: {
    min: string;
    max: string;
  };
  jobType: string[];
  experienceLevel: string[];
  company: string;
  sources: JobSource[];
  remote: boolean;
}

interface FilterSidebarProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  onClearFilters: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

const FilterSidebar: React.FC<FilterSidebarProps> = ({
  filters,
  onFiltersChange,
  onClearFilters,
  isCollapsed = false,
  onToggleCollapse,
}) => {
  const [expandedSections, setExpandedSections] = useState({
    location: true,
    salary: true,
    jobType: true,
    experience: true,
    company: false,
    sources: false,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const updateFilter = (key: keyof FilterState, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value
    });
  };

  const toggleArrayFilter = (key: 'jobType' | 'experienceLevel' | 'sources', value: string) => {
    const currentArray = filters[key] as string[];
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value];
    updateFilter(key, newArray);
  };

  const jobTypes = ['Full-time', 'Part-time', 'Contract', 'Internship', 'Freelance'];
  const experienceLevels = ['Entry Level', 'Mid Level', 'Senior Level', 'Lead', 'Executive'];
  const sources = Object.values(JobSource);

  const activeFiltersCount = Object.entries(filters).reduce((count, [key, value]) => {
    if (key === 'location' && value) return count + 1;
    if (key === 'salary' && (value as any).min || (value as any).max) return count + 1;
    if (key === 'company' && value) return count + 1;
    if (key === 'remote' && value) return count + 1;
    if (Array.isArray(value) && value.length > 0) return count + 1;
    return count;
  }, 0);

  if (isCollapsed) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <Button 
          variant="outline" 
          onClick={onToggleCollapse}
          className="w-full"
        >
          <ChevronDown className="w-4 h-4 mr-2" />
          Show Filters {activeFiltersCount > 0 && `(${activeFiltersCount})`}
        </Button>
      </div>
    );
  }

  const FilterSection: React.FC<{
    title: string;
    icon: React.ReactNode;
    isExpanded: boolean;
    onToggle: () => void;
    children: React.ReactNode;
  }> = ({ title, icon, isExpanded, onToggle, children }) => (
    <div className="border-b border-gray-200 pb-4">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full py-2 text-left"
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-medium text-gray-900">{title}</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-500" />
        )}
      </button>
      {isExpanded && <div className="mt-3">{children}</div>}
    </div>
  );

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">
            Filters {activeFiltersCount > 0 && `(${activeFiltersCount})`}
          </h3>
          <div className="flex items-center gap-2">
            {activeFiltersCount > 0 && (
              <Button variant="ghost" size="sm" onClick={onClearFilters}>
                <X className="w-4 h-4 mr-1" />
                Clear
              </Button>
            )}
            {onToggleCollapse && (
              <Button variant="ghost" size="sm" onClick={onToggleCollapse}>
                <ChevronUp className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Filter Content */}
      <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
        
        {/* Location Filter */}
        <FilterSection
          title="Location"
          icon={<MapPin className="w-4 h-4" />}
          isExpanded={expandedSections.location}
          onToggle={() => toggleSection('location')}
        >
          <Input
            placeholder="City, state, or country"
            value={filters.location}
            onChange={(e) => updateFilter('location', e.target.value)}
          />
          <div className="mt-2">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={filters.remote}
                onChange={(e) => updateFilter('remote', e.target.checked)}
                className="rounded"
              />
              Remote work
            </label>
          </div>
        </FilterSection>

        {/* Salary Filter */}
        <FilterSection
          title="Salary Range"
          icon={<DollarSign className="w-4 h-4" />}
          isExpanded={expandedSections.salary}
          onToggle={() => toggleSection('salary')}
        >
          <div className="grid grid-cols-2 gap-2">
            <Input
              placeholder="Min"
              value={filters.salary.min}
              onChange={(e) => updateFilter('salary', { ...filters.salary, min: e.target.value })}
            />
            <Input
              placeholder="Max"
              value={filters.salary.max}
              onChange={(e) => updateFilter('salary', { ...filters.salary, max: e.target.value })}
            />
          </div>
        </FilterSection>

        {/* Job Type Filter */}
        <FilterSection
          title="Job Type"
          icon={<Building className="w-4 h-4" />}
          isExpanded={expandedSections.jobType}
          onToggle={() => toggleSection('jobType')}
        >
          <div className="space-y-2">
            {jobTypes.map((type) => (
              <label key={type} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={filters.jobType.includes(type)}
                  onChange={() => toggleArrayFilter('jobType', type)}
                  className="rounded"
                />
                {type}
              </label>
            ))}
          </div>
        </FilterSection>

        {/* Experience Level Filter */}
        <FilterSection
          title="Experience Level"
          icon={<Building className="w-4 h-4" />}
          isExpanded={expandedSections.experience}
          onToggle={() => toggleSection('experience')}
        >
          <div className="space-y-2">
            {experienceLevels.map((level) => (
              <label key={level} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={filters.experienceLevel.includes(level)}
                  onChange={() => toggleArrayFilter('experienceLevel', level)}
                  className="rounded"
                />
                {level}
              </label>
            ))}
          </div>
        </FilterSection>

        {/* Company Filter */}
        <FilterSection
          title="Company"
          icon={<Building className="w-4 h-4" />}
          isExpanded={expandedSections.company}
          onToggle={() => toggleSection('company')}
        >
          <Input
            placeholder="Company name"
            value={filters.company}
            onChange={(e) => updateFilter('company', e.target.value)}
          />
        </FilterSection>

        {/* Source Filter */}
        <FilterSection
          title="Job Sources"
          icon={<Building className="w-4 h-4" />}
          isExpanded={expandedSections.sources}
          onToggle={() => toggleSection('sources')}
        >
          <div className="space-y-2">
            {sources.map((source) => (
              <label key={source} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={filters.sources.includes(source)}
                  onChange={() => toggleArrayFilter('sources', source)}
                  className="rounded"
                />
                {source}
              </label>
            ))}
          </div>
        </FilterSection>
      </div>

      {/* Active Filters */}
      {activeFiltersCount > 0 && (
        <div className="p-4 border-t bg-gray-50">
          <div className="flex flex-wrap gap-2">
            {filters.location && (
              <Badge variant="secondary" className="text-xs">
                Location: {filters.location}
                <X 
                  className="w-3 h-3 ml-1 cursor-pointer" 
                  onClick={() => updateFilter('location', '')}
                />
              </Badge>
            )}
            {(filters.salary.min || filters.salary.max) && (
              <Badge variant="secondary" className="text-xs">
                Salary: {filters.salary.min || '0'} - {filters.salary.max || '∞'}
                <X 
                  className="w-3 h-3 ml-1 cursor-pointer" 
                  onClick={() => updateFilter('salary', { min: '', max: '' })}
                />
              </Badge>
            )}
            {filters.remote && (
              <Badge variant="secondary" className="text-xs">
                Remote
                <X 
                  className="w-3 h-3 ml-1 cursor-pointer" 
                  onClick={() => updateFilter('remote', false)}
                />
              </Badge>
            )}
            {filters.jobType.map((type) => (
              <Badge key={type} variant="secondary" className="text-xs">
                {type}
                <X 
                  className="w-3 h-3 ml-1 cursor-pointer" 
                  onClick={() => toggleArrayFilter('jobType', type)}
                />
              </Badge>
            ))}
            {filters.experienceLevel.map((level) => (
              <Badge key={level} variant="secondary" className="text-xs">
                {level}
                <X 
                  className="w-3 h-3 ml-1 cursor-pointer" 
                  onClick={() => toggleArrayFilter('experienceLevel', level)}
                />
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export type { FilterState };
export default FilterSidebar;