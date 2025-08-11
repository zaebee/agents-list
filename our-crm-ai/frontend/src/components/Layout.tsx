import React, { ReactNode, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  User, 
  LogOut, 
  Bell, 
  Bot, 
  LayoutDashboard, 
  MessageSquare, 
  CheckSquare, 
  Menu,
  X,
  BarChart3
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useAgents } from '../contexts/AgentContext';

interface LayoutProps {
  children: ReactNode;
}

const navigationItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/agents', label: 'AI Agents', icon: Bot },
  { path: '/chat', label: 'AI Chat', icon: MessageSquare },
  { path: '/tasks', label: 'Task Manager', icon: CheckSquare },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
];

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuth();
  const { systemStatus } = useAgents();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigate = (path: string) => {
    navigate(path);
    setMobileMenuOpen(false);
  };

  const handleLogout = () => {
    logout();
    setUserMenuOpen(false);
  };

  const isCurrentPath = (path: string) => {
    return location.pathname === path;
  };

  const SidebarContent = ({ mobile = false }: { mobile?: boolean }) => (
    <div className={`${mobile ? 'h-full' : ''} bg-white/95 backdrop-blur-sm`}>
      <div className="p-6 text-center border-b border-gray-200">
        <h2 className="text-lg font-bold text-primary-600">🎯 AI Project Manager</h2>
        <p className="text-xs text-gray-500 mt-1">v2.0 - Production Ready</p>
      </div>
      
      <nav className="p-4">
        <ul className="space-y-2">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const current = isCurrentPath(item.path);
            return (
              <li key={item.path}>
                <button
                  onClick={() => handleNavigate(item.path)}
                  className={`w-full flex items-center space-x-3 px-4 py-2 rounded-lg text-left transition-colors ${
                    current
                      ? 'bg-primary-500 text-white'
                      : 'text-gray-700 hover:bg-primary-50 hover:text-primary-600'
                  }`}
                >
                  <Icon size={20} />
                  <span className="font-medium">{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
      
      {systemStatus && (
        <div className="p-4 border-t border-gray-200">
          <div className="text-xs font-medium text-gray-600 mb-2">System Status</div>
          <div className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center space-x-2 ${
            systemStatus.active_agents > 0 
              ? 'bg-green-100 text-green-800' 
              : 'bg-yellow-100 text-yellow-800'
          }`}>
            <Bot size={16} />
            <span>{systemStatus.active_agents}/{systemStatus.total_agents} Agents</span>
          </div>
          <div className="text-xs text-gray-500 text-center mt-2">
            {systemStatus.system_status === 'ready' ? 'All systems operational' : 'Demo mode active'}
          </div>
        </div>
      )}
    </div>
  );

  if (!user) return null;

  return (
    <div className="min-h-screen flex bg-gray-100">
      {/* Desktop Sidebar */}
      <div className="hidden md:block w-64 fixed inset-y-0 left-0 bg-white shadow-lg">
        <SidebarContent />
      </div>

      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="fixed inset-0 bg-black opacity-50" onClick={() => setMobileMenuOpen(false)} />
          <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-lg">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold">Menu</h2>
              <button 
                onClick={() => setMobileMenuOpen(false)}
                className="p-1 rounded-lg hover:bg-gray-100"
              >
                <X size={20} />
              </button>
            </div>
            <SidebarContent mobile />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 md:ml-64">
        {/* Top Navigation */}
        <header className="bg-white/95 backdrop-blur-sm border-b border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setMobileMenuOpen(true)}
                className="md:hidden p-2 rounded-lg hover:bg-gray-100"
              >
                <Menu size={20} />
              </button>
              <h1 className="text-lg font-bold text-primary-600 hidden md:block">
                🎯 AI Project Manager
              </h1>
            </div>

            <div className="flex items-center space-x-4">
              {/* AI Status Indicator */}
              {systemStatus && (
                <div className={`px-3 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${
                  systemStatus.active_agents > 0 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  <Bot size={14} />
                  <span>{systemStatus.active_agents}/{systemStatus.total_agents}</span>
                </div>
              )}

              {/* Notifications */}
              <button className="p-2 rounded-lg hover:bg-gray-100 relative">
                <Bell size={20} />
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  3
                </span>
              </button>

              {/* User Menu */}
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100"
                >
                  <div className="w-8 h-8 rounded-full bg-primary-500 text-white flex items-center justify-center text-sm font-semibold">
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                </button>

                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-10">
                    <div className="px-4 py-2 border-b border-gray-200">
                      <div className="flex items-center space-x-2">
                        <User size={16} />
                        <span className="text-sm font-medium">{user.username}</span>
                      </div>
                      <div className="text-xs text-gray-500">Role: {user.role}</div>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center space-x-2"
                    >
                      <LogOut size={16} />
                      <span>Logout</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="gradient-primary min-h-screen p-6">
          {children}
        </main>
      </div>
    </div>
  );
}