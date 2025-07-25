import { Button } from '@/components/ui/button';
import { adminApi } from '@/services/api';
import {
  Activity,
  BarChart3,
  BookOpen,
  Briefcase,
  Database,
  Home,
  LogOut,
  Search,
  Settings,
  Users
} from 'lucide-react';
import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

interface SidebarProps {
  className?: string;
}

interface NavItem {
  label: string;
  icon: React.ReactNode;
  path: string;
  description?: string;
}

const Sidebar: React.FC<SidebarProps> = ({ className = '' }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    adminApi.logout();
    navigate('/admin/login');
  };

  const navItems: NavItem[] = [
    {
      label: 'Dashboard',
      icon: <Home className="h-4 w-4" />,
      path: '/admin/dashboard',
      description: 'Overview and statistics'
    },
    {
      label: 'Job Search',
      icon: <Search className="h-4 w-4" />,
      path: '/',
      description: 'Public job search page'
    },
    {
      label: 'Jobs Management',
      icon: <Briefcase className="h-4 w-4" />,
      path: '/admin/jobs',
      description: 'Manage job listings'
    },
    {
      label: 'Crawl Logs',
      icon: <BarChart3 className="h-4 w-4" />,
      path: '/admin/crawl-logs',
      description: 'Monitor crawler activity'
    },
    {
      label: 'Analytics',
      icon: <Activity className="h-4 w-4" />,
      path: '/admin/analytics',
      description: 'Platform analytics'
    },
    {
      label: 'User Management',
      icon: <Users className="h-4 w-4" />,
      path: '/admin/users',
      description: 'Manage users'
    },
    {
      label: 'Data Sources',
      icon: <Database className="h-4 w-4" />,
      path: '/admin/sources',
      description: 'Configure crawl sources'
    },
    {
      label: 'Documentation',
      icon: <BookOpen className="h-4 w-4" />,
      path: '/admin/docs',
      description: 'API documentation'
    },
    {
      label: 'Settings',
      icon: <Settings className="h-4 w-4" />,
      path: '/admin/settings',
      description: 'System configuration'
    }
  ];

  const isActivePath = (path: string) => {
    return location.pathname === path;
  };

  return (
    <aside className={`bg-white border-r border-gray-200 flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">JC</span>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Job Crawler</h2>
            <p className="text-xs text-gray-500">Admin Panel</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <Button
            key={item.path}
            variant={isActivePath(item.path) ? "default" : "ghost"}
            className={`w-full justify-start h-auto p-3 ${
              isActivePath(item.path) 
                ? 'bg-blue-50 text-blue-700 border-blue-200' 
                : 'text-gray-700 hover:bg-gray-100'
            }`}
            onClick={() => navigate(item.path)}
          >
            <div className="flex items-center space-x-3 w-full">
              <div className="flex-shrink-0">
                {item.icon}
              </div>
              <div className="flex-1 text-left">
                <div className="font-medium text-sm">{item.label}</div>
                {item.description && (
                  <div className="text-xs opacity-70 mt-0.5">{item.description}</div>
                )}
              </div>
            </div>
          </Button>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <Button
          variant="ghost"
          className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50"
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4 mr-3" />
          Logout
        </Button>
      </div>
    </aside>
  );
};

export default Sidebar;
