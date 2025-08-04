import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { JOB_SOURCES, MOCK_DATES, SOURCE_CONFIGURATION, UI_MESSAGES } from '@/config/constants';
import { adminApi } from '@/services/api';
import { JobSource } from '@/types';
import {
  AlertCircle,
  CheckCircle,
  Database,
  Globe,
  Plus,
  RefreshCw,
  Settings,
  XCircle
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface DataSource {
  id: string;
  name: string;
  type: JobSource;
  url: string;
  status: 'active' | 'inactive' | 'error';
  lastCrawl?: Date;
  jobsCount: number;
  description: string;
}

const DataSourceCard: React.FC<{ 
  source: DataSource; 
  onSync: (source: JobSource) => void; 
  onToggle: (id: string) => void;
  onSettings: (source: DataSource) => void;
}> = ({ source, onSync, onToggle, onSettings }) => {
  const getStatusIcon = () => {
    switch (source.status) {
      case 'active':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'inactive':
        return <XCircle className="h-5 w-5 text-gray-400" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
  };

  const getStatusText = () => {
    switch (source.status) {
      case 'active':
        return 'Active';
      case 'inactive':
        return 'Inactive';
      case 'error':
        return 'Error';
    }
  };

  const getStatusColor = () => {
    switch (source.status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Database className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <CardTitle className="text-lg">{source.name}</CardTitle>
              <CardDescription className="flex items-center gap-2">
                {getStatusIcon()}
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor()}`}>
                  {getStatusText()}
                </span>
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onSync(source.type)}
              disabled={source.status === 'inactive'}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onSettings(source)}
            >
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <p className="text-sm text-gray-600">{source.description}</p>
          
          <div className="flex items-center gap-2 text-sm">
            <Globe className="h-4 w-4 text-gray-400" />
            <a 
              href={source.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              {source.url}
            </a>
          </div>
          
          <div className="grid grid-cols-2 gap-4 pt-3 border-t">
            <div>
              <p className="text-sm font-medium text-gray-900">{source.jobsCount.toLocaleString()}</p>
              <p className="text-xs text-gray-500">Jobs Collected</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">
                {source.lastCrawl ? source.lastCrawl.toLocaleDateString() : 'Never'}
              </p>
              <p className="text-xs text-gray-500">Last Crawl</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const DataSourcesPage: React.FC = () => {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!adminApi.isAuthenticated()) {
      navigate('/admin/login');
      return;
    }
    loadDataSources();
    loadStats();
  }, [navigate]);

  const loadDataSources = async () => {
    try {
      // Get dashboard stats to populate job counts
      const dashboardStats = await adminApi.getDashboardStats();
      
      // Create data sources based on the stats from backend
      const sourcesFromStats: DataSource[] = Object.entries(dashboardStats.jobs_by_source || {}).map(([sourceName, jobCount]) => {
        const sourceType = mapSourceNameToEnum(sourceName);
        return {
          id: sourceName.toLowerCase(),
          name: sourceName,
          type: sourceType,
          url: getSourceUrl(sourceType),
          status: 'active' as const,
          lastCrawl: new Date(), // Using current date since we don't have this info yet
          jobsCount: jobCount as number,
          description: getSourceDescription(sourceType)
        };
      });
      
      setSources(sourcesFromStats);
    } catch (error) {
      console.error('Failed to load data sources:', error);
      // Fallback to mock data if API fails
      const mockSources: DataSource[] = [
        {
          id: '1',
          name: JOB_SOURCES.LINKEDIN.name,
          type: JobSource.LINKEDIN,
          url: JOB_SOURCES.LINKEDIN.url,
          status: 'active',
          lastCrawl: MOCK_DATES.LINKEDIN_LAST_CRAWL,
          jobsCount: 0,
          description: JOB_SOURCES.LINKEDIN.description
        },
        {
          id: '2',
          name: JOB_SOURCES.TOPCV.name,
          type: JobSource.TOPCV,
          url: JOB_SOURCES.TOPCV.url,
          status: 'active',
          lastCrawl: MOCK_DATES.TOPCV_LAST_CRAWL,
          jobsCount: 0,
          description: JOB_SOURCES.TOPCV.description
        },
        {
          id: '3',
          name: JOB_SOURCES.ITVIEC.name,
          type: JobSource.ITVIEC,
          url: JOB_SOURCES.ITVIEC.url,
          status: 'active',
          lastCrawl: MOCK_DATES.ITVIEC_LAST_CRAWL,
          jobsCount: 0,
          description: JOB_SOURCES.ITVIEC.description
        },
        {
          id: '4',
          name: JOB_SOURCES.VIETNAMWORKS.name,
          type: JobSource.VIETNAMWORKS,
          url: JOB_SOURCES.VIETNAMWORKS.url,
          status: 'active',
          lastCrawl: MOCK_DATES.VIETNAMWORKS_LAST_CRAWL,
          jobsCount: 0,
          description: JOB_SOURCES.VIETNAMWORKS.description
        }
      ];
      setSources(mockSources);
    } finally {
      setLoading(false);
    }
  };

  // Helper function to map source names to JobSource enum
  const mapSourceNameToEnum = (sourceName: string): JobSource => {
    switch (sourceName) {
      case 'LinkedIn':
        return JobSource.LINKEDIN;
      case 'TopCV':
        return JobSource.TOPCV;
      case 'ITViec':
        return JobSource.ITVIEC;
      case 'VietnamWorks':
        return JobSource.VIETNAMWORKS;
      default:
        return JobSource.OTHER;
    }
  };

  // Helper functions for source information
  const getSourceUrl = (sourceType: JobSource): string => {
    switch (sourceType) {
      case JobSource.LINKEDIN:
        return JOB_SOURCES.LINKEDIN.url;
      case JobSource.TOPCV:
        return JOB_SOURCES.TOPCV.url;
      case JobSource.ITVIEC:
        return JOB_SOURCES.ITVIEC.url;
      case JobSource.VIETNAMWORKS:
        return JOB_SOURCES.VIETNAMWORKS.url;
      default:
        return JOB_SOURCES.OTHER.url;
    }
  };

  const getSourceDescription = (sourceType: JobSource): string => {
    switch (sourceType) {
      case JobSource.LINKEDIN:
        return JOB_SOURCES.LINKEDIN.description;
      case JobSource.TOPCV:
        return JOB_SOURCES.TOPCV.description;
      case JobSource.ITVIEC:
        return JOB_SOURCES.ITVIEC.description;
      case JobSource.VIETNAMWORKS:
        return JOB_SOURCES.VIETNAMWORKS.description;
      default:
        return JOB_SOURCES.OTHER.description;
    }
  };

  const loadStats = async () => {
    try {
      const dashboardStats = await adminApi.getDashboardStats();
      setStats(dashboardStats);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleSyncSource = async (sourceType: JobSource) => {
    try {
      await adminApi.syncJobs({ sources: [sourceType] });
      await loadDataSources(); // Refresh data
      await loadStats(); // Refresh stats
    } catch (error) {
      console.error('Failed to sync source:', error);
    }
  };

  const handleToggleSource = async (sourceId: string) => {
    try {
      // In real implementation, this would call an API to toggle source status
      setSources(prev => prev.map(source => 
        source.id === sourceId 
          ? { ...source, status: source.status === 'active' ? 'inactive' : 'active' as any }
          : source
      ));
    } catch (error) {
      console.error('Failed to toggle source:', error);
    }
  };

  const handleSyncAll = async () => {
    try {
      const activeSources = sources
        .filter(source => source.status === 'active')
        .map(source => source.type);
      
      if (activeSources.length > 0) {
        await adminApi.syncJobs({ sources: activeSources });
        await loadDataSources();
        await loadStats();
      }
    } catch (error) {
      console.error('Failed to sync all sources:', error);
    }
  };

  const handleAddSource = () => {
    // For now, show an alert with available sources
    // In a real implementation, this would open a modal or form
    alert(`${UI_MESSAGES.ADD_SOURCE.title}:\n\n${UI_MESSAGES.ADD_SOURCE.content}`);
  };

  const handleSourceSettings = (source: DataSource) => {
    // For now, show source configuration options
    // In a real implementation, this would open a settings modal
    const configOptions = UI_MESSAGES.SETTINGS.configurationOptions.map(option => `- ${option}`).join('\n');
    alert(`Settings for ${source.name}:\n\n` +
          `Status: ${source.status}\n` +
          `Jobs Count: ${source.jobsCount}\n` +
          `URL: ${source.url}\n` +
          `Last Crawl: ${source.lastCrawl?.toLocaleDateString() || 'Never'}\n\n` +
          `Configuration options:\n${configOptions}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p>Loading data sources...</p>
        </div>
      </div>
    );
  }

  const activeSources = sources.filter(s => s.status === 'active');
  const totalJobs = sources.reduce((sum, source) => sum + source.jobsCount, 0);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Data Sources</h1>
        <p className="mt-1 text-sm text-gray-500">Configure and manage job crawling sources</p>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={handleAddSource}>
            <Plus className="h-4 w-4 mr-2" />
            Add Source
          </Button>
        </div>
        <Button onClick={handleSyncAll}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Sync All Active Sources
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Sources</p>
                <p className="text-2xl font-bold text-gray-900">{sources.length}</p>
              </div>
              <Database className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Sources</p>
                <p className="text-2xl font-bold text-gray-900">{activeSources.length}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Jobs</p>
                <p className="text-2xl font-bold text-gray-900">{totalJobs.toLocaleString()}</p>
              </div>
              <Globe className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Last Sync</p>
                <p className="text-2xl font-bold text-gray-900">Today</p>
              </div>
              <RefreshCw className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Data Sources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
        {sources.map((source) => (
          <DataSourceCard
            key={source.id}
            source={source}
            onSync={handleSyncSource}
            onToggle={handleToggleSource}
            onSettings={handleSourceSettings}
          />
        ))}
      </div>

      {/* Source Configuration */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Source Configuration</CardTitle>
          <CardDescription>
            Configure crawling settings and schedules for each data source
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Crawling Schedule</h4>
                <p className="text-sm text-gray-600">
                  {SOURCE_CONFIGURATION.DEFAULT_CRAWL_SCHEDULE}.
                  You can manually trigger crawls at any time using the sync buttons above.
                </p>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Data Retention</h4>
                <p className="text-sm text-gray-600">
                  {SOURCE_CONFIGURATION.DATA_RETENTION_DESCRIPTION}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DataSourcesPage;
