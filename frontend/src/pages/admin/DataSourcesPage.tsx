import { JsonEditor } from '@/components/JsonEditor';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { adminApi } from '@/services/api';
import {
  CheckCircle,
  Database,
  Edit,
  Globe,
  Plus,
  RefreshCw,
  Settings,
  TestTube,
  Trash2,
  XCircle
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface DataSource {
  id: string;
  site_name: string;
  site_url: string;
  config: any;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const DataSourceCard: React.FC<{ 
  source: DataSource; 
  onEdit: (source: DataSource) => void;
  onDelete: (source: DataSource) => void;
  onTest: (source: DataSource) => void;
  onToggleActive: (source: DataSource) => void;
}> = ({ source, onEdit, onDelete, onTest, onToggleActive }) => {
  const getStatusIcon = () => {
    if (source.is_active) {
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    } else {
      return <XCircle className="h-5 w-5 text-gray-400" />;
    }
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <div>
              <CardTitle className="text-lg">{source.site_name}</CardTitle>
              <CardDescription>
                {source.is_active ? 'Active' : 'Inactive'}
              </CardDescription>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onTest(source)}
              title="Test connection"
            >
              <TestTube className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onEdit(source)}
              title="Edit configuration"
            >
              <Edit className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDelete(source)}
              title="Delete"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm">
            <Globe className="h-4 w-4 text-gray-400" />
            <a 
              href={source.site_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline truncate"
            >
              {source.site_url}
            </a>
          </div>
          
          <div className="grid grid-cols-2 gap-4 pt-3 border-t">
            <div>
              <p className="text-sm font-medium text-gray-900">Status</p>
              <div className="flex items-center gap-2 mt-1">
                <Switch
                  checked={source.is_active}
                  onCheckedChange={() => onToggleActive(source)}
                />
                <span className="text-xs text-gray-500">
                  {source.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">Updated</p>
              <p className="text-xs text-gray-500">
                {new Date(source.updated_at).toLocaleDateString()}
              </p>
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
  const [editingSource, setEditingSource] = useState<DataSource | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isJsonEditorOpen, setIsJsonEditorOpen] = useState(false);
  const [currentConfig, setCurrentConfig] = useState<any>({});
  const navigate = useNavigate();

  // Form state for create/edit
  const [formData, setFormData] = useState({
    site_name: '',
    site_url: '',
    config: {},
    is_active: true
  });

  useEffect(() => {
    if (!adminApi.isAuthenticated()) {
      navigate('/admin/login');
      return;
    }
    loadDataSources();
  }, [navigate]);

  const loadDataSources = async () => {
    try {
      setLoading(true);
      const data = await adminApi.getDataSources();
      setSources(data);
    } catch (error) {
      console.error('Failed to load data sources:', error);
      // Fallback to empty array if API fails
      setSources([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSource = async () => {
    try {
      await adminApi.createDataSource(formData);
      await loadDataSources();
      setIsCreateDialogOpen(false);
      resetForm();
    } catch (error) {
      console.error('Failed to create data source:', error);
      alert('Failed to create data source. Please check the console for details.');
    }
  };

  const handleEditSource = (source: DataSource) => {
    setEditingSource(source);
    setFormData({
      site_name: source.site_name,
      site_url: source.site_url,
      config: source.config,
      is_active: source.is_active
    });
    setCurrentConfig(source.config);
  };

  const handleUpdateSource = async () => {
    if (!editingSource) return;
    
    try {
      await adminApi.updateDataSource(editingSource.site_name, formData);
      await loadDataSources();
      setEditingSource(null);
      resetForm();
    } catch (error) {
      console.error('Failed to update data source:', error);
      alert('Failed to update data source. Please check the console for details.');
    }
  };

  const handleDeleteSource = async (source: DataSource) => {
    if (!confirm(`Are you sure you want to delete "${source.site_name}"?`)) {
      return;
    }

    try {
      await adminApi.deleteDataSource(source.site_name);
      await loadDataSources();
    } catch (error) {
      console.error('Failed to delete data source:', error);
      alert('Failed to delete data source. Please check the console for details.');
    }
  };

  const handleTestSource = async (source: DataSource) => {
    try {
      const result = await adminApi.testDataSource(source.site_name);
      
      const status = result.is_available ? 'Available ✅' : 'Unavailable ❌';
      let details = '';
      
      if (result.is_available) {
        details = `Status: ${result.status_code}, Response time: ${result.response_time_ms}ms`;
        if (result.final_url && result.final_url !== source.site_url) {
          details += `\nRedirected to: ${result.final_url}`;
        }
        if (result.note) {
          details += `\nNote: ${result.note}`;
        }
      } else {
        details = result.error 
          ? `Error: ${result.error}` 
          : `Status: ${result.status_code}, Response time: ${result.response_time_ms}ms`;
        if (result.note) {
          details += `\nNote: ${result.note}`;
        }
      }
      
      alert(`Test Result for ${source.site_name}:\n${status}\n${details}`);
    } catch (error) {
      console.error('Failed to test data source:', error);
      alert('Failed to test data source connectivity.');
    }
  };

  const handleToggleActive = async (source: DataSource) => {
    try {
      await adminApi.updateDataSource(source.site_name, {
        is_active: !source.is_active
      });
      await loadDataSources();
    } catch (error) {
      console.error('Failed to toggle data source:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      site_name: '',
      site_url: '',
      config: {},
      is_active: true
    });
    setCurrentConfig({});
  };

  const handleConfigSave = (newConfig: any) => {
    setFormData(prev => ({ ...prev, config: newConfig }));
    setCurrentConfig(newConfig);
    setIsJsonEditorOpen(false);
  };

  const openConfigEditor = () => {
    setCurrentConfig(formData.config);
    setIsJsonEditorOpen(true);
  };

  const activeSources = sources.filter(source => source.is_active);

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

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Data Sources</h1>
          <p className="text-gray-600 mt-1">Manage crawler configurations and data source settings</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => setIsCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Source
          </Button>
          <Button onClick={loadDataSources}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
                <p className="text-sm font-medium text-gray-600">Last Updated</p>
                <p className="text-2xl font-bold text-gray-900">Today</p>
              </div>
              <RefreshCw className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Data Sources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sources.map((source) => (
          <DataSourceCard
            key={source.id}
            source={source}
            onEdit={handleEditSource}
            onDelete={handleDeleteSource}
            onTest={handleTestSource}
            onToggleActive={handleToggleActive}
          />
        ))}
      </div>

      {sources.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No data sources configured</h3>
            <p className="text-gray-600 mb-4">
              Get started by adding your first data source configuration.
            </p>
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Data Source
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Create Data Source Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add New Data Source</DialogTitle>
            <DialogDescription>
              Configure a new data source for job crawling.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="site_name">Site Name</Label>
                <Input
                  id="site_name"
                  value={formData.site_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, site_name: e.target.value }))}
                  placeholder="e.g., TopCV"
                />
              </div>
              <div>
                <Label htmlFor="site_url">Site URL</Label>
                <Input
                  id="site_url"
                  value={formData.site_url}
                  onChange={(e) => setFormData(prev => ({ ...prev, site_url: e.target.value }))}
                  placeholder="https://example.com"
                />
              </div>
            </div>
            
            <div>
              <Label>Configuration</Label>
              <div className="flex gap-2 mt-2">
                <Input
                  readOnly
                  value={Object.keys(formData.config).length > 0 ? 'Configuration set' : 'No configuration'}
                  className="flex-1"
                />
                <Button onClick={openConfigEditor} variant="outline">
                  <Settings className="h-4 w-4 mr-2" />
                  Edit Config
                </Button>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked: boolean) => setFormData(prev => ({ ...prev, is_active: checked }))}
              />
              <Label htmlFor="is_active">Active</Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateSource}>
              Create Source
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Data Source Dialog */}
      <Dialog open={!!editingSource} onOpenChange={(open) => !open && setEditingSource(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Data Source</DialogTitle>
            <DialogDescription>
              Update the configuration for {editingSource?.site_name}.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_site_name">Site Name</Label>
                <Input
                  id="edit_site_name"
                  value={formData.site_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, site_name: e.target.value }))}
                  placeholder="e.g., TopCV"
                />
              </div>
              <div>
                <Label htmlFor="edit_site_url">Site URL</Label>
                <Input
                  id="edit_site_url"
                  value={formData.site_url}
                  onChange={(e) => setFormData(prev => ({ ...prev, site_url: e.target.value }))}
                  placeholder="https://example.com"
                />
              </div>
            </div>
            
            <div>
              <Label>Configuration</Label>
              <div className="flex gap-2 mt-2">
                <Input
                  readOnly
                  value={Object.keys(formData.config).length > 0 ? 'Configuration set' : 'No configuration'}
                  className="flex-1"
                />
                <Button onClick={openConfigEditor} variant="outline">
                  <Settings className="h-4 w-4 mr-2" />
                  Edit Config
                </Button>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="edit_is_active"
                checked={formData.is_active}
                onCheckedChange={(checked: boolean) => setFormData(prev => ({ ...prev, is_active: checked }))}
              />
              <Label htmlFor="edit_is_active">Active</Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingSource(null)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateSource}>
              Update Source
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* JSON Editor for Configuration */}
      <Dialog open={isJsonEditorOpen} onOpenChange={setIsJsonEditorOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Edit Data Source Configuration</DialogTitle>
            <DialogDescription>
              Edit JSON data and click save when finished
            </DialogDescription>
          </DialogHeader>
          <JsonEditor
            isOpen={isJsonEditorOpen}
            onOpenChange={setIsJsonEditorOpen}
            data={currentConfig}
            onSave={handleConfigSave}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DataSourcesPage;
